#!/bin/bash
#
# ELB DDoS Defender - Complete Automated Installer
# Installs everything in one command with zero interaction
#
# Usage: curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Banner
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║         ELB DDoS Defender - Automated Installer          ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

# Detect OS
log_info "Detecting operating system..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    log_error "Cannot detect OS"
    exit 1
fi

log_success "Detected: $OS $VERSION"

# Step 1: Update system
log_info "[1/10] Updating system packages..."
if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ] || [ "$OS" = "centos" ]; then
    yum update -y > /dev/null 2>&1
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update -y > /dev/null 2>&1
    apt-get upgrade -y > /dev/null 2>&1
fi
log_success "System updated"

# Step 2: Install Python 3.11+
log_info "[2/10] Installing Python 3.11..."
if [ "$OS" = "amzn" ]; then
    yum install -y python3.11 python3.11-pip > /dev/null 2>&1
    ln -sf /usr/bin/python3.11 /usr/bin/python3
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get install -y python3.11 python3-pip > /dev/null 2>&1
fi
log_success "Python $(python3 --version) installed"

# Step 3: Install system dependencies
log_info "[3/10] Installing system dependencies..."
if [ "$OS" = "amzn" ]; then
    yum install -y tcpdump wireshark-cli git libpcap-devel gcc python3.11-devel > /dev/null 2>&1
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get install -y tcpdump tshark git libpcap-dev gcc python3-dev > /dev/null 2>&1
fi
log_success "System dependencies installed"

# Step 4: Install Python packages
log_info "[4/10] Installing Python packages..."
pip3 install --upgrade pip > /dev/null 2>&1
pip3 install boto3 scapy pyyaml jinja2 requests rich pyshark > /dev/null 2>&1
log_success "Python packages installed"

# Step 5: Create directories
log_info "[5/10] Creating directories..."
mkdir -p /opt/elb-ddos-defender
mkdir -p /var/log/elb-ddos-defender
mkdir -p /var/log/pcaps
mkdir -p /etc/elb-ddos-defender
log_success "Directories created"

# Step 6: Download application files
log_info "[6/10] Downloading application files..."
cd /opt/elb-ddos-defender

# Download from GitHub
REPO_URL="https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender"

curl -sSL "$REPO_URL/elb-ddos-defender.py" -o elb-ddos-defender.py
curl -sSL "$REPO_URL/elb-ddos-dashboard.py" -o elb-ddos-dashboard.py
curl -sSL "$REPO_URL/dashboard.sh" -o dashboard.sh
curl -sSL "$REPO_URL/config.yaml.template" -o config.yaml.template

# Download SDK files
mkdir -p sdk
curl -sSL "$REPO_URL/sdk/cloudwatch_sdk.py" -o sdk/cloudwatch_sdk.py
curl -sSL "$REPO_URL/sdk/pcap_capture_sdk.py" -o sdk/pcap_capture_sdk.py
curl -sSL "$REPO_URL/sdk/__init__.py" -o sdk/__init__.py

chmod +x elb-ddos-defender.py
chmod +x elb-ddos-dashboard.py
chmod +x dashboard.sh

log_success "Application files downloaded"

# Step 7: Auto-discover and configure
log_info "[7/10] Auto-discovering AWS resources..."

# Get instance metadata
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
VPC_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].VpcId' --output text)

log_info "Instance: $INSTANCE_ID"
log_info "Region: $REGION"
log_info "VPC: $VPC_ID"

# Discover load balancers in this VPC
log_info "Discovering load balancers in VPC..."
LB_ARNS=$(aws elbv2 describe-load-balancers --region $REGION --query "LoadBalancers[?VpcId=='$VPC_ID'].LoadBalancerArn" --output text)

if [ -z "$LB_ARNS" ]; then
    log_warn "No load balancers found in this VPC"
    log_warn "You'll need to configure manually"
else
    LB_COUNT=$(echo "$LB_ARNS" | wc -w)
    log_success "Found $LB_COUNT load balancer(s)"
fi

# Step 8: Create configuration
log_info "[8/10] Creating configuration..."

cat > /opt/elb-ddos-defender/config.yaml << EOF
# ELB DDoS Defender Configuration
# Auto-generated on $(date)

aws:
  region: $REGION

# Load balancers to monitor
load_balancers:
EOF

# Add discovered load balancers
for ARN in $LB_ARNS; do
    LB_NAME=$(aws elbv2 describe-load-balancers --load-balancer-arns $ARN --region $REGION --query 'LoadBalancers[0].LoadBalancerName' --output text)
    cat >> /opt/elb-ddos-defender/config.yaml << EOF
  - name: $LB_NAME
    arn: $ARN
    log_prefix: $LB_NAME
EOF
done

cat >> /opt/elb-ddos-defender/config.yaml << EOF

# Email alerts (configure SES first)
email:
  enabled: false  # Set to true after SES setup
  from: alerts@example.com
  to:
    - security@example.com

# Detection thresholds
thresholds:
  connections_per_second: 1000
  syn_packets_per_second: 5000
  http_requests_per_second: 2000
  ports_scanned_threshold: 20
  eni_connection_warning: 44000
  eni_connection_critical: 52000

# Monitoring
monitoring:
  enabled: true
  interval: 1  # seconds
  
  pyshark:
    enabled: true
    display_filter: "tcp or udp"
    capture_interface: eth0
  
  pcap:
    enabled: true
    directory: /var/log/pcaps
    max_size: 100
    rotation: 10
  
  cloudwatch:
    enabled: true
    log_group: /aws/elb-ddos-defender
    metrics_namespace: ELBDDoSDefender

# Logging
logging:
  level: INFO
  file: /var/log/elb-ddos-defender/defender.log
  max_size: 100
  backup_count: 10
EOF

log_success "Configuration created"

# Step 9: Create systemd service
log_info "[9/10] Creating systemd service..."

cat > /etc/systemd/system/elb-ddos-defender.service << EOF
[Unit]
Description=ELB DDoS Defender
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/elb-ddos-defender
ExecStart=/usr/bin/python3 /opt/elb-ddos-defender/elb-ddos-defender.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
log_success "Systemd service created"

# Step 10: Set up VPC Traffic Mirroring
log_info "[10/10] Setting up VPC Traffic Mirroring..."

# Get this instance's ENI
INSTANCE_ENI=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' --output text)

# Create mirror target
MIRROR_TARGET_ID=$(aws ec2 create-traffic-mirror-target \
    --network-interface-id $INSTANCE_ENI \
    --region $REGION \
    --query 'TrafficMirrorTarget.TrafficMirrorTargetId' \
    --output text 2>/dev/null)

if [ -n "$MIRROR_TARGET_ID" ]; then
    log_success "Traffic mirror target created: $MIRROR_TARGET_ID"
    
    # Create mirror filter (allow all)
    MIRROR_FILTER_ID=$(aws ec2 create-traffic-mirror-filter \
        --region $REGION \
        --query 'TrafficMirrorFilter.TrafficMirrorFilterId' \
        --output text 2>/dev/null)
    
    aws ec2 create-traffic-mirror-filter-rule \
        --traffic-mirror-filter-id $MIRROR_FILTER_ID \
        --traffic-direction ingress \
        --rule-number 100 \
        --rule-action accept \
        --protocol 0 \
        --source-cidr-block 0.0.0.0/0 \
        --destination-cidr-block 0.0.0.0/0 \
        --region $REGION > /dev/null 2>&1
    
    log_success "Traffic mirror filter created: $MIRROR_FILTER_ID"
    
    # Mirror ELB ENIs
    SESSION_COUNT=0
    for ARN in $LB_ARNS; do
        # Get ELB ENIs
        LB_ENIS=$(aws ec2 describe-network-interfaces \
            --filters "Name=description,Values=ELB*" \
            --region $REGION \
            --query 'NetworkInterfaces[].NetworkInterfaceId' \
            --output text)
        
        for ENI in $LB_ENIS; do
            aws ec2 create-traffic-mirror-session \
                --traffic-mirror-target-id $MIRROR_TARGET_ID \
                --traffic-mirror-filter-id $MIRROR_FILTER_ID \
                --network-interface-id $ENI \
                --session-number $((100 + SESSION_COUNT)) \
                --region $REGION > /dev/null 2>&1
            
            if [ $? -eq 0 ]; then
                SESSION_COUNT=$((SESSION_COUNT + 1))
            fi
        done
    done
    
    log_success "Created $SESSION_COUNT traffic mirror sessions"
else
    log_warn "Could not create traffic mirror target (may need additional permissions)"
fi

# Final steps
log_info "Starting service..."
systemctl enable elb-ddos-defender > /dev/null 2>&1
systemctl start elb-ddos-defender

sleep 2

if systemctl is-active --quiet elb-ddos-defender; then
    log_success "Service started successfully"
else
    log_warn "Service may not have started correctly"
fi

# Print summary
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║              Installation Complete! 🎉                    ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "  • Instance: $INSTANCE_ID"
echo "  • Region: $REGION"
echo "  • VPC: $VPC_ID"
echo "  • Load Balancers: $LB_COUNT"
echo "  • Mirror Sessions: $SESSION_COUNT"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. View Dashboard:"
echo "   sudo /opt/elb-ddos-defender/dashboard.sh"
echo ""
echo "2. Check Status:"
echo "   sudo systemctl status elb-ddos-defender"
echo ""
echo "3. View Logs:"
echo "   sudo tail -f /var/log/elb-ddos-defender/defender.log"
echo ""
echo "4. Configure Email Alerts:"
echo "   • Set up AWS SES"
echo "   • Edit /opt/elb-ddos-defender/config.yaml"
echo "   • Set email.enabled: true"
echo "   • Restart: sudo systemctl restart elb-ddos-defender"
echo ""
echo "5. Access Dashboard:"
echo "   • SSH: ssh -i your-key.pem ec2-user@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "   • Session Manager: aws ssm start-session --target $INSTANCE_ID"
echo ""
echo "📚 Documentation:"
echo "   https://github.com/acchitty/Network-Tools/tree/main/ELB_DDoS_Defender"
echo ""
echo "✅ Your load balancers are now protected!"
echo ""
