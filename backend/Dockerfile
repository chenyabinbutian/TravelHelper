# 使用 Python 3.10 轻量版
FROM python:3.10-slim

WORKDIR /app

# 安装系统库（ChromaDB 可能需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY . .

# 暴露 FastAPI 端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "app.main"]
