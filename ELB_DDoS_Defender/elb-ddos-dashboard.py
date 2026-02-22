#!/usr/bin/env python3.11
"""Interactive ELB DDoS Defender Dashboard"""
import time
import yaml
import subprocess
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

console = Console()

def load_config():
    try:
        with open('/opt/elb-ddos-defender/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

def show_menu():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]ELB DDoS Defender - Interactive Dashboard[/bold cyan]\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="cyan"
    ))
    console.print()
    
    config = load_config()
    
    # Load Balancers
    table = Table(title="Monitored Load Balancers", box=box.ROUNDED, show_header=True)
    table.add_column("#", style="dim", width=5)
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Status", style="green", width=15)
    
    lbs = config.get('load_balancers', [])
    if lbs:
        for i, lb in enumerate(lbs, 1):
            table.add_row(str(i), lb.get('name', 'Unknown'), "✓ Active")
    else:
        table.add_row("-", "No load balancers configured", "⚠ Pending")
    
    console.print(table)
    console.print()
    
    # Menu
    menu = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    menu.add_column(style="bold cyan")
    menu.add_column(style="white")
    
    menu.add_row("1", "View Real-time Logs")
    menu.add_row("2", "Check Service Status")
    menu.add_row("3", "View Configuration")
    menu.add_row("4", "List All Load Balancers")
    menu.add_row("5", "Restart Service")
    menu.add_row("R", "Refresh Dashboard")
    menu.add_row("Q", "Quit")
    
    console.print(Panel(menu, title="[bold]Menu Options[/bold]", border_style="green"))
    console.print()

def view_logs():
    console.clear()
    console.print("[bold cyan]Real-time Logs (Press Ctrl+C to return)[/bold cyan]\n")
    try:
        subprocess.run(["tail", "-f", "/var/log/elb-ddos-defender/defender.log"])
    except KeyboardInterrupt:
        pass

def check_status():
    console.clear()
    console.print("[bold cyan]Service Status[/bold cyan]\n")
    subprocess.run(["systemctl", "status", "elb-ddos-defender"])
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def view_config():
    console.clear()
    console.print("[bold cyan]Configuration[/bold cyan]\n")
    subprocess.run(["cat", "/opt/elb-ddos-defender/config.yaml"])
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def list_load_balancers():
    console.clear()
    console.print("[bold cyan]All Load Balancers in Region[/bold cyan]\n")
    subprocess.run(["/usr/local/bin/aws", "elbv2", "describe-load-balancers", 
                    "--region", "us-east-1", "--query", 
                    "LoadBalancers[*].[LoadBalancerName,LoadBalancerArn]", 
                    "--output", "table"])
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def restart_service():
    console.clear()
    console.print("[bold yellow]Restarting service...[/bold yellow]\n")
    subprocess.run(["systemctl", "restart", "elb-ddos-defender"])
    console.print("[bold green]✓ Service restarted![/bold green]")
    time.sleep(2)

def main():
    while True:
        show_menu()
        choice = Prompt.ask("[bold cyan]Select option[/bold cyan]", 
                           choices=["1", "2", "3", "4", "5", "r", "R", "q", "Q"],
                           default="r")
        
        if choice in ["q", "Q"]:
            console.clear()
            console.print("\n[bold yellow]Dashboard closed.[/bold yellow]\n")
            break
        elif choice == "1":
            view_logs()
        elif choice == "2":
            check_status()
        elif choice == "3":
            view_config()
        elif choice == "4":
            list_load_balancers()
        elif choice == "5":
            restart_service()
        elif choice in ["r", "R"]:
            continue

if __name__ == "__main__":
    main()
