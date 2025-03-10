# 股票交易与分析系统

这是一个综合性的股票交易与分析系统，提供股票数据采集、历史走势分析、风险评估、基本面数据展示以及模拟交易功能。系统使用Flask框架构建Web界面，通过Yahoo Finance API获取股票数据，并将数据存储在MySQL数据库中进行管理和分析。

## 功能特性

### 1. 用户管理系统
- 用户注册和登录
- 管理员登录和管理
- 用户权限控制

### 2. 股票历史走势分析
- 交互式股票价格图表
- 多种时间范围选择（1个月、3个月、6个月、1年、全部）
- 自定义日期范围分析
- 实时股票行情展示（价格、交易量、最高价、最低价）

### 3. 蒙特卡洛模拟预测
- 基于历史数据的股票价格模拟
- 可配置模拟天数和模拟次数
- 可视化模拟结果
- 多种视图模式切换

### 4. 公司基本面数据分析
- 基本财务指标（市值、市盈率、市净率、股息收益率等）
- 资产负债表数据（流动资产、非流动资产、总资产、负债等）
- 利润表数据（营业收入、营业成本、毛利润、净利润等）
- 数据可视化展示

### 5. 股票风险分析
- 多股票风险评估
- 估值指标和风险指标分析
- 风险评级和警报系统
- 可视化风险仪表盘

### 6. AI智能助手
- 基于Gemini API的智能问答
- 股票相关问题解答
- 投资建议和市场分析

## 技术栈

### 前端
- HTML5 / CSS3 / JavaScript
- Bootstrap 5 框架
- Chart.js 图表库
- Font Awesome 图标库

### 后端
- Python 3.8+
- Flask Web框架
- Flask-Login 用户认证
- Flask-SQLAlchemy ORM

### 数据库
- MySQL 8.0+

### 数据分析
- Pandas 数据处理
- NumPy 数学计算
- yfinance 股票数据API

### AI集成
- Google Gemini API

## 安装指南

### 1. 系统要求
- Python 3.8+
- MySQL 8.0+
- pip包管理器

### 2. 克隆项目
```bash
git clone https://github.com/yourusername/stock-trading-analysis-system.git
cd stock-trading-analysis-system
```

### 3. 虚拟环境设置
```bash
# 创建虚拟环境
python -m venv flask_env

# 激活虚拟环境
source flask_env/bin/activate  # Linux/macOS
# 或
.\flask_env\Scripts\activate  # Windows
```

### 4. 安装依赖
```bash
# 确保在虚拟环境中
pip install -r requirements.txt
```

### 5. 数据库配置
```sql
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE stock_data_v1;
```

更新数据库配置（在app.py中）：
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/stock_data_v1'
```

### 6. 初始化数据库
```bash
# 确保在虚拟环境中
python app.py init-db
```

### 7. 采集股票数据
```bash
# 确保在虚拟环境中
python obtain_stock_data.py
```

## 使用指南

### 1. 启动系统
```bash
# 确保在虚拟环境中
python app.py
```

访问 http://localhost:5001 查看Web界面

### 2. 用户注册/登录
- 访问登录页面
- 新用户可以注册账号
- 使用注册的账号登录系统

### 3. 股票历史走势分析
- 在导航菜单中选择"股票历史走势"
- 选择股票代码和时间范围
- 查看股票价格图表和实时行情
- 可以运行蒙特卡洛模拟进行预测分析

### 4. 股票风险分析
- 在导航菜单中选择"估值和风控预警"
- 输入股票代码和日期范围
- 点击"分析风险"按钮
- 查看风险评级和详细指标

### 5. 使用AI智能助手
- 在导航菜单中选择"AI智能助手"
- 输入股票相关问题
- 获取AI生成的回答和建议

## 项目结构

```
.
├── app.py                    # Flask应用主文件
├── models.py                 # 数据库模型定义
├── obtain_stock_data.py      # 股票数据采集脚本
├── risk_monitor.py           # 风险监控和分析模块
├── monte_carlo_simulation.py # 蒙特卡洛模拟模块
├── chat_with_gemini.py       # Gemini API集成模块
├── requirements.txt          # 项目依赖文件
├── README.md                 # 项目说明文档
├── static/                   # 静态资源目录
│   ├── css/                  # CSS样式文件
│   │   ├── main.css          # 主样式文件
│   │   ├── stock_chart.css   # 股票图表样式
│   │   ├── account.css       # 账户页面样式
│   │   └── ...               # 其他样式文件
│   └── js/                   # JavaScript文件
│       ├── auth/             # 认证相关JS
│       │   ├── login.js      # 登录逻辑
│   │   └── register.js   # 注册逻辑
│   └── user/             # 用户页面JS
│       ├── stock_chart.js # 股票图表逻辑
│       ├── stock_analysis.js # 风险分析逻辑
│       └── ...           # 其他JS文件
├── templates/                # HTML模板目录
│   ├── auth/                 # 认证相关模板
│   │   ├── login.html        # 用户登录页面
│   │   └── register.html     # 用户注册页面
│   ├── user/                 # 用户页面模板
│   │   ├── layout.html       # 用户页面布局
│   │   ├── stock_chart.html  # 股票图表页面
│   │   ├── stock_analysis.html # 风险分析页面
│   │   └── ...               # 其他用户页面
│   └── admin/                # 管理员页面模板
└── routes/                   # 路由模块目录
    ├── __init__.py           # 路由初始化
    ├── auth_routes.py        # 认证相关路由
    ├── user_routes.py        # 用户相关路由
    └── admin_routes.py       # 管理员相关路由
```

## 主要功能模块详解

### 1. 股票历史走势分析

股票历史走势分析模块提供了交互式的股票价格图表，支持多种时间范围的数据查看。用户可以选择不同的股票和时间范围，系统会实时获取并展示相关数据。

**主要特点：**
- 实时行情展示（价格、交易量、最高价、最低价）
- 交互式价格走势图表
- 多种时间范围选择
- 自定义日期范围分析

### 2. 蒙特卡洛模拟预测

蒙特卡洛模拟模块使用随机过程模拟股票未来价格走势，帮助用户了解股票的潜在风险和收益。

**主要特点：**
- 可配置模拟天数（1-365天）
- 可配置模拟次数（100-10000次）
- 可视化模拟结果
- 提供统计分析（预期收益、风险值、置信区间等）

### 3. 股票风险分析

股票风险分析模块提供全面的风险评估和估值分析，帮助用户识别潜在的投资风险。

**主要特点：**
- 多股票同时分析
- 估值指标分析（市盈率、市净率等）
- 风险指标分析（波动率、贝塔系数等）
- 风险评级和警报系统
- 可视化风险仪表盘

### 4. 公司基本面数据

公司基本面数据模块提供详细的财务数据和指标，帮助用户了解公司的财务状况和业务表现。

**主要特点：**
- 基本财务指标
- 资产负债表数据
- 利润表数据
- 数据可视化展示

## 贡献指南

欢迎对本项目进行贡献！如果您想贡献代码，请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个Pull Request