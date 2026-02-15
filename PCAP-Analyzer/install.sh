#!/bin/bash
# PCAP Analyzer v4 - Installation Script
# Automated deployment for macOS

set -e

echo "======================================"
echo "PCAP Analyzer v4 - Installation"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is for macOS only"
    exit 1
fi

echo "📋 Checking system requirements..."

# Find Python 3
PYTHON=""
for py in python3 /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 /usr/local/bin/python3; do
    if command -v $py &> /dev/null; then
        VERSION=$($py --version 2>&1 | awk '{print $2}')
        echo "✓ Found Python $VERSION at $py"
        PYTHON=$py
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3 not found. Please install Python 3.9 or later"
    exit 1
fi

# Check tcpdump
if ! command -v tcpdump &> /dev/null; then
    echo "❌ tcpdump not found (should be pre-installed on macOS)"
    exit 1
fi
echo "✓ tcpdump found"

echo ""
echo "📦 Installing Python dependencies..."
$PYTHON -m pip install --quiet --upgrade pip
$PYTHON -m pip install --quiet scapy matplotlib networkx ipwhois requests pillow

echo "✓ Python packages installed"

echo ""
echo "📁 Creating directories..."
mkdir -p ~/.pcap_tools
mkdir -p ~/Desktop/pcap_analysis_output
echo "✓ Directories created"

echo ""
echo "📄 Installing analyzer script..."
if [ -f "pcap_analyzer_v3.py" ]; then
    cp pcap_analyzer_v3.py ~/.pcap_tools/
    echo "✓ Analyzer installed to ~/.pcap_tools/"
else
    echo "⚠️  pcap_analyzer_v3.py not found in current directory"
    echo "   Checking if already installed..."
    if [ -f ~/.pcap_tools/pcap_analyzer_v3.py ]; then
        echo "✓ Analyzer already installed"
    else
        echo "❌ Analyzer script not found"
        exit 1
    fi
fi

echo ""
echo "🔧 Installing 'analyze' command..."

# Create analyze wrapper
sudo tee /usr/local/bin/analyze > /dev/null << EOF
#!/bin/bash
# PCAP Analyzer - Easy Launcher

PYTHON="$PYTHON"
ANALYZER="\$HOME/.pcap_tools/pcap_analyzer_v3.py"

# Run the analyzer with the correct Python
\$PYTHON \$ANALYZER "\$@"
EOF

sudo chmod +x /usr/local/bin/analyze
echo "✓ Command installed to /usr/local/bin/analyze"

echo ""
echo "✅ Installation complete!"
echo ""
echo "======================================"
echo "🚀 QUICK START"
echo "======================================"
echo ""
echo "Run from anywhere:"
echo "  ${GREEN}analyze capture.pcap${NC}"
echo ""
echo "With visual diagrams:"
echo "  ${GREEN}analyze capture.pcap --visual${NC}"
echo ""
echo "Full analysis:"
echo "  ${GREEN}analyze capture.pcap --visual --whois --tor --export-json${NC}"
echo ""
echo "All outputs save to:"
echo "  ${YELLOW}~/Desktop/pcap_analysis_output/${NC}"
echo ""
echo "For help:"
echo "  ${GREEN}analyze --help${NC}"
echo ""
echo "======================================"
