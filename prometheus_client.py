"""
Prometheus Integration for Kubernetes Dashboard
Fetches metrics from Prometheus and provides them to the dashboard
"""

import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PrometheusClient:
    def __init__(self, prometheus_url="http://localhost:9090"):
        self.base_url = prometheus_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
    
    def query(self, query):
        """Execute a PromQL query"""
        try:
            response = requests.get(f"{self.api_url}/query", params={'query': query}, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus query failed: {e}")
            return None
    
    def query_range(self, query, start, end, step='15s'):
        """Execute a PromQL range query"""
        try:
            params = {
                'query': query,
                'start': start,
                'end': end,
                'step': step
            }
            response = requests.get(f"{self.api_url}/query_range", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus range query failed: {e}")
            return None
    
    def get_pod_cpu_usage(self, namespace=None, pod_name=None, duration='5m'):
        """Get CPU usage for pods"""
        query = 'rate(container_cpu_usage_seconds_total{container!=""}[5m])'
        if namespace:
            query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}",container!=""}}[5m])'
        if pod_name:
            query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}",pod="{pod_name}",container!=""}}[5m])'
        
        return self.query(query)
    
    def get_pod_memory_usage(self, namespace=None, pod_name=None):
        """Get memory usage for pods"""
        query = 'container_memory_working_set_bytes{container!=""}'
        if namespace:
            query = f'container_memory_working_set_bytes{{namespace="{namespace}",container!=""}}'
        if pod_name:
            query = f'container_memory_working_set_bytes{{namespace="{namespace}",pod="{pod_name}",container!=""}}'
        
        return self.query(query)
    
    def get_pod_network_receive(self, namespace=None, pod_name=None):
        """Get network receive bytes for pods"""
        query = 'rate(container_network_receive_bytes_total[5m])'
        if namespace:
            query = f'rate(container_network_receive_bytes_total{{namespace="{namespace}"}}[5m])'
        if pod_name:
            query = f'rate(container_network_receive_bytes_total{{namespace="{namespace}",pod="{pod_name}"}}[5m])'
        
        return self.query(query)
    
    def get_pod_network_transmit(self, namespace=None, pod_name=None):
        """Get network transmit bytes for pods"""
        query = 'rate(container_network_transmit_bytes_total[5m])'
        if namespace:
            query = f'rate(container_network_transmit_bytes_total{{namespace="{namespace}"}}[5m])'
        if pod_name:
            query = f'rate(container_network_transmit_bytes_total{{namespace="{namespace}",pod="{pod_name}"}}[5m])'
        
        return self.query(query)
    
    def get_metrics_range(self, namespace=None, pod_names=None, duration_minutes=60):
        """Get time-series metrics for the dashboard"""
        end = datetime.now()
        start = end - timedelta(minutes=duration_minutes)
        
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        
        metrics = {
            'cpu': [],
            'memory': [],
            'network_rx': [],
            'network_tx': []
        }
        
        # Build query filters
        filter_str = ''
        if namespace:
            filter_str = f'namespace="{namespace}"'
        if pod_names:
            pod_filter = '|'.join(pod_names)
            if filter_str:
                filter_str += f',pod=~"{pod_filter}"'
            else:
                filter_str = f'pod=~"{pod_filter}"'
        
        # CPU query
        cpu_query = f'rate(container_cpu_usage_seconds_total{{{filter_str},container!=""}}[5m])'
        cpu_data = self.query_range(cpu_query, start_ts, end_ts)
        if cpu_data and cpu_data.get('status') == 'success':
            metrics['cpu'] = cpu_data.get('data', {}).get('result', [])
        
        # Memory query
        mem_query = f'container_memory_working_set_bytes{{{filter_str},container!=""}}'
        mem_data = self.query_range(mem_query, start_ts, end_ts)
        if mem_data and mem_data.get('status') == 'success':
            metrics['memory'] = mem_data.get('data', {}).get('result', [])
        
        # Network RX query
        rx_query = f'rate(container_network_receive_bytes_total{{{filter_str}}}[5m])'
        rx_data = self.query_range(rx_query, start_ts, end_ts)
        if rx_data and rx_data.get('status') == 'success':
            metrics['network_rx'] = rx_data.get('data', {}).get('result', [])
        
        # Network TX query
        tx_query = f'rate(container_network_transmit_bytes_total{{{filter_str}}}[5m])'
        tx_data = self.query_range(tx_query, start_ts, end_ts)
        if tx_data and tx_data.get('status') == 'success':
            metrics['network_tx'] = tx_data.get('data', {}).get('result', [])
        
        return metrics
    
    def check_connection(self):
        """Check if Prometheus is accessible"""
        try:
            response = requests.get(f"{self.base_url}/-/healthy", timeout=3)
            return response.status_code == 200
        except:
            return False
