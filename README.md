# 股票数据采集与分析系统

这个项目是一个完整的股票数据采集和分析系统，集成了用户管理、数据采集和数据分析功能。系统使用Flask框架构建Web界面，通过Yahoo Finance API获取主要科技公司的股票数据，并将数据存储在MySQL数据库中进行管理和分析。

## 项目架构

```
.
├── README.md                 # 项目说明文档
├── requirements.txt          # 项目依赖文件
├── app.py                    # Flask应用主文件
├── models.py                 # 数据库模型定义
├── obtain_stock_data.py      # 股票数据采集脚本
├── static/                   # 静态资源目录
│   ├── css/                 # CSS样式文件
│   │   └── main.css        # 主样式文件
│   └── js/                 # JavaScript文件
│       ├── auth/           # 认证相关JS
│       │   ├── login.js    # 登录逻辑
│       │   └── register.js # 注册逻辑
│       ├── user/           # 用户页面JS
│       └── admin/          # 管理员页面JS
├── templates/               # HTML模板目录
│   ├── auth/              # 认证相关模板
│   │   ├── login.html    # 用户登录页面
│   │   └── register.html # 用户注册页面
│   ├── user/             # 用户页面模板
│   │   └── dashboard.html # 用户仪表盘
│   └── admin/            # 管理员页面模板
└── routes/                 # 路由模块目录
    ├── __init__.py       # 路由初始化
    ├── auth_routes.py    # 认证相关路由
    ├── user_routes.py    # 用户相关路由
    └── admin_routes.py   # 管理员相关路由
```

## 系统功能

### 1. 用户管理系统
- 用户注册和登录
- 管理员登录和管理
- 用户权限控制

### 2. 数据采集功能
- 自动获取主要科技股数据：
  - AAPL (苹果)
  - MSFT (微软)
  - AMZN (亚马逊)
  - GOOGL (谷歌)
  - META (Meta)
  - NFLX (奈飞)
  - TSLA (特斯拉)

### 3. 数据存储
- 市场数据 (MarketData)
  - 开盘价、最高价、最低价
  - 收盘价、交易量
  - 数据时间戳
- 基本面数据 (FundamentalData)
  - 市值、市盈率、市净率
  - 股息收益率
  - 收入和净利润
- 资产负债表数据 (BalanceSheet)
  - 流动资产和非流动资产
  - 流动负债和非流动负债
- 利润表数据 (IncomeStatement)
  - 收入和成本
  - 营业利润和净利润

## 环境配置

### 1. 系统要求
- Python 3.8+
- MySQL 8.0+
- pip包管理器

### 2. 虚拟环境设置
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
# 确保在虚拟环境中
pip install -r requirements.txt
```

### 4. 数据库配置
```sql
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE stock_data_v1;
```

更新数据库配置（在obtain_stock_data.py中）：
```python
DB_CONFIG = {
    'user': 'root',
    'password': 'your_password',
    'host': 'localhost',
    'port': '3306',
    'database': 'stock_data_v1'
}
```

## 启动系统

### 1. 初始化数据库
```bash
# 确保在虚拟环境中
python app.py init-db
```

### 2. 采集股票数据
```bash
# 确保在虚拟环境中
python obtain_stock_data.py
```

### 3. 启动Web应用
```bash
# 确保在虚拟环境中
python app.py
```

访问 http://localhost:5001 查看Web界面

## 数据查询示例

### 1. 获取特定股票数据
```python
from models import MarketData
from app import app

with app.app_context():
    # 获取苹果公司最近的股票数据
    apple_data = MarketData.query.filter_by(ticker='AAPL')\
                         .order_by(MarketData.date.desc())\
                         .limit(5).all()
```

### 2. 分析基本面数据
```python
from models import FundamentalData
import pandas as pd

with app.app_context():
    # 获取所有公司的市值数据
    market_caps = FundamentalData.query.with_entities(
        FundamentalData.ticker,
        FundamentalData.market_cap
    ).all()
    
    # 转换为DataFrame进行分析
    df = pd.DataFrame(market_caps, columns=['ticker', 'market_cap'])
```

## 注意事项

### 1. 环境相关
- 始终在虚拟环境中运行命令
- 定期更新依赖包
- 确保MySQL服务正常运行

### 2. 数据采集
- Yahoo Finance API可能有请求限制
- 建议错开高峰期采集数据
- 某些数据可能暂时不可用

### 3. 数据安全
- 定期备份数据库
- 不要将数据库密码提交到版本控制
- 及时更新安全补丁

## 故障排除

### 1. 数据库连接问题
```bash
# 检查MySQL服务状态
sudo service mysql status  # Linux
# 或
net start mysql  # Windows
```

### 2. 依赖包冲突
```bash
# 重新创建虚拟环境
deactivate  # 退出当前虚拟环境
rm -rf venv  # 删除旧环境
python -m venv flask_env  # 创建新环境
source flask_env/bin/activate # 激活环境
pip install -r requirements.txt  # 重新安装依赖
```