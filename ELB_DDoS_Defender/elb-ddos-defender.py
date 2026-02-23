#!/usr/bin/env python3.11
"""ELB DDoS Defender - Real-time Traffic Monitor"""
import time
import yaml
import logging
import pyshark
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/elb-ddos-defender/defender.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrafficMonitor:
    def __init__(self, config):
        self.config = config
        self.stats = {
            'total_packets': 0,
            'total_bytes': 0,
            'connections_per_sec': 0,
            'unique_ips': set(),
            'syn_packets': 0,
            'ack_packets': 0,
            'udp_packets': 0,
            'attacks_detected': []
        }
        self.connection_tracker = defaultdict(lambda: deque(maxlen=1000))
        self.packet_times = deque(maxlen=10000)
        self.udp_times = deque(maxlen=5000)
        self.syn_times = deque(maxlen=5000)
        self.bytes_history = deque(maxlen=60)  # Last 60 seconds
        self.running = True
        
        # Thresholds from config
        self.syn_flood_threshold = config.get('thresholds', {}).get('syn_flood_ratio', 3.0)  # SYN:ACK ratio
        self.udp_flood_threshold = config.get('thresholds', {}).get('udp_packets_per_sec', 1000)
        self.packet_rate_threshold = config.get('thresholds', {}).get('packets_per_sec', 5000)
        self.bandwidth_threshold = config.get('thresholds', {}).get('bytes_per_sec', 10000000)  # 10 MB/s
        self.multi_source_threshold = config.get('thresholds', {}).get('multi_source_ips', 50)  # 50 IPs attacking
        
    def analyze_packet(self, packet):
        """Analyze individual packet for threats"""
        try:
            timestamp = time.time()
            self.packet_times.append(timestamp)
            self.stats['total_packets'] += 1
            
            # Get packet size
            packet_size = 0
            if hasattr(packet, 'length'):
                packet_size = int(packet.length)
                self.stats['total_bytes'] += packet_size
                self.bytes_history.append((timestamp, packet_size))
            
            # Extract real IPs from VXLAN or regular packets
            src_ip = None
            dst_ip = None
            dst_port = None
            
            # Check if this is a VXLAN packet (VPC Traffic Mirror)
            is_vxlan = False
            if hasattr(packet, 'udp') and hasattr(packet.udp, 'dstport') and packet.udp.dstport == '4789':
                is_vxlan = True
            
            # ONLY process VXLAN packets (mirrored traffic)
            # Skip defender's own traffic
            if not is_vxlan:
                return
            
            # Get all IP layers
            ip_layers = []
            for layer in packet.layers:
                if layer.layer_name == 'ip':
                    ip_layers.append(layer)
            
            if len(ip_layers) >= 2:
                # VXLAN packet: Use INNER IP (last IP layer)
                # Structure: Outer IP (ALB ENI) → VXLAN → Inner IP (Real Client → ALB)
                inner_ip = ip_layers[-1]  # Last IP layer is the real packet
                
                # For mirrored traffic from ALB:
                # Inner packet shows: Client IP → ALB ENI IP
                if hasattr(inner_ip, 'src') and hasattr(inner_ip, 'dst'):
                    inner_src = inner_ip.src
                    inner_dst = inner_ip.dst
                    
                    # Real client is the one NOT in 10.0.x.x range
                    if not inner_src.startswith('10.0.') and not inner_src.startswith('169.254.'):
                        # Normal: src is the real client
                        src_ip = inner_src
                        dst_ip = inner_dst
                    elif not inner_dst.startswith('10.0.') and not inner_dst.startswith('169.254.'):
                        # Reversed: dst is the real client (response packet)
                        src_ip = inner_dst
                        dst_ip = inner_src
                    else:
                        # Both are 10.0.x.x, skip
                        src_ip = None
                        dst_ip = None
            elif len(ip_layers) > 0:
                # Regular packet: Use first IP layer
                outer_ip = ip_layers[0]
                if hasattr(outer_ip, 'src'):
                    src_ip = outer_ip.src
                if hasattr(outer_ip, 'dst'):
                    dst_ip = outer_ip.dst
            
            # Skip if source is ALB ENI (10.0.x.x) - this means VXLAN decode failed
            if src_ip and src_ip.startswith('10.0.'):
                # Try to find any non-10.0.x.x IP in the packet
                for layer in ip_layers:
                    if hasattr(layer, 'src') and not layer.src.startswith('10.0.'):
                        src_ip = layer.src
                        if hasattr(layer, 'dst'):
                            dst_ip = layer.dst
                        break
            
            # Get destination port from TCP/UDP
            if hasattr(packet, 'tcp') and hasattr(packet.tcp, 'dstport'):
                dst_port = packet.tcp.dstport
            elif hasattr(packet, 'udp') and hasattr(packet.udp, 'dstport'):
                if packet.udp.dstport != '4789':  # Skip VXLAN port
                    dst_port = packet.udp.dstport
            
            # Only process if we have a valid source IP (not ALB ENI)
            if src_ip:
                # Debug: Log what IPs we're seeing
                if src_ip.startswith('10.0.'):
                    logger.debug(f"Skipping ALB ENI IP: {src_ip}")
                else:
                    logger.info(f"Real client IP detected: {src_ip} → {dst_ip}:{dst_port}")
                    
                self.stats['unique_ips'].add(src_ip)
                
                # Track connections per IP with destination info
                conn_info = {
                    'timestamp': timestamp,
                    'dst_ip': dst_ip,
                    'dst_port': dst_port
                }
                self.connection_tracker[src_ip].append(conn_info)
                
                # Check for connection flood from single IP (skip 10.0.x.x)
                if not src_ip.startswith('10.0.'):
                    recent_conns = [c for c in self.connection_tracker[src_ip] 
                                   if timestamp - c['timestamp'] < 1.0]
                    if len(recent_conns) > 100:
                        # Get destination for attack report
                        dest = f"{dst_ip}:{dst_port}" if dst_ip and dst_port else "unknown"
                    self.detect_attack('connection_flood', src_ip, len(recent_conns), dest)
            
            # TCP analysis
            if hasattr(packet, 'tcp'):
                if hasattr(packet.tcp, 'flags'):
                    flags = int(packet.tcp.flags, 16) if isinstance(packet.tcp.flags, str) else packet.tcp.flags
                    # SYN flag (0x02)
                    if flags & 0x02:
                        self.stats['syn_packets'] += 1
                        self.syn_times.append(timestamp)
                    # ACK flag (0x10)
                    if flags & 0x10:
                        self.stats['ack_packets'] += 1
            
            # UDP analysis
            if hasattr(packet, 'udp'):
                self.stats['udp_packets'] += 1
                self.udp_times.append(timestamp)
                
        except Exception as e:
            logger.debug(f"Packet analysis error: {e}")
    
    def detect_attack(self, attack_type, source_ip, metric_value, destination=None):
        """Log detected attack"""
        attack = {
            'type': attack_type,
            'source': source_ip,
            'destination': destination,
            'value': metric_value,
            'timestamp': datetime.now().isoformat()
        }
        self.stats['attacks_detected'].append(attack)
        dest_str = f" → {destination}" if destination else ""
        logger.warning(f"⚠️  ATTACK DETECTED: {attack_type} from {source_ip}{dest_str} ({metric_value} conn/sec)")
    
    def calculate_metrics(self):
        """Calculate real-time metrics"""
        now = time.time()
        
        # Packets per second (last 1 second)
        recent_packets = [t for t in self.packet_times if now - t < 1.0]
        pps = len(recent_packets)
        
        # Connections per second
        total_recent_conns = 0
        for ip, times in self.connection_tracker.items():
            recent = [t for t in times if now - t < 1.0]
            total_recent_conns += len(recent)
        
        self.stats['connections_per_sec'] = total_recent_conns
        self.stats['packets_per_sec'] = pps
        
        # Run DDoS detection checks
        self.check_syn_flood(now)
        self.check_udp_flood(now)
        self.check_packet_rate_spike(pps)
        self.check_bandwidth_spike(now)
        self.check_multi_source_attack(now)
        
        return self.stats
    
    def check_syn_flood(self, now):
        """Detect SYN flood - high SYN:ACK ratio"""
        recent_syns = [t for t in self.syn_times if now - t < 5.0]
        syn_count = len(recent_syns)
        ack_count = self.stats['ack_packets']
        
        if syn_count > 100 and ack_count > 0:
            ratio = syn_count / ack_count
            if ratio > self.syn_flood_threshold:
                self.detect_attack('syn_flood', 'multiple_sources', f"SYN:ACK ratio {ratio:.1f}:1")
    
    def check_udp_flood(self, now):
        """Detect UDP flood - excessive UDP packets"""
        recent_udp = [t for t in self.udp_times if now - t < 1.0]
        udp_per_sec = len(recent_udp)
        
        if udp_per_sec > self.udp_flood_threshold:
            self.detect_attack('udp_flood', 'multiple_sources', f"{udp_per_sec} UDP/s")
    
    def check_packet_rate_spike(self, pps):
        """Detect packet rate spike"""
        if pps > self.packet_rate_threshold:
            self.detect_attack('packet_rate_spike', 'multiple_sources', f"{pps} packets/s")
    
    def check_bandwidth_spike(self, now):
        """Detect bandwidth spike"""
        # Calculate bytes in last second
        recent_bytes = sum(size for ts, size in self.bytes_history if now - ts < 1.0)
        
        if recent_bytes > self.bandwidth_threshold:
            mb_per_sec = recent_bytes / 1024 / 1024
            self.detect_attack('bandwidth_spike', 'multiple_sources', f"{mb_per_sec:.1f} MB/s")
    
    def check_multi_source_attack(self, now):
        """Detect coordinated multi-source attack"""
        # Count IPs with recent activity
        active_attackers = 0
        for ip, times in self.connection_tracker.items():
            recent = [t for t in times if now - t < 5.0]
            if len(recent) > 50:  # IP making >50 connections in 5 seconds
                active_attackers += 1
        
        if active_attackers >= self.multi_source_threshold:
            self.detect_attack('multi_source_ddos', f"{active_attackers}_ips", f"{active_attackers} attacking IPs")
    
    def start_capture(self, interface='ens5'):
        """Start packet capture"""
        logger.info(f"Starting packet capture on {interface}")
        
        try:
            capture = pyshark.LiveCapture(
                interface=interface,
                bpf_filter='tcp or udp'
            )
            
            for packet in capture.sniff_continuously():
                if not self.running:
                    break
                self.analyze_packet(packet)
                
        except Exception as e:
            logger.error(f"Capture error: {e}")
            logger.info("Falling back to simulation mode...")
            self.simulate_traffic()
    
    def simulate_traffic(self):
        """Simulate traffic for testing (when no mirror configured)"""
        import random
        logger.info("Running in simulation mode - generating test traffic")
        
        while self.running:
            # Simulate packets
            for _ in range(random.randint(50, 200)):
                self.stats['total_packets'] += 1
                self.stats['total_bytes'] += random.randint(64, 1500)
                self.packet_times.append(time.time())
            
            # Simulate some IPs
            for _ in range(random.randint(5, 20)):
                fake_ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
                self.stats['unique_ips'].add(fake_ip)
                self.connection_tracker[fake_ip].append(time.time())
            
            time.sleep(0.1)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False

class MetricsWriter:
    """Write metrics to file for dashboard"""
    def __init__(self, monitor):
        self.monitor = monitor
        self.running = True
        
    def write_loop(self):
        """Continuously write metrics"""
        while self.running:
            try:
                # Get metrics snapshot
                stats = self.monitor.stats
                
                # Create safe copy
                metrics_json = {
                    'total_packets': stats['total_packets'],
                    'total_bytes': stats['total_bytes'],
                    'connections_per_sec': stats['connections_per_sec'],
                    'unique_ips': len(stats['unique_ips']),
                    'syn_packets': stats['syn_packets'],
                    'udp_packets': stats['udp_packets'],
                    'attacks_detected': stats['attacks_detected'][-10:],  # Last 10 only
                    'packets_per_sec': stats.get('packets_per_sec', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Write to file
                with open('/var/log/elb-ddos-defender/metrics.json', 'w') as f:
                    json.dump(metrics_json, f, indent=2)
                
                time.sleep(1)
            except Exception as e:
                logger.debug(f"Metrics write error: {e}")
                time.sleep(1)
    
    def stop(self):
        self.running = False

def load_config():
    """Load configuration"""
    try:
        with open('/opt/elb-ddos-defender/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Config load error: {e}")
        return {'monitoring': {'interval': 1}}

def main():
    logger.info("🚀 ELB DDoS Defender started!")
    
    config = load_config()
    
    # Check if load balancers configured
    lbs = config.get('load_balancers', [])
    if lbs:
        logger.info(f"Monitoring {len(lbs)} load balancer(s):")
        for lb in lbs:
            logger.info(f"  - {lb.get('name', 'Unknown')}")
    else:
        logger.warning("⚠️  No load balancers configured - use dashboard to add them")
    
    # Start traffic monitor
    monitor = TrafficMonitor(config)
    
    # Start metrics writer
    metrics_writer = MetricsWriter(monitor)
    metrics_thread = threading.Thread(target=metrics_writer.write_loop, daemon=True)
    metrics_thread.start()
    
    # Start packet capture (will fall back to simulation if no mirror)
    logger.info("Starting traffic analysis...")
    try:
        monitor.start_capture()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        monitor.stop()
        metrics_writer.stop()

if __name__ == '__main__':
    main()
