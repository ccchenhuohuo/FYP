"""
订单处理任务
定期检查和执行待处理的限价单和市价单
"""
from models import db, Order
from utils.order_utils import get_market_price, can_execute_immediately, execute_order
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
        # 使用配置的检查间隔或默认值
        self.check_interval = app.config.get('ORDER_CHECK_INTERVAL', 5)  # 默认每5秒检查一次

    def process_orders(self):
        """
        处理所有待处理的订单
        包括限价单和市价单
        """
        while self.running:
            try:
                with self.app.app_context():
                    # 获取所有待处理的订单（包括限价单和市价单）
                    pending_orders = Order.query.filter_by(order_status='pending').all()
                    
                    logger.info(f"检查 {len(pending_orders)} 个待处理的订单")
                    
                    # 首先处理市价单
                    market_orders = [order for order in pending_orders if order.order_execution_type == 'market']
                    limit_orders = [order for order in pending_orders if order.order_execution_type == 'limit']
                    
                    logger.info(f"其中 {len(market_orders)} 个市价单, {len(limit_orders)} 个限价单")
                    
                    # 处理市价单
                    for order in market_orders:
                        try:
                            # 获取当前市场价格
                            price_success, price_result = get_market_price(order.ticker)
                            
                            if not price_success:
                                logger.warning(f"无法获取 {order.ticker} 的市场价格: {price_result}")
                                continue
                                
                            market_price = price_result
                            
                            # 市价单应该立即执行
                            exec_success, exec_message = execute_order(order, market_price)
                            
                            if exec_success:
                                logger.info(f"市价单 #{order.order_id} 执行成功")
                            else:
                                logger.error(f"市价单 #{order.order_id} 执行失败: {exec_message}")
                        
                        except Exception as e:
                            logger.error(f"处理市价单 #{order.order_id} 时发生错误: {str(e)}")
                            continue
                    
                    # 处理限价单
                    for order in limit_orders:
                        try:
                            # 获取当前市场价格
                            price_success, price_result = get_market_price(order.ticker)
                            
                            if not price_success:
                                logger.warning(f"无法获取 {order.ticker} 的市场价格: {price_result}")
                                continue
                                
                            market_price = price_result
                            
                            # 检查是否满足执行条件
                            if can_execute_immediately(order, market_price):
                                # 尝试执行订单
                                exec_success, exec_message = execute_order(order, market_price)
                                
                                if exec_success:
                                    logger.info(f"限价单 #{order.order_id} 执行成功")
                                else:
                                    logger.error(f"限价单 #{order.order_id} 执行失败: {exec_message}")
                        
                        except Exception as e:
                            logger.error(f"处理限价单 #{order.order_id} 时发生错误: {str(e)}")
                            continue
                
            except Exception as e:
                logger.error(f"处理订单时发生错误: {str(e)}")
            
            # 等待指定时间后再次检查
            time.sleep(self.check_interval)

    def start(self):
        """
        启动订单处理器
        在后台线程中运行，定期检查和执行订单
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.process_orders, daemon=True)
            self.thread.start()
            logger.info(f"订单处理器已启动，检查间隔：{self.check_interval}秒")

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