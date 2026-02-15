#!/usr/bin/env python3
"""
Advanced PCAP Analyzer v4 - Enhanced Edition
Combines tcpdump analysis with Scapy deep packet inspection
NEW: Visual diagrams, Whois lookups, Tor detection, Interactive HTML maps
Features: Protocol analysis, payload extraction, conversation tracking, statistical analysis
"""

import subprocess
import sys
import re
import json
import argparse
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Set output directory to Desktop
OUTPUT_DIR = Path.home() / "Desktop" / "pcap_analysis_output"
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    from scapy.all import rdpcap, IP, TCP, UDP, ICMP, DNS, Raw, ARP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("⚠ Scapy not installed. Install with: pip3 install scapy")
    print("Running in tcpdump-only mode...\n")

# Optional visual features
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import networkx as nx
    VISUAL_AVAILABLE = True
except ImportError:
    VISUAL_AVAILABLE = False

try:
    from ipwhois import IPWhois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

def run_tcpdump(pcap_file, filter_expr='', count=None):
    """Run tcpdump and return output lines"""
    cmd = ['tcpdump', '-r', pcap_file, '-nn']
    if count:
        cmd.extend(['-c', str(count)])
    if filter_expr:
        cmd.extend(filter_expr.split())
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    lines = [line.strip() for line in result.stdout.split('\n') 
             if line.strip() and not line.startswith('reading from file') and 'link-type' not in line]
    return lines

def analyze_with_scapy(pcap_file):
    """Deep packet analysis using Scapy"""
    if not SCAPY_AVAILABLE:
        return None
    
    print("\n" + "="*100)
    print("SCAPY DEEP PACKET ANALYSIS")
    print("="*100)
    
    packets = rdpcap(pcap_file)
    
    analysis = {
        'total_packets': len(packets),
        'protocols': Counter(),
        'conversations': defaultdict(lambda: {'packets': 0, 'bytes': 0}),
        'src_ips': Counter(),
        'dst_ips': Counter(),
        'src_ports': Counter(),
        'dst_ports': Counter(),
        'packet_sizes': [],
        'http_requests': [],
        'http_responses': [],
        'dns_queries': [],
        'dns_responses': [],
        'tcp_streams': defaultdict(list),
        'payloads': [],
        'timestamps': []
    }
    
    for pkt in packets:
        # Protocol detection
        if IP in pkt:
            analysis['protocols']['IP'] += 1
            analysis['src_ips'][pkt[IP].src] += 1
            analysis['dst_ips'][pkt[IP].dst] += 1
            analysis['packet_sizes'].append(len(pkt))
            
            # Conversation tracking
            if TCP in pkt:
                analysis['protocols']['TCP'] += 1
                analysis['src_ports'][pkt[TCP].sport] += 1
                analysis['dst_ports'][pkt[TCP].dport] += 1
                
                conv_key = f"{pkt[IP].src}:{pkt[TCP].sport} <-> {pkt[IP].dst}:{pkt[TCP].dport}"
                analysis['conversations'][conv_key]['packets'] += 1
                analysis['conversations'][conv_key]['bytes'] += len(pkt)
                
                # TCP stream tracking
                stream_key = f"{pkt[IP].src}:{pkt[TCP].sport}-{pkt[IP].dst}:{pkt[TCP].dport}"
                analysis['tcp_streams'][stream_key].append(pkt)
                
                # HTTP detection
                if Raw in pkt:
                    payload = pkt[Raw].load
                    try:
                        payload_str = payload.decode('utf-8', errors='ignore')
                        
                        # HTTP Request
                        if payload_str.startswith(('GET ', 'POST ', 'PUT ', 'DELETE ', 'HEAD ', 'OPTIONS ')):
                            lines = payload_str.split('\r\n')
                            analysis['http_requests'].append({
                                'src': f"{pkt[IP].src}:{pkt[TCP].sport}",
                                'dst': f"{pkt[IP].dst}:{pkt[TCP].dport}",
                                'method': lines[0].split()[0] if lines else '',
                                'uri': lines[0].split()[1] if len(lines[0].split()) > 1 else '',
                                'headers': lines[1:10]
                            })
                        
                        # HTTP Response
                        if payload_str.startswith('HTTP/'):
                            lines = payload_str.split('\r\n')
                            status_match = re.search(r'HTTP/\d\.\d\s+(\d{3})', lines[0])
                            analysis['http_responses'].append({
                                'src': f"{pkt[IP].src}:{pkt[TCP].sport}",
                                'dst': f"{pkt[IP].dst}:{pkt[TCP].dport}",
                                'status': status_match.group(1) if status_match else 'Unknown',
                                'headers': lines[1:10]
                            })
                        
                        # Store payload samples
                        if len(analysis['payloads']) < 50 and len(payload_str) > 20:
                            analysis['payloads'].append({
                                'src': f"{pkt[IP].src}",
                                'dst': f"{pkt[IP].dst}",
                                'protocol': 'TCP',
                                'port': pkt[TCP].dport,
                                'data': payload_str[:200]
                            })
                    except:
                        pass
            
            elif UDP in pkt:
                analysis['protocols']['UDP'] += 1
                analysis['src_ports'][pkt[UDP].sport] += 1
                analysis['dst_ports'][pkt[UDP].dport] += 1
                
                conv_key = f"{pkt[IP].src}:{pkt[UDP].sport} <-> {pkt[IP].dst}:{pkt[UDP].dport}"
                analysis['conversations'][conv_key]['packets'] += 1
                analysis['conversations'][conv_key]['bytes'] += len(pkt)
                
                # DNS detection
                if DNS in pkt:
                    analysis['protocols']['DNS'] += 1
                    if pkt[DNS].qr == 0:  # Query
                        analysis['dns_queries'].append({
                            'src': pkt[IP].src,
                            'query': pkt[DNS].qd.qname.decode() if pkt[DNS].qd else 'Unknown'
                        })
                    else:  # Response
                        analysis['dns_responses'].append({
                            'src': pkt[IP].src,
                            'query': pkt[DNS].qd.qname.decode() if pkt[DNS].qd else 'Unknown',
                            'answers': pkt[DNS].an.rdata if pkt[DNS].an else None
                        })
                
                # UDP payload
                if Raw in pkt and len(analysis['payloads']) < 50:
                    try:
                        payload_str = pkt[Raw].load.decode('utf-8', errors='ignore')
                        if len(payload_str) > 20:
                            analysis['payloads'].append({
                                'src': f"{pkt[IP].src}",
                                'dst': f"{pkt[IP].dst}",
                                'protocol': 'UDP',
                                'port': pkt[UDP].dport,
                                'data': payload_str[:200]
                            })
                    except:
                        pass
            
            elif ICMP in pkt:
                analysis['protocols']['ICMP'] += 1
        
        elif ARP in pkt:
            analysis['protocols']['ARP'] += 1
        
        # Timestamp tracking
        if hasattr(pkt, 'time'):
            analysis['timestamps'].append(float(pkt.time))
    
    return analysis

def print_scapy_analysis(analysis):
    """Print Scapy analysis results"""
    if not analysis:
        return
    
    # Protocol Distribution
    print("\n📊 Protocol Distribution:")
    for proto, count in analysis['protocols'].most_common():
        pct = (count / analysis['total_packets']) * 100
        print(f"  {proto:<10} {count:>8,} packets ({pct:5.1f}%)")
    
    # Top Conversations
    print("\n💬 Top 10 Conversations (by packet count):")
    sorted_convs = sorted(analysis['conversations'].items(), key=lambda x: x[1]['packets'], reverse=True)
    for conv, stats in sorted_convs[:10]:
        print(f"  {conv}")
        print(f"    Packets: {stats['packets']:,} | Bytes: {stats['bytes']:,}")
    
    # Top Talkers
    print("\n🔝 Top 10 Source IPs:")
    for ip, count in analysis['src_ips'].most_common(10):
        print(f"  {ip:<20} {count:>8,} packets")
    
    print("\n🎯 Top 10 Destination IPs:")
    for ip, count in analysis['dst_ips'].most_common(10):
        print(f"  {ip:<20} {count:>8,} packets")
    
    # Port Analysis
    print("\n🔌 Top 10 Source Ports:")
    for port, count in analysis['src_ports'].most_common(10):
        print(f"  {port:<10} {count:>8,} packets")
    
    print("\n🔌 Top 10 Destination Ports:")
    for port, count in analysis['dst_ports'].most_common(10):
        print(f"  {port:<10} {count:>8,} packets")
    
    # Packet Size Statistics
    if analysis['packet_sizes']:
        sizes = analysis['packet_sizes']
        print(f"\n📦 Packet Size Statistics:")
        print(f"  Min: {min(sizes)} bytes")
        print(f"  Max: {max(sizes)} bytes")
        print(f"  Avg: {sum(sizes)/len(sizes):.1f} bytes")
        print(f"  Total: {sum(sizes):,} bytes")
    
    # Time-based Analysis
    if len(analysis['timestamps']) > 1:
        duration = analysis['timestamps'][-1] - analysis['timestamps'][0]
        pps = len(analysis['timestamps']) / duration if duration > 0 else 0
        
        # Calculate inter-packet delays
        delays = []
        for i in range(1, len(analysis['timestamps'])):
            delay = (analysis['timestamps'][i] - analysis['timestamps'][i-1]) * 1000  # Convert to ms
            delays.append(delay)
        
        # Find gaps (potential network issues or idle periods)
        large_gaps = [(i, d) for i, d in enumerate(delays) if d > 1000]  # Gaps > 1 second
        
        print(f"\n⏱️  Time Analysis:")
        print(f"  Capture Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        print(f"  First Packet: {datetime.fromtimestamp(analysis['timestamps'][0]).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"  Last Packet: {datetime.fromtimestamp(analysis['timestamps'][-1]).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"  Packets/sec: {pps:.1f}")
        
        if delays:
            print(f"\n  Inter-Packet Delay Statistics:")
            print(f"    Min delay: {min(delays):.3f} ms")
            print(f"    Max delay: {max(delays):.3f} ms")
            print(f"    Avg delay: {sum(delays)/len(delays):.3f} ms")
            print(f"    Median delay: {sorted(delays)[len(delays)//2]:.3f} ms")
        
        if large_gaps:
            print(f"\n  ⚠ Large Time Gaps Detected ({len(large_gaps)} gaps > 1 second):")
            for idx, gap in large_gaps[:10]:
                gap_time = analysis['timestamps'][idx]
                print(f"    Packet {idx}: {gap/1000:.2f}s gap at {datetime.fromtimestamp(gap_time).strftime('%H:%M:%S')}")
        
        # Detect burst patterns (many packets in short time)
        burst_threshold = 100  # packets
        burst_window = 0.1  # 100ms
        bursts = []
        i = 0
        while i < len(analysis['timestamps']) - burst_threshold:
            window_duration = analysis['timestamps'][i + burst_threshold] - analysis['timestamps'][i]
            if window_duration < burst_window:
                bursts.append((i, burst_threshold / window_duration))
                i += burst_threshold
            else:
                i += 1
        
        if bursts:
            print(f"\n  🚀 Traffic Bursts Detected ({len(bursts)} bursts):")
            for pkt_idx, rate in bursts[:5]:
                burst_time = analysis['timestamps'][pkt_idx]
                print(f"    Packet {pkt_idx}: {rate:.0f} packets/sec at {datetime.fromtimestamp(burst_time).strftime('%H:%M:%S')}")
    
    # HTTP Analysis
    if analysis['http_requests']:
        print(f"\n🌐 HTTP Requests ({len(analysis['http_requests'])} total):")
        for req in analysis['http_requests'][:10]:
            print(f"  {req['method']} {req['uri']}")
            print(f"    {req['src']} -> {req['dst']}")
    
    if analysis['http_responses']:
        print(f"\n📨 HTTP Responses ({len(analysis['http_responses'])} total):")
        status_counts = Counter(r['status'] for r in analysis['http_responses'])
        for status, count in status_counts.most_common():
            marker = '✗' if status.startswith('5') else '⚠' if status.startswith('4') else '✓'
            print(f"  {marker} {status}: {count} responses")
        
        # Show detailed error responses
        error_responses = [r for r in analysis['http_responses'] if r['status'].startswith(('4', '5'))]
        if error_responses:
            print(f"\n  Detailed Error Responses (showing first 10 of {len(error_responses)}):")
            for resp in error_responses[:10]:
                print(f"    {resp['status']} - {resp['src']} -> {resp['dst']}")
                for header in resp['headers'][:3]:
                    if header.strip():
                        print(f"      {header[:100]}")
    
    # DNS Analysis
    if analysis['dns_queries']:
        print(f"\n🔍 DNS Queries ({len(analysis['dns_queries'])} total, showing first 10):")
        for query in analysis['dns_queries'][:10]:
            print(f"  {query['src']} -> {query['query']}")
    
    # Payload Samples
    if analysis['payloads']:
        print(f"\n📄 Payload Samples ({len(analysis['payloads'])} captured, showing first 5):")
        for i, payload in enumerate(analysis['payloads'][:5], 1):
            print(f"\n  Sample {i}: {payload['protocol']} {payload['src']} -> {payload['dst']}:{payload['port']}")
            print(f"    {payload['data'][:150]}...")

def export_analysis(analysis, output_file):
    """Export analysis to JSON"""
    if not analysis:
        return
    
    # Save to Desktop output folder
    output_file = OUTPUT_DIR / Path(output_file).name
    
    # Convert to JSON-serializable format
    export_data = {
        'total_packets': analysis['total_packets'],
        'protocols': dict(analysis['protocols']),
        'conversations': {k: v for k, v in analysis['conversations'].items()},
        'top_src_ips': dict(analysis['src_ips'].most_common(20)),
        'top_dst_ips': dict(analysis['dst_ips'].most_common(20)),
        'top_src_ports': dict(analysis['src_ports'].most_common(20)),
        'top_dst_ports': dict(analysis['dst_ports'].most_common(20)),
        'http_requests': analysis['http_requests'],
        'http_responses': analysis['http_responses'],
        'dns_queries': analysis['dns_queries'][:100],
        'packet_size_stats': {
            'min': min(analysis['packet_sizes']) if analysis['packet_sizes'] else 0,
            'max': max(analysis['packet_sizes']) if analysis['packet_sizes'] else 0,
            'avg': sum(analysis['packet_sizes'])/len(analysis['packet_sizes']) if analysis['packet_sizes'] else 0
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n💾 Analysis exported to: {output_file}")

def get_whois_info(ip, cache={}):
    """Get whois information for an IP (with caching)"""
    if not WHOIS_AVAILABLE:
        return None
    
    if ip in cache:
        return cache[ip]
    
    try:
        obj = IPWhois(ip)
        result = obj.lookup_rdap(depth=1)
        info = {
            'country': result.get('asn_country_code', 'Unknown'),
            'org': result.get('asn_description', 'Unknown'),
            'asn': result.get('asn', 'Unknown')
        }
        cache[ip] = info
        return info
    except:
        cache[ip] = None
        return None

def check_tor_exit_nodes():
    """Download Tor exit node list"""
    if not REQUESTS_AVAILABLE:
        return set()
    
    try:
        url = "https://check.torproject.org/torbulkexitlist"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return set(response.text.strip().split('\n'))
    except:
        pass
    return set()

def generate_network_diagram(analysis, output_file):
    """Generate visual network diagram using NetworkX and Matplotlib"""
    if not VISUAL_AVAILABLE or not analysis:
        return
    
    # Save to Desktop output folder
    output_file = OUTPUT_DIR / Path(output_file).name
    
    print(f"\n🎨 Generating network diagram...")
    
    G = nx.DiGraph()
    
    # Add top conversations to graph
    top_convs = sorted(analysis['conversations'].items(), 
                      key=lambda x: x[1]['packets'], reverse=True)[:30]
    
    for conv, stats in top_convs:
        parts = conv.split(' <-> ')
        if len(parts) == 2:
            src = parts[0].split(':')[0]
            dst = parts[1].split(':')[0]
            G.add_edge(src, dst, weight=stats['packets'])
    
    # Create figure
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                          node_size=3000, alpha=0.9)
    
    # Draw edges with varying thickness
    edges = G.edges()
    weights = [G[u][v]['weight'] for u, v in edges]
    max_weight = max(weights) if weights else 1
    widths = [5 * (w / max_weight) for w in weights]
    
    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.5, 
                          edge_color='gray', arrows=True, 
                          arrowsize=20, arrowstyle='->')
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    
    plt.title("Network Topology - Top 30 Conversations", fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Network diagram saved: {output_file}")

def generate_protocol_chart(protocol_stats, total, output_file):
    """Generate protocol hierarchy pie chart"""
    if not VISUAL_AVAILABLE:
        return
    
    # Save to Desktop output folder
    output_file = OUTPUT_DIR / Path(output_file).name
    
    print(f"\n📊 Generating protocol chart...")
    
    # Filter protocols with >0 packets
    data = {k: v for k, v in protocol_stats.items() if v > 0}
    
    if not data:
        return
    
    plt.figure(figsize=(12, 8))
    
    # Create pie chart
    colors = plt.cm.Set3(range(len(data)))
    wedges, texts, autotexts = plt.pie(data.values(), labels=data.keys(), 
                                        autopct='%1.1f%%', colors=colors,
                                        startangle=90, textprops={'fontsize': 10})
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.title(f"Protocol Distribution - {total:,} Total Packets", 
             fontsize=14, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Protocol chart saved: {output_file}")

def generate_interactive_html(analysis, pcap_file, output_file):
    """Generate interactive HTML report with embedded visualizations"""
    if not analysis:
        return
    
    # Save to Desktop output folder
    output_file = OUTPUT_DIR / Path(output_file).name
    
    print(f"\n🌐 Generating interactive HTML map...")
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PCAP Analysis Report - {Path(pcap_file).name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .stat-box h3 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }}
        .stat-box .value {{ font-size: 32px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; font-weight: bold; }}
        tr:hover {{ background: #f5f5f5; }}
        .conversation {{ font-family: monospace; font-size: 12px; background: #ecf0f1; padding: 10px; margin: 5px 0; border-radius: 4px; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .network-node {{ display: inline-block; background: #3498db; color: white; padding: 8px 15px; margin: 5px; border-radius: 20px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 PCAP Analysis Report</h1>
        <p><strong>File:</strong> {Path(pcap_file).name}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <div class="stat-box">
                <h3>Total Packets</h3>
                <div class="value">{analysis['total_packets']:,}</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>Unique IPs</h3>
                <div class="value">{len(analysis['src_ips'])}</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3>Conversations</h3>
                <div class="value">{len(analysis['conversations'])}</div>
            </div>
            <div class="stat-box" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <h3>Protocols</h3>
                <div class="value">{len([p for p in analysis['protocols'] if analysis['protocols'][p] > 0])}</div>
            </div>
        </div>
        
        <h2>🔝 Top Source IPs</h2>
        <table>
            <tr><th>IP Address</th><th>Packets</th><th>Percentage</th></tr>
"""
    
    for ip, count in analysis['src_ips'].most_common(10):
        pct = (count / analysis['total_packets']) * 100
        html_content += f"<tr><td>{ip}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>\n"
    
    html_content += """
        </table>
        
        <h2>💬 Top Conversations</h2>
"""
    
    top_convs = sorted(analysis['conversations'].items(), 
                      key=lambda x: x[1]['packets'], reverse=True)[:15]
    
    for conv, stats in top_convs:
        html_content += f"""
        <div class="conversation">
            {conv}<br>
            <strong>{stats['packets']:,}</strong> packets | <strong>{stats['bytes']:,}</strong> bytes
        </div>
"""
    
    html_content += """
        <h2>📡 Protocol Distribution</h2>
        <table>
            <tr><th>Protocol</th><th>Packets</th><th>Percentage</th></tr>
"""
    
    for proto, count in sorted(analysis['protocols'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / analysis['total_packets']) * 100
            html_content += f"<tr><td>{proto}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>\n"
    
    html_content += """
        </table>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✓ Interactive HTML saved: {output_file}")

def analyze_pcap(pcap_file, export_json=False, enable_whois=False, enable_tor=False, enable_visual=False):
    """Main analysis function"""
    
    print("\n" + "="*100)
    print(f"COMPREHENSIVE PCAP ANALYSIS v3")
    print(f"File: {pcap_file}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    # TCP FLAGS REFERENCE
    print("\n" + "="*100)
    print("TCP FLAGS REFERENCE")
    print("="*100)
    print("""
  S   = SYN     (Synchronize - Start connection)
  A   = ACK     (Acknowledge - Confirm receipt)
  F   = FIN     (Finish - Close connection gracefully)
  R   = RST     (Reset - Abort connection immediately)
  P   = PSH     (Push - Send data immediately)
  U   = URG     (Urgent - Priority data)
  E   = ECE     (ECN Echo - Congestion notification)
  C   = CWR     (Congestion Window Reduced)

Common Flag Combinations:
  S       = SYN (Connection request)
  SA      = SYN+ACK (Connection accepted)
  A       = ACK (Acknowledgment)
  PA      = PSH+ACK (Data transfer)
  FA      = FIN+ACK (Graceful close)
  R       = RST (Connection reset/refused)
  RA      = RST+ACK (Connection reset with ack)
    """)
    
    # TCPDUMP ANALYSIS (Quick Overview)
    print("\n" + "="*100)
    print("BASIC STATISTICS (tcpdump)")
    print("="*100)
    
    all_packets = run_tcpdump(pcap_file)
    tcp_packets = run_tcpdump(pcap_file, 'tcp')
    udp_packets = run_tcpdump(pcap_file, 'udp')
    
    total = len(all_packets)
    tcp_count = len(tcp_packets)
    udp_count = len(udp_packets)
    
    print(f"\nTotal Packets: {total:,}")
    if total > 0:
        print(f"TCP: {tcp_count:,} ({tcp_count/total*100:.1f}%)")
        print(f"UDP: {udp_count:,} ({udp_count/total*100:.1f}%)")
    else:
        print("⚠ No packets found!")
        return
    
    # TCP FLAGS
    print("\n" + "="*100)
    print("TCP FLAGS ANALYSIS")
    print("="*100)
    
    syn_packets = run_tcpdump(pcap_file, 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0')
    synack_packets = run_tcpdump(pcap_file, 'tcp[tcpflags] & (tcp-syn|tcp-ack) == (tcp-syn|tcp-ack)')
    rst_packets = run_tcpdump(pcap_file, 'tcp[tcpflags] & tcp-rst != 0')
    fin_packets = run_tcpdump(pcap_file, 'tcp[tcpflags] & tcp-fin != 0')
    
    syn_count = len(syn_packets)
    synack_count = len(synack_packets)
    rst_count = len(rst_packets)
    fin_count = len(fin_packets)
    
    print(f"\nSYN: {syn_count:,} | SYN+ACK: {synack_count:,} | RST: {rst_count:,} | FIN: {fin_count:,}")
    
    if syn_count > 0:
        success_rate = (synack_count / syn_count) * 100
        print(f"TCP Handshake Success Rate: {success_rate:.1f}%", end=" ")
        if success_rate > 95:
            print("✓ HEALTHY")
        elif success_rate > 80:
            print("⚠ WARNING")
        else:
            print("✗ CRITICAL")
    
    # TCP ISSUES
    print("\n" + "="*100)
    print("TCP ISSUE DETECTION")
    print("="*100)
    
    retrans = [l for l in tcp_packets if 'Retransmission' in l or 'retransmission' in l]
    zero_win = [l for l in tcp_packets if 'win 0' in l]
    dup_ack = [l for l in tcp_packets if 'Dup ACK' in l or 'duplicate ack' in l.lower()]
    out_of_order = [l for l in tcp_packets if 'Out-of-Order' in l or 'out of order' in l.lower()]
    fast_retrans = [l for l in tcp_packets if 'Fast Retransmission' in l]
    spurious_retrans = [l for l in tcp_packets if 'Spurious Retransmission' in l]
    
    # Store for summary
    has_retrans = len(retrans) > 0
    has_dup_ack = len(dup_ack) > 0
    has_out_of_order = len(out_of_order) > 0
    has_zero_win = len(zero_win) > 0
    
    issues = []
    if retrans:
        issues.append(f"⚠ Retransmissions: {len(retrans)}")
    if zero_win:
        issues.append(f"⚠ Zero window: {len(zero_win)}")
    if dup_ack:
        issues.append(f"⚠ Duplicate ACKs: {len(dup_ack)}")
    if out_of_order:
        issues.append(f"⚠ Out-of-order packets: {len(out_of_order)}")
    if fast_retrans:
        issues.append(f"⚠ Fast retransmissions: {len(fast_retrans)}")
    if spurious_retrans:
        issues.append(f"⚠ Spurious retransmissions: {len(spurious_retrans)}")
    if total > 0 and (rst_count / total) * 100 > 5:
        issues.append(f"⚠ High RST rate: {(rst_count/total)*100:.1f}%")
    
    if issues:
        print("\n" + " | ".join(issues))
        
        if retrans:
            print(f"\n{'='*100}")
            print(f"RETRANSMISSIONS - Packet Loss/Network Issues ({len(retrans)} packets)")
            print(f"{'='*100}")
            
            # Extract IPs from retransmissions to identify who's dropping
            retrans_sources = Counter()
            retrans_dests = Counter()
            for pkt in retrans:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                if len(ips) >= 2:
                    retrans_sources[ips[0]] += 1
                    retrans_dests[ips[1]] += 1
            
            print(f"\n  📍 Retransmission Sources (who's resending):")
            for ip, count in retrans_sources.most_common(5):
                print(f"    {ip}: {count} retransmissions")
            
            print(f"\n  📍 Retransmission Destinations (who's not ACKing):")
            for ip, count in retrans_dests.most_common(5):
                print(f"    {ip}: {count} packets not acknowledged")
            
            print(f"\n  Packet samples:")
            for pkt in retrans[:10]:
                print(f"    {pkt}")
        
        if dup_ack:
            print(f"\n{'='*100}")
            print(f"DUPLICATE ACKs - Receiver Signaling Missing Packets ({len(dup_ack)} packets)")
            print(f"{'='*100}")
            
            dup_ack_sources = Counter()
            for pkt in dup_ack:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                if ips:
                    dup_ack_sources[ips[0]] += 1
            
            print(f"\n  📍 Hosts sending duplicate ACKs (missing data):")
            for ip, count in dup_ack_sources.most_common(5):
                print(f"    {ip}: {count} duplicate ACKs")
            
            print(f"\n  Packet samples:")
            for pkt in dup_ack[:10]:
                print(f"    {pkt}")
        
        if out_of_order:
            print(f"\n{'='*100}")
            print(f"OUT-OF-ORDER PACKETS - Network Path Issues ({len(out_of_order)} packets)")
            print(f"{'='*100}")
            print(f"\n  Packet samples:")
            for pkt in out_of_order[:10]:
                print(f"    {pkt}")
        
        if zero_win:
            print(f"\n{'='*100}")
            print(f"ZERO WINDOW - Receiver Buffer Full ({len(zero_win)} packets)")
            print(f"{'='*100}")
            
            # Extract who's announcing zero window
            zero_win_hosts = Counter()
            for pkt in zero_win:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                if len(ips) >= 1:
                    zero_win_hosts[ips[0]] += 1
            
            print(f"\n  📍 Hosts with full buffers (can't receive more data):")
            for ip, count in zero_win_hosts.most_common(5):
                print(f"    {ip}: {count} zero window announcements")
            
            print(f"\n  Packet samples:")
            for pkt in zero_win[:10]:
                print(f"    {pkt}")
        
        if rst_count > 0:
            print(f"\n{'='*100}")
            print(f"RST PACKETS - Connection Resets ({rst_count} packets)")
            print(f"{'='*100}")
            
            # Extract who's sending RSTs
            rst_sources = Counter()
            rst_dests = Counter()
            for pkt in rst_packets:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                if len(ips) >= 2:
                    rst_sources[ips[0]] += 1
                    rst_dests[ips[1]] += 1
            
            print(f"\n  📍 RST Sources (who's rejecting connections):")
            for ip, count in rst_sources.most_common(5):
                print(f"    {ip}: {count} RST packets sent")
            
            print(f"\n  📍 RST Destinations (who's getting rejected):")
            for ip, count in rst_dests.most_common(5):
                print(f"    {ip}: {count} connections rejected")
            
            print(f"\n  Packet samples:")
            for pkt in rst_packets[:10]:
                print(f"    {pkt}")
    else:
        print("\n✓ No TCP issues detected")
    
    # SCAPY DEEP ANALYSIS
    scapy_analysis = None
    if SCAPY_AVAILABLE:
        scapy_analysis = analyze_with_scapy(pcap_file)
        if scapy_analysis:
            print_scapy_analysis(scapy_analysis)
            
            if export_json:
                output_file = Path(pcap_file).stem + '_analysis.json'
                export_analysis(scapy_analysis, output_file)
    
    # WHOIS LOOKUP
    if enable_whois and WHOIS_AVAILABLE and scapy_analysis:
        print("\n" + "="*100)
        print("🌍 WHOIS / GEOLOCATION ANALYSIS")
        print("="*100)
        
        print(f"\n  Looking up top 10 IPs (this may take a moment)...")
        top_ips = list(scapy_analysis['src_ips'].most_common(10)) + list(scapy_analysis['dst_ips'].most_common(10))
        unique_ips = list(dict.fromkeys([ip for ip, _ in top_ips]))[:10]
        
        whois_results = {}
        for ip in unique_ips:
            # Skip private IPs
            if ip.startswith(('10.', '192.168.', '172.', '127.')):
                continue
            
            info = get_whois_info(ip)
            if info:
                whois_results[ip] = info
        
        if whois_results:
            print(f"\n  📍 IP Geolocation Results:")
            print(f"  {'IP Address':<20} {'Country':<10} {'Organization':<40} {'ASN'}")
            print(f"  {'-'*90}")
            for ip, info in whois_results.items():
                print(f"  {ip:<20} {info['country']:<10} {info['org'][:38]:<40} {info['asn']}")
        else:
            print(f"\n  ℹ️  No external IPs found for whois lookup")
    elif enable_whois and not WHOIS_AVAILABLE:
        print(f"\n⚠ Whois requested but ipwhois not installed. Run: pip3 install ipwhois")
    
    # TOR DETECTION
    if enable_tor and REQUESTS_AVAILABLE and scapy_analysis:
        print("\n" + "="*100)
        print("🧅 TOR EXIT NODE DETECTION")
        print("="*100)
        
        print(f"\n  Downloading Tor exit node list...")
        tor_nodes = check_tor_exit_nodes()
        
        if tor_nodes:
            print(f"  ✓ Loaded {len(tor_nodes)} Tor exit nodes")
            
            # Check if any IPs in capture are Tor nodes
            all_ips = set(scapy_analysis['src_ips'].keys()) | set(scapy_analysis['dst_ips'].keys())
            tor_ips_found = all_ips & tor_nodes
            
            if tor_ips_found:
                print(f"\n  🔴 TOR EXIT NODES DETECTED: {len(tor_ips_found)} IPs")
                for ip in list(tor_ips_found)[:10]:
                    src_count = scapy_analysis['src_ips'].get(ip, 0)
                    dst_count = scapy_analysis['dst_ips'].get(ip, 0)
                    print(f"    {ip}: {src_count} sent, {dst_count} received")
            else:
                print(f"\n  ✓ No Tor exit nodes detected in traffic")
        else:
            print(f"  ⚠ Could not download Tor exit node list")
    elif enable_tor and not REQUESTS_AVAILABLE:
        print(f"\n⚠ Tor detection requested but requests not installed. Run: pip3 install requests")
    
    # DNS ANALYSIS (tcpdump)
    print("\n" + "="*100)
    print("DNS ANALYSIS (Quick Overview)")
    print("="*100)
    
    dns_packets = run_tcpdump(pcap_file, 'udp port 53 or tcp port 53')
    dns_queries = run_tcpdump(pcap_file, 'udp port 53 or tcp port 53', 100)  # Sample first 100
    dns_servers = Counter()
    
    if dns_packets:
        print(f"\nDNS Traffic: {len(dns_packets)} packets")
        
        # Extract domain patterns
        domains = []
        for pkt in dns_queries:
            # Extract DNS server IPs
            ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)\.53', pkt)
            for ip in ips:
                dns_servers[ip] += 1
            
            # Try to extract domain names (basic pattern)
            # This is limited with tcpdump, Scapy does better
            if '?' in pkt:
                parts = pkt.split('?')
                if len(parts) > 1:
                    domain_part = parts[1].split()[0] if parts[1].split() else ''
                    if domain_part and '.' in domain_part:
                        domains.append(domain_part)
        
        if dns_servers:
            print(f"\n  📍 DNS Servers:")
            for server, count in dns_servers.most_common(5):
                print(f"    {server}: {count} queries")
        
        if domains:
            domain_counts = Counter(domains)
            print(f"\n  🔍 Top Queried Domains (sample from first 100 packets):")
            for domain, count in domain_counts.most_common(10):
                print(f"    {domain}: {count} queries")
        
        print(f"\n  Sample DNS packets:")
        for pkt in dns_queries[:5]:
            print(f"    {pkt}")
    else:
        print("\n✓ No DNS traffic detected")
    
    # TLS/SSL ANALYSIS
    print("\n" + "="*100)
    print("TLS/SSL ANALYSIS")
    print("="*100)
    
    https_packets = run_tcpdump(pcap_file, 'tcp port 443 or tcp port 8443')
    https_servers = Counter()
    https_clients = Counter()
    
    if https_packets:
        print(f"\nTLS/SSL Traffic: {len(https_packets)} packets on ports 443/8443")
        
        # Look for TLS handshake patterns (ClientHello, ServerHello)
        # This is basic - Scapy can decode TLS better
        tls_handshakes = [p for p in https_packets if 'Flags [S]' in p or 'Flags [S.]' in p]
        
        # Extract HTTPS endpoints
        for pkt in https_packets[:100]:
            ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
            if len(ips) >= 2:
                # Assume server is on port 443/8443
                if '.443' in pkt or '.8443' in pkt:
                    if ips[1] + '.443' in pkt or ips[1] + '.8443' in pkt:
                        https_servers[ips[1]] += 1
                        https_clients[ips[0]] += 1
                    else:
                        https_servers[ips[0]] += 1
                        https_clients[ips[1]] += 1
        
        if tls_handshakes:
            print(f"  TLS Handshakes: {len(tls_handshakes)} connection attempts")
        
        if https_servers:
            print(f"\n  📍 Top HTTPS Servers:")
            for server, count in https_servers.most_common(5):
                print(f"    {server}: {count} packets")
        
        if https_clients:
            print(f"\n  📍 Top HTTPS Clients:")
            for client, count in https_clients.most_common(5):
                print(f"    {client}: {count} packets")
    else:
        print("\n✓ No TLS/SSL traffic detected")
    
    # ARP ANALYSIS
    print("\n" + "="*100)
    print("ARP ANALYSIS (Address Resolution)")
    print("="*100)
    
    arp_packets = run_tcpdump(pcap_file, 'arp')
    arp_requests = []
    arp_replies = []
    
    if arp_packets:
        print(f"\nARP Traffic: {len(arp_packets)} packets")
        
        arp_requests = [p for p in arp_packets if 'Request who-has' in p]
        arp_replies = [p for p in arp_packets if 'Reply' in p]
        
        print(f"  ARP Requests: {len(arp_requests)}")
        print(f"  ARP Replies: {len(arp_replies)}")
        
        # Extract IPs being resolved
        requested_ips = Counter()
        for pkt in arp_requests:
            match = re.search(r'who-has (\d+\.\d+\.\d+\.\d+)', pkt)
            if match:
                requested_ips[match.group(1)] += 1
        
        if requested_ips:
            print(f"\n  📍 Most Requested IPs (ARP lookups):")
            for ip, count in requested_ips.most_common(10):
                print(f"    {ip}: {count} requests")
        
        # Detect potential ARP spoofing (multiple MACs for same IP)
        if len(arp_replies) > 0:
            print(f"\n  Sample ARP replies:")
            for pkt in arp_replies[:5]:
                print(f"    {pkt}")
    else:
        print("\n✓ No ARP traffic detected")
    
    # BANDWIDTH ANALYSIS
    print("\n" + "="*100)
    print("BANDWIDTH ANALYSIS")
    print("="*100)
    
    # Get packet sizes from all packets
    bandwidth_by_ip = defaultdict(int)
    packet_sizes = []
    
    for pkt in all_packets[:1000]:  # Sample first 1000 for performance
        # Extract length from tcpdump output
        length_match = re.search(r'length (\d+)', pkt)
        if length_match:
            size = int(length_match.group(1))
            packet_sizes.append(size)
            
            # Extract IPs
            ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
            for ip in ips:
                bandwidth_by_ip[ip] += size
    
    if packet_sizes:
        total_bytes = sum(packet_sizes)
        print(f"\n  Total Data (sample): {total_bytes:,} bytes ({total_bytes/1024:.1f} KB, {total_bytes/1024/1024:.2f} MB)")
        print(f"  Average Packet Size: {sum(packet_sizes)/len(packet_sizes):.1f} bytes")
        print(f"  Smallest Packet: {min(packet_sizes)} bytes")
        print(f"  Largest Packet: {max(packet_sizes)} bytes")
        
        # Packet size distribution
        small_pkts = len([s for s in packet_sizes if s < 100])
        medium_pkts = len([s for s in packet_sizes if 100 <= s < 1000])
        large_pkts = len([s for s in packet_sizes if s >= 1000])
        
        print(f"\n  📊 Packet Size Distribution:")
        print(f"    Small (<100 bytes): {small_pkts} packets ({small_pkts/len(packet_sizes)*100:.1f}%)")
        print(f"    Medium (100-999 bytes): {medium_pkts} packets ({medium_pkts/len(packet_sizes)*100:.1f}%)")
        print(f"    Large (≥1000 bytes): {large_pkts} packets ({large_pkts/len(packet_sizes)*100:.1f}%)")
    
    if bandwidth_by_ip:
        print(f"\n  📍 Top 10 Bandwidth Consumers (by IP):")
        sorted_bw = sorted(bandwidth_by_ip.items(), key=lambda x: x[1], reverse=True)
        for ip, bytes_used in sorted_bw[:10]:
            print(f"    {ip}: {bytes_used:,} bytes ({bytes_used/1024:.1f} KB)")
    
    # PROTOCOL HIERARCHY
    print("\n" + "="*100)
    print("PROTOCOL HIERARCHY")
    print("="*100)
    
    protocol_stats = {
        'TCP': tcp_count,
        'UDP': udp_count,
        'ICMP': len(run_tcpdump(pcap_file, 'icmp')),
        'ARP': len(arp_packets) if arp_packets else 0,
        'DNS': len(dns_packets) if dns_packets else 0,
        'HTTP': len(run_tcpdump(pcap_file, 'tcp port 80 or tcp port 8080')),
        'HTTPS': len(https_packets) if https_packets else 0,
    }
    
    print(f"\n  📊 Protocol Breakdown:")
    print(f"  {'Protocol':<15} {'Packets':<12} {'Percentage':<12} {'Visual'}")
    print(f"  {'-'*70}")
    
    for proto, count in sorted(protocol_stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / total) * 100 if total > 0 else 0
            bar_length = int(pct / 2)  # Scale to 50 chars max
            bar = '█' * bar_length
            print(f"  {proto:<15} {count:>8,} pkts  {pct:>5.1f}%       {bar}")
    
    # Application layer breakdown
    if SCAPY_AVAILABLE and scapy_analysis:
        print(f"\n  🌐 Application Layer Protocols:")
        app_protocols = {}
        
        if scapy_analysis.get('http_requests'):
            app_protocols['HTTP Requests'] = len(scapy_analysis['http_requests'])
        if scapy_analysis.get('http_responses'):
            app_protocols['HTTP Responses'] = len(scapy_analysis['http_responses'])
        if scapy_analysis.get('dns_queries'):
            app_protocols['DNS Queries'] = len(scapy_analysis['dns_queries'])
        if scapy_analysis.get('dns_responses'):
            app_protocols['DNS Responses'] = len(scapy_analysis['dns_responses'])
        
        if app_protocols:
            for proto, count in sorted(app_protocols.items(), key=lambda x: x[1], reverse=True):
                print(f"    {proto:<20} {count:>6,} messages")
    
    # Port distribution
    if SCAPY_AVAILABLE and scapy_analysis and scapy_analysis.get('dst_ports'):
        print(f"\n  🔌 Top 10 Destination Ports:")
        print(f"  {'Port':<10} {'Service':<15} {'Packets':<12} {'Visual'}")
        print(f"  {'-'*60}")
        
        port_names = {
            20: 'FTP-Data', 21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP',
            53: 'DNS', 67: 'DHCP', 68: 'DHCP', 80: 'HTTP', 110: 'POP3',
            123: 'NTP', 143: 'IMAP', 161: 'SNMP', 443: 'HTTPS', 445: 'SMB',
            3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL', 6081: 'Geneve',
            8080: 'HTTP-Alt', 8443: 'HTTPS-Alt', 9090: 'HTTP-Proxy'
        }
        
        for port, count in scapy_analysis['dst_ports'].most_common(10):
            service = port_names.get(port, 'Unknown')
            pct = (count / total) * 100 if total > 0 else 0
            bar_length = int(pct / 2)
            bar = '█' * bar_length if bar_length > 0 else ''
            print(f"  {port:<10} {service:<15} {count:>6,} pkts  {bar}")
    
    # NETWORK VISUALIZATION
    print("\n" + "="*100)
    print("🗺️  NETWORK TOPOLOGY VISUALIZATION")
    print("="*100)
    
    if SCAPY_AVAILABLE and scapy_analysis:
        # Build network map
        print(f"\n  Network Map (Top Communications):")
        print(f"  {'-'*90}")
        
        # Get top conversations
        top_convs = sorted(scapy_analysis['conversations'].items(), 
                          key=lambda x: x[1]['packets'], reverse=True)[:15]
        
        for conv, stats in top_convs:
            parts = conv.split(' <-> ')
            if len(parts) == 2:
                src = parts[0]
                dst = parts[1]
                packets = stats['packets']
                bytes_val = stats['bytes']
                
                # Visual representation
                if packets > 100:
                    arrow = '═══════>'
                elif packets > 50:
                    arrow = '══════>'
                elif packets > 10:
                    arrow = '═════>'
                else:
                    arrow = '────>'
                
                print(f"  {src:<30} {arrow} {dst:<30}")
                print(f"  {'':30} {packets:>6,} pkts | {bytes_val:>10,} bytes")
                print()
        
        # Network summary
        print(f"\n  📊 Network Summary:")
        unique_src = len(scapy_analysis['src_ips'])
        unique_dst = len(scapy_analysis['dst_ips'])
        total_convs = len(scapy_analysis['conversations'])
        
        print(f"    Unique Source IPs: {unique_src}")
        print(f"    Unique Destination IPs: {unique_dst}")
        print(f"    Total Conversations: {total_convs}")
        print(f"    Average Packets/Conversation: {total/total_convs:.1f}" if total_convs > 0 else "")
        
        # Communication matrix
        print(f"\n  🔀 Communication Patterns:")
        
        # Internal vs External
        internal_ips = set()
        external_ips = set()
        
        for ip in list(scapy_analysis['src_ips'].keys()) + list(scapy_analysis['dst_ips'].keys()):
            if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                internal_ips.add(ip)
            elif ip != '127.0.0.1':
                external_ips.add(ip)
        
        print(f"    Internal IPs: {len(internal_ips)}")
        print(f"    External IPs: {len(external_ips)}")
        
        if len(internal_ips) > 0 and len(external_ips) > 0:
            print(f"    Network Type: Mixed (Internal + External)")
        elif len(internal_ips) > 0:
            print(f"    Network Type: Internal Only")
        else:
            print(f"    Network Type: External Only")
        
        # Export network graph option
        print(f"\n  💡 Tip: For visual network diagram, use:")
        print(f"     python3 pcap_analyzer_v3.py <file.pcap> --export-json")
        print(f"     Then use tools like Gephi, Cytoscape, or D3.js to visualize the JSON")
    else:
        print(f"\n  ⚠ Install Scapy for detailed network visualization")
        print(f"    pip3 install scapy")
    
    # GENEVE PROTOCOL ANALYSIS
    print("\n" + "="*100)
    print("GENEVE PROTOCOL ANALYSIS")
    print("="*100)
    
    geneve_packets = run_tcpdump(pcap_file, 'udp port 6081')
    
    if geneve_packets:
        print(f"\n✓ Geneve encapsulation detected: {len(geneve_packets)} packets")
        
        # Extract Geneve endpoints
        geneve_sources = Counter()
        geneve_dests = Counter()
        for pkt in geneve_packets:
            ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
            if len(ips) >= 2:
                geneve_sources[ips[0]] += 1
                geneve_dests[ips[1]] += 1
        
        print(f"\n  📍 Geneve Tunnel Sources:")
        for ip, count in geneve_sources.most_common(5):
            print(f"    {ip}: {count} packets")
        
        print(f"\n  📍 Geneve Tunnel Destinations:")
        for ip, count in geneve_dests.most_common(5):
            print(f"    {ip}: {count} packets")
        
        print(f"\n  Packet samples (first 10):")
        for pkt in geneve_packets[:10]:
            print(f"    {pkt}")
    else:
        print("\n✓ No Geneve encapsulation detected")
    
    # UDP ERRORS (ICMP)
    print("\n" + "="*100)
    print("UDP ERROR DETECTION")
    print("="*100)
    
    icmp_unreach = run_tcpdump(pcap_file, 'icmp and icmp[icmptype] == icmp-unreach')
    icmp_time_exceeded = run_tcpdump(pcap_file, 'icmp and icmp[icmptype] == icmp-timxceed')
    port_unreach = []
    host_unreach = []
    net_unreach = []
    proto_unreach = []
    frag_needed = []
    
    if icmp_unreach or icmp_time_exceeded:
        if icmp_unreach:
            print(f"\n⚠ ICMP Unreachable messages: {len(icmp_unreach)} packets")
        if icmp_time_exceeded:
            print(f"\n⚠ ICMP Time Exceeded (TTL=0): {len(icmp_time_exceeded)} packets")
        
        port_unreach = [l for l in icmp_unreach if 'port unreachable' in l.lower()]
        host_unreach = [l for l in icmp_unreach if 'host unreachable' in l.lower()]
        net_unreach = [l for l in icmp_unreach if 'net unreachable' in l.lower()]
        proto_unreach = [l for l in icmp_unreach if 'protocol unreachable' in l.lower()]
        frag_needed = [l for l in icmp_unreach if 'frag needed' in l.lower() or 'unreachable - need to frag' in l.lower()]
        
        if port_unreach:
            print(f"\n{'='*100}")
            print(f"PORT UNREACHABLE - Service Not Listening ({len(port_unreach)} packets)")
            print(f"{'='*100}")
            
            # Extract who's rejecting and which ports
            rejecting_hosts = Counter()
            unreachable_ports = Counter()
            for pkt in port_unreach:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                ports = re.findall(r'udp port (\d+)', pkt)
                if ips:
                    rejecting_hosts[ips[0]] += 1
                if ports:
                    unreachable_ports[ports[0]] += 1
            
            print(f"\n  📍 Hosts rejecting UDP traffic:")
            for ip, count in rejecting_hosts.most_common(5):
                print(f"    {ip}: {count} port unreachable responses")
            
            if unreachable_ports:
                print(f"\n  📍 Unreachable ports:")
                for port, count in unreachable_ports.most_common(5):
                    port_name = {
                        '53': 'DNS', '67': 'DHCP', '68': 'DHCP', '123': 'NTP',
                        '161': 'SNMP', '162': 'SNMP Trap', '514': 'Syslog', '6081': 'Geneve'
                    }.get(port, 'Unknown')
                    print(f"    Port {port} ({port_name}): {count} rejections")
            
            print(f"\n  Packet samples:")
            for pkt in port_unreach[:10]:
                print(f"    {pkt}")
        
        if host_unreach:
            print(f"\n{'='*100}")
            print(f"HOST UNREACHABLE - Destination Not Reachable ({len(host_unreach)} packets)")
            print(f"{'='*100}")
            
            # Extract unreachable hosts
            unreachable_hosts = Counter()
            for pkt in host_unreach:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                if len(ips) >= 2:
                    unreachable_hosts[ips[1]] += 1
            
            print(f"\n  📍 Unreachable destination hosts:")
            for ip, count in unreachable_hosts.most_common(5):
                print(f"    {ip}: {count} host unreachable messages")
            
            print(f"\n  Packet samples:")
            for pkt in host_unreach[:10]:
                print(f"    {pkt}")
        
        if net_unreach:
            print(f"\n{'='*100}")
            print(f"NETWORK UNREACHABLE - Routing Issues ({len(net_unreach)} packets)")
            print(f"{'='*100}")
            
            # Extract unreachable networks
            unreachable_nets = Counter()
            for pkt in net_unreach:
                ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', pkt)
                if len(ips) >= 2:
                    unreachable_nets[ips[1]] += 1
            
            print(f"\n  📍 Unreachable destination networks:")
            for ip, count in unreachable_nets.most_common(5):
                print(f"    {ip}: {count} network unreachable messages")
            
            print(f"\n  Packet samples:")
            for pkt in net_unreach[:10]:
                print(f"    {pkt}")
        
        if proto_unreach:
            print(f"\n{'='*100}")
            print(f"PROTOCOL UNREACHABLE - Protocol Not Supported ({len(proto_unreach)} packets)")
            print(f"{'='*100}")
            for pkt in proto_unreach[:10]:
                print(f"    {pkt}")
        
        if frag_needed:
            print(f"\n{'='*100}")
            print(f"FRAGMENTATION NEEDED - MTU Issues ({len(frag_needed)} packets)")
            print(f"{'='*100}")
            print(f"  ⚠ Path MTU Discovery issue - packets too large for network path")
            for pkt in frag_needed[:10]:
                print(f"    {pkt}")
        
        if icmp_time_exceeded:
            print(f"\n{'='*100}")
            print(f"ICMP TIME EXCEEDED - TTL Expired ({len(icmp_time_exceeded)} packets)")
            print(f"{'='*100}")
            print(f"  ⚠ Routing loop or TTL too small")
            for pkt in icmp_time_exceeded[:10]:
                print(f"    {pkt}")
    else:
        print("\n✓ No UDP/ICMP errors detected")
    
    # FIREWALL/SECURITY ANALYSIS
    print("\n" + "="*100)
    print("FIREWALL & SECURITY ANALYSIS")
    print("="*100)
    
    # ICMP admin prohibited
    icmp_admin_prohibited = run_tcpdump(pcap_file, 'icmp and icmp[icmptype] == icmp-unreach and icmp[icmpcode] == 13')
    
    # TCP connection refused patterns
    connection_refused = [l for l in rst_packets if any(port in l for port in [':22 ', ':23 ', ':3389 ', ':445 '])]
    
    # Blocked ports analysis
    blocked_ports = Counter()
    if port_unreach:
        for pkt in port_unreach:
            ports = re.findall(r'port (\d+)', pkt)
            for port in ports:
                blocked_ports[port] += 1
    
    firewall_indicators = []
    
    if icmp_admin_prohibited:
        firewall_indicators.append(f"⚠ ICMP Admin Prohibited: {len(icmp_admin_prohibited)} packets (firewall blocking)")
        print(f"\n  📍 ICMP Admin Prohibited (firewall explicitly blocking):")
        for pkt in icmp_admin_prohibited[:10]:
            print(f"    {pkt}")
    
    if connection_refused:
        firewall_indicators.append(f"⚠ Connection Refused: {len(connection_refused)} packets (service/firewall blocking)")
        print(f"\n  📍 Connection Refused on common ports:")
        for pkt in connection_refused[:10]:
            print(f"    {pkt}")
    
    if blocked_ports:
        firewall_indicators.append(f"⚠ Blocked Ports: {len(blocked_ports)} unique ports")
        print(f"\n  📍 Most blocked ports:")
        for port, count in blocked_ports.most_common(10):
            port_name = {
                '22': 'SSH', '23': 'Telnet', '80': 'HTTP', '443': 'HTTPS',
                '3389': 'RDP', '445': 'SMB', '3306': 'MySQL', '5432': 'PostgreSQL'
            }.get(port, 'Unknown')
            print(f"    Port {port} ({port_name}): {count} blocks")
    
    # Check for port scanning behavior
    if SCAPY_AVAILABLE and scapy_analysis:
        # Detect if single source is hitting many ports on same dest
        for conv, stats in scapy_analysis['conversations'].items():
            if stats['packets'] < 5:  # Few packets per port = scanning
                parts = conv.split(' <-> ')
                if len(parts) == 2:
                    src_ip = parts[0].split(':')[0]
                    # Count unique dest ports from this source
                    dest_ports_from_src = [c.split(':')[-1] for c in scapy_analysis['conversations'].keys() 
                                          if c.startswith(src_ip)]
                    if len(set(dest_ports_from_src)) > 20:
                        firewall_indicators.append(f"⚠ Possible port scan from {src_ip} ({len(set(dest_ports_from_src))} ports)")
                        break
    
    if firewall_indicators:
        print(f"\n  🔥 Firewall/Security Indicators:")
        for indicator in firewall_indicators:
            print(f"    {indicator}")
    else:
        print("\n✓ No obvious firewall blocks detected")
    
    # DDOS DETECTION
    print("\n" + "="*100)
    print("🚨 DDoS / ATTACK DETECTION")
    print("="*100)
    
    ddos_indicators = []
    ddos_score = 0
    
    # 1. SYN Flood Detection
    syn_flood_threshold = 100  # SYN packets per second
    if SCAPY_AVAILABLE and scapy_analysis and len(scapy_analysis.get('timestamps', [])) > 1:
        duration = scapy_analysis['timestamps'][-1] - scapy_analysis['timestamps'][0]
        syn_rate = syn_count / duration if duration > 0 else 0
        
        if syn_rate > syn_flood_threshold:
            ddos_indicators.append(f"🔴 SYN FLOOD: {syn_rate:.1f} SYN packets/sec (threshold: {syn_flood_threshold})")
            ddos_score += 3
        elif syn_rate > syn_flood_threshold / 2:
            ddos_indicators.append(f"⚠ Elevated SYN rate: {syn_rate:.1f} SYN packets/sec")
            ddos_score += 1
    
    # 2. High RST Rate (connection exhaustion)
    rst_rate = (rst_count / total) * 100 if total > 0 else 0
    if rst_rate > 20:
        ddos_indicators.append(f"🔴 VERY HIGH RST RATE: {rst_rate:.1f}% - possible connection exhaustion attack")
        ddos_score += 3
    elif rst_rate > 10:
        ddos_indicators.append(f"⚠ High RST rate: {rst_rate:.1f}% - possible attack or misconfiguration")
        ddos_score += 2
    
    # 3. Single Source Flooding
    if SCAPY_AVAILABLE and scapy_analysis and scapy_analysis.get('src_ips'):
        top_src = scapy_analysis['src_ips'].most_common(1)[0]
        src_percentage = (top_src[1] / total) * 100 if total > 0 else 0
        
        if src_percentage > 50:
            ddos_indicators.append(f"🔴 SINGLE SOURCE FLOOD: {top_src[0]} sending {src_percentage:.1f}% of all traffic")
            ddos_score += 3
        elif src_percentage > 30:
            ddos_indicators.append(f"⚠ Dominant source: {top_src[0]} sending {src_percentage:.1f}% of traffic")
            ddos_score += 1
    
    # 4. UDP Flood Detection
    udp_rate = (udp_count / total) * 100 if total > 0 else 0
    if udp_count > 1000 and udp_rate > 50:
        ddos_indicators.append(f"🔴 UDP FLOOD: {udp_count:,} UDP packets ({udp_rate:.1f}% of traffic)")
        ddos_score += 3
    
    # 5. ICMP Flood
    icmp_packets = run_tcpdump(pcap_file, 'icmp')
    icmp_count = len(icmp_packets)
    if icmp_count > 1000:
        ddos_indicators.append(f"🔴 ICMP FLOOD: {icmp_count:,} ICMP packets")
        ddos_score += 2
    
    # 6. Port Scan Detection
    if SCAPY_AVAILABLE and scapy_analysis:
        # Check for many connections to different ports from same source
        src_port_map = defaultdict(set)
        for conv in scapy_analysis['conversations'].keys():
            parts = conv.split(' <-> ')
            if len(parts) == 2:
                src = parts[0].split(':')[0]
                dst_port = parts[1].split(':')[1]
                src_port_map[src].add(dst_port)
        
        for src, ports in src_port_map.items():
            if len(ports) > 50:
                ddos_indicators.append(f"🔴 PORT SCAN: {src} scanned {len(ports)} different ports")
                ddos_score += 2
                break
    
    # 7. Packet Rate Analysis
    if SCAPY_AVAILABLE and scapy_analysis and len(scapy_analysis.get('timestamps', [])) > 1:
        duration = scapy_analysis['timestamps'][-1] - scapy_analysis['timestamps'][0]
        pps = total / duration if duration > 0 else 0
        
        if pps > 10000:
            ddos_indicators.append(f"🔴 EXTREME PACKET RATE: {pps:.0f} packets/sec")
            ddos_score += 3
        elif pps > 5000:
            ddos_indicators.append(f"⚠ High packet rate: {pps:.0f} packets/sec")
            ddos_score += 1
    
    # 8. Half-Open Connections (SYN without SYN-ACK)
    half_open = syn_count - synack_count
    if half_open > 100:
        ddos_indicators.append(f"🔴 HALF-OPEN CONNECTIONS: {half_open} SYN without SYN-ACK (SYN flood)")
        ddos_score += 3
    
    # 9. Retransmission Storm
    if has_retrans and len(retrans) > total * 0.1:
        ddos_indicators.append(f"🔴 RETRANSMISSION STORM: {len(retrans)/total*100:.1f}% retransmissions")
        ddos_score += 2
    
    # Display Results
    if ddos_indicators:
        print(f"\n  ⚠️  DDoS Indicators Detected:")
        for indicator in ddos_indicators:
            print(f"    {indicator}")
        
        print(f"\n  📊 DDoS Threat Level:")
        if ddos_score >= 8:
            print(f"    🔴 CRITICAL (Score: {ddos_score}/10+) - Active DDoS attack likely")
        elif ddos_score >= 5:
            print(f"    🟠 HIGH (Score: {ddos_score}/10) - Possible DDoS or network abuse")
        elif ddos_score >= 3:
            print(f"    🟡 MEDIUM (Score: {ddos_score}/10) - Suspicious activity detected")
        else:
            print(f"    🟢 LOW (Score: {ddos_score}/10) - Minor anomalies")
        
        print(f"\n  💡 Recommended Actions:")
        if ddos_score >= 8:
            print(f"    • IMMEDIATE: Enable DDoS mitigation (rate limiting, traffic filtering)")
            print(f"    • Block attacking source IPs at firewall/upstream")
            print(f"    • Contact ISP/DDoS protection service")
        elif ddos_score >= 5:
            print(f"    • Investigate source IPs and traffic patterns")
            print(f"    • Enable connection rate limiting")
            print(f"    • Monitor for escalation")
        else:
            print(f"    • Continue monitoring")
            print(f"    • Review logs for patterns")
    else:
        print("\n  ✓ No DDoS indicators detected - Traffic appears normal")
    
    # SUMMARY
    print("\n" + "="*100)
    print("EXECUTIVE SUMMARY")
    print("="*100)
    print(f"\n✓ Analysis complete - {total:,} packets processed")
    print(f"✓ TCP: {tcp_count:,} | UDP: {udp_count:,}")
    if syn_count > 0:
        print(f"✓ TCP Success Rate: {(synack_count/syn_count)*100:.1f}%")
    
    # Quick health indicators
    health_issues = []
    if retrans and len(retrans) > total * 0.01:  # >1% retransmissions
        health_issues.append(f"⚠ High retransmission rate: {len(retrans)/total*100:.2f}%")
    if rst_count > total * 0.05:  # >5% RST
        health_issues.append(f"⚠ High RST rate: {rst_count/total*100:.1f}%")
    if zero_win:
        health_issues.append(f"⚠ Buffer issues detected ({len(zero_win)} zero window)")
    if icmp_unreach and len(icmp_unreach) > 10:
        health_issues.append(f"⚠ Connectivity issues ({len(icmp_unreach)} ICMP unreachable)")
    
    if health_issues:
        print(f"\n🔴 Network Health Issues:")
        for issue in health_issues:
            print(f"  {issue}")
    else:
        print(f"\n🟢 Network Health: GOOD - No major issues detected")
    
    # COMPREHENSIVE SUMMARY
    print("\n" + "="*100)
    print("📋 COMPREHENSIVE ANALYSIS SUMMARY")
    print("="*100)
    
    print(f"\n{'='*100}")
    print("📊 TRAFFIC OVERVIEW")
    print(f"{'='*100}")
    print(f"  Total Packets Analyzed: {total:,}")
    print(f"  TCP Packets: {tcp_count:,} ({tcp_count/total*100:.1f}%)")
    print(f"  UDP Packets: {udp_count:,} ({udp_count/total*100:.1f}%)")
    if dns_packets:
        print(f"  DNS Queries: {len(dns_packets):,}")
    if https_packets:
        print(f"  HTTPS Traffic: {len(https_packets):,} packets")
    if arp_packets:
        print(f"  ARP Traffic: {len(arp_packets):,} packets")
    
    print(f"\n{'='*100}")
    print("🔌 TCP CONNECTION HEALTH")
    print(f"{'='*100}")
    if syn_count > 0:
        success_rate = (synack_count/syn_count)*100
        status = "✓ EXCELLENT" if success_rate > 95 else "⚠ DEGRADED" if success_rate > 80 else "✗ POOR"
        print(f"  Connection Attempts (SYN): {syn_count:,}")
        print(f"  Successful Connections (SYN+ACK): {synack_count:,}")
        print(f"  Success Rate: {success_rate:.1f}% {status}")
    print(f"  Connection Resets (RST): {rst_count:,}")
    print(f"  Graceful Closes (FIN): {fin_count:,}")
    
    print(f"\n{'='*100}")
    print("⚠️  ERROR SUMMARY")
    print(f"{'='*100}")
    
    error_summary = []
    if has_retrans:
        error_summary.append(f"  • Retransmissions: {len(retrans):,} packets (packet loss/network congestion)")
    if has_dup_ack:
        error_summary.append(f"  • Duplicate ACKs: {len(dup_ack):,} packets (missing data)")
    if has_out_of_order:
        error_summary.append(f"  • Out-of-Order: {len(out_of_order):,} packets (routing issues)")
    if has_zero_win:
        error_summary.append(f"  • Zero Window: {len(zero_win):,} packets (receiver buffer full)")
    if rst_count > 0:
        error_summary.append(f"  • RST Packets: {rst_count:,} (connection resets)")
    if icmp_unreach:
        error_summary.append(f"  • ICMP Unreachable: {len(icmp_unreach):,} packets (connectivity issues)")
    if icmp_time_exceeded:
        error_summary.append(f"  • ICMP Time Exceeded: {len(icmp_time_exceeded):,} packets (routing loops/TTL)")
    
    if error_summary:
        for err in error_summary:
            print(err)
    else:
        print("  ✓ No errors detected - Network is healthy!")
    
    print(f"\n{'='*100}")
    print("🌐 APPLICATION LAYER")
    print(f"{'='*100}")
    if dns_packets:
        print(f"  DNS Traffic: {len(dns_packets):,} packets")
        if dns_servers and len(dns_servers) > 0:
            print(f"    Primary DNS Server: {dns_servers.most_common(1)[0][0]}")
    if https_packets:
        print(f"  HTTPS/TLS Traffic: {len(https_packets):,} packets")
        if https_servers and len(https_servers) > 0:
            print(f"    Top HTTPS Server: {https_servers.most_common(1)[0][0]}")
    
    # HTTP status summary
    if SCAPY_AVAILABLE and scapy_analysis and scapy_analysis.get('http_responses'):
        http_ok = len([r for r in scapy_analysis['http_responses'] if r['status'].startswith('2')])
        http_4xx = len([r for r in scapy_analysis['http_responses'] if r['status'].startswith('4')])
        http_5xx = len([r for r in scapy_analysis['http_responses'] if r['status'].startswith('5')])
        if http_ok or http_4xx or http_5xx:
            print(f"  HTTP Responses:")
            if http_ok:
                print(f"    ✓ Success (2xx): {http_ok}")
            if http_4xx:
                print(f"    ⚠ Client Errors (4xx): {http_4xx}")
            if http_5xx:
                print(f"    ✗ Server Errors (5xx): {http_5xx}")
    
    print(f"\n{'='*100}")
    print("📈 PERFORMANCE METRICS")
    print(f"{'='*100}")
    if packet_sizes:
        print(f"  Average Packet Size: {sum(packet_sizes)/len(packet_sizes):.0f} bytes")
        print(f"  Total Data Volume: {sum(packet_sizes)/1024/1024:.2f} MB (sample)")
    
    if SCAPY_AVAILABLE and scapy_analysis and len(scapy_analysis.get('timestamps', [])) > 1:
        duration = scapy_analysis['timestamps'][-1] - scapy_analysis['timestamps'][0]
        pps = len(scapy_analysis['timestamps']) / duration if duration > 0 else 0
        print(f"  Capture Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"  Average Packet Rate: {pps:.1f} packets/second")
    
    print(f"\n{'='*100}")
    print("🎯 TOP TALKERS")
    print(f"{'='*100}")
    if SCAPY_AVAILABLE and scapy_analysis:
        if scapy_analysis.get('src_ips'):
            top_src = scapy_analysis['src_ips'].most_common(3)
            print(f"  Top Source IPs:")
            for ip, count in top_src:
                print(f"    {ip}: {count:,} packets")
        
        if scapy_analysis.get('dst_ips'):
            top_dst = scapy_analysis['dst_ips'].most_common(3)
            print(f"  Top Destination IPs:")
            for ip, count in top_dst:
                print(f"    {ip}: {count:,} packets")
    
    print(f"\n{'='*100}")
    print("🔍 SECURITY OBSERVATIONS")
    print(f"{'='*100}")
    
    security_notes = []
    if rst_count > total * 0.1:
        security_notes.append("  ⚠ Very high RST rate - possible connection scanning or DDoS")
    if port_unreach and len(port_unreach) > 50:
        security_notes.append("  ⚠ Many port unreachable messages - possible port scanning")
    if retrans and len(retrans) > total * 0.05:
        security_notes.append("  ⚠ High retransmission rate - network congestion or packet loss")
    if icmp_admin_prohibited:
        security_notes.append(f"  🔥 Firewall blocks detected: {len(icmp_admin_prohibited)} packets")
    
    if security_notes:
        for note in security_notes:
            print(note)
    else:
        print("  ✓ No obvious security concerns detected")
    
    print(f"\n{'='*100}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*100}")
    
    recommendations = []
    if has_retrans and len(retrans) > total * 0.02:
        recommendations.append("  • Investigate network path for packet loss or congestion")
    if has_zero_win:
        recommendations.append("  • Check receiver buffer sizes and application performance")
    if rst_count > total * 0.05:
        recommendations.append("  • Review connection reset causes - may indicate application issues")
    if icmp_unreach and len(icmp_unreach) > 20:
        recommendations.append("  • Verify routing and firewall configurations")
    if has_dup_ack:
        recommendations.append("  • Duplicate ACKs indicate missing packets - check network quality")
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    else:
        print("  ✓ Network appears healthy - no immediate action required")
    
    print(f"\n{'='*100}")
    print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")
    
    # GENERATE VISUAL OUTPUTS
    if enable_visual and VISUAL_AVAILABLE and scapy_analysis:
        print("\n" + "="*100)
        print("🎨 GENERATING VISUAL OUTPUTS")
        print("="*100)
        
        base_name = Path(pcap_file).stem
        
        # Generate network diagram
        network_diagram = f"{base_name}_network_diagram.png"
        generate_network_diagram(scapy_analysis, network_diagram)
        
        # Generate protocol chart
        protocol_chart = f"{base_name}_protocol_chart.png"
        generate_protocol_chart(protocol_stats, total, protocol_chart)
        
        # Generate interactive HTML
        html_report = f"{base_name}_report.html"
        generate_interactive_html(scapy_analysis, pcap_file, html_report)
        
        print(f"\n✅ Visual outputs generated:")
        print(f"   📊 Network Diagram: {network_diagram}")
        print(f"   📈 Protocol Chart: {protocol_chart}")
        print(f"   🌐 HTML Report: {html_report}")
    elif enable_visual and not VISUAL_AVAILABLE:
        print(f"\n⚠ Visual outputs requested but matplotlib/networkx not installed")
        print(f"   Run: pip3 install matplotlib networkx")
    
    print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Advanced PCAP Analyzer v4 - Enhanced Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis (fast)
  python3 pcap_analyzer_v3.py capture.pcap
  
  # With JSON export
  python3 pcap_analyzer_v3.py capture.pcap --export-json
  
  # With visual diagrams
  python3 pcap_analyzer_v3.py capture.pcap --visual
  
  # With whois lookups
  python3 pcap_analyzer_v3.py capture.pcap --whois
  
  # With Tor detection
  python3 pcap_analyzer_v3.py capture.pcap --tor
  
  # Full analysis with all features
  python3 pcap_analyzer_v3.py capture.pcap --visual --whois --tor --export-json
        """
    )
    
    parser.add_argument('pcap_file', help='PCAP file to analyze')
    parser.add_argument('--export-json', action='store_true', 
                       help='Export analysis to JSON file')
    parser.add_argument('--visual', action='store_true',
                       help='Generate visual diagrams (PNG) and interactive HTML report')
    parser.add_argument('--whois', action='store_true',
                       help='Perform whois lookups for top IPs (slower)')
    parser.add_argument('--tor', action='store_true',
                       help='Check for Tor exit nodes in traffic')
    
    args = parser.parse_args()
    
    analyze_pcap(args.pcap_file, 
                export_json=args.export_json,
                enable_whois=args.whois,
                enable_tor=args.tor,
                enable_visual=args.visual)
