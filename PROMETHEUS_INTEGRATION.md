# Prometheus Integration Guide

## Overview
The Kubernetes Dashboard can now fetch real metrics from Prometheus instead of using simulated data.

## Prerequisites

1. **Prometheus must be running** in your Kubernetes cluster
2. **Port-forward Prometheus** to localhost:9090

## Setup Steps

### 1. Install Prometheus (if not already installed)

```bash
cd /root/kubernetes-dashboard
./setup_prometheus.sh
```

### 2. Port-forward Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Keep this running in a separate terminal.

### 3. Test Prometheus Connection

```bash
curl http://localhost:9090/-/healthy
```

Should return: `Prometheus is Healthy.`

## Usage in Dashboard

### Python Integration

```python
from prometheus_client import PrometheusClient

# Initialize client
prom = PrometheusClient("http://localhost:9090")

# Check connection
if prom.check_connection():
    print("✅ Prometheus connected")

# Get CPU usage for a namespace
cpu_data = prom.get_pod_cpu_usage(namespace="test-application")

# Get memory usage for specific pod
mem_data = prom.get_pod_memory_usage(namespace="test-application", pod_name="my-pod")

# Get time-series metrics for dashboard
metrics = prom.get_metrics_range(
    namespace="test-application",
    pod_names=["pod-1", "pod-2"],
    duration_minutes=60
)
```

## API Endpoint Example

Add this to your Flask server (`k8s_dashboard_server_updated.py`):

```python
from prometheus_client import PrometheusClient

prom_client = PrometheusClient("http://localhost:9090")

@app.route('/api/prometheus/metrics')
def get_prometheus_metrics():
    namespace = request.args.get('namespace')
    pods = request.args.getlist('pod')
    duration = int(request.args.get('duration', 60))
    
    if not prom_client.check_connection():
        return jsonify({'error': 'Prometheus not available'}), 503
    
    metrics = prom_client.get_metrics_range(
        namespace=namespace,
        pod_names=pods if pods else None,
        duration_minutes=duration
    )
    
    return jsonify(metrics)
```

## Available Metrics

### CPU Usage
- Query: `rate(container_cpu_usage_seconds_total[5m])`
- Returns: CPU cores used per second

### Memory Usage
- Query: `container_memory_working_set_bytes`
- Returns: Memory in bytes

### Network Receive
- Query: `rate(container_network_receive_bytes_total[5m])`
- Returns: Bytes received per second

### Network Transmit
- Query: `rate(container_network_transmit_bytes_total[5m])`
- Returns: Bytes transmitted per second

## Troubleshooting

### Prometheus not accessible
```bash
# Check if Prometheus pod is running
kubectl get pods -n monitoring | grep prometheus

# Check port-forward
netstat -tuln | grep 9090
```

### No data returned
- Ensure your pods have metrics endpoints
- Check if metrics are being scraped: http://localhost:9090/targets
- Verify namespace and pod names are correct

## Configuration

Edit `prometheus_client.py` to change:
- Default Prometheus URL (default: `http://localhost:9090`)
- Query intervals
- Metric retention

## Next Steps

1. Integrate with metrics.js to use real Prometheus data
2. Add Prometheus health check in dashboard UI
3. Configure custom PromQL queries for specific metrics
