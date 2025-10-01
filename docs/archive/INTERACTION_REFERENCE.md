# qPCR Assistant - Interaction Reference Card

## 🚀 Current Interaction Method: Interactive Chat Interface (NEW!)

### How It Works Now

```
┌──────────────────────────────────────────────────────────┐
│  1. User starts container (./start_interactive.sh)      │
│     ↓                                                     │
│  2. System loads API key from .env                       │
│     ↓                                                     │
│  3. Initializes MCP servers + 3 agents                   │
│     ↓                                                     │
│  4. Presents interactive chat interface                  │
│     ↓                                                     │
│  5. User types requests naturally                        │
│     ↓                                                     │
│  6. Agents collaborate in real-time                      │
│     ↓                                                     │
│  7. Shows progress, logs saved to /results/              │
│     ↓                                                     │
│  8. Ready for next request (or type 'exit')             │
└──────────────────────────────────────────────────────────┘
```

## 📋 Quick Start (3 Steps)

### Step 1: Configure
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key" > autogen_app/.env
```

### Step 2: Start Interactive Mode (NEW!)
```bash
# One-command startup
./start_interactive.sh

# Or manually
docker compose -f docker-compose.autogen.yml up -d
docker attach qpcr-assistant
```

### Step 3: Chat Naturally
```
┌─[qPCR Assistant]
└─> Design a qPCR assay to identify Atlantic salmon...

🚀 STARTING WORKFLOW
[Agents collaborate in real-time...]
✓ WORKFLOW COMPLETED

┌─[qPCR Assistant]
└─>
```

## 🆕 What's New in Interactive Mode

✅ **Natural chat interface** - Type requests like talking to Claude Code
✅ **Real-time progress** - See agents working as it happens
✅ **Multiple requests** - Submit many tasks in one session
✅ **Built-in commands** - `help`, `logs`, `clear`, `exit`
✅ **Interrupt workflows** - Press Ctrl+C to stop
✅ **No code editing** - No need to rebuild containers

---

## 📋 Old Method (Automatic Mode)

For reference, the old automatic mode is documented below:

### Step 1: Configure
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key" > autogen_app/.env
```

### Step 2: Start
```bash
# Start system
docker compose -f docker-compose.autogen.yml up -d

# Expected: 2 containers running
# - qpcr-assistant (Up)
# - ndiag-database-server (Up, unhealthy is OK)
```

### Step 3: Monitor
```bash
# Watch real-time activity
docker logs -f qpcr-assistant

# Expected output:
# ✓ "MCP servers connected"
# ✓ "Created 3 agents"
# ✓ Coordinator plans workflow
# ✓ DatabaseAgent retrieves sequences
# ✓ AnalystAgent analyzes data
# ✓ "Task log saved to: /results/task_*.json"
```

## 📊 Understanding Multi-Agent Activity

### What Happens Per Task

```
User Request: "Design qPCR for Atlantic Salmon"
                    ↓
┌───────────────────────────────────────────────┐
│ COORDINATOR AGENT                             │
│ - Receives request                            │
│ - Creates workflow plan                       │
│ - Delegates to specialists                    │
└───────────────┬───────────────────────────────┘
                ↓
┌───────────────────────────────────────────────┐
│ DATABASE AGENT                                │
│ - Uses MCP Tool: get_sequences                │
│   • Connects to: ndiag-database-server        │
│   • Queries: NCBI GenBank                     │
│   • Retrieves: ~100 COI sequences             │
│   • Size: ~292KB of FASTA data                │
│ - Returns: Sequence data to team              │
└───────────────┬───────────────────────────────┘
                ↓
┌───────────────────────────────────────────────┐
│ ANALYST AGENT                                 │
│ - Receives: Sequences from DatabaseAgent      │
│ - Analyzes: Conserved vs variable regions     │
│ - Recommends: Primer design strategy          │
└───────────────┬───────────────────────────────┘
                ↓
           Task Complete
           Logs Saved to /results/
```

### Timeline Example

| Time | Agent | Action | Details |
|------|-------|--------|---------|
| 00:00 | user | Submit request | "Design qPCR for Atlantic Salmon" |
| 00:16 | Coordinator | Create plan | 4-step workflow plan |
| 00:19 | DatabaseAgent | Call tool | get_sequences(taxon="Salmo salar") |
| 00:20 | MCP Server | Query NCBI | Retrieve 100 sequences |
| 00:21 | DatabaseAgent | Return data | 292KB of sequences |
| 00:22 | AnalystAgent | Analyze | Identify signature regions |
| 00:23 | System | Save logs | /results/task_*.json created |

## 🔍 Viewing Task Logs

### Quick Commands

```bash
# List all logs
docker exec qpcr-assistant ls -lh /results

# View latest summary
docker exec qpcr-assistant tail -50 \
  $(docker exec qpcr-assistant ls -t /results/*_summary.txt | head -1)

# Get statistics
docker exec qpcr-assistant cat /results/*.json | jq '.statistics'

# Copy to your machine
docker cp qpcr-assistant:/results ./my_logs
```

### What's in the Logs

**1. User Request** - What you asked for
```
USER REQUEST:
Design a qPCR assay to identify Atlantic salmon (Salmo salar)
and distinguish it from rainbow trout...
```

**2. Statistics** - What was done
```
STATISTICS:
  Total Agents Involved: 2
  Total Tool Calls: 1
  Successful: 1
  Failed: 0
```

**3. Agent Workflow** - Who did what
```
[1] Coordinator - Creates workflow plan
[2] DatabaseAgent - Retrieves sequences using get_sequences tool
[3] AnalystAgent - Analyzes sequences
```

**4. Tool Calls** - Database queries
```
Tool: get_sequences
Arguments: {taxon: "Salmo salar", region: "COI"}
Result: 100 sequences (292,015 characters)
Status: ✓ SUCCESS
```

## 🛠️ Available MCP Tools

Each tool can be called by DatabaseAgent:

| Tool | Purpose | Example |
|------|---------|---------|
| `get_sequences` | Retrieve DNA/RNA sequences | Get COI sequences for salmon |
| `get_taxonomy` | Get taxonomic info | Get family/genus for species |
| `get_neighbors` | Find related species | Find other Salmo species |
| `extract_sequence_columns` | Parse sequence metadata | Extract accession numbers |
| `search_sra_studies` | Search SRA database | Find sequencing projects |

## 📈 Interpreting Results

### Success Indicators ✅

```bash
# Check if workflow succeeded
docker exec qpcr-assistant cat /results/*.json | jq '.statistics'
```

**Good:**
```json
{
  "successful_tool_calls": 5,
  "failed_tool_calls": 0
}
```

**Problem:**
```json
{
  "successful_tool_calls": 0,
  "failed_tool_calls": 3
}
```

### Tool Call Success ✅

```bash
# View tool call details
docker exec qpcr-assistant cat /results/*.json | jq '.tool_calls[]'
```

**Good:**
```json
{
  "tool": "get_sequences",
  "result_length": 292015,
  "success": true
}
```

**Problem:**
```json
{
  "tool": "get_sequences",
  "result_length": 45,
  "success": false
}
```

## 🔄 How to Submit New Requests

### Current Method: Edit & Rebuild

**Step 1:** Edit the request
```bash
# Edit qpcr_assistant.py line 456
nano autogen_app/qpcr_assistant.py

# Change user_request to your new request
user_request = """
Your custom request here...
"""
```

**Step 2:** Rebuild
```bash
docker compose -f docker-compose.autogen.yml down
docker compose -f docker-compose.autogen.yml up --build -d
```

**Step 3:** Monitor
```bash
docker logs -f qpcr-assistant
```

## 🎯 Example Use Cases

### 1. Species Identification
```
Request: "Design qPCR to identify Atlantic salmon (Salmo salar)
and distinguish from rainbow trout (Oncorhynchus mykiss)"

Expected:
✓ Coordinator creates plan
✓ DatabaseAgent retrieves COI sequences
✓ AnalystAgent finds signature regions
✓ Log shows tool call: get_sequences
✓ Result: 100+ sequences
```

### 2. Pathogen Detection
```
Request: "Design qPCR to detect Mycobacterium tuberculosis
in clinical samples"

Expected:
✓ Coordinator creates plan
✓ DatabaseAgent retrieves 16S/specific genes
✓ AnalystAgent identifies conserved regions
✓ Log shows multiple tool calls
✓ Result: Species-specific primers
```

### 3. Environmental Monitoring
```
Request: "Design qPCR for invasive zebra mussels
(Dreissena polymorpha) in eDNA samples"

Expected:
✓ Coordinator creates plan
✓ DatabaseAgent retrieves COI sequences
✓ get_neighbors finds related species
✓ AnalystAgent recommends primers
✓ Log shows 2-3 tool calls
```

## ⚠️ Known Limitations

### 1. Token Limit Issue

**Symptom:** Workflow fails after sequences retrieved

**In Logs:**
```
Error: RateLimitError: Requested 73859 tokens, Limit 10000
```

**Why:** 100 sequences = too much data for GPT-4

**Workaround:**
```python
# Edit qpcr_assistant.py
# Reduce max_results from 100 to 20
"max_results": 20  # Instead of 100
```

### 2. Static Workflow

**Limitation:** Can't submit custom requests interactively

**Current:** Must edit code and rebuild

**Future:** Interactive CLI, REST API, Web UI coming

### 3. No Real-Time Interaction

**Current:** One workflow per container start

**To run multiple:**
```bash
# Run workflow 1
docker compose up -d
# Wait for completion
docker logs qpcr-assistant | grep "Task log saved"

# Run workflow 2 (edit qpcr_assistant.py first)
docker compose restart qpcr-assistant
```

## 📚 Documentation Guide

| Document | Purpose | When to Read |
|----------|---------|-------------|
| **QUICK_START.md** | Get started in 5 min | First time users |
| **USER_GUIDE.md** | Complete guide | All users |
| **INTERACTION_REFERENCE.md** | Quick reference | Quick lookups |
| **TASK_LOGGING_SUMMARY.md** | Log interpretation | Understanding logs |
| **AUTOGEN_INTEGRATION.md** | Technical details | Developers |
| **CLAUDE.md** | Project overview | Developers |

## 🆘 Troubleshooting

### Container Won't Start

```bash
# Check API key
cat autogen_app/.env

# Check logs
docker logs qpcr-assistant

# Rebuild
docker compose -f docker-compose.autogen.yml up --build --force-recreate -d
```

### No Logs Created

```bash
# Check /results exists
docker exec qpcr-assistant ls -la /results

# Check permissions
docker exec qpcr-assistant touch /results/test.txt
```

### Tool Calls Failed

```bash
# Check MCP connection
docker logs qpcr-assistant | grep "MCP servers connected"

# Check database server
docker logs ndiag-database-server

# Check tool errors
docker logs qpcr-assistant | grep -i error
```

## 📞 Support

- **Logs:** Check `/results/*_summary.txt` first
- **Docs:** See `USER_GUIDE.md` for detailed help
- **Issues:** GitHub issues for bugs/features

---

## 🎓 Key Takeaways

1. **Current Interaction:** Automatic container execution
2. **Agents:** 3 agents (Coordinator, DatabaseAgent, AnalystAgent)
3. **Tools:** 5 MCP tools for database access
4. **Logging:** Automatic task logs in `/results/`
5. **Customization:** Edit qpcr_assistant.py and rebuild
6. **Future:** Interactive CLI, API, Web UI coming

**Start Now:**
```bash
docker compose -f docker-compose.autogen.yml up -d
docker logs -f qpcr-assistant
docker cp qpcr-assistant:/results ./logs
```
