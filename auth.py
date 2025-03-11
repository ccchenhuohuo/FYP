"""
auth.py

这个文件包含了与用户认证相关的功能，包括：
1. Flask-Login的初始化
2. 用户加载函数
3. 其他与认证相关的辅助函数

将认证相关的功能集中在一个文件中可以提高代码的组织性和可维护性。
"""
from flask_login import LoginManager
from models import User, Admin

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 设置登录视图的端点
login_manager.login_message = "请先登录以访问此页面"  # 设置登录提示消息
login_manager.login_message_category = "info"  # 设置登录提示消息类别

def init_login_manager(app):
    """
    初始化Flask-Login
    
    参数:
    app (Flask): Flask应用实例
    """
    login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login用户加载回调函数

    这个函数被Flask-Login用来根据用户ID重新加载用户对象。
    它支持加载两种类型的用户：普通用户和管理员。

    参数:
    user_id (str): 用户的唯一标识符。对于管理员，格式为'admin_数字'；对于普通用户，为数字字符串。

    返回:
    User 或 Admin: 返回找到的用户对象（User或Admin实例）。
    None: 如果未找到用户，则返回None。

    注意:
    - 管理员ID的格式为'admin_数字'，例如'admin_1'
    - 普通用户ID为纯数字字符串
    """
    if user_id.startswith('admin_'):
        # 如果是管理员ID（格式为'admin_数字'）
        admin_id = int(user_id.split('_')[1])
        return Admin.query.get(admin_id)
    else:
        # 如果是普通用户ID
        return User.query.get(int(user_id)) 