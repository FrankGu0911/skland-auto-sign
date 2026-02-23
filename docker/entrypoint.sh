#!/bin/bash
# 森空岛自动签到系统 - Docker 容器启动脚本

set -e

echo "=========================================="
echo "  森空岛自动签到系统"
echo "=========================================="
echo ""

# 设置环境变量
export PYTHONPATH=/app/src

# 检查 .env 文件是否存在
if [ -f "/app/.env" ]; then
    echo "加载环境变量配置..."
    export $(cat /app/.env | grep -v '^#' | xargs)
else
    echo "警告: .env 文件不存在，请确保已配置账号信息"
fi

# 检查数据库是否存在
if [ ! -f "/app/data/skland.db" ]; then
    echo "数据库不存在，正在初始化..."
    python /app/scripts/init_db.py
    echo "数据库初始化完成"
    echo ""
else
    echo "数据库已存在，跳过初始化"
    echo ""
fi

# 启动 Web 服务
echo "启动 Web 服务..."
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务"
echo ""
echo "=========================================="
echo ""

# 启动服务
exec python /app/scripts/run_web.py
