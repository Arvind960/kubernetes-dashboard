# Monitoring Integrations Guide

## Overview
Your Kubernetes Dashboard now has a dedicated Monitoring Integrations page with GUI controls for CloudWatch, Prometheus, and Azure Monitor.

## Access the Monitoring Page

**URL:** http://localhost:8888/monitoring

Or click the **"Monitoring"** link in the dashboard sidebar.

---

## 1. AWS CloudWatch Integration ✅ ACTIVE

### Status: Already Configured and Running

CloudWatch Container Insights is actively collecting metrics from your cluster.

### GUI Actions:
- **View Metrics** button → Opens AWS CloudWatch Console
- **Test Connection** button → Verifies CloudWatch API connectivity
- Real-time metrics display on the card

### What's Monitored:
- Cluster node count
- Running/Failed/Pending pods
- Container metrics
- Node status

### AWS Console Access:
https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#metricsV2

---

## 2. Prometheus Integration

### Status: Not Configured (Setup Available)

### Quick Setup via GUI:
1. Go to http://localhost:8888/monitoring
2. Click **"Setup Prometheus"** button
3. Or run manually:
   ```bash
   cd /root/kubernetes-dashboard
   ./setup_prometheus.sh
   ```

### Manual Setup:
```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus + Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### Access Prometheus:
```bash
# Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090

# Grafana UI (recommended for visualization)
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open: http://localhost:3000
# Login: admin / prom-operator
```

### Grafana Dashboards:
Once installed, Grafana comes with pre-built Kubernetes dashboards:
- Kubernetes / Compute Resources / Cluster
- Kubernetes / Compute Resources / Namespace
- Kubernetes / Compute Resources / Pod

---

## 3. Azure Monitor Integration

### Status: Not Configured

### For AKS Clusters:

#### Enable Container Insights:
```bash
az aks enable-addons \
  -a monitoring \
  -n <your-cluster-name> \
  -g <your-resource-group>
```

#### View in Azure Portal:
1. Navigate to your AKS cluster
2. Go to "Monitoring" → "Insights"
3. View metrics, logs, and container health

### For Non-AKS Clusters:

Deploy Azure Monitor agent:
```bash
kubectl apply -f https://aka.ms/ama-for-containers-yaml
```

Configure Log Analytics workspace connection.

---

## Architecture

### Current Setup:

```
┌─────────────────────────────────────┐
│   Kubernetes Dashboard (Port 8888)  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Monitoring Integrations UI  │  │
│  └──────────────────────────────┘  │
│              │                      │
│    ┌─────────┼─────────┐           │
│    │         │         │           │
│    ▼         ▼         ▼           │
│  ┌────┐  ┌────┐  ┌────┐           │
│  │ CW │  │Prom│  │Azure│           │
│  └────┘  └────┘  └────┘           │
└─────────────────────────────────────┘
         │         │         │
         ▼         ▼         ▼
    AWS Cloud  K8s Cluster  Azure
```

### Components:

1. **Dashboard Server** (`k8s_dashboard_server_updated.py`)
   - Flask web server
   - Kubernetes API client
   - CloudWatch API integration

2. **CloudWatch Exporter** (`k8s_cloudwatch_exporter.py`)
   - Background service
   - Sends metrics every 60 seconds
   - PID: Check with `ps aux | grep cloudwatch`

3. **Monitoring UI** (`templates/monitoring_integrations.html`)
   - Interactive GUI
   - Real-time metrics display
   - One-click setup buttons

---

## API Endpoints

### CloudWatch:
```bash
# Cluster metrics
curl http://localhost:8888/api/cloudwatch/cluster/kubernetes

# Pod metrics
curl http://localhost:8888/api/cloudwatch/pod/<namespace>/<pod-name>

# Node metrics
curl http://localhost:8888/api/cloudwatch/node/<node-name>
```

### Prometheus (after setup):
```bash
# Query Prometheus directly
curl http://localhost:9090/api/v1/query?query=up
```

---

## Troubleshooting

### CloudWatch Not Working:
```bash
# Check exporter logs
tail -f /root/kubernetes-dashboard/logs/cloudwatch_exporter.log

# Verify AWS credentials
aws sts get-caller-identity

# Restart exporter
pkill -f k8s_cloudwatch_exporter
cd /root/kubernetes-dashboard
nohup python3 k8s_cloudwatch_exporter.py >> logs/cloudwatch_exporter.log 2>&1 &
```

### Prometheus Not Installing:
```bash
# Check Helm
helm version

# Check namespace
kubectl get ns monitoring

# View Prometheus pods
kubectl get pods -n monitoring
```

### Dashboard Not Loading:
```bash
# Check dashboard status
ps aux | grep k8s_dashboard_server_updated

# View logs
tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log

# Restart dashboard
pkill -f k8s_dashboard_server_updated
cd /root/kubernetes-dashboard
nohup python3 k8s_dashboard_server_updated.py >> logs/k8s_dashboard.log 2>&1 &
```

---

## Next Steps

1. ✅ **CloudWatch** - Already working, view metrics in GUI
2. 🔧 **Prometheus** - Click "Setup Prometheus" button or run setup script
3. 🔧 **Azure Monitor** - Follow Azure setup guide if using AKS

---

## Files Reference

- `/root/kubernetes-dashboard/templates/monitoring_integrations.html` - GUI page
- `/root/kubernetes-dashboard/k8s_dashboard_server_updated.py` - Main server
- `/root/kubernetes-dashboard/cloudwatch_integration.py` - CloudWatch client
- `/root/kubernetes-dashboard/setup_prometheus.sh` - Prometheus installer
- `/root/kubernetes-dashboard/CLOUDWATCH_SETUP_COMPLETE.md` - CloudWatch docs

---

## Support

For issues or questions:
1. Check logs in `/root/kubernetes-dashboard/logs/`
2. Review documentation files in `/root/kubernetes-dashboard/`
3. Test API endpoints with curl commands above
