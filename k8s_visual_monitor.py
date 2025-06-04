#!/usr/bin/env python3
"""
Kubernetes Cluster Visual Monitoring Tool
Provides a web-based dashboard for monitoring Kubernetes cluster health and resources.
"""
import os
import sys
import json
import time
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import psutil
import requests
from tabulate import tabulate
from flask import Flask, render_template, jsonify, request
import threading

# Initialize Flask app
app = Flask(__name__)

class K8sMonitor:
    def __init__(self):
        try:
            # Try to load from within cluster first
            try:
                config.load_incluster_config()
                self.running_mode = "Running inside the cluster"
            except:
                # Fall back to kubeconfig
                config.load_kube_config()
                self.running_mode = "Running outside the cluster"
            
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.storage_v1 = client.StorageV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            
            # Store monitoring data
            self.data = {
                "overall_health": {},
                "nodes": [],
                "pods": {"running": [], "failed": []},
                "suspected_failures": [],
                "resource_utilization": {},
                "connectivity": {},
                "storage": {},
                "rbac": {},
                "last_updated": ""
            }
        except Exception as e:
            print(f"Failed to initialize Kubernetes client: {e}")
            sys.exit(1)

    def check_overall_health(self):
        """Check overall Kubernetes cluster health"""
        health_data = {"status": "Healthy", "components": []}
        
        try:
            # Check API server health
            api_health = self.core_v1.get_api_resources()
            health_data["components"].append({"name": "API Server", "status": "Healthy"})
            
            # Check component statuses (deprecated but still useful)
            try:
                components = self.core_v1.list_component_status()
                for item in components.items:
                    status = "Healthy" if all(cond.status == "True" for cond in item.conditions) else "Unhealthy"
                    health_data["components"].append({"name": item.metadata.name, "status": status})
            except:
                health_data["components"].append({"name": "Component Status", "status": "Not Available"})
                
            self.data["overall_health"] = health_data
            return True
        except Exception as e:
            health_data["status"] = "Unhealthy"
            health_data["components"].append({"name": "API Server", "status": f"Unhealthy - {str(e)}"})
            self.data["overall_health"] = health_data
            return False

    def check_nodes_health(self):
        """Check health status of all nodes"""
        nodes_data = []
        
        try:
            nodes = self.core_v1.list_node()
            
            for node in nodes.items:
                node_info = {
                    "name": node.metadata.name,
                    "status": "Ready",
                    "cpu": "N/A",
                    "memory": "N/A"
                }
                
                # Check node conditions
                for condition in node.status.conditions:
                    if condition.type == "Ready":
                        node_info["status"] = "Ready" if condition.status == "True" else "NotReady"
                
                # Get resource usage
                try:
                    # Fallback to node status for capacity info (not actual usage)
                    allocatable_cpu = node.status.allocatable.get("cpu", "N/A")
                    allocatable_memory = node.status.allocatable.get("memory", "N/A")
                    node_info["cpu"] = f"Allocatable: {allocatable_cpu}"
                    node_info["memory"] = f"Allocatable: {allocatable_memory}"
                except Exception as e:
                    pass
                
                nodes_data.append(node_info)
            
            self.data["nodes"] = nodes_data
            return True
        except Exception as e:
            print(f"Failed to check nodes health: {e}")
            return False

    def check_pods_status(self):
        """Check status of all pods"""
        running_pods = []
        failed_pods = []
        
        try:
            pods = self.core_v1.list_pod_for_all_namespaces(watch=False)
            
            for pod in pods.items:
                pod_info = {
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "restarts": 0
                }
                
                # Count restarts
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        pod_info["restarts"] += container.restart_count
                
                if pod.status.phase == "Running":
                    running_pods.append(pod_info)
                elif pod.status.phase in ["Failed", "Pending"]:
                    # Get reason for failure
                    reason = "Unknown"
                    message = "No details available"
                    
                    if pod.status.conditions:
                        for condition in pod.status.conditions:
                            if condition.reason:
                                reason = condition.reason
                            if condition.message:
                                message = condition.message
                    
                    pod_info["reason"] = reason
                    pod_info["message"] = message
                    failed_pods.append(pod_info)
            
            self.data["pods"]["running"] = running_pods
            self.data["pods"]["failed"] = failed_pods
            return True
        except Exception as e:
            print(f"Failed to check pods status: {e}")
            return False

    def check_suspected_failures(self):
        """Check for pods with high restart counts or other issues"""
        suspected_failures = []
        
        try:
            # Use data already collected in check_pods_status
            for pod in self.data["pods"]["running"]:
                issues = []
                
                # Check for high restart count
                if pod["restarts"] > 5:
                    issues.append(f"High restart count: {pod['restarts']}")
                
                if issues:
                    suspected_failures.append({
                        "namespace": pod["namespace"],
                        "name": pod["name"],
                        "status": pod["status"],
                        "restarts": pod["restarts"],
                        "issues": issues
                    })
            
            self.data["suspected_failures"] = suspected_failures
            return True
        except Exception as e:
            print(f"Failed to check suspected failures: {e}")
            return False

    def check_resource_utilization(self):
        """Check cluster resource utilization"""
        resource_data = {
            "cpu": {"total": 0, "requested": 0, "percent": 0},
            "memory": {"total": 0, "requested": 0, "percent": 0},
            "top_pods": []
        }
        
        try:
            # Get nodes to calculate total capacity
            nodes = self.core_v1.list_node()
            for node in nodes.items:
                if node.status.capacity:
                    cpu = node.status.capacity.get("cpu")
                    if cpu:
                        resource_data["cpu"]["total"] += int(cpu)
                    
                    memory = node.status.capacity.get("memory")
                    if memory and memory.endswith("Ki"):
                        memory_gb = int(memory[:-2]) / (1024 * 1024)
                        resource_data["cpu"]["total"] += memory_gb
            
            # Get pod resource requests
            pods = self.core_v1.list_pod_for_all_namespaces(watch=False)
            pod_resources = []
            
            for pod in pods.items:
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
                                    cpu_request += float(cpu_req)
                            
                            # Memory requests
                            if container.resources.requests.get("memory"):
                                mem_req = container.resources.requests.get("memory")
                                if mem_req.endswith("Mi"):
                                    memory_request += int(mem_req[:-2]) / 1024
                                elif mem_req.endswith("Gi"):
                                    memory_request += int(mem_req[:-2])
                                elif mem_req.endswith("Ki"):
                                    memory_request += int(mem_req[:-2]) / (1024 * 1024)
                
                pod_resources.append({
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "cpu_request": cpu_request,
                    "memory_request": memory_request
                })
            
            # Sort by CPU request and get top consumers
            pod_resources.sort(key=lambda x: x["cpu_request"], reverse=True)
            resource_data["top_pods"] = pod_resources[:10]
            
            # Calculate total requested resources
            resource_data["cpu"]["requested"] = sum(pod["cpu_request"] for pod in pod_resources)
            resource_data["memory"]["requested"] = sum(pod["memory_request"] for pod in pod_resources)
            
            # Calculate percentages
            if resource_data["cpu"]["total"] > 0:
                resource_data["cpu"]["percent"] = (resource_data["cpu"]["requested"] / resource_data["cpu"]["total"]) * 100
            
            if resource_data["memory"]["total"] > 0:
                resource_data["memory"]["percent"] = (resource_data["memory"]["requested"] / resource_data["memory"]["total"]) * 100
            
            self.data["resource_utilization"] = resource_data
            return True
        except Exception as e:
            print(f"Failed to check resource utilization: {e}")
            return False

    def run_all_checks(self):
        """Run all monitoring checks and update data"""
        self.check_overall_health()
        self.check_nodes_health()
        self.check_pods_status()
        self.check_suspected_failures()
        self.check_resource_utilization()
        
        self.data["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.data

# Create monitor instance
monitor = K8sMonitor()

# Background monitoring thread
def background_monitoring():
    while True:
        monitor.run_all_checks()
        time.sleep(30)  # Update every 30 seconds

# Flask routes
@app.route('/')
def index():
    return render_template('index.html', running_mode=monitor.running_mode)

@app.route('/api/data')
def get_data():
    return jsonify(monitor.data)

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    monitor.run_all_checks()
    return jsonify({"status": "success", "last_updated": monitor.data["last_updated"]})

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Start background monitoring thread
    monitoring_thread = threading.Thread(target=background_monitoring)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # Initial data collection
    monitor.run_all_checks()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=9090, debug=True)
