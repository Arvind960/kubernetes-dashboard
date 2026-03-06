# Fix for "status=200/CHDIR" Error

## Problem
The systemd service fails with `status=200/CHDIR` error because the WorkingDirectory path in the service file doesn't match the actual installation location.

## Quick Fix

### Option 1: Use the Setup Script (Recommended)
```bash
cd /tmp/kubernetes-dashboard  # or wherever you installed it
./setup_service.sh
```

This script automatically detects the installation directory and configures the service correctly.

### Option 2: Manual Fix

1. **Stop the failing service:**
```bash
sudo systemctl stop k8s-dashboard.service
```

2. **Edit the service file:**
```bash
sudo nano /etc/systemd/system/k8s-dashboard.service
```

3. **Update all paths to match your installation directory:**

If installed in `/tmp/kubernetes-dashboard`, change:
```ini
[Unit]
Description=Kubernetes Dashboard Service
After=network.target

[Service]
User=root
WorkingDirectory=/tmp/kubernetes-dashboard
ExecStart=/usr/bin/python3 /tmp/kubernetes-dashboard/k8s_dashboard_server_updated.py
Restart=always
RestartSec=10
StandardOutput=append:/tmp/kubernetes-dashboard/logs/k8s_dashboard.log
StandardError=append:/tmp/kubernetes-dashboard/logs/k8s_dashboard.log

[Install]
WantedBy=multi-user.target
```

4. **Create logs directory:**
```bash
mkdir -p /tmp/kubernetes-dashboard/logs
```

5. **Reload and restart:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart k8s-dashboard.service
sudo systemctl status k8s-dashboard.service
```

## Verification

Check if the service is running:
```bash
sudo systemctl status k8s-dashboard.service
```

Should show: `Active: active (running)`

View logs:
```bash
tail -f /tmp/kubernetes-dashboard/logs/k8s_dashboard.log
```

Access dashboard:
```
http://localhost:8888
```

## Common Issues

### Issue: Python not found
**Solution:** Install Python 3 and required packages:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
pip3 install flask kubernetes
```

### Issue: Permission denied
**Solution:** Ensure the user has permissions:
```bash
sudo chown -R root:root /tmp/kubernetes-dashboard
chmod +x /tmp/kubernetes-dashboard/*.sh
chmod +x /tmp/kubernetes-dashboard/*.py
```

### Issue: Port already in use
**Solution:** Check what's using port 8888:
```bash
sudo lsof -i :8888
# Kill the process or change the port in k8s_dashboard_server_updated.py
```

## Alternative: Run Without Systemd

If you don't want to use systemd, run directly:
```bash
cd /tmp/kubernetes-dashboard
./start_dashboard.sh
```

Or manually:
```bash
cd /tmp/kubernetes-dashboard
nohup python3 k8s_dashboard_server_updated.py > logs/k8s_dashboard.log 2>&1 &
```
