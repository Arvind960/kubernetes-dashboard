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
    
    // Add issue type metrics
    for (const [type, count] of Object.entries(issuesByType)) {
        const issueTypeMetric = document.createElement('div');
        issueTypeMetric.className = 'health-metric';
        issueTypeMetric.innerHTML = `
            <div class="health-metric-value warning">${count}</div>
            <div class="health-metric-label">${type}</div>
        `;
        healthMetricsSummary.appendChild(issueTypeMetric);
    }
    
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
    const modal = document.getElementById('podDetailsModal');
    const modalTitle = document.getElementById('podDetailsModalLabel');
    const modalContent = document.getElementById('podDetailsContent');
    const restartBtn = document.getElementById('restartPodBtn');
    
    if (!modal || !modalTitle || !modalContent || !restartBtn) {
        console.error('Modal elements not found');
        alert(`Pod Details: ${podName} in namespace ${namespace}`);
        return;
    }
    
    // Set modal title
    modalTitle.textContent = `Pod Details: ${podName}`;
    
    // Build content HTML
    let contentHtml = `
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
                        <td><span class="status-badge ${pod.status === 'Running' ? 'running' : pod.status === 'Pending' ? 'pending' : 'failed'}">${pod.status}</span></td>
                    </tr>
                    <tr>
                        <th>Start Time:</th>
                        <td>${pod.start_time ? new Date(pod.start_time).toLocaleString() : 'N/A'}</td>
                    </tr>
                </table>
            </div>
            
            <div class="details-section">
                <h5>Detected Issues</h5>
                <div class="alert alert-warning">
                    <ul>
    `;
    
    // Add issues
    if (pod.potential_issues && pod.potential_issues.length > 0) {
        pod.potential_issues.forEach(issue => {
            contentHtml += `<li><strong>${issue.type}:</strong> ${issue.description} (${issue.severity})</li>`;
        });
    } else {
        contentHtml += `<li>No issues detected</li>`;
    }
    
    contentHtml += `
                    </ul>
                </div>
            </div>
    `;
    
    // Add container statuses
    if (pod.container_statuses && pod.container_statuses.length > 0) {
        contentHtml += `
            <div class="details-section">
                <h5>Container Statuses</h5>
                <table class="table table-sm table-striped">
                    <thead>
                        <tr>
                            <th>Container</th>
                            <th>State</th>
                            <th>Ready</th>
                            <th>Restarts</th>
                            <th>Started At</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        pod.container_statuses.forEach(container => {
            contentHtml += `
                <tr>
                    <td>${container.name}</td>
                    <td>${container.state}</td>
                    <td>${container.ready ? 'Yes' : 'No'}</td>
                    <td>${container.restart_count}</td>
                    <td>${container.started_at ? new Date(container.started_at).toLocaleString() : 'N/A'}</td>
                </tr>
            `;
        });
        
        contentHtml += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    // Add troubleshooting guidance based on issue type
    contentHtml += `
        <div class="details-section">
            <h5>Troubleshooting Guidance</h5>
            <div class="alert alert-info">
    `;
    
    // Add specific guidance based on issue types
    if (pod.potential_issues && pod.potential_issues.length > 0) {
        const issueTypes = pod.potential_issues.map(issue => issue.type);
        
        if (issueTypes.includes('Application Deadlock')) {
            contentHtml += `
                <p><strong>For Application Deadlock:</strong></p>
                <ul>
                    <li>Check application logs: <code>kubectl logs ${podName} -n ${namespace}</code></li>
                    <li>Verify readiness probe configuration</li>
                    <li>Check for resource constraints that might be causing the application to hang</li>
                    <li>Consider attaching to the container for debugging: <code>kubectl exec -it ${podName} -n ${namespace} -- sh</code></li>
                </ul>
            `;
        }
        
        if (issueTypes.includes('Stuck Init Container')) {
            contentHtml += `
                <p><strong>For Stuck Init Container:</strong></p>
                <ul>
                    <li>Check init container logs: <code>kubectl logs ${podName} -n ${namespace} -c init-container</code></li>
                    <li>Verify that any dependencies the init container is waiting for are available</li>
                    <li>Check for network connectivity issues if the init container is trying to reach external services</li>
                </ul>
            `;
        }
        
        if (issueTypes.includes('Crash Loop')) {
            contentHtml += `
                <p><strong>For Crash Loop:</strong></p>
                <ul>
                    <li>Check previous container logs: <code>kubectl logs ${podName} -n ${namespace} --previous</code></li>
                    <li>Look for error messages in the logs that indicate why the container is crashing</li>
                    <li>Verify that the container command and arguments are correct</li>
                    <li>Check for resource constraints that might be causing the container to be OOMKilled</li>
                </ul>
            `;
        }
        
        if (issueTypes.includes('Volume Mount Issue')) {
            contentHtml += `
                <p><strong>For Volume Mount Issue:</strong></p>
                <ul>
                    <li>Check if the PVC exists: <code>kubectl get pvc -n ${namespace}</code></li>
                    <li>Verify that the PVC is bound to a PV: <code>kubectl describe pvc -n ${namespace}</code></li>
                    <li>Check for storage class issues: <code>kubectl get sc</code></li>
                    <li>Ensure that the storage backend is functioning properly</li>
                </ul>
            `;
        }
        
        if (issueTypes.includes('Resource Starvation')) {
            contentHtml += `
                <p><strong>For Resource Starvation:</strong></p>
                <ul>
                    <li>Check resource usage: <code>kubectl top pod ${podName} -n ${namespace}</code></li>
                    <li>Verify that the pod has appropriate resource requests and limits</li>
                    <li>Check node resource availability: <code>kubectl top nodes</code></li>
                    <li>Consider scaling up resources or optimizing the application</li>
                </ul>
            `;
        }
    } else {
        contentHtml += `<p>No specific issues detected. Monitor the pod for any changes in behavior.</p>`;
    }
    
    contentHtml += `
            </div>
        </div>
    `;
    
    // Set modal content
    modalContent.innerHTML = contentHtml;
    
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

// Initialize pod health monitoring
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing pod health monitor");
    // Check if we're on the right page
    if (document.getElementById('hangDetectionTable')) {
        console.log("Found hangDetectionTable, setting up monitoring");
        // Initial data fetch
        fetchPodHealthData();
        
        // Set up refresh interval
        setInterval(fetchPodHealthData, 10000); // Refresh every 10 seconds for testing
    } else {
        console.warn("hangDetectionTable not found in DOM");
    }
});
