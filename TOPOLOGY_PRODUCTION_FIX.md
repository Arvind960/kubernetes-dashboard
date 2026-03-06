# Topology Production Optimization

## Changes Made (March 6, 2026)

### Issue
- Topology was filtering data (missing some resources in production)
- Initial load was slow for large clusters
- No background cache refresh

### Solution

#### 1. Removed Data Filtering
- **Before**: Filtered out succeeded pods and limited namespaces
- **After**: Fetches ALL pods, services, deployments, replicasets, namespaces, ingresses, and nodes
- Ensures complete topology visibility in production

#### 2. Increased Cache TTL
- **Before**: 5 seconds cache
- **After**: 30 seconds cache
- Reduces API load while keeping data reasonably fresh

#### 3. Background Cache Warmer
- Automatically refreshes cache every 25 seconds (before 30s TTL expires)
- Ensures first user request always hits warm cache
- Runs as background async task

#### 4. Loading State
- Shows "⏳ Loading topology data..." while fetching
- Better user feedback for large clusters
- Error handling with clear messages

### Performance Benefits

**For Production Clusters:**
- First load: Full data fetch (may take 5-10s for large clusters)
- Subsequent loads: Instant (uses 30s cache)
- Background refresh: Keeps cache warm without user waiting
- Click on pods: Instant (uses cached graph data)

### Configuration

```python
# In topology_backend.py
self._cache_ttl = 30  # Adjust based on cluster size
# Background refresh at 25s (5s before expiry)
```

### Monitoring

Check logs for:
- "Building fresh topology data" - Fresh fetch
- "Returning cached topology data" - Cache hit
- "Background cache refresh" - Auto refresh

### Recommendations

For very large clusters (1000+ pods):
- Increase cache TTL to 60 seconds
- Adjust background refresh to 55 seconds
- Consider namespace filtering if needed
