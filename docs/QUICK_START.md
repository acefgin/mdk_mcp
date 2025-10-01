# qPCR Assistant - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- Basic understanding of qPCR assay design

### 1. Setup Environment

```bash
cd /home/raycifeng/mdk_mcp

# Create .env file with your API key
echo "OPENAI_API_KEY=sk-your-key-here" > autogen_app/.env

# Optional: Add NCBI API key for higher rate limits
echo "NCBI_API_KEY=your-ncbi-key" >> autogen_app/.env
```

### 2. Start the System

```bash
# Start all containers
docker compose -f docker-compose.autogen.yml up -d

# Verify containers are running
docker ps | grep -E 'qpcr|database'
```

Expected output:
```
qpcr-assistant         Up 30 seconds
ndiag-database-server  Up 30 seconds (unhealthy)
```
*Note: database-server showing "unhealthy" is normal for MCP stdio servers*

### 3. Monitor Activity

```bash
# Watch real-time logs
docker logs -f qpcr-assistant

# You should see:
# ✓ "MCP servers connected"
# ✓ "Created 3 agents"
# ✓ "Starting qPCR design workflow"
# ✓ Agents exchanging messages
# ✓ "Task log saved to: /results/task_*.json"
```

### 4. Access Results

```bash
# List all task logs
docker exec qpcr-assistant ls -lh /results

# View latest summary
docker exec qpcr-assistant cat \
  $(docker exec qpcr-assistant ls -t /results/*_summary.txt | head -1)

# Copy logs to your machine
docker cp qpcr-assistant:/results ./qpcr_logs
```

## 📊 Understanding the Workflow

The system automatically runs a demo workflow on startup. Here's what happens:

### Step 1: User Request (Automatic)
```
Design a qPCR assay to identify Atlantic salmon (Salmo salar)
and distinguish it from rainbow trout (Oncorhynchus mykiss)
```

### Step 2: Coordinator Agent
- Analyzes the request
- Creates a step-by-step plan
- Coordinates with other agents

### Step 3: DatabaseAgent
**Uses MCP Tools to:**
- ✅ `get_sequences`: Retrieves COI sequences from NCBI
- ✅ Returns ~100 sequences for Salmo salar
- ✅ Each sequence ~500-700 bp

**Example Tool Call:**
```json
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Salmo salar",
    "region": "COI",
    "source": "ncbi",
    "max_results": 100
  },
  "status": "SUCCESS",
  "result_length": 292015
}
```

### Step 4: AnalystAgent
- Analyzes retrieved sequences
- Identifies conserved regions
- Recommends primer design strategy

### Step 5: Results Saved
```
/results/
├── task_20251001_175526.json          # Machine-readable
└── task_20251001_175526_summary.txt   # Human-readable
```

## 🔍 Viewing Task Logs

### Quick Stats
```bash
docker exec qpcr-assistant cat /results/task_*.json | \
  jq '.statistics'
```

Output:
```json
{
  "total_agents": 2,
  "total_actions": 2,
  "total_tool_calls": 1,
  "successful_tool_calls": 1,
  "failed_tool_calls": 0,
  "total_messages": 6
}
```

### Tool Call Details
```bash
docker exec qpcr-assistant cat /results/task_*.json | \
  jq '.tool_calls[] | {agent, tool, success}'
```

Output:
```json
{
  "agent": "DatabaseAgent",
  "tool": "get_sequences",
  "success": true
}
```

### Agent Actions
```bash
docker exec qpcr-assistant cat /results/task_*.json | \
  jq '.agents[] | {agent, action}'
```

Output:
```json
{
  "agent": "user",
  "action": "message"
}
{
  "agent": "Coordinator",
  "action": "message"
}
```

## 🎯 Current Capabilities

### ✅ Working Features

1. **Multi-Agent Collaboration**
   - Coordinator, DatabaseAgent, AnalystAgent
   - Automatic task delegation
   - Coordinated workflow execution

2. **MCP Tool Integration**
   - `get_sequences`: Retrieve sequences from NCBI/BOLD
   - `get_taxonomy`: Taxonomic information
   - `get_neighbors`: Find related species
   - `extract_sequence_columns`: Parse metadata
   - `search_sra_studies`: Search SRA database

3. **Task Logging**
   - JSON logs for programmatic access
   - Human-readable summaries
   - Timestamp tracking
   - Success/failure tracking
   - Statistics generation

4. **Sequence Retrieval**
   - ✅ NCBI GenBank access
   - ✅ BOLD Systems database
   - ✅ Multiple regions: COI, 16S, ITS, etc.
   - ✅ Handles large responses (292KB+)

### 🚧 Limitations

1. **Static Workflow**: Currently runs predefined demo
2. **No Interactive Mode**: Can't submit custom requests yet
3. **Limited Analysis**: Primer design is recommendation-only (Phase 4 tools not implemented)
4. **No Validation**: Primer validation tools not available (Phase 5)

## 📝 How Agents Work Per Task

### Example: "Design qPCR for Atlantic Salmon"

**Timeline:**
```
[00:00] User submits request
[00:01] Coordinator receives and analyzes
[00:02] Coordinator creates workflow plan
[00:05] DatabaseAgent called
[00:06] DatabaseAgent uses get_sequences tool
        ↓
        MCP Bridge → Database Server → NCBI API
        ↓
[00:20] Returns 100 sequences (292KB)
[00:21] AnalystAgent analyzes sequences
[00:23] AnalystAgent provides recommendations
[00:24] Workflow completes
[00:24] Logs saved to /results
```

**Agent Breakdown:**

| Agent | Actions | Tools Used | Output |
|-------|---------|------------|--------|
| Coordinator | 1 message | None | Workflow plan |
| DatabaseAgent | 1 message | get_sequences | 100 COI sequences |
| AnalystAgent | 1 message | None | Analysis & recommendations |

## 🔧 Customization (Advanced)

### Modify the Request

Edit `autogen_app/qpcr_assistant.py`, line 456:

```python
user_request = """
YOUR CUSTOM REQUEST HERE

Requirements:
- Target: [Your species]
- Off-targets: [Related species]
- Genomic region: [COI/16S/ITS/etc.]
- Application: [Your use case]

Please:
1. Retrieve sequences for target and off-targets
2. Identify other potential cross-reactive species
3. Analyze sequences to find signature regions
4. Recommend primer design strategy
"""
```

Then rebuild:
```bash
docker compose -f docker-compose.autogen.yml up --build -d
```

### Add More Tools

When Phase 4 tools become available, add them to DatabaseAgent:

```python
tools=[
    self.mcp_tools.get_sequences,
    self.mcp_tools.get_taxonomy,
    self.mcp_tools.get_neighbors,
    # Phase 4 tools:
    # self.mcp_tools.find_signature_regions,
    # self.mcp_tools.design_primers,
]
```

## 🐛 Troubleshooting

### Container Exits Immediately

**Check API key:**
```bash
docker logs qpcr-assistant --tail 20
# Should NOT see: "OPENAI_API_KEY environment variable not set"
```

**Fix:**
```bash
# Ensure .env file exists
cat autogen_app/.env

# Recreate container
docker compose -f docker-compose.autogen.yml up --force-recreate -d
```

### No Sequences Retrieved

**Check MCP connection:**
```bash
docker logs qpcr-assistant 2>&1 | grep "MCP servers connected"
```

**Check tool calls:**
```bash
docker logs qpcr-assistant 2>&1 | grep "Calling database"
```

**Check for errors:**
```bash
docker logs qpcr-assistant 2>&1 | grep -i error
```

### Task Logs Not Created

**Verify directory:**
```bash
docker exec qpcr-assistant ls -la /results
```

**Check permissions:**
```bash
docker exec qpcr-assistant touch /results/test.txt
docker exec qpcr-assistant rm /results/test.txt
```

## 📚 Next Steps

1. **Read Full Documentation**
   - `USER_GUIDE.md` - Complete interaction guide
   - `AUTOGEN_INTEGRATION.md` - Technical details
   - `CLAUDE.md` - Project overview

2. **Explore Logs**
   - Review generated task logs
   - Understand agent workflows
   - Analyze tool call patterns

3. **Experiment**
   - Modify the user request
   - Try different species
   - Test different genomic regions

4. **Monitor Development**
   - Phase 2: Sequence processing tools
   - Phase 3: Alignment & phylogenetics
   - Phase 4: Primer design tools (coming soon!)
   - Phase 5: Validation & literature search

## 🎓 Learning Resources

### Understanding the Multi-Agent System

**Key Concepts:**
- **Agents**: Autonomous AI entities with specific roles
- **Tools**: Functions agents can call (via MCP)
- **Workflow**: Coordinated sequence of agent actions
- **Logging**: Tracking all activities for transparency

**Agent Roles:**
```
┌─────────────┐
│ Coordinator │ ← Plans and coordinates
└──────┬──────┘
       │
   ┌───┴────┬────────────┐
   │        │            │
┌──┴──────┐ ┌┴───────────┐ ┌┴─────────┐
│Database │ │  Analyst   │ │Future... │
│ Agent   │ │   Agent    │ │  Agents  │
└──┬──────┘ └────────────┘ └──────────┘
   │
   │ Uses MCP Tools
   ↓
┌──────────────────┐
│  MCP Servers     │
│ ├─ Database      │
│ ├─ Processing    │
│ ├─ Alignment     │
│ └─ Design        │
└──────────────────┘
```

### Example Task Log Analysis

**What to look for:**
1. ✅ All agents participated
2. ✅ Tool calls succeeded
3. ✅ Reasonable execution time
4. ✅ Non-empty results
5. ✅ No error messages

**Red flags:**
- ❌ Tool calls failed
- ❌ Very short results
- ❌ Missing agent actions
- ❌ Error in logs

## 💡 Tips & Best Practices

1. **Check Logs First**: Always review logs after workflow completion
2. **Understand Statistics**: Use tool call counts to gauge complexity
3. **Monitor Performance**: Track execution times in timestamps
4. **Save Logs**: Copy important task logs for later analysis
5. **Incremental Testing**: Start simple, add complexity gradually

## ⚡ Quick Reference Commands

```bash
# Start system
docker compose -f docker-compose.autogen.yml up -d

# View logs
docker logs -f qpcr-assistant

# Check task logs
docker exec qpcr-assistant ls -lh /results

# View latest summary
docker exec qpcr-assistant tail -50 \
  $(docker exec qpcr-assistant ls -t /results/*_summary.txt | head -1)

# Get statistics
docker exec qpcr-assistant cat /results/task_*.json | jq '.statistics'

# Copy all logs
docker cp qpcr-assistant:/results ./qpcr_logs

# Stop system
docker compose -f docker-compose.autogen.yml down

# Full restart
docker compose -f docker-compose.autogen.yml down && \
docker compose -f docker-compose.autogen.yml up --build -d
```

---

**Need Help?**
- Check `USER_GUIDE.md` for detailed instructions
- Review logs in `/results` for troubleshooting
- See `CLAUDE.md` for architecture details
