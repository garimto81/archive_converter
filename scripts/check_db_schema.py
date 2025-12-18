"""
NAS DB 스키마 확인 스크립트
"""
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
NAS_DB = PROJECT_ROOT / "data" / "nas_footage.db"

conn = sqlite3.connect(str(NAS_DB))
cursor = conn.cursor()

# 테이블 목록
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("테이블 목록:")
for table in tables:
    print(f"  - {table[0]}")

# 각 테이블의 스키마
for table in tables:
    table_name = table[0]
    print(f"\n{table_name} 테이블 스키마:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # 샘플 데이터
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
    rows = cursor.fetchall()
    print(f"\n샘플 데이터 (2건):")
    for row in rows:
        print(f"  {row}")

conn.close()
