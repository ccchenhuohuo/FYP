"""
管理员相关路由
包含管理员仪表盘、资金交易管理和订单管理的路由
"""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user, logout_user
from functools import wraps
from models import db, User, Order, Transaction, FundTransaction, AccountBalance, Portfolio
from datetime import datetime
import pandas as pd
from utils import create_safe_dict

from . import admin_bp

# 管理员权限检查装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查用户是否已登录
        if not current_user.is_authenticated:
            flash('请先登录管理员账户', 'warning')
            return redirect(url_for('auth.admin_login'))
        
        # 检查用户是否为管理员
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('您没有管理员权限访问此页面', 'danger')
            
            # 登出当前用户（如果不是管理员）
            logout_user()
            
            # 重定向到管理员登录页面
            return redirect(url_for('auth.admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    管理员仪表盘
    显示系统统计数据和活动概览
    """
    # 获取用户总数
    users_count = User.query.count()
    
    # 获取订单总数
    orders_count = Order.query.count()
    
    # 获取交易总数
    transactions_count = Transaction.query.count()
    
    # 获取未处理的充值总数
    pending_deposits_count = FundTransaction.query.filter_by(status='pending', transaction_type='deposit').count()
    
    # 获取未处理的提现总数
    pending_withdrawals_count = FundTransaction.query.filter_by(status='pending', transaction_type='withdrawal').count()
    
    # 获取未处理的订单总数
    pending_orders_count = Order.query.filter_by(order_status='pending').count()
    
    # 获取最近的订单活动（最近5个订单）
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # 获取最近的资金交易活动（最近5个资金交易）
    recent_fund_transactions = FundTransaction.query.order_by(
        FundTransaction.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        users_count=users_count,
        orders_count=orders_count,
        transactions_count=transactions_count,
        pending_deposits_count=pending_deposits_count,
        pending_withdrawals_count=pending_withdrawals_count,
        pending_orders_count=pending_orders_count,
        recent_orders=recent_orders,
        recent_fund_transactions=recent_fund_transactions
    )

@admin_bp.route('/fund-transactions', methods=['GET'])
@admin_required
def manage_fund_transactions():
    """管理所有资金交易"""
    # 获取筛选条件
    transaction_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    
    # 构建查询
    query = FundTransaction.query.join(User, FundTransaction.user_id == User.user_id)
    
    # 应用过滤器
    if transaction_type != 'all':
        query = query.filter(FundTransaction.transaction_type == transaction_type)
    
    if status != 'all':
        query = query.filter(FundTransaction.status == status)
    
    # 获取所有交易
    transactions = query.order_by(FundTransaction.created_at.desc()).all()
    
    # 分离待处理和已完成的交易
    pending_transactions = [t for t in transactions if t.status == 'pending']
    completed_transactions = [t for t in transactions if t.status != 'pending']
    
    # 转换为安全的对象列表以避免日期时间问题
    safe_pending = [create_safe_dict(t) for t in pending_transactions]
    safe_completed = [create_safe_dict(t) for t in completed_transactions]
    
    return render_template(
        'admin/fund_transactions.html',
        pending_transactions=safe_pending,
        completed_transactions=safe_completed,
        current_type=transaction_type,
        current_status=status,
        title='资金交易管理'
    )

@admin_bp.route('/deposits', methods=['GET'])
@admin_required
def manage_deposits():
    """管理充值请求"""
    # 获取所有充值交易
    transactions = FundTransaction.query.filter_by(
        transaction_type='deposit'
    ).join(User, FundTransaction.user_id == User.user_id).order_by(
        FundTransaction.created_at.desc()
    ).all()
    
    # 分离待处理和已完成的交易
    pending_transactions = [t for t in transactions if t.status == 'pending']
    completed_transactions = [t for t in transactions if t.status != 'pending']
    
    # 转换为安全的对象列表以避免日期时间问题
    safe_pending = [create_safe_dict(t) for t in pending_transactions]
    safe_completed = [create_safe_dict(t) for t in completed_transactions]
    
    return render_template(
        'admin/fund_transactions.html',
        pending_transactions=safe_pending,
        completed_transactions=safe_completed,
        transaction_type='deposit',
        title='充值管理'
    )

@admin_bp.route('/withdrawals', methods=['GET'])
@admin_required
def manage_withdrawals():
    """管理提现请求"""
    # 获取所有提现交易
    transactions = FundTransaction.query.filter_by(
        transaction_type='withdrawal'
    ).join(User, FundTransaction.user_id == User.user_id).order_by(
        FundTransaction.created_at.desc()
    ).all()
    
    # 分离待处理和已完成的交易
    pending_transactions = [t for t in transactions if t.status == 'pending']
    completed_transactions = [t for t in transactions if t.status != 'pending']
    
    # 转换为安全的对象列表以避免日期时间问题
    safe_pending = [create_safe_dict(t) for t in pending_transactions]
    safe_completed = [create_safe_dict(t) for t in completed_transactions]
    
    return render_template(
        'admin/fund_transactions.html',
        pending_transactions=safe_pending,
        completed_transactions=safe_completed,
        transaction_type='withdrawal',
        title='提现管理'
    )

@admin_bp.route('/fund-transactions/<transaction_id>/approve', methods=['POST'])
@admin_required
def approve_fund_transaction(transaction_id):
    """批准资金交易"""
    transaction = FundTransaction.query.get_or_404(transaction_id)
    
    if transaction.status != 'pending':
        flash('该交易已经被处理', 'danger')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    # 设置交易状态为已批准
    transaction.status = 'approved'
    transaction.updated_at = datetime.utcnow()
    
    # 如果是充值交易，增加用户余额
    if transaction.transaction_type == 'deposit':
        # 获取用户的账户余额记录
        account_balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
        if not account_balance:
            account_balance = AccountBalance(
                user_id=transaction.user_id,
                available_balance=0.0,
                frozen_balance=0.0,
                total_balance=0.0
            )
            db.session.add(account_balance)
        
        # 更新可用余额和总余额
        account_balance.available_balance += float(transaction.amount)
        account_balance.total_balance = account_balance.available_balance + account_balance.frozen_balance
        db.session.add(account_balance)
    
    # 如果是提现交易，从冻结余额中扣除金额
    elif transaction.transaction_type == 'withdrawal':
        account_balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
        if account_balance:
            account_balance.frozen_balance -= float(transaction.amount)
            account_balance.total_balance = account_balance.available_balance + account_balance.frozen_balance
            db.session.add(account_balance)
        transaction.status = 'completed'
    
    db.session.add(transaction)
    
    try:
        db.session.commit()
        flash('交易已成功批准', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'处理交易时出错: {str(e)}', 'danger')
    
    # 根据交易类型重定向到相应页面
    if transaction.transaction_type == 'deposit':
        return redirect(url_for('admin.manage_deposits'))
    elif transaction.transaction_type == 'withdrawal':
        return redirect(url_for('admin.manage_withdrawals'))
    else:
        return redirect(url_for('admin.manage_fund_transactions'))

@admin_bp.route('/fund-transactions/<transaction_id>/reject', methods=['POST'])
@admin_required
def reject_fund_transaction(transaction_id):
    """拒绝资金交易"""
    transaction = FundTransaction.query.get_or_404(transaction_id)
    
    if transaction.status != 'pending':
        flash('该交易已经被处理', 'danger')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    # 获取拒绝理由
    reject_reason = request.form.get('reject_reason', '')
    
    # 设置交易状态为已拒绝
    transaction.status = 'rejected'
    transaction.remark = reject_reason
    transaction.updated_at = datetime.utcnow()
    
    # 如果是提现交易，将金额从冻结余额转回可用余额
    if transaction.transaction_type == 'withdrawal':
        # 获取用户的账户余额记录
        account_balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
        if account_balance:
            # 将金额从冻结余额转回可用余额
            account_balance.frozen_balance -= float(transaction.amount)
            account_balance.available_balance += float(transaction.amount)
            # 总余额保持不变，因为只是在两个余额之间转移
            db.session.add(account_balance)
    
    db.session.add(transaction)
    
    try:
        db.session.commit()
        flash('交易已被拒绝', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'处理交易时出错: {str(e)}', 'danger')
    
    # 根据交易类型重定向到相应页面
    if transaction.transaction_type == 'deposit':
        return redirect(url_for('admin.manage_deposits'))
    elif transaction.transaction_type == 'withdrawal':
        return redirect(url_for('admin.manage_withdrawals'))
    else:
        return redirect(url_for('admin.manage_fund_transactions'))

@admin_bp.route('/orders')
@login_required
@admin_required
def manage_orders():
    """
    订单管理页面
    显示所有待处理和已完成的订单
    """
    # 查询所有待处理的订单
    pending_orders = Order.query.filter_by(order_status='pending').order_by(
        Order.created_at.desc()
    ).all()
    
    # 查询所有已完成的订单（最近30个）
    completed_orders = Order.query.filter(
        Order.order_status.in_(['executed', 'rejected', 'cancelled'])
    ).order_by(Order.updated_at.desc()).limit(30).all()
    
    # 按类型分组订单
    buy_orders = [order for order in pending_orders if order.order_type == 'buy']
    sell_orders = [order for order in pending_orders if order.order_type == 'sell']
    
    return render_template(
        'admin/orders.html',
        buy_orders=buy_orders,
        sell_orders=sell_orders,
        completed_orders=completed_orders
    )

@admin_bp.route('/orders/<int:order_id>/execute', methods=['POST'])
@login_required
@admin_required
def execute_order(order_id):
    """
    执行订单
    处理买入或卖出订单的执行操作
    """
    order = Order.query.get_or_404(order_id)
    
    # 检查订单是否已处理
    if order.order_status != 'pending':
        flash('该订单已经被处理过', 'warning')
        return redirect(url_for('admin.manage_orders'))
    
    try:
        # 更新订单状态
        order.order_status = 'executed'
        order.updated_at = datetime.utcnow()
        order.admin_id = current_user.id
        
        # 获取执行价格
        price = float(request.form.get('execution_price', 0))
        if price <= 0:
            raise ValueError('执行价格必须大于0')
        
        # 获取用户账户
        account = AccountBalance.query.filter_by(user_id=order.user_id).first()
        if not account:
            raise ValueError('用户没有账户余额')
        
        # 获取用户投资组合
        portfolio = Portfolio.query.filter_by(user_id=order.user_id, ticker=order.ticker).first()
        
        # 计算交易总额
        total_amount = price * order.quantity
        
        # 处理买入订单
        if order.order_type == 'buy':
            # 检查余额是否足够
            if account.balance < total_amount:
                raise ValueError('用户余额不足')
            
            # 扣除账户余额
            account.balance -= total_amount
            
            # 更新投资组合
            if portfolio:
                # 如果已持有该股票，更新平均成本和数量
                old_value = portfolio.avg_price * portfolio.quantity
                new_value = old_value + total_amount
                new_quantity = portfolio.quantity + order.quantity
                portfolio.avg_price = new_value / new_quantity
                portfolio.quantity = new_quantity
            else:
                # 如果尚未持有该股票，创建新的投资组合条目
                portfolio = Portfolio(
                    user_id=order.user_id,
                    ticker=order.ticker,
                    quantity=order.quantity,
                    avg_price=price
                )
                db.session.add(portfolio)
        
        # 处理卖出订单
        elif order.order_type == 'sell':
            # 检查是否持有足够的股票
            if not portfolio or portfolio.quantity < order.quantity:
                raise ValueError('用户没有足够的股票')
            
            # 增加账户余额
            account.balance += total_amount
            
            # 更新投资组合
            portfolio.quantity -= order.quantity
            
            # 如果股票数量为0，删除投资组合条目
            if portfolio.quantity == 0:
                db.session.delete(portfolio)
        
        # 创建交易记录
        transaction = Transaction(
            user_id=order.user_id,
            order_id=order.id,
            ticker=order.ticker,
            quantity=order.quantity,
            price=price,
            total_amount=total_amount,
            transaction_type=order.order_type,
            status='completed',
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
        
        # 保存更改
        db.session.commit()
        flash(f'已执行{order.order_type}订单', 'success')
    
    except ValueError as e:
        db.session.rollback()
        flash(f'无法执行订单: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'处理订单时发生错误: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_orders'))

@admin_bp.route('/orders/<int:order_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_order(order_id):
    """
    拒绝订单
    处理买入或卖出订单的拒绝操作
    """
    order = Order.query.get_or_404(order_id)
    
    # 检查订单是否已处理
    if order.order_status != 'pending':
        flash('该订单已经被处理过', 'warning')
        return redirect(url_for('admin.manage_orders'))
    
    try:
        # 更新订单状态为已拒绝
        order.order_status = 'rejected'
        order.updated_at = datetime.utcnow()
        order.admin_id = current_user.id
        
        # 获取拒绝原因（如果提供）
        reject_reason = request.form.get('reject_reason', '')
        if reject_reason:
            order.admin_notes = reject_reason
        
        # 保存更改
        db.session.commit()
        flash(f'已拒绝{order.order_type}订单', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'处理订单时发生错误: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_orders')) 