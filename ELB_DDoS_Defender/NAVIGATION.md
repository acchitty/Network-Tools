# 🧭 ELB DDoS Defender - Documentation Navigator

## Where Do I Start?

### 👋 I'm New Here
**Start with:** [README.md](README.md)
- Overview of features
- Quick start options
- What it monitors

**Then:** [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)
- Compare 4 deployment methods
- Choose what fits your workflow
- See time estimates

**Finally:** Pick your method:
- [install.sh](install.sh) - Automated (5 min)
- [MANUAL_INSTALLATION.md](MANUAL_INSTALLATION.md) - Manual (30 min)
- [cloudformation/README.md](cloudformation/README.md) - CloudFormation (10 min)
- [terraform/README.md](terraform/README.md) - Terraform (5 min)

### ⚡ I Want Quick Setup (5 Minutes)
**Option 1 - Automated:**
```bash
curl -sSL https://raw.githubusercontent.com/.../install.sh | sudo bash
```

**Option 2 - Terraform:**
```bash
cd terraform/ && terraform apply
```

**Then:** [ACCESS_GUIDE.md](ACCESS_GUIDE.md) to connect

### 🏗️ I Want Production Deployment
**Follow this path:**
1. [README.md](README.md) - Understand the system
2. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Review architecture
3. [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md) - Choose method
4. [terraform/README.md](terraform/README.md) or [cloudformation/README.md](cloudformation/README.md)
5. [docs/SES_SETUP.md](docs/SES_SETUP.md) - Configure email alerts
6. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Daily operations

### 📖 I Need Daily Operations Reference
**Use:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- Essential commands
- Common tasks
- Quick troubleshooting

### 🔧 I'm Having Issues
**Check:** 
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) - Common issues
- [ACCESS_GUIDE.md](ACCESS_GUIDE.md) - Connection problems
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick fixes
- Method-specific guides:
  - [MANUAL_INSTALLATION.md](MANUAL_INSTALLATION.md) - Step troubleshooting
  - [terraform/README.md](terraform/README.md) - Terraform issues

### 🏛️ I Want to Understand the Architecture
**Read:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- System design
- Component details
- Data flow
- Scalability

### 📧 I Need to Set Up Email Alerts
**Follow:** [docs/SES_SETUP.md](docs/SES_SETUP.md)
- AWS SES configuration
- Email verification
- Testing alerts

### 🐳 I Want to Use Docker
**See:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#method-3-docker-installation)
- Docker installation
- Container configuration
- Running the container

### ☁️ I Want Infrastructure as Code
**Choose:**
- **CloudFormation:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#method-4-cloudformation-deployment)
- **Terraform:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#method-5-terraform-deployment)

---

## 📚 Complete Documentation Map

```
ELB DDoS Defender Documentation
│
├─ 🏠 README.md
│  └─ Overview, features, quick start
│
├─ ⚡ QUICKSTART.md
│  └─ 5-minute installation
│
├─ 📖 DEPLOYMENT_GUIDE.md
│  ├─ Prerequisites
│  ├─ 5 Installation Methods
│  ├─ Configuration
│  ├─ Verification
│  ├─ Usage
│  ├─ Troubleshooting
│  ├─ Architecture
│  └─ FAQ
│
├─ 📋 QUICK_REFERENCE.md
│  ├─ Installation commands
│  ├─ Service management
│  ├─ Monitoring
│  ├─ Configuration
│  └─ Common issues
│
└─ 📁 docs/
   ├─ 🏗️ ARCHITECTURE.md
   │  ├─ System overview
   │  ├─ Component details
   │  ├─ Data flow
   │  ├─ Monitoring layers
   │  ├─ Scalability
   │  ├─ High availability
   │  └─ Security
   │
   ├─ 🚀 DEPLOYMENT.md
   │  └─ Deployment details
   │
   ├─ 📦 INSTALLATION.md
   │  └─ Installation guide
   │
   ├─ 📧 SES_SETUP.md
   │  └─ Email configuration
   │
   └─ 🔍 PACKET_CORRELATION.md
      └─ Packet analysis
```

---

## 🎯 Quick Links by Task

### Installation
- [One-command install](QUICKSTART.md)
- [Manual install](DEPLOYMENT_GUIDE.md#method-2-manual-installation)
- [Docker install](DEPLOYMENT_GUIDE.md#method-3-docker-installation)
- [CloudFormation](DEPLOYMENT_GUIDE.md#method-4-cloudformation-deployment)
- [Terraform](DEPLOYMENT_GUIDE.md#method-5-terraform-deployment)

### Configuration
- [Basic config](DEPLOYMENT_GUIDE.md#basic-configuration)
- [Advanced config](DEPLOYMENT_GUIDE.md#advanced-configuration)
- [Email setup](docs/SES_SETUP.md)
- [Tuning](QUICK_REFERENCE.md#tuning)

### Operations
- [Start/stop service](QUICK_REFERENCE.md#service-management)
- [View logs](QUICK_REFERENCE.md#service-management)
- [Monitor status](QUICK_REFERENCE.md#monitoring)
- [Generate reports](QUICK_REFERENCE.md#reports)

### Troubleshooting
- [Service won't start](DEPLOYMENT_GUIDE.md#service-wont-start)
- [No packets captured](DEPLOYMENT_GUIDE.md#no-packets-captured)
- [Emails not sending](DEPLOYMENT_GUIDE.md#emails-not-sending)
- [High CPU usage](DEPLOYMENT_GUIDE.md#high-cpu-usage)
- [False positives](DEPLOYMENT_GUIDE.md#false-positives)

### Understanding
- [Architecture](docs/ARCHITECTURE.md)
- [How it works](docs/ARCHITECTURE.md#data-flow)
- [Monitoring layers](docs/ARCHITECTURE.md#monitoring-layers)
- [Scalability](docs/ARCHITECTURE.md#scalability)

---

## 💡 Tips for Navigation

### For Beginners
1. Start with README.md
2. Follow DEPLOYMENT_GUIDE.md
3. Keep QUICK_REFERENCE.md handy

### For Experienced Users
1. Jump to QUICK_REFERENCE.md
2. Use DEPLOYMENT_GUIDE.md for specific tasks
3. Refer to ARCHITECTURE.md when needed

### For Troubleshooting
1. Check QUICK_REFERENCE.md first
2. Then DEPLOYMENT_GUIDE.md troubleshooting section
3. Review ARCHITECTURE.md if issue persists

### For Production
1. Read ARCHITECTURE.md first
2. Follow DEPLOYMENT_GUIDE.md (CloudFormation/Terraform)
3. Configure using docs/SES_SETUP.md
4. Operate using QUICK_REFERENCE.md

---

## 🔍 Search by Keyword

| Looking for... | Go to... |
|----------------|----------|
| Installation | DEPLOYMENT_GUIDE.md |
| Quick setup | QUICKSTART.md |
| Commands | QUICK_REFERENCE.md |
| Architecture | docs/ARCHITECTURE.md |
| Email setup | docs/SES_SETUP.md |
| Troubleshooting | DEPLOYMENT_GUIDE.md |
| Configuration | DEPLOYMENT_GUIDE.md |
| Docker | DEPLOYMENT_GUIDE.md |
| CloudFormation | DEPLOYMENT_GUIDE.md |
| Terraform | DEPLOYMENT_GUIDE.md |
| Monitoring | QUICK_REFERENCE.md |
| Reports | QUICK_REFERENCE.md |
| Performance | docs/ARCHITECTURE.md |
| Scalability | docs/ARCHITECTURE.md |
| Security | docs/ARCHITECTURE.md |

---

## 📞 Still Can't Find What You Need?

1. **Search the docs:** Use Ctrl+F in your browser
2. **Check FAQ:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#faq)
3. **GitHub Issues:** https://github.com/acchitty/Network-Tools/issues
4. **Email:** support@example.com

---

*Documentation Navigator v1.0 - 2026-02-22*
