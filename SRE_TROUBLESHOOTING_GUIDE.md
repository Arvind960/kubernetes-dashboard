# SRE-Level Troubleshooting Guide

## Quick Diagnostics

```bash
# Check dashboard service status
systemctl status k8s-dashboard.service

# View recent logs
tail -100 /root/kubernetes-dashboard/logs/k8s_dashboard.log

# Test Kubernetes API connectivity
kubectl cluster-info

# Check metrics server
kubectl top nodes
```

## Common Issues

### 1. Dashboard Not Accessible

**Symptoms**: Cannot access http://localhost:8888

**Diagnosis**:
```bash
# Check if service is running
ps aux | grep k8s_dashboard_server

# Check port binding
netstat -tlnp | grep 8888

# Check firewall
iptables -L -n | grep 8888
```

**Resolution**:
```bash
# Restart service
systemctl restart k8s-dashboard.service

# Check logs for errors
journalctl -u k8s-dashboard.service -n 50
```

### 2. No Metrics Displayed

**Symptoms**: Dashboard loads but shows no CPU/memory data

**Diagnosis**:
```bash
# Verify metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Test metrics API
kubectl top nodes
kubectl top pods -A
```

**Resolution**:
```bash
# Install metrics-server if missing
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For development clusters, may need insecure TLS
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

### 3. Authentication Failures

**Symptoms**: "Unauthorized" or "Forbidden" errors in logs

**Diagnosis**:
```bash
# Check kubeconfig
kubectl config view

# Test current context
kubectl auth can-i get pods --all-namespaces

# Verify service account permissions
kubectl describe serviceaccount default
```

**Resolution**:
```bash
# Create RBAC if needed
kubectl create clusterrolebinding dashboard-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=default:default
```

### 4. High Memory Usage

**Symptoms**: Dashboard consuming excessive memory

**Diagnosis**:
```bash
# Check process memory
ps aux | grep k8s_dashboard | awk '{print $6}'

# Monitor over time
watch -n 5 'ps aux | grep k8s_dashboard'
```

**Resolution**:
```bash
# Restart service to clear memory
systemctl restart k8s-dashboard.service

# Add memory limits to service file
# Edit /etc/systemd/system/k8s-dashboard.service
# Add: MemoryLimit=512M
```

### 5. Slow Response Times

**Symptoms**: Dashboard takes >5 seconds to load data

**Diagnosis**:
```bash
# Check API server latency
kubectl get --raw /metrics | grep apiserver_request_duration

# Test direct API calls
time kubectl get pods -A

# Check network connectivity
ping -c 5 $(kubectl config view -o jsonpath='{.clusters[0].cluster.server}' | cut -d/ -f3 | cut -d: -f1)
```

**Resolution**:
```bash
# Reduce polling frequency in dashboard
# Implement caching for frequently accessed data
# Consider using watch API instead of polling
```

## Advanced Diagnostics

### Log Analysis

```bash
# Find errors in last hour
grep -i error /root/kubernetes-dashboard/logs/k8s_dashboard.log | tail -50

# Check for API timeouts
grep -i timeout /root/kubernetes-dashboard/logs/k8s_dashboard.log

# Monitor live logs
tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log | grep -E 'ERROR|WARNING|CRITICAL'
```

### Performance Profiling

```bash
# Enable Flask debug mode (development only)
export FLASK_DEBUG=1

# Add timing to API calls
curl -w "@-" -o /dev/null -s http://localhost:8888/api/data <<'EOF'
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_total:  %{time_total}\n
EOF
```

### Database Connection Issues

```bash
# Check if Kubernetes API is reachable
kubectl cluster-info dump | grep -i error

# Verify DNS resolution
nslookup kubernetes.default.svc.cluster.local

# Test API server directly
curl -k https://$(kubectl config view -o jsonpath='{.clusters[0].cluster.server}' | cut -d/ -f3)/api/v1/namespaces
```

## Monitoring & Alerting

### Key Metrics to Monitor

1. **Response Time**: API endpoint latency
2. **Error Rate**: HTTP 5xx responses
3. **Memory Usage**: Process RSS
4. **CPU Usage**: Process CPU percentage
5. **API Call Rate**: Requests to Kubernetes API

### Health Check Script

```bash
#!/bin/bash
# /root/kubernetes-dashboard/health_check.sh

ENDPOINT="http://localhost:8888/api/data"
TIMEOUT=10

response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT $ENDPOINT)

if [ "$response" = "200" ]; then
    echo "OK: Dashboard is healthy"
    exit 0
else
    echo "CRITICAL: Dashboard returned $response"
    systemctl restart k8s-dashboard.service
    exit 2
fi
```

## Disaster Recovery

### Backup Configuration

```bash
# Backup service file
cp /etc/systemd/system/k8s-dashboard.service /root/backup/

# Backup application code
tar -czf /root/backup/dashboard-$(date +%Y%m%d).tar.gz /root/kubernetes-dashboard/
```

### Recovery Procedures

```bash
# Complete service restart
systemctl stop k8s-dashboard.service
pkill -f k8s_dashboard_server
systemctl start k8s-dashboard.service

# Clear logs if disk full
> /root/kubernetes-dashboard/logs/k8s_dashboard.log

# Reinstall dependencies
pip install --force-reinstall -r /root/kubernetes-dashboard/requirements.txt
```

## Performance Tuning

### Optimize API Calls

```python
# Implement caching in k8s_dashboard_server_updated.py
from functools import lru_cache
from datetime import datetime, timedelta

cache_time = {}

@lru_cache(maxsize=128)
def get_cached_pods(timestamp):
    # Cache for 5 seconds
    return v1.list_pod_for_all_namespaces()
```

### Reduce Polling Frequency

```javascript
// In frontend, adjust refresh interval
const REFRESH_INTERVAL = 10000; // 10 seconds instead of 5
```

### Connection Pooling

```python
# Use connection pooling for Kubernetes client
from kubernetes import client, config
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

config.load_kube_config()
configuration = client.Configuration.get_default_copy()
configuration.retries = Retry(total=3, backoff_factor=0.3)
```

## Security Hardening

### Enable HTTPS

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /root/kubernetes-dashboard/key.pem \
  -out /root/kubernetes-dashboard/cert.pem \
  -days 365 -subj "/CN=localhost"

# Update Flask to use SSL
# In k8s_dashboard_server_updated.py:
# app.run(host='0.0.0.0', port=8888, ssl_context=('cert.pem', 'key.pem'))
```

### Implement Authentication

```python
# Add basic auth to Flask app
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

auth = HTTPBasicAuth()

users = {
    "admin": generate_password_hash("secure_password")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
```

## Troubleshooting Checklist

- [ ] Service is running: `systemctl status k8s-dashboard.service`
- [ ] Port 8888 is listening: `netstat -tlnp | grep 8888`
- [ ] Kubernetes API accessible: `kubectl cluster-info`
- [ ] Metrics server running: `kubectl top nodes`
- [ ] No errors in logs: `tail -50 /root/kubernetes-dashboard/logs/k8s_dashboard.log`
- [ ] Sufficient disk space: `df -h`
- [ ] Sufficient memory: `free -h`
- [ ] Python dependencies installed: `pip list | grep -E 'flask|kubernetes'`
- [ ] Kubeconfig valid: `kubectl config view`
- [ ] Network connectivity: `curl -I http://localhost:8888`

## Escalation Procedures

### When to Escalate

1. Dashboard down for >15 minutes
2. Data corruption or inconsistencies
3. Security incidents
4. Persistent performance degradation
5. Kubernetes API issues affecting multiple services

### Information to Collect

```bash
# Generate diagnostic bundle
mkdir -p /tmp/dashboard-diagnostics
systemctl status k8s-dashboard.service > /tmp/dashboard-diagnostics/service-status.txt
journalctl -u k8s-dashboard.service -n 500 > /tmp/dashboard-diagnostics/service-logs.txt
cp /root/kubernetes-dashboard/logs/k8s_dashboard.log /tmp/dashboard-diagnostics/
kubectl cluster-info dump > /tmp/dashboard-diagnostics/cluster-info.txt
kubectl get pods -A -o wide > /tmp/dashboard-diagnostics/all-pods.txt
kubectl top nodes > /tmp/dashboard-diagnostics/node-metrics.txt
tar -czf /tmp/dashboard-diagnostics-$(date +%Y%m%d-%H%M%S).tar.gz /tmp/dashboard-diagnostics/
```

## Contact & Support

- GitHub Issues: https://github.com/Arvind960/kubernetes-dashboard/issues
- Documentation: /root/kubernetes-dashboard/README.md
- Architecture: /root/kubernetes-dashboard/ARCHITECTURE.md
