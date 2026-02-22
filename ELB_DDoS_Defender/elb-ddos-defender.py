#!/usr/bin/env python3
"""
ELB DDoS Defender - Main Application
Monitors AWS load balancers for DDoS attacks using VPC Traffic Mirroring
"""

import os
import sys
import yaml
import time
import threading
from datetime import datetime
from collections import defaultdict

# Add SDK to path
sys.path.insert(0, os.path.dirname(__file__))

# Import SDKs
from sdk.cloudwatch_sdk import CloudWatchSDK
from sdk.pcap_capture_sdk import PCAPCaptureSDK

# Configuration
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.yaml')
LOG_FILE = "/var/log/elb-ddos-defender.log"

# Load configuration
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

# Initialize SDKs
cw_sdk = CloudWatchSDK(
    log_group=config.get('logging', {}).get('log_group', '/aws/elb-monitor'),
    region=config.get('aws', {}).get('region', 'us-east-1')
)

pcap_sdk = PCAPCaptureSDK(
    pcap_dir=config.get('logging', {}).get('pcap_dir', '/var/log/pcaps')
)

# Track traffic per IP
ip_tracker = defaultdict(lambda: {
    "count": 0,
    "last_reset": time.time(),
    "protocols": defaultdict(int),
    "ports": defaultdict(int)
})

def log_message(message, level="INFO", lb_name=None):
    """Log message to file and CloudWatch"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    
    # Write to global log
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")
    
    # Write to per-LB log if specified
    if lb_name:
        for lb in config.get('load_balancers', []):
            if lb['name'] == lb_name:
                log_prefix = lb.get('log_prefix', lb_name)
                lb_log_dir = f"/var/log/elb-ddos-defender/{log_prefix}"
                os.makedirs(lb_log_dir, exist_ok=True)
                with open(f"{lb_log_dir}/monitor.log", "a") as f:
                    f.write(log_line + "\n")
                break
    
    print(log_line)
    
    # Send to CloudWatch
    try:
        cw_sdk.put_log(log_line)
    except:
        pass

def detect_attack(src_ip):
    """Simple attack detection based on connection rate"""
    data = ip_tracker[src_ip]
    threshold = config.get('global_thresholds', {}).get('connections_per_second', 100)
    
    if data["count"] > threshold:
        return True
    return False

def handle_attack(src_ip):
    """Handle detected attack"""
    log_message(f"🚨 ATTACK DETECTED from {src_ip}", "CRITICAL")
    log_message(f"   Packets/sec: {ip_tracker[src_ip]['count']}", "CRITICAL")
    
    # Send CloudWatch metric
    try:
        cw_sdk.put_metric(
            metric_name='DDoSAttackDetected',
            value=1,
            dimensions={'SourceIP': src_ip}
        )
    except:
        pass
    
    # TODO: Generate report and send email
    # TODO: Implement mitigation

def track_packet(src_ip, protocol, dst_port):
    """Track packet for attack detection"""
    current_time = time.time()
    
    # Reset counter every second
    if current_time - ip_tracker[src_ip]["last_reset"] > 1:
        ip_tracker[src_ip]["count"] = 0
        ip_tracker[src_ip]["last_reset"] = current_time
    
    ip_tracker[src_ip]["count"] += 1
    ip_tracker[src_ip]["protocols"][protocol] += 1
    ip_tracker[src_ip]["ports"][dst_port] += 1
    
    # Check for attack
    if detect_attack(src_ip):
        handle_attack(src_ip)
        ip_tracker[src_ip]["count"] = 0  # Reset to avoid repeated alerts

def process_packet(packet):
    """Process captured packet (placeholder for Scapy integration)"""
    # This would use Scapy to parse VXLAN packets
    # For now, this is a placeholder
    pass

def monitor_health(lb_configs):
    """Monitor load balancer health"""
    while True:
        for lb in lb_configs:
            if not lb.get('enabled', True):
                continue
            
            # TODO: Check target health
            # TODO: Send health metrics
            
        time.sleep(60)

def main():
    """Main application entry point"""
    log_message("🚀 ELB DDoS Defender Started", "INFO")
    log_message(f"📧 Email alerts: {config['alerts']['email']['sender']}", "INFO")
    
    # Log monitored load balancers
    for lb in config.get('load_balancers', []):
        if lb.get('enabled', True):
            log_message(f"📊 Monitoring: {lb['name']} ({lb['type']})", "INFO")
    
    # Start background PCAP capture
    log_message("📹 Starting background PCAP capture...", "INFO")
    try:
        pcap_sdk.start_background_capture()
        log_message("✅ Background capture started", "INFO")
    except Exception as e:
        log_message(f"⚠️  PCAP capture failed: {e}", "WARNING")
    
    # Start health monitoring thread
    lb_configs = config.get('load_balancers', [])
    health_thread = threading.Thread(target=monitor_health, args=(lb_configs,), daemon=True)
    health_thread.start()
    
    # Main monitoring loop
    log_message("📡 Listening for traffic...", "INFO")
    
    try:
        # TODO: Implement Scapy packet capture
        # For now, just keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("🛑 Shutting down...", "INFO")
    except Exception as e:
        log_message(f"❌ Error: {e}", "ERROR")
        raise

if __name__ == "__main__":
    main()
