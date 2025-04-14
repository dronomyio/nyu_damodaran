FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    # Clean cache to reduce image size
    rm -rf /root/.cache/pip

# Copy application files
COPY . .

# Create directories if they don't exist
RUN mkdir -p templates static

# Expose port
EXPOSE 5000

# Set environment variables for better performance
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Command to run the application with optimized settings
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers=2", "--threads=4", "--timeout=120", "--access-logfile=-", "--error-logfile=-", "app:app"]