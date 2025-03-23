"""
用户订单相关路由
包含创建订单、取消订单等功能
"""
from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Order, AccountBalance, Portfolio, MarketData

from . import user_bp

@user_bp.route('/api/create_order', methods=['POST'])
@login_required
def create_order():
    """
    创建订单API
    处理用户买入或卖出股票的请求
    """
    print("=== 开始处理订单创建请求 ===")
    print("请求方法:", request.method)
    print("请求头:", dict(request.headers))
    print("请求内容类型:", request.content_type)
    
    try:
        data = request.get_json()
        print("收到订单数据:", data)
    except Exception as e:
        print("解析JSON数据失败:", str(e))
        return jsonify({'error': '无效的请求数据格式'}), 400
    
    # 获取所有必要参数
    ticker = data.get('ticker')
    order_quantity = data.get('order_quantity')
    order_type = data.get('order_type')
    order_execution_type = data.get('order_execution_type')
    order_price = data.get('order_price')
    
    print("解析后的参数:")
    print(f"- ticker: {ticker}")
    print(f"- order_quantity: {order_quantity}")
    print(f"- order_type: {order_type}")
    print(f"- order_execution_type: {order_execution_type}")
    print(f"- order_price: {order_price}")
    
    # 参数验证
    if not all([ticker, order_quantity, order_type, order_execution_type]):
        missing_params = []
        if not ticker: missing_params.append('ticker')
        if not order_quantity: missing_params.append('order_quantity')
        if not order_type: missing_params.append('order_type')
        if not order_execution_type: missing_params.append('order_execution_type')
        print("缺少必要参数:", missing_params)
        return jsonify({'error': f'缺少必要参数: {", ".join(missing_params)}'}), 400
    
    try:
        # 转换并验证数量
        order_quantity = int(order_quantity)
        if order_quantity <= 0:
            return jsonify({'error': '数量必须为正整数'}), 400
        
        # 验证订单类型
        if order_type not in ['buy', 'sell']:
            return jsonify({'error': '无效的订单类型'}), 400
            
        # 验证执行类型
        if order_execution_type not in ['market', 'limit']:
            return jsonify({'error': '无效的执行类型'}), 400
            
        # 验证价格（对于限价单）
        if order_execution_type == 'limit':
            if order_price is None:
                return jsonify({'error': '限价单必须指定价格'}), 400
            try:
                order_price = float(order_price)
                if order_price <= 0:
                    return jsonify({'error': '价格必须大于0'}), 400
            except (TypeError, ValueError):
                return jsonify({'error': '无效的价格格式'}), 400
        
        # 对于卖单，验证用户是否持有足够的股票
        if order_type == 'sell':
            portfolio = Portfolio.query.filter_by(
                user_id=current_user.user_id,
                ticker=ticker
            ).first()
            
            if not portfolio:
                return jsonify({'error': f'您没有持有{ticker}的股票'}), 400
                
            if portfolio.quantity < order_quantity:
                return jsonify({'error': f'您只持有{portfolio.quantity}股{ticker}，无法卖出{order_quantity}股'}), 400
        
        # 获取市场价格
        market_price_result = get_market_price_with_message(ticker)
        if isinstance(market_price_result, tuple):
            return jsonify({'error': market_price_result[0]}), market_price_result[1]
        market_price = market_price_result
        
        # 对于买单，验证用户是否有足够的资金
        if order_type == 'buy':
            account = AccountBalance.query.filter_by(user_id=current_user.user_id).first()
            
            if not account:
                return jsonify({'error': '未找到您的账户信息'}), 400
                
            estimated_cost = market_price * order_quantity if order_execution_type == 'market' else order_price * order_quantity
            
            if account.available_balance < estimated_cost:
                return jsonify({
                    'error': f'账户余额不足。估计成本: ¥{estimated_cost:.2f}, 您的可用余额: ¥{account.available_balance:.2f}'
                }), 400
        
        # 创建订单
        order = Order(
            user_id=current_user.user_id,
            ticker=ticker,
            order_type=order_type,
            order_execution_type=order_execution_type,
            order_price=order_price if order_execution_type == 'limit' else None,
            order_quantity=order_quantity,
            order_status='pending'
        )
        
        # 检查限价单是否可以立即执行
        can_execute_immediately = False
        if order_execution_type == 'limit':
            if order_type == 'buy' and market_price <= order_price:
                can_execute_immediately = True
                print(f"买入限价单可以立即执行：市场价格({market_price}) <= 限价({order_price})")
            elif order_type == 'sell' and market_price >= order_price:
                can_execute_immediately = True
                print(f"卖出限价单可以立即执行：市场价格({market_price}) >= 限价({order_price})")
        
        db.session.add(order)
        db.session.commit()
        print(f"订单创建成功: #{order.order_id}")
        
        # 如果是限价单且可以立即执行，尝试执行订单
        if order_execution_type == 'limit' and can_execute_immediately:
            print("尝试立即执行限价单")
            if execute_market_order(order):
                return jsonify({
                    'message': f'限价单已立即执行',
                    'order_id': order.order_id,
                    'executed_price': market_price,
                    'total_amount': market_price * order_quantity
                })
        
        # 如果是限价单但不能立即执行，或者执行失败
        if order_execution_type == 'limit':
            execution_condition = "高于" if order_type == 'sell' else "低于"
            return jsonify({
                'message': f'限价单已创建，将在市场价格{execution_condition}{order_price}时执行',
                'order_id': order.order_id,
                'limit_price': order_price,
                'current_market_price': market_price
            })
        
        # 如果是市价单
        return jsonify({
            'message': f'市价单已创建',
            'order_id': order.order_id,
            'estimated_price': market_price,
            'estimated_total': market_price * order_quantity
        })
        
    except ValueError as e:
        print(f"数据格式错误: {str(e)}")
        return jsonify({'error': f'无效的数据格式: {str(e)}'}), 400
    except Exception as e:
        print(f"创建订单失败: {str(e)}")
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
        if order.user_id != current_user.user_id:
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