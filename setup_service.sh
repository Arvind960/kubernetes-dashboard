#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up Kubernetes Dashboard service..."
echo "Installation directory: $SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Create service file with correct paths
cat > /tmp/k8s-dashboard.service << EOF
[Unit]
Description=Kubernetes Dashboard Service
After=network.target

[Service]
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/k8s_dashboard_server_updated.py
Restart=always
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/logs/k8s_dashboard.log
StandardError=append:$SCRIPT_DIR/logs/k8s_dashboard.log

[Install]
WantedBy=multi-user.target
EOF

# Copy service file to systemd directory
sudo cp /tmp/k8s-dashboard.service /etc/systemd/system/k8s-dashboard.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable k8s-dashboard.service
sudo systemctl restart k8s-dashboard.service

# Wait a moment for service to start
sleep 2

# Check status
sudo systemctl status k8s-dashboard.service --no-pager

echo ""
echo "Setup complete!"
echo "Dashboard URL: http://localhost:8888"
echo "Logs: $SCRIPT_DIR/logs/k8s_dashboard.log"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status k8s-dashboard.service"
echo "  sudo systemctl restart k8s-dashboard.service"
echo "  tail -f $SCRIPT_DIR/logs/k8s_dashboard.log"
