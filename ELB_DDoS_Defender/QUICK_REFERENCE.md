# ELB DDoS Defender - Quick Reference

## 🚀 Installation (Choose One)

### Option 1: One-Command (Easiest)
```bash
curl -sSL https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/install.sh | sudo bash
```

### Option 2: CloudFormation
```bash
aws cloudformation create-stack \
  --stack-name elb-ddos-defender \
  --template-url https://raw.githubusercontent.com/acchitty/Network-Tools/main/ELB_DDoS_Defender/cloudformation-template.yaml \
  --parameters ParameterKey=VpcId,ParameterValue=vpc-xxx \
  --capabilities CAPABILITY_IAM
```

### Option 3: Docker
```bash
docker run -d --name elb-ddos-defender \
  --network host --cap-add NET_ADMIN \
  acchitty/elb-ddos-defender:latest
```

---

## ⚙️ Essential Commands

### Service Management
```bash
# Start
sudo systemctl start elb-ddos-defender

# Stop
sudo systemctl stop elb-ddos-defender

# Restart
sudo systemctl restart elb-ddos-defender

# Status
sudo systemctl status elb-ddos-defender

# Logs
sudo tail -f /var/log/elb-ddos-defender/defender.log
```

### Monitoring
```bash
# Real-time dashboard
sudo /opt/elb-ddos-defender/dashboard.sh

# Or directly
python3 /opt/elb-ddos-defender/elb-ddos-dashboard.py

# Statistics
sudo /opt/elb-ddos-defender/stats.sh

# Test alert
sudo /opt/elb-ddos-defender/test-alert.sh
```

### Packet Capture
```bash
# Capture 1000 packets
sudo /opt/elb-ddos-defender/capture.sh --count 1000

# Capture for 60 seconds
sudo /opt/elb-ddos-defender/capture.sh --duration 60

# Capture with filter
sudo /opt/elb-ddos-defender/capture.sh --filter "tcp port 80"
```

### Reports
```bash
# Last hour
sudo /opt/elb-ddos-defender/report.sh --last-hour

# Last 24 hours
sudo /opt/elb-ddos-defender/report.sh --last-day

# Custom range
sudo /opt/elb-ddos-defender/report.sh \
  --start "2026-02-22 14:00:00" \
  --end "2026-02-22 15:00:00"
```

---

## 📝 Configuration File

Location: `/opt/elb-ddos-defender/config.yaml`

### Minimal Config
```yaml
aws:
  region: us-east-1

load_balancers:
  - name: my-alb
    arn: arn:aws:elasticloadbalancing:...

email:
  from: alerts@example.com
  to: security@example.com
```

### After Editing
```bash
# Validate
sudo /opt/elb-ddos-defender/validate-config.sh

# Restart
sudo systemctl restart elb-ddos-defender
```

---

## 🚨 Common Issues

### Service Won't Start
```bash
# Check logs
sudo journalctl -u elb-ddos-defender -n 50

# Validate config
sudo /opt/elb-ddos-defender/validate-config.sh

# Reinstall dependencies
sudo pip3 install -r /opt/elb-ddos-defender/requirements.txt
```

### No Packets Captured
```bash
# Check interface
ip addr show

# Test capture
sudo tcpdump -i eth0 -c 10

# Fix permissions
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.11
```

### Emails Not Sending
```bash
# Verify SES
aws ses verify-email-identity --email-address alerts@example.com

# Test email
sudo /opt/elb-ddos-defender/test-email.sh

# Check logs
sudo grep "email" /var/log/elb-ddos-defender/defender.log
```

---

## 📊 Key Metrics

### CloudWatch Metrics
```bash
# View in console
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:namespace=ELBDDoSDefender

# CLI
aws cloudwatch get-metric-statistics \
  --namespace ELBDDoSDefender \
  --metric-name PacketsPerSecond \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average
```

### Important Metrics
- `PacketsPerSecond` - Traffic volume
- `ConnectionsPerENI` - ENI utilization
- `AttacksDetected` - Attack count
- `TargetHealthy` - Target health status

---

## 🔧 Tuning

### Reduce False Positives
```yaml
# Edit config.yaml
thresholds:
  connections_per_second: 5000  # Increase
  http_requests_per_second: 10000  # Increase
```

### Reduce CPU Usage
```yaml
# Edit config.yaml
monitoring:
  interval: 5  # Increase from 1
  
pyshark:
  enabled: false  # Use tcpdump only
```

### Increase Detection Sensitivity
```yaml
# Edit config.yaml
thresholds:
  connections_per_second: 500  # Decrease
  ports_scanned_threshold: 10  # Decrease
```

---

## 📞 Quick Help

| Issue | Command |
|-------|---------|
| Check status | `sudo systemctl status elb-ddos-defender` |
| View logs | `sudo tail -f /var/log/elb-ddos-defender/defender.log` |
| Test alerts | `sudo /opt/elb-ddos-defender/test-alert.sh` |
| Validate config | `sudo /opt/elb-ddos-defender/validate-config.sh` |
| Update | `cd /opt/Network-Tools/ELB_DDoS_Defender && sudo git pull` |

---

## 🎯 Next Steps

1. ✅ Install using one of the methods above
2. ✅ Edit `/opt/elb-ddos-defender/config.yaml`
3. ✅ Start service: `sudo systemctl start elb-ddos-defender`
4. ✅ Test alert: `sudo /opt/elb-ddos-defender/test-alert.sh`
5. ✅ Monitor: `sudo /opt/elb-ddos-defender/dashboard.sh`

**Full documentation:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

*Quick Reference v2.0 - 2026-02-22*
