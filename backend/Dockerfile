# 使用 Python 3.10 轻量版
FROM python:3.10-slim

WORKDIR /app

# 安装系统库
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有代码
COPY . .

# 暴露端口
EXPOSE 8000

# 核心修复：直接通过 uvicorn 启动，并强制绑定 0.0.0.0
# 移除 reload 模式，在生产环境更稳定
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
