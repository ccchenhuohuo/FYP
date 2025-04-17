# 股票交易与分析系统

这是一个基于 Flask 的 Web 应用程序，旨在提供一个模拟股票交易和数据分析的平台。它集成了用户管理、股票数据展示、模拟交易（市价单与限价单）、后台订单处理、蒙特卡洛模拟以及基于 Google Gemini 的 AI 投资助手等功能。

## 1. 项目基本信息

### 1.1 项目概况

本系统模拟了真实的股票交易环境，允许用户注册账户、管理资金（模拟）、查看实时和历史股票数据、执行买卖订单，并利用数据分析工具和 AI 助手进行投资决策辅助。系统包含用户端和管理端，管理员负责审核用户资金操作和管理系统。

### 1.2 技术架构与栈

*   **后端框架**: Flask 2.2.3
*   **数据库 ORM**: Flask-SQLAlchemy 3.0.3, SQLAlchemy 2.0.7
*   **数据库**: MySQL (使用 PyMySQL 1.0.3 或 mysql-connector-python 8.0.33 连接)
*   **数据库迁移**: Flask-Migrate 4.0.4
*   **用户认证**: Flask-Login 0.6.2
*   **Web 服务器**: Werkzeug 2.2.3 (开发环境)
*   **前端**: HTML, CSS, JavaScript, Bootstrap, Chart.js
*   **数据获取**: yfinance 0.2.20 (股票数据), Alpha Vantage API (实时数据)
*   **数据处理**: Pandas 2.0.1, NumPy 1.24.3
*   **AI 助手**: Google Generative AI (Gemini API)
*   **后台任务**: Standard Python `threading` (用于订单处理器)
*   **依赖管理**: pip, `requirements.txt`
*   **版本控制**: Git

## 2. 快速上手指南

### 2.1 环境准备

*   **Python**: 3.8 或更高版本
*   **MySQL**: 5.7 或更高版本
*   **Git**: 用于克隆项目仓库
*   **pip**: Python 包管理器 (通常随 Python 一起安装)
*   **操作系统**: Linux, macOS 或 Windows

### 2.2 配置说明

1.  **克隆仓库**:
```bash
git clone <仓库URL>
cd <项目目录>
```

2.  **创建并激活虚拟环境**:
```bash
# 创建虚拟环境
python -m venv flask_env

    # 激活虚拟环境 (Linux/macOS)
    source flask_env/bin/activate
    # 或者 (Windows)
    .\flask_env\Scripts\activate
    ```

3.  **安装依赖**:
```bash
pip install -r requirements.txt
```

4.  **配置数据库**:
    *   确保您的 MySQL 服务正在运行。
    *   创建一个新的数据库 (例如 `stock_data_v1`):
```sql
        CREATE DATABASE stock_data_v1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        ```
    *   打开 `config.py` 文件。
    *   修改 `SQLALCHEMY_DATABASE_URI` 为您的 MySQL 连接字符串，格式如下:
        ```python
        # 示例: mysql+pymysql://<用户名>:<密码>@<主机名>:<端口号>/<数据库名>
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:your_password@localhost:3306/stock_data_v1'
        ```
        *注意: 如果使用 `mysql-connector-python`，则前缀为 `mysql+mysqlconnector://`*
    *   (可选) 同时更新 `DB_CONFIG` 字典（如果项目的某些部分直接使用它）。

5.  **配置 API 密钥**:
    *   **Google Gemini API**:
        *   访问 [Google AI Studio](https://ai.google.dev/) 获取 API 密钥。
        *   在 `config.py` 中设置 `GEMINI_API_KEY` 的值，或者设置同名环境变量 `GEMINI_API_KEY`。
    *   **Alpha Vantage API**:
        *   访问 [Alpha Vantage](https://www.alphavantage.co/support/#api-key) 获取免费 API 密钥。
        *   在 `config.py` 中设置 `ALPHA_VANTAGE_API_KEY` 的值，或者设置同名环境变量 `ALPHA_VANTAGE_API_KEY`。

6.  **数据库初始化与迁移**:
    *   首次运行时，需要初始化数据库表结构。Flask-Migrate 用于管理数据库模式变更。
    *   确保 Flask 应用可以找到 (通常通过设置 `FLASK_APP=app.py` 环境变量)。
    *   运行以下命令生成和应用数据库迁移：
```bash
      # 设置 Flask 应用入口 (如果尚未设置)
      export FLASK_APP=app.py # Linux/macOS
      # set FLASK_APP=app.py # Windows

      # 初始化迁移环境 (仅需首次运行)
      flask db init

      # 生成初始迁移脚本
      flask db migrate -m "Initial migration."

      # 应用迁移到数据库
      flask db upgrade
      ```
      *注意: `init_db(app)` 函数在 `app.py` 中被调用，它会创建表并可能包含一些初始数据（如默认管理员）。`flask db upgrade` 会执行这些创建操作。*

### 2.3 启动与调试

*   **启动开发服务器**:
```bash
flask run --debug
```
    *   `--debug` 标志会启用调试模式，提供详细错误信息并在代码更改时自动重载。
    *   应用默认运行在 `http://127.0.0.1:5003` (端口号在 `config.py` 中定义)。

*   **访问应用**:
    *   打开浏览器访问 `http://127.0.0.1:5003/`。
    *   默认管理员账户: 用户名 `admin`，密码 `admin123secure` (或 `config.py` / 环境变量中设置的值)。
    *   普通用户需要先注册。

*   **后台任务**:
    *   限价单处理器 (`tasks/order_processor.py`) 会在应用启动时自动在后台线程中运行。
    *   应用关闭时 (`atexit`) 会尝试停止该处理器。

## 3. 核心功能与模块设计

### 3.1 主要功能

*   **用户认证**: 普通用户注册、登录、登出；管理员登录。
*   **账户管理**: 查看账户余额 (可用、冻结、总额)，模拟充值、提现 (需管理员审核)。
*   **股票行情**: 查看股票列表，搜索股票，展示实时/近实时价格 (Alpha Vantage 或数据库缓存)，历史 K 线图 (yfinance)。
*   **模拟交易**: 创建市价单、限价单 (买入/卖出)，查看订单历史，取消待处理订单。
*   **持仓管理**: 查看当前持有的股票、数量、平均成本、总成本、当前市值和盈亏。
*   **数据分析**:
    *   基于历史数据的技术指标计算与展示 (集成在图表库或后端计算)。
    *   蒙特卡洛模拟预测股价未来走势。
    *   风险评估 (基于 `utils/stock_data.py` 可能的实现)。
*   **AI 助手**: 与 Gemini AI 模型进行交互，获取市场分析、股票信息或投资建议。
*   **管理员功能**: 用户管理，资金审核 (充值/提现)，订单管理 (查看、手动执行/拒绝)，数据管理。
*   **后台订单处理**: 自动检查市场价格，执行满足条件的限价单。

### 3.2 模块逻辑与技术实现

*   **应用入口 (`app.py`)**:
    *   使用 `create_app()` 工厂模式创建和配置 Flask 应用实例。
    *   加载 `config.py` 中的配置。
    *   初始化 SQLAlchemy (`models.init_db`) 和 Flask-Migrate。
    *   初始化 Flask-Login (`auth.init_login_manager`)。
    *   注册蓝图 (`routes.register_routes`)，将不同功能的路由模块化。
    *   启动后台订单处理器 (`tasks.order_processor.start_order_processor`) 并通过 `atexit` 注册清理函数。
    *   定义全局错误处理器 (如处理 Jinja2 未定义错误)。
    *   注册自定义 Jinja2 模板过滤器 (`safe_round`, `format_datetime`)。
    *   定义根路由 `/`，根据登录状态和角色重定向到相应仪表盘或登录页。

*   **配置 (`config.py`)**:
    *   存储应用密钥、数据库 URI、API 密钥、默认管理员凭证、股票代码列表、订单处理间隔等常量和配置。
    *   使用环境变量覆盖部分敏感配置是推荐的最佳实践。

*   **数据模型 (`models/`)**:
    *   定义数据库表的 SQLAlchemy 模型 (User, Admin, Order, Transaction, AccountBalance, FundTransaction, Portfolio, MarketData 等)。
    *   `__init__.py` 中的 `init_db` 函数负责数据库初始化逻辑，包括创建表和可能的初始数据填充。

*   **路由 (`routes/`)**:
    *   按功能划分蓝图 (Auth, User, Admin, Core)。
    *   每个蓝图下的 Python 文件定义具体的视图函数和对应的 URL 规则。
    *   处理 HTTP 请求，调用服务/工具函数，与模型交互，渲染 HTML 模板或返回 JSON API 响应。
    *   用户路由 (`user/`) 包含账户、订单、股票数据、分析、AI 助手等接口。
    *   管理员路由 (`admin/`) 包含管理功能接口。
    *   认证路由 (`auth/`) 处理登录、注册、登出。

*   **后台任务 (`tasks/order_processor.py`)**:
    *   使用 Python `threading` 模块实现。
    *   定期 (由 `config.ORDER_CHECK_INTERVAL` 控制) 查询待处理的限价单。
    *   获取相关股票的当前市场价格。
    *   匹配并执行符合价格条件的订单，更新订单状态和用户余额/持仓。
    *   包含启动和停止处理器的逻辑。

*   **工具函数 (`utils/`)**:
    *   封装可重用的逻辑，如:
        *   `stock_data.py`: 获取和处理股票数据 (yfinance, Alpha Vantage)。
        *   `monte_carlo.py`: 执行蒙特卡洛模拟计算。
        *   `chat_ai.py`: 与 Gemini API 交互。
        *   `number_utils.py`: 安全的数字格式化。

*   **前端 (`static/`, `templates/`)**:
    *   `templates/`: 使用 Jinja2 模板引擎渲染动态 HTML 页面。包含基础布局 (`layout.html`) 和各个功能的页面模板。
    *   `static/`: 存放 CSS 样式表、JavaScript 文件和图片等静态资源。
        *   CSS 按页面或模块组织。
        *   JavaScript 处理前端交互逻辑，如图表绘制 (Chart.js)、表单提交 (AJAX)、用户界面更新等。

### 3.3 详细项目结构

```
/
├── .git/                       # Git 版本控制目录
├── .gitignore                  # Git 忽略配置文件
├── .cursor/                    # Cursor IDE 配置目录
├── .DS_Store                   # macOS 文件夹属性文件
├── __pycache__/                # Python 编译缓存
├── flask_env/                  # Python 虚拟环境目录
├── logs/                       # 日志文件目录
│   ├── app.log                 # 应用日志文件
│   └── error.log               # 错误日志文件
├── test/                       # 单元测试和集成测试目录
│   ├── __init__.py             # 测试包初始化
│   ├── test_auth.py            # 认证模块测试
│   ├── test_models.py          # 数据模型测试
│   ├── test_routes.py          # 路由模块测试
│   └── test_utils.py           # 工具函数测试
├── app.py                      # 应用入口点
├── config.py                   # 配置文件
├── requirements.txt            # 项目依赖列表
├── README.md                   # 项目说明文档
├── auth/                       # 认证核心逻辑
│   ├── __init__.py             # 初始化文件
│   └── login_manager.py        # Flask-Login 配置
├── models/                     # 数据库模型
│   ├── __init__.py             # 模型初始化
│   ├── user.py                 # 用户模型
│   ├── admin.py                # 管理员模型
│   ├── trade.py                # 交易模型
│   ├── finance.py              # 财务模型
│   └── market.py               # 市场数据模型
├── routes/                     # 路由模块
│   ├── __init__.py             # 路由注册
│   ├── core/                   # 核心路由
│   │   ├── __init__.py         # 核心蓝图初始化
│   │   ├── home.py             # 首页路由
│   │   ├── about.py            # 关于页面路由
│   │   └── privacy.py          # 隐私政策路由
│   ├── auth/                   # 认证路由
│   │   ├── __init__.py         # 认证蓝图初始化
│   │   ├── login.py            # 登录路由
│   │   ├── register.py         # 注册路由
│   │   └── admin_login.py      # 管理员登录路由
│   ├── user/                   # 用户功能路由
│   │   ├── __init__.py         # 用户蓝图初始化
│   │   ├── dashboard.py        # 用户仪表盘
│   │   ├── account.py          # 账户管理
│   │   ├── order.py            # 订单管理
│   │   ├── stock.py            # 股票数据
│   │   ├── monte_carlo.py      # 蒙特卡洛模拟
│   │   └── ai_assistant.py     # AI助手
│   └── admin/                  # 管理员功能路由
│       ├── __init__.py         # 管理员蓝图初始化
│       ├── dashboard.py        # 管理员仪表盘
│       ├── user_manage.py      # 用户管理
│       ├── fund_manage.py      # 资金管理
│       ├── order_manage.py     # 订单管理
│       └── data_manage.py      # 数据管理
├── static/                     # 静态资源
│   ├── css/                    # CSS 样式表
│   │   ├── main.css            # 主样式
│   │   ├── auth/               # 认证样式
│   │   │   ├── auth.css        # 认证页面样式
│   │   │   ├── login.css       # 登录页面样式
│   │   │   └── register.css    # 注册页面样式
│   │   ├── user/               # 用户页面样式
│   │   │   ├── dashboard.css   # 仪表盘样式
│   │   │   ├── account.css     # 账户页面样式
│   │   │   ├── stock_chart.css # 图表页面样式
│   │   │   ├── stock_analysis.css # 分析页面样式
│   │   │   └── ai_assistant.css # AI助手样式
│   │   └── admin/              # 管理员样式
│   │       ├── dashboard.css   # 仪表盘样式
│   │       ├── common.css      # 通用样式
│   │       ├── layout.css      # 布局样式
│   │       ├── fund_manage.css # 资金管理样式
│   │       └── user_manage.css # 用户管理样式
│   ├── js/                     # JavaScript 文件
│   │   ├── main.js             # 主脚本
│   │   ├── chart_utils.js      # 图表工具
│   │   ├── auth/               # 认证脚本
│   │   │   ├── login.js        # 登录脚本
│   │   │   ├── register.js     # 注册脚本
│   │   │   └── admin_login.js  # 管理员登录脚本
│   │   ├── user/               # 用户脚本
│   │   │   ├── navigation.js   # 导航栏脚本
│   │   │   ├── account.js      # 账户操作脚本
│   │   │   ├── stock_chart.js  # 股票图表脚本
│   │   │   ├── stock_chart_extra.js # 图表附加功能
│   │   │   ├── stock_analysis.js # 股票分析脚本
│   │   │   └── ai_assistant.js # AI助手交互脚本
│   │   └── admin/              # 管理员脚本
│   │       ├── navigation.js   # 导航栏脚本
│   │       ├── dashboard.js    # 仪表盘脚本
│   │       ├── deposits.js     # 充值管理脚本
│   │       └── withdrawals.js  # 提现管理脚本
│   └── images/                 # 图片资源
│       ├── logo.png            # 网站logo
│       ├── favicon.ico         # 网站图标
│       ├── background.jpg      # 背景图
│       ├── user-avatar.png     # 默认用户头像
│       ├── stock-chart.svg     # 股票图表图标
│       └── team/               # 团队成员图片
│           ├── chenyu.png      # 团队成员照片
│           ├── zhenghaowen.png # 团队成员照片
│           ├── xumingyang.png  # 团队成员照片
│           ├── liaoqiyue.png   # 团队成员照片
│           ├── chenguanqi.png  # 团队成员照片
│           └── frankie.png     # 团队成员照片
├── templates/                  # HTML 模板
│   ├── layout/                 # 布局模板
│   │   ├── base.html           # 基础布局
│   │   ├── user_layout.html    # 用户布局
│   │   └── admin_layout.html   # 管理员布局
│   ├── core/                   # 核心页面
│   │   ├── index.html          # 首页
│   │   ├── about.html          # 关于页面
│   │   └── privacy.html        # 隐私政策页面
│   ├── auth/                   # 认证页面
│   │   ├── login.html          # 登录页面
│   │   ├── register.html       # 注册页面
│   │   └── admin_login.html    # 管理员登录页面
│   ├── user/                   # 用户页面
│   │   ├── dashboard.html      # 用户仪表盘
│   │   ├── account.html        # 账户页面
│   │   ├── stock_chart.html    # 股票图表页面
│   │   ├── stock_analysis.html # 股票分析页面
│   │   └── ai_assistant.html   # AI助手页面
│   ├── admin/                  # 管理员页面
│   │   ├── dashboard.html      # 仪表盘页面
│   │   ├── user_manage.html    # 用户管理页面
│   │   ├── fund_transactions.html # 资金交易页面
│   │   └── orders.html         # 订单管理页面
│   ├── partials/               # 页面片段
│   │   ├── _nav.html           # 导航条
│   │   ├── _footer.html        # 页脚
│   │   ├── _pagination.html    # 分页控件
│   │   └── _flash_messages.html # 消息提示
│   └── error.html              # 错误页面
├── tasks/                      # 后台任务
│   ├── __init__.py             # 任务初始化
│   └── order_processor.py      # 订单处理器
└── utils/                      # 工具函数
    ├── __init__.py             # 初始化文件
    ├── stock_data.py           # 股票数据工具
    ├── monte_carlo.py          # 蒙特卡洛模拟
    ├── risk_monitor.py         # 风险监测
    ├── chat_ai.py              # AI聊天功能
    └── number_utils.py         # 数字处理工具
```

## 4. 接口与数据设计

### 4.1 接口文档 (API Endpoints)

*(此部分基于现有 README 的 API 文档，已根据代码文件进行核对和微调)*

#### 核心 (Core)

*   **GET /**: 根路径，根据登录状态重定向。
*   **GET /about**: 关于页面。
*   **GET /privacy**: 隐私政策页面。
*   **GET /logout**: 登出操作 (重定向到 `auth.logout`)。

#### 认证 (Auth Blueprint: `/auth`)

*   **GET /**: 认证蓝图根路径 (通常重定向)。
*   **GET, POST /login**: 用户登录。
*   **GET, POST /register**: 用户注册。
*   **GET, POST /admin-login**: 管理员登录。
*   **GET /logout**: 用户/管理员登出。

#### 用户 (User Blueprint: `/user`)

*   **GET /dashboard**: 用户仪表盘 (通常重定向到 `/user/stock_chart`)。
*   **GET /account**: 用户账户页面。
*   **POST /api/deposit**: 用户充值 API。
*   **POST /api/withdraw**: 用户提现 API。
*   **GET /api/orders**: 获取用户订单列表 API (支持分页和过滤)。
*   **POST /api/create_order**: 创建交易订单 API (市价/限价)。
*   **POST /orders/<order_id>/cancel**: 取消订单 API。
*   **GET /stock_chart**: 股票图表与交易页面。
*   **GET /stock_analysis**: 股票分析页面。
*   **POST /api/stock_analysis**: 股票风险分析 API。
*   **GET /api/market_data**: 获取股票历史行情数据 API。
*   **GET /api/fundamental_data**: 获取股票基本面数据 API。
*   **GET /api/balance_sheet**: 获取资产负债表 API。
*   **GET /api/income_statement**: 获取利润表 API。
*   **GET /api/real_time_stock_data**: 获取实时/近实时报价 API。
*   **GET /api/monte-carlo/<ticker>**: 获取蒙特卡洛模拟结果 API。
*   **GET /ai_assistant**: AI 智能助手页面。
*   **POST /api/chat**: 与 AI 助手对话 API。

#### 管理员 (Admin Blueprint: `/admin`)

*   **GET /, /dashboard**: 管理员仪表盘。
*   **GET /fund-transactions**: 查看资金交易列表 (充值/提现)。
*   **GET /deposits**: 查看充值列表 (是 `/fund-transactions` 的过滤视图)。
*   **GET /withdrawals**: 查看提现列表 (是 `/fund-transactions` 的过滤视图)。
*   **POST /fund-transactions/<transaction_id>/approve**: 批准资金交易 API。
*   **POST /fund-transactions/<transaction_id>/reject**: 拒绝资金交易 API。
*   **GET /orders**: 查看所有用户订单列表。
*   **POST /orders/<int:order_id>/execute**: (可能存在) 手动执行订单 API。
*   **POST /orders/<int:order_id>/reject**: (可能存在) 手动拒绝订单 API。
*   **GET /user_management**: 用户管理页面。

*(注意: API 的具体请求体、响应格式和查询参数请参考现有 README 或直接查看 `routes/` 下的源码)*

### 4.2 数据库设计

系统使用 MySQL 数据库（名称 `stock_data_v1`），通过 SQLAlchemy ORM 进行交互。详细数据表结构如下:

#### 用户相关表

##### 用户表 (user)
- `user_id`: 整型, 主键, 自增
- `user_name`: 字符串(64), 唯一, 非空
- `user_email`: 字符串(120), 唯一, 非空
- `user_password`: 字符串(128), 非空 (存储哈希值)
- `created_at`: 日期时间, 默认当前时间

##### 管理员表 (admin)
- `admin_id`: 整型, 主键, 自增
- `admin_name`: 字符串(64), 唯一, 非空
- `admin_password`: 字符串(128), 非空 (存储哈希值)

#### 财务相关表

##### 账户余额表 (account_balance)
- `balance_id`: 整型, 主键, 自增
- `user_id`: 整型, 外键(user.user_id), 唯一, 非空
- `available_balance`: 浮点型(精度待定, 如 DECIMAL(15, 2)), 非空, 默认 0.00
- `frozen_balance`: 浮点型(精度待定), 非空, 默认 0.00
- `total_balance`: 浮点型(精度待定), 非空, 默认 0.00 (通常由可用+冻结计算得出)
- `updated_at`: 日期时间, 默认当前时间, 更新时刷新

##### 资金交易表 (fund_transaction)
- `transaction_id`: 整型, 主键, 自增
- `user_id`: 整型, 外键(user.user_id), 非空
- `transaction_type`: 字符串(10), 非空 ('deposit', 'withdrawal')
- `amount`: 浮点型(精度待定), 非空
- `status`: 字符串(10), 非空 ('pending', 'approved', 'rejected'), 默认 'pending', 加索引
- `created_at`: 日期时间, 默认当前时间, 加索引
- `updated_at`: 日期时间, 默认当前时间, 更新时刷新
- `remark`: 字符串(255), 可空 (如拒绝原因)
- `operator_id`: 整型, 外键(admin.admin_id), 可空 (审核管理员)

#### 交易相关表

##### 订单表 (orders)
- `order_id`: 整型, 主键, 自增
- `user_id`: 整型, 外键(user.user_id), 非空, 加索引
- `ticker`: 字符串(10), 非空, 加索引
- `order_type`: 字符串(4), 非空 ('buy', 'sell'), 加索引
- `order_execution_type`: 字符串(6), 非空 ('market', 'limit'), 加索引
- `order_price`: 浮点型(精度待定), 可空 (市价单为空)
- `order_quantity`: 整型, 非空
- `filled_quantity`: 整型, 非空, 默认 0 (已成交数量)
- `order_status`: 字符串(10), 非空 ('pending', 'filled', 'partially_filled', 'cancelled', 'rejected'), 默认 'pending', 加索引
- `created_at`: 日期时间, 默认当前时间, 加索引
- `updated_at`: 日期时间, 默认当前时间, 更新时刷新
- `executed_at`: 日期时间, 可空 (完全成交时间)
- `remark`: 文本, 可空

##### 交易记录表 (transaction)
- `transaction_id`: 整型, 主键, 自增
- `order_id`: 整型, 外键(orders.order_id), 非空, 加索引
- `user_id`: 整型, 外键(user.user_id), 非空, 加索引
- `ticker`: 字符串(10), 非空
- `transaction_type`: 字符串(4), 非空 ('buy', 'sell')
- `transaction_price`: 浮点型(精度待定), 非空
- `transaction_quantity`: 整型, 非空
- `transaction_amount`: 浮点型(精度待定), 非空 (价格 * 数量)
- `transaction_time`: 日期时间, 非空, 默认当前时间, 加索引
- `commission`: 浮点型(精度待定), 可空 (手续费)

##### 持仓表 (portfolio)
- `id`: 整型, 主键, 自增
- `user_id`: 整型, 外键(user.user_id), 非空
- `ticker`: 字符串(10), 非空
- `quantity`: 整型, 非空
- `average_price`: 浮点型(精度待定), 非空
- `total_cost`: 浮点型(精度待定), 非空
- `last_updated`: 日期时间, 默认当前时间, 更新时刷新
- 约束: `UNIQUE(user_id, ticker)`

#### 市场数据相关表

##### 股票行情数据表 (market_data)
- `ticker`: 字符串(10), 主键部分
- `date`: 日期, 主键部分
- `open`: 浮点型(精度待定)
- `high`: 浮点型(精度待定)
- `low`: 浮点型(精度待定)
- `close`: 浮点型(精度待定)
- `adj_close`: 浮点型(精度待定) (复权收盘价)
- `volume`: 长整型
- `data_collected_at`: 日期时间, 默认当前时间
- 主键: `PRIMARY KEY (ticker, date)`

##### 基本面数据表 (fundamental_data)
- `ticker`: 字符串(10), 主键部分
- `date`: 日期, 主键部分 (通常是财报日期)
- `market_cap`: 长整型, 可空
- `pe_ratio`: 浮点型, 可空
- `pb_ratio`: 浮点型, 可空
- `dividend_yield`: 浮点型, 可空
- `revenue`: 长整型, 可空
- `net_income`: 长整型, 可空
- `eps`: 浮点型, 可空 (每股收益)
- `data_collected_at`: 日期时间, 默认当前时间
- 主键: `PRIMARY KEY (ticker, date)`

*(注意: 资产负债表和利润表结构类似，字段较多，此处省略，可参考 `models/market.py` 或原 README)*

### 4.3 数据库关系图 (文本表示)

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
    └── 1:N fund_transaction (资金交易表，作为operator_id关联)

交易相关
├── orders (订单表)
│   └── 1:N transaction (交易记录表) (一个订单可能分多次成交)
└── portfolio (持仓表)
    └── N:1 user (用户表)

市场数据相关 (通常与用户/交易数据无直接外键关联)
├── market_data (股票行情数据表)
│   └── (ticker, date) 联合主键
├── fundamental_data (基本面数据表)
│   └── (ticker, date) 联合主键
... (其他市场数据表)

关系说明：
- 1:1 表示一对一关系
- 1:N 表示一对多关系
- N:1 表示多对一关系
- (字段) 表示关联外键
```

---
**注意**: 本系统仅为模拟和学习用途，请勿用于真实交易决策。股票数据和 AI 分析结果仅供参考。