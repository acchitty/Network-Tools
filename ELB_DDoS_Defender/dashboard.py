#!/usr/bin/env python3
"""Enhanced Dashboard - Interactive ELB Selection & Traffic Mirror Setup"""
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
        return {'total_packets': 0, 'unique_ips': 0, 'attacks_detected': []}

# AWS clients
elbv2 = boto3.client('elbv2', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')

def get_instance_eni():
    """Get this instance's ENI for mirror target"""
    try:
        response = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Find the defender instance (has our security group)
                for eni in instance.get('NetworkInterfaces', []):
                    return eni['NetworkInterfaceId']
    except:
        pass
    return None

def setup_traffic_mirror(source_enis):
    """Setup traffic mirroring for selected ENIs"""
    clear()
    print("=" * 80)
    print("                🔧 SETTING UP TRAFFIC MIRRORING")
    print("=" * 80)
    
    # Get or create mirror target
    target_eni = get_instance_eni()
    if not target_eni:
        print("\n❌ Could not find defender instance ENI")
        input("\nPress Enter to continue...")
        return
    
    print(f"\n✓ Defender ENI: {target_eni}")
    
    # Check for existing target
    try:
        targets = ec2.describe_traffic_mirror_targets()
        target_id = None
        for target in targets['TrafficMirrorTargets']:
            if target.get('NetworkInterfaceId') == target_eni:
                target_id = target['TrafficMirrorTargetId']
                print(f"✓ Using existing mirror target: {target_id}")
                break
        
        if not target_id:
            # Create new target
            response = ec2.create_traffic_mirror_target(
                NetworkInterfaceId=target_eni,
                Description='ELB DDoS Defender Target'
            )
            target_id = response['TrafficMirrorTarget']['TrafficMirrorTargetId']
            print(f"✓ Created mirror target: {target_id}")
    except Exception as e:
        print(f"❌ Error creating target: {e}")
        input("\nPress Enter to continue...")
        return
    
    # Get or create filter
    try:
        filters = ec2.describe_traffic_mirror_filters()
        filter_id = None
        if filters['TrafficMirrorFilters']:
            filter_id = filters['TrafficMirrorFilters'][0]['TrafficMirrorFilterId']
            print(f"✓ Using existing filter: {filter_id}")
        else:
            # Create filter
            response = ec2.create_traffic_mirror_filter(
                Description='ELB DDoS Defender Filter'
            )
            filter_id = response['TrafficMirrorFilter']['TrafficMirrorFilterId']
            
            # Add rules
            ec2.create_traffic_mirror_filter_rule(
                TrafficMirrorFilterId=filter_id,
                TrafficDirection='ingress',
                RuleNumber=100,
                RuleAction='accept',
                Protocol=0,
                SourceCidrBlock='0.0.0.0/0',
                DestinationCidrBlock='0.0.0.0/0'
            )
            print(f"✓ Created filter: {filter_id}")
    except Exception as e:
        print(f"❌ Error creating filter: {e}")
        input("\nPress Enter to continue...")
        return
    
    # Create sessions for each ENI
    print(f"\n📡 Creating mirror sessions for {len(source_enis)} ENIs...")
    session_num = 1
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
            print(f"  ✓ Session {session_num}: {session_id} (ENI: {eni})")
            session_num += 1
        except Exception as e:
            if 'already exists' in str(e):
                print(f"  ⚠ Session already exists for {eni}")
            else:
                print(f"  ❌ Error for {eni}: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Traffic mirroring setup complete!")
    print("Packets from selected ELB ENIs are now being mirrored to this instance.")
    input("\nPress Enter to continue...")

def select_and_monitor_elb():
    """Interactive ELB selection"""
    clear()
    print("=" * 80)
    print("              🎯 SELECT LOAD BALANCER TO MONITOR")
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
            print(f"{i}. {name} ({lb_type.upper()})")
            print(f"   DNS: {dns}")
            print()
        
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
        print(f"\n🔍 Scanning ENIs for {name}...")
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
            
            print(f"\n  📍 {zone} (Subnet: {subnet})")
            for eni in eni_response.get('NetworkInterfaces', []):
                eni_id = eni['NetworkInterfaceId']
                private_ip = eni.get('PrivateIpAddress', 'N/A')
                public_ip = eni.get('Association', {}).get('PublicIp', 'None')
                
                print(f"     ENI: {eni_id}")
                print(f"     Private IP: {private_ip}")
                print(f"     Public IP: {public_ip}")
                
                all_enis.append(eni_id)
        
        if not all_enis:
            print("\n❌ No ENIs found for this load balancer")
            input("\nPress Enter to continue...")
            return
        
        print(f"\n✅ Found {len(all_enis)} ENI(s)")
        
        # Ask to setup mirroring
        setup = input("\nSetup traffic mirroring for these ENIs? (y/n): ").strip().lower()
        
        if setup == 'y':
            setup_traffic_mirror(all_enis)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("\nPress Enter to continue...")

def show_metrics():
    """Display live metrics"""
    clear()
    metrics = load_metrics()
    print("=" * 80)
    print("                    📊 LIVE METRICS")
    print("=" * 80)
    print(f"Total Packets:        {metrics.get('total_packets', 0):,}")
    print(f"Total Traffic:        {metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB")
    print(f"Unique IPs:           {metrics.get('unique_ips', 0):,}")
    print(f"SYN Packets:          {metrics.get('syn_packets', 0):,}")
    print(f"UDP Packets:          {metrics.get('udp_packets', 0):,}")
    print(f"Attacks Detected:     {len(metrics.get('attacks_detected', []))}")
    print("=" * 80)
    input("\nPress Enter to continue...")

def show_attacks():
    """Show detected attacks"""
    clear()
    metrics = load_metrics()
    attacks = metrics.get('attacks_detected', [])
    
    print("=" * 80)
    print("                    🚨 DETECTED ATTACKS")
    print("=" * 80)
    
    if not attacks:
        print("\n✅ No attacks detected")
    else:
        for i, attack in enumerate(attacks[-20:], 1):
            print(f"\n[{i}] {attack.get('timestamp', 'N/A')}")
            print(f"    Type: {attack.get('type', 'Unknown')}")
            print(f"    Source: {attack.get('source', 'N/A')}")
            print(f"    Target: {attack.get('destination', 'N/A')}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def main_menu():
    """Main menu"""
    while True:
        clear()
        print("=" * 80)
        print("                    ELB DDoS DEFENDER")
        print("=" * 80)
        print("\n1. 🎯 Select & Monitor Load Balancer (Setup Traffic Mirror)")
        print("2. 📊 View Live Metrics")
        print("3. 🚨 View Detected Attacks")
        print("4. 🔄 Exit")
        print("\n" + "=" * 80)
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            select_and_monitor_elb()
        elif choice == '2':
            show_metrics()
        elif choice == '3':
            show_attacks()
        elif choice == '4':
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
