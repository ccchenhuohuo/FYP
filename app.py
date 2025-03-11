"""
这个文件是Flask应用的主入口点。它负责以下主要功能：
1. 配置和初始化Flask应用
2. 设置数据库连接
3. 初始化Flask-Login进行用户认证管理
4. 注册路由和蓝图
5. 启动开发服务器（当直接运行此文件时）

该应用主要用于股票数据分析和用户管理，包括普通用户和管理员两种角色。
"""
# 导入所需的Flask模块和扩展
from flask import Flask

# 导入自定义的配置、认证和路由模块
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, DEBUG, PORT
from models import db, init_db
from auth import init_login_manager
from routes import register_routes

def create_app():
    """
    创建并配置Flask应用
    
    返回:
    Flask: 配置好的Flask应用实例
    """
    # 创建Flask应用实例
    app = Flask(__name__)

    # 配置应用
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

    # 初始化数据库
    init_db(app)

    # 初始化Flask-Login
    init_login_manager(app)

    # 注册路由
    register_routes(app)

    return app

# 创建应用实例
app = create_app()

# 只有直接运行此文件时才启动应用
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT) 