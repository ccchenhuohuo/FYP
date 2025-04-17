"""
user路由模块
包含用户功能相关路由
"""
from flask import Blueprint

# 创建用户相关蓝图
user_bp = Blueprint('user', __name__, url_prefix='/user')

# 导入路由模块
from . import account  # 账户相关路由
from . import order    # 订单相关路由 
from . import stock    # 股票相关路由
from . import monte_carlo  # 蒙特卡洛模拟路由
from . import ai_assistant  # AI助手路由
from . import ai_analysis  # AI分析路由 