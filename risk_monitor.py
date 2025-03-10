import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import datetime as dt

class ValuationRiskMonitor:
    def __init__(self, tickers, start_date=None, end_date=None, benchmark_ticker="^GSPC"):
        """
        初始化估值和风险监测系统
        
        参数:
        tickers (list): 股票代码列表
        start_date (str): 起始日期，格式 'YYYY-MM-DD'
        end_date (str): 结束日期，格式 'YYYY-MM-DD'
        benchmark_ticker (str): 基准指数，默认为S&P 500
        """
        self.tickers = tickers if isinstance(tickers, list) else [tickers]
        self.start_date = start_date if start_date else (dt.datetime.now() - dt.timedelta(days=365*3)).strftime('%Y-%m-%d')
        self.end_date = end_date if end_date else dt.datetime.now().strftime('%Y-%m-%d')
        self.benchmark_ticker = benchmark_ticker
        self.stock_data = {}
        self.fundamentals = {}
        self.risk_metrics = {}
        self.valuation_metrics = {}
        self.benchmark_data = None
        
    def download_data(self):
        """下载股票数据和基准数据"""
        print("正在下载市场数据...")
        # 下载股票价格数据
        for ticker in self.tickers:
            self.stock_data[ticker] = yf.download(ticker, start=self.start_date, end=self.end_date)
            print(f"已下载 {ticker} 的历史价格数据")
            
        # 下载基准数据
        self.benchmark_data = yf.download(self.benchmark_ticker, start=self.start_date, end=self.end_date)
        print(f"已下载 {self.benchmark_ticker} 的基准数据")
        
        # 获取基本面数据
        self._get_fundamentals()
        
        return self.stock_data
    
    def _get_fundamentals(self):
        """获取股票的基本面数据"""
        print("正在获取基本面数据...")
        for ticker in self.tickers:
            stock = yf.Ticker(ticker)
            # 获取财务报表
            try:
                self.fundamentals[ticker] = {
                    'info': stock.info,
                    'balance_sheet': stock.balance_sheet,
                    'income_stmt': stock.income_stmt,
                    'cash_flow': stock.cashflow,
                    'earnings': stock.earnings
                }
                print(f"已获取 {ticker} 的基本面数据")
            except Exception as e:
                print(f"获取 {ticker} 的基本面数据时出错: {e}")
                
    def calculate_valuation_metrics(self):
        """计算各种估值指标"""
        print("正在计算估值指标...")
        for ticker in self.tickers:
            try:
                info = self.fundamentals[ticker]['info']
                self.valuation_metrics[ticker] = {
                    'pe_ratio': info.get('trailingPE', np.nan),
                    'forward_pe': info.get('forwardPE', np.nan),
                    'price_to_book': info.get('priceToBook', np.nan),
                    'price_to_sales': info.get('priceToSalesTrailing12Months', np.nan),
                    'ev_to_ebitda': info.get('enterpriseToEbitda', np.nan),
                    'peg_ratio': info.get('pegRatio', np.nan),
                    'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                    'market_cap': info.get('marketCap', np.nan),
                }
                
                # 计算历史市盈率变化
                if ('earnings' in self.fundamentals[ticker] and 
                    self.fundamentals[ticker]['earnings'] is not None and 
                    not isinstance(self.fundamentals[ticker]['earnings'], type(None)) and 
                    hasattr(self.fundamentals[ticker]['earnings'], 'empty') and 
                    not self.fundamentals[ticker]['earnings'].empty):
                    
                    earnings = self.fundamentals[ticker]['earnings']
                    if 'Earnings' in earnings.columns:
                        prices = self.stock_data[ticker]['Close'].resample('Y').last()
                        merged_data = pd.DataFrame({
                            'Price': prices,
                            'EPS': earnings['Earnings'].values[:len(prices)]
                        })
                        merged_data = merged_data.dropna()
                        if not merged_data.empty:
                            merged_data['PE'] = merged_data['Price'] / merged_data['EPS']
                            self.valuation_metrics[ticker]['historical_pe'] = merged_data['PE'].tolist()
                            self.valuation_metrics[ticker]['historical_pe_mean'] = merged_data['PE'].mean()
                            self.valuation_metrics[ticker]['historical_pe_median'] = merged_data['PE'].median()
                
                print(f"已计算 {ticker} 的估值指标")
            except Exception as e:
                print(f"计算 {ticker} 的估值指标时出错: {e}")
                self.valuation_metrics[ticker] = {
                    'pe_ratio': np.nan,
                    'forward_pe': np.nan,
                    'price_to_book': np.nan,
                    'price_to_sales': np.nan,
                    'ev_to_ebitda': np.nan,
                    'peg_ratio': np.nan,
                    'dividend_yield': 0,
                    'market_cap': np.nan
                }
                
        return self.valuation_metrics
    
    def calculate_risk_metrics(self, window=252):
        """
        计算风险指标
        
        参数:
        window (int): 计算波动率和贝塔系数的窗口大小，默认为252（一年交易日）
        """
        print("正在计算风险指标...")
        for ticker in self.tickers:
            try:
                # 确保数据足够
                if len(self.stock_data[ticker]) < window:
                    print(f"警告: {ticker} 的数据不足 {window} 天，使用可用的所有数据")
                    window = min(len(self.stock_data[ticker]), window)
                
                # 检查是否有 'Adj Close' 列，如果没有则使用 'Close' 列
                price_col = 'Adj Close' if 'Adj Close' in self.stock_data[ticker].columns else 'Close'
                benchmark_price_col = 'Adj Close' if 'Adj Close' in self.benchmark_data.columns else 'Close'
                
                # 计算每日收益率
                stock_prices = self.stock_data[ticker][price_col]
                benchmark_prices = self.benchmark_data[benchmark_price_col]
                
                # 确保日期对齐
                common_dates = stock_prices.index.intersection(benchmark_prices.index)
                stock_prices = stock_prices.loc[common_dates]
                benchmark_prices = benchmark_prices.loc[common_dates]
                
                # 计算收益率
                stock_returns = stock_prices.pct_change().dropna()
                benchmark_returns = benchmark_prices.pct_change().dropna()
                
                # 确保收益率日期对齐
                common_dates = stock_returns.index.intersection(benchmark_returns.index)
                stock_returns = stock_returns.loc[common_dates]
                benchmark_returns = benchmark_returns.loc[common_dates]
                
                # 转换为numpy数组以避免Series比较问题
                stock_returns_array = stock_returns.values
                benchmark_returns_array = benchmark_returns.values
                
                # 计算波动率
                daily_std = np.std(stock_returns_array)
                annual_volatility = daily_std * np.sqrt(252)
                
                # 计算贝塔系数
                if len(stock_returns_array) > 1 and len(benchmark_returns_array) > 1:
                    cov = np.cov(stock_returns_array, benchmark_returns_array)[0, 1]
                    var = np.var(benchmark_returns_array)
                    beta = cov / var if var != 0 else np.nan
                else:
                    beta = np.nan
                
                # 计算阿尔法和R²
                if len(stock_returns_array) > 1 and len(benchmark_returns_array) > 1:
                    # 计算均值
                    x_mean = np.mean(benchmark_returns_array)
                    y_mean = np.mean(stock_returns_array)
                    
                    # 计算beta和alpha (y = alpha + beta * x)
                    xy_cov = np.sum((benchmark_returns_array - x_mean) * (stock_returns_array - y_mean)) / len(benchmark_returns_array)
                    x_var = np.sum((benchmark_returns_array - x_mean) ** 2) / len(benchmark_returns_array)
                    beta_reg = xy_cov / x_var if x_var != 0 else np.nan
                    alpha = y_mean - beta_reg * x_mean if not np.isnan(beta_reg) else np.nan
                    
                    # 计算R²
                    if not np.isnan(alpha) and not np.isnan(beta_reg):
                        y_pred = alpha + beta_reg * benchmark_returns_array
                        ss_total = np.sum((stock_returns_array - y_mean) ** 2)
                        ss_residual = np.sum((stock_returns_array - y_pred) ** 2)
                        r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else np.nan
                    else:
                        r_squared = np.nan
                else:
                    alpha = np.nan
                    beta_reg = np.nan
                    r_squared = np.nan
                
                # 计算夏普比率
                risk_free_rate = 0.02
                annual_return = np.mean(stock_returns_array) * 252
                sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility != 0 else np.nan
                
                # 计算最大回撤
                cum_returns = (1 + stock_returns).cumprod()
                running_max = cum_returns.cummax()
                drawdown = (cum_returns / running_max) - 1
                max_drawdown = drawdown.min()
                
                # 计算Value at Risk (VaR)
                var_95 = np.percentile(stock_returns_array, 5) * np.sqrt(252)
                var_99 = np.percentile(stock_returns_array, 1) * np.sqrt(252)
                
                # 计算滚动波动率
                rolling_vol = stock_returns.rolling(window=min(20, len(stock_returns))).std() * np.sqrt(252)
                
                # 存储风险指标
                self.risk_metrics[ticker] = {
                    'annual_volatility': annual_volatility,
                    'beta': beta,
                    'beta_reg': beta_reg,
                    'alpha_annualized': alpha * 252 if not np.isnan(alpha) else np.nan,
                    'r_squared': r_squared,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'var_95': var_95,
                    'var_99': var_99,
                    'rolling_volatility': rolling_vol,
                    'rolling_beta': pd.Series(index=stock_returns.index)  # 初始化为空Series
                }
                
                print(f"已计算 {ticker} 的风险指标")
            except Exception as e:
                print(f"计算 {ticker} 的风险指标时出错: {e}")
                self.risk_metrics[ticker] = {
                    'annual_volatility': np.nan,
                    'beta': np.nan,
                    'beta_reg': np.nan,
                    'alpha_annualized': np.nan,
                    'r_squared': np.nan,
                    'sharpe_ratio': np.nan,
                    'max_drawdown': np.nan,
                    'var_95': np.nan,
                    'var_99': np.nan,
                    'rolling_volatility': pd.Series(),
                    'rolling_beta': pd.Series()
                }
                
        return self.risk_metrics
    
    def generate_valuation_report(self, sector_comparison=False):
        """
        生成估值报告
        
        参数:
        sector_comparison (bool): 是否与行业比较
        """
        if not self.valuation_metrics:
            self.calculate_valuation_metrics()
            
        report = pd.DataFrame()
        
        for ticker in self.tickers:
            metrics = self.valuation_metrics[ticker]
            ticker_report = pd.DataFrame([metrics], index=[ticker])
            report = pd.concat([report, ticker_report])
        
        if sector_comparison:
            # 获取每个股票的行业
            sectors = {}
            for ticker in self.tickers:
                try:
                    sectors[ticker] = self.fundamentals[ticker]['info'].get('sector', 'Unknown')
                except:
                    sectors[ticker] = 'Unknown'
            
            # 添加行业信息
            report['Sector'] = [sectors.get(ticker, 'Unknown') for ticker in report.index]
            
            # 对每个指标计算行业平均值
            sector_avg = {}
            for sector in set(sectors.values()):
                sector_stocks = [t for t, s in sectors.items() if s == sector]
                if len(sector_stocks) > 1:  # 需要至少两只股票来计算平均值
                    sector_data = report.loc[sector_stocks].drop('Sector', axis=1)
                    sector_avg[sector] = sector_data.mean()
            
            # 计算每只股票与行业平均的差异
            for ticker in self.tickers:
                sector = sectors.get(ticker, 'Unknown')
                if sector in sector_avg:
                    for metric in ['pe_ratio', 'price_to_book', 'price_to_sales', 'ev_to_ebitda']:
                        if metric in report.columns:
                            diff_col = f"{metric}_vs_sector"
                            report.loc[ticker, diff_col] = report.loc[ticker, metric] / sector_avg[sector][metric] - 1
        
        return report
    
    def generate_risk_report(self):
        """生成风险报告"""
        if not self.risk_metrics:
            self.calculate_risk_metrics()
            
        report = pd.DataFrame()
        
        for ticker in self.tickers:
            metrics = {k: v for k, v in self.risk_metrics[ticker].items() if not isinstance(v, pd.Series)}
            ticker_report = pd.DataFrame([metrics], index=[ticker])
            report = pd.concat([report, ticker_report])
        
        return report
    
    def plot_valuation_comparison(self):
        """绘制估值比较图"""
        if not self.valuation_metrics:
            self.calculate_valuation_metrics()
            
        metrics_to_plot = ['pe_ratio', 'price_to_book', 'price_to_sales', 'ev_to_ebitda']
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        for i, metric in enumerate(metrics_to_plot):
            # 获取数据并替换 NaN 值为 0
            data = []
            for ticker in self.tickers:
                value = self.valuation_metrics[ticker].get(metric, np.nan)
                data.append(0 if pd.isna(value) else value)
            
            axes[i].bar(self.tickers, data)
            axes[i].set_title(f'Comparison of {metric.replace("_", " ").title()}')
            axes[i].set_ylabel(metric.replace("_", " ").title())
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return fig
    
    def plot_risk_comparison(self):
        """绘制风险比较图"""
        if not self.risk_metrics:
            self.calculate_risk_metrics()
            
        metrics_to_plot = ['annual_volatility', 'beta', 'sharpe_ratio', 'max_drawdown']
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        for i, metric in enumerate(metrics_to_plot):
            # 获取数据并替换 NaN 值为 0
            data = []
            for ticker in self.tickers:
                value = self.risk_metrics[ticker].get(metric, np.nan)
                if isinstance(value, pd.Series):
                    value = value.mean() if not value.empty else 0
                data.append(0 if pd.isna(value) else value)
            
            axes[i].bar(self.tickers, data)
            axes[i].set_title(f'Comparison of {metric.replace("_", " ").title()}')
            axes[i].set_ylabel(metric.replace("_", " ").title())
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return fig
    
    def plot_rolling_metrics(self, ticker):
        """
        绘制滚动风险指标
        
        参数:
        ticker (str): 股票代码
        """
        if ticker not in self.risk_metrics:
            raise ValueError(f"{ticker} 的风险指标尚未计算")
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # 绘制滚动波动率
        if 'rolling_volatility' in self.risk_metrics[ticker]:
            rolling_vol = self.risk_metrics[ticker]['rolling_volatility']
            if isinstance(rolling_vol, pd.Series) and not rolling_vol.empty and rolling_vol.notna().any():
                rolling_vol.plot(ax=axes[0])
                axes[0].set_title(f'{ticker} 20日滚动波动率（年化）')
                axes[0].set_ylabel('波动率')
                
                annual_vol = self.risk_metrics[ticker].get('annual_volatility', np.nan)
                if not pd.isna(annual_vol):
                    axes[0].axhline(y=annual_vol, color='r', linestyle='--', 
                                   label=f'平均波动率: {annual_vol:.2f}')
                axes[0].legend()
        
        # 绘制滚动贝塔
        if 'rolling_beta' in self.risk_metrics[ticker]:
            rolling_beta = self.risk_metrics[ticker]['rolling_beta']
            if isinstance(rolling_beta, pd.Series) and not rolling_beta.empty and rolling_beta.notna().any():
                rolling_beta.plot(ax=axes[1])
                axes[1].set_title(f'{ticker} 252日滚动贝塔系数')
                axes[1].set_ylabel('贝塔系数')
                
                beta = self.risk_metrics[ticker].get('beta', np.nan)
                if not pd.isna(beta):
                    axes[1].axhline(y=beta, color='r', linestyle='--', 
                                   label=f'平均贝塔: {beta:.2f}')
                axes[1].legend()
        
        plt.tight_layout()
        return fig
    
    def calculate_intrinsic_value(self, ticker, growth_rate=0.05, years=5, terminal_growth=0.02, discount_rate=0.08):
        """
        使用简化的DCF模型计算内在价值
        
        参数:
        ticker (str): 股票代码
        growth_rate (float): 预期年增长率
        years (int): 预测年数
        terminal_growth (float): 永续增长率
        discount_rate (float): 折现率
        
        返回:
        float: 每股内在价值估计
        """
        try:
            # 获取基本数据
            info = self.fundamentals[ticker]['info']
            income = self.fundamentals[ticker]['income_stmt']
            
            # 获取最新的EPS、自由现金流或净利润
            eps = info.get('trailingEPS')
            
            if pd.isna(eps) or eps is None:
                # 尝试从收入报表计算
                if not income.empty and 'Net Income' in income.columns:
                    net_income = income.loc['Net Income'].iloc[0]
                    shares_outstanding = info.get('sharesOutstanding')
                    if shares_outstanding:
                        eps = net_income / shares_outstanding
                    else:
                        return np.nan
                else:
                    return np.nan
            
            # 计算内在价值
            value = 0
            for year in range(1, years + 1):
                # 每年现金流增长
                future_eps = eps * (1 + growth_rate) ** year
                # 折现到现值
                present_value = future_eps / (1 + discount_rate) ** year
                value += present_value
            
            # 计算终值
            terminal_value = (eps * (1 + growth_rate) ** years * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            terminal_value_present = terminal_value / (1 + discount_rate) ** years
            
            # 总内在价值
            intrinsic_value = value + terminal_value_present
            
            return intrinsic_value
        except Exception as e:
            print(f"计算 {ticker} 的内在价值时出错: {e}")
            return np.nan
    
    def generate_valuation_alert(self, threshold=0.2):
        """
        生成估值警报
        
        参数:
        threshold (float): 触发警报的阈值
        
        返回:
        dict: 包含警报信息的字典
        """
        if not self.valuation_metrics:
            self.calculate_valuation_metrics()
            
        valuation_report = self.generate_valuation_report(sector_comparison=True)
        alerts = {}
        
        for ticker in self.tickers:
            ticker_alerts = []
            
            # 检查PE与历史均值的差异
            if 'historical_pe_mean' in self.valuation_metrics[ticker] and 'pe_ratio' in self.valuation_metrics[ticker]:
                hist_pe = self.valuation_metrics[ticker]['historical_pe_mean']
                current_pe = self.valuation_metrics[ticker]['pe_ratio']
                if not pd.isna(hist_pe) and not pd.isna(current_pe):
                    pe_diff = current_pe / hist_pe - 1
                    if abs(pe_diff) > threshold:
                        status = '偏高' if pe_diff > 0 else '偏低'
                        ticker_alerts.append(f"当前PE比历史均值{status} {abs(pe_diff):.1%}")
            
            # 检查与行业平均的差异
            for metric in ['pe_ratio_vs_sector', 'price_to_book_vs_sector', 'price_to_sales_vs_sector', 'ev_to_ebitda_vs_sector']:
                if metric in valuation_report.columns and not pd.isna(valuation_report.loc[ticker, metric]):
                    diff = valuation_report.loc[ticker, metric]
                    if abs(diff) > threshold:
                        base_metric = metric.split('_vs_sector')[0]
                        status = '偏高' if diff > 0 else '偏低'
                        ticker_alerts.append(f"{base_metric.replace('_', ' ').title()}比行业平均{status} {abs(diff):.1%}")
            
            # 计算内在价值并比较
            current_price = self.stock_data[ticker]['Close'].iloc[-1]
            intrinsic_value = self.calculate_intrinsic_value(ticker)
            
            if not pd.isna(intrinsic_value):
                price_to_value = current_price / intrinsic_value
                if abs(price_to_value - 1) > threshold:
                    status = '高估' if price_to_value > 1 else '低估'
                    ticker_alerts.append(f"当前价格比估计内在价值{status} {abs(price_to_value - 1):.1%}")
            
            if ticker_alerts:
                alerts[ticker] = ticker_alerts
                
        return alerts
    
    def generate_risk_alert(self, volatility_threshold=0.3, beta_threshold=0.3, max_drawdown_threshold=-0.2):
        """
        生成风险警报
        
        参数:
        volatility_threshold (float): 波动率警报阈值
        beta_threshold (float): 贝塔系数警报阈值
        max_drawdown_threshold (float): 最大回撤警报阈值
        
        返回:
        dict: 包含警报信息的字典
        """
        if not self.risk_metrics:
            self.calculate_risk_metrics()
            
        alerts = {}
        
        for ticker in self.tickers:
            ticker_alerts = []
            metrics = self.risk_metrics[ticker]
            
            # 检查波动率
            annual_volatility = metrics.get('annual_volatility', np.nan)
            if not np.isnan(annual_volatility) and annual_volatility > volatility_threshold:
                ticker_alerts.append(f"年化波动率高: {annual_volatility:.1%}")
            
            # 检查贝塔系数
            beta = metrics.get('beta', np.nan)
            if not np.isnan(beta) and abs(beta - 1) > beta_threshold:
                status = '高' if beta > 1 else '低'
                ticker_alerts.append(f"贝塔系数{status}: {beta:.2f}")
            
            # 检查最大回撤
            max_drawdown = metrics.get('max_drawdown', np.nan)
            if isinstance(max_drawdown, (int, float)) and not np.isnan(max_drawdown) and max_drawdown < max_drawdown_threshold:
                ticker_alerts.append(f"最大回撤较大: {max_drawdown:.1%}")
            
            # 检查VaR
            var_95 = metrics.get('var_95', np.nan)
            var_99 = metrics.get('var_99', np.nan)
            if not np.isnan(var_95):
                ticker_alerts.append(f"95%置信区间VaR: {abs(var_95):.1%}")
            if not np.isnan(var_99):
                ticker_alerts.append(f"99%置信区间VaR: {abs(var_99):.1%}")
            
            if ticker_alerts:
                alerts[ticker] = ticker_alerts
                
        return alerts
    
    def run_comprehensive_analysis(self):
        """运行综合分析并返回完整报告"""
        # 下载数据
        self.download_data()
        
        # 计算指标
        self.calculate_valuation_metrics()
        self.calculate_risk_metrics()
        
        # 生成报告
        valuation_report = self.generate_valuation_report(sector_comparison=True)
        risk_report = self.generate_risk_report()
        valuation_alerts = self.generate_valuation_alert()
        risk_alerts = self.generate_risk_alert()
        
        # 返回结果
        return {
            'valuation_report': valuation_report,
            'risk_report': risk_report,
            'valuation_alerts': valuation_alerts,
            'risk_alerts': risk_alerts
        }

# 示例用法
def run_analysis(tickers, start_date=None, end_date=None):
    """
    运行完整分析并显示结果
    
    参数:
    tickers (list): 股票代码列表
    start_date (str): 起始日期，格式 'YYYY-MM-DD'
    end_date (str): 结束日期，格式 'YYYY-MM-DD'
    """
    monitor = ValuationRiskMonitor(tickers, start_date, end_date)
    results = monitor.run_comprehensive_analysis()
    
    print("=" * 50)
    print("估值报告:")
    print(results['valuation_report'])
    print("\n" + "=" * 50)
    print("风险报告:")
    print(results['risk_report'])
    
    print("\n" + "=" * 50)
    print("估值警报:")
    for ticker, alerts in results['valuation_alerts'].items():
        print(f"\n{ticker}:")
        for alert in alerts:
            print(f"  - {alert}")
    
    print("\n" + "=" * 50)
    print("风险警报:")
    for ticker, alerts in results['risk_alerts'].items():
        print(f"\n{ticker}:")
        for alert in alerts:
            print(f"  - {alert}")
    
    # 绘制图表
    monitor.plot_valuation_comparison()
    monitor.plot_risk_comparison()
    
    # 为每个股票绘制滚动指标
    for ticker in tickers:
        monitor.plot_rolling_metrics(ticker)
    
    plt.show()
    
    return monitor

def run_analysis_text_only_simple(tickers, start_date=None, end_date=None):
    """
    运行完整分析并仅显示简化的文本结果，不生成图表
    
    参数:
    tickers (list或str): 股票代码列表或逗号分隔的字符串
    start_date (str): 起始日期，格式 'YYYY-MM-DD'
    end_date (str): 结束日期，格式 'YYYY-MM-DD'
    
    返回:
    dict: 包含分析结果的结构化数据
    """
    # 确保tickers是列表
    if isinstance(tickers, str):
        tickers = [ticker.strip().upper() for ticker in tickers.split(',') if ticker.strip()]
    
    # 打印开始分析的信息
    print(f"开始分析股票: {', '.join(tickers)}")
    print(f"分析时间范围: {start_date} 至 {end_date}")
    
    try:
        # 创建监控对象
        monitor = ValuationRiskMonitor(tickers, start_date, end_date)
        
        # 运行综合分析
        results = monitor.run_comprehensive_analysis()
        
        # 打印分析时间范围
        print("\n" + "=" * 80)
        print(f"分析时间范围: {monitor.start_date} 至 {monitor.end_date}")
        print("=" * 80)
        
        # 创建结构化结果
        structured_results = {}
        
        # 安全获取值的函数
        def safe_get(metrics, key):
            if key in metrics:
                value = metrics[key]
                if isinstance(value, (int, float)) and not isinstance(value, bool) and not pd.isna(value):
                    return value
            return None
        
        # 处理每只股票的详细指标
        for ticker in tickers:
            print(f"\n{ticker} 详细分析:")
            print("=" * 80)
            
            # 初始化股票结果
            structured_results[ticker] = {
                'name': monitor.fundamentals.get(ticker, {}).get('info', {}).get('shortName', ticker),
                'metrics': {
                    '估值指标': {},
                    '风险指标': {},
                    '内在价值': {}
                },
                'alerts': []
            }
            
            # 估值指标
            print("\n估值指标:")
            print("-" * 40)
            val_metrics = monitor.valuation_metrics.get(ticker, {})
            
            metrics_to_extract = [
                ('pe_ratio', '市盈率 (P/E)'),
                ('forward_pe', '预期市盈率'),
                ('price_to_book', '市净率 (P/B)'),
                ('price_to_sales', '市销率 (P/S)'),
                ('ev_to_ebitda', '企业价值/EBITDA'),
                ('dividend_yield', '股息收益率'),
                ('market_cap', '市值')
            ]
            
            for key, display_name in metrics_to_extract:
                value = safe_get(val_metrics, key)
                if value is not None:
                    # 特殊处理市值，转换为十亿
                    if key == 'market_cap':
                        value = value / 1e9
                        print(f"  {display_name}: ${value:.2f}B")
                    elif key == 'dividend_yield':
                        print(f"  {display_name}: {value:.2f}%")
                    else:
                        print(f"  {display_name}: {value:.2f}")
                    
                    # 添加到结构化结果
                    structured_results[ticker]['metrics']['估值指标'][display_name] = value
            
            # 风险指标
            print("\n风险指标:")
            print("-" * 40)
            risk_metrics = monitor.risk_metrics.get(ticker, {})
            
            risk_metrics_to_extract = [
                ('annual_volatility', '年化波动率'),
                ('beta', '贝塔系数'),
                ('beta_reg', '回归贝塔'),
                ('alpha_annualized', '年化阿尔法'),
                ('r_squared', 'R²'),
                ('sharpe_ratio', '夏普比率'),
                ('max_drawdown', '最大回撤'),
                ('var_95', '95%置信区间VaR'),
                ('var_99', '99%置信区间VaR')
            ]
            
            for key, display_name in risk_metrics_to_extract:
                value = safe_get(risk_metrics, key)
                if value is not None:
                    # 特殊处理百分比值
                    if key in ['annual_volatility', 'alpha_annualized', 'max_drawdown', 'var_95', 'var_99']:
                        print(f"  {display_name}: {value:.2%}")
                        # 存储为小数
                        structured_results[ticker]['metrics']['风险指标'][display_name] = abs(value) if 'VaR' in display_name else value
                    else:
                        print(f"  {display_name}: {value:.2f}")
                        structured_results[ticker]['metrics']['风险指标'][display_name] = value
            
            # 内在价值估计
            try:
                intrinsic_value = monitor.calculate_intrinsic_value(ticker)
                if isinstance(intrinsic_value, (int, float)) and not pd.isna(intrinsic_value):
                    current_price = monitor.stock_data[ticker]['Close'].iloc[-1]
                    price_to_value = current_price / intrinsic_value
                    print(f"\n内在价值估计:")
                    print("-" * 40)
                    print(f"  当前价格: ${current_price:.2f}")
                    print(f"  估计内在价值: ${intrinsic_value:.2f}")
                    print(f"  价格/价值比: {price_to_value:.2f}")
                    
                    # 添加到结构化结果
                    structured_results[ticker]['metrics']['内在价值']['当前价格'] = current_price
                    structured_results[ticker]['metrics']['内在价值']['估计内在价值'] = intrinsic_value
                    structured_results[ticker]['metrics']['内在价值']['价格/价值比'] = price_to_value
                    
                    if price_to_value > 1.2:
                        status = f"可能高估 ({(price_to_value-1)*100:.1f}%)"
                        print(f"  状态: {status}")
                        structured_results[ticker]['metrics']['内在价值']['状态'] = status
                    elif price_to_value < 0.8:
                        status = f"可能低估 ({(1-price_to_value)*100:.1f}%)"
                        print(f"  状态: {status}")
                        structured_results[ticker]['metrics']['内在价值']['状态'] = status
                    else:
                        print(f"  状态: 接近公允价值")
                        structured_results[ticker]['metrics']['内在价值']['状态'] = "接近公允价值"
            except Exception as e:
                print(f"\n内在价值估计: 无法计算 ({str(e)})")
            
            # 警报
            valuation_alerts = results['valuation_alerts'].get(ticker, [])
            risk_alerts = results['risk_alerts'].get(ticker, [])
            
            if valuation_alerts or risk_alerts:
                print("\n警报:")
                print("-" * 40)
                
                if valuation_alerts:
                    print("  估值警报:")
                    for alert in valuation_alerts:
                        print(f"    - {alert}")
                        structured_results[ticker]['alerts'].append(alert)
                
                if risk_alerts:
                    print("  风险警报:")
                    for alert in risk_alerts:
                        print(f"    - {alert}")
                        structured_results[ticker]['alerts'].append(alert)
        
        print("\n分析完成!")
        return structured_results
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"分析过程中出错: {str(e)}")
        print(error_details)
        raise

# 使用示例
if __name__ == "__main__":
    # 分析一组股票
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
    start_date = "2020-01-01"
    
    # 选择是否显示图表
    show_charts = False
    
    if show_charts:
        monitor = run_analysis(tickers, start_date)
    else:
        monitor = run_analysis_text_only_simple(tickers, start_date)