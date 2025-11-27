# Quick Start Guide

## Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `mysql-connector-python` - MySQL database connector
- `pythonping` - Python ping library
- `pyyaml` - YAML configuration parser

## Step 2: Configure Settings

Edit `config.yaml` and update:

1. **Database credentials** (if different from defaults):
   ```yaml
   database:
     host: "127.0.0.1"
     user: "root"
     password: "unknown"
     database: "network_monitor"
   ```

2. **Monitoring targets**:
   ```yaml
   ping:
     targets:
       - "google.com"
       - "8.8.8.8"
   
   traceroute:
     targets:
       - "google.com"
   ```

3. **Intervals** (optional):
   ```yaml
   ping:
     interval_seconds: 10  # Default: 10 seconds
   
   traceroute:
     interval_seconds: 60  # Default: 60 seconds
   ```

## Step 3: Set Up Database

Run the database setup script:

```powershell
python setup_db.py
```

This creates:
- Database: `network_monitor`
- Table: `ping` (for ping results)
- Table: `traceroute` (for traceroute hops)

## Step 4: Start Monitoring

```powershell
python network_monitor.py
```

Or use the quick-start script:

```powershell
.\start.ps1
```

## Monitoring Output

The monitor will:
- Log to console in real-time
- Save logs to `network_monitor.log`
- Store all data in MySQL tables

Example console output:
```
2025-11-26 10:00:00 - ping_monitor - INFO - Ping google.com (142.250.80.46): 15.23ms, Loss: 0.0%, Reachable: True
2025-11-26 10:01:00 - traceroute_monitor - INFO - Traceroute to google.com: 12 hops stored
```

## Querying the Data

### Recent ping results:
```sql
SELECT timestamp, target, ip_address, ping_ms, packet_loss, is_reachable
FROM ping 
ORDER BY timestamp DESC 
LIMIT 10;
```

### Traceroute for specific target:
```sql
SELECT timestamp, hop_number, hop_ip, hop_hostname, rtt_ms
FROM traceroute
WHERE target = 'google.com'
  AND trace_id = (SELECT trace_id FROM traceroute WHERE target = 'google.com' ORDER BY timestamp DESC LIMIT 1)
ORDER BY hop_number;
```

### Average ping by target:
```sql
SELECT target, 
       AVG(ping_ms) as avg_ping,
       AVG(packet_loss) as avg_loss,
       COUNT(*) as measurements
FROM ping
WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY target;
```

## Stopping the Monitor

Press `Ctrl+C` to gracefully stop all monitoring threads.

## Troubleshooting

**MySQL connection failed:**
- Verify MySQL is running: `mysql -u root -p`
- Check credentials in `config.yaml`
- Ensure database `network_monitor` exists

**Import errors:**
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.7+)

**Ping/Traceroute not working:**
- May require administrator privileges
- On Windows, ensure `tracert` is available
- On Linux, ensure `traceroute` is installed

**No data in database:**
- Check `network_monitor.log` for errors
- Verify targets are reachable
- Check firewall settings
