#!/bin/bash
# 停止服务脚本

cd "$(dirname "$0")"

echo "停止森空岛自动签到系统..."
docker-compose down

echo "服务已停止"
