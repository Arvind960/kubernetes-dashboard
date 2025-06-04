# Kubernetes Dashboard

A lightweight, web-based Kubernetes monitoring dashboard that provides real-time insights into your cluster's resources.

## Features

- **Real-time Metrics**: Monitor CPU and memory usage for all pods and nodes
- **Resource Overview**: View counts and status of pods, deployments, services, and namespaces
- **Pod Management**: Pause and resume deployments directly from the UI
- **Cluster Health**: Monitor the health status of your cluster components
- **Alerts**: Get notified about potential issues in your cluster
- **Namespace Filtering**: Filter resources by namespace
- **Search Functionality**: Quickly find specific resources

## Components

- **Backend**: Python Flask server that interacts with the Kubernetes API
- **Frontend**: Responsive web UI built with HTML, CSS, and JavaScript
- **Metrics Collection**: Integration with Kubernetes metrics-server

## Requirements

- Python 3.6+
- Kubernetes cluster with metrics-server installed
- kubectl configured with cluster access

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/kubernetes-dashboard.git
   cd kubernetes-dashboard
   ```

2. Install the required Python packages:
   ```
   pip install flask kubernetes
   ```

3. Run the dashboard server:
   ```
   python k8s_dashboard_server_updated.py
   ```

4. Access the dashboard in your browser:
   ```
   http://localhost:8888
   ```

## Usage

- **View Resources**: Navigate through the different sections to view pods, deployments, services, and namespaces
- **Filter Resources**: Use the namespace dropdown to filter resources by namespace
- **Search**: Use the search box to find specific resources
- **Pod Management**: Use the Pause and Resume buttons to control deployments
- **Refresh**: Click the refresh button to update the dashboard with the latest data

## Architecture

The dashboard consists of the following components:

- **k8s_dashboard_server_updated.py**: Main Flask server that handles API requests and serves the UI
- **metrics_helper.py**: Helper module for collecting metrics from the Kubernetes metrics-server
- **templates/fixed_template.html**: The dashboard UI template

## Screenshots

![Dashboard Overview](dashboard_overview.png)

## License

MIT License
