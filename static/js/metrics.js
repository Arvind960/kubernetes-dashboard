// Metrics Dashboard JavaScript
let metricsCharts = {};
let metricsInterval = null;

// Initialize metrics dashboard
function initMetricsDashboard() {
    loadNamespaces();
    loadMetricsData();
    
    // Auto-refresh every 30 seconds
    if (metricsInterval) clearInterval(metricsInterval);
    metricsInterval = setInterval(loadMetricsData, 30000);
}

// Load namespaces for filter
async function loadNamespaces() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        const select = document.getElementById('metricsNamespace');
        
        const namespaces = [...new Set(data.pods.map(p => p.namespace))];
        select.innerHTML = '<option value="">All Namespaces</option>';
        namespaces.forEach(ns => {
            select.innerHTML += `<option value="${ns}">${ns}</option>`;
        });
    } catch (error) {
        console.error('Error loading namespaces:', error);
    }
}

// Load metrics data
async function loadMetricsData() {
    try {
        const namespace = document.getElementById('metricsNamespace').value;
        const podName = document.getElementById('metricsPod').value;
        const timeRange = document.getElementById('metricsTimeRange').value;
        
        const response = await fetch('/api/data');
        const data = await response.json();
        
        // Filter pods
        let pods = data.pods;
        if (namespace) pods = pods.filter(p => p.namespace === namespace);
        if (podName) pods = pods.filter(p => p.name === podName);
        
        // Update pod selector
        updatePodSelector(data.pods, namespace);
        
        // Calculate metrics - pass all pods for uptime calculation
        const metrics = calculateMetrics(pods.length > 0 ? pods : data.pods);
        
        // Fetch real API metrics if dsdp namespace is selected
        if (namespace === 'dsdp') {
            try {
                let apiUrl = `/api/request-metrics/${namespace}?time_range=${timeRange}`;
                if (podName) {
                    apiUrl += `&pod=${podName}`;
                }
                
                const apiResponse = await fetch(apiUrl);
                const apiData = await apiResponse.json();
                
                // Store historical data
                if (!window.metricsHistory) {
                    window.metricsHistory = [];
                }
                
                // Add current data point
                window.metricsHistory.push({
                    time: new Date(),
                    submit: apiData.submit,
                    delivered: apiData.delivered,
                    failure: apiData.failure,
                    successRate: apiData.success_rate
                });
                
                // Keep only last 20 data points
                if (window.metricsHistory.length > 20) {
                    window.metricsHistory.shift();
                }
                
                // Use historical data for chart
                metrics.apiRequests = window.metricsHistory.map(h => ({
                    time: h.time,
                    submit: h.submit,
                    delivered: h.delivered,
                    failure: h.failure,
                    successRate: h.successRate
                }));
                
            } catch (error) {
                console.log('Using simulated API metrics');
            }
        }
        
        // Update status cards
        updateStatusCards(metrics);
        
        // Update charts
        updateCharts(metrics);
        
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

// Update pod selector
function updatePodSelector(allPods, namespace) {
    const select = document.getElementById('metricsPod');
    const currentValue = select.value;
    
    let pods = allPods;
    if (namespace) pods = pods.filter(p => p.namespace === namespace);
    
    select.innerHTML = '<option value="">All Pods</option>';
    pods.forEach(pod => {
        select.innerHTML += `<option value="${pod.name}">${pod.name}</option>`;
    });
    
    if (currentValue) select.value = currentValue;
}

// Calculate metrics from pods
function calculateMetrics(pods) {
    const now = new Date();
    const metrics = {
        status: 'UP',
        uptime: '-',
        startTime: '-',
        podInfo: `${pods.length} pod(s)`,
        cpu: [],
        memory: [],
        network: { rx: [], tx: [] },
        apiRequests: []
    };
    
    if (pods.length === 0) return metrics;
    
    // Calculate uptime from oldest pod
    let oldestStart = null;
    pods.forEach(pod => {
        if (pod.creation_time) {
            const start = new Date(pod.creation_time);
            if (!oldestStart || start < oldestStart) {
                oldestStart = start;
            }
        }
    });
    
    if (oldestStart) {
        metrics.startTime = oldestStart.toLocaleString();
        const uptimeMs = now - oldestStart;
        const days = Math.floor(uptimeMs / (1000 * 60 * 60 * 24));
        const hours = Math.floor((uptimeMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60));
        if (days > 0) {
            metrics.uptime = `${days}d ${hours}h`;
        } else if (hours > 0) {
            metrics.uptime = `${hours}h ${minutes}m`;
        } else {
            metrics.uptime = `${minutes}m`;
        }
    } else {
        // Use current time if no pod start time available
        metrics.startTime = now.toLocaleString();
        metrics.uptime = '0m';
    }
    
    // Generate sample data for charts (last 20 points)
    for (let i = 0; i < 20; i++) {
        const time = new Date(now - (19 - i) * 60000);
        
        // CPU (0-1 cores with variation)
        const cpuBase = 0.3 + Math.random() * 0.4;
        metrics.cpu.push({ time, value: cpuBase });
        
        // Memory (in MB)
        const memBase = 100 + Math.random() * 50;
        metrics.memory.push({ time, value: memBase, limit: 256 });
        
        // Network (in KB/s)
        metrics.network.rx.push({ time, value: 50 + Math.random() * 100 });
        metrics.network.tx.push({ time, value: 30 + Math.random() * 80 });
        
        // API Requests - generate realistic load data
        const baseSubmit = 100 + Math.floor(Math.random() * 50);
        const successRate = 0.88 + Math.random() * 0.08; // 88-96% success
        const deliveredCount = Math.floor(baseSubmit * successRate);
        const failureCount = baseSubmit - deliveredCount;
        metrics.apiRequests.push({ 
            time, 
            submit: baseSubmit,
            delivered: deliveredCount,
            failure: failureCount,
            successRate: (successRate * 100).toFixed(2)
        });
    }
    
    return metrics;
}

// Update status cards
function updateStatusCards(metrics) {
    document.getElementById('metricsStatus').textContent = metrics.status;
    document.getElementById('metricsUptime').textContent = metrics.uptime;
    document.getElementById('metricsStartTime').textContent = metrics.startTime;
    document.getElementById('metricsPodInfo').textContent = metrics.podInfo;
    
    // Update legend values with min/max/avg
    if (metrics.cpu.length > 0) {
        const cpuValues = metrics.cpu.map(d => d.value * 100);
        const lastCpu = cpuValues[cpuValues.length - 1];
        const minCpu = Math.min(...cpuValues);
        const maxCpu = Math.max(...cpuValues);
        const avgCpu = cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length;
        document.getElementById('cpuCurrent').textContent = `${lastCpu.toFixed(1)}%`;
        document.getElementById('cpuStats').textContent = `min: ${minCpu.toFixed(1)}% | max: ${maxCpu.toFixed(1)}% | avg: ${avgCpu.toFixed(1)}%`;
    }
    
    if (metrics.memory.length > 0) {
        const memValues = metrics.memory.map(d => d.value);
        const lastMem = memValues[memValues.length - 1];
        const minMem = Math.min(...memValues);
        const maxMem = Math.max(...memValues);
        const avgMem = memValues.reduce((a, b) => a + b, 0) / memValues.length;
        document.getElementById('memUsed').textContent = `${lastMem.toFixed(0)} MB`;
        document.getElementById('memLimit').textContent = `${metrics.memory[0].limit} MB`;
        document.getElementById('memStats').textContent = `min: ${minMem.toFixed(0)} MB | max: ${maxMem.toFixed(0)} MB | avg: ${avgMem.toFixed(0)} MB`;
    }
    
    if (metrics.network.rx.length > 0) {
        const rxValues = metrics.network.rx.map(d => d.value);
        const txValues = metrics.network.tx.map(d => d.value);
        const lastRx = rxValues[rxValues.length - 1];
        const lastTx = txValues[txValues.length - 1];
        const minRx = Math.min(...rxValues);
        const maxRx = Math.max(...rxValues);
        const avgRx = rxValues.reduce((a, b) => a + b, 0) / rxValues.length;
        const minTx = Math.min(...txValues);
        const maxTx = Math.max(...txValues);
        const avgTx = txValues.reduce((a, b) => a + b, 0) / txValues.length;
        document.getElementById('netReceive').textContent = `${lastRx.toFixed(0)} KB/s`;
        document.getElementById('netTransmit').textContent = `${lastTx.toFixed(0)} KB/s`;
        document.getElementById('netStats').textContent = `RX - min: ${minRx.toFixed(0)} | max: ${maxRx.toFixed(0)} | avg: ${avgRx.toFixed(0)} KB/s | TX - min: ${minTx.toFixed(0)} | max: ${maxTx.toFixed(0)} | avg: ${avgTx.toFixed(0)} KB/s`;
    }
    
    if (metrics.apiRequests.length > 0) {
        const lastRequest = metrics.apiRequests[metrics.apiRequests.length - 1];
        const submitValues = metrics.apiRequests.map(d => d.submit);
        const deliveredValues = metrics.apiRequests.map(d => d.delivered);
        const failureValues = metrics.apiRequests.map(d => d.failure);
        
        // Calculate overall success rate
        const totalSubmit = submitValues.reduce((a, b) => a + b, 0);
        const totalDelivered = deliveredValues.reduce((a, b) => a + b, 0);
        const overallSuccessRate = ((totalDelivered / totalSubmit) * 100).toFixed(2);
        
        document.getElementById('apiSubmit').textContent = lastRequest.submit;
        document.getElementById('apiDelivered').textContent = lastRequest.delivered;
        document.getElementById('apiFailure').textContent = lastRequest.failure;
        
        const avgSubmit = Math.floor(submitValues.reduce((a, b) => a + b, 0) / submitValues.length);
        const avgDelivered = Math.floor(deliveredValues.reduce((a, b) => a + b, 0) / deliveredValues.length);
        const avgFailure = Math.floor(failureValues.reduce((a, b) => a + b, 0) / failureValues.length);
        
        document.getElementById('apiStats').textContent = `Submit avg: ${avgSubmit} | Delivered avg: ${avgDelivered} | Failure avg: ${avgFailure} | Success Rate: ${overallSuccessRate}%`;
        
        // Store failure data for modal
        window.apiFailureData = metrics.apiRequests;
    }
}

// Update charts
function updateCharts(metrics) {
    const labels = metrics.cpu.map(d => d.time.toLocaleTimeString());
    
    // CPU Chart
    updateChart('cpuChart', {
        labels,
        datasets: [{
            label: 'CPU',
            data: metrics.cpu.map(d => (d.value * 100).toFixed(2)),
            borderColor: '#3dba8c',
            backgroundColor: 'rgba(61, 186, 140, 0.1)',
            fill: true,
            tension: 0.4
        }]
    }, { max: 100, unit: '%' });
    
    // Memory Chart
    updateChart('memoryChart', {
        labels,
        datasets: [{
            label: 'Used',
            data: metrics.memory.map(d => d.value.toFixed(0)),
            borderColor: '#326ce5',
            backgroundColor: 'rgba(50, 108, 229, 0.1)',
            fill: true,
            tension: 0.4
        }]
    }, { max: 300, unit: 'MB' });
    
    // Network Chart
    updateChart('networkChart', {
        labels,
        datasets: [
            {
                label: 'RX',
                data: metrics.network.rx.map(d => d.value.toFixed(0)),
                borderColor: '#3dba8c',
                backgroundColor: 'rgba(61, 186, 140, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'TX',
                data: metrics.network.tx.map(d => d.value.toFixed(0)),
                borderColor: '#ff6b6b',
                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                fill: true,
                tension: 0.4
            }
        ]
    }, { unit: 'KB/s' });
    
    // API Request Chart
    updateChart('apiRequestChart', {
        labels,
        datasets: [
            {
                label: 'Delivered',
                data: metrics.apiRequests.map(d => d.delivered),
                borderColor: '#3dba8c',
                backgroundColor: 'rgba(61, 186, 140, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Submit',
                data: metrics.apiRequests.map(d => d.submit),
                borderColor: '#326ce5',
                backgroundColor: 'rgba(50, 108, 229, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Failure',
                data: metrics.apiRequests.map(d => d.failure),
                borderColor: '#ff6b6b',
                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                fill: true,
                tension: 0.4
            }
        ]
    }, { unit: '' });
}

// Update or create chart
function updateChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    if (metricsCharts[canvasId]) {
        metricsCharts[canvasId].data = data;
        metricsCharts[canvasId].update('none');
    } else {
        metricsCharts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#3e3e42',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: { color: '#3e3e42' },
                        ticks: { color: '#888', maxTicksLimit: 8 }
                    },
                    y: {
                        display: true,
                        grid: { color: '#3e3e42' },
                        ticks: { 
                            color: '#888',
                            callback: function(value) {
                                return value + (options.unit || '');
                            }
                        },
                        max: options.max
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
}

// Cleanup on section change
function cleanupMetrics() {
    if (metricsInterval) {
        clearInterval(metricsInterval);
        metricsInterval = null;
    }
    // Clear history when leaving metrics section
    window.metricsHistory = [];
}

// Refresh metrics manually
function refreshMetrics() {
    // Clear history to force fresh data
    window.metricsHistory = [];
    // Show refresh animation
    const btn = document.querySelector('.metrics-refresh-btn i');
    if (btn) {
        btn.classList.add('fa-spin');
        setTimeout(() => btn.classList.remove('fa-spin'), 1000);
    }
    // Load fresh data
    loadMetricsData();
}

// Show API failure details modal
function showFailureDetails() {
    const modal = new bootstrap.Modal(document.getElementById('apiFailureModal'));
    const content = document.getElementById('apiFailureContent');
    
    if (!window.apiFailureData || window.apiFailureData.length === 0) {
        content.innerHTML = '<div class="alert alert-info">No failure data available</div>';
        modal.show();
        return;
    }
    
    // Generate sample failure descriptions
    const failureTypes = [
        { code: 'TIMEOUT', message: 'Request timeout after 30 seconds', severity: 'error' },
        { code: 'CONNECTION_REFUSED', message: 'Connection refused by target service', severity: 'error' },
        { code: 'INVALID_PAYLOAD', message: 'Invalid request payload format', severity: 'warning' },
        { code: 'RATE_LIMIT', message: 'Rate limit exceeded', severity: 'warning' },
        { code: 'SERVICE_UNAVAILABLE', message: 'Target service temporarily unavailable', severity: 'error' },
        { code: 'AUTH_FAILED', message: 'Authentication failed', severity: 'error' }
    ];
    
    let html = '<div class="table-responsive"><table class="table table-sm table-hover">';
    html += '<thead><tr><th>Time</th><th>Error Code</th><th>Description</th><th>Count</th><th>Severity</th></tr></thead><tbody>';
    
    // Show last 10 failure entries
    const recentFailures = window.apiFailureData.slice(-10).reverse();
    recentFailures.forEach(data => {
        if (data.failure > 0) {
            const failure = failureTypes[Math.floor(Math.random() * failureTypes.length)];
            const severityClass = failure.severity === 'error' ? 'danger' : 'warning';
            html += `
                <tr>
                    <td>${data.time.toLocaleTimeString()}</td>
                    <td><code>${failure.code}</code></td>
                    <td>${failure.message}</td>
                    <td><span class="badge bg-${severityClass}">${data.failure}</span></td>
                    <td><span class="badge bg-${severityClass}">${failure.severity.toUpperCase()}</span></td>
                </tr>
            `;
        }
    });
    
    if (recentFailures.filter(d => d.failure > 0).length === 0) {
        html += '<tr><td colspan="5" class="text-center">No failures in recent data</td></tr>';
    }
    
    html += '</tbody></table></div>';
    content.innerHTML = html;
    modal.show();
}
