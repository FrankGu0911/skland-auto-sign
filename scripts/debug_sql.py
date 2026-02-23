"""添加 SQL 调试的数据库配置"""

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
from sqlalchemy import select


async def test_query():
    """测试查询"""
    await db.init()

    async with db.get_session() as session:
        # 启用 SQL echo
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

        print("\n=== 测试查询用户 ===")
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()

        print(f"找到 {len(users)} 个用户:")
        for user in users:
            print(f"  - ID: {user.id}, Name: {user.name}")

    await db.close()


if __name__ == "__main__":
    asyncio.run(test_query())
