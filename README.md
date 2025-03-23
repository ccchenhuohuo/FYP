# 股票交易与分析系统

这是一个基于Flask的股票交易与分析系统，提供用户账户管理、股票数据分析、交易模拟、蒙特卡洛模拟以及AI助手等功能。

## 功能特性

### 用户管理
- 用户注册与登录
- 管理员账户管理
- 个人资料管理

### 账户与资金
- 账户余额查看
- 资金充值与提现（需要管理员审核）
- 交易记录查询与管理

### 股票交易
- 股票行情实时查看
- 买入/卖出股票（支持市价单和限价单）
- 限价单自动执行系统
- 订单管理（创建、查看、取消）
- 持仓查询与分析

### 数据分析
- 股票历史数据图表可视化
- 技术指标分析（MA、RSI、MACD等）
- 蒙特卡洛模拟预测
- 风险评估与模拟

### AI助手
- 基于Gemini AI的智能助手
- 股票相关问题咨询
- 投资建议与市场分析

## 技术栈

- **后端**: Flask, SQLAlchemy, PyMySQL
- **前端**: HTML, CSS, JavaScript, Bootstrap, Chart.js
- **数据库**: MySQL
- **AI**: Google Generative AI (Gemini)
- **数据分析**: Pandas, NumPy
- **并发处理**: Threading

## 安装步骤

### 前提条件
- Python 3.8+
- MySQL 5.7+
- pip (Python包管理器)

### 安装过程

1. 克隆仓库
```bash
git clone <仓库URL>
cd <项目目录>
```

2. 创建并激活虚拟环境
```bash
# 创建虚拟环境
python -m venv flask_env

# 激活虚拟环境
source flask_env/bin/activate  # Linux/macOS
# 或
.\flask_env\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置数据库
- 创建MySQL数据库
```sql
CREATE DATABASE stock_data_v1;
```
- 修改`config.py`中的数据库连接信息

5. 配置API密钥
- 获取Gemini AI API密钥: [Google AI Studio](https://ai.google.dev/)
- 获取Alpha Vantage API密钥: [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- 更新`config.py`中的API密钥或设置环境变量:
```bash
export GEMINI_API_KEY="您的Gemini API密钥"
export ALPHA_VANTAGE_API_KEY="您的Alpha Vantage API密钥"
```

6. 运行应用
```bash
flask run --debug
```

## 详细项目结构

```
/
├── app.py                      # 应用入口点，Flask应用配置和初始化
├── config.py                   # 配置文件，包含数据库和API密钥等配置
├── auth.py                     # 认证相关功能，用户登录验证
├── models/                     # 数据库模型
│   ├── __init__.py             # 模型初始化和公共函数
│   ├── admin.py                # 管理员模型
│   ├── user.py                 # 用户模型
│   ├── trade.py                # 交易相关模型（订单、交易记录）
│   ├── finance.py              # 财务相关模型（余额、资金交易）
│   └── market.py               # 市场数据模型（股票价格、基本面数据）
├── routes/                     # 路由模块
│   ├── __init__.py             # 路由注册
│   ├── auth/                   # 认证路由
│   │   ├── __init__.py         # 认证蓝图初始化
│   │   ├── login.py            # 登录路由
│   │   └── register.py         # 注册路由
│   ├── user/                   # 用户路由
│   │   ├── __init__.py         # 用户蓝图初始化
│   │   ├── account.py          # 账户管理（余额、充值、提现）
│   │   ├── order.py            # 订单管理（创建、取消、查询）
│   │   ├── stock.py            # 股票相关（行情、图表）
│   │   ├── monte_carlo.py      # 蒙特卡洛模拟
│   │   └── ai_assistant.py     # AI助手接口
│   ├── admin/                  # 管理员路由
│   │   ├── __init__.py         # 管理员蓝图初始化
│   │   ├── user_manage.py      # 用户管理
│   │   ├── fund_manage.py      # 资金管理（审核充值提现）
│   │   └── data_manage.py      # 数据管理
│   └── core/                   # 核心路由
│       ├── __init__.py         # 核心蓝图初始化
│       ├── home.py             # 首页
│       └── about.py            # 关于页面
├── static/                     # 静态资源
│   ├── css/                    # 样式表
│   │   ├── main.css            # 主样式表
│   │   ├── auth.css            # 认证页面样式
│   │   ├── admin.css           # 管理员界面样式
│   │   └── stock_chart.css     # 股票图表样式
│   ├── js/                     # JavaScript文件
│   │   ├── user/               # 用户相关JS
│   │   │   ├── navigation.js   # 导航栏交互
│   │   │   ├── account.js      # 账户操作（充值提现）
│   │   │   ├── stock_chart.js  # 股票图表和订单创建
│   │   │   ├── stock_chart_extra.js # 图表附加功能
│   │   │   ├── stock_analysis.js # 股票分析
│   │   │   └── ai_assistant.js # AI助手交互
│   │   ├── admin/              # 管理员相关JS
│   │   └── auth/               # 认证相关JS
│   └── picture.png             # 图片资源
├── templates/                  # HTML模板
│   ├── auth/                   # 认证相关模板
│   │   ├── login.html          # 登录页面
│   │   └── register.html       # 注册页面
│   ├── user/                   # 用户相关模板
│   │   ├── layout.html         # 用户界面布局
│   │   ├── account.html        # 账户页面
│   │   ├── stock_chart.html    # 股票图表页面
│   │   ├── ai_assistant.html   # AI助手页面
│   │   └── stock_analysis.html # 股票分析页面
│   ├── admin/                  # 管理员相关模板
│   │   ├── layout.html         # 管理员界面布局
│   │   ├── user_manage.html    # 用户管理页面
│   │   └── fund_manage.html    # 资金管理页面
│   ├── error.html              # 错误页面
│   ├── about.html              # 关于页面
│   └── privacy.html            # 隐私政策页面
├── tasks/                      # 后台任务
│   ├── __init__.py             # 任务初始化
│   └── order_processor.py      # 订单处理器（自动执行限价单）
├── utils/                      # 工具函数
│   ├── stock_data.py           # 股票数据处理
│   ├── monte_carlo.py          # 蒙特卡洛模拟
│   ├── risk_monitor.py         # 风险监测
│   ├── chat_ai.py              # AI聊天功能
│   └── number_utils.py         # 数字处理工具
├── flask_env/                  # Python虚拟环境
├── requirements.txt            # 项目依赖
├── .gitignore                  # Git忽略文件
└── README.md                   # 项目说明文档
```

## 核心模块功能说明

### 1. 数据模型 (models/)
- **user.py**: 用户信息模型，包含用户ID、用户名、密码、邮箱等基本信息
- **admin.py**: 管理员模型，管理系统权限和功能
- **trade.py**: 交易相关模型，包括订单(Order)和交易记录(Transaction)
- **finance.py**: 财务相关模型，包括账户余额(AccountBalance)和资金交易(FundTransaction)
- **market.py**: 市场数据模型，包括股票价格数据(MarketData)和基本面数据(FundamentalData)

### 2. 路由模块 (routes/)
- **auth/**: 处理用户登录注册和授权
- **user/account.py**: 处理用户账户信息、余额查询、充值提现等
- **user/order.py**: 处理订单创建、取消、查询等功能，支持市价单和限价单
- **user/stock.py**: 处理股票数据展示、图表生成等功能
- **user/monte_carlo.py**: 处理蒙特卡洛模拟和预测
- **user/ai_assistant.py**: 处理AI助手的交互和回复
- **admin/**: 处理管理员的各项功能

### 3. 任务处理 (tasks/)
- **order_processor.py**: 限价单自动处理系统，在后台线程中运行，定期检查市场价格并执行符合条件的限价单

### 4. 前端模块 (static/js/)
- **user/account.js**: 处理账户页面的交互，充值提现操作
- **user/stock_chart.js**: 处理股票图表展示和交互，包括订单创建表单
- **user/stock_chart_extra.js**: 提供图表附加功能，如技术指标计算
- **user/stock_analysis.js**: 处理股票分析页面的交互和图表
- **user/ai_assistant.js**: 处理AI助手界面的交互和消息发送

## 系统功能详解

### 1. 用户账户系统
- 用户注册与登录
- 个人资料管理
- 账户余额查看
- 充值和提现功能（需要管理员审核）
- 交易记录和资金记录查询

### 2. 股票交易系统
- **股票查询**: 搜索并查看股票基本信息和实时价格
- **交易功能**: 
  - 市价单: 以当前市场价格立即执行的订单
  - 限价单: 设定价格条件的订单，当市场价格达到条件时自动执行
- **订单管理**: 查看、取消订单
- **持仓管理**: 查看当前持仓股票、平均成本、盈亏情况

### 3. 数据分析系统
- **历史数据**: 展示股票历史价格走势
- **技术指标**: 计算并展示MA、RSI、MACD等常用技术指标
- **蒙特卡洛模拟**: 基于历史数据进行随机模拟预测
- **风险评估**: 计算并展示股票的波动率、风险指标等

### 4. AI助手
- 基于自然语言处理的股票咨询助手
- 支持股票信息查询、市场情况分析、基本投资建议
- 实时响应用户问题并提供相关信息

## API文档

### 用户API
- `POST /user/api/chat`: AI助手聊天接口
- `POST /user/api/deposit`: 资金充值接口
- `POST /user/api/withdraw`: 资金提现接口
- `POST /user/api/create_order`: 创建订单接口
- `POST /user/orders/{order_id}/cancel`: 取消订单接口

### 股票数据API
- `GET /user/api/market_data`: 获取股票市场数据
- `GET /user/api/monte_carlo`: 执行蒙特卡洛模拟
- `GET /user/api/fundamental_data`: 获取股票基本面数据

## 注意事项

- 本系统仅用于模拟交易和学习，不涉及真实资金交易
- 股票数据来源于公开API，可能存在延迟
- AI助手基于Gemini AI，需要有效的API密钥才能正常使用
- 默认管理员账户: 用户名 `admin`，密码 `admin`
- 限价单处理系统在后台自动运行，每30秒检查一次市场价格