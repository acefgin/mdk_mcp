# qPCR Assistant - Interactive Mode Guide

## Overview

The qPCR Assistant now features an interactive chat interface similar to Claude Code, allowing you to submit tasks, see real-time progress, and provide feedback naturally.

## Quick Start

### 1. Start the System

```bash
# Start containers
docker compose -f docker-compose.autogen.yml up -d

# Attach to interactive session
docker attach qpcr-assistant
```

### 2. Use the Interface

You'll see a welcome banner with available commands:

```
╔══════════════════════════════════════════════════════════════════════════╗
║                     qPCR ASSISTANT - Interactive Mode                   ║
║  Multi-Agent AI System for qPCR Assay Design                           ║
╚══════════════════════════════════════════════════════════════════════════╝

┌─[qPCR Assistant]
└─>
```

## Available Commands

| Command | Description |
|---------|-------------|
| **Type naturally** | Submit your qPCR design request |
| `help` | Show usage examples |
| `logs` | View recent task logs |
| `clear` | Clear screen |
| `exit` or `quit` | Exit the assistant |

## Example Interactions

### Example 1: Species Identification

```
┌─[qPCR Assistant]
└─> Design a qPCR assay to identify Atlantic salmon (Salmo salar)
    and distinguish it from rainbow trout (Oncorhynchus mykiss).
    Target: COI region for aquaculture verification.

═══════════════════════════════════════════════════════════════════════════
🚀 STARTING WORKFLOW
═══════════════════════════════════════════════════════════════════════════

[Coordinator] Planning workflow...
  Step 1: Retrieve COI sequences for Salmo salar
  Step 2: Retrieve COI sequences for Oncorhynchus mykiss
  Step 3: Analyze for signature regions
  Step 4: Recommend primer design strategy

[DatabaseAgent] Calling tool: get_sequences
  Arguments: taxon="Salmo salar", region="COI", max_results=100
  ✓ Retrieved 100 sequences (292,015 characters)

[AnalystAgent] Analyzing sequences...
  • Identified 15 conserved regions in target
  • Found 3 signature regions unique to Salmo salar
  • Recommending primers in signature region 2 (position 450-470)

═══════════════════════════════════════════════════════════════════════════
✓ WORKFLOW COMPLETED
═══════════════════════════════════════════════════════════════════════════
Task log saved to /results/

┌─[qPCR Assistant]
└─>
```

### Example 2: Pathogen Detection

```
┌─[qPCR Assistant]
└─> Design a qPCR assay to detect Mycobacterium tuberculosis
    in clinical samples with specificity against other Mycobacterium species.

[Workflow output...]
```

### Example 3: Environmental Monitoring

```
┌─[qPCR Assistant]
└─> Design qPCR for invasive zebra mussels (Dreissena polymorpha) in eDNA samples

[Workflow output...]
```

## Real-Time Progress Display

As agents work, you'll see:

1. **Coordinator Planning**
   ```
   [Coordinator] Creating workflow plan...
   - Step 1: Retrieve sequences
   - Step 2: Analyze sequences
   - Step 3: Design primers
   ```

2. **DatabaseAgent Tool Calls**
   ```
   [DatabaseAgent] Calling tool: get_sequences
     Arguments: {taxon: "Species name", region: "COI"}
     ✓ Retrieved 100 sequences (292KB)
   ```

3. **AnalystAgent Analysis**
   ```
   [AnalystAgent] Analyzing sequences...
     • Identified conserved regions
     • Found signature regions
     • Recommending primer strategy
   ```

## Viewing Task Logs

### During Session

```
┌─[qPCR Assistant]
└─> logs

═══════════════════════════════════════════════════════════════════════════
RECENT TASK LOGS:
═══════════════════════════════════════════════════════════════════════════

1. task_20251001_180903_summary.txt
   [First 30 lines of summary shown...]

2. task_20251001_175526_summary.txt
   [Summary preview...]
```

### Outside Session

```bash
# List all logs
docker exec qpcr-assistant ls -lh /results

# View latest summary
docker exec qpcr-assistant cat \
  $(docker exec qpcr-assistant ls -t /results/*_summary.txt | head -1)

# Copy logs to local machine
docker cp qpcr-assistant:/results ./qpcr_logs
```

## Interrupting Workflows

Press `Ctrl+C` during workflow execution:

```
⚠️  Workflow interrupted by user (Ctrl+C)
Type 'exit' to quit or continue with a new request

┌─[qPCR Assistant]
└─>
```

The workflow stops, but you can submit a new request.

## Detaching Without Stopping

To detach from the interactive session without stopping the container:

**Press:** `Ctrl+P` then `Ctrl+Q`

The container continues running in the background.

To reattach:
```bash
docker attach qpcr-assistant
```

## Tips for Effective Requests

### Be Specific

✅ **Good:**
```
Design a qPCR assay to identify Atlantic salmon (Salmo salar)
and distinguish it from rainbow trout (Oncorhynchus mykiss).
Target: COI region, Application: Aquaculture verification
```

❌ **Too vague:**
```
Design primers for salmon
```

### Include Context

Mention:
- **Target species** (scientific name)
- **Off-target species** (potential cross-reactivity)
- **Genomic region** (COI, 16S, ITS, etc.)
- **Application** (clinical diagnostics, environmental monitoring, etc.)

### Example Template

```
Design a qPCR assay to [identify/detect] [Target Species]
and distinguish it from [Off-target Species].

Requirements:
- Target: [Scientific name]
- Off-targets: [List of species or genera]
- Genomic region: [COI/16S/ITS/custom]
- Application: [Purpose]

Additional considerations:
- [Any specific requirements]
```

## Multi-Agent Workflow

### Agent Roles

```
┌─────────────┐
│ Coordinator │ ← Plans and coordinates
└──────┬──────┘
       │
   ┌───┴────┬────────────┐
   │        │            │
┌──┴──────┐ ┌┴───────────┐
│Database │ │  Analyst   │
│ Agent   │ │   Agent    │
└──┬──────┘ └────────────┘
   │
   │ Uses MCP Tools:
   │ • get_sequences
   │ • get_taxonomy
   │ • get_neighbors
   │ • extract_sequence_columns
   │ • search_sra_studies
   ↓
```

### Typical Workflow Timeline

```
[00:00] User submits request
[00:01] Coordinator analyzes and creates plan
[00:05] DatabaseAgent retrieves sequences (tool: get_sequences)
[00:20] DatabaseAgent returns 100 sequences (292KB)
[00:21] AnalystAgent analyzes sequences
[00:25] AnalystAgent provides recommendations
[00:26] Workflow completes
[00:26] Task log saved to /results/
```

## Troubleshooting

### Container Exits Immediately

**Symptom:** Attached session exits right away

**Solution:**
```bash
# Check logs
docker logs qpcr-assistant --tail 50

# Verify API key
docker exec qpcr-assistant env | grep OPENAI_API_KEY

# Rebuild
docker compose -f docker-compose.autogen.yml down
docker compose -f docker-compose.autogen.yml up --build -d
docker attach qpcr-assistant
```

### Cannot Attach to Container

**Symptom:** `Error: No such container`

**Solution:**
```bash
# Check if running
docker ps | grep qpcr-assistant

# Start if stopped
docker compose -f docker-compose.autogen.yml up -d

# Then attach
docker attach qpcr-assistant
```

### Workflow Takes Too Long

**Symptom:** Agent seems stuck

**Possible causes:**
1. Large sequence retrieval (100+ sequences)
2. Network latency to NCBI/BOLD
3. Token limit issues with OpenAI API

**Actions:**
- Press `Ctrl+C` to interrupt
- Check logs: `logs` command
- Try simpler request first

### Token Limit Errors

**Symptom:**
```
ERROR: RateLimitError: Requested 73859 tokens, Limit 10000
```

**Solution:**
This occurs when retrieving too many sequences. The system is being enhanced to:
1. Automatically reduce sequence counts
2. Implement chunking for large datasets
3. Use summarization before analysis

For now, requests with 20-30 sequences work best.

## Advanced Usage

### Running Multiple Workflows

You can submit multiple requests in one session:

```
┌─[qPCR Assistant]
└─> [First request]
[Workflow completes]

┌─[qPCR Assistant]
└─> [Second request]
[Workflow completes]

┌─[qPCR Assistant]
└─> logs
[View all task logs]

┌─[qPCR Assistant]
└─> exit
```

Each workflow gets its own task log file.

### Accessing Logs Programmatically

```bash
# Get all task statistics
docker exec qpcr-assistant cat /results/*.json | jq '.statistics'

# Extract tool call details
docker exec qpcr-assistant cat /results/*.json | \
  jq '.tool_calls[] | {agent, tool, success, result_length}'

# Find failed workflows
docker exec qpcr-assistant cat /results/*.json | \
  jq 'select(.statistics.failed_tool_calls > 0)'
```

### Custom Automation

```python
# Submit requests programmatically
import subprocess

requests = [
    "Design qPCR for Species A...",
    "Design qPCR for Species B...",
    "Design qPCR for Species C..."
]

for request in requests:
    subprocess.run([
        "docker", "exec", "-i", "qpcr-assistant",
        "python", "-c",
        f"import asyncio; from qpcr_assistant import QPCRAssistant; "
        f"asyncio.run(QPCRAssistant().run_workflow_stream('{request}'))"
    ])
```

## Comparison: Interactive vs. Automatic Mode

| Feature | Interactive Mode | Automatic Mode (Old) |
|---------|------------------|---------------------|
| **User Input** | Natural chat interface | Edit code + rebuild |
| **Real-time Feedback** | ✅ Yes | ❌ No |
| **Multiple Requests** | ✅ Yes, in one session | ❌ One per restart |
| **View Progress** | ✅ Streaming output | ❌ Check logs after |
| **Interrupt Workflow** | ✅ Ctrl+C | ❌ Must restart |
| **View Logs** | ✅ `logs` command | ❌ Docker exec |
| **Ease of Use** | ✅ Beginner-friendly | ❌ Developer-only |

## Next Steps

1. **Try Example Requests**: Start with the provided examples
2. **Explore Commands**: Use `help` and `logs` commands
3. **Review Task Logs**: Check `/results` for detailed workflow records
4. **Iterate Requests**: Refine based on results
5. **Provide Feedback**: Report issues or suggestions

## Support

For issues or questions:
- Check task logs: `logs` command or `/results` directory
- Review docs: `USER_GUIDE.md`, `QUICK_START.md`
- GitHub: https://github.com/acefgin/mdk_mcp/issues

---

**Ready to get started?**

```bash
docker attach qpcr-assistant
```

Welcome to interactive qPCR assay design! 🧬
