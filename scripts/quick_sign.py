#!/usr/bin/env python3
"""快速签到测试脚本"""

import sys
import os
from pathlib import Path

# 设置 UTF-8 编码输出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"

# 添加到 Python 路径
sys.path.insert(0, str(SRC_DIR))
os.environ["PYTHONPATH"] = str(SRC_DIR)

import asyncio
from database import db
from core.sign_service import sign_all_users
from utils import setup_logger
from utils.logger import logger


async def main():
    """主函数"""
    setup_logger()

    await db.init()

    async with db.get_session() as session:
        print("\n" + "="*50)
        print("开始执行签到")
        print("="*50 + "\n")

        results = await sign_all_users(session, "all", auto_sync=True)

        for user_name, result in results.items():
            print(f"\n用户: {user_name}")
            print(f"总计: {result.total}, 成功: {result.success}, 失败: {result.failed}, 已签到: {result.duplicate}")
            for nickname, detail in result.details.items():
                # 简化输出，移除 emoji
                detail_clean = detail.replace("✅", "[成功]").replace("❌", "[失败]").replace("ℹ️", "[信息]").replace("📦", "")
                print(f"  {nickname}: {detail_clean}")

    print("\n" + "="*50)
    print("签到完成")
    print("="*50 + "\n")

    await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n操作已取消")
