from flask import Flask, render_template, jsonify, send_file
import os
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', running_mode='Production Mode')

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
    
    # Define pods based on kubectl get po -A output
    pods = [
        {'name': 'datadog-5qglw', 'namespace': 'datadog', 'status': 'Pending', 'ready': '0/2', 'restarts': 0, 'age': '10m', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-1'},
        {'name': 'datadog-h8wbx', 'namespace': 'datadog', 'status': 'Pending', 'ready': '0/2', 'restarts': 0, 'age': '10m', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-2'},
        {'name': 'calico-kube-controllers-79949b87d-mvl85', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 15, 'age': '18d', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-master-1'},
        {'name': 'calico-node-97n64', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 8, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-master-1'},
        {'name': 'calico-node-b75gq', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-master-2'},
        {'name': 'calico-node-jnvx7', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-master-3'},
        {'name': 'calico-node-mfs42', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-worker-1'},
        {'name': 'calico-node-rx4c6', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 7, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-worker-2'},
        {'name': 'coredns-668d6bf9bc-2zdf5', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-worker-1'},
        {'name': 'coredns-668d6bf9bc-vjdnc', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-worker-2'},
        {'name': 'etcd-kube-master-1', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 9, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-master-1'},
        {'name': 'etcd-kube-master-2', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 7, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-master-2'},
        {'name': 'etcd-kube-master-3', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-master-3'},
        {'name': 'kube-apiserver-kube-master-1', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 13, 'age': '18d', 'cpu': '0.5 cores', 'memory': '512 MB', 'node': 'kube-master-1'},
        {'name': 'kube-apiserver-kube-master-2', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 12, 'age': '18d', 'cpu': '0.5 cores', 'memory': '512 MB', 'node': 'kube-master-2'},
        {'name': 'kube-apiserver-kube-master-3', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 13, 'age': '18d', 'cpu': '0.5 cores', 'memory': '512 MB', 'node': 'kube-master-3'},
        {'name': 'kube-controller-manager-kube-master-1', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 14, 'age': '18d', 'cpu': '0.3 cores', 'memory': '256 MB', 'node': 'kube-master-1'},
        {'name': 'kube-controller-manager-kube-master-2', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 16, 'age': '18d', 'cpu': '0.3 cores', 'memory': '256 MB', 'node': 'kube-master-2'},
        {'name': 'kube-controller-manager-kube-master-3', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 7, 'age': '18d', 'cpu': '0.3 cores', 'memory': '256 MB', 'node': 'kube-master-3'},
        {'name': 'kube-proxy-855jv', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-master-1'},
        {'name': 'kube-proxy-q8922', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-master-2'},
        {'name': 'kube-proxy-srlc8', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 7, 'age': '18d', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-master-3'},
        {'name': 'kube-proxy-vqrhb', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 6, 'age': '18d', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-worker-1'},
        {'name': 'kube-proxy-vvvd7', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 8, 'age': '18d', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-worker-2'},
        {'name': 'kube-scheduler-kube-master-1', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 12, 'age': '18d', 'cpu': '0.2 cores', 'memory': '128 MB', 'node': 'kube-master-1'},
        {'name': 'kube-scheduler-kube-master-2', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 15, 'age': '18d', 'cpu': '0.2 cores', 'memory': '128 MB', 'node': 'kube-master-2'},
        {'name': 'kube-scheduler-kube-master-3', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 8, 'age': '18d', 'cpu': '0.2 cores', 'memory': '128 MB', 'node': 'kube-master-3'},
        {'name': 'metrics-server-59988764cc-sbr7v', 'namespace': 'kube-system', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '11h', 'cpu': '0.1 cores', 'memory': '128 MB', 'node': 'kube-worker-1'},
        {'name': 'nginx-5fff689cfc-kts4t', 'namespace': 'nginx', 'status': 'Running', 'ready': '1/1', 'restarts': 1, 'age': '2d7h', 'cpu': '0.1 cores', 'memory': '64 MB', 'node': 'kube-worker-2'},
        {'name': 'app-1', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-1'},
        {'name': 'app-2', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-1'},
        {'name': 'app-3', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-1'},
        {'name': 'db-1', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.5 cores', 'memory': '1 GB', 'node': 'kube-worker-2'},
        {'name': 'db-2', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.5 cores', 'memory': '1 GB', 'node': 'kube-worker-2'},
        {'name': 'cache-1', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.3 cores', 'memory': '512 MB', 'node': 'kube-worker-1'},
        {'name': 'cache-2', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.3 cores', 'memory': '512 MB', 'node': 'kube-worker-2'},
        {'name': 'monitoring', 'namespace': 'prod', 'status': 'Running', 'ready': '1/1', 'restarts': 0, 'age': '18d', 'cpu': '0.2 cores', 'memory': '256 MB', 'node': 'kube-worker-2'}
    ]
    
    # Define services based on kubectl get svc -A output
    services = [
        {'name': 'datadog', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.105.180.185', 'external_ip': 'None', 'ports': '8125/UDP,8126/TCP'},
        {'name': 'datadog-agent', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.105.36.154', 'external_ip': 'None', 'ports': '8125/UDP,8126/TCP'},
        {'name': 'datadog-agent-cluster-agent', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.106.215.182', 'external_ip': 'None', 'ports': '5005/TCP'},
        {'name': 'datadog-agent-cluster-agent-admission-controller', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.96.1.28', 'external_ip': 'None', 'ports': '443/TCP'},
        {'name': 'datadog-cluster-agent', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.109.210.188', 'external_ip': 'None', 'ports': '5005/TCP'},
        {'name': 'datadog-cluster-agent-admission-controller', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.106.230.226', 'external_ip': 'None', 'ports': '443/TCP'},
        {'name': 'datadog-cluster-agent-metrics-api', 'namespace': 'datadog', 'type': 'ClusterIP', 'cluster_ip': '10.102.15.8', 'external_ip': 'None', 'ports': '8443/TCP'},
        {'name': 'kubernetes', 'namespace': 'default', 'type': 'ClusterIP', 'cluster_ip': '10.96.0.1', 'external_ip': 'None', 'ports': '443/TCP'},
        {'name': 'kube-dns', 'namespace': 'kube-system', 'type': 'ClusterIP', 'cluster_ip': '10.96.0.10', 'external_ip': 'None', 'ports': '53/UDP,53/TCP,9153/TCP'},
        {'name': 'metrics-server', 'namespace': 'kube-system', 'type': 'ClusterIP', 'cluster_ip': '10.99.161.28', 'external_ip': 'None', 'ports': '443/TCP'},
        {'name': 'nginx', 'namespace': 'nginx', 'type': 'NodePort', 'cluster_ip': '10.108.47.222', 'external_ip': 'None', 'ports': '80:30080/TCP'}
    ]
    
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
    
    # Define deployments based on the pods
    deployments = [
        {'name': 'calico-kube-controllers', 'namespace': 'kube-system', 'replicas': '1/1', 'age': '18d', 'status': 'Available'},
        {'name': 'coredns', 'namespace': 'kube-system', 'replicas': '2/2', 'age': '18d', 'status': 'Available'},
        {'name': 'metrics-server', 'namespace': 'kube-system', 'replicas': '1/1', 'age': '11h', 'status': 'Available'},
        {'name': 'nginx', 'namespace': 'nginx', 'replicas': '1/1', 'age': '2d7h', 'status': 'Available'},
        {'name': 'datadog', 'namespace': 'datadog', 'replicas': '0/2', 'age': '10m', 'status': 'Progressing'},
        {'name': 'app', 'namespace': 'prod', 'replicas': '3/3', 'age': '18d', 'status': 'Available'},
        {'name': 'db', 'namespace': 'prod', 'replicas': '2/2', 'age': '18d', 'status': 'Available'},
        {'name': 'cache', 'namespace': 'prod', 'replicas': '2/2', 'age': '18d', 'status': 'Available'},
        {'name': 'monitoring', 'namespace': 'prod', 'replicas': '1/1', 'age': '18d', 'status': 'Available'}
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
