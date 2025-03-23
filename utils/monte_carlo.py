"""
蒙特卡洛模拟模块
用于预测股票价格的未来走势
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import traceback

def monte_carlo_simulation(ticker, days=60, simulations=200):
    """
    执行完整的蒙特卡洛模拟流程
    
    参数:
        ticker (str): 股票代码
        days (int): 模拟天数，默认60天
        simulations (int): 模拟次数，默认200次
        
    返回:
        dict: 包含模拟结果的字典
    """
    try:
        # 获取历史数据
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="1y")
        
        if hist_data.empty:
            raise ValueError(f"无法获取{ticker}的历史数据")
        
        # 获取当前价格
        current_price = float(hist_data['Close'].iloc[-1])
        
        # 计算日收益率和波动率
        returns = np.log(1 + hist_data['Close'].pct_change())
        mu = float(returns.mean())  # 日均收益率
        sigma = float(returns.std())  # 日波动率
        
        # 生成模拟日期
        date_strings = []
        current_date = datetime.now()
        for i in range(days):
            future_date = current_date + timedelta(days=i)
            date_strings.append(future_date.strftime('%Y-%m-%d'))
            
        # 创建存储所有路径的数组
        paths = np.zeros((simulations, days))
        paths[:, 0] = current_price
        
        # 使用几何布朗运动模型进行模拟
        dt = 1  # 时间步长为1天
        for t in range(1, days):
            brownian = np.random.standard_normal(simulations)
            paths[:, t] = paths[:, t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * brownian)
        
        # 将Numpy数组转换为Python列表
        paths_list = paths.tolist()
        
        # 计算最终价格和统计数据
        final_prices = paths[:, -1]
        mean_price = float(np.mean(final_prices))
        median_price = float(np.median(final_prices))
        percentile_5 = float(np.percentile(final_prices, 5))
        percentile_25 = float(np.percentile(final_prices, 25))
        percentile_75 = float(np.percentile(final_prices, 75))
        percentile_95 = float(np.percentile(final_prices, 95))
        
        # 计算年化收益率和波动率
        annual_return = float((mean_price / current_price) ** (365 / days) - 1) * 100
        annual_volatility = float(sigma * np.sqrt(252) * 100)  # 252个交易日/年
        
        # 返回结果
        result = {
            "mean_price": mean_price,
            "median_price": median_price,
            "percentile_5": percentile_5,
            "percentile_25": percentile_25,
            "percentile_75": percentile_75,
            "percentile_95": percentile_95,
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "current_price": current_price,
            "ticker": ticker,
            "dates": date_strings,
            "all_paths": paths_list
        }
        
        return result
    
    except Exception as e:
        print(f"蒙特卡洛模拟失败: {str(e)}")
        print(traceback.format_exc())
        raise Exception(f"模拟过程中出现错误: {str(e)}")

# 向后兼容的函数，简单包装新函数
def get_simulation_data(ticker, days=60, simulations=200):
    """兼容旧API的包装函数"""
    return monte_carlo_simulation(ticker, days, simulations)

# 测试函数
def test_monte_carlo():
    """测试蒙特卡洛模拟功能"""
    test_ticker = "AAPL"
    try:
        simulation_results = get_simulation_data(test_ticker)
        print(f"模拟成功完成！")
        print(f"预测{test_ticker}在30天后的平均价格: ${simulation_results['mean_price']:.2f}")
        print(f"90%置信区间: ${simulation_results['percentile_5']:.2f} - ${simulation_results['percentile_95']:.2f}")
        return True
    except Exception as e:
        print(f"模拟失败: {str(e)}")
        return False 