# Packet Correlation - Complete Traceability

## Overview

The ELB DDoS Defender includes a **Packet Correlation Engine** that traces individual packets across all log sources, providing complete end-to-end visibility.

---

## What Gets Correlated

### 1. VPC Flow Logs (40+ fields)
- Source/destination IP and port
- Protocol, packets, bytes
- Interface, VPC, subnet, instance
- TCP flags, flow direction, traffic path
- Action (ACCEPT/REJECT)

### 2. ALB Access Logs
- Client IP and port
- Target IP and port
- Request ID (unique identifier)
- HTTP request details
- Status codes (ELB and target)
- Timing (request, target, response processing)
- SSL/TLS details
- User agent

### 3. NLB Connection Logs
- Client IP and port
- Target IP and port
- Connection ID
- Listener ID
- TLS cipher and protocol

### 4. Connection Logs (TCP State Tracking)
- Connection state (SYN, SYN-ACK, ESTABLISHED, FIN, RST)
- Sequence and ACK numbers
- Window size, MSS
- TCP flags
- Retransmissions
- RTT measurements

### 5. PCAP Captures
- Full packet details
- Packet and payload size
- TCP flags
- TTL, window size
- Raw packet data

---

## How Correlation Works

### Correlation Key

Each packet is identified by a **5-tuple + time window**:

```
Correlation Key = hash(src_ip, dst_ip, src_port, dst_port, protocol, timestamp_window)
```

**Example:**
```
Source: 203.0.113.45:54321
Destination: 10.0.1.5:443
Protocol: TCP (6)
Timestamp: 2026-02-21 15:00:00

Correlation Key: a1b2c3d4e5f6g7h8
```

All log entries with the same 5-tuple within a 1-second window get the same correlation key.

---

## Complete Trace Example

```
================================================================================
COMPLETE PACKET TRACE REPORT
================================================================================

Connection: 203.0.113.45:54321 -> 10.0.1.5:443
Protocol: TCP (6)
Correlation Key: a1b2c3d4e5f6g7h8

VPC FLOW LOG:
  Interface: eni-abc123
  VPC: vpc-xyz789
  Subnet: subnet-123
  Instance: i-abc123
  Packets: 10
  Bytes: 5000
  Action: ACCEPT
  TCP Flags: 2 (SYN)
  Flow Direction: ingress
  Traffic Path: 1

CONNECTION LOGS (TCP State Tracking):
  [1] 15:00:00.000 - State: SYN
      Seq: 1000000 | Ack: 0
      Window: 65535 | MSS: 1460
      TCP Flags: S
  [2] 15:00:00.010 - State: SYN-ACK
      Seq: 2000000 | Ack: 1000001
      Window: 65535 | MSS: 1460
      TCP Flags: SA
      RTT: 10ms
  [3] 15:00:00.020 - State: ESTABLISHED
      Seq: 1000001 | Ack: 2000001
      Window: 65535
      TCP Flags: A

ALB ACCESS LOG:
  Request ID: req-abc123
  Load Balancer: app/my-alb/abc123
  Target: 10.0.1.5:443
  Status: ELB=200 Target=200
  Request: GET https://example.com/ HTTP/1.1
  User Agent: Mozilla/5.0
  SSL: TLSv1.2 / ECDHE-RSA-AES128-GCM-SHA256
  Timing: Request=0.001s Target=0.050s Response=0.002s
  Bytes: Received=500 Sent=4500

PCAP CAPTURE:
  Packet Size: 1500 bytes
  Payload Size: 1460 bytes
  TCP Flags: SYN
  TTL: 64
  Window Size: 65535

COMPLETE TIMELINE:
  [2026-02-21 15:00:00.000] PCAP: Packet captured [SYN]
  [2026-02-21 15:00:00.000] Connection Log: SYN [Seq=1000000]
  [2026-02-21 15:00:00.000] VPC Flow Log: Flow started
  [2026-02-21 15:00:00.000] ALB Access Log: HTTP Request received
  [2026-02-21 15:00:00.010] Connection Log: SYN-ACK [Seq=2000000, RTT=10ms]
  [2026-02-21 15:00:00.020] Connection Log: ESTABLISHED

================================================================================
```

---

## Use Cases

### 1. Attack Forensics
- Which interface received the packets (VPC Flow)
- TCP handshake state (Connection Logs)
- Whether packets reached ALB (ALB Access Logs)
- Full packet details (PCAP)
- Complete timeline of attack

### 2. Performance Troubleshooting
- Network latency (VPC Flow Logs)
- TCP retransmissions (Connection Logs)
- ALB processing time (ALB Access Logs)
- Target processing time (ALB Access Logs)
- RTT measurements (Connection Logs)

### 3. Security Investigation
- All connections from suspicious IP (VPC Flow)
- HTTP requests made (ALB Access Logs)
- Connection patterns (Connection Logs)
- Packet-level details (PCAP)
- Geographic origin (Threat Intel)

---

## CLI Usage

```bash
# Trace a specific connection
sudo elb-ddos-defender trace \
  --src-ip 203.0.113.45 \
  --dst-ip 10.0.1.5 \
  --src-port 54321 \
  --dst-port 443 \
  --timestamp "2026-02-21 15:00:00"

# View by correlation key
sudo elb-ddos-defender trace --key a1b2c3d4e5f6g7h8

# Find all traces for an IP
sudo elb-ddos-defender trace --ip 203.0.113.45
```

---

## Benefits

✅ **No Guessing**: Correlation key automatically links all log sources  
✅ **Complete Visibility**: See packet journey from client to target  
✅ **Timeline View**: Exact sequence of events  
✅ **Attack Forensics**: Trace malicious packets end-to-end  
✅ **Performance Analysis**: Identify bottlenecks at each layer  
✅ **Security Investigation**: Full context for suspicious activity  

---

## Configuration

```yaml
# config.yaml

packet_correlation:
  enabled: true
  time_window_seconds: 1
  
  # What to correlate
  sources:
    vpc_flow_logs: true
    alb_access_logs: true
    nlb_connection_logs: true
    connection_logs: true
    pcap_captures: true
```

---

## See Also

- [Installation Guide](INSTALLATION.md)
- [Attack Detection](../README.md#attack-detection)
- [Configuration Guide](../config.yaml.template)
