# Production Namespace Testing - Queue & Issue Tracking

## Deployed Resources in Production Namespace

### ✅ Healthy Deployment
**prod-web-app** (Frontend)
- **Status**: 3/3 Running
- **Service**: prod-web-service
- **Endpoints**: 3 healthy pods
- **Topology Shows**: Green borders, all healthy

### ❌ CrashLoopBackOff Issue
**prod-api-crash** (Backend API)
- **Status**: 1/2 pods failing
- **Issue**: Container exits with code 1 after 3 seconds
- **Restarts**: Increasing (1, 2, 3...)
- **Service**: prod-api-service (1 endpoint only)
- **Topology Shows**:
  - 🔄 Restart counts on pods
  - Red edges to failing pods
  - ⚠️ DOWN indicator
  - Error Details: "api-server: Error (exit 1)"

### ⏳ ImagePullBackOff Queue
**prod-db-image-error** (Database)
- **Status**: 0/1 - ImagePullBackOff
- **Issue**: Invalid image tag "postgres:99.99-invalid"
- **Queue Size**: 1 container waiting
- **Service**: prod-db-service (0 endpoints)
- **Topology Shows**:
  - ⏳ Q:1 on node
  - Orange edges with queue indicator
  - Queue Issues: "postgres: ImagePullBackOff"
  - Message: "Failed to pull image postgres:99.99-invalid"

### 💥 OOMKilled Issue
**prod-cache-oom** (Cache)
- **Status**: 0/1 - OOMKilled
- **Issue**: Memory consumption exceeds 100Mi limit
- **Restarts**: Increasing due to OOM
- **Service**: prod-cache-service (0 endpoints)
- **Topology Shows**:
  - 🔄 Restart count
  - Red borders and edges
  - Error Details: "redis: OOMKilled (exit 137)"

## Test the Topology Map

### Access the Dashboard
```
http://localhost:8888/topology
```

### What to Look For:

#### 1. Namespace View
- Filter by "production" namespace to see only production resources
- See all 4 deployments with their services

#### 2. Healthy Resources (prod-web-app)
- **Green borders** on all 3 pods
- **Service shows**: [3 endpoints]
- **Deployment shows**: (3/3)
- Click pod to see: Status: Running, Health: HEALTHY

#### 3. CrashLoopBackOff (prod-api-crash)
- **Red dashed borders** on failing pods
- **🔄 2** or higher restart count visible
- **Red edges** from service to pods
- Click pod to see:
  ```
  Status: CrashLoopBackOff
  🔄 Restarts: 2
  ❌ Error Details: api-server: Error (exit 1)
  ```

#### 4. ImagePullBackOff (prod-db-image-error)
- **Orange edges** to the pod
- **⏳ Q:1** on the node
- **Service shows**: [0 endpoints]
- Click pod to see:
  ```
  Status: ImagePullBackOff
  ⏳ QUEUE SIZE: 1
  📋 Queue Issues:
    postgres: ImagePullBackOff
    → Failed to pull image "postgres:99.99-invalid"
  ```

#### 5. OOMKilled (prod-cache-oom)
- **Red borders** with restart count
- **🔄 1+** restarts
- Click pod to see:
  ```
  Status: CrashLoopBackOff
  🔄 Restarts: 1
  ❌ Error Details: redis: OOMKilled (exit 137)
  ```

## Testing Checklist

- [ ] Open topology map: http://localhost:8888/topology
- [ ] Verify production namespace resources are visible
- [ ] Click on prod-web-app pod - should show HEALTHY
- [ ] Click on prod-api-crash pod - should show restart count and exit code
- [ ] Click on prod-db-image-error pod - should show queue size and image pull error
- [ ] Click on prod-cache-oom pod - should show OOMKilled error
- [ ] Verify services show correct endpoint counts
- [ ] Verify edges are color-coded (green=healthy, orange=queued, red=failing)
- [ ] Verify deployments show replica status (3/3, 0/1, etc.)

## Expected Topology Flow

```
Ingress (if any)
    ↓
Services (with endpoint counts)
    ↓
Deployments (with replica status)
    ↓
ReplicaSets
    ↓
Pods (with health indicators, queue size, restart counts)
```

## Cleanup

To remove test deployments:
```bash
kubectl delete -f /root/kubernetes-dashboard/production-test-deployment.yaml
```

To keep only healthy deployments:
```bash
kubectl delete deployment prod-api-crash prod-db-image-error prod-cache-oom -n production
```

## Real-World Scenarios Tested

1. ✅ **Normal Operation**: prod-web-app shows how healthy services look
2. 🔄 **Application Crashes**: prod-api-crash simulates buggy code
3. ⏳ **Configuration Errors**: prod-db-image-error simulates wrong image tags
4. 💥 **Resource Limits**: prod-cache-oom simulates memory issues

All scenarios are now visible in the topology map with detailed diagnostics!
