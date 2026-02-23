#!/usr/bin/env python3
"""Full Visual Dashboard with Rich Widgets"""
import json
import time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box

console = Console()

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
    """Top panel - Main metrics"""
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
    """Protocol breakdown panel"""
    table = Table(box=box.ROUNDED, show_header=False, expand=True)
    table.add_column("Protocol", style="yellow", width=20)
    table.add_column("Count", style="bold magenta", width=15)
    
    table.add_row("🔵 TCP SYN", f"{metrics.get('syn_packets', 0):,}")
    table.add_row("🟣 UDP", f"{metrics.get('udp_packets', 0):,}")
    
    return Panel(table, title="[bold yellow]🔵 PROTOCOL BREAKDOWN[/bold yellow]", border_style="yellow")

def create_attacks_panel(metrics):
    """Attacks panel"""
    attacks = metrics.get('attacks_detected', [])
    
    if not attacks:
        content = "[green]✅ No attacks detected[/green]"
    else:
        table = Table(box=box.SIMPLE, show_header=True, expand=True)
        table.add_column("Type", style="red", width=15)
        table.add_column("Source → Target", style="white", width=35)
        table.add_column("Count", style="yellow", width=10)
        
        for attack in attacks[-5:]:  # Last 5 attacks
            atype = attack.get('type', 'Unknown')
            src = attack.get('source', 'N/A')
            dst = attack.get('destination', 'N/A')
            count = attack.get('count', 'N/A')
            
            table.add_row(atype, f"{src} → {dst}", str(count))
        
        content = table
    
    title = f"[bold red]🚨 ATTACKS DETECTED: {len(attacks)}[/bold red]"
    return Panel(content, title=title, border_style="red")

def create_activity_panel(metrics):
    """Recent activity log"""
    attacks = metrics.get('attacks_detected', [])
    
    lines = []
    if attacks:
        for attack in attacks[-10:]:  # Last 10
            timestamp = attack.get('timestamp', 'N/A')
            atype = attack.get('type', 'Unknown')
            src = attack.get('source', 'N/A')
            
            lines.append(f"[dim]{timestamp}[/dim] [red]{atype}[/red] from [yellow]{src}[/yellow]")
    else:
        lines.append("[green]No recent activity[/green]")
    
    content = "\n".join(lines[-8:])  # Show last 8 lines
    
    return Panel(content, title="[bold cyan]📝 RECENT ACTIVITY[/bold cyan]", border_style="cyan")

def create_status_panel(metrics):
    """System status"""
    timestamp = metrics.get('timestamp', 'N/A')
    
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("", style="dim", width=20)
    table.add_column("", style="white", width=30)
    
    table.add_row("🟢 Status", "[green]MONITORING ACTIVE[/green]")
    table.add_row("⏰ Last Update", timestamp)
    table.add_row("🎯 Mode", "Real-time Analysis")
    
    return Panel(table, title="[bold green]⚙️  SYSTEM STATUS[/bold green]", border_style="green")

def create_dashboard():
    """Create full dashboard layout"""
    layout = Layout()
    
    # Split into top and bottom
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    # Split main into left and right
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1)
    )
    
    # Split left into top and bottom
    layout["left"].split_column(
        Layout(name="metrics"),
        Layout(name="attacks")
    )
    
    # Split right into top and bottom
    layout["right"].split_column(
        Layout(name="protocol"),
        Layout(name="activity")
    )
    
    return layout

def update_dashboard(layout):
    """Update all panels with current data"""
    metrics = load_metrics()
    
    # Header
    layout["header"].update(
        Panel(
            "[bold white]ELB DDoS DEFENDER - LIVE MONITORING DASHBOARD[/bold white]",
            style="bold white on blue"
        )
    )
    
    # Main panels
    layout["metrics"].update(create_metrics_panel(metrics))
    layout["protocol"].update(create_protocol_panel(metrics))
    layout["attacks"].update(create_attacks_panel(metrics))
    layout["activity"].update(create_activity_panel(metrics))
    
    # Footer
    layout["footer"].update(
        Panel(
            "[dim]Press Ctrl+C to exit | Updates every 2 seconds[/dim]",
            style="dim white on black"
        )
    )

def main():
    """Run live dashboard"""
    layout = create_dashboard()
    
    try:
        with Live(layout, refresh_per_second=0.5, screen=True):
            while True:
                update_dashboard(layout)
                time.sleep(2)
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

if __name__ == '__main__':
    main()
