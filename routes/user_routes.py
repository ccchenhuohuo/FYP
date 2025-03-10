"""
用户相关路由
包含股票图表和其他用户页面的路由
"""
from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import MarketData, db, Order, Transaction, User, FundamentalData, BalanceSheet, IncomeStatement
import pandas as pd
import random
import google.generativeai as genai

from . import user_bp

# 配置Gemini API
GEMINI_API_KEY = "AIzaSyDYcL5BBKz812t_66bbBq0h3xm9v6DOG-M"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

@user_bp.route('/stock_chart')
@login_required
def stock_chart():
    """股票历史走势图页面"""
    return render_template('user/stock_chart.html')

@user_bp.route('/about')
@login_required
def about():
    """团队介绍页面"""
    return render_template('user/about.html')

@user_bp.route('/privacy')
@login_required
def privacy():
    """隐私政策页面"""
    return render_template('user/privacy.html')

@user_bp.route('/page2')
@login_required
def page2():
    """用户页面2路由"""
    return render_template('user/page2.html')

@user_bp.route('/page3')
@login_required
def page3():
    """用户页面3路由 - 重定向到股票风险分析页面"""
    return redirect(url_for('user.stock_analysis'))

@user_bp.route('/stock_analysis')
@login_required
def stock_analysis():
    """股票风险分析页面"""
    return render_template('user/stock_analysis.html')

@user_bp.route('/api/stock_analysis', methods=['POST'])
@login_required
def api_stock_analysis():
    """股票风险分析API"""
    try:
        # 获取请求数据 - 支持表单数据和JSON数据
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        print(f"收到股票分析请求: {data}")
        
        # 获取股票代码列表 - 支持多个股票代码输入
        tickers = data.getlist('tickers') if hasattr(data, 'getlist') else data.get('tickers', '').split(',')
        tickers = [t.strip() for t in tickers if t.strip()]
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 验证输入
        if not tickers:
            return jsonify({'error': '请提供至少一个股票代码'}), 400
        
        if not start_date or not end_date:
            return jsonify({'error': '请提供开始和结束日期'}), 400
        
        # 导入风险监控模块
        import sys
        import io
        import os
        import json
        
        # 确保当前目录在sys.path中
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        
        print(f"Python路径: {sys.path}")
        print(f"当前目录: {current_dir}")
        print(f"工作目录: {os.getcwd()}")
        
        # 检查risk_monitor.py文件是否存在
        risk_monitor_path = os.path.join(current_dir, 'risk_monitor.py')
        if not os.path.exists(risk_monitor_path):
            return jsonify({'error': f'找不到risk_monitor.py文件: {risk_monitor_path}'}), 500
        else:
            print(f"找到risk_monitor.py文件: {risk_monitor_path}")
        
        # 导入模块
        try:
            from risk_monitor import run_analysis_text_only_simple
            print("成功导入 risk_monitor 模块")
        except ImportError as e:
            error_msg = f'导入模块失败: {str(e)}'
            print(error_msg)
            return jsonify({'error': error_msg}), 500
        
        # 捕获打印输出
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        
        # 运行分析
        try:
            # 将股票代码列表转换为逗号分隔的字符串
            tickers_str = ','.join(tickers)
            print(f"开始分析: tickers={tickers_str}, start_date={start_date}, end_date={end_date}")
            
            # 运行分析
            analysis_results = run_analysis_text_only_simple(tickers_str, start_date, end_date)
            analysis_output = new_stdout.getvalue()
            print(f"分析完成，输出长度: {len(analysis_output)}")
            
            # 准备返回数据
            response_data = {
                'tickers': tickers,
                'start_date': start_date,
                'end_date': end_date,
                'data': analysis_results
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f'分析过程出错: {str(e)}\n{error_details}'
            print(error_msg)
            return jsonify({'error': error_msg}), 500
        finally:
            sys.stdout = old_stdout
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"股票分析API错误: {str(e)}\n{error_details}"
        print(error_msg)
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@user_bp.route('/account')
@login_required
def account():
    """用户账户详情页面，显示用户订单、交易记录和余额"""
    # 获取当前用户的订单
    orders = Order.query.filter_by(user_id=current_user.user_id).order_by(Order.created_at.desc()).all()
    
    # 获取当前用户的交易记录
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.transaction_time.desc()).all()
    
    return render_template('user/account.html', orders=orders, transactions=transactions)

@user_bp.route('/api/deposit', methods=['POST'])
@login_required
def deposit():
    """处理用户充值请求"""
    amount = request.form.get('amount', type=float)
    
    if not amount or amount <= 0:
        flash('请输入有效的充值金额', 'danger')
        return redirect(url_for('user.account'))
    
    try:
        # 更新用户余额
        user = User.query.get(current_user.user_id)
        user.balance += amount
        
        # 创建一个特殊的交易记录，用于记录充值
        # 为了适应Transaction表的结构，我们需要创建一个虚拟订单
        deposit_order = Order(
            user_id=current_user.user_id,
            ticker='DEPOSIT',  # 使用特殊的代码表示充值
            order_type='deposit',
            order_price=amount,
            order_quantity=1,
            order_status='executed'
        )
        db.session.add(deposit_order)
        db.session.flush()  # 获取order_id
        
        # 创建交易记录
        deposit_transaction = Transaction(
            order_id=deposit_order.order_id,
            user_id=current_user.user_id,
            ticker='DEPOSIT',
            transaction_type='deposit',
            transaction_price=amount,
            transaction_quantity=1,
            transaction_amount=amount,
            transaction_status='completed'
        )
        db.session.add(deposit_transaction)
        db.session.commit()
        
        flash(f'充值成功: {amount}元已添加到您的账户', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'充值失败: {str(e)}', 'danger')
    
    return redirect(url_for('user.account'))

@user_bp.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    """创建新订单"""
    ticker = request.form.get('ticker')
    order_type = request.form.get('order_type')
    order_price = request.form.get('price', type=float)
    order_quantity = request.form.get('quantity', type=int)
    
    if not all([ticker, order_type, order_price, order_quantity]):
        flash('请填写所有必填字段', 'danger')
        return redirect(url_for('user.account'))
    
    if order_quantity <= 0 or order_price <= 0:
        flash('价格和数量必须大于零', 'danger')
        return redirect(url_for('user.account'))
    
    # 检查用户余额是否足够（如果是买入订单）
    if order_type == 'buy':
        total_cost = order_price * order_quantity
        if current_user.balance < total_cost:
            flash('余额不足，无法创建订单', 'danger')
            return redirect(url_for('user.account'))
    
    try:
        # 创建新订单
        new_order = Order(
            user_id=current_user.user_id,
            ticker=ticker,
            order_type=order_type,
            order_price=order_price,
            order_quantity=order_quantity,
            order_status='pending'
        )
        db.session.add(new_order)
        db.session.commit()
        
        # 如果是买入订单，冻结用户余额
        if order_type == 'buy':
            user = User.query.get(current_user.user_id)
            user.balance -= order_price * order_quantity
            db.session.commit()
        
        flash('订单创建成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'订单创建失败: {str(e)}', 'danger')
    
    return redirect(url_for('user.account'))

@user_bp.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """取消订单"""
    order = Order.query.get_or_404(order_id)
    
    # 确保只能取消自己的订单
    if order.user_id != current_user.user_id:
        flash('无权操作此订单', 'danger')
        return redirect(url_for('user.account'))
    
    # 确保订单状态为待执行
    if order.order_status != 'pending':
        flash('只能取消待执行的订单', 'danger')
        return redirect(url_for('user.account'))
    
    try:
        # 更新订单状态
        order.order_status = 'cancelled'
        
        # 如果是买入订单，返还冻结的余额
        if order.order_type == 'buy':
            user = User.query.get(current_user.user_id)
            user.balance += order.order_price * order.order_quantity
        
        db.session.commit()
        flash('订单已取消', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'订单取消失败: {str(e)}', 'danger')
    
    return redirect(url_for('user.account'))

@user_bp.route('/api/market_data')
@login_required
def get_market_data():
    """
    获取股票市场数据的API端点
    参数:
        ticker: 股票代码 (例如: AAPL, MSFT)
        range: 时间范围 (例如: 7, 30, 90, all)
    返回:
        JSON格式的股票市场数据
    """
    # 获取请求参数
    ticker = request.args.get('ticker', 'AAPL')
    range_param = request.args.get('range', 'all')
    
    try:
        # 构建查询
        query = MarketData.query.filter_by(ticker=ticker)
        
        # 应用时间范围过滤
        if range_param != 'all' and range_param.isdigit():
            days = int(range_param)
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(MarketData.date >= cutoff_date)
        
        # 按日期排序
        query = query.order_by(MarketData.date)
        
        # 执行查询
        market_data = query.all()
        
        # 如果没有数据，生成模拟数据
        if not market_data:
            return generate_demo_data(ticker, range_param)
        
        # 转换为JSON格式
        result = []
        for data in market_data:
            result.append({
                'ticker': data.ticker,
                'date': data.date.isoformat(),
                'open': data.open,
                'high': data.high,
                'low': data.low,
                'close': data.close,
                'volume': data.volume
            })
        
        return jsonify(result)
        
    except Exception as e:
        # 处理错误
        return jsonify({'error': str(e)}), 500

def generate_demo_data(ticker, range_param):
    """
    生成演示数据，当数据库中没有数据时使用
    """
    result = []
    today = datetime.now()
    
    # 确定生成多少天的数据
    if range_param == 'all':
        days = 180  # 默认半年
    else:
        days = int(range_param) if range_param.isdigit() else 30
    
    # 基础价格 - 不同股票有不同起点
    base_prices = {
        'AAPL': 150.0,
        'MSFT': 300.0,
        'AMZN': 130.0,
        'GOOGL': 120.0,
        'META': 300.0,
        'NFLX': 400.0,
        'TSLA': 250.0
    }
    
    base_price = base_prices.get(ticker, 100.0)
    price = base_price
    
    # 生成历史数据
    for i in range(days):
        date = today - timedelta(days=days-i)
        # 随机波动 ±3%
        change_pct = (random.random() - 0.5) * 0.06
        price = price * (1 + change_pct)
        
        # 确保价格在合理范围内波动
        if price < base_price * 0.7:
            price = base_price * 0.7
        elif price > base_price * 1.3:
            price = base_price * 1.3
            
        # 生成开高低收价格
        open_price = price * (1 + (random.random() - 0.5) * 0.02)
        high_price = max(open_price, price) * (1 + random.random() * 0.015)
        low_price = min(open_price, price) * (1 - random.random() * 0.015)
        volume = int(random.random() * 10000000 + 5000000)  # 500万到1500万之间
        
        result.append({
            'ticker': ticker,
            'date': date.isoformat(),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(price, 2),
            'volume': volume
        })
    
    return jsonify(result)

@user_bp.route('/api/fundamental_data', methods=['GET'])
@login_required
def get_fundamental_data():
    """获取股票基本面数据"""
    ticker = request.args.get('ticker', 'AAPL')
    
    # 查询最新的基本面数据
    try:
        fundamental = FundamentalData.query.filter_by(ticker=ticker).order_by(FundamentalData.date.desc()).first()
        
        if not fundamental:
            return jsonify({
                'status': 'error',
                'message': f'未找到股票 {ticker} 的基本面数据'
            }), 404
        
        data = {
            'ticker': fundamental.ticker,
            'date': fundamental.date.strftime('%Y-%m-%d'),
            'market_cap': fundamental.market_cap,
            'pe_ratio': fundamental.pe_ratio,
            'pb_ratio': fundamental.pb_ratio,
            'dividend_yield': fundamental.dividend_yield,
            'revenue': fundamental.revenue,
            'net_income': fundamental.net_income,
            'operating_cash_flow': fundamental.operating_cash_flow
        }
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        # 记录错误以便调试
        print(f"基本面数据查询错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取基本面数据时发生错误: {str(e)}'
        }), 500

@user_bp.route('/api/balance_sheet', methods=['GET'])
@login_required
def get_balance_sheet():
    """获取股票资产负债表数据"""
    ticker = request.args.get('ticker', 'AAPL')
    
    try:
        # 查询最新的资产负债表数据
        balance_sheet = BalanceSheet.query.filter_by(ticker=ticker).order_by(BalanceSheet.date.desc()).first()
        
        if not balance_sheet:
            return jsonify({
                'status': 'error',
                'message': f'未找到股票 {ticker} 的资产负债表数据'
            }), 404
        
        data = {
            'ticker': balance_sheet.ticker,
            'date': balance_sheet.date.strftime('%Y-%m-%d'),
            'current_assets': balance_sheet.current_assets,
            'non_current_assets': balance_sheet.non_current_assets,
            'total_assets': balance_sheet.current_assets + balance_sheet.non_current_assets if balance_sheet.current_assets and balance_sheet.non_current_assets else None,
            'current_liabilities': balance_sheet.current_liabilities,
            'non_current_liabilities': balance_sheet.non_current_liabilities,
            'total_liabilities': balance_sheet.current_liabilities + balance_sheet.non_current_liabilities if balance_sheet.current_liabilities and balance_sheet.non_current_liabilities else None,
            'equity': (balance_sheet.current_assets + balance_sheet.non_current_assets) - (balance_sheet.current_liabilities + balance_sheet.non_current_liabilities) if all([balance_sheet.current_assets, balance_sheet.non_current_assets, balance_sheet.current_liabilities, balance_sheet.non_current_liabilities]) else None
        }
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        # 记录错误以便调试
        print(f"资产负债表数据查询错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取资产负债表数据时发生错误: {str(e)}'
        }), 500

@user_bp.route('/api/income_statement', methods=['GET'])
@login_required
def get_income_statement():
    """获取股票利润表数据"""
    ticker = request.args.get('ticker', 'AAPL')
    
    try:
        # 查询最新的利润表数据
        income_stmt = IncomeStatement.query.filter_by(ticker=ticker).order_by(IncomeStatement.date.desc()).first()
        
        if not income_stmt:
            return jsonify({
                'status': 'error',
                'message': f'未找到股票 {ticker} 的利润表数据'
            }), 404
        
        data = {
            'ticker': income_stmt.ticker,
            'date': income_stmt.date.strftime('%Y-%m-%d'),
            'revenue': income_stmt.revenue,
            'cost_of_revenue': income_stmt.cost_of_revenue,
            'gross_profit': income_stmt.revenue - income_stmt.cost_of_revenue if income_stmt.revenue and income_stmt.cost_of_revenue else None,
            'operating_income': income_stmt.operating_income,
            'income_before_tax': income_stmt.income_before_tax,
            'net_income': income_stmt.net_income,
            'profit_margin': round((income_stmt.net_income / income_stmt.revenue) * 100, 2) if income_stmt.net_income and income_stmt.revenue else None
        }
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        # 记录错误以便调试
        print(f"利润表数据查询错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取利润表数据时发生错误: {str(e)}'
        }), 500

@user_bp.route('/ai-assistant', methods=['GET'])
@login_required
def ai_assistant():
    """AI智能助手页面"""
    return render_template('user/ai_assistant.html')

@user_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """处理与AI助手的对话"""
    try:
        message = request.json.get('message', '')
        if not message:
            return jsonify({'error': '消息不能为空'}), 400

        # 创建聊天会话并发送消息
        chat = model.start_chat(history=[])
        response = chat.send_message(message)
        
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 