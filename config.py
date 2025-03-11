"""
config.py

这个文件包含了应用程序的所有配置项，包括：
1. 密钥配置
2. 数据库连接配置
3. 其他应用程序设置

将配置集中在一个文件中可以使应用程序更易于维护和配置。
"""

# Flask应用配置
SECRET_KEY = 'your-secret-key'  # 设置密钥，用于会话安全

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql://root:Cyy-20030611@localhost/stock_data_v1'  # 设置数据库连接URI
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭SQLAlchemy的修改跟踪功能，减少内存使用

# 股票数据API配置
GEMINI_API_KEY = "AIzaSyDYcL5BBKz812t_66bbBq0h3xm9v6DOG-M"

# 数据库连接配置
DB_CONFIG = {
    'user': 'root',
    'password': 'Cyy-20030611',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data_v1'
}

# 股票代码列表
TECH_TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "TSLA"]

# 应用运行配置
DEBUG = True
PORT = 5003