"""
数据库模型定义
包含用户、管理员、订单等模型
"""
from flask_sqlalchemy import SQLAlchemy
import pymysql #纯 Python 实现的 MySQL ​客户端库，用于直接与 MySQL 服务器通信。它负责：1.建立 TCP/IP 连接 2.执行 SQL 语句 3.传输数据并处理结果集
import sqlalchemy # Flask-SQLAlchemy 是 SQLAlchemy 的 Flask 集成版，提供 ​ORM（对象关系映射）​ 功能：1.将 Python 类映射到数据库表（如 User 类 → users 表）2.用 Python 对象操作数据库 3.集成 Flask 应用生命周期（自动关闭连接、配置管理）
import traceback
from datetime import datetime
import os

# 配置 PyMySQL 以兼容 MySQLdb
pymysql.install_as_MySQLdb()

# 初始化SQLAlchemy
db = SQLAlchemy()

# 导入所有模型
from .user import User
from .admin import Admin
from .market import MarketData, FundamentalData, BalanceSheet, IncomeStatement
from .trade import Order, Transaction, Portfolio
from .finance import AccountBalance, FundTransaction

def init_db(app):
    """初始化数据库并创建表"""
    # 初始化SQLAlchemy与应用的关联
    db.init_app(app)
    
    try:
        # 确保所有表都存在
        with app.app_context():
            inspector = sqlalchemy.inspect(db.engine)
            tables = inspector.get_table_names()
            
            # 检查数据库中是否已有表
            if not tables:
                print("数据库为空，开始创建所有表...")
            else:
                print(f"数据库中已有表: {tables}")
            
            # 以下代码尝试确保模型与数据库表结构一致
            try:
                # 先尝试创建所有表
                db.create_all()
                print("数据库表已创建/更新")
            except Exception as table_error:
                print(f"创建/更新表时出错: {str(table_error)}")
                traceback.print_exc()
            
            # 尝试创建默认管理员账户
            try:
                create_default_admin(app)
            except Exception as admin_error:
                print(f"创建管理员账户时出错: {str(admin_error)}")
                traceback.print_exc()
            
            # 尝试确保用户余额记录
            try:
                ensure_user_balances()
            except Exception as balance_error:
                print(f"确保用户余额记录时出错: {str(balance_error)}")
                traceback.print_exc()
            
    except Exception as e:
        print(f"数据库初始化错误: {str(e)}")
        traceback.print_exc()

def ensure_user_balances():
    """确保每个用户都有一个账户余额记录"""
    try:
        # 找出所有没有余额记录的用户
        users_without_balance = User.query.outerjoin(AccountBalance).filter(AccountBalance.balance_id == None).all()
        
        for user in users_without_balance:
            # 创建新的余额记录
            balance = AccountBalance(
                user_id=user.user_id,
                available_balance=0.0,
                frozen_balance=0.0,
                total_balance=0.0
            )
            db.session.add(balance)
        
        if users_without_balance:
            db.session.commit()
            print(f"为 {len(users_without_balance)} 个用户创建了账户余额记录")
    except Exception as e:
        db.session.rollback()
        print(f"创建用户账户余额记录时出错: {str(e)}")
        traceback.print_exc()

def create_default_admin(app):
    """创建默认管理员账户"""
    try:
        from werkzeug.security import generate_password_hash
        
        # 从配置中获取默认管理员用户名和密码
        default_admin_username = app.config.get('DEFAULT_ADMIN_USERNAME', 'admin')
        default_admin_password = app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin')
        
        admin = Admin.query.filter_by(admin_name=default_admin_username).first()
        if not admin:
            admin = Admin(
                admin_name=default_admin_username,
                admin_password=generate_password_hash(default_admin_password, method='pbkdf2:sha256')
            )
            db.session.add(admin)
            db.session.commit()
            print(f"默认管理员账户 '{default_admin_username}' 已创建")
    except Exception as e:
        db.session.rollback()
        print(f"创建默认管理员账户失败: {str(e)}")
        traceback.print_exc() 