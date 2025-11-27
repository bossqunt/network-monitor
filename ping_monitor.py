"""
Ping monitoring module
"""
import time
import socket
import logging
from datetime import datetime
from pythonping import ping as pythonping_ping
from threading import Thread, Event

logger = logging.getLogger(__name__)


class PingMonitor:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.stop_event = Event()
        self.thread = None
    
    def resolve_hostname(self, target):
        """Resolve hostname to IP address"""
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            return None
    
    def perform_ping(self, target, count=4, timeout=2):
        """
        Perform ping test and return results
        Returns: (ip_address, avg_ping_ms, packet_loss, is_reachable)
        """
        try:
            # Resolve IP address
            ip_address = self.resolve_hostname(target)
            
            # Perform ping
            response = pythonping_ping(target, count=count, timeout=timeout)
            
            # Calculate statistics
            success_count = sum(1 for r in response if r.success)
            packet_loss = ((count - success_count) / count) * 100
            is_reachable = success_count > 0
            
            # Calculate average ping time for successful pings
            avg_ping_ms = None
            if success_count > 0:
                total_time = sum(r.time_elapsed_ms for r in response if r.success)
                avg_ping_ms = total_time / success_count
            
            return ip_address, avg_ping_ms, packet_loss, is_reachable
            
        except Exception as e:
            logger.error(f"Error pinging {target}: {e}")
            return None, None, 100.0, False
    
    def calculate_connection_status(self, ping_ms, packet_loss, is_reachable):
        """
        Calculate connection status based on ping time and packet loss
        Returns: 'excellent', 'good', 'fair', 'poor', or 'down'
        """
        if not is_reachable or packet_loss >= 50:
            return 'down'
        elif packet_loss >= 10 or (ping_ms and ping_ms > 200):
            return 'poor'
        elif packet_loss >= 5 or (ping_ms and ping_ms > 100):
            return 'fair'
        elif packet_loss > 0 or (ping_ms and ping_ms > 50):
            return 'good'
        else:
            return 'excellent'
    
    def store_ping_result(self, target, ip_address, ping_ms, packet_loss, is_reachable):
        """Store ping result in database"""
        now = datetime.now()
        unix_timestamp = int(time.time() * 1000)  # milliseconds
        
        # Calculate connection status
        connection_status = self.calculate_connection_status(ping_ms, packet_loss, is_reachable)
        
        success = self.db_manager.insert_ping_result(
            timestamp=now,
            unix_timestamp=unix_timestamp,
            target=target,
            ip_address=ip_address,
            ping_ms=ping_ms,
            packet_loss=packet_loss,
            is_reachable=is_reachable,
            connection_status=connection_status
        )
        
        if success:
            ping_str = f"{ping_ms:.2f}" if ping_ms is not None else "N/A"
            logger.info(f"Ping {target} ({ip_address}): {ping_str}ms, "
                       f"Loss: {packet_loss:.1f}%, Status: {connection_status}")
        else:
            logger.error(f"Failed to store ping result for {target}")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        interval = self.config.get('interval_seconds', 10)
        targets = self.config.get('targets', ['google.com'])
        count = self.config.get('count', 4)
        timeout = self.config.get('timeout_seconds', 2)
        
        logger.info(f"Starting ping monitor with {len(targets)} targets, "
                   f"interval: {interval}s")
        
        while not self.stop_event.is_set():
            for target in targets:
                if self.stop_event.is_set():
                    break
                
                ip_address, ping_ms, packet_loss, is_reachable = self.perform_ping(
                    target, count, timeout
                )
                self.store_ping_result(target, ip_address, ping_ms, 
                                      packet_loss, is_reachable)
            
            # Wait for next interval
            self.stop_event.wait(interval)
    
    def start(self):
        """Start monitoring in a separate thread"""
        if not self.config.get('enabled', True):
            logger.info("Ping monitor is disabled")
            return
        
        self.thread = Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Ping monitor started")
    
    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping ping monitor...")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Ping monitor stopped")
