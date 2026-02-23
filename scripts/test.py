#!/usr/bin/env python3
"""测试脚本 - 添加测试账号并同步角色"""

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
from models import User, Character
from sqlalchemy import select


async def add_test_account():
    """添加测试账号"""
    await db.init()

    async with db.get_session() as session:
        # 检查是否已有用户
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()

        if users:
            print(f"数据库中已有 {len(users)} 个用户:")
            for user in users:
                print(f"  - {user.name} (enabled={user.enabled})")
                # 查看角色
                char_stmt = select(Character).where(Character.user_id == user.id)
                char_result = await session.execute(char_stmt)
                chars = char_result.scalars().all()
                print(f"    角色: {len(chars)} 个")
                for char in chars:
                    print(f"      - {char.nickname} ({char.app_name})")
        else:
            print("数据库中没有用户")
            print("\n请通过 Web 界面添加账号: http://localhost:8080")
            print("或在 config/accounts.yaml 中配置账号")

    await db.close()


if __name__ == "__main__":
    asyncio.run(add_test_account())
