#!/usr/bin/env python3
"""数据库初始化脚本

初始化数据库并创建表结构。
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
from database import db
from models import User, Character, SignRecord
from utils import setup_logger
from utils.logger import logger


async def init_database():
    """初始化数据库"""
    setup_logger()
    logger.info("开始初始化数据库...")

    # 确保数据目录存在
    data_dir = ROOT_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"数据目录: {data_dir}")

    await db.init()

    # 验证表是否创建
    db_path = data_dir / "skland.db"
    if db_path.exists():
        logger.info(f"数据库文件已创建: {db_path}")
        logger.info(f"数据库大小: {db_path.stat().st_size} bytes")
    else:
        logger.error("数据库文件未创建!")

    logger.info("数据库初始化完成")
    await db.close()


async def create_test_user():
    """创建测试用户"""
    setup_logger()
    await db.init()

    from sqlalchemy import select

    async with db.get_session() as session:
        # 检查是否已有用户
        stmt = select(User).limit(1)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"数据库中已有用户: {existing.name}")
        else:
            logger.info("数据库中没有用户")
            logger.info("请通过 Web 界面添加账号: http://localhost:8080")

    await db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="森空岛自动签到 - 数据库初始化")
    parser.add_argument("--check", action="store_true", help="检查用户")

    args = parser.parse_args()

    try:
        if args.check:
            asyncio.run(create_test_user())
        else:
            asyncio.run(init_database())
    except KeyboardInterrupt:
        print("\n操作已取消")
