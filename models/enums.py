"""\n交易系统枚举类定义\n集中管理所有交易相关的枚举值\n"""
from enum import Enum, auto

class OrderType(Enum):
    """订单方向枚举类，买入或卖出"""
    BUY = 'buy'
    SELL = 'sell'
    
    def __str__(self):
        return self.value

class OrderExecutionType(Enum):
    """订单执行类型枚举类，限价单或市价单"""
    LIMIT = 'limit'
    MARKET = 'market'
    
    def __str__(self):
        return self.value

class OrderStatus(Enum):
    """订单状态枚举类"""
    PENDING = 'pending'     # 待执行
    EXECUTED = 'executed'   # 已执行
    CANCELLED = 'cancelled' # 已取消
    REJECTED = 'rejected'   # 已拒绝
    
    def __str__(self):
        return self.value

class TransactionStatus(Enum):
    """交易状态枚举类"""
    COMPLETED = 'completed' # 已完成
    FAILED = 'failed'       # 失败
    REVERSED = 'reversed'   # 已撤销
    
    def __str__(self):
        return self.value

class AccountStatus(Enum):
    """用户账户状态枚举类"""
    ACTIVE = 'active'       # 活跃状态
    SUSPENDED = 'suspended' # 已暂停
    DELETED = 'deleted'     # 已删除
    
    def __str__(self):
        return self.value