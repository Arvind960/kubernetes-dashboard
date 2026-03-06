# Kubernetes Dashboard

A lightweight, web-based Kubernetes monitoring dashboard that provides real-time insights into your cluster's resources with Grafana-style metrics visualization.

## Features

### Core Features
- **Real-time Metrics**: Monitor CPU and memory usage for all pods and nodes
- **Resource Overview**: View counts and status of pods, deployments, services, and namespaces
- **Pod Management**: Pause and resume deployments directly from the UI
- **Cluster Health**: Monitor the health status of your cluster components
- **Alerts**: Get notified about potential issues in your cluster
- **Namespace Filtering**: Filter resources by namespace
- **Search Functionality**: Quickly find specific resources
- **Persistent Service**: Runs as a systemd service that continues running even when terminal is closed

### Advanced Metrics Dashboard (NEW)
- **Grafana-Style Interface**: Professional dark theme metrics visualization
- **Real-Time API Request Tracking**: Monitor Submit, Delivered, and Failure counts
- **Live Traffic Monitoring**: Time range filters from 5 seconds to 6 hours
- **Success Rate Calculation**: Real-time success percentage from actual pod logs
- **Interactive Charts**: Chart.js powered visualizations with hover details
- **Clickable Failure Analysis**: Click on failure count to see detailed error descriptions
- **Namespace & Pod Filtering**: View metrics for specific namespaces or individual pods
- **Historical Data Tracking**: 20-point rolling window showing traffic patterns
- **Auto-Refresh**: Updates every 30 seconds with manual refresh option

## Components

- **Backend**: Python Flask server that interacts with the Kubernetes API
- **Frontend**: Responsive web UI built with HTML, CSS, and JavaScript
- **Metrics Collection**: Integration with Kubernetes metrics-server
- **Real-Time Monitoring**: Direct pod log analysis for API request metrics
- **Systemd Service**: For running the dashboard as a persistent service

## Requirements

- Python 3.6+
- Kubernetes cluster with metrics-server installed
- kubectl configured with cluster access
- Modern web browser with JavaScript enabled

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Arvind960/kubernetes-dashboard.git
   cd kubernetes-dashboard
   ```

2. Install the required Python packages:
   ```bash
   pip install flask kubernetes
   ```

3. Set up as a service (recommended):
   ```bash
   sudo cp k8s-dashboard.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable k8s-dashboard.service
   sudo systemctl start k8s-dashboard.service
   ```

4. Or run manually:
   ```bash
   ./start_dashboard.sh
   ```

5. Access the dashboard in your browser:
   ```
   http://localhost:8888
   ```

## Usage

### Basic Operations
- **View Resources**: Navigate through the different sections to view pods, deployments, services, and namespaces
- **Filter Resources**: Use the namespace dropdown to filter resources by namespace
- **Search**: Use the search box to find specific resources
- **Pod Management**: Use the Pause and Resume buttons to control deployments
- **Refresh**: Click the refresh button to update the dashboard with the latest data

### Metrics Dashboard
1. **Navigate to Metrics Tab**: Click on "Metrics" in the sidebar
2. **Select Namespace**: Choose a namespace to monitor (e.g., dsdp for test applications)
3. **Select Time Range**: Choose from:
   - 5 seconds (ultra real-time)
   - 10 seconds
   - 30 seconds
   - 60 seconds
   - 5 minutes
   - 15 minutes
   - 1 hour (default)
   - 6 hours
4. **View Metrics**:
   - **CPU Usage**: Real-time CPU consumption
   - **Memory Usage**: Memory usage with limits
   - **Network I/O**: Receive and transmit rates
   - **API Request Metrics**: Submit, Delivered, and Failure counts with success rate
5. **Analyze Failures**: Click on the failure count to see detailed error descriptions
6. **Filter by Pod**: Select a specific pod to view its individual metrics

## Service Management

- **Start the service**:
  ```bash
  ./start_dashboard.sh
  ```

- **Stop the service**:
  ```bash
  ./stop_dashboard.sh
  ```

- **View logs**:
  ```bash
  tail -f /root/kubernetes-dashboard/logs/k8s_dashboard.log
  ```

- **Check service status**:
  ```bash
  systemctl status k8s-dashboard.service
  ```

## API Endpoints

### Core Endpoints
- `GET /` - Dashboard home page
- `GET /api/data` - Get all cluster resources
- `GET /api/pod-health` - Get pod health status
- `GET /api/hpa` - Get Horizontal Pod Autoscaler information

### Metrics Endpoints (NEW)
- `GET /api/request-metrics/<namespace>` - Get API request metrics
  - Query Parameters:
    - `time_range`: 5s, 10s, 30s, 60s, 5m, 15m, 1h, 6h
    - `pod`: Specific pod name (optional)
  - Returns: Submit count, Delivered count, Failure count, Success rate

## Architecture

The dashboard consists of the following components:

### Backend
- **k8s_dashboard_server_updated.py**: Main Flask server that handles API requests and serves the UI
- **metrics_helper.py**: Helper module for collecting metrics from the Kubernetes metrics-server

### Frontend
- **templates/fixed_template.html**: The dashboard UI template
- **static/css/metrics.css**: Grafana-style dark theme for metrics
- **static/css/pod-health.css**: Pod health monitoring styles
- **static/js/metrics.js**: Metrics dashboard logic with Chart.js integration
- **static/js/pod-health.js**: Pod health monitoring functionality

### Service
- **k8s-dashboard.service**: Systemd service configuration
- **start_dashboard.sh/stop_dashboard.sh**: Convenience scripts for service management

## Documentation

- [METRICS_REDESIGN.md](METRICS_REDESIGN.md) - Detailed metrics dashboard documentation
- [METRICS_UI_WINDOW_FIX.md](METRICS_UI_WINDOW_FIX.md) - UI fixes and improvements
- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide

## Screenshots

![Dashboard Overview](dashboard_overview.png)

## License

MIT License
