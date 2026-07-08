# 宝塔面板 Docker 部署说明

本文档使用 MySQL 版本部署。生产部署文件为 `docker-compose.prod.my.yml`。

## 1. 服务器准备

在宝塔面板安装：

- Docker
- Nginx

服务器安全组/防火墙只需要开放：

- `80`
- `443`

不需要开放 MySQL、Redis、后端端口。

## 2. 拉取项目

```bash
cd /www/wwwroot
git clone <你的仓库地址> RuoYi-Vue3-FastAPI-master
cd RuoYi-Vue3-FastAPI-master
```

如果已经上传代码，直接进入项目目录即可。

## 3. 准备生产环境变量

```bash
cp deploy/prod.env.example deploy/prod.env
```

编辑 `deploy/prod.env`，至少替换这些值：

```env
MYSQL_ROOT_PASSWORD=换成强密码
REDIS_PASSWORD=换成强密码
JWT_SECRET_KEY=换成随机长字符串
```

可以用下面命令生成随机值：

```bash
openssl rand -hex 32
```

`deploy/prod.env` 已被 `.gitignore` 忽略，不要提交到仓库。

## 4. 替换传输加密密钥

正式部署前建议替换 `ruoyi-fastapi-backend/.env.dockermy` 里的：

```env
TRANSPORT_CRYPTO_PUBLIC_KEY
TRANSPORT_CRYPTO_PRIVATE_KEY
```

生成密钥：

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out transport_private.pem
openssl rsa -pubout -in transport_private.pem -out transport_public.pem
```

转成 `.env` 可写入的单行格式：

```bash
awk 'NF {sub(/\r/, ""); printf "%s\\\\n",$0;}' transport_private.pem
awk 'NF {sub(/\r/, ""); printf "%s\\\\n",$0;}' transport_public.pem
```

将输出分别填入 `.env.dockermy` 对应字段。

## 5. 启动 Docker 服务

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

查看状态：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml ps
```

查看日志：

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml logs -f
```

本机访问测试：

```bash
curl -I http://127.0.0.1:12580/
```

生产配置只监听服务器本机的 `127.0.0.1:12580`，公网不能直接访问 `服务器IP:12580`。请通过宝塔站点反向代理访问。

## 6. 宝塔反向代理

在宝塔面板新建站点，绑定你的域名。

站点反向代理目标填写：

```text
http://127.0.0.1:12580
```

然后在宝塔里申请 SSL。完成后访问：

```text
https://你的域名
```

## 7. 更新项目

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
git pull
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml up -d --build
```

## 8. 停止服务

```bash
docker compose --env-file deploy/prod.env -f docker-compose.prod.my.yml down
```

不要随便加 `-v`，否则会删除数据库和 Redis 数据卷。

## 9. 数据备份

备份 MySQL：

```bash
docker exec ruoyi-mysql mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" ruoyi-fastapi > ruoyi-fastapi-backup.sql
```

如果当前 shell 没有 `MYSQL_ROOT_PASSWORD`，先执行：

```bash
source deploy/prod.env
```
