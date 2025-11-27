"""
Traceroute monitoring module
"""
import time
import socket
import subprocess
import re
import uuid
import logging
from datetime import datetime
from threading import Thread, Event
import platform

logger = logging.getLogger(__name__)


class TracerouteMonitor:
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.stop_event = Event()
        self.thread = None
        self.is_windows = platform.system().lower() == 'windows'
    
    def parse_traceroute_output(self, output, target):
        """
        Parse traceroute output and extract hop information
        Returns list of hop dictionaries
        """
        hops = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Windows tracert format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
            # Linux traceroute format: " 1  192.168.1.1 (192.168.1.1)  0.123 ms  0.456 ms  0.789 ms"
            
            if self.is_windows:
                hop_data = self.parse_windows_tracert(line)
            else:
                hop_data = self.parse_linux_traceroute(line)
            
            if hop_data:
                hops.append(hop_data)
        
        return hops
    
    def parse_windows_tracert(self, line):
        """Parse Windows tracert output line"""
        # Match pattern like: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
        # Or: "  2     *        *        *     Request timed out."
        
        # Try to extract hop number first
        hop_match = re.match(r'^\s*(\d+)\s+', line)
        if not hop_match:
            return None
        
        hop_number = int(hop_match.group(1))
        
        # Check for timeout
        if 'timed out' in line.lower() or '*' in line:
            return {
                'hop_number': hop_number,
                'hop_ip': None,
                'hop_hostname': None,
                'rtt_ms': None,
                'packets_sent': 3,
                'packets_received': 0,
                'is_timeout': True
            }
        
        # Extract IP and hostname
        # Pattern: hop_num  time1  time2  time3  [hostname] ip
        ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
        hostname_pattern = r'([a-zA-Z0-9\-\.]+)\s+\[(\d+\.\d+\.\d+\.\d+)\]'
        
        hop_ip = None
        hop_hostname = None
        
        # Try to match hostname with IP
        hostname_match = re.search(hostname_pattern, line)
        if hostname_match:
            hop_hostname = hostname_match.group(1)
            hop_ip = hostname_match.group(2)
        else:
            # Just IP address
            ip_match = re.search(ip_pattern, line)
            if ip_match:
                hop_ip = ip_match.group(1)
        
        # Extract RTT times
        rtt_times = []
        rtt_pattern = r'<?(\d+)\s*ms'
        for match in re.finditer(rtt_pattern, line):
            rtt_times.append(float(match.group(1)))
        
        packets_received = len(rtt_times)
        avg_rtt = sum(rtt_times) / len(rtt_times) if rtt_times else None
        
        return {
            'hop_number': hop_number,
            'hop_ip': hop_ip,
            'hop_hostname': hop_hostname,
            'rtt_ms': avg_rtt,
            'packets_sent': 3,
            'packets_received': packets_received,
            'is_timeout': packets_received == 0
        }
    
    def parse_linux_traceroute(self, line):
        """Parse Linux traceroute output line"""
        # Pattern: " 1  192.168.1.1 (192.168.1.1)  0.123 ms  0.456 ms  0.789 ms"
        # Or: " 2  * * *"
        
        hop_match = re.match(r'^\s*(\d+)\s+', line)
        if not hop_match:
            return None
        
        hop_number = int(hop_match.group(1))
        
        # Check for timeout
        if line.count('*') >= 3:
            return {
                'hop_number': hop_number,
                'hop_ip': None,
                'hop_hostname': None,
                'rtt_ms': None,
                'packets_sent': 3,
                'packets_received': 0,
                'is_timeout': True
            }
        
        # Extract hostname and IP
        hostname_ip_pattern = r'([a-zA-Z0-9\-\.]+)\s+\((\d+\.\d+\.\d+\.\d+)\)'
        ip_only_pattern = r'(\d+\.\d+\.\d+\.\d+)'
        
        hop_ip = None
        hop_hostname = None
        
        hostname_match = re.search(hostname_ip_pattern, line)
        if hostname_match:
            hop_hostname = hostname_match.group(1)
            hop_ip = hostname_match.group(2)
        else:
            ip_match = re.search(ip_only_pattern, line)
            if ip_match:
                hop_ip = ip_match.group(1)
        
        # Extract RTT times
        rtt_times = []
        rtt_pattern = r'(\d+\.?\d*)\s*ms'
        for match in re.finditer(rtt_pattern, line):
            rtt_times.append(float(match.group(1)))
        
        packets_received = len(rtt_times)
        avg_rtt = sum(rtt_times) / len(rtt_times) if rtt_times else None
        
        return {
            'hop_number': hop_number,
            'hop_ip': hop_ip,
            'hop_hostname': hop_hostname,
            'rtt_ms': avg_rtt,
            'packets_sent': 3,
            'packets_received': packets_received,
            'is_timeout': packets_received == 0
        }
    
    def perform_traceroute(self, target, max_hops=30, timeout=2):
        """
        Perform traceroute and return list of hops
        """
        try:
            if self.is_windows:
                cmd = ['tracert', '-h', str(max_hops), '-w', str(timeout * 1000), target]
            else:
                cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), target]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max_hops * timeout + 10
            )
            
            hops = self.parse_traceroute_output(result.stdout, target)
            return hops
            
        except subprocess.TimeoutExpired:
            logger.error(f"Traceroute to {target} timed out")
            return []
        except Exception as e:
            logger.error(f"Error performing traceroute to {target}: {e}")
            return []
    
    def store_traceroute_results(self, target, hops):
        """Store traceroute results in database"""
        if not hops:
            return
        
        trace_id = str(uuid.uuid4())
        now = datetime.now()
        unix_timestamp = int(time.time() * 1000)
        
        for hop in hops:
            success = self.db_manager.insert_traceroute_hop(
                trace_id=trace_id,
                timestamp=now,
                unix_timestamp=unix_timestamp,
                target=target,
                hop_number=hop['hop_number'],
                hop_ip=hop['hop_ip'],
                hop_hostname=hop['hop_hostname'],
                rtt_ms=hop['rtt_ms'],
                packets_sent=hop['packets_sent'],
                packets_received=hop['packets_received'],
                is_timeout=hop['is_timeout']
            )
            
            if not success:
                logger.error(f"Failed to store traceroute hop {hop['hop_number']} for {target}")
        
        logger.info(f"Traceroute to {target}: {len(hops)} hops stored (trace_id: {trace_id})")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        interval = self.config.get('interval_seconds', 60)
        targets = self.config.get('targets', ['google.com'])
        max_hops = self.config.get('max_hops', 30)
        timeout = self.config.get('timeout_seconds', 2)
        
        logger.info(f"Starting traceroute monitor with {len(targets)} targets, "
                   f"interval: {interval}s")
        
        while not self.stop_event.is_set():
            for target in targets:
                if self.stop_event.is_set():
                    break
                
                hops = self.perform_traceroute(target, max_hops, timeout)
                self.store_traceroute_results(target, hops)
            
            # Wait for next interval
            self.stop_event.wait(interval)
    
    def start(self):
        """Start monitoring in a separate thread"""
        if not self.config.get('enabled', True):
            logger.info("Traceroute monitor is disabled")
            return
        
        self.thread = Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Traceroute monitor started")
    
    def stop(self):
        """Stop monitoring"""
        logger.info("Stopping traceroute monitor...")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Traceroute monitor stopped")
