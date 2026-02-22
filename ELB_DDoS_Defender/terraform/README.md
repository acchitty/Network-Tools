# Terraform Deployment Guide

## Quick Start

### Interactive Setup (Recommended)

```bash
cd terraform/
./setup.sh
```

**The script will:**
1. ✅ List available VPCs and let you choose
2. ✅ List subnets in your VPC
3. ✅ Ask for SSH key (optional)
4. ✅ Ask for email address
5. ✅ Choose instance type
6. ✅ Show summary and confirm
7. ✅ Deploy automatically

**Time:** ~5 minutes

---

### Manual Setup

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Configure VPC, subnet, email

terraform init
terraform plan
terraform apply
```

**Time:** ~5 minutes

### 4. Connect

**Session Manager (recommended):**
```bash
aws ssm start-session --target $(terraform output -raw instance_id)
```

**SSH (if enabled):**
```bash
ssh -i your-key.pem ec2-user@$(terraform output -raw instance_public_ip)
```

### 5. Verify

```bash
# Wait for installation
tail -f /var/log/cloud-init-output.log

# Check service
sudo systemctl status elb-ddos-defender

# View dashboard
sudo /opt/elb-ddos-defender/dashboard.sh
```

---

## Configuration Options

### Instance Type

**Recommended:**
- `t3.medium` - Up to 5 load balancers
- `t3.large` - 5-10 load balancers
- `t3.xlarge` - 10+ load balancers

### Network Configuration

**Private Subnet (Recommended):**
```hcl
subnet_id        = "subnet-private-xxxxx"
enable_public_ip = false
key_name         = ""  # Use Session Manager
```

**Public Subnet:**
```hcl
subnet_id        = "subnet-public-xxxxx"
enable_public_ip = true
key_name         = "my-key-pair"
allowed_ssh_cidr = "1.2.3.4/32"  # Your IP only
```

### Tags

```hcl
tags = {
  Project     = "ELB-DDoS-Defender"
  Environment = "Production"
  CostCenter  = "Security"
  Owner       = "security-team@example.com"
}
```

---

## Outputs

After deployment, Terraform provides:

```bash
# View all outputs
terraform output

# Specific outputs
terraform output instance_id
terraform output session_manager_command
terraform output dashboard_command
```

**Available outputs:**
- `instance_id` - EC2 instance ID
- `instance_private_ip` - Private IP
- `instance_public_ip` - Public IP (if enabled)
- `security_group_id` - Security group ID
- `iam_role_arn` - IAM role ARN
- `cloudwatch_log_group` - Log group name
- `session_manager_command` - Connect command
- `ssh_command` - SSH command (if enabled)
- `dashboard_command` - Dashboard command
- `next_steps` - Post-deployment instructions

---

## What Gets Deployed

### Infrastructure
- ✅ EC2 instance (Amazon Linux 2023)
- ✅ IAM role with required permissions
- ✅ Security group with minimal access
- ✅ CloudWatch log group
- ✅ 30GB encrypted EBS volume

### Software
- ✅ Python 3.11
- ✅ All dependencies (tcpdump, tshark, PyShark)
- ✅ ELB DDoS Defender application
- ✅ TUI dashboard
- ✅ Systemd service
- ✅ VPC Traffic Mirroring (auto-configured)

### Security
- ✅ IMDSv2 enforced
- ✅ Encrypted EBS volume
- ✅ Least-privilege IAM role
- ✅ Session Manager enabled
- ✅ CloudTrail logging
- ✅ VPC-only traffic mirroring

---

## Cost Estimate

**Monthly cost for us-east-1:**

| Resource | Cost |
|----------|------|
| t3.medium instance | ~$30 |
| 30GB EBS gp3 | ~$2.40 |
| VPC Traffic Mirroring | ~$0.015/GB |
| CloudWatch Logs | ~$0.50/GB |
| **Total** | **~$35-40/month** |

*Traffic mirroring cost varies by traffic volume*

---

## Management

### Update Configuration

```bash
# Edit variables
nano terraform.tfvars

# Apply changes
terraform plan
terraform apply
```

### Scale Instance

```hcl
# In terraform.tfvars
instance_type = "t3.large"
```

```bash
terraform apply
```

### Destroy

```bash
terraform destroy
```

**Warning:** This deletes:
- EC2 instance
- Security group
- IAM role
- CloudWatch logs
- VPC Traffic Mirroring sessions

---

## Troubleshooting

### Installation Failed

**Check cloud-init logs:**
```bash
aws ssm start-session --target $(terraform output -raw instance_id)
tail -f /var/log/cloud-init-output.log
```

### Can't Connect via Session Manager

**Verify IAM role:**
```bash
terraform output iam_role_arn
```

**Check SSM agent:**
```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$(terraform output -raw instance_id)"
```

### Service Not Running

**Connect and check:**
```bash
sudo systemctl status elb-ddos-defender
sudo journalctl -u elb-ddos-defender -n 50
```

### Terraform State Issues

**Refresh state:**
```bash
terraform refresh
```

**Import existing resource:**
```bash
terraform import aws_instance.defender i-xxxxx
```

---

## Advanced Configuration

### Remote State

**S3 Backend:**
```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "elb-ddos-defender/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}
```

### Multiple Environments

```bash
# Development
terraform workspace new dev
terraform apply -var-file=dev.tfvars

# Production
terraform workspace new prod
terraform apply -var-file=prod.tfvars
```

### Custom AMI

```hcl
# main.tf
data "aws_ami" "custom" {
  most_recent = true
  owners      = ["self"]
  
  filter {
    name   = "name"
    values = ["my-custom-ami-*"]
  }
}

resource "aws_instance" "defender" {
  ami = data.aws_ami.custom.id
  # ...
}
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy ELB DDoS Defender

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: hashicorp/setup-terraform@v2
      
      - name: Terraform Init
        run: terraform init
        working-directory: terraform
      
      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: terraform
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### GitLab CI

```yaml
deploy:
  image: hashicorp/terraform:latest
  script:
    - cd terraform
    - terraform init
    - terraform apply -auto-approve
  only:
    - main
```

---

## Next Steps

1. **Configure Email Alerts:**
   - Verify SES email address
   - See: `docs/SES_SETUP.md`

2. **Monitor Dashboard:**
   ```bash
   sudo /opt/elb-ddos-defender/dashboard.sh
   ```

3. **Review Logs:**
   ```bash
   sudo tail -f /var/log/elb-ddos-defender/defender.log
   ```

4. **Set Up CloudWatch Alarms:**
   - See: `DEPLOYMENT_GUIDE.md`

---

*Terraform Guide v1.0 - 2026-02-22*
