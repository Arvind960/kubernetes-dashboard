import os
import time
import sys
import logging
from flask import Flask, render_template, jsonify, request
from kubernetes import client, config
import datetime
from kubernetes.client.rest import ApiException
import traceback
import subprocess
import json
from metrics_helper import get_pod_metrics, get_node_metrics, format_cpu, format_memory

# Set up logging to file
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'k8s_dashboard.log')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('k8s_dashboard')

# Redirect stdout and stderr to the log file
sys.stdout = open(log_file, 'a', buffering=1)
sys.stderr = open(log_file, 'a', buffering=1)

app = Flask(__name__)

# Load Kubernetes configuration
try:
    config.load_kube_config()
    logger.info("Loaded kube config successfully")
except Exception as e:
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster config successfully")
    except Exception as e:
        logger.error(f"Could not load Kubernetes config: {e}")

# Initialize Kubernetes API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
storage_v1 = client.StorageV1Api()
networking_v1 = client.NetworkingV1Api()

@app.route('/')
def index():
    return render_template('dashboard.html', running_mode='Production Mode')

@app.route('/full-dashboard')
def full_dashboard():
    return render_template('fixed_template.html', running_mode='Production Mode')

@app.route('/api/data')
def get_data():
    try:
        # Get version information
        version_info = {
            "kubernetes_version": "N/A",
            "kubectl_version": "N/A",
            "cri_version": "N/A"
        }
        
        try:
            # Get Kubernetes version
            version_output = subprocess.check_output(["kubectl", "version", "--output=json"], stderr=subprocess.STDOUT)
            version_data = json.loads(version_output)
            
            if "serverVersion" in version_data:
                version_info["kubernetes_version"] = version_data["serverVersion"]["gitVersion"]
            
            if "clientVersion" in version_data:
                version_info["kubectl_version"] = version_data["clientVersion"]["gitVersion"]
            
            # Get CRI version from a node
            try:
                # Use kubectl directly to get the container runtime
                nodes_output = subprocess.check_output(["kubectl", "get", "nodes", "-o", "wide"], stderr=subprocess.STDOUT)
                nodes_lines = nodes_output.decode('utf-8').strip().split('\n')
                
                if len(nodes_lines) > 1:  # Header + at least one node
                    # Get the first node's container runtime
                    node_line = nodes_lines[1]
                    columns = node_line.split()
                    if len(columns) >= 10:
                        # The container runtime is typically the last column
                        version_info["cri_version"] = columns[-1]
                        logger.info(f"Found CRI version: {version_info['cri_version']}")
            except Exception as e:
                logger.error(f"Error getting CRI version: {e}")
                version_info["cri_version"] = "N/A"
        except Exception as e:
            logger.error(f"Error getting version information: {e}")
        
        # Get metrics first
        pod_metrics = get_pod_metrics()
        node_metrics = get_node_metrics()
        
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
            
            # Get node metrics
            node_metric = node_metrics.get(node.metadata.name, {})
            cpu_usage = node_metric.get("cpu", "N/A")
            cpu_percent = node_metric.get("cpu_percent", "N/A")
            memory_usage = node_metric.get("memory", "N/A")
            memory_percent = node_metric.get("memory_percent", "N/A")
            
            nodes.append({
                "name": node.metadata.name,
                "role": role,
                "status": status,
                "ip": node_ip,
                "cpu_allocatable": cpu_allocatable,
                "memory_allocatable": memory_allocatable,
                "cpu_capacity": cpu_capacity,
                "memory_capacity": memory_capacity,
                "cpu_usage": cpu_usage,
                "cpu_percent": cpu_percent,
                "memory_usage": memory_usage,
                "memory_percent": memory_percent,
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
                # Calculate age
                age = calculate_age(creation_timestamp)
            else:
                creation_time = "Unknown"
                age = "Unknown"
            
            # Get pod IP
            pod_ip = pod.status.pod_ip or "N/A"
            
            # Get container statuses
            container_statuses = []
            ready_count = 0
            total_count = 0
            restart_count = 0
            
            if pod.status.container_statuses:
                total_count = len(pod.status.container_statuses)
                for container in pod.status.container_statuses:
                    if container.ready:
                        ready_count += 1
                    restart_count += container.restart_count
                    
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
            
            # Check if the pod's owner is a deployment and if it's paused
            is_paused = False
            if owner_kind == "ReplicaSet":
                try:
                    # Try to find the deployment that owns this replicaset
                    rs = apps_v1.read_namespaced_replica_set(name=owner, namespace=pod.metadata.namespace)
                    if rs.metadata.owner_references:
                        for owner_ref in rs.metadata.owner_references:
                            if owner_ref.kind == "Deployment":
                                deployment_name = owner_ref.name
                                try:
                                    deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=pod.metadata.namespace)
                                    if deployment.spec.paused:
                                        is_paused = True
                                        status = "Paused"  # Override status for paused deployments
                                    owner = deployment_name
                                    owner_kind = "Deployment"
                                except:
                                    pass
                except:
                    pass
            
            # Get pod metrics
            pod_metric_key = f"{pod.metadata.namespace}/{pod.metadata.name}"
            pod_metric = pod_metrics.get(pod_metric_key, {})
            cpu = pod_metric.get("cpu", "0m")
            memory = pod_metric.get("memory", "0Mi")
            
            pods.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": status,
                "ip": pod_ip,
                "node": pod.spec.node_name if pod.spec.node_name else "N/A",
                "creation_time": creation_time,
                "age": age,
                "ready": f"{ready_count}/{total_count}",
                "restarts": restart_count,
                "cpu": cpu,
                "memory": memory,
                "containers": container_statuses,
                "owner": owner,
                "owner_kind": owner_kind,
                "owner_name": owner,  # For consistency with the frontend
                "is_paused": is_paused
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
                # Calculate age
                age = calculate_age(creation_timestamp)
            else:
                creation_time = "Unknown"
                age = "Unknown"
            
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
            
            # For NodePort services, include the NodePort in the external IP
            if service_type == "NodePort" and service.spec.ports and len(service.spec.ports) > 0:
                # Get the first NodePort
                for port in service.spec.ports:
                    if port.node_port:
                        # Get a list of worker node IPs
                        node_list = v1.list_node()
                        worker_ips = []
                        for node in node_list.items:
                            if node.status.conditions:
                                is_ready = any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions)
                                if is_ready:
                                    for address in node.status.addresses:
                                        if address.type == "InternalIP":
                                            worker_ips.append(address.address)
                                            break
                        
                        if worker_ips:
                            # Use the first worker node IP with the NodePort
                            external_ip = f"{worker_ips[0]}:{port.node_port}"
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
                "creation_time": creation_time,
                "age": age
            })
        
        # Get deployments
        deployments = []
        deployment_list = apps_v1.list_deployment_for_all_namespaces(watch=False)
        for deployment in deployment_list.items:
            # Get deployment status
            available_replicas = deployment.status.available_replicas or 0
            replicas = deployment.spec.replicas or 0
            
            if deployment.spec.paused:
                status = "Paused"
            elif available_replicas == replicas:
                status = "Available"
            else:
                status = f"Scaling ({available_replicas}/{replicas})"
            
            # Get deployment creation time
            creation_timestamp = deployment.metadata.creation_timestamp
            
            # Format creation time
            if creation_timestamp:
                creation_time = creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                # Calculate age
                age = calculate_age(creation_timestamp)
            else:
                creation_time = "Unknown"
                age = "Unknown"
            
            deployments.append({
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": replicas,
                "available_replicas": available_replicas,
                "status": status,
                "creation_time": creation_time,
                "age": age,
                "paused": deployment.spec.paused
            })
        
        # Calculate resource usage
        cpu_capacity = 0
        cpu_allocatable = 0
        memory_capacity = 0
        memory_allocatable = 0
        cpu_used = 0
        memory_used = 0
        
        for node in nodes:
            if node["status"] == "Ready":
                try:
                    cpu_capacity += float(node["cpu_capacity"])
                    cpu_allocatable += float(node["cpu_allocatable"])
                    
                    # Convert memory strings to GB
                    memory_capacity += convert_k8s_memory_to_gb(node["memory_capacity"])
                    memory_allocatable += convert_k8s_memory_to_gb(node["memory_allocatable"])
                    
                    # Add used resources
                    if node["cpu_usage"] != "N/A":
                        cpu_str = node["cpu_usage"]
                        if cpu_str.endswith('m'):
                            cpu_used += float(cpu_str[:-1]) / 1000
                        else:
                            cpu_used += float(cpu_str)
                    
                    if node["memory_usage"] != "N/A":
                        memory_str = node["memory_usage"]
                        if memory_str.endswith('Mi'):
                            memory_used += float(memory_str[:-2]) / 1024
                        elif memory_str.endswith('Ki'):
                            memory_used += float(memory_str[:-2]) / (1024 * 1024)
                        elif memory_str.endswith('Gi'):
                            memory_used += float(memory_str[:-2])
                        else:
                            memory_used += float(memory_str) / (1024 * 1024 * 1024)
                except (ValueError, TypeError):
                    pass
        
        # Prepare cluster health data
        cluster_health = {
            "status": "Healthy" if all(node["status"] == "Ready" for node in nodes) else "Warning",
            "components": [
                {"name": "API Server", "status": "Healthy"},
                {"name": "Controller Manager", "status": "Healthy"},
                {"name": "Scheduler", "status": "Healthy"},
                {"name": "etcd", "status": "Healthy"}
            ]
        }
        
        # Check for any not ready nodes
        not_ready_nodes = [node for node in nodes if node["status"] != "Ready"]
        if not_ready_nodes:
            cluster_health["status"] = "Warning"
            cluster_health["components"].append({
                "name": "Nodes", 
                "status": f"Warning: {len(not_ready_nodes)} node(s) not ready - {', '.join([node['name'] for node in not_ready_nodes])}"
            })
        
        # Check for any failed pods
        failed_pods = [pod for pod in pods if pod["status"] not in ["Running", "Succeeded", "Paused"]]
        if failed_pods:
            if len(failed_pods) > 5:
                cluster_health["status"] = "Error"
            else:
                cluster_health["status"] = "Warning"
            cluster_health["components"].append({
                "name": "Pods", 
                "status": f"Warning: {len(failed_pods)} pod(s) not running"
            })
        
        # Generate some alerts based on the cluster state
        alerts = []
        
        # Add alerts for not ready nodes
        for node in not_ready_nodes:
            alerts.append({
                "severity": "warning",
                "type": "node",
                "name": node["name"],
                "message": f"Node {node['name']} is not ready",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Add alerts for failed pods
        for pod in failed_pods[:5]:  # Limit to 5 alerts
            alerts.append({
                "severity": "error" if pod["status"] == "Failed" else "warning",
                "type": "pod",
                "name": pod["name"],
                "namespace": pod["namespace"],
                "message": f"Pod {pod['name']} is in {pod['status']} state",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Count pods by namespace
        namespace_pod_counts = {}
        namespace_service_counts = {}
        
        for pod in pods:
            namespace = pod["namespace"]
            if namespace not in namespace_pod_counts:
                namespace_pod_counts[namespace] = 0
            namespace_pod_counts[namespace] += 1
        
        for service in services:
            namespace = service["namespace"]
            if namespace not in namespace_service_counts:
                namespace_service_counts[namespace] = 0
            namespace_service_counts[namespace] += 1
        
        # Update namespace data with pod and service counts
        for namespace in namespaces:
            namespace_name = namespace["name"]
            namespace["pods"] = namespace_pod_counts.get(namespace_name, 0)
            namespace["services"] = namespace_service_counts.get(namespace_name, 0)
            
            # Calculate age
            creation_time = datetime.datetime.strptime(namespace["creation_time"], "%Y-%m-%d %H:%M:%S")
            namespace["age"] = calculate_age(creation_time)
        
        # Update node data with formatted CPU and memory
        for node in nodes:
            node["cpu"] = f"{node['cpu_allocatable']}/{node['cpu_capacity']}"
            node["memory"] = format_memory(node["memory_allocatable"], node["memory_capacity"])
        
        return jsonify({
            "nodes": nodes,
            "namespaces": namespaces,
            "pods": pods,
            "services": services,
            "deployments": deployments,
            "resource_usage": {
                "cpu": {
                    "used": cpu_used,
                    "total": cpu_capacity
                },
                "memory": {
                    "used": memory_used,
                    "total": memory_capacity
                }
            },
            "cluster_health": cluster_health,
            "alerts": alerts,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version_info": version_info
        })
    except Exception as e:
        logger.error(f"Error getting data: {e}")
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 500

def calculate_age(timestamp):
    """Calculate age from timestamp to now"""
    if not timestamp:
        return "Unknown"
    
    now = datetime.datetime.now(timestamp.tzinfo)
    diff = now - timestamp
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"

def convert_k8s_memory_to_gb(memory_str):
    """Convert Kubernetes memory string to GB"""
    if not memory_str or not isinstance(memory_str, str):
        return 0
    
    try:
        if memory_str.endswith('Ki'):
            return int(memory_str[:-2]) / (1024 * 1024)
        elif memory_str.endswith('Mi'):
            return int(memory_str[:-2]) / 1024
        elif memory_str.endswith('Gi'):
            return int(memory_str[:-2])
        elif memory_str.endswith('Ti'):
            return int(memory_str[:-2]) * 1024
        else:
            return int(memory_str) / (1024 * 1024 * 1024)
    except (ValueError, TypeError):
        return 0

def format_memory(allocatable, capacity):
    """Format memory for display"""
    try:
        if allocatable.endswith('Ki'):
            alloc_mi = int(allocatable[:-2]) / 1024
            alloc_str = f"{alloc_mi:.0f}Mi"
        else:
            alloc_str = allocatable
        
        if capacity.endswith('Ki'):
            cap_mi = int(capacity[:-2]) / 1024
            cap_str = f"{cap_mi:.0f}Mi"
        else:
            cap_str = capacity
        
        return f"{alloc_str}/{cap_str}"
    except (ValueError, TypeError, AttributeError):
        return f"{allocatable}/{capacity}"

@app.route('/api/pods/stop', methods=['POST'])
def stop_pod():
    try:
        data = request.get_json()
        namespace = data.get('namespace')
        name = data.get('name')
        owner_kind = data.get('owner_kind')
        owner_name = data.get('owner_name')
        
        if not namespace or not name:
            return jsonify({
                'success': False,
                'message': "Namespace and pod name are required"
            }), 400
        
        logger.info(f"Pausing pod {name} in namespace {namespace}")
        
        # If the pod is owned by a deployment, pause the deployment
        if owner_kind == "Deployment" and owner_name:
            try:
                logger.info(f"Pod is owned by Deployment {owner_name}, pausing deployment")
                
                # Create a patch to set paused to true
                patch = {"spec": {"paused": True}}
                
                apps_v1.patch_namespaced_deployment(
                    name=owner_name,
                    namespace=namespace,
                    body=patch
                )
                
                return jsonify({
                    'success': True,
                    'message': f"Deployment {owner_name} in namespace {namespace} has been paused"
                })
            except ApiException as e:
                logger.error(f"Error pausing deployment: {e}")
                # Fall back to deleting the pod if there's an error with the deployment
        
        # For standalone pods, we can't actually pause them in Kubernetes
        # So we'll need to delete and recreate them
        try:
            # First, get the pod details so we can recreate it later
            pod = v1.read_namespaced_pod(name=name, namespace=namespace)
            pod_spec = pod.spec
            
            # Store the pod spec in an annotation on a ConfigMap for later retrieval
            config_map_name = f"pod-{name}-backup"
            
            # Convert pod spec to dict for storage
            pod_spec_dict = client.ApiClient().sanitize_for_serialization(pod_spec)
            
            # Create or update ConfigMap with pod spec
            try:
                # Try to get existing ConfigMap
                v1.read_namespaced_config_map(name=config_map_name, namespace=namespace)
                
                # Update existing ConfigMap
                v1.patch_namespaced_config_map(
                    name=config_map_name,
                    namespace=namespace,
                    body={
                        "data": {
                            "pod_spec": str(pod_spec_dict),
                            "pod_name": name
                        }
                    }
                )
            except ApiException as e:
                if e.status == 404:
                    # Create new ConfigMap
                    v1.create_namespaced_config_map(
                        namespace=namespace,
                        body=client.V1ConfigMap(
                            metadata=client.V1ObjectMeta(
                                name=config_map_name
                            ),
                            data={
                                "pod_spec": str(pod_spec_dict),
                                "pod_name": name
                            }
                        )
                    )
                else:
                    raise e
            
            # Now delete the pod
            v1.delete_namespaced_pod(name=name, namespace=namespace)
            
            return jsonify({
                'success': True,
                'message': f"Pod {name} in namespace {namespace} has been paused (stored for later resumption)"
            })
        except ApiException as e:
            if e.status == 404:
                return jsonify({
                    'success': False,
                    'message': f"Pod {name} not found in namespace {namespace}"
                }), 404
            else:
                print(f"Error pausing pod: {e}")
                return jsonify({
                    'success': False,
                    'message': f"Error pausing pod: {e.reason}"
                }), e.status
                
    except Exception as e:
        print(f"Error pausing pod: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Error pausing pod: {str(e)}"
        }), 500

@app.route('/api/pods/start', methods=['POST'])
def start_pod():
    try:
        data = request.get_json()
        namespace = data.get('namespace', 'default')
        name = data.get('name')
        owner_kind = data.get('owner_kind')
        owner_name = data.get('owner_name')
        
        logger.info(f"Resuming pod/deployment: {namespace}/{name}, owner: {owner_kind}/{owner_name}")
        
        # If the pod is owned by a deployment, unpause the deployment
        if owner_kind == "Deployment" and owner_name:
            try:
                logger.info(f"Pod is owned by Deployment {owner_name}, unpausing deployment")
                
                # Create a patch to set paused to false
                patch = {"spec": {"paused": False}}
                
                apps_v1.patch_namespaced_deployment(
                    name=owner_name,
                    namespace=namespace,
                    body=patch
                )
                
                return jsonify({
                    'success': True,
                    'message': f"Deployment {owner_name} in namespace {namespace} has been resumed"
                })
            except ApiException as e:
                logger.error(f"Error unpausing deployment: {e}")
                return jsonify({
                    'success': False,
                    'message': f"Error unpausing deployment: {e.reason}"
                }), e.status
        
        # For standalone pods, check if we have a backup ConfigMap
        config_map_name = f"pod-{name}-backup"
        try:
            # Try to get the ConfigMap with the pod spec
            config_map = v1.read_namespaced_config_map(name=config_map_name, namespace=namespace)
            
            if config_map.data and "pod_spec" in config_map.data:
                # We have the pod spec, recreate the pod
                pod_spec_str = config_map.data["pod_spec"]
                
                # This is a simple approach - in a real system, you'd want to properly deserialize this
                # For now, we'll create a basic pod with the same name
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
                                "image": "nginx:alpine",
                                "ports": [{"containerPort": 80}]
                            }
                        ]
                    }
                }
                
                try:
                    v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
                    
                    # Delete the backup ConfigMap
                    v1.delete_namespaced_config_map(name=config_map_name, namespace=namespace)
                    
                    return jsonify({
                        'success': True,
                        'message': f"Pod {name} in namespace {namespace} has been resumed"
                    })
                except ApiException as create_error:
                    print(f"Error recreating pod: {create_error}")
                    return jsonify({
                        'success': False,
                        'message': f"Error recreating pod: {create_error.reason}"
                    }), create_error.status
            else:
                return jsonify({
                    'success': False,
                    'message': f"No pod spec found for {name} in namespace {namespace}"
                }), 404
        except ApiException as e:
            if e.status == 404:
                # No ConfigMap found, check if pod exists
                try:
                    v1.read_namespaced_pod(name=name, namespace=namespace)
                    return jsonify({
                        'success': False,
                        'message': f"Pod {name} already exists in namespace {namespace}"
                    })
                except ApiException as pod_error:
                    if pod_error.status == 404:
                        # Pod doesn't exist, create a new one
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
                                        "image": "nginx:alpine",
                                        "ports": [{"containerPort": 80}]
                                    }
                                ]
                            }
                        }
                        
                        try:
                            v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
                            logger.info(f"Created pod {name}")
                            return jsonify({
                                'success': True,
                                'message': f"Pod {name} created in namespace {namespace}"
                            })
                        except ApiException as create_error:
                            logger.error(f"Error creating pod: {create_error}")
                            return jsonify({
                                'success': False,
                                'message': f"Error creating pod: {create_error.reason}"
                            }), create_error.status
                    else:
                        logger.error(f"Error checking if pod exists: {pod_error}")
                        return jsonify({
                            'success': False,
                            'message': f"Error checking if pod exists: {pod_error.reason}"
                        }), pod_error.status
            else:
                logger.error(f"Error checking for ConfigMap: {e}")
                return jsonify({
                    'success': False,
                    'message': f"Error checking for ConfigMap: {e.reason}"
                }), e.status
            
    except Exception as e:
        logger.error(f"Unexpected error in start_pod: {e}")
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

# Import pod health monitoring module
from pod_health_monitor import get_pod_health, restart_pod

@app.route('/api/pod-health')
def api_pod_health():
    return get_pod_health(v1, logger)

@app.route('/api/pods/<namespace>/<pod_name>/restart', methods=['POST'])
def api_restart_pod(namespace, pod_name):
    return restart_pod(v1, namespace, pod_name, logger)

if __name__ == '__main__':
    logger.info("Starting Kubernetes Dashboard Server")
    app.run(host='0.0.0.0', port=8888)
@app.route('/api/daemonsets')
def get_daemonsets():
    try:
        daemonsets = []
        ds_list = apps_v1.list_daemon_set_for_all_namespaces()
        
        for ds in ds_list.items:
            daemonsets.append({
                'name': ds.metadata.name,
                'namespace': ds.metadata.namespace,
                'desiredNumberScheduled': ds.status.desired_number_scheduled,
                'currentNumberScheduled': ds.status.current_number_scheduled,
                'numberReady': ds.status.number_ready,
                'numberAvailable': ds.status.number_available if hasattr(ds.status, 'number_available') else 0,
                'numberUnavailable': ds.status.number_unavailable if hasattr(ds.status, 'number_unavailable') else 0
            })
        
        return jsonify(daemonsets)
    except Exception as e:
        logger.error(f"Error getting DaemonSets: {e}")
        return jsonify({'error': str(e)}), 500

# Import pod health monitoring module
from pod_health_monitor import get_pod_health, restart_pod

@app.route('/api/pod-health')
def api_pod_health():
    return get_pod_health(v1, logger)

@app.route('/api/pods/<namespace>/<pod_name>/restart', methods=['POST'])
def api_restart_pod(namespace, pod_name):
    return restart_pod(v1, namespace, pod_name, logger)
