#!/usr/bin/env python3.11
import json
import time
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from collections import deque
import re

console = Console()

# Store recent packets
recent_packets = deque(maxlen=15)

def parse_log_for_packets():
    """Parse defender log for recent packet activity"""
    try:
        with open('/var/log/elb-ddos-defender/defender.log', 'r') as f:
            lines = f.readlines()[-50:]  # Last 50 lines
            
        for line in lines:
            # Match: Real client IP detected: 2.57.122.238 → 10.0.3.152:22
            match = re.search(r'Real client IP detected: ([\d.]+) → ([\d.]+):(\d+)', line)
            if match:
                timestamp = line.split(' - ')[0].split(',')[0]
                src_ip = match.group(1)
                dst_ip = match.group(2)
                dst_port = match.group(3)
                
                packet_info = {
                    'time': timestamp.split(' ')[1] if ' ' in timestamp else timestamp,
                    'src': src_ip,
                    'dst': f"{dst_ip}:{dst_port}"
                }
                
                # Add if not duplicate
                if not recent_packets or recent_packets[-1] != packet_info:
                    recent_packets.append(packet_info)
    except:
        pass

def load_metrics():
    try:
        with open('/var/log/elb-ddos-defender/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def create_metrics_table(metrics):
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green bold")
    
    table.add_row("📦 Total Packets", f"{metrics.get('total_packets', 0):,}")
    table.add_row("💾 Total Traffic", f"{metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB")
    table.add_row("👥 Unique IPs", f"{metrics.get('unique_ips', 0):,}")
    table.add_row("⚡ Packets/sec", f"{metrics.get('packets_per_sec', 0)}")
    table.add_row("🔗 Connections/sec", f"{metrics.get('connections_per_sec', 0)}")
    
    return table

def create_protocol_table(metrics):
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Protocol", style="cyan")
    table.add_column("Count", style="yellow bold")
    
    table.add_row("🔵 TCP SYN", f"{metrics.get('syn_packets', 0):,}")
    table.add_row("🟣 UDP", f"{metrics.get('udp_packets', 0):,}")
    
    return table

def create_packet_stream_table():
    """Create table showing live packet flow"""
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Time", style="dim", width=10)
    table.add_column("Source IP", style="cyan", width=18)
    table.add_column("→", style="white", width=3)
    table.add_column("Destination", style="green", width=25)
    
    if not recent_packets:
        table.add_row("", "No packets yet", "", "")
    else:
        for pkt in list(recent_packets)[-15:]:
            table.add_row(
                pkt['time'],
                pkt['src'],
                "→",
                pkt['dst']
            )
    
    return table

def create_attacks_panel(metrics):
    attacks = metrics.get('attacks_detected', [])
    if not attacks:
        return Panel("✅ No attacks detected", style="green")
    
    content = "\n".join([f"🚨 {a}" for a in attacks[:5]])
    return Panel(content, style="red bold")

def update_dashboard(layout):
    parse_log_for_packets()
    metrics = load_metrics()
    
    layout["header"].update(
        Panel("🛡️  ELB DDoS DEFENDER - LIVE MONITORING", style="bold white on blue")
    )
    
    layout["metrics"].update(
        Panel(create_metrics_table(metrics), title="📊 LIVE TRAFFIC METRICS", border_style="cyan")
    )
    
    layout["protocol"].update(
        Panel(create_protocol_table(metrics), title="🔵 PROTOCOL BREAKDOWN", border_style="blue")
    )
    
    layout["attacks"].update(
        Panel(create_attacks_panel(metrics), title=f"🚨 ATTACKS DETECTED: {len(metrics.get('attacks_detected', []))}", border_style="red")
    )
    
    layout["stream"].update(
        Panel(create_packet_stream_table(), title="📡 LIVE PACKET STREAM", border_style="green")
    )
    
    layout["menu"].update(
        Panel(
            "Press Ctrl+C to stop and access menu",
            style="bold yellow"
        )
    )

def main():
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="menu", size=3)
    )
    
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    layout["left"].split_column(
        Layout(name="metrics"),
        Layout(name="attacks")
    )
    
    layout["right"].split_column(
        Layout(name="protocol", size=10),
        Layout(name="stream")
    )
    
    print("Starting dashboard... Press Ctrl+C to access menu")
    
    with Live(layout, refresh_per_second=0.5, screen=True):
        while True:
            update_dashboard(layout)
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
