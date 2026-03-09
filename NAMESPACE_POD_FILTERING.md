# Namespace and Pod Filtering for API Request Metrics

## Feature: Filtered Metrics Display

### How It Works:

**1. Select Namespace Only (e.g., dsdp):**
- Shows aggregated metrics from **all pods** in that namespace
- Example: 3 pods × 100 requests = 300 total

**2. Select Namespace + Specific Pod:**
- Shows metrics from **that pod only**
- Example: 1 pod = 100 requests

## Testing:

### All Pods in Namespace:
```bash
curl "http://localhost:8888/api/request-metrics/dsdp"
```
**Result:**
```json
{
  "submit": 300,
  "delivered": 300,
  "failure": 0,
  "success_rate": 100.0
}
```
*(3 pods × 100 lines = 300 total)*

### Single Pod:
```bash
curl "http://localhost:8888/api/request-metrics/dsdp?pod=java-api-app-744cbf5944-gmx96"
```
**Result:**
```json
{
  "submit": 100,
  "delivered": 100,
  "failure": 0,
  "success_rate": 100.0
}
```
*(1 pod × 100 lines = 100 total)*

## Dashboard Usage:

### Scenario 1: View All Pods in Namespace
1. Go to **Metrics** tab
2. Select namespace: **dsdp**
3. Leave pod selector as: **All Pods**
4. API Request Metrics shows: **Combined data from all 3 pods**

### Scenario 2: View Specific Pod
1. Go to **Metrics** tab
2. Select namespace: **dsdp**
3. Select pod: **java-api-app-744cbf5944-gmx96**
4. API Request Metrics shows: **Data from that pod only**

## Verification:

**Check all pods:**
```bash
# Count from all pods
kubectl logs -n dsdp -l app=java-api --tail=100 | grep "GET / HTTP" | wc -l
# Should match dashboard when "All Pods" selected
```

**Check single pod:**
```bash
# Count from specific pod
kubectl logs -n dsdp java-api-app-744cbf5944-gmx96 --tail=100 | grep "GET / HTTP" | wc -l
# Should match dashboard when that pod is selected
```

## Examples:

### Example 1: Namespace Filter
- **Namespace:** dsdp
- **Pod:** All Pods
- **Result:** Submit: 300, Delivered: 300, Failure: 0
- **Source:** All 3 java-api pods (100 lines each)

### Example 2: Pod Filter
- **Namespace:** dsdp
- **Pod:** java-api-app-744cbf5944-gmx96
- **Result:** Submit: 100, Delivered: 100, Failure: 0
- **Source:** Single pod (100 lines)

### Example 3: Different Namespace
- **Namespace:** kube-system
- **Pod:** Any
- **Result:** Simulated data (no java-api pods)
- **Source:** Generated metrics

## Key Points:

✅ **Namespace Filter:**
- Only shows data from selected namespace
- Aggregates all pods in that namespace

✅ **Pod Filter:**
- Only shows data from selected pod
- Requires namespace to be selected first

✅ **Real Data:**
- dsdp namespace shows real log data
- Other namespaces show simulated data

✅ **Auto-Refresh:**
- Updates every 30 seconds
- Maintains selected filters

## Validation Commands:

**All pods in dsdp:**
```bash
kubectl get pods -n dsdp -l app=java-api
kubectl logs -n dsdp -l app=java-api --tail=100 | grep "GET / HTTP" | wc -l
```

**Single pod:**
```bash
POD=java-api-app-744cbf5944-gmx96
kubectl logs -n dsdp $POD --tail=100 | grep "GET / HTTP" | wc -l
```

**Compare with API:**
```bash
# All pods
curl "http://localhost:8888/api/request-metrics/dsdp"

# Single pod
curl "http://localhost:8888/api/request-metrics/dsdp?pod=$POD"
```

All counts should match! ✅
