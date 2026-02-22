#!/usr/bin/env python3
"""
AWS Service Detection Module
Detects AWS-specific traffic patterns in PCAP files
"""

from collections import Counter, defaultdict
from scapy.all import IP, TCP, UDP, Raw

def detect_aws_services(packets):
    """
    Detect AWS-specific traffic patterns
    Returns dict with AWS service analysis
    """
    
    aws_analysis = {
        'elb_health_checks': {
            'alb': 0,
            'clb': 0,
            'nlb_tcp': 0,
            'total': 0,
            'success': 0,
            'failures': [],
            'targets': defaultdict(lambda: {'success': 0, 'failure': 0})
        },
        'imds_access': {
            'v1_get': 0,
            'v2_token': 0,
            'total': 0,
            'paths': Counter(),
            'sources': Counter(),
            'security_warning': False
        },
        'nat_gateway': {
            'total_connections': 0,
            'rst_packets': 0,
            'timeouts': 0,
            'port_exhaustion_risk': False
        },
        'transit_gateway': {
            'cross_vpc_traffic': 0,
            'potential_asymmetric': [],
            'vpc_cidrs': set()
        }
    }
    
    # Track TCP streams for NLB health check detection
    tcp_streams = defaultdict(lambda: {'syn': False, 'synack': False})
    
    for pkt in packets:
        if not IP in pkt:
            continue
        
        # IMDS Detection (169.254.169.254)
        if pkt[IP].dst == '169.254.169.254':
            aws_analysis['imds_access']['total'] += 1
            aws_analysis['imds_access']['sources'][pkt[IP].src] += 1
            
            if TCP in pkt and Raw in pkt:
                payload = pkt[Raw].load.decode('utf-8', errors='ignore')
                
                # IMDSv2 token request
                if 'PUT' in payload and '/latest/api/token' in payload:
                    aws_analysis['imds_access']['v2_token'] += 1
                
                # IMDSv1 GET request
                elif 'GET' in payload:
                    aws_analysis['imds_access']['v1_get'] += 1
                    aws_analysis['imds_access']['security_warning'] = True
                    
                    # Extract path
                    if 'GET /' in payload:
                        path = payload.split('GET ')[1].split(' ')[0]
                        aws_analysis['imds_access']['paths'][path] += 1
        
        # ELB Health Check Detection
        if TCP in pkt and Raw in pkt:
            payload = pkt[Raw].load.decode('utf-8', errors='ignore')
            
            # ALB/CLB health checks
            if 'ELB-HealthChecker' in payload:
                aws_analysis['elb_health_checks']['total'] += 1
                target = pkt[IP].dst
                
                # Detect version
                if 'ELB-HealthChecker/2.0' in payload:
                    aws_analysis['elb_health_checks']['alb'] += 1
                elif 'ELB-HealthChecker/1.0' in payload:
                    aws_analysis['elb_health_checks']['clb'] += 1
                
                # Check response code
                if 'HTTP/' in payload:
                    if '200 OK' in payload:
                        aws_analysis['elb_health_checks']['success'] += 1
                        aws_analysis['elb_health_checks']['targets'][target]['success'] += 1
                    else:
                        # Extract status code
                        code_match = payload.split('HTTP/')[1].split()[0] if 'HTTP/' in payload else 'Unknown'
                        aws_analysis['elb_health_checks']['targets'][target]['failure'] += 1
                        aws_analysis['elb_health_checks']['failures'].append({
                            'target': target,
                            'code': code_match,
                            'time': pkt.time
                        })
        
        # NLB Health Check Detection (TCP SYN/SYN-ACK)
        if TCP in pkt:
            stream_key = f"{pkt[IP].src}:{pkt[TCP].sport}-{pkt[IP].dst}:{pkt[TCP].dport}"
            
            # SYN packet
            if pkt[TCP].flags & 0x02 and not pkt[TCP].flags & 0x10:  # SYN, no ACK
                tcp_streams[stream_key]['syn'] = True
            
            # SYN-ACK packet
            if pkt[TCP].flags & 0x12 == 0x12:  # SYN+ACK
                reverse_key = f"{pkt[IP].dst}:{pkt[TCP].dport}-{pkt[IP].src}:{pkt[TCP].sport}"
                if tcp_streams[reverse_key]['syn']:
                    tcp_streams[reverse_key]['synack'] = True
                    aws_analysis['elb_health_checks']['nlb_tcp'] += 1
        
        # NAT Gateway Detection
        if TCP in pkt:
            aws_analysis['nat_gateway']['total_connections'] += 1
            
            # RST packets (potential port exhaustion)
            if pkt[TCP].flags & 0x04:  # RST flag
                if pkt[TCP].sport > 1024:  # Ephemeral port
                    aws_analysis['nat_gateway']['rst_packets'] += 1
            
            # Check for port exhaustion risk (>50k connections)
            if aws_analysis['nat_gateway']['total_connections'] > 50000:
                aws_analysis['nat_gateway']['port_exhaustion_risk'] = True
        
        # Transit Gateway / Cross-VPC Detection
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        
        # Detect RFC1918 addresses (private IPs)
        if _is_private_ip(src_ip) and _is_private_ip(dst_ip):
            src_subnet = '.'.join(src_ip.split('.')[:2])
            dst_subnet = '.'.join(dst_ip.split('.')[:2])
            
            # Different subnets = potential cross-VPC
            if src_subnet != dst_subnet:
                aws_analysis['transit_gateway']['cross_vpc_traffic'] += 1
                aws_analysis['transit_gateway']['vpc_cidrs'].add(src_subnet)
                aws_analysis['transit_gateway']['vpc_cidrs'].add(dst_subnet)
    
    # Post-processing: Check for NLB health check success rate
    nlb_success = sum(1 for s in tcp_streams.values() if s['syn'] and s['synack'])
    nlb_total = sum(1 for s in tcp_streams.values() if s['syn'])
    
    if nlb_total > 0:
        aws_analysis['elb_health_checks']['nlb_success_rate'] = (nlb_success / nlb_total) * 100
    
    return aws_analysis


def _is_private_ip(ip):
    """Check if IP is in RFC1918 private range"""
    octets = ip.split('.')
    if len(octets) != 4:
        return False
    
    first = int(octets[0])
    second = int(octets[1])
    
    # 10.0.0.0/8
    if first == 10:
        return True
    # 172.16.0.0/12
    if first == 172 and 16 <= second <= 31:
        return True
    # 192.168.0.0/16
    if first == 192 and second == 168:
        return True
    
    return False


def print_aws_analysis(aws_analysis):
    """Print AWS service detection results"""
    
    print("\n" + "="*80)
    print("AWS SERVICE DETECTION")
    print("="*80)
    
    # ELB Health Checks
    elb = aws_analysis['elb_health_checks']
    if elb['total'] > 0:
        print("\n[ELB Health Checks]")
        print(f"  Total: {elb['total']}")
        print(f"    ALB (v2.0): {elb['alb']}")
        print(f"    CLB (v1.0): {elb['clb']}")
        print(f"    NLB (TCP): {elb['nlb_tcp']}")
        print(f"  Success: {elb['success']}")
        print(f"  Failures: {len(elb['failures'])}")
        
        if elb['failures']:
            print("\n  Failed Health Checks:")
            for failure in elb['failures'][:5]:  # Show first 5
                print(f"    ❌ {failure['target']} returned {failure['code']}")
        
        if elb['targets']:
            print("\n  Per-Target Summary:")
            for target, counts in sorted(elb['targets'].items()):
                total = counts['success'] + counts['failure']
                rate = (counts['success'] / total * 100) if total > 0 else 0
                status = "✓" if rate == 100 else "✗"
                print(f"    {status} {target}: {counts['success']}/{total} ({rate:.0f}%)")
    
    # IMDS Access
    imds = aws_analysis['imds_access']
    if imds['total'] > 0:
        print("\n[IMDS Access - 169.254.169.254]")
        print(f"  Total requests: {imds['total']}")
        print(f"    IMDSv1 (GET): {imds['v1_get']}")
        print(f"    IMDSv2 (token): {imds['v2_token']}")
        
        if imds['security_warning']:
            print("\n  ⚠️  WARNING: IMDSv1 access detected!")
            print("     Consider migrating to IMDSv2 for better security")
        
        if imds['paths']:
            print("\n  Top accessed paths:")
            for path, count in imds['paths'].most_common(5):
                print(f"    {count:3d}x {path}")
        
        if imds['sources']:
            print("\n  Sources accessing IMDS:")
            for src, count in imds['sources'].most_common(5):
                print(f"    {src}: {count} requests")
    
    # NAT Gateway
    nat = aws_analysis['nat_gateway']
    if nat['total_connections'] > 0:
        print("\n[NAT Gateway Analysis]")
        print(f"  Total connections: {nat['total_connections']}")
        print(f"  RST packets: {nat['rst_packets']}")
        
        if nat['port_exhaustion_risk']:
            print("\n  ⚠️  WARNING: High connection count detected!")
            print("     NAT Gateway limit: 55,000 connections per IP")
            print("     Consider adding more NAT Gateways")
    
    # Transit Gateway
    tgw = aws_analysis['transit_gateway']
    if tgw['cross_vpc_traffic'] > 0:
        print("\n[Transit Gateway / Cross-VPC Traffic]")
        print(f"  Cross-VPC packets: {tgw['cross_vpc_traffic']}")
        print(f"  Detected VPC subnets: {len(tgw['vpc_cidrs'])}")
        if tgw['vpc_cidrs']:
            print(f"    {', '.join(sorted(tgw['vpc_cidrs']))}")


if __name__ == '__main__':
    print("AWS Service Detection Module")
    print("Import this module into pcap_analyzer_v3.py")
