"""
core路由模块
包含核心功能和欢迎界面相关路由
"""
from flask import Blueprint

# 创建主路由蓝图
main_bp = Blueprint('main', __name__) 