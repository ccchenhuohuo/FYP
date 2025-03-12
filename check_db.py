from app import app
from models import db
from sqlalchemy import text

print("检查数据库表结构...")

with app.app_context():
    conn = db.engine.connect()
    
    try:
        # 检查orders表是否有updated_at字段
        result = conn.execute(text("SHOW COLUMNS FROM orders LIKE 'updated_at'"))
        updated_at_exists = result.rowcount > 0
        print(f"updated_at字段是否存在: {updated_at_exists}")
        
        # 检查orders表是否有remark字段
        result = conn.execute(text("SHOW COLUMNS FROM orders LIKE 'remark'"))
        remark_exists = result.rowcount > 0
        print(f"remark字段是否存在: {remark_exists}")
        
    except Exception as e:
        print(f"检查字段时出错: {str(e)}")
    
    conn.close() 