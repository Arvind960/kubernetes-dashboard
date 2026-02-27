# Problematic Pods for Topology Testing

## Created Resources

### 1. **problematic-app** (CrashLoopBackOff)
- **Issue**: Containers exit with error code 1 after 5 seconds
- **Replicas**: 3 pods
- **Status**: CrashLoopBackOff with increasing restart counts
- **Topology Shows**: 
  - 🔄 Restart counts on pods
  - Red edges to failing pods
  - ⚠️ DOWN indicator
  - Service with 0 endpoints

### 2. **image-pull-error** (ImagePullBackOff)
- **Issue**: Tries to pull non-existent image
- **Replicas**: 2 pods
- **Status**: ImagePullBackOff / ErrImagePull
- **Topology Shows**:
  - ⏳ QUEUED status (containers waiting)
  - Orange edges indicating queue
  - Service with 0 endpoints
  - Deployment with 0/2 ready

### 3. **oom-killer** (Memory Issues)
- **Issue**: Consumes more memory than limit
- **Replicas**: 1 pod
- **Status**: May get OOMKilled or run with stress
- **Topology Shows**:
  - Potential restart counts if OOM occurs
  - Resource pressure indicators

## Services Created
- **problematic-service**: Routes to problematic-app (0 endpoints)
- **image-error-service**: Routes to image-pull-error (0 endpoints)

## View in Topology Map

Access: http://localhost:8888/topology

**What You'll See:**
1. **Red dashed borders** on failed/down pods
2. **🔄 Restart counts** on crashing pods
3. **⏳ QUEUED** labels on ImagePullBackOff pods
4. **Orange/Red edges** showing problematic connections
5. **[0 endpoints]** on services with no healthy pods
6. **Blinking animations** on down components
7. **Deployment status** showing 0/3 or 0/2 ready replicas

## Cleanup

To remove these problematic resources:
```bash
kubectl delete -f /root/kubernetes-dashboard/problematic-deployments.yaml
```
