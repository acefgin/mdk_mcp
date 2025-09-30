# Kubernetes Deployment for qPCR Assistant

Production-grade Kubernetes deployment for AutoGen-powered qPCR assay design system with MCP servers.

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Kubernetes Cluster (ndiag-qpcr)       │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  LoadBalancer Service                     │  │
│  │  (qpcr-assistant:80)                      │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼───────────────────────────┐  │
│  │  qPCR Assistant Deployment               │  │
│  │  - Replicas: 3-10 (auto-scaling)         │  │
│  │  - AutoGen agents                        │  │
│  │  - MCP client bridge                     │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                                │
│  ┌──────────────▼───────────────────────────┐  │
│  │  Database MCP Server StatefulSet         │  │
│  │  - Replicas: 2 (HA)                      │  │
│  │  - Persistent cache (10Gi per pod)       │  │
│  │  - Headless service                      │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  Persistent Volumes                       │  │
│  │  - Results: 100Gi (ReadWriteMany)        │  │
│  │  - Cache: 10Gi per pod (ReadWriteOnce)   │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   - kubectl configured
   - Sufficient resources (8+ vCPUs, 16+ GB RAM)

2. **Container Images**
   ```bash
   docker build -t ndiag-database-server:latest ./mcp_servers/database_server
   docker build -t qpcr-assistant:latest ./autogen_app
   ```

3. **Secrets**
   - OpenAI API key
   - NCBI API key (optional, for higher rate limits)

## Deployment Steps

### 1. Create Namespace
```bash
kubectl apply -f kubernetes/namespace.yaml
```

### 2. Configure Secrets
```bash
# OpenAI API Key
kubectl create secret generic qpcr-assistant-secrets \
  --from-literal=OPENAI_API_KEY=your_key_here \
  --namespace=ndiag-qpcr

# NCBI API Key (optional)
kubectl create secret generic database-server-secrets \
  --from-literal=NCBI_API_KEY=your_ncbi_key \
  --namespace=ndiag-qpcr
```

### 3. Deploy MCP Servers
```bash
# Database server (Phase 1)
kubectl apply -f kubernetes/database-server.yaml

# Verify deployment
kubectl get statefulset -n ndiag-qpcr
kubectl get pods -n ndiag-qpcr -l component=database-server
```

### 4. Deploy qPCR Assistant
```bash
kubectl apply -f kubernetes/qpcr-assistant.yaml

# Verify deployment
kubectl get deployment -n ndiag-qpcr
kubectl get pods -n ndiag-qpcr -l component=qpcr-assistant
```

### 5. Access the Application
```bash
# Get LoadBalancer IP
kubectl get service qpcr-assistant -n ndiag-qpcr

# Access via browser
# http://<EXTERNAL-IP>
```

## Scaling

### Manual Scaling
```bash
# Scale qPCR assistant
kubectl scale deployment qpcr-assistant --replicas=5 -n ndiag-qpcr

# Scale database servers
kubectl scale statefulset database-server --replicas=3 -n ndiag-qpcr
```

### Auto-Scaling
HorizontalPodAutoscaler automatically scales qPCR assistant based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Min replicas: 3
- Max replicas: 10

```bash
# Check HPA status
kubectl get hpa -n ndiag-qpcr
```

## Monitoring

### Pod Status
```bash
# Watch all pods
kubectl get pods -n ndiag-qpcr -w

# Check specific pod logs
kubectl logs -f <pod-name> -n ndiag-qpcr
```

### Resource Usage
```bash
# CPU and memory usage
kubectl top pods -n ndiag-qpcr
kubectl top nodes
```

### Service Health
```bash
# Check endpoints
kubectl get endpoints -n ndiag-qpcr

# Test service connectivity
kubectl run test-pod --image=busybox --rm -it -n ndiag-qpcr -- sh
# Inside pod: wget -O- http://database-server-0.database-server:8000/health
```

## Troubleshooting

### Pods Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name> -n ndiag-qpcr

# Check logs
kubectl logs <pod-name> -n ndiag-qpcr --previous
```

### MCP Connection Issues
```bash
# Verify database server is accessible
kubectl exec -it qpcr-assistant-xxx -n ndiag-qpcr -- sh
# Inside pod: ping database-server-0.database-server
```

### Storage Issues
```bash
# Check PVCs
kubectl get pvc -n ndiag-qpcr

# Check PV status
kubectl get pv
```

## Updating Deployments

### Rolling Update
```bash
# Update image
kubectl set image deployment/qpcr-assistant \
  qpcr-assistant=qpcr-assistant:v2.0 \
  -n ndiag-qpcr

# Check rollout status
kubectl rollout status deployment/qpcr-assistant -n ndiag-qpcr
```

### Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/qpcr-assistant -n ndiag-qpcr

# Rollback to specific revision
kubectl rollout undo deployment/qpcr-assistant --to-revision=2 -n ndiag-qpcr
```

## Backup and Restore

### Backup Results
```bash
# Create backup pod
kubectl run backup --image=alpine --rm -it -n ndiag-qpcr \
  --overrides='{"spec":{"volumes":[{"name":"results","persistentVolumeClaim":{"claimName":"results-pvc"}}],"containers":[{"name":"backup","image":"alpine","command":["tar","czf","/backup/results.tar.gz","-C","/results","."],"volumeMounts":[{"name":"results","mountPath":"/results"}]}]}}'
```

### Restore Results
```bash
# Similar process with tar extraction
```

## Cleanup

### Remove Everything
```bash
# Delete all resources in namespace
kubectl delete namespace ndiag-qpcr
```

### Remove Specific Components
```bash
# Remove qPCR assistant only
kubectl delete -f kubernetes/qpcr-assistant.yaml

# Remove database server
kubectl delete -f kubernetes/database-server.yaml
```

## Production Checklist

- [ ] Configure resource limits appropriately
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation (ELK/Loki)
- [ ] Enable network policies for security
- [ ] Configure pod security policies
- [ ] Set up backup automation
- [ ] Configure alerts for failures
- [ ] Test disaster recovery procedures
- [ ] Document runbooks
- [ ] Enable RBAC for access control

## Cost Optimization

1. **Right-size Resources**: Monitor actual usage and adjust requests/limits
2. **Use Node Affinity**: Place MCP servers on same nodes to reduce latency
3. **Implement Pod Disruption Budgets**: Ensure availability during updates
4. **Use Spot Instances**: For non-critical workloads
5. **Configure Cluster Autoscaler**: Scale nodes based on demand

## Security Best Practices

1. **Network Policies**: Restrict pod-to-pod communication
2. **Pod Security Standards**: Enforce restricted profile
3. **Secret Management**: Use external secret managers (Vault, AWS Secrets Manager)
4. **Image Scanning**: Scan container images for vulnerabilities
5. **RBAC**: Implement least-privilege access control
