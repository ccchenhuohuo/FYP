"""
Number processing utility module
Provide helper functions for number formatting and processing
"""

def db_round(value, method='common', precision=2):
    """
    Round a number
    
    Parameters:
    value (float): the number to round
    method (str): rounding method, optional values are 'common' (common rounding), 'ceil' (round up), 'floor' (round down)
    precision (int): number of decimal places to keep
    
    Returns:
    float: the rounded number
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
    A dictionary class that supports the round method
    Used in templates to use round filter
    """
    def __round__(self, precision=0):
        """
        Implement the round method
        
        Parameters:
        precision (int): number of decimal places to keep
        
        Returns:
        float: the rounded number
        """
        # If the dictionary has a value key, round it
        if 'value' in self:
            return round(float(self['value']), precision)
        # Otherwise try to find a key that needs rounding
        for key in ['amount', 'price', 'average_price', 'current_price', 'market_value', 'pnl', 'pnl_percentage']:
            if key in self:
                return round(float(self[key]), precision)
        # If no suitable key is found, return 0
        return 0.0 