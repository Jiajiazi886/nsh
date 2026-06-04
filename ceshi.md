这个项目建议开两个 PowerShell 终端，一个跑后端，一个跑前端。

**后端**

```powershell
cd E:\nsh\nshls\RuoYi-Vue3-FastAPI-master\ruoyi-fastapi-backend

.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

.\.venv\Scripts\ruoyi.exe app doctor --env=dev --output=json

.\.venv\Scripts\ruoyi.exe app run --env=dev
```

后端默认地址一般是：

```text
http://localhost:9099
```

接口文档通常可以看：

```text
http://localhost:9099/docs
```

如果没有 `.venv`，先创建虚拟环境：

```powershell
cd E:\nsh\nshls\RuoYi-Vue3-FastAPI-master\ruoyi-fastapi-backend

py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

**前端**

另开一个 PowerShell：

```powershell
cd E:\nsh\nshls\RuoYi-Vue3-FastAPI-master\ruoyi-fastapi-frontend

npm.cmd install

npm.cmd run dev -- --host 0.0.0.0 --port 8080
```

然后浏览器打开：

```text
http://localhost:8080
```

需要注意：后端依赖 MySQL 和 Redis，配置在后端的 `.env.dev` 里。前端的 `/dev-api` 会代理到后端 `http://localhost:9099`，所以后端要先正常启动。停止服务就在两个终端里分别按 `Ctrl+C`。