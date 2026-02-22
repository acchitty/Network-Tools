# ELB DDoS Defender - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERNET TRAFFIC                            │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS LOAD BALANCER (ALB/NLB/CLB/GWLB)            │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │  ELB Node 1  │    │  ELB Node 2  │    │  ELB Node 3  │        │
│  │   (AZ-1)     │    │   (AZ-2)     │    │   (AZ-3)     │        │
│  │ eni-elb-001  │    │ eni-elb-002  │    │ eni-elb-003  │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
└─────────┼────────────────────┼────────────────────┼────────────────┘
          │                    │                    │
          └────────────────────┴────────────────────┘
                               ↓
          ┌────────────────────────────────────────┐
          │    VPC Traffic Mirroring               │
          │    (Copies all packets)                │
          └────────────────┬───────────────────────┘
                           ↓
          ┌────────────────────────────────────────┐
          │   ELB DDoS Defender EC2 Instance       │
          │   (t3.medium or larger)                │
          │                                        │
          │  ┌──────────────────────────────────┐ │
          │  │  PyShark Live Capture            │ │
          │  │  - Real-time packet analysis     │ │
          │  │  - Wireshark display filters     │ │
          │  │  - Protocol dissection           │ │
          │  └────────────┬─────────────────────┘ │
          │               ↓                        │
          │  ┌──────────────────────────────────┐ │
          │  │  ENI Discovery Engine            │ │
          │  │  - Auto-discover ELB node ENIs   │ │
          │  │  - Auto-discover target ENIs     │ │
          │  │  - Track all network interfaces  │ │
          │  └────────────┬─────────────────────┘ │
          │               ↓                        │
          │  ┌──────────────────────────────────┐ │
          │  │  Analysis Engine                 │ │
          │  │  ┌────────────────────────────┐  │ │
          │  │  │ Port Scan Detector         │  │ │
          │  │  │ - 7 scan types             │  │ │
          │  │  │ - Pattern analysis         │  │ │
          │  │  └────────────────────────────┘  │ │
          │  │  ┌────────────────────────────┐  │ │
          │  │  │ DDoS Detector              │  │ │
          │  │  │ - SYN/UDP/ICMP floods      │  │ │
          │  │  │ - HTTP floods              │  │ │
          │  │  │ - Slowloris attacks        │  │ │
          │  │  │ - Connection exhaustion    │  │ │
          │  │  └────────────────────────────┘  │ │
          │  │  ┌────────────────────────────┐  │ │
          │  │  │ Threat Intelligence        │  │ │
          │  │  │ - GeoIP lookup             │  │ │
          │  │  │ - WHOIS data               │  │ │
          │  │  │ - Botnet lists             │  │ │
          │  │  │ - Tor exit nodes           │  │ │
          │  │  └────────────────────────────┘  │ │
          │  │  ┌────────────────────────────┐  │ │
          │  │  │ Connection Limit Monitor   │  │ │
          │  │  │ - Track ENI connections    │  │ │
          │  │  │ - Alert at 80% (44k)       │  │ │
          │  │  │ - Predict exhaustion       │  │ │
          │  │  └────────────────────────────┘  │ │
          │  └────────────┬─────────────────────┘ │
          │               ↓                        │
          │  ┌──────────────────────────────────┐ │
          │  │  Alert & Response System         │ │
          │  │  - Email (AWS SES)               │ │
          │  │  - SNS notifications             │ │
          │  │  - Slack webhooks                │ │
          │  │  - PagerDuty integration         │ │
          │  │  - CloudWatch alarms             │ │
          │  └────────────┬─────────────────────┘ │
          │               ↓                        │
          │  ┌──────────────────────────────────┐ │
          │  │  Storage & Reporting             │ │
          │  │  - PCAP files (local + S3)       │ │
          │  │  - HTML/PDF reports              │ │
          │  │  - JSON data export              │ │
          │  │  - CloudWatch Logs               │ │
          │  └──────────────────────────────────┘ │
          └────────────────────────────────────────┘
                           ↓
          ┌────────────────────────────────────────┐
          │    Target EC2 Instances                │
          │                                        │
          │  ┌────────┐  ┌────────┐  ┌────────┐  │
          │  │  i-1   │  │  i-2   │  │  i-3   │  │
          │  │eni-001 │  │eni-002 │  │eni-003 │  │
          │  └────────┘  └────────┘  └────────┘  │
          └────────────────────────────────────────┘
```

## Component Details

### 1. VPC Traffic Mirroring

**Purpose:** Copies all network traffic to the defender instance

**Configuration:**
- Mirror Source: ELB ENIs + Target ENIs
- Mirror Target: Defender EC2 instance
- Filter: All traffic (no filtering)

**Traffic Flow:**
```
Original Traffic: Client → ELB → Target (unaffected)
Mirrored Traffic: ELB/Target → Defender (passive copy)
```

### 2. PyShark Live Capture

**Purpose:** Real-time packet capture and analysis

**Features:**
- Captures packets as they arrive (< 1ms latency)
- Uses Wireshark display filters
- Protocol dissection (HTTP, TCP, UDP, DNS, etc.)
- Deep packet inspection

**Performance:**
- Handles 100,000 packets/second
- < 10ms processing per packet
- Continuous 24/7 operation

### 3. ENI Discovery Engine

**Purpose:** Auto-discover all network interfaces

**Discovers:**
- ELB node ENIs (AWS-managed)
- Target ENIs (your EC2 instances)
- Updates when targets change

**Process:**
```python
1. Query ELB ARN
2. Get availability zones
3. Find ELB ENIs in each subnet
4. Get target groups
5. Get target instances
6. Extract target ENIs
7. Monitor all ENIs
```

### 4. Analysis Engine

**Components:**

#### Port Scan Detector
- Detects 7 scan types
- Pattern analysis (sequential, random, targeted)
- Timing analysis (fast, slow, distributed)
- Threat intelligence correlation

#### DDoS Detector
- Layer 3/4: SYN, UDP, ICMP floods
- Layer 7: HTTP floods, slowloris, slow POST
- Connection exhaustion
- Behavioral anomaly detection

#### Threat Intelligence
- GeoIP: Identify attack origin
- WHOIS: Get network owner info
- Botnet lists: Check known bad IPs
- Tor detection: Identify anonymized traffic

#### Connection Limit Monitor
- Tracks connections per ENI
- Alerts at 80% capacity (44,000 connections)
- Predicts when limit will be reached
- Recommends scaling actions

### 5. Alert & Response System

**Alert Channels:**

**Email (AWS SES):**
- Rich HTML reports
- PCAP attachments
- Actionable recommendations
- < 1 second delivery

**SNS:**
- JSON payload
- Multi-subscriber support
- Lambda integration

**Slack:**
- Webhook integration
- Formatted messages
- Interactive buttons

**PagerDuty:**
- Incident creation
- Severity levels
- On-call routing

**CloudWatch:**
- Custom metrics
- Alarms
- Dashboards

### 6. Storage & Reporting

**PCAP Storage:**
- Local: `/var/log/pcaps/`
- S3: Automatic upload
- Rotation: Keep last 10 files
- Compression: gzip

**Reports:**
- HTML: Rich formatting
- PDF: Printable
- JSON: Machine-readable
- TXT: Plain text

**CloudWatch Logs:**
- Structured logging
- Searchable
- Retention: 90 days

## Data Flow

### Normal Traffic Flow

```
1. Client sends request
2. ELB receives request
3. Traffic mirrored to defender (passive)
4. ELB forwards to target
5. Target responds
6. Response mirrored to defender (passive)
7. ELB returns response to client

Defender monitors but doesn't interfere
```

### Attack Detection Flow

```
1. Attack packets arrive at ELB
2. Traffic mirrored to defender
3. PyShark captures packets (< 1ms)
4. Analysis engine processes (< 10ms)
5. Attack pattern detected (< 1 second)
6. Alert triggered immediately
7. Email sent via SES (< 1 second)
8. CloudWatch alarm created
9. PCAP evidence saved
10. Report generated

Total: < 2 seconds from attack start to alert
```

## Monitoring Layers

### Layer 1: ELB Node ENIs (Front-line)

**What:** AWS-managed network interfaces for ELB nodes

**Monitors:**
- Packets hitting the load balancer
- Connection count per ELB node
- Traffic distribution across AZs
- Attack patterns at ELB layer

**Why:** Detect attacks before they reach your instances

### Layer 2: Target ENIs (Your Instances)

**What:** Network interfaces on your EC2 instances

**Monitors:**
- Packets reaching your instances
- Connection count per instance
- Per-instance attack detection
- Target health correlation

**Why:** Detect attacks that bypass ELB or overwhelm targets

### Layer 3: Correlation

**What:** Correlate traffic between layers

**Analyzes:**
- Is attack blocked at ELB?
- Is attack reaching targets?
- Which layer is under stress?
- Is traffic distribution even?

**Why:** Understand attack impact and effectiveness of defenses

## Scalability

### Vertical Scaling

| Instance Type | Packets/sec | Connections | Cost/month |
|---------------|-------------|-------------|------------|
| t3.medium | 100,000 | 55,000 | $30 |
| t3.large | 200,000 | 110,000 | $60 |
| t3.xlarge | 400,000 | 220,000 | $120 |
| c5.2xlarge | 1,000,000 | 550,000 | $250 |

### Horizontal Scaling

**Multi-Region:**
```
Region 1: Defender → ELBs in us-east-1
Region 2: Defender → ELBs in us-west-2
Region 3: Defender → ELBs in eu-west-1

Central: Aggregate alerts and reports
```

**Multi-VPC:**
```
VPC 1: Defender → ELBs in production VPC
VPC 2: Defender → ELBs in staging VPC
VPC 3: Defender → ELBs in development VPC
```

## High Availability

### Active-Passive

```
Primary Defender (Active)
    ↓
  Monitors ELBs
    ↓
  Sends heartbeat to CloudWatch
    ↓
  If heartbeat fails:
    ↓
Secondary Defender (Passive) activates
```

### Active-Active

```
Defender 1 → Monitors ELB nodes in AZ-1, AZ-2
Defender 2 → Monitors ELB nodes in AZ-2, AZ-3

Both send alerts
Deduplication in SNS/Lambda
```

## Security

### IAM Permissions

**Minimum required:**
- `elasticloadbalancing:Describe*`
- `ec2:DescribeNetworkInterfaces`
- `ec2:DescribeInstances`
- `cloudwatch:PutMetricData`
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`
- `ses:SendEmail`

**Optional (for auto-response):**
- `ec2:CreateNetworkAclEntry`
- `ec2:AuthorizeSecurityGroupIngress`
- `wafv2:CreateIPSet`

### Network Security

**Defender Security Group:**
- Inbound: Traffic mirroring (UDP 4789)
- Outbound: HTTPS (443) for AWS APIs

**No public access required**

### Data Security

- PCAP files encrypted at rest (S3 SSE)
- CloudWatch Logs encrypted
- No credentials in config files
- IAM role-based authentication

## Performance Optimization

### CPU Optimization

```yaml
# Reduce CPU usage
monitoring:
  interval: 5  # Increase from 1 second
  
pyshark:
  enabled: false  # Use tcpdump only for basic analysis
```

### Memory Optimization

```yaml
# Reduce memory usage
pcap:
  max_size: 50  # Reduce from 100 MB
  rotation: 5  # Keep fewer files
```

### Network Optimization

```yaml
# Reduce network overhead
cloudwatch:
  batch_size: 100  # Batch metrics
  flush_interval: 60  # Send every 60 seconds
```

## Troubleshooting

### High CPU Usage

**Cause:** Too many packets or deep inspection enabled

**Solution:**
1. Increase monitoring interval
2. Disable PyShark deep inspection
3. Use larger instance type
4. Filter traffic at mirror source

### Missing Packets

**Cause:** Traffic mirroring not configured

**Solution:**
1. Verify mirror session exists
2. Check mirror target is defender instance
3. Verify security group allows UDP 4789
4. Check ENI capacity

### False Positives

**Cause:** Thresholds too sensitive

**Solution:**
1. Increase detection thresholds
2. Baseline normal traffic first
3. Adjust per-ELB thresholds
4. Enable behavioral learning

### Alerts Not Sending

**Cause:** SES not configured or email not verified

**Solution:**
1. Verify email in SES
2. Check SES sending limits
3. Review IAM permissions
4. Test with test-alert.sh

---

*Architecture v2.0 - 2026-02-22*
