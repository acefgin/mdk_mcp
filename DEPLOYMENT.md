# Deployment Guide: qPCR Assistant with AutoGen + MCP

Complete deployment guide for the multi-agent qPCR assay design system.

## Quick Start (Docker Compose)

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key
- (Optional) NCBI API key for higher rate limits

### 1. Clone and Configure
```bash
git clone <repository>
cd mdk_mcp

# Copy environment template
cp autogen_app/.env.template autogen_app/.env

# Edit .env and add your OpenAI API key
nano autogen_app/.env
```

### 2. Build and Start
```bash
# Build all services
docker-compose -f docker-compose.autogen.yml build

# Start services
docker-compose -f docker-compose.autogen.yml up -d

# Check status
docker-compose -f docker-compose.autogen.yml ps
```

### 3. Verify MCP Servers
```bash
# Check database server is running
docker logs ndiag-database-server

# Test MCP connection
docker exec -i ndiag-database-server python -c "
import asyncio
from database_mcp_server import handle_list_tools
print('MCP Server is operational')
"
```

### 4. Run qPCR Assistant
```bash
# View logs
docker logs -f qpcr-assistant

# Or run interactively
docker-compose -f docker-compose.autogen.yml run --rm qpcr-assistant python qpcr_assistant.py
```

### 5. Stop Services
```bash
docker-compose -f docker-compose.autogen.yml down
```

## Production Deployment (Kubernetes)

### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- Container registry (Docker Hub, GCR, ECR, etc.)

### 1. Build and Push Images
```bash
# Build images
docker build -t <your-registry>/ndiag-database-server:v1.0 ./mcp_servers/database_server
docker build -t <your-registry>/qpcr-assistant:v1.0 ./autogen_app

# Push to registry
docker push <your-registry>/ndiag-database-server:v1.0
docker push <your-registry>/qpcr-assistant:v1.0
```

### 2. Configure Secrets
```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Create OpenAI API key secret
kubectl create secret generic qpcr-assistant-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key-here \
  --namespace=ndiag-qpcr

# Create NCBI API key secret (optional)
kubectl create secret generic database-server-secrets \
  --from-literal=NCBI_API_KEY=your-ncbi-key \
  --namespace=ndiag-qpcr
```

### 3. Deploy Services
```bash
# Deploy database MCP server
kubectl apply -f kubernetes/database-server.yaml

# Wait for database server to be ready
kubectl wait --for=condition=ready pod -l component=database-server -n ndiag-qpcr --timeout=120s

# Deploy qPCR assistant
kubectl apply -f kubernetes/qpcr-assistant.yaml

# Check deployment
kubectl get all -n ndiag-qpcr
```

### 4. Access the Application
```bash
# Get LoadBalancer IP
kubectl get service qpcr-assistant -n ndiag-qpcr

# Or use port-forward for testing
kubectl port-forward service/qpcr-assistant 8501:80 -n ndiag-qpcr
# Access at http://localhost:8501
```

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     User Interface Layer                      │
│  (CLI / Streamlit / API)                                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                AutoGen Multi-Agent System                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Coordinator  │  │   Database   │  │   Analyst    │       │
│  │    Agent     │◄─┤     Agent    │◄─┤    Agent     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │                │
│         └──────────────────┼──────────────────┘                │
└───────────────────────────┼──────────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │ MCP Client      │
                   │    Bridge       │
                   └────────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│   Database     │  │ Processing  │  │   Alignment     │
│  MCP Server    │  │ MCP Server  │  │  MCP Server     │
│  (Phase 1) ✅  │  │ (Phase 2)⏳ │  │  (Phase 3)⏳    │
└────────────────┘  └─────────────┘  └─────────────────┘
```

## Component Roles

### 1. MCP Servers (Bioinformatics Tools)
- **Database Server** (Phase 1): Sequence retrieval, taxonomy, SRA search
- **Processing Server** (Phase 2): QC, deduplication, chimera detection
- **Alignment Server** (Phase 3): Multiple sequence alignment, phylogenetics
- **Design Server** (Phase 4): Primer design, signature region finding
- **Validation Server** (Phase 5): BLAST validation, in-silico PCR
- **Export Server** (Phase 6): Results export, report generation

### 2. AutoGen Agents
- **Coordinator Agent**: Orchestrates workflow, interprets user intent
- **Database Agent**: Uses MCP database tools to retrieve sequences
- **Analyst Agent**: Analyzes sequences, recommends primer strategies
- **Designer Agent**: Designs primers (when Phase 4 complete)
- **Validator Agent**: Validates designs (when Phase 5 complete)

### 3. MCP Client Bridge
- Connects AutoGen agents to MCP servers via stdio protocol
- Translates AutoGen function calls to MCP tool calls
- Handles async communication and error recovery

## Usage Examples

### Example 1: Basic Species Identification
```python
user_request = """
Design a qPCR assay to identify Pacific salmon (Oncorhynchus spp.)
and distinguish from Atlantic salmon (Salmo salar).
Target region: COI
"""

await assistant.run_workflow(user_request)
```

**Expected Workflow**:
1. Coordinator interprets request
2. Database Agent retrieves COI sequences for:
   - Oncorhynchus genus (target)
   - Salmo salar (off-target)
3. Database Agent identifies other Salmonidae species
4. Analyst Agent analyzes sequences for signature regions
5. Coordinator summarizes findings and recommends next steps

### Example 2: Advanced Multi-Species Panel
```python
user_request = """
Design a multiplex qPCR panel for aquaculture species verification:
- Atlantic salmon (Salmo salar)
- Rainbow trout (Oncorhynchus mykiss)
- Arctic char (Salvelinus alpinus)

Requirements:
- Species-specific assays for each
- Internal control (18S rRNA)
- Minimal cross-reactivity with other salmonids
"""

await assistant.run_workflow(user_request)
```

## Monitoring and Troubleshooting

### Docker Compose

**View Logs**:
```bash
# All services
docker-compose -f docker-compose.autogen.yml logs -f

# Specific service
docker-compose -f docker-compose.autogen.yml logs -f qpcr-assistant
docker-compose -f docker-compose.autogen.yml logs -f database-server
```

**Check Service Health**:
```bash
# List running containers
docker-compose -f docker-compose.autogen.yml ps

# Check resource usage
docker stats
```

**Debug MCP Connection**:
```bash
# Enter database server
docker exec -it ndiag-database-server sh

# Test MCP tools
python -c "from database_mcp_server import handle_list_tools; import asyncio; asyncio.run(handle_list_tools())"
```

### Kubernetes

**View Logs**:
```bash
# qPCR assistant logs
kubectl logs -f deployment/qpcr-assistant -n ndiag-qpcr

# Database server logs
kubectl logs -f statefulset/database-server -n ndiag-qpcr

# Follow specific pod
kubectl logs -f <pod-name> -n ndiag-qpcr
```

**Check Pod Status**:
```bash
# All pods
kubectl get pods -n ndiag-qpcr

# With more details
kubectl describe pod <pod-name> -n ndiag-qpcr
```

**Debug Inside Pod**:
```bash
# Enter qPCR assistant pod
kubectl exec -it deployment/qpcr-assistant -n ndiag-qpcr -- sh

# Enter database server pod
kubectl exec -it database-server-0 -n ndiag-qpcr -- sh
```

**Check Service Connectivity**:
```bash
# Test database server from qpcr-assistant
kubectl exec -it deployment/qpcr-assistant -n ndiag-qpcr -- sh
# Inside pod:
ping database-server-0.database-server
```

## Performance Tuning

### Docker Compose

**Resource Limits**:
Edit `docker-compose.autogen.yml` to adjust:
```yaml
services:
  qpcr-assistant:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### Kubernetes

**Horizontal Scaling**:
```bash
# Scale qPCR assistant manually
kubectl scale deployment qpcr-assistant --replicas=5 -n ndiag-qpcr

# Scale database servers
kubectl scale statefulset database-server --replicas=3 -n ndiag-qpcr
```

**Auto-Scaling** (already configured via HPA):
- Scales based on CPU (70%) and memory (80%)
- Min: 3 replicas
- Max: 10 replicas

**Resource Adjustments**:
Edit `kubernetes/qpcr-assistant.yaml`:
```yaml
resources:
  requests:
    memory: "2Gi"  # Increase for larger workflows
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "8000m"
```

## Security Considerations

1. **API Keys**: Store in secrets, never commit to git
2. **Network Policies**: Restrict pod-to-pod communication in production
3. **RBAC**: Implement least-privilege access in Kubernetes
4. **Image Scanning**: Scan containers for vulnerabilities
5. **TLS**: Enable HTTPS for external access

## Cost Optimization

1. **Right-size Resources**: Monitor actual usage and adjust
2. **Use Spot Instances**: For non-critical workloads (Kubernetes)
3. **Implement Caching**: MCP servers cache frequently accessed data
4. **Batch Requests**: Process multiple designs in single session
5. **Shutdown When Idle**: Stop services when not in use (Docker Compose)

## Backup and Recovery

### Docker Compose
```bash
# Backup results
docker cp qpcr-assistant:/results ./backups/results_$(date +%Y%m%d)

# Backup database cache
docker cp ndiag-database-server:/tmp/mcp_cache ./backups/cache_$(date +%Y%m%d)
```

### Kubernetes
```bash
# Backup using PVC snapshot (if supported)
kubectl create volumesnapshot results-snapshot \
  --volume=results-pvc \
  --namespace=ndiag-qpcr

# Or manually copy data
kubectl cp ndiag-qpcr/<pod-name>:/results ./backups/
```

## Upgrade Path

### Adding New MCP Servers (Future Phases)

1. **Build new server**:
   ```bash
   docker build -t ndiag-processing-server:latest ./mcp_servers/processing_server
   ```

2. **Add to docker-compose.autogen.yml**:
   ```yaml
   processing-server:
     build: ./mcp_servers/processing_server
     container_name: ndiag-processing-server
     stdin_open: true
     networks:
       - ndiag-network
   ```

3. **Update AutoGen bridge**:
   ```python
   server_configs = {
       "database": {...},
       "processing": {
           "container": "ndiag-processing-server",
           "command": ["python", "/app/processing_mcp_server.py"]
       }
   }
   ```

4. **Add functions to AutoGen**:
   Update `create_autogen_functions()` with new processing tools

## Support

For issues and questions:
- Check logs first (see Monitoring section)
- Review AUTOGEN_INTEGRATION.md for architecture details
- Check PHASE1_STATUS.md for implementation status
- Open issues on GitHub repository

## Next Steps

After deployment:
1. Test with example workflows
2. Monitor performance and resource usage
3. Implement Phase 2 (Processing) MCP server
4. Expand agent capabilities as more phases complete
5. Add custom agents for specific use cases
