"""
管理员相关路由
包含管理员仪表盘、资金交易管理和订单管理的路由
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user
from functools import wraps
from models import db, User, Order, Transaction, FundTransaction, AccountBalance, Portfolio
from datetime import datetime, timedelta
from sqlalchemy import func, desc, asc
import pandas as pd
from utils import create_safe_dict

from . import admin_bp

# 管理员权限检查装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录管理员账户', 'warning')
            return redirect(url_for('auth.admin_login'))
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            flash('您没有管理员权限访问此页面', 'danger')
            logout_user()
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_daily_counts(model, date_column, count_column, days=30, filter_criteria=None):
    """Helper function to get daily counts for the last N days."""
    end_date = datetime.utcnow().date() + timedelta(days=1) # Include today
    start_date = end_date - timedelta(days=days)
    
    query = db.session.query(
        func.date(date_column).label('date'),
        func.count(count_column).label('count')
    ).filter(
        date_column >= start_date,
        date_column < end_date
    )
    
    if filter_criteria is not None:
        query = query.filter(filter_criteria)
        
    results = query.group_by(func.date(date_column)).order_by(func.date(date_column)).all()
    
    counts_dict = {item.date.strftime('%Y-%m-%d'): item.count for item in results}
    date_list = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    final_counts = [counts_dict.get(date, 0) for date in date_list]
    
    return date_list, final_counts

@admin_bp.route('/')
@admin_bp.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    管理员仪表盘 V2
    显示核心统计数据和趋势图
    """
    # --- Core Stats --- 
    users_count = User.query.count()
    orders_count = Order.query.count()
    transactions_count = FundTransaction.query.count()
    deposits_count = FundTransaction.query.filter_by(transaction_type='deposit').count()
    withdrawals_count = FundTransaction.query.filter_by(transaction_type='withdrawal').count()
    
    # --- Recent Activity --- 
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_fund_transactions = FundTransaction.query.order_by(FundTransaction.created_at.desc()).limit(5).all()

    # --- Chart Data (Last 30 days) --- 
    chart_days = 30
    labels, user_data = get_daily_counts(User, User.created_at, User.user_id, days=chart_days)
    _, order_data = get_daily_counts(Order, Order.created_at, Order.order_id, days=chart_days)
    _, transaction_data = get_daily_counts(FundTransaction, FundTransaction.created_at, FundTransaction.transaction_id, days=chart_days)
    _, deposit_data = get_daily_counts(FundTransaction, FundTransaction.created_at, FundTransaction.transaction_id, days=chart_days, filter_criteria=(FundTransaction.transaction_type == 'deposit'))
    _, withdrawal_data = get_daily_counts(FundTransaction, FundTransaction.created_at, FundTransaction.transaction_id, days=chart_days, filter_criteria=(FundTransaction.transaction_type == 'withdrawal'))

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "New Users",
                "data": user_data,
                "borderColor": '#36A2EB',
                "backgroundColor": 'rgba(54, 162, 235, 0.1)',
                "fill": "true",
                "tension": 0.1
            },
            {
                "label": "Orders",
                "data": order_data,
                "borderColor": '#FF6384',
                "backgroundColor": 'rgba(255, 99, 132, 0.1)',
                "fill": "true",
                "tension": 0.1
            },
             {
                "label": "Transactions", # All Fund Transactions
                "data": transaction_data,
                "borderColor": '#FFCE56',
                "backgroundColor": 'rgba(255, 206, 86, 0.1)',
                "fill": "true",
                "tension": 0.1
            },
            {
                "label": "Deposits",
                "data": deposit_data,
                "borderColor": '#4BC0C0',
                "backgroundColor": 'rgba(75, 192, 192, 0.1)',
                "fill": "true",
                "tension": 0.1
            },
            {
                "label": "Withdrawals",
                "data": withdrawal_data,
                "borderColor": '#9966FF',
                "backgroundColor": 'rgba(153, 102, 255, 0.1)',
                "fill": "true",
                "tension": 0.1
            }
        ]
    }

    return render_template(
        'admin/dashboard.html',
        users_count=users_count,
        orders_count=orders_count,
        transactions_count=transactions_count, 
        deposits_count=deposits_count,       
        withdrawals_count=withdrawals_count, 
        recent_orders=recent_orders,
        recent_fund_transactions=recent_fund_transactions,
        chart_data=chart_data
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """
    用户管理页面
    显示所有用户及其详细信息
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    query = User.query
    if search:
        query = query.filter(
            (User.user_name.like(f'%{search}%')) | 
            (User.user_email.like(f'%{search}%'))
        )
    query = query.order_by(asc(User.user_name))
    pagination = query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    # Render the renamed template
    return render_template(
        'admin/user_management.html', 
        users=users,
        pagination=pagination,
        search=search
    )

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    """
    查看用户详情
    """
    user = User.query.get_or_404(user_id)
    # Assuming user_detail.html is kept
    return render_template('admin/user_detail.html', user=user)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """
    编辑用户信息
    """
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.user_name = request.form.get('user_name')
        user.user_email = request.form.get('user_email')
        account_status_str = request.form.get('account_status')
        if account_status_str:
            from models.enums import AccountStatus
            try:
                user.account_status = AccountStatus[account_status_str]
            except KeyError:
                flash(f'Invalid account status: {account_status_str}', 'danger')
                # Consider not committing or returning early
        
        # TODO: Update balance requires careful handling - is this intended?
        # balance_str = request.form.get('balance')
        # if balance_str is not None:
        #     try:
        #         new_balance = float(balance_str)
        #         if user.balance:
        #             user.balance.available_balance = new_balance 
        #             # Recalculate total balance if needed
        #             user.balance.total_balance = user.balance.available_balance + user.balance.frozen_balance
        #         else:
        #             # Create balance if not exists? Should be ensured by init_db
        #             pass
        #     except ValueError:
        #          flash('Invalid balance amount', 'danger')

        db.session.commit()
        flash('用户信息已更新', 'success')
        return redirect(url_for('admin.view_user', user_id=user.user_id))
    
    # Render the renamed template
    return render_template('admin/user_edit.html', user=user)

# Placeholder for manage_orders route - assuming it exists and renders the order template
@admin_bp.route('/orders') 
@login_required
@admin_required
def manage_orders():
    """管理订单"""
    user_email = request.args.get('user_email')
    buy_orders = []
    sell_orders = []
    completed_orders = []
    target_user = None

    if user_email:
        target_user = User.query.filter_by(user_email=user_email).first()
        if target_user:
            buy_orders = Order.query.filter_by(user_id=target_user.user_id, order_type='buy', order_status='pending').order_by(desc(Order.created_at)).all()
            sell_orders = Order.query.filter_by(user_id=target_user.user_id, order_type='sell', order_status='pending').order_by(desc(Order.created_at)).all()
            completed_orders = Order.query.filter(
                Order.user_id == target_user.user_id,
                Order.order_status.in_(['executed', 'rejected', 'cancelled', 'failed'])
            ).order_by(desc(Order.updated_at)).all()
        else:
            flash(f'User with email {user_email} not found.', 'warning')

    # Render the renamed template
    return render_template(
        'admin/order_management.html', 
        buy_orders=buy_orders,
        sell_orders=sell_orders,
        completed_orders=completed_orders,
        user_email=user_email
    )

@admin_bp.route('/fund-transactions', methods=['GET'])
@admin_required
def manage_fund_transactions():
    """管理所有资金交易 - Renders the new history template"""
    status = request.args.get('status', 'all')
    query = FundTransaction.query.join(User, FundTransaction.user_id == User.user_id)
    if status != 'all':
        query = query.filter(FundTransaction.status == status)
    
    transactions = query.order_by(FundTransaction.created_at.desc()).all()
    pending_transactions = [t for t in transactions if t.status == 'pending']
    completed_transactions = [t for t in transactions if t.status != 'pending']
    safe_pending = [create_safe_dict(t) for t in pending_transactions]
    safe_completed = [create_safe_dict(t) for t in completed_transactions]
    
    # Render the new history template
    return render_template(
        'admin/transaction_history.html',
        pending_transactions=safe_pending,
        completed_transactions=safe_completed,
        current_status=status,
        title='Transaction History' # Explicit title for this page
    )

@admin_bp.route('/deposits', methods=['GET'])
@admin_required
def manage_deposits():
    """管理充值和提现请求 - Renders the unified deposit/withdrawal template"""
    # Fetch Deposits
    deposit_transactions = FundTransaction.query.filter_by(
        transaction_type='deposit'
    ).join(User, FundTransaction.user_id == User.user_id).order_by(
        FundTransaction.created_at.desc()
    ).all()
    pending_deposits = [create_safe_dict(t) for t in deposit_transactions if t.status == 'pending']
    completed_deposits = [create_safe_dict(t) for t in deposit_transactions if t.status != 'pending']

    # Fetch Withdrawals
    withdrawal_transactions = FundTransaction.query.filter_by(
        transaction_type='withdrawal'
    ).join(User, FundTransaction.user_id == User.user_id).order_by(
        FundTransaction.created_at.desc()
    ).all()
    pending_withdrawals = [create_safe_dict(t) for t in withdrawal_transactions if t.status == 'pending']
    completed_withdrawals = [create_safe_dict(t) for t in withdrawal_transactions if t.status != 'pending']
    
    # Render the unified deposit/withdrawal template
    return render_template(
        'admin/deposit_withdrawal.html', 
        pending_deposits=pending_deposits,
        completed_deposits=completed_deposits,
        pending_withdrawals=pending_withdrawals,
        completed_withdrawals=completed_withdrawals,
        title='Deposit & Withdrawal Management'
    )

@admin_bp.route('/fund-transactions/<transaction_id>/approve', methods=['POST'])
@admin_required
def approve_fund_transaction(transaction_id):
    """批准资金交易"""
    transaction = FundTransaction.query.get_or_404(transaction_id)
    if transaction.status != 'pending':
        flash('该交易已经被处理', 'danger')
    else:
        transaction.status = 'approved'
        transaction.updated_at = datetime.utcnow()
        
        # Update balance based on transaction type
        account_balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
        if not account_balance:
             # This shouldn't happen if init_db ensures balances
             account_balance = AccountBalance(user_id=transaction.user_id)
             db.session.add(account_balance)
        
        if transaction.transaction_type == 'deposit':
            account_balance.available_balance += transaction.amount
            account_balance.total_balance += transaction.amount
            flash('充值已批准，用户余额已更新', 'success')
        elif transaction.transaction_type == 'withdrawal':
            # On approval, the money is considered sent, reduce available
            # Frozen balance was likely handled during withdrawal request creation
            account_balance.frozen_balance -= transaction.amount # Unfreeze the amount
            # No change to available or total yet, actual transfer happens separately maybe?
            # OR: Assume approval means deducted from available:
            # account_balance.available_balance -= transaction.amount # If approval means deduction
            # account_balance.total_balance -= transaction.amount
            flash('提现已批准', 'success') 
            # Note: Ensure withdrawal logic correctly handles frozen/available balance flow
        
        db.session.commit()

    # Redirect back to the specific page (deposit or withdrawal)
    if transaction.transaction_type == 'deposit':
        return redirect(url_for('admin.manage_deposits'))
    else:
        return redirect(url_for('admin.manage_withdrawals'))

@admin_bp.route('/fund-transactions/<transaction_id>/reject', methods=['POST'])
@admin_required
def reject_fund_transaction(transaction_id):
    """拒绝资金交易"""
    transaction = FundTransaction.query.get_or_404(transaction_id)
    if transaction.status != 'pending':
        flash('该交易已经被处理', 'danger')
    else:
        reject_reason = request.form.get('reject_reason', 'Rejected by admin')
        transaction.status = 'rejected'
        transaction.remark = reject_reason
        transaction.updated_at = datetime.utcnow()
        
        # If it was a withdrawal, unfreeze the balance
        if transaction.transaction_type == 'withdrawal':
            account_balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
            if account_balance:
                account_balance.frozen_balance -= transaction.amount
                account_balance.available_balance += transaction.amount # Return to available
                # Total balance remains the same
            flash('提现已拒绝，冻结金额已返还用户可用余额', 'success')
        else:
             flash('充值已拒绝', 'success')
             
        db.session.commit()
        
    # Redirect back to the specific page (deposit or withdrawal)
    if transaction.transaction_type == 'deposit':
        return redirect(url_for('admin.manage_deposits'))
    else:
        return redirect(url_for('admin.manage_withdrawals'))

# Placeholder for reject_order route
@admin_bp.route('/orders/<order_id>/reject', methods=['POST'])
@admin_required
def reject_order(order_id):
    """拒绝挂单"""
    order = Order.query.get_or_404(order_id)
    if order.order_status != 'pending':
         flash('Order has already been processed.', 'warning')
         return redirect(url_for('admin.manage_orders', user_email=order.user.user_email))
    
    rejection_reason = request.form.get('rejection_reason', 'Rejected by admin')
    order.order_status = 'rejected'
    order.remark = rejection_reason # Assuming Order model has a remark field
    order.updated_at = datetime.utcnow()
    
    # If order rejection needs to unfreeze balance/assets, add logic here
    # Example: Unfreeze balance for a pending buy order
    if order.order_type == 'buy':
        account_balance = AccountBalance.query.filter_by(user_id=order.user_id).first()
        if account_balance:
            cost = order.order_price * order.order_quantity if order.order_execution_type == 'limit' else 0 # Market order cost is tricky
            # This needs refinement based on how frozen balance is calculated for orders
            # account_balance.frozen_balance -= cost
            # account_balance.available_balance += cost
            pass # Add actual unfreeze logic here
    
    # Example: Unfreeze assets for a pending sell order
    elif order.order_type == 'sell':
        portfolio = Portfolio.query.filter_by(user_id=order.user_id, ticker=order.ticker).first()
        if portfolio:
             # This needs refinement based on how frozen assets are calculated
             # portfolio.frozen_quantity -= order.order_quantity
             # portfolio.available_quantity += order.order_quantity
             pass # Add actual unfreeze logic here

    db.session.commit()
    flash(f'Order #{order_id} has been rejected.', 'success')
    return redirect(url_for('admin.manage_orders', user_email=order.user.user_email)) 