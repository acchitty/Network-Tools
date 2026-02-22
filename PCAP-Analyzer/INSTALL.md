# PCAP Analyzer - Installation Guide

## 🚀 Quick Install (All Platforms)

### One-Command Installation

**macOS / Linux:**
```bash
cd PCAP_Analyzer_Deployment/PCAP-Analyzer
python3 install.py
```

**Windows:**
```powershell
cd PCAP_Analyzer_Deployment\PCAP-Analyzer
python install.py
```

That's it! The installer handles everything automatically.

---

## What Gets Installed

### 1. Python Dependencies
- ✅ scapy (packet analysis)
- ✅ matplotlib (visualizations)
- ✅ networkx (network graphs)
- ✅ ipwhois (IP lookups)
- ✅ requests (HTTP requests)

### 2. Analyzer Files

**macOS / Linux:**
```
~/.pcap_tools/
├── pcap_analyzer_v3.py      (75 KB) - Main analyzer
├── aws_detection.py          (9.6 KB) - AWS module
└── security_analysis.py      (7.7 KB) - Security module
```

**Windows:**
```
%USERPROFILE%\.pcap_tools\
├── pcap_analyzer_v3.py      (75 KB) - Main analyzer
├── aws_detection.py          (9.6 KB) - AWS module
└── security_analysis.py      (7.7 KB) - Security module
```

### 3. Command Wrapper

**macOS / Linux:**
- Location: `/usr/local/bin/analyze`
- Usage: `analyze capture.pcap`

**Windows:**
- Location: `%LOCALAPPDATA%\Programs\pcap-analyzer\analyze.bat`
- Usage: `analyze capture.pcap` (after restarting terminal)

### 4. Output Directory

**All Platforms:**
```
~/Desktop/pcap_analysis_output/
```

---

## Installation Process

The installer automatically:

1. ✅ **Checks Python version** (requires 3.7+)
2. ✅ **Installs all dependencies** via pip
3. ✅ **Copies analyzer files** to `~/.pcap_tools/`
4. ✅ **Creates command wrapper** (`analyze`)
5. ✅ **Creates output directory** on Desktop
6. ✅ **Adds to PATH** (Windows only)
7. ✅ **Tests installation** to verify it works
8. ✅ **Shows usage instructions**

---

## Usage

### Basic Analysis
```bash
analyze capture.pcap
```

### AWS-Specific Analysis
```bash
analyze capture.pcap --aws --security
```

### Full Analysis with Visuals
```bash
analyze capture.pcap --aws --security --visual --export-json
```

### All Available Flags
```bash
analyze capture.pcap \
  --aws \           # AWS service detection
  --security \      # Security analysis
  --visual \        # PNG diagrams + HTML
  --export-json \   # JSON export
  --whois \         # IP geolocation
  --tor             # Tor detection
```

---

## Platform-Specific Notes

### macOS
- ✅ Works out of the box
- ✅ tcpdump pre-installed
- ⚠️  May need to enter password for `/usr/local/bin` access

### Linux
- ✅ Works on all distributions
- ✅ tcpdump usually pre-installed
- ⚠️  May need sudo for `/usr/local/bin` access

### Windows
- ✅ Works on Windows 10/11
- ⚠️  Requires Npcap (Wireshark includes this)
- ⚠️  Must restart terminal after installation
- ⚠️  May need to run as Administrator

**Install Npcap (Windows only):**
1. Download: https://npcap.com/#download
2. Install with "WinPcap API-compatible Mode" checked
3. Restart computer

---

## Verification

### Check Installation
```bash
analyze --help
```

**Expected output:**
```
usage: pcap-analyzer [-h] [--export-json] [--visual] [--whois] [--tor]
                     [--aws] [--security]
                     pcap_file

Advanced PCAP Analyzer v4 - Enhanced Edition
```

### Check Dependencies
```bash
python3 -c "import scapy, matplotlib, networkx; print('All dependencies OK')"
```

### Check Files
**macOS / Linux:**
```bash
ls -lh ~/.pcap_tools/
```

**Windows:**
```powershell
dir %USERPROFILE%\.pcap_tools
```

---

## Troubleshooting

### Issue: "python3: command not found"
**Solution:** Install Python 3.7+ from https://python.org

### Issue: "Permission denied" (macOS/Linux)
**Solution:** Run with sudo:
```bash
sudo python3 install.py
```

### Issue: "analyze: command not found" (Windows)
**Solution:** Restart PowerShell/Command Prompt

### Issue: "No module named 'scapy'"
**Solution:** Manually install dependencies:
```bash
pip3 install scapy matplotlib networkx ipwhois requests
```

### Issue: Npcap not installed (Windows)
**Solution:** 
1. Download from https://npcap.com/#download
2. Install with WinPcap compatibility
3. Restart computer

---

## Uninstallation

### Remove Files
**macOS / Linux:**
```bash
rm -rf ~/.pcap_tools
sudo rm /usr/local/bin/analyze
rm -rf ~/Desktop/pcap_analysis_output
```

**Windows:**
```powershell
rmdir /s %USERPROFILE%\.pcap_tools
rmdir /s %LOCALAPPDATA%\Programs\pcap-analyzer
rmdir /s %USERPROFILE%\Desktop\pcap_analysis_output
```

### Remove Dependencies (Optional)
```bash
pip3 uninstall scapy matplotlib networkx ipwhois requests
```

---

## Update

To update to the latest version:

```bash
cd PCAP_Analyzer_Deployment/PCAP-Analyzer
git pull  # If using git
python3 install.py  # Reinstall
```

The installer will overwrite old files with new ones.

---

## Manual Installation (Advanced)

If the automatic installer doesn't work:

### 1. Install Dependencies
```bash
pip3 install scapy matplotlib networkx ipwhois requests
```

### 2. Copy Files
```bash
mkdir -p ~/.pcap_tools
cp pcap_analyzer_v3.py ~/.pcap_tools/
cp aws_detection.py ~/.pcap_tools/
cp security_analysis.py ~/.pcap_tools/
```

### 3. Create Wrapper (macOS/Linux)
```bash
sudo tee /usr/local/bin/analyze << 'EOF'
#!/bin/bash
python3 ~/.pcap_tools/pcap_analyzer_v3.py "$@"
EOF
sudo chmod +x /usr/local/bin/analyze
```

### 4. Create Wrapper (Windows)
```powershell
mkdir "$env:LOCALAPPDATA\Programs\pcap-analyzer"
@"
@echo off
python %USERPROFILE%\.pcap_tools\pcap_analyzer_v3.py %*
"@ | Out-File -FilePath "$env:LOCALAPPDATA\Programs\pcap-analyzer\analyze.bat" -Encoding ASCII
```

### 5. Create Output Directory
```bash
mkdir -p ~/Desktop/pcap_analysis_output
```

---

## Requirements

### Minimum Requirements
- Python 3.7 or higher
- 100 MB free disk space
- Internet connection (for installation only)

### Recommended
- Python 3.9+
- 500 MB free disk space (for large captures)
- 4 GB RAM

### Operating Systems
- ✅ macOS 10.14+
- ✅ Linux (any distribution)
- ✅ Windows 10/11

---

## Support

### Check Version
```bash
analyze --help | head -5
```

### Get Help
```bash
analyze --help
```

### Report Issues
Include this information:
- Operating system and version
- Python version (`python3 --version`)
- Error message
- Command you ran

---

## Quick Start After Installation

### 1. Capture Traffic
```bash
# macOS/Linux
sudo tcpdump -i any -w capture.pcap -c 1000

# Windows (requires Npcap)
# Use Wireshark GUI to capture
```

### 2. Analyze
```bash
analyze capture.pcap --aws --security --visual
```

### 3. View Results
```bash
# macOS/Linux
open ~/Desktop/pcap_analysis_output/

# Windows
explorer %USERPROFILE%\Desktop\pcap_analysis_output
```

---

## What's Next?

After installation:

1. ✅ Test with sample capture
2. ✅ Review output files
3. ✅ Try different flags
4. ✅ Read the full documentation

**Happy analyzing!** 🎉
