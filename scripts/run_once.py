#!/usr/bin/env python3
"""单次运行脚本

执行一次签到，不启动定时任务。
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

import asyncio
import argparse
from main import SklandAutoSign


async def run_once(game_type: str = "all"):
    """运行一次签到

    Args:
        game_type: 游戏类型 ("arknights", "endfield", "all")
    """
    app = SklandAutoSign()
    await app.run_once(game_type)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="森空岛自动签到 - 单次运行")
    parser.add_argument(
        "--game",
        choices=["arknights", "endfield", "all"],
        default="all",
        help="游戏类型 (默认: all)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_once(args.game))
    except KeyboardInterrupt:
        print("\n操作已取消")
