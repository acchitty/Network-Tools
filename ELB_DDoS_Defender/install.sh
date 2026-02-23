#!/bin/bash
# ELB DDoS Defender - Quick Install (Fixed)
set -e

echo "=== ELB DDoS Defender Installer ==="

# Step 1: Install dependencies
echo "[1/5] Installing dependencies..."
yum install -y python3.11 python3.11-pip wireshark-cli git
pip3.11 install pyshark pyyaml rich flask flask-cors requests

# Step 2: Create directories
echo "[2/5] Creating directories..."
mkdir -p /opt/elb-ddos-defender/sdk
mkdir -p /var/log/elb-ddos-defender

# Step 3: Download core files
echo "[3/5] Downloading application files..."
cd /opt/elb-ddos-defender
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/elb-ddos-defender.py -o elb-ddos-defender.py
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/elb-ddos-dashboard.py -o elb-ddos-dashboard.py
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/elb-ddos-web.py -o elb-ddos-web.py
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/dashboard.sh -o dashboard.sh
chmod +x dashboard.sh elb-ddos-defender.py elb-ddos-dashboard.py elb-ddos-web.py

# Step 4: Download SDK files
echo "[4/5] Downloading SDK files..."
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/sdk/__init__.py -o sdk/__init__.py
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/sdk/cloudwatch_sdk.py -o sdk/cloudwatch_sdk.py
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/sdk/pcap_capture_sdk.py -o sdk/pcap_capture_sdk.py

# Step 5: Create config
echo "[5/5] Creating configuration..."
if [ ! -f config.yaml ]; then
    tee config.yaml > /dev/null << 'EOF'
aws:
  region: us-east-1

load_balancers: []

thresholds:
  syn_flood_ratio: 3.0
  udp_packets_per_sec: 1000
  packets_per_sec: 5000
  bytes_per_sec: 10000000
  multi_source_ips: 50

monitoring:
  enabled: true
  interval: 1
  
logging:
  level: INFO
  file: /var/log/elb-ddos-defender/defender.log
EOF
fi

# Create systemd services
echo "Creating systemd services..."
tee /etc/systemd/system/elb-ddos-defender.service > /dev/null << 'EOF'
[Unit]
Description=ELB DDoS Defender
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elb-ddos-defender
ExecStart=/usr/bin/python3.11 /opt/elb-ddos-defender/elb-ddos-defender.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/elb-ddos-web.service > /dev/null << 'EOF'
[Unit]
Description=ELB DDoS Defender Web Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elb-ddos-defender
ExecStart=/usr/bin/python3.11 /opt/elb-ddos-defender/elb-ddos-web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start services
echo "Starting services..."
systemctl daemon-reload
systemctl enable elb-ddos-defender elb-ddos-web
systemctl start elb-ddos-defender elb-ddos-web

echo ""
echo "✅ Installation complete!"
echo ""
echo "Check status:"
echo "  sudo systemctl status elb-ddos-defender"
echo "  sudo systemctl status elb-ddos-web"
echo ""
echo "View dashboard:"
echo "  sudo /opt/elb-ddos-defender/dashboard.sh"
echo ""
