# Kubernetes Dashboard Architecture

This document describes the architecture and data flow of the Kubernetes Dashboard application with advanced metrics monitoring capabilities.

## System Architecture Overview

The Kubernetes Dashboard is a web-based application that provides real-time monitoring and management capabilities for Kubernetes clusters with Grafana-style metrics visualization. It consists of the following components:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Web Browser    │◄────┤  Flask Server   │◄────┤  Kubernetes API │
│  (Chart.js)     │     │  (Python)       │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                         │
        │                       │                         │
        │                       ▼                         ▼
        │               ┌─────────────────┐     ┌─────────────────┐
        │               │                 │     │                 │
        └──────────────►│  Metrics Server │     │   Pod Logs      │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

## Component Details

### 1. Flask Server (`k8s_dashboard_server_updated.py`)

The core of the application is a Python Flask server that:
- Serves the web UI
- Handles API requests from the frontend
- Communicates with the Kubernetes API
- Processes and formats data for display
- Manages pod and deployment operations
- **NEW**: Fetches and analyzes pod logs for API request metrics
- **NEW**: Provides time-range filtered metrics data

Key modules:
- **Flask Application**: Handles HTTP requests and serves HTML templates
- **Kubernetes Client**: Interfaces with the Kubernetes API
- **Metrics Helper**: Collects and processes resource usage metrics
- **Pod Health Monitor**: Detects and reports pod health issues
- **Request Metrics Analyzer**: Parses pod logs for API request tracking

### 2. Metrics Helper (`metrics_helper.py`)

A specialized module that:
- Retrieves CPU and memory metrics from the Kubernetes Metrics Server
- Formats metrics into human-readable values
- Calculates resource utilization percentages

### 3. Pod Health Monitor (`pod_health_monitor.py`)

Monitors pod health and detects common issues:
- Identifies pods in "hang" states
- Detects application deadlocks
- Monitors for resource starvation
- Identifies crash loops and stuck init containers
- Detects volume mount issues
- Provides troubleshooting guidance

### 4. Frontend UI

#### Main Dashboard (`templates/fixed_template.html`)
The dashboard UI built with:
- HTML5
- CSS3 with Bootstrap 5
- JavaScript for dynamic updates
- AJAX for asynchronous data fetching
- **NEW**: Chart.js for metrics visualization
- Modal dialogs for detailed views

#### Metrics Dashboard (NEW)
- **CSS**: `static/css/metrics.css` - Grafana-inspired dark theme
- **JavaScript**: `static/js/metrics.js` - Real-time metrics logic
- **Features**:
  - Live API request tracking
  - Time-range filtering (5s to 6h)
  - Historical data visualization
  - Interactive charts with Chart.js
  - Namespace and pod filtering

#### Pod Health Monitoring
- **CSS**: `static/css/pod-health.css` - Health monitoring styles
- **JavaScript**: `static/js/pod-health.js` - Health monitoring logic

### 5. Systemd Service (`k8s-dashboard.service`)

Manages the application as a persistent system service:
- Ensures the dashboard runs continuously
- Handles automatic restarts
- Manages logging

## Data Flow

### 1. User Interaction
- User accesses the dashboard via web browser
- Frontend JavaScript code makes API requests to the Flask server
- **NEW**: Metrics dashboard fetches real-time data every 30 seconds

### 2. Data Retrieval

#### Core Resources
- Flask server receives API requests
- Server queries the Kubernetes API for cluster information
- Metrics Helper retrieves resource usage data from Metrics Server
- Pod Health Monitor analyzes pod states for potential issues
- Data is processed and formatted

#### Metrics Dashboard (NEW)
- User selects namespace and time range
- Frontend requests metrics via `/api/request-metrics/<namespace>`
- Backend fetches pod logs using Kubernetes API
- Logs are parsed for HTTP requests (GET, POST, etc.)
- Counts are calculated: Submit, Delivered (200), Failure (404, 500)
- Success rate is computed: (Delivered / Submit) × 100
- Data is returned as JSON with time range metadata

### 3. Data Display

#### Core Dashboard
- Processed data is returned to the frontend as JSON
- JavaScript updates the UI with the latest information
- Tables and status cards are refreshed
- Health metrics are updated

#### Metrics Dashboard (NEW)
- Chart.js renders four interactive charts:
  - CPU Usage (line chart)
  - Memory Usage (line chart with limit)
  - Network I/O (dual-line chart)
  - API Request Metrics (triple-line chart)
- Historical data stored in browser (20-point rolling window)
- Time labels synchronized across all charts
- Statistics displayed: min, max, avg, success rate

### 4. Management Operations
- User initiates actions (e.g., restart pods, view details)
- Frontend sends action requests to the Flask server
- Server executes Kubernetes API calls to perform the requested actions
- Results are returned to the frontend
- **NEW**: Click on failure count to view detailed error descriptions

## Directory Structure

```
kubernetes-dashboard/
├── k8s_dashboard_server_updated.py  # Main Flask application
├── metrics_helper.py                # Helper for metrics collection
├── pod_health_monitor.py            # Pod health monitoring functions
├── k8s-dashboard.service            # Systemd service definition
├── start_dashboard.sh               # Convenience script to start service
├── stop_dashboard.sh                # Convenience script to stop service
├── requirements.txt                 # Python dependencies
├── README.md                        # Project overview and features
├── INSTALLATION.md                  # Installation instructions
├── ARCHITECTURE.md                  # Architecture documentation (this file)
├── METRICS_REDESIGN.md              # Metrics dashboard documentation
├── METRICS_UI_WINDOW_FIX.md         # UI fixes documentation
├── logs/                            # Log directory
│   └── k8s_dashboard.log            # Application logs
├── static/                          # Static assets
│   ├── css/                         # CSS stylesheets
│   │   ├── styles.css               # Main stylesheet
│   │   ├── dashboard.css            # Dashboard styles
│   │   ├── pod-health.css           # Pod health monitoring styles
│   │   └── metrics.css              # NEW: Grafana-style metrics theme
│   ├── js/                          # JavaScript files
│   │   ├── pod-health.js            # Pod health monitoring scripts
│   │   ├── pod-actions.js           # Pod action handlers
│   │   ├── dashboard.js             # Dashboard logic
│   │   └── metrics.js               # NEW: Metrics dashboard logic
│   └── img/                         # Images and icons
│       ├── k8s-logo.svg             # Kubernetes logo
│       ├── pod.svg                  # Pod icon
│       ├── deployment.svg           # Deployment icon
│       ├── service.svg              # Service icon
│       └── node.svg                 # Node icon
└── templates/                       # HTML templates
    ├── dashboard.html               # Simple dashboard view
    ├── fixed_template.html          # Full-featured dashboard view
    └── chatbot.html                 # AI chatbot interface
```

## API Endpoints

The dashboard provides several API endpoints:

### Core Endpoints
1. **`GET /`**: Main dashboard page
2. **`GET /api/data`**: Returns all cluster data including nodes, pods, services, deployments, namespaces
3. **`GET /api/pod-health`**: Returns health data for all pods with potential issues
4. **`POST /api/pods/<namespace>/<pod_name>/restart`**: Restarts a specific pod
5. **`GET /api/daemonsets`**: Returns information about DaemonSets in the cluster
6. **`GET /api/hpa`**: Returns Horizontal Pod Autoscaler information
7. **`GET /api/pod-communication`**: Returns pod communication topology

### Metrics Endpoints (NEW)
8. **`GET /api/request-metrics/<namespace>`**: Returns API request metrics
   - **Query Parameters**:
     - `time_range`: Time window for metrics (5s, 10s, 30s, 60s, 5m, 15m, 1h, 6h)
     - `pod`: Optional specific pod name
   - **Response**:
     ```json
     {
       "submit": 1234,
       "delivered": 1100,
       "failure": 134,
       "success_rate": 89.15,
       "time_range": "5m"
     }
     ```

## Communication Protocols

1. **Browser to Flask Server**: HTTP/HTTPS
2. **Flask Server to Kubernetes API**: HTTPS using kubeconfig authentication
3. **Flask Server to Metrics Server**: HTTPS via Kubernetes API
4. **Flask Server to Pod Logs**: HTTPS via Kubernetes API (for metrics analysis)

## Security Considerations

- The dashboard uses the same authentication as configured in kubeconfig
- All communication with the Kubernetes API uses TLS encryption
- The dashboard runs with the permissions of the authenticated user
- Pod logs are accessed with read-only permissions
- For production use, consider implementing additional authentication for the web UI
- API endpoints should be protected with authentication in production

## Monitoring Features

The dashboard includes several monitoring features:

### 1. Resource Monitoring
- CPU and memory usage across the cluster
- Node resource utilization
- Pod resource consumption
- Real-time metrics updates

### 2. Health Monitoring
- Pod status tracking (Running, Pending, Failed)
- Node health status
- Application deadlock detection
- Resource starvation detection
- Crash loop detection
- Volume mount issue detection

### 3. Advanced Metrics Dashboard (NEW)
- **Real-Time API Request Tracking**:
  - Submit count (total requests)
  - Delivered count (successful requests with 200 status)
  - Failure count (errors with 404, 500, 503 status)
  - Success rate percentage
- **Time Range Filtering**:
  - Ultra real-time: 5s, 10s, 30s, 60s
  - Short-term: 5m, 15m
  - Long-term: 1h, 6h
- **Namespace & Pod Filtering**:
  - View metrics for specific namespaces
  - Filter by individual pods
- **Interactive Visualizations**:
  - CPU Usage chart
  - Memory Usage chart with limits
  - Network I/O chart (RX/TX)
  - API Request Metrics chart (Submit/Delivered/Failure)
- **Historical Data**:
  - 20-point rolling window
  - Traffic pattern visualization
  - Auto-refresh every 30 seconds

### 4. Visualization
- Node distribution chart
- Resource usage progress bars
- Status indicators with color coding
- Health metrics summary
- **NEW**: Chart.js powered interactive charts
- **NEW**: Grafana-style dark theme

### 5. Troubleshooting
- Detailed pod information modal
- Issue-specific troubleshooting guidance
- Direct pod management actions
- Real-time status updates
- **NEW**: Clickable failure analysis with error details

## Data Processing Pipeline

### Metrics Collection Flow
```
1. User selects namespace + time range
        ↓
2. Frontend requests /api/request-metrics/<namespace>?time_range=5m
        ↓
3. Backend fetches pod logs via Kubernetes API
        ↓
4. Log parser analyzes HTTP requests:
   - Counts total requests (GET, POST, etc.)
   - Identifies successful requests (200 status)
   - Identifies failures (404, 500, 503 status)
        ↓
5. Metrics calculator computes:
   - Submit = Total requests
   - Delivered = Successful requests
   - Failure = Error requests
   - Success Rate = (Delivered / Submit) × 100
        ↓
6. JSON response returned to frontend
        ↓
7. Chart.js renders visualization
        ↓
8. Historical data stored in browser (20 points)
        ↓
9. Auto-refresh after 30 seconds
```

## Scalability

The dashboard is designed for monitoring individual Kubernetes clusters:

- **Single Cluster**: Optimized for clusters with up to 1000 pods
- **Multi-Cluster**: Deploy separate dashboard instances for each cluster
- **High Traffic**: Metrics dashboard handles high-volume log analysis
- **Browser Performance**: Chart.js efficiently renders up to 20 data points per chart
- **Log Analysis**: Processes last 100 lines per pod (configurable)

For larger deployments:
- Consider using dedicated monitoring solutions like Prometheus and Grafana
- Implement caching for frequently accessed metrics
- Use database for historical data storage

## Performance Considerations

### Backend
- Pod log fetching: ~100-500ms per pod
- Metrics calculation: ~10-50ms
- API response time: <1 second for typical requests

### Frontend
- Chart rendering: ~50-100ms
- Auto-refresh interval: 30 seconds (configurable)
- Historical data: 20 points × 4 charts = 80 data points in memory

### Optimization
- Logs fetched with time-based filtering (since_seconds)
- Only active pods are queried
- Browser caches static assets
- Minimal DOM manipulation for updates

## Logging and Monitoring

- Application logs are stored in `/root/kubernetes-dashboard/logs/k8s_dashboard.log`
- The systemd service provides standard output and error logging
- Log rotation should be configured for production use
- Metrics dashboard logs API request counts and errors

## Technology Stack

### Backend
- **Python 3.6+**: Core language
- **Flask 3.0.0**: Web framework
- **kubernetes 26.1.0**: Kubernetes API client
- **requests 2.31.0**: HTTP library
- **psutil 5.9.5**: System monitoring
- **boto3 1.34.0**: AWS CloudWatch integration (optional)

### Frontend
- **HTML5**: Structure
- **CSS3**: Styling
- **Bootstrap 5.3.0**: UI framework
- **JavaScript (ES6+)**: Logic
- **Chart.js 4.4.0**: Data visualization
- **Font Awesome 6.4.0**: Icons

### Infrastructure
- **Systemd**: Service management
- **Kubernetes API**: Cluster communication
- **Metrics Server**: Resource metrics

## Future Architecture Enhancements

Potential improvements to the architecture:
- Implement WebSockets for real-time updates without polling
- Add user authentication and role-based access control (RBAC)
- Create a backend database for historical metrics storage
- Develop a plugin system for custom extensions
- Add support for multiple clusters in single dashboard
- Implement Prometheus integration for advanced metrics
- Add alerting system with notifications
- Create mobile-responsive progressive web app (PWA)
- Add export functionality for metrics data (CSV, JSON)
- Implement custom dashboard layouts and widgets
