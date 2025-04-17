"""
utils/__init__.py

This file is the initialization file for the utils package, used to export functionalities from each module.
"""

# Version information
__version__ = '0.1.1'

# Export all modules
from . import stock_data
from . import monte_carlo
from . import risk_monitor
from . import chat_ai
from . import number_utils
from . import datetime_utils
from . import order_utils

# Export common functions
# Stock data module
from .stock_data import fetch_stock_data, save_to_database, print_data_samples, run_stock_data_collection

# Monte Carlo simulation module
from .monte_carlo import monte_carlo_simulation, get_simulation_data, test_monte_carlo

# Risk monitoring module
from .risk_monitor import ValuationRiskMonitor, run_analysis, run_analysis_text_only_simple, test_risk_analysis

# AI chat module
from .chat_ai import print_markdown, chat_with_gemini, run_chat

# Number processing module
from .number_utils import db_round, RoundableDict

# Date and time processing module
from .datetime_utils import safe_date_format, create_safe_dict

# Order processing module
from .order_utils import (
    process_new_order,
    execute_order,
    validate_order_params,
    get_market_price,
    check_account_balance,
    can_execute_immediately,
    order_transaction_scope
)

# Define __all__ to control behavior of 'from utils import *' (optional but recommended)
__all__ = [
    # Stock data
    'fetch_stock_data', 'save_to_database', 'print_data_samples', 'run_stock_data_collection',
    # Monte Carlo
    'monte_carlo_simulation', 'get_simulation_data', 'test_monte_carlo',
    # Risk monitoring
    'ValuationRiskMonitor', 'run_analysis', 'run_analysis_text_only_simple', 'test_risk_analysis',
    # AI chat
    'print_markdown', 'chat_with_gemini', 'run_chat',
    # Number processing
    'db_round', 'RoundableDict',
    # Date and time
    'safe_date_format', 'create_safe_dict',
    # Order processing
    'process_new_order', 'execute_order', 'validate_order_params', 'get_market_price',
    'check_account_balance', 'can_execute_immediately', 'order_transaction_scope',
    # Modules themselves (if direct module access is needed)
    'stock_data', 'monte_carlo', 'risk_monitor', 'chat_ai', 'number_utils',
    'datetime_utils', 'order_utils'
] 