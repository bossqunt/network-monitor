"""
HTTP/HTTPS monitoring module
"""
import time
import logging
import ssl
import socket
from datetime import datetime
from threading import Thread, Event
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTTPMonitor:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.stop_event = Event()
        self.thread = None
    
    def measure_tls_handshake(self, hostname, port=443, timeout=5):
        """Measure TLS handshake time"""
        try:
            context = ssl.create_default_context()
            start_time = time.time()
            
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    tls_time = (time.time() - start_time) * 1000
                    return tls_time, ssock.version()
        except Exception as e:
            logger.debug(f"TLS handshake error for {hostname}: {e}")
            return None, None
    
    def perform_http_request(self, url, timeout=10):
        """
        Perform HTTP request and measure timing metrics
        Returns: (dns_time_ms, connect_time_ms, tls_time_ms, ttfb_ms, total_time_ms, 
                 status_code, response_size, is_successful, error_message)
        """
        try:
            # Parse URL
            parsed = urlparse(url)
            hostname = parsed.hostname
            is_https = parsed.scheme == 'https'
            
            # Measure TLS handshake time separately if HTTPS
            tls_time_ms = None
            tls_version = None
            if is_https:
                tls_time_ms, tls_version = self.measure_tls_handshake(hostname, 443, timeout)
            
            # Perform HTTP request with detailed timing
            start_time = time.time()
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            total_time_ms = (time.time() - start_time) * 1000
            
            # Get detailed timing from requests
            # Note: requests doesn't provide detailed timing, so we estimate
            dns_time_ms = None  # Not directly available in requests
            connect_time_ms = None  # Not directly available
            
            # TTFB approximation (time to first byte)
            # In requests, elapsed.total_seconds() gives us response time
            ttfb_ms = response.elapsed.total_seconds() * 1000
            
            response_size = len(response.content)
            status_code = response.status_code
            
            return (dns_time_ms, connect_time_ms, tls_time_ms, ttfb_ms, total_time_ms,
                   status_code, response_size, tls_version, True, None)
            
        except requests.exceptions.Timeout:
            return None, None, None, None, None, None, None, None, False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            return None, None, None, None, None, None, None, None, False, f"Connection error: {str(e)}"
        except requests.exceptions.TooManyRedirects:
            return None, None, None, None, None, None, None, None, False, "Too many redirects"
        except Exception as e:
            return None, None, None, None, None, None, None, None, False, str(e)
    
    def store_http_result(self, url, dns_time_ms, connect_time_ms, tls_time_ms, 
                         ttfb_ms, total_time_ms, status_code, response_size, 
                         tls_version, is_successful, error_message):
        """Store HTTP request result in database"""
        now = datetime.now()
        unix_timestamp = int(time.time() * 1000)
        
        success = self.db_manager.insert_http_result(
            timestamp=now,
            unix_timestamp=unix_timestamp,
            url=url,
            dns_time_ms=dns_time_ms,
            connect_time_ms=connect_time_ms,
            tls_time_ms=tls_time_ms,
            ttfb_ms=ttfb_ms,
            total_time_ms=total_time_ms,
            status_code=status_code,
            response_size=response_size,
            tls_version=tls_version,
            is_successful=is_successful,
            error_message=error_message
        )
        
        if success and is_successful:
            logger.info(f"HTTP {url}: {total_time_ms:.0f}ms total, "
                       f"TTFB: {ttfb_ms:.0f}ms, Status: {status_code}, "
                       f"Size: {response_size} bytes")
        elif success:
            logger.warning(f"HTTP {url} failed: {error_message}")
        else:
            logger.error(f"Failed to store HTTP result for {url}")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        interval = self.config.get('interval_seconds', 60)
        urls = self.config.get('urls', [
            'https://www.google.com',
            'https://www.cloudflare.com',
            'https://www.github.com'
        ])
        timeout = self.config.get('timeout_seconds', 10)
        
        logger.info(f"Starting HTTP monitor with {len(urls)} URLs, interval: {interval}s")
        
        while not self.stop_event.is_set():
            for url in urls:
                if self.stop_event.is_set():
                    break
                
                (dns_time_ms, connect_time_ms, tls_time_ms, ttfb_ms, total_time_ms,
                 status_code, response_size, tls_version, is_successful, error_message) = \
                    self.perform_http_request(url, timeout)
                
                self.store_http_result(url, dns_time_ms, connect_time_ms, tls_time_ms,
                                      ttfb_ms, total_time_ms, status_code, response_size,
                                      tls_version, is_successful, error_message)
            
            # Wait for next interval
            self.stop_event.wait(interval)
    
    def start(self):
        """Start monitoring in a separate thread"""
        if not self.config.get('enabled', True):
            logger.info("HTTP monitor is disabled")
            return
        
        self.thread = Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("HTTP monitor started")
    
    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping HTTP monitor...")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("HTTP monitor stopped")
