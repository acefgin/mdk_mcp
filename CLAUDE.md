# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **mdk_mcp** (Neglected Diagnostics MCP), an MCP-based system for biological sequence analysis and primer design. The project uses the Model Context Protocol (MCP) to expose bioinformatics capabilities as distributed services that can be orchestrated by AI assistants for natural language-driven diagnostic tool development.

## Architecture

**MCP Server Architecture**: The system is organized into consolidated MCP servers, each handling a major phase of the analysis pipeline:

- **Database Server** (`mcp_servers/database_server/`): Unified access to NCBI, BOLD, SILVA, UNITE, and SRA databases via gget and BioPython
- **Processing Server** (planned): Quality control, deduplication, masking, chimera detection
- **Alignment Server** (planned): MAFFT/MUSCLE alignment + phylogenetic analysis
- **Design Server** (planned): Signature region discovery + Primer3 primer design
- **Validation Server** (planned): BLAST validation + in-silico PCR + literature search
- **Export Server** (planned): Results export + provenance tracking

**Current Status**: Phase 1 (Database Integration) is implemented. The database server provides 12+ MCP tools for sequence retrieval, taxonomic queries, and SRA/BioProject searches.

## Key Technologies

- **MCP Framework**: stdio-based protocol for tool exposure
- **gget**: Standardized genomic database access (Ensembl, NCBI, UniProt)
- **BioPython**: Sequence parsing and manipulation
- **pysradb**: SRA/BioProject metadata access
- **Docker**: Containerized MCP servers with isolated dependencies

## Development Commands

### Build and Run Database Server

```bash
cd mcp_servers/database_server

# Build Docker image
docker build -t ndiag-database-server:latest .

# Run with docker-compose (preferred)
docker-compose up --build

# Run standalone container
docker run -d --name ndiag-database-server -i ndiag-database-server:latest
```

### Testing

```bash
# Run tests for database server
cd mcp_servers/database_server
python -m pytest tests/ -v

# Test specific MCP tool
python tests/test_mcp_client.py
```

### Configuration

Environment variables are set via `.env` file or docker-compose.yml:
- `NCBI_API_KEY`: Optional, increases NCBI rate limits
- `GOOGLE_APPLICATION_CREDENTIALS`: For SRA BigQuery access
- `LOG_LEVEL`: INFO (default), DEBUG, WARNING, ERROR

## Code Structure Patterns

### MCP Server Implementation

Each MCP server follows this structure:
```
mcp_servers/<server_name>/
├── <server_name>_mcp_server.py  # Main server with tool handlers
├── config.py                     # Configuration management
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Local deployment
├── mcp-server.json              # MCP manifest
└── tests/                        # Unit and integration tests
```

### MCP Tool Definition Pattern

Tools are defined using the MCP framework's `@server.list_tools()` and `@server.call_tool()` decorators:

```python
@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="tool_name",
            description="What the tool does",
            inputSchema={
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]):
    if name == "tool_name":
        result = await tool_implementation(**arguments)
    return [types.TextContent(type="text", text=str(result))]
```

### Database Source Integration

The database server uses a unified `get_sequences()` function that routes to source-specific implementations:
- `get_ncbi_sequences()`: Uses BioPython's Entrez API
- `get_bold_sequences()`: REST API calls to BOLD Systems
- `get_silva_sequences()`: SILVA database queries
- `get_unite_sequences()`: UNITE database queries

All sources return standardized FASTA or GenBank format.

### Sequence Metadata Extraction

The `extract_sequence_columns()` tool parses FASTA headers and GenBank records to extract metadata:
- Handles both FASTA (limited metadata) and GenBank (comprehensive metadata) formats
- Supports 20+ metadata fields: Accession, Organism, Geographic Location, Collection Date, Authors, etc.
- Output formats: JSON, CSV, TSV, or formatted table

## Important Design Decisions

1. **stdio Transport**: MCP servers use stdio (not HTTP) for communication. This is the standard MCP protocol.

2. **Consolidated Servers**: Rather than micro-services for each tool, related tools are grouped into logical servers (e.g., all database access in one server) to reduce operational overhead.

3. **gget Integration**: Prioritize gget for genomic database access due to its standardized API, comprehensive coverage, and active maintenance.

4. **Async/Await**: All tool handlers are async functions to support concurrent operations.

5. **Error Handling**: Tools return error messages as strings rather than raising exceptions to maintain MCP protocol compliance.

## Common Development Tasks

### Adding a New MCP Tool

1. Add tool definition to `handle_list_tools()`
2. Add handler case in `handle_call_tool()`
3. Implement async tool function
4. Add unit tests in `tests/`
5. Update README.md with usage examples

### Testing MCP Tools Locally

Use the test client pattern from `tests/test_mcp_client.py`:
```python
async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
    # Send tool call request
    # Parse response
```

### Debugging MCP Communication

- Set `LOG_LEVEL=DEBUG` in environment
- Check logs for tool call arguments and responses
- Use `logger.info()` and `logger.error()` liberally
- MCP communication is JSON-based over stdio

## Roadmap Reference

The project follows a 6-phase roadmap (see `road_map.md`):
- Phase 1: Database Integration (current, 5-7 weeks)
- Phase 2: Sequence Processing (3 weeks)
- Phase 3: Alignment & Phylogenetics (4-5 weeks)
- Phase 4: Design & Primers (7-9 weeks)
- Phase 5: Validation & Literature (4-5 weeks)
- Phase 6: Export & Provenance (1-2 weeks)

Detailed implementation actions for Phases 1-2 are in `phase1-2-actions.md`.

## Dependencies and Versions

- Python 3.11+
- MCP SDK ≥0.9.0
- gget ≥0.28.0
- BioPython ≥1.81
- pysradb ≥1.4.0

See `mcp_servers/database_server/requirements.txt` for full dependency list.

## Known Limitations

- SILVA and UNITE integrations are placeholders (not yet fully implemented)
- Cloud SQL (BigQuery/Athena) requires additional credentials setup
- Rate limiting is basic (no distributed rate limiting across instances)
- No caching layer implemented yet (planned for future)
