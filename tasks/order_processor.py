"""
订单处理任务
定期检查和执行待处理的限价单
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
        self.check_interval = app.config.get('ORDER_CHECK_INTERVAL', 3600)  # 默认每小时检查一次

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
                logger.error(f"处理限价单时发生错误: {str(e)}")
            
            # 等待指定时间后再次检查
            time.sleep(self.check_interval)

    def start(self):
        """
        启动订单处理器
        在后台线程中运行，定期检查和执行限价单
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.process_limit_orders, daemon=True)
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