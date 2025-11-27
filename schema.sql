-- Create database
CREATE DATABASE IF NOT EXISTS network_monitor;
USE network_monitor;

-- Ping monitoring table
CREATE TABLE IF NOT EXISTS ping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(3) NOT NULL,
    unix_timestamp BIGINT NOT NULL,
    target VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    ping_ms FLOAT,
    packet_loss FLOAT,
    is_reachable BOOLEAN NOT NULL,
    connection_status ENUM('excellent', 'good', 'fair', 'poor', 'down') NOT NULL,
    INDEX idx_timestamp (timestamp),
    INDEX idx_target (target),
    INDEX idx_unix_timestamp (unix_timestamp),
    INDEX idx_connection_status (connection_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Traceroute monitoring table
CREATE TABLE IF NOT EXISTS traceroute (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trace_id VARCHAR(36) NOT NULL,  -- UUID to group hops from same traceroute
    timestamp DATETIME(3) NOT NULL,
    unix_timestamp BIGINT NOT NULL,
    target VARCHAR(255) NOT NULL,
    hop_number INT NOT NULL,
    hop_ip VARCHAR(45),
    hop_hostname VARCHAR(255),
    rtt_ms FLOAT,
    packets_sent INT NOT NULL,
    packets_received INT NOT NULL,
    is_timeout BOOLEAN NOT NULL,
    INDEX idx_trace_id (trace_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_target (target),
    INDEX idx_hop_number (hop_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Speed test monitoring table
CREATE TABLE IF NOT EXISTS speedtest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(3) NOT NULL,
    unix_timestamp BIGINT NOT NULL,
    server_name VARCHAR(255),
    server_location VARCHAR(255),
    server_country VARCHAR(100),
    download_mbps FLOAT,
    upload_mbps FLOAT,
    ping_ms FLOAT,
    jitter_ms FLOAT,
    packet_loss FLOAT,
    isp VARCHAR(255),
    external_ip VARCHAR(45),
    test_duration_seconds FLOAT,
    is_successful BOOLEAN NOT NULL,
    error_message TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_unix_timestamp (unix_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
