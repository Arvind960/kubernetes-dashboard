// Dashboard specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize circular progress indicators
    updateCircularProgress('podStatusCircle', 85);
    updateCircularProgress('nodeStatusCircle', 100);
    updateCircularProgress('deploymentStatusCircle', 90);
    
    // Update the dashboard data periodically
    fetchDashboardData();
    setInterval(fetchDashboardData, 10000); // Refresh every 10 seconds
});

// Update circular progress indicators
function updateCircularProgress(id, percentage) {
    const circle = document.getElementById(id);
    if (!circle) return;
    
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference - (percentage / 100) * circumference;
}

// Fetch dashboard data from API
function fetchDashboardData() {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
            updateResourceStatus(data);
            updateAlerts(data);
            updateEvents(data);
        })
        .catch(error => console.error('Error fetching dashboard data:', error));
}

// Update dashboard statistics
function updateDashboardStats(data) {
    // Update pod stats
    const totalPods = data.pods ? data.pods.length : 0;
    const runningPods = data.pods ? data.pods.filter(pod => pod.status === 'Running').length : 0;
    document.getElementById('podCount').textContent = totalPods;
    document.getElementById('runningPodCount').textContent = `${runningPods} Running`;
    updateCircularProgress('podStatusCircle', totalPods > 0 ? (runningPods / totalPods) * 100 : 0);
    
    // Update node stats
    const totalNodes = data.nodes ? data.nodes.length : 0;
    const readyNodes = data.nodes ? data.nodes.filter(node => node.status === 'Ready').length : 0;
    document.getElementById('nodeCount').textContent = totalNodes;
    document.getElementById('readyNodeCount').textContent = `${readyNodes} Ready`;
    updateCircularProgress('nodeStatusCircle', totalNodes > 0 ? (readyNodes / totalNodes) * 100 : 0);
    
    // Update deployment stats
    const totalDeployments = data.deployments ? data.deployments.length : 0;
    const availableDeployments = data.deployments ? data.deployments.filter(deployment => deployment.status === 'Available').length : 0;
    document.getElementById('deploymentCount').textContent = totalDeployments;
    document.getElementById('availableDeploymentCount').textContent = `${availableDeployments} Available`;
    updateCircularProgress('deploymentStatusCircle', totalDeployments > 0 ? (availableDeployments / totalDeployments) * 100 : 0);
    
    // Update resource usage
    if (data.resource_usage) {
        const cpuUsage = data.resource_usage.cpu ? Math.round((data.resource_usage.cpu.used / data.resource_usage.cpu.total) * 100) : 0;
        const memoryUsage = data.resource_usage.memory ? Math.round((data.resource_usage.memory.used / data.resource_usage.memory.total) * 100) : 0;
        
        document.getElementById('cpuUsagePercent').textContent = `${cpuUsage}%`;
        document.getElementById('memoryUsagePercent').textContent = `${memoryUsage}%`;
        
        document.getElementById('cpuUsageBar').style.width = `${cpuUsage}%`;
        document.getElementById('memoryUsageBar').style.width = `${memoryUsage}%`;
    }
}

// Update resource status indicators
function updateResourceStatus(data) {
    // Update cluster health status
    if (data.cluster_health) {
        const statusElement = document.getElementById('clusterHealthStatus');
        if (statusElement) {
            statusElement.textContent = data.cluster_health.status;
            statusElement.className = `status-badge ${data.cluster_health.status.toLowerCase()}`;
        }
        
        // Update component status
        const componentsList = document.getElementById('componentsList');
        if (componentsList && data.cluster_health.components) {
            let componentsHtml = '';
            data.cluster_health.components.forEach(component => {
                let statusClass = 'green';
                if (component.status.includes('Warning')) statusClass = 'yellow';
                if (component.status.includes('Error')) statusClass = 'red';
                
                componentsHtml += `
                <div class="status-item">
                    <div class="label">
                        <div class="dot ${statusClass}"></div>
                        ${component.name}
                    </div>
                    <div class="value">${component.status.includes('Healthy') ? 'Healthy' : component.status}</div>
                </div>`;
            });
            componentsList.innerHTML = componentsHtml;
        }
    }
}

// Update alerts section
function updateAlerts(data) {
    const alertsList = document.getElementById('alertsList');
    if (alertsList && data.alerts) {
        if (data.alerts.length === 0) {
            alertsList.innerHTML = '<div class="alert-item info">No active alerts</div>';
            return;
        }
        
        let alertsHtml = '';
        data.alerts.slice(0, 5).forEach(alert => {
            let severityClass = 'info';
            if (alert.severity === 'warning') severityClass = 'warning';
            if (alert.severity === 'error') severityClass = 'critical';
            
            alertsHtml += `
            <div class="alert-item ${severityClass}">
                <div><strong>${alert.name}</strong> - ${alert.message}</div>
                <div class="text-muted">${alert.timestamp}</div>
            </div>`;
        });
        alertsList.innerHTML = alertsHtml;
    }
}

// Update events chart
function updateEvents(data) {
    // This would typically use real event data from the API
    // For now, we'll use placeholder data
    const errorCount = data.alerts ? data.alerts.filter(alert => alert.severity === 'error').length : 0;
    const warningCount = data.alerts ? data.alerts.filter(alert => alert.severity === 'warning').length : 0;
    const infoCount = 5; // Placeholder
    
    const total = Math.max(errorCount + warningCount + infoCount, 1);
    
    document.getElementById('errorBar').style.width = `${(errorCount / total) * 100}%`;
    document.getElementById('errorCount').textContent = errorCount;
    
    document.getElementById('warningBar').style.width = `${(warningCount / total) * 100}%`;
    document.getElementById('warningCount').textContent = warningCount;
    
    document.getElementById('infoBar').style.width = `${(infoCount / total) * 100}%`;
    document.getElementById('infoCount').textContent = infoCount;
}
