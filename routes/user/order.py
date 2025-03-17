"""
用户订单相关路由
包含创建订单、取消订单等功能
"""
from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Order, AccountBalance, Portfolio

from . import user_bp

@user_bp.route('/api/create_order', methods=['POST'])
@login_required
def create_order():
    """
    创建订单API
    处理用户买入或卖出股票的请求
    """
    data = request.get_json()
    ticker = data.get('ticker')
    quantity = data.get('quantity')
    order_type = data.get('order_type')  # 'buy' 或 'sell'
    
    # 参数验证
    if not ticker or not quantity or not order_type:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        # 转换并验证数量
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({'error': '数量必须为正整数'}), 400
        
        # 验证订单类型
        if order_type not in ['buy', 'sell']:
            return jsonify({'error': '无效的订单类型'}), 400
        
        # 对于卖单，验证用户是否持有足够的股票
        if order_type == 'sell':
            portfolio = Portfolio.query.filter_by(
                user_id=current_user.id,
                ticker=ticker
            ).first()
            
            if not portfolio:
                return jsonify({'error': f'您没有持有{ticker}的股票'}), 400
                
            if portfolio.quantity < quantity:
                return jsonify({'error': f'您只持有{portfolio.quantity}股{ticker}，无法卖出{quantity}股'}), 400
        
        # 获取市场价格 (这里简化处理，实际应从市场数据获取)
        market_price = get_market_price_with_message(ticker)
        if isinstance(market_price, tuple) and len(market_price) == 2 and isinstance(market_price[0], str):
            # 返回错误消息
            return jsonify({'error': market_price[0]}), 400
        
        # 对于买单，验证用户是否有足够的资金
        if order_type == 'buy':
            account = AccountBalance.query.filter_by(user_id=current_user.id).first()
            
            if not account:
                return jsonify({'error': '您的账户余额不足'}), 400
                
            estimated_cost = market_price * quantity
            
            if account.balance < estimated_cost:
                return jsonify({
                    'error': f'账户余额不足。估计成本: ${estimated_cost:.2f}, 您的余额: ${float(account.balance):.2f}'
                }), 400
        
        # 创建订单
        order = Order(
            user_id=current_user.id,
            ticker=ticker,
            quantity=quantity,
            order_type=order_type,
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.commit()
        
        # 根据系统设置，可以选择自动执行市价单或等待管理员审核
        if False:  # 设置为自动执行市价单的条件
            execute_market_order(order)
        
        return jsonify({
            'message': f'已创建{order_type}单',
            'order_id': order.id,
            'estimated_price': market_price,
            'estimated_total': market_price * quantity
        })
        
    except ValueError as e:
        return jsonify({'error': f'无效的数量格式: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建订单失败: {str(e)}'}), 500

@user_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """
    取消订单API
    处理用户取消未执行订单的请求
    """
    try:
        # 查找订单
        order = Order.query.get_or_404(order_id)
        
        # 检查订单是否属于当前用户
        if order.user_id != current_user.id:
            return jsonify({'error': '您没有权限取消此订单'}), 403
        
        # 检查订单状态是否为待处理
        if order.status != 'pending':
            return jsonify({'error': f'无法取消已{order.status}的订单'}), 400
        
        # 更新订单状态
        order.status = 'cancelled'
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'已取消订单 #{order_id}',
            'order': {
                'id': order.id,
                'ticker': order.ticker,
                'quantity': order.quantity,
                'order_type': order.order_type,
                'status': order.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取消订单失败: {str(e)}'}), 500

def get_market_price_with_message(ticker):
    """
    获取股票市场价格
    如果价格不可用，返回错误消息
    否则返回价格
    
    返回值:
        float 或 tuple: 价格或包含错误消息的元组 (message, error_code)
    """
    try:
        from models import MarketData
        
        # 获取最新的市场数据
        latest_data = MarketData.query.filter_by(ticker=ticker).order_by(MarketData.date.desc()).first()
        
        if not latest_data:
            return (f"无法获取{ticker}的市场数据", 404)
        
        # 使用收盘价作为市场价格
        return float(latest_data.close)
        
    except Exception as e:
        return (f"获取市场价格时发生错误: {str(e)}", 500)

def execute_market_order(order):
    """
    执行市价单
    立即处理订单，更新账户余额和投资组合
    注意：此功能保留但当前禁用，使用管理员审核代替
    
    参数:
        order (Order): 要执行的订单对象
    """
    from models import Transaction, Portfolio, AccountBalance
    
    try:
        # 获取市场价格
        market_price = get_market_price_with_message(order.ticker)
        if isinstance(market_price, tuple):
            # 价格不可用，无法执行订单
            order.status = 'rejected'
            order.admin_notes = f"无法获取市场价格: {market_price[0]}"
            db.session.commit()
            return False
        
        # 获取用户账户
        account = AccountBalance.query.filter_by(user_id=order.user_id).first()
        if not account:
            # 账户不存在，无法执行订单
            order.status = 'rejected'
            order.admin_notes = "用户没有账户余额"
            db.session.commit()
            return False
        
        # 计算交易总额
        total_amount = market_price * order.quantity
        
        # 处理买单
        if order.order_type == 'buy':
            # 检查余额是否足够
            if account.balance < total_amount:
                order.status = 'rejected'
                order.admin_notes = "账户余额不足"
                db.session.commit()
                return False
            
            # 扣除账户余额
            account.balance -= total_amount
            
            # 更新投资组合
            portfolio = Portfolio.query.filter_by(
                user_id=order.user_id,
                ticker=order.ticker
            ).first()
            
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
                    avg_price=market_price
                )
                db.session.add(portfolio)
        
        # 处理卖单
        elif order.order_type == 'sell':
            # 检查是否持有足够的股票
            portfolio = Portfolio.query.filter_by(
                user_id=order.user_id,
                ticker=order.ticker
            ).first()
            
            if not portfolio or portfolio.quantity < order.quantity:
                order.status = 'rejected'
                order.admin_notes = "持有的股票不足"
                db.session.commit()
                return False
            
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
            price=market_price,
            total_amount=total_amount,
            transaction_type=order.order_type,
            status='completed',
            created_at=datetime.utcnow()
        )
        db.session.add(transaction)
        
        # 更新订单状态
        order.status = 'executed'
        order.updated_at = datetime.utcnow()
        
        # 保存更改
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        order.status = 'rejected'
        order.admin_notes = f"执行订单时发生错误: {str(e)}"
        db.session.commit()
        return False 