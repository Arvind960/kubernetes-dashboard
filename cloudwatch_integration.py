#!/usr/bin/env python3
"""
CloudWatch Integration for Kubernetes Dashboard
Fetches and displays CloudWatch metrics alongside Kubernetes metrics
"""
import boto3
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class CloudWatchMetrics:
    def __init__(self, region='ap-south-1'):
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.region = region
            logger.info(f"CloudWatch client initialized for region: {region}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            self.cloudwatch = None
    
    def get_pod_metrics(self, namespace, pod_name, minutes=5):
        """Get CloudWatch Container Insights metrics for a pod"""
        if not self.cloudwatch:
            return None
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        metrics = {}
        metric_queries = [
            ('pod_cpu_utilization', 'ContainerInsights', 'pod_cpu_utilization'),
            ('pod_memory_utilization', 'ContainerInsights', 'pod_memory_utilization'),
            ('pod_network_rx_bytes', 'ContainerInsights', 'pod_network_rx_bytes'),
            ('pod_network_tx_bytes', 'ContainerInsights', 'pod_network_tx_bytes'),
            ('pod_restart_count', 'ContainerInsights', 'pod_restart_count'),
            ('pod_container_count', 'ContainerInsights', 'pod_container_count'),
            ('pod_ready_containers', 'ContainerInsights', 'pod_ready_containers'),
        ]
        
        for key, namespace_cw, metric_name in metric_queries:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=namespace_cw,
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'PodName', 'Value': pod_name},
                        {'Name': 'Namespace', 'Value': namespace}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                if response['Datapoints']:
                    latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                    metrics[key] = {
                        'average': latest.get('Average', 0),
                        'maximum': latest.get('Maximum', 0),
                        'timestamp': latest['Timestamp'].isoformat()
                    }
            except ClientError as e:
                logger.warning(f"Failed to get {metric_name}: {e}")
        
        return metrics
    
    def get_node_metrics(self, node_name, minutes=5):
        """Get CloudWatch metrics for a node"""
        if not self.cloudwatch:
            return None
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        metrics = {}
        metric_queries = [
            ('node_cpu_utilization', 'ContainerInsights', 'node_cpu_utilization'),
            ('node_memory_utilization', 'ContainerInsights', 'node_memory_utilization'),
            ('node_filesystem_utilization', 'ContainerInsights', 'node_filesystem_utilization'),
            ('node_status', 'ContainerInsights', 'node_status'),
            ('node_pod_count', 'ContainerInsights', 'node_pod_count'),
        ]
        
        for key, namespace_cw, metric_name in metric_queries:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=namespace_cw,
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'NodeName', 'Value': node_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                if response['Datapoints']:
                    latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                    metrics[key] = {
                        'average': latest.get('Average', 0),
                        'maximum': latest.get('Maximum', 0),
                        'timestamp': latest['Timestamp'].isoformat()
                    }
            except ClientError as e:
                logger.warning(f"Failed to get {metric_name}: {e}")
        
        return metrics
    
    def get_cluster_metrics(self, cluster_name, minutes=5):
        """Get CloudWatch metrics for entire cluster"""
        if not self.cloudwatch:
            return None
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        metrics = {}
        metric_queries = [
            ('cluster_failed_node_count', 'ContainerInsights', 'cluster_failed_node_count'),
            ('cluster_node_count', 'ContainerInsights', 'cluster_node_count'),
            ('namespace_number_of_running_pods', 'ContainerInsights', 'namespace_number_of_running_pods'),
            ('pod_failed_count', 'ContainerInsights', 'pod_failed_count'),
            ('pod_pending_count', 'ContainerInsights', 'pod_pending_count'),
        ]
        
        for key, namespace_cw, metric_name in metric_queries:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=namespace_cw,
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'ClusterName', 'Value': cluster_name}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Average', 'Maximum', 'Sum']
                )
                if response['Datapoints']:
                    latest = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])[-1]
                    metrics[key] = {
                        'value': latest.get('Sum', latest.get('Average', 0)),
                        'timestamp': latest['Timestamp'].isoformat()
                    }
            except ClientError as e:
                logger.warning(f"Failed to get {metric_name}: {e}")
        
        return metrics
    
    def get_custom_metrics(self, namespace, metric_name, dimensions, minutes=5):
        """Get custom CloudWatch metrics"""
        if not self.cloudwatch:
            return None
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Sum', 'Maximum', 'Minimum']
            )
            return response['Datapoints']
        except ClientError as e:
            logger.error(f"Failed to get custom metric {metric_name}: {e}")
            return None
