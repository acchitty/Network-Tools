#!/usr/bin/env python3.11
"""ELB DDoS Defender - Web Dashboard"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import subprocess
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

METRICS_FILE = '/var/log/elb-ddos-defender/metrics.json'

def load_metrics():
    """Load real-time metrics"""
    try:
        with open(METRICS_FILE, 'r') as f:
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

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """Real-time metrics endpoint"""
    metrics = load_metrics()
    
    # Convert unique_ips set to count if needed
    if isinstance(metrics.get('unique_ips'), set):
        metrics['unique_ips'] = len(metrics['unique_ips'])
    
    return jsonify(metrics)

@app.route('/api/attacks')
def get_attacks():
    """Get attack history"""
    metrics = load_metrics()
    attacks = metrics.get('attacks_detected', [])
    
    # Get last 50 attacks
    recent_attacks = attacks[-50:] if len(attacks) > 50 else attacks
    
    # Group by IP for top attackers
    top_attackers = {}
    for attack in attacks:
        src = attack.get('source', 'unknown')
        if src != 'unknown' and src != 'multiple_sources':
            if src not in top_attackers:
                top_attackers[src] = {
                    'ip': src,
                    'count': 0,
                    'types': set(),
                    'last_seen': attack.get('timestamp'),
                    'destination': attack.get('destination', 'N/A')
                }
            top_attackers[src]['count'] += 1
            top_attackers[src]['types'].add(attack.get('type', 'unknown'))
    
    # Convert sets to lists for JSON
    for ip in top_attackers:
        top_attackers[ip]['types'] = list(top_attackers[ip]['types'])
    
    # Sort by count
    top_list = sorted(top_attackers.values(), key=lambda x: x['count'], reverse=True)[:10]
    
    return jsonify({
        'recent': recent_attacks,
        'top_attackers': top_list
    })

@app.route('/api/whois/<ip>')
def whois_lookup(ip):
    """WHOIS lookup for IP"""
    try:
        result = subprocess.run(['whois', ip], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Parse key information
            lines = result.stdout.split('\n')
            info = {}
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key in ['netname', 'orgname', 'country', 'descr', 'owner', 'inetnum', 'cidr', 'organization']:
                        info[key] = value
            
            return jsonify({
                'success': True,
                'ip': ip,
                'info': info,
                'raw': result.stdout
            })
        else:
            return jsonify({'success': False, 'error': 'WHOIS lookup failed'})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'WHOIS lookup timed out'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/system')
def system_info():
    """Get system information"""
    try:
        # Get service status
        service_status = subprocess.run(['systemctl', 'is-active', 'elb-ddos-defender'],
                                       capture_output=True, text=True)
        
        # Get instance ID
        instance_id = 'unknown'
        try:
            token = subprocess.run(['curl', '-s', '-X', 'PUT', 
                                   'http://169.254.169.254/latest/api/token',
                                   '-H', 'X-aws-ec2-metadata-token-ttl-seconds: 21600'],
                                  capture_output=True, text=True, timeout=2)
            if token.returncode == 0:
                result = subprocess.run(['curl', '-s', '-H', f'X-aws-ec2-metadata-token: {token.stdout}',
                                       'http://169.254.169.254/latest/meta-data/instance-id'],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    instance_id = result.stdout.strip()
        except:
            pass
        
        return jsonify({
            'service_status': service_status.stdout.strip(),
            'instance_id': instance_id,
            'uptime': subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip()
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
