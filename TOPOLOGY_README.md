# Kubernetes Dynamic Topology Visualization

## Architecture

### Components
1. **Backend (FastAPI)**: Discovers resources via Kubernetes API, builds graph structure
2. **Frontend (Vis.js)**: Interactive graph visualization with real-time updates
3. **WebSocket**: Live updates using Kubernetes Watch API

### Resource Discovery Flow
```
Kubernetes API → TopologyBuilder → Graph Structure → WebSocket → Frontend
```

### Relationship Detection
- **Deployment → ReplicaSet → Pods**: Uses `ownerReferences`
- **Service → Pods**: Matches `spec.selector` with pod labels
- **Ingress → Service**: Parses `spec.rules.backend.service.name`
- **Namespace**: Groups all resources by `metadata.namespace`

## Features

✅ Auto-discovery of all cluster resources
✅ Automatic relationship detection
✅ Traffic flow visualization (Ingress → Service → Pod)
✅ Interactive clickable nodes
✅ Details panel with labels, selectors, status
✅ Health status color-coding (green/yellow/red)
✅ Live updates via WebSocket
✅ Hierarchical layout (left-to-right flow)

## Installation

### 1. Apply RBAC
```bash
kubectl apply -f kubernetes/topology-rbac.yaml
```

### 2. Deploy Application
```bash
kubectl apply -f kubernetes/topology-deployment.yaml
```

### 3. Access
```bash
# NodePort
http://<node-ip>:30889/topology

# Port Forward
kubectl port-forward svc/k8s-topology-viewer 8889:8889
http://localhost:8889/topology
```

## API Endpoints

- `GET /api/topology` - Get current topology snapshot
- `WS /ws/topology` - WebSocket for live updates

## Graph Structure

```json
{
  "nodes": [
    {
      "id": "pod-1",
      "type": "pod",
      "label": "nginx-abc",
      "namespace": "default",
      "status": "Running",
      "health": "healthy",
      "labels": {"app": "nginx"}
    }
  ],
  "edges": [
    {
      "source": "svc-1",
      "target": "pod-1",
      "type": "routes"
    }
  ]
}
```

## Health Status

- **Green**: Healthy (Running pods, ready replicas)
- **Yellow**: Warning (Pending, partial replicas)
- **Red**: Error (Failed, no replicas)

## Technology Stack

- **Backend**: Python, FastAPI, kubernetes-client
- **Frontend**: HTML5, Vis.js Network
- **Communication**: REST API + WebSocket
- **Deployment**: Kubernetes with RBAC
