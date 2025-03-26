"""
订单处理工具函数
用于验证、创建和执行订单

包含了订单处理的核心逻辑，包括：
1. 订单参数验证
2. 执行条件检查
3. 订单执行逻辑
"""
from datetime import datetime
from flask import current_app
import logging
from models import db, Order, AccountBalance, Portfolio, Transaction, MarketData

# 设置日志
logger = logging.getLogger(__name__)

def validate_order_params(user_id, ticker, order_type, order_execution_type, order_quantity, order_price=None):
    """
    验证订单参数
    
    参数:
        user_id (int): 用户ID
        ticker (str): 股票代码
        order_type (str): 订单类型 (buy/sell)
        order_execution_type (str): 执行类型 (market/limit)
        order_quantity (int): 订单数量
        order_price (float, optional): 订单价格，限价单必须提供
        
    返回:
        tuple: (成功标志, 错误信息或None)
    """
    # 检查基本参数
    if not all([ticker, order_type, order_execution_type, order_quantity]):
        missing = []
        if not ticker: missing.append('ticker')
        if not order_type: missing.append('order_type')
        if not order_execution_type: missing.append('order_execution_type')
        if not order_quantity: missing.append('order_quantity')
        return False, f"缺少必要参数: {', '.join(missing)}"
    
    # 检查数量
    try:
        order_quantity = int(order_quantity)
        if order_quantity <= 0:
            return False, "数量必须为正整数"
    except (ValueError, TypeError):
        return False, "无效的数量格式"
    
    # 检查订单类型
    if order_type not in ['buy', 'sell']:
        return False, "无效的订单类型，必须是 'buy' 或 'sell'"
    
    # 检查执行类型
    if order_execution_type not in ['market', 'limit']:
        return False, "无效的执行类型，必须是 'market' 或 'limit'"
    
    # 检查价格（仅限价单）
    if order_execution_type == 'limit':
        if order_price is None:
            return False, "限价单必须指定价格"
        try:
            order_price = float(order_price)
            if order_price <= 0:
                return False, "价格必须大于0"
        except (ValueError, TypeError):
            return False, "无效的价格格式"
    
    # 对于卖单，检查用户是否持有足够的股票
    if order_type == 'sell':
        portfolio = Portfolio.query.filter_by(user_id=user_id, ticker=ticker).first()
        if not portfolio:
            return False, f"您没有持有{ticker}的股票"
        if portfolio.quantity < order_quantity:
            return False, f"您只持有{portfolio.quantity}股{ticker}，无法卖出{order_quantity}股"
    
    return True, None

def get_market_price(ticker):
    """
    获取股票的当前市场价格
    
    参数:
        ticker (str): 股票代码
        
    返回:
        tuple: (成功标志, 价格或错误信息)
    """
    try:
        # 从数据库获取最新价格数据
        latest_data = MarketData.query.filter_by(ticker=ticker).order_by(MarketData.date.desc()).first()
        
        if not latest_data:
            return False, f"无法获取{ticker}的市场数据"
        
        # 使用收盘价作为市场价格
        return True, float(latest_data.close)
    except Exception as e:
        logger.error(f"获取市场价格出错: {str(e)}")
        return False, f"获取市场价格时发生错误: {str(e)}"

def check_account_balance(user_id, cost):
    """
    检查用户账户余额是否足够
    
    参数:
        user_id (int): 用户ID
        cost (float): 估计成本
        
    返回:
        tuple: (成功标志, 账户或错误信息)
    """
    account = AccountBalance.query.filter_by(user_id=user_id).first()
    
    if not account:
        return False, "未找到您的账户信息"
    
    if account.available_balance < cost:
        return False, f"账户余额不足。估计成本: ¥{cost:.2f}, 您的可用余额: ¥{account.available_balance:.2f}"
    
    return True, account

def create_order(user_id, ticker, order_type, order_execution_type, order_quantity, order_price=None):
    """
    创建新订单
    
    参数:
        user_id (int): 用户ID
        ticker (str): 股票代码
        order_type (str): 订单类型 (buy/sell)
        order_execution_type (str): 执行类型 (market/limit)
        order_quantity (int): 订单数量
        order_price (float, optional): 订单价格，限价单必须提供
        
    返回:
        tuple: (成功标志, 订单对象或错误信息, 状态码)
    """
    try:
        # 验证订单参数
        valid, message = validate_order_params(
            user_id, ticker, order_type, order_execution_type, order_quantity, order_price
        )
        if not valid:
            return False, message, 400
        
        # 获取市场价格
        price_success, price_result = get_market_price(ticker)
        if not price_success:
            return False, price_result, 404
        
        market_price = price_result
        
        # 对于买单，检查账户余额是否足够
        if order_type == 'buy':
            estimated_cost = market_price * int(order_quantity) if order_execution_type == 'market' else float(order_price) * int(order_quantity)
            balance_success, account_or_error = check_account_balance(user_id, estimated_cost)
            
            if not balance_success:
                return False, account_or_error, 400
                
            # 对于限价单，将资金从可用余额转移到冻结余额
            if order_execution_type == 'limit':
                account = account_or_error
                account.available_balance -= estimated_cost
                account.frozen_balance += estimated_cost
                # 总余额保持不变
                logger.info(f"已冻结用户 {user_id} 资金: ¥{estimated_cost:.2f} 用于限价单")
        
        # 创建订单对象
        order = Order(
            user_id=user_id,
            ticker=ticker,
            order_type=order_type,
            order_execution_type=order_execution_type,
            order_price=float(order_price) if order_execution_type == 'limit' else None,
            order_quantity=int(order_quantity),
            order_status='pending'
        )
        
        # 保存到数据库
        db.session.add(order)
        db.session.commit()
        
        logger.info(f"创建订单成功: #{order.order_id}")
        
        return True, order, 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建订单失败: {str(e)}")
        return False, f"创建订单失败: {str(e)}", 500

def can_execute_immediately(order, market_price):
    """
    检查订单是否可以立即执行
    
    参数:
        order (Order): 订单对象
        market_price (float): 当前市场价格
        
    返回:
        bool: 是否可以立即执行
    """
    # 市价单总是可以立即执行
    if order.order_execution_type == 'market':
        return True
    
    # 限价单需要检查价格条件
    if order.order_execution_type == 'limit':
        # 买入限价单: 当市场价格 <= 限价时可执行
        if order.order_type == 'buy' and market_price <= order.order_price:
            logger.info(f"买入限价单 #{order.order_id} 可以执行: 市场价格({market_price}) <= 限价({order.order_price})")
            return True
        
        # 卖出限价单: 当市场价格 >= 限价时可执行
        elif order.order_type == 'sell' and market_price >= order.order_price:
            logger.info(f"卖出限价单 #{order.order_id} 可以执行: 市场价格({market_price}) >= 限价({order.order_price})")
            return True
    
    return False

def execute_order(order, market_price=None):
    """
    执行订单
    
    参数:
        order (Order): 订单对象
        market_price (float, optional): 执行价格，如果未提供会重新获取
        
    返回:
        tuple: (成功标志, 成功消息或错误信息)
    """
    try:
        # 如果未提供市场价格，重新获取
        if market_price is None:
            price_success, price_result = get_market_price(order.ticker)
            if not price_success:
                order.order_status = 'rejected'
                order.remark = price_result
                db.session.commit()
                return False, price_result
            
            market_price = price_result
        
        # 获取用户账户
        account = AccountBalance.query.filter_by(user_id=order.user_id).first()
        if not account:
            order.order_status = 'rejected'
            order.remark = "用户没有账户信息"
            db.session.commit()
            return False, "用户没有账户信息"
        
        # 计算交易总额
        total_amount = market_price * order.order_quantity
        
        # 处理买单
        if order.order_type == 'buy':
            # 如果是限价单，需要从冻结余额中处理
            if order.order_execution_type == 'limit':
                # 检查冻结余额是否足够（应该足够，因为创建订单时已经冻结）
                estimated_cost = order.order_price * order.order_quantity
                
                # 从冻结余额中扣除
                account.frozen_balance -= estimated_cost
                
                # 如果市场价低于限价，退回差额
                if market_price < order.order_price:
                    refund_amount = (order.order_price - market_price) * order.order_quantity
                    account.available_balance += refund_amount
                    logger.info(f"为用户 {order.user_id} 退回价格差额: ¥{refund_amount:.2f}")
            else:
                # 市价单，直接从可用余额扣除
                if account.available_balance < total_amount:
                    order.order_status = 'rejected'
                    order.remark = "账户余额不足"
                    db.session.commit()
                    return False, f"账户余额不足。需要: ¥{total_amount:.2f}, 可用: ¥{account.available_balance:.2f}"
                
                account.available_balance -= total_amount
            
            # 更新投资组合
            portfolio = Portfolio.query.filter_by(user_id=order.user_id, ticker=order.ticker).first()
            
            if portfolio:
                # 更新现有持仓
                old_value = portfolio.average_price * portfolio.quantity
                new_value = old_value + total_amount
                new_quantity = portfolio.quantity + order.order_quantity
                portfolio.average_price = new_value / new_quantity
                portfolio.quantity = new_quantity
            else:
                # 创建新持仓
                portfolio = Portfolio(
                    user_id=order.user_id,
                    ticker=order.ticker,
                    quantity=order.order_quantity,
                    average_price=market_price
                )
                db.session.add(portfolio)
        
        # 处理卖单
        elif order.order_type == 'sell':
            # 检查是否持有足够股票
            portfolio = Portfolio.query.filter_by(user_id=order.user_id, ticker=order.ticker).first()
            
            if not portfolio or portfolio.quantity < order.order_quantity:
                order.order_status = 'rejected'
                order.remark = "持有股票数量不足"
                db.session.commit()
                return False, "持有股票数量不足"
            
            # 增加账户余额
            account.available_balance += total_amount
            
            # 更新持仓
            portfolio.quantity -= order.order_quantity
            
            # 如果持仓为0，移除记录
            if portfolio.quantity == 0:
                db.session.delete(portfolio)
        
        # 创建交易记录
        transaction = Transaction(
            user_id=order.user_id,
            order_id=order.order_id,
            ticker=order.ticker,
            transaction_type=order.order_type,
            transaction_price=market_price,
            transaction_quantity=order.order_quantity,
            transaction_amount=total_amount,
            transaction_status='completed',
            transaction_time=datetime.now()
        )
        db.session.add(transaction)
        
        # 更新订单状态
        order.order_status = 'executed'
        order.executed_at = datetime.now()
        order.updated_at = datetime.now()
        
        db.session.commit()
        logger.info(f"订单 #{order.order_id} 执行成功，价格: {market_price}, 数量: {order.order_quantity}")
        
        return True, "订单执行成功"
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"执行订单失败: {str(e)}")
        
        # 更新订单状态为拒绝
        try:
            order.order_status = 'rejected'
            order.remark = f"执行过程中发生错误: {str(e)}"
            order.updated_at = datetime.now()
            db.session.commit()
        except:
            logger.error("无法更新订单状态")
        
        return False, f"执行订单失败: {str(e)}"

def process_new_order(user_id, ticker, order_type, order_execution_type, order_quantity, order_price=None):
    """
    处理新订单请求
    包括创建订单并判断是否可以立即执行
    
    参数:
        user_id (int): 用户ID
        ticker (str): 股票代码
        order_type (str): 订单类型 (buy/sell)
        order_execution_type (str): 执行类型 (market/limit)
        order_quantity (int): 订单数量
        order_price (float, optional): 订单价格，限价单必须提供
        
    返回:
        tuple: (响应数据, 状态码)
    """
    # 创建订单
    success, result, status_code = create_order(
        user_id, ticker, order_type, order_execution_type, order_quantity, order_price
    )
    
    if not success:
        return {'error': result}, status_code
    
    order = result
    
    # 获取市场价格
    price_success, price_result = get_market_price(ticker)
    if not price_success:
        return {
            'message': f'订单已创建，但无法获取实时价格，订单将等待处理',
            'order_id': order.order_id,
            'status': order.order_status
        }, 201
    
    market_price = price_result
    
    # 检查是否可以立即执行
    if can_execute_immediately(order, market_price):
        # 尝试立即执行订单
        exec_success, exec_message = execute_order(order, market_price)
        
        if exec_success:
            return {
                'message': f'订单已成功执行',
                'order_id': order.order_id,
                'executed_price': market_price,
                'total_amount': market_price * order.order_quantity,
                'status': 'executed'
            }, 200
        else:
            return {
                'message': f'订单已创建，但无法立即执行: {exec_message}',
                'order_id': order.order_id,
                'status': order.order_status
            }, 201
    
    # 对于不能立即执行的限价单
    if order.order_execution_type == 'limit':
        execution_condition = "高于" if order.order_type == 'sell' else "低于"
        return {
            'message': f'限价单已创建，将在市场价格{execution_condition}{order.order_price}时执行',
            'order_id': order.order_id,
            'limit_price': order.order_price,
            'current_market_price': market_price,
            'status': 'pending'
        }, 201
    
    # 市价单 (这种情况应该不会发生，因为市价单总是应该立即执行)
    return {
        'message': f'市价单已创建，将尽快执行',
        'order_id': order.order_id,
        'estimated_price': market_price,
        'estimated_total': market_price * order.order_quantity,
        'status': 'pending'
    }, 201 