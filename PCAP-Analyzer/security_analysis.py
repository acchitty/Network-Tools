#!/usr/bin/env python3
"""
Security Analysis Module
Detects security issues, firewall blocks, and attack patterns
"""

from collections import Counter, defaultdict
from scapy.all import IP, TCP, UDP, ICMP

def analyze_security(packets):
    """
    Analyze security issues and attack patterns
    Returns dict with security analysis
    """
    
    security = {
        'security_group_blocks': [],
        'nacl_blocks': [],
        'tcp_rst_analysis': {
            'total': 0,
            'by_source': Counter(),
            'by_dest_port': Counter(),
            'patterns': []
        },
        'ddos_indicators': {
            'syn_flood': False,
            'udp_flood': False,
            'icmp_flood': False,
            'dns_amplification': False
        },
        'port_scans': [],
        'suspicious_activity': []
    }
    
    # Track TCP connections
    tcp_connections = defaultdict(lambda: {'syn': 0, 'synack': 0, 'rst': 0, 'fin': 0})
    
    # Track packet rates
    packet_rates = {
        'syn_per_second': Counter(),
        'udp_per_second': Counter(),
        'icmp_per_second': Counter()
    }
    
    # Track port scan attempts
    port_scan_tracker = defaultdict(set)  # src_ip -> set of dst_ports
    
    for pkt in packets:
        if not IP in pkt:
            continue
        
        timestamp = int(pkt.time)
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        
        # TCP Analysis
        if TCP in pkt:
            dst_port = pkt[TCP].dport
            flags = pkt[TCP].flags
            conn_key = f"{src_ip}:{pkt[TCP].sport}-{dst_ip}:{dst_port}"
            
            # Track SYN packets
            if flags & 0x02 and not flags & 0x10:  # SYN, no ACK
                tcp_connections[conn_key]['syn'] += 1
                packet_rates['syn_per_second'][timestamp] += 1
                
                # Track potential port scan
                port_scan_tracker[src_ip].add(dst_port)
            
            # Track SYN-ACK packets
            if flags & 0x12 == 0x12:  # SYN+ACK
                tcp_connections[conn_key]['synack'] += 1
            
            # Track RST packets
            if flags & 0x04:  # RST
                tcp_connections[conn_key]['rst'] += 1
                security['tcp_rst_analysis']['total'] += 1
                security['tcp_rst_analysis']['by_source'][src_ip] += 1
                security['tcp_rst_analysis']['by_dest_port'][dst_port] += 1
                
                # Categorize RST pattern
                if pkt[TCP].seq == 0:
                    pattern = 'Firewall/Security Appliance RST'
                elif dst_port < 1024:
                    pattern = 'Service not listening'
                else:
                    pattern = 'Connection refused'
                
                security['tcp_rst_analysis']['patterns'].append({
                    'src': src_ip,
                    'dst': dst_ip,
                    'port': dst_port,
                    'pattern': pattern,
                    'time': pkt.time
                })
            
            # Track FIN packets
            if flags & 0x01:  # FIN
                tcp_connections[conn_key]['fin'] += 1
        
        # UDP Analysis
        if UDP in pkt:
            packet_rates['udp_per_second'][timestamp] += 1
            
            # DNS amplification detection
            if pkt[UDP].sport == 53 and len(pkt) > 512:
                security['ddos_indicators']['dns_amplification'] = True
        
        # ICMP Analysis
        if ICMP in pkt:
            packet_rates['icmp_per_second'][timestamp] += 1
    
    # Post-processing: Detect security group blocks
    for conn_key, counts in tcp_connections.items():
        if counts['syn'] > 0 and counts['synack'] == 0 and counts['rst'] == 0:
            # SYN without response = likely security group block
            parts = conn_key.split('-')
            src = parts[0]
            dst = parts[1]
            security['security_group_blocks'].append({
                'src': src,
                'dst': dst,
                'syn_count': counts['syn']
            })
    
    # Detect DDoS patterns
    max_syn_rate = max(packet_rates['syn_per_second'].values()) if packet_rates['syn_per_second'] else 0
    max_udp_rate = max(packet_rates['udp_per_second'].values()) if packet_rates['udp_per_second'] else 0
    max_icmp_rate = max(packet_rates['icmp_per_second'].values()) if packet_rates['icmp_per_second'] else 0
    
    if max_syn_rate > 1000:
        security['ddos_indicators']['syn_flood'] = True
    if max_udp_rate > 5000:
        security['ddos_indicators']['udp_flood'] = True
    if max_icmp_rate > 1000:
        security['ddos_indicators']['icmp_flood'] = True
    
    # Detect port scans
    for src_ip, ports in port_scan_tracker.items():
        if len(ports) > 20:  # Scanned more than 20 ports
            security['port_scans'].append({
                'src': src_ip,
                'ports_scanned': len(ports),
                'ports': sorted(list(ports))[:10]  # First 10 ports
            })
    
    return security


def print_security_analysis(security):
    """Print security analysis results"""
    
    print("\n" + "="*80)
    print("SECURITY ANALYSIS")
    print("="*80)
    
    # Security Group Blocks
    if security['security_group_blocks']:
        print("\n[Security Group Blocks Detected]")
        print(f"  Total: {len(security['security_group_blocks'])}")
        print("\n  Blocked connections (SYN without response):")
        for block in security['security_group_blocks'][:10]:  # Show first 10
            print(f"    ❌ {block['src']} → {block['dst']} ({block['syn_count']} attempts)")
        
        print("\n  💡 Recommendation: Check security group rules for these connections")
    
    # TCP RST Analysis
    rst = security['tcp_rst_analysis']
    if rst['total'] > 0:
        print("\n[TCP RST Analysis]")
        print(f"  Total RST packets: {rst['total']}")
        
        print("\n  Top sources sending RSTs:")
        for src, count in rst['by_source'].most_common(5):
            print(f"    {src}: {count} RSTs")
        
        print("\n  Top destination ports:")
        for port, count in rst['by_dest_port'].most_common(5):
            print(f"    Port {port}: {count} RSTs")
        
        if rst['patterns']:
            print("\n  RST patterns detected:")
            pattern_counts = Counter(p['pattern'] for p in rst['patterns'])
            for pattern, count in pattern_counts.most_common():
                print(f"    {pattern}: {count}")
    
    # DDoS Indicators
    ddos = security['ddos_indicators']
    if any(ddos.values()):
        print("\n[⚠️  DDoS/Flood Indicators Detected]")
        if ddos['syn_flood']:
            print("  ⚠️  TCP SYN Flood detected (>1000 SYN/sec)")
        if ddos['udp_flood']:
            print("  ⚠️  UDP Flood detected (>5000 UDP/sec)")
        if ddos['icmp_flood']:
            print("  ⚠️  ICMP Flood detected (>1000 ICMP/sec)")
        if ddos['dns_amplification']:
            print("  ⚠️  DNS Amplification attack detected (large DNS responses)")
        
        print("\n  💡 Recommendation: Enable AWS Shield and review CloudWatch metrics")
    
    # Port Scans
    if security['port_scans']:
        print("\n[Port Scan Detection]")
        print(f"  Total scanners detected: {len(security['port_scans'])}")
        
        for scan in security['port_scans'][:5]:  # Show first 5
            print(f"\n  ⚠️  {scan['src']}")
            print(f"     Scanned {scan['ports_scanned']} ports")
            print(f"     Sample ports: {', '.join(map(str, scan['ports']))}")
        
        print("\n  💡 Recommendation: Block scanner IPs in NACL or security groups")


if __name__ == '__main__':
    print("Security Analysis Module")
    print("Import this module into pcap_analyzer_v3.py")
