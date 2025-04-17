"""
Risk monitoring module
Used to monitor and analyze the risk and valuation of stocks
"""
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import datetime as dt

class ValuationRiskMonitor:
    """
    Valuation and risk monitoring system
    """
    def __init__(self, tickers, start_date=None, end_date=None, benchmark_ticker="^GSPC", min_data_points=60):
        """
        Initialize the valuation and risk monitoring system
        
        Parameters:
        tickers (list): list of stock codes
        start_date (str): start date, format 'YYYY-MM-DD'
        end_date (str): end date, format 'YYYY-MM-DD'
        benchmark_ticker (str): benchmark index, default is S&P 500
        min_data_points (int): minimum number of data points required to calculate beta
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
        """Download stock data and benchmark data"""
        print("Downloading market data...")
        
        # Check if there are valid stock codes
        if not self.tickers:
            print("No valid stock codes provided")
            return {}
        
        # Download stock price data
        for ticker in self.tickers:
            try:
                data = yf.download(ticker, start=self.start_date, end=self.end_date)
                
                # Check if data is obtained
                if data.empty:
                    print(f"Warning: cannot get data for {ticker}")
                    self.stock_data[ticker] = pd.DataFrame()  # 空数据框
                else:
                    self.stock_data[ticker] = data
                    print(f"Downloaded historical price data for {ticker}")
            except Exception as e:
                print(f"Error downloading data for {ticker}: {str(e)}")
                self.stock_data[ticker] = pd.DataFrame()  # 空数据框
        
        # Download benchmark data
        try:
            self.benchmark_data = yf.download(self.benchmark_ticker, start=self.start_date, end=self.end_date)
            if self.benchmark_data.empty:
                print(f"Warning: cannot get data for {self.benchmark_ticker}")
            else:
                print(f"Downloaded benchmark data for {self.benchmark_ticker}")
        except Exception as e:
            print(f"Error downloading benchmark data: {str(e)}")
            self.benchmark_data = pd.DataFrame()  # 空数据框
        
        # Get fundamental data
        self._get_fundamentals()
        
        return self.stock_data
    
    def _get_fundamentals(self):
        """Get fundamental data of stocks"""
        print("Getting fundamental data...")
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                # Get financial statements
                try:
                    # Get net income from income statement, replacing the deprecated earnings
                    income_stmt = stock.income_stmt if hasattr(stock, 'income_stmt') else pd.DataFrame()
                    net_income = None
                    if not income_stmt.empty and 'Net Income' in income_stmt.index:
                        net_income = income_stmt.loc['Net Income']
                    
                    self.fundamentals[ticker] = {
                        'info': stock.info if hasattr(stock, 'info') else {},
                        'balance_sheet': stock.balance_sheet if hasattr(stock, 'balance_sheet') else pd.DataFrame(),
                        'income_stmt': income_stmt,
                        'cash_flow': stock.cashflow if hasattr(stock, 'cashflow') else pd.DataFrame(),
                        'net_income': net_income  # Use net income extracted from income_stmt instead of earnings
                    }
                    print(f"Got fundamental data for {ticker}")
                except Exception as e:
                    print(f"Error getting fundamental data for {ticker}: {e}")
                    # Provide empty fundamental data structure
                    self.fundamentals[ticker] = {
                        'info': {},
                        'balance_sheet': pd.DataFrame(),
                        'income_stmt': pd.DataFrame(),
                        'cash_flow': pd.DataFrame(),
                        'net_income': None
                    }
            except Exception as e:
                print(f"Error creating Ticker object for {ticker}: {e}")
                # Provide empty fundamental data structure
                self.fundamentals[ticker] = {
                    'info': {},
                    'balance_sheet': pd.DataFrame(),
                    'income_stmt': pd.DataFrame(),
                    'cash_flow': pd.DataFrame(),
                    'net_income': None
                }
    
    def calculate_risk_metrics(self):
        """Calculate risk metrics"""
        print("Calculating risk metrics...")
        for ticker in self.tickers:
            try:
                # Check if there is enough data
                if ticker not in self.stock_data or self.stock_data[ticker].empty or len(self.stock_data[ticker]) < 2:
                    print(f"Warning: {ticker} has insufficient price data, cannot calculate risk metrics")
                    self.risk_metrics[ticker] = {
                        'data_available': False,
                        'error_message': 'Insufficient price data'
                    }
                    continue
                
                # Calculate returns
                returns = self.stock_data[ticker]['Close'].pct_change().dropna()
                
                # Check benchmark data
                if self.benchmark_data is None or self.benchmark_data.empty or len(self.benchmark_data) < 2:
                    print(f"Warning: insufficient benchmark data, cannot calculate beta for {ticker}")
                    benchmark_returns = None
                else:
                    benchmark_returns = self.benchmark_data['Close'].pct_change().dropna()
                
                # Initialize risk metrics dictionary
                self.risk_metrics[ticker] = {
                    'data_available': True
                }
                
                # Calculate volatility
                volatility = returns.std() * np.sqrt(252)
                # Fix float conversion for single element Series
                self.risk_metrics[ticker]['volatility'] = float(volatility.item()) if hasattr(volatility, 'item') else float(volatility)
                
                # Calculate Sharpe ratio - handle division by zero case
                # Use .item() method to get scalar value
                returns_std = returns.std().item() if hasattr(returns.std(), 'item') else returns.std()
                returns_mean = returns.mean().item() if hasattr(returns.mean(), 'item') else returns.mean()
                
                if returns_std > 0:
                    sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252)
                    # Fix float conversion for single element Series
                    self.risk_metrics[ticker]['sharpe_ratio'] = float(sharpe_ratio) if isinstance(sharpe_ratio, (np.float64, np.float32)) else sharpe_ratio
                else:
                    print(f"Warning: {ticker} has a standard deviation of 0, cannot calculate Sharpe ratio")
                    self.risk_metrics[ticker]['sharpe_ratio'] = 0.0
                
                # Calculate maximum drawdown
                try:
                    max_drawdown = self._calculate_max_drawdown(self.stock_data[ticker]['Close'])
                    self.risk_metrics[ticker]['max_drawdown'] = float(max_drawdown) if max_drawdown is not None else None
                except Exception as e:
                    print(f"Error calculating max drawdown for {ticker}: {str(e)}")
                    self.risk_metrics[ticker]['max_drawdown'] = None
                
                # Calculate VaR
                if len(returns) >= 5:
                    var_95 = np.percentile(returns, 5)
                    var_99 = np.percentile(returns, 1)
                    # Fix float conversion for single element Series
                    self.risk_metrics[ticker]['var_95'] = float(var_95.item()) if hasattr(var_95, 'item') else float(var_95)
                    self.risk_metrics[ticker]['var_99'] = float(var_99.item()) if hasattr(var_99, 'item') else float(var_99)
                else:
                    print(f"Warning: {ticker} has insufficient data, cannot calculate reliable VaR")
                    self.risk_metrics[ticker]['var_95'] = None
                    self.risk_metrics[ticker]['var_99'] = None
                
                # Calculate skewness and kurtosis
                if len(returns) > 3:  # Need at least 4 data points
                    skewness = stats.skew(returns)
                    kurtosis = stats.kurtosis(returns)
                    # Fix float conversion for single element Series
                    self.risk_metrics[ticker]['skewness'] = float(skewness.item()) if hasattr(skewness, 'item') else float(skewness)
                    self.risk_metrics[ticker]['kurtosis'] = float(kurtosis.item()) if hasattr(kurtosis, 'item') else float(kurtosis)
                else:
                    print(f"Warning: {ticker} has insufficient data, cannot calculate skewness and kurtosis")
                    self.risk_metrics[ticker]['skewness'] = None
                    self.risk_metrics[ticker]['kurtosis'] = None
                
                # Calculate beta coefficient - improved version
                self._calculate_beta(ticker, returns, benchmark_returns)
                
                # Calculate information ratio
                self._calculate_information_ratio(ticker, returns, benchmark_returns)
                
                # Calculate Treynor ratio
                self._calculate_treynor_ratio(ticker, returns, benchmark_returns)
                
                # Calculate Sortino ratio
                self._calculate_sortino_ratio(ticker, returns)
                
            except Exception as e:
                print(f"Error calculating risk metrics for {ticker}: {str(e)}")
                self.risk_metrics[ticker] = {
                    'data_available': False,
                    'error_message': f'Error calculating risk metrics: {str(e)}'
                }
                
        return self.risk_metrics
    
    def _calculate_max_drawdown(self, price_series):
        """Calculate maximum drawdown"""
        try:
            if price_series.empty or len(price_series) < 2:
                print("Price series is empty or insufficient data, cannot calculate max drawdown")
                return None
            
            roll_max = price_series.cummax()
            drawdown = (price_series / roll_max - 1)
            min_drawdown = drawdown.min()
            # Fix float conversion for single element Series
            return float(min_drawdown.item()) if hasattr(min_drawdown, 'item') else float(min_drawdown)
        except Exception as e:
            print(f"Error calculating max drawdown: {str(e)}")
            return None
    
    def _calculate_beta(self, ticker, returns, benchmark_returns):
        """
        Calculate beta coefficient - improved version
        
        Parameters:
        ticker (str): stock code
        returns (Series): stock return series
        benchmark_returns (Series): benchmark index return series
        """
        if benchmark_returns is None or len(returns) < self.min_data_points or len(benchmark_returns) < self.min_data_points:
            print(f"Warning: insufficient data points, {self.min_data_points}, cannot calculate beta for {ticker}")
            self.risk_metrics[ticker]['beta'] = None
            self.risk_metrics[ticker]['r_squared'] = None
            self.risk_metrics[ticker]['residual_risk'] = None
            self.risk_metrics[ticker]['systematic_risk_pct'] = None
            return
        
        try:
            # Ensure two sequences have the same index
            common_index = returns.index.intersection(benchmark_returns.index)
            if len(common_index) < self.min_data_points:
                print(f"Warning: insufficient common data points, {self.min_data_points}, cannot calculate beta for {ticker}")
                self.risk_metrics[ticker]['beta'] = None
                self.risk_metrics[ticker]['r_squared'] = None
                self.risk_metrics[ticker]['residual_risk'] = None
                self.risk_metrics[ticker]['systematic_risk_pct'] = None
                return
            
            # Align data
            stock_returns_aligned = returns.loc[common_index]
            benchmark_returns_aligned = benchmark_returns.loc[common_index]
            
            # Use numpy to calculate covariance and variance, avoid DataFrame and Series comparison issues
            stock_returns_np = stock_returns_aligned.values
            benchmark_returns_np = benchmark_returns_aligned.values
            
            # Calculate covariance and variance
            cov_matrix = np.cov(stock_returns_np, benchmark_returns_np, ddof=1)
            if cov_matrix.shape == (2, 2):
                covariance = cov_matrix[0, 1]
                benchmark_variance = np.var(benchmark_returns_np, ddof=1)
                
                # Check if variance is zero
                if benchmark_variance > 0:
                    beta = covariance / benchmark_variance
                    self.risk_metrics[ticker]['beta'] = float(beta)
                    
                    # Calculate R-squared value (coefficient of determination)
                    correlation = np.corrcoef(stock_returns_np, benchmark_returns_np)[0, 1]
                    r_squared = correlation ** 2
                    self.risk_metrics[ticker]['r_squared'] = float(r_squared)
                    
                    # Calculate residual risk (specific risk)
                    predicted_returns = benchmark_returns_np * beta
                    residual_returns = stock_returns_np - predicted_returns
                    residual_risk = np.std(residual_returns, ddof=1) * np.sqrt(252)
                    self.risk_metrics[ticker]['residual_risk'] = float(residual_risk)
                    
                    # Calculate systematic risk percentage
                    total_risk = np.std(stock_returns_np, ddof=1) * np.sqrt(252)
                    systematic_risk = beta * np.std(benchmark_returns_np, ddof=1) * np.sqrt(252)
                    systematic_risk_pct = (systematic_risk / total_risk) ** 2
                    self.risk_metrics[ticker]['systematic_risk_pct'] = float(systematic_risk_pct)
                else:
                    print(f"Warning: benchmark return variance is 0, cannot calculate beta for {ticker}")
                    self.risk_metrics[ticker]['beta'] = None
                    self.risk_metrics[ticker]['r_squared'] = None
                    self.risk_metrics[ticker]['residual_risk'] = None
                    self.risk_metrics[ticker]['systematic_risk_pct'] = None
            else:
                print(f"Warning: covariance matrix shape is incorrect, cannot calculate beta for {ticker}")
                self.risk_metrics[ticker]['beta'] = None
                self.risk_metrics[ticker]['r_squared'] = None
                self.risk_metrics[ticker]['residual_risk'] = None
                self.risk_metrics[ticker]['systematic_risk_pct'] = None
        except Exception as e:
            print(f"Error calculating beta for {ticker}: {str(e)}")
            self.risk_metrics[ticker]['beta'] = None
            self.risk_metrics[ticker]['r_squared'] = None
            self.risk_metrics[ticker]['residual_risk'] = None
            self.risk_metrics[ticker]['systematic_risk_pct'] = None
    
    def _calculate_information_ratio(self, ticker, returns, benchmark_returns):
        """
        Calculate information ratio
        
        Parameters:
        ticker (str): stock code
        returns (Series): stock return series
        benchmark_returns (Series): benchmark index return series
        """
        if benchmark_returns is None or len(returns) < 30 or len(benchmark_returns) < 30:
            print(f"Warning: insufficient data, cannot calculate information ratio for {ticker}")
            self.risk_metrics[ticker]['information_ratio'] = None
            return
        
        try:
            # Ensure two sequences have the same index
            common_index = returns.index.intersection(benchmark_returns.index)
            if len(common_index) < 30:
                print(f"Warning: insufficient common data points, cannot calculate information ratio for {ticker}")
                self.risk_metrics[ticker]['information_ratio'] = None
                return
            
            # Align data
            stock_returns_aligned = returns.loc[common_index]
            benchmark_returns_aligned = benchmark_returns.loc[common_index]
            
            # Convert to numpy array, avoid Series comparison issues
            stock_returns_np = stock_returns_aligned.values
            benchmark_returns_np = benchmark_returns_aligned.values
            
            # Calculate excess returns
            excess_returns = stock_returns_np - benchmark_returns_np
            
            # Calculate information ratio
            excess_returns_mean = np.mean(excess_returns)
            excess_returns_std = np.std(excess_returns, ddof=1)
            
            if excess_returns_std > 0:
                information_ratio = excess_returns_mean / excess_returns_std * np.sqrt(252)
                self.risk_metrics[ticker]['information_ratio'] = float(information_ratio)
            else:
                print(f"Warning: excess return standard deviation is 0, cannot calculate information ratio for {ticker}")
                self.risk_metrics[ticker]['information_ratio'] = None
        except Exception as e:
            print(f"Error calculating information ratio for {ticker}: {str(e)}")
            self.risk_metrics[ticker]['information_ratio'] = None
    
    def _calculate_treynor_ratio(self, ticker, returns, benchmark_returns):
        """
        Calculate Treynor ratio
        
        Parameters:
        ticker (str): stock code
        returns (Series): stock return series
        benchmark_returns (Series): benchmark index return series
        """
        if 'beta' not in self.risk_metrics[ticker] or self.risk_metrics[ticker]['beta'] is None:
            print(f"Warning: beta coefficient is not available, cannot calculate Treynor ratio for {ticker}")
            self.risk_metrics[ticker]['treynor_ratio'] = None
            return
        
        try:
            # Calculate risk-free rate (assumed to be 0, can be adjusted according to actual situation)
            risk_free_rate = 0.0
            
            # Calculate annualized average return
            returns_mean = returns.mean() * 252
            
            # Calculate Treynor ratio
            beta = self.risk_metrics[ticker]['beta']
            if beta != 0:
                treynor_ratio = (returns_mean - risk_free_rate) / beta
                self.risk_metrics[ticker]['treynor_ratio'] = float(treynor_ratio)
            else:
                print(f"Warning: beta coefficient is 0, cannot calculate Treynor ratio for {ticker}")
                self.risk_metrics[ticker]['treynor_ratio'] = None
        except Exception as e:
            print(f"Error calculating Treynor ratio for {ticker}: {str(e)}")
            self.risk_metrics[ticker]['treynor_ratio'] = None
    
    def _calculate_sortino_ratio(self, ticker, returns):
        """
        Calculate Sortino ratio
        
        Parameters:
        ticker (str): stock code
        returns (Series): stock return series
        """
        if len(returns) < 30:
            print(f"Warning: insufficient data, cannot calculate Sortino ratio for {ticker}")
            self.risk_metrics[ticker]['sortino_ratio'] = None
            self.risk_metrics[ticker]['downside_deviation'] = None
            return
        
        try:
            # Convert to numpy array, avoid Series comparison issues
            returns_np = returns.values
            
            # Calculate risk-free rate (assumed to be 0, can be adjusted according to actual situation)
            risk_free_rate = 0.0
            
            # Calculate annualized average return
            returns_mean = np.mean(returns_np) * 252
            
            # Calculate downside risk (only consider negative returns)
            negative_returns = returns_np[returns_np < 0]
            if len(negative_returns) > 0:
                downside_risk = np.std(negative_returns, ddof=1) * np.sqrt(252)
                
                # Calculate Sortino ratio
                if downside_risk > 0:
                    sortino_ratio = (returns_mean - risk_free_rate) / downside_risk
                    self.risk_metrics[ticker]['sortino_ratio'] = float(sortino_ratio)
                    
                    # Calculate downside deviation
                    target_return = 0  # Target return, can be adjusted according to actual situation
                    downside_returns = returns_np[returns_np < target_return]
                    downside_deviation = np.sqrt(np.sum((downside_returns - target_return) ** 2) / len(returns_np)) * np.sqrt(252)
                    self.risk_metrics[ticker]['downside_deviation'] = float(downside_deviation)
                else:
                    print(f"Warning: downside risk is 0, cannot calculate Sortino ratio for {ticker}")
                    self.risk_metrics[ticker]['sortino_ratio'] = None
                    self.risk_metrics[ticker]['downside_deviation'] = 0.0
            else:
                print(f"Warning: no negative returns, set Sortino ratio for {ticker} to infinity")
                self.risk_metrics[ticker]['sortino_ratio'] = float('inf')
                self.risk_metrics[ticker]['downside_deviation'] = 0.0
        except Exception as e:
            print(f"Error calculating Sortino ratio for {ticker}: {str(e)}")
            self.risk_metrics[ticker]['sortino_ratio'] = None
            self.risk_metrics[ticker]['downside_deviation'] = None
    
    # Other methods...

def run_analysis(tickers, start_date=None, end_date=None):
    """
    Run comprehensive analysis
    
    Parameters:
    tickers (list): stock code list
    start_date (str): start date, format 'YYYY-MM-DD'
    end_date (str): end date, format 'YYYY-MM-DD'
    
    Returns:
    ValuationRiskMonitor: analyzer instance
    """
    # Create monitor instance
    monitor = ValuationRiskMonitor(tickers, start_date, end_date)
    
    # Download data
    monitor.download_data()
    
    # Calculate risk metrics
    monitor.calculate_risk_metrics()
    
    # Calculate valuation metrics
    if hasattr(monitor, 'calculate_valuation_metrics'):
        monitor.calculate_valuation_metrics()
    
    # Print results
    print("\nAnalysis results:")
    for ticker in monitor.tickers:
        print(f"\n{ticker} risk metrics:")
        for metric, value in monitor.risk_metrics[ticker].items():
            print(f"  {metric}: {value:.4f}")
        
        if hasattr(monitor, 'valuation_metrics') and ticker in monitor.valuation_metrics:
            print(f"\n{ticker} valuation metrics:")
            for metric, value in monitor.valuation_metrics[ticker].items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    print(f"  {metric}: {value:.4f}")
                else:
                    print(f"  {metric}: {value}")
    
    return monitor

def run_analysis_text_only_simple(tickers, start_date=None, end_date=None):
    """
    Run simplified text analysis, return JSON format risk analysis results
    
    Parameters:
    tickers (list or str): stock code list or single stock code string
    start_date (str): start date, format 'YYYY-MM-DD'
    end_date (str): end date, format 'YYYY-MM-DD'
    
    Returns:
    dict: JSON object containing risk analysis results
    """
    # If tickers is a string, convert it to a list
    if isinstance(tickers, str):
        tickers = [ticker.strip() for ticker in tickers.split(',') if ticker.strip()]
    
    # Create monitor instance
    monitor = ValuationRiskMonitor(tickers, start_date, end_date)
    
    try:
        # Download data
        monitor.download_data()
        
        # Calculate risk metrics
        risk_metrics = monitor.calculate_risk_metrics()
        
        # Collect the result of the first stock code (or the only one)
        ticker = tickers[0] if tickers else None
        
        if not ticker or ticker not in risk_metrics:
            return {"error": "Failed to get stock risk data"}
        
        metrics = risk_metrics[ticker]
        
        # Create result dictionary
        result = {}
        
        # Volatility
        volatility = metrics.get('volatility')
        if volatility is not None:
            result["volatility"] = round(volatility * 100, 2)  # Convert to percentage
            # Add risk rating
            if volatility > 0.3:
                result["volatility_rating"] = "High"
            elif volatility < 0.15:
                result["volatility_rating"] = "Low"
            else:
                result["volatility_rating"] = "Medium"
        
        # Maximum drawdown
        max_drawdown = metrics.get('max_drawdown')
        if max_drawdown is not None:
            result["max_drawdown"] = round(max_drawdown * 100, 2)  # Convert to percentage
            # Add risk rating
            if max_drawdown < -0.3:
                result["drawdown_rating"] = "High"
            elif max_drawdown > -0.1:
                result["drawdown_rating"] = "Low"
            else:
                result["drawdown_rating"] = "Medium"
        
        # Beta coefficient
        beta = metrics.get('beta')
        if beta is not None and not np.isnan(beta):
            result["beta"] = round(beta, 2)
            # Add risk rating
            if beta > 1.5:
                result["beta_rating"] = "High"
            elif beta < 0.5:
                result["beta_rating"] = "Low"
            else:
                result["beta_rating"] = "中"
        
        # R方值
        r_squared = metrics.get('r_squared')
        if r_squared is not None:
            result["r_squared"] = round(r_squared, 2)
        
        # Systematic risk percentage
        systematic_risk_pct = metrics.get('systematic_risk_pct')
        if systematic_risk_pct is not None:
            result["systematic_risk_pct"] = round(systematic_risk_pct * 100, 2)
        
        # Residual risk
        residual_risk = metrics.get('residual_risk')
        if residual_risk is not None:
            result["residual_risk"] = round(residual_risk * 100, 2)
        
        # Risk value (VaR)
        var_95 = metrics.get('var_95')
        if var_95 is not None:
            result["var_95"] = round(var_95 * 100, 2)
            # Add risk rating
            if var_95 < -0.03:
                result["var_rating"] = "High"
            elif var_95 > -0.015:
                result["var_rating"] = "Low"
            else:
                result["var_rating"] = "Medium"
        
        # Sharpe ratio
        sharpe = metrics.get('sharpe_ratio')
        if sharpe is not None:
            result["sharpe_ratio"] = round(sharpe, 2)
            # Add risk rating
            if sharpe > 1:
                result["sharpe_rating"] = "Good"
            elif sharpe < 0:
                result["sharpe_rating"] = "Bad"
            else:
                result["sharpe_rating"] = "Medium"
        
        # Information ratio
        info_ratio = metrics.get('information_ratio')
        if info_ratio is not None:
            result["information_ratio"] = round(info_ratio, 2)
        
        # Treynor ratio
        treynor = metrics.get('treynor_ratio')
        if treynor is not None:
            result["treynor_ratio"] = round(treynor, 2)
        
        # Sortino ratio
        sortino = metrics.get('sortino_ratio')
        if sortino is not None:
            if sortino == float('inf'):
                result["sortino_ratio"] = "∞"
            else:
                result["sortino_ratio"] = round(sortino, 2)
                # Add risk rating
                if sortino > 1:
                    result["sortino_rating"] = "Good"
                elif sortino < 0:
                    result["sortino_rating"] = "Bad"
                else:
                    result["sortino_rating"] = "Medium"
        
        # Downside deviation
        downside_dev = metrics.get('downside_deviation')
        if downside_dev is not None:
            result["downside_deviation"] = round(downside_dev * 100, 2)
        
        # Skewness and kurtosis
        skew = metrics.get('skewness')
        kurt = metrics.get('kurtosis')
        if skew is not None:
            result["skewness"] = round(skew, 2)
        if kurt is not None:
            result["kurtosis"] = round(kurt, 2)
        
        # Add risk assessment summary
        result["risk_summary"] = []
        
        # Overall risk level
        if volatility is not None:
            if volatility > 0.3:
                result["risk_summary"].append("High volatility stock, overall risk is high")
                result["overall_risk"] = "High"
            elif volatility < 0.15:
                result["risk_summary"].append("Low volatility stock, overall risk is low")
                result["overall_risk"] = "Low"
            else:
                result["risk_summary"].append("Medium volatility stock, overall risk is medium")
                result["overall_risk"] = "Medium"
        
        # Market correlation
        if beta is not None and r_squared is not None:
            if beta > 1.2 and r_squared > 0.6:
                result["risk_summary"].append("High market correlation and amplified market volatility")
            elif beta < 0.8 and r_squared > 0.6:
                result["risk_summary"].append("High market correlation but low volatility")
            elif r_squared < 0.3:
                result["risk_summary"].append("Low market correlation, good diversification effect")
        
        # Risk-adjusted return
        if sharpe is not None and sortino is not None:
            if sharpe > 1 and sortino > 1:
                result["risk_summary"].append("Risk-adjusted return is excellent")
                result["risk_adjusted_return"] = "Good"
            elif sharpe < 0 and sortino < 0:
                result["risk_summary"].append("Risk-adjusted return is poor")
                result["risk_adjusted_return"] = "Bad"
            else:
                result["risk_summary"].append("Risk-adjusted return is medium")
                result["risk_adjusted_return"] = "Medium"
        
        # Extreme risk
        if var_95 is not None and max_drawdown is not None and kurt is not None:
            if var_95 < -0.03 and max_drawdown < -0.2 and kurt > 3:
                result["risk_summary"].append("存在显著的极端风险，需要谨慎存在显著的极端风险，需要谨慎 ")
                result["extreme_risk"] = "High"
            elif var_95 > -0.015 and max_drawdown > -0.1:
                result["risk_summary"].append("Extreme risk is relatively low")
                result["extreme_risk"] = "Low"
            else:
                result["extreme_risk"] = "Medium"
        
        return result
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        trace = traceback.format_exc()
        print(f"Error occurred during analysis: {error_msg}")
        print(trace)
        return {
            "error": f"Error occurred during analysis: {error_msg}",
            "details": trace
        }

# Test function
def test_risk_analysis():
    """Test risk analysis functionality"""
    tickers = ["AAPL", "MSFT"]
    start_date = (dt.datetime.now() - dt.timedelta(days=365)).strftime('%Y-%m-%d')
    
    try:
        monitor = run_analysis_text_only_simple(tickers, start_date)
        if monitor:
            print("\nRisk analysis test successful!")
            return True
        else:
            print("\nRisk analysis test failed!")
            return False
    except Exception as e:
        print(f"\nRisk analysis test failed: {str(e)}")
        return False 