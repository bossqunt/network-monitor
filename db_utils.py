"""
Database utility module for MySQL operations
"""
import mysql.connector
from mysql.connector import Error
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            if self.connection.is_connected():
                logger.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False
        return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
    
    def execute_query(self, query, params=None):
        """Execute a query (INSERT, UPDATE, DELETE)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return False
    
    def insert_ping_result(self, timestamp, unix_timestamp, target, ip_address, 
                          ping_ms, packet_loss, is_reachable, connection_status):
        """Insert ping result into database"""
        query = """
            INSERT INTO ping (timestamp, unix_timestamp, target, ip_address, 
                            ping_ms, packet_loss, is_reachable, connection_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp, unix_timestamp, target, ip_address, 
                 ping_ms, packet_loss, is_reachable, connection_status)
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
                                isp, external_ip, test_duration_seconds,
                                is_successful, error_message=None):
        """Insert speed test result into database"""
        query = """
            INSERT INTO speedtest (timestamp, unix_timestamp, server_name,
                                 server_location, server_country, download_mbps,
                                 upload_mbps, ping_ms, jitter_ms, packet_loss,
                                 isp, external_ip, test_duration_seconds,
                                 is_successful, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp, unix_timestamp, server_name, server_location,
                 server_country, download_mbps, upload_mbps, ping_ms, jitter_ms,
                 packet_loss, isp, external_ip, test_duration_seconds,
                 is_successful, error_message)
        return self.execute_query(query, params)
