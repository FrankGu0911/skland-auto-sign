#!/bin/bash
# Docker Compose 快速启动脚本

cd "$(dirname "$0")"

echo "启动森空岛自动签到系统..."
echo ""

# 停止并删除旧容器
docker-compose down

# 构建并启动
docker-compose up --build -d

echo ""
echo "服务已启动！"
echo "访问地址: http://localhost:8080"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart"
