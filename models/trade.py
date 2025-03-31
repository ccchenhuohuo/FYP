"""
交易相关模型定义
包括订单、交易记录和持仓信息
"""
from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import NUMERIC
from .enums import OrderType, OrderExecutionType, OrderStatus, TransactionStatus


class Order(db.Model):
    """
    订单数据模型
    对应数据库中的order表
    存储用户的股票订单信息
    
    属性:
        order_id (Integer): 订单ID，主键
        user_id (Integer): 用户ID，外键关联user表
        ticker (String): 股票代码，如'AAPL'，最长10字符
        order_type (Enum): 订单类型，使用OrderType枚举，如买入、卖出
        order_execution_type (Enum): 订单执行类型，使用OrderExecutionType枚举，如限价单、市价单
        order_price (NUMERIC): 订单价格，精确到0.0001，市价单可为空
        order_quantity (Integer): 订单数量(股数)
        order_status (Enum): 订单状态，使用OrderStatus枚举，如待处理、已完成、已取消
        created_at (DateTime): 订单创建时间
        updated_at (DateTime): 订单更新时间
        executed_at (DateTime): 订单执行时间
        remark (Text): 备注信息，用于存储拒绝原因等
    """
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    order_type = db.Column(db.Enum(OrderType), nullable=False)  # 使用OrderType枚举
    order_execution_type = db.Column(db.Enum(OrderExecutionType), nullable=False, default=OrderExecutionType.LIMIT)  # 使用OrderExecutionType枚举
    order_price = db.Column(NUMERIC(12,4), nullable=True)  # 可以为空，用于市价单
    order_quantity = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)  # 使用OrderStatus枚举
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    remark = db.Column(db.Text, nullable=True)  # 用于存储拒绝原因等备注信息

    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    def __init__(self, user_id, ticker, order_type, order_execution_type, order_price, order_quantity, order_status=OrderStatus.PENDING):
        self.user_id = user_id
        self.ticker = ticker
        self.order_type = order_type
        self.order_execution_type = order_execution_type
        self.order_price = order_price
        self.order_quantity = order_quantity
        self.order_status = order_status

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
    
    属性:
        transaction_id (Integer): 交易ID，主键
        order_id (Integer): 订单ID，外键关联orders表，唯一索引
        user_id (Integer): 用户ID，外键关联user表，索引
        ticker (String): 股票代码，如'AAPL'，最长10字符，索引
        transaction_type (Enum): 交易类型，使用OrderType枚举，如买入、卖出
        transaction_price (NUMERIC): 交易价格，精确到0.0001
        transaction_quantity (Integer): 交易数量(股数)
        transaction_amount (NUMERIC): 交易总金额，精确到0.0001，等于价格乘以数量
        transaction_time (DateTime): 交易时间
        transaction_status (Enum): 交易状态，使用TransactionStatus枚举，默认为已完成
    """
    __tablename__ = 'transaction'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    transaction_type = db.Column(db.Enum(OrderType), nullable=False)  # 使用OrderType枚举
    transaction_price = db.Column(NUMERIC(12,4), nullable=False)
    transaction_quantity = db.Column(db.Integer, nullable=False)
    transaction_amount = db.Column(NUMERIC(12,4), nullable=False)  # 总金额 = 价格 * 数量
    transaction_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    transaction_status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED)  # 使用TransactionStatus枚举
    
    # 添加与User的关系
    user = db.relationship('User', backref='transactions', lazy=True)
    # 添加与Order的关系
    order = db.relationship('Order', backref='transaction', lazy=True, uselist=False)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Transaction {self.transaction_id}: {self.transaction_type} {self.ticker} x{self.transaction_quantity}>'

class Portfolio(db.Model):
    """
    持仓信息模型
    对应数据库中的portfolio表
    记录用户的股票持仓情况
    
    属性:
        id (Integer): 持仓记录ID，主键
        user_id (Integer): 用户ID，外键关联user表，索引
        ticker (String): 股票代码，如'AAPL'，最长10字符，索引
        quantity (Integer): 持有数量(股数)，默认为0
        average_price (NUMERIC): 平均购入价格，精确到0.0001
        total_cost (NUMERIC): 总成本，精确到0.0001
        last_updated (DateTime): 最后更新时间，自动更新
    """
    __tablename__ = 'portfolio'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    average_price = db.Column(NUMERIC(12,4), nullable=True)  # 平均购入价格
    total_cost = db.Column(NUMERIC(12,4), nullable=True)     # 总成本
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 添加与User的关系
    user = db.relationship('User', backref='portfolio', lazy=True)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<Portfolio {self.user_id}-{self.ticker}: {self.quantity} @ {self.average_price}>'