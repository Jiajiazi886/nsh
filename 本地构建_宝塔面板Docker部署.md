# 宝塔面板部署指南：本地构建 + 手动上传 + Docker

本项目采用**本地构建、服务器只运行**的部署方式。

- 前端 `npm install`、`npm run build` 在本地完成。
- 后端 `pip install` 在本地 Docker 构建时完成。
- MySQL、Redis 镜像也在本地下载后一起导出。
- 服务器只执行 `docker load` 和 `docker compose up -d`。
- 本指南只使用 HTTP，不配置 SSL/HTTPS。

这样可以避免低配置服务器在打包或安装依赖时内存不足、构建失败。

## 0. 发布流程总览

```text
本地生成生产配置
    ↓
本地构建前端、后端、MySQL、Redis 镜像
    ↓
导出 images.tar 离线包
    ↓
宝塔文件管理器手动上传整个发布目录
    ↓
服务器导入镜像并启动容器
    ↓
宝塔 Nginx 用 HTTP 80 端口反向代理到 127.0.0.1:12580
```

## 1. 本地检查 Docker

在项目根目录打开 PowerShell，执行：

```powershell
docker version
docker info --format '{{.OSType}}/{{.Architecture}}'
```

正常结果应包含：

```text
linux/amd64
```

这表示 Docker Desktop 已启动且处于 Linux 容器模式。本项目已经验证过本机 Docker 为 `linux/amd64`。

如果服务器终端执行 `uname -m` 返回：

- `x86_64`：使用后面的默认构建命令。
- `aarch64`：构建时追加 `-Platform linux/arm64`。

## 2. 本地生产配置

生产配置文件是：

```text
deploy/prod.env
```

它保存 MySQL、Redis、JWT、RSA 加密密钥，已被 Git 忽略，不能提交到 GitHub。

首次生成时运行：

```powershell
.\deploy\New-ProductionEnv.ps1
```

本项目已生成该文件。若需要使用 AI 内功图片识别，编辑该文件并填写：

```env
MIMO_API_KEY=你的真实API密钥
```

不使用 AI 识别时，`MIMO_API_KEY` 可以留空。

## 3. 本地构建离线发布包

确保 Docker Desktop 正在运行，执行：

```powershell
.\deploy\Prepare-OfflineRelease.ps1
```

如果服务器是 ARM 架构，执行：

```powershell
.\deploy\Prepare-OfflineRelease.ps1 -Platform linux/arm64
```

脚本会完成：

1. 本地打包 Vue 前端。
2. 本地构建 FastAPI 后端镜像。
3. 本地拉取 MySQL 8.0 和 Redis 7 镜像。
4. 导出完整离线包到 `deploy/releases/nsh-时间戳/`。

生成目录中必须有：

```text
images.tar
docker-compose.yml
prod.env
SHA256SUMS.txt
sql/ruoyi-fastapi.sql
```

`images.tar` 较大是正常现象；它包含了服务器不需要再下载或构建的全部镜像。

## 4. 宝塔面板准备

### 4.1 宝塔防火墙

进入宝塔面板：

```text
安全 → 系统防火墙 → 放行端口
```

只需放行：

```text
80     HTTP 网站访问
```

不用 SSL 时不需要配置 `443`。不要放行以下端口：

```text
3306   MySQL
6379   Redis
9099   后端接口
12580  Docker 前端内部端口
```

### 4.2 安装 Docker 和 Nginx

进入宝塔面板：

```text
软件商店 → Docker 管理器 → 安装
软件商店 → Nginx → 安装
```

安装完成后，在宝塔终端执行：

```bash
docker --version
docker compose version
```

两个命令都能输出版本号即可。服务器不需要安装 Node.js、Python、MySQL 或 Redis。

### 4.3 检查服务器架构

在宝塔终端执行：

```bash
uname -m
```

通常服务器会输出 `x86_64`。若输出 `aarch64`，必须回到本地，按第 3 节 ARM 命令重新打包。

## 5. 手动上传发布包

在宝塔文件管理器中创建目录：

```text
/www/wwwroot/nsh-release/
```

将本地生成的整个目录上传到这里，例如：

```text
本地：deploy/releases/nsh-20260713153000/
服务器：/www/wwwroot/nsh-release/nsh-20260713153000/
```

必须上传整个目录，尤其不能遗漏：

```text
images.tar
docker-compose.yml
prod.env
SHA256SUMS.txt
sql/ruoyi-fastapi.sql
```

上传时不要解压 `images.tar`，它会直接由 Docker 导入。

## 6. 服务器启动项目

在宝塔终端中执行。下面的目录名替换为你实际上传的目录名：

```bash
cd /www/wwwroot/nsh-release/nsh-20260713153000
```

先检查文件是否上传完整：

```bash
ls -lh
ls -lh sql
```

校验文件未损坏：

```bash
sha256sum -c SHA256SUMS.txt
```

所有文件应显示 `OK`。然后导入镜像：

```bash
docker load -i images.tar
```

启动容器：

```bash
docker compose --env-file prod.env -f docker-compose.yml up -d --remove-orphans
```

查看状态：

```bash
docker compose --env-file prod.env -f docker-compose.yml ps
```

第一次启动时 MySQL 需要初始化，等 30 到 60 秒后再执行一次 `ps`。正常时应看到：

```text
ruoyi-frontend
ruoyi-backend-my
ruoyi-mysql
ruoyi-redis
```

并且 MySQL、Redis 显示 `healthy`。

## 7. 服务器本机验证

在服务器终端执行：

```bash
curl -I http://127.0.0.1:12580/
```

返回 `HTTP/1.1 200 OK` 表示 Docker 前端已启动。

若失败，按顺序查看日志：

```bash
docker logs --tail 100 ruoyi-mysql
docker logs --tail 100 ruoyi-redis
docker logs --tail 100 ruoyi-backend-my
docker logs --tail 100 ruoyi-frontend
```

## 8. 宝塔 Nginx 配置 HTTP 访问

进入宝塔：

```text
网站 → 添加站点
```

域名填写你的域名；没有域名时可填服务器公网 IP。PHP 版本选择“纯静态”。

进入站点：

```text
设置 → 反向代理 → 添加反向代理
```

填写：

```text
代理名称：nsh
目标 URL：http://127.0.0.1:12580
发送域名：$host
```

保存即可。不要申请 SSL，也不要开启强制 HTTPS。

最后使用浏览器访问：

```text
http://你的域名
```

或：

```text
http://服务器公网IP
```

## 9. 后续更新

每次修改代码后按以下顺序操作：

1. 本地重新执行 `Prepare-OfflineRelease.ps1`。
2. 用宝塔手动上传新生成的 `nsh-时间戳` 目录。
3. 在服务器新目录执行第 6 节的四条命令。

数据库、Redis、后端日志和上传文件使用固定 Docker 数据卷保存，更新发布包不会清空数据。

**不要执行下面的命令：**

```bash
docker compose down -v
```

其中 `-v` 会删除 MySQL 和 Redis 数据卷。

## 10. 数据库备份

在服务器发布目录执行：

```bash
cd /www/wwwroot/nsh-release/nsh-你的时间戳
set -a && . ./prod.env && set +a
docker exec ruoyi-mysql mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" > backup-$(date +%F).sql
```

将生成的备份文件从宝塔下载到本地保存。
