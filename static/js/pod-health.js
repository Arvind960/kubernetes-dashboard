// Function to fetch pod health data
async function fetchPodHealthData() {
    try {
        const response = await fetch('/api/pod-health');
        const data = await response.json();
        updatePodHealthUI(data);
    } catch (error) {
        console.error('Error fetching pod health data:', error);
    }
}

// Function to update the pod health UI
function updatePodHealthUI(podHealthData) {
    const hangDetectionTable = document.getElementById('hangDetectionTable');
    const podHealthMetrics = document.getElementById('podHealthMetrics');
    
    // Clear previous content
    hangDetectionTable.innerHTML = '';
    podHealthMetrics.innerHTML = '';
    
    // Collect statistics
    let totalIssues = 0;
    let issuesByType = {};
    let podsWithIssues = new Set();
    
    // Process pod health data
    podHealthData.forEach(pod => {
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
    // Implement pod details view
    console.log(`View details for pod ${podName} in namespace ${namespace}`);
    // You could open a modal or navigate to a pod details page
    alert(`Viewing details for pod ${podName} in namespace ${namespace}`);
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
    // Check if we're on the right page
    if (document.getElementById('hangDetectionTable')) {
        // Initial data fetch
        fetchPodHealthData();
        
        // Set up refresh interval
        setInterval(fetchPodHealthData, 30000); // Refresh every 30 seconds
    }
});
