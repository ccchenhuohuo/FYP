"""
蒙特卡洛模拟API路由
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from utils.monte_carlo import monte_carlo_simulation
import traceback

# 蒙特卡洛相关蓝图
monte_carlo_bp = Blueprint('monte_carlo', __name__)

@monte_carlo_bp.route('/api/monte-carlo/<ticker>', methods=['GET'])
@login_required
def get_monte_carlo_simulation(ticker):
    """
    获取股票的蒙特卡洛模拟数据
    
    参数:
        ticker (str): 股票代码
    查询参数:
        days (int): 可选，模拟天数，默认60天
        simulations (int): 可选，模拟次数，默认200次
    """
    try:
        # 获取并验证参数
        days = request.args.get('days', default=60, type=int)
        simulations = request.args.get('simulations', default=200, type=int)
        
        # 参数验证
        if days <= 0 or days > 365:
            return jsonify({
                'error': f'模拟天数必须在1-365之间，当前值: {days}'
            }), 400
            
        if simulations <= 0 or simulations > 1000:
            return jsonify({
                'error': f'模拟次数必须在1-1000之间，当前值: {simulations}'
            }), 400
            
        # 直接调用模拟函数
        result = monte_carlo_simulation(ticker, days, simulations)
        
        # 直接返回结果，不再嵌套
        return jsonify(result)
        
    except Exception as e:
        # 记录详细错误
        error_msg = str(e)
        print(f"蒙特卡洛模拟API错误: {error_msg}")
        print(traceback.format_exc())
        
        # 返回友好的错误信息
        return jsonify({
            'error': f'模拟失败: {error_msg}'
        }), 500 