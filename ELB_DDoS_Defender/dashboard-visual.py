#!/usr/bin/env python3.11
import json
import time
import os
import boto3
import subprocess
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from collections import deque
import re

console = Console()
recent_packets = deque(maxlen=15)

# AWS clients
elbv2 = boto3.client('elbv2', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

def parse_log_for_packets():
    try:
        with open('/var/log/elb-ddos-defender/defender.log', 'r') as f:
            lines = f.readlines()[-50:]
        for line in lines:
            match = re.search(r'Real client IP detected: ([\d.]+) → ([\d.]+):(\d+)', line)
            if match:
                timestamp = line.split(' - ')[0].split(',')[0]
                packet_info = {
                    'time': timestamp.split(' ')[1] if ' ' in timestamp else timestamp,
                    'src': match.group(1),
                    'dst': f"{match.group(2)}:{match.group(3)}"
                }
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
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Time", style="dim", width=10)
    table.add_column("Source IP", style="cyan", width=18)
    table.add_column("→", style="white", width=3)
    table.add_column("Destination", style="green", width=25)
    if not recent_packets:
        table.add_row("", "No packets yet", "", "")
    else:
        for pkt in list(recent_packets)[-15:]:
            table.add_row(pkt['time'], pkt['src'], "→", pkt['dst'])
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
    layout["header"].update(Panel("🛡️  ELB DDoS DEFENDER - LIVE MONITORING", style="bold white on blue"))
    layout["metrics"].update(Panel(create_metrics_table(metrics), title="📊 LIVE TRAFFIC METRICS", border_style="cyan"))
    layout["protocol"].update(Panel(create_protocol_table(metrics), title="🔵 PROTOCOL BREAKDOWN", border_style="blue"))
    layout["attacks"].update(Panel(create_attacks_panel(metrics), title=f"🚨 ATTACKS DETECTED: {len(metrics.get('attacks_detected', []))}", border_style="red"))
    layout["stream"].update(Panel(create_packet_stream_table(), title="📡 LIVE PACKET STREAM", border_style="green"))
    layout["menu"].update(Panel("Press Ctrl+C to stop and access menu", style="bold yellow"))

def show_visual_dashboard():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="menu", size=3)
    )
    layout["body"].split_row(Layout(name="left"), Layout(name="right"))
    layout["left"].split_column(Layout(name="metrics"), Layout(name="attacks"))
    layout["right"].split_column(Layout(name="protocol", size=10), Layout(name="stream"))
    
    console.print("[yellow]Starting visual dashboard... Press Ctrl+C to access menu[/yellow]")
    time.sleep(1)
    
    try:
        with Live(layout, refresh_per_second=0.5, screen=True):
            while True:
                update_dashboard(layout)
                time.sleep(2)
    except KeyboardInterrupt:
        pass

def show_menu():
    os.system('clear')
    print("=" * 80)
    print("                     ELB DDoS DEFENDER - MENU")
    print("=" * 80)
    print("\n1. 🎯 Select ELB & Setup Traffic Mirroring")
    print("2. 🔵 View All Load Balancers (Detailed with ENIs/IPs)")
    print("3. 🌐 View VPC & Traffic Mirroring Status")
    print("4. 📝 View Logs")
    print("5. 🚨 View Detected Attacks")
    print("6. 📄 Generate Report")
    print("7. 🔄 Return to Visual Dashboard")
    print("8. ❌ Exit")
    print("=" * 80)

def view_load_balancers():
    os.system('clear')
    print("=" * 80)
    print("                🔵 ALL LOAD BALANCERS")
    print("=" * 80)
    try:
        response = elbv2.describe_load_balancers()
        for lb in response['LoadBalancers']:
            print(f"\n📌 {lb['LoadBalancerName']} ({lb['Type'].upper()})")
            print(f"   DNS: {lb['DNSName']}")
            print(f"   VPC: {lb['VpcId']}")
            print(f"   State: {lb['State']['Code']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    input("\nPress Enter to continue...")

def view_vpc_status():
    os.system('clear')
    print("=" * 80)
    print("                🌐 VPC & TRAFFIC MIRRORING STATUS")
    print("=" * 80)
    try:
        sessions = ec2.describe_traffic_mirror_sessions()
        print(f"\n✅ Active Mirror Sessions: {len(sessions['TrafficMirrorSessions'])}")
        for s in sessions['TrafficMirrorSessions']:
            print(f"\n   Session: {s['TrafficMirrorSessionId']}")
            print(f"   Source ENI: {s['NetworkInterfaceId']}")
            print(f"   Target: {s['TrafficMirrorTargetId']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    input("\nPress Enter to continue...")

def view_logs():
    os.system('clear')
    print("=" * 80)
    print("                📝 RECENT LOGS (Last 30 lines)")
    print("=" * 80)
    try:
        result = subprocess.run(['tail', '-30', '/var/log/elb-ddos-defender/defender.log'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error: {e}")
    input("\nPress Enter to continue...")

def view_attacks():
    os.system('clear')
    print("=" * 80)
    print("                🚨 DETECTED ATTACKS")
    print("=" * 80)
    metrics = load_metrics()
    attacks = metrics.get('attacks_detected', [])
    if not attacks:
        print("\n✅ No attacks detected")
    else:
        for i, attack in enumerate(attacks, 1):
            print(f"\n{i}. {attack}")
    input("\nPress Enter to continue...")

def generate_report():
    os.system('clear')
    print("=" * 80)
    print("                📄 GENERATING REPORT")
    print("=" * 80)
    metrics = load_metrics()
    filename = f"/tmp/ddos-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write("ELB DDoS DEFENDER REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(f"Total Packets: {metrics.get('total_packets', 0):,}\n")
        f.write(f"Unique IPs: {metrics.get('unique_ips', 0):,}\n")
        f.write(f"Attacks: {len(metrics.get('attacks_detected', []))}\n")
    print(f"\n✅ Report saved to: {filename}")
    input("\nPress Enter to continue...")

def main():
    while True:
        show_visual_dashboard()
        
        while True:
            show_menu()
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == '1':
                print("\n⚠️  Use AWS Console or CLI to setup traffic mirroring")
                input("\nPress Enter to continue...")
            elif choice == '2':
                view_load_balancers()
            elif choice == '3':
                view_vpc_status()
            elif choice == '4':
                view_logs()
            elif choice == '5':
                view_attacks()
            elif choice == '6':
                generate_report()
            elif choice == '7':
                break  # Return to visual dashboard
            elif choice == '8':
                console.print("[yellow]Exiting...[/yellow]")
                return
            else:
                print("❌ Invalid option")
                time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
