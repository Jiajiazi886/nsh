# 宝塔面板部署：本地构建，服务器直接运行

本项目采用固定部署方式：

- Windows 本地完成 Vue 前端打包。
- Windows Docker Desktop 构建 Linux/amd64 前端、FastAPI 后端镜像。
- Redis 镜像一并导出到 `images.tar`。
- 服务器使用宝塔 MySQL 8，MySQL 不放进 Docker。
- Linux 服务器不执行 `npm install`、`npm build`、`pip install` 或 `docker build`。
- Docker 与三个应用容器都设置为开机自动启动。
- 网站仅使用 HTTP，域名为 `www.xn--kbrr2vyxjytebq4azkrrie.icu`。

## 1. GitHub 与离线包的区别

GitHub 仓库保存源码、Dockerfile、Compose 和构建脚本。`images.tar` 约数百 MB，超过 GitHub 普通仓库 100 MB 的单文件限制，因此不会提交到 Git。

服务器真正直接运行所需的文件由本地脚本生成：

```text
deploy/releases/nsh-发布标签/
```

生成后将整个目录手动上传到宝塔。服务器只需校验、导入镜像并启动容器。

## 2. 本地构建

先确认 Docker Desktop 使用 Linux 容器：

```powershell
docker info --format '{{.OSType}}/{{.Architecture}}'
```

应输出 `linux/x86_64` 或等价的 `linux/amd64` 信息。

生产配置在 `deploy/prod.env`，该文件包含数据库、Redis、JWT 和 RSA 密钥，已经被 Git 忽略。首次使用时执行：

```powershell
.\deploy\New-ProductionEnv.ps1
```

确认配置后提交所有需要发布的代码。构建脚本会拒绝存在未提交的跟踪文件，确保镜像能够对应一个准确的 Git 提交。

构建 Linux/amd64 离线包：

```powershell
.\deploy\Prepare-OfflineRelease.ps1 -Tag 20260811-baota -Platform linux/amd64
```

如果 Docker Hub 暂时无法连接，但本机已经加载过上一版离线镜像，可以完全复用本地镜像层：

```powershell
.\deploy\Prepare-OfflineRelease.ps1 `
  -Tag 20260811-baota `
  -Platform linux/amd64 `
  -UseLocalBaseImages `
  -FrontendBaseImage nsh-frontend:上一版标签 `
  -BackendBaseImage nsh-backend-my:上一版标签
```

Dockerfile 会先清空旧应用目录，再复制当前前端 `dist` 和后端源码；旧版本业务文件不会残留。Python 依赖已包含在上一版后端镜像中，只有当前依赖清单新增包时才需要恢复网络拉取。

脚本会完成：

1. 执行前端 `npm run build:docker`。
2. 将前端 `dist` 放入 Nginx 镜像。
3. 将后端源码和 Python 依赖放入 FastAPI 镜像。
4. 准备 Redis 7 镜像。
5. 生成 `images.tar`、Compose、生产环境文件、SQL、校验和与 `BUILD-INFO.txt`。
6. 给前后端镜像写入 Git 提交号和 UTC 构建时间标签。

## 3. 上传清单

将整个发布目录上传到：

```text
/www/wwwroot/nsh-release/nsh-发布标签/
```

必须包含：

```text
images.tar
docker-compose.yml
prod.env
BUILD-INFO.txt
SHA256SUMS.txt
BAOTA-README.md
site-config.example.env
sql/ruoyi-fastapi.sql
sql/20260725_reset_admin_credentials.sql
```

不要把 `prod.env`、私密 OpenCode 提示词或 API Key 提交到 GitHub。

## 4. 宝塔服务器准备

宝塔软件商店安装：

```text
Docker 管理器
Nginx
MySQL 8.0
```

在宝塔终端执行：

```bash
uname -m
docker --version
docker compose version
sudo systemctl enable --now docker
systemctl is-enabled docker
```

服务器架构必须是 `x86_64`，最后一个命令必须输出 `enabled`。

公网只放行 80 端口，不放行 3306、6379、9099、12580。

## 5. 使用宝塔 MySQL 8

在宝塔 MySQL 中创建：

```text
数据库：ruoyi-fastapi
用户：nsh_app
密码：与发布目录 prod.env 中 MYSQL_PASSWORD 相同
允许来源：Docker 网段 172.28.%
```

MySQL 需要监听 Docker 网桥可访问的地址，但 3306 不得向公网放行。首次部署导入：

```bash
mysql -h 127.0.0.1 -uroot -p ruoyi-fastapi < sql/ruoyi-fastapi.sql
```

如果数据库已有业务数据，必须先备份，不能重复导入全量初始化 SQL。

## 6. 服务器直接启动

进入上传目录：

```bash
cd /www/wwwroot/nsh-release/nsh-发布标签
sha256sum -c SHA256SUMS.txt
docker load -i images.tar
docker compose --env-file prod.env -f docker-compose.yml up -d --remove-orphans
docker compose --env-file prod.env -f docker-compose.yml ps
```

服务器不会构建任何代码。正常情况下只有三个项目容器：

```text
ruoyi-frontend
ruoyi-backend-my
ruoyi-redis
```

检查本机访问：

```bash
curl -I http://127.0.0.1:12580/
```

应返回 HTTP 200。

## 7. 自动启动验证

Compose 中三个服务均使用 `restart: always`。检查：

```bash
systemctl is-enabled docker
docker inspect ruoyi-frontend ruoyi-backend-my ruoyi-redis --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}'
```

Docker 应为 `enabled`，三个容器都应显示 `always`。首次部署后执行一次：

```bash
sudo reboot
```

重启完成后复查：

```bash
docker compose --env-file prod.env -f docker-compose.yml ps
curl -I http://127.0.0.1:12580/
```

无需人工执行 `docker compose up` 即可恢复，才算通过。

## 8. 宝塔 Nginx

在宝塔添加纯静态站点：

```text
www.xn--kbrr2vyxjytebq4azkrrie.icu
```

新增反向代理：

```text
目标：http://127.0.0.1:12580
发送域名：$host
```

不申请 SSL，不开启强制 HTTPS。最终访问：

```text
http://www.xn--kbrr2vyxjytebq4azkrrie.icu/
```

更详细的逐项命令以离线包中的 `BAOTA-README.md` 和本地私密文件 `OpenCode服务器部署系统提示词_不上传GitHub.md` 为准。
