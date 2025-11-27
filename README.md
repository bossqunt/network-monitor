# Network Monitor

A lightweight network monitoring tool that measures ping and traceroute data and stores it in MySQL.

## Features

- **Ping Monitoring**: Measures latency, packet loss, and reachability every 10 seconds (configurable)
- **Traceroute Monitoring**: Tracks network path and hop-by-hop latency every 1 minute (configurable)
- **MySQL Storage**: All data stored in structured MySQL tables with proper indexing
- **Concurrent Monitoring**: Both ping and traceroute run in parallel threads
- **Configurable**: Easy YAML configuration for targets, intervals, and database settings

## Database Schema

### Ping Table
Stores ping test results with:
- Timestamp (datetime and unix timestamp)
- Target hostname
- Resolved IP address
- Average ping time in milliseconds
- Packet loss percentage
- Reachability boolean

### Traceroute Table
Stores traceroute hop data with:
- Trace ID (UUID to group hops from the same traceroute)
- Timestamp (datetime and unix timestamp)
- Target hostname
- Hop number
- Hop IP and hostname
- Round-trip time in milliseconds
- Packets sent/received
- Timeout indicator

## Installation

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. Install PyYAML for configuration:
```powershell
pip install pyyaml
```

3. Set up the MySQL database:
```powershell
mysql -u root -p < schema.sql
```

## Configuration

Edit `config.yaml` to configure:

- **Database settings**: Host, port, user, password, database name
- **Ping targets and interval**: Which hosts to ping and how often
- **Traceroute targets and interval**: Which hosts to trace and how often
- **Timeouts and packet counts**: Fine-tune monitoring behavior

## Usage

Run the network monitor:

```powershell
python network_monitor.py
```

The application will:
1. Connect to MySQL database
2. Start ping monitoring (default: every 10 seconds)
3. Start traceroute monitoring (default: every 60 seconds)
4. Log all activities to console and `network_monitor.log`

Press `Ctrl+C` to stop gracefully.

## Example Queries

View recent ping results:
```sql
SELECT * FROM ping ORDER BY timestamp DESC LIMIT 10;
```

View traceroute for a specific target:
```sql
SELECT * FROM traceroute 
WHERE target = 'google.com' 
ORDER BY timestamp DESC, hop_number ASC 
LIMIT 30;
```

Group hops by trace ID:
```sql
SELECT trace_id, target, COUNT(*) as hop_count, MAX(hop_number) as max_hops
FROM traceroute 
GROUP BY trace_id, target 
ORDER BY timestamp DESC;
```

## Requirements

- Python 3.7+
- MySQL 5.7+ or 8.0+
- Windows (uses `tracert`) or Linux (uses `traceroute`)
- Administrator/root privileges may be required for ICMP ping operations
