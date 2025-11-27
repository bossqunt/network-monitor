"""
Speed test monitoring module
"""
import time
import logging
from datetime import datetime
from threading import Thread, Event
import speedtest

logger = logging.getLogger(__name__)


class SpeedTestMonitor:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.stop_event = Event()
        self.thread = None
    
    def perform_speedtest(self, server_id=None):
        """
        Perform speed test and return results
        Returns: dict with test results or None on error
        """
        try:
            start_time = time.time()
            
            st = speedtest.Speedtest()
            
            # Get server list and select best server
            logger.info("Getting server list...")
            st.get_servers()
            
            if server_id:
                st.get_servers([server_id])
            
            logger.info("Selecting best server...")
            st.get_best_server()
            
            server = st.results.server
            
            # Perform download test
            logger.info(f"Testing download speed (server: {server['sponsor']}, {server['name']})...")
            st.download()
            
            # Perform upload test
            logger.info("Testing upload speed...")
            st.upload()
            
            test_duration = time.time() - start_time
            
            # Get results
            results = st.results.dict()
            
            return {
                'server_name': server['sponsor'],
                'server_location': server['name'],
                'server_country': server['country'],
                'download_mbps': results['download'] / 1_000_000,  # Convert to Mbps
                'upload_mbps': results['upload'] / 1_000_000,  # Convert to Mbps
                'ping_ms': results['ping'],
                'jitter_ms': None,  # speedtest-cli doesn't provide jitter
                'packet_loss': None,  # speedtest-cli doesn't provide packet loss
                'isp': results.get('client', {}).get('isp', None),
                'external_ip': results.get('client', {}).get('ip', None),
                'test_duration_seconds': test_duration,
                'is_successful': True,
                'error_message': None
            }
            
        except Exception as e:
            logger.error(f"Error performing speed test: {e}")
            return {
                'server_name': None,
                'server_location': None,
                'server_country': None,
                'download_mbps': None,
                'upload_mbps': None,
                'ping_ms': None,
                'jitter_ms': None,
                'packet_loss': None,
                'isp': None,
                'external_ip': None,
                'test_duration_seconds': None,
                'is_successful': False,
                'error_message': str(e)
            }
    
    def store_speedtest_result(self, result):
        """Store speed test result in database"""
        now = datetime.now()
        unix_timestamp = int(time.time() * 1000)
        
        success = self.db_manager.insert_speedtest_result(
            timestamp=now,
            unix_timestamp=unix_timestamp,
            server_name=result['server_name'],
            server_location=result['server_location'],
            server_country=result['server_country'],
            download_mbps=result['download_mbps'],
            upload_mbps=result['upload_mbps'],
            ping_ms=result['ping_ms'],
            jitter_ms=result['jitter_ms'],
            packet_loss=result['packet_loss'],
            isp=result['isp'],
            external_ip=result['external_ip'],
            test_duration_seconds=result['test_duration_seconds'],
            is_successful=result['is_successful'],
            error_message=result['error_message']
        )
        
        if success and result['is_successful']:
            logger.info(f"Speed test completed: Down {result['download_mbps']:.2f} Mbps, "
                       f"Up {result['upload_mbps']:.2f} Mbps, "
                       f"Ping: {result['ping_ms']:.2f}ms "
                       f"(Server: {result['server_name']}, {result['server_location']})")
        elif success:
            logger.warning(f"Speed test failed: {result['error_message']}")
        else:
            logger.error("Failed to store speed test result")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        interval = self.config.get('interval_seconds', 300)  # Default 5 minutes
        server_id = self.config.get('server_id', None)
        
        logger.info(f"Starting speed test monitor, interval: {interval}s")
        
        while not self.stop_event.is_set():
            result = self.perform_speedtest(server_id)
            self.store_speedtest_result(result)
            
            # Wait for next interval
            self.stop_event.wait(interval)
    
    def start(self):
        """Start monitoring in a separate thread"""
        if not self.config.get('enabled', True):
            logger.info("Speed test monitor is disabled")
            return
        
        self.thread = Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Speed test monitor started")
    
    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping speed test monitor...")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Speed test monitor stopped")
