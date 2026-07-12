# 小白教程：不用 Docker 手动部署到宝塔服务器

这份教程适合你不想用 Docker，或者 Docker 部署失败时的备用方案。

手动部署比 Docker 麻烦，因为你要自己安装和配置：

```text
MySQL
Redis
Python
Node.js
Nginx
```

但好处是宝塔面板里看得比较直观。

## 0. 手动部署的运行结构

手动部署后，结构是：

```text
宝塔 Nginx：对外提供网站
前端 dist：放在 Nginx 网站目录
后端 Python：监听 127.0.0.1:9099
MySQL：宝塔安装的 MySQL
Redis：宝塔安装的 Redis
```

访问链路：

```text
浏览器 -> 域名 -> 宝塔 Nginx -> 前端页面
浏览器 -> 域名/prod-api -> 宝塔 Nginx -> 后端 127.0.0.1:9099
```

## 1. 宝塔安装软件

打开宝塔面板。

点击左侧：

```text
软件商店
```

安装这些软件：

```text
Nginx
MySQL 8.0
Redis
Node.js 版本管理器
Python 项目管理器
```

如果没有 Python 项目管理器，也没关系，后面用命令启动。

## 2. 准备项目目录

假设你的项目已经下载到：

```text
/www/wwwroot/RuoYi-Vue3-FastAPI-master
```

SSH 进入服务器：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
```

确认能看到：

```bash
ls
```

应该有：

```text
ruoyi-fastapi-backend
ruoyi-fastapi-frontend
```

## 3. 宝塔创建 MySQL 数据库

宝塔面板左侧点击：

```text
数据库
```

点击：

```text
添加数据库
```

填写：

```text
数据库名：ruoyi-fastapi
用户名：ruoyi_fastapi
密码：自己生成一个强密码
访问权限：本地服务器
```

字符集选择：

```text
utf8mb4
```

记住这三个值：

```text
数据库名
用户名
密码
```

后面要写进后端配置。

## 4. 导入数据库 SQL

项目 SQL 文件是：

```text
ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

### 方法 A：用宝塔 phpMyAdmin

宝塔左侧：

```text
数据库
```

找到 `ruoyi-fastapi`，点击：

```text
管理
```

进入 phpMyAdmin 后：

```text
选择数据库 ruoyi-fastapi -> 导入 -> 选择文件 -> 执行
```

选择这个文件：

```text
/www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

### 方法 B：用命令导入

如果你知道 MySQL 密码，也可以命令导入：

```bash
mysql -u ruoyi_fastapi -p ruoyi-fastapi < /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

回车后输入数据库密码。

## 5. 启动 Redis

宝塔面板左侧：

```text
软件商店 -> Redis -> 设置
```

确认 Redis 已启动。

手动检查：

```bash
redis-cli ping
```

正常返回：

```text
PONG
```

如果你给 Redis 设置了密码，记住密码，后面要写入 `.env.prod`。

## 6. 配置后端生产环境

编辑后端生产配置：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend
nano .env.prod
```

重点修改这些：

```env
APP_ENV = 'prod'
APP_ROOT_PATH = '/prod-api'
APP_HOST = '127.0.0.1'
APP_PORT = 9099
APP_RELOAD = false
APP_DISABLE_SWAGGER = true
APP_DISABLE_REDOC = true

JWT_SECRET_KEY = '换成随机长字符串'

DB_TYPE = 'mysql'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USERNAME = 'ruoyi_fastapi'
DB_PASSWORD = '你在宝塔创建数据库时设置的密码'
DB_DATABASE = 'ruoyi-fastapi'
DB_ECHO = false

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_USERNAME = ''
REDIS_PASSWORD = ''
REDIS_DATABASE = 2
```

如果 Redis 设置了密码：

```env
REDIS_PASSWORD = '你的Redis密码'
```

生成 JWT 随机字符串：

```bash
openssl rand -hex 32
```

保存：

```text
Ctrl + O
回车
Ctrl + X
```

## 7. 安装后端 Python 环境

进入后端目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend
```

确认 Python 版本：

```bash
python3 --version
```

推荐 Python：

```text
3.10 或 3.11
```

创建虚拟环境：

```bash
python3 -m venv .venv
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

升级 pip：

```bash
pip install -U pip
```

安装依赖：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果安装很慢，可以等；第一次会比较久。

## 8. 测试启动后端

还是在后端目录：

```bash
source .venv/bin/activate
python app.py --env=prod
```

如果没有报错，另开一个终端测试：

```bash
curl -I http://127.0.0.1:9099/docs
```

因为 `.env.prod` 里默认禁用了 Swagger，`/docs` 可能不是 200。只要后端没有报数据库或 Redis 错误就可以。

按：

```text
Ctrl + C
```

停止测试运行。

## 9. 用 systemd 后台运行后端

创建服务文件：

```bash
nano /etc/systemd/system/ruoyi-backend.service
```

粘贴下面内容：

```ini
[Unit]
Description=RuoYi FastAPI Backend
After=network.target mysql.service redis.service

[Service]
Type=simple
WorkingDirectory=/www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend
ExecStart=/www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend/.venv/bin/python app.py --env=prod
Restart=always
RestartSec=5
Environment=PYTHONUTF8=1
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
```

保存后执行：

```bash
systemctl daemon-reload
systemctl enable ruoyi-backend
systemctl start ruoyi-backend
```

查看状态：

```bash
systemctl status ruoyi-backend
```

查看日志：

```bash
journalctl -u ruoyi-backend -f
```

退出日志：

```text
Ctrl + C
```

## 10. 安装前端 Node 依赖

宝塔软件商店安装：

```text
Node.js 版本管理器
```

选择安装：

```text
Node.js 18 或 Node.js 20
```

SSH 检查：

```bash
node -v
npm -v
```

进入前端目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-frontend
```

设置 npm 镜像：

```bash
npm config set registry https://registry.npmmirror.com
```

安装依赖：

```bash
npm install
```

## 11. 配置前端生产接口

查看文件：

```bash
nano .env.production
```

确认这里是：

```env
VITE_APP_BASE_API = '/prod-api'
```

保存退出。

## 12. 打包前端

进入前端目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-frontend
```

执行：

```bash
npm run build:prod
```

成功后会生成：

```text
ruoyi-fastapi-frontend/dist
```

## 13. 宝塔创建前端网站

宝塔面板左侧：

```text
网站 -> 添加站点
```

域名填写你的域名。

PHP 版本选择：

```text
纯静态
```

网站根目录设置为：

```text
/www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-frontend/dist
```

如果宝塔添加站点时不方便直接选 dist，先创建站点，然后进站点设置改根目录。

## 14. 配置宝塔 Nginx

进入网站设置：

```text
配置文件
```

找到 `server { ... }`，在里面加入下面配置。

如果你不确定放哪里，就放在 `server` 大括号里面，其他 `location` 旁边。

```nginx
location / {
    try_files $uri $uri/ /index.html;
}

location /prod-api/ {
    proxy_pass http://127.0.0.1:9099/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

保存。

点击宝塔里的：

```text
重载配置
```

或者 SSH 执行：

```bash
nginx -t
systemctl reload nginx
```

## 15. 申请 HTTPS

宝塔网站设置：

```text
SSL -> Let's Encrypt
```

申请证书。

申请成功后开启：

```text
强制 HTTPS
```

访问：

```text
https://你的域名
```

## 16. 测试网站

浏览器打开：

```text
https://你的域名
```

登录后台。

如果前端能打开，但登录失败，检查接口：

```bash
curl -I https://你的域名/prod-api/
```

再看后端日志：

```bash
journalctl -u ruoyi-backend -f
```

## 17. 后续更新项目

进入项目目录：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master
git pull
```

### 如果改了后端

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
systemctl restart ruoyi-backend
```

### 如果改了前端

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-frontend
npm install
npm run build:prod
systemctl reload nginx
```

### 如果前后端都改了

两段都执行。

## 18. 常用命令

查看后端状态：

```bash
systemctl status ruoyi-backend
```

重启后端：

```bash
systemctl restart ruoyi-backend
```

查看后端日志：

```bash
journalctl -u ruoyi-backend -f
```

检查 Nginx 配置：

```bash
nginx -t
```

重载 Nginx：

```bash
systemctl reload nginx
```

检查端口：

```bash
ss -lntp | grep -E '9099|3306|6379|80|443'
```

## 19. 常见问题

### 问题 1：后端启动失败

看日志：

```bash
journalctl -u ruoyi-backend -n 100
```

常见原因：

- `.env.prod` 数据库密码写错。
- MySQL 没启动。
- Redis 没启动。
- Python 依赖没安装完整。

### 问题 2：前端打开空白

重新打包：

```bash
cd /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-frontend
npm run build:prod
```

确认宝塔网站根目录是：

```text
ruoyi-fastapi-frontend/dist
```

### 问题 3：刷新页面 404

Nginx 缺少：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 问题 4：登录接口 404

确认前端 `.env.production`：

```env
VITE_APP_BASE_API = '/prod-api'
```

确认 Nginx 有：

```nginx
location /prod-api/ {
    proxy_pass http://127.0.0.1:9099/;
}
```

确认后端 `.env.prod`：

```env
APP_ROOT_PATH = '/prod-api'
APP_PORT = 9099
```

### 问题 5：数据库没有表

说明 SQL 没导入。

重新导入：

```bash
mysql -u ruoyi_fastapi -p ruoyi-fastapi < /www/wwwroot/RuoYi-Vue3-FastAPI-master/ruoyi-fastapi-backend/sql/ruoyi-fastapi.sql
```

## 20. 手动部署检查清单

- [ ] 宝塔已安装 Nginx
- [ ] 宝塔已安装 MySQL
- [ ] 宝塔已安装 Redis
- [ ] 宝塔已安装 Node.js
- [ ] 服务器有 Python 3.10 或 3.11
- [ ] MySQL 已创建 `ruoyi-fastapi` 数据库
- [ ] 已导入 `ruoyi-fastapi.sql`
- [ ] `.env.prod` 数据库密码正确
- [ ] `.env.prod` Redis 配置正确
- [ ] 后端 `.venv` 已创建
- [ ] 后端依赖已安装
- [ ] `ruoyi-backend.service` 已启动
- [ ] 前端依赖已安装
- [ ] 前端已 `npm run build:prod`
- [ ] 宝塔网站根目录指向 `ruoyi-fastapi-frontend/dist`
- [ ] Nginx 已配置 `/prod-api/` 代理
- [ ] HTTPS 已申请成功
