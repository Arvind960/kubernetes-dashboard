#!/bin/bash
# Quick Prometheus Integration Check

echo "=== Prometheus Integration Check ==="
echo ""

echo "1. Checking port-forward..."
if ps aux | grep -q "[p]ort-forward.*9090"; then
    echo "   ✅ Port-forward is running"
else
    echo "   ❌ Port-forward is NOT running"
    echo "   Run: ./start_prometheus_forward.sh"
fi
echo ""

echo "2. Checking Prometheus health..."
if curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -q "Healthy"; then
    echo "   ✅ Prometheus is healthy"
else
    echo "   ❌ Prometheus is not accessible"
fi
echo ""

echo "3. Checking dashboard API..."
STATUS=$(curl -s http://localhost:8888/api/prometheus/status 2>/dev/null | grep -o '"connected":[^,]*')
if echo "$STATUS" | grep -q "true"; then
    echo "   ✅ Dashboard connected to Prometheus"
else
    echo "   ❌ Dashboard NOT connected to Prometheus"
fi
echo ""

echo "4. Testing metrics fetch..."
if curl -s "http://localhost:8888/api/prometheus/metrics?namespace=test-application" 2>/dev/null | grep -q "cpu"; then
    echo "   ✅ Metrics are being fetched"
else
    echo "   ❌ No metrics data"
fi
echo ""

echo "=== Summary ==="
if ps aux | grep -q "[p]ort-forward.*9090" && curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -q "Healthy"; then
    echo "✅ Prometheus integration is WORKING"
    echo ""
    echo "Open dashboard: http://localhost:8888"
    echo "Go to Metrics tab and look for green 'Prometheus' badge"
else
    echo "❌ Prometheus integration is NOT working"
    echo ""
    echo "To fix, run:"
    echo "  cd /root/kubernetes-dashboard"
    echo "  ./start_prometheus_forward.sh"
fi
echo ""
