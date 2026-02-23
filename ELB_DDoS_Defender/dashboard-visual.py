#!/usr/bin/env python3
"""Visual Dashboard with Menu at Bottom"""
import json
import time
import os
import sys
import boto3
import subprocess
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
from rich.text import Text

console = Console()

# AWS clients
elbv2 = boto3.client('elbv2', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

# Global state
current_menu_option = None
menu_active = False

def load_metrics():
    try:
        with open('/var/log/elb-ddos-defender/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return {
            'total_packets': 0,
            'total_bytes': 0,
            'unique_ips': 0,
            'packets_per_sec': 0,
            'connections_per_sec': 0,
            'syn_packets': 0,
            'udp_packets': 0,
            'attacks_detected': [],
            'timestamp': 'N/A'
        }

def create_metrics_panel(metrics):
    table = Table(box=box.ROUNDED, show_header=False, expand=True)
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="bold green", width=20)
    
    table.add_row("📦 Total Packets", f"{metrics.get('total_packets', 0):,}")
    table.add_row("💾 Total Traffic", f"{metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB")
    table.add_row("👥 Unique IPs", f"{metrics.get('unique_ips', 0):,}")
    table.add_row("⚡ Packets/sec", f"{metrics.get('packets_per_sec', 0)}")
    table.add_row("🔗 Connections/sec", f"{metrics.get('connections_per_sec', 0)}")
    
    return Panel(table, title="[bold blue]📊 LIVE TRAFFIC METRICS[/bold blue]", border_style="blue")

def create_protocol_panel(metrics):
    table = Table(box=box.ROUNDED, show_header=False, expand=True)
    table.add_column("Protocol", style="yellow", width=20)
    table.add_column("Count", style="bold magenta", width=15)
    
    table.add_row("🔵 TCP SYN", f"{metrics.get('syn_packets', 0):,}")
    table.add_row("🟣 UDP", f"{metrics.get('udp_packets', 0):,}")
    
    return Panel(table, title="[bold yellow]🔵 PROTOCOL BREAKDOWN[/bold yellow]", border_style="yellow")

def create_attacks_panel(metrics):
    attacks = metrics.get('attacks_detected', [])
    
    if not attacks:
        content = "[green]✅ No attacks detected[/green]"
    else:
        table = Table(box=box.SIMPLE, show_header=True, expand=True)
        table.add_column("Type", style="red", width=15)
        table.add_column("Source → Target", style="white", width=35)
        table.add_column("Count", style="yellow", width=10)
        
        for attack in attacks[-5:]:
            atype = attack.get('type', 'Unknown')
            src = attack.get('source', 'N/A')
            dst = attack.get('destination', 'N/A')
            count = attack.get('count', 'N/A')
            
            table.add_row(atype, f"{src} → {dst}", str(count))
        
        content = table
    
    title = f"[bold red]🚨 ATTACKS DETECTED: {len(attacks)}[/bold red]"
    return Panel(content, title=title, border_style="red")

def create_activity_panel(metrics):
    attacks = metrics.get('attacks_detected', [])
    
    lines = []
    if attacks:
        for attack in attacks[-10:]:
            timestamp = attack.get('timestamp', 'N/A')
            atype = attack.get('type', 'Unknown')
            src = attack.get('source', 'N/A')
            
            lines.append(f"[dim]{timestamp}[/dim] [red]{atype}[/red] from [yellow]{src}[/yellow]")
    else:
        lines.append("[green]No recent activity[/green]")
    
    content = "\n".join(lines[-8:])
    
    return Panel(content, title="[bold cyan]📝 RECENT ACTIVITY[/bold cyan]", border_style="cyan")

def create_menu_panel():
    """Menu at bottom"""
    menu_text = Text()
    menu_text.append("MENU: ", style="bold white")
    menu_text.append("[1]", style="bold cyan")
    menu_text.append(" Setup ELB  ", style="white")
    menu_text.append("[2]", style="bold cyan")
    menu_text.append(" View ELBs  ", style="white")
    menu_text.append("[3]", style="bold cyan")
    menu_text.append(" VPC Status  ", style="white")
    menu_text.append("[4]", style="bold cyan")
    menu_text.append(" Logs  ", style="white")
    menu_text.append("[5]", style="bold cyan")
    menu_text.append(" Attacks  ", style="white")
    menu_text.append("[6]", style="bold cyan")
    menu_text.append(" Report  ", style="white")
    menu_text.append("[7]", style="bold cyan")
    menu_text.append(" Exit", style="white")
    
    return Panel(menu_text, title="[bold green]⚙️  NAVIGATION MENU[/bold green]", border_style="green")

def create_dashboard():
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=3),
        Layout(name="menu", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1)
    )
    
    layout["left"].split_column(
        Layout(name="metrics"),
        Layout(name="attacks")
    )
    
    layout["right"].split_column(
        Layout(name="protocol"),
        Layout(name="activity")
    )
    
    return layout

def update_dashboard(layout):
    metrics = load_metrics()
    
    layout["header"].update(
        Panel(
            "[bold white]ELB DDoS DEFENDER - LIVE MONITORING DASHBOARD[/bold white]",
            style="bold white on blue"
        )
    )
    
    layout["metrics"].update(create_metrics_panel(metrics))
    layout["protocol"].update(create_protocol_panel(metrics))
    layout["attacks"].update(create_attacks_panel(metrics))
    layout["activity"].update(create_activity_panel(metrics))
    layout["menu"].update(create_menu_panel())

def main():
    layout = create_dashboard()
    
    console.print("[yellow]Starting dashboard... Press Ctrl+C to access menu[/yellow]")
    time.sleep(2)
    
    try:
        with Live(layout, refresh_per_second=0.5, screen=True):
            while True:
                update_dashboard(layout)
                time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n[green]Menu activated![/green]")
        show_menu()

def show_menu():
    """Show interactive menu"""
    os.system('clear')
    while True:
        print("=" * 80)
        print("                    ELB DDoS DEFENDER - MENU")
        print("=" * 80)
        print("\n1. 🎯 Select ELB & Setup Traffic Mirroring")
        print("2. 🔵 View All Load Balancers (Detailed)")
        print("3. 🌐 View VPC & Traffic Mirroring Status")
        print("4. 📝 View Logs")
        print("5. 🚨 View Detected Attacks (with WHOIS)")
        print("6. 📄 Generate Report")
        print("7. 🔄 Exit")
        print("\n" + "=" * 80)
        
        choice = input("\nSelect option (1-7, or 'v' for visual dashboard): ").strip()
        
        if choice == 'v':
            main()
            return
        elif choice == '7':
            print("\nExiting...")
            sys.exit(0)
        elif choice in ['1', '2', '3', '4', '5', '6']:
            print(f"\n⚙️  Option {choice} - Feature available in dashboard-complete.py")
            print("Run: python3.11 /opt/elb-ddos-defender/dashboard-complete.py")
            input("\nPress Enter to continue...")
        else:
            print("\n❌ Invalid option")
            input("Press Enter to continue...")
        
        os.system('clear')

if __name__ == '__main__':
    main()
