# Kubernetes Dashboard Installation Guide

This document provides detailed instructions for installing and configuring the Kubernetes Dashboard application.

## Prerequisites

Before installing the dashboard, ensure you have the following prerequisites:

- Kubernetes cluster with version 1.19+
- `kubectl` configured with cluster access
- Python 3.6+
- `pip` package manager
- Metrics Server installed on your Kubernetes cluster
- Systemd (for service installation)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/Arvind960/kubernetes-dashboard.git
cd kubernetes-dashboard
```

### 2. Install Required Python Packages

```bash
pip install -r requirements.txt
```

The requirements include:
- flask
- kubernetes
- requests
- datetime

### 3. Configure Kubernetes Access

Ensure your `kubectl` is properly configured to access your cluster:

```bash
kubectl cluster-info
```

The dashboard uses the same configuration as `kubectl`, so if this command works, the dashboard should be able to connect to your cluster.

### 4. Set Up as a Systemd Service (Recommended)

For persistent operation, set up the dashboard as a systemd service:

```bash
# Copy the service file to systemd directory
sudo cp k8s-dashboard.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable k8s-dashboard.service

# Start the service
sudo systemctl start k8s-dashboard.service
```

### 5. Verify Installation

Check if the service is running:

```bash
sudo systemctl status k8s-dashboard.service
```

Access the dashboard in your web browser:

```
http://localhost:8888
```

For the full dashboard with all features:

```
http://localhost:8888/full-dashboard
```

## Configuration Options

### Custom Port

To change the default port (8888), modify the `k8s_dashboard_server_updated.py` file:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=False)
```

Change `port=8888` to your desired port number.

### Log Location

Logs are stored in:

```
/root/python-script/logs/k8s_dashboard.log
```

To view logs in real-time:

```bash
tail -f /root/python-script/logs/k8s_dashboard.log
```

### Refresh Interval

To change the refresh interval for the Pod Health Monitor, modify the `static/js/pod-health.js` file:

```javascript
// Set up refresh interval
setInterval(fetchPodHealthData, 10000); // 10000 ms = 10 seconds
```

## Troubleshooting

### Dashboard Cannot Connect to Kubernetes API

If the dashboard cannot connect to the Kubernetes API:

1. Verify your kubeconfig:
   ```bash
   kubectl get nodes
   ```

2. Check if the metrics server is installed:
   ```bash
   kubectl get apiservice v1beta1.metrics.k8s.io
   ```

3. Examine the dashboard logs:
   ```bash
   tail -f /root/python-script/logs/k8s_dashboard.log
   ```

### Pod Health Monitor Not Showing Data

If the Pod Health Monitor section is not showing data:

1. Check if the API endpoint is working:
   ```bash
   curl http://localhost:8888/api/pod-health
   ```

2. Verify that JavaScript is enabled in your browser
3. Check the browser console for any errors
4. Ensure the pod_health_monitor.py file is properly imported in the main server file

### Details Modal Not Working

If the pod details modal is not appearing when clicking the Details button:

1. Check the browser console for JavaScript errors
2. Verify that Bootstrap is properly loaded
3. Ensure the modal HTML is present in the template
4. Check that the viewPodDetails function is being called

### Service Won't Start

If the service won't start:

1. Check the service status:
   ```bash
   sudo systemctl status k8s-dashboard.service
   ```

2. Verify the Python path in the service file:
   ```bash
   cat /etc/systemd/system/k8s-dashboard.service
   ```

3. Try running the script manually:
   ```bash
   python3 /root/python-script/k8s_dashboard_server_updated.py
   ```

## Uninstallation

To uninstall the dashboard:

```bash
# Stop and disable the service
sudo systemctl stop k8s-dashboard.service
sudo systemctl disable k8s-dashboard.service

# Remove the service file
sudo rm /etc/systemd/system/k8s-dashboard.service

# Reload systemd
sudo systemctl daemon-reload
```

## Next Steps

After installation, refer to the README.md file for usage instructions and features.
