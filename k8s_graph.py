from flask import Flask, jsonify, render_template
from kubernetes import client, config
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
net_v1 = client.NetworkingV1Api()

def match_labels(selector, labels):
    if not selector or not labels:
        return False
    return all(labels.get(k) == v for k, v in selector.items())

@app.route('/')
def index():
    return render_template('graph.html')

@app.route('/api/graph')
def get_graph():
    nodes = []
    edges = []
    node_id = 0
    
    # Get all resources
    pods = v1.list_pod_for_all_namespaces().items
    services = v1.list_service_for_all_namespaces().items
    deployments = apps_v1.list_deployment_for_all_namespaces().items
    try:
        ingresses = net_v1.list_ingress_for_all_namespaces().items
    except:
        ingresses = []
    
    # Create node maps
    pod_nodes = {}
    svc_nodes = {}
    deploy_nodes = {}
    ingress_nodes = {}
    
    # Add Pods
    for pod in pods:
        pod_id = f"pod-{node_id}"
        node_id += 1
        pod_nodes[f"{pod.metadata.namespace}/{pod.metadata.name}"] = pod_id
        nodes.append({
            'id': pod_id,
            'label': pod.metadata.name,
            'type': 'pod',
            'namespace': pod.metadata.namespace,
            'status': pod.status.phase,
            'labels': pod.metadata.labels or {},
            'ip': pod.status.pod_ip
        })
    
    # Add Deployments
    for deploy in deployments:
        deploy_id = f"deploy-{node_id}"
        node_id += 1
        deploy_nodes[f"{deploy.metadata.namespace}/{deploy.metadata.name}"] = deploy_id
        nodes.append({
            'id': deploy_id,
            'label': deploy.metadata.name,
            'type': 'deployment',
            'namespace': deploy.metadata.namespace,
            'replicas': deploy.spec.replicas,
            'selector': deploy.spec.selector.match_labels or {}
        })
        
        # Link Deployment to Pods
        for pod in pods:
            if pod.metadata.namespace == deploy.metadata.namespace:
                if match_labels(deploy.spec.selector.match_labels, pod.metadata.labels):
                    pod_id = pod_nodes.get(f"{pod.metadata.namespace}/{pod.metadata.name}")
                    if pod_id:
                        edges.append({
                            'from': deploy_id,
                            'to': pod_id,
                            'type': 'manages'
                        })
    
    # Add Services
    for svc in services:
        svc_id = f"svc-{node_id}"
        node_id += 1
        svc_nodes[f"{svc.metadata.namespace}/{svc.metadata.name}"] = svc_id
        nodes.append({
            'id': svc_id,
            'label': svc.metadata.name,
            'type': 'service',
            'namespace': svc.metadata.namespace,
            'type_detail': svc.spec.type,
            'selector': svc.spec.selector or {},
            'ports': [{'port': p.port, 'target': p.target_port} for p in (svc.spec.ports or [])]
        })
        
        # Link Service to Pods
        for pod in pods:
            if pod.metadata.namespace == svc.metadata.namespace:
                if match_labels(svc.spec.selector, pod.metadata.labels):
                    pod_id = pod_nodes.get(f"{pod.metadata.namespace}/{pod.metadata.name}")
                    if pod_id:
                        edges.append({
                            'from': svc_id,
                            'to': pod_id,
                            'type': 'routes'
                        })
    
    # Add Ingresses
    for ing in ingresses:
        ing_id = f"ing-{node_id}"
        node_id += 1
        ingress_nodes[f"{ing.metadata.namespace}/{ing.metadata.name}"] = ing_id
        
        rules = []
        if ing.spec.rules:
            for rule in ing.spec.rules:
                if rule.http and rule.http.paths:
                    for path in rule.http.paths:
                        rules.append({
                            'host': rule.host,
                            'path': path.path,
                            'service': path.backend.service.name if path.backend.service else None
                        })
        
        nodes.append({
            'id': ing_id,
            'label': ing.metadata.name,
            'type': 'ingress',
            'namespace': ing.metadata.namespace,
            'rules': rules
        })
        
        # Link Ingress to Services
        for rule in rules:
            if rule['service']:
                svc_id = svc_nodes.get(f"{ing.metadata.namespace}/{rule['service']}")
                if svc_id:
                    edges.append({
                        'from': ing_id,
                        'to': svc_id,
                        'type': 'routes',
                        'path': rule.get('path', '/')
                    })
    
    return jsonify({'nodes': nodes, 'edges': edges})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=True)
