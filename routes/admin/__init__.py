"""
admin路由模块
包含管理员功能相关路由
"""
from flask import Blueprint

# 创建管理员相关蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin') 