FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# 创建数据目录
RUN mkdir -p data/logs

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV TZ=Asia/Shanghai

# 暴露端口（Web 管理界面）
EXPOSE 8080

# 使用启动脚本
CMD ["bash", "docker/entrypoint.sh"]
