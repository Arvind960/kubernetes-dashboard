# Multi-Pod Metrics Fix

## Problem
When selecting multiple pods in the dsdp namespace (or any namespace), the metrics showed the same data whether you selected 1 pod or multiple pods. This was because:

1. **Identical Replicas**: The 3 pods in dsdp namespace are replicas of the same deployment with nearly identical resource usage
2. **Averaging**: The frontend was averaging metrics across all selected pods, making individual pod differences invisible

## Solution
Changed the metrics display to show **individual pod lines** instead of averaged data.

### Changes Made

#### 1. Frontend (`static/js/metrics.js`)

**convertPrometheusToChart()**: Now returns array of series (one per pod) instead of averaging:
```javascript
// Before: Averaged all pods into single line
// After: Returns [{pod: 'pod1', data: [...]}, {pod: 'pod2', data: [...]}]
```

**updateCharts()**: Now handles both single and multi-series data:
- Single pod: Shows one line (original behavior)
- Multiple pods: Shows separate colored line for each pod
- Each pod gets a unique color from palette

#### 2. Backend (`prometheus_client.py`)

Added `separate_pods` parameter to `get_metrics_range()`:
- Returns raw Prometheus data with pod labels intact
- Frontend extracts pod name from `series.metric.pod`
- Each pod's time series is kept separate

#### 3. Backend (`k8s_dashboard_server_updated.py`)

Updated `/api/prometheus/metrics` endpoint:
- Passes `separate_pods=True` to Prometheus client
- Returns per-pod data structure

## Result

### Before:
- Select 1 pod: Shows one line
- Select 2 pods: Shows one averaged line (looks identical)
- Select 3 pods: Shows one averaged line (looks identical)

### After:
- Select 1 pod: Shows one line (same as before)
- Select 2 pods: Shows TWO separate colored lines
- Select 3 pods: Shows THREE separate colored lines

## Testing

1. Open dashboard: http://localhost:8888/full-dashboard
2. Go to Metrics tab
3. Select namespace: `dsdp`
4. Select multiple pods using checkboxes
5. Observe: Each pod now has its own colored line in the charts

## Color Palette

Pods are assigned colors in order:
1. Green (#3dba8c)
2. Blue (#326ce5)
3. Red (#ff6b6b)
4. Orange (#ffa500)
5. Purple (#9b59b6)
6. Teal (#1abc9c)

## Network Chart

- Solid lines: RX (receive)
- Dashed lines: TX (transmit)
- Each pod has both RX and TX lines in its assigned color

## Notes

- If pods have identical workloads, lines will overlap (this is expected)
- To see differences, create load on specific pods
- Works with both Prometheus metrics and simulated data
- Backward compatible: single pod selection works as before
