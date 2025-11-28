# Network Monitor

A lightweight network monitoring tool that measures ping, traceroute, and speed test data and stores it in MySQL.

## Features

- **Ping Monitoring**: Measures latency, packet loss, and reachability every 10 seconds (configurable)
- **Traceroute Monitoring**: Tracks network path and hop-by-hop latency every 1 minute (configurable)
- **Speed Test Monitoring**: Measures download/upload speeds every 5 minutes (configurable)
- **Connection Status**: Automatically calculates connection quality (excellent, good, fair, poor, down)
- **MySQL Storage**: All data stored in structured MySQL tables with proper indexing
- **Concurrent Monitoring**: All monitors run in parallel threads
- **Docker Support**: Easy deployment with Docker Compose
- **Grafana Ready**: Pre-built queries for visualization

## Database Schema

### Ping Table
- Timestamp, target, IP address
- Average ping time, packet loss percentage
- Reachability status, connection quality

### Traceroute Table
- Trace ID (UUID to group hops)
- Hop details: number, IP, hostname, latency
- Packet statistics, timeout indicators

### Speed Test Table
- Download/upload speeds (Mbps)
- Server information and location
- ISP, external IP, test duration

## Quick Start with Docker

### 1. Using Docker Compose (Recommended)

```bash
# Start everything (MySQL + Network Monitor)
docker-compose up -d

# View logs
docker-compose logs -f network_monitor

# Stop everything
docker-compose down

# Stop and remove data
docker-compose down -v
```

### 2. Configuration

Edit `config.yaml` before starting:
```yaml
database:
  host: "mysql"  # Use 'mysql' for Docker, '127.0.0.1' for local
  
ping:
  interval_seconds: 10
  targets:
    - "google.com"
    - "8.8.8.8"
    
traceroute:
  interval_seconds: 60
  
speedtest:
  interval_seconds: 300  # 5 minutes
```

### 3. Access MySQL

```bash
# Connect to MySQL in Docker
docker exec -it network_monitor_mysql mysql -u root -punknown network_monitor

# Or from host (if port is exposed)
mysql -h 127.0.0.1 -u root -punknown network_monitor
```

## Local Installation (Without Docker)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up MySQL

```bash
mysql -u root -p < schema.sql
# Or use the setup script
python setup_db.py
```

### 3. Configure

Copy `config.yaml` and update database host to `127.0.0.1`:
```bash
cp config.yaml config.local.yaml
# Edit config.local.yaml and change host to "127.0.0.1"
```

### 4. Run

```bash
python network_monitor.py
```

## Running at Startup

### Windows - Task Scheduler
```powershell
# Run as Administrator
.\install_service.ps1
```

### Linux - Systemd
```bash
# Create service file
sudo nano /etc/systemd/system/network-monitor.service

# Enable and start
sudo systemctl enable network-monitor
sudo systemctl start network-monitor
```

## Grafana Integration

All queries are in `grafana_queries.sql`. Import them into Grafana with MySQL data source.

### Key Dashboards:
1. **Connection Status Over Time** - Real-time quality monitoring
2. **Ping Latency Graph** - Latency trends
3. **Packet Loss Tracking** - Network stability
4. **Speed Test Results** - Download/upload speeds
5. **Anomaly Detection** - High latency, packet loss, outages
6. **Traceroute Analysis** - Network path visualization

### Example Grafana Query:
```sql
-- Connection Status (Time Series)
SELECT 
    timestamp as time,
    target as metric,
    CASE connection_status
        WHEN 'excellent' THEN 5
        WHEN 'good' THEN 4
        WHEN 'fair' THEN 3
        WHEN 'poor' THEN 2
        WHEN 'down' THEN 1
    END as value
FROM ping
WHERE $__timeFilter(timestamp)
ORDER BY timestamp;
```

## Project Structure

```
network-monitor/
├── network_monitor.py      # Main application
├── ping_monitor.py         # Ping monitoring
├── traceroute_monitor.py   # Traceroute monitoring
├── speedtest_monitor.py    # Speed test monitoring
├── db_utils.py             # Database operations
├── config_loader.py        # Configuration management
├── config.yaml             # Configuration file
├── schema.sql              # Database schema
├── grafana_queries.sql     # Grafana query templates
├── Dockerfile              # Docker image
├── docker-compose.yml      # Docker Compose setup
└── requirements.txt        # Python dependencies
```

## Environment Variables

You can override config via environment variables:
```bash
DB_HOST=mysql
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=network_monitor
```

## Troubleshooting

### Docker Issues
```bash
# Rebuild containers
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Check MySQL connection
docker exec -it network_monitor_app ping mysql
```

### Permission Issues
- Linux: May need `sudo` for ICMP ping
- Docker: Container runs as non-root user for security

### High Resource Usage
- Increase ping/traceroute intervals in `config.yaml`
- Disable speedtest if not needed: `speedtest.enabled: false`

## Development

### Run Tests
```bash
python -m pytest tests/
```

### Update Schema
```bash
python update_schema.py
```

## License

MIT License - feel free to use and modify

## Contributing

Pull requests welcome! Please ensure:
1. Code follows existing style
2. All tests pass
3. Documentation is updated
