#!/usr/bin/env python3
"""
CloudWatch API endpoints for Kubernetes Dashboard
"""
from flask import Blueprint, jsonify, request
from cloudwatch_integration import CloudWatchMetrics
import logging
import os

logger = logging.getLogger(__name__)

cloudwatch_bp = Blueprint('cloudwatch', __name__, url_prefix='/api/cloudwatch')

# Initialize CloudWatch client
region = os.environ.get('AWS_REGION', 'ap-south-1')
cw_metrics = CloudWatchMetrics(region=region)

@cloudwatch_bp.route('/pod/<namespace>/<pod_name>')
def get_pod_cloudwatch_metrics(namespace, pod_name):
    """Get CloudWatch metrics for a specific pod"""
    minutes = request.args.get('minutes', default=5, type=int)
    metrics = cw_metrics.get_pod_metrics(namespace, pod_name, minutes)
    
    if metrics is None:
        return jsonify({'error': 'CloudWatch not available'}), 503
    
    return jsonify({
        'namespace': namespace,
        'pod_name': pod_name,
        'metrics': metrics,
        'region': region
    })

@cloudwatch_bp.route('/node/<node_name>')
def get_node_cloudwatch_metrics(node_name):
    """Get CloudWatch metrics for a specific node"""
    minutes = request.args.get('minutes', default=5, type=int)
    metrics = cw_metrics.get_node_metrics(node_name, minutes)
    
    if metrics is None:
        return jsonify({'error': 'CloudWatch not available'}), 503
    
    return jsonify({
        'node_name': node_name,
        'metrics': metrics,
        'region': region
    })

@cloudwatch_bp.route('/cluster/<cluster_name>')
def get_cluster_cloudwatch_metrics(cluster_name):
    """Get CloudWatch metrics for the cluster"""
    minutes = request.args.get('minutes', default=5, type=int)
    metrics = cw_metrics.get_cluster_metrics(cluster_name, minutes)
    
    if metrics is None:
        return jsonify({'error': 'CloudWatch not available'}), 503
    
    return jsonify({
        'cluster_name': cluster_name,
        'metrics': metrics,
        'region': region
    })

@cloudwatch_bp.route('/custom')
def get_custom_cloudwatch_metrics():
    """Get custom CloudWatch metrics"""
    namespace = request.args.get('namespace', required=True)
    metric_name = request.args.get('metric_name', required=True)
    dimensions_str = request.args.get('dimensions', '[]')
    minutes = request.args.get('minutes', default=5, type=int)
    
    try:
        import json
        dimensions = json.loads(dimensions_str)
    except:
        return jsonify({'error': 'Invalid dimensions format'}), 400
    
    datapoints = cw_metrics.get_custom_metrics(namespace, metric_name, dimensions, minutes)
    
    if datapoints is None:
        return jsonify({'error': 'Failed to fetch metrics'}), 503
    
    return jsonify({
        'namespace': namespace,
        'metric_name': metric_name,
        'datapoints': datapoints
    })
