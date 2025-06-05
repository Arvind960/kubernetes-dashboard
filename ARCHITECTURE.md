# Kubernetes Dashboard Architecture

This document describes the architecture and data flow of the Kubernetes Dashboard application.

## System Architecture Overview

The Kubernetes Dashboard is a web-based application that provides real-time monitoring and management capabilities for Kubernetes clusters. It consists of the following components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Web Browser    │◄────┤  Flask Server   │◄────┤  Kubernetes API │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              │
                              ▼
                        ┌─────────────────┐
                        │                 │
                        │  Metrics Server │
                        │                 │
                        └─────────────────┘
```

## Component Details

### 1. Flask Server (`k8s_dashboard_server_updated.py`)

The core of the application is a Python Flask server that:
- Serves the web UI
- Handles API requests from the frontend
- Communicates with the Kubernetes API
- Processes and formats data for display
- Manages pod and deployment operations

Key modules:
- **Flask Application**: Handles HTTP requests and serves HTML templates
- **Kubernetes Client**: Interfaces with the Kubernetes API
- **Metrics Helper**: Collects and processes resource usage metrics

### 2. Metrics Helper (`metrics_helper.py`)

A specialized module that:
- Retrieves CPU and memory metrics from the Kubernetes Metrics Server
- Formats metrics into human-readable values
- Calculates resource utilization percentages

### 3. Pod Actions (`pod_actions.py`)

Handles pod management operations:
- Pausing deployments (scaling to zero)
- Resuming deployments (scaling back to original replicas)
- Managing pod lifecycle

### 4. Frontend UI (`templates/fixed_template.html`)

The dashboard UI built with:
- HTML5
- CSS3 with Bootstrap 5
- JavaScript for dynamic updates
- AJAX for asynchronous data fetching

### 5. Systemd Service (`k8s-dashboard.service`)

Manages the application as a persistent system service:
- Ensures the dashboard runs continuously
- Handles automatic restarts
- Manages logging

## Data Flow

1. **User Interaction**:
   - User accesses the dashboard via web browser
   - Frontend JavaScript code makes API requests to the Flask server

2. **Data Retrieval**:
   - Flask server receives API requests
   - Server queries the Kubernetes API for cluster information
   - Metrics Helper retrieves resource usage data from Metrics Server
   - Data is processed and formatted

3. **Data Display**:
   - Processed data is returned to the frontend as JSON
   - JavaScript updates the UI with the latest information
   - Charts and tables are refreshed

4. **Management Operations**:
   - User initiates actions (e.g., pause/resume deployments)
   - Frontend sends action requests to the Flask server
   - Server executes Kubernetes API calls to perform the requested actions
   - Results are returned to the frontend

## Directory Structure

```
kubernetes-dashboard/
├── k8s_dashboard_server_updated.py  # Main Flask application
├── metrics_helper.py                # Helper for metrics collection
├── pod_actions.py                   # Pod management functions
├── k8s-dashboard.service            # Systemd service definition
├── start_dashboard.sh               # Convenience script to start service
├── stop_dashboard.sh                # Convenience script to stop service
├── requirements.txt                 # Python dependencies
├── logs/                            # Log directory
│   └── k8s_dashboard.log            # Application logs
├── static/                          # Static assets
│   ├── css/                         # CSS stylesheets
│   └── js/                          # JavaScript files
└── templates/                       # HTML templates
    ├── dashboard.html               # Simple dashboard view
    └── fixed_template.html          # Full-featured dashboard view
```

## Communication Protocols

1. **Browser to Flask Server**: HTTP/HTTPS
2. **Flask Server to Kubernetes API**: HTTPS using kubeconfig authentication
3. **Flask Server to Metrics Server**: HTTPS via Kubernetes API

## Security Considerations

- The dashboard uses the same authentication as configured in kubeconfig
- All communication with the Kubernetes API uses TLS encryption
- The dashboard runs with the permissions of the authenticated user
- For production use, consider implementing additional authentication for the web UI

## Scalability

The dashboard is designed for monitoring individual Kubernetes clusters. For multi-cluster monitoring:

- Deploy separate dashboard instances for each cluster
- Consider using dedicated monitoring solutions like Prometheus and Grafana for larger deployments

## Logging and Monitoring

- Application logs are stored in `/root/python-script/logs/k8s_dashboard.log`
- The systemd service provides standard output and error logging
- Log rotation should be configured for production use

## Future Architecture Enhancements

Potential improvements to the architecture:
- Implement WebSockets for real-time updates
- Add user authentication and role-based access control
- Create a backend database for historical metrics
- Develop a plugin system for custom extensions
