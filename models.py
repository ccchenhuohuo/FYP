"""
数据库模型定义
定义User和Admin模型，对应数据库中已存在的表结构
以及股票数据相关模型
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import pymysql
import sqlalchemy
from datetime import datetime
import traceback

# 配置 PyMySQL 以兼容 MySQLdb
pymysql.install_as_MySQLdb()

# 初始化SQLAlchemy
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    用户模型
    对应数据库中的user表
    """
    __tablename__ = 'user'
    
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), unique=True, nullable=False)
    user_email = db.Column(db.String(120), unique=True, nullable=False)
    user_password = db.Column(db.String(200), nullable=False)
    
    # 关联关系
    balance = db.relationship('AccountBalance', backref='user', uselist=False, lazy=True)
    fund_transactions = db.relationship('FundTransaction', backref='user', lazy=True)
    
    def get_id(self):
        """
        返回用户ID（Flask-Login要求）
        """
        return str(self.user_id)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<User {self.user_name}>'

class Admin(db.Model, UserMixin):
    """
    管理员模型
    对应数据库中的admin表
    """
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(80), unique=True, nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    
    def get_id(self):
        """
        返回管理员ID（Flask-Login要求）
        为了区分普通用户和管理员，添加'admin_'前缀
        """
        return f"admin_{self.admin_id}"
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Admin {self.admin_name}>'

# 股票数据模型定义
class MarketData(db.Model):
    """
    股票市场数据模型
    对应数据库中的market_data表
    存储股票的OHLCV (开盘价、最高价、最低价、收盘价、交易量) 数据
    """
    __tablename__ = 'market_data'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False, index=True)
    open = db.Column(db.Float, nullable=True)
    high = db.Column(db.Float, nullable=True)
    low = db.Column(db.Float, nullable=True)
    close = db.Column(db.Float, nullable=True)
    volume = db.Column(db.BigInteger, nullable=True)
    data_collected_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<MarketData {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class FundamentalData(db.Model):
    """
    股票基本面数据模型
    对应数据库中的fundamental_data表
    存储股票的市值、市盈率、市净率等基本面数据
    """
    __tablename__ = 'fundamental_data'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False, index=True)
    market_cap = db.Column(db.BigInteger, nullable=True)
    pe_ratio = db.Column(db.Float, nullable=True)
    pb_ratio = db.Column(db.Float, nullable=True)
    dividend_yield = db.Column(db.Float, nullable=True)
    revenue = db.Column(db.BigInteger, nullable=True)
    net_income = db.Column(db.BigInteger, nullable=True)
    operating_cash_flow = db.Column(db.BigInteger, nullable=True)
    data_collected_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<FundamentalData {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class BalanceSheet(db.Model):
    """
    资产负债表数据模型
    对应数据库中的balance_sheet表
    存储公司的资产和负债信息
    """
    __tablename__ = 'balance_sheet'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False, index=True)
    current_assets = db.Column(db.BigInteger, nullable=True)
    non_current_assets = db.Column(db.BigInteger, nullable=True)
    current_liabilities = db.Column(db.BigInteger, nullable=True)
    non_current_liabilities = db.Column(db.BigInteger, nullable=True)
    data_collected_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<BalanceSheet {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class IncomeStatement(db.Model):
    """
    利润表数据模型
    对应数据库中的income_statement表
    存储公司的收入和利润信息
    """
    __tablename__ = 'income_statement'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False, index=True)
    revenue = db.Column(db.BigInteger, nullable=True)
    cost_of_revenue = db.Column(db.BigInteger, nullable=True)
    operating_income = db.Column(db.BigInteger, nullable=True)
    income_before_tax = db.Column(db.BigInteger, nullable=True)
    net_income = db.Column(db.BigInteger, nullable=True)
    data_collected_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<IncomeStatement {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class Order(db.Model):
    """
    订单数据模型
    对应数据库中的order表
    存储用户的股票订单信息
    """
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    order_type = db.Column(db.String(10), nullable=False)  # buy, sell
    order_execution_type = db.Column(db.String(10), nullable=False, default='limit')  # limit, market
    order_price = db.Column(db.Float, nullable=True)  # 可以为空，用于市价单
    order_quantity = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, executed, cancelled, rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    remark = db.Column(db.Text, nullable=True)  # 用于存储拒绝原因等备注信息

    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    def __init__(self, user_id, ticker, order_type, order_price, order_quantity, order_execution_type='limit'):
        self.user_id = user_id
        self.ticker = ticker
        self.order_type = order_type
        self.order_execution_type = order_execution_type
        self.order_price = order_price
        self.order_quantity = order_quantity
        self.order_status = 'pending'

    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Order {self.order_id}: {self.order_type} {self.ticker} x{self.order_quantity}>'

class Transaction(db.Model):
    """
    交易数据模型
    对应数据库中的transaction表
    存储用户的股票交易信息
    """
    __tablename__ = 'transaction'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'buy' 或 'sell'
    transaction_price = db.Column(db.Float, nullable=False)
    transaction_quantity = db.Column(db.Integer, nullable=False)
    transaction_amount = db.Column(db.Float, nullable=False)  # 总金额 = 价格 * 数量
    transaction_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    transaction_status = db.Column(db.String(20), nullable=False, default='completed')  # 'completed', 'failed', 'reversed'
    
    # 添加与User的关系
    user = db.relationship('User', backref='transactions', lazy=True)
    
    # 添加与Order的关系
    order = db.relationship('Order', backref='transaction', lazy=True, uselist=False)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Transaction {self.transaction_id}: {self.transaction_type} {self.ticker} x{self.transaction_quantity}>'

class AccountBalance(db.Model):
    """
    账户余额模型
    对应数据库中的account_balance表
    单独管理用户资金状态
    """
    __tablename__ = 'account_balance'
    
    balance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    available_balance = db.Column(db.Float, nullable=False, default=0.0)  # 可用余额
    frozen_balance = db.Column(db.Float, nullable=False, default=0.0)     # 冻结余额
    total_balance = db.Column(db.Float, nullable=False, default=0.0)      # 总余额 = 可用 + 冻结
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<AccountBalance {self.user_id}: available={self.available_balance}, frozen={self.frozen_balance}>'

class FundTransaction(db.Model):
    """
    资金交易模型
    对应数据库中的fund_transaction表
    统一管理充值、提现等资金操作记录
    """
    __tablename__ = 'fund_transaction'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    remark = db.Column(db.String(255), nullable=True)
    operator_id = db.Column(db.Integer, nullable=True)
    original_id = db.Column(db.Integer, nullable=True)  # 用于记录原始充值/提现ID，方便数据迁移后的参考
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<FundTransaction {self.transaction_id}: {self.transaction_type} {self.amount} ({self.status})>'

class Portfolio(db.Model):
    """
    持仓信息模型
    对应数据库中的portfolio表
    记录用户的股票持仓情况
    """
    __tablename__ = 'portfolio'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    average_price = db.Column(db.Float, nullable=True)  # 平均购入价格
    total_cost = db.Column(db.Float, nullable=True)     # 总成本
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 添加与User的关系
    user = db.relationship('User', backref='portfolio', lazy=True)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Portfolio {self.user_id}-{self.ticker}: {self.quantity} @ {self.average_price}>'

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
            
            # 创建所有表
            db.create_all()
            
            # 确保有默认管理员账户
            create_default_admin()
            
            # 确保每个用户都有一个账户余额记录
            ensure_user_balances()
            
            print("数据库表已同步")
    except Exception as e:
        print(f"数据库初始化错误: {str(e)}")
        traceback.print_exc()
        # 如果出错，继续尝试创建表
        try:
            with app.app_context():
                db.create_all()
        except Exception as inner_e:
            print(f"创建表失败: {str(inner_e)}")

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

def create_default_admin():
    """创建默认管理员账户"""
    from werkzeug.security import generate_password_hash
    admin = Admin.query.filter_by(admin_name='admin').first()
    if not admin:
        admin = Admin(
            admin_name='admin',
            admin_password=generate_password_hash('admin')
        )
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账户已创建") 