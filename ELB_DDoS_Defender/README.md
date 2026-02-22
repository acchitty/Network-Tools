# ELB DDoS Defender

**Real-time DDoS detection and protection for AWS Elastic Load Balancers**

Monitors ALB, NLB, CLB, and GWLB with advanced packet analysis, threat intelligence, and automated alerting.

---

## 🚀 Quick Start

### Choose Your Deployment Method

**Automated (5 minutes):**
```bash
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
```

**Terraform (5 minutes):**
```bash
cd terraform/ && terraform apply
```

**See all options:** [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)

---

## 📚 Documentation

### Getting Started
- **[Deployment Options](DEPLOYMENT_OPTIONS.md)** - Choose your method (Automated, Manual, CloudFormation, Terraform)
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete installation reference
- **[Manual Installation](MANUAL_INSTALLATION.md)** - Step-by-step with explanations
- **[Access Guide](ACCESS_GUIDE.md)** - How to connect to your instance

### Operations
- **[Quick Reference](QUICK_REFERENCE.md)** - Essential commands
- **[Architecture](docs/ARCHITECTURE.md)** - System design
- **[Navigation](NAVIGATION.md)** - Documentation map

---

## ✨ Features

### Real-Time Protection
- ⚡ **< 1 second** attack detection
- 🔍 **PyShark** deep packet inspection
- 🎯 **ENI-level** monitoring (ELB nodes + targets)
- 📊 **Live TUI dashboard** with real-time metrics
- 🎨 **Beautiful interface** with color-coded status

### Advanced Detection
- 🛡️ **10+ attack types** - SYN flood, HTTP flood, slowloris, etc.
- 🔎 **Port scan detection** - 7 scan types with pattern analysis
- 🤖 **Behavioral analysis** - ML-based anomaly detection
- 🌍 **Threat intelligence** - GeoIP, WHOIS, botnet lists

### Comprehensive Monitoring
- 📡 **All ELB nodes** - Monitor AWS-managed ENIs
- 🖥️ **All targets** - Monitor your EC2 instances
- 💯 **Connection limits** - Track ENI capacity (55k limit)
- ❤️ **Health correlation** - Link attacks to target health

### Rich Reporting
- 📧 **Email alerts** - HTML reports via AWS SES
- 📱 **Multi-channel** - SNS, Slack, PagerDuty
- 📦 **PCAP evidence** - Full packet captures
- 📈 **CloudWatch** - Metrics, logs, dashboards

---

## 🎯 What It Monitors

```
Internet → ELB Nodes → Your EC2 Targets
           ↓ Monitor   ↓ Monitor
           
✓ ELB node ENIs (AWS-managed)
✓ Target ENIs (your instances)
✓ Connection limits per ENI
✓ Attack patterns at both layers
✓ Target health status
✓ Traffic distribution
```

---

## 📋 Requirements

**Minimum:**
- EC2 instance (t3.medium)
- Amazon Linux 2023 or Ubuntu 22.04
- Same VPC as your load balancers
- IAM role with ELB/CloudWatch/SES permissions

**Optional:**
- AWS SES for email alerts
- SNS topic for notifications
- S3 bucket for PCAP storage

---

## 🔧 Installation Methods

Choose the method that fits your workflow:

| Method | Time | Best For |
|--------|------|----------|
| **Automated** | 5 min | Quick testing |
| **Manual** | 30 min | Learning |
| **CloudFormation** | 10 min | AWS-native |
| **Terraform** | 5 min | IaC workflows |

**Full comparison:** [DEPLOYMENT_OPTIONS.md](DEPLOYMENT_OPTIONS.md)

### Quick Commands

**Automated:**
```bash
curl -sSL https://raw.githubusercontent.com/.../install.sh | sudo bash
```

**Terraform:**
```bash
cd terraform/ && terraform apply
```

**CloudFormation:**
```bash
aws cloudformation create-stack --stack-name elb-ddos-defender --template-url https://...
```

**Manual:**
See [MANUAL_INSTALLATION.md](MANUAL_INSTALLATION.md) for 14 detailed steps.

---

## ⚙️ Configuration

Edit `/opt/elb-ddos-defender/config.yaml`:

```yaml
aws:
  region: us-east-1

load_balancers:
  - name: my-alb
    arn: arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/abc123

email:
  from: alerts@example.com
  to: security@example.com

thresholds:
  connections_per_second: 1000
  http_requests_per_second: 2000
  ports_scanned_threshold: 20
```

**See [Configuration Guide](docs/CONFIGURATION.md) for all options.**

---

## 🚨 Attack Detection

### Detects 10+ Attack Types:

**Layer 3/4 (Network/Transport):**
- SYN Flood
- UDP Flood
- ICMP Flood
- Connection Exhaustion

**Layer 7 (Application):**
- HTTP Flood
- Slowloris (slow headers)
- Slow POST (slow body)
- Slow Read
- Cache-busting
- API abuse

**Reconnaissance:**
- Port scanning (7 types)
- Network mapping
- Service enumeration

---

## 📊 Real-Time Dashboard

### TUI Dashboard (Terminal)

```bash
sudo /opt/elb-ddos-defender/dashboard.sh
```

**Features:**
- 🔷 Load balancer status with detailed metrics
- 🔌 ENI connection usage with visual progress bars
- 📊 Real-time statistics (packets, connections, bandwidth)
- 🚨 Active alerts and warnings
- 📋 Live event log with color-coding
- 🌍 Threat intelligence and GeoIP
- ⌨️ Interactive controls (Q=quit, R=refresh, H=help)

**Screenshot:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🛡️  ELB DDoS Defender | Real-Time Monitor | Uptime: 2d 14h 23m         │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─ Load Balancers ─────────────────────────────────────────────────┐   │
│ │ prod-alb-1 (ALB)                                    [HEALTHY] ✓  │   │
│ │ ├─ Packets/sec: 1,234        Connections: 5,678                 │   │
│ │ ├─ Requests/sec: 890         Errors: 12 (1.3%)                  │   │
│ │ └─ Targets: 4/4 healthy                                         │   │
│ └───────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│ ┌─ ENI Connection Usage ───────────────────────────────────────────┐   │
│ │ eni-elb-001 [████████████████░░░░░░░░] 18,234/55,000 (33%)     │   │
│ │ eni-elb-002 [███████████████░░░░░░░░░] 17,890/55,000 (33%)     │   │
│ └───────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📧 Email Alerts

Receive detailed HTML reports via AWS SES:

- 🚨 Attack summary and severity
- 📊 Traffic analysis and patterns
- 🌍 Geographic distribution
- 🎯 Affected resources (ENIs, instances)
- 📦 PCAP evidence attached
- 💡 Recommended actions
- 🔗 Links to CloudWatch and reports

**See [example report](docs/EXAMPLE_REPORT.md)**

---

## 🎯 Use Cases

### 1. Production ELB Protection
Monitor all production load balancers 24/7 with real-time alerts.

### 2. Multi-Region Deployment
Deploy in each region to protect global infrastructure.

### 3. Compliance & Auditing
Maintain PCAP evidence and detailed reports for compliance.

### 4. Incident Response
Automated evidence collection and threat intelligence.

### 5. Capacity Planning
Track connection usage and predict when to scale.

---

## 💰 Cost

**Typical monthly cost:**
- EC2 (t3.medium): ~$30
- VPC Traffic Mirroring: ~$0.015/GB
- CloudWatch: ~$5
- SES: First 62,000 emails free
- **Total: ~$35-50/month**

---

## 🔒 Security

- ✅ IAM role-based authentication
- ✅ Encrypted CloudWatch logs
- ✅ Secure PCAP storage (S3 encryption)
- ✅ No credentials in config files
- ✅ Least-privilege IAM policies

---

## 📈 Performance

- ✅ Handles 100,000 packets/second (t3.medium)
- ✅ < 1 second attack detection
- ✅ < 1 second alert delivery
- ✅ Real-time monitoring (1-second intervals)
- ✅ No impact on application performance

---

## 🤝 Support

**Documentation:**
- 📖 [Deployment Guide](DEPLOYMENT_GUIDE.md)
- 📝 [Quick Reference](QUICK_REFERENCE.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- 💡 [Examples](docs/EXAMPLES.md)

**Community:**
- 💬 [GitHub Issues](https://github.com/acchitty/Network-Tools/issues)
- 📧 Email: support@example.com

**Emergency:**
- 🚨 For active attacks, contact AWS Support
- ☎️ AWS Support: 1-866-947-7829

---

## 🎉 Getting Started

1. **Install** - Run one-command installer
2. **Configure** - Edit config.yaml with your ELB ARN
3. **Start** - `sudo systemctl start elb-ddos-defender`
4. **Verify** - Check dashboard and test alerts
5. **Monitor** - View real-time protection

**Ready to protect your ELBs?**

```bash
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

Built with:
- [PyShark](https://github.com/KimiNewt/pyshark) - Packet analysis
- [Scapy](https://scapy.net/) - Packet manipulation
- [Boto3](https://boto3.amazonaws.com/) - AWS SDK
- [Wireshark](https://www.wireshark.org/) - Protocol dissection

---

*ELB DDoS Defender v2.0 - Real-time protection for AWS Load Balancers*
                                    (VPC Flow + ALB/NLB + Connection + PCAP)
                                              ↓
                                    Attack Detection
                                              ↓
                                    Threat Intelligence
                                              ↓
                                    Advisory Mitigation (with approval)
                                              ↓
                                    Complete Trace Reports & Alerts
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## What Gets Installed

- System dependencies (tcpdump, tshark, mtr, whois)
- Python dependencies (boto3, scapy, pyyaml, jinja2, weasyprint)
- IAM role with required permissions
- VPC Traffic Mirroring configuration
- **Automatic log enablement** (VPC Flow Logs with full 40+ fields, ALB/NLB access logs)
- **Packet correlation engine** (traces packets across all log sources)
- **Advisory mitigation system** (suggests actions, requires approval)
- Application code and configuration
- Systemd service for auto-start

## Directory Structure After Installation

```
/opt/elb-ddos-defender/          # Application
/var/log/elb-ddos-defender/      # Per-LB logs
/var/log/attack-reports/         # Per-LB reports
/var/log/pcaps/                  # Per-LB packet captures
```

## Usage

```bash
# Check status
sudo systemctl status elb-ddos-defender

# View logs
sudo tail -f /var/log/elb-ddos-defender.log

# View per-LB logs
sudo tail -f /var/log/elb-ddos-defender/alb-app/monitor.log

# View reports
ls -lh /var/log/attack-reports/

# Edit configuration
sudo nano /opt/elb-ddos-defender/config.yaml

# Restart service
sudo systemctl restart elb-ddos-defender
```

## Configuration

Edit `/opt/elb-ddos-defender/config.yaml`:

```yaml
alerts:
  email:
    enabled: true
    backend: ses
    sender: security@example.com
    recipients:
      - admin@example.com

load_balancers:
  - name: my-alb
    type: ALB
    enabled: true
    email_recipients:
      - alb-team@example.com
    thresholds:
      connections_per_second: 100
      bandwidth_mbps: 500

# Mitigation settings (advisory mode with approval)
mitigation:
  mode: advisory_with_approval  # advisory_only, advisory_with_approval, disabled
  require_approval: true
  approval_methods:
    - email_confirmation
    - cli_interactive
  approval_timeout_minutes: 30
  auto_detect_waf: true
  capabilities:
    waf_ip_blocking: true
    nacl_rules: false
    security_groups: false
  max_ips_per_action: 256
  auto_expire_hours: 24
  whitelist:
    - 203.0.113.0/24  # Office network

# Packet correlation
packet_correlation:
  enabled: true
  time_window_seconds: 1
  sources:
    vpc_flow_logs: true
    alb_access_logs: true
    nlb_connection_logs: true
    connection_logs: true
    pcap_captures: true
```

## Support

- **GitHub Issues**: https://github.com/YOUR-USERNAME/elb-ddos-defender/issues
- **Documentation**: https://github.com/YOUR-USERNAME/elb-ddos-defender/wiki

## License

MIT License
