"""
列出数据库中所有表
"""
from app import app
from models import db
from sqlalchemy import inspect

def list_all_tables():
    """列出数据库中所有表"""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"数据库中共有 {len(tables)} 个表:")
        for idx, table in enumerate(sorted(tables), 1):
            print(f"{idx}. {table}")

if __name__ == "__main__":
    list_all_tables() 