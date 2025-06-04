/**
 * Kubernetes Actions JavaScript
 * Provides functionality for managing Kubernetes resources
 */

// Pod Actions
function deletePod(namespace, name) {
    if (!confirm(`Are you sure you want to delete pod "${name}" in namespace "${namespace}"?`)) {
        return;
    }
    
    showLoading(`Deleting pod ${name}...`);
    
    fetch('/api/pods/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            namespace: namespace,
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('success', data.message);
            refreshData();
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('error', 'Failed to delete pod. See console for details.');
    });
}

function restartPod(namespace, name) {
    if (!confirm(`Are you sure you want to restart pod "${name}" in namespace "${namespace}"?`)) {
        return;
    }
    
    showLoading(`Restarting pod ${name}...`);
    
    fetch('/api/pods/restart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            namespace: namespace,
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('success', data.message);
            refreshData();
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('error', 'Failed to restart pod. See console for details.');
    });
}

// Deployment Actions
function createDeployment() {
    const namespace = document.getElementById('deploymentNamespace').value;
    const name = document.getElementById('deploymentName').value;
    const image = document.getElementById('deploymentImage').value;
    const replicas = document.getElementById('deploymentReplicas').value;
    
    if (!namespace || !name || !image) {
        showNotification('error', 'Namespace, name, and image are required');
        return;
    }
    
    showLoading(`Creating deployment ${name}...`);
    
    fetch('/api/deployments/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            namespace: namespace,
            name: name,
            image: image,
            replicas: replicas
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('success', data.message);
            // Close modal if it exists
            const modal = bootstrap.Modal.getInstance(document.getElementById('createDeploymentModal'));
            if (modal) {
                modal.hide();
            }
            refreshData();
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('error', 'Failed to create deployment. See console for details.');
    });
}

function scaleDeployment(namespace, name) {
    const replicas = prompt(`Enter the number of replicas for deployment "${name}" in namespace "${namespace}":`, "1");
    
    if (replicas === null) {
        return; // User cancelled
    }
    
    // Validate input is a number
    if (!/^\d+$/.test(replicas)) {
        showNotification('error', 'Please enter a valid number for replicas');
        return;
    }
    
    showLoading(`Scaling deployment ${name} to ${replicas} replicas...`);
    
    fetch('/api/deployments/scale', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            namespace: namespace,
            name: name,
            replicas: parseInt(replicas)
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('success', data.message);
            refreshData();
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('error', 'Failed to scale deployment. See console for details.');
    });
}

function restartDeployment(namespace, name) {
    if (!confirm(`Are you sure you want to restart deployment "${name}" in namespace "${namespace}"?`)) {
        return;
    }
    
    showLoading(`Restarting deployment ${name}...`);
    
    fetch('/api/deployments/restart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            namespace: namespace,
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('success', data.message);
            refreshData();
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('error', 'Failed to restart deployment. See console for details.');
    });
}

function deleteDeployment(namespace, name) {
    if (!confirm(`Are you sure you want to delete deployment "${name}" in namespace "${namespace}"?`)) {
        return;
    }
    
    showLoading(`Deleting deployment ${name}...`);
    
    fetch('/api/deployments/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            namespace: namespace,
            name: name
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification('success', data.message);
            refreshData();
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('error', 'Failed to delete deployment. See console for details.');
    });
}

// UI Helpers
function showCreateDeploymentModal() {
    // Create modal if it doesn't exist
    if (!document.getElementById('createDeploymentModal')) {
        const modalHTML = `
        <div class="modal fade" id="createDeploymentModal" tabindex="-1" aria-labelledby="createDeploymentModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title" id="createDeploymentModalLabel">Create Deployment</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="deploymentNamespace" class="form-label">Namespace</label>
                            <input type="text" class="form-control" id="deploymentNamespace" placeholder="default">
                        </div>
                        <div class="mb-3">
                            <label for="deploymentName" class="form-label">Deployment Name</label>
                            <input type="text" class="form-control" id="deploymentName" placeholder="my-deployment">
                        </div>
                        <div class="mb-3">
                            <label for="deploymentImage" class="form-label">Container Image</label>
                            <input type="text" class="form-control" id="deploymentImage" placeholder="nginx:latest">
                        </div>
                        <div class="mb-3">
                            <label for="deploymentReplicas" class="form-label">Replicas</label>
                            <input type="number" class="form-control" id="deploymentReplicas" value="1" min="1">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="createDeployment()">Create</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('createDeploymentModal'));
    modal.show();
}

function showLoading(message) {
    // Create loading overlay if it doesn't exist
    if (!document.getElementById('loadingOverlay')) {
        const loadingHTML = `
        <div id="loadingOverlay" class="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center" style="background-color: rgba(0,0,0,0.5); z-index: 9999; display: none;">
            <div class="card p-4 text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div id="loadingMessage" class="text-white">Loading...</div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    }
    
    // Update message and show
    document.getElementById('loadingMessage').textContent = message || 'Loading...';
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

function showNotification(type, message) {
    const notificationArea = document.getElementById('notification-area');
    if (!notificationArea) {
        // Create notification area if it doesn't exist
        const newNotificationArea = document.createElement('div');
        newNotificationArea.id = 'notification-area';
        newNotificationArea.style.position = 'fixed';
        newNotificationArea.style.top = '20px';
        newNotificationArea.style.right = '20px';
        newNotificationArea.style.zIndex = '9999';
        document.body.appendChild(newNotificationArea);
    }
    
    // Map type to Bootstrap alert class
    let alertClass;
    switch(type) {
        case 'success':
            alertClass = 'success';
            break;
        case 'error':
            alertClass = 'danger';
            break;
        case 'info':
            alertClass = 'info';
            break;
        case 'warning':
            alertClass = 'warning';
            break;
        default:
            alertClass = 'primary';
    }
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.getElementById('notification-area').appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

function refreshData() {
    // Refresh data after a short delay
    setTimeout(() => {
        fetchData();
    }, 1000);
}

// Make functions globally available
window.deletePod = deletePod;
window.restartPod = restartPod;
window.createDeployment = createDeployment;
window.scaleDeployment = scaleDeployment;
window.restartDeployment = restartDeployment;
window.deleteDeployment = deleteDeployment;
window.showCreateDeploymentModal = showCreateDeploymentModal;
