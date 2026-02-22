# Quick Start: Integrating AWS Modules into PCAP Analyzer

## What Was Created

Two new analysis modules based on the Wireshark AWS Guide:

1. **aws_detection.py** - Detects AWS-specific traffic patterns
2. **security_analysis.py** - Detects security issues and attacks

## Integration Steps

### 1. Add Imports to pcap_analyzer_v3.py

Add at the top of the file (around line 20):

```python
# Import AWS modules
try:
    from aws_detection import detect_aws_services, print_aws_analysis
    from security_analysis import analyze_security, print_security_analysis
    AWS_MODULES_AVAILABLE = True
except ImportError:
    AWS_MODULES_AVAILABLE = False
```

### 2. Add Command-Line Options

In the `argparse` section (around line 1775):

```python
parser.add_argument('--aws', action='store_true',
                    help='Enable AWS-specific analysis (ELB, IMDS, NAT, TGW)')
parser.add_argument('--security', action='store_true',
                    help='Enable security analysis (SG blocks, RST, DDoS, port scans)')
```

### 3. Call Modules in Main Analysis Function

In `analyze_pcap()` function, after Scapy analysis (around line 800):

```python
# AWS-specific analysis
if args.aws and AWS_MODULES_AVAILABLE and SCAPY_AVAILABLE:
    aws_analysis = detect_aws_services(packets)
    print_aws_analysis(aws_analysis)

# Security analysis
if args.security and AWS_MODULES_AVAILABLE and SCAPY_AVAILABLE:
    security_analysis = analyze_security(packets)
    print_security_analysis(security_analysis)
```

## Usage Examples

### Basic AWS Analysis
```bash
analyze capture.pcap --aws
```

**Detects:**
- ALB/CLB/NLB health checks
- IMDS access (v1 vs v2)
- NAT Gateway issues
- Transit Gateway cross-VPC traffic

### Security Analysis
```bash
analyze capture.pcap --security
```

**Detects:**
- Security group blocks
- TCP RST patterns
- DDoS/flood indicators
- Port scans

### Combined Analysis
```bash
analyze capture.pcap --aws --security --visual
```

### Full Analysis
```bash
analyze capture.pcap --aws --security --visual --whois --export-json
```

## What Each Module Detects

### AWS Detection Module

#### 1. ELB Health Checks
- **ALB**: `ELB-HealthChecker/2.0` user agent
- **CLB**: `ELB-HealthChecker/1.0` user agent
- **NLB**: TCP SYN/SYN-ACK patterns
- Success/failure rates per target
- Failed health check details

#### 2. IMDS Access (169.254.169.254)
- IMDSv1 (GET) vs IMDSv2 (PUT token)
- Security warnings for IMDSv1
- Most accessed metadata paths
- Source IPs accessing IMDS

#### 3. NAT Gateway
- Total connections
- RST packet count
- Port exhaustion risk (>50k connections)
- Timeout detection

#### 4. Transit Gateway
- Cross-VPC traffic detection
- VPC CIDR identification
- Potential asymmetric routing

### Security Analysis Module

#### 1. Security Group Blocks
- SYN packets without SYN-ACK response
- Silent drops vs explicit rejects
- Blocked connection details

#### 2. TCP RST Analysis
- Total RST count
- Top sources sending RSTs
- Top destination ports
- RST patterns:
  - Firewall/security appliance RST
  - Service not listening
  - Connection refused

#### 3. DDoS/Flood Detection
- **TCP SYN Flood**: >1000 SYN/sec
- **UDP Flood**: >5000 UDP/sec
- **ICMP Flood**: >1000 ICMP/sec
- **DNS Amplification**: Large DNS responses

#### 4. Port Scan Detection
- Sources scanning >20 ports
- Scanned port list
- Scanner IP identification

## Output Example

```
================================================================================
AWS SERVICE DETECTION
================================================================================

[ELB Health Checks]
  Total: 45
    ALB (v2.0): 30
    CLB (v1.0): 10
    NLB (TCP): 5
  Success: 42
  Failures: 3

  Failed Health Checks:
    ❌ 10.0.2.15 returned 503

  Per-Target Summary:
    ✓ 10.0.2.10: 15/15 (100%)
    ✗ 10.0.2.15: 12/15 (80%)

[IMDS Access - 169.254.169.254]
  Total requests: 23
    IMDSv1 (GET): 18
    IMDSv2 (token): 5

  ⚠️  WARNING: IMDSv1 access detected!
     Consider migrating to IMDSv2 for better security

  Top accessed paths:
     12x /latest/meta-data/instance-id
      6x /latest/meta-data/iam/security-credentials/

================================================================================
SECURITY ANALYSIS
================================================================================

[Security Group Blocks Detected]
  Total: 8

  Blocked connections (SYN without response):
    ❌ 203.0.113.50 → 10.0.2.10:8080 (5 attempts)
    ❌ 198.51.100.25 → 10.0.2.15:443 (3 attempts)

  💡 Recommendation: Check security group rules for these connections

[TCP RST Analysis]
  Total RST packets: 127

  Top sources sending RSTs:
    10.0.2.10: 45 RSTs
    10.0.2.15: 32 RSTs

  Top destination ports:
    Port 80: 67 RSTs
    Port 443: 35 RSTs

  RST patterns detected:
    Service not listening: 89
    Connection refused: 38
```

## Testing

### Test with Sample Traffic

```bash
# Capture some traffic
sudo tcpdump -i eth0 -w test.pcap -c 1000

# Analyze with new modules
analyze test.pcap --aws --security
```

### Test Specific Scenarios

```bash
# Test IMDS detection
curl http://169.254.169.254/latest/meta-data/instance-id
analyze imds-test.pcap --aws

# Test health check detection
# (Capture traffic on ALB target during health checks)
analyze alb-traffic.pcap --aws

# Test security analysis
# (Capture during port scan or connection attempts)
analyze security-test.pcap --security
```

## Next Steps

1. **Test the modules** with real AWS traffic
2. **Add to HTML report** - Include AWS/security sections in HTML output
3. **Add filters** - Create pre-built Wireshark filters for AWS services
4. **Enhance detection** - Add more AWS service patterns
5. **AWS CLI integration** - Correlate with VPC Flow Logs, Security Groups

## Files Modified

- ✅ Created: `aws_detection.py`
- ✅ Created: `security_analysis.py`
- ⏳ To modify: `pcap_analyzer_v3.py` (add imports and calls)

## Benefits

1. **Faster AWS Troubleshooting**
   - Automatic detection of common AWS issues
   - Clear identification of service-specific problems

2. **Better Security Visibility**
   - Identify misconfigurations
   - Detect attack patterns
   - Security group validation

3. **Actionable Recommendations**
   - Specific suggestions for each issue
   - AWS CLI commands to fix problems

4. **Comprehensive Analysis**
   - Combines general packet analysis with AWS-specific insights
   - Single tool for all network troubleshooting
