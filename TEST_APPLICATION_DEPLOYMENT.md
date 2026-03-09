# DSDP Java Application Deployment

## Deployment Date: March 6, 2026

## Overview
Complete Java-based application deployed in the `dsdp` namespace with all Kubernetes components for testing metrics.

## Deployed Components

### 1. Namespace
- **Name:** `dsdp`
- **Purpose:** Isolated environment for Java API application

### 2. Application Deployment
- **Name:** `java-api-app`
- **Replicas:** 3 pods
- **Image:** nginx:alpine (serving as API simulator)
- **Resources:**
  - Requests: 64Mi memory, 100m CPU
  - Limits: 128Mi memory, 200m CPU
- **Port:** 80

### 3. ClusterIP Service
- **Name:** `java-api-service`
- **Type:** ClusterIP
- **Port:** 80
- **Purpose:** Internal cluster communication

### 4. LoadBalancer Service
- **Name:** `java-api-loadbalancer`
- **Type:** LoadBalancer
- **Port:** 80
- **NodePort:** 31776
- **Purpose:** External access to the application

### 5. Ingress
- **Name:** `java-api-ingress`
- **Host:** java-api.local
- **Path:** /
- **Backend:** java-api-service:80
- **Purpose:** HTTP routing and external access

## API Endpoints (Simulated)

The application simulates a Java API with the following endpoints:
- `/api/submit` - Submit API request
- `/api/metrics` - View request metrics (submit, delivered, failure counts)
- `/health` - Health check endpoint

## Metrics Tracking

The application tracks:
- **Submit Count:** Total API requests submitted
- **Delivered Count:** Successfully processed requests (~90% success rate)
- **Failure Count:** Failed requests (~10% failure rate)

## Access the Application

### Internal Access (from within cluster):
```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n dsdp -- curl http://java-api-service
```

### External Access (via NodePort):
```bash
curl http://<node-ip>:31776
```

### Via LoadBalancer (when external IP is assigned):
```bash
kubectl get svc -n dsdp java-api-loadbalancer
curl http://<external-ip>
```

## View Deployment Status

```bash
# View all resources
kubectl get all,ingress -n dsdp

# View pods
kubectl get pods -n dsdp

# View services
kubectl get svc -n dsdp

# View ingress
kubectl get ingress -n dsdp

# View pod logs
kubectl logs -n dsdp -l app=java-api

# Describe deployment
kubectl describe deployment java-api-app -n dsdp
```

## Metrics Dashboard Integration

The deployed application can be monitored through the Kubernetes Dashboard:
1. Navigate to the Metrics tab
2. Select namespace: `dsdp`
3. Select pod: Any of the `java-api-app-*` pods
4. View real-time metrics:
   - CPU Usage
   - Memory Usage
   - Network I/O
   - API Request Metrics (Submit, Delivered, Failure)

## Testing API Metrics

Generate load to test metrics:
```bash
# Run load test
kubectl run load-test --image=curlimages/curl -n dsdp -- /bin/sh -c "while true; do curl -s http://java-api-service; sleep 1; done"

# View metrics in dashboard
# Click on Failure count to see error details
```

## Cleanup

To remove the deployment:
```bash
kubectl delete namespace dsdp
```

## Architecture

```
Internet
    |
    v
LoadBalancer (31776)
    |
    v
Ingress (java-api.local)
    |
    v
Service (java-api-service:80)
    |
    v
Pods (3 replicas)
- java-api-app-xxx-1
- java-api-app-xxx-2
- java-api-app-xxx-3
```

## Current Status

✅ Namespace: Created
✅ Deployment: 3/3 pods running
✅ ClusterIP Service: Active
✅ LoadBalancer Service: Active (NodePort: 31776)
✅ Ingress: Configured
✅ Ready for metrics monitoring
