#!/bin/bash
# Complete Prometheus Setup and Integration Script

set -e

echo "=========================================="
echo "Prometheus Setup for Kubernetes Dashboard"
echo "=========================================="
echo ""

# Step 1: Check Kubernetes cluster
echo "Step 1: Checking Kubernetes cluster..."
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible"
    echo "Please ensure kubectl is configured and cluster is running"
    exit 1
fi
echo "✅ Kubernetes cluster is accessible"
echo ""

# Step 2: Install Helm if not present
echo "Step 2: Checking Helm installation..."
if ! command -v helm &> /dev/null; then
    echo "Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi
echo "✅ Helm is installed: $(helm version --short)"
echo ""

# Step 3: Add Prometheus Helm repository
echo "Step 3: Adding Prometheus Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update
echo "✅ Prometheus repository added"
echo ""

# Step 4: Install Prometheus
echo "Step 4: Installing Prometheus..."
if kubectl get namespace monitoring &> /dev/null; then
    echo "⚠️  Monitoring namespace already exists"
else
    kubectl create namespace monitoring
fi

if helm list -n monitoring | grep -q prometheus; then
    echo "⚠️  Prometheus already installed, upgrading..."
    helm upgrade prometheus prometheus-community/kube-prometheus-stack \
      --namespace monitoring \
      --set prometheus.service.type=NodePort \
      --set grafana.enabled=false
else
    echo "Installing Prometheus stack..."
    helm install prometheus prometheus-community/kube-prometheus-stack \
      --namespace monitoring \
      --set prometheus.service.type=NodePort \
      --set grafana.enabled=false
fi
echo "✅ Prometheus installed"
echo ""

# Step 5: Wait for Prometheus to be ready
echo "Step 5: Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
echo "✅ Prometheus is ready"
echo ""

# Step 6: Get Prometheus service details
echo "Step 6: Prometheus service details:"
PROM_PORT=$(kubectl get svc -n monitoring prometheus-kube-prometheus-prometheus -o jsonpath='{.spec.ports[0].nodePort}')
echo "NodePort: $PROM_PORT"
echo ""

# Step 7: Create port-forward script
echo "Step 7: Creating port-forward helper script..."
cat > /root/kubernetes-dashboard/start_prometheus_forward.sh << 'EOF'
#!/bin/bash
echo "Starting Prometheus port-forward on localhost:9090..."
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
EOF
chmod +x /root/kubernetes-dashboard/start_prometheus_forward.sh
echo "✅ Created start_prometheus_forward.sh"
echo ""

# Step 8: Install Python dependencies
echo "Step 8: Installing Python dependencies..."
pip3 install requests -q
echo "✅ Python dependencies installed"
echo ""

echo "=========================================="
echo "✅ Prometheus Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Start Prometheus port-forward (in a separate terminal):"
echo "   cd /root/kubernetes-dashboard"
echo "   ./start_prometheus_forward.sh"
echo ""
echo "2. Test Prometheus connection:"
echo "   curl http://localhost:9090/-/healthy"
echo ""
echo "3. Restart the dashboard to use Prometheus metrics:"
echo "   cd /root/kubernetes-dashboard"
echo "   ./stop_dashboard.sh"
echo "   ./start_dashboard.sh"
echo ""
echo "4. Access Prometheus UI (optional):"
echo "   kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "   Open: http://localhost:9090"
echo ""
