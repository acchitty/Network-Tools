#!/usr/bin/env python3
"""Simple working dashboard for ELB DDoS Defender"""
import json
import time
import os
from datetime import datetime

def clear_screen():
    os.system('clear')

def load_metrics():
    try:
        with open('/var/log/elb-ddos-defender/metrics.json', 'r') as f:
            return json.load(f)
    except:
        return None

def display_dashboard():
    while True:
        clear_screen()
        metrics = load_metrics()
        
        print("=" * 80)
        print("                    ELB DDoS DEFENDER - LIVE MONITOR")
        print("=" * 80)
        print()
        
        if not metrics:
            print("⚠️  No metrics available yet. Service may be starting...")
            time.sleep(2)
            continue
        
        # Main Stats
        print("📊 TRAFFIC STATISTICS")
        print("-" * 80)
        print(f"  Total Packets:        {metrics.get('total_packets', 0):,}")
        print(f"  Total Traffic:        {metrics.get('total_bytes', 0) / 1024 / 1024:.2f} MB")
        print(f"  Unique IPs:           {metrics.get('unique_ips', 0):,}")
        print(f"  Packets/sec:          {metrics.get('packets_per_sec', 0)}")
        print(f"  Connections/sec:      {metrics.get('connections_per_sec', 0)}")
        print()
        
        # Protocol Stats
        print("🔵 PROTOCOL BREAKDOWN")
        print("-" * 80)
        print(f"  SYN Packets:          {metrics.get('syn_packets', 0):,}")
        print(f"  UDP Packets:          {metrics.get('udp_packets', 0):,}")
        print()
        
        # Attacks
        attacks = metrics.get('attacks_detected', [])
        print(f"🚨 ATTACKS DETECTED: {len(attacks)}")
        print("-" * 80)
        if attacks:
            for attack in attacks[-5:]:  # Show last 5
                print(f"  [{attack.get('timestamp', 'N/A')}]")
                print(f"    Type: {attack.get('type', 'Unknown')}")
                print(f"    From: {attack.get('source', 'N/A')} → To: {attack.get('destination', 'N/A')}")
                print()
        else:
            print("  ✅ No attacks detected")
        print()
        
        # Footer
        print("-" * 80)
        print(f"Last Updated: {metrics.get('timestamp', 'N/A')}")
        print("Press Ctrl+C to exit")
        print("=" * 80)
        
        time.sleep(2)

if __name__ == '__main__':
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n\nExiting dashboard...")
