#!/usr/bin/env python3
"""
Enhanced Kubernetes Dashboard with CloudWatch Integration
"""
import os
import sys
import logging
from flask import Flask, render_template, jsonify, request
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from cloudwatch_api import cloudwatch_bp

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'k8s_dashboard.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('k8s_dashboard')

app = Flask(__name__)

# Register CloudWatch blueprint
app.register_blueprint(cloudwatch_bp)

# Load Kubernetes configuration
try:
    config.load_kube_config()
    logger.info("Loaded kube config successfully")
except:
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster config successfully")
    except Exception as e:
        logger.error(f"Could not load Kubernetes config: {e}")

# Initialize Kubernetes API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pods')
def get_pods():
    """Get all pods with optional CloudWatch metrics"""
    namespace = request.args.get('namespace', 'default')
    include_cloudwatch = request.args.get('cloudwatch', 'false').lower() == 'true'
    
    try:
        pods = v1.list_namespaced_pod(namespace)
        pod_list = []
        
        for pod in pods.items:
            pod_data = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase,
                'node': pod.spec.node_name,
                'ip': pod.status.pod_ip
            }
            pod_list.append(pod_data)
        
        return jsonify({'pods': pod_list})
    except ApiException as e:
        logger.error(f"Error fetching pods: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/nodes')
def get_nodes():
    """Get all nodes"""
    try:
        nodes = v1.list_node()
        node_list = []
        
        for node in nodes.items:
            node_data = {
                'name': node.metadata.name,
                'status': 'Ready' if any(c.type == 'Ready' and c.status == 'True' 
                                        for c in node.status.conditions) else 'NotReady',
                'version': node.status.node_info.kubelet_version
            }
            node_list.append(node_data)
        
        return jsonify({'nodes': node_list})
    except ApiException as e:
        logger.error(f"Error fetching nodes: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
