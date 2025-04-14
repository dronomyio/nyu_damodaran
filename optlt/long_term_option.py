import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

def long_term_option_pricing(S, K, T, r, sigma, dividend_yield=0.0):
    """
    Calculate the price of a long-term option with dividend adjustment using Black-Scholes model.
    
    Parameters:
    -----------
    S : float
        Current stock price
    K : float
        Strike price of the option
    T : float
        Time to expiration in years
    r : float
        Risk-free interest rate (annualized, continuous compounding)
    sigma : float
        Volatility of the underlying stock (annualized)
    dividend_yield : float
        Annualized continuous dividend yield of the stock
    
    Returns:
    --------
    tuple
        (call_price, put_price, d1, d2, N_d1, N_d2)
    """
    # Calculate variance
    variance = sigma**2
    
    # Calculate d1 and d2
    if sigma <= 0 or T <= 0:
        return max(0, S - K * np.exp(-r * T)), max(0, K * np.exp(-r * T) - S), 0, 0, 0, 0
    
    d1 = (np.log(S / K) + (r - dividend_yield + 0.5 * variance) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Calculate N(d1) and N(d2) - cumulative normal distribution
    N_d1 = norm.cdf(d1)
    N_d2 = norm.cdf(d2)
    
    # Calculate option values using Black-Scholes formula with dividend adjustment
    call_price = S * np.exp(-dividend_yield * T) * N_d1 - K * np.exp(-r * T) * N_d2
    
    # Put price using put-call parity
    put_price = call_price + K * np.exp(-r * T) - S * np.exp(-dividend_yield * T)
    
    return call_price, put_price, d1, d2, N_d1, N_d2

def calculate_greeks(S, K, T, r, sigma, dividend_yield=0.0):
    """
    Calculate the Greeks for a long-term option with dividend adjustment.
    
    Returns:
    --------
    dict
        Dictionary containing the Greeks (delta, gamma, theta, vega, rho)
    """
    # Small change for finite difference
    h = 0.01
    
    # Base option price
    call_price, _, _, _, _, _ = long_term_option_pricing(S, K, T, r, sigma, dividend_yield)
    
    # Delta - partial derivative with respect to stock price
    call_price_up, _, _, _, _, _ = long_term_option_pricing(S + h, K, T, r, sigma, dividend_yield)
    delta = (call_price_up - call_price) / h
    
    # Gamma - second partial derivative with respect to stock price
    call_price_down, _, _, _, _, _ = long_term_option_pricing(S - h, K, T, r, sigma, dividend_yield)
    gamma = (call_price_up - 2 * call_price + call_price_down) / (h**2)
    
    # Theta - partial derivative with respect to time (expressed in days)
    if T <= h/365:
        theta = 0
    else:
        call_price_t, _, _, _, _, _ = long_term_option_pricing(S, K, T - h/365, r, sigma, dividend_yield)
        theta = (call_price_t - call_price) / (h/365)
    
    # Vega - partial derivative with respect to volatility
    call_price_v, _, _, _, _, _ = long_term_option_pricing(S, K, T, r, sigma + h, dividend_yield)
    vega = (call_price_v - call_price) / h
    
    # Rho - partial derivative with respect to interest rate
    call_price_r, _, _, _, _, _ = long_term_option_pricing(S, K, T, r + h, sigma, dividend_yield)
    rho = (call_price_r - call_price) / h
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

def plot_option_values(S_range, K, T, r, sigma, dividend_yield=0.0):
    """
    Plot option values for a range of stock prices.
    
    Parameters:
    -----------
    S_range : array-like
        Range of stock prices to plot
    K, T, r, sigma, dividend_yield : float
        Option parameters
    """
    call_prices = []
    put_prices = []
    
    for S in S_range:
        call, put, _, _, _, _ = long_term_option_pricing(S, K, T, r, sigma, dividend_yield)
        call_prices.append(call)
        put_prices.append(put)
    
    plt.figure(figsize=(10, 6))
    plt.plot(S_range, call_prices, 'b-', label='Call Option')
    plt.plot(S_range, put_prices, 'r-', label='Put Option')
    plt.axvline(x=K, color='gray', linestyle='--', label='Strike Price')
    
    plt.xlabel('Stock Price')
    plt.ylabel('Option Value')
    plt.title('Long-Term Option Values with Dividend Adjustment')
    plt.legend()
    plt.grid(True)
    
    plt.savefig('option_values.png')
    plt.close()
    
    return 'option_values.png'

if __name__ == "__main__":
    # Example parameters from the Excel file
    S = 500.0               # Stock price
    K = 600.0               # Strike price
    T = 15.0                # Time to expiration in years
    r = 0.05                # Risk-free rate (continuous compounding)
    sigma = np.sqrt(0.25)   # Volatility (sqrt of variance)
    dividend_yield = 0.0    # Dividend yield
    
    # Calculate option prices and parameters
    call_price, put_price, d1, d2, N_d1, N_d2 = long_term_option_pricing(
        S, K, T, r, sigma, dividend_yield
    )
    
    print("Long-Term Option Pricing Results:")
    print(f"Stock Price: {S}")
    print(f"Strike Price: {K}")
    print(f"Time to Expiration: {T} years")
    print(f"Risk-free Rate: {r}")
    print(f"Volatility: {sigma}")
    print(f"Dividend Yield: {dividend_yield}")
    print("\nCalculated Values:")
    print(f"d1: {d1:.6f}")
    print(f"N(d1): {N_d1:.6f}")
    print(f"d2: {d2:.6f}")
    print(f"N(d2): {N_d2:.6f}")
    print(f"Call Option Value: {call_price:.6f}")
    print(f"Put Option Value: {put_price:.6f}")
    
    # Calculate and print the Greeks
    greeks = calculate_greeks(S, K, T, r, sigma, dividend_yield)
    print("\nGreeks:")
    for greek, value in greeks.items():
        print(f"{greek.capitalize()}: {value:.6f}")
    
    # Plot option values for a range of stock prices
    S_range = np.linspace(S * 0.5, S * 1.5, 100)
    plot_path = plot_option_values(S_range, K, T, r, sigma, dividend_yield)
    print(f"\nOption value plot saved to: {plot_path}")
    
    # Performance test
    import time
    
    def test_performance(n_iterations=10000):
        start_time = time.time()
        for _ in range(n_iterations):
            long_term_option_pricing(S, K, T, r, sigma, dividend_yield)
        end_time = time.time()
        return end_time - start_time
    
    n_iterations = 10000
    execution_time = test_performance(n_iterations)
    print(f"\nPerformance:")
    print(f"Python execution time for {n_iterations} iterations: {execution_time:.4f} seconds")
    print(f"Average time per calculation: {execution_time/n_iterations*1000:.4f} ms")
