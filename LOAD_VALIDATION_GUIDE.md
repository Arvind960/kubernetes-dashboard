# Load Traffic Validation Guide

## How to Validate Load Traffic vs API Request Metrics

### Method 1: Using Validation Script

Run the automated validation script:
```bash
/root/kubernetes-dashboard/validate-load.sh
```

**Output shows:**
- Actual request count from logs (last 60 seconds)
- Success/Error breakdown
- Requests per pod
- Load generator status
- Real-time monitoring (10-second sample)

### Method 2: Manual Log Analysis

**Count total requests:**
```bash
kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | wc -l
```

**Count successful requests (200 status):**
```bash
kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | grep " 200 " | wc -l
```

**Count errors:**
```bash
kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | grep -v " 200 " | wc -l
```

**Real-time monitoring:**
```bash
kubectl logs -n dsdp -l app=java-api -f | grep "GET / HTTP"
```

### Method 3: API Endpoint

**Fetch real metrics via API:**
```bash
curl http://localhost:8888/api/request-metrics/dsdp
```

**Response format:**
```json
{
  "submit": 1234,
  "delivered": 1234,
  "failure": 0,
  "success_rate": 100.0
}
```

### Method 4: Dashboard Integration

**View in Metrics Dashboard:**
1. Navigate to **Metrics** tab
2. Select namespace: **dsdp**
3. The API Request Metrics chart now shows:
   - **Real counts** from actual pod logs (last 100 lines per pod)
   - **Live success rate** calculated from actual requests
   - **Automatic refresh** every 30 seconds

### Validation Comparison

#### Expected vs Actual:

**Load Generators:**
- 15 pods × 6 req/sec = **~90 requests/second**
- Per minute: **~5,400 requests**

**Actual Measurement (from logs):**
```bash
# Run this to get 1-minute count
kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | wc -l
```

**Dashboard Display:**
- Shows last 100 log lines per pod (3 pods = 300 total)
- Updates every 30 seconds
- Displays real success rate from actual HTTP status codes

### Verification Steps

**1. Check Load Generator Activity:**
```bash
kubectl get pods -n dsdp -l app=load-generator
# Should show 15 running pods
```

**2. Verify Application Receiving Traffic:**
```bash
kubectl logs -n dsdp -l app=java-api --tail=20
# Should show continuous GET requests
```

**3. Compare Counts:**
```bash
# Get actual count
ACTUAL=$(kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | wc -l)
echo "Actual requests in last 60s: $ACTUAL"
echo "Expected rate: ~90 req/sec = ~5400 req/min"
```

**4. Check Dashboard Metrics:**
- Open dashboard → Metrics tab
- Select namespace: dsdp
- Verify API Request Metrics shows similar counts

### Understanding the Numbers

**Why counts might differ:**

1. **Time Window:**
   - Logs: Last 60 seconds
   - Dashboard: Last 100 lines per pod (time varies)
   
2. **Log Rotation:**
   - Kubernetes rotates logs
   - Only recent entries available
   
3. **Sampling:**
   - Dashboard samples every 30 seconds
   - Logs show all requests

**Both should show:**
- ✅ High request volume (thousands per minute)
- ✅ Success rate ~100% (all 200 status codes)
- ✅ Consistent traffic pattern
- ✅ Load distributed across 3 pods

### Real-time Comparison Test

Run this to compare in real-time:
```bash
echo "Starting 30-second comparison test..."
echo ""

# Count before
START=$(kubectl logs -n dsdp -l app=java-api --tail=5000 | grep "GET / HTTP" | wc -l)
echo "Starting count: $START"

# Wait 30 seconds
echo "Waiting 30 seconds..."
sleep 30

# Count after
END=$(kubectl logs -n dsdp -l app=java-api --tail=5000 | grep "GET / HTTP" | wc -l)
echo "Ending count: $END"

# Calculate
DIFF=$((END - START))
RATE=$((DIFF * 2))
echo ""
echo "Requests in 30 seconds: $DIFF"
echo "Estimated rate: $RATE requests/minute"
echo "Expected rate: ~5400 requests/minute"
echo ""

# Check dashboard
echo "Now check the dashboard Metrics tab (namespace: dsdp)"
echo "The API Request Metrics should show similar numbers"
```

### Success Rate Validation

**From Logs:**
```bash
TOTAL=$(kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | wc -l)
SUCCESS=$(kubectl logs -n dsdp -l app=java-api --since=60s | grep "GET / HTTP" | grep " 200 " | wc -l)
RATE=$(echo "scale=2; ($SUCCESS * 100) / $TOTAL" | bc)
echo "Success Rate: ${RATE}%"
```

**From Dashboard:**
- Shows in API Request Metrics stats
- Format: "Success Rate: XX.XX%"
- Should match log calculation

### Troubleshooting

**If counts don't match:**

1. **Check time windows are aligned**
2. **Verify load generators are running:**
   ```bash
   kubectl get pods -n dsdp -l app=load-generator
   ```
3. **Check application pods are healthy:**
   ```bash
   kubectl get pods -n dsdp -l app=java-api
   ```
4. **Verify logs are accessible:**
   ```bash
   kubectl logs -n dsdp -l app=java-api --tail=10
   ```

### Continuous Monitoring

**Terminal 1 - Real-time logs:**
```bash
kubectl logs -n dsdp -l app=java-api -f | grep "GET / HTTP"
```

**Terminal 2 - Count every 10 seconds:**
```bash
watch -n 10 'kubectl logs -n dsdp -l app=java-api --since=10s | grep "GET / HTTP" | wc -l'
```

**Browser - Dashboard:**
- Keep Metrics tab open with namespace: dsdp
- Watch API Request Metrics update every 30 seconds

All three should show consistent high traffic! ✅
