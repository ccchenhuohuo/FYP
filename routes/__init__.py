"""
routes/__init__.py

这个文件是routes包的初始化文件，负责：
1. 导入各个子模块
2. 提供注册所有路由的函数

routes/
├── __init__.py             # 导入子模块并提供路由注册函数
├── auth/                   # 认证相关路由
│   ├── __init__.py         # 定义auth蓝图
│   └── auth.py             # 认证功能实现
├── user/                   # 用户相关路由
│   ├── __init__.py         # 定义user蓝图
│   ├── account.py          # 账户管理功能
│   ├── order.py            # 订单管理功能
│   ├── stock.py            # 股票相关功能
│   ├── monte_carlo.py      # 蒙特卡洛模拟功能
│   └── ai_assistant.py     # AI助手功能
├── admin/                  # 管理员相关路由
│   ├── __init__.py         # 定义admin蓝图
│   └── admin.py            # 管理员功能实现
└── core/                   # 核心路由
    ├── __init__.py         # 定义main蓝图
    └── welcome.py          # 欢迎页面路由
"""

def register_routes(app):
    """
    注册所有路由到Flask应用
    
    参数:
    app (Flask): Flask应用实例
    """
    # 导入子模块
    from .auth import auth_bp
    from .user import user_bp
    from .admin import admin_bp
    from .core import main_bp
    from .user.monte_carlo import monte_carlo_bp
    
    # 导入路由实现
    from .auth import auth
    from .user import account, order, stock, ai_assistant
    from .admin import admin
    from .core import welcome
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(monte_carlo_bp) 