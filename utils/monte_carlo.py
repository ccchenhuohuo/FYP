"""
Monte Carlo simulation module
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import traceback

def monte_carlo_simulation(ticker, days=60, simulations=200):
    """
    Execute the complete Monte Carlo simulation process
    
    Parameters:
        ticker (str): stock code
        days (int): simulation days, default 60 days
        simulations (int): simulation times, default 200 times
        
    Returns:
        dict: dictionary containing simulation results
    """
    try:
        # Get historical data
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="1y")
        
        if hist_data.empty:
            raise ValueError(f"Cannot get historical data for {ticker}")
        
        # Get current price
        current_price = float(hist_data['Close'].iloc[-1])
        
        # Calculate daily returns and volatility
        returns = np.log(1 + hist_data['Close'].pct_change())
        mu = float(returns.mean())  # daily return
        sigma = float(returns.std())  # daily volatility
        
        # Generate simulation dates
        date_strings = []
        current_date = datetime.now()
        for i in range(days):
            future_date = current_date + timedelta(days=i)
            date_strings.append(future_date.strftime('%Y-%m-%d'))
            
        # Create array to store all paths
        paths = np.zeros((simulations, days))
        paths[:, 0] = current_price
        
        # Use geometric Brownian motion model for simulation
        dt = 1  # time step is 1 day
        for t in range(1, days):
            brownian = np.random.standard_normal(simulations)
            paths[:, t] = paths[:, t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * brownian)
        
        # Convert Numpy array to Python list
        paths_list = paths.tolist()
        
        # Calculate final prices and statistics
        final_prices = paths[:, -1]
        mean_price = float(np.mean(final_prices))
        median_price = float(np.median(final_prices))
        percentile_5 = float(np.percentile(final_prices, 5))
        percentile_25 = float(np.percentile(final_prices, 25))
        percentile_75 = float(np.percentile(final_prices, 75))
        percentile_95 = float(np.percentile(final_prices, 95))
        
        # Calculate annual return and volatility
        annual_return = float((mean_price / current_price) ** (365 / days) - 1) * 100
        annual_volatility = float(sigma * np.sqrt(252) * 100)  # 252个交易日/年
        
        # Return results
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
        print(f"Monte Carlo simulation failed: {str(e)}")
        print(traceback.format_exc())
        raise Exception(f"Error occurred during simulation: {str(e)}")

# Compatibility wrapper for old API
def get_simulation_data(ticker, days=60, simulations=200):
    """Compatibility wrapper for old API"""
    return monte_carlo_simulation(ticker, days, simulations)

# Test function
def test_monte_carlo():
    """Test Monte Carlo simulation function"""
    test_ticker = "AAPL"
    try:
        simulation_results = get_simulation_data(test_ticker)
        print(f"Simulation completed successfully!")
        print(f"Predict the average price of {test_ticker} in 30 days: ${simulation_results['mean_price']:.2f}")
        print(f"90% confidence interval: ${simulation_results['percentile_5']:.2f} - ${simulation_results['percentile_95']:.2f}")
        return True
    except Exception as e:
        print(f"Simulation failed: {str(e)}")
        return False 