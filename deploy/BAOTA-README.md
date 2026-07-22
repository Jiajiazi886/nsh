# 宝塔面板操作说明

此目录已经包含前端、后端、MySQL、Redis 的 Docker 离线镜像。请只在宝塔面板中按下面步骤操作。

## 1. 安装软件

宝塔左侧进入“软件商店”，安装：

```text
Docker 管理器
Nginx
```

然后进入“终端”，执行：

```bash
docker --version
docker compose version
```

两个命令都能显示版本号即可。

## 2. 放行 HTTP 端口

宝塔左侧进入：

```text
安全 → 系统防火墙 → 放行端口
```

放行端口：

```text
80
```

不要放行 `3306`、`6379`、`9099`、`12580`。本次部署不使用 SSL，不需要配置 `443`。

## 3. 上传本目录

在宝塔“文件”中创建目录：

```text
/www/wwwroot/nsh-release/
```

将当前整个发布目录上传到该目录下。例如：

```text
/www/wwwroot/nsh-release/nsh-20260713153000/
```

必须保留以下文件：

```text
images.tar
docker-compose.yml
prod.env
SHA256SUMS.txt
sql/ruoyi-fastapi.sql
```

不要解压 `images.tar`。

## 4. 启动 Docker 容器

进入宝塔“终端”，将下面的目录名替换为实际目录名：

```bash
cd /www/wwwroot/nsh-release/nsh-20260713153000
sha256sum -c SHA256SUMS.txt
docker load -i images.tar
docker compose --env-file prod.env -f docker-compose.yml up -d --remove-orphans
docker compose --env-file prod.env -f docker-compose.yml ps
```

第一次启动后等待约 60 秒，再执行一次：

```bash
docker compose --env-file prod.env -f docker-compose.yml ps
```

应看到 `ruoyi-frontend`、`ruoyi-backend-my`、`ruoyi-mysql`、`ruoyi-redis`；MySQL 和 Redis 状态应为 `healthy`。

## 5. 宝塔 HTTP 反向代理

宝塔左侧进入：

```text
网站 → 添加站点
```

填写域名或服务器公网 IP，PHP 版本选择“纯静态”。创建后进入：

```text
站点设置 → 反向代理 → 添加反向代理
```

填写：

```text
代理名称：nsh
目标 URL：http://127.0.0.1:12580
发送域名：$host
```

保存后直接通过以下地址访问：

```text
http://你的域名
```

或：

```text
http://服务器公网IP
```

不要申请 SSL，不要开启强制 HTTPS。

## 6. 故障检查

在宝塔终端执行：

```bash
docker logs --tail 100 ruoyi-mysql
docker logs --tail 100 ruoyi-redis
docker logs --tail 100 ruoyi-backend-my
docker logs --tail 100 ruoyi-frontend
```

不要运行 `docker compose down -v`，其中的 `-v` 会删除数据库数据。
