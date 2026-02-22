"""
PCAP Capture SDK using tcpdump and tshark
"""
import subprocess
import os
from datetime import datetime

class PCAPCaptureSDK:
    def __init__(self, pcap_dir="/var/log/pcaps"):
        self.pcap_dir = pcap_dir
        os.makedirs(pcap_dir, exist_ok=True)
        self.background_capture = None
    
    def start_background_capture(self):
        """Start continuous tcpdump capture with hourly rotation"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        pcap_pattern = f"{self.pcap_dir}/continuous-%Y%m%d-%H%M%S.pcap"
        
        cmd = [
            'tcpdump',
            '-i', 'eth0',
            '-w', pcap_pattern,
            '-G', '3600',      # Rotate every hour
            '-W', '24',        # Keep 24 files (24 hours)
            '-Z', 'root',
            '-s', '0',         # Capture full packets
            'udp port 4789'    # VXLAN traffic
        ]
        
        self.background_capture = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return self.background_capture.pid
    
    def start_attack_capture(self, ip, duration=300, pcap_file=None):
        """Start targeted tcpdump capture for specific attacker IP"""
        if not pcap_file:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            pcap_file = f"{self.pcap_dir}/attack-{ip.replace('.', '-')}-{timestamp}.pcap"
        
        cmd = [
            'tcpdump',
            '-i', 'eth0',
            '-w', pcap_file,
            '-G', str(duration),
            '-W', '1',
            '-s', '0',
            f'host {ip}'
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return pcap_file
    
    def analyze_with_tshark(self, pcap_file):
        """Analyze PCAP with tshark"""
        if not os.path.exists(pcap_file):
            return {"error": "PCAP file not found"}
        
        analyses = {}
        
        try:
            # Get protocol hierarchy
            cmd = ['tshark', '-r', pcap_file, '-q', '-z', 'io,phs']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            analyses['protocol_hierarchy'] = result.stdout
            
            # Get TCP conversations
            cmd = ['tshark', '-r', pcap_file, '-q', '-z', 'conv,tcp']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            analyses['tcp_conversations'] = result.stdout
            
        except Exception as e:
            analyses['error'] = str(e)
        
        return analyses
