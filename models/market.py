"""
市场数据相关模型定义
包括股票行情数据、基本面数据、资产负债表和利润表
"""
from . import db
from datetime import datetime

class MarketData(db.Model):
    """
    股票市场数据模型
    对应数据库中的market_data表
    存储股票的OHLCV (开盘价、最高价、最低价、收盘价、交易量) 数据
    """
    __tablename__ = 'market_data'
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
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
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
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
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
    current_assets = db.Column(db.String(255), nullable=True)  # 修改为String类型以匹配数据库
    non_current_assets = db.Column(db.Float, nullable=True)
    current_liabilities = db.Column(db.String(255), nullable=True)  # 修改为String类型以匹配数据库
    non_current_liabilities = db.Column(db.String(255), nullable=True)  # 修改为String类型以匹配数据库
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
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
    revenue = db.Column(db.Float, nullable=True)
    cost_of_revenue = db.Column(db.Float, nullable=True)
    operating_income = db.Column(db.Float, nullable=True)
    income_before_tax = db.Column(db.String(255), nullable=True)  # 修改为String类型以匹配数据库
    net_income = db.Column(db.Float, nullable=True)
    data_collected_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        """
        模型的字符串表示
        """
        return f'<IncomeStatement {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>' 