#!/bin/bash
export AWS_REGION=ap-south-1
cd /root/kubernetes-dashboard

echo "Testing CloudWatch Integration..."
echo "================================="
echo ""

# Get EKS cluster name
CLUSTER_NAME=$(kubectl config current-context 2>/dev/null | cut -d'/' -f2 || echo "my-cluster")
echo "Cluster: $CLUSTER_NAME"
echo ""

# Start server in background
python3 k8s_dashboard_server_updated.py > /tmp/dashboard.log 2>&1 &
SERVER_PID=$!
echo "Dashboard started (PID: $SERVER_PID)"
sleep 3

# Test endpoints
echo ""
echo "Testing CloudWatch endpoints:"
echo "-----------------------------"

# Test cluster metrics
echo "1. Cluster metrics:"
curl -s http://localhost:5000/api/cloudwatch/cluster/$CLUSTER_NAME | python3 -m json.tool 2>/dev/null || echo "No data yet"

echo ""
echo "2. Available pods:"
kubectl get pods -A --no-headers 2>/dev/null | head -3

# Kill server
kill $SERVER_PID 2>/dev/null
echo ""
echo "Test complete. Check logs at /tmp/dashboard.log"
