"""
数据库模型定义
定义User和Admin模型，对应数据库中已存在的表结构
以及股票数据相关模型
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import pymysql
import sqlalchemy
from sqlalchemy.exc import OperationalError
from datetime import datetime

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
    balance = db.Column(db.Float, nullable=False, default=0.0)  # 用户余额
    
    # 添加与Order的关系
    orders = db.relationship('Order', backref='user', lazy=True)
    
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
    __tablename__ = 'order'
    
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    order_type = db.Column(db.String(10), nullable=False)  # 'buy' 或 'sell'
    order_price = db.Column(db.Float, nullable=False)
    order_quantity = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'executed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # 添加与Transaction的关系
    transaction = db.relationship('Transaction', backref='order', lazy=True, uselist=False)
    
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
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False, unique=True, index=True)
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
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Transaction {self.transaction_id}: {self.transaction_type} {self.ticker} x{self.transaction_quantity}>'

def init_db(app):
    """
    初始化数据库
    只初始化SQLAlchemy，不创建表或修改表结构
    """
    db.init_app(app)
    
    # 创建数据库表
    with app.app_context():
        try:
            # 检查现有表结构
            inspector = sqlalchemy.inspect(db.engine)
            tables = inspector.get_table_names()
            
            # 首先处理数据库迁移
            if 'user' in tables:
                columns = [column['name'] for column in inspector.get_columns('user')]
                if 'user_email' not in columns:
                    try:
                        # 添加email列，但允许为null以便添加默认值
                        with db.engine.connect() as conn:
                            conn.execute(sqlalchemy.text('ALTER TABLE user ADD COLUMN user_email VARCHAR(120)'))
                        print("添加user_email列到user表")
                        
                        # 为现有用户添加默认邮箱
                        users = User.query.all()
                        for user in users:
                            default_email = f"{user.user_name}@example.com"
                            with db.engine.connect() as conn:
                                conn.execute(sqlalchemy.text(f"UPDATE user SET user_email = '{default_email}' WHERE user_id = {user.user_id}"))
                                conn.commit()
                        
                        # 添加唯一约束
                        with db.engine.connect() as conn:
                            conn.execute(sqlalchemy.text('ALTER TABLE user MODIFY COLUMN user_email VARCHAR(120) NOT NULL UNIQUE'))
                            conn.commit()
                        print("为现有用户添加默认邮箱并设置约束")
                    except Exception as e:
                        print(f"迁移数据时出错: {e}")
                
                # 检查并添加balance列
                if 'balance' not in columns:
                    try:
                        # 添加balance列，默认值为0
                        with db.engine.connect() as conn:
                            conn.execute(sqlalchemy.text('ALTER TABLE user ADD COLUMN balance FLOAT NOT NULL DEFAULT 0.0'))
                            conn.commit()
                        print("添加balance列到user表")
                    except Exception as e:
                        print(f"添加balance列时出错: {e}")
            
            # 创建股票数据表 (如果不存在)
            # 因为我们使用SQLAlchemy的ORM，可以直接使用create_all()，它只会创建不存在的表
            db.create_all()
            print("数据库表已同步")
            
            # 导入在这里以避免循环导入
            from werkzeug.security import generate_password_hash
            
            # 检查是否有默认管理员
            admin = Admin.query.filter_by(admin_name='admin').first()
            if not admin:
                admin = Admin(
                    admin_name='admin',
                    admin_password=generate_password_hash('admin')
                )
                db.session.add(admin)
                db.session.commit()
                print("默认管理员账户已创建")
                
        except OperationalError as e:
            # 处理数据库操作错误
            print(f"数据库初始化错误: {e}")
            # 如果表不存在，创建所有表
            db.create_all()
            print("创建所有数据库表")
            
            # 创建默认管理员
            from werkzeug.security import generate_password_hash
            admin = Admin(
                admin_name='admin',
                admin_password=generate_password_hash('admin')
            )
            db.session.add(admin)
            db.session.commit()
            print("默认管理员账户已创建") 