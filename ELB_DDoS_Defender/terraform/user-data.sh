#!/bin/bash
set -e

exec > >(tee /var/log/elb-ddos-defender-install.log)
exec 2>&1

echo "=== ELB DDoS Defender Installation Started ==="
echo "Timestamp: $(date)"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect OS"
    exit 1
fi

# Update system
echo "Updating system packages..."
if [ "$OS" = "amzn" ]; then
    yum update -y
    yum install -y python3.11 python3.11-pip tcpdump git
elif [ "$OS" = "ubuntu" ]; then
    apt-get update -y
    apt-get install -y python3.11 python3-pip tcpdump tshark git
fi

# Install Python packages
echo "Installing Python packages..."
pip3.11 install boto3 scapy pyyaml rich pyshark

# Create directories
echo "Creating directories..."
mkdir -p /opt/elb-ddos-defender
mkdir -p /var/log/elb-ddos-defender
mkdir -p /var/log/pcaps

# Get instance metadata
echo "Getting instance metadata..."
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
REGION=$(ec2-metadata --availability-zone | cut -d " " -f 2 | sed 's/[a-z]$//')
VPC_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].VpcId' --output text)

echo "Instance ID: $INSTANCE_ID"
echo "Region: $REGION"
echo "VPC ID: $VPC_ID"

# Create basic config
echo "Creating configuration..."
cat > /opt/elb-ddos-defender/config.yaml <<EOF
aws:
  region: $REGION

load_balancers: []

email:
  from: ${email_address}
  to: ${email_address}

thresholds:
  connections_per_second: 1000
  http_requests_per_second: 2000
  ports_scanned_threshold: 20
  eni_connection_warning: 44000
  eni_connection_critical: 52000

monitoring:
  interval: 1
  pyshark:
    enabled: true
EOF

# Create placeholder Python files (will be replaced with real code)
cat > /opt/elb-ddos-defender/elb-ddos-defender.py <<'PYEOF'
#!/usr/bin/env python3
import time
import yaml
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/elb-ddos-defender/defender.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("ELB DDoS Defender started")
    logger.info("Monitoring initialized - waiting for full deployment")
    
    while True:
        logger.info("Service running - placeholder mode")
        time.sleep(60)

if __name__ == "__main__":
    main()
PYEOF

chmod +x /opt/elb-ddos-defender/elb-ddos-defender.py

# Create systemd service
cat > /etc/systemd/system/elb-ddos-defender.service <<EOF
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

# Enable and start service
systemctl daemon-reload
systemctl enable elb-ddos-defender
systemctl start elb-ddos-defender

echo "=== Installation Complete ==="
echo "Status: $(systemctl is-active elb-ddos-defender)"
echo "Logs: /var/log/elb-ddos-defender/defender.log"
echo "Config: /opt/elb-ddos-defender/config.yaml"
