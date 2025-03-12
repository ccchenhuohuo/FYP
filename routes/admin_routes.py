"""
管理员相关路由
包含管理员仪表盘、资金交易管理和订单管理的路由
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Order, Transaction, FundTransaction, AccountBalance, Portfolio
from datetime import datetime
import pandas as pd

# 使用从__init__.py导入的蓝图
from . import admin_bp

# 管理员权限检查装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'danger')
            return redirect(url_for('auth.login'))
            
        # 只检查是否为Admin类型，移除User的is_admin检查
        if hasattr(current_user, 'admin_id'):
            return f(*args, **kwargs)
            
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    users_count = User.query.count()
    orders_count = Order.query.count()
    transactions_count = Transaction.query.count()
    
    # 获取待处理的提现和充值请求数量
    pending_withdrawals_count = FundTransaction.query.filter_by(
        transaction_type='withdrawal',
        status='pending'
    ).count()
    
    pending_deposits_count = FundTransaction.query.filter_by(
        transaction_type='deposit',
        status='pending'
    ).count()
    
    # 获取待处理的订单数量
    pending_orders_count = Order.query.filter_by(
        order_status='pending'
    ).count()
    
    return render_template('admin/dashboard.html', 
                           users_count=users_count,
                           orders_count=orders_count, 
                           transactions_count=transactions_count,
                           pending_withdrawals_count=pending_withdrawals_count,
                           pending_deposits_count=pending_deposits_count,
                           pending_orders_count=pending_orders_count)

@admin_bp.route('/fund_transactions')
@login_required
@admin_required
def manage_fund_transactions():
    transaction_type = request.args.get('type', 'all')
    status = request.args.get('status', 'all')
    
    # 构建基础查询
    query = FundTransaction.query
    
    # 应用过滤条件
    if transaction_type != 'all':
        query = query.filter_by(transaction_type=transaction_type)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    # 按时间排序，最新的在前
    transactions = query.order_by(FundTransaction.created_at.desc()).all()
    
    return render_template('admin/fund_transactions.html', 
                          transactions=transactions,
                          current_type=transaction_type,
                          current_status=status)

@admin_bp.route('/fund_transactions/<int:transaction_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_fund_transaction(transaction_id):
    transaction = FundTransaction.query.get_or_404(transaction_id)
    
    if transaction.status != 'pending':
        flash('只能处理待审核的交易请求', 'warning')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    # 获取用户余额记录
    balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
    if not balance:
        flash(f'用户 ID {transaction.user_id} 没有余额记录', 'danger')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    try:
        # 处理不同类型的交易
        if transaction.transaction_type == 'deposit':
            # 充值：增加可用余额
            balance.available_balance += float(transaction.amount)
            balance.total_balance += float(transaction.amount)
            
        elif transaction.transaction_type == 'withdrawal':
            # 提现：减少冻结余额（之前提现申请时已经从可用余额转移到了冻结余额）
            balance.frozen_balance -= float(transaction.amount)
            balance.total_balance -= float(transaction.amount)
            
        # 更新交易状态和备注
        transaction.status = 'completed'
        transaction.remark = f'{transaction.remark or ""}\n已批准 - {current_user.admin_name} 于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        transaction.operator_id = current_user.admin_id
        transaction.updated_at = datetime.now()
        
        db.session.commit()
        flash('交易请求已批准', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'处理失败: {str(e)}', 'danger')
    
    # 返回到相应类型的交易列表
    return redirect(url_for('admin.manage_fund_transactions', type=transaction.transaction_type))

@admin_bp.route('/fund_transactions/<int:transaction_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_fund_transaction(transaction_id):
    transaction = FundTransaction.query.get_or_404(transaction_id)
    rejection_reason = request.form.get('rejection_reason', '')
    
    if transaction.status != 'pending':
        flash('只能处理待审核的交易请求', 'warning')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    # 获取用户余额记录
    balance = AccountBalance.query.filter_by(user_id=transaction.user_id).first()
    if not balance:
        flash(f'用户 ID {transaction.user_id} 没有余额记录', 'danger')
        return redirect(url_for('admin.manage_fund_transactions'))
    
    try:
        # 处理不同类型的交易
        if transaction.transaction_type == 'deposit':
            # 充值拒绝：不需要修改余额
            pass
            
        elif transaction.transaction_type == 'withdrawal':
            # 提现拒绝：将冻结的余额返还给用户
            balance.frozen_balance -= float(transaction.amount)
            balance.available_balance += float(transaction.amount)
            # 总余额不变
            
        # 更新交易状态和备注
        transaction.status = 'rejected'
        transaction.remark = f'{transaction.remark or ""}\n已拒绝 - {rejection_reason} - {current_user.admin_name} 于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        transaction.operator_id = current_user.admin_id
        transaction.updated_at = datetime.now()
        
        db.session.commit()
        flash('交易请求已拒绝', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'处理失败: {str(e)}', 'danger')
    
    # 返回到相应类型的交易列表
    return redirect(url_for('admin.manage_fund_transactions', type=transaction.transaction_type))

# 保留旧的路由地址以保持兼容性
@admin_bp.route('/deposits')
@login_required
@admin_required
def manage_deposits():
    return redirect(url_for('admin.manage_fund_transactions', type='deposit'))

@admin_bp.route('/withdrawals')
@login_required
@admin_required
def manage_withdrawals():
    return redirect(url_for('admin.manage_fund_transactions', type='withdrawal'))

@admin_bp.route('/orders')
@login_required
@admin_required
def manage_orders():
    order_type = request.args.get('order_type', 'all')
    execution_type = request.args.get('execution_type', 'all')
    status = request.args.get('status', 'all')
    
    # 构建基础查询
    query = Order.query
    
    # 应用过滤条件
    if order_type != 'all':
        query = query.filter_by(order_type=order_type)
    
    if execution_type != 'all':
        query = query.filter_by(order_execution_type=execution_type)
    
    if status != 'all':
        query = query.filter_by(order_status=status)
    
    # 按时间排序，最新的在前
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', 
                          orders=orders,
                          current_order_type=order_type,
                          current_execution_type=execution_type,
                          current_status=status)

@admin_bp.route('/orders/<int:order_id>/execute', methods=['POST'])
@login_required
@admin_required
def execute_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.order_status != 'pending':
        flash('只能执行待处理的订单', 'warning')
        return redirect(url_for('admin.manage_orders'))
    
    try:
        # 执行市价单逻辑
        if order.order_execution_type == 'market':
            # 模拟市场价格 (实际应从行情API获取)
            current_price = order.order_price  # 假设当前价格就是订单价格
            
            # 执行订单
            # 1. 更新订单状态
            order.order_status = 'executed'
            order.updated_at = datetime.now()
            
            # 2. 创建交易记录
            transaction = Transaction(
                order_id=order.order_id,
                user_id=order.user_id,
                ticker=order.ticker,
                transaction_type=order.order_type,  # 'buy' 或 'sell'
                transaction_price=current_price,
                transaction_quantity=order.order_quantity,
                transaction_amount=current_price * order.order_quantity
            )
            db.session.add(transaction)
            
            # 3. 更新用户余额（如果是买入则已经冻结资金，如果是卖出则更新余额）
            account_balance = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if not account_balance:
                raise Exception(f"未找到用户ID {order.user_id} 的账户余额记录")
                
            if order.order_type == 'buy':
                # 买入：从冻结余额扣除实际成交金额，多余的返还到可用余额
                frozen_amount = order.order_price * order.order_quantity
                actual_amount = current_price * order.order_quantity
                refund = frozen_amount - actual_amount if frozen_amount > actual_amount else 0
                
                account_balance.frozen_balance -= frozen_amount
                account_balance.available_balance += refund
                
                # 更新用户持仓
                portfolio = Portfolio.query.filter_by(
                    user_id=order.user_id, 
                    ticker=order.ticker
                ).first()
                
                if portfolio:
                    # 更新现有持仓
                    portfolio.quantity += order.order_quantity
                    portfolio.updated_at = datetime.now()
                else:
                    # 创建新持仓
                    portfolio = Portfolio(
                        user_id=order.user_id,
                        ticker=order.ticker,
                        quantity=order.order_quantity
                    )
                    db.session.add(portfolio)
                    
            elif order.order_type == 'sell':
                # 卖出：增加可用余额
                transaction_amount = current_price * order.order_quantity
                account_balance.available_balance += transaction_amount
                
                # 更新用户持仓
                portfolio = Portfolio.query.filter_by(
                    user_id=order.user_id, 
                    ticker=order.ticker
                ).first()
                
                if portfolio:
                    # 确保持仓数量充足
                    if portfolio.quantity < order.order_quantity:
                        raise Exception(f"持仓数量不足: 需要 {order.order_quantity} 股，但只有 {portfolio.quantity} 股")
                    
                    # 更新持仓数量
                    portfolio.quantity -= order.order_quantity
                    portfolio.updated_at = datetime.now()
                    
                    # 如果持仓为0，可以选择删除该记录
                    if portfolio.quantity == 0:
                        db.session.delete(portfolio)
                else:
                    raise Exception(f"未找到用户ID {order.user_id} 的 {order.ticker} 持仓记录")
            
            # 提交事务
            db.session.commit()
            flash(f'订单 #{order.order_id} 已成功执行，成交价：{current_price}', 'success')
            
        # 执行限价单逻辑
        elif order.order_execution_type == 'limit':
            # 获取最新市场价格 (实际应从行情API获取)
            current_price = order.order_price  # 假设当前价格就是订单价格
            
            # 检查价格条件是否满足
            condition_met = False
            if order.order_type == 'buy' and current_price <= order.order_price:
                condition_met = True
            elif order.order_type == 'sell' and current_price >= order.order_price:
                condition_met = True
                
            if not condition_met:
                flash(f'当前市价不满足限价单执行条件', 'warning')
                return redirect(url_for('admin.manage_orders'))
                
            # 价格条件满足，执行订单（与市价单逻辑类似）
            order.order_status = 'executed'
            order.updated_at = datetime.now()
            
            transaction = Transaction(
                order_id=order.order_id,
                user_id=order.user_id,
                ticker=order.ticker,
                transaction_type=order.order_type,
                transaction_price=current_price,
                transaction_quantity=order.order_quantity,
                transaction_amount=current_price * order.order_quantity
            )
            db.session.add(transaction)
            
            # 更新余额和持仓（与市价单逻辑类似）
            account_balance = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if not account_balance:
                raise Exception(f"未找到用户ID {order.user_id} 的账户余额记录")
                
            if order.order_type == 'buy':
                frozen_amount = order.order_price * order.order_quantity
                actual_amount = current_price * order.order_quantity
                refund = frozen_amount - actual_amount if frozen_amount > actual_amount else 0
                
                account_balance.frozen_balance -= frozen_amount
                account_balance.available_balance += refund
                
                portfolio = Portfolio.query.filter_by(
                    user_id=order.user_id, 
                    ticker=order.ticker
                ).first()
                
                if portfolio:
                    portfolio.quantity += order.order_quantity
                    portfolio.updated_at = datetime.now()
                else:
                    portfolio = Portfolio(
                        user_id=order.user_id,
                        ticker=order.ticker,
                        quantity=order.order_quantity
                    )
                    db.session.add(portfolio)
                    
            elif order.order_type == 'sell':
                transaction_amount = current_price * order.order_quantity
                account_balance.available_balance += transaction_amount
                
                portfolio = Portfolio.query.filter_by(
                    user_id=order.user_id, 
                    ticker=order.ticker
                ).first()
                
                if portfolio:
                    if portfolio.quantity < order.order_quantity:
                        raise Exception(f"持仓数量不足: 需要 {order.order_quantity} 股，但只有 {portfolio.quantity} 股")
                    
                    portfolio.quantity -= order.order_quantity
                    portfolio.updated_at = datetime.now()
                    
                    if portfolio.quantity == 0:
                        db.session.delete(portfolio)
                else:
                    raise Exception(f"未找到用户ID {order.user_id} 的 {order.ticker} 持仓记录")
            
            # 提交事务
            db.session.commit()
            flash(f'限价单 #{order.order_id} 已成功执行，成交价：{current_price}', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'执行订单失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_orders'))

@admin_bp.route('/orders/<int:order_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_order(order_id):
    order = Order.query.get_or_404(order_id)
    rejection_reason = request.form.get('rejection_reason', '管理员拒绝')
    
    if order.order_status != 'pending':
        flash('只能拒绝待处理的订单', 'warning')
        return redirect(url_for('admin.manage_orders'))
    
    try:
        # 1. 更新订单状态
        order.order_status = 'rejected'
        order.updated_at = datetime.now()
        order.remark = f"拒绝原因: {rejection_reason}"
        
        # 2. 如果是买入订单，释放冻结的资金
        if order.order_type == 'buy':
            account_balance = AccountBalance.query.filter_by(user_id=order.user_id).first()
            if account_balance:
                frozen_amount = order.order_price * order.order_quantity
                account_balance.frozen_balance -= frozen_amount
                account_balance.available_balance += frozen_amount
        
        db.session.commit()
        flash(f'订单 #{order.order_id} 已被拒绝', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'拒绝订单失败: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_orders')) 