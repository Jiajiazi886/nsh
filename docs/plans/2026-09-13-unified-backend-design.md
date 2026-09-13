# 统一后端改造设计（暂拟）

日期：2026-09-13。业务阶段：第三步“规划怎么做”和第四步“设计系统结构”。
代码基线：`xiaochengxu@86cedd14da360f82724b410451f2158954cd9a5a`。
本文件描述拟改造内容，不代表接口或数据库已经开发完成。

## 1. 为什么改

目标不是再做一套独立小程序后端，而是让一个账号、一个帮会、一场活动在网页、小程序、机器人三个入口保持一致：

1. 网页负责完整管理和鼠标拖拽排表。
2. 小程序负责移动查看、点击排表和公开抢凳子。
3. 机器人负责查询公开活动、职业补人、通知和辅助处理文件。
4. 同一场活动的最终阵容和 CSV 形成唯一分析依据，不能各端自行保存一套正式阵容。

核心闭环：

```text
若依系统账号 → 玩家职业/别名 → 帮会成员
                                   ↓
可复用模板 → 活动独立阵容 → 管理员/助理预排
                                   ↓
                            保存不可变快照（可多次）
                                   ↓
管理员发布快照 → 公开版本 + 实时占位 → 合职业玩家抢位
                                   ↓
                           报名截止 → 最终参战快照
                                   ↓
CSV 上传/待处理 → 匹配预览 → 确认绑定 → 总览/玩家/队伍/分析盒子
                                   ↓
                            活动和分析历史归档
```

## 2. 依据与证据边界

### 2.1 参考对象

| 参考 | 角色 |
| --- | --- |
| 原项目 `ruoyi-fastapi-backend` | 正式后端已有实现 |
| 原项目 `ruoyi-fastapi-frontend` | 已有网页接口和页面 |
| `E:/nsh/nshls/xiaocghengxu-dewmo` | 最新小程序纯前端效果与交互参考 |
| 原项目 `逆水寒联赛综合管理系统功能与使用说明.md` | 产品 V2 规划；含已确认/待确认事项 |
| 原项目 `后端机器人文档.md` | 机器人暂定查询、通知、CSV 和知识库需求 |
| `D:/wechattttt/nishuihanliansai/项目分析与说明文档.md` | 另一套 Demo 的功能参考；不迁入其 Node 后端和独立账号体系 |

原项目后两份文档和 HTML demo 当前为未跟踪文件，本副本没有将它们加入 Git。对另一项目的运行状况只采用其文档描述，不声称本轮已联调验证。

### 2.2 源码定位

以下路径相对本副本根目录，均在基线中存在。只进行了静态读取，没有导入后端应用或连接数据库。

| 编号 | 已检查文件 | 观察到的实现 |
| --- | --- | --- |
| SRC-01 | `ruoyi-fastapi-backend/module_admin/controller/login_controller.py` | `/login`、`/getInfo`、`/getRouters`、`/register`、`/logout` |
| SRC-02 | `ruoyi-fastapi-backend/module_admin/controller/captcha_controller.py` | `/captchaImage` 返回验证码开关、图像和 uuid |
| SRC-03 | `ruoyi-fastapi-backend/module_admin/service/login_service.py` | `authenticate_user`、`get_current_user`，JWT + Redis 会话 |
| SRC-04 | `ruoyi-fastapi-backend/config/env.py` | `app_same_time_login` 默认 True；实际运行值仍需检查环境 |
| SRC-05 | `ruoyi-fastapi-backend/common/aspect/pre_auth.py` | `PreAuthDependency`、`CurrentUserDependency` |
| SRC-06 | `ruoyi-fastapi-backend/common/aspect/interface_auth.py` | 菜单/接口权限检查，不替代业务对象归属校验 |
| SRC-07 | `ruoyi-fastapi-backend/module_guild/entity/do/member_do.py` | 成员有 `user_id`、`guild_id`、`member_user_id`、主/副职业 |
| SRC-08 | `ruoyi-fastapi-backend/module_guild/service/member_service.py` | 多个管理查询用当前用户 ID 作为成员归属；帮会名关联 SysUser 昵称 |
| SRC-09 | `ruoyi-fastapi-backend/module_guild/dao/member_dao.py` | 活跃成员查询和 `member_user_id` 绑定；部分查询会尝试补 schema |
| SRC-10 | `ruoyi-fastapi-backend/module_guild/dao/join_application_dao.py` | 按 SysRole `common` 用户查找帮会，帮会 ID 使用用户 ID |
| SRC-11 | `ruoyi-fastapi-backend/module_guild/entity/do/schedule_do.py` | 当前排表、团、小队、分配、Univer workbook |
| SRC-12 | `ruoyi-fastapi-backend/module_guild/service/schedule_service.py` | 单用户当前排表、六人分配、历史复制与恢复；尚无独立席位职业实体 |
| SRC-13 | `ruoyi-fastapi-backend/module_guild/entity/do/battle_registration_do.py` | 邀请链接、待审核报名/请假，区别于直接抢位 |
| SRC-14 | `ruoyi-fastapi-backend/module_guild/service/battle_registration_service.py` | 公开报名存 `applicant_user_id=0`；已存在登录账号入会复用流程 |
| SRC-15 | `ruoyi-fastapi-backend/module_guild/controller/battle_controller.py` | 现有导入接收 BattleImportModel JSON，不是统一 CSV 文件解析入口 |
| SRC-16 | `ruoyi-fastapi-backend/module_guild/service/battle_service.py` | 保存解析后的 records；部分写入 `guild_id/initiator_guild_id=1` |
| SRC-17 | `ruoyi-fastapi-backend/module_guild/entity/do/battle_do.py` | 现有比赛主表及稳定英文字段的玩家指标明细 |
| SRC-18 | `ruoyi-fastapi-backend/module_guild/service/analysis_service.py` | 选历史排表和比赛分析，按 my_guild_name 过滤和规范化名字匹配 |
| SRC-19 | `ruoyi-fastapi-backend/module_guild/controller/analysis_controller.py` | `GET /guild/analysis/schedule-battle` |
| SRC-20 | `ruoyi-fastapi-backend/common/router.py` | 自动扫描 `*/controller/[!_]*.py`，可发现新增模块 |
| SRC-21 | `ruoyi-fastapi-backend/middlewares/transport_crypto_middleware.py` | 业务加密信封与 required/路径规则，移动端必须明确兼容策略 |
| SRC-22 | `ruoyi-fastapi-backend/utils/response_util.py` | code/msg/data；登录 token 在顶层；不能假设所有响应都套 data |
| SRC-23 | `ruoyi-fastapi-frontend/src/api/login.js` | form-urlencoded 登录，后续使用已有 request 封装 |
| SRC-24 | `ruoyi-fastapi-frontend/src/views/guild/schedule/index.vue` | 主编辑区域仍使用 ScheduleUniverSheet 和 workbook 同步 |
| SRC-25 | `ruoyi-fastapi-frontend/src/api/guild/schedule.js` | /current、/history、/assignment、/snapshot、workbook 接口 |
| SRC-26 | `ruoyi-fastapi-frontend/src/api/guild/analysis.js` | 网页调用既有排表-比赛分析接口 |
| SRC-27 | `ruoyi-fastapi-backend/module_guild/constants/class_color_defaults.json` | 既有可配置职业色，与小程序默认颜色/职业集合不完全一致 |

小程序额外检查：`miniprogram/utils/demo-store.js`、`store.ts`、`analytics-store.js`、`importer.js`、`box-selection.js`、`profession-tree.js`、`pages/lineup/lineup.ts`、`app.json`（15 个正式页面）。

### 2.3 已发现的改造阻点

- **归属不统一**：不能把当前助理 userId 当成帮会管理员 ownerUserId；增加组织范围服务，拒绝依赖客户端传来的 owner ID。
- **排表不对应单场活动**：旧当前排表以用户维度维护，不具备活动/发布/最终版本三层关系。
- **报名不是抢位**：现有公开报名是成员申请/审核流，不能直接改成占某个凳子而破坏旧网页。
- **明细查询需要复查对象权限**：battle_controller 的 records 路由虽读取 current_user，却只把 battleId 传给 query_records_service；该服务也未接收操作者。新接口上线前必须补对象范围测试和校验。此处是静态风险定位，不是已执行的攻击验证。
- **历史分析缺少绑定记录**：现有分析可临时选择任意有权限的排表，没有强制活动最终快照。
- **客户端状态分裂**：Demo 有活动 `nsh_integrated_frontend_demo_v2`、阵容 `zhou-nuan-mini-demo-v1`、分析 `jiusi_mp_state_v3` 三份状态；排表 publish 只是 publicizeActivity，未传递排表完整内容。
- **名称/职业不能作为权限或主键**：Demo 的 canManage、名字登录、昵称代理人只能演示，不能进入正式身份逻辑。
- **启动/查询可能写库**：已有 schema 补齐和初始化机制，隔离副本仍不能指向原数据库进行“只读联调”。

## 3. 方案取舍

| 方案 | 好处 | 问题 | 结论 |
| --- | --- | --- | --- |
| A：在现有 FastAPI 中扩展独立活动模块，保留旧 API | 最大程度复用账号、成员、记录；可渐进迁移 | 需要清楚区分新旧对象 | 推荐 |
| B：强行把旧 schedule/invite/battle 表全部改成活动模型 | 表少、入口看似统一 | 单用户排表语义、审核报名和抢位混在一起，旧网页容易破坏 | 不推荐 |
| C：迁入另一项目 Express 后端，三端各做数据同步 | Demo 转移快 | 两套账号、权限和同步逻辑，违背统一系统目标 | 不采用 |

暂拟选 A；仍是一个 FastAPI 应用，不增加独立微服务、另一套密码表或第二个运行数据库。

## 4. 系统结构

```text
现有 Vue 网页      原生微信小程序      微信机器人/iLink（暂定）
    │                  │                    │
    └──── REST ────────┴── REST ──┐       通道适配器
                                 │          │
                    API / 查询组合层      命令/MCP 白名单
                                 └────┬─────┘
                           同一应用业务服务
          ┌───────────────────────────┼──────────────────────┐
      账号/组织权限          模板→活动→阵容→报名        CSV→匹配→分析
          │                          │                       │
          └──────────── 数据库事务 + 操作日志 ────────────────┘
                                    │
                             通知 Outbox → worker
                                    │
                           可替换通道能力/重试/去重
```

Controller 负责请求/响应和身份提取，Service 负责全部业务规则，DAO 负责带组织范围的访问。网页拖拽、小程序点击和机器人命令不能各自实现不同抢位算法。

### 4.1 拟新增/调整的代码位置

下面是未来文件清单，本次没有创建这些运行文件：

| 模块 | 拟位置 | 工作 |
| --- | --- | --- |
| 组织范围 | `module_guild/service/org_scope_service.py`、组织 DO/DAO/VO | owner 兼容映射、组织成员身份、管理员/助理能力 |
| 玩家资料 | `module_identity/controller/profile_controller.py`、service/dao/entity | 不在帮会也能维护角色、职业、别名；仍绑定 SysUser |
| 微信身份 | `module_identity/controller/binding_controller.py`、service | 一次性绑定、解绑、撤销，不保存系统密码 |
| 阵容模板 | `module_activity/controller/template_controller.py`、service/dao/entity | 团→小队→席位结构及 JSON 预览 |
| 活动与排表 | `module_activity/controller/activity_controller.py`、`lineup_controller.py` | 独立活动、排序、职业、预排、临时替补 |
| 快照 | `module_activity/controller/snapshot_controller.py`、service | 保存、恢复、发布、最终版本 |
| 报名 | `module_activity/controller/signup_controller.py`、service | 本人抢位、取消、并发与幂等 |
| CSV/分析扩展 | `module_guild/service/csv_import_service.py`、`activity_analysis_service.py` | 服务端重校验、最终快照绑定、旧指标适配 |
| 分析盒子 | `module_guild/controller/analysis_box_controller.py`、service/dao/entity | 以分析 run 为范围保存自由组合规则 |
| 移动查询聚合 | `module_activity/controller/mini_bootstrap_controller.py` | 适合手机的读取 DTO，不另存业务状态 |
| 机器人 | `module_bot/controller`、`service`、`transports` | 暂定 iLink 适配器、假通道、工具白名单 |
| 通知 | `module_bot/service/notification_service.py`、outbox DAO | 用户通知偏好、职业筛选、去重、退避 |
| 旧入口兼容 | SRC-08/12/15/18 对应 Service/Controller | 渐进调用新范围服务；旧 response 和 workbook 先保留 |

## 5. 账号、身份和数据权限

### 5.1 共用账号密码

- 唯一系统账号来源：现有 SysUser、UserService、LoginService。
- 小程序第一版调用现有 `POST /login`，沿用 form-urlencoded、验证码和失败限流；读取现有 getInfo。
- 同一账号可在 PC 和小程序各持有独立 sessionId，使用已有并行会话机制。默认配置不能证明运行环境：验收必须测试 PC 登录后小程序登录、单端退出不误踢另一端。
- 客户端类型用于审计，不是管理员身份依据，不让用户通过传 loginInfo/canManage 获权。
- 是否提供 token 刷新单独评估；不凭空假设已有 refresh_token。
- 若业务加密 required 模式影响小程序，需开发经过测试的兼容封装或经确认的严格限定路径策略，不能全局关闭安全策略解决联调。
- 微信一键登录只是预留：provider adapter、绑定账号、能力配置。未取得真实身份代码交换验证前返回“未启用”，不得生成假 openid。

### 5.2 区分五类身份

| 身份 | 唯一标识/用途 |
| --- | --- |
| 系统账号 | SysUser.user_id，登录和审计 |
| 游戏角色 | 新玩家资料 ID，名称/别名/主副职业 |
| 正式成员 | GuildMember.member_id，属于一个真实帮会范围 |
| 活动参与者 | participantId，只在指定活动中表示一名参战人员 |
| 微信身份 | provider + app/channel + subject，不假设机器人标识等于小程序 openid |

同一绑定正式成员与账号报名需要解析为同一活动 identityKey，不能通过两种来源占两位。尚未绑定账号的正式成员仍可由管理员预排。

### 5.3 组织范围迁移

拟新增组织实体，不再用系统昵称保存唯一帮会名。先保存 legacyOwnerUserId 到 orgId 映射，不直接重新解释旧表 guild_id。

1. 读取旧成员、当前排表、邀请和比赛归属，生成映射预览。
2. 人工确认真正的帮会 owner；异常、零 ID、硬编码 1 的比赛不可自动归到所有人。
3. 分批建立组织、管理员角色和账号-成员关系。
4. 旧表先保留字段；旧 API 使用兼容 owner，新的 Service 使用 orgScope。
5. 普通成员只访问自己可见组织，助理只访问被授权组织；切换活动 ID 必须重新校验范围。

系统管理员身份与“本帮会管理员/助理”不是同一角色。管理员是否跨组织查看业务资料应是显式策略并写审计，不能把一个帮会助理升级成全站角色。

## 6. 团队、席位和活动阵容

### 6.1 结构不变量

```text
组织
 ├─ 可复用结构模板（没有本场人员）
 └─ 一场活动
     ├─ 当前编辑阵容
     │   └─ 团队盒子 → 小队 → 1..6 凳子 → 活动参与者
     ├─ 当前发布快照 + 公开实时占位
     ├─ 多个不可变历史快照
     ├─ 最终参战快照
     └─ 多份 CSV 导入 → 不可变分析 run → 分析盒子
```

- 团队只能含小队，不能直接挂玩家。
- 每队默认生成 6 个席位；最多 6 个占位，slotNo 在 1..6 内且唯一。少于 6 个开放位置可通过禁用席位表示，是否支持可变席位数待确认。
- 团、小队、席位有稳定 ID/key 和独立 orderNum；拖拽只改变顺序/分配，不用展示名称或全局座位号做主键。
- 席位职业暂用“单一职业 ID 或 null（不限）”；多职业任选保持为待确认项。
- 排列位置保存结构化行列/排序，不保存 PC 像素、WXML 样式、树节点是否折叠。
- 已占位的团/队删除必须预览影响、显式确认，并事务释放占位；归档和最终快照不受删除影响。

### 6.2 两种 JSON 不能混用

1. **阵容模板 JSON**：团→小队→席位职业/顺序，不带 players，复制到活动后相互独立。
2. **现有团队名单 JSON**：保留 `version/groups/teams/players/name/aliases` 格式，作为名单导入/历史分析参考入口。

正式活动导入名单时，要先映射本帮会成员或当前活动临时替补，预览未匹配项。不能因为 JSON 写了外帮名字就自动创建永久成员、自动绑定账号或直接放入未公开阵容。

团名、同团队名、玩家名不能为空；规范化后的重复玩家/别名冲突拒绝导入并定位 JSON 路径。正式结构必须校验六人上限，不能照搬 Demo 未限制每队人数的解析器。

Demo 团队 JSON 导入会清空旧分析盒子并建“全部队员”；正式版仅在独立分析配置导入且明确确认重置盒子时提供此行为，绝不通过该操作覆盖活动快照或历史分析。

### 6.3 发布前安排

管理员/助理只能选择本帮会有效成员或**当前活动**临时替补。普通用户看不到草稿也不能报名。

职业不符先返回冲突预览；预排强制安排暂拟需要管理员/授权助理、显式确认和理由，并写审计。普通公开报名不能使用此例外。

### 6.4 临时替补

以活动参与者 sourceType=TEMPORARY 表示，activityId 必填：

- 名称、职业、别名、原帮会/备注只属于这场活动。
- 不写 GuildMember，不计入帮会人数/长期职业统计。
- 不出现在其他活动候选区或长期外援库。
- 保存进当前活动快照，可参与最终 CSV 匹配和分析盒子。
- 活动归档后历史保留，但不能复制到另一活动；“另存模板”也会剔除临时替补和所有人员。

## 7. 快照、发布和公开报名

### 7.1 三种版本必须独立

| 数据 | 能否改变 | 用途 |
| --- | --- | --- |
| 当前编辑阵容 + revision | 可以，需 expectedVersion | 管理员/助理排表 |
| 历史快照 payload | 不可以；仅名称/备注可另行改 | 保存当时全部结构和人员 |
| 发布快照 | 不可以 | 公开结构与预排人员的基线 |
| 公开实时占位 | 只有合法报名/撤销等命令可改 | 展示最新空位，不改发布快照 |
| 最终参战快照 | 不可以 | 汇总发布后报名和关单后确认的参战人员，用于分析 |

发布某个快照后，创建公开阵容副本和 releaseId；**不能把冻结的发布快照当成一直变化的报名记录**。保存最终快照时必须包含后来抢位的玩家，而不是原样指向发布前快照。

快照冻结：活动信息、团/队/席位 ID 与位置、职业要求、正式成员/临时替补/公开报名人员、当时名称/别名/本场职业、保存人和时间。

同活动多次保存新增 versionNo；恢复历史内容只生成新的编辑版本，历史快照、公开占位和已生成分析都不被覆盖。

### 7.2 活动状态

暂拟：DRAFT → READY → OPEN → CLOSED → RUNNING → ENDED → ARCHIVED。

- “公开可见”和“允许报名”分开。已公开但已截止仍可展示，不再计为可报名活动。
- 活动开始、结束、signupDeadline 三个时间分开；不能沿用另一个 Demo 用 endTime 同时表示所有截止逻辑。
- 每次请求都检查服务端时间和状态，不能依赖定时任务刚好执行，也不能相信手机时间。
- READY 保存完整发布候选；OPEN 只在管理员发布成功后生效。
- CSV 可先进入待处理区；正式分析需 ENDED、finalSnapshotId 和确认绑定。

### 7.3 发布后调整的保守草案

这是待用户确认的默认方案，不是已定业务：第一版 OPEN 时禁止直接编辑公开结构/替换发布版本，避免把已报名玩家丢掉。

若要修改：先关闭报名，再基于当前公开占位保存快照、预览变更、通知受影响用户；是否允许重新开放/助理发布需后续决定。接口预留版本冲突和影响预览，暂不启用“自动覆盖重发布”。

### 7.4 公开报名与并发

“所有人可见”指公开活动不局限本帮会；匿名访客是否可查看未确认。暂拟登录用户跨帮会可查看公开摘要，报名始终需要真实系统账号。

本人报名校验：OPEN、isPublic、未超过 deadline、当前 releaseId、空位/未禁用、用户本场职业确属已验证主副职业、符合要求、同活动未重复占位。

数据库事务按统一顺序锁活动、参与者、目标席位；占位唯一约束与活动身份唯一约束是最终防线。并发两人抢一凳子最多一人成功，同一人抢两凳子也最多成功一次。Redis 可做限流/短缓存，不能代替数据库约束。

所有写命令带幂等键；相同键同请求返回原结果，不同请求内容复用同键拒绝。管理员移动/交换也检查来源与目标版本。

代理报名“每场最多 12 人”是另一个 Demo 行为，未确认为正式规则。第一版默认只开放本人报名和管理预排；若启用代理，需真实 actorUserId、活动内被代理身份、重复/职业/权限校验，不能让代报输入绕过本人规则。

## 8. 拟数据实体（未执行建表）

表名为草案，用于估算，不代表最终 SQL。新增表不覆盖旧表；live 结构用关系实体，模板/快照用版本化 JSON。

| 拟表/实体 | 关键字段与关系 |
| --- | --- |
| league_org | orgId、类型、名称、legacyOwnerUserId；俱乐部能力开关暂不启用 |
| league_org_role | orgId、userId、组织角色、能力配置；unique(orgId,userId) |
| league_player_profile | SysUser.userId → 游戏角色、区服、主副职业；不复用帮会管理员昵称 |
| league_player_alias | profileId、原名、normalizedKey；作用域冲突必须显式解决 |
| league_lineup_template | orgId、名称、version、结构 JSON；不含人员 |
| league_activity | orgId、状态/公开、三个时间、editLineupId/publicLineupId/finalSnapshotId、revision |
| league_lineup | activityId、EDIT/PUBLIC scope、releaseId、来源快照、revision |
| league_lineup_group | lineupId、groupId、名字、orderNum/结构位置；无玩家字段 |
| league_lineup_squad | groupId、squadId、名字、capacity<=6、orderNum |
| league_lineup_seat | lineupId/squadId、slotKey/slotNo、requiredProfession、disabled、participantId、本场职业、版本、操作者/来源 |
| league_activity_participant | activityId、identityKey、sourceType/sourceId、当时名称/别名；TEMPORARY 仅活动范围 |
| league_lineup_snapshot | activityId、versionNo、schemaVersion、不可变 payload/hash、名称备注、保存人/时间 |
| league_csv_import | orgId、可空 activityId、原文件受控位置/hash、parserVersion、状态、预览报告；每份上传新记录 |
| league_analysis_run | activityId、finalSnapshotId、csvImportId、campKey、matchPolicyVersion、matches/report、旧 battleId |
| league_analysis_box | runId、creatorUserId、名称、选队/手动增减规则、metricIds、version |
| sys_external_identity | userId、provider/app/channel/subject、绑定时间、撤销状态；不保存系统密码 |
| league_notification_preference | userId、职业补人/公开活动通知 opt-in、通道和静默配置 |
| league_notification_outbox | 业务事件、目标账号/通道、去重键、待发/成功/失败/重试、错误分类 |
| league_command_receipt | userId、命令/幂等键、payloadHash、结果；持久保证重试不重复变更 |
| league_operation_log | org/activity/run、actorUserId、行为、脱敏前后摘要、原因、requestId |

关键数据库约束：

- 同一阵容 slotKey 唯一；同队 slotNo 唯一且 1..6。
- 同一 live 阵容 participantId 只能占一位；同活动 identityKey 唯一。
- participant/activity、seat/lineup/squad 和 snapshot/activity 的父子关系一致；以复合外键或事务服务强校验保证不能跨活动引用。
- 每活动 snapshot versionNo 唯一，finalSnapshotId 必须指向该活动快照。
- 每个分析 run 的 CSV、快照和组织范围一致；原文件与 payload 不原地覆盖。
- 机器人身份唯一键包含 provider/app/channel，不能只用昵称。

## 9. CSV、匹配和联赛分析

### 9.1 两阶段导入

上传 → 严格服务端解析/预览 → 用户确认 → 事务保存比赛明细 + 分析绑定。

现有网页传 records JSON 可暂保留；新三端上传原 CSV，服务端是唯一权威解析器。客户端预览只能辅助，不能信任传来的 camp/统计/匹配数量。

上传草案大小上限 5 MiB（可配置，待确认）、限制后缀和实际内容、UTF-8/BOM、引用字段/换行；文件存受控目录，不接受客户端任意路径/URL。机器人文件下载仅使用经认证通道文件引用，需大小和来源校验，不允许任意 URL 下载。

未绑定文件保留 orgId/上传人/状态。机器人只推荐同范围近期活动，必须由管理员确认；不能凭“最近排表”静默绑定。

### 9.2 目标帮会匹配

基于最终快照冻结的名字和 aliases，去首尾空白、忽略空格、统一约定尾点；不做未经确认的模糊自动合并，简繁差异优先显式 aliases。

按“匹配唯一玩家数最高 → matchRate 最高 → 文件顺序”选择。为兼容 Demo，matchRate 定义为 matchedCount / finalRosterCount；同快照分母相同，第二条件实际上无法区分同匹配数的帮会，保留说明，不暗自改成另一公式。

重复玩家（同帮会）、一个名字/别名对应多个最终参与者、缺列、损坏引用字段和非法数字阻止确认。声明人数不符警告。零匹配仍按文件首项预选，必须显示 0 人警告并人工明确确认，不能当“成功的完整团队分析”。

报告含全部帮会/声明和实际人数、最终选择、快照人数、匹配数、CSV 独有、阵容缺数据、冲突位置和规范化规则版本。

### 9.3 稳定指标与分析盒子

沿用原 battle_record 英文字段，通过 DTO 映射到小程序稳定 metricId；完整映射见接口草案。名称和中文表头只做展示，不作为统计键。

团队有效分析玩家 = 最终阵容成员 ∩ 选定 CSV 帮会玩家；未匹配成员不填造假的 0 行混入平均分母。

CSV 独有玩家保留在本 run 玩家页，可手动加入分析盒子，但不因此成为正式帮会成员或改变最终阵容。

分析盒子有效集合：

```text
（选中团/小队的有效数据玩家 ∪ 手动加入玩家）－ 手动移除玩家
                               ↓
                        按稳定数据玩家 ID 去重
```

手动覆盖先作用于所有基选，manualRemove 优先。runId 隔离玩家/队伍引用；重新导入生成新 run，旧盒子与统计保留，迁移盒子需映射预览，不静默抹掉旧分析。

## 10. 职业分类与简单界面契约

- 复用 ProfessionService 和 ClassColorService，但统一 professionId/名称/orderNum/颜色的 DTO。
- 现有网页和 Demo 默认职业集合/配色不同，先比较并经管理员确认；不得本次直接覆盖原网页的职业配置。
- 每个职业返回可识别 color，未知职业进入“未分类”，不得因为预设顺序缺职业而隐藏玩家。
- UI 使用“职业 → 玩家”的折叠树，候选区还可分“正式成员/帮会替补/本场临时替补”。
- 同一页面统计“每名成员一条”按主职业/本场职业分类；副职业查询和可报名资格另算，不能人数重复累计。
- 页面折叠/排序偏好保留客户端；职业源和可见玩家由后端范围查询提供。
- 界面继续白/浅灰、深色文字、蓝色操作色，职业只作色块/标签识别。后端不返回整片主题样式。

## 11. 机器人、通知、MCP 和知识库

### 11.1 适配器而不是第二套业务

传输接口暂拟：verifyInbound、normalizeMessage、sendText、sendFileReference、sendActivityEntry、capabilities。

首个适配器为 fake/mock；iLink 默认关闭。通道参数与凭证只在服务端环境/密钥管理中配置，不提交真实凭证。

截至本轮，没有获得足以锁定所有能力的完整可核验官方 iLink 协议契约。主动私聊、消息可用上下文、文件收取、小程序卡片/码、群聊和发送频率都需要实际验证；不能承诺“可向每个微信用户无限主动发消息”。若通道不支持某种入口，返回已验证的文本活动码/链接替代方案，不造假小程序码。

### 11.2 绑定与权限

已登录系统用户生成短期一次性绑定挑战（默认 5 分钟草案、摘要存储、尝试限流）；用户在机器人发送挑战，服务端从已验证的入站消息提取微信 subject，再原子消费并绑定。

小程序微信身份与机器人身份分别验证，不假设二者 subject 可直接互换。一个 subject 重复绑定到另一个账号必须拒绝或走明确解绑/重新验证；解绑后立即停止私有查询和通知。

机器人不询问密码、不复用管理员 token、不允许消息附带 userId 冒充身份。

### 11.3 首批查询/通知

| 需求 | 服务层规则 |
| --- | --- |
| 公开活动数量 | 只统计公开且可查询活动；区分公开总数与当前可报名数 |
| 缺指定职业活动 | 根据实时公开空席位 + deadline，不查询编辑稿 |
| 我能报名什么 | 绑定用户真实主副职业，不限位另计；已被安排不再次推荐抢位 |
| 本帮职业人数 | 需本组织权限，排除活动临时人员 |
| 公开活动通知 | 发布事务写 outbox；按用户偏好、职业、通道能力选择接收者 |
| 房间补人信息 | 管理员/授权助理确认发布；密码仅向有权限的目标发送，公开摘要不泄漏 |
| CSV | 经认证文件引用、权限校验、进入待处理/推荐活动、人工确认 |

通知默认关闭且以用户 opt-in 为准；发布、补人、变位等事件使用目标/事件版本/通道去重键。事务内只写 outbox，提交后 worker 发送，失败不回滚已成功的报名或发布。退避、限频、死信和解绑后的再次权限检查需覆盖。

### 11.4 MCP/AI

工具面向应用服务，不向 AI 暴露数据库连接或任意 SQL。首批仅公开查询与本人/本帮权限允许的查询；写操作需绑定身份、明确意图、确认和审计，暂不开放全站管理工具。

系统知识库是帮助文档；用户资料和历史数据库必须按身份过滤后检索。文件、CSV、聊天内容中的指令始终是数据，不能提高调用权限。知识库向量检索也带 org/user 访问条件，不能先检索全库再靠 AI“自觉不泄漏”。

## 12. 既有网页和小程序怎么衔接

旧网页 API/表格先保留只读和兼容，不在本次副本修改 UI。

未来网页增加结构化模板和活动阵容页：左职业树候选，右团→小队→六席位。拖拽发送与小程序点击相同的分配命令，不把 workbook JSON 当正式阵容。

旧 workbook 仅作历史查看/导出；迁移时读取已持久化的团/小队/assignment，必要时人工处理纯表格单元格，预览后生成新模板/活动。新页稳定验收前不删除旧表或旧路由。

小程序逐页替换假 store：每次选择 activityId 加载同活动编辑/公开/最终/分析上下文；不要整份上传 Demo 本地 state，不迁入任意名字登录和静态 canManage。

具体页面-接口映射、请求结构、错误和任务顺序见另外两份草案。
