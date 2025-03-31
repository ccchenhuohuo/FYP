"""
市场数据相关模型定义
包括股票行情数据、基本面数据、资产负债表和利润表
"""
from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import NUMERIC

class MarketData(db.Model):
    """
    股票市场数据模型
    对应数据库中的market_data表
    存储股票的OHLCV(开盘价、最高价、最低价、收盘价、交易量)数据
    
    属性:
        ticker (str): 股票代码，如'AAPL'，最长10字符
        date (datetime): 数据日期，与ticker联合构成主键
        open (NUMERIC): 开盘价，精确到0.0001
        high (NUMERIC): 当日最高价，精确到0.0001
        low (NUMERIC): 当日最低价，精确到0.0001
        close (NUMERIC): 收盘价，精确到0.0001
        volume (BigInteger): 成交量(股数)
        data_collected_at (datetime): 数据采集时间
    """
    __tablename__ = 'market_data'
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
    open = db.Column(NUMERIC(12,4), nullable=True)
    high = db.Column(NUMERIC(12,4), nullable=True)
    low = db.Column(NUMERIC(12,4), nullable=True)
    close = db.Column(NUMERIC(12,4), nullable=True)
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
    
    属性:
        ticker (str): 股票代码，如'AAPL'，最长10字符
        date (datetime): 数据日期，与ticker联合构成主键
        market_cap (BigInteger): 市值，以基础货币单位计算
        pe_ratio (NUMERIC): 市盈率，精确到0.0001
        pb_ratio (NUMERIC): 市净率，精确到0.0001
        dividend_yield (NUMERIC): 股息收益率，精确到0.000001
        net_income (BigInteger): 净利润，以基础货币单位计算
        operating_cash_flow (BigInteger): 经营现金流，以基础货币单位计算
        data_collected_at (datetime): 数据采集时间
    """
    __tablename__ = 'fundamental_data'
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
    market_cap = db.Column(db.BigInteger, nullable=True)
    pe_ratio = db.Column(NUMERIC(10,4), nullable=True)
    pb_ratio = db.Column(NUMERIC(10,4), nullable=True)
    dividend_yield = db.Column(NUMERIC(10,6), nullable=True)
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
    
    属性:
        ticker (str): 股票代码，如'AAPL'，最长10字符
        date (datetime): 数据日期，与ticker联合构成主键
        current_assets (BigInteger): 流动资产总额，以基础货币单位计算
        non_current_assets (BigInteger): 非流动资产总额，以基础货币单位计算
        current_liabilities (BigInteger): 流动负债总额，以基础货币单位计算
        non_current_liabilities (BigInteger): 非流动负债总额，以基础货币单位计算
        data_collected_at (datetime): 数据采集时间
    """
    __tablename__ = 'balance_sheet'
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
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
    
    属性:
        ticker (str): 股票代码，如'AAPL'，最长10字符
        date (datetime): 数据日期，与ticker联合构成主键
        revenue (BigInteger): 营业收入，以基础货币单位计算
        cost_of_revenue (BigInteger): 营业成本，以基础货币单位计算
        operating_income (BigInteger): 营业利润，以基础货币单位计算
        income_before_tax (BigInteger): 税前利润，以基础货币单位计算
        net_income (BigInteger): 净利润，以基础货币单位计算
        data_collected_at (datetime): 数据采集时间
    """
    __tablename__ = 'income_statement'
    
    # 使用ticker和date作为联合主键
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
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