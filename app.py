import streamlit as st
import sys
import os

# Add the subdirectories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'optlt'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'warrent'))

# Import necessary components from both modules
from warrent.warrant_pricing import warrant_pricing, calculate_greeks as warrant_greeks
from optlt.long_term_option import long_term_option_pricing, calculate_greeks as option_greeks

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="Damodaran Financial Tools",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #0D47A1;
    }
    .info-text {
        font-size: 1rem;
        color: #37474F;
    }
    .highlight {
        background-color: #E3F2FD;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: 500;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #0D47A1;
    }
    .tool-card {
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .tool-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Custom function to fetch stock data from Yahoo Finance
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_stock_data(ticker, period="1y"):
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

# Function to estimate volatility from historical data
def estimate_volatility(stock_data, window_days=252):
    if len(stock_data) < 5:
        return 0.4  # Default if not enough data
    
    # Calculate daily returns
    returns = stock_data['Close'].pct_change().dropna()
    
    # Calculate annualized volatility (standard deviation of returns * sqrt(trading days))
    volatility = returns.tail(min(window_days, len(returns))).std() * np.sqrt(252)
    
    return volatility

# Function to get risk-free rate (proxied by 10Y Treasury yield)
@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_risk_free_rate():
    try:
        # Use Treasury bond (^TNX) as risk-free rate proxy
        tnx = yf.Ticker("^TNX")
        tnx_data = tnx.history(period="1d")
        rf_rate = float(tnx_data['Close'].iloc[-1]) / 100.0
        return rf_rate
    except:
        return 0.02  # Default value if unable to fetch

# Main App
def main():
    # Create sidebar navigation
    st.sidebar.markdown('<p class="sub-header">Navigation</p>', unsafe_allow_html=True)
    app_mode = st.sidebar.radio(
        "Select Tool",
        ["Home", "Warrant Pricing Calculator", "Long-Term Option Pricing"]
    )
    
    # Home Page
    if app_mode == "Home":
        st.markdown('<p class="main-header">Financial Education & Analysis Tools</p>', unsafe_allow_html=True)
        st.markdown('<p class="info-text">Interactive tools for understanding financial models and enhancing investment value</p>', unsafe_allow_html=True)
        
        # Show tool cards
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                """
                <div class="tool-card">
                    <h3>Warrant Pricing Calculator</h3>
                    <p>A comprehensive tool for warrant pricing, market analysis, and portfolio optimization.</p>
                    <p><strong>Features:</strong></p>
                    <ul>
                        <li>Dilution-Adjusted Pricing</li>
                        <li>Interactive Visualizations</li>
                        <li>Market Data Integration</li>
                        <li>Sensitivity Analysis</li>
                    </ul>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                """
                <div class="tool-card">
                    <h3>Long-Term Option Pricing</h3>
                    <p>Learn about fundamental option pricing theory and apply models to real-world scenarios.</p>
                    <p><strong>What You'll Learn:</strong></p>
                    <ul>
                        <li>Black-Scholes Model Fundamentals</li>
                        <li>Option Greeks & Sensitivities</li>
                        <li>Long-term Option Analysis</li>
                        <li>Market Data Integration</li>
                    </ul>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Additional resources
        st.markdown("### Additional Resources")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(
                """
                <div class="tool-card">
                    <h4>Options Theory</h4>
                    <p>Understand the theoretical underpinnings of options pricing and valuation.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                """
                <div class="tool-card">
                    <h4>Monte Carlo Simulations</h4>
                    <p>Explore advanced pricing techniques using simulations and statistical models.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                """
                <div class="tool-card">
                    <h4>Volatility Analysis</h4>
                    <p>Learn to analyze and predict volatility for improved option pricing.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; color: #666;">
            <p>© 2025 Damodaran Financial Tools. All rights reserved.</p>
            <p>These tools are developed for educational purposes only, not financial advice.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Warrant Pricing Calculator
    elif app_mode == "Warrant Pricing Calculator":
        from warrent.app import main as warrant_main
        warrant_main()
    
    # Long-Term Option Pricing
    elif app_mode == "Long-Term Option Pricing":
        st.markdown('<p class="main-header">Long-Term Option Pricing Calculator</p>', unsafe_allow_html=True)
        st.markdown('<p class="info-text">A financial tool for calculating long-term option prices and Greeks using the Black-Scholes model.</p>', unsafe_allow_html=True)
        
        # Create tabs for different modes
        tab1, tab2 = st.tabs(["Calculator", "Educational Resources"])
        
        with tab1:
            # Create two columns for input and results
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown('<p class="sub-header">Inputs</p>', unsafe_allow_html=True)
                
                # Input tabs
                input_tab1, input_tab2 = st.tabs(["Manual Entry", "Stock Lookup"])
                
                with input_tab1:
                    # Basic parameters
                    S = st.number_input("Stock Price ($)", min_value=0.01, value=500.0, step=0.01)
                    K = st.number_input("Strike Price ($)", min_value=0.01, value=600.0, step=0.01)
                    T = st.number_input("Time to Expiration (years)", min_value=0.01, value=15.0, step=0.01)
                    
                    # Advanced parameters
                    with st.expander("Advanced Parameters"):
                        sigma = st.number_input("Volatility (annual)", min_value=0.01, max_value=2.0, value=0.5, step=0.01)
                        r = st.number_input("Risk-free Rate", min_value=0.0, max_value=0.2, value=0.05, step=0.001, format="%.3f")
                        dividend_yield = st.number_input("Dividend Yield", min_value=0.0, max_value=0.2, value=0.0, step=0.001, format="%.3f")
                
                with input_tab2:
                    ticker_input = st.text_input("Stock Ticker Symbol", "AAPL")
                    lookup_button = st.button("Lookup Stock Data")
                    
                    if lookup_button:
                        with st.spinner("Fetching stock data..."):
                            stock_result = get_stock_data(ticker_input)
                            
                            if stock_result['success']:
                                st.session_state.stock_data = stock_result['data']
                                st.session_state.stock_info = stock_result['info']
                                st.session_state.options_data = stock_result['options']
                                
                                # Update parameters based on stock data
                                if 'stock_data' in st.session_state:
                                    data = st.session_state.stock_data
                                    info = st.session_state.stock_info
                                    
                                    # Current stock price
                                    current_price = data['Close'].iloc[-1]
                                    st.session_state.S = current_price
                                    
                                    # Volatility estimate
                                    est_vol = estimate_volatility(data)
                                    st.session_state.sigma = min(max(est_vol, 0.1), 1.5)
                                    
                                    # Dividend yield
                                    if 'dividendYield' in info and info['dividendYield'] is not None:
                                        st.session_state.dividend_yield = info['dividendYield']
                                    else:
                                        st.session_state.dividend_yield = 0.0
                                    
                                    # Update risk-free rate
                                    st.session_state.r = get_risk_free_rate()
                                    
                                    # If options data available, use nearest strike and expiry
                                    if st.session_state.options_data:
                                        options = st.session_state.options_data
                                        calls = options['calls']
                                        
                                        # Find closest strike to current price
                                        closest_strike = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]['strike'].values[0]
                                        st.session_state.K = closest_strike
                                        
                                        # Calculate time to expiry
                                        expiry = datetime.strptime(options['next_expiry'], '%Y-%m-%d')
                                        days_to_expiry = (expiry - datetime.now()).days
                                        st.session_state.T = max(days_to_expiry / 365, 0.01)
                                
                                st.success(f"Successfully loaded data for {ticker_input}")
                            else:
                                st.error(f"Error fetching data: {stock_result['error']}")
                
                # Use values from stock lookup if available
                if 'S' in st.session_state:
                    S = st.session_state.S
                if 'K' in st.session_state:
                    K = st.session_state.K
                if 'T' in st.session_state:
                    T = st.session_state.T
                if 'sigma' in st.session_state:
                    sigma = st.session_state.sigma
                if 'r' in st.session_state:
                    r = st.session_state.r
                if 'dividend_yield' in st.session_state:
                    dividend_yield = st.session_state.dividend_yield
                
                # Calculate button
                calculate_button = st.button("Calculate Option Prices")
            
            with col2:
                if calculate_button or 'last_calculation' in st.session_state:
                    st.markdown('<p class="sub-header">Option Pricing Results</p>', unsafe_allow_html=True)
                    
                    # Store these values in session state for persistence
                    if calculate_button:
                        st.session_state.last_calculation = {
                            'S': S, 'K': K, 'T': T, 'r': r, 'sigma': sigma, 'dividend_yield': dividend_yield
                        }
                    else:
                        # Use stored values from session state
                        S = st.session_state.last_calculation['S']
                        K = st.session_state.last_calculation['K']
                        T = st.session_state.last_calculation['T']
                        r = st.session_state.last_calculation['r']
                        sigma = st.session_state.last_calculation['sigma']
                        dividend_yield = st.session_state.last_calculation['dividend_yield']
                    
                    # Calculate option price and Greeks
                    call_price, put_price, d1, d2, N_d1, N_d2 = long_term_option_pricing(
                        S, K, T, r, sigma, dividend_yield
                    )
                    greeks = option_greeks(S, K, T, r, sigma, dividend_yield)
                    
                    # Display parameters and results
                    params_df = pd.DataFrame({
                        'Parameter': ['Stock Price', 'Strike Price', 'Time to Expiration', 'Risk-free Rate', 
                                    'Volatility', 'Dividend Yield'],
                        'Value': [f"${S:.2f}", f"${K:.2f}", f"{T:.2f} years", f"{r:.2%}", 
                                f"{sigma:.2%}", f"{dividend_yield:.2%}"]
                    })
                    
                    st.dataframe(params_df, hide_index=True)
                    
                    # Display price in metrics
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Call Option Price", f"${call_price:.4f}")
                    with col2:
                        st.metric("Put Option Price", f"${put_price:.4f}")
                    
                    # Display Greeks
                    st.markdown('<p class="sub-header">Greeks</p>', unsafe_allow_html=True)
                    
                    greeks_df = pd.DataFrame({
                        'Greek': ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho'],
                        'Value': [f"{greeks['delta']:.4f}", f"{greeks['gamma']:.4f}", 
                                f"{greeks['theta']:.4f}", f"{greeks['vega']:.4f}", f"{greeks['rho']:.4f}"],
                        'Description': [
                            'Rate of change of option price with respect to stock price',
                            'Rate of change of delta with respect to stock price',
                            'Rate of change of option price with respect to time (per day)',
                            'Rate of change of option price with respect to volatility',
                            'Rate of change of option price with respect to interest rate'
                        ]
                    })
                    
                    st.dataframe(greeks_df, hide_index=True)
                    
                    # Display model parameters
                    st.markdown('<p class="sub-header">Model Parameters</p>', unsafe_allow_html=True)
                    
                    model_df = pd.DataFrame({
                        'Parameter': ['d1', 'd2', 'N(d1)', 'N(d2)'],
                        'Value': [f"{d1:.4f}", f"{d2:.4f}", f"{N_d1:.4f}", f"{N_d2:.4f}"]
                    })
                    
                    st.dataframe(model_df, hide_index=True)
                    
                    # Create comparison chart
                    if S > 0 and K > 0:
                        st.markdown('<p class="sub-header">Visual Analysis</p>', unsafe_allow_html=True)
                        
                        # Create price points around current stock price
                        price_range = np.linspace(max(0.1, S * 0.5), S * 1.5, 100)
                        
                        # Calculate option prices and intrinsic values for each price point
                        call_prices = []
                        put_prices = []
                        call_intrinsic = []
                        put_intrinsic = []
                        
                        for p in price_range:
                            c, pu, _, _, _, _ = long_term_option_pricing(p, K, T, r, sigma, dividend_yield)
                            call_prices.append(c)
                            put_prices.append(pu)
                            call_intrinsic.append(max(0, p - K))
                            put_intrinsic.append(max(0, K - p))
                        
                        # Create figure
                        fig = go.Figure()
                        
                        # Add call price line
                        fig.add_trace(go.Scatter(
                            x=price_range, 
                            y=call_prices,
                            mode='lines',
                            name='Call Price',
                            line=dict(color='#1E88E5', width=3)
                        ))
                        
                        # Add put price line
                        fig.add_trace(go.Scatter(
                            x=price_range, 
                            y=put_prices,
                            mode='lines',
                            name='Put Price',
                            line=dict(color='#FFC107', width=3)
                        ))
                        
                        # Add intrinsic value lines
                        fig.add_trace(go.Scatter(
                            x=price_range, 
                            y=call_intrinsic,
                            mode='lines',
                            name='Call Intrinsic Value',
                            line=dict(color='#1E88E5', width=2, dash='dash')
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=price_range, 
                            y=put_intrinsic,
                            mode='lines',
                            name='Put Intrinsic Value',
                            line=dict(color='#FFC107', width=2, dash='dash')
                        ))
                        
                        # Add current price marker
                        fig.add_trace(go.Scatter(
                            x=[S],
                            y=[call_price],
                            mode='markers',
                            name='Current Call Price',
                            marker=dict(color='blue', size=10)
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=[S],
                            y=[put_price],
                            mode='markers',
                            name='Current Put Price',
                            marker=dict(color='orange', size=10)
                        ))
                        
                        # Add vertical line at strike price
                        fig.add_vline(x=K, line_dash="dash", line_color="green", annotation_text="Strike Price")
                        
                        # Update layout
                        fig.update_layout(
                            title='Option Price vs. Stock Price',
                            xaxis_title='Stock Price ($)',
                            yaxis_title='Option Price ($)',
                            hovermode='x unified',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown('<p class="sub-header">Understanding Option Pricing</p>', unsafe_allow_html=True)
            
            st.markdown("""
            ### Black-Scholes Model
            
            The Black-Scholes model is a mathematical model used for pricing options contracts. It was developed by Fischer Black, Myron Scholes, and Robert Merton in the early 1970s.
            
            #### Key Assumptions:
            
            - The stock price follows a geometric Brownian motion with constant drift and volatility
            - No transaction costs or taxes
            - No dividends during the life of the option (though our implementation includes dividend adjustments)
            - Risk-free interest rate is constant
            - No arbitrage opportunities
            
            #### The Formula:
            
            For a call option:
            
            ```
            C = S * N(d1) - K * e^(-rT) * N(d2)
            ```
            
            For a put option:
            
            ```
            P = K * e^(-rT) * N(-d2) - S * N(-d1)
            ```
            
            Where:
            - C = Call option price
            - P = Put option price
            - S = Current stock price
            - K = Strike price
            - r = Risk-free interest rate
            - T = Time to expiration (in years)
            - N = Cumulative distribution function of the standard normal distribution
            - d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
            - d2 = d1 - σ√T
            
            ### Option Greeks
            
            The Greeks measure the sensitivity of option prices to various factors:
            
            - **Delta**: Measures the rate of change of option price with respect to changes in the underlying asset's price
            - **Gamma**: Measures the rate of change of delta with respect to changes in the underlying price
            - **Theta**: Measures the rate of change of option price with respect to the passage of time
            - **Vega**: Measures the rate of change of option price with respect to volatility
            - **Rho**: Measures the rate of change of option price with respect to the risk-free interest rate
            """)
            
            st.markdown("### Educational Resources")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                #### Books:
                - Options, Futures, and Other Derivatives by John C. Hull
                - Option Volatility & Pricing by Sheldon Natenberg
                - The Bible of Options Strategies by Guy Cohen
                """)
            
            with col2:
                st.markdown("""
                #### Online Resources:
                - [Khan Academy: Options, Swaps, Futures, MBSs, CDOs, and Other Derivatives](https://www.khanacademy.org/economics-finance-domain/core-finance/derivative-securities)
                - [Investopedia: Options Basics Tutorial](https://www.investopedia.com/options-basics-tutorial-4583012)
                - [Aswath Damodaran's Option Pricing Resources](http://pages.stern.nyu.edu/~adamodar/New_Home_Page/optionvirtuosos.html)
                """)

if __name__ == "__main__":
    main()