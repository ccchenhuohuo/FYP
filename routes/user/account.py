"""
用户账户相关路由
包含账户管理、资金存取和订单管理等功能
"""
from flask import render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Order, Transaction, User, Portfolio, AccountBalance, FundTransaction
from decimal import Decimal
import json
from utils.number_utils import RoundableDict
from utils.datetime_utils import safe_date_format

from . import user_bp

@user_bp.route('/account')
@login_required
def account():
    """
    用户账户页面
    显示账户余额、持仓情况和交易历史
    """
    # 获取用户账户信息
    account_balance = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
    
    # 如果用户没有账户余额记录，创建一个
    if not account_balance:
        account_balance = AccountBalance(
            user_id=current_user.user_id,
            available_balance=0.0,
            frozen_balance=0.0,
            total_balance=0.0
        )
        db.session.add(account_balance)
        db.session.commit()
    
    # 获取用户投资组合
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.user_id).all()
    
    # 计算投资组合总价值
    portfolio_value = 0
    portfolio_data = []
    
    # 处理投资组合数据
    for item in portfolio_items:
        # 增加市场价格和当前价值
        market_price = item.current_price if hasattr(item, 'current_price') else item.average_price
        current_value = market_price * item.quantity
        portfolio_value += current_value
        
        # 计算盈亏和盈亏百分比
        profit_loss = (market_price - item.average_price) * item.quantity
        pnl_percentage = 0
        if item.average_price > 0:
            pnl_percentage = (market_price - item.average_price) / item.average_price * 100
        
        # 构建模板数据
        portfolio_data.append({
            'ticker': item.ticker,
            'quantity': item.quantity,
            'average_price': item.average_price,
            'current_price': market_price,
            'current_value': current_value,
            'market_value': current_value,  # 添加市值字段
            'profit_loss': profit_loss,
            'pnl': profit_loss,  # 添加pnl字段
            'pnl_percentage': pnl_percentage  # 添加盈亏百分比
        })
    
    # 获取用户的交易记录
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.transaction_time.desc()).limit(10).all()
    
    # 获取用户的订单历史
    orders = Order.query.filter_by(user_id=current_user.user_id).order_by(Order.created_at.desc()).limit(10).all()
    
    # 转换订单数据格式以匹配模板期望的格式
    order_data = []
    for order in orders:
        # 添加调试信息
        print(f"订单ID: {order.order_id}, 状态: {order.order_status}, 价格: {order.order_price}")
        order_data.append({
            'order_id': order.order_id,  # 保持原字段名
            'id': order.order_id,        # 为模板添加id字段
            'ticker': order.ticker,
            'order_type': order.order_type,
            'type': order.order_type,    # 为模板添加type字段 
            'order_execution_type': order.order_execution_type,
            'execution_type': order.order_execution_type,  # 为模板添加execution_type字段
            'order_price': order.order_price,
            'price': order.order_price,  # 为模板添加price字段
            'order_quantity': order.order_quantity,
            'quantity': order.order_quantity,  # 为模板添加quantity字段
            'order_status': order.order_status,
            'status': order.order_status,  # 为模板添加status字段
            'created_at': safe_date_format(order.created_at),
            'updated_at': safe_date_format(order.updated_at),
            'executed_at': safe_date_format(order.executed_at)
        })
    
    # 获取用户资金交易记录
    fund_transactions = FundTransaction.query.filter_by(user_id=current_user.user_id).order_by(FundTransaction.created_at.desc()).limit(5).all()
    
    # 处理资金交易记录，确保字段名正确
    fund_tx_data = []
    for fund_tx in fund_transactions:
        fund_tx_data.append({
            'transaction_id': fund_tx.transaction_id,
            'user_id': fund_tx.user_id,
            'transaction_type': fund_tx.transaction_type,
            'amount': fund_tx.amount,
            'status': fund_tx.status,
            'created_at': safe_date_format(fund_tx.created_at),
            'updated_at': safe_date_format(fund_tx.updated_at),
            'remark': fund_tx.remark
        })
    
    # 处理交易记录，确保字段名正确
    transaction_data = []
    for tx in transactions:
        transaction_data.append({
            'transaction_id': tx.transaction_id,
            'order_id': tx.order_id,
            'user_id': tx.user_id,
            'ticker': tx.ticker,
            'transaction_type': tx.transaction_type,
            'transaction_price': tx.transaction_price,
            'transaction_quantity': tx.transaction_quantity,
            'transaction_amount': tx.transaction_amount,
            'transaction_time': safe_date_format(tx.transaction_time),
            'transaction_status': tx.transaction_status
        })
    
    # 渲染账户页面
    return render_template(
        'user/account.html',
        user=current_user,
        balance=account_balance,
        portfolio=portfolio_data,
        portfolio_value=portfolio_value,
        transactions=transaction_data,
        orders=order_data,
        fund_transactions=fund_tx_data
    )

@user_bp.route('/api/deposit', methods=['POST'])
@login_required
def deposit():
    """
    资金存入API
    处理用户存款请求
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'error': '缺少金额参数'}), 400
    
    try:
        # 验证金额
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': '存款金额必须大于0'}), 400
        
        # 创建存款交易记录
        fund_transaction = FundTransaction(
            user_id=current_user.user_id,
            amount=amount,
            transaction_type='deposit',
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(fund_transaction)
        db.session.commit()
        
        return jsonify({
            'message': '存款请求已提交，等待管理员审核',
            'transaction_id': fund_transaction.transaction_id
        })
        
    except ValueError:
        return jsonify({'error': '无效的金额格式'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'存款请求失败: {str(e)}'}), 500

@user_bp.route('/api/withdraw', methods=['POST'])
@login_required
def withdraw():
    """
    资金提取API
    处理用户取款请求
    """
    data = request.get_json()
    amount = data.get('amount')
    
    if not amount:
        return jsonify({'error': '缺少金额参数'}), 400
    
    try:
        # 验证金额
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': '取款金额必须大于0'}), 400
        
        # 检查用户账户余额
        account = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
        
        if not account:
            return jsonify({'error': '未找到账户信息'}), 404
        
        # 验证余额是否足够
        if account.available_balance < amount:
            return jsonify({'error': '账户余额不足'}), 400
        
        # 创建取款交易记录
        fund_transaction = FundTransaction(
            user_id=current_user.user_id,
            amount=amount,
            transaction_type='withdrawal',
            status='pending',
            created_at=datetime.utcnow()
        )
        
        # 将金额从可用余额转移到冻结余额
        account.available_balance -= amount
        account.frozen_balance += amount
        # 总余额保持不变，因为只是在两个余额之间转移
        
        db.session.add(fund_transaction)
        db.session.add(account)
        db.session.commit()
        
        return jsonify({
            'message': '取款请求已提交，等待管理员审核',
            'transaction_id': fund_transaction.transaction_id
        })
        
    except ValueError:
        return jsonify({'error': '无效的金额格式'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取款请求失败: {str(e)}'}), 500 