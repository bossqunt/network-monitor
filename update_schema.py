"""
Update existing database schema to add new fields
"""
import mysql.connector
from mysql.connector import Error

def update_schema():
    """Update database schema with new fields"""
    print("=" * 60)
    print("Updating Database Schema")
    print("=" * 60)
    
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='unknown',
            database='network_monitor'
        )
        
        if connection.is_connected():
            print("✓ Connected to database")
            cursor = connection.cursor()
            
            # Add connection_status column to ping table
            try:
                cursor.execute("""
                    ALTER TABLE ping 
                    ADD COLUMN connection_status ENUM('excellent', 'good', 'fair', 'poor', 'down') 
                    NOT NULL DEFAULT 'down' AFTER is_reachable
                """)
                print("✓ Added connection_status column to ping table")
            except Error as e:
                if 'Duplicate column name' in str(e):
                    print("  Column connection_status already exists")
                else:
                    print(f"  Warning: {e}")
            
            # Add index for connection_status
            try:
                cursor.execute("ALTER TABLE ping ADD INDEX idx_connection_status (connection_status)")
                print("✓ Added index for connection_status")
            except Error as e:
                if 'Duplicate key name' in str(e):
                    print("  Index already exists")
                else:
                    print(f"  Warning: {e}")
            
            # Create network_anomalies table
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS network_anomalies (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME(3) NOT NULL,
                        unix_timestamp BIGINT NOT NULL,
                        target VARCHAR(255) NOT NULL,
                        anomaly_type ENUM('high_latency', 'packet_loss', 'connection_lost', 'jitter', 'route_change') NOT NULL,
                        severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
                        metric_value FLOAT,
                        threshold_value FLOAT,
                        description TEXT,
                        ping_id INT,
                        trace_id VARCHAR(36),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_target (target),
                        INDEX idx_anomaly_type (anomaly_type),
                        INDEX idx_severity (severity),
                        FOREIGN KEY (ping_id) REFERENCES ping(id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                print("✓ Created network_anomalies table")
            except Error as e:
                print(f"  Warning: {e}")
            
            # Create speedtest table
            try:
                cursor.execute("""
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
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                print("✓ Created speedtest table")
            except Error as e:
                print(f"  Warning: {e}")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("=" * 60)
            print("✓ Schema update completed!")
            print("=" * 60)
            return True
            
    except Error as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    update_schema()
