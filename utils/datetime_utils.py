"""
Date time processing utility module
Provide helper functions for date time formatting and processing
"""
from datetime import datetime

def safe_date_format(dt_value, fmt='%Y-%m-%d %H:%M'):
    """
    Safely format date time
    Handle different types of date time values, ensuring a formatted string is returned
    
    Parameters:
    dt_value - date time value, can be a datetime object or a string
    fmt - date format string
    
    Returns:
    str: formatted date time string
    """
    if dt_value is None:
        return "-"
    
    try:
        # if it's a string, try to convert to datetime
        if isinstance(dt_value, str):
            try:
                dt_value = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            except:
                return dt_value  # if it cannot be converted, return the original string
        
        # if it has a strftime method, use it to format
        if hasattr(dt_value, 'strftime'):
            return dt_value.strftime(fmt)
        
        # other cases return string representation
        return str(dt_value)
    except Exception as e:
        print(f"Error formatting date time: {e}, value: {dt_value}, type: {type(dt_value)}")
        return str(dt_value)

def create_safe_dict(transaction):
    """
    Create a safe dictionary from a transaction object
    Avoid date time format issues in templates
    
    Parameters:
    transaction - transaction object
    
    Returns:
    dict: dictionary containing transaction information
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