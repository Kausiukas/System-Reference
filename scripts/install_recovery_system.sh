#!/bin/bash
# Installation script for Process Recovery System

set -e

echo "Installing Process Recovery System..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y python3 python3-pip python3-venv systemd

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install psutil pyyaml requests

# Create necessary directories
echo "Creating directories..."
mkdir -p /workspace/src/recovery
mkdir -p /workspace/config
mkdir -p /workspace/logs
mkdir -p /workspace/scripts

# Set permissions
echo "Setting permissions..."
chmod +x /workspace/src/recovery/process_recovery_agent.py
chmod +x /workspace/scripts/start_recovery_agent.sh
chmod +x /workspace/scripts/install_recovery_system.sh

# Install systemd service
echo "Installing systemd service..."
cp /workspace/config/recovery-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable recovery-agent.service

# Create initial tasklog
echo "Creating initial tasklog..."
touch /workspace/tasklog.md
chmod 666 /workspace/tasklog.md

# Create recovery state file
echo "Creating recovery state file..."
cat > /workspace/recovery_state.json << EOF
{
  "last_activity": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "active_tasks": [],
  "completed_tasks": [],
  "failed_tasks": [],
  "recovery_count": 0,
  "last_recovery": null
}
EOF

# Start the service
echo "Starting recovery agent service..."
systemctl start recovery-agent.service

# Check status
echo "Checking service status..."
systemctl status recovery-agent.service --no-pager

echo ""
echo "Process Recovery System installed successfully!"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start recovery-agent"
echo "  Stop:    sudo systemctl stop recovery-agent"
echo "  Status:  sudo systemctl status recovery-agent"
echo "  Logs:    sudo journalctl -u recovery-agent -f"
echo ""
echo "Manual commands:"
echo "  Start:   /workspace/scripts/start_recovery_agent.sh"
echo "  Logs:    tail -f /workspace/recovery_agent.log"
echo "  Status:  ps aux | grep process_recovery_agent"
echo ""
echo "Configuration files:"
echo "  Config:  /workspace/config/recovery_config.yaml"
echo "  Tasklog: /workspace/tasklog.md"
echo "  State:   /workspace/recovery_state.json"