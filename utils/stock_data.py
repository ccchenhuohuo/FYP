"""
股票数据采集模块
使用Yahoo Finance API获取并存储主要科技股的财务数据
"""
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from config import DB_CONFIG, TECH_TICKERS

def fetch_stock_data():
    """
    获取所有股票代码的数据并整理为结构化DataFrame
    
    返回:
        tuple: 四个DataFrame，分别包含市场数据、基本面数据、资产负债表数据和利润表数据
    """
    # 创建空DataFrame用于存储不同类型的数据
    market_data = pd.DataFrame()
    fundamental_data = pd.DataFrame()
    balance_sheet_data = pd.DataFrame()
    income_statement_data = pd.DataFrame()
    
    # 获取当前时间作为数据获取时间戳
    current_time = datetime.now()
    
    for ticker in TECH_TICKERS:
        print(f"正在获取 {ticker} 的数据...")
        
        try:
            # 获取股票信息
            stock = yf.Ticker(ticker)
            
            # 获取历史价格数据 (从2018年开始)
            hist = stock.history(start="2018-01-01")
            if hist.empty:
                print(f"警告: 未能获取到 {ticker} 的历史数据")
                continue
            
            # 获取财务数据
            info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            # 市场数据表 (OHLCV)
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
            
            # 基本面数据表
            fundamental_row = {
                'ticker': ticker,
                'date': current_time,
                'market_cap': info.get('marketCap', None),
                'pe_ratio': info.get('trailingPE', None),
                'pb_ratio': info.get('priceToBook', None),
                'dividend_yield': info.get('dividendYield', None),
                'data_collected_at': current_time
            }
            
            # 添加收入和净利润数据（如果可用）
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
            
            # 资产负债表数据
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
            
            # 利润表数据
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
            print(f"获取 {ticker} 数据时出错: {str(e)}")
    
    return market_data, fundamental_data, balance_sheet_data, income_statement_data

def save_to_database(market_data, fundamental_data, balance_sheet_data, income_statement_data):
    """
    将所有收集的数据保存到MySQL数据库
    
    参数:
        market_data (DataFrame): 市场价格和交易量数据
        fundamental_data (DataFrame): 关键财务指标
        balance_sheet_data (DataFrame): 资产负债表信息
        income_statement_data (DataFrame): 利润表信息
    """
    # 创建数据库连接字符串
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
    
    try:
        # 创建数据库引擎
        engine = create_engine(connection_string, echo=False)
        
        # 检查是否有数据要保存
        if not market_data.empty:
            market_data.to_sql(name='market_data', con=engine, if_exists='replace', index=False)
            print(f"已保存 {len(market_data)} 条市场数据记录")
        else:
            print("没有市场数据可保存")
            
        if not fundamental_data.empty:
            fundamental_data.to_sql(name='fundamental_data', con=engine, if_exists='replace', index=False)
            print(f"已保存 {len(fundamental_data)} 条基本面数据记录")
        else:
            print("没有基本面数据可保存")
            
        if not balance_sheet_data.empty:
            balance_sheet_data.to_sql(name='balance_sheet', con=engine, if_exists='replace', index=False)
            print(f"已保存 {len(balance_sheet_data)} 条资产负债表数据记录")
        else:
            print("没有资产负债表数据可保存")
            
        if not income_statement_data.empty:
            income_statement_data.to_sql(name='income_statement', con=engine, if_exists='replace', index=False)
            print(f"已保存 {len(income_statement_data)} 条利润表数据记录")
        else:
            print("没有利润表数据可保存")
            
        print("所有数据已成功写入MySQL数据库!")
        
    except Exception as e:
        print(f"保存数据到数据库时出错: {str(e)}")

def clear_database():
    """
    清空数据库中的所有股票数据表
    """
    # 创建数据库连接字符串
    connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
    
    try:
        # 创建数据库引擎
        engine = create_engine(connection_string, echo=False)
        
        # 清空各个表
        with engine.connect() as connection:
            connection.execute("DELETE FROM market_data")
            connection.execute("DELETE FROM fundamental_data")
            connection.execute("DELETE FROM balance_sheet")
            connection.execute("DELETE FROM income_statement")
        
        print("所有数据表已成功清空!")
        
    except Exception as e:
        print(f"清空数据表时出错: {str(e)}")

def print_data_samples(market_data, fundamental_data, balance_sheet_data, income_statement_data):
    """
    打印每个DataFrame的样本行进行验证
    
    参数:
        market_data (DataFrame): 市场价格和交易量数据
        fundamental_data (DataFrame): 关键财务指标
        balance_sheet_data (DataFrame): 资产负债表信息
        income_statement_data (DataFrame): 利润表信息
    """
    print("\n===================== 数据样本 =====================")
    
    print("\n市场数据:")
    if not market_data.empty:
        # 显示每个股票的最新一条记录
        latest_records = market_data.sort_values('date').groupby('ticker').tail(1)
        print(latest_records[['ticker', 'date', 'open', 'close', 'volume']].head(7))
    else:
        print("无数据")
        
    print("\n基本面数据:")
    if not fundamental_data.empty:
        print(fundamental_data[['ticker', 'date', 'market_cap', 'pe_ratio', 'pb_ratio']].head(7))
    else:
        print("无数据")
        
    print("\n资产负债表数据:")
    if not balance_sheet_data.empty:
        print(balance_sheet_data[['ticker', 'date', 'current_assets', 'current_liabilities']].head(7))
    else:
        print("无数据")
        
    print("\n利润表数据:")
    if not income_statement_data.empty:
        print(income_statement_data[['ticker', 'date', 'revenue', 'net_income']].head(7))
    else:
        print("无数据")
        
    print("\n=====================================================")

# 测试函数
def run_stock_data_collection():
    """运行股票数据采集和存储流程"""
    print("开始获取股票数据...")
    
    # 获取所有股票数据
    market_data, fundamental_data, balance_sheet_data, income_statement_data = fetch_stock_data()
    
    # 显示每个数据集的记录计数
    print(f"\n获取到 {len(market_data)} 条市场数据记录")
    print(f"获取到 {len(fundamental_data)} 条基本面数据记录")
    print(f"获取到 {len(balance_sheet_data)} 条资产负债表数据记录")
    print(f"获取到 {len(income_statement_data)} 条利润表数据记录")
    
    # 打印样本数据进行验证
    print_data_samples(market_data, fundamental_data, balance_sheet_data, income_statement_data)
    
    # 保存所有数据到数据库
    save_to_database(market_data, fundamental_data, balance_sheet_data, income_statement_data)
    
    print("\n数据采集和存储完成!") 