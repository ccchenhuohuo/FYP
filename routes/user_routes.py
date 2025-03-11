"""
用户相关路由
包含股票图表和其他用户页面的路由
"""
from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import MarketData, db, Order, Transaction, User, FundamentalData, BalanceSheet, IncomeStatement
import pandas as pd
import sys
import io
import os
import json
import numpy as np

from . import user_bp
from utils.risk_monitor import run_analysis_text_only_simple
from utils.chat_ai import chat_with_gemini_api

# 配置Gemini API已移至utils/chat_ai.py

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
        
        # 获取日期范围
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # 获取用户自定义的风险阈值
        volatility_threshold = float(data.get('volatility_threshold', 30)) / 100  # 转换为小数
        drawdown_threshold = float(data.get('drawdown_threshold', 20)) / 100 * -1  # 转换为负小数
        sharpe_threshold = float(data.get('sharpe_threshold', 0))
        
        # 获取新增的风险阈值
        beta_threshold = float(data.get('beta_threshold', 1.2))
        var_threshold = float(data.get('var_threshold', 2)) / 100 * -1  # 转换为负小数
        sortino_threshold = float(data.get('sortino_threshold', 0))
        
        # 验证输入
        if not tickers:
            return jsonify({'error': '请提供至少一个股票代码'}), 400
        
        if not start_date or not end_date:
            return jsonify({'error': '请提供开始和结束日期'}), 400
        
        print(f"===== 开始分析股票 {tickers} =====")
        print(f"日期范围: {start_date} 至 {end_date}")
        print(f"风险阈值: 波动率={volatility_threshold:.2f}, 最大回撤={drawdown_threshold:.2f}, 夏普比率={sharpe_threshold:.2f}")
        print(f"额外风险阈值: 贝塔={beta_threshold:.2f}, VaR={var_threshold:.2f}, 索提诺比率={sortino_threshold:.2f}")
        
        # 捕获打印输出
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        
        try:
            # 将股票代码列表转换为逗号分隔的字符串
            tickers_str = ','.join(tickers)
            print(f"开始分析: tickers={tickers_str}, start_date={start_date}, end_date={end_date}")
            print(f"风险阈值: 波动率={volatility_threshold:.2f}, 最大回撤={drawdown_threshold:.2f}, 夏普比率={sharpe_threshold:.2f}")
            
            # 运行分析
            monitor = run_analysis_text_only_simple(tickers_str, start_date, end_date)
            analysis_output = new_stdout.getvalue()
            print(f"分析完成，输出长度: {len(analysis_output)}")
            
            # 构建前端期望的数据结构
            result_data = {}
            
            # 确保即使没有分析结果，也为每个ticker创建基本结构
            for ticker in tickers:
                result_data[ticker] = {
                    'name': ticker,
                    'metrics': {},
                    'alerts': [],
                    'analysis_text': f"无法获取{ticker}的分析数据"
                }
            
            print(f"===== 初始化结果数据结构 =====")
            print(f"初始化的result_data: {result_data}")
            
            # 如果有分析结果，填充数据
            if monitor and hasattr(monitor, 'risk_metrics'):
                print(f"===== 处理分析结果 =====")
                print(f"monitor.tickers: {monitor.tickers}")
                print(f"monitor.risk_metrics keys: {list(monitor.risk_metrics.keys())}")
                
                for ticker in monitor.tickers:
                    print(f"\n处理 {ticker} 的风险指标...")
                    if ticker in monitor.risk_metrics:
                        risk_data = monitor.risk_metrics[ticker]
                        print(f"{ticker} risk_data: {risk_data}")
                        
                        # 检查数据是否可用
                        if risk_data.get('data_available', False) == False:
                            # 数据不可用，提供错误信息
                            error_message = risk_data.get('error_message', '未知错误')
                            print(f"{ticker} 数据不可用: {error_message}")
                            result_data[ticker] = {
                                'name': ticker,
                                'metrics': {},
                                'alerts': [{
                                    "type": "danger", 
                                    "message": f"{ticker}数据获取失败: {error_message}"
                                }],
                                'analysis_text': analysis_output,
                                'data_available': False
                            }
                            continue
                        
                        # 将numpy数据类型转换为Python原生类型
                        metrics = {}
                        for key, value in risk_data.items():
                            if key == 'data_available':
                                continue
                            if isinstance(value, (np.float32, np.float64, np.int32, np.int64)):
                                metrics[key] = float(value)
                            elif value is None:
                                metrics[key] = None
                            else:
                                metrics[key] = value
                        
                        print(f"{ticker} 处理后的metrics: {metrics}")
                        
                        # 根据用户自定义阈值生成警报
                        alerts = []
                        
                        # 波动率警报
                        volatility = metrics.get('volatility')
                        if volatility is not None and volatility > volatility_threshold:
                            alerts.append({
                                "type": "warning", 
                                "message": f"{ticker}波动率为{volatility:.2%}，超过阈值{volatility_threshold:.2%}"
                            })
                        
                        # 最大回撤警报
                        max_drawdown = metrics.get('max_drawdown')
                        if max_drawdown is not None and max_drawdown < drawdown_threshold:
                            alerts.append({
                                "type": "danger", 
                                "message": f"{ticker}最大回撤为{max_drawdown:.2%}，超过阈值{drawdown_threshold:.2%}"
                            })
                        
                        # 夏普比率警报
                        sharpe_ratio = metrics.get('sharpe_ratio')
                        if sharpe_ratio is not None and sharpe_ratio < sharpe_threshold:
                            alerts.append({
                                "type": "warning", 
                                "message": f"{ticker}夏普比率为{sharpe_ratio:.2f}，低于阈值{sharpe_threshold:.2f}"
                            })
                            
                        # 贝塔系数警报
                        beta = metrics.get('beta')
                        if beta is not None and not np.isnan(beta) and beta > beta_threshold:
                            alerts.append({
                                "type": "warning", 
                                "message": f"{ticker}贝塔系数为{beta:.2f}，高于阈值{beta_threshold:.2f}"
                            })
                            
                        # VaR警报
                        var_95 = metrics.get('var_95')
                        if var_95 is not None and var_95 < var_threshold:
                            alerts.append({
                                "type": "danger", 
                                "message": f"{ticker}VaR(95%)为{var_95:.2%}，超过阈值{var_threshold:.2%}"
                            })
                            
                        # 索提诺比率警报
                        sortino_ratio = metrics.get('sortino_ratio')
                        if sortino_ratio is not None and sortino_ratio < sortino_threshold:
                            alerts.append({
                                "type": "warning", 
                                "message": f"{ticker}索提诺比率为{sortino_ratio:.2f}，低于阈值{sortino_threshold:.2f}"
                            })
                        
                        print(f"{ticker} 生成的警报: {alerts}")
                        
                        # 检查是否有缺失的指标
                        missing_metrics = []
                        if 'volatility' not in metrics or metrics['volatility'] is None:
                            missing_metrics.append('波动率')
                        if 'max_drawdown' not in metrics or metrics['max_drawdown'] is None:
                            missing_metrics.append('最大回撤')
                        if 'sharpe_ratio' not in metrics or metrics['sharpe_ratio'] is None:
                            missing_metrics.append('夏普比率')
                        
                        if missing_metrics:
                            alerts.append({
                                "type": "info", 
                                "message": f"无法计算以下指标: {', '.join(missing_metrics)}"
                            })
                        
                        # 更新结果数据
                        result_data[ticker] = {
                            'name': ticker,
                            'data_available': True,
                            'analysis_text': analysis_output,
                            'alerts': alerts
                        }
                        
                        # 直接将指标添加到结果数据的根级别
                        result_data[ticker].update(metrics)
                        
                        print(f"{ticker} 最终结果数据: {result_data[ticker]}")
            
            # 恢复标准输出
            sys.stdout = old_stdout
            
            # 返回结果
            return jsonify({
                'data': result_data,
                'start_date': start_date,
                'end_date': end_date
            })
            
        except Exception as e:
            # 恢复标准输出
            sys.stdout = old_stdout
            print(f"分析过程中出错: {str(e)}")
            raise
            
    except Exception as e:
        print(f"股票风险分析API错误: {str(e)}")
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

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
    """获取市场数据API"""
    ticker = request.args.get('ticker', 'AAPL')
    range_param = request.args.get('range', '30')
    
    try:
        # 查询数据库
        if range_param == 'all':
            # 获取所有数据
            market_data = MarketData.query.filter_by(ticker=ticker).order_by(MarketData.date).all()
        else:
            # 获取指定天数的数据
            days = int(range_param)
            cutoff_date = datetime.now() - timedelta(days=days)
            market_data = MarketData.query.filter_by(ticker=ticker).filter(MarketData.date >= cutoff_date).order_by(MarketData.date).all()
        
        # 如果数据库中没有数据，返回错误
        if not market_data:
            return jsonify({'error': f'没有找到 {ticker} 的市场数据'}), 404
        
        # 格式化数据
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
        return jsonify({'error': str(e)}), 500

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

        # 使用utils/chat_ai.py中的功能
        response_text = chat_with_gemini_api(message)
        
        return jsonify({'response': response_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 