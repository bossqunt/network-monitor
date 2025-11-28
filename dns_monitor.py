"""
DNS monitoring module
"""
import time
import socket
import logging
from datetime import datetime
from threading import Thread, Event
import dns.resolver
import dns.exception

logger = logging.getLogger(__name__)


class DNSMonitor:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.stop_event = Event()
        self.thread = None
    
    def perform_dns_query(self, domain, nameserver, record_type='A', timeout=5):
        """
        Perform DNS query and measure resolution time
        Returns: (resolution_time_ms, resolved_ips, is_successful, error_message)
        """
        try:
            # Create resolver
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [nameserver]
            resolver.timeout = timeout
            resolver.lifetime = timeout
            
            # Measure resolution time
            start_time = time.time()
            answers = resolver.resolve(domain, record_type)
            resolution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Extract resolved IPs/values
            resolved_values = [str(rdata) for rdata in answers]
            
            return resolution_time, resolved_values, True, None
            
        except dns.exception.Timeout:
            return None, None, False, "DNS query timeout"
        except dns.resolver.NXDOMAIN:
            return None, None, False, "Domain does not exist (NXDOMAIN)"
        except dns.resolver.NoAnswer:
            return None, None, False, "No answer from DNS server"
        except dns.resolver.NoNameservers:
            return None, None, False, "No nameservers available"
        except Exception as e:
            return None, None, False, str(e)
    
    def store_dns_result(self, domain, nameserver, record_type, resolution_time_ms, 
                        resolved_ips, is_successful, error_message):
        """Store DNS query result in database"""
        now = datetime.now()
        unix_timestamp = int(time.time() * 1000)
        
        # Join resolved IPs into comma-separated string
        resolved_ips_str = ','.join(resolved_ips) if resolved_ips else None
        
        success = self.db_manager.insert_dns_result(
            timestamp=now,
            unix_timestamp=unix_timestamp,
            domain=domain,
            nameserver=nameserver,
            record_type=record_type,
            resolution_time_ms=resolution_time_ms,
            resolved_ips=resolved_ips_str,
            is_successful=is_successful,
            error_message=error_message
        )
        
        if success and is_successful:
            logger.info(f"DNS {domain} via {nameserver}: {resolution_time_ms:.2f}ms -> {resolved_ips_str}")
        elif success:
            logger.warning(f"DNS {domain} via {nameserver} failed: {error_message}")
        else:
            logger.error(f"Failed to store DNS result for {domain}")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        interval = self.config.get('interval_seconds', 60)
        domains = self.config.get('domains', ['google.com', 'cloudflare.com'])
        nameservers = self.config.get('nameservers', ['8.8.8.8', '1.1.1.1', '8.8.4.4'])
        record_type = self.config.get('record_type', 'A')
        timeout = self.config.get('timeout_seconds', 5)
        
        logger.info(f"Starting DNS monitor with {len(domains)} domains, "
                   f"{len(nameservers)} nameservers, interval: {interval}s")
        
        while not self.stop_event.is_set():
            for domain in domains:
                for nameserver in nameservers:
                    if self.stop_event.is_set():
                        break
                    
                    resolution_time_ms, resolved_ips, is_successful, error_message = \
                        self.perform_dns_query(domain, nameserver, record_type, timeout)
                    
                    self.store_dns_result(domain, nameserver, record_type, 
                                        resolution_time_ms, resolved_ips, 
                                        is_successful, error_message)
            
            # Wait for next interval
            self.stop_event.wait(interval)
    
    def start(self):
        """Start monitoring in a separate thread"""
        if not self.config.get('enabled', True):
            logger.info("DNS monitor is disabled")
            return
        
        self.thread = Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("DNS monitor started")
    
    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping DNS monitor...")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("DNS monitor stopped")
