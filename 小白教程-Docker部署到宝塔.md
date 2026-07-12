# 小白教程：用 Docker 把项目部署到宝塔服务器

这份教程适合第一次用 Docker 的人。你已经完成的状态是：

```text
GitHub 项目已经下载到服务器上了
```

下面从这里继续。

## 0. 先记住这个逻辑

Docker 部署时，你不用手动安装 Python、Node、MySQL、Redis。

Docker 会帮你启动 4 个容器：

```text
前端容器：ruoyi-frontend
后端容器：ruoyi-backend-my
数据库容器：ruoyi-mysql
缓存容器：ruoyi-redis
```

宝塔只做两件事：

1. 安装 Docker。
2. 用 Nginx 把你的域名转发到 Docker 前端。

## 1. 宝塔面板安装 Docker

打开宝塔面板。

点击左边菜单：

```text
软件商店
```

搜索：

```text
Docker
```

安装：

```text
Docker 管理器
```

如果宝塔提示安装 Docker Compose，也一起安装。

安装完成后，SSH 登录服务器，检查：

```bash
docker --version
docker compose version
```

看到版本号就说明安装好了。

## 2. 进入项目目录

宝塔左侧点：

```text
终端
```

或者用 Xshell / FinalShell / WindTerm 连接服务器。

进入你已经下载好的项目目录。

如果你的项目在 `/www/wwwroot/RuoYi-Vue3-FastAPI-master`：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
```

确认目录里有这些文件：

```bash
ls
```

应该能看到：

```text
docker-compose.prod.my.yml
deploy
ruoyi-fastapi-backend
ruoyi-fastapi-frontend
```

如果没有 `docker-compose.prod.my.yml`，说明服务器代码不是最新的，需要先更新代码。

## 3. 创建生产配置文件

执行：

```bash
cp deploy/prod.env.example deploy/prod.env
```

然后编辑：

```bash
nano deploy/prod.env
```

你会看到类似内容：

```env
FRONTEND_PORT=12580

MYSQL_DATABASE=ruoyi-fastapi
MYSQL_ROOT_PASSWORD=CHANGE_ME_mysql_root_password

REDIS_PASSWORD=CHANGE_ME_redis_password

JWT_SECRET_KEY=CHANGE_ME_64_hex_or_long_random_string
```

至少把这三个 `CHANGE_ME` 改掉：

```env
MYSQL_ROOT_PASSWORD=你的MySQL密码
REDIS_PASSWORD=你的Redis密码
JWT_SECRET_KEY=你的JWT随机密钥
```

不会生成随机字符串的话，执行：

```bash
openssl rand -hex 32
```

执行一次复制给 `MYSQL_ROOT_PASSWORD`，再执行一次复制给 `REDIS_PASSWORD`，再执行一次复制给 `JWT_SECRET_KEY`。

示例：

```env
MYSQL_ROOT_PASSWORD=0d0e54c9cf52b23e6af491cc7f0f5c3a
REDIS_PASSWORD=b46d883f6cdb1af32c4d973171f20f90
JWT_SECRET_KEY=9d9e8d1f14de47a83a5db8f19cc82879bfb8c56b41333a9e314af1d8f91c5a2d
```

保存：

```text
Ctrl + O
回车
Ctrl + X
```

## 4. 启动 Docker 项目

还是在项目根目录执行：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

第一次会比较慢，因为要下载镜像、安装依赖、打包前端。

等待完成后，查看状态：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml ps
```

你应该能看到这些服务：

```text
ruoyi-frontend
ruoyi-backend-my
ruoyi-mysql
ruoyi-redis
```

状态最好是：

```text
running
healthy
```

## 5. 如果启动失败，先看日志

看全部日志：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml logs -f
```

只看后端日志：

```bash
docker logs -f ruoyi-backend-my
```

只看前端日志：

```bash
docker logs -f ruoyi-frontend
```

只看 MySQL 日志：

```bash
docker logs -f ruoyi-mysql
```

只看 Redis 日志：

```bash
docker logs -f ruoyi-redis
```

退出日志：

```text
Ctrl + C
```

## 6. 服务器本机测试

Docker 生产配置为了安全，只让前端监听服务器本机：

```text
127.0.0.1:12580
```

所以你不能直接用浏览器访问：

```text
http://服务器IP:12580
```

你要在服务器终端里测试：

```bash
curl -I http://127.0.0.1:12580/
```

看到：

```text
HTTP/1.1 200 OK
```

说明 Docker 前端启动成功。

再测试接口代理：

```bash
curl -I http://127.0.0.1:12580/docker-api/
```

这个地址不一定返回 200，只要不是连接失败，就说明 Nginx 能找到 Docker 前端。

## 7. 宝塔添加网站

打开宝塔面板。

点击左侧：

```text
网站
```

点击：

```text
添加站点
```

填写你的域名，例如：

```text
example.com
```

PHP 版本可以选：

```text
纯静态
```

提交。

## 8. 宝塔设置反向代理

进入你刚刚创建的网站。

点击：

```text
设置
```

找到：

```text
反向代理
```

点击：

```text
添加反向代理
```

填写：

```text
代理名称：ruoyi
目标 URL：http://127.0.0.1:12580
发送域名：$host
```

保存。

现在访问：

```text
http://你的域名
```

如果页面打开了，说明宝塔反代成功。

## 9. 宝塔申请 HTTPS

网站设置里找到：

```text
SSL
```

选择：

```text
Let's Encrypt
```

申请证书。

申请成功后打开：

```text
强制 HTTPS
```

以后访问：

```text
https://你的域名
```

## 10. 后续更新项目

以后你本地改完代码，推到 GitHub 后，在服务器执行：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
git pull
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

## 11. 重启项目

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml restart
```

## 12. 停止项目

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml down
```

不要执行：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml down -v
```

因为 `-v` 会删除数据库数据。

## 13. 备份数据库

进入项目目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
source deploy/prod.env
```

备份：

```bash
docker exec ruoyi-mysql mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" ruoyi-fastapi > ruoyi-fastapi-backup-$(date +%F).sql
```

备份文件会出现在项目根目录。

## 14. 最常见问题

### 问题 1：`deploy/prod.env not found`

说明你没复制配置文件。

执行：

```bash
cp deploy/prod.env.example deploy/prod.env
```

### 问题 2：网页打不开

先看容器：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml ps
```

再看前端：

```bash
curl -I http://127.0.0.1:12580/
```

如果这里都打不开，是 Docker 没起来。

如果这里能打开，但域名打不开，是宝塔反向代理没配好。

### 问题 3：登录接口失败

看后端日志：

```bash
docker logs -f ruoyi-backend-my
```

看 MySQL 是否健康：

```bash
docker logs -f ruoyi-mysql
```

### 问题 4：Docker 面板按钮不会用

最简单的方式是：

```text
宝塔只负责安装 Docker 和配置网站反代
真正启动项目用终端命令
```

你不需要在宝塔 Docker 页面里点复杂的“创建容器”按钮，因为本项目已经有 `docker-compose.prod.my.yml`，一条命令就能创建全部容器。

## 15. Docker 部署检查清单

- [ ] 宝塔已安装 Docker
- [ ] 项目目录里有 `docker-compose.prod.my.yml`
- [ ] 已创建 `deploy/prod.env`
- [ ] 已修改 `MYSQL_ROOT_PASSWORD`
- [ ] 已修改 `REDIS_PASSWORD`
- [ ] 已修改 `JWT_SECRET_KEY`
- [ ] 已执行 `docker compose ... up -d --build`
- [ ] `docker compose ps` 看到 4 个容器
- [ ] `curl -I http://127.0.0.1:12580/` 返回 200
- [ ] 宝塔网站已添加反向代理到 `http://127.0.0.1:12580`
- [ ] HTTPS 已申请成功
