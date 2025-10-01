# AG2 Integration Architecture

**Purpose**: Enable MCP servers as tools for AG2 agents to assist scientists in qPCR assay design for species identification.

## Overview

This project provides MCP (Model Context Protocol) servers that expose bioinformatics tools. AG2 agents orchestrate these tools to create an intelligent assistant for qPCR assay design.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AG2 Multi-Agent System                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Coordinator  │  │   Database   │  │   Designer   │      │
│  │    Agent     │  │     Agent    │  │    Agent     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                           │                                   │
└───────────────────────────┼───────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  MCP Client    │
                    │    Bridge      │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│   Database     │  │ Processing  │  │   Alignment     │
│  MCP Server    │  │ MCP Server  │  │  MCP Server     │
│  (Phase 1)     │  │ (Phase 2)   │  │  (Phase 3)      │
└────────────────┘  └─────────────┘  └─────────────────┘
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│   Design       │  │ Validation  │  │    Export       │
│  MCP Server    │  │ MCP Server  │  │  MCP Server     │
│  (Phase 4)     │  │ (Phase 5)   │  │  (Phase 6)      │
└────────────────┘  └─────────────┘  └─────────────────┘
```

## AG2 Agent Roles

### 1. Coordinator Agent
**Role**: Orchestrate workflow, interpret user intent, coordinate other agents

**Responsibilities**:
- Parse user requests (e.g., "Design qPCR primers for salmon identification")
- Create workflow plans
- Manage agent collaboration
- Summarize results for users

### 2. Database Agent
**Role**: Retrieve and analyze sequence data

**MCP Tools Used**:
- `get_sequences` - Retrieve target and off-target sequences
- `get_taxonomy` - Understand taxonomic relationships
- `get_neighbors` - Identify closely related species
- `extract_sequence_columns` - Parse metadata

**Workflow**:
1. Search for target species sequences
2. Identify potential off-target species
3. Retrieve comprehensive sequence datasets
4. Extract and organize metadata

### 3. Designer Agent
**Role**: Design qPCR primers and probes

**MCP Tools Used** (when Phase 4 complete):
- `find_signature_regions` - Identify target-specific regions
- `primer3_design` - Design primers
- `oligo_qc` - Validate primer quality

**Workflow**:
1. Analyze sequences from Database Agent
2. Identify signature regions
3. Design candidate primers
4. Optimize for specificity and efficiency

### 4. Validator Agent
**Role**: Validate primer designs

**MCP Tools Used** (when Phase 5 complete):
- `blast_nt` - Check specificity
- `in_silico_pcr` - Test amplification
- `assess_coverage` - Evaluate target coverage

**Workflow**:
1. BLAST primers against databases
2. Run in-silico PCR simulations
3. Assess coverage across target species
4. Identify potential cross-reactivity

### 5. Report Agent
**Role**: Generate comprehensive reports

**MCP Tools Used** (when Phase 6 complete):
- `export_panel` - Export primer sequences
- `generate_report` - Create documentation
- `record_provenance` - Track design decisions

## MCP Client Bridge for AutoGen

AutoGen agents need a bridge to communicate with MCP servers via stdio protocol.

### Bridge Architecture

```python
# autogen_mcp_bridge.py
import asyncio
import json
from typing import Dict, Any, List
import subprocess


class MCPClientBridge:
    """Bridge between AutoGen and MCP servers."""

    def __init__(self, server_configs: Dict[str, str]):
        """
        Initialize MCP client bridge.

        Args:
            server_configs: Dict mapping server names to container names
                           {"database": "ndiag-database-server", ...}
        """
        self.servers = server_configs
        self.processes = {}

    async def start_servers(self):
        """Start stdio connections to MCP servers."""
        for server_name, container_name in self.servers.items():
            # Connect to MCP server via docker exec
            process = await asyncio.create_subprocess_exec(
                "docker", "exec", "-i", container_name,
                "python", "/app/database_mcp_server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.processes[server_name] = process

            # Initialize MCP connection
            await self._initialize_server(server_name)

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool.

        Args:
            server: Server name (e.g., "database")
            tool_name: Tool to call (e.g., "get_sequences")
            arguments: Tool arguments

        Returns:
            Tool result
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._gen_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        process = self.processes[server]

        # Send request
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # Read response
        response_line = await process.stdout.readline()
        response = json.loads(response_line.decode())

        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")

        return response["result"]

    async def list_tools(self, server: str) -> List[Dict[str, Any]]:
        """List available tools from a server."""
        request = {
            "jsonrpc": "2.0",
            "id": self._gen_request_id(),
            "method": "tools/list",
            "params": {}
        }

        process = self.processes[server]
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        response_line = await process.stdout.readline()
        response = json.loads(response_line.decode())

        return response["result"]["tools"]


# AutoGen Function Wrappers
def create_autogen_functions(bridge: MCPClientBridge) -> List[Dict]:
    """
    Create AutoGen-compatible function definitions from MCP tools.

    Returns:
        List of function definitions for AutoGen agents
    """
    functions = []

    # Database Server Functions
    functions.append({
        "name": "get_sequences",
        "description": "Retrieve biological sequences from multiple databases (NCBI, BOLD, gget)",
        "parameters": {
            "type": "object",
            "properties": {
                "taxon": {
                    "type": "string",
                    "description": "Scientific name or taxon ID (e.g., 'Salmo salar')"
                },
                "region": {
                    "type": "string",
                    "enum": ["COI", "16S", "ITS", "mitogenome", "whole"],
                    "description": "Target genomic region"
                },
                "source": {
                    "type": "string",
                    "enum": ["gget", "ncbi", "bold", "silva", "unite"],
                    "default": "ncbi",
                    "description": "Database source"
                },
                "max_results": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum number of sequences to retrieve"
                }
            },
            "required": ["taxon"]
        }
    })

    functions.append({
        "name": "get_taxonomy",
        "description": "Get detailed taxonomic information for a species",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Species name or accession number"
                }
            },
            "required": ["query"]
        }
    })

    functions.append({
        "name": "get_neighbors",
        "description": "Find taxonomically similar species (potential off-targets)",
        "parameters": {
            "type": "object",
            "properties": {
                "taxon": {
                    "type": "string",
                    "description": "Target taxon name"
                },
                "rank": {
                    "type": "string",
                    "enum": ["species", "genus", "family"],
                    "description": "Taxonomic rank for neighbor search"
                },
                "distance": {
                    "type": "integer",
                    "default": 1,
                    "description": "Taxonomic distance"
                }
            },
            "required": ["taxon", "rank"]
        }
    })

    functions.append({
        "name": "extract_sequence_columns",
        "description": "Extract metadata columns from sequence data",
        "parameters": {
            "type": "object",
            "properties": {
                "sequence_data": {
                    "type": "string",
                    "description": "FASTA, GenBank, or JSON sequence data"
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to extract (Id, Accession, Organism, etc.)"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["json", "csv", "tsv"],
                    "default": "json"
                }
            },
            "required": ["sequence_data"]
        }
    })

    return functions


# Async function implementations for AutoGen
async def autogen_get_sequences(
    bridge: MCPClientBridge,
    taxon: str,
    region: str = "COI",
    source: str = "ncbi",
    max_results: int = 100
) -> str:
    """AutoGen-callable wrapper for get_sequences."""
    result = await bridge.call_tool(
        server="database",
        tool_name="get_sequences",
        arguments={
            "taxon": taxon,
            "region": region,
            "source": source,
            "max_results": max_results
        }
    )
    return result


async def autogen_get_taxonomy(
    bridge: MCPClientBridge,
    query: str
) -> str:
    """AutoGen-callable wrapper for get_taxonomy."""
    result = await bridge.call_tool(
        server="database",
        tool_name="get_taxonomy",
        arguments={"query": query}
    )
    return result
```

## Deployment Configuration

### Docker Compose for AutoGen + MCP

```yaml
# docker-compose.autogen.yml
version: '3.8'

services:
  # MCP Servers (Phase 1 - Database)
  database-server:
    build: ./mcp_servers/database_server
    container_name: ndiag-database-server
    stdin_open: true  # Keep stdin open for MCP stdio protocol
    tty: false
    networks:
      - ndiag-network
    environment:
      - NCBI_API_KEY=${NCBI_API_KEY:-}
      - LOG_LEVEL=INFO
    restart: unless-stopped

  # Future MCP servers (when implemented)
  # processing-server:
  #   build: ./mcp_servers/processing_server
  #   container_name: ndiag-processing-server
  #   stdin_open: true
  #   networks:
  #     - ndiag-network

  # AutoGen Agent Application
  autogen-qpcr-assistant:
    build: ./autogen_app
    container_name: qpcr-assistant
    depends_on:
      - database-server
    networks:
      - ndiag-network
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_DATABASE_SERVER=ndiag-database-server
      - LOG_LEVEL=INFO
    volumes:
      - ./autogen_app:/app
      - ./results:/results  # For saving primer designs
    ports:
      - "8501:8501"  # Streamlit UI
    command: python qpcr_assistant.py

networks:
  ndiag-network:
    driver: bridge
```

### AutoGen Application Dockerfile

```dockerfile
# autogen_app/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install AutoGen and dependencies
RUN pip install --no-cache-dir \
    pyautogen>=0.2.0 \
    openai>=1.0.0 \
    streamlit>=1.28.0 \
    pandas>=2.0.0 \
    biopython>=1.81

# Copy application code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "qpcr_assistant.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Example AutoGen Agent Configuration

```python
# autogen_app/qpcr_assistant.py
import autogen
import asyncio
from autogen_mcp_bridge import MCPClientBridge, create_autogen_functions


# Configuration
config_list = [
    {
        "model": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY")
    }
]

llm_config = {
    "config_list": config_list,
    "timeout": 120,
    "temperature": 0.7,
}

# Initialize MCP Bridge
mcp_bridge = MCPClientBridge({
    "database": "ndiag-database-server",
    # "processing": "ndiag-processing-server",  # When Phase 2 ready
    # "alignment": "ndiag-alignment-server",    # When Phase 3 ready
    # "design": "ndiag-design-server",          # When Phase 4 ready
})

await mcp_bridge.start_servers()

# Create AutoGen agents
coordinator = autogen.AssistantAgent(
    name="Coordinator",
    system_message="""You are a qPCR assay design coordinator.
    Your role is to:
    1. Understand user requirements for species identification
    2. Coordinate with Database Agent to gather sequences
    3. Orchestrate the primer design workflow
    4. Present results to the user

    Always think step-by-step and explain your reasoning.""",
    llm_config=llm_config
)

database_agent = autogen.AssistantAgent(
    name="DatabaseAgent",
    system_message="""You are a biological database specialist.
    Your role is to:
    1. Retrieve target species sequences
    2. Identify closely related species (off-targets)
    3. Gather comprehensive sequence datasets
    4. Extract and organize sequence metadata

    Use the MCP tools: get_sequences, get_taxonomy, get_neighbors, extract_sequence_columns""",
    llm_config={
        **llm_config,
        "functions": create_autogen_functions(mcp_bridge)
    }
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    code_execution_config=False
)

# Register MCP functions
@user_proxy.register_for_execution()
@database_agent.register_for_llm(description="Retrieve biological sequences from databases")
async def get_sequences(taxon: str, region: str = "COI", source: str = "ncbi", max_results: int = 100):
    """Retrieve sequences for a taxon from biological databases."""
    result = await mcp_bridge.call_tool(
        "database",
        "get_sequences",
        {"taxon": taxon, "region": region, "source": source, "max_results": max_results}
    )
    return result

@user_proxy.register_for_execution()
@database_agent.register_for_llm(description="Get taxonomic information")
async def get_taxonomy(query: str):
    """Get taxonomic information for a species."""
    result = await mcp_bridge.call_tool(
        "database",
        "get_taxonomy",
        {"query": query}
    )
    return result

# Start group chat
groupchat = autogen.GroupChat(
    agents=[user_proxy, coordinator, database_agent],
    messages=[],
    max_round=20
)

manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Example interaction
user_proxy.initiate_chat(
    manager,
    message="""I need to design a qPCR assay to identify Atlantic salmon (Salmo salar)
    and distinguish it from rainbow trout (Oncorhynchus mykiss).
    The assay should target the COI gene region."""
)
```

## Kubernetes Deployment (Production)

For production deployment with auto-scaling and service discovery, see `kubernetes/` directory.

Key features:
- StatefulSet for MCP servers
- Service mesh for inter-container communication
- Horizontal Pod Autoscaler for AutoGen application
- Persistent volumes for results storage

## Interface Summary

### For AutoGen Developers

**What you need**:
1. MCP servers running in Docker containers
2. `autogen_mcp_bridge.py` - Bridging library
3. Function definitions from `create_autogen_functions()`
4. Register functions with AutoGen agents

**Example Usage**:
```python
# 1. Start MCP servers
bridge = MCPClientBridge({"database": "ndiag-database-server"})
await bridge.start_servers()

# 2. Get function definitions
functions = create_autogen_functions(bridge)

# 3. Configure AutoGen agent with MCP tools
agent = autogen.AssistantAgent(
    name="DatabaseAgent",
    llm_config={"functions": functions}
)

# 4. Use tools in conversation
result = await get_sequences(taxon="Salmo salar", region="COI")
```

## Next Steps

1. ✅ Create AutoGen-MCP bridge library
2. ✅ Configure Docker deployment
3. Create example qPCR assistant application
4. Test AutoGen-MCP integration
5. Create Kubernetes manifests
6. Document best practices for multi-agent workflows
