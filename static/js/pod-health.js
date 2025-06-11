// Function to fetch pod health data
async function fetchPodHealthData() {
    try {
        console.log("Fetching pod health data...");
        const response = await fetch('/api/pod-health');
        const data = await response.json();
        console.log("Pod health data received:", data);
        updatePodHealthUI(data);
    } catch (error) {
        console.error('Error fetching pod health data:', error);
    }
}

// Function to view pod logs
function viewPodLogs(namespace, podName) {
    console.log(`View logs for pod ${podName} in namespace ${namespace}`);
    
    // Get the modal elements
    const modal = document.getElementById('podLogsModal') || createPodLogsModal();
    const modalTitle = document.getElementById('podLogsModalLabel');
    const modalContent = document.getElementById('podLogsContent');
    
    if (!modal || !modalTitle || !modalContent) {
        console.error('Modal elements not found');
        alert(`Error: Could not display logs for ${podName}`);
        return;
    }
    
    // Update modal title
    modalTitle.textContent = `Logs: ${podName}`;
    
    // Show loading indicator
    modalContent.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading logs...</div>';
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Fetch pod logs
    fetch(`/api/pods/${namespace}/${podName}/logs`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Format logs with line numbers
                const logLines = data.logs.split('\n');
                let formattedLogs = '';
                
                if (data.logs.trim() === '') {
                    formattedLogs = '<div class="text-center">No logs available for this pod</div>';
                } else {
                    logLines.forEach((line, index) => {
                        formattedLogs += `<div class="log-line"><span class="log-line-number">${index + 1}</span><span class="log-line-content">${escapeHtml(line)}</span></div>`;
                    });
                }
                
                modalContent.innerHTML = `
                    <div class="logs-container">
                        ${formattedLogs}
                    </div>
                    <div class="mt-3">
                        <button class="btn btn-sm btn-outline-secondary" onclick="refreshPodLogs('${namespace}', '${podName}')">
                            <i class="fas fa-sync"></i> Refresh Logs
                        </button>
                    </div>
                `;
            } else {
                modalContent.innerHTML = `<div class="alert alert-danger">Error fetching logs: ${data.error}</div>`;
            }
        })
        .catch(error => {
            console.error('Error fetching pod logs:', error);
            modalContent.innerHTML = `<div class="alert alert-danger">Error fetching logs: ${error.message}</div>`;
        });
}

// Function to refresh pod logs
function refreshPodLogs(namespace, podName) {
    viewPodLogs(namespace, podName);
}

// Helper function to create the pod logs modal if it doesn't exist
function createPodLogsModal() {
    const modalHtml = `
        <div class="modal fade" id="podLogsModal" tabindex="-1" aria-labelledby="podLogsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="podLogsModalLabel">Pod Logs</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div id="podLogsContent"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer.firstChild);
    
    // Add CSS for logs
    const style = document.createElement('style');
    style.textContent = `
        .logs-container {
            max-height: 500px;
            overflow-y: auto;
            background-color: #1e1e1e;
            color: #f8f8f8;
            font-family: monospace;
            padding: 10px;
            border-radius: 4px;
        }
        .log-line {
            display: flex;
            padding: 1px 0;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .log-line:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        .log-line-number {
            min-width: 40px;
            color: #888;
            text-align: right;
            padding-right: 10px;
            user-select: none;
        }
        .log-line-content {
            flex: 1;
        }
    `;
    document.head.appendChild(style);
    
    return document.getElementById('podLogsModal');
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Function to update the pod health UI
function updatePodHealthUI(podHealthData) {
    const hangDetectionTable = document.getElementById('hangDetectionTable');
    const podHealthMetrics = document.getElementById('podHealthMetrics');
    
    if (!hangDetectionTable || !podHealthMetrics) {
        console.error('Required DOM elements not found');
        return;
    }
    
    // Clear previous content
    hangDetectionTable.innerHTML = '';
    podHealthMetrics.innerHTML = '';
    
    // Collect statistics
    let totalIssues = 0;
    let issuesByType = {};
    let podsWithIssues = new Set();
    
    // Store pod data for details view
    window.podDetailsData = {};
    
    // Process pod health data
    podHealthData.forEach(pod => {
        // Store pod data for details view
        window.podDetailsData[`${pod.namespace}/${pod.name}`] = pod;
        
        if (pod.potential_issues && pod.potential_issues.length > 0) {
            podsWithIssues.add(pod.name);
            
            pod.potential_issues.forEach(issue => {
                totalIssues++;
                
                if (!issuesByType[issue.type]) {
                    issuesByType[issue.type] = 0;
                }
                issuesByType[issue.type]++;
                
                // Add row to hang detection table
                const row = document.createElement('tr');
                
                // Determine status class based on severity
                let statusClass = 'status-badge';
                if (issue.severity === 'Warning') {
                    statusClass += ' pending';
                } else if (issue.severity === 'Error') {
                    statusClass += ' failed';
                }
                
                row.innerHTML = `
                    <td>${pod.name}</td>
                    <td>${pod.namespace}</td>
                    <td>${issue.type}</td>
                    <td>${issue.duration}</td>
                    <td><span class="${statusClass}">${issue.severity}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewPodDetails('${pod.namespace}', '${pod.name}')">
                            <i class="fas fa-search"></i> Details
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="restartPod('${pod.namespace}', '${pod.name}')">
                            <i class="fas fa-sync"></i> Restart
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="viewPodLogs('${pod.namespace}', '${pod.name}')">
                            <i class="fas fa-file-alt"></i> Log
                        </button>
                    </td>
                `;
                
                hangDetectionTable.appendChild(row);
            });
        }
    });
    
    // Create health metrics summary
    const healthMetricsSummary = document.createElement('div');
    healthMetricsSummary.className = 'health-metrics-summary';
    
    // Add total issues metric
    const totalIssuesMetric = document.createElement('div');
    totalIssuesMetric.className = 'health-metric';
    totalIssuesMetric.innerHTML = `
        <div class="health-metric-value ${totalIssues > 0 ? 'warning' : 'healthy'}">${totalIssues}</div>
        <div class="health-metric-label">Total Issues</div>
    `;
    healthMetricsSummary.appendChild(totalIssuesMetric);
    
    // Add pods with issues metric
    const podsWithIssuesMetric = document.createElement('div');
    podsWithIssuesMetric.className = 'health-metric';
    podsWithIssuesMetric.innerHTML = `
        <div class="health-metric-value ${podsWithIssues.size > 0 ? 'warning' : 'healthy'}">${podsWithIssues.size}</div>
        <div class="health-metric-label">Pods with Issues</div>
    `;
    healthMetricsSummary.appendChild(podsWithIssuesMetric);
    
    // Add issue types metric
    const issueTypesCount = Object.keys(issuesByType).length;
    const issueTypesMetric = document.createElement('div');
    issueTypesMetric.className = 'health-metric';
    issueTypesMetric.innerHTML = `
        <div class="health-metric-value">${issueTypesCount}</div>
        <div class="health-metric-label">Issue Types</div>
    `;
    healthMetricsSummary.appendChild(issueTypesMetric);
    
    // Add metrics to container
    podHealthMetrics.appendChild(healthMetricsSummary);
    
    // If no issues found, show a message
    if (totalIssues === 0) {
        hangDetectionTable.innerHTML = '<tr><td colspan="6" class="text-center">No potential hang issues detected</td></tr>';
    }
}

// Function to view pod details
function viewPodDetails(namespace, podName) {
    console.log(`View details for pod ${podName} in namespace ${namespace}`);
    
    // Get pod data from stored data
    const podKey = `${namespace}/${podName}`;
    const pod = window.podDetailsData[podKey];
    
    if (!pod) {
        console.error(`Pod data not found for ${podKey}`);
        alert(`Error: Pod data not found for ${podName}`);
        return;
    }
    
    // Get the modal elements
    const modal = document.getElementById('podDetailsModal') || createPodDetailsModal();
    const modalTitle = document.getElementById('podDetailsModalLabel');
    const modalContent = document.getElementById('podDetailsContent');
    const restartBtn = document.getElementById('restartPodBtn');
    
    if (!modal || !modalTitle || !modalContent || !restartBtn) {
        console.error('Modal elements not found');
        alert(`Pod Details: ${podName} in namespace ${namespace}`);
        return;
    }
    
    // Update modal title
    modalTitle.textContent = `Pod Details: ${podName}`;
    
    // Build modal content
    let content = `
        <div class="pod-details">
            <div class="details-section">
                <h5>Basic Information</h5>
                <table class="table table-sm">
                    <tr>
                        <th>Name:</th>
                        <td>${pod.name}</td>
                    </tr>
                    <tr>
                        <th>Namespace:</th>
                        <td>${pod.namespace}</td>
                    </tr>
                    <tr>
                        <th>Status:</th>
                        <td><span class="status-badge ${pod.status.toLowerCase()}">${pod.status}</span></td>
                    </tr>
                    <tr>
                        <th>Start Time:</th>
                        <td>${pod.start_time ? new Date(pod.start_time).toLocaleString() : 'N/A'}</td>
                    </tr>
                </table>
            </div>
    `;
    
    // Add container statuses
    if (pod.container_statuses && pod.container_statuses.length > 0) {
        content += `
            <div class="details-section">
                <h5>Container Statuses</h5>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Container</th>
                            <th>State</th>
                            <th>Ready</th>
                            <th>Restarts</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        pod.container_statuses.forEach(container => {
            content += `
                <tr>
                    <td>${container.name}</td>
                    <td>${container.state}${container.reason ? ` (${container.reason})` : ''}</td>
                    <td>${container.ready ? 'Yes' : 'No'}</td>
                    <td>${container.restart_count}</td>
                </tr>
            `;
        });
        
        content += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Add potential issues
    if (pod.potential_issues && pod.potential_issues.length > 0) {
        content += `
            <div class="details-section">
                <h5>Potential Issues</h5>
                <div class="list-group">
        `;
        
        pod.potential_issues.forEach(issue => {
            const severityClass = issue.severity === 'Warning' ? 'warning' : 'danger';
            content += `
                <div class="list-group-item list-group-item-${severityClass}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${issue.type}</h6>
                        <small>${issue.duration}</small>
                    </div>
                    <p class="mb-1">${issue.description}</p>
                </div>
            `;
        });
        
        content += `
                </div>
            </div>
        `;
    } else {
        content += `
            <div class="details-section">
                <h5>Potential Issues</h5>
                <div class="alert alert-success">No issues detected</div>
            </div>
        `;
    }
    
    content += `</div>`;
    
    // Update modal content
    modalContent.innerHTML = content;
    
    // Set up restart button
    restartBtn.onclick = function() {
        restartPod(namespace, podName);
        const modalInstance = bootstrap.Modal.getInstance(modal);
        modalInstance.hide();
    };
    
    // Show the modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

// Function to restart a pod
function restartPod(namespace, podName) {
    if (confirm(`Are you sure you want to restart pod ${podName}?`)) {
        fetch(`/api/pods/${namespace}/${podName}/restart`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Pod ${podName} restart initiated successfully`);
                // Refresh data after a short delay
                setTimeout(fetchPodHealthData, 2000);
            } else {
                alert(`Failed to restart pod: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error restarting pod:', error);
            alert('Error restarting pod. See console for details.');
        });
    }
}

// Helper function to create the pod details modal if it doesn't exist
function createPodDetailsModal() {
    const modalHtml = `
        <div class="modal fade" id="podDetailsModal" tabindex="-1" aria-labelledby="podDetailsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="podDetailsModalLabel">Pod Details</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div id="podDetailsContent"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" id="restartPodBtn" class="btn btn-warning">Restart Pod</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer.firstChild);
    
    return document.getElementById('podDetailsModal');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing pod health monitor");
    
    // Fetch initial data
    fetchPodHealthData();
    
    // Set up refresh interval
    setInterval(fetchPodHealthData, 30000); // Refresh every 30 seconds
});
