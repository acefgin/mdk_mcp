---
name: mcp-server-dev
description: MCP (Model Context Protocol) server development patterns for Python-based bioinformatics tools. Use when creating MCP servers, implementing tool handlers, defining input schemas, working with async/await patterns, testing MCP tools, or containerizing servers. Covers stdio transport, tool registration, error handling, BioPython integration, and Docker deployment.
---

# MCP Server Development Guidelines

## Purpose

Establish consistent patterns for developing MCP servers in the mdk_mcp bioinformatics platform. This skill covers the complete lifecycle of MCP tool development from design to deployment.

## When to Use This Skill

Automatically activates when working on:
- Creating or modifying MCP servers
- Implementing tool handlers (`handle_call_tool`, `handle_list_tools`)
- Defining tool schemas and input validation
- Working with stdio-based MCP communication
- Testing MCP tools with Inspector or pytest
- Integrating bioinformatics libraries (BioPython, seqkit, vsearch, MAFFT)
- Containerizing MCP servers with Docker

---

## Quick Start

### New MCP Tool Checklist

- [ ] **Tool Definition**: Add to `handle_list_tools()` with clear description
- [ ] **Input Schema**: Define JSON schema with proper types and validation
- [ ] **Handler**: Implement in `handle_call_tool()` with async function
- [ ] **Error Handling**: Return error strings, don't raise exceptions
- [ ] **Testing**: Add unit tests in `tests/` directory
- [ ] **Documentation**: Update README with usage examples
- [ ] **Container**: Rebuild Docker image if dependencies changed

### New MCP Server Checklist

- [ ] Directory structure (`mcp_servers/<server_name>/`)
- [ ] Main server file (`<server_name>_mcp_server.py`)
- [ ] Configuration module (`config.py`)
- [ ] Requirements file (`requirements.txt`)
- [ ] Dockerfile with proper base image
- [ ] docker-compose.yml for local testing
- [ ] MCP manifest (`mcp-server.json`)
- [ ] Test suite in `tests/` directory

---

## MCP Architecture Overview

### stdio Transport (Standard MCP Protocol)

MCP servers communicate via **stdin/stdout** (not HTTP):

```
┌──────────────────┐         JSON-RPC         ┌──────────────────┐
│   MCP Client     │ ◄──────over stdio──────► │   MCP Server     │
│  (AG2/Claude)    │      (stdin/stdout)      │  (Python app)    │
└──────────────────┘                          └──────────────────┘
```

**Key Principles:**
- All communication is JSON-RPC 2.0 format
- Server reads from stdin, writes to stdout
- Use `mcp.server.stdio.stdio_server()` for transport
- Never write debug output to stdout (use stderr or logging)

See [stdio-protocol.md](resources/stdio-protocol.md) for complete details.

---

## Core MCP Server Pattern

### Minimal Server Structure

```python
#!/usr/bin/env python3
import asyncio
import logging
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

# Setup logging (to stderr, never stdout!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Goes to stderr by default
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("server-name")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Define available tools.
    Called by client to discover what tools are available.
    """
    return [
        types.Tool(
            name="tool_name",
            description="Clear description of what the tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Parameter description",
                        "default": 100
                    }
                },
                "required": ["param1"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    """
    Handle tool invocation.
    Route to specific tool implementations based on name.
    """
    try:
        if name == "tool_name":
            result = await tool_implementation(**arguments)
            return [types.TextContent(
                type="text",
                text=str(result)
            )]
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        # Return error as text, don't raise
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def tool_implementation(param1: str, param2: int = 100) -> str:
    """
    Actual tool logic implementation.
    Keep handlers separate from routing.
    """
    # Implementation here
    return f"Result for {param1}"

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="server-name",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Tool Definition Patterns

### JSON Schema Best Practices

**Use precise types:**
```python
{
    "type": "object",
    "properties": {
        "taxon": {
            "type": "string",
            "description": "Scientific name (e.g., 'Salmo salar')"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum sequences to retrieve",
            "minimum": 1,
            "maximum": 1000,
            "default": 100
        },
        "min_length": {
            "type": "integer",
            "description": "Minimum sequence length in base pairs"
        },
        "remove_duplicates": {
            "type": "boolean",
            "description": "Remove exact duplicate sequences",
            "default": true
        },
        "databases": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Databases to search",
            "default": ["ncbi", "bold"]
        }
    },
    "required": ["taxon"]
}
```

**Common patterns from mdk_mcp:**

| Type | Example | Validation |
|------|---------|-----------|
| Scientific name | `"Salmo salar"` | String, usually required |
| Gene region | `"COI"`, `"16S"` | String enum or free text |
| File path | `"/results/file.fasta"` | String, validate exists if input |
| Count/limit | `100`, `1000` | Integer with min/max |
| Percentage | `5.0`, `95.0` | Number, 0-100 range |
| Boolean flag | `true`, `false` | Boolean with default |

See [input-schemas.md](resources/input-schemas.md) for comprehensive patterns.

---

## Async/Await Patterns

### Why Async for MCP Tools

1. **I/O Operations**: Most bioinformatics tools involve file I/O, network requests, or subprocess calls
2. **Concurrent Execution**: Multiple tools can run simultaneously
3. **MCP Protocol**: Designed for async communication

### Async Tool Implementation

```python
async def get_sequences(
    taxon: str,
    region: str = "COI",
    max_results: int = 100
) -> str:
    """
    Retrieve sequences asynchronously.
    """
    try:
        # Async file I/O
        sequences = await async_fetch_from_ncbi(taxon, region, max_results)
        
        # Write to file asynchronously
        output_path = f"/results/{taxon}_{region}.fasta"
        async with aiofiles.open(output_path, 'w') as f:
            await f.write(sequences)
        
        return f"✓ Retrieved {len(sequences)} sequences → {output_path}"
    
    except Exception as e:
        logger.error(f"Error retrieving sequences: {e}")
        return f"Error: {str(e)}"
```

### Calling External Tools Asynchronously

```python
import asyncio

async def run_external_tool(command: list[str], input_data: str = None) -> str:
    """
    Run external bioinformatics tool asynchronously.
    """
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if input_data else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate(
        input=input_data.encode() if input_data else None
    )
    
    if process.returncode != 0:
        raise RuntimeError(f"Tool failed: {stderr.decode()}")
    
    return stdout.decode()

# Example: Run MAFFT alignment
async def align_with_mafft(input_fasta: str) -> str:
    """Align sequences using MAFFT."""
    result = await run_external_tool(
        ["mafft", "--auto", input_fasta]
    )
    return result
```

See [async-patterns.md](resources/async-patterns.md) for more examples.

---

## Error Handling

### MCP Error Handling Pattern

**❌ DON'T: Raise exceptions**
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "tool_name":
        raise ValueError("This breaks MCP protocol!")  # ❌ DON'T
```

**✅ DO: Return error messages**
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    try:
        if name == "tool_name":
            result = await tool_implementation(**arguments)
            return [types.TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]  # ✅ Return error as text
```

### Structured Error Messages

```python
def format_error(error_type: str, message: str, details: dict = None) -> str:
    """Format consistent error messages."""
    error_msg = f"❌ {error_type}: {message}"
    if details:
        error_msg += f"\nDetails: {json.dumps(details, indent=2)}"
    return error_msg

# Usage
return [types.TextContent(
    type="text",
    text=format_error(
        "ValidationError",
        "Invalid taxon name",
        {"taxon": taxon, "suggestion": "Use scientific name like 'Salmo salar'"}
    )
)]
```

See [error-handling.md](resources/error-handling.md) for comprehensive patterns.

---

## BioPython Integration Patterns

### Common BioPython Operations in MCP Tools

**Parse FASTA files:**
```python
from Bio import SeqIO

async def parse_fasta(fasta_path: str) -> list:
    """Parse FASTA file and return sequence records."""
    sequences = []
    for record in SeqIO.parse(fasta_path, "fasta"):
        sequences.append({
            "id": record.id,
            "description": record.description,
            "sequence": str(record.seq),
            "length": len(record.seq)
        })
    return sequences
```

**Write FASTA files:**
```python
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

async def write_fasta(sequences: list, output_path: str):
    """Write sequences to FASTA format."""
    records = [
        SeqRecord(
            Seq(seq["sequence"]),
            id=seq["id"],
            description=seq.get("description", "")
        )
        for seq in sequences
    ]
    SeqIO.write(records, output_path, "fasta")
```

**Query NCBI Entrez:**
```python
from Bio import Entrez

Entrez.email = "your@email.com"  # Required by NCBI

async def search_ncbi(taxon: str, region: str, max_results: int):
    """Search NCBI GenBank for sequences."""
    search_term = f"{taxon}[Organism] AND {region}[Gene]"
    
    # Search for IDs
    handle = Entrez.esearch(
        db="nucleotide",
        term=search_term,
        retmax=max_results
    )
    search_results = Entrez.read(handle)
    id_list = search_results["IdList"]
    
    # Fetch sequences
    handle = Entrez.efetch(
        db="nucleotide",
        id=id_list,
        rettype="fasta",
        retmode="text"
    )
    sequences = handle.read()
    return sequences
```

See [biopython-patterns.md](resources/biopython-patterns.md) for complete integration guide.

---

## Testing MCP Servers

### MCP Inspector (Interactive Testing)

**Best for:** Manual testing, exploring tool behavior, debugging

```bash
# Start MCP Inspector
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py

# Opens UI at http://localhost:6274
# - Lists all available tools
# - Interactive tool invocation
# - Real-time request/response inspection
```

### pytest (Automated Testing)

**Best for:** CI/CD, regression testing, comprehensive coverage

```python
# tests/test_tool.py
import pytest
import asyncio
from ..database_mcp_server import get_sequences

@pytest.mark.asyncio
async def test_get_sequences_success():
    """Test successful sequence retrieval."""
    result = await get_sequences(
        taxon="Salmo salar",
        region="COI",
        max_results=10
    )
    
    assert "Retrieved" in result
    assert "sequences" in result
    assert ".fasta" in result

@pytest.mark.asyncio
async def test_get_sequences_invalid_taxon():
    """Test error handling for invalid taxon."""
    result = await get_sequences(
        taxon="InvalidSpecies12345",
        region="COI",
        max_results=10
    )
    
    assert "Error" in result or "0 sequences" in result
```

### Integration Testing with MCP Client

```python
# tests/test_mcp_integration.py
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_full_mcp_workflow():
    """Test complete MCP communication workflow."""
    server_params = StdioServerParameters(
        command="python3",
        args=["database_mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            assert "get_sequences" in tool_names
            
            # Call tool
            result = await session.call_tool(
                "get_sequences",
                arguments={
                    "taxon": "Escherichia coli",
                    "region": "16S",
                    "max_results": 5
                }
            )
            
            assert len(result.content) > 0
            assert "Error" not in result.content[0].text
```

See [testing-guide.md](resources/testing-guide.md) for comprehensive testing patterns.

---

## Docker Integration

### Dockerfile Pattern for MCP Servers

```dockerfile
FROM python:3.11-slim

# Install system dependencies for bioinformatics tools
RUN apt-get update && apt-get install -y \\
    wget \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install bioinformatics tools (if needed)
# Example: MAFFT, MUSCLE, seqkit, etc.
RUN wget -O /usr/local/bin/seqkit.tar.gz \\
    https://github.com/shenwei356/seqkit/releases/download/v2.6.1/seqkit_linux_amd64.tar.gz \\
    && tar -xzf /usr/local/bin/seqkit.tar.gz -C /usr/local/bin/ \\
    && chmod +x /usr/local/bin/seqkit

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY . .

# Run server (stdio mode)
CMD ["python3", "database_mcp_server.py"]
```

### docker-compose.yml for Local Testing

```yaml
version: '3.8'

services:
  database-server:
    build:
      context: .
      dockerfile: Dockerfile
    image: ndiag-database-server:latest
    container_name: ndiag-database-server
    stdin_open: true        # Required for stdio
    tty: false              # Don't allocate TTY (interferes with stdio)
    environment:
      - NCBI_API_KEY=${NCBI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./results:/results  # Shared results directory
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

See [docker-deployment.md](resources/docker-deployment.md) for complete deployment guide.

---

## mdk_mcp Server Architecture

### Server Organization (Phase 1-4)

| Server | Purpose | Tools | Key Libraries |
|--------|---------|-------|---------------|
| **database_server** | Sequence retrieval | 11 tools | gget, BioPython, pysradb |
| **processing_server** | QC & processing | 5 tools | seqkit, vsearch, BioPython |
| **alignment_server** | MSA & phylogeny | 5 tools | MAFFT, MUSCLE, CIAlign |
| **design_server** | Primer design | 6 tools | Primer3, ViennaRNA |

### Tool Naming Conventions

- **Action + Target**: `get_sequences`, `align_sequences`, `design_primers`
- **Process + Type**: `process_sequences`, `calculate_distances`
- **Tool + Operation**: `fasta_qc`, `oligo_qc`

### File Organization Pattern

```
/results/
├── sequences/
│   ├── Salmo_salar_COI_20251023.fasta
│   └── README.md                          # Auto-generated metadata
├── alignments/
│   └── alignment_20251023.fasta
├── phylogenies/
│   └── tree_20251023.nwk
└── task_logs/
    ├── task_20251023_181530.json          # Machine-readable
    └── task_20251023_181530_summary.txt   # Human-readable
```

---

## Quick Reference

### MCP Tool Development Workflow

1. **Design** → Define tool purpose and input schema
2. **Implement** → Create async handler function
3. **Register** → Add to `handle_list_tools()` and `handle_call_tool()`
4. **Test** → Write pytest tests
5. **Manual Test** → Use MCP Inspector
6. **Document** → Update README with examples
7. **Container** → Update Dockerfile if dependencies changed
8. **Deploy** → Rebuild Docker image

### Common MCP Operations

```python
# List all tools
tools = await session.list_tools()

# Call a tool
result = await session.call_tool("tool_name", {"param": "value"})

# Read tool result
text_content = result.content[0].text

# Handle errors
if "Error" in text_content:
    # Handle error
```

### Debugging Tips

- ✅ Use `logging` module (writes to stderr)
- ❌ Never use `print()` (interferes with stdio)
- ✅ Test with MCP Inspector for quick iteration
- ✅ Check Docker logs: `docker logs <container_name>`
- ✅ Validate JSON schema with online validators

---

## Resource Files

For detailed information on specific topics:

- **[stdio-protocol.md](resources/stdio-protocol.md)** - MCP stdio transport deep dive
- **[input-schemas.md](resources/input-schemas.md)** - JSON schema patterns and validation
- **[async-patterns.md](resources/async-patterns.md)** - Advanced async/await patterns
- **[error-handling.md](resources/error-handling.md)** - Comprehensive error handling strategies
- **[biopython-patterns.md](resources/biopython-patterns.md)** - BioPython integration guide
- **[testing-guide.md](resources/testing-guide.md)** - Complete testing methodologies
- **[docker-deployment.md](resources/docker-deployment.md)** - Containerization and deployment

---

## Common Patterns from mdk_mcp

### Pattern: Database Query Tool

```python
async def get_sequences(
    taxon: str,
    region: str = "COI",
    database: str = "ncbi",
    max_results: int = 100
) -> str:
    """Standard pattern for database query tools."""
    try:
        # 1. Validate inputs
        if not taxon:
            return "Error: taxon is required"
        
        # 2. Query database
        sequences = await query_database(taxon, region, database, max_results)
        
        # 3. Generate output path
        timestamp = datetime.now().strftime("%Y%m%d")
        taxon_clean = taxon.replace(" ", "_")
        output_path = f"/results/sequences/{taxon_clean}_{region}_{timestamp}.fasta"
        
        # 4. Write results
        await write_fasta(sequences, output_path)
        
        # 5. Generate metadata README
        await create_readme(output_path, taxon, region, len(sequences))
        
        # 6. Return success message
        return f"✓ Retrieved {len(sequences)} sequences → {output_path}"
    
    except Exception as e:
        logger.error(f"Error in get_sequences: {e}")
        return f"Error: {str(e)}"
```

### Pattern: Processing Pipeline Tool

```python
async def process_sequences(
    input_fasta: str,
    min_length: int = 400,
    max_n_percent: float = 5.0,
    remove_duplicates: bool = True,
    mask_low_complexity: bool = True
) -> str:
    """Standard pattern for multi-step processing tools."""
    try:
        stats = {"input": 0, "passed": 0, "filtered": {}}
        
        # 1. Validate input file
        if not os.path.exists(input_fasta):
            return f"Error: Input file not found: {input_fasta}"
        
        # 2. Count input sequences
        stats["input"] = count_sequences(input_fasta)
        
        # 3. Step 1: Quality control
        qc_output = await run_qc(input_fasta, min_length, max_n_percent)
        stats["filtered"]["qc"] = stats["input"] - count_sequences(qc_output)
        
        # 4. Step 2: Remove duplicates
        if remove_duplicates:
            dedup_output = await remove_duplicates(qc_output)
            stats["filtered"]["duplicates"] = count_sequences(qc_output) - count_sequences(dedup_output)
        else:
            dedup_output = qc_output
        
        # 5. Step 3: Mask low complexity
        if mask_low_complexity:
            final_output = await mask_sequences(dedup_output)
        else:
            final_output = dedup_output
        
        # 6. Calculate final stats
        stats["passed"] = count_sequences(final_output)
        
        # 7. Generate summary
        return format_processing_summary(stats, final_output)
    
    except Exception as e:
        logger.error(f"Error in process_sequences: {e}")
        return f"Error: {str(e)}"
```

---

## Best Practices Summary

1. **✅ Always use async/await** for tool handlers
2. **✅ Return errors as text**, never raise exceptions in handlers
3. **✅ Log to stderr** using `logging` module, never `print()`
4. **✅ Validate inputs** before processing
5. **✅ Generate timestamped output files** for traceability
6. **✅ Create README.md files** with metadata for results
7. **✅ Use type hints** for better code clarity
8. **✅ Test with MCP Inspector** before writing pytest tests
9. **✅ Write comprehensive tests** with pytest
10. **✅ Document tool usage** in server README

---

**Ready to build MCP tools?** Start with the checklist at the top, follow the core patterns, and refer to resource files for deep dives.

