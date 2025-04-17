import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import matplotlib.pyplot as plt
from scipy import stats

# 添加项目根目录到Python路径，以便导入utils模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.risk_monitor import ValuationRiskMonitor, run_analysis_text_only_simple

def test_yfinance_data():
    """测试从yfinance获取数据"""
    # 设置日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 测试股票代码
    ticker = "AAPL"
    
    print(f"获取 {ticker} 的数据，从 {start_date} 到 {end_date}")
    
    try:
        # 获取股票数据
        data = yf.download(ticker, start=start_date, end=end_date)
        
        # 检查数据是否为空
        if data.empty:
            print(f"警告: 无法获取 {ticker} 的数据")
            return
        
        # 打印数据基本信息
        print(f"获取到 {len(data)} 行数据")
        print("\n数据前5行:")
        print(data.head())
        
        # 打印数据列
        print("\n数据列:")
        print(data.columns)
        
        # 计算基本指标
        returns = data['Close'].pct_change().dropna()
        
        # 计算风险指标
        volatility = returns.std() * np.sqrt(252)
        volatility_value = float(volatility.iloc[0]) if hasattr(volatility, 'iloc') else float(volatility)
        
        # 使用.item()方法获取标量值
        returns_std = returns.std().item() if hasattr(returns.std(), 'item') else returns.std()
        returns_mean = returns.mean().item() if hasattr(returns.mean(), 'item') else returns.mean()
        
        sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252) if returns_std > 0 else 0
        
        # 计算最大回撤
        roll_max = data['Close'].cummax()
        drawdown = (data['Close'] / roll_max - 1)
        max_drawdown = float(drawdown.min().item()) if hasattr(drawdown.min(), 'item') else float(drawdown.min())
        
        # 打印风险指标
        print("\n风险指标:")
        print(f"年化波动率: {volatility_value:.2%}")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"最大回撤: {max_drawdown:.2%}")
        
    except Exception as e:
        import traceback
        print(f"获取价格数据时出错: {str(e)}")
        print(traceback.format_exc())
    
    # 单独测试基本面数据
    try:
        print("\n获取基本面数据:")
        stock = yf.Ticker(ticker)
        
        # 打印可用属性
        print("\n可用属性:")
        for attr in dir(stock):
            if not attr.startswith('_'):
                print(attr)
        
        # 获取收入表
        print("\n尝试获取收入表:")
        try:
            income_stmt = stock.income_stmt
            print(f"收入表类型: {type(income_stmt)}")
            if isinstance(income_stmt, pd.DataFrame) and not income_stmt.empty:
                print("收入表数据可用")
                print(f"收入表索引: {income_stmt.index}")
                if 'Net Income' in income_stmt.index:
                    net_income = income_stmt.loc['Net Income']
                    print(f"净收入: {net_income}")
                else:
                    print("收入表中没有'Net Income'字段")
            else:
                print("收入表为空或不是DataFrame")
        except Exception as e:
            print(f"获取收入表时出错: {str(e)}")
        
        # 尝试获取info
        print("\n尝试获取info:")
        try:
            info = stock.info
            print(f"info类型: {type(info)}")
            if isinstance(info, dict) and info:
                print(f"info包含 {len(info)} 个键")
                print("部分键: " + ", ".join(list(info.keys())[:5]))
            else:
                print("info为空或不是字典")
        except Exception as e:
            print(f"获取info时出错: {str(e)}")
        
    except Exception as e:
        print(f"获取基本面数据时出错: {str(e)}")

def test_risk_monitor_class():
    """测试ValuationRiskMonitor类的完整功能"""
    print("\n===== 测试ValuationRiskMonitor类 =====")
    
    # 设置日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 测试股票代码
    tickers = ["AAPL", "MSFT"]
    
    print(f"分析股票: {tickers}")
    print(f"日期范围: {start_date} 至 {end_date}")
    
    try:
        # 创建ValuationRiskMonitor实例
        monitor = ValuationRiskMonitor(tickers, start_date, end_date, min_data_points=30)
        
        # 下载数据
        print("\n下载数据:")
        stock_data = monitor.download_data()
        
        # 检查数据
        print("\n检查下载的数据:")
        for ticker in tickers:
            if ticker in stock_data and not stock_data[ticker].empty:
                print(f"{ticker} 数据可用，行数: {len(stock_data[ticker])}")
            else:
                print(f"{ticker} 数据不可用或为空")
        
        # 计算风险指标
        print("\n计算风险指标:")
        risk_metrics = monitor.calculate_risk_metrics()
        
        # 检查风险指标
        print("\n检查风险指标:")
        for ticker in tickers:
            if ticker in risk_metrics:
                print(f"\n{ticker} 风险指标:")
                
                # 基本风险指标
                basic_metrics = ['volatility', 'sharpe_ratio', 'max_drawdown', 'var_95', 'var_99', 'skewness', 'kurtosis']
                print("\n基本风险指标:")
                for metric in basic_metrics:
                    if metric in risk_metrics[ticker] and risk_metrics[ticker][metric] is not None:
                        if isinstance(risk_metrics[ticker][metric], (int, float)) and not isinstance(risk_metrics[ticker][metric], bool):
                            print(f"  {metric}: {risk_metrics[ticker][metric]:.4f}")
                        else:
                            print(f"  {metric}: {risk_metrics[ticker][metric]}")
                
                # 市场相关风险指标
                market_metrics = ['beta', 'r_squared', 'residual_risk', 'systematic_risk_pct']
                print("\n市场相关风险指标:")
                for metric in market_metrics:
                    if metric in risk_metrics[ticker] and risk_metrics[ticker][metric] is not None:
                        if isinstance(risk_metrics[ticker][metric], (int, float)) and not isinstance(risk_metrics[ticker][metric], bool):
                            print(f"  {metric}: {risk_metrics[ticker][metric]:.4f}")
                        else:
                            print(f"  {metric}: {risk_metrics[ticker][metric]}")
                
                # 风险调整回报指标
                return_metrics = ['information_ratio', 'treynor_ratio', 'sortino_ratio', 'downside_deviation']
                print("\n风险调整回报指标:")
                for metric in return_metrics:
                    if metric in risk_metrics[ticker] and risk_metrics[ticker][metric] is not None:
                        if isinstance(risk_metrics[ticker][metric], (int, float)) and not isinstance(risk_metrics[ticker][metric], bool):
                            print(f"  {metric}: {risk_metrics[ticker][metric]:.4f}")
                        else:
                            print(f"  {metric}: {risk_metrics[ticker][metric]}")
            else:
                print(f"{ticker} 没有风险指标")
        
        # 测试单元素Series的float转换
        print("\n测试单元素Series的float转换:")
        for ticker in tickers:
            if ticker in monitor.stock_data and not monitor.stock_data[ticker].empty:
                # 创建一个单元素Series进行测试
                test_series = pd.Series([0.5])
                print(f"原始Series: {test_series}")
                
                # 测试转换
                converted_value = float(test_series.iloc[0]) if hasattr(test_series, 'iloc') else float(test_series)
                print(f"转换后的值: {converted_value}")
                
                # 测试是否为单元素Series
                is_series = isinstance(test_series, pd.Series)
                has_iloc = hasattr(test_series, 'iloc')
                print(f"是Series: {is_series}, 有iloc属性: {has_iloc}")
                break
        
    except Exception as e:
        import traceback
        print(f"测试ValuationRiskMonitor时出错: {str(e)}")
        print(traceback.format_exc())

def test_run_analysis_function():
    """测试run_analysis_text_only_simple函数"""
    print("\n===== 测试run_analysis_text_only_simple函数 =====")
    
    # 设置日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 测试股票代码
    tickers = "AAPL,MSFT"
    
    print(f"分析股票: {tickers}")
    print(f"日期范围: {start_date} 至 {end_date}")
    
    try:
        # 运行分析
        monitor = run_analysis_text_only_simple(tickers, start_date, end_date)
        
        # 检查结果
        if monitor:
            print("\n分析成功完成")
            
            # 检查风险指标
            if hasattr(monitor, 'risk_metrics'):
                print("\n检查风险指标:")
                for ticker in monitor.tickers:
                    if ticker in monitor.risk_metrics:
                        print(f"\n{ticker} 风险指标:")
                        for metric, value in monitor.risk_metrics[ticker].items():
                            if isinstance(value, (int, float)) and not isinstance(value, bool):
                                print(f"  {metric}: {value:.4f}")
                            else:
                                print(f"  {metric}: {value}")
                    else:
                        print(f"{ticker} 没有风险指标")
            else:
                print("monitor没有risk_metrics属性")
        else:
            print("分析失败，返回None")
        
    except Exception as e:
        import traceback
        print(f"测试run_analysis_text_only_simple时出错: {str(e)}")
        print(traceback.format_exc())

def test_manual_risk_calculation():
    """手动实现风险计算算法进行测试"""
    print("\n===== 手动实现风险计算算法 =====")
    
    # 设置日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 测试股票代码
    ticker = "AAPL"
    benchmark_ticker = "^GSPC"  # S&P 500
    
    print(f"分析股票: {ticker}")
    print(f"基准指数: {benchmark_ticker}")
    print(f"日期范围: {start_date} 至 {end_date}")
    
    try:
        # 获取股票数据
        stock_data = yf.download(ticker, start=start_date, end=end_date)
        benchmark_data = yf.download(benchmark_ticker, start=start_date, end=end_date)
        
        # 检查数据
        if stock_data.empty:
            print(f"警告: 无法获取 {ticker} 的数据")
            return
        
        if benchmark_data.empty:
            print(f"警告: 无法获取基准 {benchmark_ticker} 的数据")
        
        print(f"获取到 {ticker} 数据行数: {len(stock_data)}")
        print(f"获取到 {benchmark_ticker} 数据行数: {len(benchmark_data)}")
        
        # 计算收益率
        stock_returns = stock_data['Close'].pct_change().dropna()
        benchmark_returns = benchmark_data['Close'].pct_change().dropna()
        
        # 转换为NumPy数组，避免Series比较问题
        stock_returns_np = stock_returns.values
        benchmark_returns_np = benchmark_returns.values
        
        # 计算风险指标
        print("\n计算风险指标:")
        
        # 1. 波动率
        volatility = np.std(stock_returns_np, ddof=1) * np.sqrt(252)
        print(f"年化波动率: {volatility:.2%}")
        
        # 2. 夏普比率
        returns_mean = np.mean(stock_returns_np)
        returns_std = np.std(stock_returns_np, ddof=1)
        
        if returns_std > 0:
            sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252)
            print(f"夏普比率: {sharpe_ratio:.2f}")
        else:
            print("警告: 收益率标准差为0，无法计算夏普比率")
            sharpe_ratio = 0.0
        
        # 3. 最大回撤
        roll_max = stock_data['Close'].cummax().values
        close_values = stock_data['Close'].values
        drawdown = close_values / roll_max - 1
        max_drawdown = np.min(drawdown)
        print(f"最大回撤: {max_drawdown:.2%}")
        
        # 4. VaR
        if len(stock_returns_np) >= 5:
            var_95 = np.percentile(stock_returns_np, 5)
            var_99 = np.percentile(stock_returns_np, 1)
            print(f"95% VaR: {var_95:.2%}")
            print(f"99% VaR: {var_99:.2%}")
        else:
            print("警告: 数据不足，无法计算可靠的VaR")
        
        # 5. 偏度和峰度
        if len(stock_returns_np) > 3:
            skewness = stats.skew(stock_returns_np)
            kurtosis = stats.kurtosis(stock_returns_np)
            # 确保skewness和kurtosis是标量值
            if hasattr(skewness, 'item'):
                skewness = skewness.item()
            if hasattr(kurtosis, 'item'):
                kurtosis = kurtosis.item()
            print(f"偏度: {skewness:.2f}")
            print(f"峰度: {kurtosis:.2f}")
        else:
            print("警告: 数据不足，无法计算偏度和峰度")
        
        # 6. 贝塔系数和R方值
        if len(stock_returns_np) > 30 and len(benchmark_returns_np) > 30:
            # 确保两个序列有相同的索引
            common_index = stock_returns.index.intersection(benchmark_returns.index)
            if len(common_index) > 30:
                # 对齐数据
                stock_returns_aligned = stock_returns.loc[common_index].values
                benchmark_returns_aligned = benchmark_returns.loc[common_index].values
                
                # 计算协方差和方差
                cov_matrix = np.cov(stock_returns_aligned, benchmark_returns_aligned, ddof=1)
                if cov_matrix.shape == (2, 2):
                    covariance = cov_matrix[0, 1]
                    benchmark_variance = np.var(benchmark_returns_aligned, ddof=1)
                    
                    if benchmark_variance > 0:
                        beta = covariance / benchmark_variance
                        print(f"贝塔系数: {beta:.2f}")
                        
                        # 计算R方值
                        correlation = np.corrcoef(stock_returns_aligned, benchmark_returns_aligned)[0, 1]
                        r_squared = correlation ** 2
                        print(f"R方值: {r_squared:.2f}")
                        
                        # 计算残差风险
                        predicted_returns = benchmark_returns_aligned * beta
                        residual_returns = stock_returns_aligned - predicted_returns
                        residual_risk = np.std(residual_returns, ddof=1) * np.sqrt(252)
                        print(f"残差风险: {residual_risk:.2%}")
                        
                        # 计算系统性风险占比
                        total_risk = np.std(stock_returns_aligned, ddof=1) * np.sqrt(252)
                        systematic_risk = beta * np.std(benchmark_returns_aligned, ddof=1) * np.sqrt(252)
                        systematic_risk_pct = (systematic_risk / total_risk) ** 2
                        print(f"系统性风险占比: {systematic_risk_pct:.2%}")
                    else:
                        print("警告: 基准收益率方差为0，无法计算贝塔系数")
                else:
                    print("警告: 协方差矩阵形状不正确，无法计算贝塔系数")
            else:
                print("警告: 共同数据点数量不足30，无法计算贝塔系数")
        else:
            print("警告: 数据不足，无法计算贝塔系数")
        
        # 7. 信息比率
        if len(stock_returns_np) > 30 and len(benchmark_returns_np) > 30:
            common_index = stock_returns.index.intersection(benchmark_returns.index)
            if len(common_index) > 30:
                stock_returns_aligned = stock_returns.loc[common_index].values
                benchmark_returns_aligned = benchmark_returns.loc[common_index].values
                
                excess_returns = stock_returns_aligned - benchmark_returns_aligned
                excess_returns_mean = np.mean(excess_returns)
                excess_returns_std = np.std(excess_returns, ddof=1)
                
                if excess_returns_std > 0:
                    information_ratio = excess_returns_mean / excess_returns_std * np.sqrt(252)
                    print(f"信息比率: {information_ratio:.2f}")
                else:
                    print("警告: 超额收益标准差为0，无法计算信息比率")
            else:
                print("警告: 共同数据点数量不足30，无法计算信息比率")
        else:
            print("警告: 数据不足，无法计算信息比率")
        
        # 8. 索提诺比率
        if len(stock_returns_np) > 30:
            negative_returns = stock_returns_np[stock_returns_np < 0]
            if len(negative_returns) > 0:
                downside_risk = np.std(negative_returns, ddof=1) * np.sqrt(252)
                
                if downside_risk > 0:
                    sortino_ratio = (returns_mean * 252) / downside_risk
                    print(f"索提诺比率: {sortino_ratio:.2f}")
                    
                    # 计算下行偏差
                    target_return = 0
                    downside_returns = stock_returns_np[stock_returns_np < target_return]
                    downside_deviation = np.sqrt(np.sum((downside_returns - target_return) ** 2) / len(stock_returns_np)) * np.sqrt(252)
                    print(f"下行偏差: {downside_deviation:.2%}")
                else:
                    print("警告: 下行风险为0，无法计算索提诺比率")
            else:
                print("警告: 没有负收益，索提诺比率为无穷大")
        else:
            print("警告: 数据不足，无法计算索提诺比率")
        
        # 9. 绘制收益率分布图
        plt.figure(figsize=(10, 6))
        plt.hist(stock_returns_np, bins=50, alpha=0.7, color='blue')
        plt.title(f'{ticker} 收益率分布')
        plt.xlabel('日收益率')
        plt.ylabel('频率')
        plt.grid(True, alpha=0.3)
        
        # 保存图表
        plt.savefig(f'{ticker}_returns_distribution.png')
        print(f"\n收益率分布图已保存为 {ticker}_returns_distribution.png")
        
    except Exception as e:
        import traceback
        print(f"手动计算风险指标时出错: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    # 测试基本的yfinance数据获取
    test_yfinance_data()
    
    # 测试ValuationRiskMonitor类
    test_risk_monitor_class()
    
    # 测试run_analysis_text_only_simple函数
    test_run_analysis_function()
    
    # 测试手动实现的风险计算算法
    test_manual_risk_calculation() 