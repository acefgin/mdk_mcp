# mdk_mcp - Neglected Diagnostics MCP Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![AG2](https://img.shields.io/badge/AG2-0.7.5-green.svg)](https://github.com/ag2ai/ag2)
[![MCP](https://img.shields.io/badge/MCP-0.9.0-purple.svg)](https://modelcontextprotocol.io)

An **MCP (Model Context Protocol)** based multi-agent AI system for designing species-specific qPCR assays for molecular diagnostics. The system uses AG2 (formerly AutoGen) to orchestrate specialized AI agents that collaborate to retrieve sequences, analyze data, and recommend primer design strategies.

## 🎯 What is mdk_mcp?

mdk_mcp is a **bioinformatics automation platform** that combines:
- **MCP Servers**: Modular bioinformatics tools (sequence retrieval, alignment, primer design)
- **AG2 Agents**: Collaborative AI agents with specialized roles
- **Interactive Interface**: Natural language chat for qPCR assay design
- **Task Logging**: Comprehensive workflow tracking and audit trails

### Primary Use Case: qPCR Assay Design

Scientists can interact naturally with the system to design species-specific qPCR primers:

```
┌─[qPCR Assistant]
└─> Design a qPCR assay to identify Atlantic salmon (Salmo salar)
    and distinguish it from rainbow trout (Oncorhynchus mykiss).
    Target: COI region for aquaculture verification.

🚀 STARTING WORKFLOW

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

✓ WORKFLOW COMPLETED
Task log saved to /results/task_20251001_181530.json
```

## 🚀 Quick Start (3 Steps)

### Prerequisites

- Docker and Docker Compose
- **LLM API Key**: Choose one or both:
  - **Google Gemini API key** (recommended - free tier with 1M context window)
  - **OpenAI API key** (GPT-4 support)
- Basic understanding of qPCR assay design

### Step 1: Clone and Configure

```bash
# Clone repository
git clone https://github.com/acefgin/mdk_mcp.git
cd mdk_mcp

# Option A: Use Google Gemini (Recommended - Free with 1M context)
echo "GOOGLE_API_KEY=your-google-api-key" > autogen_app/.env

# Option B: Use OpenAI GPT-4
echo "OPENAI_API_KEY=sk-your-key-here" > autogen_app/.env

# Option C: Use both (system will try Gemini first)
echo "GOOGLE_API_KEY=your-google-api-key" > autogen_app/.env
echo "OPENAI_API_KEY=sk-your-key-here" >> autogen_app/.env

# Optional: Add NCBI API key for higher rate limits
echo "NCBI_API_KEY=your-ncbi-key" >> autogen_app/.env
```

### Step 2: Start Interactive Mode

```bash
# One-command start (recommended)
./start_interactive.sh

# Or manually
docker compose -f docker-compose.autogen.yml up -d
docker attach qpcr-assistant
```

### Step 3: Use the Assistant

Type your qPCR design requests naturally:

```
┌─[qPCR Assistant]
└─> Design qPCR for detecting E. coli O157:H7 in food samples

[Watch agents collaborate in real-time...]

┌─[qPCR Assistant]
└─> help         # Show examples
└─> logs         # View task history
└─> exit         # Exit assistant
```

## ✨ Key Features

### 🧠 Multiple LLM Support

The system supports multiple language models with automatic fallback:

| Model | Provider | Context Window | Cost | Best For |
|-------|----------|----------------|------|----------|
| **gemini-2.5-flash-lite** | Google | 1M tokens | Free tier | Large sequence datasets (recommended) |
| **gpt-4** | OpenAI | 128K tokens | Paid | Complex analysis, reasoning |

**Why Gemini 2.5 Flash Lite?**
- ✅ **1 Million token context window** - Handle large sequence datasets without chunking
- ✅ **Free tier available** - No cost for reasonable usage
- ✅ **Fast inference** - Optimized for speed
- ✅ **Built-in support** - Native AG2 integration via `ag2[gemini]`

Configuration is automatic via `autogen_app/OAI_CONFIG_LIST.json` - the system reads API keys from environment variables.

### 🤖 Multi-Agent Architecture

Three specialized AI agents collaborate on qPCR design:

| Agent | Role | Capabilities |
|-------|------|-------------|
| **Coordinator** | Project Manager | Analyzes requests, creates workflow plans, coordinates agents |
| **DatabaseAgent** | Data Specialist | Retrieves sequences from NCBI/BOLD using 5 MCP tools |
| **AnalystAgent** | Biology Expert | Analyzes sequences, identifies signature regions, recommends primers |

### 🛠️ MCP Tools (Phase 1 Complete)

**Database Server** provides 5 bioinformatics tools:

1. **get_sequences** - Retrieve DNA/RNA sequences from NCBI GenBank or BOLD Systems
2. **get_taxonomy** - Fetch taxonomic information for species
3. **get_neighbors** - Find taxonomically related species (potential off-targets)
4. **extract_sequence_columns** - Parse sequence metadata (accession, location, etc.)
5. **search_sra_studies** - Search SRA database for sequencing projects

### 💬 Interactive Chat Interface

- **Natural Language Input**: Type requests conversationally
- **Real-time Progress**: See agents working as workflows execute
- **Built-in Commands**: `help`, `logs`, `clear`, `exit`
- **Multiple Requests**: Submit many tasks in one session
- **Workflow Control**: Interrupt with Ctrl+C, detach with Ctrl+P+Q

### 📊 Comprehensive Task Logging

Every workflow generates:
- **JSON logs** (`task_TIMESTAMP.json`) - Machine-readable workflow data
- **Text summaries** (`task_TIMESTAMP_summary.txt`) - Human-readable reports

Logs include:
- User requests and timestamps
- Agent actions and coordination
- Tool calls with arguments and results
- Execution statistics (success/failure counts)
- Complete message timeline

### 🐳 Containerized Architecture

- **Isolated MCP servers** - Each tool server runs in its own container
- **AutoGen orchestration** - Separate container for agent runtime
- **Docker Compose** - One-command deployment
- **Kubernetes ready** - Production manifests included

## 📖 Documentation

### User Documentation

- **[docs/INTERACTIVE_MODE.md](docs/INTERACTIVE_MODE.md)** - Complete interactive mode guide
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - 5-minute getting started guide
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - Comprehensive user guide

### Technical Documentation

- **[CLAUDE.md](CLAUDE.md)** - Project overview and development guide
- **[docs/AUTOGEN_INTEGRATION.md](docs/AUTOGEN_INTEGRATION.md)** - AG2 integration details
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[road_map.md](road_map.md)** - Development roadmap (6 phases)

### Historical Documentation

- **[docs/archive/](docs/archive/)** - Previous status reports and testing docs

## 🧪 Testing

### Manual Testing

```bash
# Start the system
./start_interactive.sh

# Test with example requests
┌─[qPCR Assistant]
└─> Design qPCR to identify Mycobacterium tuberculosis
    with specificity against other Mycobacterium species

# Verify task logs
┌─[qPCR Assistant]
└─> logs
```

### Unit Tests

```bash
# Test database MCP server
cd mcp_servers/database_server
python -m pytest tests/ -v

# Test specific tool
python -m pytest tests/test_get_sequences.py -v
```

### Integration Tests

```bash
# Test MCP bridge communication
cd autogen_app
python -m pytest tests/test_mcp_bridge.py -v

# Test agent collaboration
python -m pytest tests/test_multi_agent.py -v
```

### Viewing and Downloading Task Logs

Every workflow generates JSON logs and summary files in the container's `/results` directory:

```bash
# Check container logs
docker logs qpcr-assistant

# View task execution logs
docker exec qpcr-assistant ls -lh /results

# Extract statistics from JSON logs
docker exec qpcr-assistant cat /results/*.json | jq '.statistics'

# Copy all logs to local machine
docker cp qpcr-assistant:/results ./test_logs

# Download specific summary file
docker cp qpcr-assistant:/results/task_20251001_212336_summary.txt ./

# Download specific JSON log
docker cp qpcr-assistant:/results/task_20251001_212336.json ./

# Download all summary files
docker exec qpcr-assistant sh -c 'cd /results && tar czf summaries.tar.gz *_summary.txt'
docker cp qpcr-assistant:/results/summaries.tar.gz ./
tar xzf summaries.tar.gz

# Download all JSON logs
docker exec qpcr-assistant sh -c 'cd /results && tar czf logs.tar.gz *.json'
docker cp qpcr-assistant:/results/logs.tar.gz ./
tar xzf logs.tar.gz
```

## 🚢 Deployment

### Development Deployment

```bash
# Use docker-compose for local development
docker compose -f docker-compose.autogen.yml up -d

# Access logs
docker logs -f qpcr-assistant

# Interactive session
docker attach qpcr-assistant
```

### Production Deployment (Kubernetes)

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/database-server.yaml
kubectl apply -f kubernetes/qpcr-assistant.yaml

# Check status
kubectl get pods -n ndiag

# View logs
kubectl logs -f deployment/qpcr-assistant -n ndiag

# Access service
kubectl port-forward service/qpcr-assistant 8501:8501 -n ndiag
```

### Environment Configuration

**Required (choose one or both):**
```bash
GOOGLE_API_KEY=your-key        # Google Gemini API key (recommended)
OPENAI_API_KEY=sk-...          # OpenAI API key for GPT-4
```

**Optional:**
```bash
NCBI_API_KEY=your-ncbi-key     # Increases NCBI rate limits
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
MCP_DATABASE_SERVER=ndiag-database-server  # Container name
```

**Getting API Keys:**
- **Google Gemini**: Get free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI**: Get API key at [OpenAI Platform](https://platform.openai.com/api-keys)

### Scaling Considerations

- **MCP Servers**: Stateless, can scale horizontally
- **AutoGen Agents**: One instance per user session
- **Database Cache**: Redis/Memcached for sequence caching
- **Rate Limiting**: NCBI API has rate limits (3 req/sec without key, 10 req/sec with key)

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for complete deployment guide.

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       │
│         (Interactive Terminal / REST API)               │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              AutoGen Multi-Agent System                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Coordinator  │  │ DatabaseAgent│  │ AnalystAgent │  │
│  │    Agent     │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
└─────────┼──────────────────┼──────────────────────────┘
          │                  │
          │         ┌────────▼────────┐
          │         │  MCP Bridge     │
          │         │  (stdio client) │
          │         └────────┬────────┘
          │                  │
┌─────────▼──────────────────▼────────────────────────────┐
│                    MCP Servers                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Database   │  │  Processing  │  │  Alignment   │  │
│  │    Server    │  │   Server     │  │   Server     │  │
│  │  (Phase 1)   │  │  (Phase 2)   │  │  (Phase 3)   │  │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  │
└─────────┼──────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────┐
│            External Data Sources                       │
│   NCBI GenBank │ BOLD Systems │ SILVA │ UNITE │ SRA   │
└────────────────────────────────────────────────────────┘
```

### MCP Server Phases

| Phase | Server | Status | Tools |
|-------|--------|--------|-------|
| **Phase 1** | Database | ✅ Complete | get_sequences, get_taxonomy, get_neighbors, extract_sequence_columns, search_sra_studies |
| **Phase 2** | Processing | 🚧 Planned | quality_control, deduplicate, mask_low_complexity, detect_chimeras |
| **Phase 3** | Alignment | 🚧 Planned | align_sequences, build_phylogeny, calculate_distances |
| **Phase 4** | Design | 🚧 Planned | find_signature_regions, design_primers, validate_primers |
| **Phase 5** | Validation | 🚧 Planned | blast_primers, insilico_pcr, search_literature |
| **Phase 6** | Export | 🚧 Planned | export_results, generate_report, track_provenance |

See **[docs/road_map.md](docs/road_map.md)** for detailed roadmap.

## 📂 Project Structure

```
mdk_mcp/
├── README.md                           # This file
├── CLAUDE.md                           # Project overview for Claude Code
├── start_interactive.sh                # One-command launcher
├── docker-compose.autogen.yml          # Docker Compose configuration
│
├── autogen_app/                        # AG2 application
│   ├── qpcr_assistant.py               # Main assistant with interactive interface
│   ├── autogen_mcp_bridge.py           # MCP client bridge for AG2
│   ├── gemini_client.py                # Gemini model client wrapper
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile                      # Container definition
│   ├── .env                            # API keys (create this)
│   ├── .env.template                   # Template for .env file
│   └── OAI_CONFIG_LIST.json            # Model configuration (Gemini + GPT-4)
│
├── mcp_servers/                        # MCP servers
│   ├── database_server/                # Phase 1: Database access
│   │   ├── database_mcp_server.py      # Server implementation
│   │   ├── config.py                   # Configuration
│   │   ├── requirements.txt            # Dependencies
│   │   ├── Dockerfile                  # Container definition
│   │   ├── mcp-server.json             # MCP manifest
│   │   └── tests/                      # Unit tests
│   └── [future servers...]
│
├── docs/                               # Documentation
│   ├── INDEX.md                        # Documentation index and navigation
│   ├── USER_GUIDE.md                   # Comprehensive user reference
│   ├── AUTOGEN_INTEGRATION.md          # AG2 integration architecture
│
├── kubernetes/                         # Kubernetes manifests
│   ├── namespace.yaml
│   ├── database-server.yaml
│   └── qpcr-assistant.yaml
│
└── results/                            # Task logs (generated at runtime in container)
    ├── task_TIMESTAMP.json             # Machine-readable workflow data
    └── task_TIMESTAMP_summary.txt      # Human-readable reports
```

## 🤝 Contributing

Contributions are welcome! Areas needing help:

### Phase 2-6 Implementation
- Processing server (quality control, deduplication)
- Alignment server (MAFFT/MUSCLE integration)
- Design server (signature region discovery, Primer3)
- Validation server (BLAST, in-silico PCR)
- Export server (report generation)

### Infrastructure
- Sequence caching layer (Redis)
- Rate limiting across distributed instances
- Web UI (React/Vue frontend)
- REST API for programmatic access

### Testing

**MCP Server Testing:**
- 📘 **[Complete Testing Guide](docs/MCP_TESTING_GUIDE.md)** - Comprehensive guide for testing MCP servers with Inspector
- 📋 **[Quick Reference](docs/MCP_TESTING_QUICKREF.md)** - Quick commands and examples
- 🧪 **Automated Script**: `./test_mcp_server.sh [database|processing]`

**Test with MCP Inspector:**
```bash
# Database server
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py

# Processing server
cd mcp_servers/processing_server
npx @modelcontextprotocol/inspector python3 processing_mcp_server.py

# Then open http://localhost:6274
```

**Integration Testing:**
- Integration tests for multi-agent workflows
- Load testing for production scenarios
- End-to-end workflow validation

## 🐛 Known Issues

### ~~Token Limit Issue~~ (RESOLVED ✅)

**Previous Problem:** Large sequence datasets (100+ sequences, ~292KB) exceeded GPT-4's token limits.

**Solution:** Integrated **Google Gemini 2.5 Flash Lite** with **1 million token context window**:
- ✅ Handle 100+ sequences (292KB+) without chunking
- ✅ Process entire datasets in single requests
- ✅ No workflow failures due to token limits
- ✅ Free tier available for reasonable usage

**To use:** Set `GOOGLE_API_KEY` in `autogen_app/.env` (see Quick Start above)

### Static Database Sources

**Issue:** SILVA and UNITE integrations are placeholder implementations.

**Status:** Planned for Phase 1 completion.

## 📊 Current Status

**Overall Progress: Phase 1 & 2 Complete (33% of 6-phase roadmap)**

### ✅ Phase 1: Database Integration (COMPLETE)
- 11 MCP tools for sequence retrieval from NCBI, BOLD, SILVA, UNITE, SRA
- gget integration for Ensembl/NCBI access
- Sequence metadata extraction with multiple output formats
- Docker containerization
- Test coverage with pytest
- Full documentation

### ✅ Phase 2: Sequence Processing (COMPLETE)
- 5 MCP tools for sequence QC, dereplication, masking, chimera detection
- seqkit integration for QC and statistics
- vsearch integration for clustering, DUST masking, UCHIME chimera detection
- Unified pipeline orchestration tool
- Docker containerization
- Comprehensive testing guides with MCP Inspector
- Test automation scripts

### ✅ AG2 Multi-Agent System (COMPLETE)
- MCPClientBridge for AG2 ↔ MCP communication
- Multi-agent qPCR assistant system
- Interactive chat interface with readline support
- Comprehensive task logging (JSON + text summaries)
- Docker Compose deployment
- Multi-LLM support (Gemini 2.5 Flash Lite + GPT-4)
- 1M token context window via Gemini

### ✅ Testing Infrastructure (NEW)
- MCP Inspector testing guide (comprehensive)
- Quick reference cards for all tools
- Automated test scripts
- Both UI and CLI testing methods documented

### 🔜 Phase 3: Alignment & Phylogenetics (NEXT)
- MAFFT, MUSCLE, Clustal Omega alignment
- CIAlign for alignment cleaning
- Phylogenetic tree construction
- Distance matrix calculation
- Estimated: 4-5 weeks

### 📋 Future Phases
- Phase 4: Design & Primers (7-9 weeks)
- Phase 5: Validation & Literature (4-5 weeks)
- Phase 6: Export & Provenance (1-2 weeks)

See **[docs/road_map.md](docs/road_map.md)** for complete timeline.

## 🔧 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs qpcr-assistant --tail 50

# Verify API key
cat autogen_app/.env | grep OPENAI_API_KEY

# Rebuild from scratch
docker compose -f docker-compose.autogen.yml down
docker compose -f docker-compose.autogen.yml up --build -d
```

### No Tool Calls Made

```bash
# Verify MCP server connection
docker logs qpcr-assistant 2>&1 | grep "MCP servers connected"

# Check for tool call attempts
docker logs qpcr-assistant 2>&1 | grep "ToolCall"

# Test database server
docker logs ndiag-database-server
```

### Workflow Fails with Token Limit Error

**Error:** `RateLimitError: Requested 73859 tokens, Limit 10000`

**Solution:** This is a known issue. Reduce sequence count in your request or wait for chunking implementation.

### Can't Attach to Container

```bash
# Check if running
docker ps | grep qpcr-assistant

# Start if stopped
docker compose -f docker-compose.autogen.yml up -d

# Attach
docker attach qpcr-assistant
```

## 📞 Support

- **Documentation**: Check [docs/](docs/) folder
- **Issues**: [GitHub Issues](https://github.com/acefgin/mdk_mcp/issues)
- **Task Logs**: Check `/results` directory in container
- **Claude Code**: See [CLAUDE.md](CLAUDE.md) for AI assistant guidance

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AG2** - Multi-agent framework (formerly Microsoft AutoGen)
- **Google Gemini** - Large language model with 1M context window
- **Model Context Protocol (MCP)** - Tool protocol by Anthropic
- **gget** - Genomic database access library
- **BioPython** - Bioinformatics utilities
- **NCBI/BOLD/SILVA/UNITE** - Sequence databases

## 🔗 Links

- **GitHub Repository**: https://github.com/acefgin/mdk_mcp
- **AG2 Documentation**: https://docs.ag2.ai
- **Google Gemini API**: https://makersuite.google.com/app/apikey
- **MCP Specification**: https://modelcontextprotocol.io
- **gget Documentation**: https://github.com/pachterlab/gget

---

**Ready to design qPCR assays with AI?**

```bash
./start_interactive.sh
```

🧬 Welcome to the future of molecular diagnostics!
