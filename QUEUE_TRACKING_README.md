# Enhanced Queue Size and Issue Tracking

## New Features Added to Topology Map

### 1. Queue Size Display
- **On Nodes**: Shows `⏳ Q:X` where X is the number of waiting containers
- **On Edges**: Displays queue size on connections to queued pods
- **In Details**: Shows exact queue size with color coding

### 2. Detailed Issue Reasons

#### Queue Issues (Orange/Yellow)
When you click on a queued pod, you'll see:
- **Container name** that's waiting
- **Reason**: ImagePullBackOff, CrashLoopBackOff, CreateContainerError, etc.
- **Message**: Detailed error message (first 100 chars)

Example:
```
📋 Queue Issues:
  bad-image: ImagePullBackOff
  → Failed to pull image "nonexistent-image:invalid-tag": rpc error: code = Unknown
```

#### Error Details (Red)
For failed/crashed pods:
- **Container name** that failed
- **Termination reason**: Error, OOMKilled, ContainerCannotRun, etc.
- **Exit code**: Shows the container exit code
- **Pod conditions**: Unschedulable, InsufficientMemory, etc.

Example:
```
❌ Error Details:
  crash-container: Error (exit 1)
  Pod: Unschedulable - 0/3 nodes are available: insufficient memory
```

### 3. Visual Indicators

**On Graph Nodes:**
- `⏳ Q:2` - 2 containers waiting in queue
- `🔄 5` - 5 restarts occurred
- `⚠️ DOWN` - Pod is down/failed

**On Graph Edges:**
- Orange edges with `⏳ Q:1` - Connection to queued pod
- Red edges with `🔄 5` - Connection to frequently restarting pod
- Thicker lines indicate severity

**In Details Panel:**
- **Queue Size**: Highlighted in orange
- **Queue Issues**: Full breakdown of why containers are waiting
- **Error Details**: Complete error information with exit codes
- **Restart Count**: Color-coded (orange >0, red >2)

### 4. Current Issues Being Tracked

#### ImagePullBackOff
- **Queue Size**: 1 (one container waiting)
- **Reason**: Failed to pull image
- **Message**: Image not found or registry error

#### CrashLoopBackOff
- **Queue Size**: 0 (not queued, actively crashing)
- **Restart Count**: Increasing (3, 5, 7...)
- **Error**: Exit code 1, container terminated

#### OOMKilled
- **Queue Size**: 0
- **Restart Count**: Increasing
- **Error**: OOMKilled (exit 137)

#### CreateContainerError
- **Queue Size**: 1
- **Reason**: Configuration error
- **Message**: Invalid volume mount, missing secret, etc.

## How to Use

1. **View Topology**: http://localhost:8888/topology
2. **Click on any pod** with issues
3. **Details panel shows**:
   - Queue size if containers are waiting
   - Specific reasons for queue (ImagePullBackOff, etc.)
   - Error details with exit codes
   - Full diagnostic information

## Example Output

When clicking on a problematic pod:

```
POD: problematic-app-6f7557888d-6dqgf ⚠️ DOWN
Status: CrashLoopBackOff | Node: kube-worker-02 | 🔄 Restarts: 5
❌ Error Details: crash-container: Error (exit 1)
```

When clicking on an image-pull-error pod:

```
POD: image-pull-error-798b87db4c-lxcq4 ⚠️ DOWN
Status: ImagePullBackOff | ⏳ QUEUE SIZE: 1
📋 Queue Issues: bad-image: ImagePullBackOff | → Failed to pull image "nonexistent-image:invalid-tag"
```

## Benefits

- **Instant diagnosis** of why pods are failing
- **Queue visibility** shows bottlenecks
- **Root cause analysis** with detailed error messages
- **Proactive monitoring** of restart patterns
- **Visual indicators** make issues obvious at a glance
