#!/bin/bash
# Apply the fix to k8s_dashboard_server_updated.py

echo "Applying multi-namespace query fix..."

# The key change: Remove <namespace> from route path, use query parameter instead

# OLD (line ~1567):
# @app.route('/api/request-metrics/<namespace>')
# def get_request_metrics(namespace):

# NEW:
# @app.route('/api/request-metrics')
# def get_request_metrics():
#     namespace = request.args.get('namespace', 'all')

# OLD (line ~1587):
# if namespace == 'all':

# NEW:
# if not namespace or namespace == 'all':

echo "
CHANGES NEEDED in k8s_dashboard_server_updated.py:

1. Line ~1567: Change route decorator
   FROM: @app.route('/api/request-metrics/<namespace>')
   TO:   @app.route('/api/request-metrics')

2. Line ~1568: Change function signature
   FROM: def get_request_metrics(namespace):
   TO:   def get_request_metrics():

3. Line ~1569: Add query parameter extraction
   ADD:  namespace = request.args.get('namespace', 'all')

4. Line ~1587: Fix condition
   FROM: if namespace == 'all':
   TO:   if not namespace or namespace == 'all':

FRONTEND CHANGES:

Change API calls from:
  /api/request-metrics/all
  /api/request-metrics/default
  /api/request-metrics/production

To:
  /api/request-metrics?namespace=all
  /api/request-metrics?namespace=default
  /api/request-metrics?namespace=production
  /api/request-metrics?namespace=production&pod=app-xyz
"

echo "
TESTING:

# Cluster-wide
curl 'http://localhost:8888/api/request-metrics?namespace=all&time_range=1h'

# Namespace
curl 'http://localhost:8888/api/request-metrics?namespace=default&time_range=1h'

# Pod
curl 'http://localhost:8888/api/request-metrics?namespace=default&pod=nginx&time_range=1h'
"
