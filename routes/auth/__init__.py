"""
auth路由模块
包含认证相关功能路由
"""
from flask import Blueprint

# 创建认证相关蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth') 