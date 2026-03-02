# Enhanced Kubernetes Topology - AKS Network Flow Architecture

## Overview
This topology visualization follows Azure AKS networking concepts to provide a comprehensive view of traffic flow from external access through to pod execution on infrastructure nodes.

## Network Flow Layers (Based on AKS Architecture)

### Layer 1: Namespace (Logical Isolation)
- **Purpose**: Logical resource isolation and multi-tenancy
- **Visual**: Purple boxes
- **Shows**: Active/Inactive status

### Layer 2: Infrastructure (Physical/Virtual Nodes)
- **Purpose**: Compute resources where pods are scheduled
- **Visual**: Gray boxes with 🖥️ icon
- **Shows**: 
  - Node name and addresses
  - Ready/NotReady status
  - Pod-to-Node scheduling relationships (dashed lines)

### Layer 3: Workload (Pods)
- **Purpose**: Running application containers
- **Visual**: Pink dots
- **Shows**:
  - Pod status (Running, Failed, CrashLoopBackOff)
  - Container restart counts
  - Queue size for waiting containers
  - Pod IP and assigned node
  - Health indicators

### Layer 4: Workload Management (ReplicaSets & Deployments)
- **Purpose**: Declarative pod lifecycle management
- **Visual**: 
  - Deployments: Green ellipses
  - ReplicaSets: Indigo ellipses
- **Shows**:
  - Desired vs actual replica counts
  - Management hierarchy (Deployment → ReplicaSet → Pod)

### Layer 5: Network Services (Internal Load Balancing)
- **Purpose**: Service discovery and internal load balancing
- **Visual**: Blue boxes
- **Shows**:
  - Service type (ClusterIP, NodePort, LoadBalancer)
  - Cluster IP address
  - Endpoint count (healthy pods)
  - Port mappings (port → targetPort → nodePort)
  - External access indicator (🌐)
  - Traffic routing to pods

### Layer 6: Ingress (External Access & L7 Routing)
- **Purpose**: HTTP/HTTPS routing and external access
- **Visual**: Orange diamonds
- **Shows**:
  - Ingress rules (host + path)
  - L7 routing to services
  - Path-based routing labels

## Traffic Flow Visualization

### External → Internal Flow
```
Internet/External Traffic
    ↓
Ingress Controller (L7 Load Balancer)
    ↓ [path-based routing]
Service (L4 Load Balancer)
    ↓ [endpoint selection]
Pod (Application Container)
    ↓ [scheduled on]
Node (Infrastructure)
```

### Service Types & External Access

#### ClusterIP (Internal Only)
- Default service type
- Only accessible within cluster
- No external access indicator

#### NodePort (External via Node IP)
- Exposes service on each node's IP
- Shows NodePort in port mapping
- 🌐 External access indicator

#### LoadBalancer (External via Cloud LB)
- Cloud provider load balancer
- Shows external IP address
- 🌐 External access indicator
- Typical for production external services

## Edge Color Coding

| Color | Meaning | Layer |
|-------|---------|-------|
| Gray (dashed) | Pod scheduled on Node | Infrastructure |
| Blue | Service routing to Pod | Network |
| Orange | Ingress routing to Service | Ingress |
| Orange (thick) | Queue/waiting containers | Issue |
| Red (thick) | High restart count (>2) | Issue |

## Service Discovery Flow

1. **DNS Resolution**: Service name → Cluster IP
2. **Endpoint Selection**: Service → Healthy Pod IPs
3. **Traffic Routing**: Load balanced across endpoints
4. **Pod Execution**: Container processes request

## Network Policies (Future Enhancement)
- Ingress rules (incoming traffic)
- Egress rules (outgoing traffic)
- Pod-to-Pod communication policies

## Key Metrics Displayed

### Service Level
- **Endpoints**: Number of healthy pods backing the service
- **Type**: ClusterIP, NodePort, LoadBalancer
- **Ports**: Service port → Target port → Node port
- **External Access**: Whether accessible from outside cluster

### Pod Level
- **Status**: Running, Pending, Failed, CrashLoopBackOff
- **Restarts**: Container restart count
- **Queue Size**: Containers waiting to start
- **Node Assignment**: Which infrastructure node hosts the pod
- **IP Address**: Pod IP for direct communication

### Infrastructure Level
- **Node Status**: Ready/NotReady
- **Addresses**: Internal IP, External IP, Hostname
- **Pod Count**: Number of pods scheduled on node

## Use Cases

### 1. Troubleshooting Service Connectivity
- Trace path: Ingress → Service → Pods
- Check endpoint count (0 = no healthy pods)
- Verify service type and ports
- Identify pod issues (crashes, queues)

### 2. Understanding Traffic Flow
- See complete request path
- Identify load balancing points
- Understand service exposure (internal vs external)
- Track traffic from internet to pod

### 3. Capacity Planning
- View pod distribution across nodes
- Check replica counts vs desired state
- Monitor service endpoint availability
- Identify resource bottlenecks

### 4. Security Analysis
- Identify externally exposed services
- Review ingress rules and paths
- Check service types (minimize external exposure)
- Understand network boundaries

## Best Practices Visualization

### ✅ Healthy Pattern
```
Ingress → Service (LoadBalancer, 3 EP) → 3 Pods (Running) → 3 Nodes
```
- Multiple healthy endpoints
- Pods distributed across nodes
- External access properly configured

### ⚠️ Warning Pattern
```
Ingress → Service (ClusterIP, 1 EP) → 1 Pod (Running, 🔄 2) → 1 Node
```
- Single point of failure
- Pod restarting (potential issue)
- No redundancy

### ❌ Error Pattern
```
Ingress → Service (LoadBalancer, 0 EP) → 2 Pods (CrashLoopBackOff) → 2 Nodes
```
- No healthy endpoints
- Service unavailable
- Pods failing to start

## Comparison with AKS Documentation

This implementation follows Microsoft AKS networking concepts:

1. **Service Types**: ClusterIP, NodePort, LoadBalancer
2. **Ingress Controllers**: L7 HTTP/HTTPS routing
3. **Network Policies**: Pod-to-pod communication (future)
4. **DNS**: Service discovery via kube-dns/CoreDNS
5. **Load Balancing**: Service-level and ingress-level
6. **External Access**: Multiple exposure methods

## Future Enhancements

- [ ] Network Policies visualization
- [ ] DNS query paths
- [ ] ConfigMaps and Secrets references
- [ ] Persistent Volume Claims
- [ ] StatefulSets and DaemonSets
- [ ] HPA (Horizontal Pod Autoscaler) indicators
- [ ] Resource quotas and limits
- [ ] Service mesh integration (Istio, Linkerd)

## References

- [Azure AKS Network Concepts](https://learn.microsoft.com/en-us/azure/aks/concepts-network-services)
- Kubernetes Service Types
- Ingress Controllers
- Network Policies
- Service Discovery
