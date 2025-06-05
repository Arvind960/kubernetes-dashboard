import datetime
from flask import jsonify

def get_pod_health(v1, logger):
    try:
        pod_health_data = []
        pods = v1.list_pod_for_all_namespaces(watch=False)
        
        for pod in pods.items:
            # Basic pod info
            pod_info = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': pod.status.phase,
                'start_time': pod.status.start_time.isoformat() if pod.status.start_time else None,
                'container_statuses': [],
                'potential_issues': []
            }
            
            # Check for container issues
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    container_info = {
                        'name': container.name,
                        'ready': container.ready,
                        'restart_count': container.restart_count,
                        'state': 'unknown'
                    }
                    
                    # Determine container state
                    if container.state.running:
                        container_info['state'] = 'running'
                        container_info['started_at'] = container.state.running.started_at.isoformat() if container.state.running.started_at else None
                    elif container.state.waiting:
                        container_info['state'] = 'waiting'
                        container_info['reason'] = container.state.waiting.reason
                    elif container.state.terminated:
                        container_info['state'] = 'terminated'
                        container_info['reason'] = container.state.terminated.reason
                        container_info['exit_code'] = container.state.terminated.exit_code
                    
                    pod_info['container_statuses'].append(container_info)
            
            # Check for potential hang issues
            detect_hang_issues(pod, pod_info)
            
            pod_health_data.append(pod_info)
        
        return jsonify(pod_health_data)
    except Exception as e:
        logger.error(f"Error getting pod health data: {e}")
        return jsonify({'error': str(e)}), 500

def detect_hang_issues(pod, pod_info):
    """Detect potential hang issues in pods"""
    
    # 1. Check for application deadlock signs (running but not ready for long time)
    if pod.status.phase == 'Running':
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if not container.ready and container.state.running:
                    # Container running but not ready
                    started_time = container.state.running.started_at
                    current_time = datetime.datetime.now(datetime.timezone.utc)
                    running_duration = current_time - started_time
                    
                    if running_duration.total_seconds() > 300:  # 5 minutes threshold
                        pod_info['potential_issues'].append({
                            'type': 'Application Deadlock',
                            'description': f'Container {container.name} running but not ready for {int(running_duration.total_seconds())} seconds',
                            'severity': 'Warning',
                            'duration': str(running_duration).split('.')[0]  # Format as HH:MM:SS
                        })
    
    # 2. Check for resource starvation - we'll use restart count as a proxy since metrics API might not be available
    if pod.status.container_statuses:
        for container in pod.status.container_statuses:
            if container.restart_count > 3 and container.restart_count <= 10:
                pod_info['potential_issues'].append({
                    'type': 'Resource Starvation',
                    'description': f'Container {container.name} has restarted {container.restart_count} times, possible resource issues',
                    'severity': 'Warning',
                    'duration': 'Ongoing'
                })
    
    # 3. Check for crash loop without exiting
    if pod.status.container_statuses:
        for container in pod.status.container_statuses:
            if container.restart_count > 10:
                pod_info['potential_issues'].append({
                    'type': 'Crash Loop',
                    'description': f'Container {container.name} has restarted {container.restart_count} times',
                    'severity': 'Error',
                    'duration': 'Ongoing'
                })
    
    # 4. Check for stuck init containers
    if hasattr(pod.status, 'init_container_statuses') and pod.status.init_container_statuses:
        for init_container in pod.status.init_container_statuses:
            if hasattr(init_container.state, 'waiting') and init_container.state.waiting and init_container.state.waiting.reason != 'PodInitializing':
                pod_info['potential_issues'].append({
                    'type': 'Stuck Init Container',
                    'description': f'Init container {init_container.name} stuck: {init_container.state.waiting.reason}',
                    'severity': 'Error',
                    'duration': 'Ongoing'
                })
    
    # 5. Check for volume mount issues - if pod is stuck in ContainerCreating for a long time
    if pod.status.phase == 'Pending':
        if hasattr(pod, 'status') and hasattr(pod.status, 'conditions'):
            for condition in pod.status.conditions:
                if condition.type == 'PodScheduled' and condition.status == 'True':
                    # Pod is scheduled but still pending - might be volume issues
                    if pod.status.start_time:
                        current_time = datetime.datetime.now(datetime.timezone.utc)
                        pending_duration = current_time - pod.status.start_time
                        
                        if pending_duration.total_seconds() > 300:  # 5 minutes threshold
                            pod_info['potential_issues'].append({
                                'type': 'Volume Mount Issue',
                                'description': f'Pod stuck in Pending state for {int(pending_duration.total_seconds())} seconds',
                                'severity': 'Warning',
                                'duration': str(pending_duration).split('.')[0]  # Format as HH:MM:SS
                            })

def restart_pod(v1, namespace, pod_name, logger):
    try:
        # Delete the pod (it will be recreated by its controller)
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error restarting pod {pod_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
