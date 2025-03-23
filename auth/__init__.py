"""
认证模块
负责用户认证和会话管理
"""
from flask_login import LoginManager
from models import User, Admin

def init_login_manager(app):
    """
    初始化Flask-Login
    配置用户加载函数和未登录用户的处理
    """
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        """根据用户ID加载用户"""
        if user_id.startswith('admin_'):
            # 如果ID以'admin_'开头，表示这是管理员ID
            admin_id = int(user_id.split('_')[1])
            return Admin.query.get(admin_id)
        else:
            # 否则是普通用户ID
            return User.query.get(int(user_id)) 