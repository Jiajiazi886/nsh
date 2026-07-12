# 服务器 Docker 部署完整指南

本文档说明如何把当前项目部署到宝塔面板服务器上，使用 Docker Compose 启动前端、后端、MySQL 和 Redis。

推荐部署方式：

- 服务器系统：Linux
- 面板：宝塔面板
- Web 服务：宝塔 Nginx
- 应用运行：Docker Compose
- 数据库：Docker MySQL
- 缓存：Docker Redis
- 对外访问：宝塔 Nginx 反向代理到 Docker 前端

## 一、部署前确认

### 1. 本地代码要先推到 GitHub

服务器一般通过 `git clone` 拉代码，所以本地代码需要先推到 GitHub。

当前项目远端是：

```text
https://github.com/Jiajiazi886/nsh.git
```

如果你本地还没推成功，先在本地项目根目录执行：

```bash
git push origin main
```

如果网络连不上 GitHub，服务器部署有两个选择：

1. 等本地能推到 GitHub 后，在服务器 `git clone`。
2. 直接把本地项目压缩上传到服务器。

推荐方式是第 1 种，后续更新最方便。

### 2. 服务器需要安装的软件

在宝塔面板的软件商店安装：

- Docker
- Nginx

如果宝塔没有 Docker Compose 命令，可以 SSH 登录服务器检查：

```bash
docker --version
docker compose version
```

能看到版本号即可。

### 3. 防火墙开放端口

公网只需要开放：

```text
80
443
```

不建议开放：

```text
3306
6379
9099
12580
```

生产配置里的前端只监听服务器本机：

```text
127.0.0.1:12580
```

所以外网不能直接访问 `服务器IP:12580`，需要通过宝塔 Nginx 反向代理访问。

## 二、把代码放到服务器

### 方式 A：从 GitHub 拉取

SSH 登录服务器：

```bash
cd /www/wwwroot
git clone https://github.com/Jiajiazi886/nsh.git RuoYi-Vue3-FastAPI-master
cd RuoYi-Vue3-FastAPI-master
```

如果仓库是私有仓库，服务器需要配置 GitHub 登录或 Personal Access Token。

### 方式 B：手动上传项目

如果 GitHub 暂时推不上去，可以在本地压缩项目，上传到：

```text
/www/wwwroot/RuoYi-Vue3-FastAPI-master
```

注意不要上传这些目录：

```text
.git
ruoyi-fastapi-frontend/node_modules
ruoyi-fastapi-frontend/dist
ruoyi-fastapi-backend/.venv
logs
caches
```

上传后 SSH 进入目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
```

## 三、准备生产环境配置

项目已经提供了生产 Docker 配置：

```text
docker-compose.prod.my.yml
```

生产环境变量模板：

```text
deploy/prod.env.example
```

在服务器复制一份真实配置：

```bash
cp deploy/prod.env.example deploy/prod.env
```

编辑配置：

```bash
nano deploy/prod.env
```

至少修改下面三个值：

```env
MYSQL_ROOT_PASSWORD=换成你的MySQL强密码
REDIS_PASSWORD=换成你的Redis强密码
JWT_SECRET_KEY=换成随机长字符串
```

可以用这个命令生成随机字符串：

```bash
openssl rand -hex 32
```

示例：

```env
MYSQL_ROOT_PASSWORD=5f0e8b1b2d1c9a7e9d0f8c6a12345678
REDIS_PASSWORD=6ac51ddcc22541e5a30e9dcf12345678
JWT_SECRET_KEY=2c586ac79adcc14dc4dff53da7b6a5c7083ff2f724a8bdaf75df63fd59da3333
```

不要把 `deploy/prod.env` 提交到 GitHub。

项目 `.gitignore` 已经忽略：

```text
deploy/prod.env
```

## 四、替换传输加密密钥

正式部署建议替换后端默认的传输加密密钥。

文件位置：

```text
ruoyi-fastapi-backend/.env.dockermy
```

需要替换：

```env
TRANSPORT_CRYPTO_PUBLIC_KEY
TRANSPORT_CRYPTO_PRIVATE_KEY
```

在服务器项目根目录执行：

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out transport_private.pem
openssl rsa -pubout -in transport_private.pem -out transport_public.pem
```

转成 `.env` 可填写的一行格式：

```bash
awk 'NF {sub(/\r/, ""); printf "%s\\\\n",$0;}' transport_private.pem
awk 'NF {sub(/\r/, ""); printf "%s\\\\n",$0;}' transport_public.pem
```

把第一个输出填入：

```env
TRANSPORT_CRYPTO_PRIVATE_KEY='这里放私钥输出'
```

把第二个输出填入：

```env
TRANSPORT_CRYPTO_PUBLIC_KEY='这里放公钥输出'
```

替换完成后可以删除临时密钥文件：

```bash
rm -f transport_private.pem transport_public.pem
```

## 五、启动 Docker 服务

在项目根目录执行：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

这个命令会启动：

- `ruoyi-frontend`
- `ruoyi-backend-my`
- `ruoyi-mysql`
- `ruoyi-redis`

查看容器状态：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml ps
```

正常情况下应该看到容器状态为：

```text
running
healthy
```

查看日志：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml logs -f
```

只看后端日志：

```bash
docker logs -f ruoyi-backend-my
```

只看前端 Nginx 日志：

```bash
docker logs -f ruoyi-frontend
```

## 六、服务器本机测试

因为生产配置只监听 `127.0.0.1:12580`，所以需要在服务器 SSH 里测试：

```bash
curl -I http://127.0.0.1:12580/
```

如果返回类似：

```text
HTTP/1.1 200 OK
```

说明前端容器可以访问。

测试后端代理：

```bash
curl -I http://127.0.0.1:12580/docker-api/
```

后端根路径不一定返回 200，只要不是连接失败即可。

## 七、宝塔面板配置域名

### 1. 新建站点

宝塔面板进入：

```text
网站 -> 添加站点
```

填写你的域名，例如：

```text
example.com
```

站点根目录可以随便选一个空目录，因为实际访问走反向代理。

### 2. 添加反向代理

进入站点设置：

```text
反向代理 -> 添加反向代理
```

目标 URL 填：

```text
http://127.0.0.1:12580
```

发送域名建议填：

```text
$host
```

开启代理后访问：

```text
http://你的域名
```

### 3. 申请 SSL

宝塔站点设置里进入：

```text
SSL -> Let's Encrypt
```

申请证书后，开启：

```text
强制 HTTPS
```

最终访问：

```text
https://你的域名
```

## 八、推荐的宝塔 Nginx 反代配置

如果宝塔自动生成的反代配置不够稳定，可以在站点 Nginx 配置中确认包含类似内容：

```nginx
location / {
    proxy_pass http://127.0.0.1:12580;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

前端容器内部 Nginx 已经配置了：

```text
/docker-api/ -> ruoyi-backend-my:9099
```

所以宝塔只需要整体代理到 `127.0.0.1:12580`，不需要单独再配 `/docker-api`。

## 九、默认账号

项目初始 SQL 通常会创建后台默认账号。

常见默认账号可能是：

```text
admin
admin123
```

如果登录失败，需要查看项目 SQL 文件：

```text
ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

部署成功后请第一时间修改管理员密码。

## 十、更新项目

以后本地开发完成并推到 GitHub 后，在服务器执行：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
git pull
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

如果只改了前端，也可以直接执行同一条命令，Docker 会重新构建前端镜像。

如果只改了后端，也同样执行同一条命令即可。

## 十一、停止和重启

重启全部服务：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml restart
```

停止服务：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml down
```

不要随便执行：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml down -v
```

`-v` 会删除数据卷，可能导致数据库数据丢失。

## 十二、数据卷说明

生产 compose 使用了这些 Docker 数据卷：

```text
ruoyi-mysql-data
ruoyi-redis-data
ruoyi-backend-logs
ruoyi-backend-vf-admin
```

作用：

- `ruoyi-mysql-data`：MySQL 数据
- `ruoyi-redis-data`：Redis 数据
- `ruoyi-backend-logs`：后端日志
- `ruoyi-backend-vf-admin`：后端上传文件、生成文件等运行数据

查看数据卷：

```bash
docker volume ls | grep ruoyi
```

## 十三、备份数据库

进入项目目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
source deploy/prod.env
```

备份 MySQL：

```bash
docker exec ruoyi-mysql mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" ruoyi-fastapi > ruoyi-fastapi-backup-$(date +%F).sql
```

恢复 MySQL：

```bash
source deploy/prod.env
docker exec -i ruoyi-mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" ruoyi-fastapi < ruoyi-fastapi-backup.sql
```

建议定期把备份 SQL 下载到本地或对象存储。

## 十四、常见问题

### 1. `docker compose` 提示找不到 `deploy/prod.env`

先确认文件是否存在：

```bash
ls -l deploy/prod.env
```

如果没有，复制模板：

```bash
cp deploy/prod.env.example deploy/prod.env
```

### 2. 前端访问 502

检查前端容器：

```bash
docker logs -f ruoyi-frontend
```

检查后端容器：

```bash
docker logs -f ruoyi-backend-my
```

检查容器状态：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml ps
```

### 3. 后端连不上数据库

检查 MySQL 是否 healthy：

```bash
docker ps | grep ruoyi-mysql
```

查看 MySQL 日志：

```bash
docker logs -f ruoyi-mysql
```

确认 `deploy/prod.env` 里的 `MYSQL_ROOT_PASSWORD` 没有特殊换行或空格。

### 4. Redis 密码错误

查看 Redis 日志：

```bash
docker logs -f ruoyi-redis
```

测试 Redis：

```bash
source deploy/prod.env
docker exec -it ruoyi-redis redis-cli -a "$REDIS_PASSWORD" ping
```

正常返回：

```text
PONG
```

### 5. 修改了配置但没生效

重新构建并启动：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

如果只改了 `deploy/prod.env`，也可以：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d
```

### 6. GitHub 拉取失败

如果服务器不能访问 GitHub：

1. 在本地打包代码上传服务器。
2. 或者给服务器配置代理。
3. 或者使用 Gitee 镜像仓库。

手动上传时，注意不要覆盖服务器上的：

```text
deploy/prod.env
```

## 十五、完整部署命令速查

第一次部署：

```bash
cd /www/wwwroot
git clone https://github.com/Jiajiazi886/nsh.git RuoYi-Vue3-FastAPI-master
cd RuoYi-Vue3-FastAPI-master
cp deploy/prod.env.example deploy/prod.env
nano deploy/prod.env
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml ps
```

更新部署：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
git pull
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

查看日志：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml logs -f
```

停止服务：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml down
```

## 十六、部署后检查清单

- [ ] `deploy/prod.env` 已修改强密码
- [ ] `docker compose ps` 所有容器正常
- [ ] `curl -I http://127.0.0.1:12580/` 返回 200
- [ ] 宝塔反向代理目标为 `http://127.0.0.1:12580`
- [ ] 域名 HTTPS 可访问
- [ ] 管理员账号可登录
- [ ] 已修改默认管理员密码
- [ ] 已确认服务器防火墙只开放 `80/443`
- [ ] 已安排 MySQL 备份
