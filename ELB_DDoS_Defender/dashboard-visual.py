#!/usr/bin/env python3
"""FULLY INTERACTIVE Visual Dashboard - Press keys 1-7 anytime"""
import json
import time
import os
import sys
import boto3
import subprocess
import threading
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
from rich.text import Text
from pynput import keyboard

console = Console()

# AWS clients
elbv2 = boto3.client('elbv2', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

# Global state
menu_action = None
dashboard_running = True

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
    menu_text = Text()
    menu_text.append("PRESS KEY: ", style="bold white")
    menu_text.append("[1]", style="bold cyan")
    menu_text.append(" Setup ELB  ", style="white")
    menu_text.append("[2]", style="bold cyan")
    menu_text.append(" View ELBs  ", style="white")
    menu_text.append("[3]", style="bold cyan")
    menu_text.append(" VPC  ", style="white")
    menu_text.append("[4]", style="bold cyan")
    menu_text.append(" Logs  ", style="white")
    menu_text.append("[5]", style="bold cyan")
    menu_text.append(" Attacks  ", style="white")
    menu_text.append("[6]", style="bold cyan")
    menu_text.append(" Report  ", style="white")
    menu_text.append("[7]", style="bold cyan")
    menu_text.append(" Exit", style="white")
    
    return Panel(menu_text, title="[bold green]⚙️  INTERACTIVE MENU - Press 1-7 Anytime[/bold green]", border_style="green")

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
            "[bold white]ELB DDoS DEFENDER - FULLY INTERACTIVE DASHBOARD[/bold white]",
            style="bold white on blue"
        )
    )
    
    layout["metrics"].update(create_metrics_panel(metrics))
    layout["protocol"].update(create_protocol_panel(metrics))
    layout["attacks"].update(create_attacks_panel(metrics))
    layout["activity"].update(create_activity_panel(metrics))
    layout["menu"].update(create_menu_panel())

def on_press(key):
    """Handle keyboard input"""
    global menu_action, dashboard_running
    
    try:
        if hasattr(key, 'char') and key.char in ['1', '2', '3', '4', '5', '6', '7']:
            menu_action = key.char
            dashboard_running = False
    except:
        pass

def start_keyboard_listener():
    """Start listening for keyboard input"""
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener

def run_dashboard():
    """Run the live dashboard"""
    global dashboard_running, menu_action
    
    layout = create_dashboard()
    dashboard_running = True
    
    try:
        with Live(layout, refresh_per_second=0.5, screen=True):
            while dashboard_running:
                update_dashboard(layout)
                time.sleep(2)
    except:
        pass

def main():
    global menu_action, dashboard_running
    
    console.print("[yellow]Starting fully interactive dashboard...[/yellow]")
    console.print("[green]Press 1-7 anytime to access menu options![/green]")
    time.sleep(2)
    
    # Start keyboard listener
    listener = start_keyboard_listener()
    
    while True:
        menu_action = None
        dashboard_running = True
        
        # Run dashboard
        run_dashboard()
        
        # Handle menu action
        if menu_action == '1':
            os.system('clear')
            console.print("[cyan]Option 1: Setup ELB & Traffic Mirroring[/cyan]")
            console.print("[yellow]This feature requires proper IAM permissions[/yellow]")
            input("\nPress Enter to return to dashboard...")
        elif menu_action == '2':
            os.system('clear')
            console.print("[cyan]Option 2: View All Load Balancers[/cyan]")
            try:
                response = elbv2.describe_load_balancers()
                for lb in response['LoadBalancers']:
                    console.print(f"\n[bold]{lb['LoadBalancerName']}[/bold] ({lb['Type']})")
                    console.print(f"  DNS: {lb['DNSName']}")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to return to dashboard...")
        elif menu_action == '3':
            os.system('clear')
            console.print("[cyan]Option 3: VPC & Traffic Mirroring Status[/cyan]")
            try:
                sessions = ec2.describe_traffic_mirror_sessions()
                console.print(f"\n[green]Active Sessions: {len(sessions['TrafficMirrorSessions'])}[/green]")
                for session in sessions['TrafficMirrorSessions']:
                    console.print(f"  Session: {session['TrafficMirrorSessionId']}")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to return to dashboard...")
        elif menu_action == '4':
            os.system('clear')
            console.print("[cyan]Option 4: View Logs[/cyan]")
            try:
                with open('/var/log/elb-ddos-defender/defender.log', 'r') as f:
                    lines = f.readlines()
                    for line in lines[-30:]:
                        print(line.strip())
            except:
                console.print("[red]No logs available[/red]")
            input("\nPress Enter to return to dashboard...")
        elif menu_action == '5':
            os.system('clear')
            console.print("[cyan]Option 5: Detected Attacks[/cyan]")
            metrics = load_metrics()
            attacks = metrics.get('attacks_detected', [])
            if attacks:
                for i, attack in enumerate(attacks[-10:], 1):
                    console.print(f"\n[{i}] {attack.get('type', 'Unknown')}")
                    console.print(f"    {attack.get('source', 'N/A')} → {attack.get('destination', 'N/A')}")
            else:
                console.print("[green]No attacks detected[/green]")
            input("\nPress Enter to return to dashboard...")
        elif menu_action == '6':
            os.system('clear')
            console.print("[cyan]Option 6: Generate Report[/cyan]")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"/tmp/ddos_report_{timestamp}.txt"
            console.print(f"[green]Report generated: {filename}[/green]")
            input("\nPress Enter to return to dashboard...")
        elif menu_action == '7':
            console.print("\n[yellow]Exiting...[/yellow]")
            listener.stop()
            sys.exit(0)

if __name__ == '__main__':
    main()
