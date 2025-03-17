# 股票交易与分析系统

这是一个基于Flask的股票交易与分析系统，提供用户账户管理、股票数据分析、交易模拟、蒙特卡洛模拟以及AI助手等功能。

## 功能特性

### 用户管理
- 用户注册与登录
- 管理员账户管理
- 个人资料管理

### 账户与资金
- 账户余额查看
- 资金充值与提现
- 交易记录查询

### 股票交易
- 股票行情查看
- 买入/卖出股票
- 订单管理
- 持仓查询

### 数据分析
- 股票历史数据查询
- 技术指标分析（MA、RSI、MACD等）
- 蒙特卡洛模拟预测
- 风险评估

### AI助手
- 基于Gemini AI的智能助手
- 股票相关问题咨询
- 投资建议与市场分析

## 技术栈

- **后端**: Flask, SQLAlchemy, PyMySQL
- **前端**: HTML, CSS, JavaScript, Bootstrap
- **数据库**: MySQL
- **AI**: Google Generative AI (Gemini)
- **数据分析**: Pandas, NumPy

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

6. 初始化数据库
```bash
flask db init
flask db migrate
flask db upgrade
```

7. 运行应用
```bash
python app.py
```

## 项目结构

```
/
├── app.py                 # 应用入口点
├── config.py              # 配置文件
├── models.py              # 数据库模型
├── auth.py                # 认证相关功能
├── routes/                # 路由模块
│   ├── __init__.py        # 路由注册
│   ├── auth/              # 认证路由
│   ├── user/              # 用户路由
│   ├── admin/             # 管理员路由
│   └── core/              # 核心路由
├── static/                # 静态资源
│   ├── css/               # 样式表
│   ├── js/                # JavaScript文件
│   └── picture.png        # 图片资源
├── templates/             # HTML模板
│   ├── auth/              # 认证相关模板
│   ├── user/              # 用户相关模板
│   ├── admin/             # 管理员相关模板
│   ├── about.html         # 关于页面
│   └── privacy.html       # 隐私政策页面
└── utils/                 # 工具函数
    ├── stock_data.py      # 股票数据处理
    ├── monte_carlo.py     # 蒙特卡洛模拟
    ├── risk_monitor.py    # 风险监测
    ├── chat_ai.py         # AI聊天功能
    └── number_utils.py    # 数字处理工具
```

## 使用说明

### 用户功能
1. 注册/登录账户
2. 查看账户余额和持仓情况
3. 浏览股票行情
4. 进行股票交易
5. 使用蒙特卡洛模拟进行预测
6. 与AI助手交流获取投资建议

### 管理员功能
1. 管理用户账户
2. 审核充值/提现请求
3. 监控系统运行状态
4. 管理股票数据

## API文档

### 用户API
- `POST /user/api/chat`: AI助手聊天接口
- `POST /user/api/deposit`: 资金充值接口
- `POST /user/api/withdraw`: 资金提现接口
- `POST /user/api/order`: 下单交易接口

### 股票数据API
- `GET /api/stock/{ticker}`: 获取股票数据
- `GET /api/stock/{ticker}/indicators`: 获取股票技术指标

## 注意事项

- 本系统仅用于模拟交易和学习，不涉及真实资金交易
- 股票数据来源于Alpha Vantage API，可能存在延迟
- AI助手基于Gemini AI，需要有效的API密钥才能正常使用
- 默认管理员账户: 用户名 `admin`，密码 `admin`

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请联系项目维护者。