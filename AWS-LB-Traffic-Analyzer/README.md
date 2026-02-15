# AWS Load Balancer Traffic Analyzer

Low-impact packet analyzer for EC2 instances behind AWS Load Balancers (ALB, NLB, CLB, GWLB).

## Features

- **Multi-LB Support**: Works with ALB, NLB, CLB, and GWLB
- **Protocol Coverage**: TCP, UDP, HTTP, HTTPS
- **Error Detection**: TCP resets, connection failures, HTTP errors
- **Health Check Monitoring**: Tracks success/failure of LB health checks
- **Loop Detection**: Identifies traffic loops and retransmissions
- **Client IP Extraction**: Handles X-Forwarded-For headers and NLB passthrough
- **Low Resource Impact**: ~1-2% CPU, 50-100 MB RAM
- **Automatic Logging**: Errors saved to logs/ directory with 7-day retention

## Installation on EC2

### 1. Upload files to EC2

```bash
# From your laptop
scp -r ~/aws-lb-traffic-analyzer ec2-user@10.0.7.75:~/
```

### 2. Make script executable

```bash
ssh ec2-user@10.0.7.75
cd ~/aws-lb-traffic-analyzer
chmod +x aws-lb-traffic-analyzer.py
```

### 3. Test manually

```bash
sudo python3 aws-lb-traffic-analyzer.py
# Press Ctrl+C to stop
```

### 4. Install as systemd service (recommended)

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

## Usage

### Manual Run

```bash
# Default settings (eth0, sample rate 1/10)
sudo python3 aws-lb-traffic-analyzer.py

# Custom interface
sudo python3 aws-lb-traffic-analyzer.py -i ens5

# Lower impact (sample 1 in 20 packets)
sudo python3 aws-lb-traffic-analyzer.py -s 20

# Custom log directory
sudo python3 aws-lb-traffic-analyzer.py -l /var/log/traffic-analyzer
```

### Service Management

```bash
# View live logs
sudo journalctl -u traffic-analyzer -f

# View errors only
sudo journalctl -u traffic-analyzer | grep ERROR

# Restart service
sudo systemctl restart traffic-analyzer

# Stop service
sudo systemctl stop traffic-analyzer
```

### Check Error Logs

```bash
# View today's errors
cat ~/aws-lb-traffic-analyzer/logs/errors_$(date +%Y-%m-%d).log

# Watch errors in real-time
tail -f ~/aws-lb-traffic-analyzer/logs/errors_*.log

# Search for specific errors
grep "TCP_ERROR" ~/aws-lb-traffic-analyzer/logs/*.log
grep "HEALTH_CHECK_FAIL" ~/aws-lb-traffic-analyzer/logs/*.log
```

## Output

### Real-time Error Logs

```
[2026-02-15 09:30:15] TCP_ERROR: Connection reset: 10.0.2.100:8080->10.0.1.50:43210
[2026-02-15 09:30:16] HEALTH_CHECK_FAIL: HTTP 503 from 10.0.1.50:54321->10.0.2.100:8080
[2026-02-15 09:30:17] APP_ERROR: HTTP 500 from 10.0.2.100:8080->10.0.1.50:12345
```

### Stats Summary (every 30 seconds)

```
======================================================================
AWS Load Balancer Traffic Analyzer (sampled 1/10)
======================================================================
Total: 15000 | TCP: 14500 | UDP: 500
HTTP: 8000 | HTTPS: 6500

--- Detected LB Types ---
  ALB: 8000 indicators
  NLB: 500 indicators

--- Health Checks ---
Success: 120 | Failed: 3
TCP: 50 | UDP: 10

--- TCP Errors ---
  RST: 47
  RETRANSMIT: 12
  ZERO_WINDOW: 3

--- HTTP Errors ---
  HTTP 500: 15
  HTTP 502: 5
  HTTP 503: 8

--- Top Client IPs ---
  203.0.113.45: 1247 requests
  198.51.100.23: 892 requests
```

## Log Retention

- Logs stored in: `~/aws-lb-traffic-analyzer/logs/`
- Format: `errors_YYYY-MM-DD.log`
- Retention: 7 days (automatic cleanup on startup)
- Typical size: 1-50 MB per day

## Resource Usage

- **CPU**: 1-2% (with default sample rate 1/10)
- **Memory**: 50-100 MB
- **Disk**: 1-50 MB/day (error logs only)
- **Network**: No additional traffic generated

## Troubleshooting

**Error: Requires root privileges**
- Run with `sudo`

**Error: No such device 'eth0'**
- Find your interface: `ip link show`
- Use correct interface: `-i ens5` or `-i eth1`

**No traffic captured**
- Verify interface is correct
- Check security groups allow traffic
- Ensure EC2 is receiving traffic from LB

**Service won't start**
- Check logs: `sudo journalctl -u traffic-analyzer -n 50`
- Verify Python 3 installed: `python3 --version`
- Check file permissions: `ls -l aws-lb-traffic-analyzer.py`

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop traffic-analyzer
sudo systemctl disable traffic-analyzer
sudo rm /etc/systemd/system/traffic-analyzer.service
sudo systemctl daemon-reload

# Remove files
rm -rf ~/aws-lb-traffic-analyzer
```
