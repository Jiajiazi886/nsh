# 逆水寒帮会管理系统

这是一个面向逆水寒帮会日常管理的后台系统。项目基于 `RuoYi-Vue3-FastAPI` 二次开发，保留了原有的用户、角色、菜单、权限、日志等后台基础能力，并在此基础上扩展了帮会成员、职业、分团、约战、审核、排表等业务功能。

当前仓库已经被整理为新的初始项目，后续开发以本仓库的 `main` 分支为主线，通过 Git 和 GitHub 管理版本。

仓库地址：[https://github.com/Jiajiazi886/nsh.git](https://github.com/Jiajiazi886/nsh.git)

## 项目定位

本系统主要用于帮会管理人员维护成员资料、审核成员申请、管理职业信息、安排约战排表，并通过角色权限控制不同用户能看到和操作的功能。

适用场景：

- 帮会成员资料管理
- 帮会加入申请审核
- 约战报名与约战审核
- 约战排表和分团管理
- 职业信息与职业颜色维护
- 用户、角色、菜单、日志等后台权限管理

## 技术栈

### 前端

- Vue 3
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios
- ECharts

前端目录：

```text
ruoyi-fastapi-frontend/
```

### 后端

- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic
- MySQL
- Redis
- JWT / OAuth2

后端目录：

```text
ruoyi-fastapi-backend/
```

### 测试与辅助目录

```text
ruoyi-fastapi-test/
```

## 主要功能

### 系统管理

- 用户管理：维护系统登录用户、用户状态、用户角色。
- 角色管理：配置角色权限、菜单权限、数据权限。
- 菜单管理：维护系统菜单、按钮权限和路由配置。
- 字典管理：维护系统通用字典数据。
- 参数设置：维护系统运行参数。
- 通知公告：发布和管理系统公告。
- 操作日志：查看用户操作记录。
- 登录日志：查看登录记录和异常登录信息。

### 帮会管理

- 帮会信息：维护帮会基础资料。
- 成员管理：维护帮会成员、职业、副职、备注等信息。
- 成员审核：审核用户提交的加入帮会申请。
- 职业信息：维护职业基础资料，供成员和约战功能使用。
- 职业颜色设置：维护职业显示颜色。
- 分团管理：管理团队、小队和成员排布。
- 约战管理：创建约战、生成临时报名链接。
- 约战审核：审核约战报名信息。
- 约战排表：将通过审核的成员加入约战排表，用于分团安排。
- 数据分析：查看帮会相关统计数据。

### 个人管理

- 加入帮会：普通用户提交加入帮会申请。
- 内功管理：维护个人内功相关信息。
- 个人信息编辑：普通用户维护自己的主职业、副职、备注等资料。

### 公开页面

- 约战邀请链接：未登录用户也可以通过临时链接进入报名页面。
- 公开报名：用户可选择加入帮会或提交约战报名。

## 本地启动

### 1. 启动后端

进入后端目录：

```powershell
cd ruoyi-fastapi-backend
```

如果已经创建好虚拟环境并安装依赖，可以直接启动：

```powershell
.\.venv\Scripts\ruoyi.exe app run --env=dev
```

后端默认地址：

```text
http://localhost:9099
```

接口文档地址：

```text
http://localhost:9099/docs
```

### 2. 启动前端

进入前端目录：

```powershell
cd ruoyi-fastapi-frontend
```

安装依赖：

```powershell
npm install --registry=https://registry.npmmirror.com
```

启动开发服务：

```powershell
npm run dev
```

前端默认地址：

```text
http://localhost:8080
```

### 3. 数据库和 Redis

本地开发需要准备：

- MySQL
- Redis

开发环境配置文件位于：

```text
ruoyi-fastapi-backend/.env.dev
```

注意：`.env.*` 文件属于本地环境配置，不应该提交到 GitHub。

## Docker 部署

项目保留了 Docker 相关配置，后续可以用于服务器部署。

MySQL 版本编排文件：

```text
docker-compose.my.yml
```

PostgreSQL 版本编排文件：

```text
docker-compose.pg.yml
```

常见部署思路：

1. 在服务器安装 Docker 和 Docker Compose。
2. 拉取 GitHub 仓库代码。
3. 准备生产环境配置。
4. 使用 Docker Compose 启动前端、后端、数据库和 Redis。
5. 配置域名和 Nginx 反向代理。

## Git 和 GitHub 开发流程

当前主分支：

```text
main
```

以后开发新功能时，建议从 `main` 创建新分支：

```powershell
git switch main
git pull
git switch -c codex/功能名
```

开发完成后提交：

```powershell
git status
git add -A
git commit -m "feat: 功能说明"
```

推送到 GitHub：

```powershell
git push -u origin codex/功能名
```

如果只是很小的文档修改，也可以直接在 `main` 上提交并推送。

## 文件说明

```text
README.md
```

项目首页说明文档。

```text
数据库.md
```

数据库表结构和字段说明。

```text
Git结构说明.md
```

给新手看的 Git 结构和操作说明。

```text
docker-compose.my.yml
docker-compose.pg.yml
```

Docker 编排文件。

```text
ruoyi-fastapi-backend/
```

后端代码。

```text
ruoyi-fastapi-frontend/
```

前端代码。

```text
ruoyi-fastapi-test/
```

测试代码。

## 注意事项

- 不要提交 `.env.*`、`.venv`、`node_modules`、`dist`、`logs` 等本地环境文件。
- 修改功能前先确认当前分支和 Git 状态。
- 每完成一个稳定功能点就提交一次。
- 推送 GitHub 前先检查是否包含账号、密码、数据库连接等敏感信息。
- 服务器部署时不要直接使用开发环境密码。

## 项目状态

项目仍在持续开发中。当前版本已经具备后台基础权限、帮会管理、成员管理、职业管理、约战审核、约战排表和个人信息维护等核心模块，后续功能会继续通过 Git 和 GitHub 进行版本管理。
