"""
Trade related model definitions
Include order, transaction record and portfolio information
"""
from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import NUMERIC
from .enums import OrderType, OrderExecutionType, OrderStatus, TransactionStatus


class Order(db.Model):
    """
    Order data model
    Corresponds to the order table in the database
    Store user's stock order information
    
    Attributes:
        order_id (Integer): Order ID, primary key
        user_id (Integer): User ID, foreign key associated with user table
        ticker (String): Stock code, e.g. 'AAPL', max 10 characters
        order_type (Enum): Order type, use OrderType enumeration, e.g. buy or sell
        order_execution_type (Enum): Order execution type, use OrderExecutionType enumeration, e.g. limit or market
        order_price (NUMERIC): Order price, accurate to 0.0001, market order can be empty
        order_quantity (Integer): Order quantity (shares)
        order_status (Enum): Order status, use OrderStatus enumeration, e.g. pending, completed, cancelled
        created_at (DateTime): Order creation time
        updated_at (DateTime): Order update time
        executed_at (DateTime): Order execution time
        remark (Text): Remark information, used to store rejection reasons
    """
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    order_type = db.Column(db.Enum(OrderType), nullable=False)  # Use OrderType enumeration
    order_execution_type = db.Column(db.Enum(OrderExecutionType), nullable=False, default=OrderExecutionType.LIMIT)  # Use OrderExecutionType enumeration
    order_price = db.Column(NUMERIC(12,4), nullable=True)  # Can be empty, used for market order
    order_quantity = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.Enum(OrderStatus, native_enum=False, length=10), nullable=False, default=OrderStatus.PENDING)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    remark = db.Column(db.Text, nullable=True)  # Used to store rejection reasons

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
        Model string representation
        """
        return f'<Order {self.order_id}: {self.order_type} {self.ticker} x{self.order_quantity}>'

class Transaction(db.Model):
    """
    Transaction data model
    Corresponds to the transaction table in the database
    Store user's stock transaction information
    
    Attributes:
        transaction_id (Integer): Transaction ID, primary key
        order_id (Integer): Order ID, foreign key associated with orders table, unique index
        user_id (Integer): User ID, foreign key associated with user table, index
        ticker (String): Stock code, e.g. 'AAPL', max 10 characters, index
        transaction_type (Enum): Transaction type, use OrderType enumeration, e.g. buy or sell
        transaction_price (NUMERIC): Transaction price, accurate to 0.0001
        transaction_quantity (Integer): Transaction quantity (shares)
        transaction_amount (NUMERIC): Transaction total amount, accurate to 0.0001, equal to price multiplied by quantity
        transaction_time (DateTime): Transaction time
        transaction_status (Enum): Transaction status, use TransactionStatus enumeration, default is completed
    """
    __tablename__ = 'transaction'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    transaction_type = db.Column(db.Enum(OrderType), nullable=False)  # Use OrderType enumeration
    transaction_price = db.Column(NUMERIC(12,4), nullable=False)
    transaction_quantity = db.Column(db.Integer, nullable=False)
    transaction_amount = db.Column(NUMERIC(12,4), nullable=False)  # Total amount = price * quantity
    transaction_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    transaction_status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED)  # Use TransactionStatus enumeration
    
    # Add relationship with User
    user = db.relationship('User', backref='transactions', lazy=True)
    # Add relationship with Order
    order = db.relationship('Order', backref='transaction', lazy=True, uselist=False)
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<Transaction {self.transaction_id}: {self.transaction_type} {self.ticker} x{self.transaction_quantity}>'

class Portfolio(db.Model):
    """
    Portfolio information model
    Corresponds to the portfolio table in the database
    Record user's stock portfolio information
    
    Attributes:
        id (Integer): Portfolio record ID, primary key
        user_id (Integer): User ID, foreign key associated with user table, index
        ticker (String): Stock code, e.g. 'AAPL', max 10 characters, index
        quantity (Integer): Holding quantity (shares), default is 0
        average_price (NUMERIC): Average purchase price, accurate to 0.0001
        total_cost (NUMERIC): Total cost, accurate to 0.0001
        last_updated (DateTime): Last updated time, automatically updated
    """
    __tablename__ = 'portfolio'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, index=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    average_price = db.Column(NUMERIC(12,4), nullable=True)  # Average purchase price
    total_cost = db.Column(NUMERIC(12,4), nullable=True)     # Total cost
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Add relationship with User
    user = db.relationship('User', backref='portfolio', lazy=True)
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<Portfolio {self.user_id}-{self.ticker}: {self.quantity} @ {self.average_price}>'