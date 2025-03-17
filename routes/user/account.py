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
    
    for item in portfolio_items:
        # 获取当前市场价格
        item_value = item.average_price * item.quantity  # 使用平均价格代替实时价格
        portfolio_value += item_value
        
        # 使用RoundableDict代替普通字典
        portfolio_data.append(RoundableDict({
            'ticker': item.ticker,
            'quantity': item.quantity,
            'average_price': float(item.average_price),
            'current_price': float(item.average_price),  # 使用平均价格代替当前价格
            'market_value': float(item_value),
            'pnl': 0.0,  # 这里需要计算盈亏
            'pnl_percentage': 0.0  # 这里需要计算盈亏比例
        }))
    
    # 获取用户订单历史
    orders = Order.query.filter_by(user_id=current_user.user_id).order_by(Order.created_at.desc()).limit(10).all()
    order_history = []
    
    for order in orders:
        order_history.append(RoundableDict({
            'id': order.order_id,
            'ticker': order.ticker,
            'quantity': order.order_quantity,
            'order_type': order.order_type,
            'status': order.order_status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }))
    
    # 获取用户交易历史
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.transaction_time.desc()).limit(10).all()
    transaction_history = []
    
    for transaction in transactions:
        transaction_history.append(RoundableDict({
            'id': transaction.transaction_id,
            'ticker': transaction.ticker,
            'quantity': transaction.transaction_quantity,
            'price': float(transaction.transaction_price),
            'total_amount': float(transaction.transaction_amount),
            'transaction_type': transaction.transaction_type,
            'status': transaction.transaction_status,
            'created_at': transaction.transaction_time.strftime('%Y-%m-%d %H:%M:%S')
        }))
    
    # 获取用户资金交易历史
    fund_transactions = FundTransaction.query.filter_by(user_id=current_user.user_id).order_by(FundTransaction.created_at.desc()).limit(10).all()
    fund_history = []
    
    for fund_tx in fund_transactions:
        fund_history.append(RoundableDict({
            'id': fund_tx.transaction_id,
            'amount': float(fund_tx.amount),
            'transaction_type': fund_tx.transaction_type,
            'status': fund_tx.status,
            'created_at': fund_tx.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }))
    
    return render_template(
        'user/account.html',
        balance=account_balance,
        portfolio_value=portfolio_value,
        portfolio=portfolio_data,
        orders=order_history,
        transactions=transaction_history,
        fund_transactions=fund_history
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
            'transaction_id': fund_transaction.id
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
        if account.balance_id < amount:
            return jsonify({'error': '账户余额不足'}), 400
        
        # 创建取款交易记录
        fund_transaction = FundTransaction(
            user_id=current_user.user_id,
            amount=amount,
            transaction_type='withdrawal',
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(fund_transaction)
        db.session.commit()
        
        return jsonify({
            'message': '取款请求已提交，等待管理员审核',
            'transaction_id': fund_transaction.id
        })
        
    except ValueError:
        return jsonify({'error': '无效的金额格式'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取款请求失败: {str(e)}'}), 500 