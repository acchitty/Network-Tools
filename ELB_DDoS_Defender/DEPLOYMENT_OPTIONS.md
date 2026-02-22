# ELB DDoS Defender - Deployment Options

Choose the deployment method that best fits your workflow:

---

## 🚀 Option A: Automated One-Click (5 minutes)

**Best for:** Quick deployment, testing, single instance

**Steps:**
1. Launch EC2 instance (Amazon Linux 2023, t3.medium)
2. SSH or Session Manager to instance
3. Run:
```bash
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
```

**What it does:**
- ✅ Auto-detects OS
- ✅ Installs all dependencies
- ✅ Auto-discovers load balancers
- ✅ Creates configuration
- ✅ Sets up VPC Traffic Mirroring
- ✅ Starts monitoring

**Time:** ~5 minutes  
**Interaction:** Zero (fully automated)  
**Documentation:** `install.sh`

---

## 📖 Option B: Manual Step-by-Step (30 minutes)

**Best for:** Learning, customization, understanding internals

**Steps:**
1. Launch EC2 instance
2. Follow 14 detailed steps in `MANUAL_INSTALLATION.md`
3. Each step includes:
   - Exact commands
   - Expected output
   - Verification
   - Troubleshooting

**What you learn:**
- ✅ Every component installed
- ✅ How configuration works
- ✅ VPC Traffic Mirroring setup
- ✅ Service management
- ✅ Full system understanding

**Time:** ~30 minutes  
**Interaction:** High (hands-on)  
**Documentation:** `MANUAL_INSTALLATION.md`

---

## ☁️ Option C: CloudFormation (10 minutes)

**Best for:** AWS-native deployments, repeatable infrastructure

**Steps:**

1. Clone repository
2. Run interactive setup:
```bash
cd cloudformation/
./setup.sh
```

**The script will ask you:**
- ✅ Which AWS region?
- ✅ Which VPC?
- ✅ Which subnet?
- ✅ Which SSH key? (optional)
- ✅ Email address for alerts
- ✅ Instance type (t3.medium/large/xlarge)
- ✅ Stack name

**Then automatically:**
- ✅ Creates CloudFormation stack
- ✅ Waits for completion
- ✅ Shows connection command
- ✅ Displays next steps

**What it creates:**
- ✅ EC2 instance
- ✅ IAM role
- ✅ Security group
- ✅ CloudWatch log group
- ✅ All configurations

**Time:** ~10 minutes  
**Interaction:** Minimal (form-based)  
**Documentation:** `cloudformation/README.md`

---

## 🏗️ Option D: Terraform (5 minutes)

**Best for:** Infrastructure as Code, version control, multi-environment

**Steps:**

1. Clone repository
2. Run interactive setup:
```bash
cd terraform/
./setup.sh
```

**The script will ask you:**
- ✅ Which AWS region?
- ✅ Which VPC?
- ✅ Which subnet?
- ✅ SSH key or Session Manager?
- ✅ Email address for alerts
- ✅ Instance type (t3.medium/large/xlarge)

**Then automatically:**
- ✅ Creates terraform.tfvars
- ✅ Runs terraform init
- ✅ Shows plan
- ✅ Deploys infrastructure
- ✅ Shows connection command

**What it creates:**
- ✅ Complete infrastructure
- ✅ IAM roles and policies
- ✅ Security groups
- ✅ CloudWatch logs
- ✅ Automated installation
- ✅ State management

**Time:** ~5 minutes  
**Interaction:** Minimal (config file)  
**Documentation:** `terraform/README.md`

**Advantages:**
- Version control infrastructure
- Multi-environment support
- Easy updates and rollbacks
- CI/CD integration
- State tracking

---

## 📊 Comparison Matrix

| Feature | Automated | Manual | CloudFormation | Terraform |
|---------|-----------|--------|----------------|-----------|
| **Time** | 5 min | 30 min | 10 min | 5 min |
| **Complexity** | Low | High | Medium | Medium |
| **Learning** | None | High | Low | Medium |
| **Repeatability** | Low | Low | High | High |
| **Version Control** | No | No | Yes | Yes |
| **Multi-Env** | No | No | Yes | Yes |
| **Customization** | Low | High | Medium | High |
| **Prerequisites** | None | None | AWS Console | Terraform CLI |
| **Best For** | Testing | Learning | AWS-native | IaC workflows |

---

## 🎯 Decision Guide

### Choose **Automated** if:
- ✅ You want to test quickly
- ✅ You're deploying one instance
- ✅ You don't need infrastructure tracking
- ✅ You want zero configuration

### Choose **Manual** if:
- ✅ You want to understand every step
- ✅ You need custom configuration
- ✅ You're learning the system
- ✅ You have specific requirements

### Choose **CloudFormation** if:
- ✅ You use AWS-native tools
- ✅ You need repeatable deployments
- ✅ You want AWS Console integration
- ✅ You're already using CloudFormation

### Choose **Terraform** if:
- ✅ You use Infrastructure as Code
- ✅ You need version control
- ✅ You manage multiple environments
- ✅ You want CI/CD integration
- ✅ You're already using Terraform

---

## 🔄 Migration Between Methods

### From Automated → Terraform
```bash
# Import existing instance
terraform import aws_instance.defender i-xxxxx
terraform import aws_security_group.defender sg-xxxxx
terraform import aws_iam_role.defender ELBDDoSDefenderRole
```

### From Manual → CloudFormation
1. Note all resource IDs
2. Create CloudFormation template
3. Import existing resources
4. Manage via CloudFormation

### From CloudFormation → Terraform
```bash
# Use cf2tf tool
cf2tf cloudformation-template.yaml > main.tf
terraform init
terraform import ...
```

---

## 📚 Documentation by Method

### Automated
- `install.sh` - Installation script
- `QUICK_REFERENCE.md` - Daily operations

### Manual
- `MANUAL_INSTALLATION.md` - Step-by-step guide
- `ACCESS_GUIDE.md` - Connection methods
- `QUICK_REFERENCE.md` - Commands

### CloudFormation
- `cloudformation/README.md` - Deployment guide
- `cloudformation/template.yaml` - Stack template
- `DEPLOYMENT_GUIDE.md` - Complete reference

### Terraform
- `terraform/README.md` - Deployment guide
- `terraform/main.tf` - Infrastructure code
- `terraform/terraform.tfvars.example` - Configuration
- `DEPLOYMENT_GUIDE.md` - Complete reference

---

## 💰 Cost (All Methods)

**Same cost regardless of deployment method:**

| Resource | Monthly Cost |
|----------|--------------|
| t3.medium instance | ~$30 |
| 30GB EBS gp3 | ~$2.40 |
| VPC Traffic Mirroring | ~$0.015/GB |
| CloudWatch Logs | ~$0.50/GB |
| **Total** | **~$35-40/month** |

---

## 🔐 Security (All Methods)

**All methods provide:**
- ✅ IMDSv2 enforced
- ✅ Encrypted EBS volumes
- ✅ Least-privilege IAM roles
- ✅ Session Manager support
- ✅ VPC-only traffic mirroring
- ✅ CloudTrail logging

---

## 🆘 Support

**Getting Help:**
- 📖 Read documentation for your method
- 🔍 Check `TROUBLESHOOTING.md`
- 💬 Open GitHub issue
- 📧 Contact support

**Common Issues:**
- Installation failures → Check logs
- Connection issues → Verify security groups
- Service not starting → Check systemd logs
- Dashboard not working → Install rich library

---

## ✅ Next Steps After Deployment

**Regardless of method:**

1. **Connect to instance:**
   - SSH or Session Manager
   - See `ACCESS_GUIDE.md`

2. **Verify installation:**
   ```bash
   sudo systemctl status elb-ddos-defender
   ```

3. **View dashboard:**
   ```bash
   sudo /opt/elb-ddos-defender/dashboard.sh
   ```

4. **Configure email alerts:**
   - Verify SES email
   - See `docs/SES_SETUP.md`

5. **Monitor logs:**
   ```bash
   sudo tail -f /var/log/elb-ddos-defender/defender.log
   ```

---

*Deployment Options Guide v1.0 - 2026-02-22*
