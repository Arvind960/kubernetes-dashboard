# Quick Fix for Topology Showing Dots in Production

## Problem
Topology shows dots instead of network graph because production server can't access CDN (cdnjs.cloudflare.com).

## Solution

### On Your Development Machine (with internet):

```bash
cd /root/kubernetes-dashboard

# Download all required libraries locally
./prepare_offline_deployment.sh

# Create deployment package
tar -czf k8s-dashboard-offline.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/*.log' \
    .
```

### Transfer to Production Server:

```bash
# Copy to production
scp k8s-dashboard-offline.tar.gz user@production-server:/tmp/

# On production server
ssh user@production-server
cd /tmp
tar -xzf k8s-dashboard-offline.tar.gz -C kubernetes-dashboard
cd kubernetes-dashboard

# Setup and start
./setup_service.sh
```

## What Was Fixed

1. **topology.html** - Now loads vis-network library from local file first
2. **static/libs/** - Contains all required JavaScript/CSS libraries
3. **No CDN dependency** - Works without internet access

## Verify Fix

```bash
# Check library exists
ls -lh static/libs/vis-network.min.js

# Should show: -rw-r--r-- 1 root root 458K

# Test topology
curl http://localhost:8889/topology
# Should return HTML without errors
```

## Files Added

- `static/libs/vis-network.min.js` - Required for topology (458KB)
- `prepare_offline_deployment.sh` - Script to download all libraries
- `TOPOLOGY_CDN_FIX.md` - Detailed troubleshooting guide

## Quick Test

After deployment, open in browser:
- http://localhost:8888/topology

Should show full network graph, not just dots!
