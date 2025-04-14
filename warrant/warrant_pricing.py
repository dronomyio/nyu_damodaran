import numpy as np
from scipy.stats import norm

def warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares):
    """
    Calculate the price of a warrant with dilution adjustment using Black-Scholes model.
    
    Parameters:
    -----------
    S : float
        Current stock price
    K : float
        Strike price of the warrant
    T : float
        Time to expiration in years
    r : float
        Risk-free interest rate (annualized)
    sigma : float
        Volatility of the underlying stock (annualized)
    dividend_yield : float
        Annualized dividend yield of the stock
    num_warrants : int
        Number of warrants outstanding
    num_shares : int
        Number of shares outstanding
    
    Returns:
    --------
    float
        Price of the warrant
    """
    # Calculate dilution factor
    dilution_factor = num_shares / (num_shares + num_warrants)
    
    # Adjust stock price for dilution
    adjusted_S = S * dilution_factor
    
    # Strike price remains the same (no adjustment needed)
    adjusted_K = K
    
    # Calculate variance
    variance = sigma**2
    
    # Dividend adjusted interest rate
    div_adj_rate = r - dividend_yield
    
    # Calculate d1 and d2
    if sigma <= 0 or T <= 0:
        return max(0, adjusted_S - adjusted_K * np.exp(-r * T))
    
    d1 = (np.log(adjusted_S / adjusted_K) + (div_adj_rate + 0.5 * variance) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Calculate N(d1) and N(d2) - cumulative normal distribution
    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)
    
    # Calculate warrant value using Black-Scholes formula with dilution adjustment
    warrant_value = (adjusted_S * np.exp(-dividend_yield * T) * Nd1 - 
                     adjusted_K * np.exp(-r * T) * Nd2)
    
    return warrant_value

def calculate_greeks(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares):
    """
    Calculate the Greeks for a warrant with dilution adjustment.
    
    Returns:
    --------
    dict
        Dictionary containing the Greeks (delta, gamma, theta, vega, rho)
    """
    # Small change for finite difference
    h = 0.01
    
    # Calculate dilution factor
    dilution_factor = num_shares / (num_shares + num_warrants)
    
    # Base warrant price
    price = warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    
    # Delta - partial derivative with respect to stock price
    delta_price = warrant_pricing(S + h, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    delta = (delta_price - price) / h
    
    # Gamma - second partial derivative with respect to stock price
    gamma_price_plus = warrant_pricing(S + h, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    gamma_price_minus = warrant_pricing(S - h, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    gamma = (gamma_price_plus - 2 * price + gamma_price_minus) / (h**2)
    
    # Theta - partial derivative with respect to time (expressed in days)
    if T <= h/365:
        theta_price = 0
    else:
        theta_price = warrant_pricing(S, K, T - h/365, r, sigma, dividend_yield, num_warrants, num_shares)
    theta = (theta_price - price) / (h/365)
    
    # Vega - partial derivative with respect to volatility
    vega_price = warrant_pricing(S, K, T, r, sigma + h, dividend_yield, num_warrants, num_shares)
    vega = (vega_price - price) / h
    
    # Rho - partial derivative with respect to interest rate
    rho_price = warrant_pricing(S, K, T, r + h, sigma, dividend_yield, num_warrants, num_shares)
    rho = (rho_price - price) / h
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

if __name__ == "__main__":
    # Example parameters from the Excel file
    S = 10.0                # Current stock price
    K = 10.0                # Strike price
    T = 5.0                 # Time to expiration in years
    sigma = 0.4             # Volatility
    dividend_yield = 0.0    # Dividend yield
    r = 0.02                # Risk-free rate
    num_warrants = 100      # Number of warrants outstanding
    num_shares = 1000       # Number of shares outstanding
    
    # Calculate warrant price
    price = warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    print(f"Warrant Price: {price:.6f}")
    
    # Calculate and print the Greeks
    greeks = calculate_greeks(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
    print("\nGreeks:")
    for greek, value in greeks.items():
        print(f"{greek.capitalize()}: {value:.6f}")
    
    # Verify calculations match Excel file
    print("\nVerification against Excel file:")
    dilution_factor = num_shares / (num_shares + num_warrants)
    adjusted_S = S * dilution_factor
    print(f"Adjusted S: {adjusted_S:.6f} (Expected: 9.396451)")
    
    d1 = (np.log(adjusted_S / K) + (r - dividend_yield + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    print(f"d1: {d1:.6f} (Expected: 0.489416)")
    
    Nd1 = norm.cdf(d1)
    print(f"N(d1): {Nd1:.6f} (Expected: 0.687726)")
    
    d2 = d1 - sigma * np.sqrt(T)
    print(f"d2: {d2:.6f} (Expected: -0.405011)")
    
    Nd2 = norm.cdf(d2)
    print(f"N(d2): {Nd2:.6f} (Expected: 0.342735)")
    
    # Performance test
    import time
    
    def test_performance(n_iterations=1000):
        start_time = time.time()
        for _ in range(n_iterations):
            warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
        end_time = time.time()
        return end_time - start_time
    
    n_iterations = 10000
    execution_time = test_performance(n_iterations)
    print(f"\nPerformance:")
    print(f"Python execution time for {n_iterations} iterations: {execution_time:.4f} seconds")
    print(f"Average time per calculation: {execution_time/n_iterations*1000:.4f} ms")
