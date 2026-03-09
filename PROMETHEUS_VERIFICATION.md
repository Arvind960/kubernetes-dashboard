# How to Verify Prometheus Integration

## Visual Indicators in Dashboard

### 1. Prometheus Status Badge

**Location:** Top right of Metrics tab, next to Refresh button

**What to look for:**
```
✅ Connected:  [🟢 Prometheus] Refresh
❌ Not Connected: Only [Refresh] button visible
```

If you see the green **Prometheus** badge, integration is working!

---

## Step-by-Step Verification

### Step 1: Check Dashboard Logs

```bash
tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log
```

**Look for:**
```
✅ Prometheus connected at http://localhost:9090
```

**If you see:**
```
⚠️  Prometheus not connected. Metrics will use simulated data.
```
Then Prometheus is not running or port-forward is not active.

---

### Step 2: Check Prometheus API Status

```bash
curl http://localhost:8888/api/prometheus/status
```

**Expected output (Connected):**
```json
{
  "available": true,
  "connected": true,
  "url": "http://localhost:9090"
}
```

**Output (Not Connected):**
```json
{
  "available": true,
  "connected": false,
  "url": "http://localhost:9090"
}
```

---

### Step 3: Check Browser Console

1. Open dashboard: http://localhost:8888
2. Go to **Metrics** tab
3. Press **F12** (Developer Tools)
4. Go to **Console** tab

**Look for:**
```
✅ Using Prometheus metrics
```

**If you see:**
```
⚠️ Prometheus not available, using simulated metrics
```
Then Prometheus is not connected.

---

### Step 4: Visual Differences in Metrics

#### With Prometheus (Real Data):
- CPU values change realistically (not smooth curves)
- Memory shows actual usage patterns
- Network traffic reflects real pod activity
- Values may have spikes and drops

#### Without Prometheus (Simulated):
- Smooth, predictable curves
- Random values between fixed ranges
- No real correlation to pod activity

---

## Quick Test Commands

### Test 1: Check Prometheus Port-Forward
```bash
ps aux | grep "port-forward.*9090"
```
**Should show:** `kubectl port-forward -n monitoring svc/prometheus...`

### Test 2: Check Prometheus Health
```bash
curl http://localhost:9090/-/healthy
```
**Should return:** `Prometheus is Healthy.`

### Test 3: Test Prometheus Query
```bash
curl "http://localhost:9090/api/v1/query?query=up"
```
**Should return:** JSON with metrics data

### Test 4: Check Dashboard Metrics API
```bash
curl "http://localhost:8888/api/prometheus/metrics?namespace=test-application"
```
**Should return:** JSON with cpu, memory, network_rx, network_tx data

---

## Troubleshooting Checklist

### ❌ No Prometheus Badge Visible

**Fix:**
```bash
# Start port-forward
cd /root/kubernetes-dashboard
./start_prometheus_forward.sh
```

### ❌ Badge Shows but No Real Data

**Check:**
```bash
# Verify pods are being scraped
kubectl get servicemonitors -n monitoring
kubectl get pods -n test-application
```

### ❌ "Prometheus not available" in Console

**Fix:**
```bash
# Restart dashboard
cd /root/kubernetes-dashboard
./stop_dashboard.sh
./start_dashboard.sh
```

---

## Expected Behavior After Integration

### ✅ When Prometheus is Connected:

1. **Dashboard startup log:**
   ```
   ✅ Prometheus connected at http://localhost:9090
   ```

2. **Metrics tab shows:**
   - Green Prometheus badge (top right)
   - Real CPU/Memory/Network values
   - Data matches actual pod activity

3. **Browser console shows:**
   ```
   ✅ Using Prometheus metrics
   ```

4. **API returns real data:**
   ```bash
   curl http://localhost:8888/api/prometheus/metrics?namespace=test-application
   # Returns actual metrics from Prometheus
   ```

### ⚠️ When Prometheus is NOT Connected:

1. **Dashboard startup log:**
   ```
   ⚠️  Prometheus not connected. Metrics will use simulated data.
   ```

2. **Metrics tab shows:**
   - No Prometheus badge
   - Simulated metrics (smooth curves)

3. **Browser console shows:**
   ```
   ⚠️ Prometheus not available, using simulated metrics
   ```

---

## Quick Verification Script

Save this as `check_prometheus.sh`:

```bash
#!/bin/bash
echo "=== Prometheus Integration Check ==="
echo ""

echo "1. Checking port-forward..."
if ps aux | grep -q "[p]ort-forward.*9090"; then
    echo "   ✅ Port-forward is running"
else
    echo "   ❌ Port-forward is NOT running"
    echo "   Run: ./start_prometheus_forward.sh"
fi
echo ""

echo "2. Checking Prometheus health..."
if curl -s http://localhost:9090/-/healthy | grep -q "Healthy"; then
    echo "   ✅ Prometheus is healthy"
else
    echo "   ❌ Prometheus is not accessible"
fi
echo ""

echo "3. Checking dashboard API..."
STATUS=$(curl -s http://localhost:8888/api/prometheus/status | grep -o '"connected":[^,]*')
if echo "$STATUS" | grep -q "true"; then
    echo "   ✅ Dashboard connected to Prometheus"
else
    echo "   ❌ Dashboard NOT connected to Prometheus"
fi
echo ""

echo "4. Testing metrics fetch..."
if curl -s "http://localhost:8888/api/prometheus/metrics?namespace=test-application" | grep -q "cpu"; then
    echo "   ✅ Metrics are being fetched"
else
    echo "   ❌ No metrics data"
fi
echo ""
```

Run it:
```bash
chmod +x check_prometheus.sh
./check_prometheus.sh
```

---

## Summary

**3 Quick Checks:**

1. **Visual:** Green Prometheus badge in dashboard ✅
2. **Console:** "Using Prometheus metrics" message ✅
3. **Command:** `curl http://localhost:8888/api/prometheus/status` shows `"connected": true` ✅

If all 3 pass, Prometheus integration is working perfectly! 🚀
