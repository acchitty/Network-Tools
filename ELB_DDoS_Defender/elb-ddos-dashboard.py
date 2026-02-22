#!/usr/bin/env python3.11
"""Live ELB DDoS Defender Dashboard with Real-time Metrics"""
import time
import yaml
import json
import subprocess
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.layout import Layout
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

def load_config():
    try:
        with open('/opt/elb-ddos-defender/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except:
        return {}

def load_metrics():
    """Load real-time metrics from service"""
    try:
        with open('/var/log/elb-ddos-defender/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return {
            'total_packets': 0,
            'total_bytes': 0,
            'packets_per_sec': 0,
            'connections_per_sec': 0,
            'unique_ips': 0,
            'syn_packets': 0,
            'udp_packets': 0,
            'attacks_detected': []
        }

def format_bytes(bytes_val):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"

def create_metrics_panel(metrics):
    """Create real-time metrics display"""
    
    # Traffic metrics
    traffic_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    traffic_table.add_column("Metric", style="cyan")
    traffic_table.add_column("Value", style="bold green")
    
    traffic_table.add_row("📊 Total Packets", f"{metrics['total_packets']:,}")
    traffic_table.add_row("📈 Packets/sec", f"{metrics.get('packets_per_sec', 0):,}")
    traffic_table.add_row("🔗 Connections/sec", f"{metrics['connections_per_sec']:,}")
    traffic_table.add_row("💾 Total Traffic", format_bytes(metrics['total_bytes']))
    traffic_table.add_row("🌐 Unique IPs", f"{metrics['unique_ips']:,}")
    
    # Protocol breakdown
    protocol_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    protocol_table.add_column("Protocol", style="yellow")
    protocol_table.add_column("Count", style="bold")
    
    protocol_table.add_row("SYN Packets", f"{metrics['syn_packets']:,}")
    protocol_table.add_row("UDP Packets", f"{metrics['udp_packets']:,}")
    
    # Connection rate meter
    conn_rate = metrics['connections_per_sec']
    threshold = 1000
    conn_percent = min(100, (conn_rate / threshold) * 100)
    
    meter_bar = "█" * int(conn_percent / 5) + "░" * (20 - int(conn_percent / 5))
    meter_color = "green" if conn_rate < 500 else "yellow" if conn_rate < 800 else "red"
    
    meter_text = f"[{meter_color}]{meter_bar}[/{meter_color}] {conn_rate}/{threshold} conn/s"
    
    # Attacks
    attacks = metrics.get('attacks_detected', [])
    recent_attacks = attacks[-5:] if attacks else []
    
    attack_text = ""
    if recent_attacks:
        attack_text = "\n[bold red]⚠️  RECENT ATTACKS:[/bold red]\n"
        for attack in recent_attacks:
            attack_text += f"  • {attack['type']} from {attack['source']} ({attack['value']} conn/s)\n"
    else:
        attack_text = "\n[green]✓ No attacks detected[/green]"
    
    content = f"""[bold cyan]Real-time Traffic Metrics[/bold cyan]

{traffic_table}

[bold yellow]Protocol Analysis[/bold yellow]

{protocol_table}

[bold]Connection Rate Monitor[/bold]
{meter_text}

{attack_text}

[dim]Last updated: {metrics.get('timestamp', 'N/A')}[/dim]
"""
    
    return Panel(content, title="📡 Live Monitoring", border_style="cyan")

def create_dashboard():
    """Create main dashboard layout"""
    config = load_config()
    metrics = load_metrics()
    
    # Load balancers table with ENI info
    lb_table = Table(title="Monitored Load Balancers", box=box.ROUNDED, show_header=True)
    lb_table.add_column("#", style="cyan", width=5)
    lb_table.add_column("Name", style="green", width=25)
    lb_table.add_column("ENIs", style="yellow", width=15)
    lb_table.add_column("IPs", style="magenta", width=30)
    lb_table.add_column("Status", style="blue", width=12)
    
    lbs = config.get('load_balancers', [])
    if lbs:
        for i, lb in enumerate(lbs, 1):
            # Get ENI and IP info
            try:
                result = subprocess.run([
                    "/usr/local/bin/aws", "elbv2", "describe-load-balancers",
                    "--load-balancer-arns", lb['arn'],
                    "--region", "us-east-1",
                    "--query", "LoadBalancers[0].AvailabilityZones[*].[NetworkInterfaceId,LoadBalancerAddresses[0].IpAddress]",
                    "--output", "json"
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    eni_count = len(data) if data else 0
                    ips = [item[1] for item in data if item and len(item) > 1 and item[1]]
                    ip_display = ", ".join(ips[:2]) + ("..." if len(ips) > 2 else "")
                    lb_table.add_row(str(i), lb.get('name', 'Unknown'), f"{eni_count} ENIs", ip_display or "N/A", "✓ Active")
                else:
                    lb_table.add_row(str(i), lb.get('name', 'Unknown'), "?", "N/A", "✓ Active")
            except:
                lb_table.add_row(str(i), lb.get('name', 'Unknown'), "?", "N/A", "✓ Active")
    else:
        lb_table.add_row("-", "No load balancers configured", "-", "-", "⚠ Pending")
    
    # Menu
    menu = Table(title="Menu Options", box=box.ROUNDED, show_header=True, padding=(0, 2))
    menu.add_column("Key", style="cyan bold", width=8)
    menu.add_column("Action", style="white", width=40)
    
    menu.add_row("1", "Add Load Balancers to Monitor")
    menu.add_row("2", "View ENI Details for Load Balancers")
    menu.add_row("3", "View Service Logs")
    menu.add_row("4", "View Configuration")
    menu.add_row("5", "Restart Service")
    menu.add_row("6", "Setup VPC Traffic Mirroring")
    menu.add_row("R", "Refresh Dashboard")
    menu.add_row("Q", "Quit")
    
    # Layout
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"[bold cyan]ELB DDoS Defender - Live Dashboard[/bold cyan]\n[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]", 
                    border_style="blue"), size=3),
        Layout(lb_table, size=8),
        Layout(create_metrics_panel(metrics)),
        Layout(menu, size=12)
    )
    
    return layout

def add_load_balancers():
    console.clear()
    console.print("[bold cyan]Discover and Add Load Balancers[/bold cyan]\n")
    console.print("[yellow]Scanning for load balancers...[/yellow]\n")
    
    result = subprocess.run(["/usr/local/bin/aws", "elbv2", "describe-load-balancers", 
                            "--region", "us-east-1", "--output", "json"],
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        console.print("[red]Error: Could not fetch load balancers[/red]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    data = json.loads(result.stdout)
    lbs = data.get('LoadBalancers', [])
    
    if not lbs:
        console.print("[yellow]No load balancers found in region[/yellow]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    table = Table(title="Available Load Balancers", box=box.ROUNDED, show_header=True)
    table.add_column("#", style="cyan", width=5)
    table.add_column("Name", style="green", width=25)
    table.add_column("Type", style="yellow", width=15)
    table.add_column("State", style="magenta", width=15)
    
    for i, lb in enumerate(lbs, 1):
        lb_type = lb['Type'].upper()
        table.add_row(str(i), lb['LoadBalancerName'], lb_type, lb['State']['Code'])
    
    console.print(table)
    console.print()
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
    
    config = load_config()
    if 'load_balancers' not in config:
        config['load_balancers'] = []
    
    for lb in selected_lbs:
        exists = any(existing['arn'] == lb['LoadBalancerArn'] 
                    for existing in config['load_balancers'])
        if not exists:
            config['load_balancers'].append({
                'name': lb['LoadBalancerName'],
                'arn': lb['LoadBalancerArn']
            })
    
    with open('/tmp/config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    subprocess.run(['sudo', 'mv', '/tmp/config.yaml', '/opt/elb-ddos-defender/config.yaml'])
    subprocess.run(['sudo', 'systemctl', 'restart', 'elb-ddos-defender'])
    
    console.print(f"\n[bold green]✓ Added {len(selected_lbs)} load balancer(s) and restarted service![/bold green]")
    time.sleep(3)

def view_eni_details():
    """Show detailed ENI information for all load balancers"""
    console.clear()
    console.print("[bold cyan]Load Balancer ENI Details[/bold cyan]\n")
    
    config = load_config()
    lbs = config.get('load_balancers', [])
    
    if not lbs:
        console.print("[yellow]No load balancers configured[/yellow]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    for lb in lbs:
        console.print(f"\n[bold green]Load Balancer: {lb['name']}[/bold green]")
        console.print(f"[dim]ARN: {lb['arn']}[/dim]\n")
        
        # Get LB details
        result = subprocess.run([
            "/usr/local/bin/aws", "elbv2", "describe-load-balancers",
            "--load-balancer-arns", lb['arn'],
            "--region", "us-east-1",
            "--output", "json"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            lb_data = data['LoadBalancers'][0]
            vpc_id = lb_data.get('VpcId')
            azs = lb_data.get('AvailabilityZones', [])
            
            # Get ENIs for this LB by description pattern
            # ENI description format: "ELB app/ALBTest/e3f3f7cdb19c225e"
            search_pattern = f"ELB*{lb['name']}*"
            
            eni_result = subprocess.run([
                "/usr/local/bin/aws", "ec2", "describe-network-interfaces",
                "--filters", f"Name=description,Values={search_pattern}",
                "--region", "us-east-1",
                "--output", "json"
            ], capture_output=True, text=True)
            
            table = Table(box=box.SIMPLE, show_header=True)
            table.add_column("AZ", style="cyan", width=15)
            table.add_column("Subnet ID", style="yellow", width=25)
            table.add_column("ENI ID", style="green", width=25)
            table.add_column("Private IP", style="magenta", width=18)
            
            if eni_result.returncode == 0:
                enis_data = json.loads(eni_result.stdout)
                enis = enis_data.get('NetworkInterfaces', [])
                if enis:
                    for eni in enis:
                        table.add_row(
                            eni.get('AvailabilityZone', 'N/A'),
                            eni.get('SubnetId', 'N/A'),
                            eni.get('NetworkInterfaceId', 'N/A'),
                            eni.get('PrivateIpAddress', 'N/A')
                        )
                else:
                    # Fallback to AZ info
                    for az in azs:
                        table.add_row(
                            az.get('ZoneName', 'N/A'),
                            az.get('SubnetId', 'N/A'),
                            "Not found",
                            "N/A"
                        )
            else:
                for az in azs:
                    table.add_row(
                        az.get('ZoneName', 'N/A'),
                        az.get('SubnetId', 'N/A'),
                        "Error",
                        "N/A"
                    )
            
            console.print(table)
        else:
            console.print("[red]Error fetching ENI details[/red]")
    
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def view_logs():
    console.clear()
    console.print("[bold cyan]Service Logs (Ctrl+C to exit)[/bold cyan]\n")
    subprocess.run(['sudo', 'tail', '-f', '/var/log/elb-ddos-defender/defender.log'])

def view_config():
    console.clear()
    console.print("[bold cyan]Current Configuration[/bold cyan]\n")
    subprocess.run(['cat', '/opt/elb-ddos-defender/config.yaml'])
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def restart_service():
    console.clear()
    console.print("[yellow]Restarting service...[/yellow]")
    subprocess.run(['sudo', 'systemctl', 'restart', 'elb-ddos-defender'])
    time.sleep(2)
    console.print("[green]✓ Service restarted[/green]")
    time.sleep(2)

def setup_traffic_mirroring():
    console.clear()
    console.print("[bold cyan]VPC Traffic Mirroring Setup[/bold cyan]\n")
    console.print("[yellow]This will configure traffic mirroring from your ELBs to this instance[/yellow]\n")
    console.print("[dim]Press Enter to continue or Ctrl+C to cancel...[/dim]")
    input()
    console.print("\n[red]Feature coming soon - requires AWS permissions[/red]")
    time.sleep(3)

def main():
    """Main dashboard loop"""
    while True:
        console.clear()
        layout = create_dashboard()
        console.print(layout)
        
        choice = Prompt.ask("[bold cyan]Select option[/bold cyan]", 
                           choices=["1", "2", "3", "4", "5", "6", "r", "R", "q", "Q"],
                           default="r")
        
        if choice in ["q", "Q"]:
            console.clear()
            console.print("\n[bold yellow]Dashboard closed.[/bold yellow]\n")
            break
        elif choice == "1":
            add_load_balancers()
        elif choice == "2":
            view_eni_details()
        elif choice == "3":
            view_logs()
        elif choice == "4":
            view_config()
        elif choice == "5":
            restart_service()
        elif choice == "6":
            setup_traffic_mirroring()
        elif choice in ["r", "R"]:
            continue

if __name__ == '__main__':
    main()
