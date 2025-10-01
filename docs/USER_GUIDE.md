# qPCR Assistant - User Interaction Guide

## Overview

The qPCR Assistant is a multi-agent AI system powered by AG2 that helps design species-specific qPCR assays for molecular diagnostics. The system uses multiple specialized agents that collaborate to retrieve sequences, analyze data, and recommend primer design strategies.

## Current System Architecture

### Active Agents

1. **Coordinator Agent**
   - Role: Project manager for qPCR assay design
   - Responsibilities:
     - Understand user requirements
     - Create step-by-step workflow plans
     - Coordinate with other agents
     - Summarize findings and recommend next steps

2. **DatabaseAgent** (with MCP Tools)
   - Role: Biological database specialist
   - Responsibilities:
     - Retrieve sequences from NCBI, BOLD, and other databases
     - Identify taxonomically similar species (potential off-targets)
     - Extract and organize sequence metadata
     - Search for existing sequencing studies (SRA/BioProject)
   - Available Tools:
     - `get_sequences`: Retrieve DNA/RNA sequences
     - `get_taxonomy`: Get taxonomic information
     - `get_neighbors`: Find related species
     - `extract_sequence_columns`: Parse sequence metadata
     - `search_sra_studies`: Search SRA database

3. **AnalystAgent**
   - Role: Molecular biology analyst
   - Responsibilities:
     - Analyze retrieved sequences
     - Identify conserved regions in target species
     - Identify variable regions between targets and off-targets
     - Recommend candidate regions for primer design
     - Assess potential primer specificity

## How to Interact with the System

### Method 1: Docker Container (Current Setup)

The system runs automatically when the container starts. It executes a predefined workflow:

```bash
# Start the system
docker compose -f docker-compose.autogen.yml up -d

# View real-time logs
docker logs -f qpcr-assistant

# Access task logs
docker exec qpcr-assistant ls /results

# Copy task logs to your local machine
docker cp qpcr-assistant:/results ./task_logs
```

### Method 2: Python API (Programmatic Access)

You can modify the `qpcr_assistant.py` main function to accept custom requests:

```python
import asyncio
from qpcr_assistant import QPCRAssistant

async def run_custom_task():
    # Initialize assistant
    assistant = QPCRAssistant(openai_api_key="your-key-here")
    await assistant.initialize()

    # Submit your request
    user_request = """
    I need to design a qPCR assay to identify [Target Species]
    and distinguish it from [Off-target Species].

    Requirements:
    - Target: [Scientific name]
    - Off-targets: [List of species or genera]
    - Genomic region: [COI, 16S, ITS, etc.]
    - Application: [Purpose of the assay]

    Please:
    1. Retrieve sequences for target and off-targets
    2. Identify other potential cross-reactive species
    3. Analyze sequences to find signature regions
    4. Recommend primer design strategy
    """

    # Run workflow with logging
    await assistant.run_workflow_stream(user_request)

    # Cleanup
    await assistant.shutdown()

# Run
asyncio.run(run_custom_task())
```

### Method 3: Interactive Script (Recommended for Development)

Create a custom interaction script:

```python
# save as: interactive_qpcr.py
import asyncio
import os
from qpcr_assistant import QPCRAssistant

async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    assistant = QPCRAssistant(api_key)

    await assistant.initialize()

    print("\n" + "="*80)
    print("qPCR ASSISTANT - Interactive Mode")
    print("="*80)

    while True:
        print("\nEnter your qPCR design request (or 'quit' to exit):")
        user_input = input("> ").strip()

        if user_input.lower() == 'quit':
            break

        if not user_input:
            continue

        try:
            await assistant.run_workflow_stream(user_input)
        except Exception as e:
            print(f"Error: {e}")

    await assistant.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

Then run:
```bash
docker exec -it qpcr-assistant python /app/interactive_qpcr.py
```

## Understanding Task Logs

After each workflow execution, the system generates two types of logs:

### 1. JSON Log (Machine-Readable)

Location: `/results/task_YYYYMMDD_HHMMSS.json`

Structure:
```json
{
  "session_id": "20251001_174900",
  "start_time": "2025-10-01T17:49:00.123456",
  "end_time": "2025-10-01T17:52:30.654321",
  "user_request": "User's original request...",
  "agents": [
    {
      "timestamp": "2025-10-01T17:49:05.000000",
      "agent": "Coordinator",
      "action": "message",
      "content": "Agent's action or message..."
    }
  ],
  "tool_calls": [
    {
      "timestamp": "2025-10-01T17:49:10.000000",
      "agent": "DatabaseAgent",
      "tool": "get_sequences",
      "arguments": {"taxon": "Salmo salar", "region": "COI"},
      "result_preview": "Retrieved sequences...",
      "result_length": 15000,
      "success": true
    }
  ],
  "messages": [...],
  "statistics": {
    "total_agents": 3,
    "total_actions": 15,
    "total_tool_calls": 5,
    "successful_tool_calls": 5,
    "failed_tool_calls": 0
  },
  "summary": "Workflow completion summary"
}
```

### 2. Human-Readable Summary

Location: `/results/task_YYYYMMDD_HHMMSS_summary.txt`

Contains:
- Session metadata
- User request
- Execution statistics
- Chronological agent workflow
- Tool call details with arguments and results
- Message timeline
- Final summary

Example:
```
================================================================================
qPCR ASSISTANT - TASK EXECUTION LOG
================================================================================

Session ID: 20251001_174900
Start Time: 2025-10-01T17:49:00.123456
End Time: 2025-10-01T17:52:30.654321

USER REQUEST:
--------------------------------------------------------------------------------
Design a qPCR assay for Atlantic salmon...

STATISTICS:
--------------------------------------------------------------------------------
  Total Agents Involved: 3
  Total Agent Actions: 15
  Total Tool Calls: 5
    - Successful: 5
    - Failed: 0
  Total Messages: 25

AGENT WORKFLOW:
--------------------------------------------------------------------------------
[1] 2025-10-01T17:49:05 - Coordinator
    Action: message
    Content: I will create a step-by-step workflow plan...

[2] 2025-10-01T17:49:10 - DatabaseAgent
    Action: message
    Content: Retrieving COI sequences for Salmo salar...

TOOL CALLS:
--------------------------------------------------------------------------------
[1] 2025-10-01T17:49:10 - DatabaseAgent
    Tool: get_sequences
    Arguments: {
      "taxon": "Salmo salar",
      "region": "COI",
      "source": "ncbi",
      "max_results": 100
    }
    Status: ✓ SUCCESS
    Result Preview: >PV570336.1 Salmo salar isolate SS04...
    Result Length: 15234 characters

[2] 2025-10-01T17:49:25 - DatabaseAgent
    Tool: get_neighbors
    Arguments: {
      "taxon": "Salmo salar",
      "rank": "genus",
      "distance": 1
    }
    Status: ✓ SUCCESS
    Result Preview: Found 15 related species in Salmo genus...
    Result Length: 2456 characters
```

## Example Use Cases

### Use Case 1: Species Identification for Aquaculture

```
Request: "Design a qPCR assay to identify Atlantic salmon (Salmo salar)
and distinguish it from rainbow trout (Oncorhynchus mykiss) for aquaculture
product verification."

Expected Output:
- COI sequences for both species
- Analysis of conserved vs. variable regions
- Recommended primer design strategy
- Task log showing all agents' work
```

### Use Case 2: Pathogen Detection

```
Request: "Design a qPCR assay to detect Mycobacterium tuberculosis in
clinical samples, with specificity against other Mycobacterium species."

Expected Output:
- 16S rRNA or specific gene sequences
- Identification of cross-reactive species
- Signature region recommendations
- Detailed workflow log
```

### Use Case 3: Environmental Monitoring

```
Request: "Design a qPCR assay for detecting invasive zebra mussels
(Dreissena polymorpha) in environmental DNA samples."

Expected Output:
- COI sequences for target species
- Related species analysis
- Primer design recommendations
- Complete agent interaction log
```

## Monitoring Agent Activity

### Real-Time Monitoring

```bash
# Watch container logs in real-time
docker logs -f qpcr-assistant

# Filter for specific agent activities
docker logs qpcr-assistant 2>&1 | grep "DatabaseAgent"

# Filter for tool calls
docker logs qpcr-assistant 2>&1 | grep "Calling database"

# Filter for errors
docker logs qpcr-assistant 2>&1 | grep "ERROR"
```

### Post-Execution Analysis

```bash
# List all task logs
docker exec qpcr-assistant ls -lh /results

# View latest summary
docker exec qpcr-assistant tail -100 \
  $(docker exec qpcr-assistant ls -t /results/*_summary.txt | head -1)

# Extract tool call statistics
docker exec qpcr-assistant cat /results/task_*.json | \
  jq '.statistics'
```

## Configuration

### Environment Variables

Set in `autogen_app/.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
NCBI_API_KEY=your_ncbi_key  # Increases NCBI rate limits
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
MCP_DATABASE_SERVER=ndiag-database-server  # Container name
```

### Adjusting Agent Behavior

Edit `qpcr_assistant.py` to modify agent system messages:

```python
# Example: Make DatabaseAgent more verbose
self.agents["database"] = AssistantAgent(
    name="DatabaseAgent",
    description="...",
    model_client=model_client,
    system_message="""You are a biological database specialist.

    IMPORTANT: Always explain what you're doing before calling tools.
    Report detailed statistics about retrieved sequences.
    Suggest additional searches if initial results are limited.

    Your responsibilities:
    ...
    """,
    tools=[...]
)
```

## Troubleshooting

### Container Keeps Restarting

**Symptom:** `docker ps` shows constant restarts

**Solution:**
```bash
# Check logs for error
docker logs qpcr-assistant --tail 50

# Verify API key is loaded
docker exec qpcr-assistant env | grep OPENAI_API_KEY

# Restart with fresh build
docker compose -f docker-compose.autogen.yml down
docker compose -f docker-compose.autogen.yml up --build -d
```

### No Tool Calls Being Made

**Symptom:** Agents discuss but don't use MCP tools

**Check:**
```bash
# Verify MCP server connection
docker logs qpcr-assistant 2>&1 | grep "MCP servers connected"

# Verify tools are registered
docker logs qpcr-assistant 2>&1 | grep "Created.*agents"

# Check for tool call attempts
docker logs qpcr-assistant 2>&1 | grep "ToolCall"
```

### Empty or Missing Task Logs

**Symptom:** `/results` directory is empty

**Solution:**
```bash
# Verify directory exists
docker exec qpcr-assistant ls -la /results

# Check permissions
docker exec qpcr-assistant ls -ld /results

# Run workflow and check logs immediately
docker exec qpcr-assistant ls -lht /results | head
```

## Future Enhancements

### Coming Soon

1. **Web Interface**: Browser-based UI for submitting requests and viewing results
2. **API Endpoint**: REST API for programmatic access
3. **Interactive Chat**: Real-time chat interface with agents
4. **Batch Processing**: Submit multiple assay designs at once
5. **Result Export**: Direct export to CSV, Excel, or PDF formats

### Planned Features

- Primer validation agent (BLAST, in-silico PCR)
- Sequence alignment visualization
- Automated report generation
- Integration with primer ordering systems
- Species database auto-updates

## Support and Feedback

For issues or feature requests:
- GitHub Issues: https://github.com/acefgin/mdk_mcp/issues
- Documentation: See `CLAUDE.md` and `AUTOGEN_INTEGRATION.md`
- Logs: Check `/results` directory for detailed execution logs

## Best Practices

1. **Be Specific**: Provide clear target/off-target species names
2. **Include Context**: Mention application (diagnostics, research, etc.)
3. **Specify Region**: Indicate preferred genomic region (COI, 16S, etc.)
4. **Review Logs**: Always check task logs for complete workflow details
5. **Iterate**: Refine requests based on initial results
