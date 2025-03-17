"""
蒙特卡洛模拟API路由
"""
from flask import Blueprint, jsonify, request
from utils.monte_carlo import get_simulation_data

# 蒙特卡洛相关蓝图
monte_carlo_bp = Blueprint('monte_carlo', __name__)

@monte_carlo_bp.route('/api/monte-carlo/<ticker>', methods=['GET'])
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
        days = request.args.get('days', default=60, type=int)
        simulations = request.args.get('simulations', default=200, type=int)
        
        # 参数验证
        if days <= 0 or simulations <= 0:
            return jsonify({
                'error': '参数无效，天数和模拟次数必须大于0'
            }), 400
            
        # 调用蒙特卡洛模拟
        simulation_data = get_simulation_data(ticker, days, simulations)
        return jsonify(simulation_data)
        
    except Exception as e:
        return jsonify({
            'error': f'模拟失败: {str(e)}'
        }), 500 