# 新版项目前台守护启动脚本

日期：2026-09-15

## 目标

- 双击根目录 BAT，启动独立副本的后端 9101 与网页 5173，并让 CMD 窗口在运行期间一直保留。
- 后端继续通过 `tools/local_activity_dev.py serve` 使用 `nsh_activity_dev_20260914` 和 Redis DB15；不建库、不迁移、不清库。
- 5173 或 9101 已被占用时直接报错，不主动结束未知进程。
- 子服务在守护 CMD 下运行，日志写入 `logs/activity-dev`，启动后轮询认证接口与网页直至成功或超时。
- 关闭守护 CMD 窗口时，通过 Windows Job Object 自动结束前端、后端及其子进程。
- 不打开浏览器，不操作微信开发者工具，不启动原毕业项目。

## 实现

1. 使用纯 ASCII 的 `start-current-project.ps1` 实现单实例检查、健康检查、运行状态监控和失败日志提示；保留中文 PowerShell 文件作为兼容入口。
2. 使用 Windows Job Object 的 `KILL_ON_JOB_CLOSE` 约束前后端进程树，守护进程结束时由系统清理所有子进程。
3. `启动当前项目.bat` 同步调用核心 PowerShell 脚本，不使用 `start` 或脱离窗口的后台启动方式，避免 Windows CMD 与 PowerShell 5.1 编码错误。
4. 增加静态契约测试和生命周期测试；验证两个地址返回 HTTP 200，并验证终止守护进程后 5173、9101 自动释放。
