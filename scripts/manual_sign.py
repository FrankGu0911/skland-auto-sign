#!/usr/bin/env python3
"""手动测试签到脚本"""

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
from database import db
from models import User
from core.sign_service import sign_all_users
from utils import setup_logger
from utils.logger import logger


async def main():
    """主函数"""
    setup_logger()

    await db.init()

    async with db.get_session() as session:
        print("\n" + "="*50)
        print("开始执行签到测试")
        print("="*50 + "\n")

        results = await sign_all_users(session, "all", auto_sync=True)

        for user_name, result in results.items():
            print(f"\n{result.summary}")
            for nickname, detail in result.details.items():
                print(f"  {nickname}: {detail}")

    print("\n" + "="*50)
    print("签到测试完成")
    print("="*50 + "\n")

    await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n操作已取消")
