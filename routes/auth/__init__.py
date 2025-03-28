"""
auth路由模块

该模块包含所有与认证相关的路由处理功能:
1. 用户登录和注册
2. 管理员登录
3. 用户登出
4. 其他认证相关功能

注意: 
- 这个模块负责路由和视图逻辑，而核心认证功能在auth包中实现
- 这里定义的是路由处理，而不是认证机制本身
"""
from flask import Blueprint

# 创建认证相关蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth') 