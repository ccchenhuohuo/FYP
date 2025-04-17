"""
Stock data collection module
Use Yahoo Finance API to get and store financial data of major tech stocks
"""
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from config import DB_CONFIG, TECH_TICKERS

def fetch_stock_data():
    """
    Get all stock codes data and organize it into structured DataFrames
    
    Returns:
        tuple: Four DataFrames,It includes market data, fundamental data, 
        balance sheet data and income statement data respectively
    """
    # Create empty DataFrames to store different types of data
    market_data = pd.DataFrame()
    fundamental_data = pd.DataFrame()
    balance_sheet_data = pd.DataFrame()
    income_statement_data = pd.DataFrame()
    
    # Get current time as data acquisition timestamp
    current_time = datetime.now()
    
    for ticker in TECH_TICKERS:
        print(f"Getting data for {ticker}...")
        
        try:
            # Get stock information
            stock = yf.Ticker(ticker)
            
            # Get historical price data (from 2018)
            hist = stock.history(start="2018-01-01")
            if hist.empty:
                print(f"Warning: Unable to get historical data for {ticker}")
                continue
            
            # Get financial data
            info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            # Market data table (OHLCV)
            ticker_market_data = pd.DataFrame({
                'ticker': ticker,
                'date': hist.index,
                'open': hist['Open'],
                'high': hist['High'],
                'low': hist['Low'],
                'close': hist['Close'],
                'volume': hist['Volume'],
                'data_collected_at': current_time
            })
            market_data = pd.concat([market_data, ticker_market_data], ignore_index=True)
            
            # Fundamental data table
            fundamental_row = {
                'ticker': ticker,
                'date': current_time,
                'market_cap': info.get('marketCap', None),
                'pe_ratio': info.get('trailingPE', None),
                'pb_ratio': info.get('priceToBook', None),
                'dividend_yield': info.get('dividendYield', None),
                'data_collected_at': current_time
            }
            
            # Add income and net income data (if available)
            if not financials.empty and 'Total Revenue' in financials.index:
                fundamental_row['revenue'] = financials.loc['Total Revenue'].values[0]
            else:
                fundamental_row['revenue'] = None
                
            if not financials.empty and 'Net Income' in financials.index:
                fundamental_row['net_income'] = financials.loc['Net Income'].values[0]
            else:
                fundamental_row['net_income'] = None
                
            if not cash_flow.empty and 'Operating Cash Flow' in cash_flow.index:
                fundamental_row['operating_cash_flow'] = cash_flow.loc['Operating Cash Flow'].values[0]
            else:
                fundamental_row['operating_cash_flow'] = None
                
            fundamental_data = pd.concat([fundamental_data, pd.DataFrame([fundamental_row])], ignore_index=True)
            
            # Balance sheet data
            if not balance_sheet.empty:
                balance_sheet_row = {
                    'ticker': ticker,
                    'date': balance_sheet.columns[0] if len(balance_sheet.columns) > 0 else current_time,
                    'current_assets': balance_sheet.loc['Total Current Assets'].values[0] if 'Total Current Assets' in balance_sheet.index else None,
                    'non_current_assets': balance_sheet.loc['Total Non Current Assets'].values[0] if 'Total Non Current Assets' in balance_sheet.index else None,
                    'current_liabilities': balance_sheet.loc['Total Current Liabilities'].values[0] if 'Total Current Liabilities' in balance_sheet.index else None,
                    'non_current_liabilities': balance_sheet.loc['Total Non Current Liabilities'].values[0] if 'Total Non Current Liabilities' in balance_sheet.index else None,
                    'data_collected_at': current_time
                }
                balance_sheet_data = pd.concat([balance_sheet_data, pd.DataFrame([balance_sheet_row])], ignore_index=True)
            
            # Income statement data
            if not financials.empty:
                income_statement_row = {
                    'ticker': ticker,
                    'date': financials.columns[0] if len(financials.columns) > 0 else current_time,
                    'revenue': financials.loc['Total Revenue'].values[0] if 'Total Revenue' in financials.index else None,
                    'cost_of_revenue': financials.loc['Cost Of Revenue'].values[0] if 'Cost Of Revenue' in financials.index else None,
                    'operating_income': financials.loc['Operating Income'].values[0] if 'Operating Income' in financials.index else None,
                    'income_before_tax': financials.loc['Income Before Tax'].values[0] if 'Income Before Tax' in financials.index else None,
                    'net_income': financials.loc['Net Income'].values[0] if 'Net Income' in financials.index else None,
                    'data_collected_at': current_time
                }
                income_statement_data = pd.concat([income_statement_data, pd.DataFrame([income_statement_row])], ignore_index=True)
        
        except Exception as e:
            print(f"Error getting data for {ticker}: {str(e)}")
    
    return market_data, fundamental_data, balance_sheet_data, income_statement_data

def save_to_database(market_data, fundamental_data, balance_sheet_data, income_statement_data):
    """
    Save all collected data to MySQL database
    
    Parameters:
        market_data (DataFrame): Market price and transaction volume data
        fundamental_data (DataFrame): Key financial indicators
        balance_sheet_data (DataFrame): Balance sheet information
        income_statement_data (DataFrame): Income statement information
    """
    # Create database connection string
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
    
    try:
        # Create database engine
        engine = create_engine(connection_string, echo=False)
        
        # Check if there is data to save
        if not market_data.empty:
            market_data.to_sql(name='market_data', con=engine, if_exists='replace', index=False)
            print(f"Saved {len(market_data)} market data records")
        else:
            print("No market data to save")
            
        if not fundamental_data.empty:
            fundamental_data.to_sql(name='fundamental_data', con=engine, if_exists='replace', index=False)
            print(f"Saved {len(fundamental_data)} fundamental data records")
        else:
            print("No fundamental data to save")
            
        if not balance_sheet_data.empty:
            balance_sheet_data.to_sql(name='balance_sheet', con=engine, if_exists='replace', index=False)
            print(f"Saved {len(balance_sheet_data)} balance sheet data records")
        else:
            print("No balance sheet data to save")
            
        if not income_statement_data.empty:
            income_statement_data.to_sql(name='income_statement', con=engine, if_exists='replace', index=False)
            print(f"Saved {len(income_statement_data)} income statement data records")
        else:
            print("No income statement data to save")
            
        print("All data has been successfully written to the MySQL database!")
        
    except Exception as e:
        print(f"Error saving data to database: {str(e)}")

def clear_database():
    """
    Clear all stock data tables in the database
    """
    # Create database connection string
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
    
    try:
        # Create database engine
        engine = create_engine(connection_string, echo=False)
        
        # Clear each table
        with engine.connect() as connection:
            connection.execute("DELETE FROM market_data")
            connection.execute("DELETE FROM fundamental_data")
            connection.execute("DELETE FROM balance_sheet")
            connection.execute("DELETE FROM income_statement")
        
        print("All data tables have been successfully cleared!")
        
    except Exception as e:
        print(f"Error clearing data tables: {str(e)}")

def print_data_samples(market_data, fundamental_data, balance_sheet_data, income_statement_data):
    """
    Print sample rows of each DataFrame for verification
    
    Parameters:
        market_data (DataFrame): Market price and transaction volume data
        fundamental_data (DataFrame): Key financial indicators
        balance_sheet_data (DataFrame): Balance sheet information
        income_statement_data (DataFrame): Income statement information
    """
    print("\n===================== Data samples =====================")
    
    print("\nMarket data:")
    if not market_data.empty:
        # Display the latest record for each stock
        latest_records = market_data.sort_values('date').groupby('ticker').tail(1)
        print(latest_records[['ticker', 'date', 'open', 'close', 'volume']].head(7))
    else:
        print("No data")
        
    print("\nFundamental data:")
    if not fundamental_data.empty:
        print(fundamental_data[['ticker', 'date', 'market_cap', 'pe_ratio', 'pb_ratio']].head(7))
    else:
        print("No data")
        
    print("\nBalance sheet data:")
    if not balance_sheet_data.empty:
        print(balance_sheet_data[['ticker', 'date', 'current_assets', 'current_liabilities']].head(7))
    else:
        print("No data")
        
    print("\nIncome statement data:")
    if not income_statement_data.empty:
        print(income_statement_data[['ticker', 'date', 'revenue', 'net_income']].head(7))
    else:
        print("No data")
        
    print("\n=====================================================")

# Test function
def run_stock_data_collection():
    """Run the stock data collection and storage process"""
    print("Starting to get stock data...")
    
    # Get all stock data
    market_data, fundamental_data, balance_sheet_data, income_statement_data = fetch_stock_data()
    
    # Display the record count of each dataset
    print(f"\nGot {len(market_data)} market data records")
    print(f"Got {len(fundamental_data)} fundamental data records")
    print(f"Got {len(balance_sheet_data)} balance sheet data records")
    print(f"Got {len(income_statement_data)} income statement data records")
    
    # Print sample data for verification
    print_data_samples(market_data, fundamental_data, balance_sheet_data, income_statement_data)
    
    # Save all data to database
    save_to_database(market_data, fundamental_data, balance_sheet_data, income_statement_data)
    
    print("\nData collection and storage completed!") 