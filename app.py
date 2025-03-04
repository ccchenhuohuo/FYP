# 导入所需的Flask模块和扩展
from flask import Flask, redirect, url_for
from flask_login import LoginManager

# 导入自定义的数据库模型和路由
from models import db, User, Admin, init_db
from routes import init_routes
from routes.monte_carlo import monte_carlo_bp  # 导入蒙特卡洛模拟蓝图

# 创建Flask应用实例
app = Flask(__name__)

# 配置应用
app.config['SECRET_KEY'] = 'your-secret-key'  # 设置密钥，用于会话安全
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Cyy-20030611@localhost/stock_data_v1'  # 设置数据库连接URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭SQLAlchemy的修改跟踪功能，减少内存使用

# 初始化数据库
init_db(app)

# 初始化Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'  # 设置登录视图的端点
login_manager.login_message = "请先登录以访问此页面"  # 设置登录提示消息
login_manager.login_message_category = "info"  # 设置登录提示消息类别

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login用户加载回调函数
    根据用户ID加载用户对象，支持普通用户和管理员两种类型
    """
    if user_id.startswith('admin_'):
        # 如果是管理员ID（格式为'admin_数字'）
        admin_id = int(user_id.split('_')[1])
        return Admin.query.get(admin_id)
    else:
        # 如果是普通用户ID
        return User.query.get(int(user_id))

# 初始化路由
init_routes(app)

# 注册蒙特卡洛模拟蓝图
app.register_blueprint(monte_carlo_bp)

# 添加根路由重定向
@app.route('/')
def index():
    return redirect(url_for('auth.index'))

# 添加登出路由重定向
@app.route('/logout')
def root_logout():
    """将根路径的登出请求重定向到auth.logout"""
    return redirect(url_for('auth.logout'))

# 只有直接运行此文件时才启动应用
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # 启动开发服务器，开启调试模式，监听5001端口 