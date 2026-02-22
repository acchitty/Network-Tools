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
    
    menu.add_row("1", "Add Load Balancers to Monitor")
    menu.add_row("2", "View Real-time Logs")
    menu.add_row("3", "Check Service Status")
    menu.add_row("4", "View Configuration")
    menu.add_row("5", "Restart Service")
    menu.add_row("R", "Refresh Dashboard")
    menu.add_row("Q", "Quit")
    
    console.print(Panel(menu, title="[bold]Menu Options[/bold]", border_style="green"))
    console.print()

def add_load_balancers():
    console.clear()
    console.print("[bold cyan]Discover and Add Load Balancers[/bold cyan]\n")
    console.print("[yellow]Scanning for load balancers...[/yellow]\n")
    
    # Get all load balancers
    result = subprocess.run(["/usr/local/bin/aws", "elbv2", "describe-load-balancers", 
                            "--region", "us-east-1", "--output", "json"],
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        console.print("[red]Error: Could not fetch load balancers[/red]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    import json
    data = json.loads(result.stdout)
    lbs = data.get('LoadBalancers', [])
    
    if not lbs:
        console.print("[yellow]No load balancers found in region[/yellow]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    # Show table of load balancers
    table = Table(title="Available Load Balancers", box=box.ROUNDED, show_header=True)
    table.add_column("#", style="cyan", width=5)
    table.add_column("Name", style="green", width=20)
    table.add_column("Type", style="yellow", width=15)
    table.add_column("State", style="magenta", width=15)
    
    for i, lb in enumerate(lbs, 1):
        lb_type = lb['Type'].upper()
        table.add_row(str(i), lb['LoadBalancerName'], lb_type, lb['State']['Code'])
    
    console.print(table)
    console.print()
    
    # Let user select
    console.print("[bold]Enter numbers to add (comma-separated, e.g., 1,3,4) or 'all':[/bold]")
    selection = input("> ").strip()
    
    if not selection:
        return
    
    selected_lbs = []
    if selection.lower() == 'all':
        selected_lbs = lbs
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_lbs = [lbs[i] for i in indices if 0 <= i < len(lbs)]
        except:
            console.print("[red]Invalid selection[/red]")
            time.sleep(2)
            return
    
    # Load current config
    config = load_config()
    if 'load_balancers' not in config:
        config['load_balancers'] = []
    
    # Add selected LBs
    for lb in selected_lbs:
        # Check if already exists
        exists = any(existing['arn'] == lb['LoadBalancerArn'] 
                    for existing in config['load_balancers'])
        if not exists:
            config['load_balancers'].append({
                'name': lb['LoadBalancerName'],
                'arn': lb['LoadBalancerArn']
            })
    
    # Save config
    with open('/tmp/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    subprocess.run(['sudo', 'mv', '/tmp/config.yaml', '/opt/elb-ddos-defender/config.yaml'])
    subprocess.run(['sudo', 'systemctl', 'restart', 'elb-ddos-defender'])
    
    console.print(f"\n[bold green]✓ Added {len(selected_lbs)} load balancer(s) and restarted service![/bold green]")
    time.sleep(3)

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
            add_load_balancers()
        elif choice == "2":
            view_logs()
        elif choice == "3":
            check_status()
        elif choice == "4":
            view_config()
        elif choice == "5":
            restart_service()
        elif choice in ["r", "R"]:
            continue

if __name__ == "__main__":
    main()
