#!/usr/bin/env python3

import os
import time
from flask import Flask, render_template, jsonify, request
from kubernetes import client, config
import datetime
from kubernetes.client.rest import ApiException
import traceback
import json

app = Flask(__name__, static_folder='static')

# Load Kubernetes configuration
try:
    config.load_kube_config()
    print("Loaded kube config successfully")
except Exception as e:
    try:
        config.load_incluster_config()
        print("Loaded in-cluster config successfully")
    except Exception as e:
        print(f"Could not load Kubernetes config: {e}")

# Initialize Kubernetes API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

@app.route('/')
def index():
    return render_template('fixed_template.html', running_mode='Production Mode')

@app.route('/debug')
def debug():
    return render_template('debug_template.html')

@app.route('/deployment-control')
def deployment_control():
    """Render the deployment control page"""
    return render_template('deployment_control.html')

@app.route('/api/data')
def get_data():
    try:
        # Get nodes
        nodes = []
        node_list = v1.list_node()
        for node in node_list.items:
            # Determine node role
            role = "worker"
            for label in node.metadata.labels:
                if "node-role.kubernetes.io/master" in label or "node-role.kubernetes.io/control-plane" in label:
                    role = "master"
                    break
            
            # Get node status
            status = "Unknown"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    status = "Ready" if condition.status == "True" else "NotReady"
                    break
            
            # Get node resources
            allocatable = node.status.allocatable
            capacity = node.status.capacity
            
            cpu_allocatable = allocatable.get("cpu", "N/A")
            memory_allocatable = allocatable.get("memory", "N/A")
            cpu_capacity = capacity.get("cpu", "N/A")
            memory_capacity = capacity.get("memory", "N/A")
            
            # Get node creation time
            creation_timestamp = node.metadata.creation_timestamp
            
            # Format creation time
            if creation_timestamp:
                creation_time = creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                creation_time = "Unknown"
            
            # Get node IP
            node_ip = "Unknown"
            for address in node.status.addresses:
                if address.type == "InternalIP":
                    node_ip = address.address
                    break
            
            nodes.append({
                "name": node.metadata.name,
                "role": role,
                "status": status,
                "ip": node_ip,
                "cpu_allocatable": cpu_allocatable,
                "memory_allocatable": memory_allocatable,
                "cpu_capacity": cpu_capacity,
                "memory_capacity": memory_capacity,
                "creation_time": creation_time
            })
        
        # Get namespaces
        namespaces = []
        namespace_list = v1.list_namespace()
        for namespace in namespace_list.items:
            namespaces.append({
                "name": namespace.metadata.name,
                "status": namespace.status.phase,
                "creation_time": namespace.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") if namespace.metadata.creation_timestamp else "Unknown"
            })
        
        # Get pods
        pods = []
        pod_list = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pod_list.items:
            # Get pod status
            status = pod.status.phase
            
            # Get pod creation time
            creation_timestamp = pod.metadata.creation_timestamp
            
            # Format creation time
            if creation_timestamp:
                creation_time = creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                creation_time = "Unknown"
            
            # Get pod IP
            pod_ip = pod.status.pod_ip or "N/A"
            
            # Get container statuses
            container_statuses = []
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    container_status = {
                        "name": container.name,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "image": container.image
                    }
                    
                    # Determine container state
                    if container.state.running:
                        container_status["state"] = "Running"
                        container_status["started_at"] = container.state.running.started_at.strftime("%Y-%m-%d %H:%M:%S") if container.state.running.started_at else "Unknown"
                    elif container.state.waiting:
                        container_status["state"] = "Waiting"
                        container_status["reason"] = container.state.waiting.reason
                    elif container.state.terminated:
                        container_status["state"] = "Terminated"
                        container_status["reason"] = container.state.terminated.reason
                        container_status["exit_code"] = container.state.terminated.exit_code
                    else:
                        container_status["state"] = "Unknown"
                    
                    container_statuses.append(container_status)
            
            # Get pod owner
            owner = "None"
            owner_kind = "None"
            if pod.metadata.owner_references:
                owner = pod.metadata.owner_references[0].name
                owner_kind = pod.metadata.owner_references[0].kind
            
            pods.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": status,
                "ip": pod_ip,
                "node": pod.spec.node_name if pod.spec.node_name else "N/A",
                "creation_time": creation_time,
                "containers": container_statuses,
                "owner": owner,
                "owner_kind": owner_kind
            })
        
        # Get services
        services = []
        service_list = v1.list_service_for_all_namespaces(watch=False)
        for service in service_list.items:
            # Get service type
            service_type = service.spec.type
            
            # Get service creation time
            creation_timestamp = service.metadata.creation_timestamp
            
            # Format creation time
            if creation_timestamp:
                creation_time = creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                creation_time = "Unknown"
            
            # Get service cluster IP
            cluster_ip = service.spec.cluster_ip or "N/A"
            
            # Get service external IP
            external_ip = "N/A"
            if service.status.load_balancer.ingress:
                for ingress in service.status.load_balancer.ingress:
                    if ingress.ip:
                        external_ip = ingress.ip
                        break
                    elif ingress.hostname:
                        external_ip = ingress.hostname
                        break
            
            # Get service ports
            ports = []
            if service.spec.ports:
                for port in service.spec.ports:
                    port_info = {
                        "name": port.name if port.name else "unnamed",
                        "port": port.port,
                        "target_port": port.target_port,
                        "protocol": port.protocol
                    }
                    if port.node_port:
                        port_info["node_port"] = port.node_port
                    ports.append(port_info)
            
            services.append({
                "name": service.metadata.name,
                "namespace": service.metadata.namespace,
                "type": service_type,
                "cluster_ip": cluster_ip,
                "external_ip": external_ip,
                "ports": ports,
                "creation_time": creation_time
            })
        
        # Get deployments
        deployments = []
        deployment_list = apps_v1.list_deployment_for_all_namespaces(watch=False)
        for deployment in deployment_list.items:
            # Get deployment status
            available_replicas = deployment.status.available_replicas or 0
            replicas = deployment.spec.replicas or 0
            
            if available_replicas == replicas:
                status = "Available"
            else:
                status = f"Scaling ({available_replicas}/{replicas})"
            
            # Get deployment creation time
            creation_timestamp = deployment.metadata.creation_timestamp
            
            # Format creation time
            if creation_timestamp:
                creation_time = creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                creation_time = "Unknown"
            
            deployments.append({
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": replicas,
                "available_replicas": available_replicas,
                "status": status,
                "creation_time": creation_time
            })
        
        return jsonify({
            "nodes": nodes,
            "namespaces": namespaces,
            "pods": pods,
            "services": services,
            "deployments": deployments
        })
    except Exception as e:
        print(f"Error getting data: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/pods/stop', methods=['POST'])
def stop_pod():
    try:
        data = request.get_json()
        namespace = data.get('namespace')
        name = data.get('name')
        
        if not namespace or not name:
            return jsonify({
                'success': False,
                'message': "Namespace and pod name are required"
            }), 400
        
        # Delete the pod
        v1.delete_namespaced_pod(name=name, namespace=namespace)
        
        return jsonify({
            'success': True,
            'message': f"Pod {name} in namespace {namespace} has been stopped"
        })
    except Exception as e:
        print(f"Error stopping pod: {e}")
        return jsonify({
            'success': False,
            'message': f"Error stopping pod: {str(e)}"
        }), 500

@app.route('/api/pods/start', methods=['POST'])
def start_pod():
    try:
        data = request.get_json()
        namespace = data.get('namespace', 'default')
        name = data.get('name')
        owner = data.get('owner')  # This could be a deployment, statefulset, etc.
        
        if name:
            # Check if pod already exists
            try:
                v1.read_namespaced_pod(name=name, namespace=namespace)
                return jsonify({
                    'success': False,
                    'message': f"Pod {name} already exists in namespace {namespace}"
                })
            except ApiException as e:
                if e.status == 404:
                    # Pod doesn't exist, create it
                    pod_manifest = {
                        "apiVersion": "v1",
                        "kind": "Pod",
                        "metadata": {
                            "name": name,
                            "namespace": namespace
                        },
                        "spec": {
                            "containers": [
                                {
                                    "name": "nginx",
                                    "image": "nginx:latest",
                                    "ports": [{"containerPort": 80}]
                                }
                            ]
                        }
                    }
                    
                    try:
                        v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
                        print(f"Created pod {name}")
                        return jsonify({
                            'success': True,
                            'message': f"Pod {name} created in namespace {namespace}"
                        })
                    except ApiException as create_error:
                        print(f"Error creating pod: {create_error}")
                        return jsonify({
                            'success': False,
                            'message': f"Error creating pod: {create_error.reason}"
                        }), create_error.status
                else:
                    print(f"Error checking if pod exists: {e}")
                    return jsonify({
                        'success': False,
                        'message': f"Error checking if pod exists: {e.reason}"
                    }), e.status
        
        # If we don't have a specific pod name or owner, create a new pod
        new_pod_name = f"manual-pod-{int(time.time())}"
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": new_pod_name,
                "namespace": namespace
            },
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx:latest",
                        "ports": [{"containerPort": 80}]
                    }
                ]
            }
        }
        
        try:
            v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
            print(f"Created new pod {new_pod_name}")
            return jsonify({
                'success': True,
                'message': f"New pod {new_pod_name} created in namespace {namespace}"
            })
        except ApiException as e:
            print(f"Error creating new pod: {e}")
            return jsonify({
                'success': False,
                'message': f"Error creating new pod: {e.reason}"
            }), e.status
            
    except Exception as e:
        print(f"Unexpected error in start_pod: {e}")
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

# New endpoints for stopping and starting deployments
@app.route('/api/deployment/stop', methods=['POST'])
def stop_deployment_api():
    """Stop a deployment by scaling it to 0 replicas and saving the original replica count"""
    try:
        data = request.get_json()
        namespace = data.get('namespace', 'default')
        deployment_name = data.get('deployment_name')
        
        if not deployment_name:
            return jsonify({
                'success': False,
                'message': "Deployment name is required"
            }), 400
        
        try:
            # Get current deployment info
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            current_replicas = deployment.spec.replicas
            
            # Save the current replica count as an annotation
            if not deployment.metadata.annotations:
                deployment.metadata.annotations = {}
            
            deployment.metadata.annotations['k8s-dashboard/original-replicas'] = str(current_replicas)
            deployment.metadata.annotations['k8s-dashboard/paused'] = 'true'
            
            # Scale the deployment to 0
            deployment.spec.replicas = 0
            apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            return jsonify({
                'success': True,
                'message': f"Deployment {deployment_name} in namespace {namespace} scaled to 0 replicas",
                'previous_replicas': current_replicas
            })
            
        except ApiException as e:
            print(f"Error stopping deployment: {e}")
            return jsonify({
                'success': False,
                'message': f"Error stopping deployment: {e.reason}"
            }), e.status
            
    except Exception as e:
        print(f"Unexpected error in stop_deployment: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

@app.route('/api/deployment/start', methods=['POST'])
def start_deployment_api():
    """Start a deployment by scaling it back to the original replica count"""
    try:
        data = request.get_json()
        namespace = data.get('namespace', 'default')
        deployment_name = data.get('deployment_name')
        replicas = data.get('replicas')
        
        if not deployment_name:
            return jsonify({
                'success': False,
                'message': "Deployment name is required"
            }), 400
        
        try:
            # Get current deployment
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            
            # If replicas not specified, try to read from annotation
            if replicas is None:
                if deployment.metadata.annotations and 'k8s-dashboard/original-replicas' in deployment.metadata.annotations:
                    replicas = int(deployment.metadata.annotations['k8s-dashboard/original-replicas'])
                else:
                    # Default to 1 replica if annotation not found
                    replicas = 1
                    print(f"No saved replica count found for {deployment_name}, defaulting to 1")
            
            # Scale the deployment back to the original/specified replica count
            deployment.spec.replicas = replicas
            
            # Update the annotation to indicate it's no longer paused
            if deployment.metadata.annotations:
                deployment.metadata.annotations['k8s-dashboard/paused'] = 'false'
            
            apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            return jsonify({
                'success': True,
                'message': f"Deployment {deployment_name} in namespace {namespace} scaled to {replicas} replicas"
            })
            
        except ApiException as e:
            print(f"Error starting deployment: {e}")
            return jsonify({
                'success': False,
                'message': f"Error starting deployment: {e.reason}"
            }), e.status
            
    except Exception as e:
        print(f"Unexpected error in start_deployment: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

@app.route('/api/deployment/status', methods=['GET'])
def deployment_status_api():
    """Get the current status of a deployment"""
    try:
        namespace = request.args.get('namespace', 'default')
        deployment_name = request.args.get('deployment_name')
        
        if not deployment_name:
            return jsonify({
                'success': False,
                'message': "Deployment name is required"
            }), 400
        
        try:
            # Get deployment info
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            
            # Get deployment status
            current_replicas = deployment.spec.replicas
            available_replicas = deployment.status.available_replicas or 0
            ready_replicas = deployment.status.ready_replicas or 0
            
            # Check if deployment was paused by our system
            paused = False
            original_replicas = None
            if deployment.metadata.annotations:
                if 'k8s-dashboard/paused' in deployment.metadata.annotations:
                    paused = deployment.metadata.annotations['k8s-dashboard/paused'] == 'true'
                if 'k8s-dashboard/original-replicas' in deployment.metadata.annotations:
                    original_replicas = int(deployment.metadata.annotations['k8s-dashboard/original-replicas'])
            
            # Determine status
            if current_replicas == 0:
                status = "Stopped"
            elif available_replicas == current_replicas:
                status = "Running"
            else:
                status = "Scaling"
            
            return jsonify({
                'success': True,
                'deployment': {
                    'name': deployment_name,
                    'namespace': namespace,
                    'status': status,
                    'current_replicas': current_replicas,
                    'available_replicas': available_replicas,
                    'ready_replicas': ready_replicas,
                    'paused': paused,
                    'original_replicas': original_replicas
                }
            })
            
        except ApiException as e:
            print(f"Error getting deployment status: {e}")
            return jsonify({
                'success': False,
                'message': f"Error getting deployment status: {e.reason}"
            }), e.status
            
    except Exception as e:
        print(f"Unexpected error in deployment_status: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
