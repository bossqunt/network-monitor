-- =====================================================
-- GRAFANA QUERIES FOR NETWORK MONITOR
-- =====================================================

-- 1. CONNECTION STATUS OVER TIME (Time Series)
-- Shows connection quality status over time
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

-- 2. PING LATENCY GRAPH (Time Series)
-- Shows ping times over time for each target
SELECT 
    timestamp as time,
    target as metric,
    ping_ms as value
FROM ping
WHERE $__timeFilter(timestamp)
  AND is_reachable = 1
ORDER BY timestamp;

-- 3. PACKET LOSS PERCENTAGE (Time Series)
SELECT 
    timestamp as time,
    target as metric,
    packet_loss as value
FROM ping
WHERE $__timeFilter(timestamp)
ORDER BY timestamp;

-- 4. UPTIME PERCENTAGE (Stat Panel)
-- Shows uptime percentage for selected time range
SELECT 
    target,
    (SUM(is_reachable) / COUNT(*)) * 100 as uptime_percentage
FROM ping
WHERE $__timeFilter(timestamp)
GROUP BY target;

-- 5. AVERAGE LATENCY BY TARGET (Stat Panel)
SELECT 
    target,
    AVG(ping_ms) as avg_latency_ms,
    MIN(ping_ms) as min_latency_ms,
    MAX(ping_ms) as max_latency_ms
FROM ping
WHERE $__timeFilter(timestamp)
  AND is_reachable = 1
GROUP BY target;

-- 6. CONNECTION STATUS DISTRIBUTION (Pie Chart)
SELECT 
    connection_status,
    COUNT(*) as count
FROM ping
WHERE $__timeFilter(timestamp)
  AND target = '$target'
GROUP BY connection_status;

-- 7. ANOMALIES TIMELINE (Table)
-- Shows all detected anomalies (calculated on-the-fly)
SELECT 
    timestamp,
    target,
    anomaly_type,
    severity,
    metric_value
FROM (
    SELECT timestamp, target, ping_ms as metric_value, 'high_latency' as anomaly_type,
           CASE WHEN ping_ms > 500 THEN 'critical' 
                WHEN ping_ms > 200 THEN 'high' 
                WHEN ping_ms > 100 THEN 'medium' END as severity
    FROM ping WHERE ping_ms > 100
    UNION ALL
    SELECT timestamp, target, packet_loss, 'packet_loss',
           CASE WHEN packet_loss >= 50 THEN 'critical' 
                WHEN packet_loss >= 10 THEN 'high' 
                WHEN packet_loss >= 5 THEN 'medium' 
                ELSE 'low' END
    FROM ping WHERE packet_loss > 0
    UNION ALL
    SELECT timestamp, target, 0, 'connection_lost', 'critical'
    FROM ping WHERE is_reachable = 0
) anomalies
WHERE $__timeFilter(timestamp)
ORDER BY timestamp DESC;

-- 8. ANOMALY COUNT BY TYPE (Bar Gauge)
SELECT 
    anomaly_type as metric,
    COUNT(*) as value
FROM (
    SELECT 'high_latency' as anomaly_type FROM ping WHERE $__timeFilter(timestamp) AND ping_ms > 100
    UNION ALL
    SELECT 'packet_loss' FROM ping WHERE $__timeFilter(timestamp) AND packet_loss > 0
    UNION ALL
    SELECT 'connection_lost' FROM ping WHERE $__timeFilter(timestamp) AND is_reachable = 0
) anomalies
GROUP BY anomaly_type;

-- 9. ANOMALY COUNT BY SEVERITY (Stat Panel)
SELECT 
    severity,
    COUNT(*) as count
FROM (
    SELECT CASE WHEN ping_ms > 500 THEN 'critical' 
                WHEN ping_ms > 200 THEN 'high' 
                WHEN ping_ms > 100 THEN 'medium' END as severity
    FROM ping WHERE $__timeFilter(timestamp) AND ping_ms > 100
    UNION ALL
    SELECT CASE WHEN packet_loss >= 50 THEN 'critical' 
                WHEN packet_loss >= 10 THEN 'high' 
                WHEN packet_loss >= 5 THEN 'medium' 
                ELSE 'low' END
    FROM ping WHERE $__timeFilter(timestamp) AND packet_loss > 0
    UNION ALL
    SELECT 'critical' FROM ping WHERE $__timeFilter(timestamp) AND is_reachable = 0
) anomalies
GROUP BY severity
ORDER BY FIELD(severity, 'critical', 'high', 'medium', 'low');

-- 10. CURRENT CONNECTION STATUS (Stat Panel with Threshold Colors)
-- Shows the most recent connection status for each target
SELECT 
    target,
    connection_status,
    ping_ms,
    packet_loss,
    timestamp
FROM ping
WHERE (target, timestamp) IN (
    SELECT target, MAX(timestamp)
    FROM ping
    GROUP BY target
);

-- 11. DOWNTIME EVENTS (Table)
-- Lists periods when connection was down
SELECT 
    target,
    timestamp as down_time,
    LEAD(timestamp) OVER (PARTITION BY target ORDER BY timestamp) as up_time,
    TIMESTAMPDIFF(SECOND, timestamp, LEAD(timestamp) OVER (PARTITION BY target ORDER BY timestamp)) as downtime_seconds
FROM ping
WHERE is_reachable = 0
  AND $__timeFilter(timestamp)
ORDER BY timestamp DESC;

-- 12. JITTER CALCULATION (Time Series)
-- Shows network stability (variation in ping times)
SELECT 
    p1.timestamp as time,
    p1.target as metric,
    ABS(p1.ping_ms - p2.ping_ms) as value
FROM ping p1
JOIN ping p2 ON p1.target = p2.target 
    AND p2.timestamp = (
        SELECT MAX(timestamp) 
        FROM ping 
        WHERE target = p1.target 
        AND timestamp < p1.timestamp
    )
WHERE $__timeFilter(p1.timestamp)
  AND p1.is_reachable = 1
  AND p2.is_reachable = 1
ORDER BY p1.timestamp;

-- 13. HOURLY UPTIME REPORT (Table)
SELECT 
    target,
    DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as hour,
    COUNT(*) as total_checks,
    SUM(is_reachable) as successful_checks,
    (SUM(is_reachable) / COUNT(*)) * 100 as uptime_percentage,
    AVG(ping_ms) as avg_ping_ms,
    AVG(packet_loss) as avg_packet_loss
FROM ping
WHERE $__timeFilter(timestamp)
GROUP BY target, DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00')
ORDER BY hour DESC;

-- 14. ANOMALY HEATMAP (Heatmap)
-- Shows anomaly frequency by hour and day
SELECT 
    DATE_FORMAT(timestamp, '%Y-%m-%d') as time,
    HOUR(timestamp) as hour,
    COUNT(*) as value
FROM (
    SELECT timestamp FROM ping WHERE ping_ms > 100
    UNION ALL
    SELECT timestamp FROM ping WHERE packet_loss > 0
    UNION ALL
    SELECT timestamp FROM ping WHERE is_reachable = 0
) anomalies
WHERE $__timeFilter(timestamp)
GROUP BY DATE_FORMAT(timestamp, '%Y-%m-%d'), HOUR(timestamp)
ORDER BY time, hour;

-- 15. TRACEROUTE HOP LATENCY (Time Series)
-- Shows latency at each hop over time
SELECT 
    t.timestamp as time,
    CONCAT(t.target, ' - Hop ', t.hop_number, ' (', COALESCE(t.hop_hostname, t.hop_ip), ')') as metric,
    t.rtt_ms as value
FROM traceroute t
WHERE $__timeFilter(t.timestamp)
  AND t.is_timeout = 0
  AND t.target = '$target'
ORDER BY t.timestamp, t.hop_number;

-- 16. ROUTE STABILITY (Table)
-- Detect if network route changes
SELECT 
    t1.timestamp,
    t1.target,
    t1.hop_number,
    t1.hop_ip as current_hop_ip,
    t2.hop_ip as previous_hop_ip,
    CASE WHEN t1.hop_ip != t2.hop_ip THEN 'Route Changed' ELSE 'Stable' END as status
FROM traceroute t1
LEFT JOIN traceroute t2 ON 
    t1.target = t2.target 
    AND t1.hop_number = t2.hop_number
    AND t2.trace_id = (
        SELECT trace_id 
        FROM traceroute 
        WHERE target = t1.target 
        AND timestamp < t1.timestamp
        ORDER BY timestamp DESC 
        LIMIT 1
    )
WHERE $__timeFilter(t1.timestamp)
  AND t1.hop_ip != t2.hop_ip
ORDER BY t1.timestamp DESC;

-- 17. CONNECTION QUALITY SCORE (Gauge)
-- Overall connection quality score (0-100)
SELECT 
    target,
    (
        (SUM(is_reachable) / COUNT(*)) * 50 + -- 50% weight for uptime
        ((100 - AVG(packet_loss)) / 100) * 30 + -- 30% weight for packet loss
        (CASE 
            WHEN AVG(ping_ms) < 20 THEN 20
            WHEN AVG(ping_ms) < 50 THEN 15
            WHEN AVG(ping_ms) < 100 THEN 10
            WHEN AVG(ping_ms) < 200 THEN 5
            ELSE 0
        END) -- 20% weight for latency
    ) as quality_score
FROM ping
WHERE $__timeFilter(timestamp)
GROUP BY target;

-- 18. ALERT SUMMARY (Stat Panel)
-- Count of critical/high severity anomalies in time range
SELECT 
    target,
    COUNT(*) as alert_count
FROM (
    SELECT target FROM ping WHERE $__timeFilter(timestamp) AND (ping_ms > 200 OR packet_loss >= 10 OR is_reachable = 0)
) critical_anomalies
GROUP BY target;

-- =====================================================
-- SPEED TEST QUERIES
-- =====================================================

-- 19. DOWNLOAD SPEED OVER TIME (Time Series)
SELECT 
    timestamp as time,
    'Download' as metric,
    download_mbps as value
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
ORDER BY timestamp;

-- 20. UPLOAD SPEED OVER TIME (Time Series)
SELECT 
    timestamp as time,
    'Upload' as metric,
    upload_mbps as value
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
ORDER BY timestamp;

-- 21. DOWNLOAD & UPLOAD COMBINED (Time Series)
SELECT 
    timestamp as time,
    metric,
    value
FROM (
    SELECT timestamp, 'Download' as metric, download_mbps as value
    FROM speedtest WHERE is_successful = 1
    UNION ALL
    SELECT timestamp, 'Upload' as metric, upload_mbps as value
    FROM speedtest WHERE is_successful = 1
) speeds
WHERE $__timeFilter(timestamp)
ORDER BY timestamp;

-- 22. SPEED TEST STATISTICS (Stat Panel)
SELECT 
    AVG(download_mbps) as avg_download_mbps,
    AVG(upload_mbps) as avg_upload_mbps,
    MIN(download_mbps) as min_download_mbps,
    MIN(upload_mbps) as min_upload_mbps,
    MAX(download_mbps) as max_download_mbps,
    MAX(upload_mbps) as max_upload_mbps
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1;

-- 23. CURRENT SPEED TEST (Stat Panel)
SELECT 
    timestamp,
    download_mbps,
    upload_mbps,
    ping_ms,
    server_name,
    server_location
FROM speedtest
WHERE is_successful = 1
ORDER BY timestamp DESC
LIMIT 1;

-- 24. SPEED TEST PING LATENCY (Time Series)
-- Shows ping measured during speed test
SELECT 
    timestamp as time,
    'Speed Test Ping' as metric,
    ping_ms as value
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
ORDER BY timestamp;

-- 25. SPEED TEST SUCCESS RATE (Stat Panel)
SELECT 
    COUNT(*) as total_tests,
    SUM(is_successful) as successful_tests,
    (SUM(is_successful) / COUNT(*)) * 100 as success_rate
FROM speedtest
WHERE $__timeFilter(timestamp);

-- 26. SPEED TEST HISTORY TABLE (Table)
SELECT 
    timestamp,
    download_mbps,
    upload_mbps,
    ping_ms,
    server_name,
    server_location,
    isp,
    test_duration_seconds
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
ORDER BY timestamp DESC;

-- 27. SPEED BY ISP (Bar Chart)
SELECT 
    isp,
    AVG(download_mbps) as avg_download,
    AVG(upload_mbps) as avg_upload
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
GROUP BY isp;

-- 28. SPEED BY SERVER LOCATION (Table)
SELECT 
    server_location,
    server_country,
    COUNT(*) as test_count,
    AVG(download_mbps) as avg_download,
    AVG(upload_mbps) as avg_upload,
    AVG(ping_ms) as avg_ping
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
GROUP BY server_location, server_country
ORDER BY test_count DESC;

-- 29. SPEED TEST FAILURES (Table)
SELECT 
    timestamp,
    error_message
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 0
ORDER BY timestamp DESC;

-- 30. HOURLY AVERAGE SPEEDS (Time Series)
SELECT 
    DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as time,
    AVG(download_mbps) as avg_download,
    AVG(upload_mbps) as avg_upload
FROM speedtest
WHERE $__timeFilter(timestamp)
  AND is_successful = 1
GROUP BY DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00')
ORDER BY time;
