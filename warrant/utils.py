import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from warrant_pricing import warrant_pricing, calculate_greeks

def get_stock_data(ticker, period="1y"):
    """
    Fetch stock data from Yahoo Finance.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    period : str
        Time period for historical data (e.g., '1d', '5d', '1mo', '3mo', '1y', '5y', 'max')
    
    Returns:
    --------
    dict
        Dictionary containing stock data, info, and options data if available
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        # Get company info
        info = stock.info
        
        # Get options data if available
        try:
            options = stock.options
            if options:
                next_expiry = options[0]
                opt_chain = stock.option_chain(next_expiry)
                options_data = {
                    'expiry_dates': options,
                    'next_expiry': next_expiry,
                    'calls': opt_chain.calls,
                    'puts': opt_chain.puts
                }
            else:
                options_data = None
        except:
            options_data = None
            
        return {
            'success': True,
            'data': data,
            'info': info,
            'options': options_data
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def estimate_volatility(stock_data, window_days=252):
    """
    Estimate volatility from historical stock data.
    
    Parameters:
    -----------
    stock_data : pandas.DataFrame
        Historical stock data with 'Close' prices
    window_days : int
        Number of trading days to use for volatility calculation
    
    Returns:
    --------
    float
        Annualized volatility estimate
    """
    if len(stock_data) < 5:
        return 0.4  # Default if not enough data
    
    # Calculate daily returns
    returns = stock_data['Close'].pct_change().dropna()
    
    # Calculate annualized volatility (standard deviation of returns * sqrt(trading days))
    volatility = returns.tail(min(window_days, len(returns))).std() * np.sqrt(252)
    
    return volatility

def get_risk_free_rate():
    """
    Get current risk-free rate (proxied by 10Y Treasury yield).
    
    Returns:
    --------
    float
        Current risk-free rate as a decimal (e.g., 0.02 for 2%)
    """
    try:
        # Use Treasury bond (^TNX) as risk-free rate proxy
        tnx = yf.Ticker("^TNX")
        tnx_data = tnx.history(period="1d")
        rf_rate = float(tnx_data['Close'].iloc[-1]) / 100.0
        return rf_rate
    except:
        return 0.02  # Default value if unable to fetch

def run_what_if_analysis(base_params, scenarios):
    """
    Run what-if analysis for different parameter scenarios.
    
    Parameters:
    -----------
    base_params : dict
        Dictionary containing base parameters (S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    scenarios : dict
        Dictionary of scenarios to analyze, where each key is a parameter name and each value is a list of values
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing scenario results
    """
    # Extract base parameters
    S = base_params.get('S', 10.0)
    K = base_params.get('K', 10.0)
    T = base_params.get('T', 5.0)
    r = base_params.get('r', 0.02)
    sigma = base_params.get('sigma', 0.4)
    dividend_yield = base_params.get('dividend_yield', 0.0)
    num_warrants = base_params.get('num_warrants', 100)
    num_shares = base_params.get('num_shares', 1000)
    
    # Calculate base price
    base_price = warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    
    # Initialize results list
    results = []
    
    # Run scenarios
    for param_name, param_values in scenarios.items():
        for value in param_values:
            # Create a copy of base parameters
            params = base_params.copy()
            
            # Update the parameter for this scenario
            params[param_name] = value
            
            # Calculate new price
            new_price = warrant_pricing(
                params.get('S', S),
                params.get('K', K),
                params.get('T', T),
                params.get('r', r),
                params.get('sigma', sigma),
                params.get('dividend_yield', dividend_yield),
                params.get('num_warrants', num_warrants),
                params.get('num_shares', num_shares)
            )
            
            # Calculate Greeks
            greeks = calculate_greeks(
                params.get('S', S),
                params.get('K', K),
                params.get('T', T),
                params.get('r', r),
                params.get('sigma', sigma),
                params.get('dividend_yield', dividend_yield),
                params.get('num_warrants', num_warrants),
                params.get('num_shares', num_shares)
            )
            
            # Calculate percent change
            percent_change = (new_price - base_price) / base_price
            
            # Add to results
            results.append({
                'Scenario': f"{param_name} = {value}",
                'Parameter': param_name,
                'Value': value,
                'Price': new_price,
                'Change': new_price - base_price,
                'Percent Change': percent_change,
                'Delta': greeks['delta'],
                'Gamma': greeks['gamma'],
                'Theta': greeks['theta'],
                'Vega': greeks['vega'],
                'Rho': greeks['rho']
            })
    
    # Convert to DataFrame
    return pd.DataFrame(results)

def batch_process_warrants(warrants_data):
    """
    Process multiple warrants in batch.
    
    Parameters:
    -----------
    warrants_data : list of dict
        List of dictionaries, each containing parameters for a warrant
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing pricing results for all warrants
    """
    results = []
    
    for warrant in warrants_data:
        # Extract parameters
        S = warrant.get('S', 10.0)
        K = warrant.get('K', 10.0)
        T = warrant.get('T', 5.0)
        r = warrant.get('r', 0.02)
        sigma = warrant.get('sigma', 0.4)
        dividend_yield = warrant.get('dividend_yield', 0.0)
        num_warrants = warrant.get('num_warrants', 100)
        num_shares = warrant.get('num_shares', 1000)
        ticker = warrant.get('ticker', 'Unknown')
        
        # Calculate price and Greeks
        price = warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
        greeks = calculate_greeks(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
        
        # Add to results
        results.append({
            'Ticker': ticker,
            'Stock Price': S,
            'Strike Price': K,
            'Time to Expiration': T,
            'Risk-free Rate': r,
            'Volatility': sigma,
            'Dividend Yield': dividend_yield,
            'Dilution Factor': num_shares / (num_shares + num_warrants),
            'Warrant Price': price,
            'Delta': greeks['delta'],
            'Gamma': greeks['gamma'],
            'Theta': greeks['theta'],
            'Vega': greeks['vega'],
            'Rho': greeks['rho']
        })
    
    # Convert to DataFrame
    return pd.DataFrame(results)