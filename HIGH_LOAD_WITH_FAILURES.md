# High Load with Failures - Configuration

## Current Load Setup

### Load Generators:
- **Success Load:** 30 pods (generating valid requests)
- **Failure Load:** 3 pods (generating 404 errors)
- **Total:** 33 generator pods

### Request Rates:
- **Valid Requests:** ~180 req/sec (30 pods × 6 req/sec)
- **Error Requests:** ~4.5 req/sec (3 pods × 1.5 req/sec)
- **Total Traffic:** ~184 req/sec (~11,000 req/min)

## Current Metrics (Real Data):

```json
{
  "submit": 300,
  "delivered": 278,
  "failure": 11,
  "success_rate": 92.67
}
```

### Breakdown:
- **Total Requests:** 300 (last 100 lines × 3 pods)
- **Successful (200):** 278 requests
- **Failed (404):** 11 requests
- **Success Rate:** 92.67%

## Failure Types Generated:

The failure-generator creates 404 errors by requesting:
- `/invalid-endpoint` - Invalid API endpoint
- `/error` - Error endpoint
- `/fail` - Fail endpoint

## Verification:

**Check failures in logs:**
```bash
kubectl logs -n dsdp -l app=java-api --tail=100 | grep " 404 "
```

**Sample output:**
```
192.168.255.251 - - [06/Mar/2026:14:42:31 +0000] "GET /invalid-endpoint HTTP/1.1" 404 153 "-" "Wget" "-"
192.168.255.252 - - [06/Mar/2026:14:42:31 +0000] "GET /fail HTTP/1.1" 404 153 "-" "Wget" "-"
192.168.255.251 - - [06/Mar/2026:14:42:31 +0000] "GET /error HTTP/1.1" 404 153 "-" "Wget" "-"
```

## Dashboard Display:

Navigate to **Metrics** tab → Select namespace: **dsdp**

**You will see:**
- **Submit:** 300 (total requests)
- **Delivered:** 278 (successful)
- **Failure:** 11 (errors) - **CLICKABLE**
- **Success Rate:** 92.67%

**Click on Failure count (11)** to see:
- Error codes (404)
- Error descriptions
- Timestamps
- Severity levels

## Scaling Options:

**Increase failures:**
```bash
kubectl scale deployment failure-generator -n dsdp --replicas=10
# More 404 errors, lower success rate
```

**Decrease failures:**
```bash
kubectl scale deployment failure-generator -n dsdp --replicas=1
# Fewer errors, higher success rate
```

**Increase overall load:**
```bash
kubectl scale deployment load-generator -n dsdp --replicas=50
# More total traffic
```

**Stop failures:**
```bash
kubectl scale deployment failure-generator -n dsdp --replicas=0
# 100% success rate
```

## Current Pod Status:

```bash
kubectl get pods -n dsdp
```

**Expected:**
- 3 java-api-app pods (application)
- 30 load-generator pods (success traffic)
- 3 failure-generator pods (error traffic)

## Real-time Monitoring:

**Watch failures:**
```bash
kubectl logs -n dsdp -l app=java-api -f | grep " 404 "
```

**Count failures per minute:**
```bash
watch -n 60 'kubectl logs -n dsdp -l app=java-api --since=60s | grep " 404 " | wc -l'
```

**Monitor success rate:**
```bash
watch -n 10 'curl -s http://localhost:8888/api/request-metrics/dsdp'
```

## Expected Behavior:

✅ **High Traffic:** ~11,000 requests/minute
✅ **Failures Present:** 5-15% failure rate
✅ **Success Rate:** 85-95%
✅ **Dashboard Updates:** Every 30 seconds
✅ **Clickable Failures:** Shows error details
✅ **Real Data:** All metrics from actual logs

## Cleanup:

**Remove failure generators:**
```bash
kubectl delete deployment failure-generator -n dsdp
```

**Reduce load:**
```bash
kubectl scale deployment load-generator -n dsdp --replicas=5
```

**Remove all:**
```bash
kubectl delete namespace dsdp
```

The system is now under high load with observable failures! 🔥
