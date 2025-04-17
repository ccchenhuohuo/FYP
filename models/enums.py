"""\nDefine the enumeration class for the trading system\nManage all enumeration values related to trading\n"""
from enum import Enum, auto

class OrderType(Enum):
    """Order direction enumeration class, buy or sell"""
    BUY = 'buy'
    SELL = 'sell'
    
    def __str__(self):
        return self.value

class OrderExecutionType(Enum):
    """Order execution type enumeration class, limit order or market order"""
    LIMIT = 'limit'
    MARKET = 'market'
    
    def __str__(self):
        return self.value

class OrderStatus(Enum):
    """Order status enumeration class"""
    PENDING = 'pending'     # Pending execution
    EXECUTED = 'executed'   # Executed
    CANCELLED = 'cancelled' # Cancelled
    REJECTED = 'rejected'   # Rejected (can be used for manual rejection by admin)
    FAILED = 'failed'       # Execution failed (e.g. insufficient balance, system error, etc.)
    
    def __str__(self):
        return self.value

class TransactionStatus(Enum):
    """Transaction status enumeration class"""
    COMPLETED = 'completed' # Completed
    FAILED = 'failed'       # Failed
    REVERSED = 'reversed'   # Reversed
    
    def __str__(self):
        return self.value

class AccountStatus(Enum):
    """User account status enumeration class"""
    ACTIVE = 'active'       # Active
    SUSPENDED = 'suspended' # Suspended
    DELETED = 'deleted'     # Deleted
    
    def __str__(self):
        return self.value