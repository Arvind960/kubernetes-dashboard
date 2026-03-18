#!/bin/bash
echo "Starting Prometheus port-forward on localhost:9090..."
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
