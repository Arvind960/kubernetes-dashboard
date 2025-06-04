/**
 * Deployment Control JavaScript
 * 
 * This file contains functions for controlling Kubernetes deployments
 * (stop, start, and check status) via the API endpoints.
 */

// Function to get the status of a deployment
function getDeploymentStatus() {
    const namespace = document.getElementById('deploymentNamespace').value;
    const deploymentName = document.getElementById('deploymentName').value;
    
    if (!deploymentName) {
        showDeploymentMessage('Please enter a deployment name', 'danger');
        return;
    }
    
    fetch(`/api/deployment/status?namespace=${namespace}&deployment_name=${deploymentName}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const deployment = data.deployment;
                let statusClass = 'info';
                
                if (deployment.status === 'Running') {
                    statusClass = 'success';
                } else if (deployment.status === 'Stopped') {
                    statusClass = 'warning';
                } else if (deployment.status === 'Scaling') {
                    statusClass = 'primary';
                }
                
                const message = `
                    <strong>Status:</strong> ${deployment.status}<br>
                    <strong>Namespace:</strong> ${deployment.namespace}<br>
                    <strong>Desired Replicas:</strong> ${deployment.current_replicas}<br>
                    <strong>Available Replicas:</strong> ${deployment.available_replicas}<br>
                    <strong>Ready Replicas:</strong> ${deployment.ready_replicas}
                `;
                
                showDeploymentMessage(message, statusClass);
            } else {
                showDeploymentMessage(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showDeploymentMessage('Error checking deployment status', 'danger');
        });
}

// Function to stop a deployment
function stopDeployment() {
    const namespace = document.getElementById('deploymentNamespace').value;
    const deploymentName = document.getElementById('deploymentName').value;
    
    if (!deploymentName) {
        showDeploymentMessage('Please enter a deployment name', 'danger');
        return;
    }
    
    const data = {
        namespace: namespace,
        deployment_name: deploymentName
    };
    
    fetch('/api/deployment/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showDeploymentMessage(`${data.message}. Previous replicas: ${data.previous_replicas}`, 'warning');
        } else {
            showDeploymentMessage(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showDeploymentMessage('Error stopping deployment', 'danger');
    });
}

// Function to start a deployment
function startDeployment() {
    const namespace = document.getElementById('deploymentNamespace').value;
    const deploymentName = document.getElementById('deploymentName').value;
    const replicas = document.getElementById('deploymentReplicas').value;
    
    if (!deploymentName) {
        showDeploymentMessage('Please enter a deployment name', 'danger');
        return;
    }
    
    const data = {
        namespace: namespace,
        deployment_name: deploymentName,
        replicas: parseInt(replicas)
    };
    
    fetch('/api/deployment/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showDeploymentMessage(data.message, 'success');
        } else {
            showDeploymentMessage(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showDeploymentMessage('Error starting deployment', 'danger');
    });
}

// Helper function to show deployment status messages
function showDeploymentMessage(message, type) {
    const messageElement = document.getElementById('deploymentStatusMessage');
    messageElement.innerHTML = message;
    messageElement.className = `alert alert-${type}`;
    messageElement.style.display = 'block';
}
