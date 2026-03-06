import boto3
import json
import logging
from kubernetes import client
from datetime import datetime

logger = logging.getLogger(__name__)

class K8sAIChatbot:
    def __init__(self, v1_api, apps_v1_api):
        self.v1 = v1_api
        self.apps_v1 = apps_v1_api
        self.conversation_history = []
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            self.ai_enabled = True
            logger.info("AI Chatbot initialized with AWS Bedrock")
        except Exception as e:
            self.ai_enabled = False
            logger.warning(f"AI not available: {e}")
    
    def get_detailed_cluster_context(self):
        """Get comprehensive cluster state for AI context"""
        try:
            pods = self.v1.list_pod_for_all_namespaces()
            services = self.v1.list_service_for_all_namespaces()
            deployments = self.apps_v1.list_deployment_for_all_namespaces()
            nodes = self.v1.list_node()
            namespaces = self.v1.list_namespace()
            
            # Detailed pod analysis
            pod_status = {'Running': 0, 'Pending': 0, 'Failed': 0, 'CrashLoopBackOff': 0, 'Unknown': 0}
            pod_issues = []
            restart_issues = []
            
            for p in pods.items:
                phase = p.status.phase
                pod_status[phase] = pod_status.get(phase, 0) + 1
                
                # Check for issues
                if phase in ['Failed', 'CrashLoopBackOff', 'Pending', 'Unknown']:
                    reason = "Unknown"
                    if p.status.container_statuses:
                        for cs in p.status.container_statuses:
                            if cs.state.waiting:
                                reason = cs.state.waiting.reason
                            elif cs.state.terminated:
                                reason = cs.state.terminated.reason
                    pod_issues.append(f"{p.metadata.namespace}/{p.metadata.name}: {phase} ({reason})")
                
                # Check restart counts
                if p.status.container_statuses:
                    for cs in p.status.container_statuses:
                        if cs.restart_count > 3:
                            restart_issues.append(f"{p.metadata.namespace}/{p.metadata.name}: {cs.restart_count} restarts")
            
            # Node analysis
            node_status = {'Ready': 0, 'NotReady': 0}
            node_issues = []
            for n in nodes.items:
                ready = any(c.type == 'Ready' and c.status == 'True' for c in n.status.conditions)
                node_status['Ready' if ready else 'NotReady'] += 1
                
                if not ready:
                    node_issues.append(f"{n.metadata.name}: Not Ready")
                
                # Check for pressure
                for cond in n.status.conditions:
                    if cond.type in ['MemoryPressure', 'DiskPressure', 'PIDPressure'] and cond.status == 'True':
                        node_issues.append(f"{n.metadata.name}: {cond.type}")
            
            # Deployment analysis
            deploy_issues = []
            for d in deployments.items:
                ready = d.status.ready_replicas or 0
                desired = d.spec.replicas or 0
                if ready < desired:
                    deploy_issues.append(f"{d.metadata.namespace}/{d.metadata.name}: {ready}/{desired} ready")
            
            # Service analysis
            svc_without_endpoints = []
            for svc in services.items:
                try:
                    endpoints = self.v1.read_namespaced_endpoints(svc.metadata.name, svc.metadata.namespace)
                    if not endpoints.subsets or not any(s.addresses for s in endpoints.subsets):
                        svc_without_endpoints.append(f"{svc.metadata.namespace}/{svc.metadata.name}")
                except:
                    pass
            
            context = f"""=== CLUSTER OVERVIEW ===
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Namespaces: {len(namespaces.items)}
Nodes: {len(nodes.items)} ({node_status['Ready']} ready, {node_status['NotReady']} not ready)
Pods: {len(pods.items)} (Running: {pod_status.get('Running', 0)}, Pending: {pod_status.get('Pending', 0)}, Failed: {pod_status.get('Failed', 0)})
Deployments: {len(deployments.items)} ({len(deploy_issues)} unhealthy)
Services: {len(services.items)} ({len(svc_without_endpoints)} without endpoints)

=== CRITICAL ISSUES ==="""
            
            if pod_issues:
                context += f"\nPod Issues ({len(pod_issues)}):\n" + "\n".join(f"  • {i}" for i in pod_issues[:10])
            
            if restart_issues:
                context += f"\n\nHigh Restart Counts ({len(restart_issues)}):\n" + "\n".join(f"  • {i}" for i in restart_issues[:5])
            
            if node_issues:
                context += f"\n\nNode Issues ({len(node_issues)}):\n" + "\n".join(f"  • {i}" for i in node_issues)
            
            if deploy_issues:
                context += f"\n\nDeployment Issues ({len(deploy_issues)}):\n" + "\n".join(f"  • {i}" for i in deploy_issues[:10])
            
            if svc_without_endpoints:
                context += f"\n\nServices Without Endpoints ({len(svc_without_endpoints)}):\n" + "\n".join(f"  • {i}" for i in svc_without_endpoints[:5])
            
            if not any([pod_issues, restart_issues, node_issues, deploy_issues, svc_without_endpoints]):
                context += "\nNo critical issues detected. Cluster is healthy! ✓"
            
            return context
        except Exception as e:
            return f"Error getting cluster context: {str(e)}"
    
    def get_ai_response(self, user_message):
        """Get AI-powered response using AWS Bedrock with conversation history"""
        if not self.ai_enabled:
            return self.get_fallback_response(user_message)
        
        try:
            cluster_context = self.get_detailed_cluster_context()
            
            # Build conversation context
            conversation = ""
            for msg in self.conversation_history[-4:]:  # Last 2 exchanges
                conversation += f"\nUser: {msg['user']}\nAssistant: {msg['assistant']}\n"
            
            prompt = f"""You are an expert Kubernetes SRE providing production-grade troubleshooting guidance.

{cluster_context}

Previous Conversation:
{conversation if conversation else "None"}

Current Question: {user_message}

Provide a comprehensive response with:

**🔍 ANALYSIS**
What's happening and severity level (Critical/Warning/Info)

**🎯 ROOT CAUSE**
Why this is occurring (be specific)

**✅ SOLUTION**
Step-by-step fix with exact kubectl commands:
```bash
# Command with explanation
kubectl command here
```

**🛡️ PREVENTION**
How to avoid this in future (monitoring, best practices)

**📊 VERIFICATION**
How to confirm the fix worked

Be concise, actionable, and production-ready. Use emojis for clarity."""

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            # Store conversation
            self.conversation_history.append({
                'user': user_message,
                'assistant': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 exchanges
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"AI error: {e}")
            return self.get_fallback_response(user_message)
    
    def get_ai_response(self, user_message):
        """Get AI-powered response using AWS Bedrock with conversation history"""
        if not self.ai_enabled:
            return self.get_fallback_response(user_message)
        
        try:
            cluster_context = self.get_detailed_cluster_context()
            
            # Build conversation context
            conversation = ""
            for msg in self.conversation_history[-4:]:  # Last 2 exchanges
                conversation += f"\nUser: {msg['user']}\nAssistant: {msg['assistant']}\n"
            
            prompt = f"""You are an expert Kubernetes SRE providing production-grade troubleshooting guidance.

{cluster_context}

Previous Conversation:
{conversation if conversation else "None"}

Current Question: {user_message}

Provide a comprehensive response with:

**🔍 ANALYSIS**
What's happening and severity level (Critical/Warning/Info)

**🎯 ROOT CAUSE**
Why this is occurring (be specific)

**✅ SOLUTION**
Step-by-step fix with exact kubectl commands:
```bash
# Command with explanation
kubectl command here
```

**🛡️ PREVENTION**
How to avoid this in future (monitoring, best practices)

**📊 VERIFICATION**
How to confirm the fix worked

Be concise, actionable, and production-ready. Use emojis for clarity."""

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            # Store conversation
            self.conversation_history.append({
                'user': user_message,
                'assistant': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 exchanges
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"AI error: {e}")
            return self.get_fallback_response(user_message)
    
    def get_fallback_response(self, user_message):
        """Fallback responses with troubleshooting guidance when AI is not available"""
        msg = user_message.lower()
        
        try:
            if 'pod' in msg and ('fail' in msg or 'crash' in msg or 'error' in msg):
                pods = self.v1.list_pod_for_all_namespaces()
                failed = [(p.metadata.namespace, p.metadata.name, p.status.phase) for p in pods.items 
                         if p.status.phase in ['Failed', 'CrashLoopBackOff', 'Error']]
                
                if failed:
                    response = "**Failed Pods Detected:**\n\n"
                    for ns, name, phase in failed[:5]:
                        response += f"• {ns}/{name} - {phase}\n"
                    
                    response += "\n**Troubleshooting Steps:**\n"
                    response += "1. Check logs: kubectl logs <pod-name> -n <namespace>\n"
                    response += "2. Describe pod: kubectl describe pod <pod-name> -n <namespace>\n"
                    response += "3. Check events: kubectl get events -n <namespace>\n"
                    response += "4. Verify resources: kubectl top pod <pod-name> -n <namespace>\n\n"
                    response += "**Common Causes:**\n"
                    response += "• Image pull errors\n• Resource limits exceeded\n• Configuration issues\n• Application crashes"
                    return response
                return "No failed pods found. Cluster is healthy!"
            
            elif 'pending' in msg:
                pods = self.v1.list_pod_for_all_namespaces()
                pending = [(p.metadata.namespace, p.metadata.name) for p in pods.items if p.status.phase == 'Pending']
                
                if pending:
                    response = f"**{len(pending)} Pending Pods:**\n\n"
                    for ns, name in pending[:5]:
                        response += f"• {ns}/{name}\n"
                    
                    response += "\n**Troubleshooting:**\n"
                    response += "1. Check node resources: kubectl describe nodes\n"
                    response += "2. Check pod details: kubectl describe pod <pod-name> -n <namespace>\n"
                    response += "3. Verify PVCs: kubectl get pvc -A\n\n"
                    response += "**Common Causes:**\n"
                    response += "• Insufficient CPU/memory\n• No available nodes\n• PVC not bound\n• Node selector mismatch"
                    return response
                return "No pending pods."
            
            elif 'node' in msg:
                nodes = self.v1.list_node()
                ready = sum(1 for n in nodes.items if any(c.type == 'Ready' and c.status == 'True' for c in n.status.conditions))
                not_ready = len(nodes.items) - ready
                
                response = f"**Node Status:**\n• Total: {len(nodes.items)}\n• Ready: {ready}\n• Not Ready: {not_ready}\n\n"
                
                if not_ready > 0:
                    response += "**Troubleshooting Not Ready Nodes:**\n"
                    response += "1. Check node status: kubectl get nodes\n"
                    response += "2. Describe node: kubectl describe node <node-name>\n"
                    response += "3. Check kubelet: systemctl status kubelet\n"
                    response += "4. View logs: journalctl -u kubelet -f\n\n"
                    response += "**Common Issues:**\n"
                    response += "• Network connectivity\n• Disk pressure\n• Memory pressure\n• Kubelet not running"
                else:
                    response += "All nodes are healthy! ✓"
                return response
            
            elif 'deployment' in msg:
                deployments = self.apps_v1.list_deployment_for_all_namespaces()
                unhealthy = [(d.metadata.namespace, d.metadata.name, d.status.ready_replicas or 0, d.spec.replicas or 0) 
                            for d in deployments.items if (d.status.ready_replicas or 0) < (d.spec.replicas or 0)]
                
                if unhealthy:
                    response = f"**{len(unhealthy)} Unhealthy Deployments:**\n\n"
                    for ns, name, ready, desired in unhealthy[:5]:
                        response += f"• {ns}/{name} - {ready}/{desired} ready\n"
                    
                    response += "\n**Troubleshooting:**\n"
                    response += "1. Check deployment: kubectl describe deployment <name> -n <namespace>\n"
                    response += "2. Check pods: kubectl get pods -n <namespace> -l app=<name>\n"
                    response += "3. Check events: kubectl get events -n <namespace>\n"
                    response += "4. Rollout status: kubectl rollout status deployment/<name> -n <namespace>\n\n"
                    response += "**Common Issues:**\n"
                    response += "• Image pull failures\n• Resource constraints\n• Liveness/readiness probe failures\n• Configuration errors"
                    return response
                return f"All {len(deployments.items)} deployments are healthy! ✓"
            
            elif 'service' in msg:
                services = self.v1.list_service_for_all_namespaces()
                response = f"**Services:** {len(services.items)} total\n\n"
                response += "**Check Service Issues:**\n"
                response += "1. List services: kubectl get svc -A\n"
                response += "2. Check endpoints: kubectl get endpoints -A\n"
                response += "3. Describe service: kubectl describe svc <name> -n <namespace>\n"
                response += "4. Test connectivity: kubectl run test --rm -it --image=busybox -- wget -O- <service-name>\n\n"
                response += "**Common Issues:**\n"
                response += "• No endpoints (selector mismatch)\n• Port configuration errors\n• Network policy blocking traffic"
                return response
            
            elif 'help' in msg or 'guide' in msg or 'manual' in msg or 'how to' in msg:
                return """**📖 Kubernetes Dashboard User Guide**

**What I Can Help With:**
• Failed/Crashed pods
• Pending pods  
• Node issues
• Deployment problems
• Service connectivity
• Resource usage
• Cluster health

**Example Questions:**
• "Why are my pods failing?"
• "Show pending pods"
• "Check node health"
• "Deployment issues"
• "Service connectivity problems"
• "Show cluster health"

**Troubleshooting Commands:**
```bash
# View pod logs
kubectl logs <pod-name> -n <namespace>

# Describe resources
kubectl describe pod/deployment/service <name> -n <namespace>

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Resource usage
kubectl top nodes
kubectl top pods -A

# Restart deployment
kubectl rollout restart deployment/<name> -n <namespace>
```

**Dashboard Features:**
• Real-time metrics monitoring
• Pod health status
• Deployment control (pause/resume)
• Network topology view
• CloudWatch integration
• AI-powered troubleshooting

**Quick Actions:**
• Click pod name for details
• Use pause/resume buttons for deployments
• Filter by namespace
• Refresh for latest data

**Need More Help?**
• Documentation: /root/kubernetes-dashboard/README.md
• SRE Guide: /root/kubernetes-dashboard/SRE_TROUBLESHOOTING_GUIDE.md
• Architecture: /root/kubernetes-dashboard/ARCHITECTURE.md

Ask me any specific question about your cluster!"""
            
            else:
                return "I can help troubleshoot:\n• Failed/Crashed pods\n• Pending pods\n• Node issues\n• Deployment problems\n• Service connectivity\n\nWhat would you like to investigate?"
        
        except Exception as e:
            return f"Error: {str(e)}"
