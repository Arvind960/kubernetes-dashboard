#!/usr/bin/env python3

from flask import Flask, jsonify, request
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import traceback

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
        
        print(f"Stopping pod {name} in namespace {namespace}")
        
        # If the pod is owned by a deployment, scale the deployment to 0
        if owner_kind == "Deployment" and owner_name:
            try:
                print(f"Pod is owned by Deployment {owner_name}, scaling to 0")
                deployment = apps_v1.read_namespaced_deployment(name=owner_name, namespace=namespace)
                
                # Save original replicas in an annotation
                if not deployment.metadata.annotations:
                    deployment.metadata.annotations = {}
                
                deployment.metadata.annotations['k8s-dashboard/original-replicas'] = str(deployment.spec.replicas)
                deployment.spec.replicas = 0
                
                apps_v1.patch_namespaced_deployment(
                    name=owner_name,
                    namespace=namespace,
                    body=deployment
                )
                
                return jsonify({
                    'success': True,
                    'message': f"Deployment {owner_name} in namespace {namespace} scaled to 0 replicas"
                })
            except ApiException as e:
                print(f"Error scaling deployment: {e}")
                # Fall back to deleting the pod
        
        # Delete the pod
        v1.delete_namespaced_pod(name=name, namespace=namespace)
        
        return jsonify({
            'success': True,
            'message': f"Pod {name} in namespace {namespace} has been stopped"
        })
    except Exception as e:
        print(f"Error stopping pod: {e}")
        traceback.print_exc()
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
        owner_kind = data.get('owner_kind')
        owner_name = data.get('owner_name')
        
        print(f"Starting pod/deployment: {namespace}/{name}, owner: {owner_kind}/{owner_name}")
        
        # If the pod is owned by a deployment, scale the deployment back up
        if owner_kind == "Deployment" and owner_name:
            try:
                print(f"Pod is owned by Deployment {owner_name}, scaling back up")
                deployment = apps_v1.read_namespaced_deployment(name=owner_name, namespace=namespace)
                
                # Get original replicas from annotation or default to 1
                replicas = 1
                if deployment.metadata.annotations and 'k8s-dashboard/original-replicas' in deployment.metadata.annotations:
                    replicas = int(deployment.metadata.annotations['k8s-dashboard/original-replicas'])
                
                deployment.spec.replicas = replicas
                
                apps_v1.patch_namespaced_deployment(
                    name=owner_name,
                    namespace=namespace,
                    body=deployment
                )
                
                return jsonify({
                    'success': True,
                    'message': f"Deployment {owner_name} in namespace {namespace} scaled to {replicas} replicas"
                })
            except ApiException as e:
                print(f"Error scaling deployment: {e}")
                return jsonify({
                    'success': False,
                    'message': f"Error scaling deployment: {e.reason}"
                }), e.status
        
        # If it's a standalone pod or we couldn't scale the deployment
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
                                    "image": "nginx:alpine",
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
                        "image": "nginx:alpine",
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
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8891)
