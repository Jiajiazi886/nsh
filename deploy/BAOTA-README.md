# 宝塔离线部署说明（使用宝塔 MySQL 8）

本发布包已在本地完成前端打包、后端镜像构建和 Redis 镜像下载。服务器不需要安装 Node.js、Python、pip，也不会执行 `docker build`。

GitHub 仓库保存源码、Dockerfile 和构建脚本；由于 `images.tar` 超过 GitHub 普通仓库的 100 MB 单文件限制，真正可直接运行的镜像包由本地 `Prepare-OfflineRelease.ps1` 生成后手动上传。服务器不能只克隆 GitHub 仓库就跳过镜像包。

发布脚本支持在 Docker Hub 暂时不可用时复用上一版本地 Linux 镜像作为构建基础。Dockerfile 会先清空旧应用目录，再写入当前提交的前端和后端文件，避免旧业务文件残留。

Docker 只运行三个容器：前端、后端和 Redis。业务数据库使用服务器上由宝塔管理的 MySQL 8，不在 Docker 容器中。

网站地址：`http://www.xn--kbrr2vyxjytebq4azkrrie.icu/`

管理员初始账号：`cptbtptp369`
管理员初始密码：`cptbtptp369`

本次部署只使用 HTTP，不申请 SSL，不开启强制 HTTPS。

## 1. 宝塔准备

在宝塔软件商店安装：

```text
Docker 管理器
Nginx
MySQL 8.0
```

在宝塔终端执行：

```bash
docker --version
docker compose version
uname -m
```

`uname -m` 必须为 `x86_64`，才能使用本离线包的 `linux/amd64` 镜像。

在宝塔的“安全 -> 系统防火墙”中只放行 `80` 端口。不要放行 `3306`、`6379`、`9099`、`12580`。

## 2. 上传发布包

在宝塔文件管理器创建：

```text
/www/wwwroot/nsh-release/
```

将整个离线发布目录上传到其中，例如：

```text
/www/wwwroot/nsh-release/nsh-发布标签/
```

必须保留以下文件和目录：

```text
images.tar
docker-compose.yml
prod.env
BUILD-INFO.txt
site-config.example.env
SHA256SUMS.txt
sql/ruoyi-fastapi.sql
sql/20260725_reset_admin_credentials.sql
BAOTA-README.md
```

不要解压 `images.tar`，也不要把 `prod.env` 上传到公开的网站目录。

进入上传目录后，先核对文件完整性：

```bash
cd /www/wwwroot/nsh-release/nsh-发布标签
sha256sum -c SHA256SUMS.txt
```

所有行都显示 `OK` 才继续。

## 3. 创建宝塔 MySQL 数据库

本包中的 `prod.env` 已生成应用数据库账号 `nsh_app` 和随机密码。先在宝塔终端查看该密码：

```bash
grep '^MYSQL_HOST\|^MYSQL_PORT\|^MYSQL_DATABASE\|^MYSQL_USERNAME\|^MYSQL_PASSWORD\|^DOCKER_NETWORK_SUBNET' prod.env
```

默认值为：

```text
数据库名：ruoyi-fastapi
数据库用户：nsh_app
数据库密码：以 prod.env 中 MYSQL_PASSWORD 的实际值为准
Docker 网段：172.28.0.0/16
```

### 3.1 允许 Docker 访问本机 MySQL

在宝塔“软件商店 -> MySQL 8.0 -> 配置修改”中，确认 `[mysqld]` 下存在：

```ini
bind-address = 0.0.0.0
```

保存后重启 MySQL。虽然 MySQL 会监听 Docker 网桥，但防火墙没有放行 `3306`，且下面的应用账号只允许 Docker 网段连接，公网无法使用此账号登录。

### 3.2 创建数据库、账号并导入结构

在宝塔终端进入 MySQL：

```bash
mysql -uroot -p
```

将下面 `这里替换为 prod.env 里的 MYSQL_PASSWORD` 替换成刚才查到的真实密码，然后依次执行：

```sql
CREATE DATABASE `ruoyi-fastapi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER 'nsh_app'@'172.28.%' IDENTIFIED BY '这里替换为 prod.env 里的 MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON `ruoyi-fastapi`.* TO 'nsh_app'@'172.28.%';
FLUSH PRIVILEGES;
EXIT;
```

导入项目数据库结构和初始数据：

```bash
mysql -h 127.0.0.1 -uroot -p ruoyi-fastapi < sql/ruoyi-fastapi.sql
```

如果服务器已有同名数据库，不要再次导入全量 SQL；请先备份，再按需要迁移数据。

## 4. 导入镜像并启动 Docker

仍在发布目录执行：

```bash
sudo systemctl enable --now docker
docker load -i images.tar
docker compose --env-file prod.env -f docker-compose.yml up -d --remove-orphans
docker compose --env-file prod.env -f docker-compose.yml ps
```

`systemctl is-enabled docker` 必须返回 `enabled`。三个服务均使用 `restart: always`，Docker 服务和服务器重新启动后都会自动恢复。

等待约 30 秒后检查：

```bash
docker compose --env-file prod.env -f docker-compose.yml ps
curl -I http://127.0.0.1:12580/
```

应看到 `ruoyi-frontend`、`ruoyi-backend-my`、`ruoyi-redis` 三个容器；Redis 应为 `healthy`，HTTP 检查应返回 `200`。

检查镜像确实来自本次 Git 提交：

```bash
cat BUILD-INFO.txt
docker image inspect "nsh-frontend:$(grep '^APP_IMAGE_TAG=' prod.env | cut -d= -f2)" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'
docker image inspect "nsh-backend-my:$(grep '^APP_IMAGE_TAG=' prod.env | cut -d= -f2)" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}'
```

两个镜像输出的提交号必须与 `BUILD-INFO.txt` 中的 `SOURCE_COMMIT` 完全一致。

若后端无法连接数据库，查看日志：

```bash
docker logs --tail 200 ruoyi-backend-my
```

重点检查 MySQL 的 `bind-address`、数据库账号授权的 `172.28.%` 网段，以及 `prod.env` 中的 `MYSQL_*` 值。

## 5. 宝塔网站与反向代理

进入宝塔“网站 -> 添加站点”：

```text
域名：www.xn--kbrr2vyxjytebq4azkrrie.icu
PHP版本：纯静态
```

创建后进入“站点设置 -> 反向代理 -> 添加反向代理”：

```text
代理名称：nsh
目标 URL：http://127.0.0.1:12580
发送域名：$host
```

保存并重载 Nginx 后访问：

```text
http://www.xn--kbrr2vyxjytebq4azkrrie.icu/
```

不要在站点中申请 SSL，也不要启用强制 HTTPS。

## 6. 上线后配置 AI Key 与模型

首次登录后进入：

```text
系统管理 -> AIKey管理
```

填写图片识别 API Key 并保存。该 Key 会加密存入宝塔 MySQL，不在 `prod.env` 或离线包中保存。

模型的访问地址、模型名称、超时和输出长度位于发布目录的 `prod.env`：

```env
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
MIMO_TIMEOUT_SECONDS=60
MIMO_MAX_COMPLETION_TOKENS=2048
```

修改这四项后执行：

```bash
docker compose --env-file prod.env -f docker-compose.yml up -d --force-recreate ruoyi-backend-my
```

`MIMO_API_KEY` 请保持为空；运行中的图片识别只读取 AIKey 管理页面保存的 Key。

## 7. 已有数据库时重置管理员

新建并导入数据库后，管理员账号和密码已经是 `cptbtptp369`。如需重置已有数据库中的管理员，在发布目录执行：

```bash
mysql -h 127.0.0.1 -uroot -p ruoyi-fastapi < sql/20260725_reset_admin_credentials.sql
docker compose --env-file prod.env -f docker-compose.yml restart ruoyi-backend-my
```

## 8. 常用维护命令

```bash
# 查看状态
docker compose --env-file prod.env -f docker-compose.yml ps

# 查看后端日志
docker logs --tail 200 ruoyi-backend-my

# 重启 Docker 服务，不影响宝塔 MySQL 数据
docker compose --env-file prod.env -f docker-compose.yml restart

# 停止 Docker 服务
docker compose --env-file prod.env -f docker-compose.yml stop

# 启动已停止的 Docker 服务
docker compose --env-file prod.env -f docker-compose.yml start

# 检查 Docker 开机启动与容器重启策略
systemctl is-enabled docker
docker inspect ruoyi-frontend ruoyi-backend-my ruoyi-redis --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}'
```

重启策略输出必须全部为 `always`。首次部署完成后可以执行一次重启演练：

```bash
sudo reboot
```

服务器恢复后再次执行 `docker compose ... ps` 和 `curl -I http://127.0.0.1:12580/`，确认无需人工启动即可恢复服务。

不要执行 `docker compose down -v`。虽然 MySQL 已不在 Docker 中，但该命令会删除 Redis 和项目上传数据卷。
