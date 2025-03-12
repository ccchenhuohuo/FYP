"""
蒙特卡洛模拟API路由
"""
from flask import Blueprint, jsonify, request
from utils.monte_carlo import get_simulation_data

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
        
        simulation_results, prediction_stats, current_price = get_simulation_data(ticker, days, simulations)
        
        # 将日期转换为ISO字符串格式，以便在JSON中序列化
        iso_dates = [date.isoformat() for date in simulation_results['dates']]
        
        return jsonify({
            'status': 'success',
            'data': {
                'ticker': ticker,
                'days': days,
                'simulations': simulations,
                'current_price': current_price,
                'prediction_stats': prediction_stats,
                'dates': iso_dates,
                'all_paths': simulation_results['all_paths'],
                'mean_price': simulation_results['mean_price'],
                'percentile_5': simulation_results['percentile_5'],
                'percentile_95': simulation_results['percentile_95']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 