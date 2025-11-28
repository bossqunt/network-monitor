-- Schema updates for new monitoring features
USE network_monitor;

-- Add jitter columns to ping table (skip if already exists)
ALTER TABLE ping
ADD COLUMN min_ping_ms FLOAT AFTER ping_ms;

ALTER TABLE ping
ADD COLUMN max_ping_ms FLOAT AFTER min_ping_ms;

ALTER TABLE ping
ADD COLUMN jitter_ms FLOAT AFTER max_ping_ms;

-- Add bufferbloat columns to speedtest table
ALTER TABLE speedtest
ADD COLUMN idle_latency_ms FLOAT AFTER external_ip;

ALTER TABLE speedtest
ADD COLUMN download_latency_ms FLOAT AFTER idle_latency_ms;

ALTER TABLE speedtest
ADD COLUMN upload_latency_ms FLOAT AFTER download_latency_ms;

ALTER TABLE speedtest
ADD COLUMN bufferbloat_rating VARCHAR(1) AFTER upload_latency_ms;

-- Create DNS monitoring table
CREATE TABLE IF NOT EXISTS dns_queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(3) NOT NULL,
    unix_timestamp BIGINT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    nameserver VARCHAR(45) NOT NULL,
    record_type VARCHAR(10) NOT NULL,
    resolution_time_ms FLOAT,
    resolved_ips TEXT,
    is_successful BOOLEAN NOT NULL,
    error_message TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_domain (domain),
    INDEX idx_nameserver (nameserver),
    INDEX idx_unix_timestamp (unix_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create HTTP monitoring table
CREATE TABLE IF NOT EXISTS http_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(3) NOT NULL,
    unix_timestamp BIGINT NOT NULL,
    url VARCHAR(500) NOT NULL,
    dns_time_ms FLOAT,
    connect_time_ms FLOAT,
    tls_time_ms FLOAT,
    ttfb_ms FLOAT,
    total_time_ms FLOAT,
    status_code INT,
    response_size INT,
    tls_version VARCHAR(20),
    is_successful BOOLEAN NOT NULL,
    error_message TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_url (url(255)),
    INDEX idx_unix_timestamp (unix_timestamp),
    INDEX idx_status_code (status_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
