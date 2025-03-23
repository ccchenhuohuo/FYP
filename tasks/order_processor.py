"""
订单处理任务
定期检查和执行待处理的限价单
"""
from models import db, Order, MarketData
from routes.user.order import execute_market_order, get_market_price_with_message
import time
import threading
import logging
from flask import current_app

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderProcessor:
    def __init__(self, app):
        self.app = app
        self.thread = None
        self.running = False

    def process_limit_orders(self):
        """
        处理所有待处理的限价单
        检查当前市场价格是否满足限价单的执行条件
        """
        while self.running:
            try:
                with self.app.app_context():
                    # 获取所有待处理的限价单
                    pending_orders = Order.query.filter_by(
                        order_status='pending',
                        order_execution_type='limit'
                    ).all()
                    
                    logger.info(f"检查 {len(pending_orders)} 个待处理的限价单")
                    
                    for order in pending_orders:
                        try:
                            # 获取当前市场价格
                            market_price_result = get_market_price_with_message(order.ticker)
                            
                            if isinstance(market_price_result, tuple):
                                logger.warning(f"无法获取 {order.ticker} 的市场价格: {market_price_result[0]}")
                                continue
                                
                            market_price = market_price_result
                            
                            # 检查是否满足执行条件
                            can_execute = False
                            if order.order_type == 'buy' and market_price <= order.order_price:
                                can_execute = True
                                logger.info(f"买入限价单 #{order.order_id} 可以执行：市场价格({market_price}) <= 限价({order.order_price})")
                            elif order.order_type == 'sell' and market_price >= order.order_price:
                                can_execute = True
                                logger.info(f"卖出限价单 #{order.order_id} 可以执行：市场价格({market_price}) >= 限价({order.order_price})")
                            
                            # 如果满足条件，执行订单
                            if can_execute:
                                if execute_market_order(order):
                                    logger.info(f"限价单 #{order.order_id} 执行成功")
                                else:
                                    logger.error(f"限价单 #{order.order_id} 执行失败")
                        
                        except Exception as e:
                            logger.error(f"处理限价单 #{order.order_id} 时发生错误: {str(e)}")
                            continue
                
            except Exception as e:
                logger.error(f"处理限价单时发生错误: {str(e)}")
            
            # 等待一段时间后再次检查
            time.sleep(60)  # 每分钟检查一次

    def start(self):
        """
        启动订单处理器
        在后台线程中运行，定期检查和执行限价单
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.process_limit_orders, daemon=True)
            self.thread.start()
            logger.info("订单处理器已启动")

    def stop(self):
        """
        停止订单处理器
        """
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1)
            logger.info("订单处理器已停止")

def start_order_processor(app):
    """
    创建并启动订单处理器
    """
    processor = OrderProcessor(app)
    processor.start()
    return processor 