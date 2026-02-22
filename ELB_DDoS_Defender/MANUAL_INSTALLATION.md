# ELB DDoS Defender - Step-by-Step Manual Installation

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS Account with appropriate permissions
- [ ] EC2 instance launched (t3.medium or larger)
- [ ] SSH key pair for instance access
- [ ] Load balancers in the same VPC
- [ ] IAM role attached to instance

---

## 🚀 Step-by-Step Installation

### Step 1: Launch EC2 Instance

**1.1 Discover Your AWS Resources:**

**List available VPCs:**
```bash
aws ec2 describe-vpcs \
  --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0],IsDefault]' \
  --output table
```

**List subnets in your chosen VPC:**
```bash
# Replace vpc-xxxxx with your VPC ID
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=vpc-xxxxx" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```

**List available SSH key pairs:**
```bash
aws ec2 describe-key-pairs \
  --query 'KeyPairs[*].[KeyName,KeyPairId,KeyType]' \
  --output table
```

**1.2 Choose AMI:**
```bash
# Amazon Linux 2023 (recommended)
AMI: ami-0c55b159cbfafe1f0

# Or Ubuntu 22.04 LTS
AMI: ami-0557a15b87f6559cf
```

**1.3 Instance Configuration:**
- **Instance Type:** t3.medium (minimum)
- **VPC:** Choose from list above
- **Subnet:** Choose from list above (private recommended)
- **Key Pair:** Choose from list above
- **Auto-assign Public IP:** Yes (for SSH) or No (for Session Manager)
- **IAM Role:** ELBDDoSDefenderRole (create if needed)

**1.4 Storage:**
- **Root Volume:** 30 GB gp3
- **Additional Volume (optional):** 100 GB for PCAPs

**1.5 Security Group:**

Create security group with these rules:

**Inbound:**
| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access (optional) |
| Custom UDP | UDP | 4789 | VPC CIDR | Traffic mirroring |

**Outbound:**
| Type | Protocol | Port | Destination | Description |
|------|----------|------|-------------|-------------|
| HTTPS | TCP | 443 | 0.0.0.0/0 | AWS API calls |
| All traffic | All | All | VPC CIDR | Internal |

**1.6 Launch Instance:**
```bash
# Replace with your selections from above
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name YOUR-KEY-NAME \
  --security-group-ids sg-xxxxx \
  --subnet-id YOUR-SUBNET-ID \
  --iam-instance-profile Name=ELBDDoSDefenderRole \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ELB-DDoS-Defender}]'
```

**1.7 Wait for instance to be running:**
```bash
aws ec2 wait instance-running --instance-ids i-xxxxx
```

---

### Step 2: Connect to Instance

**Option A: SSH**
```bash
# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# Connect
ssh -i your-key.pem ec2-user@$PUBLIC_IP
```

**Option B: Session Manager (No SSH key needed)**
```bash
aws ssm start-session --target i-xxxxx
```

---

### Step 3: Update System

**For Amazon Linux 2023:**
```bash
sudo yum update -y
```

**For Ubuntu 22.04:**
```bash
sudo apt-get update -y
sudo apt-get upgrade -y
```

**Verify:**
```bash
cat /etc/os-release
```

---

### Step 4: Install Python 3.11+

**For Amazon Linux 2023:**
```bash
# Install Python 3.11
sudo yum install -y python3.11 python3.11-pip

# Set as default
sudo ln -sf /usr/bin/python3.11 /usr/bin/python3

# Verify
python3 --version
# Should show: Python 3.11.x
```

**For Ubuntu 22.04:**
```bash
# Install Python 3.11
sudo apt-get install -y python3.11 python3-pip

# Verify
python3 --version
```

---

### Step 5: Install System Dependencies

**For Amazon Linux 2023:**
```bash
sudo yum install -y \
  tcpdump \
  wireshark-cli \
  git \
  libpcap-devel \
  gcc \
  python3.11-devel
```

**For Ubuntu 22.04:**
```bash
sudo apt-get install -y \
  tcpdump \
  tshark \
  git \
  libpcap-dev \
  gcc \
  python3-dev
```

**Verify installations:**
```bash
tcpdump --version
tshark --version
git --version
```

---

### Step 6: Install Python Packages

**6.1 Upgrade pip:**
```bash
sudo pip3 install --upgrade pip
```

**6.2 Install required packages:**
```bash
sudo pip3 install \
  boto3>=1.26.0 \
  scapy>=2.5.0 \
  pyyaml>=6.0 \
  jinja2>=3.1.0 \
  requests>=2.28.0 \
  rich>=13.0.0 \
  pyshark>=0.6
```

**6.3 Verify installations:**
```bash
python3 -c "import boto3; print('boto3:', boto3.__version__)"
python3 -c "import scapy; print('scapy:', scapy.__version__)"
python3 -c "import rich; print('rich:', rich.__version__)"
python3 -c "import pyshark; print('pyshark:', pyshark.__version__)"
```

---

### Step 7: Create Directory Structure

```bash
# Create application directory
sudo mkdir -p /opt/elb-ddos-defender
sudo mkdir -p /opt/elb-ddos-defender/sdk

# Create log directories
sudo mkdir -p /var/log/elb-ddos-defender
sudo mkdir -p /var/log/pcaps

# Create config directory
sudo mkdir -p /etc/elb-ddos-defender

# Set permissions
sudo chown -R $USER:$USER /opt/elb-ddos-defender
sudo chown -R $USER:$USER /var/log/elb-ddos-defender
sudo chown -R $USER:$USER /var/log/pcaps
```

**Verify:**
```bash
ls -la /opt/elb-ddos-defender
ls -la /var/log/elb-ddos-defender
```

---

### Step 8: Download Application Files

**8.1 Clone repository:**
```bash
cd /opt
sudo git clone https://github.com/acchitty/Network-Tools.git
```

**8.2 Copy files:**
```bash
sudo cp -r /opt/Network-Tools/ELB_DDoS_Defender/* /opt/elb-ddos-defender/
```

**8.3 Set permissions:**
```bash
sudo chmod +x /opt/elb-ddos-defender/elb-ddos-defender.py
sudo chmod +x /opt/elb-ddos-defender/elb-ddos-dashboard.py
sudo chmod +x /opt/elb-ddos-defender/dashboard.sh
```

**Verify:**
```bash
ls -lh /opt/elb-ddos-defender/
```

---

### Step 9: Configure Application

**9.1 Get instance metadata:**
```bash
# Get instance ID
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance ID: $INSTANCE_ID"

# Get region
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
echo "Region: $REGION"

# Get VPC ID
VPC_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $REGION \
  --query 'Reservations[0].Instances[0].VpcId' \
  --output text)
echo "VPC ID: $VPC_ID"
```

**9.2 Discover load balancers:**
```bash
# List load balancers in this VPC
aws elbv2 describe-load-balancers \
  --region $REGION \
  --query "LoadBalancers[?VpcId=='$VPC_ID'].[LoadBalancerName,LoadBalancerArn,Type]" \
  --output table
```

**9.3 Create configuration file:**
```bash
sudo nano /opt/elb-ddos-defender/config.yaml
```

**Paste this configuration (update with your values):**
```yaml
# ELB DDoS Defender Configuration

aws:
  region: us-east-1  # Change to your region

# Load balancers to monitor
load_balancers:
  - name: my-alb-1
    arn: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb-1/abc123
    log_prefix: my-alb-1
    
  - name: my-alb-2
    arn: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb-2/def456
    log_prefix: my-alb-2

# Email alerts
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
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

**9.4 Validate configuration:**
```bash
python3 -c "import yaml; yaml.safe_load(open('/opt/elb-ddos-defender/config.yaml'))" && echo "✓ Config valid"
```

---

### Step 10: Create Systemd Service

**10.1 Create service file:**
```bash
sudo nano /etc/systemd/system/elb-ddos-defender.service
```

**Paste this content:**
```ini
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Save and exit**

**10.2 Reload systemd:**
```bash
sudo systemctl daemon-reload
```

**10.3 Enable service:**
```bash
sudo systemctl enable elb-ddos-defender
```

**Verify:**
```bash
systemctl list-unit-files | grep elb-ddos-defender
```

---

### Step 11: Set Up VPC Traffic Mirroring

**11.1 Get this instance's ENI:**
```bash
INSTANCE_ENI=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $REGION \
  --query 'Reservations[0].Instances[0].NetworkInterfaces[0].NetworkInterfaceId' \
  --output text)
echo "Instance ENI: $INSTANCE_ENI"
```

**11.2 Create traffic mirror target:**
```bash
MIRROR_TARGET_ID=$(aws ec2 create-traffic-mirror-target \
  --network-interface-id $INSTANCE_ENI \
  --region $REGION \
  --description "ELB DDoS Defender Mirror Target" \
  --query 'TrafficMirrorTarget.TrafficMirrorTargetId' \
  --output text)

echo "Mirror Target ID: $MIRROR_TARGET_ID"
```

**11.3 Create traffic mirror filter:**
```bash
MIRROR_FILTER_ID=$(aws ec2 create-traffic-mirror-filter \
  --region $REGION \
  --description "ELB DDoS Defender Filter" \
  --query 'TrafficMirrorFilter.TrafficMirrorFilterId' \
  --output text)

echo "Mirror Filter ID: $MIRROR_FILTER_ID"
```

**11.4 Add filter rules (allow all traffic):**
```bash
# Ingress rule
aws ec2 create-traffic-mirror-filter-rule \
  --traffic-mirror-filter-id $MIRROR_FILTER_ID \
  --traffic-direction ingress \
  --rule-number 100 \
  --rule-action accept \
  --protocol 0 \
  --source-cidr-block 0.0.0.0/0 \
  --destination-cidr-block 0.0.0.0/0 \
  --region $REGION

# Egress rule
aws ec2 create-traffic-mirror-filter-rule \
  --traffic-mirror-filter-id $MIRROR_FILTER_ID \
  --traffic-direction egress \
  --rule-number 100 \
  --rule-action accept \
  --protocol 0 \
  --source-cidr-block 0.0.0.0/0 \
  --destination-cidr-block 0.0.0.0/0 \
  --region $REGION
```

**11.5 Get ELB ENIs to mirror:**
```bash
# Get all ELB ENIs in this VPC
aws ec2 describe-network-interfaces \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=description,Values=ELB*" \
  --region $REGION \
  --query 'NetworkInterfaces[].[NetworkInterfaceId,Description]' \
  --output table
```

**11.6 Create mirror sessions for each ELB ENI:**
```bash
# Example for one ENI (repeat for each)
ELB_ENI="eni-xxxxx"  # Replace with actual ENI

aws ec2 create-traffic-mirror-session \
  --traffic-mirror-target-id $MIRROR_TARGET_ID \
  --traffic-mirror-filter-id $MIRROR_FILTER_ID \
  --network-interface-id $ELB_ENI \
  --session-number 1 \
  --region $REGION \
  --description "Mirror session for $ELB_ENI"
```

**Repeat for each ELB ENI, incrementing session-number (1, 2, 3, etc.)**

---

### Step 12: Start Service

**12.1 Start the service:**
```bash
sudo systemctl start elb-ddos-defender
```

**12.2 Check status:**
```bash
sudo systemctl status elb-ddos-defender
```

**Expected output:**
```
● elb-ddos-defender.service - ELB DDoS Defender
   Loaded: loaded (/etc/systemd/system/elb-ddos-defender.service)
   Active: active (running) since Sun 2026-02-22 14:00:00 EST
```

**12.3 View logs:**
```bash
sudo tail -f /var/log/elb-ddos-defender/defender.log
```

**Expected log entries:**
```
[2026-02-22 14:00:00] [INFO] ELB DDoS Defender started
[2026-02-22 14:00:01] [INFO] Monitoring load balancer: my-alb-1
[2026-02-22 14:00:01] [INFO] Discovered 3 ELB node ENIs
[2026-02-22 14:00:01] [INFO] Discovered 4 target ENIs
[2026-02-22 14:00:02] [INFO] PyShark capture started
[2026-02-22 14:00:02] [INFO] Real-time monitoring active
```

---

### Step 13: Verify Installation

**13.1 Check service is running:**
```bash
sudo systemctl is-active elb-ddos-defender
# Should output: active
```

**13.2 Check packet capture:**
```bash
sudo tcpdump -i eth0 -c 10
# Should see packets
```

**13.3 View dashboard:**
```bash
sudo /opt/elb-ddos-defender/dashboard.sh
```

**13.4 Check CloudWatch logs:**
```bash
aws logs describe-log-streams \
  --log-group-name /aws/elb-ddos-defender \
  --region $REGION
```

---

### Step 14: Configure Email Alerts (Optional)

**14.1 Verify email in SES:**
```bash
aws ses verify-email-identity \
  --email-address alerts@example.com \
  --region $REGION
```

**14.2 Check verification status:**
```bash
aws ses get-identity-verification-attributes \
  --identities alerts@example.com \
  --region $REGION
```

**14.3 Update config:**
```bash
sudo nano /opt/elb-ddos-defender/config.yaml
```

Change:
```yaml
email:
  enabled: true  # Change from false
  from: alerts@example.com  # Your verified email
  to:
    - security@example.com  # Your email
```

**14.4 Restart service:**
```bash
sudo systemctl restart elb-ddos-defender
```

**14.5 Test alert:**
```bash
sudo /opt/elb-ddos-defender/test-alert.sh
```

---

## ✅ Installation Complete!

### Access Methods:

**1. SSH Access:**
```bash
ssh -i your-key.pem ec2-user@<public-ip>
```

**2. Session Manager (No SSH key needed):**
```bash
aws ssm start-session --target i-xxxxx
```

**3. View Dashboard:**
```bash
sudo /opt/elb-ddos-defender/dashboard.sh
```

### Verification Checklist:

- [ ] Service is running: `sudo systemctl status elb-ddos-defender`
- [ ] Logs are being written: `ls -lh /var/log/elb-ddos-defender/`
- [ ] PCAPs are being captured: `ls -lh /var/log/pcaps/`
- [ ] Dashboard works: `sudo /opt/elb-ddos-defender/dashboard.sh`
- [ ] CloudWatch logs exist: Check AWS Console
- [ ] Traffic mirroring configured: Check EC2 Console

### Next Steps:

1. Monitor dashboard for 24 hours
2. Adjust thresholds if needed
3. Set up email alerts
4. Review CloudWatch metrics
5. Test with simulated traffic

---

*Manual Installation Guide v1.0 - 2026-02-22*
