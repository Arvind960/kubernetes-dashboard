import os
import time
from flask import Flask, render_template, jsonify
from kubernetes import client, config
import datetime

app = Flask(__name__)

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
storage_v1 = client.StorageV1Api()
networking_v1 = client.NetworkingV1Api()

@app.route('/')
def index():
    return render_template('fixed_template.html', running_mode='Production Mode')

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
            
            # Get pod status
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
            
            pods.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': status,
                'ready': ready,
                'restarts': restarts,
                'age': age,
                'cpu': cpu_request,
                'memory': memory_request,
                'node': pod.spec.node_name if pod.spec.node_name else "N/A"
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
        
        # Get ReplicaSets
        replicasets = []
        rs_list = apps_v1.list_replica_set_for_all_namespaces(watch=False)
        for rs in rs_list.items:
            replicasets.append({
                'name': rs.metadata.name,
                'namespace': rs.metadata.namespace
            })
        
        # Get StatefulSets
        statefulsets = []
        try:
            ss_list = apps_v1.list_stateful_set_for_all_namespaces(watch=False)
            for ss in ss_list.items:
                statefulsets.append({
                    'name': ss.metadata.name,
                    'namespace': ss.metadata.namespace
                })
        except:
            pass
        
        # Get DaemonSets
        daemonsets = []
        try:
            ds_list = apps_v1.list_daemon_set_for_all_namespaces(watch=False)
            for ds in ds_list.items:
                daemonsets.append({
                    'name': ds.metadata.name,
                    'namespace': ds.metadata.namespace
                })
        except:
            pass
        
        # Get PersistentVolumeClaims
        pvcs = []
        try:
            pvc_list = v1.list_persistent_volume_claim_for_all_namespaces(watch=False)
            for pvc in pvc_list.items:
                pvcs.append({
                    'name': pvc.metadata.name,
                    'namespace': pvc.metadata.namespace
                })
        except:
            pass
        
        # Get Ingresses
        ingresses = []
        try:
            ingress_list = networking_v1.list_ingress_for_all_namespaces(watch=False)
            for ingress in ingress_list.items:
                ingresses.append({
                    'name': ingress.metadata.name,
                    'namespace': ingress.metadata.namespace
                })
        except:
            pass
        
        # Generate alerts based on cluster state
        alerts = []
        
        # Check for node issues
        for node in nodes:
            if node['status'] != 'Ready':
                alerts.append({
                    'severity': 'critical',
                    'type': 'node',
                    'name': node['name'],
                    'message': f"Node {node['name']} is in {node['status']} state",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Check for pod issues
        for pod in pods:
            if pod['status'] == 'Failed':
                alerts.append({
                    'severity': 'error',
                    'type': 'pod',
                    'name': pod['name'],
                    'namespace': pod['namespace'],
                    'message': f"Pod {pod['name']} in namespace {pod['namespace']} has failed",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            elif pod['status'] == 'Pending':
                alerts.append({
                    'severity': 'warning',
                    'type': 'pod',
                    'name': pod['name'],
                    'namespace': pod['namespace'],
                    'message': f"Pod {pod['name']} in namespace {pod['namespace']} has been pending for {pod['age']}",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            elif int(pod['restarts']) > 10:
                alerts.append({
                    'severity': 'warning',
                    'type': 'pod',
                    'name': pod['name'],
                    'namespace': pod['namespace'],
                    'message': f"Pod {pod['name']} in namespace {pod['namespace']} has restarted {pod['restarts']} times",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Check for deployment issues
        for deployment in deployments:
            ready_replicas, total_replicas = map(int, deployment['replicas'].split('/'))
            if deployment['status'] != 'Available':
                alerts.append({
                    'severity': 'warning',
                    'type': 'deployment',
                    'name': deployment['name'],
                    'namespace': deployment['namespace'],
                    'message': f"Deployment {deployment['name']} in namespace {deployment['namespace']} is in {deployment['status']} state",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
            elif ready_replicas < total_replicas:
                alerts.append({
                    'severity': 'warning',
                    'type': 'deployment',
                    'name': deployment['name'],
                    'namespace': deployment['namespace'],
                    'message': f"Deployment {deployment['name']} in namespace {deployment['namespace']} has {ready_replicas}/{total_replicas} ready replicas",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Check for service issues
        for service in services:
            if service['type'] == 'LoadBalancer' and service['external_ip'] == '<pending>':
                alerts.append({
                    'severity': 'warning',
                    'type': 'service',
                    'name': service['name'],
                    'namespace': service['namespace'],
                    'message': f"Service {service['name']} in namespace {service['namespace']} has pending external IP",
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Calculate resource usage
        total_cpu = sum(float(node['cpu']) for node in nodes if node['cpu'] != 'N/A')
        total_memory = sum(float(node['memory'].split()[0]) for node in nodes if node['memory'] != 'N/A')
        
        # Calculate used CPU and memory (this is an approximation since we don't have actual usage metrics)
        used_cpu = 0
        used_memory = 0
        
        for pod in pods:
            if pod['status'] == 'Running':
                # Extract CPU usage
                cpu_str = pod['cpu']
                if 'cores' in cpu_str:
                    try:
                        used_cpu += float(cpu_str.split()[0])
                    except (ValueError, IndexError):
                        pass
                
                # Extract memory usage
                memory_str = pod['memory']
                try:
                    if 'GB' in memory_str:
                        used_memory += float(memory_str.split()[0])
                    elif 'MB' in memory_str:
                        used_memory += float(memory_str.split()[0]) / 1024  # Convert MB to GB
                except (ValueError, IndexError):
                    pass
        
        # Determine overall cluster health
        cluster_health = {'status': 'Healthy', 'components': [
            {'name': 'API Server', 'status': 'Healthy'},
            {'name': 'Controller Manager', 'status': 'Healthy'},
            {'name': 'Scheduler', 'status': 'Healthy'},
            {'name': 'etcd', 'status': 'Healthy'}
        ]}
        
        # Update cluster health based on alerts
        if any(alert['severity'] == 'critical' for alert in alerts):
            cluster_health['status'] = 'Critical'
        elif any(alert['severity'] == 'error' for alert in alerts):
            cluster_health['status'] = 'Error'
        elif any(alert['severity'] == 'warning' for alert in alerts):
            cluster_health['status'] = 'Warning'
        
        # Add node status component
        if any(node['status'] != 'Ready' for node in nodes):
            cluster_health['components'].append({'name': 'Node Status', 'status': 'Warning'})
        else:
            cluster_health['components'].append({'name': 'Node Status', 'status': 'Healthy'})
        
        return jsonify({
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'cluster_health': cluster_health,
            'namespaces': namespaces,
            'nodes': nodes,
            'pods': pods,
            'deployments': deployments,
            'services': services,
            'replicasets': replicasets,
            'statefulsets': statefulsets,
            'daemonsets': daemonsets,
            'pvcs': pvcs,
            'ingresses': ingresses,
            'resource_usage': {
                'cpu': {'used': round(used_cpu, 2), 'total': total_cpu},
                'memory': {'used': round(used_memory, 2), 'total': total_memory}
            },
            'alerts': alerts
        })
    except Exception as e:
        print(f"Error fetching Kubernetes data: {e}")
        return jsonify({
            'error': str(e),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
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
