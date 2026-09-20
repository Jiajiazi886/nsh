# 构建阶段
FROM node:22-slim AS builder
WORKDIR /app

# 复制源代码
COPY . .

# 设置npm镜像源
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖。package-lock.json 由 Windows 生成时，npm 可能漏装 Rollup 的
# Linux 可选原生包（npm/cli#4828），因此在容器内显式补齐当前平台包。
RUN npm install \
    && npm install --no-save @rollup/rollup-linux-x64-gnu@4.63.3

# 执行docker构建命令
RUN npm run build:docker

# 运行阶段
FROM nginx:latest
WORKDIR /usr/share/nginx/html

# 复制构建产物
COPY --from=builder /app/dist .

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
