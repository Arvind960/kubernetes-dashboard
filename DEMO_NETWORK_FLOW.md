# Demo Network Flow Test Deployment

## Deployed Architecture

### Namespace: demo-app
Complete 3-tier application with all service types and ingress

## Components Deployed

### 1. Frontend (Web Tier)
- **Deployment**: frontend (3 replicas)
- **Pods**: 3x nginx:1.21 (Running)
- **Service**: frontend-service
  - **Type**: LoadBalancer 🌐
  - **Port**: 80 → 80
  - **External IP**: Pending (cloud provider)
  - **Endpoints**: 3 healthy pods
- **Purpose**: Public-facing web application

### 2. Backend API (Application Tier)
- **Deployment**: backend-api (2 replicas)
- **Pods**: 2x http-echo (Running)
- **Service**: backend-service
  - **Type**: ClusterIP (Internal only)
  - **Port**: 8080 → 8080
  - **Endpoints**: 2 healthy pods
- **Purpose**: Internal API service

### 3. Database (Data Tier)
- **Deployment**: database (1 replica)
- **Pods**: 1x redis:alpine (Running)
- **Service**: database-service
  - **Type**: ClusterIP (Internal only)
  - **Port**: 6379 → 6379
  - **Endpoints**: 1 healthy pod
- **Purpose**: Data persistence layer

### 4. Monitoring (Observability)
- **Deployment**: monitoring (1 replica)
- **Pods**: 1x prometheus (ContainerCreating)
- **Service**: monitoring-service
  - **Type**: NodePort 🌐
  - **Port**: 9090 → 9090
  - **NodePort**: 30090
  - **Endpoints**: 0-1 pods
- **Purpose**: Metrics collection

### 5. Ingress (L7 Routing)
- **Ingress**: demo-ingress
- **Host**: demo.example.com
- **Rules**:
  - `/` → frontend-service:80
  - `/api` → backend-service:8080
- **Purpose**: HTTP path-based routing

## Network Flow Visualization

### Complete Traffic Path

```
Internet/External Users
        ↓
[Ingress Controller] demo-ingress
    ├─ / → frontend-service (LoadBalancer, 3 EP) 🌐
    │       ↓
    │   [3 Frontend Pods] nginx:1.21
    │       ↓
    │   [3 Worker Nodes] 🖥️
    │
    └─ /api → backend-service (ClusterIP, 2 EP)
            ↓
        [2 Backend Pods] http-echo
            ↓
        [2 Worker Nodes] 🖥️
            ↓
        database-service (ClusterIP, 1 EP)
            ↓
        [1 Database Pod] redis
            ↓
        [1 Worker Node] 🖥️

Monitoring Access (Direct):
NodeIP:30090 → monitoring-service (NodePort, 1 EP) 🌐
                    ↓
                [1 Monitoring Pod] prometheus
                    ↓
                [1 Worker Node] 🖥️
```

## Service Type Demonstration

### LoadBalancer (frontend-service)
- **External Access**: ✅ Yes
- **Cloud LB**: Pending external IP
- **Use Case**: Public web application
- **Topology Shows**: 🌐 External, [LoadBalancer], 3 EP

### ClusterIP (backend-service, database-service)
- **External Access**: ❌ No
- **Internal Only**: Cluster communication
- **Use Case**: Internal microservices
- **Topology Shows**: [ClusterIP], X EP

### NodePort (monitoring-service)
- **External Access**: ✅ Yes
- **Access Via**: NodeIP:30090
- **Use Case**: Admin/monitoring tools
- **Topology Shows**: 🌐 External, [NodePort], (30090)

## What to See in Topology Map

### Access: http://localhost:8888/topology

### Layer 1: Namespace
- **demo-app** namespace (purple box)

### Layer 2: Infrastructure
- **3 Nodes** (gray boxes with 🖥️)
- Shows pod distribution across nodes

### Layer 3: Workloads
- **7 Pods** total (pink dots)
  - 3 frontend (Running)
  - 2 backend-api (Running)
  - 1 database (Running)
  - 1 monitoring (ContainerCreating)

### Layer 4: Workload Management
- **4 Deployments** (green ellipses)
  - frontend (3/3)
  - backend-api (2/2)
  - database (1/1)
  - monitoring (0/1 or 1/1)
- **4 ReplicaSets** (indigo ellipses)

### Layer 5: Network Services
- **frontend-service** (blue box)
  - [LoadBalancer] 🌐
  - 3 EP
  - Port: 80→80
  
- **backend-service** (blue box)
  - [ClusterIP]
  - 2 EP
  - Port: 8080→8080
  
- **database-service** (blue box)
  - [ClusterIP]
  - 1 EP
  - Port: 6379→6379
  
- **monitoring-service** (blue box)
  - [NodePort] 🌐
  - 0-1 EP
  - Port: 9090→9090 (NodePort: 30090)

### Layer 6: Ingress
- **demo-ingress** (orange diamond)
  - Host: demo.example.com
  - Paths: /, /api
  - Routes to frontend and backend services

## Edge Colors in Topology

- **Orange**: Ingress → Services (L7 routing)
- **Blue**: Services → Pods (L4 load balancing)
- **Gray dashed**: Pods → Nodes (scheduling)

## Testing Scenarios

### 1. External Access Flow
Click on: Ingress → frontend-service → frontend pods
- See complete path from internet to pod
- Verify LoadBalancer type and external access
- Check 3 healthy endpoints

### 2. Internal Service Communication
Click on: backend-service → backend pods
- See ClusterIP (internal only)
- No external access indicator
- 2 healthy endpoints

### 3. NodePort Access
Click on: monitoring-service
- See NodePort type
- External access via NodeIP:30090
- Port mapping visible

### 4. Multi-Tier Architecture
- Trace: Ingress → Frontend → Backend → Database
- See service types at each layer
- Understand security boundaries

## Cleanup

To remove the demo:
```bash
kubectl delete namespace demo-app
```

Or keep specific components:
```bash
kubectl delete -f /root/kubernetes-dashboard/demo-network-flow.yaml
```

## Key Observations

✅ **LoadBalancer**: Public-facing services (frontend)
✅ **ClusterIP**: Internal services (backend, database)
✅ **NodePort**: Admin/monitoring access
✅ **Ingress**: L7 HTTP routing with path-based rules
✅ **Multi-replica**: High availability (3 frontend, 2 backend)
✅ **Node distribution**: Pods spread across infrastructure
✅ **Complete flow**: Internet → Ingress → Service → Pod → Node

This demonstrates the complete AKS network architecture!
