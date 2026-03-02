from fastapi import FastAPI, WebSocket
from kubernetes import client, config, watch
import asyncio
import json
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
net_v1 = client.NetworkingV1Api()

class TopologyBuilder:
    def match_labels(self, selector: dict, labels: dict) -> bool:
        if not selector or not labels:
            return False
        return all(labels.get(k) == v for k, v in selector.items())
    
    def get_pod_queue_metrics(self, pod) -> dict:
        restart_count = 0
        waiting_containers = 0
        queue_reasons = []
        error_reasons = []
        
        if pod.status.container_statuses:
            for c in pod.status.container_statuses:
                restart_count += c.restart_count
                if c.state.waiting:
                    waiting_containers += 1
                    reason = c.state.waiting.reason or 'Unknown'
                    message = c.state.waiting.message or ''
                    queue_reasons.append(f"{c.name}: {reason}")
                    if message:
                        queue_reasons.append(f"  → {message[:100]}")
                elif c.state.terminated:
                    reason = c.state.terminated.reason or 'Unknown'
                    exit_code = c.state.terminated.exit_code
                    error_reasons.append(f"{c.name}: {reason} (exit {exit_code})")
        
        # Check pod conditions for additional issues
        if pod.status.conditions:
            for cond in pod.status.conditions:
                if cond.status == 'False' and cond.reason:
                    error_reasons.append(f"Pod: {cond.reason} - {cond.message or ''}")
        
        return {
            'restarts': restart_count,
            'waiting': waiting_containers,
            'queued': waiting_containers > 0,
            'queue_size': waiting_containers,
            'queue_reasons': queue_reasons,
            'error_reasons': error_reasons
        }
    
    def get_service_type_info(self, svc) -> dict:
        """Get service network type and exposure details"""
        svc_type = svc.spec.type
        external_access = False
        external_ip = None
        
        if svc_type == 'LoadBalancer':
            external_access = True
            if svc.status.load_balancer.ingress:
                external_ip = svc.status.load_balancer.ingress[0].ip or svc.status.load_balancer.ingress[0].hostname
        elif svc_type == 'NodePort':
            external_access = True
        
        return {
            'type': svc_type,
            'external_access': external_access,
            'external_ip': external_ip
        }
    
    def get_health(self, resource_type: str, status) -> str:
        if resource_type == 'pod':
            if status.phase == 'Running':
                return 'healthy' if all(c.ready for c in (status.container_statuses or [])) else 'warning'
            elif status.phase in ['Failed', 'CrashLoopBackOff', 'Error']:
                return 'error'
            elif status.phase == 'Succeeded':
                return 'healthy'
            return 'warning'
        elif resource_type == 'deployment':
            if status.ready_replicas == status.replicas and status.replicas > 0:
                return 'healthy'
            elif status.ready_replicas == 0 and status.replicas > 0:
                return 'error'
            return 'warning'
        return 'unknown'
    
    def build_topology(self) -> Dict:
        nodes, edges = [], []
        node_id = 0
        
        # Get resources
        namespaces = v1.list_namespace().items
        pods = v1.list_pod_for_all_namespaces().items
        services = v1.list_service_for_all_namespaces().items
        deployments = apps_v1.list_deployment_for_all_namespaces().items
        replicasets = apps_v1.list_replica_set_for_all_namespaces().items
        try:
            ingresses = net_v1.list_ingress_for_all_namespaces().items
        except:
            ingresses = []
        
        # Get nodes for infrastructure layer
        try:
            k8s_nodes = v1.list_node().items
        except:
            k8s_nodes = []
        
        # Maps
        pod_map, rs_map, deploy_map, svc_map, node_map, ns_map = {}, {}, {}, {}, {}, {}
        
        # Layer 1: Namespaces (Logical Isolation)
        for ns in namespaces:
            ns_id = f"ns-{node_id}"
            ns_map[ns.metadata.name] = ns_id
            nodes.append({
                'id': ns_id, 'type': 'namespace', 'label': ns.metadata.name,
                'status': ns.status.phase, 'health': 'healthy' if ns.status.phase == 'Active' else 'error',
                'layer': 'namespace'
            })
            node_id += 1
        
        # Layer 2: Infrastructure - Nodes
        for node in k8s_nodes:
            k8s_node_id = f"node-{node_id}"
            node_map[node.metadata.name] = k8s_node_id
            node_ready = False
            for condition in node.status.conditions or []:
                if condition.type == 'Ready':
                    node_ready = condition.status == 'True'
            
            nodes.append({
                'id': k8s_node_id, 'type': 'node', 'label': node.metadata.name,
                'status': 'Ready' if node_ready else 'NotReady',
                'health': 'healthy' if node_ready else 'error',
                'addresses': [addr.address for addr in (node.status.addresses or [])],
                'layer': 'infrastructure'
            })
            node_id += 1
        
        # Layer 3: Workload - Pods
        for pod in pods:
            pod_id = f"pod-{node_id}"
            pod_map[f"{pod.metadata.namespace}/{pod.metadata.name}"] = pod_id
            queue_metrics = self.get_pod_queue_metrics(pod)
            nodes.append({
                'id': pod_id, 'type': 'pod', 'label': pod.metadata.name,
                'namespace': pod.metadata.namespace, 'status': pod.status.phase,
                'health': self.get_health('pod', pod.status), 'ip': pod.status.pod_ip,
                'node': pod.spec.node_name, 'labels': pod.metadata.labels or {},
                'restarts': queue_metrics['restarts'], 'queued': queue_metrics['queued'],
                'queue_size': queue_metrics['queue_size'], 'queue_reasons': queue_metrics['queue_reasons'],
                'error_reasons': queue_metrics['error_reasons'], 'layer': 'workload'
            })
            node_id += 1
            
            # Pod → Node relationship
            if pod.spec.node_name and pod.spec.node_name in node_map:
                edges.append({
                    'source': pod_id, 'target': node_map[pod.spec.node_name],
                    'type': 'scheduled_on', 'layer': 'infrastructure'
                })
        
        # Layer 4: Workload Management - ReplicaSets
        for rs in replicasets:
            rs_id = f"rs-{node_id}"
            rs_map[f"{rs.metadata.namespace}/{rs.metadata.name}"] = rs_id
            nodes.append({
                'id': rs_id, 'type': 'replicaset', 'label': rs.metadata.name,
                'namespace': rs.metadata.namespace, 'replicas': rs.spec.replicas,
                'ready': rs.status.ready_replicas or 0, 'selector': rs.spec.selector.match_labels or {},
                'layer': 'workload'
            })
            node_id += 1
            
            # RS → Pods
            for pod in pods:
                if pod.metadata.namespace == rs.metadata.namespace and pod.metadata.owner_references:
                    for owner in pod.metadata.owner_references:
                        if owner.kind == 'ReplicaSet' and owner.name == rs.metadata.name:
                            pod_id = pod_map.get(f"{pod.metadata.namespace}/{pod.metadata.name}")
                            if pod_id:
                                edges.append({'source': rs_id, 'target': pod_id, 'type': 'manages', 'layer': 'workload'})
        
        # Layer 5: Workload Management - Deployments
        for deploy in deployments:
            deploy_id = f"deploy-{node_id}"
            deploy_map[f"{deploy.metadata.namespace}/{deploy.metadata.name}"] = deploy_id
            nodes.append({
                'id': deploy_id, 'type': 'deployment', 'label': deploy.metadata.name,
                'namespace': deploy.metadata.namespace, 'replicas': deploy.spec.replicas,
                'ready': deploy.status.ready_replicas or 0, 'health': self.get_health('deployment', deploy.status),
                'selector': deploy.spec.selector.match_labels or {}, 'layer': 'workload'
            })
            node_id += 1
            
            # Deploy → RS
            for rs in replicasets:
                if rs.metadata.namespace == deploy.metadata.namespace and rs.metadata.owner_references:
                    for owner in rs.metadata.owner_references:
                        if owner.kind == 'Deployment' and owner.name == deploy.metadata.name:
                            rs_id = rs_map.get(f"{rs.metadata.namespace}/{rs.metadata.name}")
                            if rs_id:
                                edges.append({'source': deploy_id, 'target': rs_id, 'type': 'manages', 'layer': 'workload'})
        
        # Layer 6: Network - Services (Internal Load Balancing)
        for svc in services:
            svc_id = f"svc-{node_id}"
            svc_map[f"{svc.metadata.namespace}/{svc.metadata.name}"] = svc_id
            svc_info = self.get_service_type_info(svc)
            
            nodes.append({
                'id': svc_id, 'type': 'service', 'label': svc.metadata.name,
                'namespace': svc.metadata.namespace, 'svc_type': svc.spec.type,
                'cluster_ip': svc.spec.cluster_ip, 'selector': svc.spec.selector or {},
                'ports': [{'port': p.port, 'target': p.target_port, 'node_port': getattr(p, 'node_port', None)} for p in (svc.spec.ports or [])],
                'external_access': svc_info['external_access'], 'external_ip': svc_info['external_ip'],
                'layer': 'network'
            })
            node_id += 1
            
            # Service → Pods (Traffic routing)
            pod_count = 0
            for pod in pods:
                if pod.metadata.namespace == svc.metadata.namespace:
                    if self.match_labels(svc.spec.selector, pod.metadata.labels):
                        pod_id = pod_map.get(f"{pod.metadata.namespace}/{pod.metadata.name}")
                        if pod_id:
                            pod_count += 1
                            edges.append({'source': svc_id, 'target': pod_id, 'type': 'routes', 'layer': 'network'})
            
            # Update service with endpoint count
            for node in nodes:
                if node['id'] == svc_id:
                    node['endpoints'] = pod_count
                    break
        
        # Layer 7: Ingress (External Access & L7 Load Balancing)
        for ing in ingresses:
            ing_id = f"ing-{node_id}"
            rules = []
            if ing.spec.rules:
                for rule in ing.spec.rules:
                    if rule.http and rule.http.paths:
                        for path in rule.http.paths:
                            svc_name = path.backend.service.name if path.backend.service else None
                            rules.append({'host': rule.host, 'path': path.path, 'service': svc_name})
            
            nodes.append({
                'id': ing_id, 'type': 'ingress', 'label': ing.metadata.name,
                'namespace': ing.metadata.namespace, 'rules': rules,
                'layer': 'ingress'
            })
            node_id += 1
            
            # Ingress → Service (L7 routing)
            for rule in rules:
                if rule['service']:
                    svc_id = svc_map.get(f"{ing.metadata.namespace}/{rule['service']}")
                    if svc_id:
                        edges.append({'source': ing_id, 'target': svc_id, 'type': 'routes', 'path': rule.get('path', '/'), 'layer': 'ingress'})
        
        return {'nodes': nodes, 'edges': edges}

topology = TopologyBuilder()

@app.get("/api/topology")
async def get_topology():
    return topology.build_topology()

@app.websocket("/ws/topology")
async def ws_topology(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(topology.build_topology())
    
    try:
        w = watch.Watch()
        for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=30):
            await websocket.send_json(topology.build_topology())
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8889)
