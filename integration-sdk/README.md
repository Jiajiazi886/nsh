# 多端接口接入说明（第一阶段）

这是开发阶段接入客户端，不是全量后端交付，也不是已经部署的微信机器人。

当前源码提供统一账号认证与本人报名/请假。组织、完整活动快照、CSV 分析、机器人绑定和可靠通知仍按实施清单推进。调用 capabilities 时以真实能力标志为准，不把 false 当作可调用功能。

## 已实现接口

所有路径相对 API 根地址。旧 /login、/public/battle 等返回保持原成功格式，新版使用以下契约。

安全修正：旧公开 leave/signup 写入口也必须登录并绑定本人；匿名写入不再兼容，旧网页公开表单需要先登录。这不是通过关闭 JWT 来解决的兼容问题。

| 方法 | 路径 | 身份/用途 |
| --- | --- | --- |
| GET | /api/v1/capabilities | 有限公开能力信息 |
| GET | /api/v1/auth/config | 有限公开认证配置 |
| GET | /api/v1/auth/captcha | 原验证码及限流服务 |
| POST | /api/v1/auth/login | JSON 账号密码；原密码、验证码、限流、审计及会话 |
| GET | /api/v1/auth/me | JWT，最小账号 DTO |
| POST | /api/v1/auth/logout | JWT，撤销当前端会话 |
| POST | /api/v1/auth/wechat/login | 暂未配置，明确返回 503；不会信任任意 code |
| POST | /api/v1/invitations/{code}/leave | JWT + 本邀请所属帮会的本人绑定成员 |
| POST | /api/v1/invitations/{code}/signup | 同上；职业取本人已验证成员资料 |

请求头：Authorization: Bearer TOKEN。memberId/userId 等数据库 ID 使用十进制字符串，不使用 JavaScript Number。

登录请求：

```json
{"userName":"账号","password":"密码","code":"验证码","uuid":"验证码编号"}
```

是否需要验证码由 auth/config 和 auth/captcha 的 captchaEnabled 决定。生产使用 HTTPS；HTTP 仅用于受控本机开发。

请假请求：

```json
{"memberId":"9","remark":"请假说明"}
```

报名可增加 playerClass、secondaryClass。不能传 userId/roles/guildId 来指定或提升身份；不能操作他人，即使登录账号是管理员。memberId 必须来自该登录账号的绑定成员，不能按同名自动认领。

```json
{"code":403,"msg":"只能提交登录账号本人的报名或请假","success":false,"requestId":"req_example","data":null,"errorKey":"MEMBER_NOT_OWNER"}
```

HTTP 状态与新版业务状态对应。成功 data 为 null 也是成功。X-Request-ID 与响应 requestId 对应，排错请提供请求号，不提供密码/token。

| HTTP | errorKey 示例 | 处理 |
| --- | --- | --- |
| 401 | AUTH_REQUIRED | 清理失效 token，重新登录 |
| 403 | MEMBER_NOT_OWNER / MEMBER_BINDING_REQUIRED | 检查本人绑定，不能改 ID 绕过 |
| 404 | INVITE_NOT_FOUND | 邀请不存在 |
| 409 | REGISTRATION_EXISTS / INVITE_INACTIVE | 重读状态或更换有效邀请 |
| 422 | VALIDATION_FAILED | 检查字段、字符串 ID 和长度 |
| 429 | RATE_LIMITED | 稍后重试登录/查询，不循环轰炸 |
| 500 | INTERNAL_ERROR | 使用请求号排错；不显示 SQL/服务器详情 |
| 503 | CAPABILITY_DISABLED | 当前能力尚未启用 |

## 网页客户端

JavaScript 客户端零依赖。打包项目可 require javascript/client.js；直接网页 script 引入后使用 window.NshApi。

```javascript
const { createClient, createFetchTransport } = require('./javascript/client.js');
let token = null;
const client = createClient({
  baseUrl: 'https://api.example.invalid/prod-api',
  getToken: () => token,
  transport: createFetchTransport(fetch)
});
// 用户完成验证码后调用 login；不要在源码保存真实账号密码。
const loginResult = await client.login({ userName, password, code, uuid });
token = loginResult.accessToken;
const account = await client.me();
await client.leave(inviteCode, { memberId: boundMemberId, remark: '请假说明' });
```

baseUrl 是 API 根地址，可包含反向代理 /prod-api 或 /dev-api，但不要再包含 /api/v1。示例域名不可访问，部署时自行设置。SDK 不负责保存密码，也不会自动更新、清除或持久化 token。

## 微信小程序客户端

```javascript
const { createClient, createWxTransport } = require('./javascript/client.js');
const client = createClient({
  baseUrl: 'https://你配置的合法服务器域名',
  getToken: () => wx.getStorageSync('accessToken'),
  transport: createWxTransport(wx)
});
client.me().then(account => {
  // 按页面需要显示，职业树和队伍编辑属于后续页面接入。
}).catch(error => {
  // error.status / error.errorKey / error.requestId
});
```

客户端传输适配已做 mock 单元测试，不代表已通过开发者工具或真机网络联调。合法域名、HTTPS 与登录页面由小程序接入阶段配置。

## Python 客户端

把 python/nsh_client.py 放入自己的模块路径；只使用标准库，不需要额外安装依赖。

```python
from nsh_client import ApiClient, ApiError

client = ApiClient(api_root, token_provider=lambda: current_token)
account = client.me()
client.leave(invite_code, bound_member_id, remark='请假说明')
```

Python 客户端是账号 JWT 客户端，不能拿它伪装机器人服务身份。双方客户端均不自动重试业务写操作。

## 内部机器人边界

module_integration/bot_auth.py 已有本系统桥接签名校验原语及测试；尚未连接公开路由、持久化绑定或实际 iLink。因此当前 botTransport=false，没有可声称已经可用的机器人 events/query 服务。

拟内部请求使用 X-Bot-Key-Id、X-Bot-Timestamp、X-Bot-Nonce、X-Bot-Signature。HMAC-SHA256 材料按 UTF-8 编码：

```text
HTTP_METHOD
/internal/bot/v1/具体路径
十进制时间戳
nonce
原始请求 body 的 SHA256 小写十六进制摘要
```

允许 ±300 秒，nonce 使用原子 Redis SET NX EX，保留 601 秒；签名密钥固定 channel/app/botAccount 范围。服务身份不等于系统账号：后续仍须消费一次性绑定挑战、查询耐久绑定，并重新检查账号状态及本人/本帮权限。

这不是微信官方 webhook。实际通道能力、发消息上下文、文件支持和用户身份提取要另行验证；目前不会向真实微信发送消息。

## 验证与部署边界

在独立后端副本目录运行：

```powershell
cd ruoyi-fastapi-backend
.\.venv\Scripts\python.exe tools/run_integration_tests.py tests --ignore=tests/cli --tb=short
.\.venv\Scripts\python.exe tools/export_integration_contract.py
```

JavaScript 单元测试：node --test integration-sdk/javascript/test/client.test.js（从副本项目根目录执行）。生成文件位于副本 .artifacts/integration-contract。

测试显式使用假配置，阻止外部 TCP/DNS，不启动正式 app lifespan，不访问真实 ruoyi/MySQL/Redis/微信。SQLite 证明事务回滚，不证明 MySQL/InnoDB 并发锁效果；目标引擎并发验收仍待完成。CLI 部署/运行测试未纳入本阶段回归。

源码修改没有重启现有服务；无 reload 的运行进程不会自动加载新接口。因此这里描述的是已测试源码，不是当前端口已经部署可用。部署、数据库兼容检查与迁移须另行确认，不能直接将开发测试配置用于正式环境。

完整实施进度：docs/plans/2026-09-13-unified-integration-api-v1-implementation.md。接口目录中的 legacy-only-review-pending 表示已盘点、未完成新版授权适配，不能视作已审计通过。

阶段归档命令：在后端目录先导出契约，再运行 python tools/build_integration_bundle.py。开发 ZIP 仅含 SDK、Postman、契约与本文；完整后端源码及测试仍在独立项目中。manifest 明确 fullObjectiveComplete=false、backendIncluded=false、realWechatVerified=false，并提供每个文件的 SHA256。它不是可直接部署的完整后端包。
