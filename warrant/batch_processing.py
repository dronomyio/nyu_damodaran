import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from utils import batch_process_warrants, get_stock_data, estimate_volatility, get_risk_free_rate

def batch_page():
    """
    Batch processing page for analyzing multiple warrants simultaneously.
    """
    # Add a row with a back button and the title
    col1, col2, col3 = st.columns([1, 10, 1])
    
    with col1:
        st.markdown('<a href="http://localhost/" target="_self"><button style="background-color: #f0f2f6; border: none; border-radius: 4px; padding: 8px 16px; font-size: 14px; cursor: pointer;">← Home</button></a>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<p class="main-header" style="text-align: center;">Batch Warrant Analysis</p>', unsafe_allow_html=True)
        st.markdown('<p class="info-text" style="text-align: center;">Analyze multiple warrants simultaneously for portfolio management or comparative analysis.</p>', unsafe_allow_html=True)
    
    # Create tabs for different batch processing methods
    tab1, tab2 = st.tabs(["Manual Entry", "File Upload"])
    
    with tab1:
        st.markdown("### Manual Entry of Multiple Warrants")
        
        # Initialize batch data if not exists
        if 'batch_warrants' not in st.session_state:
            st.session_state.batch_warrants = []
        
        # Create a form for adding a new warrant
        with st.form("add_warrant_form"):
            st.markdown("#### Add New Warrant")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ticker = st.text_input("Ticker Symbol", "AAPL")
                S = st.number_input("Stock Price ($)", min_value=0.01, value=10.0, step=0.01)
                K = st.number_input("Strike Price ($)", min_value=0.01, value=10.0, step=0.01)
                T = st.number_input("Time to Expiration (years)", min_value=0.01, value=5.0, step=0.01)
            
            with col2:
                sigma = st.number_input("Volatility (annual)", min_value=0.01, max_value=2.0, value=0.4, step=0.01)
                r = st.number_input("Risk-free Rate", min_value=0.0, max_value=0.2, value=0.02, step=0.001, format="%.3f")
                dividend_yield = st.number_input("Dividend Yield", min_value=0.0, max_value=0.2, value=0.0, step=0.001, format="%.3f")
                
                # Use default values for dilution parameters
                num_warrants = st.number_input("Number of Warrants (thousands)", min_value=1, value=100, step=1)
                num_shares = st.number_input("Number of Shares (thousands)", min_value=1, value=1000, step=1)
            
            # Add button
            submit_button = st.form_submit_button("Add Warrant")
            
            if submit_button:
                # Add warrant to session state
                st.session_state.batch_warrants.append({
                    'ticker': ticker,
                    'S': S,
                    'K': K,
                    'T': T,
                    'sigma': sigma,
                    'r': r,
                    'dividend_yield': dividend_yield,
                    'num_warrants': num_warrants * 1000,  # Convert to actual numbers
                    'num_shares': num_shares * 1000       # Convert to actual numbers
                })
                st.success(f"Added {ticker} warrant to batch")
        
        # Lookup button for fetching real data for a list of tickers
        st.markdown("### Lookup Multiple Tickers")
        
        with st.form("lookup_tickers_form"):
            tickers_input = st.text_input("Enter Ticker Symbols (comma-separated)", "AAPL, MSFT, GOOGL")
            lookup_button = st.form_submit_button("Lookup Tickers")
            
            if lookup_button:
                tickers = [t.strip() for t in tickers_input.split(",")]
                
                with st.spinner(f"Fetching data for {len(tickers)} tickers..."):
                    for ticker in tickers:
                        if not ticker:
                            continue
                        
                        # Get stock data
                        stock_result = get_stock_data(ticker)
                        
                        if stock_result['success']:
                            data = stock_result['data']
                            info = stock_result['info']
                            
                            # Current stock price
                            current_price = data['Close'].iloc[-1]
                            
                            # Volatility estimate
                            est_vol = estimate_volatility(data)
                            vol = min(max(est_vol, 0.1), 1.5)
                            
                            # Dividend yield
                            if 'dividendYield' in info and info['dividendYield'] is not None:
                                div_yield = info['dividendYield']
                            else:
                                div_yield = 0.0
                                
                            # Shares outstanding (in thousands)
                            if 'sharesOutstanding' in info and info['sharesOutstanding'] is not None:
                                shares = info['sharesOutstanding']
                            else:
                                shares = 1000000  # Default
                            
                            # Time to expiry - default to 5 years for warrants
                            T = 5.0
                            
                            # Strike price - set to current price by default
                            K = current_price
                            
                            # Risk-free rate
                            r = get_risk_free_rate()
                            
                            # Number of warrants - assume 10% of shares by default
                            warrants = shares * 0.1
                            
                            # Add to batch
                            st.session_state.batch_warrants.append({
                                'ticker': ticker,
                                'S': current_price,
                                'K': K,
                                'T': T,
                                'sigma': vol,
                                'r': r,
                                'dividend_yield': div_yield,
                                'num_warrants': warrants,
                                'num_shares': shares
                            })
                            
                            st.success(f"Added {ticker} warrant to batch with real-time data")
                        else:
                            st.error(f"Error fetching data for {ticker}: {stock_result['error']}")
        
        # Display current batch
        if st.session_state.batch_warrants:
            st.markdown("### Current Batch")
            
            # Convert to DataFrame for display
            batch_df = pd.DataFrame(st.session_state.batch_warrants)
            
            # Display in an editable form
            edited_df = st.data_editor(
                batch_df,
                column_config={
                    "ticker": "Ticker",
                    "S": st.column_config.NumberColumn("Stock Price ($)", format="$%.2f"),
                    "K": st.column_config.NumberColumn("Strike Price ($)", format="$%.2f"),
                    "T": st.column_config.NumberColumn("Time to Expiry (years)", format="%.2f"),
                    "sigma": st.column_config.NumberColumn("Volatility", format="%.2f"),
                    "r": st.column_config.NumberColumn("Risk-free Rate", format="%.3f"),
                    "dividend_yield": st.column_config.NumberColumn("Dividend Yield", format="%.3f"),
                    "num_warrants": st.column_config.NumberColumn("Warrants (thousands)", format="%.0f"),
                    "num_shares": st.column_config.NumberColumn("Shares (thousands)", format="%.0f")
                },
                hide_index=True,
                num_rows="dynamic"
            )
            
            # Update session state with edited values
            st.session_state.batch_warrants = edited_df.to_dict('records')
            
            # Clear batch button
            if st.button("Clear Batch"):
                st.session_state.batch_warrants = []
                st.success("Batch cleared")
                st.experimental_rerun()
    
    with tab2:
        st.markdown("### Upload File with Warrant Data")
        
        # File upload
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                # Check file type and read accordingly
                if uploaded_file.name.endswith('.csv'):
                    data = pd.read_csv(uploaded_file)
                else:
                    data = pd.read_excel(uploaded_file)
                
                # Display the uploaded data
                st.write("Preview of uploaded data:")
                st.dataframe(data.head())
                
                # Map columns to warrant parameters
                st.markdown("### Map Columns to Warrant Parameters")
                
                # Get column names
                columns = data.columns.tolist()
                
                # Create mapping
                col1, col2 = st.columns(2)
                
                with col1:
                    ticker_col = st.selectbox("Ticker Column", ["None"] + columns, index=0)
                    S_col = st.selectbox("Stock Price Column", ["None"] + columns, index=0)
                    K_col = st.selectbox("Strike Price Column", ["None"] + columns, index=0)
                    T_col = st.selectbox("Time to Expiry Column", ["None"] + columns, index=0)
                
                with col2:
                    sigma_col = st.selectbox("Volatility Column", ["None"] + columns, index=0)
                    r_col = st.selectbox("Risk-free Rate Column", ["None"] + columns, index=0)
                    dividend_col = st.selectbox("Dividend Yield Column", ["None"] + columns, index=0)
                    
                    # Optional columns
                    warrants_col = st.selectbox("Number of Warrants Column", ["None"] + columns, index=0)
                    shares_col = st.selectbox("Number of Shares Column", ["None"] + columns, index=0)
                
                # Process button
                if st.button("Process Uploaded Data"):
                    # Clear existing batch
                    st.session_state.batch_warrants = []
                    
                    # Process each row
                    for _, row in data.iterrows():
                        warrant = {}
                        
                        # Add required parameters
                        if ticker_col != "None":
                            warrant['ticker'] = str(row[ticker_col])
                        else:
                            warrant['ticker'] = f"Warrant_{_}"
                            
                        if S_col != "None":
                            warrant['S'] = float(row[S_col])
                        else:
                            warrant['S'] = 10.0
                            
                        if K_col != "None":
                            warrant['K'] = float(row[K_col])
                        else:
                            warrant['K'] = 10.0
                            
                        if T_col != "None":
                            warrant['T'] = float(row[T_col])
                        else:
                            warrant['T'] = 5.0
                            
                        if sigma_col != "None":
                            warrant['sigma'] = float(row[sigma_col])
                        else:
                            warrant['sigma'] = 0.4
                            
                        if r_col != "None":
                            warrant['r'] = float(row[r_col])
                        else:
                            warrant['r'] = 0.02
                            
                        if dividend_col != "None":
                            warrant['dividend_yield'] = float(row[dividend_col])
                        else:
                            warrant['dividend_yield'] = 0.0
                            
                        # Add optional parameters
                        if warrants_col != "None":
                            warrant['num_warrants'] = float(row[warrants_col])
                        else:
                            warrant['num_warrants'] = 100000
                            
                        if shares_col != "None":
                            warrant['num_shares'] = float(row[shares_col])
                        else:
                            warrant['num_shares'] = 1000000
                        
                        # Add to batch
                        st.session_state.batch_warrants.append(warrant)
                    
                    st.success(f"Processed {len(data)} warrants from uploaded file")
                    st.experimental_rerun()
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    # Process batch if warrants exist
    if 'batch_warrants' in st.session_state and st.session_state.batch_warrants:
        st.markdown("### Batch Analysis Results")
        
        # Process the batch
        results = batch_process_warrants(st.session_state.batch_warrants)
        
        # Display results
        st.dataframe(results)
        
        # Create comparison visualizations
        st.markdown("### Comparative Analysis")
        
        # Create tabs for different visualizations
        vis_tab1, vis_tab2, vis_tab3 = st.tabs(["Price Comparison", "Greeks Comparison", "Risk Analysis"])
        
        with vis_tab1:
            # Price comparison chart
            fig = px.bar(
                results,
                x='Ticker',
                y='Warrant Price',
                color='Warrant Price',
                title='Warrant Price Comparison',
                labels={'Warrant Price': 'Price ($)', 'Ticker': 'Stock Ticker'}
            )
            
            # Add price labels
            fig.update_traces(texttemplate='$%{y:.2f}', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Price to stock price ratio
            results['Price Ratio'] = results['Warrant Price'] / results['Stock Price']
            
            fig = px.bar(
                results,
                x='Ticker',
                y='Price Ratio',
                color='Price Ratio',
                title='Warrant Price to Stock Price Ratio',
                labels={'Price Ratio': 'Ratio', 'Ticker': 'Stock Ticker'}
            )
            
            # Add ratio labels
            fig.update_traces(texttemplate='%{y:.2f}', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
        with vis_tab2:
            # Greeks comparison
            greek_to_plot = st.selectbox(
                "Select Greek to Compare",
                ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho']
            )
            
            fig = px.bar(
                results,
                x='Ticker',
                y=greek_to_plot,
                color=greek_to_plot,
                title=f'{greek_to_plot} Comparison',
                labels={greek_to_plot: greek_to_plot, 'Ticker': 'Stock Ticker'}
            )
            
            # Add value labels
            fig.update_traces(texttemplate='%{y:.4f}', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Radar chart for all Greeks
            # Normalize Greeks for better visualization
            radar_data = results.copy()
            
            for greek in ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho']:
                # Handle zero values to prevent division by zero
                if radar_data[greek].abs().max() > 0:
                    radar_data[greek + '_norm'] = radar_data[greek] / radar_data[greek].abs().max()
                else:
                    radar_data[greek + '_norm'] = radar_data[greek]
            
            # Create radar chart
            fig = go.Figure()
            
            for i, row in radar_data.iterrows():
                fig.add_trace(go.Scatterpolar(
                    r=[row['Delta_norm'], row['Gamma_norm'], row['Theta_norm'], row['Vega_norm'], row['Rho_norm']],
                    theta=['Delta', 'Gamma', 'Theta', 'Vega', 'Rho'],
                    fill='toself',
                    name=row['Ticker']
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[-1, 1]
                    )),
                showlegend=True,
                title="Normalized Greeks Comparison (Radar Chart)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with vis_tab3:
            st.markdown("#### Risk Analysis")
            
            # Create a scatter plot of price vs time to expiration
            fig = px.scatter(
                results,
                x='Time to Expiration',
                y='Warrant Price',
                size='Volatility',
                color='Ticker',
                hover_data=['Strike Price', 'Stock Price', 'Delta', 'Gamma'],
                title='Warrant Price vs Time to Expiration',
                labels={
                    'Time to Expiration': 'Time to Expiration (years)',
                    'Warrant Price': 'Warrant Price ($)',
                    'Volatility': 'Volatility'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a bubble chart of volatility vs moneyness
            results['Moneyness'] = results['Stock Price'] / results['Strike Price']
            
            fig = px.scatter(
                results,
                x='Moneyness',
                y='Volatility',
                size='Warrant Price',
                color='Ticker',
                hover_data=['Strike Price', 'Stock Price', 'Delta', 'Gamma'],
                title='Volatility vs Moneyness',
                labels={
                    'Moneyness': 'Moneyness (S/K)',
                    'Volatility': 'Volatility',
                    'Warrant Price': 'Warrant Price ($)'
                }
            )
            
            # Add a vertical line at moneyness = 1
            fig.add_vline(x=1, line_dash="dash", line_color="gray")
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Add export functionality
        st.markdown("### Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export to CSV
            csv = results.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"warrant_batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export to Excel
            buffer = pd.ExcelWriter(f"warrant_batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", engine='xlsxwriter')
            results.to_excel(buffer, index=False, sheet_name='Warrant Analysis')
            buffer.close()
            
            # TODO: Add Excel export when supported in Streamlit
            st.info("Excel export will be available in a future update")
    else:
        st.info("Add warrants to the batch or upload a file to see analysis results")

if __name__ == "__main__":
    batch_page()