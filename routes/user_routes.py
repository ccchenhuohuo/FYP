"""
用户相关路由
包含股票图表和其他用户页面的路由
"""
from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import MarketData, db, Order, Transaction, User, FundamentalData, BalanceSheet, IncomeStatement, Portfolio, AccountBalance, FundTransaction
import pandas as pd
import sys
import io
import os
import json
import numpy as np
from decimal import Decimal
import requests  # 添加requests库用于API调用
import math

from . import user_bp
from utils.risk_monitor import run_analysis_text_only_simple
from utils.chat_ai import chat_with_gemini_api
from config import ALPHA_VANTAGE_API_KEY  # 从配置文件导入API密钥

# 配置Gemini API已移至utils/chat_ai.py

@user_bp.route('/stock_chart')
@login_required
def stock_chart():
    """显示股票历史走势页面"""
    # 检查当前用户是否为管理员
    if hasattr(current_user, 'admin_id'):
        flash('管理员账户无法访问用户股票交易页面', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
        
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
    """显示用户账户页面"""
    # 检查当前用户是否为管理员
    if hasattr(current_user, 'admin_id'):
        flash('管理员账户无法访问用户账户页面', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    # 获取用户余额信息
    account_balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
    if not account_balance:
        # 如果用户没有余额记录，创建一个
        account_balance = AccountBalance(
            user_id=current_user.user_id,
            available_balance=0,
            frozen_balance=0,
            total_balance=0
        )
        db.session.add(account_balance)
        db.session.commit()
    
    # 获取用户资金交易记录
    deposits = FundTransaction.query.filter_by(
        user_id=current_user.user_id, 
        transaction_type='deposit'
    ).order_by(FundTransaction.created_at.desc()).all()
    
    withdrawals = FundTransaction.query.filter_by(
        user_id=current_user.user_id, 
        transaction_type='withdrawal'
    ).order_by(FundTransaction.created_at.desc()).all()
    
    # 获取用户订单
    orders = Order.query.filter_by(user_id=current_user.user_id).order_by(Order.created_at.desc()).all()
    
    # 获取用户交易记录
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.transaction_time.desc()).all()
    
    # 获取用户持仓
    portfolio = Portfolio.query.filter_by(user_id=current_user.user_id).all()
    
    # 计算浮动盈亏
    total_pnl = 0
    for position in portfolio:
        # 使用新的函数获取价格和可能的错误消息
        current_price, error_msg = get_market_price_with_message(position.ticker)
        if current_price:
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.pnl = position.market_value - (position.average_price * position.quantity)
            position.pnl_percentage = (position.pnl / (position.average_price * position.quantity)) * 100 if position.average_price > 0 else 0
            total_pnl += position.pnl
        else:
            # 处理价格获取失败的情况
            position.current_price = None
            position.market_value = None
            position.pnl = None
            position.pnl_percentage = None
            position.price_error = error_msg
    
    return render_template('user/account.html', 
                          balance=account_balance,
                          deposits=deposits, 
                          withdrawals=withdrawals,
                          orders=orders, 
                          transactions=transactions,
                          portfolio=portfolio,
                          total_pnl=total_pnl)

@user_bp.route('/api/deposit', methods=['POST'])
@login_required
def deposit():
    """处理用户充值请求"""
    # 检查当前用户是否为管理员
    if hasattr(current_user, 'admin_id'):
        flash('管理员账户无法进行充值操作', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    amount = Decimal(request.form.get('amount', 0))
    
    if amount <= 0:
        flash('充值金额必须大于0', 'danger')
        return redirect(url_for('user.account'))
    
    # 创建充值记录，状态为pending
    deposit = FundTransaction(
        user_id=current_user.user_id,
        transaction_type='deposit',
        amount=float(amount),  # 转换为float类型
        status='pending',  # 默认为pending，需要管理员审核
        remark='用户充值申请'
    )
    
    try:
        db.session.add(deposit)
        db.session.commit()
        flash('充值请求已提交，等待管理员审核', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'充值请求提交失败: {str(e)}', 'danger')
    
    return redirect(url_for('user.account'))

@user_bp.route('/api/create_order', methods=['POST'])
@login_required
def create_order():
    """创建新订单"""
    # 检查当前用户是否为管理员
    if hasattr(current_user, 'admin_id'):
        flash('管理员账户无法创建交易订单', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
        
    ticker = request.form.get('ticker')
    order_type = request.form.get('order_type')
    order_execution_type = request.form.get('order_execution_type', 'limit')
    price = request.form.get('price', type=float)
    quantity = request.form.get('quantity', type=int)
    
    # 验证输入
    if not ticker or not order_type or not quantity or quantity <= 0:
        flash('请填写所有必填字段，并确保数量为正数', 'danger')
        return redirect(url_for('user.stock_chart'))
    
    # 对于限价单，价格是必需的
    if order_execution_type == 'limit' and (not price or price <= 0):
        flash('限价单必须指定有效的价格', 'danger')
        return redirect(url_for('user.stock_chart'))
    
    # 对于市价单，获取最新价格
    if order_execution_type == 'market':
        try:
            # 调用API获取最新价格
            latest_price, api_message = get_market_price_with_message(ticker)
            if not latest_price:
                if api_message and "API rate limit" in api_message:
                    # 专门处理API限制错误
                    flash(f'无法获取 {ticker} 的最新价格: {api_message}。建议：(1)等待次日重置；(2)使用限价单；(3)升级API计划移除限制。', 'danger')
                else:
                    # 处理其他错误
                    flash(f'无法获取 {ticker} 的最新价格: {api_message or "未知错误"}', 'danger')
                return redirect(url_for('user.stock_chart'))
            price = latest_price
        except Exception as e:
            flash(f'获取最新价格时出错: {str(e)}', 'danger')
            return redirect(url_for('user.stock_chart'))
    
    # 计算订单总价值
    total_value = price * quantity
    
    # 检查买入订单的余额
    if order_type == 'buy':
        account_balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
        if not account_balance or account_balance.available_balance < total_value:
            flash('余额不足，无法创建买入订单', 'danger')
            return redirect(url_for('user.stock_chart'))
    
    try:
        # 创建订单
        new_order = Order(
            user_id=current_user.user_id,
            ticker=ticker,
            order_type=order_type,
            order_price=price,
            order_quantity=quantity,
            order_execution_type=order_execution_type
        )
        
        # 如果是买入订单，冻结用户余额
        if order_type == 'buy':
            account_balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
            account_balance.available_balance -= total_value
            account_balance.frozen_balance += total_value
        
        db.session.add(new_order)
        db.session.commit()
        
        # 如果是市价单，立即执行
        if order_execution_type == 'market':
            success = execute_market_order(new_order)
            if success:
                flash(f'市价单已创建并执行成功，价格: ${price:.2f}', 'success')
            else:
                # 回滚到待执行状态，因为执行失败了
                new_order.order_status = 'pending'
                db.session.commit()
                flash(f'市价单已创建，但执行失败，将以待执行状态保留', 'warning')
        else:
            flash(f'限价单已创建，等待执行', 'success')
            
        # 订单创建成功后，重定向到账户页面
        return redirect(url_for('user.account'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'创建订单失败: {str(e)}', 'danger')
        print(f"创建订单错误: {str(e)}")
        # 创建订单失败，仍然重定向到股票图表页面
        return redirect(url_for('user.stock_chart'))

def get_latest_price(ticker):
    """获取股票最新价格，从实际的API获取"""
    try:
        # 使用Alpha Vantage API获取实时价格
        # 从配置文件中获取API密钥
        api_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        
        # 调用API
        response = requests.get(api_url)
        
        # 检查响应状态
        if response.status_code != 200:
            print(f"API请求失败: 状态码 {response.status_code}")
            return None
        
        # 解析响应数据
        data = response.json()
        
        # 检查API限制信息 - 修改判断条件以匹配实际响应格式
        if 'Information' in data and ('API rate limit' in data['Information'] or 'standard API rate limit' in data['Information']):
            print(f"API调用次数限制: {data['Information']}")
            return None
        
        # 检查是否有错误消息
        if 'Error Message' in data:
            print(f"API错误: {data['Error Message']}")
            return None
            
        # 检查是否达到API调用限制
        if 'Note' in data and 'API call frequency' in data['Note']:
            print(f"API调用频率限制: {data['Note']}")
            return None
        
        # 检查是否有全局报价数据
        if 'Global Quote' in data and data['Global Quote']:
            # 提取最新价格
            quote = data['Global Quote']
            if '05. price' in quote:
                price = float(quote['05. price'])
                print(f"成功获取{ticker}最新价格: ${price}")
                return price
                
        # API可能返回了空数据或不包含价格信息 - 检查是否因为API限制而无数据
        if 'Information' in data and not 'Global Quote' in data:
            print(f"API响应中没有价格数据，可能达到了API调用限制: {data['Information']}")
            return None
            
        print(f"无法从API响应中获取{ticker}的价格信息: {data}")
        return None
        
    except Exception as e:
        print(f"获取最新价格时出错: {str(e)}")
        return None

def execute_market_order(order):
    """执行市价单"""
    try:
        # 更新订单状态
        order.order_status = 'executed'
        order.executed_at = datetime.now()
        
        # 如果是买入订单，解冻余额并创建持仓
        if order.order_type == 'buy':
            # 获取账户余额
            account_balance = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if not account_balance:
                raise Exception("用户账户余额记录不存在")
                
            total_value = order.order_price * order.order_quantity
            
            # 解冻余额（已在创建订单时扣除）
            account_balance.frozen_balance -= total_value
            
            # 检查是否已有该股票的持仓
            portfolio_item = Portfolio.query.filter_by(
                user_id=order.user_id,
                ticker=order.ticker
            ).first()
            
            if portfolio_item:
                # 更新现有持仓
                portfolio_item.quantity += order.order_quantity
                portfolio_item.average_price = ((portfolio_item.average_price * (portfolio_item.quantity - order.order_quantity)) + 
                                        (order.order_price * order.order_quantity)) / portfolio_item.quantity
                portfolio_item.total_cost = portfolio_item.average_price * portfolio_item.quantity
                portfolio_item.last_updated = datetime.now()
            else:
                # 创建新持仓，确保average_price和total_cost不为null
                average_price = float(order.order_price)  # 确保转换为float类型
                total_cost = float(order.order_price * order.order_quantity)  # 确保转换为float类型
                
                # 检查计算结果是否为None或NaN
                if average_price is None or math.isnan(average_price):
                    average_price = 0.0
                if total_cost is None or math.isnan(total_cost):
                    total_cost = 0.0
                
                new_portfolio = Portfolio(
                    user_id=order.user_id,
                    ticker=order.ticker,
                    quantity=order.order_quantity,
                    average_price=average_price,
                    total_cost=total_cost,
                    last_updated=datetime.now()
                )
                db.session.add(new_portfolio)
        
        # 如果是卖出订单，更新持仓并增加余额
        elif order.order_type == 'sell':
            # 获取账户余额
            account_balance = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if not account_balance:
                raise Exception("用户账户余额记录不存在")
                
            total_value = order.order_price * order.order_quantity
            
            # 增加用户余额
            account_balance.available_balance += total_value
            account_balance.total_balance += total_value
            
            # 更新持仓
            portfolio_item = Portfolio.query.filter_by(
                user_id=order.user_id,
                ticker=order.ticker
            ).first()
            
            if portfolio_item and portfolio_item.quantity >= order.order_quantity:
                portfolio_item.quantity -= order.order_quantity
                portfolio_item.last_updated = datetime.now()
                # 如果持仓数量为0，删除该持仓记录
                if portfolio_item.quantity == 0:
                    db.session.delete(portfolio_item)
            else:
                # 持仓不足，回滚交易
                db.session.rollback()
                order.order_status = 'cancelled'
                order.remark = '持仓不足，无法执行卖出订单'
                db.session.commit()
                return False
        
        # 创建交易记录
        transaction = Transaction(
            user_id=order.user_id,
            order_id=order.order_id,
            ticker=order.ticker,
            transaction_type=order.order_type,
            transaction_price=order.order_price,
            transaction_quantity=order.order_quantity,
            transaction_amount=order.order_price * order.order_quantity
        )
        db.session.add(transaction)
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"执行市价单错误: {str(e)}")
        return False

@user_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """取消订单"""
    # 检查当前用户是否为管理员
    if hasattr(current_user, 'admin_id'):
        flash('管理员账户无法取消用户订单', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
        
    # 查找订单
    order = Order.query.filter_by(order_id=order_id, user_id=current_user.user_id).first()
    
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
            account_balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
            if account_balance:
                total_value = order.order_price * order.order_quantity
                account_balance.frozen_balance -= total_value
                account_balance.available_balance += total_value
        
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

@user_bp.route('/api/withdraw', methods=['POST'])
@login_required
def withdraw():
    """处理用户提现请求"""
    # 检查当前用户是否为管理员
    if hasattr(current_user, 'admin_id'):
        flash('管理员账户无法进行提现操作', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
        
    amount = Decimal(request.form.get('amount', 0))
    
    if amount <= 0:
        flash('提现金额必须大于0', 'danger')
        return redirect(url_for('user.account'))
    
    # 获取用户余额
    balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
    
    if not balance or balance.available_balance < float(amount):
        flash('余额不足，无法提现', 'danger')
        return redirect(url_for('user.account'))
    
    try:
        # 创建提现记录
        withdrawal = FundTransaction(
            user_id=current_user.user_id,
            transaction_type='withdrawal',
            amount=float(amount),  # 转换为float类型
            status='pending',  # 默认为pending，需要管理员审核
            remark='用户提现申请'
        )
        
        # 暂时冻结用户余额，将amount转换为float类型
        amount_float = float(amount)
        balance.available_balance -= amount_float
        balance.frozen_balance += amount_float
        # 总余额保持不变
        
        db.session.add(withdrawal)
        db.session.commit()
        flash('提现申请已提交，等待管理员审核', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'提现申请提交失败: {str(e)}', 'danger')
    
    return redirect(url_for('user.account'))

def get_market_price_with_message(ticker):
    """获取股票最新价格，同时返回API消息（如有）"""
    try:
        # 使用Alpha Vantage API获取实时价格
        # 从配置文件中获取API密钥
        api_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
        
        # 调用API
        response = requests.get(api_url)
        
        # 检查响应状态
        if response.status_code != 200:
            return None, f"API请求失败: 状态码 {response.status_code}"
        
        # 解析响应数据
        data = response.json()
        
        # 检查API限制信息
        if 'Information' in data:
            if 'API rate limit' in data['Information'] or 'standard API rate limit' in data['Information']:
                return None, data['Information']
        
        # 检查是否有错误消息
        if 'Error Message' in data:
            return None, data['Error Message']
            
        # 检查是否达到API调用限制
        if 'Note' in data and 'API call frequency' in data['Note']:
            return None, data['Note']
        
        # 检查是否有全局报价数据
        if 'Global Quote' in data and data['Global Quote']:
            # 提取最新价格
            quote = data['Global Quote']
            if '05. price' in quote:
                price = float(quote['05. price'])
                print(f"成功获取{ticker}最新价格: ${price}")
                return price, None
                
        # API可能返回了空数据或不包含价格信息
        if 'Information' in data and not 'Global Quote' in data:
            return None, data['Information']
            
        return None, f"无法解析API响应: {data}"
        
    except Exception as e:
        error_msg = f"获取最新价格时出错: {str(e)}"
        print(error_msg)
        return None, error_msg 

@user_bp.route('/api/real_time_stock_data')
@login_required
def get_real_time_stock_data():
    """获取实时股票数据API，代理Alpha Vantage请求"""
    symbol = request.args.get('symbol', 'AAPL')
    
    try:
        # 从配置文件获取API密钥
        api_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        
        # 发送请求到Alpha Vantage
        response = requests.get(api_url)
        
        if response.status_code != 200:
            return jsonify({"error": "网络响应错误"}), 500
            
        data = response.json()
        
        # 检查是否有错误消息或限制信息
        if data.get('Note') or data.get('Information'):
            return jsonify({
                "error": data.get('Note') or data.get('Information') or '请求限制，请稍后再试'
            }), 429
            
        # 将Alpha Vantage响应直接传递给前端
        return jsonify(data)
        
    except Exception as e:
        app.logger.error(f"获取实时股票数据失败: {str(e)}")
        return jsonify({"error": f"获取实时数据失败: {str(e)}"}), 500 