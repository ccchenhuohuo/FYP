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

## 注意事项

- 本系统仅用于模拟交易和学习，不涉及真实资金交易
- 股票数据来源于公开API，可能存在延迟
- AI助手基于Gemini AI，需要有效的API密钥才能正常使用
- 默认管理员账户: 用户名 `admin`，密码 `admin`
- 限价单处理系统在后台自动运行，每30秒检查一次市场价格

## 实用技巧

- 清理Python缓存文件：项目提供了清理`__pycache__`目录的脚本，可以通过以下命令运行：
  ```bash
  bash clean_pycache.sh
  ```
  或直接使用命令：
  ```bash
  find . -type d -name "__pycache__" -exec rm -r {} \;
  ```

## 详细项目结构

```
/
├── app.py                      # 应用入口点，Flask应用配置和初始化
├── config.py                   # 配置文件，包含数据库和API密钥等配置
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
│   │   ├── main.css            # 主样式表 (core/welcome.html)
│   │   ├── auth.css            # 认证页面样式 (auth/*)
│   │   ├── account.css         # 用户账户页面样式 (user/account.html)
│   │   ├── stock_chart.css     # 股票图表页面样式 (user/stock_chart.html)
│   │   ├── stock_analysis.css  # 股票分析页面样式 (user/stock_analysis.html)
│   │   ├── ai_assistant.css    # AI助手页面样式 (user/ai_assistant.html)
│   │   ├── admin_base.css      # 管理员基础样式
│   │   ├── admin_layout.css    # 管理员布局样式
│   │   ├── admin_common.css    # 管理员通用样式
│   │   ├── admin_dashboard.css # 管理员仪表盘样式
│   │   ├── admin_deposits.css  # 管理员充值管理样式
│   │   ├── admin_withdrawals.css # 管理员提现管理样式
│   │   ├── admin_fund_transactions.css # 管理员资金交易通用样式
│   │   ├── admin_orders.css    # 管理员订单管理样式
│   │   ├── about.css           # 关于页面样式
│   │   └── privacy.css         # 隐私政策页面样式
│   ├── js/                     # JavaScript文件
│   │   ├── user/               # 用户相关JS
│   │   │   ├── navigation.js   # 用户导航栏交互
│   │   │   ├── account.js      # 账户操作（充值提现）
│   │   │   ├── stock_chart.js  # 股票图表和订单创建
│   │   │   ├── stock_chart_extra.js # 图表附加功能
│   │   │   ├── stock_analysis.js # 股票分析交互
│   │   │   └── ai_assistant.js # AI助手交互
│   │   ├── admin/              # 管理员相关JS
│   │   │   ├── navigation.js   # 管理员导航栏交互
│   │   │   ├── deposits.js     # 充值管理交互
│   │   │   └── withdrawals.js  # 提现管理交互
│   │   └── auth/               # 认证相关JS
│   │       ├── login.js        # 用户登录交互
│   │       ├── register.js     # 用户注册交互
│   │       └── adminLogin.js   # 管理员登录交互
│   ├── picture.png             # 示例图片
│   ├── chenyu.png              # 团队成员图片
│   ├── zhenghaowen.png         # 团队成员图片
│   ├── xumingyang.png          # 团队成员图片
│   ├── liaoqiyue.png           # 团队成员图片
│   ├── chenguanqi.png          # 团队成员图片
│   └── frankie.png             # 团队成员图片
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
├── test/                       # 测试目录
├── flask_env/                  # Python虚拟环境
├── requirements.txt            # 项目依赖
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

## 本地数据库结构

系统使用MySQL作为本地数据库，通过SQLAlchemy进行ORM映射。数据库名称为`stock_data_v1`，包含以下主要表结构：

### 用户相关表

#### 用户表 (user)
- `user_id`: 整型，主键，用户唯一标识
- `user_name`: 字符串，唯一，用户名
- `user_email`: 字符串，唯一，用户邮箱
- `user_password`: 字符串，用户密码（加密存储）

#### 管理员表 (admin)
- `admin_id`: 整型，主键，管理员唯一标识
- `admin_name`: 字符串，唯一，管理员用户名
- `admin_password`: 字符串，管理员密码（加密存储）

### 财务相关表

#### 账户余额表 (account_balance)
- `balance_id`: 整型，主键，余额记录唯一标识
- `user_id`: 整型，外键，关联用户表
- `available_balance`: 浮点型，可用余额
- `frozen_balance`: 浮点型，冻结余额（用于待执行订单）
- `total_balance`: 浮点型，总余额 = 可用余额 + 冻结余额
- `updated_at`: 日期时间，更新时间

#### 资金交易表 (fund_transaction)
- `transaction_id`: 整型，主键，交易唯一标识
- `user_id`: 整型，外键，关联用户表
- `transaction_type`: 字符串，交易类型（充值、提现）
- `amount`: 浮点型，交易金额
- `status`: 字符串，交易状态（待处理、已完成、已拒绝）
- `created_at`: 日期时间，创建时间
- `updated_at`: 日期时间，更新时间
- `remark`: 字符串，备注信息
- `operator_id`: 整型，操作员ID（管理员）
- `original_id`: 整型，原始交易ID（数据迁移参考）

### 交易相关表

#### 订单表 (orders)
- `order_id`: 整型，主键，订单唯一标识
- `user_id`: 整型，外键，关联用户表
- `ticker`: 字符串，股票代码
- `order_type`: 字符串，订单类型（买入、卖出）
- `order_execution_type`: 字符串，执行类型（市价单、限价单）
- `order_price`: 浮点型，订单价格（限价单）
- `order_quantity`: 整型，订单数量
- `order_status`: 字符串，订单状态（待执行、已执行、已取消、已拒绝）
- `created_at`: 日期时间，创建时间
- `updated_at`: 日期时间，更新时间
- `executed_at`: 日期时间，执行时间
- `remark`: 文本，备注信息

#### 交易记录表 (transaction)
- `transaction_id`: 整型，主键，交易记录唯一标识
- `order_id`: 整型，外键，关联订单表
- `user_id`: 整型外键，关联用户表
- `ticker`: 字符串，股票代码
- `transaction_type`: 字符串，交易类型（买入、卖出）
- `transaction_price`: 浮点型，交易价格
- `transaction_quantity`: 整型，交易数量
- `transaction_amount`: 浮点型，交易金额（价格×数量）
- `transaction_time`: 日期时间，交易时间
- `transaction_status`: 字符串，交易状态（已完成、失败、已撤销）

#### 持仓表 (portfolio)
- `id`: 整型，主键，持仓记录唯一标识
- `user_id`: 整型，外键，关联用户表
- `ticker`: 字符串，股票代码
- `quantity`: 整型，持有数量
- `average_price`: 浮点型，平均购入价格
- `total_cost`: 浮点型，总成本
- `last_updated`: 日期时间，最后更新时间

### 市场数据相关表

#### 股票行情数据表 (market_data)
- `ticker`: 字符串，股票代码（联合主键）
- `date`: 日期时间，数据日期（联合主键）
- `open`: 浮点型，开盘价
- `high`: 浮点型，最高价
- `low`: 浮点型，最低价
- `close`: 浮点型，收盘价
- `volume`: 长整型，交易量
- `data_collected_at`: 日期时间，数据采集时间

#### 基本面数据表 (fundamental_data)
- `ticker`: 字符串，股票代码（联合主键）
- `date`: 日期时间，数据日期（联合主键）
- `market_cap`: 长整型，市值
- `pe_ratio`: 浮点型，市盈率
- `pb_ratio`: 浮点型，市净率
- `dividend_yield`: 浮点型，股息率
- `revenue`: 长整型，营收
- `net_income`: 长整型，净利润
- `operating_cash_flow`: 长整型，经营现金流
- `data_collected_at`: 日期时间，数据采集时间

#### 资产负债表数据表 (balance_sheet)
- `ticker`: 字符串，股票代码（联合主键）
- `date`: 日期时间，数据日期（联合主键）
- `current_assets`: 字符串，流动资产
- `non_current_assets`: 浮点型，非流动资产
- `current_liabilities`: 字符串，流动负债
- `non_current_liabilities`: 字符串，非流动负债
- `data_collected_at`: 日期时间，数据采集时间

#### 利润表数据表 (income_statement)
- `ticker`: 字符串，股票代码（联合主键）
- `date`: 日期时间，数据日期（联合主键）
- `revenue`: 浮点型，营收
- `cost_of_revenue`: 浮点型，营收成本
- `operating_income`: 浮点型，营业利润
- `income_before_tax`: 字符串，税前利润
- `net_income`: 浮点型，净利润
- `data_collected_at`: 日期时间，数据采集时间

## 数据库关系图

```
用户相关
└── user (用户表)
    ├── 1:1 account_balance (账户余额表)
    ├── 1:N fund_transaction (资金交易表)
    ├── 1:N orders (订单表)
    ├── 1:N transaction (交易记录表)
    └── 1:N portfolio (持仓表)

管理员相关
└── admin (管理员表)
    └── 1:N fund_transaction (资金交易表，作为operator_id)

交易相关
├── orders (订单表)
│   └── 1:1 transaction (交易记录表)
└── portfolio (持仓表)
    └── N:1 user (用户表)

市场数据相关
├── market_data (股票行情数据表)
│   └── (ticker, date) 联合主键
├── fundamental_data (基本面数据表)
│   └── (ticker, date) 联合主键
├── balance_sheet (资产负债表数据表)
│   └── (ticker, date) 联合主键
└── income_statement (利润表数据表)
    └── (ticker, date) 联合主键

关系说明：
- 1:1 表示一对一关系
- 1:N 表示一对多关系
- N:1 表示多对一关系
- 联合主键表示多个字段共同作为主键
```

## 数据库初始化过程

系统启动时会自动执行以下数据库初始化操作：

1. 创建所有必要的数据库表（如不存在）
2. 创建默认管理员账户（admin/admin）
3. 确保每个用户都有对应的账户余额记录

可在`models/__init__.py`中的`init_db`函数查看详细初始化流程。