import os
from flask import Flask, render_template, request, jsonify
import numpy as np
import yfinance as yf
import redis
from celery import Celery
from datetime import datetime

from long_term_option import long_term_option_pricing, calculate_greeks

app = Flask(__name__)

# Configure Redis (if available)
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
try:
    cache = redis.from_url(redis_url)
    redis_available = True
except:
    redis_available = False
    print("Redis connection failed - running without cache")

# Configure Celery (for background tasks)
app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def calculate_option_batch(params_list):
    """Background task to calculate multiple options"""
    results = []
    for params in params_list:
        call_price, put_price, d1, d2, N_d1, N_d2 = long_term_option_pricing(
            params['S'], params['K'], params['T'], params['r'], 
            params['sigma'], params.get('dividend_yield', 0.0)
        )
        results.append({
            'call_price': float(call_price),
            'put_price': float(put_price),
            'parameters': params
        })
    return results

@app.route('/')
@app.route('/app.py')  # Add this route to handle direct access to app.py
def index():
    return render_template('index.html')

@app.route('/api/price', methods=['POST'])
def price_option():
    data = request.json
    
    # Extract parameters
    S = float(data.get('stock_price', 0))
    K = float(data.get('strike_price', 0))
    T = float(data.get('years_to_expiration', 0))
    r = float(data.get('risk_free_rate', 0.05))
    sigma = float(data.get('volatility', 0.2))
    dividend_yield = float(data.get('dividend_yield', 0.0))
    
    # Calculate option price
    call_price, put_price, d1, d2, N_d1, N_d2 = long_term_option_pricing(
        S, K, T, r, sigma, dividend_yield
    )
    
    # Calculate Greeks
    greeks = calculate_greeks(S, K, T, r, sigma, dividend_yield)
    
    # Format all numpy values to regular Python floats for JSON serialization
    greeks = {k: float(v) for k, v in greeks.items()}
    
    return jsonify({
        'call_price': float(call_price),
        'put_price': float(put_price),
        'd1': float(d1),
        'd2': float(d2),
        'N_d1': float(N_d1),
        'N_d2': float(N_d2),
        'greeks': greeks,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/batch', methods=['POST'])
def batch_price():
    """API endpoint to queue batch pricing calculations"""
    data = request.json
    params_list = data.get('options', [])
    
    if not params_list:
        return jsonify({'error': 'No options provided'}), 400
    
    # Queue the task
    task = calculate_option_batch.delay(params_list)
    
    return jsonify({
        'task_id': task.id,
        'status': 'Processing',
        'options_count': len(params_list)
    })

@app.route('/api/batch/<task_id>', methods=['GET'])
def batch_result(task_id):
    """Get the result of a batch task"""
    task = calculate_option_batch.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'result': None
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'failure',
            'result': str(task.info)
        }
    else:
        response = {
            'status': task.state,
            'result': task.info
        }
    
    return jsonify(response)

@app.route('/api/market-data/<symbol>', methods=['GET'])
def get_market_data(symbol):
    """Get real-time market data for a symbol"""
    try:
        # Cache key
        cache_key = f"market_data:{symbol}"
        
        # Try to get from cache first if Redis is available
        if redis_available:
            cached_data = cache.get(cache_key)
            if cached_data:
                return jsonify(eval(cached_data))
        
        # Fetch from yfinance if not in cache
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period="1d")
        
        # Extract relevant data
        price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield:
            dividend_yield = float(dividend_yield)
            
        # Calculate historical volatility (annualized)
        if not history.empty and len(history) > 1:
            returns = np.log(history['Close'] / history['Close'].shift(1)).dropna()
            volatility = float(returns.std() * np.sqrt(252))  # Annualized
        else:
            volatility = 0.3  # Default
        
        result = {
            'symbol': symbol,
            'price': price,
            'dividend_yield': dividend_yield,
            'volatility': volatility,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result for 5 minutes if Redis is available
        if redis_available:
            cache.setex(cache_key, 300, str(result))
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
