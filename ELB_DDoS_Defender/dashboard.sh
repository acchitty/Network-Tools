#!/bin/bash
# ELB DDoS Defender - Dashboard Launcher

DASHBOARD="/opt/elb-ddos-defender/elb-ddos-dashboard.py"
PYTHON="/usr/bin/python3"

# Check if dashboard exists
if [ ! -f "$DASHBOARD" ]; then
    echo "Error: Dashboard not found at $DASHBOARD"
    exit 1
fi

# Check if rich is installed
$PYTHON -c "import rich" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing rich library..."
    pip3 install rich
fi

# Run dashboard
$PYTHON "$DASHBOARD"
