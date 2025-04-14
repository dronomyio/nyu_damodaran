FROM python:3.11-slim

WORKDIR /app

# Install dependencies and cleanup
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt && \
    # Clean cache to reduce image size
    rm -rf /root/.cache/pip

# Copy application files
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Set environment variables for better performance
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_CLIENT_TOOLBAR_MODE=minimal

# Create a .streamlit configuration directory with config
RUN mkdir -p /app/.streamlit
RUN echo '\
[server]\n\
enableStaticServing = true\n\
enableCORS = true\n\
enableXsrfProtection = false\n\
maxUploadSize = 10\n\
maxMessageSize = 200\n\
' > /app/.streamlit/config.toml

# Run the application with optimized settings
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=true", "--server.enableXsrfProtection=false", "--server.runOnSave=false", "--ui.hideSidebarNav=true"]