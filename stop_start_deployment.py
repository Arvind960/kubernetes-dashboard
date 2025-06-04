#!/usr/bin/env python3
"""
Kubernetes Deployment Controller - Command Line Tool

This script provides a command-line interface for stopping and starting
Kubernetes deployments without deleting them. It works by scaling the
deployment to 0 replicas (to stop) and then back to the original or
specified number (to start).

Usage:
  python stop_start_deployment.py stop <namespace> <deployment-name>
  python stop_start_deployment.py start <namespace> <deployment-name> [<replicas>]
  python stop_start_deployment.py status <namespace> <deployment-name>
"""

import sys
import argparse
import json
import time
import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def load_kubernetes_config():
    """Load Kubernetes configuration from kubeconfig or in-cluster"""
    try:
        config.load_kube_config()
        print("Loaded kube config successfully")
    except Exception as e:
        try:
            config.load_incluster_config()
            print("Loaded in-cluster config successfully")
        except Exception as e:
            print(f"Could not load Kubernetes config: {e}")
            sys.exit(1)

def get_deployment_info(apps_v1, namespace, deployment_name):
    """Get current deployment information including replica count"""
    try:
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        
        current_replicas = deployment.spec.replicas
        available_replicas = deployment.status.available_replicas or 0
        ready_replicas = deployment.status.ready_replicas or 0
        
        status = "Unknown"
        if current_replicas == 0:
            status = "Stopped"
        elif available_replicas == current_replicas:
            status = "Running"
        else:
            status = "Scaling"
        
        return {
            'name': deployment_name,
            'namespace': namespace,
            'current_replicas': current_replicas,
            'available_replicas': available_replicas,
            'ready_replicas': ready_replicas,
            'status': status
        }
    except ApiException as e:
        if e.status == 404:
            print(f"Deployment {deployment_name} not found in namespace {namespace}")
        else:
            print(f"Error getting deployment info: {e}")
        sys.exit(1)

def stop_deployment(apps_v1, namespace, deployment_name):
    """Stop a deployment by scaling it to 0 replicas"""
    try:
        # First, get the current replica count and save it
        deployment_info = get_deployment_info(apps_v1, namespace, deployment_name)
        current_replicas = deployment_info['current_replicas']
        
        # Create directory for storing replica information if it doesn't exist
        os.makedirs('deployment_replicas', exist_ok=True)
        
        # Save the current replica count to a file for later restoration
        replica_info = {
            'deployment_name': deployment_name,
            'namespace': namespace,
            'replicas': current_replicas
        }
        
        with open(f"deployment_replicas/{deployment_name}-{namespace}.json", "w") as f:
            json.dump(replica_info, f)
        
        print(f"Stopping deployment {deployment_name} in namespace {namespace}")
        print(f"Current replicas: {current_replicas} (saved for later restoration)")
        
        # Scale the deployment to 0
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        deployment.spec.replicas = 0
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
        
        print(f"Deployment {deployment_name} scaled to 0 replicas")
        print("Waiting for pods to terminate...")
        
        # Wait for pods to terminate
        while True:
            deployment_info = get_deployment_info(apps_v1, namespace, deployment_name)
            if deployment_info['available_replicas'] == 0:
                break
            print(".", end="", flush=True)
            time.sleep(1)
        
        print("\nDeployment successfully stopped")
        
    except ApiException as e:
        print(f"Error stopping deployment: {e}")
        sys.exit(1)

def start_deployment(apps_v1, namespace, deployment_name, replicas=None):
    """Start a deployment by scaling it back to the original replica count"""
    try:
        # If replicas not specified, try to read from saved file
        if replicas is None:
            try:
                with open(f"deployment_replicas/{deployment_name}-{namespace}.json", "r") as f:
                    replica_info = json.load(f)
                    replicas = replica_info.get('replicas', 1)
            except (FileNotFoundError, json.JSONDecodeError):
                # Default to 1 replica if file not found or invalid
                print("No saved replica count found, defaulting to 1")
                replicas = 1
        
        print(f"Starting deployment {deployment_name} in namespace {namespace}")
        print(f"Scaling to {replicas} replicas")
        
        # Scale the deployment back to the original/specified replica count
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        deployment.spec.replicas = replicas
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
        
        print(f"Deployment {deployment_name} scaled to {replicas} replicas")
        print("Waiting for pods to start...")
        
        # Wait for pods to start
        max_wait_time = 60  # Maximum wait time in seconds
        start_time = time.time()
        while True:
            deployment_info = get_deployment_info(apps_v1, namespace, deployment_name)
            if deployment_info['available_replicas'] == replicas:
                break
            
            # Check if we've waited too long
            if time.time() - start_time > max_wait_time:
                print("\nWarning: Timed out waiting for all pods to become available")
                print(f"Current state: {deployment_info['available_replicas']}/{replicas} replicas available")
                break
                
            print(".", end="", flush=True)
            time.sleep(1)
        
        print("\nDeployment successfully started")
        
    except ApiException as e:
        print(f"Error starting deployment: {e}")
        sys.exit(1)

def show_status(apps_v1, namespace, deployment_name):
    """Show the current status of the deployment"""
    deployment_info = get_deployment_info(apps_v1, namespace, deployment_name)
    
    print(f"Deployment: {deployment_info['name']}")
    print(f"Namespace: {deployment_info['namespace']}")
    print(f"Status: {deployment_info['status']}")
    print(f"Current Replicas: {deployment_info['current_replicas']}")
    print(f"Available Replicas: {deployment_info['available_replicas']}")
    print(f"Ready Replicas: {deployment_info['ready_replicas']}")

def main():
    parser = argparse.ArgumentParser(description="Control Kubernetes deployments - stop and start without deleting")
    parser.add_argument("action", choices=["stop", "start", "status"], 
                        help="Action to perform: stop, start, or check status")
    parser.add_argument("namespace", help="Kubernetes namespace")
    parser.add_argument("deployment", help="Deployment name")
    parser.add_argument("replicas", nargs="?", type=int, 
                        help="Number of replicas when starting (optional)")
    
    args = parser.parse_args()
    
    # Load Kubernetes configuration
    load_kubernetes_config()
    
    # Initialize Kubernetes API client
    apps_v1 = client.AppsV1Api()
    
    if args.action == "stop":
        stop_deployment(apps_v1, args.namespace, args.deployment)
    elif args.action == "start":
        start_deployment(apps_v1, args.namespace, args.deployment, args.replicas)
    elif args.action == "status":
        show_status(apps_v1, args.namespace, args.deployment)

if __name__ == "__main__":
    main()
