#!/bin/bash

# Make scripts executable
chmod +x /root/python-script/k8s_visual_monitor.py

# Create templates directory if it doesn't exist
mkdir -p /root/python-script/templates

# Start the monitoring application
cd /root/python-script
python3 k8s_visual_monitor.py
