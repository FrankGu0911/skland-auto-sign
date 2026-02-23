#!/usr/bin/env python3
"""检查数据库表结构"""

import sys
import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"

# 添加到 Python 路径
sys.path.insert(0, str(SRC_DIR))
os.environ["PYTHONPATH"] = str(SRC_DIR)

import sqlite3

def check_schema():
    """检查数据库表结构"""
    db_path = ROOT_DIR / "data" / "skland.db"

    if not db_path.exists():
        print(f"数据库不存在: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("\n=== 数据库表结构 ===\n")

    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for table_name, in tables:
        print(f"\n表: {table_name}")
        print("-" * 50)
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        for col in columns:
            cid, name, type_, notnull, default, pk = col
            pk_str = " (PK)" if pk else ""
            print(f"  {name:20} {type_:15}{' NOT NULL' if notnull else ''}{pk_str}")

    conn.close()


if __name__ == "__main__":
    check_schema()
