import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import time
import os
from warrant_pricing import warrant_pricing, calculate_greeks

# Set page configuration
st.set_page_config(
    page_title="Warrant Pricing Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check for Streamlit's query parameters
query_params = st.query_params
    
# If this is the initial load with the 'Page not found' error
if '_' in query_params:
    # Create a loading spinner that automatically disappears
    with st.spinner("Loading Warrant Pricing Calculator..."):
        # Sleep for a very short time
        time.sleep(0.1)
        
    # This prevents the "Page not found" message from appearing
    st.query_params.clear()

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

# Main application
def main():
    # Add a row with a back button and the title
    col1, col2, col3 = st.columns([1, 10, 1])
    
    with col1:
        st.markdown('<a href="http://localhost/" target="_self"><button style="background-color: #f0f2f6; border: none; border-radius: 4px; padding: 8px 16px; font-size: 14px; cursor: pointer;">← Home</button></a>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<p class="main-header" style="text-align: center;">Warrant Pricing Calculator</p>', unsafe_allow_html=True)
        st.markdown('<p class="info-text" style="text-align: center;">A financial tool for calculating warrant prices and Greeks using the Black-Scholes model with dilution adjustment.</p>', unsafe_allow_html=True)
    
    # Create sidebar for inputs
    with st.sidebar:
        st.markdown('<p class="sub-header">Inputs</p>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Manual Entry", "Stock Lookup"])
        
        with tab1:
            # Basic parameters
            S = st.number_input("Stock Price ($)", min_value=0.01, value=10.0, step=0.01)
            K = st.number_input("Strike Price ($)", min_value=0.01, value=10.0, step=0.01)
            T = st.number_input("Time to Expiration (years)", min_value=0.01, value=5.0, step=0.01)
            
            # Advanced parameters
            with st.expander("Advanced Parameters"):
                sigma = st.number_input("Volatility (annual)", min_value=0.01, max_value=2.0, value=0.4, step=0.01)
                r = st.number_input("Risk-free Rate", min_value=0.0, max_value=0.2, value=0.02, step=0.001, format="%.3f")
                dividend_yield = st.number_input("Dividend Yield", min_value=0.0, max_value=0.2, value=0.0, step=0.001, format="%.3f")
            
            # Dilution parameters
            with st.expander("Dilution Parameters"):
                num_warrants = st.number_input("Number of Warrants Outstanding", min_value=1, value=100, step=1)
                num_shares = st.number_input("Number of Shares Outstanding", min_value=1, value=1000, step=1)
        
        with tab2:
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
                                
                            # Shares outstanding
                            if 'sharesOutstanding' in info and info['sharesOutstanding'] is not None:
                                st.session_state.num_shares = info['sharesOutstanding']
                            
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
    if 'num_shares' in st.session_state:
        num_shares = st.session_state.num_shares
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Pricing Results", "Sensitivity Analysis", "Market Data"])
    
    with tab1:
        # Create two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<p class="sub-header">Warrant Price</p>', unsafe_allow_html=True)
            
            # Calculate warrant price and Greeks
            price = warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
            greeks = calculate_greeks(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
            
            # Display parameters and results
            params_df = pd.DataFrame({
                'Parameter': ['Stock Price', 'Strike Price', 'Time to Expiration', 'Risk-free Rate', 
                             'Volatility', 'Dividend Yield', 'Dilution Factor'],
                'Value': [f"${S:.2f}", f"${K:.2f}", f"{T:.2f} years", f"{r:.2%}", 
                         f"{sigma:.2%}", f"{dividend_yield:.2%}", 
                         f"{num_shares/(num_shares + num_warrants):.4f}"]
            })
            
            st.dataframe(params_df, hide_index=True)
            
            # Display price in a metric
            st.metric("Warrant Price", f"${price:.4f}")
            
            # Display Greeks
            st.markdown('<p class="sub-header">Greeks</p>', unsafe_allow_html=True)
            
            greeks_df = pd.DataFrame({
                'Greek': ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho'],
                'Value': [f"{greeks['delta']:.4f}", f"{greeks['gamma']:.4f}", 
                         f"{greeks['theta']:.4f}", f"{greeks['vega']:.4f}", f"{greeks['rho']:.4f}"],
                'Description': [
                    'Rate of change of warrant price with respect to stock price',
                    'Rate of change of delta with respect to stock price',
                    'Rate of change of warrant price with respect to time (per day)',
                    'Rate of change of warrant price with respect to volatility',
                    'Rate of change of warrant price with respect to interest rate'
                ]
            })
            
            st.dataframe(greeks_df, hide_index=True)
        
        with col2:
            st.markdown('<p class="sub-header">Visual Comparison</p>', unsafe_allow_html=True)
            
            # Create comparison chart
            if S > 0 and K > 0:
                # Create price points around current stock price
                price_range = np.linspace(max(0.1, S * 0.5), S * 1.5, 100)
                
                # Calculate warrant prices and intrinsic values for each price point
                warrant_prices = [warrant_pricing(p, K, T, r, sigma, dividend_yield, num_warrants, num_shares) for p in price_range]
                intrinsic_values = [max(0, p - K) for p in price_range]
                
                # Create figure
                fig = go.Figure()
                
                # Add warrant price line
                fig.add_trace(go.Scatter(
                    x=price_range, 
                    y=warrant_prices,
                    mode='lines',
                    name='Warrant Price',
                    line=dict(color='#1E88E5', width=3)
                ))
                
                # Add intrinsic value line
                fig.add_trace(go.Scatter(
                    x=price_range, 
                    y=intrinsic_values,
                    mode='lines',
                    name='Intrinsic Value',
                    line=dict(color='#FFC107', width=2, dash='dash')
                ))
                
                # Add current price marker
                fig.add_trace(go.Scatter(
                    x=[S],
                    y=[price],
                    mode='markers',
                    name='Current Price',
                    marker=dict(color='#D32F2F', size=10)
                ))
                
                # Update layout
                fig.update_layout(
                    title='Warrant Price vs. Stock Price',
                    xaxis_title='Stock Price ($)',
                    yaxis_title='Warrant Price ($)',
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
        st.markdown('<p class="sub-header">Sensitivity Analysis</p>', unsafe_allow_html=True)
        
        # Create tabs for different sensitivities
        sens_tab1, sens_tab2, sens_tab3, sens_tab4 = st.tabs([
            "Price vs Time & Volatility", 
            "Greeks vs Stock Price", 
            "Price Surface", 
            "What-If Scenarios"
        ])
        
        with sens_tab1:
            # Create a grid of time and volatility values
            time_values = np.linspace(max(0.01, T - 1), T + 1, 20)
            vol_values = np.linspace(max(0.05, sigma - 0.2), sigma + 0.2, 20)
            
            # Calculate price matrix
            price_matrix = np.zeros((len(time_values), len(vol_values)))
            
            for i, t in enumerate(time_values):
                for j, v in enumerate(vol_values):
                    price_matrix[i, j] = warrant_pricing(S, K, t, r, v, dividend_yield, num_warrants, num_shares)
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=price_matrix,
                x=vol_values,
                y=time_values,
                colorscale='Viridis',
                colorbar=dict(title='Warrant Price ($)')
            ))
            
            # Add marker for current values
            fig.add_trace(go.Scatter(
                x=[sigma],
                y=[T],
                mode='markers',
                marker=dict(
                    color='red',
                    size=10,
                    symbol='x'
                ),
                name='Current Parameters'
            ))
            
            # Update layout
            fig.update_layout(
                title='Warrant Price Sensitivity to Time and Volatility',
                xaxis_title='Volatility',
                yaxis_title='Time to Expiration (years)',
                xaxis=dict(tickformat='.0%'),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with sens_tab2:
            # Create stock price range
            price_range = np.linspace(max(0.1, S * 0.5), S * 1.5, 100)
            
            # Calculate Greeks for each price point
            delta_values = []
            gamma_values = []
            theta_values = []
            vega_values = []
            rho_values = []
            
            for p in price_range:
                greeks = calculate_greeks(p, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
                delta_values.append(greeks['delta'])
                gamma_values.append(greeks['gamma'])
                theta_values.append(greeks['theta'])
                vega_values.append(greeks['vega'])
                rho_values.append(greeks['rho'])
            
            # Create figure
            fig = go.Figure()
            
            # Add traces for each Greek
            fig.add_trace(go.Scatter(x=price_range, y=delta_values, mode='lines', name='Delta'))
            fig.add_trace(go.Scatter(x=price_range, y=gamma_values, mode='lines', name='Gamma'))
            fig.add_trace(go.Scatter(x=price_range, y=[v/10 for v in vega_values], mode='lines', name='Vega/10'))
            fig.add_trace(go.Scatter(x=price_range, y=[t/100 for t in theta_values], mode='lines', name='Theta/100'))
            fig.add_trace(go.Scatter(x=price_range, y=[r/10 for r in rho_values], mode='lines', name='Rho/10'))
            
            # Add vertical line at current stock price
            fig.add_vline(x=S, line_dash="dash", line_color="red")
            
            # Update layout
            fig.update_layout(
                title='Greeks vs Stock Price',
                xaxis_title='Stock Price ($)',
                yaxis_title='Greek Value (Scaled)',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <div class="highlight info-text">
            <strong>Note:</strong> Some Greeks are scaled to fit on the same chart:
            <ul>
                <li>Vega is divided by 10</li>
                <li>Theta is divided by 100</li>
                <li>Rho is divided by 10</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with sens_tab3:
            # Create grid of stock prices and times to expiry
            price_range = np.linspace(max(0.1, S * 0.5), S * 1.5, 30)
            time_range = np.linspace(max(0.01, T * 0.2), T, 30)
            
            # Create meshgrid
            price_grid, time_grid = np.meshgrid(price_range, time_range)
            z_values = np.zeros_like(price_grid)
            
            # Calculate warrant prices
            for i in range(len(time_range)):
                for j in range(len(price_range)):
                    z_values[i, j] = warrant_pricing(
                        price_grid[i, j], K, time_grid[i, j], r, sigma, 
                        dividend_yield, num_warrants, num_shares
                    )
            
            # Create 3D surface plot
            fig = go.Figure(data=[go.Surface(z=z_values, x=price_range, y=time_range)])
            
            # Update layout
            fig.update_layout(
                title='Warrant Price Surface',
                scene=dict(
                    xaxis_title='Stock Price ($)',
                    yaxis_title='Time to Expiry (years)',
                    zaxis_title='Warrant Price ($)'
                ),
                height=700
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with sens_tab4:
            st.markdown('<p class="info-text">Analyze how changes in parameters affect warrant price</p>', unsafe_allow_html=True)
            
            # Create columns for scenario inputs
            col1, col2, col3 = st.columns(3)
            
            # Base scenario is the current parameters
            base_price = warrant_pricing(S, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
            
            scenarios = []
            
            # Scenario 1: Stock price change
            with col1:
                st.markdown("##### Stock Price Change")
                stock_change = st.slider("Stock Price Change (%)", -50, 100, 0)
                new_stock = S * (1 + stock_change/100)
                new_price = warrant_pricing(new_stock, K, T, r, sigma, dividend_yield, num_warrants, num_shares)
                st.metric("New Warrant Price", f"${new_price:.4f}", f"{(new_price - base_price)/base_price:.2%}")
                scenarios.append(("Stock Price Change", stock_change, new_price, (new_price - base_price)/base_price))
            
            # Scenario 2: Volatility change
            with col2:
                st.markdown("##### Volatility Change")
                vol_change = st.slider("Volatility Change (% points)", -20, 20, 0)
                new_vol = max(0.01, sigma + vol_change/100)
                new_price = warrant_pricing(S, K, T, r, new_vol, dividend_yield, num_warrants, num_shares)
                st.metric("New Warrant Price", f"${new_price:.4f}", f"{(new_price - base_price)/base_price:.2%}")
                scenarios.append(("Volatility Change", vol_change, new_price, (new_price - base_price)/base_price))
            
            # Scenario 3: Time decay
            with col3:
                st.markdown("##### Time Decay")
                time_decay = st.slider("Time Passed (months)", 0, int(T*12), 0)
                new_time = max(0.01, T - time_decay/12)
                new_price = warrant_pricing(S, K, new_time, r, sigma, dividend_yield, num_warrants, num_shares)
                st.metric("New Warrant Price", f"${new_price:.4f}", f"{(new_price - base_price)/base_price:.2%}")
                scenarios.append(("Time Decay", time_decay, new_price, (new_price - base_price)/base_price))
            
            # Create a bar chart comparing scenarios
            scenario_df = pd.DataFrame(scenarios, columns=["Scenario", "Change", "New Price", "Percent Change"])
            
            fig = px.bar(
                scenario_df, 
                x="Scenario", 
                y="Percent Change",
                color="Percent Change",
                color_continuous_scale=["red", "lightgrey", "green"],
                text_auto='.2%',
                title="Impact of Parameter Changes on Warrant Price"
            )
            
            # Update layout
            fig.update_layout(yaxis_tickformat='.0%')
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        if 'stock_data' in st.session_state:
            data = st.session_state.stock_data
            info = st.session_state.stock_info
            
            # Display stock information
            st.markdown('<p class="sub-header">Stock Information</p>', unsafe_allow_html=True)
            
            # Create two columns
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Display company information
                if 'longName' in info:
                    st.markdown(f"### {info.get('longName', ticker_input)}")
                
                # Display key metrics
                metrics = {
                    'Current Price': f"${data['Close'].iloc[-1]:.2f}",
                    'Market Cap': f"${info.get('marketCap', 0)/1e9:.2f}B" if 'marketCap' in info else 'N/A',
                    '52-Week Range': f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}" if 'fiftyTwoWeekLow' in info else 'N/A',
                    'Dividend Yield': f"{info.get('dividendYield', 0)*100:.2f}%" if 'dividendYield' in info else 'N/A',
                    'Beta': f"{info.get('beta', 0):.2f}" if 'beta' in info else 'N/A',
                    'P/E Ratio': f"{info.get('trailingPE', 0):.2f}" if 'trailingPE' in info else 'N/A'
                }
                
                st.dataframe(pd.DataFrame({
                    'Metric': list(metrics.keys()),
                    'Value': list(metrics.values())
                }), hide_index=True)
                
                # Brief description
                if 'longBusinessSummary' in info:
                    with st.expander("Company Description"):
                        st.write(info['longBusinessSummary'])
            
            with col2:
                # Plot stock price history
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=data.index, 
                    y=data['Close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(color='#1E88E5', width=2)
                ))
                
                # Add volume as bar chart on secondary y-axis
                fig.add_trace(go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    yaxis='y2',
                    marker=dict(color='rgba(30, 136, 229, 0.2)')
                ))
                
                # Update layout
                fig.update_layout(
                    title=f"{ticker_input} Stock Price History",
                    xaxis_title='Date',
                    yaxis_title='Price ($)',
                    yaxis2=dict(
                        title='Volume',
                        titlefont=dict(color='rgba(30, 136, 229, 0.5)'),
                        tickfont=dict(color='rgba(30, 136, 229, 0.5)'),
                        overlaying='y',
                        side='right'
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Display options data if available
            if st.session_state.options_data is not None:
                st.markdown('<p class="sub-header">Options Data</p>', unsafe_allow_html=True)
                
                options = st.session_state.options_data
                expiry_dates = options['expiry_dates']
                
                # Create expiry date selector
                selected_expiry = st.selectbox("Select Expiry Date", expiry_dates)
                
                # Get option chain for selected expiry
                try:
                    opt_chain = yf.Ticker(ticker_input).option_chain(selected_expiry)
                    calls = opt_chain.calls
                    puts = opt_chain.puts
                    
                    # Create tabs for calls and puts
                    opt_tab1, opt_tab2 = st.tabs(["Calls", "Puts"])
                    
                    with opt_tab1:
                        # Display calls
                        calls_display = calls[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']]
                        calls_display.columns = ['Strike', 'Last Price', 'Bid', 'Ask', 'Volume', 'Open Interest', 'Implied Volatility']
                        calls_display['Implied Volatility'] = calls_display['Implied Volatility'].map(lambda x: f"{x:.2%}")
                        
                        st.dataframe(calls_display)
                    
                    with opt_tab2:
                        # Display puts
                        puts_display = puts[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']]
                        puts_display.columns = ['Strike', 'Last Price', 'Bid', 'Ask', 'Volume', 'Open Interest', 'Implied Volatility']
                        puts_display['Implied Volatility'] = puts_display['Implied Volatility'].map(lambda x: f"{x:.2%}")
                        
                        st.dataframe(puts_display)
                    
                    # Plot implied volatility smile
                    fig = go.Figure()
                    
                    # Add calls IV
                    fig.add_trace(go.Scatter(
                        x=calls['strike'],
                        y=calls['impliedVolatility'],
                        mode='markers+lines',
                        name='Calls IV',
                        marker=dict(color='#1E88E5', size=8)
                    ))
                    
                    # Add puts IV
                    fig.add_trace(go.Scatter(
                        x=puts['strike'],
                        y=puts['impliedVolatility'],
                        mode='markers+lines',
                        name='Puts IV',
                        marker=dict(color='#FFC107', size=8)
                    ))
                    
                    # Add vertical line at current price
                    fig.add_vline(x=data['Close'].iloc[-1], line_dash="dash", line_color="red")
                    
                    # Update layout
                    fig.update_layout(
                        title=f"Implied Volatility Smile ({selected_expiry})",
                        xaxis_title='Strike Price ($)',
                        yaxis_title='Implied Volatility',
                        yaxis_tickformat='.0%',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error fetching option chain: {str(e)}")
            
            # Add a real-time data update feature
            st.markdown('<p class="sub-header">Real-Time Updates</p>', unsafe_allow_html=True)
            
            auto_refresh = st.checkbox("Enable Auto-Refresh (Every 5 Minutes)")
            manual_refresh = st.button("Refresh Data Now")
            
            if manual_refresh:
                st.experimental_rerun()
            
            if auto_refresh:
                st.write("Auto-refresh is enabled. Data will update every 5 minutes.")
                # Add a placeholder to show last refresh time
                refresh_placeholder = st.empty()
                refresh_placeholder.info(f"Last refreshed at {datetime.now().strftime('%H:%M:%S')}")
                
                # Schedule next refresh with countdown
                if 'refresh_time' not in st.session_state:
                    st.session_state.refresh_time = datetime.now() + timedelta(minutes=5)
                
                # Display countdown
                time_left = max(0, (st.session_state.refresh_time - datetime.now()).total_seconds())
                st.write(f"Next refresh in: {int(time_left // 60)}:{int(time_left % 60):02d}")
        else:
            st.markdown('<p class="sub-header">Market Data</p>', unsafe_allow_html=True)
            st.info("Use the 'Stock Lookup' tab in the sidebar to fetch real-time market data.")

    # Add footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666;">
        <p>This Warrant Pricing Calculator uses a dilution-adjusted Black-Scholes model for pricing. 
        Developed for educational purposes, not financial advice.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()