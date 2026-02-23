#!/usr/bin/env python3
"""Full Featured Dashboard for ELB DDoS Defender"""
import json
import os
from datetime import datetime
import boto3

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

def show_load_balancers():
    """Show all load balancers with ENIs and IPs"""
    clear()
    print("=" * 80)
    print("                    🔵 LOAD BALANCERS")
    print("=" * 80)
    
    try:
        # Get ALBs
        response = elbv2.describe_load_balancers()
        
        for lb in response['LoadBalancers']:
            name = lb['LoadBalancerName']
            dns = lb['DNSName']
            lb_type = lb['Type']
            vpc = lb['VpcId']
            
            print(f"\n📌 {name} ({lb_type.upper()})")
            print(f"   DNS: {dns}")
            print(f"   VPC: {vpc}")
            print(f"   Availability Zones:")
            
            for az in lb.get('AvailabilityZones', []):
                zone = az['ZoneName']
                subnet = az['SubnetId']
                
                # Get ENI for this subnet
                eni_response = ec2.describe_network_interfaces(
                    Filters=[
                        {'Name': 'subnet-id', 'Values': [subnet]},
                        {'Name': 'description', 'Values': [f'*{name}*']}
                    ]
                )
                
                print(f"      {zone} (Subnet: {subnet})")
                for eni in eni_response.get('NetworkInterfaces', []):
                    eni_id = eni['NetworkInterfaceId']
                    private_ip = eni.get('PrivateIpAddress', 'N/A')
                    public_ip = eni.get('Association', {}).get('PublicIp', 'None')
                    
                    print(f"         ENI: {eni_id}")
                    print(f"         Private IP: {private_ip}")
                    print(f"         Public IP: {public_ip}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_vpc_info():
    """Show VPC and Traffic Mirroring info"""
    clear()
    print("=" * 80)
    print("                    🌐 VPC INFORMATION")
    print("=" * 80)
    
    try:
        # Get VPCs
        vpcs = ec2.describe_vpcs()
        for vpc in vpcs['Vpcs']:
            vpc_id = vpc['VpcId']
            cidr = vpc['CidrBlock']
            print(f"\n📍 VPC: {vpc_id}")
            print(f"   CIDR: {cidr}")
        
        # Get Traffic Mirror Sessions
        print("\n" + "=" * 80)
        print("                 🔍 TRAFFIC MIRROR SESSIONS")
        print("=" * 80)
        
        sessions = ec2.describe_traffic_mirror_sessions()
        for session in sessions['TrafficMirrorSessions']:
            session_id = session['TrafficMirrorSessionId']
            source_eni = session['NetworkInterfaceId']
            target_id = session['TrafficMirrorTargetId']
            
            print(f"\n🔄 Session: {session_id}")
            print(f"   Source ENI: {source_eni}")
            print(f"   Target: {target_id}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_logs():
    """Show recent logs"""
    clear()
    print("=" * 80)
    print("                    📝 RECENT LOGS")
    print("=" * 80)
    
    try:
        with open('/var/log/elb-ddos-defender/defender.log', 'r') as f:
            lines = f.readlines()
            print(''.join(lines[-50:]))
    except:
        print("\n❌ No logs available")
    
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
        print("\n1. 📊 View Live Metrics")
        print("2. 🔵 View Load Balancers (ENIs, IPs)")
        print("3. 🌐 View VPC & Traffic Mirroring")
        print("4. 📝 View Logs")
        print("5. 🚨 View Detected Attacks")
        print("6. 🔄 Exit")
        print("\n" + "=" * 80)
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            show_metrics()
        elif choice == '2':
            show_load_balancers()
        elif choice == '3':
            show_vpc_info()
        elif choice == '4':
            show_logs()
        elif choice == '5':
            show_attacks()
        elif choice == '6':
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
