"""
直接清理数据库冗余表 - 无需交互确认

此脚本会删除数据库中的冗余表和备份表，包括：
1. 各种备份表（以backup命名的表）
2. 已被新功能替代的表（如deposit和withdrawal已被fund_transaction替代）
3. 命名不规范的表（如order表已被orders替代）

注意：此脚本会直接执行删除操作，不会请求确认。
"""

from app import app
from models import db
from sqlalchemy import text, inspect
import sys

# 需要保留的表（当前活跃使用的表）
TABLES_TO_KEEP = [
    'user',              # 用户表
    'admin',             # 管理员表
    'account_balance',   # 账户余额表
    'fund_transaction',  # 资金交易表（充值/提现）
    'orders',            # 订单表
    'transaction',       # 交易记录表
    'portfolio',         # 用户持仓表
    'market_data',       # 市场数据表
    'fundamental_data',  # 基本面数据表
    'balance_sheet',     # 资产负债表
    'income_statement'   # 利润表
]

def run_cleanup():
    """执行数据库清理"""
    print("开始清理数据库冗余表...")
    
    with app.app_context():
        # 获取所有表
        inspector = inspect(db.engine)
        all_tables = inspector.get_table_names()
        print(f"数据库中共有 {len(all_tables)} 个表")
        
        # 确定要删除的表（不在保留列表中的表）
        tables_to_delete = [table for table in all_tables if table not in TABLES_TO_KEEP]
        
        if not tables_to_delete:
            print("没有需要删除的表。")
            return True
        
        print(f"\n将删除以下 {len(tables_to_delete)} 个表:")
        for idx, table in enumerate(tables_to_delete, 1):
            print(f"{idx}. {table}")
        
        # 执行删除操作
        conn = db.engine.connect()
        
        # 暂时禁用外键约束检查
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        try:
            for table in tables_to_delete:
                print(f"正在删除表 '{table}'...")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            
            # 提交事务
            db.session.commit()
            print("\n所有冗余表已成功删除!")
            
            # 列出保留的表
            print("\n保留的表:")
            for idx, table in enumerate(TABLES_TO_KEEP, 1):
                if table in all_tables:
                    print(f"{idx}. {table}")
                    
            return True
            
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            print(f"删除表时出错: {str(e)}")
            return False
            
        finally:
            # 恢复外键约束检查
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.close()

if __name__ == "__main__":
    success = run_cleanup()
    sys.exit(0 if success else 1) 