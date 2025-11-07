---
name: ag2-agent-dev
description: AG2 (AutoGen) multi-agent system development patterns for orchestrating MCP tools and workflow coordination. Use when creating agents, defining agent roles, implementing group chat, configuring MCP bridges, setting up agent collaboration, or designing multi-agent workflows. Covers agent types, LLM configuration, tool registration, conversation patterns, and bioinformatics pipeline orchestration.
---

# AG2 Agent Development Guidelines

## Purpose

Establish patterns for developing multi-agent systems using AG2 (formerly AutoGen) in the mdk_mcp bioinformatics platform. This skill covers agent design, orchestration, MCP integration, and workflow coordination for qPCR assay design.

## When to Use This Skill

Automatically activates when working on:
- Creating or modifying AG2 agents
- Designing multi-agent workflows and collaboration patterns
- Integrating MCP tools with AG2 agents
- Configuring LLM models (Gemini, GPT-4) for agents
- Implementing conversation flows and coordination logic
- Setting up GroupChat and workflow orchestration
- Testing agent interactions and tool calling

---

## Quick Start

### New Agent Checklist

- [ ] **Role Definition**: Clear purpose and responsibilities
- [ ] **Tool Assignment**: Which MCP tools this agent can use
- [ ] **System Message**: Comprehensive instructions and constraints
- [ ] **LLM Configuration**: Model selection (Gemini/GPT-4) and parameters
- [ ] **Tool Registration**: Register MCP bridge functions
- [ ] **Collaboration**: How agent interacts with other agents
- [ ] **Testing**: Verify tool calling and responses

### Multi-Agent Workflow Checklist

- [ ] Coordinator agent for orchestration
- [ ] Specialized agents for each phase
- [ ] Clear agent transition logic
- [ ] MCP bridge initialized with all servers
- [ ] Tool functions registered per agent
- [ ] GroupChat with proper speaker selection
- [ ] Task logging and result tracking

---

## AG2 Agent Architecture in mdk_mcp

### Multi-Agent Pipeline

```
User Request (Natural Language)
    ↓
┌─────────────────────────────────────────────┐
│   Coordinator Agent (Orchestrator)          │
│   - Plans workflow                          │
│   - Synthesizes results                     │
│   - No MCP tools                            │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│   DatabaseAgent (Phase 1: Retrieval)        │
│   - Retrieves sequences from databases      │
│   - 5 MCP tools: get_sequences, etc.        │
└──────────────┬──────────────────────────────┘
               ↓ (FASTA files)
┌─────────────────────────────────────────────┐
│   AnalystAgent (Phase 2-3: Curation)        │
│   - QC, processing, alignment, phylogeny    │
│   - 10 MCP tools: fasta_qc, align, etc.     │
└──────────────┬──────────────────────────────┘
               ↓ (Curated data + analysis)
┌─────────────────────────────────────────────┐
│   PrimerDesignAgent (Phase 4: Design)       │
│   - Signature regions, Primer3, QC          │
│   - 6 MCP tools: find_regions, design, etc. │
└─────────────────────────────────────────────┘
```

**Key Principles:**
- **Linear Pipeline**: Data flows through specialized agents
- **Separation of Concerns**: Each agent has focused responsibility
- **Clear Handoffs**: Agents pass files/paths, not raw data
- **Coordinator Synthesizes**: Final summary from coordinator

---

## Agent Types and Patterns

### 1. Coordinator Agent (No Tools)

**Purpose**: Workflow orchestration, planning, and synthesis

**Pattern:**
```python
from autogen import ConversableAgent

coordinator = ConversableAgent(
    name="Coordinator",
    system_message="""You are a workflow coordinator for qPCR assay design.
    
    RESPONSIBILITIES:
    1. Analyze user requests and plan multi-phase workflows
    2. Coordinate DatabaseAgent, AnalystAgent, and PrimerDesignAgent
    3. Synthesize results into comprehensive summaries
    4. Do NOT call tools yourself - delegate to specialist agents
    
    WORKFLOW PHASES:
    - Phase 1: DatabaseAgent retrieves sequences
    - Phase 2: AnalystAgent performs QC and analysis
    - Phase 3: PrimerDesignAgent designs primers
    
    OUTPUT FORMAT:
    - Clear phase transitions
    - Comprehensive final summary
    - Actionable wet lab recommendations
    """,
    llm_config={
        "config_list": config_list,
        "temperature": 0.0,
        "cache_seed": None
    },
    human_input_mode="NEVER",
    code_execution_config=False
)
```

**Key Characteristics:**
- ✅ No tool registration (pure orchestration)
- ✅ Low temperature (0.0) for consistent planning
- ✅ Comprehensive system message with workflow knowledge
- ✅ Delegates work, doesn't execute

### 2. Specialist Agent (With MCP Tools)

**Purpose**: Execute specific tasks using MCP tools

**Pattern:**
```python
from autogen import ConversableAgent

database_agent = ConversableAgent(
    name="DatabaseAgent",
    system_message="""You are a database retrieval specialist.
    
    TOOLS AVAILABLE:
    - get_sequences: Retrieve DNA/RNA sequences from NCBI, BOLD, SILVA, UNITE
    - get_taxonomy: Verify taxonomic information
    - get_neighbors: Find related species (off-targets)
    - extract_sequence_columns: Parse sequence metadata
    
    RESPONSIBILITIES:
    1. Retrieve target species sequences (species to identify)
    2. Retrieve off-target sequences (related species)
    3. Save sequences to /results/sequences/ with descriptive names
    4. Report file paths and sequence counts
    
    BEST PRACTICES:
    - Use scientific names (e.g., "Salmo salar" not "salmon")
    - Retrieve 50-100 sequences per species for robustness
    - Verify taxonomic names before retrieval
    - Report exactly which files were created
    
    OUTPUT: File paths and statistics, not raw sequences.
    """,
    llm_config={
        "config_list": config_list,
        "temperature": 0.0,
        "cache_seed": None
    },
    human_input_mode="NEVER",
    code_execution_config=False
)

# Register MCP tools with this agent
mcp_bridge.register_tools_for_agent(database_agent, "database")
```

**Key Characteristics:**
- ✅ Specific tool subset registered
- ✅ Domain expertise in system message
- ✅ Clear responsibilities and constraints
- ✅ Output format specified (file paths, not data)

### 3. UserProxy Agent

**Purpose**: Represent user input, initiate workflows

**Pattern:**
```python
from autogen import UserProxyAgent

user_proxy = UserProxyAgent(
    name="User",
    system_message="User providing qPCR design requests.",
    human_input_mode="NEVER",  # For automated workflows
    code_execution_config=False,
    max_consecutive_auto_reply=0,  # Only initiates, doesn't respond
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", "").upper()
)
```

---

## LLM Configuration

### Model Selection (Gemini vs GPT-4)

**Gemini 2.5 Flash Lite (Recommended):**
```python
config_list = [
    {
        "model": "gemini-2.0-flash-lite",
        "api_key": os.getenv("GOOGLE_API_KEY"),
        "api_type": "google"
    }
]
```

**Advantages:**
- ✅ 1M token context window (handles large sequence datasets)
- ✅ Free tier available
- ✅ Fast inference
- ✅ Native AG2 support via `ag2[gemini]`

**GPT-4 (Alternative):**
```python
config_list = [
    {
        "model": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY")
    }
]
```

**Advantages:**
- ✅ Strong reasoning capabilities
- ✅ Reliable function calling
- ⚠️ Smaller context (128K tokens)
- ⚠️ Paid API

### Multi-Model Configuration (Fallback)

```python
config_list = [
    {
        "model": "gemini-2.0-flash-lite",
        "api_key": os.getenv("GOOGLE_API_KEY"),
        "api_type": "google"
    },
    {
        "model": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY")
    }
]
# AG2 will try Gemini first, fallback to GPT-4 if Gemini fails
```

### LLM Parameters

```python
llm_config = {
    "config_list": config_list,
    "temperature": 0.0,       # Deterministic for consistency
    "cache_seed": None,       # Disable caching for fresh responses
    "timeout": 300,           # 5 minutes for complex operations
    "max_tokens": 4096        # Maximum response length
}
```

See [llm-configuration.md](resources/llm-configuration.md) for comprehensive guide.

---

## MCP Bridge Integration

### MCPClientBridge Pattern

**Purpose**: Connect AG2 agents to MCP servers

```python
from autogen_mcp_bridge import MCPClientBridge

# Initialize bridge with server configurations
bridge = MCPClientBridge({
    "database": {
        "container": "ndiag-database-server",
        "command": "python3",
        "args": ["database_mcp_server.py"],
        "cwd": "/app",
        "env": {"LOG_LEVEL": "INFO"}
    },
    "processing": {
        "container": "ndiag-processing-server",
        "command": "python3",
        "args": ["processing_mcp_server.py"],
        "cwd": "/app",
        "env": {"LOG_LEVEL": "INFO"}
    }
})

# Start all MCP servers
await bridge.start_servers()

# Register tools for specific agent
# This makes ONLY database tools available to DatabaseAgent
bridge.register_tools_for_agent(database_agent, "database")

# Analyst gets processing + alignment tools
bridge.register_tools_for_agent(analyst_agent, "processing")
bridge.register_tools_for_agent(analyst_agent, "alignment")

# Cleanup when done
await bridge.stop_servers()
```

**Key Patterns:**
- Each agent gets only the tools it needs
- Bridge manages MCP server lifecycle
- Automatic JSON-RPC communication handling
- Error handling and retries built-in

### Tool Registration Pattern

```python
class MCPClientBridge:
    def register_tools_for_agent(self, agent, server_name: str):
        """Register MCP tools as agent functions."""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not started")
        
        session = self.sessions[server_name]
        tools = await session.list_tools()
        
        for tool in tools.tools:
            # Create wrapper function for this tool
            async def tool_wrapper(**kwargs):
                result = await session.call_tool(tool.name, kwargs)
                return result.content[0].text
            
            # Register with agent
            agent.register_function(
                function_map={
                    tool.name: tool_wrapper
                }
            )
```

See [mcp-bridge-integration.md](resources/mcp-bridge-integration.md) for complete patterns.

---

## Group Chat and Orchestration

### GroupChat Pattern

```python
from autogen import GroupChat, GroupChatManager

# Define agent group
group_chat = GroupChat(
    agents=[coordinator, database_agent, analyst_agent, user_proxy],
    messages=[],
    max_round=50,
    speaker_selection_method="auto"  # Let agents self-select
)

# Manager coordinates the group
manager = GroupChatManager(
    groupchat=group_chat,
    llm_config={"config_list": config_list, "temperature": 0.0}
)

# Start workflow
user_proxy.initiate_chat(
    manager,
    message="Design qPCR assay for Salmo salar vs Oncorhynchus mykiss"
)
```

### Speaker Selection Strategies

**1. Auto (Recommended for mdk_mcp):**
```python
speaker_selection_method="auto"
# Agents decide who speaks next based on context
```

**2. Round Robin:**
```python
speaker_selection_method="round_robin"
# Fixed order: Coordinator → Database → Analyst → Primer
```

**3. Manual (Custom Logic):**
```python
def custom_speaker_selection(last_speaker, groupchat):
    """Custom logic for speaker selection."""
    if last_speaker == coordinator:
        return database_agent
    elif last_speaker == database_agent:
        return analyst_agent
    # ... more logic
    return coordinator

speaker_selection_method=custom_speaker_selection
```

### Workflow Phases Pattern

```python
# Phase 1: Planning
coordinator_msg = """
WORKFLOW PLAN:
1. DatabaseAgent: Retrieve target sequences (Salmo salar, COI, n=100)
2. DatabaseAgent: Retrieve off-target sequences (Oncorhynchus mykiss, COI, n=100)
3. AnalystAgent: Perform QC and alignment
4. AnalystAgent: Find signature regions
5. PrimerDesignAgent: Design primers
DatabaseAgent, please begin with step 1.
"""

# Phase 2: Execution (agents work sequentially)
# Phase 3: Synthesis (coordinator summarizes)
```

---

## System Message Design

### Effective System Message Structure

```python
system_message = """
[ROLE]: You are a <specific role>

[TOOLS AVAILABLE]:
- tool_1: Description
- tool_2: Description

[RESPONSIBILITIES]:
1. Specific task 1
2. Specific task 2
3. Specific task 3

[CONSTRAINTS]:
- Do NOT do X
- ALWAYS do Y
- NEVER do Z

[INPUT FORMAT]:
- What to expect from previous agents

[OUTPUT FORMAT]:
- What to provide to next agents
- File paths, not raw data
- Statistics and summaries

[BEST PRACTICES]:
- Domain-specific guidance
- Quality standards
- Error handling

[EXAMPLES]:
Example 1: ...
Example 2: ...
"""
```

### mdk_mcp Agent System Messages

**Coordinator:**
- Workflow knowledge (4 phases)
- Agent capabilities overview
- Synthesis requirements
- No tool usage

**DatabaseAgent:**
- Database sources (NCBI, BOLD, SILVA, UNITE)
- Scientific name requirements
- File organization patterns
- Sequence count recommendations

**AnalystAgent:**
- QC thresholds (length, N-content)
- Alignment algorithm selection
- Quality assessment criteria
- Signature region requirements

**PrimerDesignAgent:**
- Primer constraints (Tm, GC, length)
- Specificity requirements
- Validation strategies
- Wet lab recommendations

See [system-messages.md](resources/system-messages.md) for complete examples.

---

## Conversation Flow Patterns

### Pattern 1: Linear Pipeline (mdk_mcp)

```python
# User initiates
user_proxy.initiate_chat(
    manager,
    message="Design qPCR for E. coli O157:H7"
)

# Coordinator plans
# → DatabaseAgent executes Phase 1
# → AnalystAgent executes Phase 2-3
# → PrimerDesignAgent executes Phase 4
# → Coordinator synthesizes and terminates

# Each agent:
# 1. Acknowledges task
# 2. Calls tools
# 3. Reports results
# 4. Hands off to next agent
```

### Pattern 2: Iterative Refinement

```python
# Agent calls tool
result = await tool_function(param1="value")

# Checks result quality
if "insufficient data" in result:
    # Refine parameters and retry
    result = await tool_function(param1="better_value", max_results=200)

# Proceeds only when quality threshold met
if sequence_count >= 50:
    # Continue to next phase
    pass
```

### Pattern 3: Error Recovery

```python
try:
    result = await mcp_tool(**params)
    if "Error" in result:
        # Agent handles error gracefully
        alternative_result = await fallback_strategy()
except Exception as e:
    # Agent reports to coordinator
    response = f"Error encountered: {e}. Requesting coordinator guidance."
```

---

## Testing Agent Systems

### Unit Testing Individual Agents

```python
import pytest
from autogen import ConversableAgent

@pytest.mark.asyncio
async def test_database_agent_tool_calling():
    """Test that DatabaseAgent can call MCP tools."""
    
    # Create agent with test configuration
    agent = ConversableAgent(
        name="DatabaseAgent",
        system_message="Test agent",
        llm_config={"config_list": test_config, "temperature": 0.0}
    )
    
    # Register mock MCP tool
    def mock_get_sequences(**kwargs):
        return "Retrieved 10 sequences → /results/test.fasta"
    
    agent.register_function(
        function_map={"get_sequences": mock_get_sequences}
    )
    
    # Test tool call
    response = agent.generate_reply(
        messages=[{
            "role": "user",
            "content": "Get sequences for Escherichia coli"
        }]
    )
    
    assert "sequences" in response["content"].lower()
```

### Integration Testing Multi-Agent Workflows

```python
@pytest.mark.asyncio
async def test_full_qpcr_workflow():
    """Test complete multi-agent qPCR design workflow."""
    
    # Setup agents with real MCP bridge
    bridge = MCPClientBridge(test_server_configs)
    await bridge.start_servers()
    
    # Create agents
    coordinator = create_coordinator()
    database_agent = create_database_agent(bridge)
    analyst_agent = create_analyst_agent(bridge)
    
    # Create group chat
    group_chat = GroupChat(
        agents=[coordinator, database_agent, analyst_agent],
        messages=[],
        max_round=20
    )
    
    manager = GroupChatManager(groupchat=group_chat, llm_config=test_config)
    
    # Execute workflow
    user_proxy.initiate_chat(
        manager,
        message="Test: Design primers for E. coli"
    )
    
    # Verify workflow completion
    chat_history = group_chat.messages
    assert any("Retrieved" in msg["content"] for msg in chat_history)
    assert any("QC Complete" in msg["content"] for msg in chat_history)
    assert "TERMINATE" in chat_history[-1]["content"]
    
    await bridge.stop_servers()
```

### Manual Testing with Interactive Mode

```bash
# Start interactive assistant
./start_interactive.sh

# Test various requests
┌─[qPCR Assistant]
└─> Design qPCR for detecting Salmo salar

# Observe agent collaboration
[Coordinator] Planning workflow...
[DatabaseAgent] Retrieving sequences...
[AnalystAgent] Performing QC...
[PrimerDesignAgent] Designing primers...
[Coordinator] Workflow complete.

# Check logs
┌─[qPCR Assistant]
└─> logs
```

---

## Task Logging and Result Tracking

### Automatic Task Logging Pattern

```python
import json
from datetime import datetime

class TaskLogger:
    def __init__(self):
        self.tasks = []
        self.current_task = None
    
    def start_task(self, user_request: str):
        """Start logging a new task."""
        self.current_task = {
            "timestamp": datetime.now().isoformat(),
            "request": user_request,
            "phases": [],
            "results": [],
            "statistics": {"tools_called": 0, "errors": 0}
        }
    
    def log_tool_call(self, agent: str, tool: str, args: dict, result: str):
        """Log a tool call."""
        self.current_task["phases"].append({
            "agent": agent,
            "tool": tool,
            "arguments": args,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.current_task["statistics"]["tools_called"] += 1
    
    def save_task(self):
        """Save task log to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON log (machine-readable)
        json_path = f"/results/task_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(self.current_task, f, indent=2)
        
        # Text summary (human-readable)
        summary_path = f"/results/task_{timestamp}_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(self.format_summary())
        
        return json_path, summary_path
```

---

## Best Practices for Agent Design

### Agent Design Principles

1. **✅ Single Responsibility**: Each agent has ONE clear purpose
2. **✅ Minimal Tool Set**: Only tools needed for their job
3. **✅ Clear Handoffs**: Pass file paths, not raw data
4. **✅ Comprehensive System Messages**: Include examples and constraints
5. **✅ Error Graceful**: Handle failures without crashing workflow
6. **✅ Temperature 0.0**: For consistent, reproducible behavior
7. **✅ Test Individually**: Before testing as a group
8. **✅ Log Everything**: Task logs for debugging and auditing

### Common Pitfalls to Avoid

- **❌ Tool Overload**: Giving agent too many unrelated tools
- **❌ Vague Roles**: Agent doesn't know its specific job
- **❌ Data in Messages**: Passing large sequences in chat
- **❌ No Coordinator**: Agents talk without orchestration
- **❌ No Termination**: Workflow runs indefinitely
- **❌ High Temperature**: Non-deterministic, inconsistent behavior
- **❌ Poor Error Handling**: One failure breaks entire workflow

---

## mdk_mcp Agent Specifications

### Current Agent Configuration (Phase 1-4)

| Agent | Tools | Temperature | Max Tokens | Human Input |
|-------|-------|-------------|------------|-------------|
| **Coordinator** | 0 | 0.0 | 4096 | NEVER |
| **DatabaseAgent** | 5 | 0.0 | 4096 | NEVER |
| **AnalystAgent** | 10 | 0.0 | 4096 | NEVER |
| **PrimerDesignAgent** | 6 | 0.0 | 4096 | NEVER |
| **UserProxy** | 0 | N/A | N/A | NEVER (automated) |

### Tool Distribution Rationale

- **Coordinator**: 0 tools → Pure orchestration
- **DatabaseAgent**: 5 tools → Focused on retrieval
- **AnalystAgent**: 10 tools → Complex curation pipeline
- **PrimerDesignAgent**: 6 tools → Complete design workflow
- **Total**: 21 active MCP tools across 3 specialist agents

---

## Resource Files

For detailed information on specific topics:

- **[llm-configuration.md](resources/llm-configuration.md)** - LLM model setup and parameters
- **[mcp-bridge-integration.md](resources/mcp-bridge-integration.md)** - MCP bridge patterns
- **[system-messages.md](resources/system-messages.md)** - Effective system message templates
- **[conversation-patterns.md](resources/conversation-patterns.md)** - Advanced conversation flows
- **[testing-agents.md](resources/testing-agents.md)** - Comprehensive testing strategies

---

## Quick Reference

### Agent Creation Template

```python
agent = ConversableAgent(
    name="AgentName",
    system_message="Role and responsibilities",
    llm_config={
        "config_list": config_list,
        "temperature": 0.0,
        "cache_seed": None
    },
    human_input_mode="NEVER",
    code_execution_config=False
)

# Register tools (if specialist agent)
bridge.register_tools_for_agent(agent, "server_name")
```

### Workflow Initiation Template

```python
user_proxy.initiate_chat(
    manager,
    message="User request in natural language"
)
```

### Error Handling Template

```python
# In agent system message
"""
If a tool returns an error:
1. Log the error
2. Try alternative parameters if appropriate
3. Report to Coordinator if unrecoverable
4. Never fail silently
"""
```

---

**Ready to build AG2 agents?** Start with clear role definitions, minimal tool sets, and comprehensive system messages.

