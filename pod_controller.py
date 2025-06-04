#!/usr/bin/env python3
"""
Kubernetes Pod Controller - Stop and Start Pods managed by Deployments

This script provides functionality to temporarily stop and start pods managed by
Kubernetes Deployments without deleting the Deployment itself.

Usage:
  python pod_controller.py stop <namespace> <deployment-name>
  python pod_controller.py start <namespace> <deployment-name> [<replicas>]
  python pod_controller.py status <namespace> <deployment-name>
"""

import sys
import argparse
import subprocess
import json
import time

def get_deployment_info(namespace, deployment_name):
    """Get current deployment information including replica count"""
    try:
        cmd = f"kubectl get deployment {deployment_name} -n {namespace} -o json"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        deployment_info = json.loads(result.stdout)
        
        current_replicas = deployment_info['spec']['replicas']
        available_replicas = deployment_info.get('status', {}).get('availableReplicas', 0)
        
        return {
            'name': deployment_name,
            'namespace': namespace,
            'current_replicas': current_replicas,
            'available_replicas': available_replicas,
            'status': 'Running' if available_replicas > 0 else 'Stopped'
        }
    except subprocess.CalledProcessError as e:
        print(f"Error getting deployment info: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error parsing deployment info")
        sys.exit(1)

def stop_deployment(namespace, deployment_name):
    """Stop a deployment by scaling it to 0 replicas"""
    try:
        # First, get the current replica count and save it
        deployment_info = get_deployment_info(namespace, deployment_name)
        current_replicas = deployment_info['current_replicas']
        
        # Save the current replica count to a file for later restoration
        with open(f"{deployment_name}-{namespace}-replicas.txt", "w") as f:
            f.write(str(current_replicas))
        
        print(f"Stopping deployment {deployment_name} in namespace {namespace}")
        print(f"Current replicas: {current_replicas} (saved for later restoration)")
        
        # Scale the deployment to 0
        cmd = f"kubectl scale deployment {deployment_name} -n {namespace} --replicas=0"
        subprocess.run(cmd, shell=True, check=True)
        
        print(f"Deployment {deployment_name} scaled to 0 replicas")
        print("Waiting for pods to terminate...")
        
        # Wait for pods to terminate
        while True:
            deployment_info = get_deployment_info(namespace, deployment_name)
            if deployment_info['available_replicas'] == 0:
                break
            print(".", end="", flush=True)
            time.sleep(1)
        
        print("\nDeployment successfully stopped")
        
    except subprocess.CalledProcessError as e:
        print(f"Error stopping deployment: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def start_deployment(namespace, deployment_name, replicas=None):
    """Start a deployment by scaling it back to the original replica count"""
    try:
        # If replicas not specified, try to read from saved file
        if replicas is None:
            try:
                with open(f"{deployment_name}-{namespace}-replicas.txt", "r") as f:
                    replicas = int(f.read().strip())
            except (FileNotFoundError, ValueError):
                # Default to 1 replica if file not found or invalid
                print("No saved replica count found, defaulting to 1")
                replicas = 1
        
        print(f"Starting deployment {deployment_name} in namespace {namespace}")
        print(f"Scaling to {replicas} replicas")
        
        # Scale the deployment back to the original/specified replica count
        cmd = f"kubectl scale deployment {deployment_name} -n {namespace} --replicas={replicas}"
        subprocess.run(cmd, shell=True, check=True)
        
        print(f"Deployment {deployment_name} scaled to {replicas} replicas")
        print("Waiting for pods to start...")
        
        # Wait for pods to start
        while True:
            deployment_info = get_deployment_info(namespace, deployment_name)
            if deployment_info['available_replicas'] == replicas:
                break
            print(".", end="", flush=True)
            time.sleep(1)
        
        print("\nDeployment successfully started")
        
    except subprocess.CalledProcessError as e:
        print(f"Error starting deployment: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def show_status(namespace, deployment_name):
    """Show the current status of the deployment"""
    deployment_info = get_deployment_info(namespace, deployment_name)
    
    print(f"Deployment: {deployment_info['name']}")
    print(f"Namespace: {deployment_info['namespace']}")
    print(f"Status: {deployment_info['status']}")
    print(f"Current Replicas: {deployment_info['current_replicas']}")
    print(f"Available Replicas: {deployment_info['available_replicas']}")

def main():
    parser = argparse.ArgumentParser(description="Control Kubernetes pods managed by Deployments")
    parser.add_argument("action", choices=["stop", "start", "status"], 
                        help="Action to perform: stop, start, or check status")
    parser.add_argument("namespace", help="Kubernetes namespace")
    parser.add_argument("deployment", help="Deployment name")
    parser.add_argument("replicas", nargs="?", type=int, 
                        help="Number of replicas when starting (optional)")
    
    args = parser.parse_args()
    
    if args.action == "stop":
        stop_deployment(args.namespace, args.deployment)
    elif args.action == "start":
        start_deployment(args.namespace, args.deployment, args.replicas)
    elif args.action == "status":
        show_status(args.namespace, args.deployment)

if __name__ == "__main__":
    main()
