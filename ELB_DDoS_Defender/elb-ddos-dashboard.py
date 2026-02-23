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
    
    # Single comprehensive table
    metrics_table = Table(box=box.ROUNDED, show_header=True, padding=(0, 2))
    metrics_table.add_column("Metric", style="cyan", width=25)
    metrics_table.add_column("Value", style="bold green", width=20)
    
    metrics_table.add_row("📊 Total Packets", f"{metrics['total_packets']:,}")
    metrics_table.add_row("📈 Packets/sec", f"{metrics.get('packets_per_sec', 0):,}")
    metrics_table.add_row("🔗 Connections/sec", f"{metrics['connections_per_sec']:,}")
    metrics_table.add_row("💾 Total Traffic", format_bytes(metrics['total_bytes']))
    metrics_table.add_row("🌐 Unique IPs", f"{metrics['unique_ips']:,}")
    metrics_table.add_row("🔵 SYN Packets", f"{metrics['syn_packets']:,}")
    metrics_table.add_row("🟣 UDP Packets", f"{metrics['udp_packets']:,}")
    
    # Attacks section
    attacks = metrics.get('attacks_detected', [])
    recent_attacks = attacks[-5:] if attacks else []
    
    if recent_attacks:
        metrics_table.add_row("", "")  # Spacer
        metrics_table.add_row("⚠️  RECENT ATTACKS", f"{len(attacks)} total")
        for attack in recent_attacks:
            src = attack['source']
            dest = attack.get('destination', '')
            route = f"{src} → {dest}" if dest else src
            metrics_table.add_row(f"  {attack['type']}", f"{route} ({attack['value']}/s)")
    else:
        metrics_table.add_row("", "")
        metrics_table.add_row("✓ Status", "No attacks detected")
    
    return Panel(metrics_table, title="📡 Live Monitoring", border_style="cyan")

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
            # Get IPs quickly from ENI description search
            try:
                search_pattern = f"ELB*{lb['name']}*"
                result = subprocess.run([
                    "/usr/local/bin/aws", "ec2", "describe-network-interfaces",
                    "--filters", f"Name=description,Values={search_pattern}",
                    "--region", "us-east-1",
                    "--query", "NetworkInterfaces[*].PrivateIpAddress",
                    "--output", "json"
                ], capture_output=True, text=True, timeout=3)
                
                if result.returncode == 0:
                    import json
                    ips = json.loads(result.stdout)
                    ip_display = ", ".join(ips[:2]) + ("..." if len(ips) > 2 else "") if ips else "N/A"
                    eni_count = f"{len(ips)} ENIs" if ips else "?"
                    lb_table.add_row(str(i), lb.get('name', 'Unknown'), eni_count, ip_display, "✓ Active")
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
    menu.add_row("7", "Investigate Attacking IP (WHOIS/MTR)")
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
    
    # Ask if user wants to set up traffic mirroring
    console.print("\n[cyan]Would you like to set up VPC Traffic Mirroring now?[/cyan]")
    console.print("[dim]This will mirror traffic from the ELB ENIs to this instance for monitoring.[/dim]")
    setup_now = Prompt.ask("\nSet up traffic mirroring?", choices=["y", "n"], default="y")
    
    if setup_now.lower() == "y":
        setup_traffic_mirroring()
    else:
        console.print("\n[yellow]You can set up traffic mirroring later from the main menu (option 6)[/yellow]")
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
            table.add_column("Public IP", style="blue", width=18)
            
            if eni_result.returncode == 0:
                enis_data = json.loads(eni_result.stdout)
                enis = enis_data.get('NetworkInterfaces', [])
                if enis:
                    for eni in enis:
                        # Get public IP if exists
                        association = eni.get('Association', {})
                        public_ip = association.get('PublicIp', 'N/A')
                        
                        table.add_row(
                            eni.get('AvailabilityZone', 'N/A'),
                            eni.get('SubnetId', 'N/A'),
                            eni.get('NetworkInterfaceId', 'N/A'),
                            eni.get('PrivateIpAddress', 'N/A'),
                            public_ip
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
    
    config = load_config()
    lbs = config.get('load_balancers', [])
    
    if not lbs:
        console.print("[red]No load balancers configured. Add them first (option 1)[/red]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    console.print(f"[green]Found {len(lbs)} load balancer(s) to mirror[/green]\n")
    console.print("[dim]Press Enter to continue or Ctrl+C to cancel...[/dim]")
    input()
    
    try:
        # Get this instance's ENI using IMDSv2
        console.print("\n[cyan]Step 1: Getting defender instance ENI...[/cyan]")
        
        # Get instance ID from IMDS
        token_result = subprocess.run([
            "curl", "-X", "PUT", "-H", "X-aws-ec2-metadata-token-ttl-seconds: 21600",
            "http://169.254.169.254/latest/api/token"
        ], capture_output=True, text=True, timeout=5)
        
        if token_result.returncode == 0 and token_result.stdout:
            token = token_result.stdout.strip()
            instance_id_result = subprocess.run([
                "curl", "-H", f"X-aws-ec2-metadata-token: {token}",
                "http://169.254.169.254/latest/meta-data/instance-id"
            ], capture_output=True, text=True, timeout=5)
            instance_id = instance_id_result.stdout.strip()
        else:
            # Fallback: get from AWS CLI
            region_result = subprocess.run([
                "curl", "-s", "http://169.254.169.254/latest/meta-data/placement/region"
            ], capture_output=True, text=True, timeout=5)
            region = region_result.stdout.strip() or "us-east-1"
            
            # Get instance ID from tags or describe-instances
            instance_id_result = subprocess.run([
                "/usr/local/bin/aws", "ec2", "describe-instances",
                "--filters", "Name=instance-state-name,Values=running",
                "--region", region,
                "--query", "Reservations[0].Instances[0].InstanceId",
                "--output", "text"
            ], capture_output=True, text=True)
            instance_id = instance_id_result.stdout.strip()
        
        if not instance_id or instance_id == "None":
            console.print("[red]✗ Could not get instance ID[/red]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
            return
        
        console.print(f"[green]Instance ID: {instance_id}[/green]")
        
        eni_result = subprocess.run([
            "/usr/local/bin/aws", "ec2", "describe-instances",
            "--instance-ids", instance_id,
            "--region", "us-east-1",
            "--query", "Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId",
            "--output", "text"
        ], capture_output=True, text=True)
        
        defender_eni = eni_result.stdout.strip()
        
        if not defender_eni or defender_eni == "None":
            console.print("[red]✗ Could not get ENI for this instance[/red]")
            console.print(f"[dim]Error: {eni_result.stderr}[/dim]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
            return
            
        console.print(f"[green]✓ Defender ENI: {defender_eni}[/green]")
        
        # Create mirror target
        console.print("\n[cyan]Step 2: Creating VPC Traffic Mirror Target...[/cyan]")
        target_result = subprocess.run([
            "/usr/local/bin/aws", "ec2", "create-traffic-mirror-target",
            "--network-interface-id", defender_eni,
            "--description", "ELB DDoS Defender Mirror Target",
            "--region", "us-east-1",
            "--output", "json"
        ], capture_output=True, text=True)
        
        if target_result.returncode == 0:
            import json
            target_data = json.loads(target_result.stdout)
            target_id = target_data['TrafficMirrorTarget']['TrafficMirrorTargetId']
            console.print(f"[green]✓ Mirror Target created: {target_id}[/green]")
        else:
            # Check if already exists
            existing_result = subprocess.run([
                "/usr/local/bin/aws", "ec2", "describe-traffic-mirror-targets",
                "--filters", f"Name=network-interface-id,Values={defender_eni}",
                "--region", "us-east-1",
                "--query", "TrafficMirrorTargets[0].TrafficMirrorTargetId",
                "--output", "text"
            ], capture_output=True, text=True)
            target_id = existing_result.stdout.strip()
            if target_id and target_id != "None":
                console.print(f"[yellow]⚠ Using existing target: {target_id}[/yellow]")
            else:
                console.print(f"[red]✗ Failed to create mirror target[/red]")
                console.print(f"[dim]{target_result.stderr}[/dim]")
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
                return
        
        # Create mirror filter (all traffic)
        console.print("\n[cyan]Step 3: Creating Traffic Mirror Filter (all traffic)...[/cyan]")
        filter_result = subprocess.run([
            "/usr/local/bin/aws", "ec2", "create-traffic-mirror-filter",
            "--description", "ELB DDoS Defender - All Traffic",
            "--region", "us-east-1",
            "--output", "json"
        ], capture_output=True, text=True)
        
        if filter_result.returncode == 0:
            filter_data = json.loads(filter_result.stdout)
            filter_id = filter_data['TrafficMirrorFilter']['TrafficMirrorFilterId']
            console.print(f"[green]✓ Mirror Filter created: {filter_id}[/green]")
            
            # Add ingress rule (all traffic)
            subprocess.run([
                "/usr/local/bin/aws", "ec2", "create-traffic-mirror-filter-rule",
                "--traffic-mirror-filter-id", filter_id,
                "--traffic-direction", "ingress",
                "--rule-number", "100",
                "--rule-action", "accept",
                "--source-cidr-block", "0.0.0.0/0",
                "--destination-cidr-block", "0.0.0.0/0",
                "--region", "us-east-1"
            ], capture_output=True)
            
            # Add egress rule (all traffic)
            subprocess.run([
                "/usr/local/bin/aws", "ec2", "create-traffic-mirror-filter-rule",
                "--traffic-mirror-filter-id", filter_id,
                "--traffic-direction", "egress",
                "--rule-number", "100",
                "--rule-action", "accept",
                "--source-cidr-block", "0.0.0.0/0",
                "--destination-cidr-block", "0.0.0.0/0",
                "--region", "us-east-1"
            ], capture_output=True)
            
            console.print("[green]✓ Filter rules added (ingress + egress)[/green]")
        else:
            console.print(f"[red]✗ Failed to create mirror filter[/red]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
            return
        
        # Create mirror sessions for each LB ENI
        console.print(f"\n[cyan]Step 4: Creating Mirror Sessions for {len(lbs)} load balancer(s)...[/cyan]")
        sessions_created = 0
        
        for lb in lbs:
            console.print(f"\n[yellow]Processing {lb['name']}...[/yellow]")
            
            # Get ENIs for this LB
            search_pattern = f"ELB*{lb['name']}*"
            eni_result = subprocess.run([
                "/usr/local/bin/aws", "ec2", "describe-network-interfaces",
                "--filters", f"Name=description,Values={search_pattern}",
                "--region", "us-east-1",
                "--output", "json"
            ], capture_output=True, text=True)
            
            if eni_result.returncode == 0:
                enis_data = json.loads(eni_result.stdout)
                enis = enis_data.get('NetworkInterfaces', [])
                
                for eni in enis:
                    eni_id = eni['NetworkInterfaceId']
                    az = eni.get('AvailabilityZone', 'unknown')
                    
                    # Create mirror session
                    session_result = subprocess.run([
                        "/usr/local/bin/aws", "ec2", "create-traffic-mirror-session",
                        "--network-interface-id", eni_id,
                        "--traffic-mirror-target-id", target_id,
                        "--traffic-mirror-filter-id", filter_id,
                        "--session-number", str(100 + sessions_created),
                        "--description", f"Mirror {lb['name']} {az}",
                        "--region", "us-east-1",
                        "--output", "json"
                    ], capture_output=True, text=True)
                    
                    if session_result.returncode == 0:
                        session_data = json.loads(session_result.stdout)
                        session_id = session_data['TrafficMirrorSession']['TrafficMirrorSessionId']
                        console.print(f"  [green]✓ {eni_id} ({az}) → {session_id}[/green]")
                        sessions_created += 1
                    else:
                        console.print(f"  [red]✗ Failed: {eni_id}[/red]")
        
        console.print(f"\n[bold green]✓ Setup complete! Created {sessions_created} mirror session(s)[/bold green]")
        console.print("\n[cyan]Traffic from your load balancers is now being mirrored to this instance.[/cyan]")
        console.print("[yellow]Restarting service to switch from simulation to real capture...[/yellow]")
        
        subprocess.run(['sudo', 'systemctl', 'restart', 'elb-ddos-defender'])
        time.sleep(2)
        
        console.print("[green]✓ Service restarted - now capturing real traffic![/green]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def investigate_ip():
    """Investigate an attacking IP with WHOIS and MTR"""
    console.clear()
    console.print("[bold cyan]🔍 IP Investigation Tool[/bold cyan]\n")
    
    # Load recent attacks
    metrics = load_metrics()
    attacks = metrics.get('attacks_detected', [])
    
    if not attacks:
        console.print("[yellow]No attacks detected yet.[/yellow]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    # Show recent attacking IPs
    console.print("[bold]Recent Attacking IPs:[/bold]\n")
    unique_ips = {}
    for attack in attacks[-20:]:  # Last 20 attacks
        src = attack.get('source', 'unknown')
        if src != 'unknown' and src != 'multiple_sources':
            if src not in unique_ips:
                unique_ips[src] = {
                    'count': 0,
                    'type': attack.get('type'),
                    'dest': attack.get('destination', 'N/A')
                }
            unique_ips[src]['count'] += 1
    
    if not unique_ips:
        console.print("[yellow]No specific IPs found in recent attacks.[/yellow]")
        console.print("\n[dim]Press Enter to continue...[/dim]")
        input()
        return
    
    # Display IPs
    ip_table = Table(box=box.ROUNDED)
    ip_table.add_column("#", style="cyan")
    ip_table.add_column("IP Address", style="yellow")
    ip_table.add_column("Attack Type", style="red")
    ip_table.add_column("Count", style="magenta")
    ip_table.add_column("Target", style="blue")
    
    ip_list = list(unique_ips.items())
    for idx, (ip, info) in enumerate(ip_list, 1):
        ip_table.add_row(str(idx), ip, info['type'], str(info['count']), info['dest'])
    
    console.print(ip_table)
    console.print()
    
    # Prompt for IP selection
    choice = Prompt.ask("[bold]Enter IP number to investigate (or 'b' to go back)[/bold]")
    
    if choice.lower() == 'b':
        return
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(ip_list):
            console.print("[red]Invalid selection[/red]")
            time.sleep(2)
            return
        
        target_ip = ip_list[idx][0]
        console.clear()
        console.print(f"[bold cyan]🔍 Investigating {target_ip}[/bold cyan]\n")
        
        # WHOIS Lookup
        console.print("[bold yellow]═══ WHOIS Information ═══[/bold yellow]\n")
        try:
            result = subprocess.run(['whois', target_ip], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse key info
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['netname', 'orgname', 'country', 'descr', 'owner', 'inetnum', 'cidr']):
                        console.print(f"  {line.strip()}")
            else:
                console.print("[red]WHOIS lookup failed[/red]")
        except subprocess.TimeoutExpired:
            console.print("[red]WHOIS lookup timed out[/red]")
        except FileNotFoundError:
            console.print("[red]whois command not found (install with: yum install whois)[/red]")
        
        console.print()
        
        # MTR (My Traceroute)
        console.print("[bold yellow]═══ Network Route (MTR) ═══[/bold yellow]\n")
        console.print("[dim]Running traceroute (this may take 10-15 seconds)...[/dim]\n")
        try:
            result = subprocess.run(['mtr', '-r', '-c', '5', '-n', target_ip], 
                                   capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                console.print(result.stdout)
            else:
                console.print("[red]MTR failed[/red]")
        except subprocess.TimeoutExpired:
            console.print("[red]MTR timed out[/red]")
        except FileNotFoundError:
            console.print("[red]mtr command not found (install with: yum install mtr)[/red]")
        
        console.print()
        
        # DNS Reverse Lookup
        console.print("[bold yellow]═══ Reverse DNS ═══[/bold yellow]\n")
        try:
            result = subprocess.run(['dig', '+short', '-x', target_ip], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                console.print(f"  Hostname: {result.stdout.strip()}")
            else:
                console.print("  [dim]No reverse DNS record found[/dim]")
        except:
            console.print("  [dim]DNS lookup unavailable[/dim]")
        
    except ValueError:
        console.print("[red]Invalid input[/red]")
        time.sleep(2)
        return
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    console.print("\n[dim]Press Enter to continue...[/dim]")
    input()

def main():
    """Main dashboard loop"""
    while True:
        console.clear()
        layout = create_dashboard()
        console.print(layout)
        
        choice = Prompt.ask("[bold cyan]Select option[/bold cyan]", 
                           choices=["1", "2", "3", "4", "5", "6", "7", "r", "R", "q", "Q"],
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
        elif choice == "7":
            investigate_ip()
        elif choice in ["r", "R"]:
            continue

if __name__ == '__main__':
    main()
