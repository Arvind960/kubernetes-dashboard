#!/usr/bin/env python3
"""
Simple Kubernetes Deployment Controller

This is a simplified version of the deployment controller that provides a web UI
for stopping and starting Kubernetes deployments without deleting them.
"""

from flask import Flask, render_template, jsonify, request
from kubernetes import client, config
import traceback
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

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
apps_v1 = client.AppsV1Api()

@app.route('/')
def index():
    return render_template('deployment_control.html')

@app.route('/api/deployment/status', methods=['GET'])
def deployment_status():
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
            
        except client.rest.ApiException as e:
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

@app.route('/api/deployment/stop', methods=['POST'])
def stop_deployment():
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
            
        except client.rest.ApiException as e:
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
def start_deployment():
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
            
        except client.rest.ApiException as e:
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8889))
    app.run(host='0.0.0.0', port=port)
