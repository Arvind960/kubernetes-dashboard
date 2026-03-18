# How to Know When Prometheus is Down

## Visual Indicators in Dashboard

### 1. Status Badge (Top Right)

**Prometheus Running:**
```
[🟢 Prometheus] Refresh
```
- Green circle
- Green text "Prometheus"
- Green border

**Prometheus Down:**
```
[🔴 Prometheus Down] Refresh
```
- Red circle
- Red text "Prometheus Down"
- Red border

**Prometheus Not Available:**
```
[⚪ Prometheus N/A] Refresh
```
- Gray circle
- Gray text "Prometheus N/A"
- Gray border

---

### 2. Alert Banner (Top of Metrics Tab)

**When Prometheus is down, you'll see:**
```
⚠️ Prometheus is not connected. Showing simulated metrics. 
   Run: ./start_prometheus_forward.sh
```
- Red/orange background
- Warning icon
- Instructions to fix

**When Prometheus is running:**
- No alert banner visible

---

### 3. Browser Console Messages

Press **F12** → **Console** tab

**Prometheus Working:**
```
✅ Using Prometheus metrics
```

**Prometheus Down:**
```
⚠️ Prometheus not connected
⚠️ Prometheus not available, using simulated metrics
```

---

## Command Line Checks

### Quick Check:
```bash
cd /root/kubernetes-dashboard
./check_prometheus.sh
```

**Output when DOWN:**
```
1. Checking port-forward...
   ❌ Port-forward is NOT running

2. Checking Prometheus health...
   ❌ Prometheus is not accessible

3. Checking dashboard API...
   ❌ Dashboard NOT connected to Prometheus
```

---

### Manual Checks:

#### 1. Check Port-Forward
```bash
ps aux | grep "port-forward.*9090"
```
**If empty:** Port-forward is not running

#### 2. Check Prometheus Health
```bash
curl http://localhost:9090/-/healthy
```
**If fails:** Prometheus is not accessible

#### 3. Check Dashboard API
```bash
curl http://localhost:8888/api/prometheus/status
```
**Output when down:**
```json
{
  "available": true,
  "connected": false,
  "url": "http://localhost:9090"
}
```

#### 4. Check Prometheus Pods
```bash
kubectl get pods -n monitoring | grep prometheus
```
**Look for:** Status should be "Running"

---

## Automatic Detection

The dashboard checks Prometheus status:
- **On page load**
- **Every 30 seconds** (auto-refresh)
- **When you click Refresh**

You don't need to manually check - the UI will show you!

---

## What Happens When Prometheus Goes Down

### Immediate Effects:

1. **Badge changes** from green to red
2. **Alert banner appears** at top
3. **Metrics switch** to simulated data
4. **Console shows** warning messages

### Dashboard Behavior:

- ✅ Dashboard continues to work
- ✅ Shows simulated metrics (fallback)
- ✅ No errors or crashes
- ✅ Auto-reconnects when Prometheus comes back

---

## How to Fix When Down

### Option 1: Restart Port-Forward
```bash
cd /root/kubernetes-dashboard
./start_prometheus_forward.sh
```

### Option 2: Manual Port-Forward
```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090 &
```

### Option 3: Check Prometheus Pods
```bash
# Check if pods are running
kubectl get pods -n monitoring

# If not running, restart
kubectl rollout restart statefulset/prometheus-prometheus-kube-prometheus-prometheus -n monitoring
```

### Option 4: Full Reinstall
```bash
cd /root/kubernetes-dashboard
./setup_prometheus_complete.sh
```

---

## Testing Prometheus Down Scenario

### Simulate Prometheus Down:
```bash
# Kill port-forward
pkill -f "port-forward.*9090"

# Refresh dashboard Metrics tab
# You should see:
# - Red badge "Prometheus Down"
# - Alert banner appears
# - Simulated metrics shown
```

### Restore Prometheus:
```bash
# Start port-forward
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090 &

# Refresh dashboard Metrics tab
# You should see:
# - Green badge "Prometheus"
# - Alert banner disappears
# - Real metrics shown
```

---

## Summary: 3 Ways to Know Prometheus is Down

1. **Visual Badge:** Red circle + "Prometheus Down" text
2. **Alert Banner:** Warning message at top of Metrics tab
3. **Command:** `./check_prometheus.sh` shows ❌

The dashboard makes it **obvious** when Prometheus is down! 🚨
