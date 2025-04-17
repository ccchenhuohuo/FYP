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
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os
from datetime import datetime
import jinja2
import atexit

# 导入自定义的配置、认证和路由模块
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, DEBUG, PORT
from models import db, User, Admin, init_db
from auth import init_login_manager
from routes import register_routes
from tasks.order_processor import start_order_processor

# 设置环境变量，禁用兼容性警告
os.environ['SQLALCHEMY_WARN_20'] = '0'

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
    
    # 初始化Flask-Migrate
    migrate = Migrate(app, db)

    # 初始化Flask-Login
    init_login_manager(app)

    # 注册路由
    register_routes(app)
    
    # 启动订单处理器
    processor = start_order_processor(app)
    app.order_processor = processor  # 保存处理器实例以便后续使用
    
    # 注册关闭处理器的函数
    def cleanup():
        if hasattr(app, 'order_processor'):
            app.order_processor.stop()
            app.logger.info("订单处理器已停止")
    
    atexit.register(cleanup)
    app.logger.info("订单处理器已启动")
    
    # 添加日期时间对象错误处理
    @app.errorhandler(jinja2.exceptions.UndefinedError)
    def handle_undefined_error(e):
        # 记录错误信息和堆栈
        import traceback
        app.logger.error(f"Jinja2 UndefinedError: {str(e)}")
        app.logger.error(traceback.format_exc())
        
        # 显示友好的错误页面
        return render_template('error.html', error=str(e)), 500
    
    # 添加自定义过滤器
    @app.template_filter('safe_round')
    def safe_round(value, precision=0):
        """安全的四舍五入过滤器，处理各种类型的值"""
        try:
            if hasattr(value, '__round__'):
                return round(value, precision)
            elif isinstance(value, (int, float)):
                return round(float(value), precision)
            else:
                return value
        except (TypeError, ValueError):
            return value
            
    @app.template_filter('format_datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        """安全的日期时间格式化过滤器，处理各种类型的值"""
        if value is None:
            return "-"
        try:
            if isinstance(value, str):
                # 尝试转换字符串为日期时间对象
                try:
                    from datetime import datetime
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    return value
            if hasattr(value, 'strftime'):
                return value.strftime(format)
            return str(value)
        except Exception as e:
            app.logger.error(f"格式化日期时间出错: {str(e)}, 值: {repr(value)}, 类型: {type(value)}")
            return str(value)

    return app

# 创建应用实例
app = create_app()

# 只有直接运行此文件时才启动应用
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT) 