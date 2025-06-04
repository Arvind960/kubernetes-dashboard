# Kubernetes Monitoring Dashboard

A lightweight, web-based dashboard for monitoring Kubernetes clusters with a clean interface similar to the official Kubernetes Dashboard.

## Overview

This project provides a simple yet powerful monitoring solution for Kubernetes clusters. It displays real-time information about:

- Cluster health status
- Nodes
- Namespaces
- Pods
- Deployments
- Services
- Resource usage (CPU and memory)
- Alerts for potential issues

The dashboard is built with Python Flask and uses the Kubernetes Python client to interact with the Kubernetes API.

## Features

- **Clean, Modern UI**: Interface inspired by the official Kubernetes Dashboard
- **Real-time Monitoring**: Automatic data refresh
- **Resource Visualization**: CPU and memory usage charts
- **Alert System**: Notifications for cluster issues
- **Multi-resource View**: Monitor all key Kubernetes resources in one place

## Screenshots

![Dashboard Overview](https://github.com/kubernetes/dashboard/blob/master/docs/images/overview.png)

## Prerequisites

- Python 3.6+
- Access to a Kubernetes cluster
- `kubectl` configured with appropriate permissions

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd kubernetes-monitoring-dashboard
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure you have access to your Kubernetes cluster:
   ```
   kubectl get nodes
   ```

## Configuration

The dashboard automatically uses your current Kubernetes context. Make sure your `~/.kube/config` file is properly configured.

For in-cluster deployment, the application will use the service account token.

## Deployment Options

### Local Development

Run the dashboard locally:

```
python k8s_dashboard_server.py
```

Access the dashboard at http://localhost:8888

### Docker Deployment

1. Build the Docker image:
   ```
   docker build -t k8s-monitoring-dashboard:latest .
   ```

2. Run the container:
   ```
   docker run -p 8888:8888 -v ~/.kube:/root/.kube k8s-monitoring-dashboard:latest
   ```

### Kubernetes Deployment

1. Apply the deployment manifest:
   ```
   kubectl apply -f kubernetes/deployment.yaml
   ```

2. Access the dashboard through the created service:
   ```
   kubectl port-forward svc/k8s-monitoring-dashboard 8888:8888
   ```

## Project Structure

```
/
├── k8s_dashboard_server.py     # Main application server
├── requirements.txt            # Python dependencies
├── static/                     # Static assets (CSS, JS)
│   ├── css/
│   ├── js/
│   └── img/
└── templates/                  # HTML templates
    └── fixed_template.html     # Main dashboard template
```

## Security Considerations

- The dashboard requires read access to multiple Kubernetes resources
- For production use, consider implementing authentication
- Use RBAC to limit the service account permissions

## Customization

- Modify `fixed_template.html` to change the UI appearance
- Adjust refresh intervals in the JavaScript code
- Add additional metrics by extending the `/api/data` endpoint

## Troubleshooting

- Check the server logs for API errors
- Verify Kubernetes permissions
- Ensure the correct context is being used

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
