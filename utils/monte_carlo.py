"""
蒙特卡洛模拟模块
用于预测股票价格的未来走势
"""
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import yfinance as yf

def calculate_stock_parameters(historical_data):
    """
    计算股票的日收益率、波动率和漂移率
    
    参数:
        historical_data (pd.DataFrame): 包含历史收盘价的数据框
        
    返回:
        tuple: (日收益率均值, 日波动率)
    """
    # 计算日收益率
    returns = np.log(1 + historical_data['Close'].pct_change())
    
    # 计算年化参数
    mu = returns.mean()
    sigma = returns.std()
    
    return mu, sigma

def monte_carlo_simulation(ticker, start_price, mu, sigma, days, simulations=1000):
    """
    执行蒙特卡洛模拟
    
    参数:
        ticker (str): 股票代码
        start_price (float): 起始价格
        mu (float): 日收益率均值
        sigma (float): 日波动率
        days (int): 模拟天数
        simulations (int): 模拟次数
        
    返回:
        dict: 包含模拟结果的字典
    """
    # 生成随机正态分布数据
    dt = 1  # 每次步进1天
    simulation_matrix = np.zeros((days, simulations))
    simulation_matrix[0] = start_price
    
    # 使用几何布朗运动模型进行模拟
    for t in range(1, days):
        brownian = np.random.standard_normal(simulations)
        simulation_matrix[t] = simulation_matrix[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * brownian)
    
    # 计算统计数据
    final_prices = simulation_matrix[-1]
    mean_price = float(np.mean(final_prices))  # 转换为Python float
    percentile_5 = float(np.percentile(final_prices, 5))  # 转换为Python float
    percentile_95 = float(np.percentile(final_prices, 95))  # 转换为Python float
    
    # 生成时间序列
    dates = [datetime.now() + timedelta(days=x) for x in range(days)]
    
    # 将numpy数组转换为Python列表
    simulation_paths = simulation_matrix.T.tolist()
    
    return {
        'dates': dates,
        'mean_price': mean_price,
        'percentile_5': percentile_5,
        'percentile_95': percentile_95,
        'all_paths': simulation_paths
    }

def get_simulation_data(ticker, days=30, simulations=1000):
    """
    获取股票数据并运行蒙特卡洛模拟
    
    参数:
        ticker (str): 股票代码
        days (int): 模拟天数
        simulations (int): 模拟次数
        
    返回:
        dict: 模拟结果
    """
    try:
        # 获取最近一年的历史数据
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="1y")
        
        if hist_data.empty:
            raise ValueError(f"无法获取{ticker}的历史数据")
        
        # 获取最新收盘价
        start_price = float(hist_data['Close'].iloc[-1])  # 转换为Python float
        
        # 计算必要参数
        mu, sigma = calculate_stock_parameters(hist_data)
        mu = float(mu)  # 转换为Python float
        sigma = float(sigma)  # 转换为Python float
        
        # 运行蒙特卡洛模拟
        simulation_results = monte_carlo_simulation(
            ticker=ticker,
            start_price=start_price,
            mu=mu,
            sigma=sigma,
            days=days,
            simulations=simulations
        )
        
        return simulation_results, {
            'mean_price': simulation_results['mean_price'],
            'percentile_5': simulation_results['percentile_5'],
            'percentile_95': simulation_results['percentile_95']
        }, start_price
        
    except Exception as e:
        raise Exception(f"模拟失败: {str(e)}")

# 测试函数
def test_monte_carlo():
    """测试蒙特卡洛模拟功能"""
    test_ticker = "AAPL"
    try:
        simulation_results, prediction_stats, current_price = get_simulation_data(test_ticker)
        print(f"模拟成功完成！")
        print(f"预测{test_ticker}在30天后的平均价格: ${prediction_stats['mean_price']:.2f}")
        print(f"90%置信区间: ${prediction_stats['percentile_5']:.2f} - ${prediction_stats['percentile_95']:.2f}")
        return True
    except Exception as e:
        print(f"模拟失败: {str(e)}")
        return False 