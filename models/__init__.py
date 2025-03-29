from flask_sqlalchemy import SQLAlchemy
import pymysql  # 纯 Python 实现的 MySQL 客户端库，用于直接与 MySQL 服务器通信
import sqlalchemy  # Flask-SQLAlchemy 是 SQLAlchemy 的 Flask 集成版，提供 ORM 功能
import logging
import contextlib
from datetime import datetime
import os

# 配置日志
logger = logging.getLogger(__name__)

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

@contextlib.contextmanager
def session_scope():
    """提供事务范围的会话上下文管理器
    
    使用方法:
    with session_scope() as session:
        # 执行数据库操作
    """
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"数据库事务错误: {str(e)}", exc_info=True)
        raise
    finally:
        db.session.close()

def init_db(app):
    """初始化数据库并创建表"""
    # 初始化SQLAlchemy与应用的关联
    db.init_app(app)
    
    # 配置日志级别
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 确保所有表都存在
        with app.app_context():
            # 执行初始化步骤
            _check_and_create_tables(app)
            _create_default_admin(app)
            _ensure_user_balances()
    except Exception as e:
        logger.error(f"数据库初始化错误: {str(e)}", exc_info=True)

def _check_and_create_tables(app):
    """检查并创建数据库表"""
    inspector = sqlalchemy.inspect(db.engine)
    tables = inspector.get_table_names()
    
    # 检查数据库中是否已有表
    if not tables:
        logger.info("数据库为空，开始创建所有表...")
    else:
        logger.info(f"数据库中已有表: {tables}")
    
    try:
        # 创建所有表
        db.create_all()
        logger.info("数据库表已创建/更新")
    except Exception as e:
        logger.error(f"创建/更新表时出错: {str(e)}", exc_info=True)
        raise

def _ensure_user_balances():
    """确保每个用户都有一个账户余额记录"""
    with session_scope() as session:
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
            session.add(balance)
        
        if users_without_balance:
            logger.info(f"为 {len(users_without_balance)} 个用户创建了账户余额记录")

def _create_default_admin(app):
    """创建默认管理员账户"""
    from werkzeug.security import generate_password_hash
    
    with session_scope() as session:
        # 从配置中获取默认管理员用户名和密码
        default_admin_username = app.config.get('DEFAULT_ADMIN_USERNAME', 'admin')
        default_admin_password = app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin')
        
        admin = Admin.query.filter_by(admin_name=default_admin_username).first()
        if not admin:
            admin = Admin(
                admin_name=default_admin_username,
                admin_password=generate_password_hash(default_admin_password, method='pbkdf2:sha256')
            )
            session.add(admin)
            logger.info(f"默认管理员账户 '{default_admin_username}' 已创建")