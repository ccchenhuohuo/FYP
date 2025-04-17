"""
Market data related model definitions
Include stock market data, fundamental data, balance sheet and income statement
"""
from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import NUMERIC

class MarketData(db.Model):
    """
    Stock market data model
    Corresponds to the market_data table in the database
    Store stock OHLCV (opening price, highest price, lowest price, closing price, transaction volume) data
    
    Attributes:
        ticker (str): Stock code, e.g. 'AAPL', max 10 characters
        date (datetime): Data date, combined with ticker as primary key
        open (NUMERIC): Opening price, accurate to 0.0001
        high (NUMERIC): Highest price of the day, accurate to 0.0001
        low (NUMERIC): Lowest price of the day, accurate to 0.0001
        close (NUMERIC): Closing price, accurate to 0.0001
        volume (BigInteger): Transaction volume (shares)
        data_collected_at (datetime): Data collection time
    """
    __tablename__ = 'market_data'
    
    # Use ticker and date as a composite primary key
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
        Model string representation
        """
        return f'<MarketData {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class FundamentalData(db.Model):
    """
    Stock fundamental data model
    Corresponds to the fundamental_data table in the database
    Store fundamental data such as market cap, PE ratio, PB ratio, etc.
    
    属性:
        ticker (str): Stock code, e.g. 'AAPL', max 10 characters
        date (datetime): Data date, combined with ticker as primary key
        market_cap (BigInteger): Market cap, calculated in base currency
        pe_ratio (NUMERIC): PE ratio, accurate to 0.0001
        pb_ratio (NUMERIC): PB ratio, accurate to 0.0001
        dividend_yield (NUMERIC): Dividend yield, accurate to 0.000001
        net_income (BigInteger): Net income, calculated in base currency
        operating_cash_flow (BigInteger): Operating cash flow, calculated in base currency
        data_collected_at (datetime): Data collection time
    """
    __tablename__ = 'fundamental_data'
    
    # Use ticker and date as a composite primary key
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
        Model string representation
        """
        return f'<FundamentalData {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class BalanceSheet(db.Model):
    """
    Balance sheet data model
    Corresponds to the balance_sheet table in the database
    Store company's assets and liabilities information
    
    属性:
        ticker (str): Stock code, e.g. 'AAPL', max 10 characters
        date (datetime): Data date, combined with ticker as primary key
        current_assets (BigInteger): Total current assets, calculated in base currency
        non_current_assets (BigInteger): Total non-current assets, calculated in base currency
        current_liabilities (BigInteger): Total current liabilities, calculated in base currency
        non_current_liabilities (BigInteger): Total non-current liabilities, calculated in base currency
        data_collected_at (datetime): Data collection time
    """
    __tablename__ = 'balance_sheet'
    
    # Use ticker and date as a composite primary key
    ticker = db.Column(db.String(10), primary_key=True, nullable=False, index=True)
    date = db.Column(db.DateTime, primary_key=True, nullable=False, index=True)
    current_assets = db.Column(db.BigInteger, nullable=True)
    non_current_assets = db.Column(db.BigInteger, nullable=True)
    current_liabilities = db.Column(db.BigInteger, nullable=True)
    non_current_liabilities = db.Column(db.BigInteger, nullable=True)
    data_collected_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        """
        Model string representation
        """
        return f'<BalanceSheet {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'

class IncomeStatement(db.Model):
    """
    Income statement data model
    Corresponds to the income_statement table in the database
    Store company's income and profit information
    
    属性:
        ticker (str): Stock code, e.g. 'AAPL', max 10 characters
        date (datetime): Data date, combined with ticker as primary key
        revenue (BigInteger): Revenue, calculated in base currency
        cost_of_revenue (BigInteger): Cost of revenue, calculated in base currency
        operating_income (BigInteger): Operating income, calculated in base currency
        income_before_tax (BigInteger): Income before tax, calculated in base currency
        net_income (BigInteger): Net income, calculated in base currency
        data_collected_at (datetime): Data collection time
    """
    __tablename__ = 'income_statement'
    
    # Use ticker and date as a composite primary key
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
        Model string representation
        """
        return f'<IncomeStatement {self.ticker} @ {self.date.strftime("%Y-%m-%d")}>'