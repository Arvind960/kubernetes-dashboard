# Minimal fix for multi-namespace API request metrics

# REPLACE the existing route in k8s_dashboard_server_updated.py

@app.route('/api/request-metrics')
def get_request_metrics():
    """Get API request metrics with proper all-namespace support"""
    namespace = request.args.get('namespace', 'all')
    pod_name = request.args.get('pod', None)
    time_range = request.args.get('time_range', '1h')
    
    time_map = {'5s': 5, '10s': 10, '30s': 30, '60s': 60, '5m': 300, '15m': 900, '1h': 3600, '6h': 21600}
    since_seconds = time_map.get(time_range, 3600)
    
    try:
        # Determine scope
        if not namespace or namespace == 'all':
            # Cluster-wide
            namespaces_list = v1.list_namespace()
            pods = []
            for ns in namespaces_list.items:
                try:
                    pod_list = v1.list_namespaced_pod(ns.metadata.name)
                    pods.extend(pod_list.items)
                except:
                    pass
        elif pod_name:
            # Specific pod
            pods = [v1.read_namespaced_pod(name=pod_name, namespace=namespace)]
        else:
            # Namespace-level
            pod_list = v1.list_namespaced_pod(namespace)
            pods = pod_list.items
        
        total_requests = 0
        success_count = 0
        error_count = 0
        
        for pod in pods:
            try:
                logs = v1.read_namespaced_pod_log(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    since_seconds=since_seconds
                )
                
                for line in logs.split('\n'):
                    if ('GET /' in line or '"GET /' in line) and 'HTTP' in line:
                        total_requests += 1
                        if ' 200 ' in line or '" 200 ' in line:
                            success_count += 1
                        elif ' 404 ' in line or '" 404 ' in line or ' 500 ' in line or '" 500 ' in line or ' 503 ' in line or '" 503 ' in line:
                            error_count += 1
            except:
                pass
        
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 100
        
        return jsonify({
            'submit': total_requests,
            'delivered': success_count,
            'failure': error_count,
            'success_rate': round(success_rate, 2),
            'time_range': time_range
        })
    except Exception as e:
        logger.error(f"Error getting request metrics: {e}")
        return jsonify({'submit': 0, 'delivered': 0, 'failure': 0, 'success_rate': 0, 'time_range': time_range})


# PROMETHEUS-BASED IMPLEMENTATION (Better Performance)

class PrometheusMetrics:
    """Add to prometheus_client.py"""
    
    def get_api_request_metrics(self, namespace=None, pod=None, duration='5m'):
        """Get API request metrics with dynamic filtering"""
        
        # Build filter
        filters = []
        if namespace:
            filters.append(f'namespace="{namespace}"')
        if pod:
            filters.append(f'pod="{pod}"')
        filter_str = ','.join(filters)
        
        # Queries
        submit_query = f'sum(rate(http_requests_total{{{filter_str}}}[{duration}]))'
        delivered_query = f'sum(rate(http_requests_total{{{filter_str},status=~"2.."}}[{duration}]))'
        failure_query = f'sum(rate(http_requests_total{{{filter_str},status=~"[45].."}}[{duration}]))'
        
        submit = self.query(submit_query)
        delivered = self.query(delivered_query)
        failure = self.query(failure_query)
        
        return {
            'submit': self._extract_value(submit),
            'delivered': self._extract_value(delivered),
            'failure': self._extract_value(failure)
        }
    
    def _extract_value(self, result):
        """Extract scalar value from Prometheus result"""
        if result and result.get('status') == 'success':
            data = result.get('data', {}).get('result', [])
            if data:
                return float(data[0].get('value', [0, 0])[1])
        return 0
