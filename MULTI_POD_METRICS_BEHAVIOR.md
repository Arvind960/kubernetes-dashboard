# Multi-Pod Metrics Behavior

## How Metrics Are Calculated When Multiple Pods Are Selected

### Current Behavior: **AGGREGATED (AVERAGED)**

When you select 2 or more pods, the dashboard shows **AVERAGED** metrics across all selected pods.

---

## Example Scenario

### If you select 2 pods:
- **Pod 1:** CPU = 0.5 cores, Memory = 100 MB
- **Pod 2:** CPU = 0.3 cores, Memory = 150 MB

### What the dashboard shows:
- **CPU Usage:** 0.4 cores (average of 0.5 and 0.3)
- **Memory Usage:** 125 MB (average of 100 and 150)
- **Network RX:** Average of both pods
- **Network TX:** Average of both pods

---

## Technical Details

### With Prometheus (Real Data):

The `convertPrometheusToChart()` function:
1. Collects data from all selected pods
2. Groups by timestamp
3. **Averages** the values at each timestamp
4. Displays the averaged result

```javascript
// Line 305 in metrics.js
const avgValue = data.values.reduce((a, b) => a + b, 0) / data.values.length;
```

### Without Prometheus (Simulated Data):

The `calculateMetrics()` function:
1. Receives filtered pods array
2. Generates simulated data
3. Shows generic metrics (not pod-specific)

---

## What You See in Charts

### CPU Usage Chart
- **Single Pod:** Shows that pod's CPU usage
- **Multiple Pods:** Shows **AVERAGE** CPU across all selected pods
- **All Pods:** Shows **AVERAGE** CPU across all pods in namespace

### Memory Usage Chart
- **Single Pod:** Shows that pod's memory usage
- **Multiple Pods:** Shows **AVERAGE** memory across all selected pods
- **All Pods:** Shows **AVERAGE** memory across all pods in namespace

### Network I/O Chart
- **Single Pod:** Shows that pod's network traffic
- **Multiple Pods:** Shows **AVERAGE** network traffic across all selected pods
- **All Pods:** Shows **AVERAGE** network traffic across all pods in namespace

---

## Status Cards

### Pod Info Card
Shows: `X pod(s)` where X is the number of selected pods

### Uptime
Shows: Uptime of the **oldest** pod among selected pods

### Start Time
Shows: Start time of the **oldest** pod among selected pods

---

## Example Use Cases

### Use Case 1: Compare Individual Pods
**Action:** Select one pod at a time
**Result:** See individual pod metrics

### Use Case 2: Monitor Pod Group
**Action:** Select multiple pods (e.g., all replicas of a deployment)
**Result:** See average metrics across the group

### Use Case 3: Namespace Overview
**Action:** Don't select any pods
**Result:** See average metrics across all pods in namespace

---

## Important Notes

### ✅ Advantages of Averaging:
- Easy to see overall health of a deployment
- Smooth out individual pod spikes
- Good for monitoring replica sets

### ⚠️ Limitations:
- Cannot see individual pod spikes
- High usage in one pod may be hidden by low usage in others
- Not suitable for identifying specific problematic pods

---

## Alternative: Total vs Average

### Current: AVERAGE
```
Pod 1: 100 MB
Pod 2: 200 MB
Display: 150 MB (average)
```

### If it were TOTAL (not implemented):
```
Pod 1: 100 MB
Pod 2: 200 MB
Display: 300 MB (sum)
```

---

## How to See Individual Pod Metrics

### Option 1: Select One Pod at a Time
1. Click pod dropdown
2. Select only one pod
3. View its individual metrics

### Option 2: Use Prometheus UI Directly
1. Open: http://localhost:9090
2. Query specific pod:
   ```
   container_cpu_usage_seconds_total{pod="pod-name"}
   ```

### Option 3: Use kubectl
```bash
kubectl top pod <pod-name> -n <namespace>
```

---

## Summary

**When you select 2 pods:**
- ✅ Shows **AVERAGED** metrics of both pods
- ✅ Good for overall health monitoring
- ❌ Does NOT show individual pod spikes
- ❌ Does NOT show total/sum of both pods

**To see individual pod data:**
- Select only ONE pod at a time
- Or use Prometheus UI directly
- Or use kubectl top command
