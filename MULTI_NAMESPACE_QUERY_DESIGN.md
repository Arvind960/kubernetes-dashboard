# Multi-Namespace Query Design for API Request Metrics

## Problem
When "All Namespaces" is selected, metrics only show data from "default" namespace instead of cluster-wide aggregation.

## Solution Architecture

### 1. Query Logic Structure

```
Selection Level → Query Scope → Filter Logic
─────────────────────────────────────────────
All Namespaces  → Cluster-wide → No namespace filter
Namespace       → Namespace    → namespace="<name>"
Pod             → Pod-specific → namespace="<ns>",pod="<name>"
```

### 2. PromQL Query Patterns

#### A. Cluster-Wide Aggregation (All Namespaces)
```promql
# API Request Total (Submit)
sum(rate(http_requests_total[5m]))

# API Request Success (Delivered)
sum(rate(http_requests_total{status=~"2.."}[5m]))

# API Request Failures
sum(rate(http_requests_total{status=~"[45].."}[5m]))

# Alternative: Count by status code
sum by (status) (rate(http_requests_total[5m]))
```

#### B. Namespace-Level Aggregation
```promql
# API Request Total for specific namespace
sum(rate(http_requests_total{namespace="production"}[5m]))

# Success rate for namespace
sum(rate(http_requests_total{namespace="production",status=~"2.."}[5m]))

# Failures for namespace
sum(rate(http_requests_total{namespace="production",status=~"[45].."}[5m]))
```

#### C. Pod-Level Aggregation
```promql
# API Request Total for specific pod
sum(rate(http_requests_total{namespace="production",pod="app-xyz"}[5m]))

# Success for specific pod
sum(rate(http_requests_total{namespace="production",pod="app-xyz",status=~"2.."}[5m]))

# Failures for specific pod
sum(rate(http_requests_total{namespace="production",pod="app-xyz",status=~"[45].."}[5m]))
```

### 3. Dynamic Query Builder

```python
def build_api_request_query(metric_type, namespace=None, pod=None):
    """
    Build PromQL query based on selection
    
    metric_type: 'submit', 'delivered', 'failure'
    namespace: None (all), or specific namespace
    pod: None (all in namespace), or specific pod
    """
    
    # Base metric
    base = "http_requests_total"
    
    # Build label filters
    filters = []
    
    if namespace:
        filters.append(f'namespace="{namespace}"')
    
    if pod:
        filters.append(f'pod="{pod}"')
    
    # Add status filter based on metric type
    if metric_type == 'delivered':
        filters.append('status=~"2.."')
    elif metric_type == 'failure':
        filters.append('status=~"[45].."')
    
    # Construct query
    filter_str = ','.join(filters) if filters else ''
    query = f"sum(rate({base}{{{filter_str}}}[5m]))"
    
    return query
```

### 4. Log-Based Metrics (Current Implementation)

For log-based approach, the fix is simpler:

```python
@app.route('/api/request-metrics')
def get_request_metrics():
    """Get API request metrics with proper namespace handling"""
    namespace = request.args.get('namespace', 'all')
    pod_name = request.args.get('pod', None)
    time_range = request.args.get('time_range', '1h')
    
    # Convert time range
    time_map = {'5m': 300, '15m': 900, '1h': 3600, '6h': 21600}
    since_seconds = time_map.get(time_range, 3600)
    
    # Determine pod scope
    if namespace == 'all' or namespace == '' or namespace is None:
        # Cluster-wide: all pods from all namespaces
        namespaces_list = v1.list_namespace()
        pods = []
        for ns in namespaces_list.items:
            try:
                pod_list = v1.list_namespaced_pod(ns.metadata.name)
                pods.extend(pod_list.items)
            except:
                pass
    elif pod_name:
        # Specific pod
        pods = [v1.read_namespaced_pod(name=pod_name, namespace=namespace)]
    else:
        # All pods in namespace
        pod_list = v1.list_namespaced_pod(namespace)
        pods = pod_list.items
    
    # Aggregate metrics
    total_requests = 0
    success_count = 0
    error_count = 0
    
    for pod in pods:
        try:
            logs = v1.read_namespaced_pod_log(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                since_seconds=since_seconds
            )
            
            for line in logs.split('\n'):
                if ('GET /' in line or '"GET /' in line) and 'HTTP' in line:
                    total_requests += 1
                    if ' 200 ' in line or '" 200 ' in line:
                        success_count += 1
                    elif any(code in line for code in [' 404 ', ' 500 ', ' 503 ']):
                        error_count += 1
        except:
            pass
    
    success_rate = (success_count / total_requests * 100) if total_requests > 0 else 100
    
    return jsonify({
        'submit': total_requests,
        'delivered': success_count,
        'failure': error_count,
        'success_rate': round(success_rate, 2),
        'time_range': time_range,
        'scope': 'cluster' if namespace == 'all' else 'namespace' if not pod_name else 'pod'
    })
```

### 5. Frontend Query Parameters

```javascript
// Cluster-wide
fetch('/api/request-metrics?namespace=all&time_range=1h')

// Namespace-level
fetch('/api/request-metrics?namespace=production&time_range=1h')

// Pod-level
fetch('/api/request-metrics?namespace=production&pod=app-xyz&time_range=1h')
```

### 6. Prometheus Metric Labels (Best Practice)

When instrumenting your application, use these labels:

```python
from prometheus_client import Counter

api_requests = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['namespace', 'pod', 'method', 'endpoint', 'status']
)

# Increment
api_requests.labels(
    namespace=os.getenv('POD_NAMESPACE'),
    pod=os.getenv('POD_NAME'),
    method='GET',
    endpoint='/api/data',
    status='200'
).inc()
```

### 7. Query Optimization

```promql
# Efficient: Pre-aggregate at query time
sum(rate(http_requests_total[5m])) by (namespace)

# Efficient: Use recording rules for frequently queried metrics
# In prometheus.yml:
groups:
  - name: api_metrics
    interval: 30s
    rules:
      - record: api:requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (namespace, status)
      
      - record: api:requests:success_rate
        expr: |
          sum(rate(http_requests_total{status=~"2.."}[5m])) by (namespace)
          /
          sum(rate(http_requests_total[5m])) by (namespace)
```

### 8. Failure Drill-Down Query

When clicking "Failure" in "All Namespaces" view:

```promql
# Get failures grouped by namespace
sum(rate(http_requests_total{status=~"[45].."}[5m])) by (namespace)

# Get failures grouped by namespace and pod
sum(rate(http_requests_total{status=~"[45].."}[5m])) by (namespace, pod)

# Get top 10 pods with most failures
topk(10, sum(rate(http_requests_total{status=~"[45].."}[5m])) by (pod, namespace))
```

## Implementation Checklist

- [ ] Change route from `/api/request-metrics/<namespace>` to `/api/request-metrics`
- [ ] Use query parameter `?namespace=all` for cluster-wide
- [ ] Remove namespace filter when `namespace == 'all'`
- [ ] Add scope indicator in response
- [ ] Update frontend to pass `namespace=all` instead of `namespace=default`
- [ ] Add Prometheus queries for better performance
- [ ] Implement drill-down for failure analysis
- [ ] Add caching for cluster-wide queries (expensive operation)

## Testing

```bash
# Test cluster-wide
curl "http://localhost:8888/api/request-metrics?namespace=all&time_range=1h"

# Test namespace
curl "http://localhost:8888/api/request-metrics?namespace=default&time_range=1h"

# Test pod
curl "http://localhost:8888/api/request-metrics?namespace=default&pod=nginx-xyz&time_range=1h"
```
