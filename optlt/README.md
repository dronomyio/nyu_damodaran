# Long-Term Option Pricing Web Application

A Flask-based web application for pricing long-term options using the Black-Scholes model with dividend adjustment. The application supports real-time market data integration and batch processing capabilities.

## Features

- Black-Scholes option pricing with dividend yield adjustment
- Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Real-time market data integration through Yahoo Finance API
- Batch processing for multiple option calculations
- Redis caching for improved performance
- Celery worker for background tasks
- Dockerized for easy deployment

## Installation

### Using Docker (Recommended)

1. Clone the repository
2. Navigate to the project directory
3. Run the application using Docker Compose:

```bash
docker-compose up
```

### Manual Installation

1. Clone the repository
2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install the requirements:

```bash
pip install -r requirements.txt
```

4. Start the Flask application:

```bash
flask run
```

## Usage

Once the application is running, navigate to `http://localhost:5000` in your web browser.

### Manual Option Pricing

1. Enter the option parameters:
   - Stock price
   - Strike price
   - Years to expiration
   - Risk-free rate
   - Volatility
   - Dividend yield

2. Click "Calculate Option Prices" to see the results

### Using Real-Time Market Data

1. Enter a stock symbol (e.g., AAPL, MSFT)
2. Click "Fetch Market Data" to retrieve current price, volatility, and dividend yield
3. Enter the strike price and expiration time
4. Click "Calculate with Market Data" to price the option

### API Endpoints

- `POST /api/price`: Calculate option prices for a single set of parameters
- `POST /api/batch`: Submit a batch of options for calculation
- `GET /api/batch/<task_id>`: Retrieve the results of a batch calculation
- `GET /api/market-data/<symbol>`: Get market data for a stock symbol

## Configuration

The application can be configured using environment variables:

- `FLASK_ENV`: Set to `development` or `production`
- `PORT`: Port to run the application (default: 5000)
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)
- `CELERY_BROKER_URL`: Celery broker URL (default: redis://localhost:6379/0)
- `CELERY_RESULT_BACKEND`: Celery result backend URL (default: redis://localhost:6379/0)

## Scaling

The application is designed to scale horizontally:

1. The web application handles HTTP requests
2. Redis provides caching and message queue functionality
3. Celery workers process batch calculations
4. Additional Celery workers can be added for increased throughput

## Advanced Configuration

### Working with Multiple Exchanges

To add support for additional exchanges beyond what Yahoo Finance provides:

1. Implement additional data providers in a new module
2. Register the providers in the market data service
3. Update the market data API to support exchange selection

### Implementing Custom Pricing Models

To add custom pricing models beyond Black-Scholes:

1. Implement the model in a separate module
2. Register the model with the pricing service
3. Update the API to accept a model parameter