# Kubernetes Dashboard Installation Guide

This document provides detailed instructions for installing and configuring the Kubernetes Dashboard application with advanced metrics monitoring.

## Prerequisites

Before installing the dashboard, ensure you have the following prerequisites:

- Kubernetes cluster with version 1.19+
- `kubectl` configured with cluster access
- Python 3.6+
- `pip` package manager
- Metrics Server installed on your Kubernetes cluster
- Systemd (for service installation)
- Modern web browser with JavaScript enabled

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

## Features Overview

### Core Dashboard
- Real-time resource monitoring
- Pod, deployment, service, and namespace management
- Cluster health monitoring
- Alert notifications

### Metrics Dashboard (NEW)
- **Grafana-style interface** with dark theme
- **Real-time API request tracking** with Submit, Delivered, and Failure counts
- **Live traffic monitoring** with time ranges from 5 seconds to 6 hours
- **Success rate calculation** from actual pod logs
- **Interactive charts** powered by Chart.js
- **Namespace and pod filtering** for targeted monitoring
- **Historical data tracking** with 20-point rolling window

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
/root/kubernetes-dashboard/logs/k8s_dashboard.log
```

To view logs in real-time:

```bash
tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log
```

### Metrics Dashboard Configuration

The metrics dashboard automatically fetches data from pod logs. To monitor your applications:

1. **Deploy your application** in a namespace (e.g., `dsdp`)
2. **Ensure pods generate HTTP logs** in standard format
3. **Navigate to Metrics tab** in the dashboard
4. **Select your namespace** from the dropdown
5. **Choose time range** for monitoring (5s to 6h)

### Refresh Intervals

**Pod Health Monitor:**
```javascript
// In static/js/pod-health.js
setInterval(fetchPodHealthData, 30000); // 30 seconds
```

**Metrics Dashboard:**
```javascript
// In static/js/metrics.js
setInterval(loadMetricsData, 30000); // 30 seconds
```

## API Endpoints

### Core Endpoints
- `GET /` - Dashboard home page
- `GET /api/data` - Get all cluster resources
- `GET /api/pod-health` - Get pod health status
- `GET /api/hpa` - Get HPA information

### Metrics Endpoints
- `GET /api/request-metrics/<namespace>` - Get API request metrics
  - Query Parameters:
    - `time_range`: 5s, 10s, 30s, 60s, 5m, 15m, 1h, 6h (default: 1h)
    - `pod`: Specific pod name (optional)
  - Example:
    ```bash
    curl "http://localhost:8888/api/request-metrics/dsdp?time_range=5m"
    curl "http://localhost:8888/api/request-metrics/dsdp?time_range=30s&pod=my-pod-123"
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
   tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log
   ```

### Metrics Dashboard Not Showing Data

If the Metrics Dashboard is not showing data:

1. **Verify namespace has pods:**
   ```bash
   kubectl get pods -n <namespace>
   ```

2. **Check pod logs are accessible:**
   ```bash
   kubectl logs -n <namespace> <pod-name> --tail=10
   ```

3. **Test the API endpoint:**
   ```bash
   curl "http://localhost:8888/api/request-metrics/<namespace>?time_range=5m"
   ```

4. **Check browser console** for JavaScript errors

5. **Verify Chart.js is loaded:**
   - Open browser developer tools
   - Check Network tab for chart.js loading

### API Request Metrics Shows Zero

If API Request Metrics shows zero counts:

1. **Verify pods are generating HTTP logs:**
   ```bash
   kubectl logs -n <namespace> -l app=<your-app> --tail=50 | grep "GET"
   ```

2. **Check log format** - Logs should contain:
   - HTTP method (GET, POST, etc.)
   - Status code (200, 404, 500, etc.)
   - Example: `192.168.1.1 - - [06/Mar/2026:12:00:00 +0000] "GET / HTTP/1.1" 200 562`

3. **Verify time range** - Try shorter ranges (5s, 10s) for immediate testing

### Charts Not Updating

If charts are not updating:

1. **Check auto-refresh is enabled** (runs every 30 seconds)
2. **Click Refresh button manually**
3. **Clear browser cache** and reload
4. **Check browser console** for errors

### Pod Health Monitor Not Showing Data

If the Pod Health Monitor section is not showing data:

1. Check if the API endpoint is working:
   ```bash
   curl http://localhost:8888/api/pod-health
   ```

2. Verify that JavaScript is enabled in your browser
3. Check the browser console for any errors
4. Ensure the pod_health_monitor.py file is properly imported

### Details Modal Not Working

If the pod details modal is not appearing:

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
   python3 /root/kubernetes-dashboard/k8s_dashboard_server_updated.py
   ```

4. Check for port conflicts:
   ```bash
   sudo netstat -tulpn | grep 8888
   ```

## Testing the Metrics Dashboard

To test the metrics dashboard with sample traffic:

1. **Deploy a test application:**
   ```bash
   kubectl create namespace test-metrics
   kubectl run nginx --image=nginx -n test-metrics
   kubectl expose pod nginx --port=80 -n test-metrics
   ```

2. **Generate traffic:**
   ```bash
   kubectl run -it --rm load-test --image=busybox -n test-metrics -- /bin/sh
   # Inside the pod:
   while true; do wget -q -O- http://nginx; sleep 1; done
   ```

3. **View metrics:**
   - Navigate to Metrics tab
   - Select namespace: test-metrics
   - Select time range: 30s or 60s
   - Watch the API Request Metrics update

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

# Optionally remove the repository
cd ..
rm -rf kubernetes-dashboard
```

## Next Steps

After installation:

1. **Explore the Dashboard** - Navigate through different sections
2. **Configure Monitoring** - Set up namespaces and applications to monitor
3. **Review Documentation:**
   - [README.md](README.md) - General usage and features
   - [METRICS_REDESIGN.md](METRICS_REDESIGN.md) - Detailed metrics documentation
   - [METRICS_UI_WINDOW_FIX.md](METRICS_UI_WINDOW_FIX.md) - UI improvements

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the logs: `tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log`
- Open an issue on GitHub: https://github.com/Arvind960/kubernetes-dashboard/issues
