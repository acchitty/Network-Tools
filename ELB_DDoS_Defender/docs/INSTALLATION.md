# ELB DDoS Defender - Installation Guide

## Quick Installation

### One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/elb-ddos-defender/main/complete-install.sh | sudo bash -s -- your-email@example.com
```

## Prerequisites

### EC2 Instance Requirements

- **Instance Type**: t3.medium or larger
- **Operating System**: Amazon Linux 2023 or Ubuntu 22.04
- **Network**: Must be in the same VPC as your load balancers
- **Storage**: At least 20GB for logs and PCAPs
- **Key Pair**: For SSH access

### AWS Permissions

The installer will create an IAM role with these permissions:
- CloudWatch Logs (read/write)
- CloudWatch Metrics (write)
- Elastic Load Balancing (describe)
- EC2 (describe, create traffic mirroring)
- SES (send email, verify identity)
- S3 (read access logs)
- WAF (create rules)
- GuardDuty (read findings)

## Step-by-Step Installation

### Step 1: Launch EC2 Instance

1. Go to EC2 Console
2. Click "Launch Instance"
3. Select Amazon Linux 2023 AMI
4. Choose t3.medium instance type
5. Select your VPC (same as load balancers)
6. Select any subnet in the VPC
7. Create or select a key pair
8. Launch instance

### Step 2: SSH to Instance

```bash
ssh -i your-key.pem ec2-user@your-instance-ip
```

### Step 3: Run Installer

```bash
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/elb-ddos-defender/main/complete-install.sh | sudo bash -s -- your-email@example.com
```

### Step 4: Select Load Balancers

The installer will show all available load balancers:

```
Available Load Balancers:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1] my-application-alb (ALB)
  [2] my-network-nlb (NLB)
  [3] my-classic-lb (CLB)
  [4] my-gateway-gwlb (GWLB)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enter load balancers to monitor (comma-separated numbers, or 'all'):
Selection: 
```

**Options:**
- Enter `1,2` to monitor only ALB and NLB
- Enter `all` to monitor all load balancers
- Enter `1` to monitor only one load balancer

### Step 5: Verify Email

1. Check your email inbox
2. Look for "Amazon SES Email Address Verification Request"
3. Click the verification link in the email

### Step 6: Verify Installation

```bash
# Check service status
sudo systemctl status elb-ddos-defender

# View logs
sudo tail -f /var/log/elb-ddos-defender.log
```

## What Gets Installed

### System Packages
- tcpdump, tshark, mtr, whois, git
- Python 3 and pip
- GeoIP database

### Python Packages
- boto3 (AWS SDK)
- scapy (packet analysis)
- pyyaml (configuration)
- jinja2 (report templates)
- weasyprint (PDF generation)
- reportlab (PDF library)

### AWS Resources
- IAM Role: `ELBDDoSDefenderRole`
- IAM Instance Profile (attached to EC2)
- VPC Traffic Mirror Target
- VPC Traffic Mirror Filter
- VPC Traffic Mirror Sessions (one per load balancer)
- SES Email Verification

### Application Files
- `/opt/elb-ddos-defender/` - Application code
- `/opt/elb-ddos-defender/config.yaml` - Configuration
- `/var/log/elb-ddos-defender/` - Per-LB logs
- `/var/log/attack-reports/` - Per-LB reports
- `/var/log/pcaps/` - Per-LB packet captures
- `/etc/systemd/system/elb-ddos-defender.service` - Systemd service

## Post-Installation

### Verify Email is Working

```bash
# Check SES verification status
aws ses get-identity-verification-attributes --identities your-email@example.com

# Should show: VerificationStatus: Success
```

### Verify VPC Traffic Mirroring

```bash
# Check mirror sessions
aws ec2 describe-traffic-mirror-sessions

# Test packet capture
sudo tcpdump -i eth0 -n udp port 4789 -c 10
```

### View Configuration

```bash
cat /opt/elb-ddos-defender/config.yaml
```

## Troubleshooting Installation

### Issue: Email not verified

```bash
# Re-send verification
aws ses verify-email-identity --email-address your-email@example.com
```

### Issue: Service won't start

```bash
# Check logs
sudo journalctl -u elb-ddos-defender -n 50

# Check Python dependencies
pip3 list | grep -E "boto3|scapy|yaml"
```

### Issue: No load balancers detected

```bash
# Check AWS credentials
aws sts get-caller-identity

# List load balancers manually
aws elbv2 describe-load-balancers
```

## Next Steps

After installation:
1. [Configure the application](CONFIGURATION.md)
2. [Read the user guide](USER_GUIDE.md)
3. [Test attack detection](USER_GUIDE.md#testing)
