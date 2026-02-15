#!/usr/bin/env python3
"""
AWS Load Balancer Traffic Analyzer
Supports: ALB, NLB, CLB, GWLB
Monitors TCP/UDP/HTTP/HTTPS, detects loops, health check failures, and application errors
"""

import socket
import struct
import time
import sys
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path

# AWS SDK for CloudWatch
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

class AWSLBTrafficAnalyzer:
    def __init__(self, interface='eth0', sample_rate=10, log_dir='logs', timeout_threshold=5, enable_cloudwatch=False, sns_topic_arn=None):
        self.interface = interface
        self.sample_rate = sample_rate
        self.packet_count = 0
        self.timeout_threshold = timeout_threshold  # seconds
        self.enable_cloudwatch = enable_cloudwatch and AWS_AVAILABLE
        self.sns_topic_arn = sns_topic_arn
        
        # AWS clients
        if self.enable_cloudwatch:
            try:
                # Auto-detect region from EC2 metadata, environment, or boto3
                region = None
                
                # Method 1: Try boto3 session (uses instance metadata automatically)
                try:
                    import boto3
                    session = boto3.session.Session()
                    region = session.region_name
                except:
                    pass
                
                # Method 2: Environment variables
                if not region:
                    import os
                    region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
                
                # Method 3: Default fallback
                if not region:
                    region = 'us-east-1'
                
                self.cloudwatch = boto3.client('cloudwatch', region_name=region)
                self.logs = boto3.client('logs', region_name=region)
                self.sns = boto3.client('sns', region_name=region) if sns_topic_arn else None
                
                # Create CloudWatch Logs group and stream
                self.log_group = '/aws/ec2/traffic-analyzer'
                self.log_stream = f"instance-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                self._setup_cloudwatch_logs()
                
                print(f"✓ CloudWatch integration enabled (region: {region})")
            except Exception as e:
                print(f"Warning: AWS clients failed: {e}")
                self.enable_cloudwatch = False
        
        # Setup logging directory
        script_dir = Path(__file__).parent.absolute()
        self.log_dir = script_dir / log_dir
        self.log_dir.mkdir(exist_ok=True)
        
        # Create daily log file
        today = datetime.now().strftime('%Y-%m-%d')
        self.error_log_file = self.log_dir / f"errors_{today}.log"
        
        self.stats = {
            'total': 0,
            'tcp': 0,
            'udp': 0,
            'http': 0,
            'https': 0,
            'tcp_errors': defaultdict(int),
            'timeouts': defaultdict(int),
            'health_checks': {'success': 0, 'failed': 0, 'tcp': 0, 'udp': 0, 'timeout': 0},
            'http_errors': defaultdict(int),
            'loops_detected': 0,
            'lb_ips': set(),
            'client_ips': defaultdict(int),
            'connections': defaultdict(lambda: {'count': 0, 'errors': 0, 'bytes': 0}),
            'lb_type_indicators': defaultdict(int)
        }
        self.recent_packets = deque(maxlen=200)
        self.connection_state = {}
        self.syn_timestamps = {}
        
        # Timeout tracking
        self.pending_syns = {}  # Track SYN packets waiting for SYN-ACK
        self.pending_requests = {}  # Track HTTP requests waiting for responses
        self.pending_health_checks = {}  # Track health checks waiting for responses
        
        # Clean old logs on startup
        self.cleanup_old_logs()
    
    def _setup_cloudwatch_logs(self):
        """Create CloudWatch Logs group and stream"""
        try:
            self.logs.create_log_group(logGroupName=self.log_group)
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception as e:
            print(f"Warning: Could not create log group: {e}")
        
        try:
            self.logs.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
            self.log_sequence_token = None
        except Exception as e:
            print(f"Warning: Could not create log stream: {e}")
            self.enable_cloudwatch = False
        
    def cleanup_old_logs(self):
        """Remove log files older than 7 days"""
        retention_days = 7
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for log_file in self.log_dir.glob("errors_*.log"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    print(f"Deleted old log: {log_file.name}")
            except Exception as e:
                print(f"Error cleaning up {log_file}: {e}")
    
    def parse_ip_header(self, data):
        if len(data) < 20:
            return None
        
        ip_header = struct.unpack('!BBHHHBBH4s4s', data[:20])
        ihl = (ip_header[0] & 0xF) * 4
        protocol = ip_header[6]
        total_length = ip_header[2]
        src_ip = socket.inet_ntoa(ip_header[8])
        dst_ip = socket.inet_ntoa(ip_header[9])
        
        return {
            'ihl': ihl,
            'protocol': protocol,
            'total_length': total_length,
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'data': data[ihl:]
        }
    
    def parse_tcp_header(self, data):
        if len(data) < 20:
            return None
        
        tcp_header = struct.unpack('!HHLLBBHHH', data[:20])
        offset = (tcp_header[4] >> 4) * 4
        flags = tcp_header[5]
        
        return {
            'src_port': tcp_header[0],
            'dst_port': tcp_header[1],
            'seq': tcp_header[2],
            'ack': tcp_header[3],
            'window': tcp_header[6],
            'flags': {
                'SYN': bool(flags & 0x02),
                'ACK': bool(flags & 0x10),
                'FIN': bool(flags & 0x01),
                'RST': bool(flags & 0x04),
                'PSH': bool(flags & 0x08)
            },
            'data': data[offset:] if offset < len(data) else b''
        }
    
    def parse_udp_header(self, data):
        if len(data) < 8:
            return None
        
        udp_header = struct.unpack('!HHHH', data[:8])
        return {
            'src_port': udp_header[0],
            'dst_port': udp_header[1],
            'length': udp_header[2],
            'data': data[8:]
        }
    
    def parse_http(self, data):
        try:
            decoded = data.decode('utf-8', errors='ignore')
            if len(decoded) < 10:
                return None
                
            lines = decoded.split('\r\n')
            if not lines[0]:
                return None
            
            first_line = lines[0]
            headers = {}
            
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            if first_line.startswith(('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH')):
                parts = first_line.split()
                return {
                    'type': 'request',
                    'method': parts[0] if len(parts) > 0 else None,
                    'path': parts[1] if len(parts) > 1 else None,
                    'headers': headers
                }
            
            if first_line.startswith('HTTP/'):
                parts = first_line.split()
                status_code = int(parts[1]) if len(parts) > 1 else 0
                return {
                    'type': 'response',
                    'status_code': status_code,
                    'headers': headers
                }
        except:
            pass
        return None
    
    def detect_lb_type(self, http_headers, src_ip, protocol, has_proxy_headers):
        if 'x-amzn-trace-id' in http_headers or 'x-forwarded-for' in http_headers:
            self.stats['lb_type_indicators']['ALB'] += 1
            return 'ALB'
        
        if has_proxy_headers and 'x-forwarded-proto' in http_headers:
            self.stats['lb_type_indicators']['CLB'] += 1
            return 'CLB'
        
        if not has_proxy_headers and protocol in [6, 17]:
            self.stats['lb_type_indicators']['NLB'] += 1
            return 'NLB'
        
        return 'Unknown'
    
    def detect_loop(self, packet_sig):
        if packet_sig in self.recent_packets:
            return True
        self.recent_packets.append(packet_sig)
        return False
    
    def is_health_check(self, http_data, src_ip, tcp_data=None):
        if http_data and http_data['type'] == 'request':
            path = http_data.get('path', '')
            user_agent = http_data.get('headers', {}).get('user-agent', '')
            
            health_paths = ['/health', '/healthcheck', '/ping', '/status', '/', '/index.html']
            health_agents = ['ELB-HealthChecker', 'Amazon-Route53-Health-Check-Service']
            
            if any(path.startswith(hp) for hp in health_paths):
                if any(agent in user_agent for agent in health_agents):
                    return True
                if http_data.get('method') == 'GET' and len(http_data.get('headers', {})) <= 3:
                    return True
        
        if tcp_data and tcp_data['flags']['SYN'] and not tcp_data['data']:
            return True
        
        return False
    
    def analyze_tcp(self, ip_data, tcp_data):
        self.stats['tcp'] += 1
        src = f"{ip_data['src_ip']}:{tcp_data['src_port']}"
        dst = f"{ip_data['dst_ip']}:{tcp_data['dst_port']}"
        conn_key = f"{src}->{dst}"
        reverse_key = f"{dst}->{src}"
        flags = tcp_data['flags']
        
        self.stats['connections'][conn_key]['count'] += 1
        self.stats['connections'][conn_key]['bytes'] += len(tcp_data['data'])
        
        # Track SYN packets for timeout detection
        if flags['SYN'] and not flags['ACK']:
            self.connection_state[conn_key] = 'SYN_SENT'
            self.syn_timestamps[conn_key] = time.time()
            self.pending_syns[conn_key] = time.time()
            
        elif flags['SYN'] and flags['ACK']:
            self.connection_state[conn_key] = 'SYN_ACK'
            # Remove from pending - connection established
            if reverse_key in self.pending_syns:
                del self.pending_syns[reverse_key]
            
            if conn_key in self.syn_timestamps:
                handshake_time = time.time() - self.syn_timestamps[conn_key]
                if handshake_time > 1.0:
                    self.log_event('SLOW_HANDSHAKE', f"{conn_key} took {handshake_time:.2f}s")
                    
        elif flags['RST']:
            self.connection_state[conn_key] = 'RESET'
            self.stats['tcp_errors']['RST'] += 1
            self.stats['connections'][conn_key]['errors'] += 1
            self.log_event('TCP_ERROR', f"Connection reset: {conn_key}")
            # Clean up pending
            self.pending_syns.pop(conn_key, None)
            self.pending_syns.pop(reverse_key, None)
            
        elif flags['FIN']:
            self.connection_state[conn_key] = 'CLOSING'
            # Clean up pending
            self.pending_syns.pop(conn_key, None)
            self.pending_syns.pop(reverse_key, None)
        
        if flags['SYN'] and not flags['ACK'] and tcp_data['window'] == 0:
            self.stats['tcp_errors']['ZERO_WINDOW'] += 1
            self.log_event('TCP_ERROR', f"Zero window: {conn_key}")
        
        packet_sig = f"{src}:{dst}:{tcp_data['seq']}"
        if self.detect_loop(packet_sig):
            self.stats['loops_detected'] += 1
            self.stats['tcp_errors']['RETRANSMIT'] += 1
        
        # Health check detection
        is_hc = self.is_health_check(None, ip_data['src_ip'], tcp_data)
        if is_hc:
            self.stats['health_checks']['tcp'] += 1
            if flags['SYN'] and not flags['ACK']:
                self.pending_health_checks[conn_key] = time.time()
            elif flags['SYN'] and flags['ACK']:
                if reverse_key in self.pending_health_checks:
                    del self.pending_health_checks[reverse_key]
            elif flags['RST']:
                self.stats['health_checks']['failed'] += 1
                self.log_event('HEALTH_CHECK_FAIL', f"TCP health check failed: {conn_key}")
                self.pending_health_checks.pop(conn_key, None)
        
        if tcp_data['data']:
            http_data = self.parse_http(tcp_data['data'])
            if http_data:
                if tcp_data['dst_port'] == 443 or tcp_data['src_port'] == 443:
                    self.stats['https'] += 1
                else:
                    self.stats['http'] += 1
                
                self.analyze_http(http_data, ip_data, conn_key)
    
    def analyze_http(self, http_data, ip_data, conn_key):
        headers = http_data.get('headers', {})
        src_ip = ip_data['src_ip']
        
        has_proxy_headers = bool('x-forwarded-for' in headers or 'x-forwarded-proto' in headers)
        lb_type = self.detect_lb_type(headers, src_ip, ip_data['protocol'], has_proxy_headers)
        
        self.stats['lb_ips'].add(src_ip)
        
        if 'x-forwarded-for' in headers:
            client_ip = headers['x-forwarded-for'].split(',')[0].strip()
            self.stats['client_ips'][client_ip] += 1
        else:
            self.stats['client_ips'][src_ip] += 1
        
        # Track HTTP requests for timeout detection
        if http_data['type'] == 'request':
            request_key = f"{conn_key}:{http_data.get('method')}:{http_data.get('path')}"
            self.pending_requests[request_key] = time.time()
            
            # Track health check requests
            if self.is_health_check(http_data, src_ip):
                self.pending_health_checks[request_key] = time.time()
        
        # Track HTTP responses
        if http_data['type'] == 'response':
            # Remove from pending - got response
            for key in list(self.pending_requests.keys()):
                if key.startswith(conn_key):
                    del self.pending_requests[key]
            for key in list(self.pending_health_checks.keys()):
                if key.startswith(conn_key):
                    del self.pending_health_checks[key]
        
        if self.is_health_check(http_data, src_ip):
            if http_data['type'] == 'response':
                status = http_data.get('status_code', 0)
                if 200 <= status < 300:
                    self.stats['health_checks']['success'] += 1
                else:
                    self.stats['health_checks']['failed'] += 1
                    self.log_event('HEALTH_CHECK_FAIL', f"HTTP {status} from {conn_key}")
        
        if http_data['type'] == 'response':
            status = http_data.get('status_code', 0)
            if status >= 400:
                self.stats['http_errors'][status] += 1
                if status >= 500:
                    self.log_event('APP_ERROR', f"HTTP {status} from {conn_key}")
                elif status in [502, 503, 504]:
                    self.log_event('LB_ERROR', f"HTTP {status} (LB issue) from {conn_key}")
        
        if http_data['type'] == 'response' and 300 <= http_data.get('status_code', 0) < 400:
            location = headers.get('location', '')
            if location:
                redirect_sig = f"{conn_key}:{location}"
                if redirect_sig in self.recent_packets:
                    self.stats['loops_detected'] += 1
                    self.log_event('REDIRECT_LOOP', f"Redirect loop: {location}")
        
        via = headers.get('via', '')
        if via and via.count(',') > 3:
            self.log_event('PROXY_LOOP', f"Excessive hops ({via.count(',') + 1}): {via}")
    
    def analyze_udp(self, ip_data, udp_data):
        self.stats['udp'] += 1
        src = f"{ip_data['src_ip']}:{udp_data['src_port']}"
        dst = f"{ip_data['dst_ip']}:{udp_data['dst_port']}"
        conn_key = f"{src}->{dst}"
        
        self.stats['connections'][conn_key]['count'] += 1
        self.stats['connections'][conn_key]['bytes'] += udp_data['length']
        
        if udp_data['length'] < 100:
            self.stats['health_checks']['udp'] += 1
    
    def check_timeouts(self):
        """Check for timed out connections and requests"""
        current_time = time.time()
        
        # Check SYN timeouts (no SYN-ACK received)
        for conn_key, timestamp in list(self.pending_syns.items()):
            if current_time - timestamp > self.timeout_threshold:
                self.stats['timeouts']['SYN_TIMEOUT'] += 1
                self.stats['tcp_errors']['SYN_TIMEOUT'] += 1
                self.log_event('TIMEOUT', f"SYN timeout (no response): {conn_key}")
                del self.pending_syns[conn_key]
        
        # Check HTTP request timeouts (no response received)
        for request_key, timestamp in list(self.pending_requests.items()):
            if current_time - timestamp > self.timeout_threshold:
                self.stats['timeouts']['HTTP_TIMEOUT'] += 1
                self.log_event('TIMEOUT', f"HTTP request timeout (no response): {request_key}")
                del self.pending_requests[request_key]
        
        # Check health check timeouts
        for hc_key, timestamp in list(self.pending_health_checks.items()):
            if current_time - timestamp > self.timeout_threshold:
                self.stats['timeouts']['HEALTH_CHECK_TIMEOUT'] += 1
                self.stats['health_checks']['timeout'] += 1
                self.stats['health_checks']['failed'] += 1
                self.log_event('HEALTH_CHECK_TIMEOUT', f"Health check timeout (no response): {hc_key}")
                del self.pending_health_checks[hc_key]
    
    def analyze_packet(self, data):
        self.stats['total'] += 1
        
        if self.stats['total'] % self.sample_rate != 0:
            return
        
        ip_data = self.parse_ip_header(data)
        if not ip_data:
            return
        
        if ip_data['protocol'] == 6:
            tcp_data = self.parse_tcp_header(ip_data['data'])
            if tcp_data:
                self.analyze_tcp(ip_data, tcp_data)
        
        elif ip_data['protocol'] == 17:
            udp_data = self.parse_udp_header(ip_data['data'])
            if udp_data:
                self.analyze_udp(ip_data, udp_data)
    
    def log_event(self, event_type, message):
        """Log events to console, file, and CloudWatch Logs"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {event_type}: {message}\n"
        
        # Print to console
        print(log_line.strip(), file=sys.stderr)
        
        # Write to log file
        try:
            with open(self.error_log_file, 'a') as f:
                f.write(log_line)
        except Exception as e:
            print(f"Failed to write to log file: {e}", file=sys.stderr)
        
        # Send to CloudWatch Logs
        if self.enable_cloudwatch:
            try:
                log_event = {
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'message': f"{event_type}: {message}"
                }
                
                kwargs = {
                    'logGroupName': self.log_group,
                    'logStreamName': self.log_stream,
                    'logEvents': [log_event]
                }
                
                if self.log_sequence_token:
                    kwargs['sequenceToken'] = self.log_sequence_token
                
                response = self.logs.put_log_events(**kwargs)
                self.log_sequence_token = response.get('nextSequenceToken')
            except Exception as e:
                # Silently fail CloudWatch logging to not disrupt analysis
                pass
    
    def send_cloudwatch_metrics(self):
        """Send metrics to CloudWatch"""
        if not self.enable_cloudwatch:
            return
        
        try:
            metric_data = [
                {'MetricName': 'TimeoutCount', 'Value': sum(self.stats['timeouts'].values()), 'Unit': 'Count'},
                {'MetricName': 'TCPErrorCount', 'Value': sum(self.stats['tcp_errors'].values()), 'Unit': 'Count'},
                {'MetricName': 'HealthCheckFailures', 'Value': self.stats['health_checks']['failed'], 'Unit': 'Count'},
                {'MetricName': 'LoopCount', 'Value': self.stats['loops_detected'], 'Unit': 'Count'},
                {'MetricName': 'ConnectionCount', 'Value': len(self.stats['connections']), 'Unit': 'Count'}
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='LBTrafficAnalyzer',
                MetricData=metric_data
            )
        except Exception as e:
            print(f"CloudWatch error: {e}", file=sys.stderr)
    
    def print_stats(self):
        print("\n" + "="*70)
        print(f"AWS Load Balancer Traffic Analyzer (sampled 1/{self.sample_rate})")
        print(f"Log directory: {self.log_dir}")
        print("="*70)
        print(f"Total: {self.stats['total']} | TCP: {self.stats['tcp']} | UDP: {self.stats['udp']}")
        print(f"HTTP: {self.stats['http']} | HTTPS: {self.stats['https']}")
        
        print(f"\n--- Detected LB Types ---")
        for lb_type, count in sorted(self.stats['lb_type_indicators'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {lb_type}: {count} indicators")
        
        print(f"\n--- Health Checks ---")
        print(f"Success: {self.stats['health_checks']['success']} | Failed: {self.stats['health_checks']['failed']}")
        print(f"TCP: {self.stats['health_checks']['tcp']} | UDP: {self.stats['health_checks']['udp']} | Timeout: {self.stats['health_checks']['timeout']}")
        
        print(f"\n--- TCP Errors ---")
        for error_type, count in sorted(self.stats['tcp_errors'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
        
        print(f"\n--- Timeouts ---")
        total_timeouts = sum(self.stats['timeouts'].values())
        print(f"Total timeouts: {total_timeouts}")
        for timeout_type, count in sorted(self.stats['timeouts'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {timeout_type}: {count}")
        
        print(f"\n--- HTTP Errors ---")
        for status, count in sorted(self.stats['http_errors'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  HTTP {status}: {count}")
        
        print(f"\n--- Loops & Issues ---")
        print(f"Total loops detected: {self.stats['loops_detected']}")
        
        print(f"\n--- Load Balancer IPs ({len(self.stats['lb_ips'])}) ---")
        for lb_ip in list(self.stats['lb_ips'])[:10]:
            print(f"  {lb_ip}")
        
        print(f"\n--- Top Client IPs ---")
        sorted_clients = sorted(self.stats['client_ips'].items(), key=lambda x: x[1], reverse=True)
        for client_ip, count in sorted_clients[:15]:
            print(f"  {client_ip}: {count} requests")
        
        print(f"\n--- Top Connections ---")
        sorted_conns = sorted(self.stats['connections'].items(), key=lambda x: x[1]['count'], reverse=True)
        for conn, data in sorted_conns[:15]:
            error_marker = f" [ERRORS: {data['errors']}]" if data['errors'] > 0 else ""
            bytes_str = f" [{data['bytes']} bytes]" if data['bytes'] > 0 else ""
            print(f"  {conn}: {data['count']} pkts{bytes_str}{error_marker}")
        
        print("="*70 + "\n")
    
    def run(self):
        try:
            sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))
            sock.bind((self.interface, 0))
            
            print(f"AWS Load Balancer Traffic Analyzer")
            print(f"Interface: {self.interface} | Sample rate: 1/{self.sample_rate}")
            print(f"Timeout threshold: {self.timeout_threshold}s")
            print(f"Log directory: {self.log_dir}")
            print(f"Error log: {self.error_log_file.name}")
            print(f"Log retention: 7 days")
            print(f"Supports: ALB, NLB, CLB, GWLB")
            print(f"Monitoring: TCP, UDP, HTTP, HTTPS, Health Checks, Loops, Errors, Timeouts")
            print(f"Press Ctrl+C to view stats\n")
            
            last_stats = time.time()
            last_timeout_check = time.time()
            
            while True:
                data, addr = sock.recvfrom(65535)
                self.analyze_packet(data[14:])
                self.packet_count += 1
                
                # Check for timeouts every 2 seconds
                if time.time() - last_timeout_check > 2:
                    self.check_timeouts()
                    last_timeout_check = time.time()
                
                if time.time() - last_stats > 30:
                    self.print_stats()
                    self.send_cloudwatch_metrics()
                    last_stats = time.time()
        
        except KeyboardInterrupt:
            print("\n\nStopping analyzer...")
        except PermissionError:
            print("ERROR: Requires root privileges")
            print("Run with: sudo python3 aws-lb-traffic-analyzer.py")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            self.print_stats()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AWS Load Balancer Traffic Analyzer (ALB/NLB/CLB/GWLB)')
    parser.add_argument('-i', '--interface', default='eth0', help='Network interface (default: eth0)')
    parser.add_argument('-s', '--sample-rate', type=int, default=10, help='Sample 1 in N packets (default: 10)')
    parser.add_argument('-l', '--log-dir', default='logs', help='Log directory name (default: logs)')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='Timeout threshold in seconds (default: 5)')
    parser.add_argument('--enable-cloudwatch', action='store_true', help='Enable CloudWatch metrics')
    parser.add_argument('--sns-topic', type=str, help='SNS topic ARN for alerts')
    
    args = parser.parse_args()
    
    analyzer = AWSLBTrafficAnalyzer(
        interface=args.interface, 
        sample_rate=args.sample_rate,
        log_dir=args.log_dir,
        timeout_threshold=args.timeout,
        enable_cloudwatch=args.enable_cloudwatch,
        sns_topic_arn=args.sns_topic
    )
    analyzer.run()

if __name__ == '__main__':
    main()
