# ==============================================================================
# Stage 1: 构建前端 (Build Frontend)
# ==============================================================================
FROM node:18-alpine AS build-frontend

# 设置前端工作目录
WORKDIR /app

# 复制前端依赖文件并安装
COPY package.json package-lock.json* ./
RUN npm install

# 复制前端源码
COPY . .

# 构建前端 (生成 dist 目录)
RUN npm run build


# ==============================================================================
# Stage 2: 构建后端并整合 (Setup Backend + Serve Static Files)
# ==============================================================================
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (PDF处理相关)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装后端依赖
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# 复制后端代码
COPY backend/ ./

# 从第一阶段复制构建好的前端静态文件到后端的 static 目录
COPY --from=build-frontend /app/dist /app/static

# 创建必要的数据目录
RUN mkdir -p /app/data /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HTTP_HOST=0.0.0.0 \
    HTTP_PORT=8080

# 暴露端口 (Cloud Run 使用的端口)
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"

# 启动命令
# 使用 gunicorn 运行 aiohttp 应用
CMD exec python main.py
