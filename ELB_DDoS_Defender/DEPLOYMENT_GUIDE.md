# ELB DDoS Defender - Complete Deployment Guide

**Version 2.0 - Real-time Traffic Monitoring**

## What's New in v2.0 ✨
- ✅ **Real-time traffic monitoring** with packet capture
- ✅ **Live metrics dashboard** with visual meters and graphs
- ✅ **Attack detection** (connection floods, DDoS patterns)
- ✅ **Interactive ELB selection** from dashboard
- ✅ **Simulation mode** for testing without VPC Traffic Mirroring
- ✅ **Metrics export** (JSON file updated every second)

## 🚀 Quick Start (5 Minutes)

### Choose Your Deployment Method

**Option A: Automated (5 min)**
```bash
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
```

**Option D: Terraform Interactive (5 min)**
```bash
cd terraform/ && ./setup.sh
```

**Option C: CloudFormation Interactive (10 min)**
```bash
cd cloudformation/ && ./setup.sh
```

**All methods now include:**
- ✅ Interactive VPC/subnet/key selection
- ✅ Resource discovery and listing
- ✅ Configuration validation
- ✅ Automatic deployment

**See all options:** `DEPLOYMENT_OPTIONS.md`

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
   - [Method A: Automated](#method-a-automated-installation-recommended)
   - [Method B: Manual](#method-b-manual-installation)
   - [Method C: CloudFormation](#method-c-cloudformation)
   - [Method D: Terraform](#method-d-terraform)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Usage](#usage)
6. [Troubleshooting](#troubleshooting)
7. [Architecture](#architecture)
8. [FAQ](#faq)

---

## ✅ Prerequisites

### Required

**AWS Resources:**
- ✅ EC2 instance (t3.medium or larger)
- ✅ Load Balancer (ALB, NLB, CLB, or GWLB)
- ✅ VPC with internet access
- ✅ IAM role with required permissions

**Operating System:**
- ✅ Amazon Linux 2023 (recommended)
- ✅ Ubuntu 22.04 LTS
- ✅ Red Hat Enterprise Linux 8+

**Network:**
- ✅ Same VPC as your load balancers
- ✅ Internet access for package installation
- ✅ Security group allowing inbound traffic mirroring

### Optional (Recommended)

- ✅ AWS SES configured for email alerts
- ✅ SNS topic for notifications
- ✅ CloudWatch Logs access
- ✅ S3 bucket for PCAP storage

---

## 🎯 Installation Methods

Choose the method that best fits your workflow:

| Method | Time | Best For | Documentation |
|--------|------|----------|---------------|
| **A: Automated** | 5 min | Quick testing | Below |
| **B: Manual** | 30 min | Learning | `MANUAL_INSTALLATION.md` |
| **C: CloudFormation** | 10 min | AWS-native | `cloudformation/README.md` |
| **D: Terraform** | 5 min | IaC workflows | `terraform/README.md` |

**Full comparison:** See `DEPLOYMENT_OPTIONS.md`

---

### Method A: Automated Installation (Recommended)

**Step 1: Launch EC2 Instance**

**Discover your resources:**
```bash
# List VPCs
aws ec2 describe-vpcs \
  --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# List subnets in your VPC
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=vpc-xxxxx" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# List SSH keys
aws ec2 describe-key-pairs \
  --query 'KeyPairs[*].[KeyName,KeyPairId]' \
  --output table
```

**Launch instance:**
```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name YOUR-KEY-NAME \
  --security-group-ids sg-xxx \
  --subnet-id YOUR-SUBNET-ID \
  --iam-instance-profile Name=ELBDDoSDefenderRole \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ELB-DDoS-Defender}]'
```

**Step 2: Connect to Instance**

```bash
# Session Manager (recommended)
aws ssm start-session --target i-xxxxx

# Or SSH
ssh -i your-key.pem ec2-user@<instance-ip>
```

**Step 3: Run Installer**

```bash
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
```

**Done!** The installer auto-configures everything.

---

### Method B: Manual Installation

See `MANUAL_INSTALLATION.md` for 14 detailed steps with verification.

**Includes:**
- Resource discovery commands
- Step-by-step instructions
- Verification at each step
- Troubleshooting

---

### Method C: CloudFormation

**Interactive Setup:**
```bash
cd cloudformation/
./setup.sh
```

**The script will:**
1. List all VPCs and let you choose
2. List subnets in your VPC
3. List available SSH keys
4. Ask for email address
5. Choose instance type
6. Deploy CloudFormation stack
7. Show connection command

**Manual Setup:**
```bash
aws cloudformation create-stack \
  --stack-name elb-ddos-defender \
  --template-body file://cloudformation/template.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=vpc-xxxxx \
    ParameterKey=SubnetId,ParameterValue=subnet-xxxxx \
    ParameterKey=KeyName,ParameterValue=your-key \
    ParameterKey=EmailAddress,ParameterValue=alerts@example.com \
  --capabilities CAPABILITY_NAMED_IAM
```

**Full guide:** `cloudformation/README.md`

---

### Method D: Terraform

**Interactive Setup (Recommended):**
```bash
cd terraform/
./setup.sh
```

**The script will:**
1. List all VPCs and let you choose
2. List subnets in your VPC
3. List available SSH keys
4. Ask for email address
5. Choose instance type
6. Auto-create terraform.tfvars
7. Run terraform init/plan/apply
8. Show connection command

**Manual Setup:**
```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Configure VPC, subnet, email

terraform init
terraform plan
terraform apply
```

**What it deploys:**
- ✅ EC2 instance with IAM role
- ✅ Security group
- ✅ CloudWatch log group
- ✅ Automated installation via user-data
- ✅ Complete infrastructure as code

**Full guide:** `terraform/README.md`
sudo systemctl enable elb-ddos-defender
```

**Done!** Your ELB is now protected.

---

### Method 2: Manual Installation

**Step 1: Install Dependencies**

```bash
# Update system
sudo yum update -y  # Amazon Linux
# OR
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.11+
sudo yum install python3.11 -y  # Amazon Linux
# OR
sudo apt install python3.11 -y  # Ubuntu

# Install tcpdump and tshark
sudo yum install tcpdump wireshark-cli -y  # Amazon Linux
# OR
sudo apt install tcpdump tshark -y  # Ubuntu
```

**Step 2: Clone Repository**

```bash
cd /opt
sudo git clone https://github.com/acchitty/Network-Tools.git
cd Network-Tools/ELB_DDoS_Defender
```

**Step 3: Install Python Dependencies**

```bash
sudo pip3 install -r requirements.txt
```

**Step 4: Create Configuration**

```bash
sudo cp config.yaml.template config.yaml
sudo nano config.yaml
```

**Step 5: Set Up Service**

```bash
sudo cp elb-ddos-defender.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start elb-ddos-defender
sudo systemctl enable elb-ddos-defender
```

---

### Method 3: Docker Installation

**Step 1: Install Docker**

```bash
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
```

**Step 2: Pull Image**

```bash
sudo docker pull acchitty/elb-ddos-defender:latest
```

**Step 3: Run Container**

```bash
sudo docker run -d \
  --name elb-ddos-defender \
  --network host \
  --cap-add NET_ADMIN \
  --cap-add NET_RAW \
  -v /opt/elb-ddos-defender/config.yaml:/app/config.yaml \
  -v /var/log/elb-ddos-defender:/var/log/elb-ddos-defender \
  acchitty/elb-ddos-defender:latest
```

---

### Method 4: CloudFormation Deployment

**Step 1: Download Template**

```bash
curl -O https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/cloudformation-template.yaml
```

**Step 2: Deploy Stack**

```bash
aws cloudformation create-stack \
  --stack-name elb-ddos-defender \
  --template-body file://cloudformation-template.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=vpc-xxx \
    ParameterKey=SubnetId,ParameterValue=subnet-xxx \
    ParameterKey=KeyName,ParameterValue=your-key \
    ParameterKey=EmailAddress,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_IAM
```

**Step 3: Wait for Completion**

```bash
aws cloudformation wait stack-create-complete \
  --stack-name elb-ddos-defender
```

**Step 4: Get Instance IP**

```bash
aws cloudformation describe-stacks \
  --stack-name elb-ddos-defender \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceIP`].OutputValue' \
  --output text
```

---

### Method 5: Terraform Deployment

**Step 1: Clone Repository**

```bash
git clone https://github.com/acchitty/Network-Tools.git
cd Network-Tools/ELB_DDoS_Defender/terraform
```

**Step 2: Configure Variables**

```bash
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Step 3: Deploy**

```bash
terraform init
terraform plan
terraform apply
```

---

## ⚙️ Configuration

### Basic Configuration

Edit `/opt/elb-ddos-defender/config.yaml`:

```yaml
# Minimal configuration
aws:
  region: us-east-1

load_balancers:
  - name: my-alb
    arn: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/abc123

email:
  from: alerts@example.com
  to: security@example.com
  
monitoring:
  enabled: true
  interval: 1  # seconds
```

### Advanced Configuration

```yaml
# Full configuration with all options
aws:
  region: us-east-1
  profile: default  # Optional

# Load balancers to monitor
load_balancers:
  - name: my-alb
    arn: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/abc123
    type: alb
    log_prefix: my-alb
    
  - name: my-nlb
    arn: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/net/my-nlb/def456
    type: nlb
    log_prefix: my-nlb

# Detection thresholds
thresholds:
  # Connection limits
  connections_per_second: 1000
  syn_packets_per_second: 5000
  udp_packets_per_second: 10000
  
  # HTTP thresholds
  http_requests_per_second: 2000
  http_errors_per_second: 100
  
  # Port scan detection
  ports_scanned_threshold: 20
  scan_time_window: 60  # seconds
  
  # ENI limits
  eni_connection_warning: 44000  # 80% of 55k limit
  eni_connection_critical: 52000  # 95% of 55k limit

# Email alerts (AWS SES)
email:
  enabled: true
  from: alerts@example.com
  to:
    - security@example.com
    - oncall@example.com
  ses_region: us-east-1
  
  # Email format
  format: html  # html or text
  include_pcap: true
  max_pcap_size: 10  # MB

# SNS notifications
sns:
  enabled: true
  topic_arn: arn:aws:sns:us-east-1:123456789012:ddos-alerts

# Slack integration
slack:
  enabled: false
  webhook_url: https://hooks.slack.com/services/xxx

# PagerDuty integration
pagerduty:
  enabled: false
  integration_key: your-key

# Monitoring settings
monitoring:
  enabled: true
  interval: 1  # seconds (real-time)
  
  # PyShark settings
  pyshark:
    enabled: true
    display_filter: "tcp or udp"
    capture_interface: eth0
    
  # Packet capture
  pcap:
    enabled: true
    directory: /var/log/pcaps
    max_size: 100  # MB per file
    rotation: 10  # keep last 10 files
    
  # CloudWatch integration
  cloudwatch:
    enabled: true
    log_group: /aws/elb-ddos-defender
    metrics_namespace: ELBDDoSDefender

# Logging
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: /var/log/elb-ddos-defender/defender.log
  max_size: 100  # MB
  backup_count: 10

# Automated response
auto_response:
  enabled: false  # Requires manual approval
  
  # NACL rules
  create_nacl_rules: false
  nacl_rule_priority: 100
  
  # Security group updates
  update_security_groups: false
  
  # WAF rules
  create_waf_rules: false

# Threat intelligence
threat_intel:
  enabled: true
  
  # IP reputation checks
  check_reputation: true
  
  # GeoIP lookup
  geoip_enabled: true
  
  # WHOIS lookup
  whois_enabled: true
  
  # Known botnet lists
  botnet_lists:
    - https://rules.emergingthreats.net/blockrules/compromised-ips.txt

# Reporting
reporting:
  # Report formats
  formats:
    - html
    - json
    - pdf
  
  # Report storage
  s3_bucket: my-ddos-reports
  s3_prefix: reports/
  
  # Report retention
  retention_days: 90
```

---

## ✅ Verification

### Check Installation

```bash
# Check service status
sudo systemctl status elb-ddos-defender

# Expected output:
● elb-ddos-defender.service - ELB DDoS Defender
   Loaded: loaded (/etc/systemd/system/elb-ddos-defender.service)
   Active: active (running) since Sun 2026-02-22 14:00:00 EST
```

### Check Logs

```bash
# View real-time logs
sudo tail -f /var/log/elb-ddos-defender/defender.log

# Expected output:
[2026-02-22 14:00:00] [INFO] ELB DDoS Defender started
[2026-02-22 14:00:01] [INFO] Monitoring load balancer: my-alb
[2026-02-22 14:00:01] [INFO] Discovered 3 ELB node ENIs
[2026-02-22 14:00:01] [INFO] Discovered 4 target ENIs
[2026-02-22 14:00:02] [INFO] PyShark capture started on eth0
[2026-02-22 14:00:02] [INFO] Real-time monitoring active
```

### Test Alert

```bash
# Send test alert
sudo /opt/elb-ddos-defender/test-alert.sh

# Check email
# You should receive a test email within 1 minute
```

### Check CloudWatch

```bash
# View metrics
aws cloudwatch get-metric-statistics \
  --namespace ELBDDoSDefender \
  --metric-name PacketsPerSecond \
  --start-time 2026-02-22T14:00:00Z \
  --end-time 2026-02-22T15:00:00Z \
  --period 60 \
  --statistics Average
```

---

## 🎯 Usage

### View Dashboard

```bash
# Open web dashboard
http://<instance-ip>:8080/dashboard

# Or use TUI dashboard (recommended)
sudo /opt/elb-ddos-defender/dashboard.sh
```

**TUI Dashboard Features:**
- 📊 Real-time load balancer metrics
- 🔌 ENI connection usage with progress bars
- 📈 Live statistics and bandwidth
- 🚨 Active alerts and warnings
- 📋 Recent events log
- 🌍 Threat intelligence
- ⌨️ Interactive controls

### Manual Packet Capture

```bash
# Capture 1000 packets
sudo /opt/elb-ddos-defender/capture.sh --count 1000

# Capture for 60 seconds
sudo /opt/elb-ddos-defender/capture.sh --duration 60

# Capture with filter
sudo /opt/elb-ddos-defender/capture.sh --filter "tcp port 80"
```

### Generate Report

```bash
# Generate report for last hour
sudo /opt/elb-ddos-defender/report.sh --last-hour

# Generate report for specific time range
sudo /opt/elb-ddos-defender/report.sh \
  --start "2026-02-22 14:00:00" \
  --end "2026-02-22 15:00:00"
```

### View Statistics

```bash
# Real-time statistics
sudo /opt/elb-ddos-defender/stats.sh

# Output:
┌─────────────────────────────────────────────┐
│ ELB DDoS Defender - Real-Time Statistics   │
├─────────────────────────────────────────────┤
│ Load Balancer: my-alb                      │
│ Status: HEALTHY ✓                          │
│                                             │
│ Traffic:                                    │
│   Packets/sec: 1,234                       │
│   Connections: 5,678                       │
│   Requests/sec: 890                        │
│                                             │
│ Targets:                                    │
│   Total: 4                                  │
│   Healthy: 4 ✓                             │
│   Unhealthy: 0                             │
│                                             │
│ Attacks Detected: 0                        │
│ Last Check: 2026-02-22 14:30:00           │
└─────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Service Won't Start

**Problem:** Service fails to start

**Solution:**
```bash
# Check logs for errors
sudo journalctl -u elb-ddos-defender -n 50

# Common issues:
# 1. Missing dependencies
sudo pip3 install -r /opt/elb-ddos-defender/requirements.txt

# 2. Permission issues
sudo chown -R root:root /opt/elb-ddos-defender
sudo chmod +x /opt/elb-ddos-defender/elb-ddos-defender.py

# 3. Configuration errors
sudo /opt/elb-ddos-defender/validate-config.sh
```

### No Packets Captured

**Problem:** PyShark not capturing packets

**Solution:**
```bash
# Check network interface
ip addr show

# Verify traffic mirroring
aws ec2 describe-traffic-mirror-sessions

# Test packet capture manually
sudo tcpdump -i eth0 -c 10

# Check permissions
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.11
```

### Emails Not Sending

**Problem:** Not receiving email alerts

**Solution:**
```bash
# Verify SES configuration
aws ses verify-email-identity --email-address alerts@example.com

# Check SES sending limits
aws ses get-send-quota

# Test email manually
sudo /opt/elb-ddos-defender/test-email.sh

# Check logs
sudo grep "email" /var/log/elb-ddos-defender/defender.log
```

### High CPU Usage

**Problem:** Defender using too much CPU

**Solution:**
```bash
# Reduce monitoring frequency
sudo nano /opt/elb-ddos-defender/config.yaml
# Change: interval: 5  # from 1 to 5 seconds

# Disable PyShark deep inspection
# Change: pyshark.enabled: false

# Use tcpdump only
# Change: use_tcpdump_only: true

# Restart service
sudo systemctl restart elb-ddos-defender
```

### False Positives

**Problem:** Too many false attack alerts

**Solution:**
```bash
# Adjust thresholds
sudo nano /opt/elb-ddos-defender/config.yaml

# Increase thresholds:
thresholds:
  connections_per_second: 5000  # from 1000
  http_requests_per_second: 10000  # from 2000

# Restart service
sudo systemctl restart elb-ddos-defender
```

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Internet Traffic                     │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Load Balancer (ALB/NLB/CLB)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ ELB Node │  │ ELB Node │  │ ELB Node │             │
│  │  (AZ-1)  │  │  (AZ-2)  │  │  (AZ-3)  │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
└───────┼─────────────┼─────────────┼────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                     ↓
        ┌────────────────────────────┐
        │  VPC Traffic Mirroring     │
        └────────────┬───────────────┘
                     ↓
        ┌────────────────────────────┐
        │  ELB DDoS Defender EC2     │
        │                            │
        │  ┌──────────────────────┐  │
        │  │   PyShark Capture    │  │
        │  │   (Real-time)        │  │
        │  └──────────┬───────────┘  │
        │             ↓               │
        │  ┌──────────────────────┐  │
        │  │  Analysis Engine     │  │
        │  │  - Port Scan         │  │
        │  │  - DDoS Detection    │  │
        │  │  - Threat Intel      │  │
        │  └──────────┬───────────┘  │
        │             ↓               │
        │  ┌──────────────────────┐  │
        │  │  Alert System        │  │
        │  │  - Email (SES)       │  │
        │  │  - SNS               │  │
        │  │  - CloudWatch        │  │
        │  └──────────────────────┘  │
        └────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │  Target EC2 Instances      │
        │  ┌────┐ ┌────┐ ┌────┐     │
        │  │ i1 │ │ i2 │ │ i3 │     │
        │  └────┘ └────┘ └────┘     │
        └────────────────────────────┘
```

### Component Overview

| Component | Purpose | Technology |
|-----------|---------|------------|
| **PyShark** | Real-time packet capture | Wireshark + Python |
| **Analysis Engine** | Attack detection | Python + ML |
| **Alert System** | Notifications | SES, SNS, Slack |
| **CloudWatch** | Metrics & logs | AWS CloudWatch |
| **Storage** | PCAP & reports | S3 + Local |

---

## ❓ FAQ

### Q: How much does this cost?

**A:** Minimal costs:
- EC2 instance: ~$30/month (t3.medium)
- VPC Traffic Mirroring: ~$0.015/GB
- CloudWatch: ~$5/month
- SES: First 62,000 emails free
- **Total: ~$35-50/month**

### Q: Does this block attacks automatically?

**A:** By default, NO. It alerts you and provides recommendations. You can enable auto-blocking in config (requires approval).

### Q: Can I monitor multiple load balancers?

**A:** Yes! Add multiple load balancers in `config.yaml`.

### Q: Does this work with GWLB?

**A:** Yes! Supports ALB, NLB, CLB, and GWLB.

### Q: How much traffic can it handle?

**A:** Up to 100,000 packets/second on t3.medium. Use larger instance for more.

### Q: Does it affect my application performance?

**A:** No. Traffic mirroring is passive - no impact on your application.

### Q: Can I use this in production?

**A:** Yes! Designed for production use with 24/7 monitoring.

### Q: How do I update?

**A:**
```bash
cd /opt/Network-Tools/ELB_DDoS_Defender
sudo git pull
sudo systemctl restart elb-ddos-defender
```

### Q: Can I customize detection rules?

**A:** Yes! Edit thresholds in `config.yaml` or add custom detectors in `detectors/`.

### Q: Does it integrate with AWS Shield?

**A:** Yes! Works alongside AWS Shield for enhanced protection.

---

## 📞 Support

### Getting Help

**Documentation:**
- 📖 Full docs: https://github.com/acchitty/Network-Tools/tree/main/ELB_DDoS_Defender/docs
- 📝 Examples: https://github.com/acchitty/Network-Tools/tree/main/ELB_DDoS_Defender/docs/EXAMPLES.md

**Community:**
- 💬 GitHub Issues: https://github.com/acchitty/Network-Tools/issues
- 📧 Email: support@example.com

**Emergency:**
- 🚨 For active attacks, contact AWS Support immediately
- ☎️ AWS Support: 1-866-947-7829

---

## 🎉 Next Steps

After installation:

1. ✅ **Verify monitoring** - Check dashboard and logs
2. ✅ **Test alerts** - Run test-alert.sh
3. ✅ **Review thresholds** - Adjust for your traffic
4. ✅ **Set up VPC Traffic Mirroring** - See setup guide
5. ✅ **Configure auto-response** (optional)
6. ✅ **Schedule regular reports**

**You're now protected against DDoS attacks!** 🛡️

---

*Last updated: 2026-02-22*
*Version: 2.0*
