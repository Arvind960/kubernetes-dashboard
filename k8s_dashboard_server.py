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
            cpu = "N/A"
            memory = "N/A"
            if node.status.capacity:
                cpu = node.status.capacity.get("cpu", "N/A")
                memory_kb = int(node.status.capacity.get("memory", "0").replace("Ki", ""))
                memory = f"{memory_kb / 1024 / 1024:.1f} GB"
            
            nodes.append({
                'name': node.metadata.name,
                'status': status,
                'cpu': cpu,
                'memory': memory,
                'role': role
            })
        
        # Get namespaces
        namespaces = []
        namespace_list = v1.list_namespace()
        for ns in namespace_list.items:
            # Count pods in namespace
            pod_count = len(v1.list_namespaced_pod(ns.metadata.name).items)
            
            # Count services in namespace
            service_count = len(v1.list_namespaced_service(ns.metadata.name).items)
            
            # Calculate age
            creation_time = ns.metadata.creation_timestamp
            age = calculate_age(creation_time)
            
            namespaces.append({
                'name': ns.metadata.name,
                'status': ns.status.phase,
                'age': age,
                'pods': pod_count,
                'services': service_count
            })
        
        # Get pods
        pods = []
        pod_list = v1.list_pod_for_all_namespaces(watch=False)
        for pod in pod_list.items:
            # Calculate pod age
            creation_time = pod.metadata.creation_timestamp
            age = calculate_age(creation_time)
            
            # Get pod status - check for our custom paused label
            if pod.metadata.labels and 'k8s-dashboard/status' in pod.metadata.labels:
                if pod.metadata.labels['k8s-dashboard/status'] == 'paused':
                    status = "Paused"
                else:
                    status = pod.metadata.labels['k8s-dashboard/status']
            else:
                status = pod.status.phase
            
            # Get ready status
            containers_ready = 0
            containers_total = len(pod.spec.containers)
            for container_status in pod.status.container_statuses if pod.status.container_statuses else []:
                if container_status.ready:
                    containers_ready += 1
            ready = f"{containers_ready}/{containers_total}"
            
            # Get restart count
            restarts = 0
            for container_status in pod.status.container_statuses if pod.status.container_statuses else []:
                restarts += container_status.restart_count
            
            # Get resource requests
            cpu_request = "N/A"
            memory_request = "N/A"
            for container in pod.spec.containers:
                if container.resources and container.resources.requests:
                    if container.resources.requests.get("cpu"):
                        cpu_value = container.resources.requests["cpu"]
                        if cpu_value.endswith("m"):
                            cpu_cores = float(cpu_value[:-1]) / 1000
                            cpu_request = f"{cpu_cores} cores"
                        else:
                            cpu_request = f"{cpu_value} cores"
                    if container.resources.requests.get("memory"):
                        memory_value = container.resources.requests["memory"]
                        if memory_value.endswith("Mi"):
                            memory_mb = int(memory_value[:-2])
                            memory_request = f"{memory_mb} MB"
                        elif memory_value.endswith("Gi"):
                            memory_gb = float(memory_value[:-2])
                            memory_request = f"{memory_gb} GB"
                        else:
                            memory_request = memory_value
            
            # Find owner reference to determine if pod is part of a deployment
            owner_references = pod.metadata.owner_references
            owner_kind = None
            owner_name = None
            if owner_references:
                for ref in owner_references:
                    if ref.controller:
                        owner_kind = ref.kind
                        owner_name = ref.name
                        break
            
            pods.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': status,
                'ready': ready,
                'restarts': restarts,
                'age': age,
                'cpu': cpu_request,
                'memory': memory_request,
                'node': pod.spec.node_name if pod.spec.node_name else "N/A",
                'owner_kind': owner_kind,
                'owner_name': owner_name
            })
        
        # Get deployments
        deployments = []
        deployment_list = apps_v1.list_deployment_for_all_namespaces(watch=False)
        for deployment in deployment_list.items:
            # Calculate deployment age
            creation_time = deployment.metadata.creation_timestamp
            age = calculate_age(creation_time)
            
            # Get deployment status
            status = "Unknown"
            if deployment.status.conditions:
                for condition in deployment.status.conditions:
                    if condition.type == "Available" and condition.status == "True":
                        status = "Available"
                    elif condition.type == "Progressing" and condition.status == "True":
                        status = "Progressing"
                    elif condition.type == "ReplicaFailure" and condition.status == "True":
                        status = "Failed"
            
            # Check if deployment is paused by our dashboard
            if deployment.metadata.annotations and 'k8s-dashboard/paused' in deployment.metadata.annotations:
                status = "Paused"
            
            # Get replicas
            replicas = f"{deployment.status.ready_replicas or 0}/{deployment.spec.replicas}"
            
            deployments.append({
                'name': deployment.metadata.name,
                'namespace': deployment.metadata.namespace,
                'replicas': replicas,
                'age': age,
                'status': status
            })
        
        # Get services
        services = []
        service_list = v1.list_service_for_all_namespaces(watch=False)
        for service in service_list.items:
            # Calculate service age
            creation_time = service.metadata.creation_timestamp
            age = calculate_age(creation_time)
            
            # Get external IP
            external_ip = "None"
            if service.status.load_balancer.ingress:
                external_ip = service.status.load_balancer.ingress[0].ip or service.status.load_balancer.ingress[0].hostname or "<pending>"
            
            # Get ports
            ports = []
            for port in service.spec.ports:
                port_str = f"{port.port}"
                if port.node_port:
                    port_str += f":{port.node_port}"
                if port.protocol:
                    port_str += f"/{port.protocol}"
                ports.append(port_str)
            
            services.append({
                'name': service.metadata.name,
                'namespace': service.metadata.namespace,
                'type': service.spec.type,
                'cluster_ip': service.spec.cluster_ip,
                'external_ip': external_ip,
                'ports': ", ".join(ports)
            })
        
        # Calculate cluster health
        cluster_health = {
            'status': 'Healthy',
            'components': []
        }
        
        # Check if any node is not ready
        for node in nodes:
            if node['status'] != 'Ready':
                cluster_health['status'] = 'Warning'
                cluster_health['components'].append({
                    'name': f"Node {node['name']}",
                    'status': 'Warning'
                })
        
        # Check if any pod is not running
        for pod in pods:
            if pod['status'] != 'Running' and pod['status'] != 'Stopped':
                cluster_health['status'] = 'Warning'
                cluster_health['components'].append({
                    'name': f"Pod {pod['name']} in {pod['namespace']}",
                    'status': 'Warning'
                })
        
        # Calculate resource usage
        total_cpu = 0
        total_memory = 0
        used_cpu = 0
        used_memory = 0
        
        for node in nodes:
            try:
                if node['cpu'] != 'N/A':
                    total_cpu += float(node['cpu'])
                if node['memory'] != 'N/A':
                    # Extract the number from strings like "3.8 GB"
                    memory_str = node['memory']
                    if 'GB' in memory_str:
                        total_memory += float(memory_str.split(' ')[0])
            except (ValueError, TypeError):
                pass
        
        # Estimate usage (in a real app, you'd get actual metrics)
        used_cpu = total_cpu * 0.4  # Assume 40% CPU usage
        used_memory = total_memory * 0.5  # Assume 50% memory usage
        
        resource_usage = {
            'cpu': {
                'used': used_cpu,
                'total': total_cpu
            },
            'memory': {
                'used': used_memory,
                'total': total_memory
            }
        }
        
        return jsonify({
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'nodes': nodes,
            'namespaces': namespaces,
            'pods': pods,
            'deployments': deployments,
            'services': services,
            'cluster_health': cluster_health,
            'resource_usage': resource_usage
        })
    except Exception as e:
        print(f"Error fetching Kubernetes data: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.route('/api/pods/start', methods=['POST'])
def start_pod():
    try:
        print("Start pod endpoint called")
        data = request.json
        print(f"Request data: {data}")
        
        namespace = data.get('namespace')
        name = data.get('name')
        owner_kind = data.get('owner_kind')
        owner_name = data.get('owner_name')
        
        if not namespace:
            print("Missing namespace")
            return jsonify({'success': False, 'message': 'Namespace is required'}), 400
        
        # If this is a deployment-managed pod, check if it was paused by our dashboard
        if owner_kind and owner_kind.lower() == 'replicaset' and owner_name:
            # Find the deployment that owns this ReplicaSet
            try:
                rs = apps_v1.read_namespaced_replica_set(owner_name, namespace)
                for owner_ref in rs.metadata.owner_references or []:
                    if owner_ref.kind == 'Deployment':
                        deployment_name = owner_ref.name
                        print(f"Found parent deployment: {deployment_name}")
                        
                        # Get the deployment
                        deployment = apps_v1.read_namespaced_deployment(
                            name=deployment_name,
                            namespace=namespace
                        )
                        
                        # Check if it was paused by our dashboard
                        if deployment.metadata.annotations and 'k8s-dashboard/paused' in deployment.metadata.annotations:
                            # Get original replicas count
                            original_replicas = 1  # Default to 1 if not found
                            if 'k8s-dashboard/original-replicas' in deployment.metadata.annotations:
                                try:
                                    original_replicas = int(deployment.metadata.annotations['k8s-dashboard/original-replicas'])
                                except ValueError:
                                    print(f"Invalid original replicas value: {deployment.metadata.annotations['k8s-dashboard/original-replicas']}")
                            
                            # Remove our annotations
                            annotations = deployment.metadata.annotations.copy()
                            if 'k8s-dashboard/paused' in annotations:
                                del annotations['k8s-dashboard/paused']
                            if 'k8s-dashboard/original-replicas' in annotations:
                                del annotations['k8s-dashboard/original-replicas']
                            
                            # Update annotations
                            apps_v1.patch_namespaced_deployment(
                                name=deployment_name,
                                namespace=namespace,
                                body={
                                    "metadata": {
                                        "annotations": annotations
                                    }
                                }
                            )
                            
                            # Scale back to original replicas
                            patch = {"spec": {"replicas": original_replicas}}
                            apps_v1.patch_namespaced_deployment(
                                name=deployment_name,
                                namespace=namespace,
                                body=patch
                            )
                            
                            print(f"Resumed deployment {deployment_name} to {original_replicas} replicas")
                            return jsonify({
                                'success': True,
                                'message': f"Deployment {deployment_name} in namespace {namespace} resumed with {original_replicas} replicas"
                            })
                        else:
                            # Regular deployment, just scale to 1
                            patch = {"spec": {"replicas": 1}}
                            apps_v1.patch_namespaced_deployment(
                                name=deployment_name,
                                namespace=namespace,
                                body=patch
                            )
                            
                            print(f"Scaled deployment {deployment_name} to 1 replica")
                            return jsonify({
                                'success': True,
                                'message': f"Deployment {deployment_name} in namespace {namespace} scaled to 1 replica"
                            })
            except ApiException as e:
                print(f"Error finding parent deployment: {e}")
        
        # If we have a specific pod name, try to resume it if it was paused
        if name:
            try:
                # Try to get the pod first to see if it exists
                pod = v1.read_namespaced_pod(name=name, namespace=namespace)
                
                # If pod exists and has our paused label, resume it
                if pod.metadata.labels and 'k8s-dashboard/status' in pod.metadata.labels and pod.metadata.labels['k8s-dashboard/status'] == 'paused':
                    # Remove the paused label
                    labels = pod.metadata.labels.copy()
                    del labels['k8s-dashboard/status']
                    
                    # Update the pod
                    v1.patch_namespaced_pod(
                        name=name,
                        namespace=namespace,
                        body={"metadata": {"labels": labels}}
                    )
                    
                    print(f"Removed paused label from pod {name}")
                    
                    # Remove the paused annotation if it exists
                    if pod.metadata.annotations and 'k8s-dashboard/paused' in pod.metadata.annotations:
                        annotations = pod.metadata.annotations.copy()
                        del annotations['k8s-dashboard/paused']
                        
                        v1.patch_namespaced_pod(
                            name=name,
                            namespace=namespace,
                            body={"metadata": {"annotations": annotations}}
                        )
                    
                    # Get all container names in the pod
                    container_names = [container.name for container in pod.spec.containers]
                    
                    for container_name in container_names:
                        try:
                            # Execute the kill command with SIGCONT (18) to resume the processes
                            exec_command = [
                                "/bin/sh", 
                                "-c", 
                                "kill -CONT 1"  # In container, PID 1 is the main process
                            ]
                            
                            # Execute the command in the container
                            v1.connect_get_namespaced_pod_exec(
                                name=name,
                                namespace=namespace,
                                container=container_name,
                                command=exec_command,
                                stderr=True,
                                stdin=False,
                                stdout=True,
                                tty=False
                            )
                            
                            print(f"Sent SIGCONT to container {container_name} in pod {name}")
                        except ApiException as e:
                            print(f"Error sending SIGCONT to container {container_name}: {e}")
                            # Continue with other containers even if one fails
                    
                    return jsonify({
                        'success': True,
                        'message': f"Pod {name} in namespace {namespace} resumed successfully"
                    })
                else:
                    print(f"Pod {name} already exists but is not in paused state")
                    return jsonify({
                        'success': False,
                        'message': f"Pod {name} already exists in namespace {namespace} but is not paused"
                    })
            except ApiException as e:
                if e.status == 404:
                    # Pod doesn't exist, we can create it
                    # This is a simplified version - in a real scenario, you'd need a pod template
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
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

@app.route('/api/pods/stop', methods=['POST'])
def stop_pod():
    try:
        print("Stop pod endpoint called")
        data = request.json
        print(f"Request data: {data}")
        
        namespace = data.get('namespace')
        name = data.get('name')
        owner_kind = data.get('owner_kind')
        owner_name = data.get('owner_name')
        
        if not namespace or not name:
            print("Missing namespace or name")
            return jsonify({'success': False, 'message': 'Namespace and pod name are required'}), 400
        
        print(f"Attempting to pause pod {name} in namespace {namespace}")
        
        # If this is a deployment-managed pod, pause the deployment instead of scaling to 0
        if owner_kind and owner_kind.lower() == 'replicaset' and owner_name:
            # Find the deployment that owns this ReplicaSet
            try:
                rs = apps_v1.read_namespaced_replica_set(owner_name, namespace)
                for owner_ref in rs.metadata.owner_references or []:
                    if owner_ref.kind == 'Deployment':
                        deployment_name = owner_ref.name
                        print(f"Found parent deployment: {deployment_name}")
                        
                        # Get current deployment
                        deployment = apps_v1.read_namespaced_deployment(
                            name=deployment_name,
                            namespace=namespace
                        )
                        
                        # Store original replicas count in an annotation for later restoration
                        original_replicas = deployment.spec.replicas
                        
                        # Add annotations to store state
                        if not deployment.metadata.annotations:
                            deployment.metadata.annotations = {}
                        
                        deployment.metadata.annotations['k8s-dashboard/paused'] = 'true'
                        deployment.metadata.annotations['k8s-dashboard/original-replicas'] = str(original_replicas)
                        
                        # Update the deployment with annotations
                        apps_v1.patch_namespaced_deployment(
                            name=deployment_name,
                            namespace=namespace,
                            body={
                                "metadata": {
                                    "annotations": deployment.metadata.annotations
                                }
                            }
                        )
                        
                        # Now scale to 0 but keep the deployment
                        patch = {"spec": {"replicas": 0}}
                        apps_v1.patch_namespaced_deployment(
                            name=deployment_name,
                            namespace=namespace,
                            body=patch
                        )
                        
                        print(f"Paused deployment {deployment_name} (scaled to 0 replicas, original: {original_replicas})")
                        return jsonify({
                            'success': True,
                            'message': f"Deployment {deployment_name} in namespace {namespace} paused (pods paused)"
                        })
            except ApiException as e:
                print(f"Error handling deployment: {e}")
        
        # For standalone pods, we'll add a label to mark it as paused
        try:
            # First, check if the pod exists
            pod = v1.read_namespaced_pod(name=name, namespace=namespace)
            
            # We'll add a label to mark it as paused
            if not pod.metadata.labels:
                pod.metadata.labels = {}
            
            pod.metadata.labels['k8s-dashboard/status'] = 'paused'
            
            # Update the pod with the new label
            v1.patch_namespaced_pod(
                name=name,
                namespace=namespace,
                body={"metadata": {"labels": pod.metadata.labels}}
            )
            
            # Store the pod spec for later resumption
            if not pod.metadata.annotations:
                pod.metadata.annotations = {}
                
            # Add annotation to indicate this pod is paused by our dashboard
            pod.metadata.annotations['k8s-dashboard/paused'] = 'true'
            
            # Update the pod with the new annotations
            v1.patch_namespaced_pod(
                name=name,
                namespace=namespace,
                body={"metadata": {"annotations": pod.metadata.annotations}}
            )
            
            # For actual pausing, we'll use the Kubernetes API to send a SIGSTOP signal to the containers
            # This will pause the processes without terminating them
            
            # Get all container names in the pod
            container_names = [container.name for container in pod.spec.containers]
            
            for container_name in container_names:
                try:
                    # Execute the kill command with SIGSTOP (19) to pause the processes
                    exec_command = [
                        "/bin/sh", 
                        "-c", 
                        "kill -STOP 1"  # In container, PID 1 is the main process
                    ]
                    
                    # Execute the command in the container
                    v1.connect_get_namespaced_pod_exec(
                        name=name,
                        namespace=namespace,
                        container=container_name,
                        command=exec_command,
                        stderr=True,
                        stdin=False,
                        stdout=True,
                        tty=False
                    )
                    
                    print(f"Sent SIGSTOP to container {container_name} in pod {name}")
                except ApiException as e:
                    print(f"Error sending SIGSTOP to container {container_name}: {e}")
                    # Continue with other containers even if one fails
            
            print(f"Pod {name} marked as paused")
            
            return jsonify({
                'success': True,
                'message': f"Pod {name} in namespace {namespace} paused successfully"
            })
            
        except ApiException as e:
            print(f"API Exception when pausing pod: {e}")
            if e.status == 404:
                return jsonify({
                    'success': False,
                    'message': f"Pod {name} not found in namespace {namespace}"
                }), 404
            elif e.status == 403:
                return jsonify({
                    'success': False,
                    'message': f"Permission denied: You don't have permission to pause pod {name}"
                }), 403
            else:
                return jsonify({
                    'success': False,
                    'message': f"API Error: {e.reason}"
                }), e.status
    except Exception as e:
        print(f"Unexpected error in stop_pod: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

def calculate_age(creation_time):
    """Calculate age of a resource in human-readable format"""
    if not creation_time:
        return "Unknown"
    
    now = datetime.datetime.now(creation_time.tzinfo)
    diff = now - creation_time
    
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)

# New endpoints for stopping and starting deployments
@app.route("/api/deployment/stop", methods=["POST"])
def stop_deployment_api():
def stop_deployment_api():
    """Stop a deployment by scaling it to 0 replicas"""
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
            
            # Save the current replica count to a file for later restoration
            replica_info = {
                'deployment_name': deployment_name,
                'namespace': namespace,
                'replicas': current_replicas
            }
            
            # Create a directory for storing replica information if it doesn't exist
            os.makedirs('deployment_replicas', exist_ok=True)
            
            with open(f"deployment_replicas/{deployment_name}-{namespace}.json", "w") as f:
                json.dump(replica_info, f)
            
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

@app.route("/api/deployment/start", methods=["POST"])
def start_deployment_api():
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
        
        # If replicas not specified, try to read from saved file
        if replicas is None:
            try:
                with open(f"deployment_replicas/{deployment_name}-{namespace}.json", "r") as f:
                    replica_info = json.load(f)
                    replicas = replica_info.get('replicas', 1)
            except (FileNotFoundError, json.JSONDecodeError):
                # Default to 1 replica if file not found or invalid
                replicas = 1
                print(f"No saved replica count found for {deployment_name}, defaulting to 1")
        
        try:
            # Get current deployment
            deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            
            # Scale the deployment back to the original/specified replica count
            deployment.spec.replicas = replicas
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

@app.route("/api/deployment/status", methods=["GET"])
def deployment_status_api():
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
                    'ready_replicas': ready_replicas
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

@app.route('/deployment-control')
def deployment_control():
    """Render the deployment control page"""
    return render_template('deployment_control.html')

@app.route("/api/deployment/stop", methods=["POST"])
def stop_deployment_api():
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

@app.route("/api/deployment/start", methods=["POST"])
def start_deployment_api():
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

@app.route("/api/deployment/status", methods=["GET"])
def deployment_status_api():
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
