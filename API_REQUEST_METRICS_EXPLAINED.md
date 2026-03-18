# API Request Metrics - How It Works

## Overview

API Request Metrics shows HTTP request statistics (Submit, Delivered, Failure) by parsing pod logs.

---

## Current Behavior

### ⚠️ Only Works for `test-application` Namespace

The API metrics are **ONLY** fetched when:
- Namespace = `test-application`
- Pods have label: `app=java-api`

For other namespaces, it shows **simulated data**.

---

## How It Calculates Metrics

### When All Pods Selected (No specific pod)

**Backend Logic:**
```python
# Get all pods with label app=java-api
pod_list = v1.list_namespaced_pod(namespace, label_selector="app=java-api")
pods = pod_list.items

# Loop through ALL pods
for pod in pods:
    # Read logs from each pod
    logs = v1.read_namespaced_pod_log(name=pod.name, namespace=namespace)
    
    # Count requests in logs
    for line in logs:
        if 'GET /' in line and 'HTTP' in line:
            total_requests += 1
            if ' 200 ' in line:
                success_count += 1
            elif ' 404 ' or ' 500 ' in line:
                error_count += 1
```

**Result:**
- **Submit:** Total requests from ALL pods combined
- **Delivered:** Total successful (200) from ALL pods combined
- **Failure:** Total errors (404, 500, 503) from ALL pods combined

---

### When Specific Pods Selected

**Frontend sends:**
```
/api/request-metrics/test-application?pod=pod1,pod2
```

**Backend Logic:**
```python
pod_name = request.args.get('pod', None)  # Gets "pod1,pod2"

if pod_name:
    # Currently only reads FIRST pod
    pods = [v1.read_namespaced_pod(name=pod_name, namespace=namespace)]
```

**⚠️ Current Issue:**
- Only reads the **FIRST** pod from comma-separated list
- Ignores other selected pods

**Result:**
- **Submit:** Requests from FIRST selected pod only
- **Delivered:** Success from FIRST selected pod only
- **Failure:** Errors from FIRST selected pod only

---

## What Gets Counted

### From Pod Logs:

**Submit (Total Requests):**
- Any log line containing: `GET /` and `HTTP`
- Example: `GET /api/data HTTP/1.1`

**Delivered (Success):**
- Log lines with HTTP 200 status
- Example: `GET /api/data HTTP/1.1 200`

**Failure (Errors):**
- Log lines with HTTP 404, 500, or 503
- Example: `GET /api/data HTTP/1.1 500`

**Success Rate:**
```
(Delivered / Submit) * 100
```

---

## Time Range

Controlled by dropdown:
- 5 sec, 10 sec, 30 sec, 60 sec
- 5 min, 15 min, 1 hour, 6 hours

Backend reads logs from last X seconds:
```python
logs = v1.read_namespaced_pod_log(
    name=pod_name,
    namespace=namespace,
    since_seconds=3600  # Last 1 hour
)
```

---

## Current Limitations

### 1. Namespace Specific
- ❌ Only works for `test-application` namespace
- ❌ Other namespaces show simulated data

### 2. Label Dependent
- ❌ Only counts pods with `app=java-api` label
- ❌ Pods without this label are ignored

### 3. Multi-Pod Selection Bug
- ❌ When selecting multiple pods, only FIRST pod is counted
- ❌ Should aggregate all selected pods

### 4. Log Format Dependent
- ❌ Only works if logs contain `GET /` and `HTTP`
- ❌ Different log formats won't be counted

---

## Example Scenarios

### Scenario 1: All Pods in test-application

**Selection:**
- Namespace: test-application
- Pods: (none selected)

**What Happens:**
1. Backend finds all pods with `app=java-api`
2. Reads logs from ALL pods
3. Counts total requests across ALL pods
4. Shows aggregated metrics

**Result:**
- Submit: 500 (total from all pods)
- Delivered: 450 (total success from all pods)
- Failure: 50 (total errors from all pods)

---

### Scenario 2: Specific Pod Selected

**Selection:**
- Namespace: test-application
- Pods: java-api-app-744cbf5944-gmx96

**What Happens:**
1. Backend reads that specific pod
2. Counts requests only from that pod
3. Shows metrics for that pod only

**Result:**
- Submit: 100 (from selected pod)
- Delivered: 90 (from selected pod)
- Failure: 10 (from selected pod)

---

### Scenario 3: Multiple Pods Selected (Current Bug)

**Selection:**
- Namespace: test-application
- Pods: pod1, pod2, pod3

**What SHOULD Happen:**
- Count requests from pod1 + pod2 + pod3

**What ACTUALLY Happens:**
- Only counts requests from pod1
- Ignores pod2 and pod3

---

### Scenario 4: Different Namespace

**Selection:**
- Namespace: demo-app
- Pods: backend-api-xxx

**What Happens:**
- API metrics are NOT fetched
- Shows simulated/random data
- No real log parsing

---

## How to Fix Multi-Pod Selection

Current code:
```python
pod_name = request.args.get('pod', None)  # Gets "pod1,pod2"
if pod_name:
    pods = [v1.read_namespaced_pod(name=pod_name, namespace=namespace)]
```

Should be:
```python
pod_names = request.args.get('pod', '').split(',')
if pod_names and pod_names[0]:
    pods = []
    for name in pod_names:
        pod = v1.read_namespaced_pod(name=name.strip(), namespace=namespace)
        pods.append(pod)
```

---

## Summary

### All Pods Selected:
✅ Aggregates ALL pods with `app=java-api` label
✅ Shows total requests across all pods

### Specific Pod Selected:
✅ Shows metrics for that specific pod only
❌ Multi-pod selection broken (only counts first pod)

### Different Namespace:
❌ Shows simulated data (not real)

### Calculation Method:
- Parses pod logs
- Counts HTTP requests by status code
- Aggregates across selected pods
