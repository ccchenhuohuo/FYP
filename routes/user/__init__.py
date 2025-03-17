"""
user路由模块
包含用户功能相关路由
"""
from flask import Blueprint

# 创建用户相关蓝图
user_bp = Blueprint('user', __name__, url_prefix='/user') 