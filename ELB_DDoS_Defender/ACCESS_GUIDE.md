# ELB DDoS Defender - Access Guide

## 🔐 How to Access Your Instance

### Method 1: SSH (Traditional)

**Requirements:**
- SSH key pair (.pem file)
- Instance has public IP
- Security group allows SSH (port 22)

**Steps:**

1. **Get instance public IP:**
```bash
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

2. **Connect:**
```bash
ssh -i /path/to/your-key.pem ec2-user@<public-ip>
```

**For Ubuntu:**
```bash
ssh -i /path/to/your-key.pem ubuntu@<public-ip>
```

**Troubleshooting:**
```bash
# Fix key permissions
chmod 400 /path/to/your-key.pem

# Verbose output for debugging
ssh -v -i /path/to/your-key.pem ec2-user@<public-ip>
```

---

### Method 2: AWS Session Manager (Recommended)

**Requirements:**
- SSM Agent installed (pre-installed on Amazon Linux 2023)
- IAM role with SSM permissions
- No SSH key needed
- No public IP needed

**Steps:**

1. **Install Session Manager plugin (one-time):**

**macOS:**
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip" -o "sessionmanager-bundle.zip"
unzip sessionmanager-bundle.zip
sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin
```

**Linux:**
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/linux_64bit/session-manager-plugin.rpm" -o "session-manager-plugin.rpm"
sudo yum install -y session-manager-plugin.rpm
```

**Windows:**
Download from: https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe

2. **Connect:**
```bash
aws ssm start-session --target i-xxxxx
```

**Advantages:**
- ✅ No SSH key needed
- ✅ No public IP needed
- ✅ Works from anywhere
- ✅ All sessions logged in CloudTrail
- ✅ No security group changes needed

---

### Method 3: EC2 Instance Connect

**Requirements:**
- Amazon Linux 2023 or Ubuntu
- Instance has public IP
- Security group allows SSH (port 22)

**Steps:**

1. **From AWS Console:**
   - Go to EC2 Console
   - Select your instance
   - Click "Connect"
   - Choose "EC2 Instance Connect"
   - Click "Connect"

2. **From CLI:**
```bash
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-xxxxx \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub \
  --availability-zone us-east-1a

ssh ec2-user@<public-ip>
```

---

### Method 4: Bastion Host

**If instance is in private subnet:**

```
Your Computer → Bastion Host → Private Instance
```

**Steps:**

1. **SSH to bastion:**
```bash
ssh -i bastion-key.pem ec2-user@<bastion-public-ip>
```

2. **From bastion, SSH to private instance:**
```bash
ssh -i defender-key.pem ec2-user@<private-ip>
```

**Or use SSH tunneling:**
```bash
ssh -i bastion-key.pem -J ec2-user@<bastion-ip> ec2-user@<private-ip>
```

---

## 📊 Accessing the Dashboard

### TUI Dashboard (Terminal)

**After connecting to instance:**
```bash
sudo /opt/elb-ddos-defender/dashboard.sh
```

**Controls:**
- `Q` - Quit
- `R` - Refresh
- `H` - Help
- `Ctrl+C` - Exit

---

### Web Dashboard (Future)

**Port forwarding via SSH:**
```bash
ssh -i your-key.pem -L 8080:localhost:8080 ec2-user@<public-ip>
```

**Then open in browser:**
```
http://localhost:8080
```

---

## 📝 Viewing Logs

### Real-time Logs

**Main application log:**
```bash
sudo tail -f /var/log/elb-ddos-defender/defender.log
```

**System logs:**
```bash
sudo journalctl -u elb-ddos-defender -f
```

### Historical Logs

**Last 100 lines:**
```bash
sudo tail -n 100 /var/log/elb-ddos-defender/defender.log
```

**Search logs:**
```bash
sudo grep "ATTACK" /var/log/elb-ddos-defender/defender.log
sudo grep "ERROR" /var/log/elb-ddos-defender/defender.log
```

### CloudWatch Logs

**From AWS Console:**
1. Go to CloudWatch Console
2. Click "Log groups"
3. Find `/aws/elb-ddos-defender`
4. Click to view logs

**From CLI:**
```bash
# List log streams
aws logs describe-log-streams \
  --log-group-name /aws/elb-ddos-defender \
  --order-by LastEventTime \
  --descending

# View recent logs
aws logs tail /aws/elb-ddos-defender --follow
```

---

## 🔧 Common Commands

### Service Management

```bash
# Check status
sudo systemctl status elb-ddos-defender

# Start service
sudo systemctl start elb-ddos-defender

# Stop service
sudo systemctl stop elb-ddos-defender

# Restart service
sudo systemctl restart elb-ddos-defender

# View service logs
sudo journalctl -u elb-ddos-defender -n 50
```

### Monitoring

```bash
# View dashboard
sudo /opt/elb-ddos-defender/dashboard.sh

# Check packet capture
sudo tcpdump -i eth0 -c 10

# View PCAP files
ls -lh /var/log/pcaps/

# Check disk space
df -h
```

### Configuration

```bash
# Edit config
sudo nano /opt/elb-ddos-defender/config.yaml

# Validate config
python3 -c "import yaml; yaml.safe_load(open('/opt/elb-ddos-defender/config.yaml'))"

# Restart after config change
sudo systemctl restart elb-ddos-defender
```

---

## 🚨 Troubleshooting Access Issues

### SSH Connection Refused

**Check security group:**
```bash
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --query 'SecurityGroups[0].IpPermissions'
```

**Ensure port 22 is open from your IP**

### Session Manager Not Working

**Check SSM agent:**
```bash
sudo systemctl status amazon-ssm-agent
```

**Check IAM role:**
```bash
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'
```

**Role must have:** `AmazonSSMManagedInstanceCore` policy

### Can't Access Dashboard

**Check if service is running:**
```bash
sudo systemctl status elb-ddos-defender
```

**Check if rich library is installed:**
```bash
python3 -c "import rich; print('OK')"
```

**Install if missing:**
```bash
sudo pip3 install rich
```

---

## 📞 Quick Access Reference

| Method | Command | Requirements |
|--------|---------|--------------|
| SSH | `ssh -i key.pem ec2-user@<ip>` | Key, Public IP, SG |
| Session Manager | `aws ssm start-session --target i-xxx` | IAM role, SSM agent |
| EC2 Connect | AWS Console → Connect | Public IP, SG |
| Dashboard | `sudo /opt/elb-ddos-defender/dashboard.sh` | Connected to instance |
| Logs | `sudo tail -f /var/log/elb-ddos-defender/defender.log` | Connected to instance |

---

*Access Guide v1.0 - 2026-02-22*
