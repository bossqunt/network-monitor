"""
Database utility module for MySQL operations
"""
import mysql.connector
from mysql.connector import Error, pooling
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.pool = None
    
    def connect(self):
        """Establish connection pool to MySQL database"""
        try:
            # Create a connection pool
            self.pool = pooling.MySQLConnectionPool(
                pool_name="monitor_pool",
                pool_size=20,
                pool_reset_session=True,
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                autocommit=True,
                connect_timeout=10
            )
            # Test the connection
            conn = self.pool.get_connection()
            if conn.is_connected():
                logger.info("Successfully connected to MySQL database with connection pool")
                conn.close()
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False
        return False
    
    def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            logger.info("MySQL connection pool closed")
            self.pool = None
    
    def _get_connection(self):
        """Get a connection from the pool with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.pool is None:
                    logger.warning("Connection pool not initialized, attempting to reconnect...")
                    self.connect()
                
                conn = self.pool.get_connection()
                if conn.is_connected():
                    return conn
            except Error as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("Failed to get database connection after all retries")
                    return None
        return None
    
    def execute_query(self, query, params=None):
        """Execute a query (INSERT, UPDATE, DELETE) with automatic reconnection"""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def insert_ping_result(self, timestamp, unix_timestamp, target, ip_address, 
                          ping_ms, min_ping_ms, max_ping_ms, jitter_ms, packet_loss, is_reachable, connection_status):
        """Insert ping result into database"""
        query = """
            INSERT INTO ping (timestamp, unix_timestamp, target, ip_address, 
                            ping_ms, min_ping_ms, max_ping_ms, jitter_ms, packet_loss, is_reachable, connection_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp, unix_timestamp, target, ip_address, 
                 ping_ms, min_ping_ms, max_ping_ms, jitter_ms, packet_loss, is_reachable, connection_status)
        return self.execute_query(query, params)
    
    def insert_traceroute_hop(self, trace_id, timestamp, unix_timestamp, target,
                             hop_number, hop_ip, hop_hostname, rtt_ms,
                             packets_sent, packets_received, is_timeout):
        """Insert traceroute hop into database"""
        query = """
            INSERT INTO traceroute (trace_id, timestamp, unix_timestamp, target,
                                  hop_number, hop_ip, hop_hostname, rtt_ms,
                                  packets_sent, packets_received, is_timeout)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (trace_id, timestamp, unix_timestamp, target, hop_number,
                 hop_ip, hop_hostname, rtt_ms, packets_sent, 
                 packets_received, is_timeout)
        return self.execute_query(query, params)
    
    def insert_speedtest_result(self, timestamp, unix_timestamp, server_name,
                                server_location, server_country, download_mbps,
                                upload_mbps, ping_ms, jitter_ms, packet_loss,
                                isp, external_ip, idle_latency_ms, download_latency_ms,
                                upload_latency_ms, bufferbloat_rating, test_duration_seconds,
                                is_successful, error_message=None):
        """Insert speed test result into database"""
        query = """
            INSERT INTO speedtest (timestamp, unix_timestamp, server_name,
                                 server_location, server_country, download_mbps,
                                 upload_mbps, ping_ms, jitter_ms, packet_loss,
                                 isp, external_ip, idle_latency_ms, download_latency_ms,
                                 upload_latency_ms, bufferbloat_rating, test_duration_seconds,
                                 is_successful, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp, unix_timestamp, server_name, server_location,
                 server_country, download_mbps, upload_mbps, ping_ms, jitter_ms,
                 packet_loss, isp, external_ip, idle_latency_ms, download_latency_ms,
                 upload_latency_ms, bufferbloat_rating, test_duration_seconds,
                 is_successful, error_message)
        return self.execute_query(query, params)
    
    def insert_dns_result(self, timestamp, unix_timestamp, domain, nameserver,
                         record_type, resolution_time_ms, resolved_ips,
                         is_successful, error_message=None):
        """Insert DNS query result into database"""
        query = """
            INSERT INTO dns_queries (timestamp, unix_timestamp, domain, nameserver,
                                   record_type, resolution_time_ms, resolved_ips,
                                   is_successful, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp, unix_timestamp, domain, nameserver, record_type,
                 resolution_time_ms, resolved_ips, is_successful, error_message)
        return self.execute_query(query, params)
    
    def insert_http_result(self, timestamp, unix_timestamp, url, dns_time_ms,
                          connect_time_ms, tls_time_ms, ttfb_ms, total_time_ms,
                          status_code, response_size, tls_version,
                          is_successful, error_message=None):
        """Insert HTTP request result into database"""
        query = """
            INSERT INTO http_requests (timestamp, unix_timestamp, url, dns_time_ms,
                                     connect_time_ms, tls_time_ms, ttfb_ms, total_time_ms,
                                     status_code, response_size, tls_version,
                                     is_successful, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp, unix_timestamp, url, dns_time_ms, connect_time_ms,
                 tls_time_ms, ttfb_ms, total_time_ms, status_code, response_size,
                 tls_version, is_successful, error_message)
        return self.execute_query(query, params)
