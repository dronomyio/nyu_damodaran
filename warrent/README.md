# Warrant Pricing Calculator

A Streamlit web application for calculating warrant prices using the Black-Scholes model with dilution adjustment.

## Features

- **Interactive Pricing Tool**: Calculate warrant prices and Greeks using the Black-Scholes model with dilution adjustment
- **Real-time Market Data**: Fetch current stock prices, volatility, and dividend yield from Yahoo Finance
- **Visual Analysis**: View sensitivity analysis and interactive charts
- **What-If Scenarios**: Analyze how changes in parameters affect warrant prices
- **Options Data**: View current options chain data and implied volatility smile
- **Batch Processing**: Analyze multiple warrants simultaneously for portfolio management
- **Market Monitor**: Track indices, sectors, and custom watchlists in real-time

## Installation

### Option 1: Standard Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd Blogs/Damodaran
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

### Option 2: Docker Installation

1. Make sure you have Docker and Docker Compose installed

2. Build and run the Docker container:
   ```
   docker-compose up -d
   ```

3. Access the application at http://localhost:8501

## Deployment Options

### Streamlit Cloud

1. Create a free account on [Streamlit Cloud](https://streamlit.io/cloud)
2. Connect your GitHub repository
3. Deploy the app by selecting the repository and branch

### Self-Hosted with Docker

1. Configure Docker on your server
2. Clone this repository and navigate to the project directory
3. Run with Docker Compose:
   ```
   docker-compose up -d
   ```

## Usage

1. **Manual Entry**: Input the warrant parameters manually
   - Stock price, strike price, time to expiration
   - Volatility, risk-free rate, dividend yield
   - Number of warrants and shares outstanding

2. **Stock Lookup**: Use the ticker symbol to fetch real-time market data
   - Automatically updates price, volatility, and dividend yield
   - Displays stock price history and company information
   - Shows options data if available

3. **Batch Analysis**: Process multiple warrants simultaneously
   - Enter parameters manually or upload a CSV/Excel file
   - Compare performance across different securities
   - Visualize results with interactive charts

4. **Market Monitor**: Track real-time market data
   - View index and sector performance
   - Create custom stock watchlists
   - Analyze volatility and correlations

## Technical Background

This tool implements the Black-Scholes model for warrant pricing with dilution adjustment. The key difference between warrants and options is that warrants cause dilution when exercised, which affects the underlying stock price.

The dilution factor is calculated as:
```
dilution_factor = num_shares / (num_shares + num_warrants)
```

The adjusted stock price is:
```
adjusted_S = S * dilution_factor
```

For high-performance scenarios, a CUDA implementation is available in `warrant_pricing.cu`.

## Docker Commands

- Start the application:
  ```
  docker-compose up -d
  ```

- Stop the application:
  ```
  docker-compose down
  ```

- View logs:
  ```
  docker-compose logs -f
  ```

- Rebuild the container after changes:
  ```
  docker-compose up -d --build
  ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on Aswath Damodaran's financial modeling principles
- Uses Yahoo Finance API for real-time market data
- Built with Streamlit, Pandas, and Plotly