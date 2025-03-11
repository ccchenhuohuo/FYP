# 股票交易与分析系统

这是一个综合性的股票交易与分析系统，提供股票数据采集、历史走势分析、风险评估、基本面数据展示以及模拟交易功能。系统使用Flask框架构建Web界面，通过Yahoo Finance API获取股票数据，并将数据存储在MySQL数据库中进行管理和分析。

## 功能特性

### 1. 用户管理系统
- 用户注册和登录
- 管理员登录和管理
- 用户权限控制
- 个人账户管理

### 2. 股票历史走势分析
- 交互式股票价格图表
- 多种时间范围选择（1个月、3个月、6个月、1年、全部）
- 自定义日期范围分析
- 实时股票行情展示（价格、交易量、最高价、最低价）
- 技术指标分析（移动平均线、相对强弱指数等）

### 3. 蒙特卡洛模拟预测
- 基于历史数据的股票价格模拟
- 可配置模拟天数和模拟次数
- 可视化模拟结果
- 多种视图模式切换
- 预测结果统计分析

### 4. 公司基本面数据分析
- 基本财务指标（市值、市盈率、市净率、股息收益率等）
- 资产负债表数据（流动资产、非流动资产、总资产、负债等）
- 利润表数据（营业收入、营业成本、毛利润、净利润等）
- 数据可视化展示
- 财务比率分析

### 5. 股票风险分析
- 多股票风险评估
- 估值指标和风险指标分析
- 风险评级和警报系统
- 可视化风险仪表盘
- 自定义风险阈值设置

### 6. AI智能助手
- 基于Gemini API的智能问答
- 股票相关问题解答
- 投资建议和市场分析
- 实时数据查询

## 技术栈

### 前端
- HTML5 / CSS3 / JavaScript
- Bootstrap 5 框架
- Chart.js 图表库
- Font Awesome 图标库
- 响应式设计

### 后端
- Python 3.8+
- Flask Web框架 (2.2.3)
- Flask-Login 用户认证 (0.6.2)
- Flask-SQLAlchemy ORM (3.0.3)
- Werkzeug 安全工具 (2.2.3)

### 数据库
- MySQL 8.0+
- PyMySQL 数据库连接器 (1.0.3)
- mysql-connector-python (8.0.33)

### 数据分析
- Pandas 数据处理 (2.0.1)
- NumPy 数学计算 (1.24.3)
- yfinance 股票数据API (0.2.20)

### AI集成
- Google Gemini API

## 系统要求

- 操作系统：Windows 10+/macOS 10.15+/Linux
- Python 3.8+
- MySQL 8.0+
- 至少2GB RAM
- 至少1GB可用磁盘空间
- 现代网络浏览器（Chrome、Firefox、Safari、Edge等）
- 互联网连接（用于获取股票数据和AI功能）

## 安装指南

### 1. 系统准备
- 安装Python 3.8+
- 安装MySQL 8.0+
- 安装pip包管理器

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

### 5. 配置文件设置
编辑`config.py`文件，设置数据库连接信息和其他配置参数：
```python
# 数据库配置
DB_USERNAME = 'your_username'
DB_PASSWORD = 'your_password'
DB_HOST = 'localhost'
DB_NAME = 'stock_data_v1'

# AI配置（如果使用）
GEMINI_API_KEY = 'your_gemini_api_key'
```

### 6. 数据库配置
```sql
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE stock_data_v1;
```

### 7. 初始化数据库
```bash
# 确保在虚拟环境中
python app.py init-db
```

### 8. 采集股票数据
```bash
# 确保在虚拟环境中
python -c "from utils.stock_data import fetch_initial_data; fetch_initial_data()"
```

### 9. 启动应用
```bash
# 确保在虚拟环境中
python app.py
```

访问 http://localhost:5003 查看Web界面

## 使用指南

### 1. 用户注册/登录
- 访问登录页面
- 新用户可以注册账号
- 使用注册的账号登录系统

### 2. 股票历史走势分析
- 在导航菜单中选择"股票历史走势"
- 选择股票代码和时间范围
- 查看股票价格图表和实时行情
- 可以运行蒙特卡洛模拟进行预测分析

### 3. 股票风险分析
- 在导航菜单中选择"估值和风控预警"
- 输入股票代码和日期范围
- 设置风险阈值参数
- 点击"分析风险"按钮
- 查看风险评级和详细指标

### 4. 使用AI智能助手
- 在导航菜单中选择"AI智能助手"
- 输入股票相关问题
- 获取AI生成的回答和建议

## 项目结构

```
.
├── app.py                    # Flask应用主文件
├── models.py                 # 数据库模型定义
├── auth.py                   # 认证相关功能
├── config.py                 # 配置文件
├── check_db.py               # 数据库检查工具
├── requirements.txt          # 项目依赖文件
├── README.md                 # 项目说明文档
├── __init__.py               # 包初始化文件
├── utils/                    # 工具函数目录
│   ├── __init__.py           # 工具包初始化
│   ├── stock_data.py         # 股票数据获取和处理
│   ├── risk_monitor.py       # 风险监控和分析
│   ├── monte_carlo.py        # 蒙特卡洛模拟
│   └── chat_ai.py            # AI聊天功能
├── routes/                   # 路由模块目录
│   ├── __init__.py           # 路由初始化
│   ├── auth_routes.py        # 认证相关路由
│   ├── user_routes.py        # 用户相关路由
│   ├── admin_routes.py       # 管理员相关路由
│   └── monte_carlo_routes.py # 蒙特卡洛模拟路由
├── static/                   # 静态资源目录
│   ├── css/                  # CSS样式文件
│   │   ├── main.css          # 主样式文件
│   │   ├── stock_chart.css   # 股票图表样式
│   │   ├── stock_analysis.css # 风险分析样式
│   │   ├── account.css       # 账户页面样式
│   │   ├── auth.css          # 认证页面样式
│   │   ├── ai_assistant.css  # AI助手页面样式
│   │   ├── about.css         # 关于页面样式
│   │   └── privacy.css       # 隐私政策页面样式
│   ├── js/                   # JavaScript文件
│   │   ├── auth/             # 认证相关JS
│   │   │   ├── login.js      # 登录逻辑
│   │   │   └── register.js   # 注册逻辑
│   │   ├── admin/            # 管理员页面JS
│   │   └── user/             # 用户页面JS
│   │       ├── stock_chart.js # 股票图表逻辑
│   │       ├── stock_analysis.js # 风险分析逻辑
│   │       ├── ai_assistant.js # AI助手逻辑
│   │       └── navigation.js # 导航逻辑
│   └── picture.png           # 系统图片资源
└── templates/                # HTML模板目录
    ├── auth/                 # 认证相关模板
    │   ├── login.html        # 用户登录页面
    │   └── register.html     # 用户注册页面
    ├── user/                 # 用户页面模板
    │   ├── layout.html       # 用户页面布局
    │   ├── stock_chart.html  # 股票图表页面
    │   ├── stock_analysis.html # 风险分析页面
    │   ├── ai_assistant.html # AI助手页面
    │   ├── account.html      # 账户管理页面
    │   ├── about.html        # 关于页面
    │   └── privacy.html      # 隐私政策页面
    └── admin/                # 管理员页面模板
```

## 贡献指南

### 代码贡献

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个Pull Request

### 开发规范

1. **代码风格**：遵循PEP 8 Python代码风格指南
2. **命名规范**：
   - 类名使用驼峰命名法（如`StockData`）
   - 函数和变量使用下划线命名法（如`get_stock_data`）
   - 常量使用大写字母（如`API_KEY`）
3. **注释规范**：
   - 为所有函数添加文档字符串，说明功能、参数和返回值
   - 为复杂逻辑添加行内注释
4. **测试**：
   - 为新功能编写单元测试
   - 确保所有测试通过后再提交PR

### 问题报告

如果您发现了问题或有功能建议，请创建一个Issue，并提供以下信息：

1. 问题描述或功能建议
2. 复现步骤（如果是问题）
3. 预期行为和实际行为
4. 系统环境（操作系统、Python版本等）
5. 相关截图（如果有）

### 文档贡献

欢迎改进项目文档，包括：

1. 修正错别字或语法错误
2. 添加缺失的说明或示例
3. 改进现有文档的清晰度和完整性
4. 翻译文档到其他语言

## 许可证

本项目采用MIT许可证。详情请参阅LICENSE文件。