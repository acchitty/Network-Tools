# PCAP Analyzer Enhancement Plan
## Based on Wireshark AWS Guide Knowledge

### Current Capabilities
- Basic protocol analysis (TCP/UDP/ICMP/DNS)
- Conversation tracking
- HTTP request/response parsing
- Visual network diagrams
- Whois lookups
- Tor detection

### Proposed AWS-Specific Enhancements

## 1. AWS Service Detection Module

### Add Detection For:
- **ALB/NLB/CLB Health Checks**
  - Detect `ELB-HealthChecker/1.0` and `ELB-HealthChecker/2.0` user agents
  - Report health check success/failure rates
  - Identify target health issues

- **IMDS Access (169.254.169.254)**
  - Detect IMDSv1 (GET) vs IMDSv2 (PUT token) usage
  - Security warnings for IMDSv1
  - Most accessed metadata paths

- **NAT Gateway Traffic**
  - Identify pre-NAT vs post-NAT patterns
  - Detect port exhaustion (55k connection limit)
  - Connection timeout analysis

- **Transit Gateway Traffic**
  - Cross-VPC traffic detection
  - Asymmetric routing identification
  - Route table issue detection

### Implementation:
```python
def detect_aws_services(packets):
    """Detect AWS-specific traffic patterns"""
    aws_analysis = {
        'elb_health_checks': {'alb': 0, 'clb': 0, 'nlb': 0, 'failures': []},
        'imds_access': {'v1': 0, 'v2': 0, 'paths': Counter()},
        'nat_gateway': {'connections': 0, 'timeouts': 0},
        'transit_gateway': {'cross_vpc': 0, 'asymmetric': []}
    }
    # Implementation details...
```

---

## 2. Security Analysis Module

### Add Detection For:
- **Security Group Blocks**
  - SYN without SYN-ACK patterns
  - Silent drops vs explicit rejects

- **NACL Issues**
  - Ephemeral port blocks
  - Rule order conflicts

- **DDoS/Flood Detection**
  - TCP SYN floods
  - UDP floods
  - ICMP floods
  - DNS amplification

- **TCP RST Analysis**
  - Connection refused patterns
  - Firewall resets
  - Application resets
  - Port scanning detection

### Implementation:
```python
def analyze_security_issues(packets):
    """Detect security and firewall issues"""
    security = {
        'sg_blocks': [],
        'nacl_blocks': [],
        'ddos_indicators': {},
        'rst_analysis': {'by_source': Counter(), 'by_port': Counter()}
    }
    # Implementation details...
```

---

## 3. Performance Analysis Module

### Add Metrics For:
- **TCP Performance**
  - Retransmission rates
  - Out-of-order packets
  - Window size issues
  - Zero window events

- **Latency Analysis**
  - SYN to SYN-ACK time
  - Request to response time
  - ALB processing time (X-Amzn-Trace-Id correlation)

- **Connection Issues**
  - Failed handshakes
  - Connection timeouts
  - Keep-alive problems

### Implementation:
```python
def analyze_performance(packets):
    """Analyze network performance metrics"""
    perf = {
        'tcp_retransmissions': 0,
        'latency_stats': {'min': 0, 'max': 0, 'avg': 0},
        'failed_connections': [],
        'slow_requests': []
    }
    # Implementation details...
```

---

## 4. Load Balancer Analysis Module

### Add Detection For:
- **ALB-Specific**
  - X-Forwarded-For header analysis
  - X-Amzn-Trace-Id tracking
  - Target response codes
  - Sticky session tracking

- **NLB-Specific**
  - Flow hash distribution
  - Connection preservation
  - TCP health check patterns

- **GWLB-Specific**
  - GENEVE encapsulation detection
  - Appliance traffic flow
  - Symmetric routing verification

### Implementation:
```python
def analyze_load_balancer(packets):
    """Analyze load balancer traffic patterns"""
    lb_analysis = {
        'type': None,  # ALB, NLB, CLB, GWLB
        'targets': {},
        'distribution': Counter(),
        'health_checks': []
    }
    # Implementation details...
```

---

## 5. Container Networking Module

### Add Detection For:
- **ECS awsvpc Mode**
  - ENI-based traffic
  - Task-to-task communication
  - Service mesh patterns

- **EKS/CNI**
  - Pod IP allocation
  - Service ClusterIP traffic
  - NodePort patterns

- **Encapsulation**
  - GENEVE (port 6081)
  - VXLAN (port 4789)
  - Overlay network analysis

### Implementation:
```python
def analyze_container_networking(packets):
    """Analyze container networking patterns"""
    container = {
        'encapsulation': None,  # GENEVE, VXLAN, None
        'pod_ips': set(),
        'service_ips': set(),
        'overlay_traffic': 0
    }
    # Implementation details...
```

---

## 6. Enhanced Filtering & Reporting

### Add Pre-built Filters:
```python
AWS_FILTERS = {
    'elb_health_checks': 'http.user_agent contains "ELB-HealthChecker"',
    'imds_access': 'ip.dst == 169.254.169.254',
    'nat_gateway': 'tcp.flags.reset==1 && tcp.srcport > 1024',
    'transit_gateway': 'ip.src != ip.dst subnet',
    'security_group_blocks': 'tcp.flags.syn==1 && tcp.flags.ack==0',
    'tcp_retransmissions': 'tcp.analysis.retransmission',
    'slow_requests': 'http.time > 1.0'
}
```

### Enhanced Output:
- **AWS-Specific Summary Section**
- **Security Findings Section**
- **Performance Metrics Section**
- **Recommendations Section**

---

## 7. Integration with AWS CLI

### Add Commands:
```python
def correlate_with_vpc_flow_logs(pcap_file, log_group):
    """Correlate PCAP with VPC Flow Logs"""
    # Extract 5-tuple from PCAP
    # Query CloudWatch Logs
    # Match and correlate
    
def check_security_groups(src_ip, dst_ip, port):
    """Check if traffic should be allowed by SG"""
    # Query EC2 security groups
    # Validate rules
    # Report mismatches
```

---

## 8. Command-Line Enhancements

### New Options:
```bash
# AWS-specific analysis
analyze capture.pcap --aws

# Focus on specific AWS service
analyze capture.pcap --aws-service elb
analyze capture.pcap --aws-service imds
analyze capture.pcap --aws-service nat-gateway

# Security analysis
analyze capture.pcap --security

# Performance analysis
analyze capture.pcap --performance

# Correlate with AWS
analyze capture.pcap --correlate-vpc-flow-logs log-group-name
analyze capture.pcap --check-security-groups
```

---

## Implementation Priority

### Phase 1 (High Value, Low Effort)
1. ✅ AWS Service Detection (ELB, IMDS, NAT)
2. ✅ TCP RST Analysis
3. ✅ Security Group Block Detection
4. ✅ Basic Performance Metrics

### Phase 2 (High Value, Medium Effort)
5. Load Balancer Deep Analysis
6. DDoS/Flood Detection
7. Enhanced Reporting
8. Pre-built AWS Filters

### Phase 3 (Medium Value, High Effort)
9. Container Networking Analysis
10. AWS CLI Integration
11. VPC Flow Log Correlation
12. Interactive Dashboard

---

## File Structure

```
PCAP-Analyzer/
├── pcap_analyzer_v4.py          # Main analyzer (enhanced)
├── modules/
│   ├── aws_detection.py         # AWS service detection
│   ├── security_analysis.py     # Security & firewall analysis
│   ├── performance_analysis.py  # Performance metrics
│   ├── lb_analysis.py           # Load balancer analysis
│   └── container_analysis.py    # Container networking
├── filters/
│   └── aws_filters.json         # Pre-built AWS filters
└── templates/
    └── aws_report.html          # Enhanced HTML report
```

---

## Expected Benefits

1. **Faster Troubleshooting**
   - Automatic detection of common AWS issues
   - Pre-built filters for AWS services
   - Clear recommendations

2. **Better Security Visibility**
   - Identify security group misconfigurations
   - Detect DDoS patterns
   - IMDS security warnings

3. **Performance Insights**
   - Pinpoint latency sources
   - Identify retransmission issues
   - Load balancer health visibility

4. **AWS-Native Integration**
   - Correlate with VPC Flow Logs
   - Validate against security groups
   - Service-specific analysis

---

## Next Steps

1. Review and prioritize enhancements
2. Implement Phase 1 features
3. Test with real AWS traffic captures
4. Update documentation
5. Create example captures for each AWS service
