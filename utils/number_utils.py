"""
数字处理工具模块
提供数字格式化和处理的辅助函数
"""

def db_round(value, method='common', precision=2):
    """
    对数值进行四舍五入
    
    参数:
    value (float): 要四舍五入的值
    method (str): 四舍五入的方法，可选值为'common'（普通四舍五入）, 'ceil'（向上取整）, 'floor'（向下取整）
    precision (int): 保留的小数位数
    
    返回:
    float: 四舍五入后的值
    """
    if method not in ("common", "ceil", "floor"):
        raise ValueError("Method must be common, ceil or floor")
    
    if method == "common":
        return round(value, precision)
    elif method == "ceil":
        import math
        factor = 10 ** precision
        return math.ceil(value * factor) / factor
    elif method == "floor":
        import math
        factor = 10 ** precision
        return math.floor(value * factor) / factor

class RoundableDict(dict):
    """
    支持round方法的字典类
    用于在模板中使用round过滤器
    """
    def __round__(self, precision=0):
        """
        实现四舍五入方法
        
        参数:
        precision (int): 保留的小数位数
        
        返回:
        float: 四舍五入后的值
        """
        # 如果字典中有value键，则对其进行四舍五入
        if 'value' in self:
            return round(float(self['value']), precision)
        # 否则尝试找到可能需要四舍五入的键
        for key in ['amount', 'price', 'average_price', 'current_price', 'market_value', 'pnl', 'pnl_percentage']:
            if key in self:
                return round(float(self[key]), precision)
        # 如果没有找到合适的键，返回0
        return 0.0 