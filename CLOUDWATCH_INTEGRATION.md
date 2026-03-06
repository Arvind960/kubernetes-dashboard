# CloudWatch Integration Guide

## Overview
This integration adds AWS CloudWatch Container Insights metrics to the Kubernetes dashboard.

## Prerequisites
1. AWS credentials configured (via `~/.aws/credentials` or IAM role)
2. CloudWatch Container Insights enabled on your EKS cluster
3. boto3 installed: `pip install boto3`

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AWS Region
```bash
export AWS_REGION=us-east-1  # Change to your region
```

### 3. Add to Existing Dashboard Server

Add these lines to your main server file (e.g., `k8s_dashboard_server_updated.py`):

```python
# Import CloudWatch blueprint
from cloudwatch_api import cloudwatch_bp

# Register blueprint
app.register_blueprint(cloudwatch_bp)
```

## API Endpoints

### Pod Metrics
```
GET /api/cloudwatch/pod/<namespace>/<pod_name>?minutes=5
```

Returns:
- pod_cpu_utilization
- pod_memory_utilization
- pod_network_rx_bytes
- pod_network_tx_bytes

### Node Metrics
```
GET /api/cloudwatch/node/<node_name>?minutes=5
```

Returns:
- node_cpu_utilization
- node_memory_utilization
- node_filesystem_utilization

### Cluster Metrics
```
GET /api/cloudwatch/cluster/<cluster_name>?minutes=5
```

Returns:
- cluster_failed_node_count
- cluster_node_count
- namespace_number_of_running_pods

### Custom Metrics
```
GET /api/cloudwatch/custom?namespace=MyApp&metric_name=RequestCount&dimensions=[{"Name":"Service","Value":"api"}]&minutes=5
```

## Frontend Integration

Add CloudWatch metrics display to your pod details:

```javascript
async function fetchCloudWatchMetrics(namespace, podName) {
    const response = await fetch(`/api/cloudwatch/pod/${namespace}/${podName}`);
    const data = await response.json();
    
    if (data.metrics) {
        displayCloudWatchMetrics(data.metrics);
    }
}

function displayCloudWatchMetrics(metrics) {
    const container = document.getElementById('cloudwatch-metrics');
    container.innerHTML = `
        <h4>CloudWatch Metrics</h4>
        <div>CPU: ${metrics.pod_cpu_utilization?.average.toFixed(2)}%</div>
        <div>Memory: ${metrics.pod_memory_utilization?.average.toFixed(2)}%</div>
        <div>Network RX: ${formatBytes(metrics.pod_network_rx_bytes?.average)}</div>
        <div>Network TX: ${formatBytes(metrics.pod_network_tx_bytes?.average)}</div>
    `;
}
```

## IAM Permissions Required

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}
```

## Testing

```bash
# Test pod metrics
curl http://localhost:5000/api/cloudwatch/pod/default/my-pod

# Test node metrics
curl http://localhost:5000/api/cloudwatch/node/ip-10-0-1-100.ec2.internal

# Test cluster metrics
curl http://localhost:5000/api/cloudwatch/cluster/my-eks-cluster
```
