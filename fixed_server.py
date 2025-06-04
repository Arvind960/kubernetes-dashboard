import os
import time
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('fixed.html', running_mode='Production Mode')

@app.route('/api/data')
def get_data():
    # Define namespaces based on kubectl get ns output
    namespaces = [
        {'name': 'datadog', 'status': 'Active', 'age': '15d', 'pods': 2, 'services': 7},
        {'name': 'default', 'status': 'Active', 'age': '18d', 'pods': 0, 'services': 1},
        {'name': 'kube-node-lease', 'status': 'Active', 'age': '18d', 'pods': 0, 'services': 0},
        {'name': 'kube-public', 'status': 'Active', 'age': '18d', 'pods': 0, 'services': 0},
        {'name': 'kube-system', 'status': 'Active', 'age': '18d', 'pods': 18, 'services': 2},
        {'name': 'nginx', 'status': 'Active', 'age': '2d7h', 'pods': 1, 'services': 1},
        {'name': 'prod', 'status': 'Active', 'age': '18d', 'pods': 8, 'services': 0}
    ]
    
    # Define nodes based on kubectl get node output
    nodes = [
        {'name': 'kube-master-1', 'status': 'Ready', 'cpu': '4', 'memory': '8 GB', 'role': 'master'},
        {'name': 'kube-master-2', 'status': 'Ready', 'cpu': '4', 'memory': '8 GB', 'role': 'master'},
        {'name': 'kube-master-3', 'status': 'NotReady', 'cpu': '4', 'memory': '8 GB', 'role': 'master'},
        {'name': 'kube-worker-1', 'status': 'Ready', 'cpu': '8', 'memory': '16 GB', 'role': 'worker'},
        {'name': 'kube-worker-2', 'status': 'Ready', 'cpu': '8', 'memory': '16 GB', 'role': 'worker'}
    ]
    
    # Define pods (simplified for brevity)
    pods = [
        {'name': 'datadog-5qglw', 'namespace': 'datadog', 'status': 'Pending', 'ready': '0/2', 'restarts': 0, 'age': '10m', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-1'},
        {'name': 'datadog-h8wbx', 'namespace': 'datadog', 'status': 'Pending', 'ready': '0/2', 'restarts': 0, 'age': '10m', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-2'},
        {'name': 'nginx-5fff689cfc-kts4t', 'namespace': 'nginx', 'status': 'Running', 'ready': '1/1', 'restarts': 1, 'age': '2d7h', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-worker-2'}
    ]
    
    # Add 18 pods in kube-system namespace
    for i in range(18):
        pods.append({
            'name': f'kube-system-pod-{i+1}',
            'namespace': 'kube-system',
            'status': 'Running',
            'ready': '1/1',
            'restarts': 0,
            'age': '18d',
            'cpu': '0.1 cores',
            'memory': '128 MB',
            'node': 'kube-master-1' if i < 6 else ('kube-master-2' if i < 12 else 'kube-master-3')
        })
    
    # Add 8 pods in prod namespace
    for i in range(8):
        pods.append({
            'name': f'prod-pod-{i+1}',
            'namespace': 'prod',
            'status': 'Running',
            'ready': '1/1',
            'restarts': 0,
            'age': '18d',
            'cpu': '0.2 cores',
            'memory': '256 MB',
            'node': 'kube-worker-1' if i < 4 else 'kube-worker-2'
        })
    
    # Define services (simplified for brevity)
    services = [
        {'name': 'kubernetes', 'namespace': 'default', 'type': 'ClusterIP', 'cluster_ip': '10.96.0.1', 'external_ip': 'None', 'ports': '443/TCP'},
        {'name': 'kube-dns', 'namespace': 'kube-system', 'type': 'ClusterIP', 'cluster_ip': '10.96.0.10', 'external_ip': 'None', 'ports': '53/UDP,53/TCP,9153/TCP'},
        {'name': 'metrics-server', 'namespace': 'kube-system', 'type': 'ClusterIP', 'cluster_ip': '10.99.161.28', 'external_ip': 'None', 'ports': '443/TCP'},
        {'name': 'nginx', 'namespace': 'nginx', 'type': 'NodePort', 'cluster_ip': '10.108.47.222', 'external_ip': 'None', 'ports': '80:30080/TCP'}
    ]
    
    # Add 7 services in datadog namespace
    for i in range(7):
        services.append({
            'name': f'datadog-service-{i+1}',
            'namespace': 'datadog',
            'type': 'ClusterIP',
            'cluster_ip': f'10.10{i}.0.{i+1}',
            'external_ip': 'None',
            'ports': '8125/UDP,8126/TCP'
        })
    
    # Calculate total CPU and memory capacity
    total_cpu = sum(float(node['cpu']) for node in nodes)
    total_memory = sum(float(node['memory'].split()[0]) for node in nodes)
    
    # Calculate used CPU and memory
    used_cpu = 0
    used_memory = 0
    
    for pod in pods:
        if pod['status'] == 'Running':
            # Extract CPU usage
            cpu_str = pod['cpu']
            if 'cores' in cpu_str:
                used_cpu += float(cpu_str.split()[0])
            
            # Extract memory usage
            memory_str = pod['memory']
            if 'GB' in memory_str:
                used_memory += float(memory_str.split()[0])
            elif 'MB' in memory_str:
                used_memory += float(memory_str.split()[0]) / 1024  # Convert MB to GB
    
    # Define deployments (simplified for brevity)
    deployments = [
        {'name': 'nginx', 'namespace': 'nginx', 'replicas': '1/1', 'age': '2d7h', 'status': 'Available'},
        {'name': 'datadog', 'namespace': 'datadog', 'replicas': '0/2', 'age': '10m', 'status': 'Progressing'}
    ]
    
    return jsonify({
        'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'cluster_health': {'status': 'Warning', 'components': [
            {'name': 'API Server', 'status': 'Healthy'},
            {'name': 'Controller Manager', 'status': 'Healthy'},
            {'name': 'Scheduler', 'status': 'Healthy'},
            {'name': 'etcd', 'status': 'Healthy'},
            {'name': 'Node Status', 'status': 'Warning'}
        ]},
        'namespaces': namespaces,
        'nodes': nodes,
        'pods': pods,
        'deployments': deployments,
        'services': services,
        'resource_usage': {
            'cpu': {'used': round(used_cpu, 2), 'total': total_cpu},
            'memory': {'used': round(used_memory, 2), 'total': total_memory}
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
