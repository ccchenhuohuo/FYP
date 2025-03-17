"""
管理员相关路由
包含管理员仪表盘、资金交易管理和订单管理的路由
"""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Order, Transaction, FundTransaction, AccountBalance, Portfolio
from datetime import datetime
import pandas as pd

from . import admin_bp

# 管理员权限检查装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'danger')
            return redirect(url_for('auth.login'))
        
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('您没有管理员权限访问此页面', 'danger')
            if hasattr(current_user, 'is_admin'):
                return redirect(url_for('user.stock_chart'))
            else:
                return redirect(url_for('auth.login'))
        
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
    total_users = User.query.count()
    
    # 获取未处理的资金交易总数
    pending_fund_transactions = FundTransaction.query.filter_by(status='pending').count()
    
    # 获取未处理的订单总数
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # 获取最近的用户活动（最近5个注册用户）
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # 获取最近的订单活动（最近5个订单）
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # 获取最近的资金交易活动（最近5个资金交易）
    recent_fund_transactions = FundTransaction.query.order_by(
        FundTransaction.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        pending_fund_transactions=pending_fund_transactions,
        pending_orders=pending_orders,
        recent_users=recent_users,
        recent_orders=recent_orders,
        recent_fund_transactions=recent_fund_transactions
    )

@admin_bp.route('/fund_transactions')
@login_required
@admin_required
def manage_fund_transactions():
    """
    资金交易管理页面
    显示所有待处理的存款和取款请求
    """
    # 查询所有待处理的资金交易
    pending_transactions = FundTransaction.query.filter_by(status='pending').order_by(
        FundTransaction.created_at.desc()
    ).all()
    
    # 查询所有已完成的资金交易（最近30个）
    completed_transactions = FundTransaction.query.filter(
        FundTransaction.status.in_(['approved', 'rejected'])
    ).order_by(FundTransaction.updated_at.desc()).limit(30).all()
    
    return render_template(
        'admin/fund_transactions.html',
        pending_transactions=pending_transactions,
        completed_transactions=completed_transactions
    )

@admin_bp.route('/fund_transactions/<int:transaction_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_fund_transaction(transaction_id):
    """
    批准资金交易
    处理存款或取款请求的批准操作
    """
    transaction = FundTransaction.query.get_or_404(transaction_id)
    
    # 检查交易是否已处理
    if transaction.status != 'pending':
        flash('该交易已经被处理过', 'warning')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    try:
        # 更新交易状态为已批准
        transaction.status = 'approved'
        transaction.updated_at = datetime.utcnow()
        transaction.admin_id = current_user.id
        
        # 获取用户账户
        account = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
        
        # 如果用户没有账户，创建一个
        if not account:
            account = AccountBalance(user_id=transaction.user_id, balance=0)
            db.session.add(account)
        
        # 根据交易类型更新账户余额
        if transaction.transaction_type == 'deposit':
            account.balance += transaction.amount
        elif transaction.transaction_type == 'withdrawal':
            # 确保余额足够
            if account.balance < transaction.amount:
                raise ValueError('用户余额不足')
            account.balance -= transaction.amount
        
        # 保存更改
        db.session.commit()
        flash(f'已批准{transaction.transaction_type}请求', 'success')
    
    except ValueError as e:
        db.session.rollback()
        flash(f'无法批准交易: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'处理交易时发生错误: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_fund_transactions'))

@admin_bp.route('/fund_transactions/<int:transaction_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_fund_transaction(transaction_id):
    """
    拒绝资金交易
    处理存款或取款请求的拒绝操作
    """
    transaction = FundTransaction.query.get_or_404(transaction_id)
    
    # 检查交易是否已处理
    if transaction.status != 'pending':
        flash('该交易已经被处理过', 'warning')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    try:
        # 更新交易状态为已拒绝
        transaction.status = 'rejected'
        transaction.updated_at = datetime.utcnow()
        transaction.admin_id = current_user.id
        
        # 获取拒绝原因（如果提供）
        reject_reason = request.form.get('reject_reason', '')
        if reject_reason:
            transaction.admin_notes = reject_reason
        
        # 保存更改
        db.session.commit()
        flash(f'已拒绝{transaction.transaction_type}请求', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'处理交易时发生错误: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_fund_transactions'))

@admin_bp.route('/deposits')
@login_required
@admin_required
def manage_deposits():
    """
    存款管理页面
    筛选显示所有存款请求
    """
    return redirect(url_for('admin.manage_fund_transactions'))

@admin_bp.route('/withdrawals')
@login_required
@admin_required
def manage_withdrawals():
    """
    取款管理页面
    筛选显示所有取款请求
    """
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
    pending_orders = Order.query.filter_by(status='pending').order_by(
        Order.created_at.desc()
    ).all()
    
    # 查询所有已完成的订单（最近30个）
    completed_orders = Order.query.filter(
        Order.status.in_(['executed', 'rejected', 'cancelled'])
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
    if order.status != 'pending':
        flash('该订单已经被处理过', 'warning')
        return redirect(url_for('admin.manage_orders'))
    
    try:
        # 更新订单状态
        order.status = 'executed'
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
    if order.status != 'pending':
        flash('该订单已经被处理过', 'warning')
        return redirect(url_for('admin.manage_orders'))
    
    try:
        # 更新订单状态为已拒绝
        order.status = 'rejected'
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