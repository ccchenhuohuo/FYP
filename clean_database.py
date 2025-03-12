"""
数据库清理脚本 - 删除冗余和备份表

此脚本用于清理数据库中的冗余表、备份表和废弃表，
只保留当前models.py中定义的活跃表。

用法:
python clean_database.py           # 交互模式，会提示确认
python clean_database.py --force   # 强制模式，直接删除冗余表
"""
from app import app
from models import db
from sqlalchemy import text, inspect
import sys

# 当前模型中定义的表名（活跃表）
ACTIVE_TABLES = [
    'user',              # 用户表
    'admin',             # 管理员表
    'account_balance',   # 账户余额表
    'fund_transaction',  # 资金交易表（充值/提现）
    'orders',            # 订单表（注意：表名是复数形式）
    'transaction',       # 交易记录表
    'portfolio',         # 用户持仓表
    'market_data',       # 市场数据表
    'fundamental_data',  # 基本面数据表
    'balance_sheet',     # 资产负债表
    'income_statement'   # 利润表
]

# 已知的备份表和废弃表
KNOWN_BACKUP_TABLES = [
    'deposit_backup_1741777423',
    'deposit_backup_1741777450',
    'user_backup_1741777423',
    'user_backup_1741777450',
    'withdrawal_backup_1741777423',
    'withdrawal_backup_1741777450',
    'deposit',           # 已被fund_transaction替代
    'withdrawal',        # 已被fund_transaction替代
    'order'              # 已被orders替代
]

def get_all_tables():
    """获取数据库中的所有表"""
    with app.app_context():
        inspector = inspect(db.engine)
        return inspector.get_table_names()

def print_tables_info(tables_list, title):
    """打印表列表信息"""
    print(f"\n{title} ({len(tables_list)}):")
    for idx, table in enumerate(tables_list, 1):
        print(f"{idx}. {table}")

def confirm_deletion(tables_to_delete):
    """确认删除操作"""
    if not tables_to_delete:
        print("没有需要删除的表。")
        return False
        
    print_tables_info(tables_to_delete, "将要删除的表")
    
    while True:
        confirm = input("\n警告: 此操作将永久删除上述表及其数据且无法恢复!\n确认删除这些表吗? (yes/no): ").strip().lower()
        if confirm == "yes":
            return True
        elif confirm == "no":
            return False
        else:
            print("请输入 'yes' 或 'no'")

def delete_tables(tables_to_delete):
    """删除指定的表"""
    with app.app_context():
        conn = db.engine.connect()
        
        # 暂时禁用外键约束检查
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        try:
            for table in tables_to_delete:
                print(f"正在删除表 '{table}'...")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            
            # 提交事务
            db.session.commit()
            print("\n所有指定的表已成功删除!")
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

def get_tables_to_delete():
    """确定需要删除的表"""
    # 获取所有表
    all_tables = get_all_tables()
    
    # 确定要删除的表
    tables_to_delete = []
    
    # 添加确定的备份和废弃表
    for table in KNOWN_BACKUP_TABLES:
        if table in all_tables:
            tables_to_delete.append(table)
    
    # 寻找其他可能的备份表（包含'backup'字样）
    for table in all_tables:
        if 'backup' in table.lower() and table not in tables_to_delete:
            tables_to_delete.append(table)
    
    return all_tables, tables_to_delete

def auto_clean():
    """自动清理数据库，不需要交互确认"""
    print("开始自动清理数据库...")
    _, tables_to_delete = get_tables_to_delete()
    
    if not tables_to_delete:
        print("没有需要删除的表。")
        return True
    
    print_tables_info(tables_to_delete, "将要删除的表")
    return delete_tables(tables_to_delete)

def main():
    """主函数"""
    # 检查是否为强制模式
    force_mode = len(sys.argv) > 1 and sys.argv[1] == '--force'
    
    if force_mode:
        return auto_clean()
    
    print("开始数据库清理流程...")
    
    # 获取表信息
    all_tables, tables_to_delete = get_tables_to_delete()
    print_tables_info(all_tables, "当前数据库中的所有表")
    
    # 确认并执行删除
    if confirm_deletion(tables_to_delete):
        return delete_tables(tables_to_delete)
    else:
        print("操作已取消，没有表被删除。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 