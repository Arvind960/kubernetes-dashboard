# Query Logic Quick Reference

## The Problem
Route: `/api/request-metrics/<namespace>` forces a namespace parameter.
When "All Namespaces" selected → passes "default" → only shows default namespace data.

## The Fix
Change route to: `/api/request-metrics` (no path parameter)
Use query parameter: `?namespace=all`

## Query Logic

```python
namespace = request.args.get('namespace', 'all')

if not namespace or namespace == 'all':
    # NO FILTER - Get all pods from all namespaces
    pods = get_all_cluster_pods()
else:
    # FILTER - Get pods from specific namespace
    pods = get_namespace_pods(namespace)
```

## PromQL Patterns

### Cluster-Wide (All Namespaces)
```promql
sum(rate(http_requests_total[5m]))                    # Total
sum(rate(http_requests_total{status=~"2.."}[5m]))     # Success
sum(rate(http_requests_total{status=~"[45].."}[5m]))  # Failures
```

### Namespace-Level
```promql
sum(rate(http_requests_total{namespace="prod"}[5m]))
sum(rate(http_requests_total{namespace="prod",status=~"2.."}[5m]))
sum(rate(http_requests_total{namespace="prod",status=~"[45].."}[5m]))
```

### Pod-Level
```promql
sum(rate(http_requests_total{namespace="prod",pod="app-1"}[5m]))
sum(rate(http_requests_total{namespace="prod",pod="app-1",status=~"2.."}[5m]))
sum(rate(http_requests_total{namespace="prod",pod="app-1",status=~"[45].."}[5m]))
```

## Metric Labels (Instrumentation)

```python
from prometheus_client import Counter

requests = Counter('http_requests_total', 'HTTP requests', 
                   ['namespace', 'pod', 'status', 'method', 'endpoint'])

# In your app
requests.labels(
    namespace=os.getenv('POD_NAMESPACE'),
    pod=os.getenv('POD_NAME'),
    status='200',
    method='GET',
    endpoint='/api/data'
).inc()
```

## Frontend API Calls

```javascript
// All namespaces
fetch('/api/request-metrics?namespace=all')

// Specific namespace
fetch('/api/request-metrics?namespace=production')

// Specific pod
fetch('/api/request-metrics?namespace=production&pod=app-xyz')
```

## Failure Drill-Down

```promql
# Failures by namespace
sum(rate(http_requests_total{status=~"[45].."}[5m])) by (namespace)

# Failures by pod
sum(rate(http_requests_total{status=~"[45].."}[5m])) by (namespace, pod)

# Top 10 failing pods
topk(10, sum(rate(http_requests_total{status=~"[45].."}[5m])) by (pod))
```

## Key Takeaways

1. **No namespace filter** = cluster-wide aggregation
2. **namespace="X"** = namespace-level aggregation  
3. **namespace="X",pod="Y"** = pod-level aggregation
4. Use query parameters, not path parameters
5. Check for `namespace == 'all'` or empty/null
6. Always include namespace and pod labels in metrics
