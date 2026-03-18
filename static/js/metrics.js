// Metrics Dashboard JavaScript
let metricsCharts = {};
let metricsInterval = null;

// Initialize metrics dashboard
function initMetricsDashboard() {
    loadNamespaces();
    loadMetricsData();
    checkPrometheusStatus();
    
    // Auto-refresh every 30 seconds
    if (metricsInterval) clearInterval(metricsInterval);
    metricsInterval = setInterval(loadMetricsData, 30000);
}

// Check Prometheus status
async function checkPrometheusStatus() {
    try {
        const response = await fetch('/api/prometheus/status');
        const status = await response.json();
        const indicator = document.getElementById('prometheusStatus');
        
        if (status.connected) {
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    } catch (error) {
        document.getElementById('prometheusStatus').style.display = 'none';
    }
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
        const selectedPods = Array.from(document.querySelectorAll('#metricsPodDropdown input[type="checkbox"]:checked')).map(cb => cb.value);
        const timeRange = document.getElementById('metricsTimeRange').value;
        
        const response = await fetch('/api/data');
        const data = await response.json();
        
        // Filter pods
        let pods = data.pods;
        if (namespace) pods = pods.filter(p => p.namespace === namespace);
        if (selectedPods.length > 0) pods = pods.filter(p => selectedPods.includes(p.name));
        
        // Update pod selector
        updatePodSelector(data.pods, namespace);
        
        // Calculate metrics - pass all pods for uptime calculation
        const metrics = calculateMetrics(pods.length > 0 ? pods : data.pods);
        
        // Try to fetch Prometheus metrics first
        try {
            const promStatusResponse = await fetch('/api/prometheus/status');
            const promStatus = await promStatusResponse.json();
            
            if (promStatus.connected) {
                // Fetch real metrics from Prometheus
                let promUrl = `/api/prometheus/metrics?duration=60`;
                if (namespace) promUrl += `&namespace=${namespace}`;
                if (selectedPods.length > 0) {
                    selectedPods.forEach(pod => promUrl += `&pod=${pod}`);
                }
                
                const promResponse = await fetch(promUrl);
                if (promResponse.ok) {
                    const promData = await promResponse.json();
                    
                    // Convert Prometheus data to chart format
                    if (promData.cpu && promData.cpu.length > 0) {
                        metrics.cpu = convertPrometheusToChart(promData.cpu, 'cpu');
                    }
                    if (promData.memory && promData.memory.length > 0) {
                        metrics.memory = convertPrometheusToChart(promData.memory, 'memory');
                    }
                    if (promData.network_rx && promData.network_rx.length > 0) {
                        metrics.network.rx = convertPrometheusToChart(promData.network_rx, 'network');
                    }
                    if (promData.network_tx && promData.network_tx.length > 0) {
                        metrics.network.tx = convertPrometheusToChart(promData.network_tx, 'network');
                    }
                    
                    console.log('✅ Using Prometheus metrics');
                }
            }
        } catch (error) {
            console.log('⚠️ Prometheus not available, using simulated metrics');
        }
        
        // Fetch real API metrics for any namespace
        try {
            const apiNamespace = namespace || 'all';
            let apiUrl = `/api/request-metrics/${apiNamespace}?time_range=${timeRange}`;
            if (selectedPods.length > 0 && namespace) {
                apiUrl += `&pod=${selectedPods.join(',')}`;
            }
            
            const apiResponse = await fetch(apiUrl);
            const apiData = await apiResponse.json();
            
            // Store historical data
            if (!window.metricsHistory) {
                window.metricsHistory = [];
            }
            
            // Add current data point with current timestamp
                const now = new Date();
                window.metricsHistory.push({
                    time: now,
                    submit: apiData.submit,
                    delivered: apiData.delivered,
                    failure: apiData.failure,
                    successRate: apiData.success_rate
                });
                
                // Keep only last 20 data points
                if (window.metricsHistory.length > 20) {
                    window.metricsHistory.shift();
                }
                
                // Build chart data with proper time alignment
                metrics.apiRequests = [];
                
                // If we have less than 20 points, pad with zeros at the beginning
                const paddingNeeded = 20 - window.metricsHistory.length;
                for (let i = 0; i < paddingNeeded; i++) {
                    const time = new Date(now - (19 - i) * 60000);
                    metrics.apiRequests.push({
                        time: time,
                        submit: 0,
                        delivered: 0,
                        failure: 0,
                        successRate: 0
                    });
                }
                
                // Add actual historical data with aligned timestamps
                window.metricsHistory.forEach((h, index) => {
                    const alignedTime = new Date(now - (window.metricsHistory.length - 1 - index) * 60000);
                    metrics.apiRequests.push({
                        time: alignedTime,
                        submit: h.submit,
                        delivered: h.delivered,
                        failure: h.failure,
                        successRate: h.successRate
                    });
                });
                
        } catch (error) {
            console.log('Using simulated API metrics');
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
    const container = document.getElementById('metricsPodDropdown');
    const currentChecked = Array.from(document.querySelectorAll('#metricsPodDropdown input[type="checkbox"]:checked')).map(cb => cb.value);
    
    let pods = allPods;
    if (namespace) pods = pods.filter(p => p.namespace === namespace);
    
    if (pods.length === 0) {
        container.innerHTML = '<div style="color: #888; font-size: 11px; padding: 2px;">No pods</div>';
        updatePodLabel();
        return;
    }
    
    container.innerHTML = '';
    pods.forEach(pod => {
        const label = document.createElement('label');
        label.onmouseover = () => label.style.background = '#3e3e42';
        label.onmouseout = () => label.style.background = 'transparent';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = pod.name;
        checkbox.checked = currentChecked.includes(pod.name);
        checkbox.onchange = () => {
            updatePodLabel();
            loadMetricsData();
        };
        
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(pod.name));
        container.appendChild(label);
    });
    
    updatePodLabel();
}

// Toggle pod dropdown
function togglePodDropdown() {
    const dropdown = document.getElementById('metricsPodDropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
}

// Update pod label
function updatePodLabel() {
    const selected = Array.from(document.querySelectorAll('#metricsPodDropdown input[type="checkbox"]:checked'));
    const label = document.getElementById('metricsPodLabel');
    if (selected.length === 0) {
        label.textContent = 'Select pods...';
    } else if (selected.length === 1) {
        label.textContent = selected[0].value;
    } else {
        label.textContent = `${selected.length} pods selected`;
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('metricsPodDropdown');
    const button = document.getElementById('metricsPodButton');
    if (dropdown && button && !button.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// Convert Prometheus data to chart format
function convertPrometheusToChart(promData, type) {
    const now = new Date();
    const chartData = [];
    
    // Aggregate all series data
    const timeMap = new Map();
    
    promData.forEach(series => {
        if (series.values && series.values.length > 0) {
            series.values.forEach(([timestamp, value]) => {
                const time = new Date(timestamp * 1000);
                const key = time.getTime();
                
                if (!timeMap.has(key)) {
                    timeMap.set(key, { time: time, values: [] });
                }
                
                let numValue = parseFloat(value);
                if (type === 'cpu') {
                    numValue = numValue; // CPU is in cores
                } else if (type === 'memory') {
                    numValue = numValue / (1024 * 1024); // Convert to MB
                } else if (type === 'network') {
                    numValue = numValue / 1024; // Convert to KB/s
                }
                
                timeMap.get(key).values.push(numValue);
            });
        }
    });
    
    // Average values for each timestamp and take last 20 points
    const sortedTimes = Array.from(timeMap.keys()).sort();
    const lastTimes = sortedTimes.slice(-20);
    
    lastTimes.forEach(key => {
        const data = timeMap.get(key);
        const avgValue = data.values.reduce((a, b) => a + b, 0) / data.values.length;
        
        if (type === 'memory') {
            chartData.push({ time: data.time, value: avgValue, limit: 256 });
        } else {
            chartData.push({ time: data.time, value: avgValue });
        }
    });
    
    return chartData.length > 0 ? chartData : null;
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
async function showFailureDetails() {
    const modal = new bootstrap.Modal(document.getElementById('apiFailureModal'));
    const content = document.getElementById('apiFailureContent');
    
    const currentNamespace = document.getElementById('metricsNamespace')?.value || 'all';
    const timeRange = document.getElementById('metricsTimeRange')?.value || '1h';
    
    content.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    modal.show();
    
    try {
        const response = await fetch(`/api/failure-details?namespace=${currentNamespace}&time_range=${timeRange}`);
        const data = await response.json();
        
        if (data.failures && data.failures.length > 0) {
            let html = '<div class="table-responsive"><table class="table table-sm table-hover">';
            html += '<thead><tr><th>Time</th><th>Namespace</th><th>Pod</th><th>Error Code</th><th>Description</th><th>Count</th><th>Severity</th></tr></thead><tbody>';
            
            data.failures.forEach(failure => {
                const severityClass = failure.severity === 'CRITICAL' ? 'danger' : 
                                    failure.severity === 'ERROR' ? 'warning' : 'info';
                
                html += `<tr>
                    <td><small class="text-muted">${failure.time}</small></td>
                    <td><span class="badge bg-info">${failure.namespace}</span></td>
                    <td><code>${failure.pod}</code></td>
                    <td><span class="badge bg-secondary">${failure.error_code}</span></td>
                    <td><small>${failure.description}</small></td>
                    <td><span class="badge bg-${severityClass}">${failure.count}</span></td>
                    <td><span class="badge bg-${severityClass}">${failure.severity}</span></td>
                </tr>`;
            });
            
            html += '</tbody></table></div>';
            const namespaceText = currentNamespace === 'all' ? 'all namespaces' : `namespace: ${currentNamespace}`;
            html += `<div class="text-muted text-center mt-2"><small>Total: ${data.total} failures (${namespaceText}, ${timeRange} timeframe)</small></div>`;
            content.innerHTML = html;
        } else {
            content.innerHTML = '<div class="alert alert-success">No API failures found for the selected time range</div>';
        }
    } catch (error) {
        console.error('Error loading failure details:', error);
        content.innerHTML = '<div class="alert alert-danger">Error loading failure details</div>';
    }
}
