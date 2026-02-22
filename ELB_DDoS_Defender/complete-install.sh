#!/bin/bash
# ELB DDoS Defender - Complete Installation Script
# Usage: curl -sSL https://url/complete-install.sh | sudo bash -s -- your-email@example.com

set -e

EMAIL="$1"
INSTALL_DIR="/opt/elb-ddos-defender"
REPO_URL="https://github.com/YOUR-USERNAME/elb-ddos-defender"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}▶${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }

# Validate
[ -z "$EMAIL" ] && error "Email required: curl -sSL url | sudo bash -s -- your@email.com"
[ "$EUID" -ne 0 ] && error "Run with sudo"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      ELB DDoS Defender - Complete Installation                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Email: $EMAIL"
echo ""

# Install system dependencies
log "Installing system dependencies..."
if command -v yum &>/dev/null; then
    yum update -y -q
    yum install -y -q python3 python3-pip tcpdump wireshark mtr whois bind-utils geoip git jq
elif command -v apt-get &>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip tcpdump tshark mtr whois dnsutils geoip-bin git jq
fi
success "System dependencies installed"

# Install Python dependencies
log "Installing Python packages..."
pip3 install -q --upgrade pip
pip3 install -q boto3 scapy pyyaml jinja2 weasyprint reportlab requests
success "Python packages installed"

# Get AWS information
log "Getting AWS information..."
INSTANCE_ID=$(ec2-metadata --instance-id 2>/dev/null | cut -d' ' -f2 || echo "")
REGION=$(ec2-metadata --availability-zone 2>/dev/null | cut -d' ' -f2 | sed 's/[a-z]$//' || aws configure get region || echo "us-east-1")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -n "$INSTANCE_ID" ]; then
    success "Instance: $INSTANCE_ID, Region: $REGION"
else
    warn "Not running on EC2"
fi

# Create IAM role
log "Configuring IAM permissions..."
ROLE_NAME="ELBDDoSDefenderRole"

if ! aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF
    
    aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file:///tmp/trust-policy.json &>/dev/null
    
    cat > /tmp/permissions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:*",
        "cloudwatch:*",
        "elasticloadbalancing:*",
        "ec2:*",
        "s3:GetObject",
        "ses:*",
        "sns:*",
        "wafv2:*",
        "guardduty:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF
    
    aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "ELBDDoSDefenderPolicy" --policy-document file:///tmp/permissions-policy.json &>/dev/null
    success "IAM role created"
else
    success "IAM role exists"
fi

# Create instance profile
if ! aws iam get-instance-profile --instance-profile-name "$ROLE_NAME" &>/dev/null; then
    aws iam create-instance-profile --instance-profile-name "$ROLE_NAME" &>/dev/null
    aws iam add-role-to-instance-profile --instance-profile-name "$ROLE_NAME" --role-name "$ROLE_NAME" &>/dev/null
    sleep 5
fi

# Attach to instance
if [ -n "$INSTANCE_ID" ]; then
    CURRENT_PROFILE=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].IamInstanceProfile.Arn' --output text 2>/dev/null)
    if [ "$CURRENT_PROFILE" == "None" ] || [ -z "$CURRENT_PROFILE" ]; then
        aws ec2 associate-iam-instance-profile --instance-id "$INSTANCE_ID" --iam-instance-profile Name="$ROLE_NAME" &>/dev/null
        sleep 10
        success "IAM role attached"
    fi
fi

# Create directories
log "Creating directories..."
mkdir -p "$INSTALL_DIR"/{sdk,detectors,analyzers,reporters,tests}
mkdir -p /var/log/{pcaps,attack-reports,elb-ddos-defender}
success "Directories created"

# Download application
log "Downloading application..."
if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR" && git pull -q
else
    git clone -q "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
success "Application downloaded"

# Configure email
log "Configuring email..."
aws ses verify-email-identity --email-address "$EMAIL" --region "$REGION" &>/dev/null
success "Email verification sent to $EMAIL"

# Auto-detect load balancers
log "Detecting load balancers..."
LBS=$(aws elbv2 describe-load-balancers --region "$REGION" --query 'LoadBalancers[*].[LoadBalancerName,Type]' --output text 2>/dev/null || echo "")

if [ -n "$LBS" ]; then
    LB_COUNT=$(echo "$LBS" | wc -l)
    success "Found $LB_COUNT load balancer(s)"
    
    echo ""
    echo "Available Load Balancers:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    LB_ARRAY=()
    INDEX=1
    while IFS=$'\t' read -r name type; do
        echo "  [$INDEX] $name ($type)"
        LB_ARRAY+=("$name|$type")
        INDEX=$((INDEX + 1))
    done <<< "$LBS"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Enter load balancers to monitor (comma-separated numbers, or 'all'):"
    read -p "Selection: " LB_SELECTION
    
    SELECTED_LBS=()
    if [ "$LB_SELECTION" == "all" ]; then
        SELECTED_LBS=("${LB_ARRAY[@]}")
    else
        IFS=',' read -ra INDICES <<< "$LB_SELECTION"
        for idx in "${INDICES[@]}"; do
            idx=$(echo "$idx" | xargs)
            if [ "$idx" -ge 1 ] && [ "$idx" -le "${#LB_ARRAY[@]}" ]; then
                SELECTED_LBS+=("${LB_ARRAY[$((idx-1))]}")
            fi
        done
    fi
    
    success "Selected ${#SELECTED_LBS[@]} load balancer(s)"
else
    warn "No load balancers detected"
    SELECTED_LBS=()
fi

# Generate configuration
log "Generating configuration..."
cat > "$INSTALL_DIR/config.yaml" <<EOF
# ELB DDoS Defender Configuration
# Auto-generated: $(date)

alerts:
  email:
    enabled: true
    backend: ses
    sender: $EMAIL
    recipients:
      - $EMAIL
    region: $REGION

load_balancers:
EOF

for lb_info in "${SELECTED_LBS[@]}"; do
    IFS='|' read -r name type <<< "$lb_info"
    log_prefix=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr '-' '_')
    cat >> "$INSTALL_DIR/config.yaml" <<EOF
  - name: $name
    type: ${type^^}
    enabled: true
    email_recipients:
      - $EMAIL
    thresholds:
      connections_per_second: 100
      bandwidth_mbps: 500
    log_prefix: $log_prefix
    metrics_namespace: ELB/Monitor/${name}
EOF
    
    mkdir -p "/var/log/elb-ddos-defender/$log_prefix"
    mkdir -p "/var/log/attack-reports/$log_prefix"
    mkdir -p "/var/log/pcaps/$log_prefix"
done

cat >> "$INSTALL_DIR/config.yaml" <<EOF

global_thresholds:
  connections_per_second: 100
  bandwidth_mbps: 500

logging:
  base_dir: /var/log/elb-ddos-defender
  pcap_dir: /var/log/pcaps
  reports_dir: /var/log/attack-reports
  log_level: INFO

aws:
  region: $REGION
  account_id: $ACCOUNT_ID
EOF

success "Configuration created"

# Setup VPC Traffic Mirroring
if [ -n "$INSTANCE_ID" ] && [ ${#SELECTED_LBS[@]} -gt 0 ]; then
    log "Setting up VPC Traffic Mirroring..."
    
    MONITOR_ENI=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' --output text)
    
    TARGET_ID=$(aws ec2 create-traffic-mirror-target --network-interface-id "$MONITOR_ENI" --description "ELB DDoS Defender" --region "$REGION" --query 'TrafficMirrorTarget.TrafficMirrorTargetId' --output text 2>/dev/null || echo "")
    
    if [ -n "$TARGET_ID" ]; then
        FILTER_ID=$(aws ec2 create-traffic-mirror-filter --description "Capture All" --region "$REGION" --query 'TrafficMirrorFilter.TrafficMirrorFilterId' --output text)
        
        aws ec2 create-traffic-mirror-filter-rule --traffic-mirror-filter-id "$FILTER_ID" --traffic-direction ingress --rule-number 100 --rule-action accept --protocol -1 --region "$REGION" &>/dev/null
        
        ELB_ENIS=$(aws ec2 describe-network-interfaces --filters "Name=description,Values=*ELB*" --region "$REGION" --query 'NetworkInterfaces[*].NetworkInterfaceId' --output text)
        
        SESSION_NUM=1
        for ENI in $ELB_ENIS; do
            aws ec2 create-traffic-mirror-session --network-interface-id "$ENI" --traffic-mirror-target-id "$TARGET_ID" --traffic-mirror-filter-id "$FILTER_ID" --session-number "$SESSION_NUM" --region "$REGION" &>/dev/null || true
            SESSION_NUM=$((SESSION_NUM + 1))
        done
        
        success "VPC Traffic Mirroring configured"
    fi
fi

# Create systemd service
log "Creating systemd service..."
cat > /etc/systemd/system/elb-ddos-defender.service <<EOF
[Unit]
Description=ELB DDoS Defender
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/elb-ddos-defender.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/elb-ddos-defender.log
StandardError=append:/var/log/elb-ddos-defender.log

Environment="PYTHONUNBUFFERED=1"
Environment="AWS_DEFAULT_REGION=$REGION"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable elb-ddos-defender &>/dev/null
success "Service created"

# Start service
log "Starting service..."
systemctl start elb-ddos-defender
sleep 3

if systemctl is-active --quiet elb-ddos-defender; then
    success "Service started"
else
    warn "Service may need manual start"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Installation Complete! ✅                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📧 Email:          $EMAIL"
echo "🌍 Region:         $REGION"
echo "🖥️  Instance:       ${INSTANCE_ID:-N/A}"
echo "⚖️  Load Balancers: ${#SELECTED_LBS[@]}"
echo "📊 Status:         $(systemctl is-active elb-ddos-defender)"
echo ""
echo "⚠️  IMPORTANT: Check your email and click the verification link!"
echo ""
echo "📝 View logs:      sudo tail -f /var/log/elb-ddos-defender.log"
echo "🔍 Check status:   sudo systemctl status elb-ddos-defender"
echo ""
echo "✅ You'll receive email alerts when attacks are detected"
echo ""
