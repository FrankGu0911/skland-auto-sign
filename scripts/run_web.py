#!/usr/bin/env python3
"""Web 服务启动脚本

启动带 Web 管理界面的森空岛自动签到服务。
"""

import sys
import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"

# 添加到 Python 路径
sys.path.insert(0, str(SRC_DIR))
os.environ["PYTHONPATH"] = str(SRC_DIR)

import uvicorn

if __name__ == "__main__":
    print("启动森空岛自动签到 Web 服务...")
    print("访问地址: http://localhost:8080")
    print("按 Ctrl+C 停止服务")
    print()

    # 直接导入并运行
    from api.app import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
