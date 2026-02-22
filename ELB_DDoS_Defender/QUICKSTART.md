# ELB DDoS Defender - Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Option 1: CloudFormation (Recommended)

```bash
aws cloudformation create-stack \
  --stack-name elb-ddos-defender \
  --template-body file://cloudformation-template.yaml \
  --parameters \
      ParameterKey=EmailAddress,ParameterValue=alerts@example.com \
      ParameterKey=VpcId,ParameterValue=vpc-xxx \
      ParameterKey=SubnetId,ParameterValue=subnet-xxx \
      ParameterKey=KeyName,ParameterValue=my-key \
      ParameterKey=LoadBalancerNames,ParameterValue="my-alb,my-nlb" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Wait 15 minutes** for deployment to complete.

### Option 2: Terraform

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init
terraform apply
```

### Option 3: Manual

```bash
# SSH to EC2 instance
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/elb-ddos-defender/main/complete-install.sh -o install.sh
chmod +x install.sh
sudo ./install.sh alerts@example.com

# Enable logs and mirroring
cd /opt/elb-ddos-defender
sudo ./setup-logs-and-mirroring.sh
```

## ✅ Verify Installation

```bash
# Check service
sudo systemctl status elb-ddos-defender

# View logs
sudo tail -f /var/log/elb-ddos-defender.log

# Check traffic mirroring
sudo tcpdump -i any -n udp port 4789 -c 10
```

## 📚 Full Documentation

- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Complete deployment guide
- **[COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)** - Architecture and features
- **[SES_SETUP.md](docs/SES_SETUP.md)** - Email configuration

## 🎯 What You Get

✅ EC2 monitoring instance
✅ ALB/NLB access logs enabled
✅ VPC Flow Logs enabled (30+ fields)
✅ VPC Traffic Mirroring configured
✅ Email alerts with PDF reports
✅ CloudWatch metrics per load balancer
✅ Automatic DDoS detection
