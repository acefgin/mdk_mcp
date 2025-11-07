# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **mdk_mcp** (Neglected Diagnostics MCP), an MCP-based system for biological sequence analysis and primer design. The project uses the Model Context Protocol (MCP) to expose bioinformatics capabilities as distributed services that can be orchestrated by AI assistants for natural language-driven diagnostic tool development.

**Primary Use Case**: Multi-agent AG2 system for qPCR assay design. The MCP servers provide bioinformatics tools that AG2 agents use to help scientists design species-specific qPCR primers for molecular diagnostics.

## Architecture

**MCP Server Architecture**: The system is organized into consolidated MCP servers, each handling a major phase of the analysis pipeline:

- **Database Server** (`mcp_servers/database_server/`) ✅ **COMPLETED**: Unified access to NCBI, BOLD, SILVA, UNITE, and SRA databases via gget and BioPython
- **Processing Server** (`mcp_servers/processing_server/`) ✅ **COMPLETED**: Quality control, deduplication, masking, chimera detection via seqkit and vsearch
- **Alignment Server** (`mcp_servers/alignment_server/`) ✅ **COMPLETED**: Multiple sequence alignment (MAFFT, MUSCLE, Clustal Omega), phylogenetic analysis, and CIAlign-based quality processing
- **Design Server** (not yet implemented): Signature region discovery + Primer3 primer design + CIAlign consensus
- **Validation Server** (not yet implemented): BLAST validation + in-silico PCR + literature search
- **Export Server** (not yet implemented): Results export + provenance tracking

**Current Status (as of October 31, 2025)**:
- **Phase 1 Complete**: Database Integration MCP server (11 tools)
- **Phase 2 Complete**: Processing MCP server (5 tools)
- **Phase 3 Complete**: Alignment MCP server (5 tools)
- **AG2 Integration Complete**: Multi-agent system with MCP bridge functional, all 3 phases integrated
- **Testing Infrastructure**: Comprehensive MCP Inspector testing guides and automation
- **Ready for Phase 4**: System ready to begin Design & Primers Server implementation

## Key Technologies

- **MCP Framework**: stdio-based protocol for tool exposure
- **AG2**: Multi-agent orchestration framework for AI assistants (formerly AutoGen)
- **gget**: Standardized genomic database access (Ensembl, NCBI, UniProt)
- **BioPython**: Sequence parsing and manipulation, phylogenetic analysis
- **pysradb**: SRA/BioProject metadata access
- **seqkit**: Fast FASTA/Q manipulation and statistics
- **vsearch**: Clustering, dereplication, chimera detection, DUST masking
- **MAFFT**: Fast and accurate multiple sequence alignment
- **MUSCLE v5**: High-throughput sequence alignment
- **Clustal Omega**: General-purpose multiple sequence alignment
- **CIAlign**: Alignment cleaning and quality assessment
- **Docker**: Containerized MCP servers with isolated dependencies
- **Kubernetes**: Production orchestration and auto-scaling

## Claude Code Infrastructure

**This project has comprehensive Claude Code infrastructure** (located in `.claude/`) providing development support through auto-activating skills, specialized agents, and testing commands.

### Auto-Activating Skills

Skills that automatically suggest themselves based on your work:

- **mcp-server-dev** (791 lines) - MCP server development patterns, tool handlers, async patterns
  - Triggers: "MCP tool", "MCP server", editing `*_mcp_server.py`

- **ag2-agent-dev** (818 lines) - AG2 multi-agent orchestration, GroupChat, agent collaboration
  - Triggers: "AG2", "agent", "multi-agent", editing `autogen_app/*.py`

- **biopython-dev** (884 lines) - BioPython patterns for SeqIO, Entrez, Phylo, AlignIO
  - Triggers: "BioPython", "SeqIO", "parse FASTA", "Entrez", "phylogenetic tree"

- **primer-design-tools** (1,043 lines) - Primer3, ViennaRNA, qPCR primer design, signature regions
  - Triggers: "Primer3", "primer design", "Tm calculation", "hairpin", "signature region"

- **seq-analysis-tools** (864 lines) - CLI tools integration: seqkit, vsearch, MAFFT, MUSCLE, Clustal Omega
  - Triggers: "seqkit", "vsearch", "MAFFT", "subprocess", "alignment strategy"

- **python-dev-guidelines**, **bioinformatics-workflow**, **docker-container-dev**, **testing-and-qa** - Lightweight skills for general patterns

### Specialized Agents

Autonomous agents for complex tasks (invoke with "Use [agent-name] agent to..."):

- **mcp-tool-reviewer** - Reviews MCP tool implementations for protocol compliance, code quality, error handling
- **qpcr-workflow-planner** - Plans comprehensive qPCR assay design workflows with tool orchestration
- **test-writer** - Generates pytest test scaffolding for MCP tools automatically
- **docker-debugger** - Diagnoses Docker container build/runtime issues for all 4 server setups

### Slash Commands

Quick workflows via slash commands:

- **/dev-docs [task]** - Creates comprehensive development documentation (plan, context, tasks)
- **/test-mcp [server]** - Runs comprehensive MCP server tests (pytest → Docker → Inspector → report)
- **/ag2-test [mode]** - Tests AG2 multi-agent workflows (quick/full/agent/bridge modes)

### Infrastructure Verification

Automated health checks:

```bash
# Verify entire infrastructure (56 tests)
cd .claude && ./verify-infrastructure.sh

# Test hooks functionality (12 tests)
cd .claude/hooks && ./test-hooks.sh
```

### Usage Examples

**Example 1: Parsing FASTA files**
```
You: "I need to parse FASTA files with BioPython in the database server"
→ biopython-dev skill activates automatically
→ Provides: Safe parsing patterns, error handling, SeqIO best practices
```

**Example 2: Designing primers**
```
You: "Calculate Tm for primers using nearest-neighbor method"
→ primer-design-tools skill activates
→ Provides: Primer3 integration, BioPython MeltingTemp, salt corrections
```

**Example 3: Integrating CLI tools**
```
You: "Add seqkit length filtering to processing server"
→ seq-analysis-tools skill activates
→ Provides: Async subprocess patterns, timeout handling, error capture
```

**Example 4: Docker debugging**
```
You: "Use docker-debugger agent to diagnose database server startup failure"
→ Agent analyzes: Dockerfile, docker-compose.yml, logs, dependencies
→ Provides: Specific diagnostics and fix recommendations
```

**Example 5: Testing MCP servers**
```
You: "/test-mcp database"
→ Runs: pytest → Docker build → MCP Inspector → sample tool call
→ Generates: Markdown report with pass/fail status
```

**See `.claude/README.md` for complete infrastructure documentation.**

## Development Commands

### Build and Run MCP Servers

```bash
cd mcp_servers/database_server

# Build Docker image
docker build -t ndiag-database-server:latest .

# Run with docker-compose (preferred)
docker-compose up --build

# Run standalone container
docker run -d --name ndiag-database-server -i ndiag-database-server:latest
```

### Build and Run AG2 qPCR Assistant (Interactive Mode)

```bash
# ONE-COMMAND START (RECOMMENDED) - Interactive chat interface
./start_interactive.sh

# This will:
# 1. Check API key configuration
# 2. Build and start containers
# 3. Launch interactive chat interface
# 4. Allow natural language interaction with agents

# Or manually:
docker-compose -f docker-compose.autogen.yml up --build -d
docker attach qpcr-assistant

# The interactive interface allows you to:
# - Type qPCR design requests naturally
# - See real-time agent collaboration
# - Submit multiple requests in one session
# - Use commands: help, logs, clear, exit

# Or just build
docker-compose -f docker-compose.autogen.yml build

# Run tests
cd autogen_app
pytest tests/
```

### Testing MCP Servers

```bash
# Quick automated testing
./test_mcp_server.sh database    # Test database server
./test_mcp_server.sh processing  # Test processing server
./test_mcp_server.sh alignment   # Test alignment server

# Interactive testing with MCP Inspector (UI mode)
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py
# Open http://localhost:6274

cd mcp_servers/processing_server
npx @modelcontextprotocol/inspector python3 processing_mcp_server.py
# Open http://localhost:6274

cd mcp_servers/alignment_server
npx @modelcontextprotocol/inspector python3 alignment_mcp_server.py
# Open http://localhost:6274

# CLI testing
npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 database_mcp_server.py

# Run unit tests
cd mcp_servers/database_server
python -m pytest tests/ -v

cd mcp_servers/processing_server
python -m pytest tests/ -v

cd mcp_servers/alignment_server
python -m pytest tests/ -v

# See comprehensive guide
# docs/MCP_TESTING_GUIDE.md
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

**💡 Tip: The Claude Code infrastructure (`.claude/`) provides automatic assistance for all development tasks. Skills will auto-activate based on your work context, and you can invoke agents or slash commands for specialized help.**

### Adding a New MCP Tool

1. Add tool definition to `handle_list_tools()`
2. Add handler case in `handle_call_tool()`
3. Implement async tool function
4. Add unit tests in `tests/`
5. Update README.md with usage examples

**Claude Code assistance**: The **mcp-server-dev** skill auto-activates when you mention "MCP tool" or edit `*_mcp_server.py` files. Use the **test-writer** agent to generate test scaffolding: `"Use test-writer agent to generate tests for [tool_name]"`

### Testing MCP Tools Locally

Use the test client pattern from `tests/test_mcp_client.py`:
```python
async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
    # Send tool call request
    # Parse response
```

**Claude Code assistance**: Use `/test-mcp [server]` to run comprehensive tests (pytest → Docker → MCP Inspector → sample tool call). For AG2 testing, use `/ag2-test [mode]`.

### Debugging MCP Communication

- Set `LOG_LEVEL=DEBUG` in environment
- Check logs for tool call arguments and responses
- Use `logger.info()` and `logger.error()` liberally
- MCP communication is JSON-based over stdio

**Claude Code assistance**: For Docker issues, use the **docker-debugger** agent: `"Use docker-debugger agent to diagnose [server_name] startup failure"`. The agent analyzes Dockerfile, docker-compose.yml, logs, and dependencies.

## Roadmap Reference

The project follows a 6-phase roadmap (see `road_map.md`):
- **Phase 1: Database Integration** ✅ **COMPLETED** (7 weeks actual)
  - 11 MCP tools implemented: get_sequences, gget_ref, gget_search, gget_info, gget_seq, get_neighbors, get_taxonomy, search_sra_studies, get_sra_runinfo, search_sra_cloud, extract_sequence_columns
  - Unified access to NCBI, BOLD, SILVA, UNITE, SRA via gget and BioPython
  - Full test coverage with pytest
  - Docker containerization complete
  - AG2 integration bridge implemented and tested
- **Phase 2: Sequence Processing** ✅ **COMPLETED** (1 day actual - ahead of 3-week estimate!)
  - 5 MCP tools implemented: fasta_qc, dereplicate_sequences, mask_low_complexity, detect_chimeras, process_sequences
  - seqkit for QC and statistics, vsearch for clustering/masking/chimera detection
  - Comprehensive MCP Inspector testing guides created
  - Docker containerization with seqkit v2.6.1 + vsearch v2.25.0
  - Test automation scripts and documentation
- **Phase 3: Alignment & Phylogenetics** ✅ **COMPLETED** (1 session actual - ahead of 4-5 week estimate!)
  - 5 MCP tools implemented: align_sequences, process_alignment, build_phylogeny, calculate_distances, align_and_analyze
  - Multiple alignment algorithms: MAFFT (with strategies), MUSCLE v5, Clustal Omega, gget_muscle
  - Phylogenetic methods: Neighbor Joining, Maximum Likelihood, Maximum Parsimony
  - CIAlign integration for alignment cleaning and quality assessment
  - BioPython for distance calculations (p-distance, Jukes-Cantor, Kimura)
  - Docker containerization with MAFFT v7.505 + MUSCLE v5.1 + Clustal Omega
  - Full AG2 integration with AnalystAgent
- **Phase 4: Design & Primers** 🔜 **NEXT** (7-9 weeks estimated)
  - Will include: Signature region discovery, Primer3, CIAlign for consensus generation
- Phase 5: Validation & Literature (4-5 weeks)
- Phase 6: Export & Provenance (1-2 weeks)

## Dependencies and Versions

- Python 3.11+
- MCP SDK ≥0.9.0
- gget ≥0.28.0
- BioPython ≥1.81
- pysradb ≥1.4.0

See `mcp_servers/database_server/requirements.txt` for full dependency list.

## AG2 Integration

The MCP servers are designed to be used by AG2 agents. See `docs/AUTOGEN_INTEGRATION.md` for complete details.

**Key Files**:
- `autogen_app/autogen_mcp_bridge.py` - Bridge between AG2 and MCP servers
- `autogen_app/qpcr_assistant.py` - Multi-agent qPCR design system
- `docker-compose.autogen.yml` - Complete deployment with AG2
- `kubernetes/` - Production Kubernetes manifests

**Quick Example**:
```python
from autogen_mcp_bridge import MCPClientBridge

# Initialize bridge
bridge = MCPClientBridge({"database": {"container": "ndiag-database-server", ...}})
await bridge.start_servers()

# Call MCP tools from AG2 agents
sequences = await bridge.call_tool("database", "get_sequences", {
    "taxon": "Salmo salar",
    "region": "COI",
    "max_results": 100
})
```

## Deployment

- **Development**: Use `docker-compose.autogen.yml`
- **Production**: Use Kubernetes manifests in `kubernetes/`
- See `DEPLOYMENT.md` for complete deployment guide

## Known Limitations

- SILVA and UNITE integrations are placeholders (not yet fully implemented)
- Cloud SQL (BigQuery/Athena) requires additional credentials setup
- Rate limiting is basic (no distributed rate limiting across instances)
- No caching layer implemented yet (planned for future)
- **Phases 4-6 MCP servers not yet implemented** (Phases 1-3 complete: Database + Processing + Alignment)

## What's Been Accomplished

### Phase 1: Database Server
- ✅ 11 fully functional MCP tools for sequence retrieval and database access
- ✅ gget integration for standardized Ensembl/NCBI access
- ✅ BioPython integration for direct NCBI queries
- ✅ pysradb integration for SRA/BioProject searches
- ✅ Sequence metadata extraction tool with multiple output formats (JSON, CSV, TSV, table)
- ✅ Docker containerization with proper dependency management
- ✅ Test coverage with pytest
- ✅ Configuration management via environment variables

### Phase 2: Processing Server
- ✅ 5 fully functional MCP tools for sequence processing
- ✅ seqkit integration for QC, statistics, and basic filtering
- ✅ vsearch integration for clustering, masking (DUST), chimera detection (UCHIME)
- ✅ BioPython for sequence parsing and N-content filtering
- ✅ Unified pipeline orchestration tool (`process_sequences`)
- ✅ Docker containerization with seqkit + vsearch
- ✅ Comprehensive error handling and statistics tracking
- ✅ Test coverage with pytest
- ✅ Complete implementation documentation (README, IMPLEMENTATION_SUMMARY)

### Phase 3: Alignment Server
- ✅ 5 fully functional MCP tools for alignment and phylogenetics
- ✅ Multiple alignment algorithms: MAFFT (auto, linsi, ginsi, einsi), MUSCLE v5, Clustal Omega, gget_muscle
- ✅ CIAlign integration for alignment cleaning and quality assessment
- ✅ Phylogenetic tree construction: Neighbor Joining, Maximum Likelihood, Maximum Parsimony
- ✅ Distance matrix calculation with multiple models (p-distance, Jukes-Cantor, Kimura)
- ✅ BioPython for phylogenetic analysis and tree manipulation
- ✅ Unified pipeline tool (`align_and_analyze`) combining alignment, cleaning, and phylogeny
- ✅ Docker containerization with MAFFT v7.505 + MUSCLE v5.1 + Clustal Omega v1.2
- ✅ Test coverage with pytest
- ✅ Complete implementation documentation (README, IMPLEMENTATION_SUMMARY)
- ✅ Full AG2 integration with AnalystAgent (10 tools: 5 processing + 5 alignment)

### AG2 Integration
- ✅ MCPClientBridge implemented (`autogen_app/autogen_mcp_bridge.py`)
- ✅ Multi-agent qPCR assistant system (`autogen_app/qpcr_assistant.py`)
- ✅ Docker Compose deployment for integrated AG2+MCP system
- ✅ Interactive chat interface for natural language primer design requests
- ✅ Tested and functional end-to-end workflow
- ✅ Sequence organization with automatic file management and README generation

### Testing Infrastructure
- ✅ MCP Inspector testing guide (741 lines, comprehensive)
- ✅ MCP testing quick reference card
- ✅ Automated test script (`test_mcp_server.sh`)
- ✅ Updated documentation with testing sections

### Claude Code Infrastructure
- ✅ **9 auto-activating skills** (8,508 total lines of infrastructure)
  - mcp-server-dev (791 lines), ag2-agent-dev (818 lines), biopython-dev (884 lines)
  - primer-design-tools (1,043 lines), seq-analysis-tools (864 lines)
  - python-dev-guidelines, bioinformatics-workflow, docker-container-dev, testing-and-qa
- ✅ **4 specialized agents** for complex tasks
  - mcp-tool-reviewer (501 lines) - MCP protocol compliance review
  - qpcr-workflow-planner (615 lines) - qPCR assay design planning
  - test-writer (561 lines) - Automated pytest test generation
  - docker-debugger (778 lines) - Docker troubleshooting diagnostics
- ✅ **3 slash commands** for streamlined workflows
  - /dev-docs - Comprehensive development documentation generation
  - /test-mcp (296 lines) - MCP server testing (pytest → Docker → Inspector)
  - /ag2-test (501 lines) - AG2 multi-agent workflow testing
- ✅ **2 smart hooks** for context awareness
  - skill-activation-prompt - Auto-suggests skills based on work context
  - post-tool-use-tracker - Tracks file changes and provides reminders
- ✅ **Automated verification** (68 tests total, 100% passing)
  - test-hooks.sh (12 tests) - Hook functionality validation
  - verify-infrastructure.sh (56 tests) - Complete infrastructure health checks
- ✅ **Comprehensive documentation**
  - Priority 1, 2, 3 completion summaries
  - Complete infrastructure summary
  - Usage examples and patterns for all components

**Infrastructure Coverage**: 100% across all development areas (MCP, AG2, BioPython, primer design, CLI tools, Docker, testing)

## What's Next (Phase 4)

The Design Server is the next priority, which will add:
- Signature region discovery and identification
- Primer3 integration for qPCR primer design
- CIAlign for consensus sequence generation
- Specificity analysis for designed primers
- Multi-criteria primer evaluation (Tm, GC content, secondary structures)
- Unified `design_primers` pipeline tool

See `road_map.md` Phase 4 for detailed specifications.
