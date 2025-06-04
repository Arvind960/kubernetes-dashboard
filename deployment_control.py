#!/usr/bin/env python3
"""
Kubernetes Deployment Controller - Command Line Tool

This script provides a command-line interface for stopping and starting
Kubernetes deployments without deleting them. It works by scaling the
deployment to 0 replicas (to stop) and then back to the original or
specified number (to start).

Usage:
  python deployment_control.py stop <namespace> <deployment-name>
  python deployment_control.py start <namespace> <deployment-name> [<replicas>]
  python deployment_control.py status <namespace> <deployment-name>
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
        
        # Check if deployment was paused by our system
        paused = False
        original_replicas = None
        if deployment.metadata.annotations:
            if 'k8s-dashboard/paused' in deployment.metadata.annotations:
                paused = deployment.metadata.annotations['k8s-dashboard/paused'] == 'true'
            if 'k8s-dashboard/original-replicas' in deployment.metadata.annotations:
                original_replicas = int(deployment.metadata.annotations['k8s-dashboard/original-replicas'])
        
        return {
            'name': deployment_name,
            'namespace': namespace,
            'current_replicas': current_replicas,
            'available_replicas': available_replicas,
            'ready_replicas': ready_replicas,
            'status': status,
            'paused': paused,
            'original_replicas': original_replicas
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
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        current_replicas = deployment.spec.replicas
        
        # Save the current replica count as an annotation
        if not deployment.metadata.annotations:
            deployment.metadata.annotations = {}
        
        deployment.metadata.annotations['k8s-dashboard/original-replicas'] = str(current_replicas)
        deployment.metadata.annotations['k8s-dashboard/paused'] = 'true'
        
        print(f"Stopping deployment {deployment_name} in namespace {namespace}")
        print(f"Current replicas: {current_replicas} (saved for later restoration)")
        
        # Scale the deployment to 0
        deployment.spec.replicas = 0
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
        
        print(f"Deployment {deployment_name} scaled to 0 replicas")
        print("Waiting for pods to terminate...")
        
        # Wait for pods to terminate
        max_wait_time = 60  # Maximum wait time in seconds
        start_time = time.time()
        while True:
            deployment_info = get_deployment_info(apps_v1, namespace, deployment_name)
            if deployment_info['available_replicas'] == 0:
                break
            
            # Check if we've waited too long
            if time.time() - start_time > max_wait_time:
                print("\nWarning: Timed out waiting for all pods to terminate")
                print(f"Current state: {deployment_info['available_replicas']} replicas still available")
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
        
        print(f"Starting deployment {deployment_name} in namespace {namespace}")
        print(f"Scaling to {replicas} replicas")
        
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
    
    if deployment_info['paused']:
        print(f"Paused: Yes (Original replicas: {deployment_info['original_replicas']})")
    else:
        print("Paused: No")

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
