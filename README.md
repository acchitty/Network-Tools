# PCAP Analyzer - Complete User Guide

## 🚀 QUICK START

```bash
analyze capture.pcap
```

All outputs save to: `~/Desktop/pcap_analysis_output/`

## 📖 TABLE OF CONTENTS

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Command Options](#command-options)
4. [Output Files](#output-files)
5. [Features](#features)
6. [Performance](#performance)
7. [Troubleshooting](#troubleshooting)
8. [Examples](#examples)

## 📦 INSTALLATION

Run the installer:
```bash
cd PCAP_Analyzer_Deployment
./install.sh
```

**What it installs:**
- Python dependencies
- Analyzer script (`~/.pcap_tools/`)
- `analyze` command (`/usr/local/bin/`)
- Output folder (`~/Desktop/pcap_analysis_output/`)

## 🎯 BASIC USAGE

### Quick Analysis (10 seconds)
```bash
analyze capture.pcap
```

### With Visual Diagrams (30 seconds)
```bash
analyze capture.pcap --visual
```

### Full Analysis (3 minutes)
```bash
analyze capture.pcap --visual --whois --tor --export-json
```

## ⚙️ COMMAND OPTIONS

| Flag | Description | Time Added |
|------|-------------|------------|
| `--visual` | Generate PNG diagrams and HTML report | +20 sec |
| `--whois` | Perform IP geolocation lookups | +2 min |
| `--tor` | Check for Tor exit nodes | +5 sec |
| `--export-json` | Export data to JSON file | +1 sec |

**Combine flags:**
```bash
analyze capture.pcap --visual --tor
```

## 📁 OUTPUT FILES

All files save to: `~/Desktop/pcap_analysis_output/`

### With `--visual` flag:

1. **`filename_network_diagram.png`**
   - Visual network topology
   - Top 30 conversations
   - Arrow thickness shows traffic volume

2. **`filename_protocol_chart.png`**
   - Protocol distribution pie chart
   - Color-coded by protocol
   - Percentages labeled

3. **`filename_report.html`**
   - Interactive HTML report
   - All statistics in one page
   - Open in any web browser

4. **`filename_analysis.json`** (with `--export-json`)
   - Complete data export
   - For custom analysis
   - Import into Excel/Python/R

### Open outputs:
```bash
open ~/Desktop/pcap_analysis_output/
```

## ✨ FEATURES

### Core Analysis (Always Included)

**Network Health:**
- TCP connection success rate
- Handshake analysis (SYN/SYN-ACK/ACK)
- Connection termination (FIN/RST)

**Error Detection:**
- Retransmissions (packet loss)
- Zero window (buffer full)
- Duplicate ACKs (missing packets)
- Out-of-order packets
- Connection resets (RST)

**DDoS Detection (9 Methods):**
1. SYN flood detection
2. High RST rate analysis
3. Single source flooding
4. UDP flood detection
5. ICMP flood detection
6. Port scan detection
7. Extreme packet rate
8. Half-open connections
9. Retransmission storms

**Threat Scoring:**
- 🔴 CRITICAL (8+) - Active attack
- 🟠 HIGH (5-7) - Possible attack
- 🟡 MEDIUM (3-4) - Suspicious
- 🟢 LOW (1-2) - Minor anomalies

**Protocol Analysis:**
- TCP, UDP, ICMP, ARP, DNS
- HTTP/HTTPS traffic
- TLS/SSL handshakes
- Geneve encapsulation

**Network Topology:**
- Top conversations
- Bandwidth per IP
- Internal vs external traffic
- Communication patterns

**Performance Metrics:**
- Packet rate (packets/sec)
- Bandwidth usage
- Packet size distribution
- Traffic bursts and gaps

**Security Analysis:**
- Firewall blocks
- Port scanning
- Connection patterns
- Suspicious activity

### Optional Features

**--visual:**
- Network diagram (PNG)
- Protocol chart (PNG)
- Interactive HTML report

**--whois:**
- IP geolocation (country)
- Organization/ISP info
- ASN (Autonomous System Number)
- Cached for performance

**--tor:**
- Downloads Tor exit node list
- Identifies Tor traffic
- Shows which IPs are Tor nodes

**--export-json:**
- Complete data export
- All statistics and metrics
- For custom analysis

## ⚡ PERFORMANCE

| Mode | Time | Output |
|------|------|--------|
| Default | 10 sec | Text analysis |
| + --visual | 30 sec | + PNG + HTML |
| + --whois | 2 min | + Geolocation |
| + --tor | 15 sec | + Tor detection |
| All flags | 3 min | Everything |

**File size:** 5 MB PCAP ≈ 15,000 packets

## 🔧 TROUBLESHOOTING

### Command not found

**Check installation:**
```bash
which analyze
```

Should show: `/usr/local/bin/analyze`

**Reinstall:**
```bash
cd PCAP_Analyzer_Deployment
./install.sh
```

### No output files

**Check output folder:**
```bash
ls ~/Desktop/pcap_analysis_output/
```

**Verify --visual flag was used:**
```bash
analyze capture.pcap --visual
```

### Module not found errors

**Reinstall dependencies:**
```bash
pip3 install -r requirements.txt
```

### Permission denied

**Make command executable:**
```bash
sudo chmod +x /usr/local/bin/analyze
```

## 📚 EXAMPLES

See `EXAMPLES.md` for detailed usage scenarios including:
- Quick troubleshooting
- Creating presentations
- Security investigations
- Forensic analysis
- DDoS detection
- And more!

## 🎓 INTERPRETING RESULTS

### TCP Health

**✓ EXCELLENT (>95%)**
- Network is healthy
- No action needed

**⚠ DEGRADED (80-95%)**
- Some packet loss
- Check network path

**✗ POOR (<80%)**
- Significant issues
- Investigate immediately

### Common Issues

**Retransmissions:**
- Cause: Packet loss, congestion
- Action: Check network path

**Zero Window:**
- Cause: Receiver buffer full
- Action: Check application performance

**High RST Rate:**
- Cause: Connection resets
- Action: Review firewall rules

**ICMP Unreachable:**
- Cause: Routing/firewall issues
- Action: Verify routing tables

## 🆚 COMPARISON

### vs PcapXray

| Feature | PCAP Analyzer v4 | PcapXray |
|---------|------------------|----------|
| Speed | ⚡ 10-30 sec | 🐌 30+ min |
| DDoS Detection | ✅ 9 methods | ❌ None |
| Error Analysis | ✅ Extensive | ❌ Basic |
| Visual Diagrams | ✅ Optional | ✅ Always |
| Output Location | ✅ Organized | ❌ Scattered |
| Interface | Terminal | GUI |
| Whois Lookups | ✅ Optional | ✅ Always |
| Tor Detection | ✅ Optional | ✅ Always |

**Advantages:**
- 100x faster
- More comprehensive
- Better organized
- Optional features (stay fast)
- Command-line automation

### vs Wireshark

| Feature | PCAP Analyzer v4 | Wireshark |
|---------|------------------|-----------|
| Speed | ⚡ Automated | 🐢 Manual |
| DDoS Detection | ✅ Automatic | ❌ Manual |
| Reports | ✅ Automatic | ❌ Manual |
| Batch Processing | ✅ Easy | ❌ Difficult |
| Visual Diagrams | ✅ Automatic | ❌ Manual |
| Learning Curve | ✅ Easy | ⚠️ Steep |

**Use both:**
- Analyzer for quick automated analysis
- Wireshark for deep packet inspection

## 💡 PRO TIPS

1. **Use default mode for speed** - Only add flags when needed
2. **Pipe output to file** - `analyze capture.pcap > report.txt`
3. **Combine with grep** - `analyze capture.pcap | grep "RST"`
4. **Batch process** - `for f in *.pcap; do analyze "$f"; done`
5. **Check output folder** - `open ~/Desktop/pcap_analysis_output/`

## 📞 SUPPORT

**Get help:**
```bash
analyze --help
```

**Check version:**
```bash
analyze --version 2>&1 | head -5
```

**View examples:**
```bash
cat EXAMPLES.md
```

## 📄 FILES

- **Analyzer:** `~/.pcap_tools/pcap_analyzer_v3.py`
- **Command:** `/usr/local/bin/analyze`
- **Outputs:** `~/Desktop/pcap_analysis_output/`

## 🎉 YOU'RE READY!

Start analyzing:
```bash
analyze your_capture.pcap --visual
```

---

**Made with ❤️ for network analysis**
