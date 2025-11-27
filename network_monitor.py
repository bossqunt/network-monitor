"""
Network Monitor - Main Application
Monitors network connectivity using ping and traceroute
Stores results in MySQL database
"""
import sys
import signal
import logging
import time
from config_loader import load_config, validate_config
from db_utils import DatabaseManager
from ping_monitor import PingMonitor
from traceroute_monitor import TracerouteMonitor
from speedtest_monitor import SpeedTestMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('network_monitor.log')
    ]
)

logger = logging.getLogger(__name__)


class NetworkMonitor:
    def __init__(self, config_path='config.yaml'):
        self.config = None
        self.db_manager = None
        self.ping_monitor = None
        self.traceroute_monitor = None
        self.speedtest_monitor = None
        self.config_path = config_path
        self.running = False
    
    def initialize(self):
        """Initialize the application"""
        logger.info("=" * 60)
        logger.info("Network Monitor Starting...")
        logger.info("=" * 60)
        
        # Load configuration
        self.config = load_config(self.config_path)
        if not self.config:
            logger.error("Failed to load configuration")
            return False
        
        # Validate configuration
        if not validate_config(self.config):
            logger.error("Configuration validation failed")
            return False
        
        # Initialize database connection
        self.db_manager = DatabaseManager(self.config['database'])
        if not self.db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Initialize monitors
        self.ping_monitor = PingMonitor(self.db_manager, self.config['ping'])
        self.traceroute_monitor = TracerouteMonitor(
            self.db_manager, 
            self.config['traceroute']
        )
        self.speedtest_monitor = SpeedTestMonitor(
            self.db_manager,
            self.config['speedtest']
        )
        
        logger.info("Initialization complete")
        return True
    
    def start(self):
        """Start all monitors"""
        if not self.initialize():
            logger.error("Initialization failed, exiting")
            return False
        
        self.running = True
        
        # Start monitors
        self.ping_monitor.start()
        self.traceroute_monitor.start()
        self.speedtest_monitor.start()
        
        logger.info("=" * 60)
        logger.info("All monitors started successfully")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        self.stop()
        return True
    
    def stop(self):
        """Stop all monitors and cleanup"""
        logger.info("=" * 60)
        logger.info("Shutting down Network Monitor...")
        logger.info("=" * 60)
        
        self.running = False
        
        # Stop monitors
        if self.ping_monitor:
            self.ping_monitor.stop()
        
        if self.traceroute_monitor:
            self.traceroute_monitor.stop()
        
        if self.speedtest_monitor:
            self.speedtest_monitor.stop()
        
        # Close database connection
        if self.db_manager:
            self.db_manager.disconnect()
        
        logger.info("Network Monitor stopped")


def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start monitor
    monitor = NetworkMonitor()
    success = monitor.start()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
