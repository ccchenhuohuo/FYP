"""
utils/__init__.py

这个文件是utils包的初始化文件，用于导出各个模块的功能。
"""

# 版本信息
__version__ = '0.1.0'

# 导出所有模块
from . import stock_data
from . import monte_carlo
from . import risk_monitor
from . import chat_ai

# 导出常用函数
# 股票数据模块
from .stock_data import fetch_stock_data, save_to_database, print_data_samples, run_stock_data_collection

# 蒙特卡洛模拟模块
from .monte_carlo import calculate_stock_parameters, monte_carlo_simulation, get_simulation_data, test_monte_carlo

# 风险监测模块
from .risk_monitor import ValuationRiskMonitor, run_analysis, run_analysis_text_only_simple, test_risk_analysis

# AI聊天模块
from .chat_ai import print_markdown, chat_with_gemini, run_chat 