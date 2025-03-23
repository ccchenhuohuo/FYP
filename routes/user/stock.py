"""
用户股票相关路由
包含股票图表、行情数据等接口
"""
from flask import render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import MarketData, FundamentalData, BalanceSheet, IncomeStatement
import pandas as pd
import numpy as np
from decimal import Decimal
import requests
import json
from config import ALPHA_VANTAGE_API_KEY
import traceback

from . import user_bp
from utils.risk_monitor import run_analysis_text_only_simple

@user_bp.route('/stock_chart')
@login_required
def stock_chart():
    """
    股票历史走势图页面
    """
    return render_template('user/stock_chart.html')

@user_bp.route('/stock_detail')
@login_required
def stock_detail():
    """
    股票详情页面重定向
    将stock_detail请求重定向到stock_chart，以统一入口
    """
    return redirect(url_for('user.stock_chart'))
    
@user_bp.route('/stock_analysis')
@login_required
def stock_analysis():
    """
    股票分析页面
    """
    return render_template('user/stock_analysis.html')
    
@user_bp.route('/api/stock_analysis', methods=['POST'])
@login_required
def api_stock_analysis():
    """
    股票风险分析API
    接收多个股票代码和日期范围，返回简化的风险分析结果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据，需要JSON格式'}), 400
            
        tickers = data.get('tickers', [])
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        print(f"接收到的分析请求: tickers={tickers}, start_date={start_date_str}, end_date={end_date_str}")
        
        if not tickers:
            return jsonify({'error': '缺少股票代码参数'}), 400
        
        # 解析日期范围
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            else:
                start_date = datetime.now() - timedelta(days=365)
                
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            else:
                end_date = datetime.now()
        except ValueError as e:
            return jsonify({'error': f'日期格式无效: {str(e)}'}), 400
        
        # 存储所有股票的风险评估结果
        results = []
        
        # 对每个股票进行风险评估
        for ticker in tickers:
            try:
                # 传递ticker字符串和日期范围
                risk_assessment = run_analysis_text_only_simple(ticker, str(start_date.date()), str(end_date.date()))
                
                # 组装单个股票的结果
                stock_result = {
                    'ticker': ticker,
                    'risk_assessment': risk_assessment,
                }
                results.append(stock_result)
            except Exception as risk_e:
                print(f"股票 {ticker} 风险评估计算错误: {str(risk_e)}")
                # 添加错误信息到结果
                stock_result = {
                    'ticker': ticker,
                    'error': f"无法计算风险: {str(risk_e)}"
                }
                results.append(stock_result)
        
        # 组装最终结果
        final_result = {
            'results': results,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        return jsonify(final_result)
        
    except Exception as e:
        # 记录详细错误信息
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        print(f"股票分析API错误: {error_msg}")
        print(f"错误详情: {stack_trace}")
        
        # 返回友好的错误信息
        return jsonify({'error': f'分析失败: {error_msg}'}), 500
        
@user_bp.route('/api/market_data')
@login_required
def get_market_data():
    """
    获取市场数据API
    接收股票代码和日期范围，返回历史价格数据
    """
    ticker = request.args.get('ticker', '')
    range_param = request.args.get('range', default='365')
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        print(f"正在获取 {ticker} 的市场数据，时间范围: {range_param}")
        
        # 处理特殊情况 - 全部时间范围
        if range_param == 'all':
            # 查询所有时间范围的数据
            market_data = MarketData.query.filter_by(ticker=ticker).order_by(MarketData.date).all()
            print(f"为股票 {ticker} 查询到 {len(market_data)} 条全部时间范围的记录")
        else:
            # 尝试将范围参数转换为天数
            try:
                days = int(range_param)
            except ValueError:
                days = 365  # 默认为一年
                
            # 计算起始日期
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 查询指定日期范围的数据
            market_data = MarketData.query.filter_by(ticker=ticker).filter(
                MarketData.date >= start_date
            ).order_by(MarketData.date).all()
            print(f"为股票 {ticker} 查询到 {len(market_data)} 条记录，日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        if not market_data:
            # 如果没有数据，尝试从YFinance获取
            print(f"数据库中没有找到 {ticker} 的数据，尝试从Yahoo Finance获取")
            try:
                import yfinance as yf
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3y")
                
                if hist.empty:
                    return jsonify({'error': f'无法获取{ticker}的市场数据'}), 404
                
                # 转换为API响应格式
                result = []
                for date, row in hist.iterrows():
                    result.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': float(row['Volume'])
                    })
                
                print(f"从Yahoo Finance获取到 {len(result)} 条 {ticker} 的记录")
                return jsonify(result)
            except Exception as yf_error:
                print(f"从Yahoo Finance获取数据失败: {str(yf_error)}")
                return jsonify({'error': f'未找到{ticker}的市场数据'}), 404
        
        # 格式化结果
        result = [{
            'date': item.date.strftime('%Y-%m-%d'),
            'open': float(item.open),
            'high': float(item.high),
            'low': float(item.low),
            'close': float(item.close),
            'volume': float(item.volume)
        } for item in market_data]
        
        print(f"成功格式化并返回 {len(result)} 条 {ticker} 的市场数据")
        return jsonify(result)
        
    except Exception as e:
        print(f"获取市场数据失败: {str(e)}")
        return jsonify({'error': f'获取市场数据失败: {str(e)}'}), 500
        
@user_bp.route('/api/fundamental_data', methods=['GET'])
@login_required
def get_fundamental_data():
    """
    获取基本面数据API
    接收股票代码，返回公司基本面信息
    """
    ticker = request.args.get('ticker', '')
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 查询数据库
        fundamental = FundamentalData.query.filter_by(ticker=ticker).order_by(FundamentalData.date.desc()).first()
        
        if not fundamental:
            return jsonify({'error': f'未找到{ticker}的基本面数据'}), 404
        
        # 安全转换函数
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                print(f"警告: 无法将值 {value} (类型: {type(value)}) 转换为浮点数")
                return None
        
        # 格式化结果
        result = {
            'ticker': fundamental.ticker,
            'date': fundamental.date.strftime('%Y-%m-%d') if fundamental.date else None,
            'market_cap': safe_float(fundamental.market_cap),
            'pe_ratio': safe_float(fundamental.pe_ratio),
            'pb_ratio': safe_float(fundamental.pb_ratio),
            'dividend_yield': safe_float(fundamental.dividend_yield),
            'revenue': safe_float(fundamental.revenue),
            'net_income': safe_float(fundamental.net_income),
            'operating_cash_flow': safe_float(fundamental.operating_cash_flow)
        }
        
        print(f"返回基本面数据: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"获取基本面数据失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': f'获取基本面数据失败: {str(e)}'}), 500
        
@user_bp.route('/api/balance_sheet', methods=['GET'])
@login_required
def get_balance_sheet():
    """
    获取资产负债表API
    接收股票代码，返回公司最近的资产负债表
    """
    ticker = request.args.get('ticker', '')
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 查询数据库
        balance_sheet = BalanceSheet.query.filter_by(ticker=ticker).order_by(BalanceSheet.date.desc()).first()
        
        if not balance_sheet:
            return jsonify({'error': f'未找到{ticker}的资产负债表数据'}), 404
        
        # 安全转换函数
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                print(f"警告: 无法将值 {value} (类型: {type(value)}) 转换为浮点数")
                return None
        
        # 格式化结果
        result = {
            'ticker': balance_sheet.ticker,
            'date': balance_sheet.date.strftime('%Y-%m-%d') if balance_sheet.date else None,
            'current_assets': safe_float(balance_sheet.current_assets),
            'non_current_assets': safe_float(balance_sheet.non_current_assets),
            'current_liabilities': safe_float(balance_sheet.current_liabilities),
            'non_current_liabilities': safe_float(balance_sheet.non_current_liabilities),
            'total_assets': (safe_float(balance_sheet.current_assets) or 0) + (safe_float(balance_sheet.non_current_assets) or 0),
            'total_liabilities': (safe_float(balance_sheet.current_liabilities) or 0) + (safe_float(balance_sheet.non_current_liabilities) or 0),
            'total_equity': ((safe_float(balance_sheet.current_assets) or 0) + (safe_float(balance_sheet.non_current_assets) or 0)) - 
                           ((safe_float(balance_sheet.current_liabilities) or 0) + (safe_float(balance_sheet.non_current_liabilities) or 0))
        }
        
        print(f"返回资产负债表数据: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"获取资产负债表数据失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': f'获取资产负债表失败: {str(e)}'}), 500
        
@user_bp.route('/api/income_statement', methods=['GET'])
@login_required
def get_income_statement():
    """
    获取利润表API
    接收股票代码，返回公司最近的利润表
    """
    ticker = request.args.get('ticker', '')
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 查询数据库
        income_statement = IncomeStatement.query.filter_by(ticker=ticker).order_by(IncomeStatement.date.desc()).first()
        
        if not income_statement:
            return jsonify({'error': f'未找到{ticker}的利润表数据'}), 404
        
        # 安全转换函数
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                print(f"警告: 无法将值 {value} (类型: {type(value)}) 转换为浮点数")
                return None
        
        # 格式化结果
        result = {
            'ticker': income_statement.ticker,
            'date': income_statement.date.strftime('%Y-%m-%d') if income_statement.date else None,
            'revenue': safe_float(income_statement.revenue),
            'cost_of_revenue': safe_float(income_statement.cost_of_revenue),
            'gross_profit': safe_float(income_statement.revenue) - safe_float(income_statement.cost_of_revenue) if income_statement.revenue and income_statement.cost_of_revenue else None,
            'operating_income': safe_float(income_statement.operating_income),
            'income_before_tax': safe_float(income_statement.income_before_tax),
            'net_income': safe_float(income_statement.net_income)
        }
        
        print(f"返回利润表数据: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"获取利润表数据失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': f'获取利润表失败: {str(e)}'}), 500
        
@user_bp.route('/api/real_time_stock_data')
@login_required
def get_real_time_stock_data():
    """
    获取实时股票数据API
    使用Alpha Vantage API获取实时或近实时的股票价格数据
    """
    symbol = request.args.get('symbol', '')
    
    if not symbol:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        print(f"尝试获取 {symbol} 的实时数据")
        
        # 安全转换函数
        def safe_float(value):
            if value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                print(f"警告: 无法将值 {value} (类型: {type(value)}) 转换为浮点数")
                return None
        
        # 调用Alpha Vantage API获取实时数据
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
        response = requests.get(url)
        data = response.json()
        
        if 'Global Quote' not in data or not data['Global Quote']:
            print(f"Alpha Vantage API返回无数据，回退到数据库")
            # 如果API调用失败或没有数据，回退到使用数据库的最新记录
            latest_data = MarketData.query.filter_by(ticker=symbol).order_by(MarketData.date.desc()).first()
            
            if not latest_data:
                return jsonify({'error': f'未找到{symbol}的数据'}), 404
            
            result = {
                'ticker': symbol,
                'price': safe_float(latest_data.close),
                'change': safe_float(latest_data.close) - safe_float(latest_data.open),
                'change_percent': ((safe_float(latest_data.close) - safe_float(latest_data.open)) / safe_float(latest_data.open)) * 100 if latest_data.open and latest_data.open != 0 else 0,
                'last_updated': latest_data.date.strftime('%Y-%m-%d') if latest_data.date else None,
                'volume': safe_float(latest_data.volume),
                'high': safe_float(latest_data.high),
                'low': safe_float(latest_data.low),
                'data_source': 'database'  # 标记数据来源
            }
        else:
            # 使用Alpha Vantage的实时数据
            quote = data['Global Quote']
            
            # 确保所有字段都使用安全转换
            current_price = safe_float(quote.get('05. price'))
            previous_close = safe_float(quote.get('08. previous close'))
            
            # 计算变化百分比，避免除以零
            if previous_close and previous_close != 0:
                change_percent = ((current_price or 0) - previous_close) / previous_close * 100
            else:
                change_percent = 0
                
            # 尝试从API响应中获取百分比，如果失败则使用计算值
            try:
                api_percent = quote.get('10. change percent', '').strip('%')
                change_percent = safe_float(api_percent) or change_percent
            except:
                pass
            
            result = {
                'ticker': symbol,
                'price': current_price,
                'change': current_price - previous_close if current_price and previous_close else 0,
                'change_percent': change_percent,
                'last_updated': quote.get('07. latest trading day'),
                'volume': safe_float(quote.get('06. volume')),
                'high': safe_float(quote.get('03. high')),
                'low': safe_float(quote.get('04. low')),
                'data_source': 'alpha_vantage'  # 标记数据来源
            }
        
        print(f"返回实时数据: {result}")
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        # 处理网络请求错误
        print(f"API请求失败: {str(e)}")
        return jsonify({'error': f'API请求失败: {str(e)}'}), 500
    except Exception as e:
        # 处理其他错误
        print(f"获取实时数据失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        return jsonify({'error': f'获取实时数据失败: {str(e)}'}), 500 