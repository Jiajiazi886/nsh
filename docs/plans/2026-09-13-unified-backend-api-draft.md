# 网页、小程序与机器人接口契约（草案）

日期：2026-09-13。状态：接口设计，不是可调用 API。需要与业务默认规则一起确认后开发。

## 1. 接口分层与兼容

- **现有**：保留 /login、/getInfo、/getRouters、/register、/logout、/captchaImage、/authConfig 和 /guild/*。
- **拟新增共享业务**：/league/v1/*，网页和小程序都用这一组，不分成两套活动数据。
- **拟新增移动聚合**：/mini/v1/bootstrap，只组合读取结果。
- **拟内部机器人接入**：/internal/bot/v1/*，默认关闭、服务身份校验，不对普通客户端开放。

以上路径均相对现有 AppConfig 的 API 路径前缀；开发/生产前缀由部署环境决定，不硬编码 localhost，也不要重复拼接 /dev-api 或 /prod-api。

认证业务统一 Authorization: Bearer TOKEN。客户端只保存 token 和展示缓存，不保存密码或整套正式活动本地状态。

### 1.1 现有登录请求

```text
POST /login
Content-Type: application/x-www-form-urlencoded

username=已有若依账号&password=已有密码&code=验证码&uuid=验证码uuid
```

code/uuid 是否需要由 captchaImage 的真实响应决定，不能在小程序绕过验证码。现有登录成功 token 在**顶层**，getInfo 也不能假设是 data 内字段；按既有响应适配，不能为了新小程序重写旧网页响应。

### 1.2 拟新业务响应

```json
{
  "code": 200,
  "msg": "操作成功",
  "success": true,
  "time": "2026-09-13T10:00:00+08:00",
  "requestId": "req_demo_001",
  "data": {}
}
```

code/msg/data 与原项目一致；新业务 DTO 采用 camelCase。BigInteger 身份 ID 一律序列化成字符串。可兼容老前端的业务错误码，但新接口拟同步正确 HTTP 状态，不一律 HTTP 200。

### 1.3 错误约定

| HTTP | errorKey 示例 | 使用场景 |
| --- | --- | --- |
| 400 / 422 | INVALID_CONFIG、INVALID_CSV、INVALID_PROFESSION | 结构、字段、数值/职业校验 |
| 401 | AUTH_REQUIRED、TOKEN_EXPIRED | 未登录/会话无效 |
| 403 | ORG_PERMISSION_DENIED | 没有当前组织所需能力 |
| 404 | ACTIVITY_NOT_FOUND、SNAPSHOT_NOT_FOUND | 不存在或按隐私策略隐藏无权对象 |
| 409 | VERSION_CONFLICT、SEAT_OCCUPIED、ALREADY_ASSIGNED | 版本、席位、重复报名冲突 |
| 409 | IDEMPOTENCY_KEY_REUSED、IMPORT_CONTEXT_CHANGED | 幂等键被换内容使用、预览上下文变化 |
| 413 | FILE_TOO_LARGE | CSV 大小/行数上限 |
| 429 | RATE_LIMITED | 登录、绑定、报名、通知限流 |
| 503 | INTEGRATION_DISABLED、CHANNEL_UNAVAILABLE | 未启用通道或暂不可用；不伪报发送成功 |

```json
{
  "code": 409,
  "msg": "这个位置已经有人，请刷新后重新选择",
  "success": false,
  "errorKey": "SEAT_OCCUPIED",
  "requestId": "req_demo_002",
  "data": {
    "releaseId": "release_001",
    "seatKey": "seat_01",
    "latestSeatVersion": 8
  }
}
```

冲突响应不泄漏其他玩家联系方式或密码。运行异常不原样返回栈、SQL、密钥或文件路径。

## 2. 页面与接口对应

小程序页面来自当前外部 Demo，网页页面来自原项目。下面新路径均未实现。

| 界面 | 读取 | 操作/后续改动 |
| --- | --- | --- |
| login | 现有 authConfig/captchaImage/getInfo | 现有 login/logout；去掉任意非空密码体验登录 |
| activities | GET /league/v1/activities、/public-activities | 组织/公开/本人/历史筛选，返回真实 capability |
| organization | GET /league/v1/me/organizations、/organizations/{orgId}/members | 职业树查询；成员和本场临时参与者严格分开 |
| org-manage | 组织角色、模板、已有入会申请适配查询 | 管理助理权限、模板 JSON；组织创建/邀请码规则待确认 |
| activity | GET /league/v1/activities/{id}、公开 lineup、vacancies | 本人 signup/cancel；管理预排走 lineup commands |
| activity-manage | 活动列表、CSV 队列、模板 | 创建活动、状态命令、导入预览/确认；不是直接新建即公开 |
| lineup | 编辑 lineup、候选职业树、临时人员、snapshots | 团/队/席位/职业/位置命令、保存/恢复、管理员发布 |
| analysis | GET /league/v1/analysis-runs/{runId}/overview | 必须先选活动、最终快照、确认 CSV |
| players | /analysis-runs/{runId}/players?professionId&metricId | 保留全局排名并按职业分组；分页/搜索 |
| teams | /analysis-runs/{runId}/groups 与 squads | 统计与有效数据成员树，缺数据另计 |
| boxes | /analysis-runs/{runId}/boxes | 创建、改名、复制、删除；折叠仅本地偏好 |
| box-edit | run 的 squad/player 查询 | 基选小队 + manualAddIds/manualRemoveIds |
| player | /analysis-runs/{runId}/players/{dataPlayerId} | 当前 run 全部指标、当时所属团/队 |
| profile | /league/v1/me、me/identities | 编辑主副职业/别名、密码仍用原 UserService 流程 |
| settings | /league/v1/me/notification-preferences、/me/identities | 绑定/解绑，通知 opt-in；通道未启用时清楚显示 |
| 网页 guild/schedule | 旧历史/workbook 保留 | 新页选择 activityId，职业树 + 团/队/凳子，拖拽调用同一命令 |
| 网页 guild/analysis | 旧 schedule-battle 保留历史兼容 | 新分析选 runId，不临时拼接不相干排表和 CSV |
| 网页 guild/member/info/review | 原成员/职业/申请接口 | 加组织范围适配；不重建若依用户 |
| 微信机器人 | 相同公开/职业/本人范围服务 | 接入标准化消息、绑定、outbox，不直接操作各端本地缓存 |

## 3. 通用约定

### 3.1 版本与幂等

- 写请求使用 Idempotency-Key；服务端按真实 userId + command/resource 隔离。
- 编辑阵容与模板使用 expectedVersion；版本不是客户端时间戳。
- 抢位使用当前 releaseId + 目标席位版本。其他玩家占了另一席位不应只因全局计数变化就让合法请求失败。
- 发布/最终快照/CSV 确认都检查所引用对象属于同活动同组织且未变更。
- 幂等键相同但 payloadHash 不同返回 409，不能复用成功结果误认另一命令成功。

### 3.2 职业树读取

```text
GET /league/v1/organizations/{orgId}/members?groupBy=profession&q=封&professionId=longyin&pageSize=30&cursor=...
```

职业 DTO 包含 professionId、name、color、orderNum、enabled；未知职业归类为 unknown，不消失。树展开状态只在端内保存。

```json
{
  "groups": [
    {
      "professionId": "longyin",
      "professionName": "龙吟",
      "color": "#D95D16",
      "totalCount": 1,
      "players": [
        {
          "memberId": "member_01",
          "playerName": "封不覺",
          "aliases": ["封不觉"],
          "professionId": "longyin",
          "secondaryProfessionId": null,
          "memberRole": "MEMBER"
        }
      ],
      "nextCursor": null
    }
  ]
}
```

totalCount 是当前筛选后总数，不是本页 rows.length；主/副职业资格查询不得在主职业人数汇总中重复计算。帮会替补仍是正式成员的一个岗位标记，TEMPORARY 是另一种活动参与来源。

## 4. 拟新增接口清单

基础前缀省略 /league/v1。登录接口不在此重建。

### 4.1 资料、组织与角色

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| GET /me | 已登录 | 玩家资料、组织范围、职业和真实 capabilities |
| PATCH /me | 本人 | 修改游戏角色/职业/别名，不改系统角色、账号绑定或组织权限 |
| GET /professions | 已登录 | 统一职业 ID/顺序/色块配置 |
| GET /me/organizations | 已登录 | 当前账号合法组织列表，不暴露全站私有成员 |
| GET /organizations/{orgId}/members | 组织查看能力 | 职业树、搜索和分页 |
| PATCH /organizations/{orgId}/roles/{userId} | 本组织管理员 | 设置/取消助理和授权能力，不修改 SysRole 成为系统管理员 |

入会申请先复用现有流程并由服务端映射 legacy owner。俱乐部、创建码、邀请码期限、帮会人数上限属于另一 Demo 的功能，正式 CRUD 另行确认，不按昵称识别“特殊创建者”。

### 4.2 模板与 JSON

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| GET /organizations/{orgId}/templates | 组织查看 | 列表 |
| POST /organizations/{orgId}/templates | 模板编辑能力 | 创建无人员模板 |
| GET /templates/{templateId} | 所属组织 | 读取完整结构 |
| PATCH /templates/{templateId} | 模板编辑能力 | expectedVersion 更新结构/名字 |
| POST /templates/{templateId}/copy | 模板编辑能力 | 新 ID 复制 |
| DELETE /templates/{templateId} | 管理能力 | 不影响已复制到活动的结构；保留审计 |
| POST /organizations/{orgId}/template-import/previews | 模板编辑能力 | 校验结构 JSON，返回 previewId/hash/影响 |
| POST /template-import/previews/{previewId}/confirm | 模板编辑能力 | 服务端保存已校验快照，校验 owner/时效/版本 |
| POST /activities/{id}/roster-import/previews | 活动预排能力 | 旧团队名单 JSON → 同帮会成员映射和冲突报告 |
| POST /roster-import/previews/{previewId}/confirm | 活动预排能力 | DRAFT/READY、expectedVersion、显式处理未匹配项后原子应用 |

**模板格式草案**（例子只有一个队，正式支持多个团/队；每个队生成 6 个席位）：

```json
{
  "schemaVersion": 1,
  "name": "联赛结构模板",
  "groups": [
    {
      "key": "attack1",
      "name": "进攻一团",
      "orderNum": 1,
      "squads": [
        {
          "key": "squad1",
          "name": "一队",
          "orderNum": 1,
          "seats": [
            {"slotNo": 1, "professionId": "tieyi"},
            {"slotNo": 2, "professionId": "suwen"},
            {"slotNo": 3, "professionId": null},
            {"slotNo": 4, "professionId": null},
            {"slotNo": 5, "professionId": null},
            {"slotNo": 6, "professionId": null}
          ]
        }
      ]
    }
  ]
}
```

**兼容原团队名单格式**：version=1，groups[].name、teams[].name、players[].name/aliases；仅解析和映射，不把它当成无人员模板，不信任其中玩家权限。

```json
{
  "version": 1,
  "groups": [
    {
      "name": "进攻一团",
      "teams": [
        {
          "name": "一队",
          "players": [
            {"name": "隐曜", "aliases": []},
            {"name": "封不覺", "aliases": ["封不觉"]}
          ]
        }
      ]
    }
  ]
}
```

队伍超过 6 人、跨队重复玩家、别名冲突、团名/同团队名重复和损坏 JSON 都阻止确认。团队缺数据和 CSV 独有不同于 JSON 名单权限校验，不能混为一类“未匹配”。

### 4.3 活动、排表与快照

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| GET /activities?scope=org/mine/history | 可见范围 | 活动列表；草稿只有管理角色 |
| GET /public-activities?professionId&signupAvailable | 已登录；匿名待定 | 跨帮会公开活动；只筛真正可报名空位 |
| GET /public-activities/stats?professionId | 同上 | publicCount、openCount、matchingActivityCount |
| POST /organizations/{orgId}/activities | 活动创建能力 | 从模板/空结构生成独立草稿；不直接公开 |
| GET /activities/{id} | 活动可见性 | 按角色投影基础信息，不泄漏编辑稿 |
| PATCH /activities/{id} | 活动管理能力 | 时间/说明等元数据；状态改变走命令 |
| GET /activities/{id}/lineup?scope=EDIT/PUBLIC | scope 对应权限 | 指定阵容版本及席位 |
| GET /activities/{id}/candidates?source&groupBy=profession | 预排能力 | 本帮会有效成员/本场临时替补，排除已占位 |
| POST /activities/{id}/lineup/commands | 预排能力 | 强类型命令统一增删/改名/排序/分配/交换/职业 |
| POST /activities/{id}/temporary-participants | 预排能力 | 仅本活动创建临时替补 |
| DELETE /activities/{id}/temporary-participants/{participantId} | 预排能力 | 检查当前占位，预览确认；历史快照不删除 |
| GET /activities/{id}/snapshots | 活动管理/查询能力 | 同活动历史快照 |
| POST /activities/{id}/snapshots | 快照保存能力 | source=EDIT/PUBLIC，新增不可变版本 |
| GET /activities/{id}/snapshots/{snapshotId} | 活动查询能力 | 完整历史投影，私有资料脱敏 |
| PATCH /activities/{id}/snapshots/{snapshotId}/metadata | 管理能力 | 仅名称/备注，不改 payload |
| POST /activities/{id}/snapshots/{snapshotId}/restore | 预排能力 | 恢复为新的编辑版本，不覆盖公开报名 |
| POST /activities/{id}/publish | 默认本组织管理员 | 指定同活动 snapshotId，创建 release 和公开 live 副本 |
| POST /activities/{id}/state-transitions | 对应管理能力 | close/start/finish/archive，校验合法前置状态 |
| POST /activities/{id}/final-snapshot | 默认管理员 | 截止后包含真实报名结果，新增并设为最终参战快照 |
| POST /activities/{id}/snapshots/{snapshotId}/save-as-template | 模板编辑能力 | 只取结构/职业，剔除人员和临时替补 |

lineup commandType 白名单：ADD_GROUP、RENAME_GROUP、REMOVE_GROUP、ADD_SQUAD、RENAME_SQUAD、REMOVE_SQUAD、SET_ORDER、SET_REQUIREMENT、ASSIGN_MEMBER、MOVE_MEMBER、SWAP_SEATS、CLEAR_SEAT、DISABLE_SEAT。每种单独 VO/Pydantic 校验，禁止通用“任意对象属性更新”。

预排示例（不能传 canManage 或 ownerUserId 获取权限）：

```json
{
  "commandType": "ASSIGN_MEMBER",
  "expectedVersion": 12,
  "seatKey": "seat_01",
  "memberId": "member_01",
  "actualProfessionId": "longyin",
  "confirmProfessionConflict": false
}
```

若职位要求铁衣却安排龙吟，返回职业冲突细节；只有有权角色再次显式确认且写 reason 才可走预排例外。公开本人报名不接收该确认字段。

发布示例：

```json
{
  "snapshotId": "snapshot_003",
  "expectedActivityVersion": 5,
  "signupDeadline": "2026-09-19T19:50:00+08:00",
  "publicRemark": "请按职业选择剩余空位",
  "notifyOptedInUsers": true
}
```

客户端传 true 只表示希望生成通知事件，不表示能无视用户 opt-in 或通道能力；最终选择由服务端完成。

### 4.4 抢位、取消与缺口

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| GET /activities/{id}/vacancies?professionId | 公开范围 | requiredCountByProfession、unrestrictedCount、可报名空位 |
| POST /activities/{id}/seats/{seatKey}/signup | 真实登录本人 | OPEN/release/职业/空位/重复校验并事务占位 |
| POST /activities/{id}/seats/{seatKey}/cancel-signup | 该席位本人 | 检查取消窗口/来源/版本；预排锁定位默认不能自行释放，待确认 |

signup 请求：

```json
{
  "releaseId": "release_001",
  "expectedSeatVersion": 7,
  "actualProfessionId": "suwen"
}
```

userId/名字不从请求作为本人身份取值；使用 token 对应玩家资料。主副职业都符合时必须提交本场使用职业（暂拟）。普通用户不能通过传 PRESET/PROXY 绕过职业限制。

缺口“缺素问”仅统计明确指定素问的空位；不限位单独显示，查询“我能报名”可以包含不限位，避免重复计数。

### 4.5 CSV、绑定和分析

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| POST /csv-imports | CSV 上传能力 | multipart 原 CSV；可带 activityId 建预览，未绑定进入待处理 |
| GET /csv-imports?status=UNBOUND&orgId | 当前组织处理能力 | 待处理区，不泄漏其他组织文件 |
| GET /csv-imports/{importId} | 上传组织范围 | 原文件元信息、解析状态、帮会与校验报告 |
| GET /csv-imports/{importId}/activity-candidates | 当前组织处理能力 | 同范围近期候选活动；不自动绑定 |
| POST /csv-imports/{importId}/matching-previews | 正式分析能力 | 指定 ENDED 活动及最终快照，服务端计算匹配和 previewToken |
| POST /csv-imports/{importId}/confirm | 正式分析能力 | 重校验预览上下文后绑定，生成新 run 和既有 battle records |
| GET /analysis-runs?activityId | 活动分析查看能力 | 历次导入/重新绑定，不能只存“最新覆盖版” |
| GET /analysis-runs/{runId}/overview | 同上 | 活动、最终快照、CSV、匹配报告、总览 |
| GET /analysis-runs/{runId}/metrics | 同上 | 稳定 metricId、label、类型和汇总规则 |
| GET /analysis-runs/{runId}/players?groupBy=profession&metricId&direction | 同上 | CSV 目标帮会全部玩家，含未编队玩家 |
| GET /analysis-runs/{runId}/players/{dataPlayerId} | 同上 | 玩家全部指标和当时编队/匹配状态 |
| GET /analysis-runs/{runId}/groups | 同上 | 最终快照团统计 |
| GET /analysis-runs/{runId}/squads?groupId | 同上 | 队伍、有效人数/无数据人数、职业成员树 |

确认请求：

```json
{
  "activityId": "activity_001",
  "finalSnapshotId": "snapshot_final_001",
  "campKey": "camp_0",
  "previewToken": "opaque_preview_token",
  "acknowledgedWarningKeys": ["DECLARED_COUNT_MISMATCH"]
}
```

previewToken 绑定上传内容 hash、目标组织/活动、快照 hash、campKey、规则版本和有效期。确认不能提交客户端自算的 matches/totals；快照变化或文件失效返回 IMPORT_CONTEXT_CHANGED 并重新预览。

零匹配只有显式确认 ZERO_MATCH 警告后可进入无有效编队数据的结果；不能报告 60/60 成功。重复/缺字段/非法数值等错误不提供强制忽略开关。

**固定 CSV 表头与指标映射**

| CSV 表头 | 稳定小程序 metricId | 原 battle_record 字段 | 类型 |
| --- | --- | --- | --- |
| 玩家名字 | 非统计键 | player_name | 原始文本/匹配标识 |
| 职业 | 非统计键 | player_class | 名称→professionId；未知保留 |
| 击败/清泉 | kills_spring | kills + qingquan_kills | 双数值，分别相加 |
| 助攻 | assists | assists | 数值 |
| 资源 | resource | resources | 数值 |
| 对玩家伤害 | player_damage | dmg_to_players | 大整数 |
| 人伤卸甲 | player_armor_break | armor_break_players | 大整数 |
| 对建筑伤害 | structure_damage | dmg_to_buildings | 大整数 |
| 破塔卸甲 | tower_armor_break | armor_break_buildings | 大整数 |
| 治疗值 | healing | healing | 大整数 |
| 承受伤害 | damage_taken | dmg_taken | 大整数 |
| 重伤 | deaths | deaths | 数值 |
| 复活/清泉 | revive_spring | revives | 当前 Demo 解析为单数值；不擅自拆到 qingquan_kills |
| 焚骨 | burn_bone | burn_bones | 数值 |

当前 Demo 有 12 个统计 metricId；不要把英文资源键误写 resources 或把焚骨键误写 burn_bones 后直接给小程序。适配层映射两端。

建议新 DTO 将统计整数按十进制字符串序列化（双值为 a/b 两个字符串），由服务端精确汇总和排序，避免 BigInteger 超过 JavaScript 安全整数造成损失。手机不必依赖 BigInt 支持；需要更新指标类型/格式化适配，旧接口仍保持原类型。

字段名含“/”不必然为双值。若正式 CSV 的复活字段出现双值，先升级 parser/schema 并明确含义，不能丢失第二个数字。空数值是否沿 Demo 记 0 暂拟保留并警告；负数、小数、超界值的严格政策需用真实样本确认。

### 4.6 分析盒子

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| GET /analysis-runs/{runId}/boxes | 分析查看能力 | 盒子列表/人数/选项 |
| POST /analysis-runs/{runId}/boxes | 分析编辑能力 | 创建；默认“全部队员”按有效数据统计 |
| PATCH /analysis-runs/{runId}/boxes/{boxId} | 编辑能力且 owner 策略 | 改名/选队/玩家覆盖/指标；expectedVersion |
| POST /analysis-runs/{runId}/boxes/{boxId}/copy | 同上 | 同 run 新 ID 复制 |
| DELETE /analysis-runs/{runId}/boxes/{boxId} | 同上 | 删除盒子，不删除比赛/阵容 |
| GET /analysis-runs/{runId}/boxes/{boxId}/stats?view=players/squads | 分析查看能力 | 按去重有效集合计算 |

```json
{
  "expectedVersion": 3,
  "name": "治疗与临时替补",
  "selectedGroupIds": [],
  "selectedSquadIds": ["squad_01", "squad_02"],
  "manualAddIds": ["data_player_csv_only"],
  "manualRemoveIds": ["data_player_02"],
  "metricIds": ["healing", "damage_taken"]
}
```

manualAddIds/manualRemoveIds 都是本 run 的数据玩家 ID，不能传另一个 run 的 ID。选小队先带出队员，用户仍可逐人增减；UI 点击名称改名，独立区域展开/收起，删除位于旁边，折叠状态不修改服务器统计。

### 4.7 微信身份、偏好与机器人

| 方法/路径 | 权限 | 行为 |
| --- | --- | --- |
| POST /me/binding-challenges | 已登录本人 | 短期一次性绑定码；provider 明确区分 miniapp 和 bot |
| GET /me/identities | 已登录本人 | 脱敏身份状态，不回传 channel 凭证/session key |
| DELETE /me/identities/{identityId} | 本人 + 重新确认策略 | 撤销绑定，停通知/私有查询 |
| GET /me/notification-preferences | 本人 | 公开活动/职业补人和通道偏好 |
| PUT /me/notification-preferences | 本人 | opt-in、静默设置；职业来自合法本人资料 |

内部 /internal/bot/v1/events 是**标准化网关契约**，不是假定 iLink 自带 webhook：

- 实际通道可能轮询或回调，由适配器归一化。
- 校验通道/网关服务身份后才相信 provider、subject、messageId、fileRef。
- provider 消息重复按 channel+messageId 去重。
- resolveIdentity 得到实际绑定用户；所有业务查询重新授权。
- 通道禁用、不支持主动消息/小程序入口时显式返回能力状态。

首批工具白名单：list_public_activities、query_profession_vacancies、query_my_eligible_activities、query_my_guild_profession_counts。CSV 提交和活动创建属于后续带确认的写工具，不暴露 SQL/任意 HTTP/任意文件路径工具。

## 5. 权限矩阵（暂拟）

| 能力 | 普通玩家 | 组织助理 | 组织管理员 |
| --- | --- | --- | --- |
| 查看公开活动/本人资料 | 是 | 是 | 是 |
| 公开合职业本人报名 | 是 | 是 | 是 |
| 查看本帮会成员 | 按组织策略 | 是 | 是 |
| 编辑预排/职业/临时替补 | 否 | 经本组织授权 | 是 |
| 保存编辑快照 | 否 | 经授权 | 是 |
| 发布/关闭/最终快照/正式分析 | 否 | 默认否，可明确授权 | 是 |
| 设置/取消助理 | 否 | 否 | 是 |
| 跨组织后台操作 | 否 | 否 | 不是帮会角色自动拥有，需系统权限与范围策略 |

按钮 capabilities 只反映权限，不执行权限；所有 API 在服务端再检验当前账号、组织、活动状态和对象父子归属。
