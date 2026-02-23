#!/usr/bin/env python3
"""COMPLETE ELB DDoS Defender Dashboard - ALL FEATURES"""
import json
import os
import boto3
from datetime import datetime

def clear():
    os.system('clear')

def load_metrics():
    try:
        with open('/var/log/elb-ddos-defender/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return {'total_packets': 0, 'unique_ips': 0, 'attacks_detected': [], 'total_bytes': 0, 'syn_packets': 0, 'udp_packets': 0}

# AWS clients
elbv2 = boto3.client('elbv2', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

def show_metrics():
    """Display live metrics with auto-refresh"""
    import time
    import subprocess
    
    print("\n🔴 Starting Live Monitor (Press Ctrl+C to exit)...\n")
    time.sleep(2)
    
    try:
        while True:
            clear()
            metrics = load_metrics()
            print("=" * 80)
            print("              📊 LIVE METRICS (Auto-Refresh Every 2s)")
            print("=" * 80)
            print(f"\n📦 TRAFFIC STATISTICS")
            print(f"   Total Packets:        {metrics.get('total_packets', 0):,}")
            print(f"   Total Traffic:        {metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB")
            print(f"   Unique IPs:           {metrics.get('unique_ips', 0):,}")
            print(f"   Packets/sec:          {metrics.get('packets_per_sec', 0)}")
            print(f"   Connections/sec:      {metrics.get('connections_per_sec', 0)}")
            
            print(f"\n🔵 PROTOCOL BREAKDOWN")
            print(f"   TCP SYN Packets:      {metrics.get('syn_packets', 0):,}")
            print(f"   UDP Packets:          {metrics.get('udp_packets', 0):,}")
            
            attacks = metrics.get('attacks_detected', [])
            print(f"\n🚨 ATTACKS DETECTED: {len(attacks)}")
            if attacks:
                print(f"\n   Recent Attacks:")
                for attack in attacks[-5:]:
                    src = attack.get('source', 'N/A')
                    dst = attack.get('destination', 'N/A')
                    atype = attack.get('type', 'Unknown')
                    print(f"   • {atype}: {src} → {dst}")
            else:
                print(f"   ✅ No attacks detected")
            
            print(f"\n⏰ Last Updated: {metrics.get('timestamp', 'N/A')}")
            print("=" * 80)
            print("\nPress Ctrl+C to return to menu")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nReturning to menu...")
        time.sleep(1)

def show_all_load_balancers():
    """Show ALL load balancers with complete details"""
    clear()
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
                
                # Get ENIs
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
    """Show VPC info and traffic mirroring status"""
    clear()
    print("=" * 80)
    print("              🌐 VPC & TRAFFIC MIRRORING STATUS")
    print("=" * 80)
    
    try:
        # VPCs
        print("\n📍 VPCs:")
        vpcs = ec2.describe_vpcs()
        for vpc in vpcs['Vpcs']:
            vpc_id = vpc['VpcId']
            cidr = vpc['CidrBlock']
            is_default = vpc.get('IsDefault', False)
            print(f"   {vpc_id} - {cidr} {'(Default)' if is_default else ''}")
        
        # Traffic Mirror Targets
        print("\n🎯 Traffic Mirror Targets:")
        targets = ec2.describe_traffic_mirror_targets()
        for target in targets['TrafficMirrorTargets']:
            target_id = target['TrafficMirrorTargetId']
            eni = target.get('NetworkInterfaceId', 'N/A')
            print(f"   {target_id} → ENI: {eni}")
        
        # Traffic Mirror Filters
        print("\n🔍 Traffic Mirror Filters:")
        filters = ec2.describe_traffic_mirror_filters()
        for filt in filters['TrafficMirrorFilters']:
            filter_id = filt['TrafficMirrorFilterId']
            print(f"   {filter_id}")
        
        # Traffic Mirror Sessions
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
    """Show recent logs"""
    clear()
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
    """Show detected attacks with WHOIS lookup"""
    import subprocess
    
    clear()
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
    
    # Show attacks
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
    
    # Ask to investigate
    investigate = input("\nInvestigate an attack? Enter number (or press Enter to skip): ").strip()
    
    if investigate.isdigit():
        idx = int(investigate) - 1
        if 0 <= idx < len(attacks[-20:]):
            attack = attacks[-20:][idx]
            src_ip = attack.get('source', '')
            
            if src_ip and src_ip != 'N/A':
                print(f"\n🔍 Investigating {src_ip}...")
                print("=" * 80)
                
                # WHOIS lookup
                print("\n📋 WHOIS Information:")
                try:
                    result = subprocess.run(['whois', src_ip], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        # Show relevant lines
                        for line in lines[:30]:
                            if any(keyword in line.lower() for keyword in ['country', 'netname', 'org', 'descr', 'address', 'inetnum']):
                                print(f"   {line}")
                    else:
                        print("   ❌ WHOIS lookup failed")
                except:
                    print("   ❌ WHOIS not available")
                
                # DNS lookup
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

def select_and_setup_elb():
    """Interactive ELB selection with automatic traffic mirror setup"""
    clear()
    print("=" * 80)
    print("          🎯 SELECT ELB & SETUP TRAFFIC MIRRORING")
    print("=" * 80)
    
    try:
        # Get all load balancers
        response = elbv2.describe_load_balancers()
        lbs = response['LoadBalancers']
        
        if not lbs:
            print("\n❌ No load balancers found")
            input("\nPress Enter to continue...")
            return
        
        # Display list
        print("\nAvailable Load Balancers:\n")
        for i, lb in enumerate(lbs, 1):
            name = lb['LoadBalancerName']
            lb_type = lb['Type']
            dns = lb['DNSName']
            state = lb['State']['Code']
            print(f"{i}. {name} ({lb_type.upper()}) - {state}")
            print(f"   DNS: {dns}\n")
        
        # Get selection
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
        
        # Scan for ENIs
        print(f"\n{'='*80}")
        print(f"🔍 Scanning ENIs for: {name}")
        print(f"{'='*80}")
        
        all_enis = []
        
        for az in selected_lb.get('AvailabilityZones', []):
            subnet = az['SubnetId']
            zone = az['ZoneName']
            
            # Get ENIs
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
            print("\n❌ No ENIs found for this load balancer")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n{'='*80}")
        print(f"✅ Found {len(all_enis)} ENI(s)")
        print(f"{'='*80}")
        
        # Ask to setup mirroring
        setup = input("\n🔧 Setup traffic mirroring for these ENIs? (y/n): ").strip().lower()
        
        if setup == 'y':
            setup_traffic_mirror(all_enis)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("\nPress Enter to continue...")

def setup_traffic_mirror(source_enis):
    """Setup traffic mirroring for selected ENIs"""
    print("\n" + "=" * 80)
    print("           🔧 CONFIGURING TRAFFIC MIRRORING")
    print("=" * 80)
    
    # Get this instance's ENI
    print("\n[1/4] Finding defender instance ENI...")
    try:
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        target_eni = None
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for eni in instance.get('NetworkInterfaces', []):
                    # Use first ENI found
                    target_eni = eni['NetworkInterfaceId']
                    break
                if target_eni:
                    break
            if target_eni:
                break
        
        if not target_eni:
            print("   ❌ Could not find defender instance ENI")
            input("\nPress Enter to continue...")
            return
        
        print(f"   ✓ Defender ENI: {target_eni}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        input("\nPress Enter to continue...")
        return
    
    # Get or create mirror target
    print("\n[2/4] Setting up mirror target...")
    try:
        targets = ec2.describe_traffic_mirror_targets()
        target_id = None
        for target in targets['TrafficMirrorTargets']:
            if target.get('NetworkInterfaceId') == target_eni:
                target_id = target['TrafficMirrorTargetId']
                print(f"   ✓ Using existing target: {target_id}")
                break
        
        if not target_id:
            response = ec2.create_traffic_mirror_target(
                NetworkInterfaceId=target_eni,
                Description='ELB DDoS Defender Target'
            )
            target_id = response['TrafficMirrorTarget']['TrafficMirrorTargetId']
            print(f"   ✓ Created new target: {target_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        input("\nPress Enter to continue...")
        return
    
    # Get or create filter
    print("\n[3/4] Setting up mirror filter...")
    try:
        filters = ec2.describe_traffic_mirror_filters()
        filter_id = None
        if filters['TrafficMirrorFilters']:
            filter_id = filters['TrafficMirrorFilters'][0]['TrafficMirrorFilterId']
            print(f"   ✓ Using existing filter: {filter_id}")
        else:
            response = ec2.create_traffic_mirror_filter(
                Description='ELB DDoS Defender Filter - All Traffic'
            )
            filter_id = response['TrafficMirrorFilter']['TrafficMirrorFilterId']
            
            # Add rule to accept all traffic
            ec2.create_traffic_mirror_filter_rule(
                TrafficMirrorFilterId=filter_id,
                TrafficDirection='ingress',
                RuleNumber=100,
                RuleAction='accept',
                Protocol=0,
                SourceCidrBlock='0.0.0.0/0',
                DestinationCidrBlock='0.0.0.0/0'
            )
            print(f"   ✓ Created new filter: {filter_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        input("\nPress Enter to continue...")
        return
    
    # Create sessions
    print(f"\n[4/4] Creating mirror sessions for {len(source_enis)} ENI(s)...")
    session_num = 1
    success_count = 0
    
    for eni in source_enis:
        try:
            response = ec2.create_traffic_mirror_session(
                TrafficMirrorTargetId=target_id,
                TrafficMirrorFilterId=filter_id,
                NetworkInterfaceId=eni,
                SessionNumber=session_num,
                Description=f'ELB ENI {eni}'
            )
            session_id = response['TrafficMirrorSession']['TrafficMirrorSessionId']
            print(f"   ✓ Session {session_num}: {session_id}")
            print(f"      Source: {eni}")
            success_count += 1
            session_num += 1
        except Exception as e:
            if 'already exists' in str(e):
                print(f"   ⚠  Session already exists for {eni}")
                success_count += 1
            else:
                print(f"   ❌ Failed for {eni}: {e}")
    
    print("\n" + "=" * 80)
    print(f"✅ Traffic mirroring setup complete!")
    print(f"   {success_count}/{len(source_enis)} ENIs configured successfully")
    print(f"\n💡 Packets from selected ELB ENIs are now being mirrored.")
    print(f"   Check 'View Live Metrics' to see captured traffic.")
    print("=" * 80)
    input("\nPress Enter to continue...")

def generate_report():
    """Generate comprehensive report"""
    clear()
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
            f.write(f"Report Period: Last monitoring session\n")
            
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
                f.write("\n✅ No security incidents detected during monitoring period.\n")
            
            # Load balancer info
            f.write("\n" + "=" * 80 + "\n")
            f.write("MONITORED LOAD BALANCERS\n")
            f.write("=" * 80 + "\n")
            
            try:
                response = elbv2.describe_load_balancers()
                for lb in response['LoadBalancers']:
                    f.write(f"\nLoad Balancer: {lb['LoadBalancerName']}\n")
                    f.write(f"  Type: {lb['Type']}\n")
                    f.write(f"  DNS:  {lb['DNSName']}\n")
                    f.write(f"  VPC:  {lb['VpcId']}\n")
            except:
                f.write("\nUnable to retrieve load balancer information.\n")
            
            # Traffic mirroring status
            f.write("\n" + "=" * 80 + "\n")
            f.write("TRAFFIC MIRRORING STATUS\n")
            f.write("=" * 80 + "\n")
            
            try:
                sessions = ec2.describe_traffic_mirror_sessions()
                f.write(f"\nActive Mirror Sessions: {len(sessions['TrafficMirrorSessions'])}\n")
                for session in sessions['TrafficMirrorSessions']:
                    f.write(f"\n  Session: {session['TrafficMirrorSessionId']}\n")
                    f.write(f"    Source ENI: {session['NetworkInterfaceId']}\n")
                    f.write(f"    Target:     {session['TrafficMirrorTargetId']}\n")
            except:
                f.write("\nUnable to retrieve traffic mirroring status.\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"✅ Report generated successfully!")
        print(f"\n📁 Location: {filename}")
        print(f"\n💡 You can download this file using:")
        print(f"   scp -i your-key.pem ec2-user@<instance-ip>:{filename} .")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def main_menu():
    """Main menu with all options"""
    while True:
        clear()
        print("=" * 80)
        print("                    ELB DDoS DEFENDER")
        print("                   COMPLETE DASHBOARD")
        print("=" * 80)
        print("\n1. 🎯 Select ELB & Setup Traffic Mirroring")
        print("2. 📊 View Live Metrics (Auto-Refresh)")
        print("3. 🔵 View All Load Balancers (Detailed)")
        print("4. 🌐 View VPC & Traffic Mirroring Status")
        print("5. 📝 View Logs")
        print("6. 🚨 View Detected Attacks (with WHOIS)")
        print("7. 📄 Generate Report")
        print("8. 🔄 Exit")
        print("\n" + "=" * 80)
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            select_and_setup_elb()
        elif choice == '2':
            show_metrics()
        elif choice == '3':
            show_all_load_balancers()
        elif choice == '4':
            show_vpc_and_mirroring()
        elif choice == '5':
            show_logs()
        elif choice == '6':
            show_attacks()
        elif choice == '7':
            generate_report()
        elif choice == '8':
            print("\nExiting...")
            break
        else:
            print("\n❌ Invalid option")
            input("Press Enter to continue...")

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nExiting...")
