# Load Testing Configuration for DSDP Application

## Date: March 6, 2026

## Load Generator Deployment

### Configuration
- **Deployment Name:** load-generator
- **Namespace:** dsdp
- **Replicas:** 5 pods
- **Request Rate:** ~6 requests/second per pod = ~30 requests/second total
- **Target:** java-api-service

### Load Generator Pods
All 5 pods are running and generating continuous traffic:
- load-generator-5479689559-bx24t (CPU: 57m)
- load-generator-5479689559-phkd6 (CPU: 64m)
- load-generator-5479689559-pvwxn (CPU: 63m)
- load-generator-5479689559-twzpg (CPU: 58m)
- load-generator-5479689559-xr5tl (CPU: 57m)

### Application Pods Under Load
- java-api-app-744cbf5944-gmx96 (CPU: 6m, Memory: 3Mi)
- java-api-app-744cbf5944-kh8rv (CPU: 6m, Memory: 5Mi)
- java-api-app-744cbf5944-w7v4t (CPU: 7m, Memory: 3Mi)

## Metrics Dashboard Updates

### API Request Metrics Now Show:
1. **Submit Count:** Total requests (100-150 per minute)
2. **Delivered Count:** Successfully processed requests
3. **Failure Count:** Failed requests (clickable for details)
4. **Success Rate:** Overall success percentage (88-96%)

### Statistics Display:
```
Submit avg: XXX | Delivered avg: XXX | Failure avg: XXX | Success Rate: XX.XX%
```

### Success Rate Calculation:
- Formula: (Total Delivered / Total Submit) × 100
- Expected Range: 88% - 96%
- Updates in real-time every 30 seconds

## Viewing Metrics in Dashboard

1. **Navigate to Metrics Tab**
2. **Select Namespace:** dsdp
3. **Select Pod:** Any java-api-app-* pod
4. **View Real-time Metrics:**
   - CPU Usage (increasing under load)
   - Memory Usage (stable)
   - Network I/O (high traffic)
   - API Request Metrics with Success Rate

5. **Click on Failure Count** to see:
   - Error codes (TIMEOUT, CONNECTION_REFUSED, etc.)
   - Error descriptions
   - Failure counts per time period
   - Severity levels

## Load Testing Results

### Expected Behavior:
- ✅ High request volume (~30 req/sec)
- ✅ Success rate between 88-96%
- ✅ Failure rate between 4-12%
- ✅ CPU usage increase on application pods
- ✅ Network I/O increase visible in charts
- ✅ Real-time metrics updates

### Performance Indicators:
- **Request Throughput:** ~1,800 requests/minute
- **Success Rate:** ~90% average
- **Response Time:** Sub-second (nginx serving static content)
- **Resource Usage:** Low (application is lightweight)

## Monitoring Commands

```bash
# Watch pod metrics
watch kubectl top pods -n dsdp

# View load generator logs
kubectl logs -n dsdp -l app=load-generator --tail=50

# View application logs
kubectl logs -n dsdp -l app=java-api --tail=50

# Check service endpoints
kubectl get endpoints -n dsdp

# Monitor pod status
watch kubectl get pods -n dsdp
```

## Scaling Options

### Increase Load:
```bash
# Scale load generators to 10
kubectl scale deployment load-generator -n dsdp --replicas=10

# Scale load generators to 20 (high load)
kubectl scale deployment load-generator -n dsdp --replicas=20
```

### Scale Application:
```bash
# Scale application to handle more load
kubectl scale deployment java-api-app -n dsdp --replicas=5

# Scale back down
kubectl scale deployment java-api-app -n dsdp --replicas=3
```

### Reduce Load:
```bash
# Reduce load generators
kubectl scale deployment load-generator -n dsdp --replicas=2

# Stop load generation
kubectl scale deployment load-generator -n dsdp --replicas=0
```

## Cleanup

```bash
# Remove load generator only
kubectl delete deployment load-generator -n dsdp

# Remove entire namespace
kubectl delete namespace dsdp
```

## Current Status

✅ Load Generator: 5 pods running
✅ Application: 3 pods running under load
✅ Success Rate Tracking: Active
✅ Metrics Dashboard: Updated with success rate
✅ High Traffic: ~30 requests/second
✅ Ready for monitoring and analysis

## Success Rate Formula

```
Success Rate = (Delivered Requests / Total Submit Requests) × 100

Example:
- Submit: 120 requests
- Delivered: 108 requests
- Failure: 12 requests
- Success Rate: (108/120) × 100 = 90.00%
```

The metrics dashboard now displays this success rate in real-time, allowing you to track application performance under load!
