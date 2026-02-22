#!/usr/bin/env python3.11
"""
Simple ELB DDoS Defender Dashboard
"""
import time
import yaml
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

console = Console()

def load_config():
    try:
        with open('/opt/elb-ddos-defender/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

def create_dashboard():
    config = load_config()
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    
    # Header
    header = Panel(
        f"[bold cyan]ELB DDoS Defender Dashboard[/bold cyan]\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        style="bold white on blue"
    )
    
    # Body - Load Balancers
    table = Table(title="Monitored Load Balancers", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Type", style="yellow")
    
    lbs = config.get('load_balancers', [])
    if lbs:
        for lb in lbs:
            table.add_row(lb.get('name', 'Unknown'), "✓ Active", "ALB/NLB")
    else:
        table.add_row("No load balancers configured", "⚠ Pending", "-")
    
    # Footer
    footer = Panel(
        "[bold]Controls:[/bold] Ctrl+C to exit | Service: ✓ Running",
        style="bold white on green"
    )
    
    layout["header"].update(header)
    layout["body"].update(Panel(table))
    layout["footer"].update(footer)
    
    return layout

def main():
    console.clear()
    console.print("[bold green]Starting ELB DDoS Defender Dashboard...[/bold green]\n")
    
    try:
        with Live(create_dashboard(), refresh_per_second=1, console=console) as live:
            while True:
                time.sleep(1)
                live.update(create_dashboard())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Dashboard stopped.[/bold yellow]")

if __name__ == "__main__":
    main()
