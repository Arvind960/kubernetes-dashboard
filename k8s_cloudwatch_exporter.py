#!/usr/bin/env python3
"""
Kubernetes Metrics to CloudWatch Exporter
Collects metrics from Kubernetes and sends to CloudWatch
"""
import boto3
import time
import logging
from datetime import datetime
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class K8sCloudWatchExporter:
    def __init__(self, region='ap-south-1', cluster_name='kubernetes'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.cluster_name = cluster_name
        self.region = region
        
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
    
    def send_metric(self, namespace, metric_name, value, unit='None', dimensions=None):
        """Send a metric to CloudWatch"""
        try:
            dims = [{'Name': 'ClusterName', 'Value': self.cluster_name}]
            if dimensions:
                dims.extend(dimensions)
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': dims
                }]
            )
            logger.debug(f"Sent metric: {metric_name}={value}")
        except Exception as e:
            logger.error(f"Failed to send metric {metric_name}: {e}")
    
    def collect_cluster_metrics(self):
        """Collect cluster-level metrics"""
        try:
            nodes = self.v1.list_node()
            pods = self.v1.list_pod_for_all_namespaces()
            
            ready_nodes = sum(1 for n in nodes.items 
                            if any(c.type == 'Ready' and c.status == 'True' 
                                  for c in n.status.conditions))
            failed_nodes = len(nodes.items) - ready_nodes
            
            running_pods = sum(1 for p in pods.items if p.status.phase == 'Running')
            failed_pods = sum(1 for p in pods.items if p.status.phase == 'Failed')
            pending_pods = sum(1 for p in pods.items if p.status.phase == 'Pending')
            
            self.send_metric('ContainerInsights', 'cluster_node_count', len(nodes.items), 'Count')
            self.send_metric('ContainerInsights', 'cluster_failed_node_count', failed_nodes, 'Count')
            self.send_metric('ContainerInsights', 'namespace_number_of_running_pods', running_pods, 'Count')
            self.send_metric('ContainerInsights', 'pod_failed_count', failed_pods, 'Count')
            self.send_metric('ContainerInsights', 'pod_pending_count', pending_pods, 'Count')
            
            logger.info(f"Cluster metrics: {len(nodes.items)} nodes, {running_pods} running pods")
        except Exception as e:
            logger.error(f"Failed to collect cluster metrics: {e}")
    
    def collect_pod_metrics(self):
        """Collect pod-level metrics"""
        try:
            pods = self.v1.list_pod_for_all_namespaces()
            
            for pod in pods.items:
                if pod.status.phase != 'Running':
                    continue
                
                namespace = pod.metadata.namespace
                pod_name = pod.metadata.name
                
                # Container count
                container_count = len(pod.spec.containers) if pod.spec.containers else 0
                ready_containers = sum(1 for c in (pod.status.container_statuses or []) if c.ready)
                
                dims = [
                    {'Name': 'Namespace', 'Value': namespace},
                    {'Name': 'PodName', 'Value': pod_name}
                ]
                
                self.send_metric('ContainerInsights', 'pod_container_count', container_count, 'Count', dims)
                self.send_metric('ContainerInsights', 'pod_ready_containers', ready_containers, 'Count', dims)
                
                # Restart count
                restart_count = sum(c.restart_count for c in (pod.status.container_statuses or []))
                self.send_metric('ContainerInsights', 'pod_restart_count', restart_count, 'Count', dims)
            
            logger.info(f"Collected metrics for {len(pods.items)} pods")
        except Exception as e:
            logger.error(f"Failed to collect pod metrics: {e}")
    
    def collect_node_metrics(self):
        """Collect node-level metrics"""
        try:
            nodes = self.v1.list_node()
            
            for node in nodes.items:
                node_name = node.metadata.name
                
                is_ready = any(c.type == 'Ready' and c.status == 'True' 
                             for c in node.status.conditions)
                
                dims = [{'Name': 'NodeName', 'Value': node_name}]
                
                self.send_metric('ContainerInsights', 'node_status', 1 if is_ready else 0, 'None', dims)
                
                # Pod count on node
                pods = self.v1.list_pod_for_all_namespaces(field_selector=f'spec.nodeName={node_name}')
                pod_count = len(pods.items)
                
                self.send_metric('ContainerInsights', 'node_pod_count', pod_count, 'Count', dims)
            
            logger.info(f"Collected metrics for {len(nodes.items)} nodes")
        except Exception as e:
            logger.error(f"Failed to collect node metrics: {e}")
    
    def run(self, interval=60):
        """Run the exporter continuously"""
        logger.info(f"Starting K8s CloudWatch Exporter for cluster: {self.cluster_name}")
        logger.info(f"Sending metrics to region: {self.region}")
        
        while True:
            try:
                logger.info("Collecting metrics...")
                self.collect_cluster_metrics()
                self.collect_pod_metrics()
                self.collect_node_metrics()
                logger.info(f"Metrics sent. Sleeping for {interval}s")
            except Exception as e:
                logger.error(f"Error in collection cycle: {e}")
            
            time.sleep(interval)

if __name__ == '__main__':
    exporter = K8sCloudWatchExporter(region='ap-south-1', cluster_name='kubernetes')
    exporter.run(interval=60)
