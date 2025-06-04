import subprocess
import json
import re

def get_pod_metrics():
    """Get pod metrics from kubectl top pods"""
    try:
        result = subprocess.run(
            ["kubectl", "top", "pods", "--all-namespaces"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:
            return {}
        
        # Skip header line
        pod_metrics = {}
        for line in lines[1:]:
            # Use regex to handle potential spacing issues
            match = re.match(r'(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
            if match:
                namespace = match.group(1)
                name = match.group(2)
                cpu = match.group(3)
                memory = match.group(4)
                
                key = f"{namespace}/{name}"
                pod_metrics[key] = {
                    "cpu": cpu,
                    "memory": memory
                }
                
                # Debug output
                print(f"Added metrics for pod {key}: CPU={cpu}, Memory={memory}")
        
        return pod_metrics
    except Exception as e:
        print(f"Error getting pod metrics: {e}")
        return {}

def get_node_metrics():
    """Get node metrics from kubectl top nodes"""
    try:
        result = subprocess.run(
            ["kubectl", "top", "nodes"],
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:
            return {}
        
        # Skip header line
        node_metrics = {}
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 5:
                name = parts[0]
                cpu = parts[1]
                cpu_percent = parts[2]
                memory = parts[3]
                memory_percent = parts[4]
                
                node_metrics[name] = {
                    "cpu": cpu,
                    "cpu_percent": cpu_percent,
                    "memory": memory,
                    "memory_percent": memory_percent
                }
        
        return node_metrics
    except Exception as e:
        print(f"Error getting node metrics: {e}")
        return {}

def format_cpu(cpu_str):
    """Format CPU string for display"""
    if not cpu_str:
        return "0m"
    
    # Remove any non-numeric characters except decimal point
    if cpu_str.endswith('m'):
        return cpu_str
    
    try:
        # Convert cores to millicores
        cpu_value = float(cpu_str)
        return f"{int(cpu_value * 1000)}m"
    except ValueError:
        return cpu_str

def format_memory(memory_str):
    """Format memory string for display"""
    if not memory_str:
        return "0Mi"
    
    # Handle different formats
    if memory_str.endswith('Mi'):
        return memory_str
    elif memory_str.endswith('Ki'):
        try:
            mem_value = int(memory_str[:-2])
            return f"{mem_value // 1024}Mi"
        except ValueError:
            return memory_str
    elif memory_str.endswith('Gi'):
        try:
            mem_value = float(memory_str[:-2])
            return f"{int(mem_value * 1024)}Mi"
        except ValueError:
            return memory_str
    else:
        try:
            # Assume bytes and convert to Mi
            mem_value = int(memory_str)
            return f"{mem_value // (1024 * 1024)}Mi"
        except ValueError:
            return memory_str
