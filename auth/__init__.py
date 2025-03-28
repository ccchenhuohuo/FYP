"""
auth模块 - 用户认证系统

该模块负责：
1. 初始化Flask-Login以处理用户认证
2. 提供用户加载函数，支持普通用户和管理员登录
3. 设置登录视图和未登录用户的重定向
4. 为整个应用程序提供认证基础设施

这是应用程序认证系统的核心，由app.py在应用启动时初始化。
"""
from flask_login import LoginManager
from models import User, Admin

# 创建LoginManager实例，但不立即初始化
# 它将在init_login_manager函数中与Flask应用关联
login_manager = LoginManager()

def init_login_manager(app):
    """
    初始化Flask-Login并配置认证系统
    
    参数:
        app (Flask): Flask应用实例
    
    注意:
        此函数在app.py中的create_app函数内被调用
    """
    # 将LoginManager与Flask应用关联
    login_manager.init_app(app)
    
    # 配置登录视图端点
    login_manager.login_view = 'auth.login'
    
    # 设置未登录时的提示消息
    login_manager.login_message = "请先登录以访问此页面"
    login_manager.login_message_category = "info"
    
    # 用户加载函数已通过装饰器在下方定义
    
@login_manager.user_loader
def load_user(user_id):
    """
    加载用户的回调函数
    
    当Flask-Login需要获取当前登录用户的信息时，它会调用此函数
    
    参数:
        user_id (str): 用户的唯一标识符
            - 对于管理员，格式为'admin_数字'，例如'admin_1'
            - 对于普通用户，为数字字符串
    
    返回:
        User或Admin: 找到的用户对象
        None: 如果未找到用户
    
    安全提示:
        管理员ID必须以'admin_'开头，这是区分管理员和普通用户的关键
    """
    if user_id.startswith('admin_'):
        # 处理管理员ID
        admin_id = int(user_id.split('_')[1])
        return Admin.query.get(admin_id)
    else:
        # 处理普通用户ID
        try:
            return User.query.get(int(user_id))
        except ValueError:
            # 如果ID无法转换为整数，返回None
            return None 