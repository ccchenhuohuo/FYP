"""
风险监测模块
用于监测和分析股票的风险和估值
"""
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import datetime as dt

class ValuationRiskMonitor:
    """
    估值和风险监测系统
    """
    def __init__(self, tickers, start_date=None, end_date=None, benchmark_ticker="^GSPC", min_data_points=60):
        """
        初始化估值和风险监测系统
        
        参数:
        tickers (list): 股票代码列表
        start_date (str): 起始日期，格式 'YYYY-MM-DD'
        end_date (str): 结束日期，格式 'YYYY-MM-DD'
        benchmark_ticker (str): 基准指数，默认为S&P 500
        min_data_points (int): 计算贝塔系数所需的最小数据点数量
        """
        self.tickers = tickers if isinstance(tickers, list) else [tickers]
        self.start_date = start_date if start_date else (dt.datetime.now() - dt.timedelta(days=365*3)).strftime('%Y-%m-%d')
        self.end_date = end_date if end_date else dt.datetime.now().strftime('%Y-%m-%d')
        self.benchmark_ticker = benchmark_ticker
        self.min_data_points = min_data_points
        self.stock_data = {}
        self.fundamentals = {}
        self.risk_metrics = {}
        self.valuation_metrics = {}
        self.benchmark_data = None
        
    def download_data(self):
        """下载股票数据和基准数据"""
        print("正在下载市场数据...")
        
        # 检查是否有有效的股票代码
        if not self.tickers:
            print("没有提供有效的股票代码")
            return {}
        
        # 下载股票价格数据
        for ticker in self.tickers:
            try:
                data = yf.download(ticker, start=self.start_date, end=self.end_date)
                
                # 检查是否获取到数据
                if data.empty:
                    print(f"警告: 无法获取 {ticker} 的数据")
                    self.stock_data[ticker] = pd.DataFrame()  # 空数据框
                else:
                    self.stock_data[ticker] = data
                    print(f"已下载 {ticker} 的历史价格数据")
            except Exception as e:
                print(f"下载 {ticker} 数据时出错: {str(e)}")
                self.stock_data[ticker] = pd.DataFrame()  # 空数据框
        
        # 下载基准数据
        try:
            self.benchmark_data = yf.download(self.benchmark_ticker, start=self.start_date, end=self.end_date)
            if self.benchmark_data.empty:
                print(f"警告: 无法获取基准 {self.benchmark_ticker} 的数据")
            else:
                print(f"已下载 {self.benchmark_ticker} 的基准数据")
        except Exception as e:
            print(f"下载基准数据时出错: {str(e)}")
            self.benchmark_data = pd.DataFrame()  # 空数据框
        
        # 获取基本面数据
        self._get_fundamentals()
        
        return self.stock_data
    
    def _get_fundamentals(self):
        """获取股票的基本面数据"""
        print("正在获取基本面数据...")
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                # 获取财务报表
                try:
                    # 获取收入表中的净收入，替代已弃用的earnings
                    income_stmt = stock.income_stmt if hasattr(stock, 'income_stmt') else pd.DataFrame()
                    net_income = None
                    if not income_stmt.empty and 'Net Income' in income_stmt.index:
                        net_income = income_stmt.loc['Net Income']
                    
                    self.fundamentals[ticker] = {
                        'info': stock.info if hasattr(stock, 'info') else {},
                        'balance_sheet': stock.balance_sheet if hasattr(stock, 'balance_sheet') else pd.DataFrame(),
                        'income_stmt': income_stmt,
                        'cash_flow': stock.cashflow if hasattr(stock, 'cashflow') else pd.DataFrame(),
                        'net_income': net_income  # 使用从income_stmt中提取的净收入替代earnings
                    }
                    print(f"已获取 {ticker} 的基本面数据")
                except Exception as e:
                    print(f"获取 {ticker} 的基本面数据时出错: {e}")
                    # 提供空的基本面数据结构
                    self.fundamentals[ticker] = {
                        'info': {},
                        'balance_sheet': pd.DataFrame(),
                        'income_stmt': pd.DataFrame(),
                        'cash_flow': pd.DataFrame(),
                        'net_income': None
                    }
            except Exception as e:
                print(f"创建 {ticker} 的Ticker对象时出错: {e}")
                # 提供空的基本面数据结构
                self.fundamentals[ticker] = {
                    'info': {},
                    'balance_sheet': pd.DataFrame(),
                    'income_stmt': pd.DataFrame(),
                    'cash_flow': pd.DataFrame(),
                    'net_income': None
                }
    
    def calculate_risk_metrics(self):
        """计算风险指标"""
        print("正在计算风险指标...")
        for ticker in self.tickers:
            try:
                # 检查是否有足够的数据
                if ticker not in self.stock_data or self.stock_data[ticker].empty or len(self.stock_data[ticker]) < 2:
                    print(f"警告: {ticker} 没有足够的价格数据，无法计算风险指标")
                    self.risk_metrics[ticker] = {
                        'data_available': False,
                        'error_message': '没有足够的价格数据'
                    }
                    continue
                
                # 计算收益率
                returns = self.stock_data[ticker]['Close'].pct_change().dropna()
                
                # 检查基准数据
                if self.benchmark_data is None or self.benchmark_data.empty or len(self.benchmark_data) < 2:
                    print(f"警告: 没有足够的基准数据，无法计算 {ticker} 的贝塔系数")
                    benchmark_returns = None
                else:
                    benchmark_returns = self.benchmark_data['Close'].pct_change().dropna()
                
                # 初始化风险指标字典
                self.risk_metrics[ticker] = {
                    'data_available': True
                }
                
                # 计算波动率
                volatility = returns.std() * np.sqrt(252)
                # 修复单元素Series的float转换
                self.risk_metrics[ticker]['volatility'] = float(volatility.item()) if hasattr(volatility, 'item') else float(volatility)
                
                # 计算夏普比率 - 处理除以零的情况
                # 使用.item()方法获取标量值
                returns_std = returns.std().item() if hasattr(returns.std(), 'item') else returns.std()
                returns_mean = returns.mean().item() if hasattr(returns.mean(), 'item') else returns.mean()
                
                if returns_std > 0:
                    sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252)
                    # 修复单元素Series的float转换
                    self.risk_metrics[ticker]['sharpe_ratio'] = float(sharpe_ratio) if isinstance(sharpe_ratio, (np.float64, np.float32)) else sharpe_ratio
                else:
                    print(f"警告: {ticker} 的收益率标准差为0，无法计算夏普比率")
                    self.risk_metrics[ticker]['sharpe_ratio'] = 0.0
                
                # 计算最大回撤
                try:
                    max_drawdown = self._calculate_max_drawdown(self.stock_data[ticker]['Close'])
                    self.risk_metrics[ticker]['max_drawdown'] = float(max_drawdown) if max_drawdown is not None else None
                except Exception as e:
                    print(f"计算 {ticker} 最大回撤时出错: {str(e)}")
                    self.risk_metrics[ticker]['max_drawdown'] = None
                
                # 计算VaR
                if len(returns) >= 5:
                    var_95 = np.percentile(returns, 5)
                    var_99 = np.percentile(returns, 1)
                    # 修复单元素Series的float转换
                    self.risk_metrics[ticker]['var_95'] = float(var_95.item()) if hasattr(var_95, 'item') else float(var_95)
                    self.risk_metrics[ticker]['var_99'] = float(var_99.item()) if hasattr(var_99, 'item') else float(var_99)
                else:
                    print(f"警告: {ticker} 的数据不足，无法计算可靠的VaR")
                    self.risk_metrics[ticker]['var_95'] = None
                    self.risk_metrics[ticker]['var_99'] = None
                
                # 计算偏度和峰度
                if len(returns) > 3:  # 需要至少4个数据点
                    skewness = stats.skew(returns)
                    kurtosis = stats.kurtosis(returns)
                    # 修复单元素Series的float转换
                    self.risk_metrics[ticker]['skewness'] = float(skewness.item()) if hasattr(skewness, 'item') else float(skewness)
                    self.risk_metrics[ticker]['kurtosis'] = float(kurtosis.item()) if hasattr(kurtosis, 'item') else float(kurtosis)
                else:
                    print(f"警告: {ticker} 的数据不足，无法计算偏度和峰度")
                    self.risk_metrics[ticker]['skewness'] = None
                    self.risk_metrics[ticker]['kurtosis'] = None
                
                # 计算贝塔系数 - 改进版
                self._calculate_beta(ticker, returns, benchmark_returns)
                
                # 计算信息比率
                self._calculate_information_ratio(ticker, returns, benchmark_returns)
                
                # 计算特雷诺比率
                self._calculate_treynor_ratio(ticker, returns, benchmark_returns)
                
                # 计算索提诺比率
                self._calculate_sortino_ratio(ticker, returns)
                
            except Exception as e:
                print(f"计算 {ticker} 风险指标时出错: {str(e)}")
                self.risk_metrics[ticker] = {
                    'data_available': False,
                    'error_message': f'计算风险指标时出错: {str(e)}'
                }
                
        return self.risk_metrics
    
    def _calculate_max_drawdown(self, price_series):
        """计算最大回撤"""
        try:
            if price_series.empty or len(price_series) < 2:
                print("价格序列为空或数据不足，无法计算最大回撤")
                return None
            
            roll_max = price_series.cummax()
            drawdown = (price_series / roll_max - 1)
            min_drawdown = drawdown.min()
            # 修复单元素Series的float转换
            return float(min_drawdown.item()) if hasattr(min_drawdown, 'item') else float(min_drawdown)
        except Exception as e:
            print(f"计算最大回撤时出错: {str(e)}")
            return None
    
    def _calculate_beta(self, ticker, returns, benchmark_returns):
        """
        计算贝塔系数 - 改进版
        
        参数:
        ticker (str): 股票代码
        returns (Series): 股票收益率序列
        benchmark_returns (Series): 基准指数收益率序列
        """
        if benchmark_returns is None or len(returns) < self.min_data_points or len(benchmark_returns) < self.min_data_points:
            print(f"警告: 数据点数量不足 {self.min_data_points}，无法计算 {ticker} 的贝塔系数")
            self.risk_metrics[ticker]['beta'] = None
            self.risk_metrics[ticker]['r_squared'] = None
            self.risk_metrics[ticker]['residual_risk'] = None
            self.risk_metrics[ticker]['systematic_risk_pct'] = None
            return
        
        try:
            # 确保两个序列有相同的索引
            common_index = returns.index.intersection(benchmark_returns.index)
            if len(common_index) < self.min_data_points:
                print(f"警告: 共同数据点数量不足 {self.min_data_points}，无法计算 {ticker} 的贝塔系数")
                self.risk_metrics[ticker]['beta'] = None
                self.risk_metrics[ticker]['r_squared'] = None
                self.risk_metrics[ticker]['residual_risk'] = None
                self.risk_metrics[ticker]['systematic_risk_pct'] = None
                return
            
            # 对齐数据
            stock_returns_aligned = returns.loc[common_index]
            benchmark_returns_aligned = benchmark_returns.loc[common_index]
            
            # 使用numpy计算协方差和方差，避免DataFrame和Series的比较问题
            stock_returns_np = stock_returns_aligned.values
            benchmark_returns_np = benchmark_returns_aligned.values
            
            # 计算协方差和方差
            cov_matrix = np.cov(stock_returns_np, benchmark_returns_np, ddof=1)
            if cov_matrix.shape == (2, 2):
                covariance = cov_matrix[0, 1]
                benchmark_variance = np.var(benchmark_returns_np, ddof=1)
                
                # 检查方差是否为零
                if benchmark_variance > 0:
                    beta = covariance / benchmark_variance
                    self.risk_metrics[ticker]['beta'] = float(beta)
                    
                    # 计算R方值（决定系数）
                    correlation = np.corrcoef(stock_returns_np, benchmark_returns_np)[0, 1]
                    r_squared = correlation ** 2
                    self.risk_metrics[ticker]['r_squared'] = float(r_squared)
                    
                    # 计算残差风险（特异风险）
                    predicted_returns = benchmark_returns_np * beta
                    residual_returns = stock_returns_np - predicted_returns
                    residual_risk = np.std(residual_returns, ddof=1) * np.sqrt(252)
                    self.risk_metrics[ticker]['residual_risk'] = float(residual_risk)
                    
                    # 计算系统性风险占比
                    total_risk = np.std(stock_returns_np, ddof=1) * np.sqrt(252)
                    systematic_risk = beta * np.std(benchmark_returns_np, ddof=1) * np.sqrt(252)
                    systematic_risk_pct = (systematic_risk / total_risk) ** 2
                    self.risk_metrics[ticker]['systematic_risk_pct'] = float(systematic_risk_pct)
                else:
                    print(f"警告: 基准收益率方差为0，无法计算 {ticker} 的贝塔系数")
                    self.risk_metrics[ticker]['beta'] = None
                    self.risk_metrics[ticker]['r_squared'] = None
                    self.risk_metrics[ticker]['residual_risk'] = None
                    self.risk_metrics[ticker]['systematic_risk_pct'] = None
            else:
                print(f"警告: 协方差矩阵形状不正确，无法计算 {ticker} 的贝塔系数")
                self.risk_metrics[ticker]['beta'] = None
                self.risk_metrics[ticker]['r_squared'] = None
                self.risk_metrics[ticker]['residual_risk'] = None
                self.risk_metrics[ticker]['systematic_risk_pct'] = None
        except Exception as e:
            print(f"计算 {ticker} 贝塔系数时出错: {str(e)}")
            self.risk_metrics[ticker]['beta'] = None
            self.risk_metrics[ticker]['r_squared'] = None
            self.risk_metrics[ticker]['residual_risk'] = None
            self.risk_metrics[ticker]['systematic_risk_pct'] = None
    
    def _calculate_information_ratio(self, ticker, returns, benchmark_returns):
        """
        计算信息比率
        
        参数:
        ticker (str): 股票代码
        returns (Series): 股票收益率序列
        benchmark_returns (Series): 基准指数收益率序列
        """
        if benchmark_returns is None or len(returns) < 30 or len(benchmark_returns) < 30:
            print(f"警告: 数据不足，无法计算 {ticker} 的信息比率")
            self.risk_metrics[ticker]['information_ratio'] = None
            return
        
        try:
            # 确保两个序列有相同的索引
            common_index = returns.index.intersection(benchmark_returns.index)
            if len(common_index) < 30:
                print(f"警告: 共同数据点数量不足30，无法计算 {ticker} 的信息比率")
                self.risk_metrics[ticker]['information_ratio'] = None
                return
            
            # 对齐数据
            stock_returns_aligned = returns.loc[common_index]
            benchmark_returns_aligned = benchmark_returns.loc[common_index]
            
            # 转换为numpy数组，避免Series比较问题
            stock_returns_np = stock_returns_aligned.values
            benchmark_returns_np = benchmark_returns_aligned.values
            
            # 计算超额收益
            excess_returns = stock_returns_np - benchmark_returns_np
            
            # 计算信息比率
            excess_returns_mean = np.mean(excess_returns)
            excess_returns_std = np.std(excess_returns, ddof=1)
            
            if excess_returns_std > 0:
                information_ratio = excess_returns_mean / excess_returns_std * np.sqrt(252)
                self.risk_metrics[ticker]['information_ratio'] = float(information_ratio)
            else:
                print(f"警告: 超额收益标准差为0，无法计算 {ticker} 的信息比率")
                self.risk_metrics[ticker]['information_ratio'] = None
        except Exception as e:
            print(f"计算 {ticker} 信息比率时出错: {str(e)}")
            self.risk_metrics[ticker]['information_ratio'] = None
    
    def _calculate_treynor_ratio(self, ticker, returns, benchmark_returns):
        """
        计算特雷诺比率
        
        参数:
        ticker (str): 股票代码
        returns (Series): 股票收益率序列
        benchmark_returns (Series): 基准指数收益率序列
        """
        if 'beta' not in self.risk_metrics[ticker] or self.risk_metrics[ticker]['beta'] is None:
            print(f"警告: 贝塔系数不可用，无法计算 {ticker} 的特雷诺比率")
            self.risk_metrics[ticker]['treynor_ratio'] = None
            return
        
        try:
            # 计算无风险收益率（假设为0，可以根据实际情况调整）
            risk_free_rate = 0.0
            
            # 计算年化平均收益率
            returns_mean = returns.mean() * 252
            
            # 计算特雷诺比率
            beta = self.risk_metrics[ticker]['beta']
            if beta != 0:
                treynor_ratio = (returns_mean - risk_free_rate) / beta
                self.risk_metrics[ticker]['treynor_ratio'] = float(treynor_ratio)
            else:
                print(f"警告: 贝塔系数为0，无法计算 {ticker} 的特雷诺比率")
                self.risk_metrics[ticker]['treynor_ratio'] = None
        except Exception as e:
            print(f"计算 {ticker} 特雷诺比率时出错: {str(e)}")
            self.risk_metrics[ticker]['treynor_ratio'] = None
    
    def _calculate_sortino_ratio(self, ticker, returns):
        """
        计算索提诺比率
        
        参数:
        ticker (str): 股票代码
        returns (Series): 股票收益率序列
        """
        if len(returns) < 30:
            print(f"警告: 数据不足，无法计算 {ticker} 的索提诺比率")
            self.risk_metrics[ticker]['sortino_ratio'] = None
            self.risk_metrics[ticker]['downside_deviation'] = None
            return
        
        try:
            # 转换为numpy数组，避免Series比较问题
            returns_np = returns.values
            
            # 计算无风险收益率（假设为0，可以根据实际情况调整）
            risk_free_rate = 0.0
            
            # 计算年化平均收益率
            returns_mean = np.mean(returns_np) * 252
            
            # 计算下行风险（只考虑负收益）
            negative_returns = returns_np[returns_np < 0]
            if len(negative_returns) > 0:
                downside_risk = np.std(negative_returns, ddof=1) * np.sqrt(252)
                
                # 计算索提诺比率
                if downside_risk > 0:
                    sortino_ratio = (returns_mean - risk_free_rate) / downside_risk
                    self.risk_metrics[ticker]['sortino_ratio'] = float(sortino_ratio)
                    
                    # 计算下行偏差
                    target_return = 0  # 目标收益率，可以根据实际情况调整
                    downside_returns = returns_np[returns_np < target_return]
                    downside_deviation = np.sqrt(np.sum((downside_returns - target_return) ** 2) / len(returns_np)) * np.sqrt(252)
                    self.risk_metrics[ticker]['downside_deviation'] = float(downside_deviation)
                else:
                    print(f"警告: 下行风险为0，无法计算 {ticker} 的索提诺比率")
                    self.risk_metrics[ticker]['sortino_ratio'] = None
                    self.risk_metrics[ticker]['downside_deviation'] = 0.0
            else:
                print(f"警告: 没有负收益，{ticker} 的索提诺比率设为无穷大")
                self.risk_metrics[ticker]['sortino_ratio'] = float('inf')
                self.risk_metrics[ticker]['downside_deviation'] = 0.0
        except Exception as e:
            print(f"计算 {ticker} 索提诺比率时出错: {str(e)}")
            self.risk_metrics[ticker]['sortino_ratio'] = None
            self.risk_metrics[ticker]['downside_deviation'] = None
    
    # 其他方法...

def run_analysis(tickers, start_date=None, end_date=None):
    """
    运行综合分析
    
    参数:
    tickers (list): 股票代码列表
    start_date (str): 起始日期，格式 'YYYY-MM-DD'
    end_date (str): 结束日期，格式 'YYYY-MM-DD'
    
    返回:
    ValuationRiskMonitor: 分析器实例
    """
    # 创建监测器实例
    monitor = ValuationRiskMonitor(tickers, start_date, end_date)
    
    # 下载数据
    monitor.download_data()
    
    # 计算风险指标
    monitor.calculate_risk_metrics()
    
    # 计算估值指标
    if hasattr(monitor, 'calculate_valuation_metrics'):
        monitor.calculate_valuation_metrics()
    
    # 打印结果
    print("\n分析结果:")
    for ticker in monitor.tickers:
        print(f"\n{ticker} 风险指标:")
        for metric, value in monitor.risk_metrics[ticker].items():
            print(f"  {metric}: {value:.4f}")
        
        if hasattr(monitor, 'valuation_metrics') and ticker in monitor.valuation_metrics:
            print(f"\n{ticker} 估值指标:")
            for metric, value in monitor.valuation_metrics[ticker].items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
    
    return monitor

def run_analysis_text_only_simple(tickers, start_date=None, end_date=None):
    """
    运行简化版的文本分析，返回JSON格式的风险分析结果
    
    参数:
    tickers (list or str): 股票代码列表或单个股票代码字符串
    start_date (str): 起始日期，格式 'YYYY-MM-DD'
    end_date (str): 结束日期，格式 'YYYY-MM-DD'
    
    返回:
    dict: 包含风险分析结果的JSON对象
    """
    # 如果tickers是字符串，将其转换为列表
    if isinstance(tickers, str):
        tickers = [ticker.strip() for ticker in tickers.split(',') if ticker.strip()]
    
    # 创建监测器实例
    monitor = ValuationRiskMonitor(tickers, start_date, end_date)
    
    try:
        # 下载数据
        monitor.download_data()
        
        # 计算风险指标
        risk_metrics = monitor.calculate_risk_metrics()
        
        # 收集第一个股票代码的结果（或唯一的一个）
        ticker = tickers[0] if tickers else None
        
        if not ticker or ticker not in risk_metrics:
            return {"error": "未能获取股票风险数据"}
        
        metrics = risk_metrics[ticker]
        
        # 创建结果字典
        result = {}
        
        # 波动率
        volatility = metrics.get('volatility')
        if volatility is not None:
            result["volatility"] = round(volatility * 100, 2)  # 转为百分比
            # 添加风险评级
            if volatility > 0.3:
                result["volatility_rating"] = "高"
            elif volatility < 0.15:
                result["volatility_rating"] = "低"
            else:
                result["volatility_rating"] = "中"
        
        # 最大回撤
        max_drawdown = metrics.get('max_drawdown')
        if max_drawdown is not None:
            result["max_drawdown"] = round(max_drawdown * 100, 2)  # 转为百分比
            # 添加风险评级
            if max_drawdown < -0.3:
                result["drawdown_rating"] = "高"
            elif max_drawdown > -0.1:
                result["drawdown_rating"] = "低"
            else:
                result["drawdown_rating"] = "中"
        
        # 贝塔系数
        beta = metrics.get('beta')
        if beta is not None and not np.isnan(beta):
            result["beta"] = round(beta, 2)
            # 添加风险评级
            if beta > 1.5:
                result["beta_rating"] = "高"
            elif beta < 0.5:
                result["beta_rating"] = "低"
            else:
                result["beta_rating"] = "中"
        
        # R方值
        r_squared = metrics.get('r_squared')
        if r_squared is not None:
            result["r_squared"] = round(r_squared, 2)
        
        # 系统性风险占比
        systematic_risk_pct = metrics.get('systematic_risk_pct')
        if systematic_risk_pct is not None:
            result["systematic_risk_pct"] = round(systematic_risk_pct * 100, 2)
        
        # 残差风险
        residual_risk = metrics.get('residual_risk')
        if residual_risk is not None:
            result["residual_risk"] = round(residual_risk * 100, 2)
        
        # 风险价值(VaR)
        var_95 = metrics.get('var_95')
        if var_95 is not None:
            result["var_95"] = round(var_95 * 100, 2)
            # 添加风险评级
            if var_95 < -0.03:
                result["var_rating"] = "高"
            elif var_95 > -0.015:
                result["var_rating"] = "低"
            else:
                result["var_rating"] = "中"
        
        # 夏普比率
        sharpe = metrics.get('sharpe_ratio')
        if sharpe is not None:
            result["sharpe_ratio"] = round(sharpe, 2)
            # 添加风险评级
            if sharpe > 1:
                result["sharpe_rating"] = "好"
            elif sharpe < 0:
                result["sharpe_rating"] = "差"
            else:
                result["sharpe_rating"] = "中"
        
        # 信息比率
        info_ratio = metrics.get('information_ratio')
        if info_ratio is not None:
            result["information_ratio"] = round(info_ratio, 2)
        
        # 特雷诺比率
        treynor = metrics.get('treynor_ratio')
        if treynor is not None:
            result["treynor_ratio"] = round(treynor, 2)
        
        # 索提诺比率
        sortino = metrics.get('sortino_ratio')
        if sortino is not None:
            if sortino == float('inf'):
                result["sortino_ratio"] = "∞"
            else:
                result["sortino_ratio"] = round(sortino, 2)
                # 添加风险评级
                if sortino > 1:
                    result["sortino_rating"] = "好"
                elif sortino < 0:
                    result["sortino_rating"] = "差"
                else:
                    result["sortino_rating"] = "中"
        
        # 下行偏差
        downside_dev = metrics.get('downside_deviation')
        if downside_dev is not None:
            result["downside_deviation"] = round(downside_dev * 100, 2)
        
        # 偏度和峰度
        skew = metrics.get('skewness')
        kurt = metrics.get('kurtosis')
        if skew is not None:
            result["skewness"] = round(skew, 2)
        if kurt is not None:
            result["kurtosis"] = round(kurt, 2)
        
        # 添加风险评估总结
        result["risk_summary"] = []
        
        # 总体风险水平
        if volatility is not None:
            if volatility > 0.3:
                result["risk_summary"].append("高波动性股票，总体风险较高")
                result["overall_risk"] = "高"
            elif volatility < 0.15:
                result["risk_summary"].append("低波动性股票，总体风险较低")
                result["overall_risk"] = "低"
            else:
                result["risk_summary"].append("中等波动性股票")
                result["overall_risk"] = "中"
        
        # 市场相关性
        if beta is not None and r_squared is not None:
            if beta > 1.2 and r_squared > 0.6:
                result["risk_summary"].append("与市场高度相关且放大市场波动")
            elif beta < 0.8 and r_squared > 0.6:
                result["risk_summary"].append("与市场高度相关但波动较小")
            elif r_squared < 0.3:
                result["risk_summary"].append("与市场相关性低，可能具有良好的分散化效果")
        
        # 风险调整回报
        if sharpe is not None and sortino is not None:
            if sharpe > 1 and sortino > 1:
                result["risk_summary"].append("风险调整回报优秀")
                result["risk_adjusted_return"] = "好"
            elif sharpe < 0 and sortino < 0:
                result["risk_summary"].append("风险调整回报不佳")
                result["risk_adjusted_return"] = "差"
            else:
                result["risk_summary"].append("风险调整回报一般")
                result["risk_adjusted_return"] = "中"
        
        # 极端风险
        if var_95 is not None and max_drawdown is not None and kurt is not None:
            if var_95 < -0.03 and max_drawdown < -0.2 and kurt > 3:
                result["risk_summary"].append("存在显著的极端风险，需要谨慎")
                result["extreme_risk"] = "高"
            elif var_95 > -0.015 and max_drawdown > -0.1:
                result["risk_summary"].append("极端风险相对较低")
                result["extreme_risk"] = "低"
            else:
                result["extreme_risk"] = "中"
        
        return result
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        trace = traceback.format_exc()
        print(f"分析过程中出错: {error_msg}")
        print(trace)
        return {
            "error": f"分析过程中出错: {error_msg}",
            "details": trace
        }

# 测试函数
def test_risk_analysis():
    """测试风险分析功能"""
    tickers = ["AAPL", "MSFT"]
    start_date = (dt.datetime.now() - dt.timedelta(days=365)).strftime('%Y-%m-%d')
    
    try:
        monitor = run_analysis_text_only_simple(tickers, start_date)
        if monitor:
            print("\n风险分析测试成功!")
            return True
        else:
            print("\n风险分析测试失败!")
            return False
    except Exception as e:
        print(f"\n风险分析测试失败: {str(e)}")
        return False 