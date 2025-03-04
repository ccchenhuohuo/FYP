"""
蒙特卡洛模拟API路由
"""
from flask import Blueprint, jsonify, request
from monte_carlo_simulation import get_simulation_data

monte_carlo_bp = Blueprint('monte_carlo', __name__)

@monte_carlo_bp.route('/api/monte-carlo/<ticker>', methods=['GET'])
def get_monte_carlo_simulation(ticker):
    """
    获取股票的蒙特卡洛模拟数据
    
    参数:
        ticker (str): 股票代码
    查询参数:
        days (int): 可选，模拟天数，默认30天
        simulations (int): 可选，模拟次数，默认1000次
    """
    try:
        days = request.args.get('days', default=30, type=int)
        simulations = request.args.get('simulations', default=1000, type=int)
        
        # 参数验证
        if days <= 0 or days > 365:
            return jsonify({
                'status': 'error',
                'message': '模拟天数必须在1到365天之间'
            }), 400
            
        if simulations <= 0 or simulations > 10000:
            return jsonify({
                'status': 'error',
                'message': '模拟次数必须在1到10000次之间'
            }), 400
        
        # 获取模拟数据
        results = get_simulation_data(ticker, days, simulations)
        
        if results['status'] == 'success':
            return jsonify(results)
        else:
            return jsonify(results), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 