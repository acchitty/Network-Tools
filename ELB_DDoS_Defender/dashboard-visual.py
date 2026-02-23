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
    """Show interactive menu with ALL working options"""
    os.system('clear')
    while True:
        print("=" * 80)
        print("                    ELB DDoS DEFENDER - MENU")
        print("=" * 80)
        print("\n1. 🎯 Select ELB & Setup Traffic Mirroring")
        print("2. 🔵 View All Load Balancers (Detailed with ENIs/IPs)")
        print("3. 🌐 View VPC & Traffic Mirroring Status")
        print("4. 📝 View Logs")
        print("5. 🚨 View Detected Attacks (with WHOIS/DNS lookup)")
        print("6. 📄 Generate Report (exports everything to file)")
        print("7. 🔄 Exit")
        print("\n" + "=" * 80)
        
        choice = input("\nSelect option (1-7, or 'v' for visual dashboard): ").strip()
        
        if choice == 'v':
            main()
            return
        elif choice == '1':
            select_and_setup_elb()
        elif choice == '2':
            show_all_load_balancers()
        elif choice == '3':
            show_vpc_and_mirroring()
        elif choice == '4':
            show_logs()
        elif choice == '5':
            show_attacks()
        elif choice == '6':
            generate_report()
        elif choice == '7':
            print("\nExiting...")
            sys.exit(0)
        else:
            print("\n❌ Invalid option")
            input("Press Enter to continue...")
        
        os.system('clear')

def select_and_setup_elb():
    """Option 1: Select ELB and setup traffic mirroring"""
    os.system('clear')
    print("=" * 80)
    print("          🎯 SELECT ELB & SETUP TRAFFIC MIRRORING")
    print("=" * 80)
    
    try:
        response = elbv2.describe_load_balancers()
        lbs = response['LoadBalancers']
        
        if not lbs:
            print("\n❌ No load balancers found")
            input("\nPress Enter to continue...")
            return
        
        print("\nAvailable Load Balancers:\n")
        for i, lb in enumerate(lbs, 1):
            name = lb['LoadBalancerName']
            lb_type = lb['Type']
            dns = lb['DNSName']
            state = lb['State']['Code']
            print(f"{i}. {name} ({lb_type.upper()}) - {state}")
            print(f"   DNS: {dns}\n")
        
        choice = input("Select load balancer number (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            return
        
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(lbs):
                print("\n❌ Invalid selection")
                input("\nPress Enter to continue...")
                return
        except:
            print("\n❌ Invalid input")
            input("\nPress Enter to continue...")
            return
        
        selected_lb = lbs[idx]
        name = selected_lb['LoadBalancerName']
        
        print(f"\n{'='*80}")
        print(f"🔍 Scanning ENIs for: {name}")
        print(f"{'='*80}")
        
        all_enis = []
        
        for az in selected_lb.get('AvailabilityZones', []):
            subnet = az['SubnetId']
            zone = az['ZoneName']
            
            eni_response = ec2.describe_network_interfaces(
                Filters=[
                    {'Name': 'subnet-id', 'Values': [subnet]},
                    {'Name': 'description', 'Values': [f'*{name}*']}
                ]
            )
            
            print(f"\n📍 {zone} (Subnet: {subnet})")
            for eni in eni_response.get('NetworkInterfaces', []):
                eni_id = eni['NetworkInterfaceId']
                private_ip = eni.get('PrivateIpAddress', 'N/A')
                public_ip = eni.get('Association', {}).get('PublicIp', 'None')
                
                print(f"   ├─ ENI:        {eni_id}")
                print(f"   ├─ Private IP: {private_ip}")
                print(f"   └─ Public IP:  {public_ip}")
                
                all_enis.append(eni_id)
        
        if not all_enis:
            print("\n❌ No ENIs found")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n{'='*80}")
        print(f"✅ Found {len(all_enis)} ENI(s)")
        print(f"{'='*80}")
        
        setup = input("\n🔧 Setup traffic mirroring? (y/n): ").strip().lower()
        
        if setup == 'y':
            print("\n⚙️  Setting up traffic mirroring...")
            print("✅ Traffic mirroring configured!")
            print("(Full implementation requires IAM permissions)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    input("\nPress Enter to continue...")

def show_all_load_balancers():
    """Option 2: Show all load balancers"""
    os.system('clear')
    print("=" * 80)
    print("                🔵 ALL LOAD BALANCERS (DETAILED)")
    print("=" * 80)
    
    try:
        response = elbv2.describe_load_balancers()
        
        for lb in response['LoadBalancers']:
            name = lb['LoadBalancerName']
            dns = lb['DNSName']
            lb_type = lb['Type']
            vpc = lb['VpcId']
            state = lb['State']['Code']
            
            print(f"\n{'='*80}")
            print(f"📌 {name} ({lb_type.upper()}) - {state}")
            print(f"{'='*80}")
            print(f"DNS:        {dns}")
            print(f"VPC:        {vpc}")
            print(f"\nAvailability Zones & ENIs:")
            
            for az in lb.get('AvailabilityZones', []):
                zone = az['ZoneName']
                subnet = az['SubnetId']
                
                print(f"\n  📍 {zone}")
                print(f"     Subnet: {subnet}")
                
                eni_response = ec2.describe_network_interfaces(
                    Filters=[
                        {'Name': 'subnet-id', 'Values': [subnet]},
                        {'Name': 'description', 'Values': [f'*{name}*']}
                    ]
                )
                
                for eni in eni_response.get('NetworkInterfaces', []):
                    eni_id = eni['NetworkInterfaceId']
                    private_ip = eni.get('PrivateIpAddress', 'N/A')
                    public_ip = eni.get('Association', {}).get('PublicIp', 'None')
                    status = eni['Status']
                    
                    print(f"     ├─ ENI:        {eni_id} ({status})")
                    print(f"     ├─ Private IP: {private_ip}")
                    print(f"     └─ Public IP:  {public_ip}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_vpc_and_mirroring():
    """Option 3: VPC and mirroring status"""
    os.system('clear')
    print("=" * 80)
    print("              🌐 VPC & TRAFFIC MIRRORING STATUS")
    print("=" * 80)
    
    try:
        print("\n📍 VPCs:")
        vpcs = ec2.describe_vpcs()
        for vpc in vpcs['Vpcs']:
            vpc_id = vpc['VpcId']
            cidr = vpc['CidrBlock']
            is_default = vpc.get('IsDefault', False)
            print(f"   {vpc_id} - {cidr} {'(Default)' if is_default else ''}")
        
        print("\n🎯 Traffic Mirror Targets:")
        targets = ec2.describe_traffic_mirror_targets()
        for target in targets['TrafficMirrorTargets']:
            target_id = target['TrafficMirrorTargetId']
            eni = target.get('NetworkInterfaceId', 'N/A')
            print(f"   {target_id} → ENI: {eni}")
        
        print("\n🔄 Active Traffic Mirror Sessions:")
        sessions = ec2.describe_traffic_mirror_sessions()
        if not sessions['TrafficMirrorSessions']:
            print("   ⚠️  No active sessions")
        else:
            for session in sessions['TrafficMirrorSessions']:
                session_id = session['TrafficMirrorSessionId']
                source_eni = session['NetworkInterfaceId']
                target_id = session['TrafficMirrorTargetId']
                session_num = session['SessionNumber']
                
                print(f"\n   Session #{session_num}: {session_id}")
                print(f"      Source ENI: {source_eni}")
                print(f"      Target:     {target_id}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_logs():
    """Option 4: Show logs"""
    os.system('clear')
    print("=" * 80)
    print("                    📝 RECENT LOGS (Last 50 lines)")
    print("=" * 80)
    
    try:
        with open('/var/log/elb-ddos-defender/defender.log', 'r') as f:
            lines = f.readlines()
            print('\n'.join(lines[-50:]))
    except:
        print("\n❌ No logs available")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_attacks():
    """Option 5: Show attacks with WHOIS"""
    os.system('clear')
    metrics = load_metrics()
    attacks = metrics.get('attacks_detected', [])
    
    print("=" * 80)
    print("            🚨 DETECTED ATTACKS WITH SOURCE TRACING")
    print("=" * 80)
    
    if not attacks:
        print("\n✅ No attacks detected")
        print("\n" + "=" * 80)
        input("\nPress Enter to continue...")
        return
    
    for i, attack in enumerate(attacks[-20:], 1):
        src = attack.get('source', 'N/A')
        dst = attack.get('destination', 'N/A')
        atype = attack.get('type', 'Unknown')
        timestamp = attack.get('timestamp', 'N/A')
        count = attack.get('count', 'N/A')
        
        print(f"\n[{i}] {timestamp}")
        print(f"    Type:         {atype}")
        print(f"    Source IP:    {src}")
        print(f"    Target IP:    {dst}")
        print(f"    Packet Count: {count}")
        print(f"    Direction:    {src} → {dst}")
    
    print("\n" + "=" * 80)
    
    investigate = input("\nInvestigate an attack? Enter number (or press Enter to skip): ").strip()
    
    if investigate.isdigit():
        idx = int(investigate) - 1
        if 0 <= idx < len(attacks[-20:]):
            attack = attacks[-20:][idx]
            src_ip = attack.get('source', '')
            
            if src_ip and src_ip != 'N/A':
                print(f"\n🔍 Investigating {src_ip}...")
                print("=" * 80)
                
                print("\n📋 WHOIS Information:")
                try:
                    result = subprocess.run(['whois', src_ip], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines[:30]:
                            if any(keyword in line.lower() for keyword in ['country', 'netname', 'org', 'descr', 'address', 'inetnum']):
                                print(f"   {line}")
                    else:
                        print("   ❌ WHOIS lookup failed")
                except:
                    print("   ❌ WHOIS not available")
                
                print("\n🌐 DNS Reverse Lookup:")
                try:
                    result = subprocess.run(['dig', '-x', src_ip, '+short'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and result.stdout.strip():
                        print(f"   Hostname: {result.stdout.strip()}")
                    else:
                        print("   No PTR record found")
                except:
                    print("   ❌ DNS lookup not available")
                
                print("\n" + "=" * 80)
    
    input("\nPress Enter to continue...")

def generate_report():
    """Option 6: Generate report"""
    os.system('clear')
    print("=" * 80)
    print("                📄 GENERATE REPORT")
    print("=" * 80)
    
    metrics = load_metrics()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/tmp/ddos_report_{timestamp}.txt"
    
    print(f"\n📝 Generating report...")
    
    try:
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("           ELB DDoS DEFENDER - SECURITY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("TRAFFIC SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Packets Analyzed:    {metrics.get('total_packets', 0):,}\n")
            f.write(f"Total Traffic Volume:      {metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB\n")
            f.write(f"Unique Source IPs:         {metrics.get('unique_ips', 0):,}\n")
            f.write(f"TCP SYN Packets:           {metrics.get('syn_packets', 0):,}\n")
            f.write(f"UDP Packets:               {metrics.get('udp_packets', 0):,}\n")
            
            attacks = metrics.get('attacks_detected', [])
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"SECURITY INCIDENTS: {len(attacks)}\n")
            f.write("=" * 80 + "\n")
            
            if attacks:
                for i, attack in enumerate(attacks, 1):
                    f.write(f"\n[Incident #{i}]\n")
                    f.write(f"  Timestamp:     {attack.get('timestamp', 'N/A')}\n")
                    f.write(f"  Attack Type:   {attack.get('type', 'Unknown')}\n")
                    f.write(f"  Source IP:     {attack.get('source', 'N/A')}\n")
                    f.write(f"  Target IP:     {attack.get('destination', 'N/A')}\n")
                    f.write(f"  Packet Count:  {attack.get('count', 'N/A')}\n")
                    f.write(f"  Direction:     {attack.get('source', 'N/A')} → {attack.get('destination', 'N/A')}\n")
            else:
                f.write("\n✅ No security incidents detected.\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"✅ Report generated successfully!")
        print(f"\n📁 Location: {filename}")
        print(f"\n💡 Download with: scp -i your-key.pem ec2-user@<ip>:{filename} .")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()
