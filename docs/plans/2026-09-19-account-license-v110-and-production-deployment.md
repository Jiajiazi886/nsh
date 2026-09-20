# 账号授权卡密系统、超级管理员权限字符调整、桌面端 v1.1.0 与服务器部署任务文档

更新日期：2026-09-19
执行状态：本地代码与自动化验证完成；目标开发库 `nsh_activity_dev_20260914` 只读审计通过（61 张表、账号授权/审计/刷新令牌表及外键核验）；主项目 `xiaochengxu` 已推送并通过远端分支核验（远端提交 `023bbcf791b0a288bf9d9a7f27623cbfdfccad46`）；桌面端私有仓库 `Jiajiazi886/nsh-daluandou-desktop` 已创建并推送，`main` 提交为 `da3be1e093513c19671bf09a7fab66ba18a10bee`，`v1.1.0` 标签已发布。服务器联调部署待执行。普通助手完整回归 62 项、授权/发布契约测试 9 项、开发者工具无验证码与权限契约测试 7 项通过。公网只读检查（2026-09-20）发现正式域名返回旧 `vfadmin管理系统` Monaco 页面；`/docker-api/api/v1/auth/config`、`/docker-api/api/v1/captchaImage` 与计划中的健康入口均返回 404，不能视为新版部署成功。
> 安全说明：服务器地址、IP 和 SSH 用户可写入本任务文档；SSH 密码、私钥、数据库密码、JWT 密钥和 token 不得写入 Markdown、代码、Git 历史、命令行参数或日志。部署时通过交互式密码输入或临时安全凭据注入。此前在聊天中发送过的密码应视为已暴露，正式部署前必须轮换。
实施分支：xiaochengxu
文档用途：本文件是本任务唯一的实施、交接、部署与验收文档。新接手的开发者应先完整阅读，再按章节顺序执行。

---

## 1. 最终目标

本任务要把网页、FastAPI 后端、微信小程序、大乱斗助手和开发者卡密管理工具接入同一套 RuoYi 账号体系。

最终交付：

1. 一个可以在本地运行并部署到服务器的完整网页、后端、MySQL、Redis 和小程序 API 项目。
2. 网页“系统管理”中的账号授权式“卡密管理”。
3. 使用 RuoYi 账号登录的逆水寒大乱斗助手 v1.1.0。
4. 使用 RuoYi 超级管理员账号登录的开发者卡密管理工具 v1.1.0。
5. 本地数据库和上传文件向生产服务器的完整迁移。
6. 两个 GitHub 仓库、明确的版本标签和可重复构建流程。
7. 可验证的数据一致性、备份、回滚和验收流程。

本任务完成后，不再使用“输入卡密并绑定机器”的授权方式。天卡、周卡、月卡、永久卡表示管理员给某个 RuoYi 账号授予的使用期限。

### 1.1 开发者管理工具的验证码边界（硬性要求）

开发者卡密管理工具（`E:\nsh\jiaozi\逆水寒交子助手_v3.5\license_admin`）**不加入图片验证码**。这不是可选项，也不因后端默认配置、网页登录改动或后续重构而改变：

- 登录界面不得展示验证码图片、验证码输入框、刷新验证码按钮或验证码相关提示。
- 登录、刷新和重试请求不得请求 `/auth/captcha`，不得读取验证码图片或验证码缓存。
- 登录请求只允许提交 `userName`、`password` 和 `clientType=license-admin`；刷新请求只提交 `refreshToken` 和 `clientType=license-admin`。
- 开发者工具代码、配置、日志、缓存和打包产物不得保存或提交 `code`、`uuid`、验证码图片、验证码答案或验证码接口响应。
- 后端仅对 `clientType=license-admin` 跳过图片验证码校验，仍必须执行账号密码、账号状态、超级管理员角色 `cptbtptp`、授权管理权限、限流和审计校验。不能通过删除后端校验、伪造管理员身份或前端隐藏按钮绕过权限。
- 网页后台和普通微信小程序的既有验证码流程不受本条影响，除非另有经确认的需求；不能把开发者工具的免验证码规则扩散到其他客户端。

后续任何登录协议、SDK、桌面端或后端控制器改动，都必须保持上述边界；若需要改变，必须先更新本任务文档并重新执行本节的回归测试。

---

## 2. 安全边界

### 2.1 原毕业项目只读

原毕业项目：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-master
~~~

该目录只允许查看，禁止修改源码、新建或删除文件、执行迁移、构建、部署、Git 暂存、提交或推送。

所有网页、后端和小程序修改只在以下独立副本进行：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend
~~~

### 2.2 服务器凭据

| 项目 | 值 |
| --- | --- |
| 正式域名 | https://www.xn--kbrr2vyxjytebq4azkrrie.icu/ |
| 服务器 IP | 152.136.161.6 |
| SSH 用户 | root |
| 操作系统 | OpenCloudOS 9.6 |
| SSH 密码 | 不写入本文档；从安全渠道获取，并在部署前轮换 |

之前通过聊天传递过的 root 密码已经视为暴露。正式部署前必须生成 SSH 密钥、安装公钥、验证密钥登录、轮换 root 密码并关闭 root 密码远程登录。

绝不能上传到 GitHub：

- .env 和 prod.env。
- 数据库备份。
- 服务器密码。
- MySQL、Redis 和 JWT 密钥。
- 刷新令牌。
- 用户明文密码。
- 私钥。
- 旧 CloudBase 摘要盐。
- 日志、本地缓存和运行数据。

真实数据库只能通过 SSH 或 SCP 加密通道直接传输到服务器，不能经过 GitHub。

---

## 3. 项目目录和地址

### 3.1 网页、后端与小程序

项目根目录：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend
~~~

后端：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend\ruoyi-fastapi-backend
~~~

网页前端：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend\ruoyi-fastapi-frontend
~~~

主小程序：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend\xiaochengxu
~~~

联赛分析小程序 demo：

~~~text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend\xiaochengxu\hhhhhhtml\jiusi-data-dashboard-frontend\demo
~~~

本地访问：

| 服务 | 地址 |
| --- | --- |
| 网页 | http://127.0.0.1:5173/ |
| 登录页 | http://127.0.0.1:5173/login |
| API | http://127.0.0.1:9101/api/v1 |
| API 文档 | http://127.0.0.1:9101/docs |

正式访问：

| 服务 | 地址 |
| --- | --- |
| 网页 | https://www.xn--kbrr2vyxjytebq4azkrrie.icu/ |
| API 根地址 | https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api/api/v1 |

### 3.2 大乱斗助手

源码：

~~~text
E:\nsh\jiaozi\新的大乱斗
E:\nsh\jiaozi\新的大乱斗\app_v2
~~~

授权入口：

~~~text
E:\nsh\jiaozi\新的大乱斗\app_v2\license_gate.py
~~~

构建脚本：

~~~text
E:\nsh\jiaozi\新的大乱斗\build_airtest_final.py
~~~

v1.1.0 输出目录：

~~~text
E:\nsh\jiaozi\新的大乱斗\dist\逆水寒大乱斗助手-Airtest-v1.1.0
~~~

### 3.3 开发者卡密管理工具

源码：

~~~text
E:\nsh\jiaozi\逆水寒交子助手_v3.5\license_admin
~~~

主要文件：

- app.py：Tkinter 管理界面。
- api.py：管理 API 客户端。
- build_admin.py：PyInstaller 构建入口。

v1.1.0 输出目录：

~~~text
E:\nsh\jiaozi\新的大乱斗\dist\逆水寒大乱斗助手-Airtest-v1.1.0-开发者卡密管理工具
~~~

### 3.4 旧后端

旧 Node/CloudBase 后端：

~~~text
E:\nsh\jiaozi\逆水寒交子助手_v3.5\cloudfn_test\license-admin-api
~~~

该服务只作为旧行为参考。新系统验收前不能删除；验收通过并取得用户明确确认后才能下线。

---

## 4. 固定业务决定

- 旧 CloudBase 卡密全部作废。
- 不迁移旧卡密、摘要盐、机器绑定或签名密钥。
- 新授权只绑定 RuoYi 账号，不绑定机器。
- 普通用户使用账号密码登录，不再输入卡密字符串。
- 只有状态正常并拥有“帮会成员”角色的账号可以获得和使用授权。
- 周四、周五、周六、周日继续本地免费进入，不访问服务器。
- 周一、周二、周三必须登录且具有有效授权。
- 网页卡密管理和开发者管理工具使用同一组后端接口。
- 卡密管理只允许超级管理员操作。
- 自助注册继续开启，新账号默认获得角色 ID 100 的帮会成员角色。
- 新发布版本为 v1.1.0，保留 v1.0.3 回滚。
- 正式域名根路径替换为新版项目。

---

## 5. 超级管理员权限字符调整

### 5.1 目标

需要修改的是角色管理中的权限字符：

~~~text
sys_role.role_key
~~~

最终值：

| 角色 ID | 角色名称 | 权限字符 |
| --- | --- | --- |
| 1 | 超级管理员 | cptbtptp |
| 2 | 帮会管理 | common |
| 100 | 帮会成员 | user |

超级管理员登录账号当前是 cptbtptp369。登录账号与角色权限字符是不同字段，本任务不修改登录账号。

### 5.2 数据库迁移

MySQL 核心迁移：

~~~sql
UPDATE sys_role
SET role_key = 'cptbtptp',
    update_by = 'system',
    update_time = NOW()
WHERE role_id = 1
  AND role_key <> 'cptbtptp';
~~~

迁移必须提前检查：

1. role_id=1 存在。
2. 不存在其他 role_key=cptbtptp 的角色。
3. 超级管理员账号仍通过 sys_user_role 关联 role_id=1。
4. sys_role_menu 关系完整。

需要同步修改：

- MySQL 全量初始化 SQL。
- PostgreSQL 全量初始化 SQL。
- 内置角色初始化逻辑。
- 系统角色保护逻辑。
- 项目菜单基线。
- 增量迁移。
- 数据库说明文档。

### 5.3 代码原则

禁止继续用字符串 admin 判断超级管理员。

内部判断优先使用：

1. role_id=1。
2. 用户模型中的 admin 布尔属性。
3. 必须读取权限字符时使用统一常量 SUPER_ADMIN_ROLE_KEY，其值为 cptbtptp。

需要更新：

- 登录后的角色和权限生成。
- 用户管理的超级管理员保护。
- 角色管理的内置角色保护。
- 帮会申请、首页和统计。
- 约战报名、活动和阵容。
- 数据库管理。
- AI Key、内功、面板和 PVP 管理。
- 网页与小程序角色显示。
- 新卡密管理。
- 全部测试。

迁移后普通用户名即使叫 admin，也不能获得超级权限。

### 5.4 发布顺序

1. 备份数据库。
2. 部署同时兼容旧 admin 和新 cptbtptp 的过渡代码。
3. 执行数据库迁移。
4. 验证超级管理员登录与全部菜单。
5. 部署只保留 cptbtptp 的最终代码。
6. 再次运行权限回归。

禁止只修改数据库而不更新代码。

---

## 6. 账号授权系统

### 6.1 套餐

| 名称 | 内部值 | 有效期 |
| --- | --- | --- |
| 天卡 | daily | 1 天 |
| 周卡 | weekly | 7 天 |
| 月卡 | monthly | 30 天 |
| 永久卡 | permanent | 无到期时间 |

授权规则：

1. 管理员提交后立即生效。
2. 未到期时从原到期时间顺延。
3. 已过期或不存在时从服务器当前时间开始。
4. 永久授权不被普通临时授权覆盖。
5. 永久授权改为临时授权前必须明确撤销。
6. 撤销不删除历史记录。
7. 每批最多操作 200 个账号。
8. 批量操作全有或全无。
9. 只允许给正常、未删除、拥有角色 100 的账号授权。
10. 备注最大 500 字。
11. 所有操作写入审计。

### 6.2 免费日

周四至周日：

- 显示“免费进入（不上云）”。
- 不登录。
- 不调用授权接口。
- 不绑定设备。

周一至周三：

- 必须联网。
- 必须登录 RuoYi 账号。
- 必须拥有帮会成员角色。
- 必须有未过期且未撤销的授权。

本地日期被修改可能影响免费日判断，这是保留的已知边界。

### 6.3 数据表

新增 system_account_license：

- license_id。
- user_id，唯一关联 sys_user。
- plan_type。
- status。
- valid_from。
- expires_at，永久授权为空。
- remark。
- version。
- create_by、create_time。
- update_by、update_time。

过期状态根据 expires_at 和服务器时间动态计算。

新增 system_account_license_audit：

- audit_id。
- batch_id。
- request_id。
- user_id。
- operator_user_id。
- action。
- previous_state JSON。
- new_state JSON。
- remark。
- created_at。

操作类型至少包括 grant、extend、revoke 和 remark_update。

新增 system_auth_refresh_token：

- token_id。
- token_hash。
- user_id。
- client_type。
- issued_at。
- expires_at。
- last_used_at。
- revoked_at。
- replaced_by_token_id。

服务端只保存刷新令牌摘要。刷新令牌默认有效 30 天，每次刷新后轮换。

### 6.4 注册角色

现有注册服务已经使用 REGISTER_DEFAULT_ROLE_ID=100，不新增重复逻辑。只增加回归测试，确认注册后 sys_user_role 中存在角色 100。

---

## 7. API 契约

正式 API 根地址：

~~~text
https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api/api/v1
~~~

所有公开 ID 使用字符串。所有响应沿用现有统一信封结构。

### 7.1 登录

保留：

~~~text
POST /auth/login
~~~

桌面客户端请求：

~~~json
{
  "userName": "member001",
  "password": "用户输入的密码",
  "code": "",
  "uuid": "",
  "clientType": "desktop-assistant"
}
~~~

成功响应在现有字段基础上增加：

~~~json
{
  "success": true,
  "data": {
    "accessToken": "短期访问令牌",
    "tokenType": "Bearer",
    "expiresIn": 86400,
    "refreshToken": "仅本次返回",
    "refreshExpiresIn": 2592000
  }
}
~~~

现有网页和小程序可以忽略新增字段，不能因此破坏现有登录。

密码、验证码、Authorization 头和令牌不得写入日志。

### 7.2 刷新登录

~~~text
POST /auth/refresh
~~~

请求：

~~~json
{
  "refreshToken": "客户端保存的刷新令牌",
  "clientType": "desktop-assistant"
}
~~~

刷新成功后返回新的访问令牌和刷新令牌，旧刷新令牌立即作废。重复使用旧令牌必须拒绝并留下脱敏安全日志。

### 7.3 查询本人授权

~~~text
GET /license/me
~~~

需要 Bearer 访问令牌。

响应示例：

~~~json
{
  "success": true,
  "data": {
    "userId": "10023",
    "userName": "member001",
    "eligibleRole": true,
    "authorized": true,
    "planType": "monthly",
    "validFrom": "2026-09-19T10:00:00+08:00",
    "expiresAt": "2026-10-19T10:00:00+08:00",
    "remainingSeconds": 2592000,
    "serverTime": "2026-09-19T10:00:10+08:00",
    "reason": null
  }
}
~~~

标准原因码：

- ACCOUNT_DISABLED。
- ACCOUNT_DELETED。
- MEMBER_ROLE_REQUIRED。
- LICENSE_NOT_GRANTED。
- LICENSE_EXPIRED。
- LICENSE_REVOKED。

授权接口每次读取实时账号、角色和授权状态，不能只相信登录时的 JWT 内容。

### 7.4 管理员账号列表

~~~text
GET /license-admin/accounts
~~~

查询参数：

- pageNum。
- pageSize。
- keyword。
- accountStatus。
- authorizationStatus。
- planType。

只返回状态允许被管理的帮会成员账号及当前授权摘要。

### 7.5 批量授权

~~~text
POST /license-admin/grants
~~~

请求：

~~~json
{
  "requestId": "客户端生成的 UUID",
  "userIds": ["10023", "10024"],
  "planType": "monthly",
  "remark": "2026年9月测试批次"
}
~~~

后端在同一事务中：

1. 校验超级管理员。
2. 检查 requestId 是否已经执行。
3. 锁定账号和授权记录。
4. 校验账号状态与帮会成员角色。
5. 计算每个账号的新到期时间。
6. 写入或更新授权。
7. 写入审计。
8. 提交事务。

任意账号不符合条件时整批回滚。

### 7.6 批量撤销

~~~text
POST /license-admin/revocations
~~~

请求包含 requestId、userIds 和 reason。撤销成功后，客户端下一次查询 /license/me 时立即失效。

### 7.7 修改备注

~~~text
PUT /license-admin/accounts/{userId}/remark
~~~

备注修改必须记录修改前、修改后和操作人。

### 7.8 审计查询

~~~text
GET /license-admin/audit
~~~

支持按账号、操作人、操作类型、批次和时间范围筛选。

### 7.9 管理接口权限

所有管理接口必须同时校验：

- 当前账号存在、未删除且未禁用。
- 当前账号关联角色 ID 1。
- 超级管理员权限字符为 cptbtptp。
- 当前权限包含对应 system:license 权限或通配权限。

前端隐藏菜单不是安全措施，后端必须独立拒绝越权请求。

---

## 8. 网页任务

### 8.1 卡密管理

菜单位置：

~~~text
系统管理 → 卡密管理
~~~

仅超级管理员可见。

权限字符：

~~~text
system:license:list
system:license:grant
system:license:revoke
system:license:remark
system:license:audit
~~~

列表字段：

- 勾选框。
- 用户 ID。
- 用户名。
- 昵称。
- 账号状态。
- 帮会成员角色状态。
- 授权状态。
- 套餐。
- 生效时间。
- 到期时间。
- 剩余时间。
- 备注。
- 最后操作人。
- 最后操作时间。

页面操作：

- 用户名和昵称搜索。
- 账号状态筛选。
- 授权状态筛选。
- 套餐筛选。
- 单账号授权。
- 多账号批量授权。
- 单账号撤销。
- 多账号批量撤销。
- 编辑备注。
- 查看审计。
- 网络失败后保留勾选和填写内容并允许重试。

### 8.2 删除侧栏顶部

删除用户指出的整个侧栏顶部区域：

- logo 图片。
- vfadmin管理系统文字。
- 链接和动画。
- 原区域空白高度。
- 设置面板中的侧栏 logo 开关。

展开和折叠侧栏时都不能重新显示。浏览器标题和登录页标题不在本项范围，除非后续另行要求。

### 8.3 角色显示

统一映射：

~~~text
cptbtptp → 超级管理员
common → 帮会管理
user → 帮会成员
~~~

角色管理中，角色 ID 1 的权限字符不能通过普通编辑操作改回 admin。

---

## 9. 微信小程序任务

正式接口由当前错误的 /prod-api 改为：

~~~text
https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api
~~~

小程序角色名称映射同步改为：

~~~text
cptbtptp → 超级管理员
common → 帮会管理
user → 帮会成员
~~~

小程序不增加卡密管理入口。现有登录、个人资料、组织、约战、活动、战报、职业颜色和联赛分析功能保持不变。

---

## 10. 大乱斗助手 v1.1.0

### 10.1 启动流程

周四至周日：

1. 显示当前为免费时段。
2. 用户点击“免费进入（不上云）”。
3. 不调用登录接口。
4. 不调用授权接口。
5. 直接进入现有主程序。

周一至周三：

1. 读取 Windows DPAPI 加密保存的刷新令牌。
2. 如果存在，调用 /auth/refresh。
3. 刷新成功后调用 /license/me。
4. 授权有效则进入主程序。
5. 刷新失败或令牌不存在时显示账号密码登录。
6. 登录成功后调用 /license/me。
7. 全部校验通过后进入主程序。

### 10.2 本地凭据

- 只保存刷新令牌。
- 使用 Windows DPAPI 当前用户范围加密。
- 不保存明文密码。
- 不使用机器摘要作为授权条件。
- 用户主动退出后删除本地令牌。
- 账号禁用或令牌撤销时清理本地令牌并返回登录。

### 10.3 删除旧逻辑

删除：

- 卡密输入框。
- license_key。
- machine_hash。
- 一机一码。
- 解绑设备。
- 旧 CloudBase SERVICE_URL。
- 旧签名公钥。
- 旧 activate、validate 和 unbind 请求。

保留：

- 周四至周日免费逻辑。
- Airtest 识别。
- 目标窗口绑定。
- 鼠标驱动和轨迹。
- 紧急停止。
- 运行日志。

### 10.4 错误提示

分别显示：

- 用户名或密码错误。
- 验证码错误。
- 网络连接失败。
- 服务器维护中。
- 账号已禁用。
- 账号不是帮会成员。
- 管理员尚未授权。
- 授权已过期。
- 授权已撤销。
- 登录状态已失效。

### 10.5 版本

程序内部版本、窗口标题、构建产物和使用说明统一为 v1.1.0。禁止覆盖 v1.0.3 目录。

---

## 11. 开发者管理工具 v1.1.0

### 11.1 登录

- 使用 RuoYi 用户名和密码。
- 先读取 /auth/config。
- 不加入图片验证码；开发者工具只提交账号和密码，服务端仍校验超级管理员及账号授权管理权限。
- 登录后调用 /auth/me。
- 必须确认角色 ID 1 和权限字符 cptbtptp。
- 普通成员和帮会管理员拒绝进入。

### 11.2 功能

与网页卡密管理保持一致：

- 账号搜索。
- 分页和筛选。
- 多选。
- 批量天卡。
- 批量周卡。
- 批量月卡。
- 批量永久卡。
- 批量撤销。
- 修改备注。
- 查询审计。

删除旧卡密生成、明文卡密导出、机器摘要、解绑设备、CloudBase 地址和全局免费开关。

管理员密码不保存。访问令牌默认只保留在当前进程内，关闭程序后重新登录。

---

## 12. GitHub 方案

### 12.1 服务器项目

仓库：

~~~text
https://github.com/Jiajiazi886/nsh
~~~

分支：

~~~text
xiaochengxu
~~~

提交前执行：

~~~powershell
git status --short
git diff --check
git diff --cached --check
~~~

必须核对工作区后再暂存，不能把数据库备份、环境文件或无关文件带入提交。

### 12.2 桌面程序私有仓库

新建私有仓库：

~~~text
Jiajiazi886/nsh-daluandou-desktop
~~~

只纳入：

- app_v2。
- license_admin。
- templates。
- trajectory_host。
- 必需 DLL 和第三方许可。
- 两个构建脚本。
- 自动化测试。
- README 和构建说明。

排除：

- dist、build 和 work。
- .venv 和 node_modules。
- 日志和本地配置。
- 用户缓存和令牌。
- 旧发布包。

完成后创建 v1.1.0 Git 标签。

---

## 13. 本地开发步骤

确认 MySQL 3306 和 Redis 6379 正常，再启动独立项目：

~~~powershell
Set-Location 'E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-current-project.ps1
~~~

验证：

~~~powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5173/login
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9101/api/v1/auth/config
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:9101/docs
~~~

实施顺序：

1. 为超级管理员权限字符编写失败测试。
2. 增加统一角色常量和过渡兼容。
3. 增加数据库迁移。
4. 在本地测试库执行迁移。
5. 完成权限回归。
6. 为账号授权模型编写失败测试。
7. 实现数据表、DAO、Service 和事务。
8. 实现刷新令牌和 /license/me。
9. 实现管理员接口。
10. 实现网页卡密管理。
11. 删除侧栏 logo 区域。
12. 修改小程序接口地址与角色映射。
13. 修改大乱斗助手。
14. 修改开发者管理工具。
15. 完整回归并构建两个 v1.1.0 软件。
16. 提交两个 GitHub 仓库。
17. 执行数据迁移和服务器部署。

建议拆成可回滚的小提交：

1. test: define super admin role key migration contract
2. feat(auth): migrate super admin role key to cptbtptp
3. feat(license): add account entitlement schema and service
4. feat(auth): add rotating desktop refresh tokens
5. feat(api): add license and administration APIs
6. feat(web): add system account license management
7. fix(web): remove sidebar logo area
8. fix(mini): align production API and role mapping
9. feat(desktop): replace machine license with account authorization
10. feat(admin): rebuild developer management client
11. docs(deploy): add migration and rollback instructions

---

## 14. 本地数据库备份与迁移包制作

### 14.1 备份前提

数据库迁移前必须进入短时维护状态，停止会修改数据的本地后端、定时任务和管理脚本。不要在业务仍持续写入时直接导出，否则多个表之间可能出现时间点不一致。

迁移包属于敏感文件，只允许保存在 Git 仓库外的私有目录中，不得提交到 GitHub。建议目录：

~~~text
E:\nsh\private-migration\2026-09-19\
├─ database\
├─ uploads\
├─ checksums\
└─ notes\
~~~

### 14.2 导出本地数据库

源数据库固定为：

~~~text
nsh_activity_dev_20260914
~~~

PowerShell 示例。密码采用交互式输入，不写入命令历史、脚本或文档：

~~~powershell
$backupRoot = 'E:\nsh\private-migration\2026-09-19'
$backupSql = Join-Path $backupRoot 'database\nsh_activity_dev_20260914.sql'
New-Item -ItemType Directory -Force -Path (Split-Path $backupSql) | Out-Null
mysqldump.exe --host=127.0.0.1 --port=3306 --user=root --password --single-transaction --routines --triggers --events --default-character-set=utf8mb4 --set-gtid-purged=OFF --result-file="$backupSql" nsh_activity_dev_20260914
Get-FileHash -Algorithm SHA256 -LiteralPath $backupSql | Format-List
~~~

如果本机 MySQL 版本不支持 `--set-gtid-purged=OFF`，删除该参数后重试。导出命令成功并不等于备份有效，还必须确认文件大小大于零，并至少在一个临时数据库中完成恢复演练。

### 14.3 备份上传文件

检查后端配置中实际使用的上传目录。常见目录是 `vf_admin/uploads`，但必须以当前环境变量和代码配置为准。将上传目录完整复制到迁移包，并保留相对路径、文件名和时间戳。

~~~powershell
$sourceUploads = 'E:\nsh\nshls\RuoYi-Vue3-FastAPI-miniapp-backend\vf_admin\uploads'
$targetUploads = 'E:\nsh\private-migration\2026-09-19\uploads'
if (Test-Path -LiteralPath $sourceUploads) {
    Copy-Item -LiteralPath $sourceUploads -Destination $targetUploads -Recurse -Force
}
~~~

### 14.4 记录迁移基线

至少记录以下内容，保存到私有迁移目录的 `notes\baseline.md`：

- 数据库名、MySQL 版本、字符集和排序规则。
- 导出时间与导出操作人。
- SQL 文件大小和 SHA-256。
- 上传文件总数、总大小和目录摘要。
- 关键表行数：用户、角色、用户角色、菜单、组织、成员、约战活动、阵容快照、报名记录、玩家资料、职业颜色、账号授权。
- `sys_role` 中 role_id 为 1 的角色名称和迁移前权限字符。
- 当前 Git 分支、提交哈希和本地是否存在未提交改动。

### 14.5 本地恢复演练

在独立临时库中恢复 SQL，不得覆盖正在使用的本地开发库：

~~~sql
CREATE DATABASE nsh_activity_restore_test
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
~~~

恢复后执行后端迁移，确认超级管理员权限字符为 `cptbtptp`，再运行自动化测试和关键接口冒烟测试。恢复演练通过后，迁移包才允许上传服务器。

---

## 15. OpenCloudOS 9.6 服务器上线前检查

服务器信息：

| 项目 | 值 |
| --- | --- |
| 操作系统 | OpenCloudOS 9.6 |
| 公网 IP | `152.136.161.6` |
| SSH 用户 | `root`，仅用于首次初始化和紧急维护 |
| 正式域名 | `https://www.xn--kbrr2vyxjytebq4azkrrie.icu/` |

上线前检查：

1. 立即轮换已暴露的 root 密码。
2. 创建普通部署账号，例如 `deploy`，加入 Docker 用户组。
3. 为部署账号配置 SSH 公钥，验证公钥登录后关闭 root 密码远程登录。
4. 校准系统时区为 `Asia/Shanghai`，启用时间同步。
5. 检查磁盘、内存、CPU、端口占用和安全组。
6. 仅开放必要端口：22、80、443；数据库、Redis 和应用内部端口不直接暴露公网。
7. 安装并启用防火墙；SSH 最好限制为可信源 IP。
8. 检查域名 DNS 已指向 `152.136.161.6`。
9. 准备 TLS 证书，证书私钥不得进入 Git。
10. 创建服务器备份目录和部署目录，并限制权限。

推荐目录：

~~~text
/srv/nsh/
├─ app/                 # Git 工作区
├─ env/                 # 生产环境变量，不进入 Git
├─ data/
│  ├─ mysql/
│  ├─ redis/
│  └─ uploads/
├─ migration/           # 临时迁移包，完成后转移到安全备份区
├─ backups/
│  ├─ mysql/
│  └─ uploads/
└─ logs/
~~~

---

## 16. Docker 与基础依赖安装

优先使用项目现有 Docker Compose 方式统一部署，避免服务器 Python、Node.js、MySQL 和 Redis 版本漂移。

基本检查命令：

~~~bash
cat /etc/opencloudos-release
uname -a
df -h
free -h
ss -lntup
timedatectl
git --version
docker --version
docker compose version
~~~

如果尚未安装 Docker，应使用 OpenCloudOS 9.6 可用且受支持的软件源安装 Docker Engine 和 Compose 插件。安装完成后：

~~~bash
systemctl enable --now docker
docker info
docker compose version
~~~

不得把数据库、Redis 或后端端口直接映射到 `0.0.0.0`。容器之间通过专用 Docker 网络通信，只有 Nginx 暴露 80 和 443。

---

## 17. 服务器代码目录和 Git 拉取

### 17.1 创建部署账号和目录

首次使用 root 完成初始化，随后切换到部署账号：

~~~bash
useradd --create-home --shell /bin/bash deploy
usermod -aG docker deploy
mkdir -p /srv/nsh/{app,env,data/mysql,data/redis,data/uploads,migration,backups/mysql,backups/uploads,logs}
chown -R deploy:deploy /srv/nsh
chmod 700 /srv/nsh/env /srv/nsh/migration /srv/nsh/backups
~~~

### 17.2 拉取项目

主项目使用：

~~~text
仓库：https://github.com/Jiajiazi886/nsh
分支：xiaochengxu
~~~

~~~bash
sudo -u deploy git clone --branch xiaochengxu --single-branch https://github.com/Jiajiazi886/nsh.git /srv/nsh/app
cd /srv/nsh/app
git status
git rev-parse HEAD
~~~

部署时必须记录最终提交哈希。生产服务器不允许直接修改 Git 跟踪文件；任何代码修复都应在本地完成、测试、提交、推送，再由服务器拉取指定提交。

桌面端私有仓库 `Jiajiazi886/nsh-daluandou-desktop` 不需要部署到服务器运行，但其源代码、构建脚本和发布清单必须完整推送。服务器只部署桌面端所依赖的统一后端接口。

---

## 18. 生产环境变量与密钥管理

生产环境变量放到 `/srv/nsh/env/prod.env`，权限设置为 600，不进入 Git。至少包含：

~~~dotenv
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=9099
APP_SECRET_KEY=由安全随机生成器生成
JWT_SECRET_KEY=由安全随机生成器生成
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=nsh_activity_dev_20260914
MYSQL_USER=nsh_app
MYSQL_PASSWORD=单独生成的数据库强密码
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=单独生成的Redis强密码
UPLOAD_DIR=/srv/nsh/data/uploads
PUBLIC_API_BASE=https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api/api/v1
~~~

要求：

- 生产密钥与本地开发密钥不同。
- 生产数据库不得使用 root 作为应用账号。
- 桌面端和小程序只保存公开 API 地址，不内置数据库密码、JWT 密钥或管理员凭据。
- 日志不得打印完整 Authorization、刷新令牌、微信号、密码或数据库连接串。
- GitHub 仓库只提交 `.env.example`，其中只保留变量名和无敏感信息的示例值。

---

## 19. 迁移包上传与校验

### 19.1 上传前要求

迁移包不得通过公开 GitHub 仓库传输。推荐通过 SCP、SFTP 或受控对象存储上传。正式上传前：

1. 确认 SQL 已在本地临时库恢复成功。
2. 确认迁移包不含旧的 `.env`、访问令牌、浏览器会话或无关个人文件。
3. 为 SQL 和上传文件清单生成 SHA-256。
4. 服务器目标目录必须是 `/srv/nsh/migration/本次批次`，不能直接覆盖运行目录。

PowerShell 上传示例：

~~~powershell
$batch = '2026-09-19'
scp -r 'E:\nsh\private-migration\2026-09-19\*' "deploy@152.136.161.6:/srv/nsh/migration/$batch/"
~~~

首次连接必须人工核对 SSH 主机指纹，不能忽略主机指纹警告。上传结束后在服务器重新计算哈希并与本地结果比较：

~~~bash
cd /srv/nsh/migration/2026-09-19
sha256sum database/nsh_activity_dev_20260914.sql
find uploads -type f -print0 | sort -z | xargs -0 sha256sum > checksums/uploads.sha256
~~~

### 19.2 上传文件切换策略

不要边复制边让应用读取。先复制到暂存目录，校验数量和大小，再原子切换目录：

~~~bash
mkdir -p /srv/nsh/data/uploads.next
cp -a /srv/nsh/migration/2026-09-19/uploads/. /srv/nsh/data/uploads.next/
find /srv/nsh/data/uploads.next -type f | wc -l
~~~

确认无误后，在应用停写状态下将旧目录改名为带时间戳的备份，再把 `uploads.next` 改名为正式目录。旧目录至少保留到验收完成。

---

## 20. 生产数据库恢复和迁移

### 20.1 初始化数据库容器

先启动 MySQL 和 Redis，不启动对外后端：

~~~bash
cd /srv/nsh/app
docker compose --env-file /srv/nsh/env/prod.env up -d mysql redis
docker compose ps
docker compose logs --tail=100 mysql redis
~~~

实际服务名以仓库中的 Compose 文件为准。若不是 `mysql` 和 `redis`，必须先查看 Compose 配置后替换命令，不能猜测。

### 20.2 创建应用数据库账号

使用数据库管理员账号在容器内部创建最小权限应用账号。管理员密码只通过安全交互或受限环境变量传入，不写入命令历史。

应用账号仅授予目标数据库所需权限，不授予全局权限、文件权限或创建系统用户权限。

### 20.3 恢复 SQL

恢复前再次确认目标数据库名和目标容器。生产首次迁移允许创建空库后导入；已有生产数据时禁止直接覆盖，必须走增量迁移或停机合并方案。

示例流程：

~~~bash
docker cp /srv/nsh/migration/2026-09-19/database/nsh_activity_dev_20260914.sql nsh-mysql:/tmp/source.sql
docker exec -it nsh-mysql sh
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS nsh_activity_dev_20260914 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p nsh_activity_dev_20260914 < /tmp/source.sql
exit
~~~

容器名 `nsh-mysql` 只是示例，必须通过 `docker compose ps` 获取实际容器名。

### 20.4 执行应用迁移

SQL 恢复完成后执行仓库实际使用的迁移工具，例如 Alembic。命令必须在后端容器或与生产环境相同的 Python 环境中执行：

~~~bash
docker compose --env-file /srv/nsh/env/prod.env run --rm backend alembic upgrade head
~~~

如果项目提供专用迁移脚本，应优先使用项目脚本。迁移必须包含：

- 超级管理员权限字符从 `admin` 更新为 `cptbtptp`。
- 账号授权、授权流水、桌面刷新令牌等新表。
- 必要的索引、唯一约束、外键和审计字段。
- 对旧数据兼容的默认值和回填逻辑。

### 20.5 数据库关键校验

执行以下只读检查：

~~~sql
SELECT role_id, role_name, role_key, status
FROM sys_role
WHERE role_id = 1;

SELECT user_id, user_name, status
FROM sys_user
WHERE user_name = 'cptbtptp369';

SELECT COUNT(*) AS user_count FROM sys_user;
SELECT COUNT(*) AS role_count FROM sys_role;
SELECT COUNT(*) AS user_role_count FROM sys_user_role;
~~~

预期：

- role_id 1 的 `role_key` 为 `cptbtptp`。
- 用户名 `cptbtptp369` 保持不变且能正常登录。
- 迁移前后的关键表行数与基线一致，新增表除外。
- 不存在仍依赖 `role_key = 'admin'` 才能获得超级管理员权限的代码路径。

---

## 21. 完整服务启动与健康检查

### 21.1 构建并启动

~~~bash
cd /srv/nsh/app
git fetch origin
git checkout xiaochengxu
git pull --ff-only origin xiaochengxu
git rev-parse HEAD
docker compose --env-file /srv/nsh/env/prod.env build --pull
docker compose --env-file /srv/nsh/env/prod.env up -d
docker compose ps
~~~

生产更新只能使用快进拉取或部署固定提交，不能在服务器执行强制重置来掩盖本地改动。

### 21.2 容器内健康检查

先从服务器本机访问后端健康接口，再测试反向代理：

~~~bash
curl --fail --show-error http://127.0.0.1:9099/health
curl --fail --show-error http://127.0.0.1:9099/api/v1/system/health
docker compose logs --tail=200 backend
~~~

健康接口路径以代码实际定义为准。若尚未提供，实施阶段应增加不泄露敏感信息的健康接口，至少检查进程、数据库和 Redis 可用性。

### 21.3 登录与授权冒烟测试

使用专门测试账号完成：

1. 网页账号密码登录。
2. 超级管理员访问系统管理中的账号授权页面。
3. 普通成员无法访问管理接口。
4. 桌面端周一至周三能登录并读取授权状态。
5. 无授权账号得到明确的未授权提示。
6. 管理员发放一天授权后客户端立即可用。
7. 重复发放时从未过期时间继续延长。
8. 周四至周日客户端本地免费逻辑不请求授权接口。
9. 刷新令牌轮换和吊销符合预期。

---

## 22. Nginx 与 HTTPS 配置

外部统一使用 HTTPS，后端容器端口仅监听本机或 Docker 网络。建议沿用 `/docker-api/` 作为统一后端前缀。

Nginx 配置示例：

~~~nginx
server {
    listen 80;
    server_name www.xn--kbrr2vyxjytebq4azkrrie.icu xn--kbrr2vyxjytebq4azkrrie.icu;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.xn--kbrr2vyxjytebq4azkrrie.icu xn--kbrr2vyxjytebq4azkrrie.icu;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    client_max_body_size 100m;

    location /docker-api/ {
        proxy_pass http://127.0.0.1:9099/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 60s;
    }

    location / {
        root /srv/nsh/app/frontend-dist;
        try_files $uri $uri/ /index.html;
    }
}
~~~

配置部署后执行：

~~~bash
nginx -t
systemctl reload nginx
curl --fail --show-error --location https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api/api/v1/system/health
~~~

需要特别验证小程序生产配置。当前已知错误是使用 `/prod-api`；实施时必须改为：

~~~text
https://www.xn--kbrr2vyxjytebq4azkrrie.icu/docker-api/api/v1
~~~

微信小程序后台还需要配置合法 request 域名，并确保域名证书链完整、TLS 版本受微信支持。

---

## 23. 本地与生产数据一致性验收

“部署后的数据与本地相同”应以可核验指标定义，不能只凭页面肉眼判断。

### 23.1 数据库一致性

迁移完成后比较：

- 每个关键业务表的行数。
- 主键最小值、最大值和数量。
- 关键表按稳定主键排序后的摘要校验。
- 用户与角色关联数量。
- 组织、成员、活动、快照、报名和战报的关联完整性。
- 新授权表的初始数据是否符合设计，不得为所有用户自动发放权限。

对包含更新时间、迁移流水或新字段默认值的表，不要求整个物理 SQL 文件哈希相同，应比较业务字段和关系完整性。

### 23.2 上传文件一致性

比较：

- 文件总数。
- 总字节数。
- 每个相对路径的 SHA-256。
- 数据库引用的文件是否实际存在。
- 不存在数据库引用越界到上传目录外的路径。

### 23.3 功能一致性

使用同一测试账号分别在本地与生产验证：

- 登录身份、角色和菜单一致。
- 帮会、成员、活动、阵容和战报数据一致。
- 职业颜色与玩家资料一致。
- 账号授权状态及管理权限符合迁移方案。
- 网页、小程序和桌面端都指向正确环境，不串用本地地址。

---

## 24. 备份、日志与监控

### 24.1 数据库备份

建议：

- 每日一次完整逻辑备份。
- 备份文件压缩并加密。
- 至少保留 7 个日备份、4 个周备份和 3 个月备份。
- 至少一份备份保存在服务器之外。
- 每月至少执行一次恢复演练。

备份任务必须记录开始时间、结束时间、文件大小、哈希和结果。备份失败需要告警，不能静默跳过。

### 24.2 上传文件备份

上传文件与数据库备份应处于相近时间点，并在备份元数据中记录对应关系。只备份数据库而不备份上传文件，无法完整恢复业务。

### 24.3 日志

至少保留：

- Nginx 访问日志和错误日志。
- 后端应用日志。
- 登录失败、令牌刷新失败和授权管理审计日志。
- 数据库慢查询日志。
- 容器启动、退出和健康检查日志。

日志必须脱敏：密码、完整令牌、微信号和数据库连接凭据不得明文出现。

### 24.4 监控告警

至少监控：

- HTTPS 可用性与证书到期时间。
- 后端健康接口。
- 容器状态和重启次数。
- CPU、内存、磁盘和 inode。
- MySQL 连接、磁盘空间和备份结果。
- Redis 可用性。
- 5xx 比例和关键接口错误率。
- 登录异常峰值和授权接口异常峰值。

---

## 25. 回滚方案

上线前必须准备回滚，不允许等故障发生后临时设计。

### 25.1 代码回滚

记录上线前和上线后的 Git 提交哈希、镜像标签和 Compose 配置版本。发生严重问题时：

1. 停止对外写入。
2. 保留故障日志和数据库现场。
3. 将应用切回上一版已验证镜像或上一提交构建物。
4. 恢复与旧代码兼容的数据库状态。
5. 恢复上一版上传目录。
6. 执行健康检查和冒烟测试后再恢复流量。

### 25.2 数据库回滚

任何结构迁移前必须生成即时备份。若迁移工具提供 downgrade，仍需先验证 downgrade 不会丢失业务数据。包含破坏性字段删除、类型缩窄或数据重写时，不依赖自动 downgrade，直接从已验证备份恢复到新建数据库并切换连接。

超级管理员权限字符的独立回滚 SQL：

~~~sql
UPDATE sys_role
SET role_key = 'admin'
WHERE role_id = 1
  AND role_key = 'cptbtptp';
~~~

执行该 SQL 只恢复数据库值。若代码已经删除了对 `admin` 的兼容，必须同时回滚代码，不能只回滚数据库。

### 25.3 授权系统回滚

账号授权功能出现问题时：

- 不得把所有用户临时改成超级管理员或跳过后端权限校验。
- 可以临时关闭桌面端工作日登录入口并发布故障说明。
- 已产生的授权流水不得删除；修复后通过补偿流水纠正。
- 重复请求必须依靠幂等键避免重复加时。
- 若刷新令牌泄露，按账号或令牌族吊销，不要求用户修改业务数据。

### 25.4 桌面端回滚

保留 v1.0.3 安装包和校验值，v1.1.0 使用独立输出目录。回滚时不要覆盖用户任务配置、截图和日志目录。开发者工具与普通助手必须分别保留版本和回滚包。

---

## 26. 测试方案

### 26.1 后端单元与集成测试

必须覆盖：

- role_id 1 在权限字符为 `cptbtptp` 时仍具有超级管理员能力。
- 普通角色伪造 `role_key` 不能获得超级管理员权限。
- 仅 role_id 100 的有效账号可使用桌面授权。
- 一天、七天、三十天、永久授权计算正确。
- 未过期授权从原到期时间续期，已过期授权从当前时间开始。
- 永久授权不会被短期授权降级。
- 幂等键重复提交不会重复加时。
- 并发发放不会丢失更新或重复延长。
- 授权流水不可被普通管理员篡改或删除。
- 登录、刷新、登出和令牌轮换正确。
- 被禁用、删除或角色变更账号立即失去资格。
- 管理接口只有超级管理员可访问。

### 26.2 网页测试

- 系统管理中可见“账号授权管理”。
- 非超级管理员菜单不可见，直接访问接口也被拒绝。
- 搜索、筛选、分页、发放、续期、设为永久、撤销和流水查看正常。
- 二次确认明确展示目标账号和变化结果。
- 侧栏 logo、图片和“vfadmin管理系统”文字已删除，折叠和菜单布局无空白异常。
- 修改超级管理员权限字符后，登录、菜单、按钮权限和路由守卫正常。

### 26.3 小程序测试

- 使用与网页相同的账号密码登录。
- role_id 1 与 `cptbtptp` 映射正确。
- 生产 API 使用 `/docker-api/api/v1`。
- 用户资料、帮会、约战、阵容和战报读取同一后端数据。
- 网络失败明确提示，不以假数据伪装成功。
- 退出登录后清理令牌和账号相关缓存。

### 26.4 桌面普通助手测试

- 周四、周五、周六、周日完全使用本地免费逻辑，不访问授权接口。
- 周一、周二、周三必须登录并验证有效授权。
- 账号无 role_id 100、无授权、已过期、被禁用时均给出准确提示。
- 不再显示卡密输入和机器绑定。
- 登录令牌安全保存，日志不输出凭据。
- 断网、服务器超时、401、403、429、500 都有明确处理。
- Airtest 核心自动化功能与 v1.0.3 保持回归通过。
- 新旧版本可以独立安装或解压运行，v1.0.3 文件不被覆盖。

### 26.5 开发者管理工具测试

- 仅超级管理员账号可以进入。
- 登录页面不显示图片验证码控件；启动、登录、刷新和失败重试均不请求 `/auth/captcha`。
- 使用 HTTP 请求断言核对：登录正文只含 `userName`、`password`、`clientType=license-admin`，不含 `code`、`uuid`、验证码图片或其他验证码字段。
- 使用刷新请求断言核对：正文只含 `refreshToken`、`clientType=license-admin`，不含验证码字段。
- 普通网页和微信小程序仍按原规则请求并校验验证码，不能被开发者工具的免验证码逻辑影响。
- 账号搜索和授权状态查询准确。
- 发放短期和永久授权的结果与网页一致。
- 重复点击或网络重试不会重复加时。
- 操作历史能显示操作者、对象、前后值、原因和时间。
- 退出后令牌失效，普通账号无法绕过界面直接调用接口。

### 26.6 数据迁移测试

- SQL 能恢复到空库。
- 迁移脚本可从当前基线升级到最新版本。
- 关键表数量与本地基线一致。
- 外键和唯一约束无异常。
- 上传文件数量、大小和哈希一致。
- 迁移完成后网页、小程序、桌面端可读取同一账号和业务数据。
- 回滚演练能够恢复上一版本。

### 26.7 安全测试

- 暴力登录有限速和审计。
- JWT、刷新令牌和密码不出现在日志。
- 刷新令牌只能使用一次，旧令牌重放被拒绝。
- CORS 只允许预期来源。
- 数据库和 Redis 端口不暴露公网。
- 上传接口限制类型、大小和路径穿越。
- 普通用户无法读取其他用户的敏感资料或授权管理数据。
- Git 历史、构建产物和发布包不含 `.env`、服务器密码或私钥。

---

## 27. 分阶段验收清单

### 27.1 本地开发验收

- [ ] 所有改动只发生在独立副本和桌面端项目，原毕业项目无变更。
- [x] role_id 1 的权限字符已迁移为 `cptbtptp`（目标库 `nsh_activity_dev_20260914` 实测）。
- [x] 超级管理员用户名 `cptbtptp369` 保持不变；MySQL/PostgreSQL 全量安装脚本和目标开发库均使用该账号（真实密码未写入仓库）。
- [x] 所有硬编码 `admin` 权限字符已清理；权限判断统一使用 `role_id=1` 与 `role_key=cptbtptp`，旧 `admin` 布尔字段仅保留在集中兼容逻辑中，不作为权限字符。
- [x] 账号授权表、授权流水和刷新令牌表已建立：运行时迁移、MySQL/PostgreSQL 独立脚本及全量安装脚本均包含三张表与 `sys_user` 外键。
- [x] 已提供 `20260919_account_license_rollback_mysql.sql` 与 `20260919_account_license_rollback_postgresql.sql`；执行前必须备份并停止新版服务。
- [x] 后端自动化测试通过（隔离集成 261 项；账号授权/刷新令牌/角色专项及开发者登录边界回归通过）。
- [x] 卡密管理专用权限边界已收紧：必须同时具备数据库 `role_id=1` 与 `role_key=cptbtptp`；伪造 `role_id=2` 的同名角色被拒绝。
- [x] 网页卡密管理入口位于系统管理；菜单基线、动态路由和后端接口均限制为 `role_id=1` 且 `role_key=cptbtptp`，普通角色没有 3170–3175 菜单。
- [x] 侧栏品牌图片和文字已从网页源码移除；浏览器人工视觉验收仍待执行。
- [x] 两个小程序入口使用统一账号和正确接口（Node 契约测试 8 项通过；生产前缀为 docker-api）。
- [x] 两个桌面程序 v1.1.0 构建成功，v1.0.3 保留（普通助手与开发者工具产物均存在并已计算 SHA-256）。普通助手完整回归 62 项、授权/发布契约测试 9 项、开发者工具无验证码与权限契约测试 7 项通过。
- [x] 开发者管理工具明确不加入图片验证码：源码、契约测试（3 项通过）和界面说明均不请求或提交 `code`、`uuid`；网页和普通小程序验证码流程保持独立。
- [x] 本地启动脚本已强制注入 `DB_DATABASE=nsh_activity_dev_20260914` 并拒绝不符合 `nsh_activity_dev_YYYYMMDD` 的数据库名；生产 compose 已使用 `nsh_app` 应用账号，密码仅从 `MYSQL_PASSWORD` 注入。
- [x] 前端 `npm run build:docker` 构建成功；构建仅有既存 `%VITE_APP_TITLE%` 未定义警告。

### 27.2 GitHub 验收

- [x] 主项目 `Jiajiazi886/nsh` 的 `xiaochengxu` 分支已推送并通过远端分支核验；验收时运行 `git ls-remote --heads origin xiaochengxu` 记录实际提交。
- [x] 桌面端私有仓库 `Jiajiazi886/nsh-daluandou-desktop` 已创建并推送；仓库为私有，默认分支 `main`，远端提交 `da3be1e093513c19671bf09a7fab66ba18a10bee`，`v1.1.0` 标签已发布。发布树只纳入普通助手、开发者工具、构建脚本、测试、模板、必需 DLL 与许可，排除构建输出、缓存、`.env`、令牌、私钥、数据库导出和用户数据。
- [ ] 两个仓库无 token、`.env`、服务器密码、数据库导出、证书私钥或用户数据。
- [ ] 提交历史清晰，可定位数据库迁移、API、网页、小程序和桌面端改动。
- [x] v1.1.0 发布包有版本说明和 SHA-256：普通助手 `7177D1BC029F1EF75E6A90F926A8F9C4AC859BEB914E79E2F98A7427E6FADA1A`；开发者工具 `1EC4C923D1CB845EBB8CDAEE781AF0A9810A772223C417076F243F0DAFCE5AEF`。产物尚未进入桌面端 GitHub 私有仓库。

### 27.3 服务器部署验收

- [ ] 已轮换暴露的 root 密码并启用 SSH 密钥。
- [ ] 生产服务运行于 OpenCloudOS 9.6。
- [ ] HTTPS 证书有效，HTTP 自动跳转 HTTPS；公网根域名当前返回旧站点，尚未证明新版证书和站点配置。
- [ ] `/docker-api/api/v1` 可用，内部数据库和 Redis 不暴露公网；当前公开 API 前缀返回 404，生产部署未完成。
- [ ] 本地数据库和上传文件已按基线迁移并完成一致性核验。
- [ ] role_id 1 的生产权限字符为 `cptbtptp`。
- [ ] 网页、小程序和桌面端使用同一生产账号体系。
- [ ] 生产日志无敏感信息。
- [ ] 自动备份、健康检查和告警已启用。
- [ ] 回滚包、旧镜像、数据库备份和旧上传目录可用。

目标开发库 `nsh_activity_dev_20260914` 已完成迁移、角色字符核验和逻辑备份；生产库仍未连接，禁止用 `ruoyi` 代替生产目标或创建假的生产数据。

### 27.4 业务验收

- [ ] 超级管理员能为 role_id 100 的账号发放授权。
- [ ] 一天、七天、三十天和永久授权均正确。
- [ ] 周一至周三正确执行登录和授权校验。
- [ ] 周四至周日无需登录授权即可进入免费功能，且不调用后端授权接口。
- [ ] 非帮会成员角色不能使用桌面授权。
- [ ] 网页和开发者工具显示同一授权状态与流水。
- [ ] 禁用账号、撤销授权和角色变化能及时生效。
- [ ] 原有帮会、约战、阵容、战报和个人资料功能无回归。

---

## 28. 最终交付物与完成定义

最终必须交付：

1. 独立副本中的完整后端、网页和小程序源代码。
2. 可重复执行的数据库迁移脚本和回滚说明。
3. 系统管理中的账号授权管理页面。
4. 大乱斗助手 v1.1.0 安装包或可执行包。
5. 开发者卡密管理工具 v1.1.0 安装包或可执行包。
6. 两个软件的 SHA-256、版本说明和最小运行环境说明。
7. 主项目 GitHub `xiaochengxu` 分支。
8. 私有桌面端 GitHub 仓库 `Jiajiazi886/nsh-daluandou-desktop`。
9. 本地数据库与上传文件的私有迁移包，迁移完成后按安全策略保存或销毁。
10. OpenCloudOS 9.6 上可交互的正式系统。
11. 部署记录、生产提交哈希、数据库迁移版本、备份位置和回滚记录。
12. 自动化测试报告、人工验收记录和遗留问题清单。

任务只有在以下条件全部满足后才算完成：

- 原毕业项目始终未被修改。
- GitHub 与服务器均使用经过测试的同一提交。
- 本地业务数据和上传文件已完整迁移并通过核验。
- 超级管理员权限字符已统一为 `cptbtptp`，登录用户名未被误改。
- 账号授权取代旧卡密和机器绑定，权限在后端强制校验。
- 周四至周日免费逻辑严格留在客户端本地。
- 两个桌面端 v1.1.0 可运行，v1.0.3 可回退。
- 网页、小程序和桌面端共享同一账号与生产后端。
- 服务器密钥、数据库凭据、token、`.env` 和用户数据未进入 Git。
- HTTPS、备份、监控、日志脱敏和回滚均经过实际验证。
