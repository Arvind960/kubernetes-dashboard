# HPA Auto-Refresh Feature

## Overview
HPA section now automatically refreshes every 30 seconds to show real-time scaling status.

## Features

### 1. Manual Refresh ✅
- Click "Refresh" button anytime
- Immediately updates HPA data
- Works instantly

### 2. Auto-Refresh ✅
- Refreshes every 30 seconds automatically
- No user action required
- Shows real-time replica counts and CPU metrics

### 3. Smart Refresh ✅
- Only refreshes when HPA tab is visible
- Saves resources when viewing other tabs
- Efficient background updates

## How It Works

```javascript
// Auto-refresh every 30 seconds
setInterval(() => {
    if (hpaSection.style.display !== 'none') {
        loadHPA();
    }
}, 30000);
```

## Usage

1. Open: http://192.168.47.152:8888/full-dashboard
2. Click "HPA" in sidebar
3. Watch data update automatically every 30 seconds
4. Or click "Refresh" button for immediate update

## What Updates

- Current/Desired replicas
- CPU metrics (current vs target)
- Memory metrics (if configured)
- HPA age
- Scaling status

## Example

```
Before (0 seconds):
  backend-hpa: 2/2 replicas, CPU: 45%

After load (30 seconds):
  backend-hpa: 2/3 replicas, CPU: 85%

After scaling (60 seconds):
  backend-hpa: 3/3 replicas, CPU: 60%
```

## Benefits

- Real-time monitoring of HPA scaling
- No need to manually refresh
- See scaling decisions as they happen
- Monitor CPU/Memory trends over time

## Date Added
March 6, 2026
