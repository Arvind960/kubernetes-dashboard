#!/bin/bash

# Start the Kubernetes dashboard service
sudo systemctl start k8s-dashboard.service

# Print a message
echo "Kubernetes dashboard started. Access it at http://localhost:8888"
echo "Logs are being saved to /root/python-script/logs/k8s_dashboard.log"
echo "To view logs in real-time, run: tail -f /root/python-script/logs/k8s_dashboard.log"
echo "To stop the dashboard, run: sudo systemctl stop k8s-dashboard.service"
