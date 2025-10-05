#!/bin/bash
# Startup script for Process Recovery Agent

set -e

echo "Starting Process Recovery Agent..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is required but not installed"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import psutil, yaml, requests" 2>/dev/null || {
    echo "Installing required packages..."
    pip install psutil pyyaml requests
}

# Create necessary directories
mkdir -p /workspace/src/recovery
mkdir -p /workspace/config
mkdir -p /workspace/logs

# Set permissions
chmod +x /workspace/src/recovery/process_recovery_agent.py

# Start the recovery agent
echo "Starting Process Recovery Agent..."
cd /workspace
python3 src/recovery/process_recovery_agent.py &

# Get the PID
RECOVERY_PID=$!
echo "Recovery Agent started with PID: $RECOVERY_PID"

# Save PID for later use
echo $RECOVERY_PID > /workspace/recovery_agent.pid

echo "Process Recovery Agent is now running in the background"
echo "To stop the agent, run: kill $RECOVERY_PID"
echo "To check status, run: ps aux | grep process_recovery_agent"
echo "To view logs, run: tail -f recovery_agent.log"