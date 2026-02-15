# PCAP Analyzer v4 - Usage Examples

## 🎯 COMMON USE CASES

### 1. Quick Troubleshooting

**Scenario:** Network is slow, need to quickly identify issues

```bash
analyze capture.pcap
```

**What you get:**
- TCP errors (retransmissions, zero window, RST)
- Connection success rate
- Top talkers
- Protocol distribution
- DDoS threat assessment
- Complete in 10 seconds

---

### 2. Create Presentation Report

**Scenario:** Need visual diagrams for a meeting

```bash
analyze capture.pcap --visual
```

**What you get:**
- Network topology diagram (PNG)
- Protocol distribution chart (PNG)
- Interactive HTML report
- All text analysis
- Complete in 30 seconds

**Open the report:**
```bash
open ~/Desktop/pcap_analysis_output/*report.html
```

---

### 3. Security Investigation

**Scenario:** Suspicious traffic, need to identify sources

```bash
analyze capture.pcap --whois --tor
```

**What you get:**
- IP geolocation (country, org, ASN)
- Tor exit node detection
- DDoS threat scoring
- Port scan detection
- Firewall blocks
- Complete in 2 minutes

---

### 4. Complete Forensic Analysis

**Scenario:** Full investigation with all data

```bash
analyze capture.pcap --visual --whois --tor --export-json
```

**What you get:**
- Everything above
- JSON export for further analysis
- Complete in 3 minutes

---

### 5. Analyze Multiple Files

**Scenario:** Process several PCAP files

```bash
for file in *.pcap; do
    echo "Analyzing $file..."
    analyze "$file" --visual
done
```

All outputs organized in `~/Desktop/pcap_analysis_output/`

---

### 6. Quick DDoS Check

**Scenario:** Is this a DDoS attack?

```bash
analyze suspicious_traffic.pcap | grep -A 20 "DDoS"
```

**Look for:**
- 🔴 CRITICAL (Score 8+) - Active attack
- 🟠 HIGH (Score 5-7) - Possible attack
- 🟡 MEDIUM (Score 3-4) - Suspicious
- 🟢 LOW (Score 1-2) - Minor anomalies

---

### 7. Find Top Bandwidth Users

**Scenario:** Who's using all the bandwidth?

```bash
analyze capture.pcap | grep -A 15 "Top 10 Bandwidth"
```

---

### 8. Check for Errors Only

**Scenario:** Just show me the problems

```bash
analyze capture.pcap | grep -E "(⚠|✗|🔴)" | head -20
```

---

### 9. Export for Spreadsheet Analysis

**Scenario:** Need data in Excel/Google Sheets

```bash
analyze capture.pcap --export-json
```

Then open the JSON file in:
- Excel (Data > Get Data > From JSON)
- Google Sheets (File > Import > JSON)
- Python/R for custom analysis

---

### 10. Monitor Live Traffic

**Scenario:** Capture and analyze in real-time

```bash
# Capture for 60 seconds
sudo tcpdump -i en0 -w /tmp/live_capture.pcap -G 60 -W 1

# Analyze immediately
analyze /tmp/live_capture.pcap --visual
```

---

## 📊 INTERPRETING RESULTS

### TCP Health Indicators

**✓ EXCELLENT (>95% success rate)**
- Network is healthy
- No action needed

**⚠ DEGRADED (80-95% success rate)**
- Some packet loss
- Check network path

**✗ POOR (<80% success rate)**
- Significant issues
- Investigate immediately

### DDoS Threat Levels

**🔴 CRITICAL (8+ points)**
- Active DDoS attack likely
- Enable mitigation immediately
- Block attacking IPs
- Contact ISP/DDoS protection

**🟠 HIGH (5-7 points)**
- Possible DDoS or abuse
- Investigate source IPs
- Enable rate limiting
- Monitor for escalation

**🟡 MEDIUM (3-4 points)**
- Suspicious activity
- Continue monitoring
- Review logs

**🟢 LOW (1-2 points)**
- Minor anomalies
- Normal operation

### Common Error Patterns

**Retransmissions**
- Cause: Packet loss, network congestion
- Action: Check network path, bandwidth

**Zero Window**
- Cause: Receiver buffer full
- Action: Check application performance, increase buffers

**High RST Rate**
- Cause: Connection resets, firewall blocks
- Action: Review firewall rules, check application

**ICMP Unreachable**
- Cause: Routing issues, firewall blocks
- Action: Verify routing, check firewall

---

## 🎨 VISUAL OUTPUTS

### Network Diagram
- Shows top 30 conversations
- Arrow thickness = traffic volume
- Identifies key nodes

### Protocol Chart
- Pie chart of protocol distribution
- Color-coded by protocol
- Percentages shown

### HTML Report
- Interactive web page
- All statistics in one place
- Open in any browser

---

## 💡 PRO TIPS

**Tip 1:** Use `--visual` only when you need diagrams (saves time)

**Tip 2:** Pipe output to file for later review
```bash
analyze capture.pcap > analysis_report.txt
```

**Tip 3:** Combine with grep for specific info
```bash
analyze capture.pcap | grep "RST"
```

**Tip 4:** Check output folder regularly
```bash
open ~/Desktop/pcap_analysis_output/
```

**Tip 5:** Use JSON export for custom analysis
```bash
analyze capture.pcap --export-json
python3 my_custom_analysis.py analysis.json
```

---

## 🔍 TROUBLESHOOTING SCENARIOS

### Scenario: Slow Website

```bash
analyze website_traffic.pcap
```

**Look for:**
- High retransmission rate
- Zero window packets
- High latency (time gaps)
- DNS issues

### Scenario: Connection Timeouts

```bash
analyze timeout_capture.pcap
```

**Look for:**
- SYN without SYN-ACK
- ICMP unreachable
- High RST rate
- Firewall blocks

### Scenario: Suspected Attack

```bash
analyze attack_traffic.pcap --whois --tor
```

**Look for:**
- DDoS threat score
- Port scanning
- Tor traffic
- Single source flooding
- Unusual protocols

---

**Need more help? Run:** `analyze --help`
