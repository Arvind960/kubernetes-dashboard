#!/usr/bin/env python3
"""
Kubernetes Monitoring Dashboard
Provides a web-based dashboard for monitoring Kubernetes cluster components.
"""
import os
import time
import json
from datetime import datetime, timedelta
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import humanize
from flask import Flask, render_template, jsonify, request
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

class K8sMonitor:
    def __init__(self):
        try:
            # Try to load from within cluster first
            try:
                config.load_incluster_config()
                self.running_mode = "Running inside the cluster"
                logger.info("Running inside the cluster")
            except:
                # Fall back to kubeconfig
                config.load_kube_config()
                self.running_mode = "Running outside the cluster"
                logger.info("Running outside the cluster")
            
            # Initialize Kubernetes API clients
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            
            # Store monitoring data
            self.data = {
                "last_updated": "",
                "cluster_health": {
                    "status": "Unknown",
                    "components": []
                },
                "nodes": [],
                "pods": [],
                "deployments": [],
                "services": [],
                "resource_usage": {
                    "cpu": {"used": 0, "total": 0},
                    "memory": {"used": 0, "total": 0}
                }
            }
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise
    
    def get_pod_age(self, creation_timestamp):
        """Calculate pod age in human readable format"""
        if not creation_timestamp:
            return "Unknown"
        
        now = datetime.now(creation_timestamp.tzinfo)
        age = now - creation_timestamp
        
        # Format age in a human-readable way
        if age.days > 0:
            return f"{age.days}d"
        elif age.seconds >= 3600:
            return f"{age.seconds // 3600}h"
        elif age.seconds >= 60:
            return f"{age.seconds // 60}m"
        else:
            return f"{age.seconds}s"
    
    def collect_cluster_health(self):
        """Collect cluster health information"""
        try:
            # Check API server health
            self.core_v1.get_api_resources()
            status = "Healthy"
            
            # Check component statuses
            components = []
            try:
                component_statuses = self.core_v1.list_component_status()
                for item in component_statuses.items:
                    component_health = all(cond.status == "True" for cond in item.conditions)
                    components.append({
                        "name": item.metadata.name,
                        "status": "Healthy" if component_health else "Unhealthy"
                    })
            except:
                logger.warning("Component status check not available")
            
            self.data["cluster_health"] = {
                "status": status,
                "components": components
            }
        except Exception as e:
            logger.error(f"Failed to collect cluster health: {e}")
            self.data["cluster_health"] = {
                "status": "Unhealthy",
                "components": []
            }
    
    def collect_nodes(self):
        """Collect node information"""
        try:
            nodes = self.core_v1.list_node()
            node_data = []
            
            total_cpu = 0
            total_memory = 0
            
            for node in nodes.items:
                name = node.metadata.name
                status = "Unknown"
                
                # Check node conditions
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        status = "Ready" if condition.status == "True" else "NotReady"
                
                # Get resource capacity
                cpu_capacity = node.status.capacity.get("cpu")
                memory_capacity = node.status.capacity.get("memory", "0")
                
                # Convert memory to GB
                if memory_capacity.endswith("Ki"):
                    memory_gb = int(memory_capacity[:-2]) / (1024 * 1024)
                elif memory_capacity.endswith("Mi"):
                    memory_gb = int(memory_capacity[:-2]) / 1024
                elif memory_capacity.endswith("Gi"):
                    memory_gb = int(memory_capacity[:-2])
                else:
                    memory_gb = 0
                
                # Add to totals
                try:
                    total_cpu += int(cpu_capacity)
                    total_memory += memory_gb
                except:
                    pass
                
                node_data.append({
                    "name": name,
                    "status": status,
                    "cpu": cpu_capacity,
                    "memory": f"{memory_gb:.1f} GB",
                    "kubelet_version": node.status.node_info.kubelet_version if node.status.node_info else "Unknown"
                })
            
            self.data["nodes"] = node_data
            self.data["resource_usage"]["cpu"]["total"] = total_cpu
            self.data["resource_usage"]["memory"]["total"] = total_memory
        except Exception as e:
            logger.error(f"Failed to collect nodes: {e}")
            self.data["nodes"] = []
    
    def collect_pods(self):
        """Collect pod information"""
        try:
            pods = self.core_v1.list_pod_for_all_namespaces(watch=False)
            pod_data = []
            
            cpu_usage = 0
            memory_usage = 0
            
            for pod in pods.items:
                name = pod.metadata.name
                namespace = pod.metadata.namespace
                status = pod.status.phase
                
                # Calculate restarts
                restarts = 0
                if pod.status.container_statuses:
                    restarts = sum(container.restart_count for container in pod.status.container_statuses)
                
                # Calculate age
                age = self.get_pod_age(pod.metadata.creation_timestamp)
                
                # Calculate resource usage (requests)
                cpu_request = 0
                memory_request = 0
                
                if pod.spec.containers:
                    for container in pod.spec.containers:
                        if container.resources and container.resources.requests:
                            # CPU requests
                            if container.resources.requests.get("cpu"):
                                cpu_req = container.resources.requests.get("cpu")
                                if cpu_req.endswith("m"):
                                    cpu_request += int(cpu_req[:-1]) / 1000
                                else:
                                    try:
                                        cpu_request += float(cpu_req)
                                    except:
                                        pass
                            
                            # Memory requests
                            if container.resources.requests.get("memory"):
                                mem_req = container.resources.requests.get("memory")
                                if mem_req.endswith("Mi"):
                                    memory_request += int(mem_req[:-2]) / 1024  # Convert to GB
                                elif mem_req.endswith("Gi"):
                                    memory_request += int(mem_req[:-2])
                                elif mem_req.endswith("Ki"):
                                    memory_request += int(mem_req[:-2]) / (1024 * 1024)  # Convert to GB
                
                # Add to total usage
                cpu_usage += cpu_request
                memory_usage += memory_request
                
                # Get ready status
                ready = "False"
                if pod.status.container_statuses:
                    ready = "True" if all(container.ready for container in pod.status.container_statuses) else "False"
                
                pod_data.append({
                    "name": name,
                    "namespace": namespace,
                    "status": status,
                    "ready": ready,
                    "restarts": restarts,
                    "age": age,
                    "cpu": f"{cpu_request:.2f} cores",
                    "memory": f"{memory_request:.2f} GB",
                    "node": pod.spec.node_name if pod.spec.node_name else "Unknown"
                })
            
            self.data["pods"] = pod_data
            self.data["resource_usage"]["cpu"]["used"] = cpu_usage
            self.data["resource_usage"]["memory"]["used"] = memory_usage
        except Exception as e:
            logger.error(f"Failed to collect pods: {e}")
            self.data["pods"] = []
    
    def collect_deployments(self):
        """Collect deployment information"""
        try:
            deployments = self.apps_v1.list_deployment_for_all_namespaces()
            deployment_data = []
            
            for deployment in deployments.items:
                name = deployment.metadata.name
                namespace = deployment.metadata.namespace
                replicas = deployment.spec.replicas
                available = deployment.status.available_replicas or 0
                
                # Calculate age
                age = self.get_pod_age(deployment.metadata.creation_timestamp)
                
                deployment_data.append({
                    "name": name,
                    "namespace": namespace,
                    "replicas": f"{available}/{replicas}",
                    "age": age,
                    "status": "Available" if available == replicas else "Progressing"
                })
            
            self.data["deployments"] = deployment_data
        except Exception as e:
            logger.error(f"Failed to collect deployments: {e}")
            self.data["deployments"] = []
    
    def collect_services(self):
        """Collect service information"""
        try:
            services = self.core_v1.list_service_for_all_namespaces()
            service_data = []
            
            for service in services.items:
                name = service.metadata.name
                namespace = service.metadata.namespace
                service_type = service.spec.type
                cluster_ip = service.spec.cluster_ip
                
                # Get external IP if available
                external_ip = "None"
                if service.spec.type == "LoadBalancer" and service.status.load_balancer.ingress:
                    external_ip = service.status.load_balancer.ingress[0].ip or service.status.load_balancer.ingress[0].hostname
                
                # Get ports
                ports = []
                if service.spec.ports:
                    for port in service.spec.ports:
                        port_info = f"{port.port}"
                        if port.node_port:
                            port_info += f":{port.node_port}"
                        if port.name:
                            port_info += f"/{port.name}"
                        ports.append(port_info)
                
                service_data.append({
                    "name": name,
                    "namespace": namespace,
                    "type": service_type,
                    "cluster_ip": cluster_ip,
                    "external_ip": external_ip,
                    "ports": ", ".join(ports)
                })
            
            self.data["services"] = service_data
        except Exception as e:
            logger.error(f"Failed to collect services: {e}")
            self.data["services"] = []
    
    def collect_all_data(self):
        """Collect all monitoring data"""
        try:
            self.collect_cluster_health()
            self.collect_nodes()
            self.collect_pods()
            self.collect_deployments()
            self.collect_services()
            
            self.data["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return self.data
        except Exception as e:
            logger.error(f"Failed to collect all data: {e}")
            return self.data

# Create monitor instance
monitor = K8sMonitor()

# Background monitoring thread
def background_monitoring():
    while True:
        try:
            monitor.collect_all_data()
            logger.info(f"Data collected at {monitor.data['last_updated']}")
        except Exception as e:
            logger.error(f"Error in background monitoring: {e}")
        
        # Sleep for 30 seconds
        time.sleep(30)

# Create templates directory and HTML template
def create_templates():
    os.makedirs('templates', exist_ok=True)
    
    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { padding-top: 20px; }
        .card { margin-bottom: 20px; }
        .status-ready { color: green; }
        .status-notready { color: red; }
        .status-warning { color: orange; }
        .table-container { overflow-x: auto; }
        .resource-chart { height: 200px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row mb-3">
            <div class="col">
                <h1>Kubernetes Monitoring Dashboard</h1>
                <p>{{ running_mode }} - <span id="lastUpdated"></span></p>
                <button id="refreshBtn" class="btn btn-primary">Refresh Data</button>
            </div>
        </div>
        
        <div class="row">
            <!-- Cluster Overview -->
            <div class="col-md-6 col-lg-3">
                <div class="card">
                    <div class="card-header">
                        <h5>Cluster Overview</h5>
                    </div>
                    <div class="card-body">
                        <div id="clusterHealth"></div>
                        <div class="mt-3">
                            <h6>Resource Usage</h6>
                            <div class="mb-2">
                                <label>CPU Usage:</label>
                                <div class="progress">
                                    <div id="cpuProgress" class="progress-bar" role="progressbar" style="width: 0%"></div>
                                </div>
                                <small id="cpuText">0/0 cores</small>
                            </div>
                            <div>
                                <label>Memory Usage:</label>
                                <div class="progress">
                                    <div id="memoryProgress" class="progress-bar bg-success" role="progressbar" style="width: 0%"></div>
                                </div>
                                <small id="memoryText">0/0 GB</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5>Nodes</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Status</th>
                                        <th>CPU</th>
                                        <th>Memory</th>
                                    </tr>
                                </thead>
                                <tbody id="nodesTable"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Pods -->
            <div class="col-md-6 col-lg-9">
                <div class="card">
                    <div class="card-header">
                        <h5>Pods</h5>
                        <div class="input-group mt-2">
                            <input type="text" id="podSearch" class="form-control" placeholder="Search pods...">
                            <select id="namespaceFilter" class="form-select">
                                <option value="all">All Namespaces</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-container">
                            <table class="table table-sm table-hover">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Namespace</th>
                                        <th>Status</th>
                                        <th>Ready</th>
                                        <th>Restarts</th>
                                        <th>Age</th>
                                        <th>CPU</th>
                                        <th>Memory</th>
                                        <th>Node</th>
                                    </tr>
                                </thead>
                                <tbody id="podsTable"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Deployments</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-container">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Namespace</th>
                                                <th>Replicas</th>
                                                <th>Age</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody id="deploymentsTable"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Services</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-container">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Namespace</th>
                                                <th>Type</th>
                                                <th>Cluster IP</th>
                                                <th>External IP</th>
                                                <th>Ports</th>
                                            </tr>
                                        </thead>
                                        <tbody id="servicesTable"></tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Update UI with data
        function updateUI(data) {
            // Last updated
            document.getElementById('lastUpdated').textContent = 'Last updated: ' + data.last_updated;
            
            // Cluster health
            let healthHtml = '';
            if (data.cluster_health.status === 'Healthy') {
                healthHtml += '<div class="alert alert-success">Cluster is healthy</div>';
            } else {
                healthHtml += '<div class="alert alert-danger">Cluster has issues</div>';
            }
            
            if (data.cluster_health.components && data.cluster_health.components.length > 0) {
                healthHtml += '<ul class="list-group">';
                data.cluster_health.components.forEach(component => {
                    const statusClass = component.status === 'Healthy' ? 'status-ready' : 'status-notready';
                    healthHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                        ${component.name}
                        <span class="${statusClass}">${component.status}</span>
                    </li>`;
                });
                healthHtml += '</ul>';
            }
            document.getElementById('clusterHealth').innerHTML = healthHtml;
            
            // Resource usage
            const cpuUsed = data.resource_usage.cpu.used;
            const cpuTotal = data.resource_usage.cpu.total;
            const cpuPercent = cpuTotal > 0 ? (cpuUsed / cpuTotal) * 100 : 0;
            
            document.getElementById('cpuProgress').style.width = cpuPercent + '%';
            document.getElementById('cpuText').textContent = `${cpuUsed.toFixed(2)}/${cpuTotal} cores (${cpuPercent.toFixed(1)}%)`;
            
            const memoryUsed = data.resource_usage.memory.used;
            const memoryTotal = data.resource_usage.memory.total;
            const memoryPercent = memoryTotal > 0 ? (memoryUsed / memoryTotal) * 100 : 0;
            
            document.getElementById('memoryProgress').style.width = memoryPercent + '%';
            document.getElementById('memoryText').textContent = `${memoryUsed.toFixed(2)}/${memoryTotal.toFixed(1)} GB (${memoryPercent.toFixed(1)}%)`;
            
            // Nodes
            let nodesHtml = '';
            if (data.nodes && data.nodes.length > 0) {
                data.nodes.forEach(node => {
                    const statusClass = node.status === 'Ready' ? 'status-ready' : 'status-notready';
                    nodesHtml += `<tr>
                        <td>${node.name}</td>
                        <td class="${statusClass}">${node.status}</td>
                        <td>${node.cpu}</td>
                        <td>${node.memory}</td>
                    </tr>`;
                });
            } else {
                nodesHtml = '<tr><td colspan="4">No nodes found</td></tr>';
            }
            document.getElementById('nodesTable').innerHTML = nodesHtml;
            
            // Update namespace filter
            const namespaceFilter = document.getElementById('namespaceFilter');
            const currentSelection = namespaceFilter.value;
            
            // Clear existing options except "All Namespaces"
            while (namespaceFilter.options.length > 1) {
                namespaceFilter.remove(1);
            }
            
            // Add namespaces from pods
            const namespaces = new Set();
            if (data.pods && data.pods.length > 0) {
                data.pods.forEach(pod => {
                    namespaces.add(pod.namespace);
                });
                
                // Sort namespaces
                Array.from(namespaces).sort().forEach(namespace => {
                    const option = document.createElement('option');
                    option.value = namespace;
                    option.textContent = namespace;
                    namespaceFilter.appendChild(option);
                });
            }
            
            // Restore selection if possible
            if (Array.from(namespaceFilter.options).some(option => option.value === currentSelection)) {
                namespaceFilter.value = currentSelection;
            }
            
            // Filter and display pods
            filterAndDisplayPods(data.pods);
            
            // Deployments
            let deploymentsHtml = '';
            if (data.deployments && data.deployments.length > 0) {
                data.deployments.forEach(deployment => {
                    const statusClass = deployment.status === 'Available' ? 'status-ready' : 'status-warning';
                    deploymentsHtml += `<tr>
                        <td>${deployment.name}</td>
                        <td>${deployment.namespace}</td>
                        <td>${deployment.replicas}</td>
                        <td>${deployment.age}</td>
                        <td class="${statusClass}">${deployment.status}</td>
                    </tr>`;
                });
            } else {
                deploymentsHtml = '<tr><td colspan="5">No deployments found</td></tr>';
            }
            document.getElementById('deploymentsTable').innerHTML = deploymentsHtml;
            
            // Services
            let servicesHtml = '';
            if (data.services && data.services.length > 0) {
                data.services.forEach(service => {
                    servicesHtml += `<tr>
                        <td>${service.name}</td>
                        <td>${service.namespace}</td>
                        <td>${service.type}</td>
                        <td>${service.cluster_ip}</td>
                        <td>${service.external_ip}</td>
                        <td>${service.ports}</td>
                    </tr>`;
                });
            } else {
                servicesHtml = '<tr><td colspan="6">No services found</td></tr>';
            }
            document.getElementById('servicesTable').innerHTML = servicesHtml;
        }
        
        // Filter and display pods
        function filterAndDisplayPods(pods) {
            const searchTerm = document.getElementById('podSearch').value.toLowerCase();
            const namespaceFilter = document.getElementById('namespaceFilter').value;
            
            let filteredPods = pods;
            
            // Apply namespace filter
            if (namespaceFilter !== 'all') {
                filteredPods = filteredPods.filter(pod => pod.namespace === namespaceFilter);
            }
            
            // Apply search filter
            if (searchTerm) {
                filteredPods = filteredPods.filter(pod => 
                    pod.name.toLowerCase().includes(searchTerm) || 
                    pod.namespace.toLowerCase().includes(searchTerm)
                );
            }
            
            // Display pods
            let podsHtml = '';
            if (filteredPods && filteredPods.length > 0) {
                filteredPods.forEach(pod => {
                    const statusClass = pod.status === 'Running' ? 'status-ready' : 
                                       pod.status === 'Pending' ? 'status-warning' : 'status-notready';
                    podsHtml += `<tr>
                        <td>${pod.name}</td>
                        <td>${pod.namespace}</td>
                        <td class="${statusClass}">${pod.status}</td>
                        <td>${pod.ready}</td>
                        <td>${pod.restarts}</td>
                        <td>${pod.age}</td>
                        <td>${pod.cpu}</td>
                        <td>${pod.memory}</td>
                        <td>${pod.node}</td>
                    </tr>`;
                });
            } else {
                podsHtml = '<tr><td colspan="9">No pods found</td></tr>';
            }
            document.getElementById('podsTable').innerHTML = podsHtml;
        }
        
        // Fetch data from API
        function fetchData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    updateUI(data);
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                });
        }
        
        // Set up event listeners
        document.addEventListener('DOMContentLoaded', function() {
            // Initial data fetch
            fetchData();
            
            // Refresh button
            document.getElementById('refreshBtn').addEventListener('click', fetchData);
            
            // Pod search
            document.getElementById('podSearch').addEventListener('input', function() {
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => {
                        filterAndDisplayPods(data.pods);
                    });
            });
            
            // Namespace filter
            document.getElementById('namespaceFilter').addEventListener('change', function() {
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => {
                        filterAndDisplayPods(data.pods);
                    });
            });
            
            // Auto-refresh every 30 seconds
            setInterval(fetchData, 30000);
        });
    </script>
</body>
</html>
"""
    
    with open('templates/index.html', 'w') as f:
        f.write(index_html)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html', running_mode=monitor.running_mode)

@app.route('/api/data')
def get_data():
    return jsonify(monitor.data)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    monitor.collect_all_data()
    return jsonify({"status": "success", "last_updated": monitor.data["last_updated"]})

if __name__ == "__main__":
    try:
        # Create templates
        create_templates()
        
        # Initial data collection
        monitor.collect_all_data()
        
        # Start background monitoring thread
        monitoring_thread = threading.Thread(target=background_monitoring)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        
        # Start Flask app
        logger.info("Starting Kubernetes Monitoring Dashboard on port 9090")
        app.run(host='0.0.0.0', port=8888, debug=False)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
