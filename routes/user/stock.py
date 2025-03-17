"""
用户股票相关路由
包含股票图表、行情数据等接口
"""
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import MarketData, FundamentalData, BalanceSheet, IncomeStatement
import pandas as pd
import numpy as np
from decimal import Decimal
import requests
import json

from . import user_bp
from utils.risk_monitor import run_analysis_text_only_simple

@user_bp.route('/stock_chart')
@login_required
def stock_chart():
    """
    股票历史走势图页面
    """
    return render_template('user/stock_chart.html')
    
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
    股票分析API
    接收股票代码和分析类型，返回分析结果
    """
    data = request.get_json()
    ticker = data.get('ticker')
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 获取市场数据
        market_data = MarketData.query.filter_by(ticker=ticker).order_by(MarketData.date.desc()).limit(252).all()
        
        if not market_data:
            return jsonify({'error': f'未找到{ticker}的市场数据'}), 404
        
        # 将数据转换为DataFrame
        df = pd.DataFrame([{
            'date': item.date,
            'open': float(item.open),
            'high': float(item.high),
            'low': float(item.low),
            'close': float(item.close),
            'volume': float(item.volume)
        } for item in market_data])
        
        df = df.sort_values('date')
        
        # 计算技术指标
        # 计算移动平均线 (20天和50天)
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        
        # 计算相对强弱指标 (RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 计算布林带
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['upperband'] = df['MA20'] + (df['close'].rolling(window=20).std() * 2)
        df['lowerband'] = df['MA20'] - (df['close'].rolling(window=20).std() * 2)
        
        # 计算MACD
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['histogram'] = df['MACD'] - df['signal']
        
        # 计算历史波动率
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=21).std() * np.sqrt(252) * 100
        
        # 计算风险评估
        current_price = float(df['close'].iloc[-1])
        risk_assessment = run_analysis_text_only_simple(ticker, current_price)
        
        # 准备返回数据
        # 转换DataFrame为JSON格式
        df_json = df.fillna('').to_dict(orient='records')
        
        # 准备技术指标数据
        latest = df.iloc[-1]
        tech_indicators = {
            'MA20': round(float(latest['MA20']), 2) if not pd.isna(latest['MA20']) else None,
            'MA50': round(float(latest['MA50']), 2) if not pd.isna(latest['MA50']) else None,
            'RSI': round(float(latest['RSI']), 2) if not pd.isna(latest['RSI']) else None,
            'MACD': round(float(latest['MACD']), 2) if not pd.isna(latest['MACD']) else None,
            'Signal': round(float(latest['signal']), 2) if not pd.isna(latest['signal']) else None,
            'Volatility': round(float(latest['volatility']), 2) if not pd.isna(latest['volatility']) else None,
            'Upper_Band': round(float(latest['upperband']), 2) if not pd.isna(latest['upperband']) else None,
            'Lower_Band': round(float(latest['lowerband']), 2) if not pd.isna(latest['lowerband']) else None
        }
        
        # 获取基本面数据
        fundamental = FundamentalData.query.filter_by(ticker=ticker).order_by(FundamentalData.fiscal_year.desc()).first()
        fundamental_data = {}
        
        if fundamental:
            fundamental_data = {
                'ticker': fundamental.ticker,
                'company_name': fundamental.company_name,
                'sector': fundamental.sector,
                'industry': fundamental.industry,
                'market_cap': float(fundamental.market_cap) if fundamental.market_cap else None,
                'pe_ratio': float(fundamental.pe_ratio) if fundamental.pe_ratio else None,
                'eps': float(fundamental.eps) if fundamental.eps else None,
                'dividend_yield': float(fundamental.dividend_yield) if fundamental.dividend_yield else None,
                'fiscal_year': fundamental.fiscal_year
            }
        
        # 组装结果
        result = {
            'ticker': ticker,
            'market_data': df_json,
            'technical_indicators': tech_indicators,
            'fundamental_data': fundamental_data,
            'risk_assessment': risk_assessment
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500
        
@user_bp.route('/api/market_data')
@login_required
def get_market_data():
    """
    获取市场数据API
    接收股票代码和日期范围，返回历史价格数据
    """
    ticker = request.args.get('ticker', '')
    days = request.args.get('days', default=365, type=int)
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 计算起始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 查询数据库
        market_data = MarketData.query.filter_by(ticker=ticker).filter(
            MarketData.date >= start_date
        ).order_by(MarketData.date).all()
        
        if not market_data:
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
        
        return jsonify(result)
        
    except Exception as e:
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
        fundamental = FundamentalData.query.filter_by(ticker=ticker).order_by(FundamentalData.fiscal_year.desc()).first()
        
        if not fundamental:
            return jsonify({'error': f'未找到{ticker}的基本面数据'}), 404
        
        # 格式化结果
        result = {
            'ticker': fundamental.ticker,
            'company_name': fundamental.company_name,
            'sector': fundamental.sector,
            'industry': fundamental.industry,
            'market_cap': float(fundamental.market_cap) if fundamental.market_cap else None,
            'pe_ratio': float(fundamental.pe_ratio) if fundamental.pe_ratio else None,
            'eps': float(fundamental.eps) if fundamental.eps else None,
            'dividend_yield': float(fundamental.dividend_yield) if fundamental.dividend_yield else None,
            'fiscal_year': fundamental.fiscal_year
        }
        
        return jsonify(result)
        
    except Exception as e:
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
        balance_sheet = BalanceSheet.query.filter_by(ticker=ticker).order_by(BalanceSheet.fiscal_year.desc()).first()
        
        if not balance_sheet:
            return jsonify({'error': f'未找到{ticker}的资产负债表数据'}), 404
        
        # 格式化结果
        result = {
            'ticker': balance_sheet.ticker,
            'fiscal_year': balance_sheet.fiscal_year,
            'total_assets': float(balance_sheet.total_assets) if balance_sheet.total_assets else None,
            'total_liabilities': float(balance_sheet.total_liabilities) if balance_sheet.total_liabilities else None,
            'total_equity': float(balance_sheet.total_equity) if balance_sheet.total_equity else None,
            'cash_and_equivalents': float(balance_sheet.cash_and_equivalents) if balance_sheet.cash_and_equivalents else None,
            'short_term_investments': float(balance_sheet.short_term_investments) if balance_sheet.short_term_investments else None,
            'accounts_receivable': float(balance_sheet.accounts_receivable) if balance_sheet.accounts_receivable else None,
            'inventory': float(balance_sheet.inventory) if balance_sheet.inventory else None,
            'current_assets': float(balance_sheet.current_assets) if balance_sheet.current_assets else None,
            'long_term_investments': float(balance_sheet.long_term_investments) if balance_sheet.long_term_investments else None,
            'current_liabilities': float(balance_sheet.current_liabilities) if balance_sheet.current_liabilities else None,
            'long_term_debt': float(balance_sheet.long_term_debt) if balance_sheet.long_term_debt else None
        }
        
        return jsonify(result)
        
    except Exception as e:
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
        income_statement = IncomeStatement.query.filter_by(ticker=ticker).order_by(IncomeStatement.fiscal_year.desc()).first()
        
        if not income_statement:
            return jsonify({'error': f'未找到{ticker}的利润表数据'}), 404
        
        # 格式化结果
        result = {
            'ticker': income_statement.ticker,
            'fiscal_year': income_statement.fiscal_year,
            'total_revenue': float(income_statement.total_revenue) if income_statement.total_revenue else None,
            'cost_of_revenue': float(income_statement.cost_of_revenue) if income_statement.cost_of_revenue else None,
            'gross_profit': float(income_statement.gross_profit) if income_statement.gross_profit else None,
            'operating_expenses': float(income_statement.operating_expenses) if income_statement.operating_expenses else None,
            'operating_income': float(income_statement.operating_income) if income_statement.operating_income else None,
            'net_income': float(income_statement.net_income) if income_statement.net_income else None,
            'eps': float(income_statement.eps) if income_statement.eps else None,
            'shares_outstanding': float(income_statement.shares_outstanding) if income_statement.shares_outstanding else None
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'获取利润表失败: {str(e)}'}), 500
        
@user_bp.route('/api/real_time_stock_data')
@login_required
def get_real_time_stock_data():
    """
    获取实时股票数据API
    使用外部API获取实时或近实时的股票价格数据
    """
    ticker = request.args.get('ticker', '')
    
    if not ticker:
        return jsonify({'error': '缺少股票代码参数'}), 400
    
    try:
        # 这里应该调用您的实时股票数据API
        # 此处为演示，返回最新的数据库记录
        latest_data = MarketData.query.filter_by(ticker=ticker).order_by(MarketData.date.desc()).first()
        
        if not latest_data:
            return jsonify({'error': f'未找到{ticker}的数据'}), 404
        
        # 格式化结果
        result = {
            'ticker': ticker,
            'price': float(latest_data.close),
            'change': float(latest_data.close) - float(latest_data.open),
            'change_percent': ((float(latest_data.close) - float(latest_data.open)) / float(latest_data.open)) * 100,
            'last_updated': latest_data.date.strftime('%Y-%m-%d'),
            'volume': float(latest_data.volume),
            'high': float(latest_data.high),
            'low': float(latest_data.low)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'获取实时数据失败: {str(e)}'}), 500 