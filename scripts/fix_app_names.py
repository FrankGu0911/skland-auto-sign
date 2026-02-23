#!/usr/bin/env python3
"""修复数据库中的 app_name"""

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

def fix_app_names():
    """修复 app_name"""
    db_path = ROOT_DIR / "data" / "skland.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("修复前:")
    cursor.execute("SELECT app_code, app_name FROM skland_characters")
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]}")

    # 更新
    cursor.execute("UPDATE skland_characters SET app_name = '明日方舟' WHERE app_code = 'arknights'")
    cursor.execute("UPDATE skland_characters SET app_name = '终末地' WHERE app_code = 'endfield'")

    conn.commit()

    print("\n修复后:")
    cursor.execute("SELECT app_code, app_name FROM skland_characters")
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]}")

    conn.close()
    print("\n修复完成!")

if __name__ == "__main__":
    fix_app_names()
