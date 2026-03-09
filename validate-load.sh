#!/bin/bash

echo "=== Load Traffic Validation ==="
echo ""
echo "Checking actual request counts from application logs..."
echo ""

# Count requests in last 60 seconds from all pods
echo "1. Actual Request Count (Last 60 seconds):"
TOTAL_REQUESTS=$(kubectl logs -n dsdp -l app=java-api --since=60s 2>/dev/null | grep "GET / HTTP" | wc -l)
echo "   Total Requests: $TOTAL_REQUESTS"
echo "   Requests/second: $((TOTAL_REQUESTS / 60))"
echo ""

# Count by status code
echo "2. Request Status Breakdown:"
SUCCESS_200=$(kubectl logs -n dsdp -l app=java-api --since=60s 2>/dev/null | grep "GET / HTTP" | grep " 200 " | wc -l)
ERRORS=$(kubectl logs -n dsdp -l app=java-api --since=60s 2>/dev/null | grep "GET / HTTP" | grep -v " 200 " | wc -l)
echo "   Success (200): $SUCCESS_200"
echo "   Errors: $ERRORS"
if [ $TOTAL_REQUESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; ($SUCCESS_200 * 100) / $TOTAL_REQUESTS" | bc)
    echo "   Success Rate: ${SUCCESS_RATE}%"
fi
echo ""

# Count per pod
echo "3. Requests per Pod:"
for pod in $(kubectl get pods -n dsdp -l app=java-api -o name); do
    POD_NAME=$(basename $pod)
    POD_REQUESTS=$(kubectl logs -n dsdp $POD_NAME --since=60s 2>/dev/null | grep "GET / HTTP" | wc -l)
    echo "   $POD_NAME: $POD_REQUESTS requests"
done
echo ""

# Load generator status
echo "4. Load Generator Status:"
LOAD_PODS=$(kubectl get pods -n dsdp -l app=load-generator --no-headers 2>/dev/null | wc -l)
LOAD_RUNNING=$(kubectl get pods -n dsdp -l app=load-generator --no-headers 2>/dev/null | grep Running | wc -l)
echo "   Total Load Generators: $LOAD_PODS"
echo "   Running: $LOAD_RUNNING"
echo "   Expected Rate: ~$((LOAD_RUNNING * 6)) req/sec"
echo ""

# Real-time monitoring
echo "5. Real-time Request Monitoring (10 seconds):"
echo "   Counting requests..."
START_COUNT=$(kubectl logs -n dsdp -l app=java-api --tail=1000 2>/dev/null | grep "GET / HTTP" | wc -l)
sleep 10
END_COUNT=$(kubectl logs -n dsdp -l app=java-api --tail=1000 2>/dev/null | grep "GET / HTTP" | wc -l)
REQUESTS_10SEC=$((END_COUNT - START_COUNT))
echo "   Requests in 10 seconds: $REQUESTS_10SEC"
echo "   Current Rate: $((REQUESTS_10SEC * 6)) req/min"
echo ""

echo "=== Validation Complete ==="
echo ""
echo "To continuously monitor:"
echo "  kubectl logs -n dsdp -l app=java-api -f | grep 'GET / HTTP'"
