# Git 结构说明 / Git Structure Guide

这份文件给新手看，用来理解当前项目为什么要用 Git、Git 里每个区域是什么意思，以及以后开发功能时应该怎么保存版本。

This file is for beginners. It explains why this project uses Git, what each Git area means, and how to save work safely when developing future features.

## 1. 当前项目位置 / Current Project Location

项目根目录 / project root:

```text
E:\nsh\nshls\RuoYi-Vue3-FastAPI-master
```

这个目录下面有一个隐藏文件夹：

```text
.git
```

`.git` 就是 Git 的“仓库数据库”。它保存提交历史、分支信息、暂存区信息等。平时不要手动删除或修改它。

`.git` is Git's internal repository database. It stores commit history, branches, staging data, and other metadata. Do not edit or delete it manually.

## 2. 当前分支 / Current Branch

当前项目使用的分支是：

```text
master
```

分支 / branch：可以理解为一条开发线。现在我们是在 `master` 上开发。以后如果想更安全，可以为每个功能开一个新分支，例如：

```text
codex/personal-profile-edit
codex/battle-review
codex/guild-schedule
```

A branch is a separate line of development. The current branch is `master`. For safer work, each feature can use its own branch, such as `codex/personal-profile-edit`.

## 3. Git 的三个核心区域 / Three Core Git Areas

### 工作区 / Working Tree

工作区就是你电脑上真实看到的文件，例如：

```text
ruoyi-fastapi-backend/
ruoyi-fastapi-frontend/
README.md
数据库.md
```

你改代码、写文档、删除文件，都是先发生在工作区。

The working tree is the real files on your computer. Code edits, document changes, and file deletions happen here first.

### 暂存区 / Staging Area

暂存区是“准备提交的清单”。执行下面命令会把文件放进暂存区：

```powershell
git add 文件名
git add -A
```

`git add -A` 的意思是把所有新增、修改、删除都加入暂存区。

The staging area is the list of changes prepared for the next commit. `git add -A` stages all additions, edits, and deletions.

### 提交历史 / Commit History

提交 / commit 是一个版本快照。执行：

```powershell
git commit -m "提交说明"
```

Git 会把暂存区里的内容保存成一个历史版本。以后可以查看、对比、回退。

A commit is a saved snapshot. It records the staged changes so you can inspect, compare, or restore them later.

## 4. 常用命令 / Common Commands

查看当前状态 / check status:

```powershell
git status
```

查看简洁状态 / short status:

```powershell
git status --short --branch
```

查看改了什么 / view changes:

```powershell
git diff
```

暂存全部改动 / stage all changes:

```powershell
git add -A
```

提交一个版本 / create a commit:

```powershell
git commit -m "feat: add personal profile edit"
```

查看提交历史 / view commit history:

```powershell
git log --oneline --decorate -10
```

## 5. 提交信息怎么写 / How To Write Commit Messages

推荐格式 / recommended format:

```text
类型: 做了什么
type: what changed
```

常见类型 / common types:

| 类型 / Type | 中文含义 | English meaning | 示例 / Example |
| --- | --- | --- | --- |
| `feat` | 新功能 | new feature | `feat: add personal profile edit` |
| `fix` | 修复问题 | bug fix | `fix: correct member profile route` |
| `docs` | 文档 | documentation | `docs: add database structure guide` |
| `refactor` | 重构 | code restructure without behavior change | `refactor: simplify member service` |
| `chore` | 杂项维护 | maintenance task | `chore: update git notes` |

## 6. 推荐开发流程 / Recommended Workflow

每次开发一个功能，建议按这个顺序：

1. 先看状态 / check status

```powershell
git status --short --branch
```

2. 开始写代码 / edit code

修改前端、后端、SQL 或文档。

Edit frontend, backend, SQL, or documentation files.

3. 测试 / test

例如本项目常用：

```powershell
cd E:\nsh\nshls\RuoYi-Vue3-FastAPI-master\ruoyi-fastapi-backend
.\.venv\Scripts\python.exe -m py_compile module_guild\controller\member_controller.py
```

```powershell
cd E:\nsh\nshls\RuoYi-Vue3-FastAPI-master\ruoyi-fastapi-frontend
npm.cmd run build:stage
```

4. 查看改动 / review changes

```powershell
git diff
```

5. 暂存 / stage

```powershell
git add -A
```

6. 提交 / commit

```powershell
git commit -m "feat: add personal profile edit"
```

## 7. 当前项目的目录结构 / Current Project Folder Structure

```text
RuoYi-Vue3-FastAPI-master/
├─ .git/                         Git 仓库数据 / Git repository data
├─ ruoyi-fastapi-backend/         后端 FastAPI 项目 / FastAPI backend
│  ├─ module_admin/               系统管理模块 / system admin module
│  ├─ module_guild/               帮会业务模块 / guild business module
│  ├─ sql/                        数据库脚本 / database scripts
│  └─ app.py                      后端启动入口之一 / backend app entry
├─ ruoyi-fastapi-frontend/        前端 Vue3 项目 / Vue 3 frontend
│  ├─ src/api/                    前端接口封装 / API wrappers
│  ├─ src/views/                  页面组件 / page components
│  └─ package.json                前端脚本和依赖 / frontend scripts and dependencies
├─ ruoyi-fastapi-test/            自动化测试项目 / automated tests
├─ 数据库.md                      数据库结构文档 / database structure document
└─ Git结构说明.md                 Git 说明文档 / Git guide
```

## 8. 什么文件应该提交 / What Should Be Committed

应该提交 / commit these:

```text
后端代码 / backend code
前端代码 / frontend code
SQL 脚本 / SQL migration scripts
项目文档 / project documents
配置模板 / config examples
```

一般不要提交 / usually do not commit:

```text
node_modules/
dist/
.venv/
日志文件 / log files
本地临时文件 / local temporary files
真实密码或密钥 / real passwords or secrets
```

这些通常由 `.gitignore` 控制。

These are usually controlled by `.gitignore`.

## 9. 小白版理解 / Beginner Mental Model

可以把 Git 想成游戏存档：

- 工作区 / Working tree：你正在玩的当前画面。
- 暂存区 / Staging area：你准备放进下一个存档的内容。
- 提交 / Commit：真正保存下来的一个存档点。
- 分支 / Branch：另一条独立进度线。
- 合并 / Merge：把一条进度线的成果合到另一条进度线。

Think of Git like game saves:

- Working tree: what you are currently changing.
- Staging area: what you plan to save next.
- Commit: the saved checkpoint.
- Branch: another independent development line.
- Merge: combining work from one line into another.

## 10. 本项目建议 / Recommendation For This Project

以后每做完一个完整小功能，就提交一次：

```powershell
git add -A
git commit -m "feat: 功能名称"
```

如果只是改文档：

```powershell
git add -A
git commit -m "docs: update database and git guide"
```

这样做的好处是：后面如果某个功能出问题，可以快速定位是哪一次提交引入的。

The benefit is simple: if a feature breaks later, you can quickly find which commit introduced the problem.
