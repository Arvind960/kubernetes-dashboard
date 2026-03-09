# Prometheus Integration - Quick Start Guide

## Step-by-Step Setup

### Step 1: Run the Setup Script

```bash
cd /root/kubernetes-dashboard
chmod +x setup_prometheus_complete.sh
./setup_prometheus_complete.sh
```

This will:
- ✅ Check Kubernetes cluster
- ✅ Install Helm (if needed)
- ✅ Install Prometheus in your cluster
- ✅ Create helper scripts

**Time:** ~5-10 minutes

---

### Step 2: Start Prometheus Port-Forward

Open a **new terminal** and run:

```bash
cd /root/kubernetes-dashboard
./start_prometheus_forward.sh
```

Keep this terminal open. You should see:
```
Starting Prometheus port-forward on localhost:9090...
Forwarding from 127.0.0.1:9090 -> 9090
```

---

### Step 3: Test Prometheus Connection

In another terminal:

```bash
curl http://localhost:9090/-/healthy
```

Expected output: `Prometheus is Healthy.`

---

### Step 4: Restart Dashboard

```bash
cd /root/kubernetes-dashboard
./stop_dashboard.sh
./start_dashboard.sh
```

You should see:
```
✅ Prometheus connected at http://localhost:9090
```

---

### Step 5: Verify Integration

Open your browser: **http://localhost:8888**

Check Prometheus status:
```bash
curl http://localhost:8888/api/prometheus/status
```

Expected output:
```json
{
  "available": true,
  "connected": true,
  "url": "http://localhost:9090"
}
```

---

## Using Prometheus Metrics in Dashboard

### Option 1: Automatic (Recommended)

The dashboard will automatically use Prometheus metrics when:
1. Prometheus is running and port-forwarded
2. You select a namespace with pods
3. Metrics will show real data instead of simulated

### Option 2: API Endpoint

Fetch metrics directly:

```bash
# Get metrics for test-application namespace
curl "http://localhost:8888/api/prometheus/metrics?namespace=test-application&duration=60"

# Get metrics for specific pods
curl "http://localhost:8888/api/prometheus/metrics?namespace=test-application&pod=pod-1&pod=pod-2"
```

---

## Troubleshooting

### Problem: "Prometheus not connected"

**Solution:**
```bash
# Check if port-forward is running
ps aux | grep "port-forward.*9090"

# If not running, start it
cd /root/kubernetes-dashboard
./start_prometheus_forward.sh
```

### Problem: "Prometheus not available"

**Solution:**
```bash
# Check if Prometheus pod is running
kubectl get pods -n monitoring | grep prometheus

# If not running, reinstall
./setup_prometheus_complete.sh
```

### Problem: No metrics data

**Solution:**
```bash
# Check if your pods are being scraped
# Open Prometheus UI: http://localhost:9090
# Go to Status > Targets
# Verify your namespace/pods are listed
```

---

## What Metrics Are Available?

When Prometheus is connected, you get **real-time metrics**:

- **CPU Usage**: Actual CPU cores used by pods
- **Memory Usage**: Real memory consumption in bytes
- **Network RX**: Actual bytes received per second
- **Network TX**: Actual bytes transmitted per second

---

## Stopping Prometheus

To stop the port-forward:
```bash
# Find the process
ps aux | grep "port-forward.*9090"

# Kill it
pkill -f "port-forward.*9090"
```

To uninstall Prometheus:
```bash
helm uninstall prometheus -n monitoring
kubectl delete namespace monitoring
```

---

## Next Steps

1. ✅ Prometheus is now integrated
2. ✅ Dashboard shows real metrics
3. ✅ Multi-pod selection works with Prometheus data

Enjoy your real-time Kubernetes metrics! 🚀
