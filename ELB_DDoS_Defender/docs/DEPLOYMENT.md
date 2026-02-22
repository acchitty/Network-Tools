# ELB DDoS Defender - Deployment Guide

Complete guide for deploying the ELB DDoS Defender using Infrastructure as Code (CloudFormation or Terraform) or manual installation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Option 1: CloudFormation Deployment](#option-1-cloudformation-deployment)
4. [Option 2: Terraform Deployment](#option-2-terraform-deployment)
5. [Option 3: Manual Installation](#option-3-manual-installation)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Verification](#verification)

---

## Prerequisites

### AWS Requirements

- AWS Account with appropriate permissions
- VPC with at least one subnet
- EC2 Key Pair for SSH access
- Load balancers (ALB/NLB/CLB/GWLB) to monitor
- Amazon SES configured (see [SES_SETUP.md](SES_SETUP.md))

### IAM Permissions Required

The user deploying this solution needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "cloudformation:*",
      "ec2:*",
      "iam:*",
      "s3:*",
      "logs:*",
      "elasticloadbalancing:*"
    ],
    "Resource": "*"
  }]
}
```

---

## Deployment Options

### Quick Comparison

| Feature | CloudFormation | Terraform | Manual |
|---------|---------------|-----------|--------|
| Setup Time | 15 min | 15 min | 30 min |
| Automation | Full | Full | Partial |
| Customization | Medium | High | Full |
| Best For | AWS-native | Multi-cloud | Testing |

---

## Option 1: CloudFormation Deployment

### Step 1: Prepare Parameters

Create a parameters file `cfn-parameters.json`:

```json
[
  {
    "ParameterKey": "EmailAddress",
    "ParameterValue": "alerts@example.com"
  },
  {
    "ParameterKey": "VpcId",
    "ParameterValue": "vpc-xxxxxxxxx"
  },
  {
    "ParameterKey": "SubnetId",
    "ParameterValue": "subnet-xxxxxxxxx"
  },
  {
    "ParameterKey": "KeyName",
    "ParameterValue": "my-key-pair"
  },
  {
    "ParameterKey": "InstanceType",
    "ParameterValue": "t3.medium"
  },
  {
    "ParameterKey": "LoadBalancerNames",
    "ParameterValue": "my-alb,my-nlb"
  }
]
```

### Step 2: Deploy Stack

```bash
aws cloudformation create-stack \
  --stack-name elb-ddos-defender \
  --template-body file://cloudformation-template.yaml \
  --parameters file://cfn-parameters.json \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Step 3: Monitor Deployment

```bash
# Watch stack creation
aws cloudformation describe-stacks \
  --stack-name elb-ddos-defender \
  --query 'Stacks[0].StackStatus' \
  --output text

# View events
aws cloudformation describe-stack-events \
  --stack-name elb-ddos-defender \
  --max-items 10
```

### Step 4: Get Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name elb-ddos-defender \
  --query 'Stacks[0].Outputs'
```

---

## Option 2: Terraform Deployment

### Step 1: Initialize Terraform

```bash
cd terraform/
terraform init
```

### Step 2: Configure Variables

Copy and edit the example file:

```bash
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

Edit values:

```hcl
aws_region = "us-east-1"
email_address = "alerts@example.com"
vpc_id = "vpc-xxxxxxxxx"
subnet_id = "subnet-xxxxxxxxx"
key_name = "my-key-pair"
instance_type = "t3.medium"
load_balancer_names = ["my-alb", "my-nlb"]
```

### Step 3: Plan Deployment

```bash
terraform plan
```

Review the resources that will be created.

### Step 4: Deploy

```bash
terraform apply
```

Type `yes` when prompted.

### Step 5: Get Outputs

```bash
terraform output
```

---

## Option 3: Manual Installation

### Step 1: Launch EC2 Instance

Launch an Amazon Linux 2023 instance with:
- Instance type: t3.medium or larger
- Storage: 50 GB gp3
- Security group: Allow UDP 4789 (VXLAN) and TCP 22 (SSH)

### Step 2: Attach IAM Role

Create and attach the IAM role from `cloudformation-template.yaml` (MonitoringRole section).

### Step 3: SSH to Instance

```bash
ssh -i your-key.pem ec2-user@<instance-ip>
```

### Step 4: Run Installation Script

```bash
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/elb-ddos-defender/main/complete-install.sh -o install.sh
chmod +x install.sh
sudo ./install.sh alerts@example.com
```

Follow the interactive prompts to:
1. Select load balancers to monitor
2. Configure thresholds
3. Verify email address

### Step 5: Enable Logs and Mirroring

```bash
cd /opt/elb-ddos-defender
sudo ./setup-logs-and-mirroring.sh
```

This script will:
- ✅ Check and enable ALB access logs
- ✅ Check and enable NLB connection logs
- ✅ Verify health check configuration
- ✅ Enable VPC Flow Logs with ALL custom fields
- ✅ Configure VPC Traffic Mirroring

---

## Post-Deployment Configuration

### 1. Verify Email Address

Check your email for SES verification:

```bash
aws ses get-identity-verification-attributes \
  --identities alerts@example.com \
  --region us-east-1
```

Click the verification link in the email.

### 2. Review Configuration

```bash
sudo nano /opt/elb-ddos-defender/config.yaml
```

Adjust thresholds per load balancer:

```yaml
load_balancers:
  - name: my-alb
    type: ALB
    enabled: true
    email_recipients:
      - alerts@example.com
    thresholds:
      connections_per_second: 100
      bandwidth_mbps: 500
      syn_packets_per_second: 50
      udp_packets_per_second: 100
```

### 3. Restart Service

```bash
sudo systemctl restart elb-ddos-defender
```

---

## Verification

### Check Service Status

```bash
sudo systemctl status elb-ddos-defender
```

Expected output:
```
● elb-ddos-defender.service - ELB DDoS Defender
   Loaded: loaded
   Active: active (running)
```

### View Logs

```bash
# Application logs
sudo tail -f /var/log/elb-ddos-defender.log

# Per-LB logs
sudo tail -f /var/log/elb-ddos-defender/my-alb/monitor.log
```

### Check VPC Traffic Mirroring

```bash
aws ec2 describe-traffic-mirror-sessions --region us-east-1
```

Should show active mirror sessions for each load balancer ENI.

### Check VPC Flow Logs

```bash
aws ec2 describe-flow-logs --region us-east-1
```

Should show flow logs enabled for your VPC.

### Test Packet Capture

```bash
sudo tcpdump -i any -n udp port 4789 -c 10
```

Should see VXLAN packets from load balancer traffic.

### Check CloudWatch Metrics

```bash
aws cloudwatch list-metrics \
  --namespace "ELB/Monitor" \
  --region us-east-1
```

Should show custom metrics for each load balancer.

### Test Email Alerts

Trigger a test alert:

```bash
sudo /opt/elb-ddos-defender/elb-ddos-defender.py --test-alert
```

Check your email for the test alert with PDF/HTML/JSON reports.

---

## Troubleshooting

### Issue: Service won't start

```bash
# Check logs
sudo journalctl -u elb-ddos-defender -n 50

# Check permissions
ls -la /opt/elb-ddos-defender/

# Reinstall
sudo ./complete-install.sh alerts@example.com
```

### Issue: No traffic mirroring packets

```bash
# Check mirror sessions
aws ec2 describe-traffic-mirror-sessions

# Check security group
aws ec2 describe-security-groups --group-ids <sg-id>

# Verify UDP 4789 is allowed
```

### Issue: Email not sending

```bash
# Check SES verification
aws ses get-identity-verification-attributes \
  --identities alerts@example.com

# Check IAM permissions
aws iam get-role-policy \
  --role-name ELBDDoSDefenderRole \
  --policy-name ELBDDoSDefenderPolicy
```

### Issue: Access logs not enabled

```bash
# Run setup script again
cd /opt/elb-ddos-defender
sudo ./setup-logs-and-mirroring.sh
```

---

## Cleanup

### CloudFormation

```bash
aws cloudformation delete-stack --stack-name elb-ddos-defender
```

### Terraform

```bash
cd terraform/
terraform destroy
```

### Manual

```bash
# Stop service
sudo systemctl stop elb-ddos-defender
sudo systemctl disable elb-ddos-defender

# Remove files
sudo rm -rf /opt/elb-ddos-defender
sudo rm /etc/systemd/system/elb-ddos-defender.service

# Delete traffic mirror sessions
aws ec2 describe-traffic-mirror-sessions \
  --query 'TrafficMirrorSessions[*].TrafficMirrorSessionId' \
  --output text | xargs -n1 aws ec2 delete-traffic-mirror-session --traffic-mirror-session-id

# Terminate EC2 instance
aws ec2 terminate-instances --instance-ids <instance-id>
```

---

## Next Steps

- Review [USER_GUIDE.md](USER_GUIDE.md) for operational procedures
- Configure [SES_SETUP.md](SES_SETUP.md) for production email
- Set up CloudWatch dashboards for monitoring
- Integrate with AWS WAF for automatic mitigation

---

## Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review CloudWatch Logs
3. Open GitHub issue with logs and configuration
