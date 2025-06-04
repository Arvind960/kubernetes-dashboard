# Kubernetes Deployment Controller

This tool provides a way to stop and start Kubernetes deployments without deleting them. It works by scaling deployments to 0 replicas (to stop) and then back to their original replica count (to start).

## Web Interface

Access the web interface at: http://192.168.47.138:8889

The web interface provides a simple UI to:
- Check the status of deployments
- Stop deployments (scale to 0 replicas)
- Start deployments (scale back to original or custom replica count)

## Command Line Tool

You can also use the command line tool:

```bash
# Check deployment status
python3 /root/python-script/deployment_control.py status <namespace> <deployment-name>

# Stop a deployment
python3 /root/python-script/deployment_control.py stop <namespace> <deployment-name>

# Start a deployment (with original replicas)
python3 /root/python-script/deployment_control.py start <namespace> <deployment-name>

# Start a deployment (with custom replicas)
python3 /root/python-script/deployment_control.py start <namespace> <deployment-name> <replicas>
```

Example:
```bash
# Check status
python3 /root/python-script/deployment_control.py status nginx-demo nginx-deployment

# Stop deployment
python3 /root/python-script/deployment_control.py stop nginx-demo nginx-deployment

# Start deployment
python3 /root/python-script/deployment_control.py start nginx-demo nginx-deployment
```

## How It Works

1. **Stopping a Deployment**:
   - Gets the current replica count and saves it as an annotation
   - Scales the deployment to 0 replicas
   - Marks the deployment as paused with an annotation

2. **Starting a Deployment**:
   - Reads the original replica count from the annotation
   - Scales the deployment back to that number (or a custom number)
   - Marks the deployment as no longer paused

This approach preserves the deployment configuration while temporarily stopping the pods.
