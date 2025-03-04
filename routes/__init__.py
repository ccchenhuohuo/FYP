"""
路由模块初始化文件
用于注册所有路由蓝图
"""
from flask import Blueprint

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
user_bp = Blueprint('user', __name__, url_prefix='/user')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 导入路由模块
from . import auth_routes
from . import user_routes
from . import admin_routes

# 初始化路由
def init_routes(app):
    """
    初始化所有路由
    将蓝图注册到Flask应用
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp) 