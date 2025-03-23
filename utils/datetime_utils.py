"""
日期时间处理工具模块
提供日期时间格式化和处理的辅助函数
"""
from datetime import datetime

def safe_date_format(dt_value, fmt='%Y-%m-%d %H:%M'):
    """
    安全地格式化日期时间
    处理不同类型的日期时间值，确保返回格式化的字符串
    
    参数:
    dt_value - 日期时间值，可以是datetime对象或字符串
    fmt - 日期格式字符串
    
    返回:
    格式化的日期时间字符串
    """
    if dt_value is None:
        return "-"
    
    try:
        # 如果是字符串，尝试转换为datetime
        if isinstance(dt_value, str):
            try:
                dt_value = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            except:
                return dt_value  # 如果无法转换，直接返回原字符串
        
        # 如果有strftime方法，使用它格式化
        if hasattr(dt_value, 'strftime'):
            return dt_value.strftime(fmt)
        
        # 其他情况返回字符串表示
        return str(dt_value)
    except Exception as e:
        print(f"格式化日期时间出错: {e}, 值: {dt_value}, 类型: {type(dt_value)}")
        return str(dt_value)

def create_safe_dict(transaction):
    """
    从交易对象创建安全字典
    避免模板中的日期时间格式问题
    
    参数:
    transaction - 交易对象
    
    返回:
    包含交易信息的字典
    """
    if transaction is None:
        return None
        
    safe_dict = {
        'transaction_id': transaction.transaction_id,
        'user': {'user_name': transaction.user.user_name} if hasattr(transaction, 'user') and transaction.user else {'user_name': '未知用户'},
        'transaction_type': transaction.transaction_type,
        'amount': transaction.amount,
        'status': transaction.status,
        'remark': transaction.remark,
        'created_at': safe_date_format(transaction.created_at),
        'updated_at': safe_date_format(transaction.updated_at)
    }
    
    return safe_dict 