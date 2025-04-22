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
import contextlib # 导入 contextlib
# 导入必要的枚举类型
from models.enums import OrderStatus, TransactionStatus, OrderType, OrderExecutionType
from decimal import Decimal

# 设置日志
logger = logging.getLogger(__name__)

# 定义事务上下文管理器
@contextlib.contextmanager
def order_transaction_scope():
    """提供订单处理的事务范围会话上下文管理器"""
    try:
        yield db.session
        db.session.commit()
        logger.info("订单事务成功提交")
    except Exception as e:
        db.session.rollback()
        logger.error(f"订单事务回滚: {str(e)}", exc_info=True)
        raise # 重新抛出异常，以便上层可以捕获
    # 不需要 finally 关闭 session，Flask-SQLAlchemy 会处理

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
        tuple: (成功标志, 错误信息或None, 是否是严格错误)
              如果第三个参数为True，表示格式错误等严重问题，应该返回400
              如果为False，表示业务逻辑错误，应该记录为FAILED状态的订单
    """
    # 检查基本参数 - 这些是严格错误
    if not all([ticker, order_type, order_execution_type, order_quantity]):
        missing = []
        if not ticker: missing.append('ticker')
        if not order_type: missing.append('order_type')
        if not order_execution_type: missing.append('order_execution_type')
        if not order_quantity: missing.append('order_quantity')
        return False, f"缺少必要参数: {', '.join(missing)}", True
    
    # 检查数量 - 这些是严格错误
    try:
        order_quantity = int(order_quantity)
        if order_quantity <= 0:
            return False, "数量必须为正整数", True
    except (ValueError, TypeError):
        return False, "无效的数量格式", True
    
    # 检查订单类型 - 这些是严格错误
    if order_type not in [OrderType.BUY.value, OrderType.SELL.value]:
        return False, "无效的订单类型，必须是 'buy' 或 'sell'", True
    
    # 检查执行类型 - 这些是严格错误
    if order_execution_type not in [OrderExecutionType.MARKET.value, OrderExecutionType.LIMIT.value]:
        return False, "无效的执行类型，必须是 'market' 或 'limit'", True
    
    # 检查价格（仅限价单） - 这些是严格错误
    if order_execution_type == OrderExecutionType.LIMIT.value:
        if order_price is None:
            return False, "限价单必须指定价格", True
        try:
            order_price = float(order_price)
            if order_price <= 0:
                return False, "价格必须大于0", True
        except (ValueError, TypeError):
            return False, "无效的价格格式", True
    
    # 对于卖单，检查用户是否持有足够的股票 - 这是业务逻辑错误，应该记录订单
    if order_type == OrderType.SELL.value:
        portfolio = Portfolio.query.filter_by(user_id=user_id, ticker=ticker).first()
        if not portfolio:
            return False, f"您没有持有{ticker}的股票", False
        if portfolio.quantity < order_quantity:
            return False, f"您只持有{portfolio.quantity}股{ticker}，无法卖出{order_quantity}股", False
    
    return True, None, False

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
        valid, message, is_strict_error = validate_order_params(
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
        if order_type == OrderType.BUY.value:
            estimated_cost = market_price * int(order_quantity) if order_execution_type == OrderExecutionType.MARKET.value else float(order_price) * int(order_quantity)
            balance_success, account_or_error = check_account_balance(user_id, estimated_cost)
            
            if not balance_success:
                return False, account_or_error, 400
                
            # 对于限价单，将资金从可用余额转移到冻结余额
            if order_execution_type == OrderExecutionType.LIMIT.value:
                account = account_or_error
                account.available_balance -= estimated_cost
                account.frozen_balance += estimated_cost
                # 总余额保持不变
                logger.info(f"已冻结用户 {user_id} 资金: ¥{estimated_cost:.2f} 用于限价单")
        
        # 创建订单对象
        order_status = OrderStatus.PENDING if valid else OrderStatus.FAILED
        order = Order(
            user_id=user_id,
            ticker=ticker,
            order_type=OrderType(order_type),
            order_execution_type=OrderExecutionType(order_execution_type),
            order_price=float(order_price) if order_execution_type == OrderExecutionType.LIMIT.value else None,
            order_quantity=int(order_quantity),
            order_status=order_status
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
    if order.order_execution_type == OrderExecutionType.MARKET:
        return True
    
    # 限价单需要检查价格条件
    if order.order_execution_type == OrderExecutionType.LIMIT:
        # 买入限价单: 当市场价格 <= 限价时可执行
        if order.order_type == OrderType.BUY and market_price <= order.order_price:
            logger.info(f"买入限价单 #{order.order_id} 可以执行: 市场价格({market_price}) <= 限价({order.order_price})")
            return True
        
        # 卖出限价单: 当市场价格 >= 限价时可执行
        elif order.order_type == OrderType.SELL and market_price >= order.order_price:
            logger.info(f"卖出限价单 #{order.order_id} 可以执行: 市场价格({market_price}) >= 限价({order.order_price})")
            return True
    
    return False

def _execute_order_logic(session, order, account, portfolio, market_price, total_amount):
    """订单执行的核心数据库操作逻辑（不包含commit）"""
    # 将所有价格和数量转换为Decimal类型以避免float和Decimal混合运算
    
    # 转换为Decimal类型以确保精确计算
    market_price_decimal = Decimal(str(market_price)) if not isinstance(market_price, Decimal) else market_price
    order_quantity_decimal = Decimal(str(order.order_quantity))
    
    # 重新计算total_amount确保类型一致
    total_amount_decimal = market_price_decimal * order_quantity_decimal
    
    # 处理买单
    if order.order_type == OrderType.BUY:
        # 如果是限价单，处理冻结余额和退款
        if order.order_execution_type == OrderExecutionType.LIMIT:
            order_price_decimal = Decimal(str(order.order_price)) if not isinstance(order.order_price, Decimal) else order.order_price
            estimated_cost = order_price_decimal * order_quantity_decimal
            account.frozen_balance -= float(estimated_cost)
            refund_amount = 0 # Initialize refund_amount
            if market_price_decimal < order_price_decimal:
                refund_amount = float((order_price_decimal - market_price_decimal) * order_quantity_decimal)
                account.available_balance += refund_amount
            # 移除手动计算 total_balance，交给事件监听器处理
            # account.total_balance = account.available_balance + account.frozen_balance
            # Log refund only if it happened
            if refund_amount > 0:
                logger.info(f"退回用户 {order.user_id} 价格差额: ¥{refund_amount:.2f}")
        else: # 市价单，扣除可用余额
            account.available_balance -= float(total_amount_decimal)
            # 移除手动计算 total_balance，交给事件监听器处理
            # account.total_balance = account.available_balance + account.frozen_balance
        
        # 更新投资组合
        if portfolio:
            # Ensure average_price is not None before calculation
            if portfolio.average_price is None:
                 portfolio.average_price = 0 # Or handle appropriately
            
            # 转换portfolio相关值为Decimal
            portfolio_quantity_decimal = Decimal(str(portfolio.quantity))
            portfolio_avg_price_decimal = Decimal(str(portfolio.average_price)) if portfolio.average_price is not None else Decimal('0')
            
            # 计算新的平均价格
            old_value = portfolio_avg_price_decimal * portfolio_quantity_decimal
            new_value = old_value + total_amount_decimal
            new_quantity = portfolio_quantity_decimal + order_quantity_decimal
            
            # Avoid division by zero if new_quantity is somehow zero
            portfolio.average_price = float(new_value / new_quantity) if new_quantity > 0 else float(market_price_decimal)
            portfolio.quantity = int(new_quantity)
        else:
            portfolio = Portfolio(
                user_id=order.user_id,
                ticker=order.ticker,
                quantity=int(order_quantity_decimal),
                average_price=float(market_price_decimal)
            )
            session.add(portfolio)
            
    # 处理卖单
    elif order.order_type == OrderType.SELL:
        account.available_balance += float(total_amount_decimal)
        # 移除手动计算 total_balance，交给事件监听器处理
        # account.total_balance = account.available_balance + account.frozen_balance
        portfolio.quantity -= int(order_quantity_decimal)
        if portfolio.quantity == 0:
            session.delete(portfolio)
            
    # 创建交易记录，并立即关联 Order 对象
    transaction = Transaction(
        user_id=order.user_id,
        order=order,  # 直接关联 Order 对象
        ticker=order.ticker,
        transaction_type=order.order_type,
        transaction_price=float(market_price_decimal),
        transaction_quantity=int(order_quantity_decimal),
        transaction_amount=float(total_amount_decimal),
        transaction_status=TransactionStatus.COMPLETED, # 使用枚举
        transaction_time=datetime.now()
    )
    session.add(transaction)
        
    # 更新订单状态
    order.order_status = OrderStatus.EXECUTED # 使用枚举
    order.executed_at = datetime.now()
    order.updated_at = datetime.now()
        
    # 如果订单是新创建的（尚未添加到会话中），需要添加
    # 确保 Order 对象在 session 中，以便 flush 时能处理
    if order not in session:
        session.add(order)
    
    # Flush 以将更改写入数据库，SQLAlchemy 会处理插入顺序
    session.flush()
    
    logger.info(f"订单 #{order.order_id} ({order.order_type}) 核心逻辑执行完毕，等待提交")

def execute_order(order, market_price=None):
    """执行数据库中已存在的 pending 订单 (由后台任务调用)"""
    try:
        with order_transaction_scope() as session: 
            # 如果未提供市场价格，重新获取
            if market_price is None:
                price_success, price_result = get_market_price(order.ticker)
                if not price_success:
                    order.order_status = OrderStatus.FAILED # 改为 FAILED
                    order.remark = f"无法获取价格: {price_result}"
                    logger.warning(f"执行订单 #{order.order_id} 失败: {order.remark}")
                    # 不抛出异常，让事务提交 FAILED 状态
                    return False, order.remark # 返回失败状态和原因
                market_price = price_result
            
            # 获取用户账户
            account = AccountBalance.query.with_for_update().filter_by(user_id=order.user_id).first() # 添加行锁
            if not account:
                order.order_status = OrderStatus.FAILED # 改为 FAILED
                order.remark = "用户没有账户信息"
                logger.warning(f"执行订单 #{order.order_id} 失败: {order.remark}")
                return False, order.remark
            
            # 获取投资组合（如果是卖单，需要加锁检查）
            portfolio = None
            if order.order_type == OrderType.SELL:
                portfolio = Portfolio.query.with_for_update().filter_by(user_id=order.user_id, ticker=order.ticker).first() # 添加行锁
                if not portfolio or portfolio.quantity < order.order_quantity:
                    order.order_status = OrderStatus.FAILED # 改为 FAILED
                    order.remark = f"持有股票数量不足 (需要 {order.order_quantity}, 持有 {portfolio.quantity if portfolio else 0})"
                    logger.warning(f"执行订单 #{order.order_id} 失败: {order.remark}")
                    return False, order.remark
            elif order.order_type == OrderType.BUY: # 买单也可能需要更新或创建 portfolio
                portfolio = Portfolio.query.filter_by(user_id=order.user_id, ticker=order.ticker).first()
                
            # 计算交易总额
            total_amount = market_price * order.order_quantity
            
            # 执行核心逻辑
            _execute_order_logic(session, order, account, portfolio, market_price, total_amount)
            
            logger.info(f"订单 #{order.order_id} 事务成功执行")
            return True, "订单执行成功" # Return inside the 'with' block if successful
            
    except Exception as e:
        logger.error(f"执行订单 #{order.order_id} 过程中发生意外错误: {str(e)}", exc_info=True)
        # Attempt to update order status to FAILED outside the transaction (or in nested)
        try:
            # Fetch the order again in a new nested transaction scope if needed
            with db.session.begin_nested(): 
                 order_to_fail = Order.query.get(order.order_id) # Re-fetch within scope
                 if order_to_fail and order_to_fail.order_status == OrderStatus.PENDING:
                     order_to_fail.order_status = OrderStatus.FAILED # 改为 FAILED
                     order_to_fail.remark = f"执行时发生内部错误: {str(e)}"
                     order_to_fail.updated_at = datetime.now()
                     # db.session.commit() # Commit handled by begin_nested context manager
                     logger.info(f"已将订单 #{order.order_id} 状态更新为 FAILED (in nested transaction)")
                 # else: # Optional: log if order was not found or already processed
                 #     logger.warning(f"尝试标记订单 #{order.order_id} 为 FAILED 时，订单不存在或状态不是 PENDING")
        except Exception as nested_e:
             logger.error(f"在主事务失败后，尝试标记订单 #{order.order_id} 为 FAILED 时再次失败: {str(nested_e)}")
        
        # Return failure after handling the exception
        return False, f"执行订单失败: {str(e)}"

def process_new_order(user_id, ticker, order_type, order_execution_type, order_quantity, order_price=None):
    """处理新订单请求 (由 API 调用)"""
    failure_reason = None # 用于记录失败原因
    try:
        # 1. 验证参数
        valid, message, is_strict_error = validate_order_params(
            user_id, ticker, order_type, order_execution_type, order_quantity, order_price
        )
        if not valid:
            # 如果是严格错误（格式错误等），直接返回400
            if is_strict_error:
                return {'error': message}, 400
            # 如果是业务逻辑错误（余额不足、持仓不足等），记录failure_reason
            else:
                failure_reason = message
        
        # 2. 获取市场价格 (如果失败，直接返回404)
        price_success, price_result = get_market_price(ticker)
        if not price_success:
            return {'error': price_result}, 404
        market_price = price_result
        order_quantity = int(order_quantity)
        limit_price = float(order_price) if order_execution_type == OrderExecutionType.LIMIT.value else None

        # --- 开始数据库交互 --- 
        with order_transaction_scope() as session: 
            
            # 3. 获取账户 (可能失败)
            account = AccountBalance.query.with_for_update().filter_by(user_id=user_id).first()
            if not account and not failure_reason:
                failure_reason = "未找到账户信息"
            
            # 4. 检查余额 (买单，可能失败)
            estimated_cost = market_price * order_quantity if order_execution_type == OrderExecutionType.MARKET.value else limit_price * order_quantity
            if failure_reason is None and order_type == OrderType.BUY.value and account.available_balance < estimated_cost:
                failure_reason = f"账户余额不足 (需要 ¥{estimated_cost:.2f}, 可用 ¥{account.available_balance:.2f})"

            # 5. 检查持仓 (卖单可能已经在validate_order_params中检查过)
            portfolio = None
            if failure_reason is None and order_type == OrderType.SELL.value:
                portfolio = Portfolio.query.with_for_update().filter_by(user_id=user_id, ticker=ticker).first()
                if not portfolio or portfolio.quantity < order_quantity:
                     failure_reason = f"持有股票数量不足 (需要 {order_quantity}, 持有 {portfolio.quantity if portfolio else 0})"
            elif failure_reason is None and order_type == OrderType.BUY.value: # 买单也需要 portfolio 信息
                portfolio = Portfolio.query.filter_by(user_id=user_id, ticker=ticker).first()
        
            # 6. 创建订单对象 (总是创建)
            order_status = OrderStatus.FAILED if failure_reason else OrderStatus.PENDING # 初始状态
            order = Order(
                user_id=user_id,
                ticker=ticker,
                order_type=OrderType(order_type),
                order_execution_type=OrderExecutionType(order_execution_type),
                order_price=limit_price,
                order_quantity=order_quantity,
                order_status=order_status
            )
            # 单独设置remark字段
            if failure_reason:
                order.remark = failure_reason
                
            session.add(order) # 总是添加订单记录
            session.flush() # 需要 flush 获取 order_id

            # 7. 如果检查失败，直接提交 FAILED 订单并返回
            if failure_reason:
                logger.warning(f"订单 #{order.order_id} 创建失败: {failure_reason}")
                # 事务将在退出 with 块时提交
                return {
                    'message': '订单创建失败', # 通用失败消息
                    'error': failure_reason, # 具体原因
                    'order_id': order.order_id,
                    'status': order_status.value # 返回 'failed'
                }, 200 # 返回 200 OK，表示请求已处理但业务失败
                
            # --- 如果检查通过 --- 
            
            # 8. 判断是否立即执行
            can_execute_now = False
            execution_price = None
            
            # 市价单可以立即执行
            if order_execution_type == OrderExecutionType.MARKET.value:
                can_execute_now = True
                execution_price = market_price
            # 检查限价单是否符合立即执行条件
            elif order_execution_type == OrderExecutionType.LIMIT.value:
                # 买入限价单: 当市场价格 <= 限价时可执行
                if order_type == OrderType.BUY.value and market_price <= limit_price:
                    can_execute_now = True
                    execution_price = market_price  # 以市场价执行
                    logger.info(f"买入限价单 #{order.order_id} 可以立即执行: 市场价格({market_price}) <= 限价({limit_price})")
                
                # 卖出限价单: 当市场价格 >= 限价时可执行
                elif order_type == OrderType.SELL.value and market_price >= limit_price:
                    can_execute_now = True
                    execution_price = market_price  # 以市场价执行
                    logger.info(f"卖出限价单 #{order.order_id} 可以立即执行: 市场价格({market_price}) >= 限价({limit_price})")
            
            # 立即执行符合条件的订单(包括市价单和符合条件的限价单)
            if can_execute_now:
                logger.info(f"订单 #{order.order_id} 满足立即执行条件，执行价格: {execution_price}")
                portfolio_obj = Portfolio.query.filter_by(user_id=user_id, ticker=ticker).first()
                
                # 使用Decimal类型计算总金额以避免类型不匹配
                execution_price_decimal = Decimal(str(execution_price)) if not isinstance(execution_price, Decimal) else execution_price
                order_quantity_decimal = Decimal(str(order_quantity))
                total_amount_decimal = execution_price_decimal * order_quantity_decimal
                total_amount = float(total_amount_decimal)  # 转回float用于存储
                
                try:
                    _execute_order_logic(session, order, account, portfolio_obj, execution_price, total_amount)
                    order_data = {
                        'message': f'市价单已成功执行',
                        'order_id': order.order_id,
                        'executed_price': execution_price,
                        'total_amount': total_amount,
                        'status': 'valid',
                        'order_status': order.order_status.value,
                        'error': None
                    }
                except Exception as e:
                    logger.error(f"执行订单 #{order.order_id} 失败: {str(e)}")
                    order.order_status = OrderStatus.FAILED
                    order.remark = f"执行失败: {str(e)}"
                    order_data = {
                        'message': '订单执行失败',
                        'order_id': order.order_id,
                        'status': 'invalid',
                        'order_status': order.order_status.value,
                        'error': order.remark
                    }
            else:
                # 处理限价单 - 始终进入PENDING状态
                if order_execution_type == OrderExecutionType.LIMIT.value:
                    # 对于买入限价单，之前已经冻结过资金，这里不再重复冻结
                    execution_condition = "高于" if order_type == OrderType.SELL.value else "低于或等于"
                    order_data = {
                        'message': f'限价单已创建，将在市场价格{execution_condition}{order_price}时执行',
                        'order_id': order.order_id,
                        'limit_price': order_price,
                        'current_market_price': market_price,
                        'status': 'valid',
                        'order_status': order.order_status.value,
                        'error': None
                    }
                else:
                    # 理论上不应该到达这里，因为市价单应该已经处理过
                    order_data = {
                        'message': '订单已创建但无法立即执行',
                        'order_id': order.order_id,
                        'status': 'valid',
                        'order_status': order.order_status.value,
                        'error': None
                    }
        
    except Exception as e:
        logger.error(f"处理新订单请求时发生未预料的错误: {str(e)}", exc_info=True)
        # 尝试记录失败的订单（如果可能）
        try:
            with db.session.begin_nested(): # 使用嵌套事务
                order = Order(
                    user_id=user_id,
                    ticker=ticker,
                    order_type=OrderType(order_type) if order_type else None,
                    order_execution_type=OrderExecutionType(order_execution_type) if order_execution_type else None,
                    order_price=float(order_price) if order_price else None,
                    order_quantity=int(order_quantity) if order_quantity else None,
                    order_status=OrderStatus.FAILED # 使用枚举对象
                )
                # 单独设置remark字段
                order.remark = f"处理请求时发生内部错误: {str(e)}"
                
                db.session.add(order)
                db.session.commit()
                logger.info(f"已记录失败的订单尝试，ID: {order.order_id}")
                return {
                    'message': '订单处理失败',
                    'error': '服务器内部错误，已记录失败尝试。',
                    'order_id': order.order_id,
                    'status': OrderStatus.FAILED.value
                }, 500 # 仍然返回 500 表示服务器错误，但已记录
        except Exception as nested_e:
            logger.error(f"尝试记录失败订单时再次出错: {nested_e}")
            # 如果记录失败，返回通用 500 错误
            return {'error': '处理订单请求时发生内部错误'}, 500

        # 返回处理结果
        return order_data
    
    except Exception as e:
        logger.error(f"处理订单时发生未预期错误: {str(e)}", exc_info=True)
        return {
            'message': '订单处理失败',
            'status': 'invalid',
            'order_status': OrderStatus.FAILED.value,
            'error': f"处理订单时发生错误: {str(e)}"
        }

def simplified_process_order(user_id, ticker, order_type, order_execution_type, order_quantity, order_price=None):
    """
    简化的订单处理函数，将订单分为有效和无效两类，均记录在数据库中
    无效订单不会影响用户持仓和资金
    
    参数:
        user_id (int): 用户ID
        ticker (str): 股票代码
        order_type (str): 订单类型 (buy/sell)
        order_execution_type (str): 执行类型 (market/limit)
        order_quantity (int): 订单数量
        order_price (float, optional): 订单价格，限价单必须提供
        
    返回:
        dict: 包含处理结果的字典，status字段标识订单状态（'valid'或'invalid'）
    """
    try:
        logger.info(f"开始处理订单: {ticker}, {order_type}, {order_quantity}股")
        order_status = OrderStatus.PENDING  # 默认为待处理状态
        failure_reason = None  # 失败原因
        order_data = None      # 订单数据

        # 1. 基本参数验证
        if not all([ticker, order_type, order_execution_type, order_quantity]):
            missing = []
            if not ticker: missing.append('ticker')
            if not order_type: missing.append('order_type')
            if not order_execution_type: missing.append('order_execution_type')
            if not order_quantity: missing.append('order_quantity')
            failure_reason = f"缺少必要参数: {', '.join(missing)}"
            order_status = OrderStatus.FAILED
            logger.warning(f"订单参数验证失败: {failure_reason}")

        # 2. 订单类型和执行类型验证
        elif order_type not in [OrderType.BUY.value, OrderType.SELL.value]:
            failure_reason = f"无效的订单类型: {order_type}"
            order_status = OrderStatus.FAILED
            logger.warning(f"订单类型验证失败: {failure_reason}")
        elif order_execution_type not in [OrderExecutionType.MARKET.value, OrderExecutionType.LIMIT.value]:
            failure_reason = f"无效的执行类型: {order_execution_type}"
            order_status = OrderStatus.FAILED
            logger.warning(f"订单执行类型验证失败: {failure_reason}")

        # 3. 数量验证
        elif not isinstance(order_quantity, int) and not order_quantity.isdigit():
            failure_reason = "订单数量必须为整数"
            order_status = OrderStatus.FAILED
            logger.warning(f"订单数量验证失败: {failure_reason}")
        elif int(order_quantity) <= 0:
            failure_reason = "订单数量必须为正整数"
            order_status = OrderStatus.FAILED
            logger.warning(f"订单数量验证失败: {failure_reason}")

        # 4. 限价单价格验证
        elif order_execution_type == OrderExecutionType.LIMIT.value:
            if order_price is None:
                failure_reason = "限价单必须指定价格"
                order_status = OrderStatus.FAILED
                logger.warning(f"订单价格验证失败: {failure_reason}")
            elif not isinstance(order_price, (int, float)) and not (isinstance(order_price, str) and order_price.replace('.', '', 1).isdigit()):
                failure_reason = "价格必须为数字"
                order_status = OrderStatus.FAILED
                logger.warning(f"订单价格验证失败: {failure_reason}")
            elif float(order_price) <= 0:
                failure_reason = "价格必须大于0"
                order_status = OrderStatus.FAILED
                logger.warning(f"订单价格验证失败: {failure_reason}")

        # 转换数据类型
        order_quantity = int(order_quantity)
        if order_price is not None and order_execution_type == OrderExecutionType.LIMIT.value:
            order_price = float(order_price)

        # 5. 获取当前市场价格
        price_success, price_result = get_market_price(ticker)
        if not price_success and not failure_reason:
            failure_reason = f"无法获取市场价格: {price_result}"
            order_status = OrderStatus.FAILED
            logger.warning(f"获取市场价格失败: {failure_reason}")
        elif not failure_reason:
            market_price = price_result

        # 数据库操作
        with order_transaction_scope() as session:
            # 6. 业务规则验证 - 验证账户和持仓
            account = AccountBalance.query.filter_by(user_id=user_id).first()
            
            # 检查账户是否存在
            if not account and not failure_reason:
                failure_reason = "未找到用户账户信息"
                order_status = OrderStatus.FAILED
                logger.warning(f"账户验证失败: {failure_reason}")
            
            # 对于卖单，检查持仓是否足够
            elif order_type == OrderType.SELL.value and not failure_reason:
                portfolio = Portfolio.query.filter_by(user_id=user_id, ticker=ticker).first()
                if not portfolio:
                    failure_reason = f"您没有持有{ticker}的股票"
                    order_status = OrderStatus.FAILED
                    logger.warning(f"持仓验证失败: {failure_reason}")
                elif portfolio.quantity < order_quantity:
                    failure_reason = f"持有股票不足 (需要 {order_quantity}股, 持有 {portfolio.quantity}股)"
                    order_status = OrderStatus.FAILED
                    logger.warning(f"持仓数量验证失败: {failure_reason}")
            
            # 对于买单，检查余额是否足够
            elif order_type == OrderType.BUY.value and not failure_reason:
                # 将价格和数量转换为Decimal类型以避免float和Decimal混合运算
                market_price_decimal = Decimal(str(market_price)) if not isinstance(market_price, Decimal) else market_price
                order_quantity_decimal = Decimal(str(order_quantity))
                
                if order_execution_type == OrderExecutionType.MARKET.value:
                    estimated_cost = market_price_decimal * order_quantity_decimal
                else:
                    order_price_decimal = Decimal(str(order_price)) if not isinstance(order_price, Decimal) else order_price
                    estimated_cost = order_price_decimal * order_quantity_decimal
                
                # 将结果转回float用于比较
                estimated_cost_float = float(estimated_cost)
                
                if account.available_balance < estimated_cost_float:
                    failure_reason = f"余额不足 (需要 ¥{estimated_cost_float:.2f}, 可用 ¥{account.available_balance:.2f})"
                    order_status = OrderStatus.FAILED
                    logger.warning(f"余额验证失败: {failure_reason}")
            
            # 7. 创建订单记录
            logger.info(f"创建订单记录: 状态={order_status.value}, 原因={failure_reason or 'N/A'}")
            
            order = Order(
                user_id=user_id,
                ticker=ticker,
                order_type=OrderType(order_type),
                order_execution_type=OrderExecutionType(order_execution_type),
                order_price=order_price if order_execution_type == OrderExecutionType.LIMIT.value else None,
                order_quantity=order_quantity,
                order_status=order_status
            )
            # 单独设置remark字段
            if failure_reason:
                order.remark = failure_reason
            # 设置时间戳
            order.created_at = datetime.now()
            order.updated_at = datetime.now()
            
            session.add(order)
            session.flush()  # 确保获取订单ID
            
            # 如果是有效订单
            if order_status == OrderStatus.PENDING:
                logger.info(f"有效订单 #{order.order_id} 已创建")
                
                # 对于买入限价单，冻结资金（只在这里执行一次）
                if order_type == OrderType.BUY.value and order_execution_type == OrderExecutionType.LIMIT.value:
                    # 确保使用Decimal类型计算
                    order_price_decimal = Decimal(str(order_price)) if not isinstance(order_price, Decimal) else order_price
                    order_quantity_decimal = Decimal(str(order_quantity))
                    frozen_amount_decimal = order_price_decimal * order_quantity_decimal
                    
                    # 转回float用于数据库存储
                    frozen_amount = float(frozen_amount_decimal)
                    
                    # 更新账户余额和冻结余额
                    account.available_balance -= frozen_amount
                    account.frozen_balance += frozen_amount
                    # 移除手动计算 total_balance，交给事件监听器处理
                    
                    logger.info(f"已冻结用户 {user_id} 资金: ¥{frozen_amount:.2f} 用于限价单 #{order.order_id}")
                
                # 判断是否可以立即执行
                can_execute_now = False
                execution_price = None
                
                # 市价单可以立即执行
                if order_execution_type == OrderExecutionType.MARKET.value:
                    can_execute_now = True
                    execution_price = market_price
                # 检查限价单是否符合立即执行条件
                elif order_execution_type == OrderExecutionType.LIMIT.value:
                    # 买入限价单: 当市场价格 <= 限价时可执行
                    if order_type == OrderType.BUY.value and market_price <= order_price:
                        can_execute_now = True
                        execution_price = market_price  # 以市场价执行
                        logger.info(f"买入限价单 #{order.order_id} 可以立即执行: 市场价格({market_price}) <= 限价({order_price})")
                    
                    # 卖出限价单: 当市场价格 >= 限价时可执行
                    elif order_type == OrderType.SELL.value and market_price >= order_price:
                        can_execute_now = True
                        execution_price = market_price  # 以市场价执行
                        logger.info(f"卖出限价单 #{order.order_id} 可以立即执行: 市场价格({market_price}) >= 限价({order_price})")
                
                # 立即执行符合条件的订单(包括市价单和符合条件的限价单)
                if can_execute_now:
                    logger.info(f"订单 #{order.order_id} 满足立即执行条件，执行价格: {execution_price}")
                    portfolio_obj = Portfolio.query.filter_by(user_id=user_id, ticker=ticker).first()
                    
                    # 使用Decimal类型计算总金额以避免类型不匹配
                    execution_price_decimal = Decimal(str(execution_price)) if not isinstance(execution_price, Decimal) else execution_price
                    order_quantity_decimal = Decimal(str(order_quantity))
                    total_amount_decimal = execution_price_decimal * order_quantity_decimal
                    total_amount = float(total_amount_decimal)  # 转回float用于存储
                    
                    try:
                        _execute_order_logic(session, order, account, portfolio_obj, execution_price, total_amount)
                        order_data = {
                            'message': f'市价单已成功执行',
                            'order_id': order.order_id,
                            'executed_price': execution_price,
                            'total_amount': total_amount,
                            'status': 'valid',
                            'order_status': order.order_status.value,
                            'error': None
                        }
                    except Exception as e:
                        logger.error(f"执行订单 #{order.order_id} 失败: {str(e)}")
                        order.order_status = OrderStatus.FAILED
                        order.remark = f"执行失败: {str(e)}"
                        order_data = {
                            'message': '订单执行失败',
                            'order_id': order.order_id,
                            'status': 'invalid',
                            'order_status': order.order_status.value,
                            'error': order.remark
                        }
                else:
                    # 处理限价单 - 始终进入PENDING状态
                    if order_execution_type == OrderExecutionType.LIMIT.value:
                        # 对于买入限价单，之前已经冻结过资金，这里不再重复冻结
                        execution_condition = "高于" if order_type == OrderType.SELL.value else "低于或等于"
                        order_data = {
                            'message': f'限价单已创建，将在市场价格{execution_condition}{order_price}时执行',
                            'order_id': order.order_id,
                            'limit_price': order_price,
                            'current_market_price': market_price,
                            'status': 'valid',
                            'order_status': order.order_status.value,
                            'error': None
                        }
                    else:
                        # 理论上不应该到达这里，因为市价单应该已经处理过
                        order_data = {
                            'message': '订单已创建但无法立即执行',
                            'order_id': order.order_id,
                            'status': 'valid',
                            'order_status': order.order_status.value,
                            'error': None
                        }
            else:
                # 无效订单
                order_data = {
                    'message': '订单创建失败',
                    'order_id': order.order_id,
                    'status': 'invalid',
                    'order_status': order.order_status.value,
                    'error': failure_reason
                }
                
            # 提交事务 (由上下文管理器处理)
            
        # 返回处理结果
        return order_data
    
    except Exception as e:
        logger.error(f"处理订单时发生未预期错误: {str(e)}", exc_info=True)
        return {
            'message': '订单处理失败',
            'status': 'invalid',
            'order_status': OrderStatus.FAILED.value,
            'error': f"处理订单时发生错误: {str(e)}"
        }

def scan_pending_limit_orders():
    """
    扫描所有待处理(PENDING)状态的限价单，检查当前市场价格是否满足执行条件
    如果满足条件则执行订单
    
    此函数设计为由定时任务调用
    """
    logger.info("开始扫描待处理的限价单...")
    
    try:
        # 查询所有PENDING状态的限价单
        pending_limit_orders = Order.query.filter_by(
            order_status=OrderStatus.PENDING,
            order_execution_type=OrderExecutionType.LIMIT
        ).all()
        
        if not pending_limit_orders:
            logger.info("没有待处理的限价单")
            return
            
        logger.info(f"找到 {len(pending_limit_orders)} 个待处理的限价单")
        
        # 遍历每个待处理的限价单
        for order in pending_limit_orders:
            try:
                # 获取当前市场价格
                price_success, market_price = get_market_price(order.ticker)
                
                if not price_success:
                    logger.warning(f"无法获取 {order.ticker} 的市场价格，跳过订单 #{order.order_id}")
                    continue
                
                # 转换为Decimal类型进行精确比较
                market_price_decimal = Decimal(str(market_price)) if not isinstance(market_price, Decimal) else market_price
                order_price_decimal = Decimal(str(order.order_price)) if not isinstance(order.order_price, Decimal) else order.order_price
                
                # 检查是否满足执行条件
                can_execute = False
                
                # 买入限价单: 当市场价格 <= 限价时可执行
                if order.order_type == OrderType.BUY and market_price_decimal <= order_price_decimal:
                    can_execute = True
                    logger.info(f"买入限价单 #{order.order_id} 可以执行: 市场价格({market_price}) <= 限价({order.order_price})")
                
                # 卖出限价单: 当市场价格 >= 限价时可执行
                elif order.order_type == OrderType.SELL and market_price_decimal >= order_price_decimal:
                    can_execute = True
                    logger.info(f"卖出限价单 #{order.order_id} 可以执行: 市场价格({market_price}) >= 限价({order.order_price})")
                
                # 如果满足执行条件，执行订单
                if can_execute:
                    # 使用现有的execute_order函数执行订单
                    logger.info(f"执行限价单 #{order.order_id}, 股票: {order.ticker}, 类型: {order.order_type.value}, 价格: {market_price}")
                    success, message = execute_order(order, market_price)
                    
                    if success:
                        logger.info(f"限价单 #{order.order_id} 执行成功")
                    else:
                        logger.error(f"限价单 #{order.order_id} 执行失败: {message}")
            
            except Exception as e:
                logger.error(f"处理限价单 #{order.order_id} 时发生错误: {str(e)}", exc_info=True)
                # 继续处理下一个订单
        
        logger.info("限价单扫描完成")
        
    except Exception as e:
        logger.error(f"扫描限价单时发生错误: {str(e)}", exc_info=True)