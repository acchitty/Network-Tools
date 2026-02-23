#!/usr/bin/env python3
"""Full Featured Dashboard for ELB DDoS Defender"""
import json
import subprocess
import os
from datetime import datetime

def clear():
    os.system('clear')

def load_metrics():
    try:
        with open('/var/log/elb-ddos-defender/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return {'total_packets': 0, 'unique_ips': 0, 'attacks_detected': []}

def run_aws(cmd):
    """Run AWS CLI command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout) if result.stdout else {}
    return {}

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
    
    # Get ALBs
    albs = run_aws('/usr/bin/aws elbv2 describe-load-balancers --region us-east-1')
    
    for lb in albs.get('LoadBalancers', []):
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
            enis = run_aws(f'/usr/bin/aws ec2 describe-network-interfaces --region us-east-1 --filters "Name=subnet-id,Values={subnet}" "Name=description,Values=*{name}*"')
            
            print(f"      {zone} (Subnet: {subnet})")
            for eni in enis.get('NetworkInterfaces', []):
                eni_id = eni['NetworkInterfaceId']
                private_ip = eni.get('PrivateIpAddress', 'N/A')
                public_ip = eni.get('Association', {}).get('PublicIp', 'None')
                
                print(f"         ENI: {eni_id}")
                print(f"         Private IP: {private_ip}")
                print(f"         Public IP: {public_ip}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_vpc_info():
    """Show VPC and Traffic Mirroring info"""
    clear()
    print("=" * 80)
    print("                    🌐 VPC INFORMATION")
    print("=" * 80)
    
    # Get VPCs
    vpcs = run_aws('/usr/bin/aws ec2 describe-vpcs --region us-east-1')
    for vpc in vpcs.get('Vpcs', []):
        vpc_id = vpc['VpcId']
        cidr = vpc['CidrBlock']
        print(f"\n📍 VPC: {vpc_id}")
        print(f"   CIDR: {cidr}")
    
    # Get Traffic Mirror Sessions
    print("\n" + "=" * 80)
    print("                 🔍 TRAFFIC MIRROR SESSIONS")
    print("=" * 80)
    
    sessions = run_aws('/usr/bin/aws ec2 describe-traffic-mirror-sessions --region us-east-1')
    for session in sessions.get('TrafficMirrorSessions', []):
        session_id = session['TrafficMirrorSessionId']
        source_eni = session['NetworkInterfaceId']
        target_id = session['TrafficMirrorTargetId']
        
        print(f"\n🔄 Session: {session_id}")
        print(f"   Source ENI: {source_eni}")
        print(f"   Target: {target_id}")
    
    print("\n" + "=" * 80)
    input("\nPress Enter to continue...")

def show_logs():
    """Show recent logs"""
    clear()
    print("=" * 80)
    print("                    📝 RECENT LOGS")
    print("=" * 80)
    
    result = subprocess.run(['tail', '-50', '/var/log/elb-ddos-defender/defender.log'], 
                          capture_output=True, text=True)
    print(result.stdout if result.returncode == 0 else "No logs available")
    
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
