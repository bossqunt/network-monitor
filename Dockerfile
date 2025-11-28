FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    traceroute \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config_loader.py .
COPY db_utils.py .
COPY ping_monitor.py .
COPY traceroute_monitor.py .
COPY speedtest_monitor.py .
COPY dns_monitor.py .
COPY http_monitor.py .
COPY network_monitor.py .
COPY config.yaml .

# Create log directory
RUN mkdir -p /app/logs

# Note: Running as root to allow ICMP ping operations
# For production, consider using setcap or alternative ping methods

# Run the application
CMD ["python", "-u", "network_monitor.py"]
