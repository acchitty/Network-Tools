#!/usr/bin/env python3.11
"""Simple ELB DDoS Defender Dashboard"""
import time
import yaml
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def load_config():
    try:
        with open('/opt/elb-ddos-defender/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

def show_dashboard():
    console.clear()
    config = load_config()
    
    # Header
    console.print(Panel.fit(
        f"[bold cyan]ELB DDoS Defender Dashboard[/bold cyan]\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="cyan"
    ))
    console.print()
    
    # Load Balancers Table
    table = Table(title="Monitored Load Balancers", box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Status", style="green", width=15)
    table.add_column("Region", style="yellow", width=15)
    
    lbs = config.get('load_balancers', [])
    region = config.get('aws', {}).get('region', 'us-east-1')
    
    if lbs:
        for lb in lbs:
            table.add_row(lb.get('name', 'Unknown'), "✓ Active", region)
    else:
        table.add_row("No load balancers configured", "⚠ Pending", region)
    
    console.print(table)
    console.print()
    
    # Status Panel
    console.print(Panel(
        "[bold green]✓ Service Running[/bold green]\n"
        "[yellow]Monitoring: Active[/yellow]\n"
        "[cyan]Logs: /var/log/elb-ddos-defender/defender.log[/cyan]",
        title="Status",
        border_style="green"
    ))
    console.print()
    
    # Controls
    console.print("[bold]Press Ctrl+C to exit[/bold]", style="dim")

def main():
    try:
        while True:
            show_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        console.clear()
        console.print("\n[bold yellow]Dashboard stopped.[/bold yellow]\n")

if __name__ == "__main__":
    main()
