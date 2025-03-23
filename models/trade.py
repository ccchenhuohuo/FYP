"""
交易相关模型定义
包括订单、交易记录和持仓信息
"""
from . import db
from datetime import datetime

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
        
    def __round__(self, precision=0):
        """
        实现四舍五入方法，使模板中的round过滤器可以正常工作
        
        参数:
        precision (int): 保留的小数位数
        
        返回:
        float: 四舍五入后的值
        """
        # 根据上下文决定要四舍五入的值
        # 默认返回平均价格的四舍五入值
        return round(self.average_price, precision) 