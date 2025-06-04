#!/bin/bash

# Stop the Kubernetes dashboard service
sudo systemctl stop k8s-dashboard.service

# Print a message
echo "Kubernetes dashboard stopped."
