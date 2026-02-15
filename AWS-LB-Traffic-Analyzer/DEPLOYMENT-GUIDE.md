# AWS Load Balancer Traffic Analyzer - Deployment Guide

Complete guide for deploying the traffic analyzer to EC2 instances behind AWS Load Balancers.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Method 1: SCP Upload](#installation-method-1-scp-upload-recommended)
3. [Installation Method 2: Manual Copy-Paste](#installation-method-2-manual-copy-paste)
4. [IAM Permissions Setup](#iam-permissions-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- EC2 instance running Amazon Linux 2023, Amazon Linux 2, Ubuntu, or RHEL
- Python 3.7 or higher (pre-installed on most AMIs)
- Root/sudo access
- EC2 instance behind ALB, NLB, CLB, or GWLB

### Optional (for CloudWatch features)
- EC2 IAM role with CloudWatch permissions
- boto3 Python library (installed during setup)

---

## Installation Method 1: SCP Upload (Recommended)

### Step 1: Prepare files on your laptop

Files should be in: `~/aws-lb-traffic-analyzer/`
- `aws-lb-traffic-analyzer.py`
- `traffic-analyzer.service`
- `README.md`
- `IAM-PERMISSIONS.md`
- `ENHANCEMENTS.md`

### Step 2: Upload to EC2

```bash
# Replace with your EC2 details
EC2_IP="44.200.159.107"  # Your EC2 public IP
KEY_FILE="~/Desktop/demokey2.pem"  # Your SSH key path

# Upload files
scp -i $KEY_FILE -r ~/aws-lb-traffic-analyzer ec2-user@$EC2_IP:~/
```

### Step 3: SSH to EC2

```bash
ssh -i $KEY_FILE ec2-user@$EC2_IP
```

### Step 4: Find network interface

```bash
ip link show
```

Look for interface name (usually `eth0`, `enX0`, `ens5`, or `ens6`). Note this for later.

### Step 5: Install dependencies

```bash
# Install pip
sudo yum install python3-pip -y

# Install boto3 (for CloudWatch features)
sudo pip3 install boto3
```

### Step 6: Update service file with your interface

```bash
cd ~/aws-lb-traffic-analyzer

# Replace 'eth0' with your actual interface name
INTERFACE="enX0"  # Change this to your interface
sed -i "s/eth0/$INTERFACE/g" traffic-analyzer.service

# Verify the change
cat traffic-analyzer.service | grep ExecStart
```

### Step 7: Install systemd service

```bash
# Copy service file
sudo cp traffic-analyzer.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start traffic-analyzer

# Enable auto-start on boot
sudo systemctl enable traffic-analyzer

# Check status
sudo systemctl status traffic-analyzer
```

### Step 8: Verify it's working

```bash
# Check service status
sudo systemctl status traffic-analyzer

# View live logs
sudo journalctl -u traffic-analyzer -f

# Check error logs
ls -lh ~/aws-lb-traffic-analyzer/logs/
cat ~/aws-lb-traffic-analyzer/logs/errors_$(date +%Y-%m-%d).log
```

**✅ Installation complete!**

---

## Installation Method 2: Manual Copy-Paste

Use this method if you cannot use SCP (no direct SSH access, bastion host issues, etc.)

### Step 1: SSH to EC2

```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
```

### Step 2: Create directory

```bash
mkdir -p ~/aws-lb-traffic-analyzer
cd ~/aws-lb-traffic-analyzer
```

### Step 3: Create the Python script

```bash
nano aws-lb-traffic-analyzer.py
```

**Copy the entire contents of `aws-lb-traffic-analyzer.py` from your laptop and paste into nano.**

- Press `Ctrl+X` to exit
- Press `Y` to save
- Press `Enter` to confirm

### Step 4: Make script executable

```bash
chmod +x aws-lb-traffic-analyzer.py
```

### Step 5: Find network interface

```bash
ip link show
```

Note the interface name (e.g., `eth0`, `enX0`, `ens5`).

### Step 6: Create service file

```bash
nano traffic-analyzer.service
```

**Paste this content (replace `enX0` with your interface):**

```ini
[Unit]
Description=AWS Load Balancer Traffic Analyzer
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/ec2-user/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py -i enX0 -s 10 --enable-cloudwatch
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- Press `Ctrl+X`, `Y`, `Enter` to save

### Step 7: Install dependencies

```bash
# Install pip
sudo yum install python3-pip -y

# Install boto3
sudo pip3 install boto3
```

### Step 8: Install and start service

```bash
# Copy service file
sudo cp traffic-analyzer.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start traffic-analyzer

# Enable auto-start
sudo systemctl enable traffic-analyzer

# Check status
sudo systemctl status traffic-analyzer
```

### Step 9: Verify it's working

```bash
# View live logs
sudo journalctl -u traffic-analyzer -f

# Check error logs
ls -lh ~/aws-lb-traffic-analyzer/logs/
```

**✅ Installation complete!**

---

## IAM Permissions Setup

### Required for CloudWatch Features

Your EC2 instance IAM role needs these permissions:

#### Step 1: Find your EC2 instance role

```bash
# AWS Console
EC2 > Instances > Select your instance > Security tab > IAM Role
```

#### Step 2: Add IAM policy

**AWS Console:**
1. Go to IAM > Roles
2. Find your EC2 instance role
3. Click "Add permissions" > "Create inline policy"
4. Click "JSON" tab
5. Paste the policy below
6. Name it: `TrafficAnalyzerCloudWatch`
7. Click "Create policy"

**IAM Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchMetricsAccess",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "LBTrafficAnalyzer"
        }
      }
    },
    {
      "Sid": "CloudWatchLogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/ec2/traffic-analyzer:*"
    }
  ]
}
```

#### Step 3: Verify permissions

```bash
# On EC2 instance
aws cloudwatch put-metric-data \
  --namespace LBTrafficAnalyzer \
  --metric-name TestMetric \
  --value 1 \
  --region us-east-1

# Should return nothing (success)
# If you see "AccessDenied", permissions are missing
```

### Without CloudWatch (Basic Mode)

If you don't want CloudWatch integration, remove `--enable-cloudwatch` from the service file:

```bash
sudo nano /etc/systemd/system/traffic-analyzer.service
```

Change:
```
ExecStart=/usr/bin/python3 /home/ec2-user/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py -i enX0 -s 10 --enable-cloudwatch
```

To:
```
ExecStart=/usr/bin/python3 /home/ec2-user/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py -i enX0 -s 10
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart traffic-analyzer
```

---

## Verification

### Check Service Status

```bash
# Is it running?
sudo systemctl status traffic-analyzer

# Should show: Active: active (running)
```

### View Live Logs

```bash
# View all logs (Ctrl+C to stop)
sudo journalctl -u traffic-analyzer -f

# View last 50 lines
sudo journalctl -u traffic-analyzer -n 50

# View errors only
sudo journalctl -u traffic-analyzer | grep -E "ERROR|TIMEOUT|FAIL"
```

### Check Error Logs

```bash
# List log files
ls -lh ~/aws-lb-traffic-analyzer/logs/

# View today's errors
cat ~/aws-lb-traffic-analyzer/logs/errors_$(date +%Y-%m-%d).log

# Watch errors in real-time
tail -f ~/aws-lb-traffic-analyzer/logs/errors_*.log
```

### Check CloudWatch (if enabled)

**Metrics:**
```
AWS Console > CloudWatch > Metrics > Custom Namespaces > LBTrafficAnalyzer
```

**Logs:**
```
AWS Console > CloudWatch > Logs > Log groups > /aws/ec2/traffic-analyzer
```

**CLI:**
```bash
# List metrics
aws cloudwatch list-metrics --namespace LBTrafficAnalyzer --region us-east-1

# View logs
aws logs tail "/aws/ec2/traffic-analyzer" --follow --region us-east-1
```

---

## Troubleshooting

### Service won't start

```bash
# Check for errors
sudo journalctl -u traffic-analyzer -n 50

# Common issues:
# 1. Wrong interface name
# 2. Python not found
# 3. Permission denied
```

**Fix wrong interface:**
```bash
# Find correct interface
ip link show

# Update service file
sudo nano /etc/systemd/system/traffic-analyzer.service
# Change -i eth0 to your interface

sudo systemctl daemon-reload
sudo systemctl restart traffic-analyzer
```

### No traffic captured

```bash
# Verify interface is correct
ip link show

# Check if interface is UP
ip addr show

# Verify traffic is reaching EC2
sudo tcpdump -i enX0 -c 10
```

### Permission denied errors

```bash
# Script needs root to capture packets
# Verify service runs as root
sudo systemctl status traffic-analyzer | grep "Main PID"

# Check file permissions
ls -l ~/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py
```

### CloudWatch not working

```bash
# Check IAM permissions
aws sts get-caller-identity

# Test CloudWatch access
aws cloudwatch put-metric-data \
  --namespace LBTrafficAnalyzer \
  --metric-name TestMetric \
  --value 1 \
  --region us-east-1

# Check logs for errors
sudo journalctl -u traffic-analyzer | grep -i "cloudwatch\|permission\|denied"
```

### boto3 not found

```bash
# Install boto3
sudo pip3 install boto3

# Verify installation
python3 -c "import boto3; print('✓ boto3 installed')"

# Restart service
sudo systemctl restart traffic-analyzer
```

### High CPU usage

```bash
# Check current sample rate
sudo systemctl status traffic-analyzer | grep ExecStart

# Increase sample rate (analyze fewer packets)
sudo nano /etc/systemd/system/traffic-analyzer.service
# Change -s 10 to -s 20 (1 in 20 packets)

sudo systemctl daemon-reload
sudo systemctl restart traffic-analyzer
```

### Logs filling up disk

```bash
# Check log size
du -sh ~/aws-lb-traffic-analyzer/logs/

# Logs auto-cleanup after 7 days
# To manually clean old logs:
find ~/aws-lb-traffic-analyzer/logs/ -name "*.log" -mtime +7 -delete
```

---

## Configuration Options

### Command-line Arguments

```bash
# View all options
python3 ~/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py --help
```

**Available options:**
- `-i, --interface` - Network interface (default: eth0)
- `-s, --sample-rate` - Sample 1 in N packets (default: 10)
- `-l, --log-dir` - Log directory (default: logs)
- `-t, --timeout` - Timeout threshold in seconds (default: 5)
- `--enable-cloudwatch` - Enable CloudWatch metrics and logs
- `--sns-topic` - SNS topic ARN for alerts

**Example custom configuration:**
```bash
ExecStart=/usr/bin/python3 /home/ec2-user/aws-lb-traffic-analyzer/aws-lb-traffic-analyzer.py -i ens5 -s 20 -t 10 --enable-cloudwatch
```

This would:
- Monitor interface `ens5`
- Sample 1 in 20 packets (lower CPU)
- 10-second timeout threshold
- Send to CloudWatch

---

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop traffic-analyzer
sudo systemctl disable traffic-analyzer

# Remove service file
sudo rm /etc/systemd/system/traffic-analyzer.service
sudo systemctl daemon-reload

# Remove files
rm -rf ~/aws-lb-traffic-analyzer

# Uninstall boto3 (optional)
sudo pip3 uninstall boto3 -y
```

---

## Support

**View documentation on EC2:**
```bash
cd ~/aws-lb-traffic-analyzer
cat README.md
cat IAM-PERMISSIONS.md
cat ENHANCEMENTS.md
```

**Common commands:**
```bash
# Start
sudo systemctl start traffic-analyzer

# Stop
sudo systemctl stop traffic-analyzer

# Restart
sudo systemctl restart traffic-analyzer

# Status
sudo systemctl status traffic-analyzer

# Logs
sudo journalctl -u traffic-analyzer -f

# Error logs
cat ~/aws-lb-traffic-analyzer/logs/errors_$(date +%Y-%m-%d).log
```

---

## What Gets Monitored

**Protocols:**
- TCP (connections, errors, timeouts)
- UDP (connections)
- HTTP (requests, responses, errors)
- HTTPS (encrypted traffic metadata)

**Load Balancers:**
- Application Load Balancer (ALB)
- Network Load Balancer (NLB)
- Classic Load Balancer (CLB)
- Gateway Load Balancer (GWLB)

**Errors Detected:**
- Connection timeouts (SYN timeout)
- Application timeouts (no HTTP response)
- Health check failures
- TCP resets (RST)
- HTTP errors (4xx, 5xx)
- Traffic loops
- Slow connections

**Metrics Sent to CloudWatch:**
- TimeoutCount
- TCPErrorCount
- HealthCheckFailures
- LoopCount
- ConnectionCount

**Logs Sent to CloudWatch:**
- All error events in real-time

---

## Resource Usage

**Typical usage:**
- CPU: 2-4% (with sample rate 1/10)
- Memory: 80-150 MB
- Disk: 1-50 MB/day (error logs)
- Network: ~1 KB/minute (CloudWatch API calls)

**Very lightweight - safe for production use!**
