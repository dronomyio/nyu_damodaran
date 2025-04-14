import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import time
from utils import get_stock_data, estimate_volatility, get_risk_free_rate

# Set page configuration
st.set_page_config(
    page_title="Market Monitor",
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
</style>
""", unsafe_allow_html=True)

# Function to fetch market indices data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_market_indices():
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000',
        '^VIX': 'VIX',
        '^TNX': '10Y Treasury Yield'
    }
    
    results = {}
    
    for symbol, name in indices.items():
        try:
            index = yf.Ticker(symbol)
            data = index.history(period="1d")
            
            if not data.empty:
                last_price = data['Close'].iloc[-1]
                prev_close = data['Open'].iloc[0]
                change = last_price - prev_close
                pct_change = change / prev_close * 100
                
                results[name] = {
                    'symbol': symbol,
                    'last_price': last_price,
                    'change': change,
                    'pct_change': pct_change
                }
            else:
                results[name] = {
                    'symbol': symbol,
                    'last_price': 0,
                    'change': 0,
                    'pct_change': 0
                }
        except Exception as e:
            results[name] = {
                'symbol': symbol,
                'last_price': 0,
                'change': 0,
                'pct_change': 0,
                'error': str(e)
            }
    
    return results

# Function to fetch data for multiple stocks
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_stocks_data(tickers, period="1mo"):
    data = yf.download(tickers, period=period, group_by='ticker')
    return data

# Function to get sector performance
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_sector_performance():
    # Use sector ETFs as proxies
    sectors = {
        'XLF': 'Financials',
        'XLK': 'Technology',
        'XLE': 'Energy',
        'XLV': 'Healthcare',
        'XLI': 'Industrials',
        'XLP': 'Consumer Staples',
        'XLY': 'Consumer Discretionary',
        'XLB': 'Materials',
        'XLU': 'Utilities',
        'XLRE': 'Real Estate',
        'XLC': 'Communication Services'
    }
    
    results = []
    
    for symbol, name in sectors.items():
        try:
            sector = yf.Ticker(symbol)
            data = sector.history(period="1mo")
            
            if not data.empty:
                last_price = data['Close'].iloc[-1]
                month_start = data['Open'].iloc[0]
                month_change = last_price - month_start
                month_pct_change = month_change / month_start * 100
                
                # Calculate YTD performance
                ytd_data = sector.history(period="ytd")
                ytd_start = ytd_data['Open'].iloc[0]
                ytd_change = last_price - ytd_start
                ytd_pct_change = ytd_change / ytd_start * 100
                
                results.append({
                    'Sector': name,
                    'Symbol': symbol,
                    'Price': last_price,
                    '1-Month %': month_pct_change,
                    'YTD %': ytd_pct_change
                })
            else:
                results.append({
                    'Sector': name,
                    'Symbol': symbol,
                    'Price': 0,
                    '1-Month %': 0,
                    'YTD %': 0
                })
        except Exception as e:
            results.append({
                'Sector': name,
                'Symbol': symbol,
                'Price': 0,
                '1-Month %': 0,
                'YTD %': 0,
                'Error': str(e)
            })
    
    return pd.DataFrame(results)

# Function to get top gainers and losers
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_top_movers():
    # This is a simplified version - in a real app, you might use an API that provides this data
    # Here we'll use a predefined list of large cap stocks and calculate the top movers from that
    large_caps = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'PG', 
                 'UNH', 'HD', 'BAC', 'XOM', 'CSCO', 'PFE', 'CMCSA', 'KO', 'DIS', 'VZ']
    
    try:
        data = yf.download(large_caps, period="1d", group_by='ticker')
        
        results = []
        
        for ticker in large_caps:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty:
                    last_price = ticker_data['Close'].iloc[-1]
                    prev_close = ticker_data['Open'].iloc[0]
                    change = last_price - prev_close
                    pct_change = change / prev_close * 100
                    
                    results.append({
                        'Ticker': ticker,
                        'Price': last_price,
                        'Change': change,
                        '% Change': pct_change
                    })
        
        # Create DataFrame and sort
        df = pd.DataFrame(results)
        gainers = df.sort_values('% Change', ascending=False).head(5)
        losers = df.sort_values('% Change', ascending=True).head(5)
        
        return gainers, losers
    except Exception as e:
        # Return empty frames in case of error
        return pd.DataFrame(), pd.DataFrame()

# Main function for market monitor page
def market_monitor():
    st.markdown('<p class="main-header">Market Monitor</p>', unsafe_allow_html=True)
    st.markdown('<p class="info-text">Real-time market data and analysis for financial decision-making.</p>', unsafe_allow_html=True)
    
    # Get current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a refresh button
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("Refresh Data"):
            # Clear cache to force refresh
            get_market_indices.clear()
            get_sector_performance.clear()
            get_top_movers.clear()
            st.experimental_rerun()
    
    with col2:
        st.markdown(f"<p style='text-align: center;'>Last updated: {current_time}</p>", unsafe_allow_html=True)
    
    with col3:
        auto_refresh = st.checkbox("Auto-refresh (5 min)", value=False)
        if auto_refresh:
            # Add a countdown timer
            time_placeholder = st.empty()
            next_refresh = datetime.now() + timedelta(minutes=5)
            remaining = (next_refresh - datetime.now()).total_seconds()
            time_placeholder.markdown(f"<p style='text-align: right;'>Next refresh in: {int(remaining // 60)}m {int(remaining % 60)}s</p>", unsafe_allow_html=True)
    
    # Create tabs for different market views
    tab1, tab2, tab3, tab4 = st.tabs(["Market Overview", "Sector Performance", "Stock Watchlist", "Volatility Analysis"])
    
    with tab1:
        st.markdown("### Market Indices")
        
        # Fetch market indices data
        indices_data = get_market_indices()
        
        # Create metrics row
        cols = st.columns(len(indices_data))
        
        for i, (name, data) in enumerate(indices_data.items()):
            with cols[i]:
                delta_color = "normal"
                if name == 'VIX':  # For VIX, higher is often considered negative for markets
                    delta_color = "inverse"
                
                if name == '10Y Treasury Yield':
                    # Show as percentage
                    st.metric(
                        name,
                        f"{data['last_price']:.2f}%",
                        f"{data['change']:.2f}%",
                        delta_color=delta_color
                    )
                else:
                    # Show with 2 decimals
                    st.metric(
                        name,
                        f"{data['last_price']:.2f}",
                        f"{data['pct_change']:.2f}%",
                        delta_color=delta_color
                    )
        
        # Get historical data for the indices
        symbols = [data['symbol'] for name, data in indices_data.items()]
        historical_data = get_stocks_data(symbols, period="6mo")
        
        # Create a chart for index comparison
        st.markdown("### Index Performance (6 Months)")
        
        # Normalize the data to 100 at the starting point
        start_date = historical_data.index[0]
        
        fig = go.Figure()
        
        for symbol, name in [(data['symbol'], name) for name, data in indices_data.items()]:
            if symbol in historical_data:
                df = historical_data[symbol]['Close']
                normalized = df / df.iloc[0] * 100
                
                fig.add_trace(go.Scatter(
                    x=normalized.index,
                    y=normalized.values,
                    mode='lines',
                    name=name
                ))
        
        # Update layout
        fig.update_layout(
            title="Relative Performance (Normalized to 100)",
            xaxis_title="Date",
            yaxis_title="Normalized Value",
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add top gainers and losers
        st.markdown("### Today's Top Movers")
        
        gainers, losers = get_top_movers()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top Gainers")
            if not gainers.empty:
                # Format the data
                gainers_display = gainers.copy()
                gainers_display['Price'] = gainers_display['Price'].map('${:.2f}'.format)
                gainers_display['Change'] = gainers_display['Change'].map('${:.2f}'.format)
                gainers_display['% Change'] = gainers_display['% Change'].map('{:.2f}%'.format)
                
                st.dataframe(gainers_display, use_container_width=True)
            else:
                st.info("No data available for top gainers")
        
        with col2:
            st.markdown("#### Top Losers")
            if not losers.empty:
                # Format the data
                losers_display = losers.copy()
                losers_display['Price'] = losers_display['Price'].map('${:.2f}'.format)
                losers_display['Change'] = losers_display['Change'].map('${:.2f}'.format)
                losers_display['% Change'] = losers_display['% Change'].map('{:.2f}%'.format)
                
                st.dataframe(losers_display, use_container_width=True)
            else:
                st.info("No data available for top losers")
    
    with tab2:
        st.markdown("### Sector Performance")
        
        # Fetch sector performance data
        sector_data = get_sector_performance()
        
        # Create a bar chart for 1-month performance
        fig = px.bar(
            sector_data, 
            x='Sector', 
            y='1-Month %',
            color='1-Month %',
            color_continuous_scale=['red', 'lightgrey', 'green'],
            title="1-Month Sector Performance",
            text='1-Month %'
        )
        
        # Format text and add percent sign
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        
        # Add a horizontal line at 0%
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        # Update layout
        fig.update_layout(
            xaxis_title="Sector",
            yaxis_title="Percent Change (%)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Create a bar chart for YTD performance
        fig = px.bar(
            sector_data, 
            x='Sector', 
            y='YTD %',
            color='YTD %',
            color_continuous_scale=['red', 'lightgrey', 'green'],
            title="Year-to-Date Sector Performance",
            text='YTD %'
        )
        
        # Format text and add percent sign
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        
        # Add a horizontal line at 0%
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        
        # Update layout
        fig.update_layout(
            xaxis_title="Sector",
            yaxis_title="Percent Change (%)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display sector data in a table
        st.markdown("### Sector Data")
        
        # Format the data for display
        display_df = sector_data.copy()
        display_df['Price'] = display_df['Price'].map('${:.2f}'.format)
        display_df['1-Month %'] = display_df['1-Month %'].map('{:.2f}%'.format)
        display_df['YTD %'] = display_df['YTD %'].map('{:.2f}%'.format)
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab3:
        st.markdown("### Stock Watchlist")
        
        # Create a watchlist input
        default_watchlist = "AAPL, MSFT, GOOGL, AMZN, TSLA"
        
        watchlist_input = st.text_input(
            "Enter stock symbols separated by commas",
            value=default_watchlist
        )
        
        # Parse the watchlist
        watchlist = [symbol.strip() for symbol in watchlist_input.split(",")]
        
        if watchlist:
            # Fetch data for the watchlist
            try:
                watchlist_data = yf.download(watchlist, period="1d", group_by='ticker')
                historical_data = yf.download(watchlist, period="1y", group_by='ticker')
                
                # Create a table with current prices and performance
                watchlist_table = []
                
                for ticker in watchlist:
                    if ticker in watchlist_data:
                        ticker_data = watchlist_data[ticker]
                        if not ticker_data.empty:
                            last_price = ticker_data['Close'].iloc[-1]
                            open_price = ticker_data['Open'].iloc[0]
                            change = last_price - open_price
                            pct_change = change / open_price * 100
                            
                            # Get 52-week range
                            if ticker in historical_data:
                                year_data = historical_data[ticker]
                                week_52_high = year_data['High'].max()
                                week_52_low = year_data['Low'].min()
                                week_52_range = f"${week_52_low:.2f} - ${week_52_high:.2f}"
                            else:
                                week_52_range = "N/A"
                            
                            # Get stock info
                            try:
                                stock_info = yf.Ticker(ticker).info
                                company_name = stock_info.get('longName', ticker)
                                market_cap = stock_info.get('marketCap', None)
                                if market_cap:
                                    market_cap_str = f"${market_cap/1e9:.2f}B"
                                else:
                                    market_cap_str = "N/A"
                                    
                                pe_ratio = stock_info.get('trailingPE', None)
                                if pe_ratio:
                                    pe_ratio_str = f"{pe_ratio:.2f}"
                                else:
                                    pe_ratio_str = "N/A"
                            except:
                                company_name = ticker
                                market_cap_str = "N/A"
                                pe_ratio_str = "N/A"
                            
                            watchlist_table.append({
                                'Symbol': ticker,
                                'Company': company_name,
                                'Last Price': f"${last_price:.2f}",
                                'Change': f"${change:.2f}",
                                '% Change': f"{pct_change:.2f}%",
                                '52-Week Range': week_52_range,
                                'Market Cap': market_cap_str,
                                'P/E Ratio': pe_ratio_str
                            })
                
                # Display the watchlist table
                if watchlist_table:
                    watchlist_df = pd.DataFrame(watchlist_table)
                    st.dataframe(watchlist_df, use_container_width=True)
                    
                    # Create a chart comparing the stocks
                    st.markdown("### Performance Comparison (1 Year)")
                    
                    # Normalize the data to 100 at the starting point
                    fig = go.Figure()
                    
                    for ticker in watchlist:
                        if ticker in historical_data:
                            df = historical_data[ticker]['Close']
                            normalized = df / df.iloc[0] * 100
                            
                            fig.add_trace(go.Scatter(
                                x=normalized.index,
                                y=normalized.values,
                                mode='lines',
                                name=ticker
                            ))
                    
                    # Update layout
                    fig.update_layout(
                        title="Relative Performance (Normalized to 100)",
                        xaxis_title="Date",
                        yaxis_title="Normalized Value",
                        height=500,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available for the specified symbols")
            except Exception as e:
                st.error(f"Error fetching watchlist data: {str(e)}")
        else:
            st.info("Enter stock symbols to create a watchlist")
    
    with tab4:
        st.markdown("### Volatility Analysis")
        
        # Create a volatility input
        vol_symbols_input = st.text_input(
            "Enter stock symbols for volatility analysis (separated by commas)",
            value="SPY, QQQ, IWM, AAPL, MSFT"
        )
        
        # Parse the symbols
        vol_symbols = [symbol.strip() for symbol in vol_symbols_input.split(",")]
        
        # Time period selection
        vol_period = st.selectbox(
            "Select time period for volatility calculation",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=2
        )
        
        if vol_symbols:
            # Fetch data for volatility analysis
            try:
                # Download historical data
                vol_data = yf.download(vol_symbols, period=vol_period, group_by='ticker')
                
                # Calculate volatility for each stock
                vol_results = []
                
                for ticker in vol_symbols:
                    if ticker in vol_data:
                        ticker_data = vol_data[ticker]
                        if not ticker_data.empty:
                            # Calculate returns
                            returns = ticker_data['Close'].pct_change().dropna()
                            
                            # Calculate volatility (annualized)
                            volatility = returns.std() * np.sqrt(252) * 100  # Convert to percentage
                            
                            # Calculate other statistics
                            mean_return = returns.mean() * 252 * 100  # Annualized and converted to percentage
                            skewness = returns.skew()
                            kurtosis = returns.kurtosis()
                            
                            # Sharpe ratio (assuming risk-free rate of 2%)
                            risk_free = 0.02
                            sharpe = (mean_return/100 - risk_free) / (volatility/100)
                            
                            # Maximum drawdown
                            cum_returns = (1 + returns).cumprod()
                            running_max = cum_returns.cummax()
                            drawdown = (cum_returns / running_max - 1) * 100
                            max_drawdown = drawdown.min()
                            
                            # Get stock info
                            try:
                                stock_info = yf.Ticker(ticker).info
                                company_name = stock_info.get('longName', ticker)
                            except:
                                company_name = ticker
                            
                            vol_results.append({
                                'Symbol': ticker,
                                'Name': company_name,
                                'Volatility (%)': volatility,
                                'Ann. Return (%)': mean_return,
                                'Sharpe Ratio': sharpe,
                                'Max Drawdown (%)': max_drawdown,
                                'Skewness': skewness,
                                'Kurtosis': kurtosis
                            })
                
                # Create a DataFrame and display
                if vol_results:
                    vol_df = pd.DataFrame(vol_results)
                    
                    # Sort by volatility
                    vol_df = vol_df.sort_values('Volatility (%)', ascending=False)
                    
                    # Format the data for display
                    display_vol_df = vol_df.copy()
                    display_vol_df['Volatility (%)'] = display_vol_df['Volatility (%)'].map('{:.2f}%'.format)
                    display_vol_df['Ann. Return (%)'] = display_vol_df['Ann. Return (%)'].map('{:.2f}%'.format)
                    display_vol_df['Sharpe Ratio'] = display_vol_df['Sharpe Ratio'].map('{:.2f}'.format)
                    display_vol_df['Max Drawdown (%)'] = display_vol_df['Max Drawdown (%)'].map('{:.2f}%'.format)
                    display_vol_df['Skewness'] = display_vol_df['Skewness'].map('{:.2f}'.format)
                    display_vol_df['Kurtosis'] = display_vol_df['Kurtosis'].map('{:.2f}'.format)
                    
                    st.dataframe(display_vol_df, use_container_width=True)
                    
                    # Create a bar chart of volatility
                    fig = px.bar(
                        vol_df,
                        x='Symbol',
                        y='Volatility (%)',
                        color='Volatility (%)',
                        title=f"Annualized Volatility ({vol_period})",
                        text='Volatility (%)'
                    )
                    
                    # Format text and add percent sign
                    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    
                    # Update layout
                    fig.update_layout(
                        xaxis_title="Symbol",
                        yaxis_title="Annualized Volatility (%)",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create a scatter plot of return vs volatility
                    fig = px.scatter(
                        vol_df,
                        x='Volatility (%)',
                        y='Ann. Return (%)',
                        color='Sharpe Ratio',
                        size='Max Drawdown (%)' * -1,  # Negative so larger drawdowns have smaller bubbles
                        hover_data=['Symbol', 'Name', 'Sharpe Ratio', 'Max Drawdown (%)'],
                        title=f"Risk-Return Analysis ({vol_period})",
                        labels={
                            'Volatility (%)': 'Annualized Volatility (%)',
                            'Ann. Return (%)': 'Annualized Return (%)'
                        }
                    )
                    
                    # Add text labels for each point
                    fig.update_traces(textposition='top center', text=vol_df['Symbol'])
                    
                    # Add a horizontal line at 0% return
                    fig.add_hline(y=0, line_dash="dash", line_color="red")
                    
                    # Update layout
                    fig.update_layout(height=600)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create a correlation heatmap
                    st.markdown("### Return Correlation Matrix")
                    
                    # Create a DataFrame of returns
                    returns_df = pd.DataFrame()
                    
                    for ticker in vol_symbols:
                        if ticker in vol_data:
                            ticker_data = vol_data[ticker]
                            if not ticker_data.empty:
                                returns_df[ticker] = ticker_data['Close'].pct_change().dropna()
                    
                    # Calculate correlation matrix
                    corr_matrix = returns_df.corr()
                    
                    # Create heatmap
                    fig = px.imshow(
                        corr_matrix,
                        text_auto='.2f',
                        color_continuous_scale='RdBu_r',
                        title="Return Correlation Matrix"
                    )
                    
                    # Update layout
                    fig.update_layout(height=600)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available for volatility analysis")
            except Exception as e:
                st.error(f"Error in volatility analysis: {str(e)}")
        else:
            st.info("Enter stock symbols for volatility analysis")

# Run the main function
if __name__ == "__main__":
    market_monitor()
    
    # Add footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666;">
        <p>Market data provided by Yahoo Finance. For educational purposes only.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )