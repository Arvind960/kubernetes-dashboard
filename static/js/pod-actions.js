// Pod action functions
function startPod(namespace, name, ownerKind, ownerName) {
    console.log("Start pod called:", namespace, name);
    if (confirm(`Are you sure you want to resume pod "${name}" in namespace "${namespace}"?`)) {
        console.log("Confirmed resume, sending request");
        
        // Show loading indicator
        showLoading(`Resuming pod ${name}...`);
        
        fetch('/api/pods/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                namespace, 
                name,
                owner_kind: ownerKind,
                owner_name: ownerName
            })
        })
        .then(response => {
            console.log("Response status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Response data:", data);
            hideLoading();
            
            // Show result
            if (data.success) {
                showNotification('success', data.message);
                // Refresh data after a short delay
                setTimeout(() => {
                    // Instead of full page reload, fetch fresh data
                    fetchData();
                }, 1000);
                
                // Also schedule a second refresh after a longer delay
                // This helps catch pods that take longer to change status
                setTimeout(() => {
                    fetchData();
                }, 3000);
            } else {
                showNotification('error', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoading();
            showNotification('error', 'Failed to resume pod. See console for details.');
        });
    }
}

function stopPod(namespace, name, ownerKind, ownerName) {
    console.log("Stop pod called:", namespace, name);
    if (confirm(`Are you sure you want to pause pod "${name}" in namespace "${namespace}"?`)) {
        console.log("Confirmed pause, sending request");
        
        // Show loading indicator
        showLoading(`Pausing pod ${name}...`);
        
        fetch('/api/pods/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                namespace, 
                name,
                owner_kind: ownerKind,
                owner_name: ownerName
            })
        })
        .then(response => {
            console.log("Response status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Response data:", data);
            hideLoading();
            
            // Show result
            if (data.success) {
                showNotification('success', data.message);
                // Refresh data after a short delay
                setTimeout(() => {
                    // Instead of full page reload, fetch fresh data
                    fetchData();
                }, 1000);
                
                // Also schedule a second refresh after a longer delay
                // This helps catch pods that take longer to change status
                setTimeout(() => {
                    fetchData();
                }, 3000);
            } else {
                showNotification('error', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoading();
            showNotification('error', 'Failed to pause pod. See console for details.');
        });
    }
}

// UI helper functions
let loadingElement = null;

function showLoading(message) {
    hideLoading(); // Remove any existing loading indicator
    
    loadingElement = document.createElement('div');
    loadingElement.className = 'loading-overlay';
    loadingElement.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="loading-message">${message}</div>
        </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .loading-content {
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }
        .loading-message {
            margin-top: 10px;
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(loadingElement);
}

function hideLoading() {
    if (loadingElement && loadingElement.parentNode) {
        loadingElement.parentNode.removeChild(loadingElement);
    }
    loadingElement = null;
}

function showNotification(type, message) {
    // Create notification area if it doesn't exist
    let notificationArea = document.getElementById('notification-area');
    if (!notificationArea) {
        notificationArea = document.createElement('div');
        notificationArea.id = 'notification-area';
        notificationArea.style.position = 'fixed';
        notificationArea.style.top = '20px';
        notificationArea.style.right = '20px';
        notificationArea.style.zIndex = '9999';
        notificationArea.style.maxWidth = '400px';
        document.body.appendChild(notificationArea);
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
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${alertClass} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    notificationArea.appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Make functions globally available
window.startPod = startPod;
window.stopPod = stopPod;
