# mdk_mcp - Neglected Diagnostics MCP Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![AG2](https://img.shields.io/badge/AG2-0.7.5-green.svg)](https://github.com/ag2ai/ag2)
[![MCP](https://img.shields.io/badge/MCP-0.9.0-purple.svg)](https://modelcontextprotocol.io)

An **MCP (Model Context Protocol)** based multi-agent AI system for designing species-specific qPCR assays for molecular diagnostics. The system uses AG2 (formerly AutoGen) to orchestrate specialized AI agents that collaborate to retrieve sequences, analyze data, and recommend primer design strategies.

**🎉 Phase 4 Complete!** The system now includes complete primer design capabilities with signature region discovery, Primer3 integration, and quality control. **27 total MCP tools** available across database, processing, alignment, and design servers.

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
  Step 2: Perform quality control on sequences
  Step 3: Retrieve COI sequences for Oncorhynchus mykiss
  Step 4: Analyze for signature regions
  Step 5: Recommend primer design strategy

[DatabaseAgent] Calling tool: get_sequences
  Arguments: taxon="Salmo salar", region="COI", max_results=100
  ✓ Retrieved 100 sequences → /results/sequences/Salmo_salar_COI_20251023.fasta

[DatabaseAgent] Calling tool: fasta_qc
  Arguments: min_length=400, max_n_percent=5.0, remove_duplicates=true
  ✓ QC Complete: 87 sequences passed (13 removed: 8 short, 3 high N-content, 2 duplicates)

[DatabaseAgent] Calling tool: get_sequences
  Arguments: taxon="Oncorhynchus mykiss", region="COI", max_results=100
  ✓ Retrieved 100 sequences → /results/sequences/Oncorhynchus_mykiss_COI_20251023.fasta

[AnalystAgent] Analyzing sequences...
  • Compared 87 Salmo salar vs 95 Oncorhynchus mykiss sequences
  • Identified 15 conserved regions in target species
  • Found 3 signature regions unique to Salmo salar
  • Recommending primers in signature region 2 (position 450-470)
  • Expected amplicon size: 120bp

✓ WORKFLOW COMPLETED
Task log saved to /results/task_20251023_181530.json
Sequences saved to /results/sequences/ with README.md
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

### 🔬 Complete Sequence Processing Pipeline (NEW in Phase 2)

The system now provides end-to-end sequence processing capabilities:

1. **Retrieve** sequences from multiple databases (NCBI, BOLD, SILVA, UNITE)
2. **Quality Control** - Filter by length, N-content, remove duplicates
3. **Dereplicate** - Remove redundant sequences, cluster similar ones
4. **Mask** - Hide low-complexity regions to improve alignment
5. **Detect Chimeras** - Identify and remove chimeric sequences
6. **Process** - Run complete pipeline with one command

**Example Workflow:**
```
User: "Get 100 COI sequences for Salmo salar and perform quality control"

[DatabaseAgent] → Retrieves 100 sequences from NCBI
              → Applies QC: min_length=400, max_n_percent=5.0
              → Result: 87 sequences passed (13 filtered out)
              → Sequences saved to /results/sequences/
```

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

Four specialized AI agents collaborate in a clear pipeline for qPCR design:

| Agent | Role | Capabilities | Tools | Phase |
|-------|------|-------------|-------|-------|
| **Coordinator** | Workflow Manager | Plans workflow, orchestrates agents, synthesizes results | 0 tools | Planning + Summary |
| **DatabaseAgent** | Data Retrieval | Retrieves sequences from NCBI/BOLD/SILVA/UNITE/SRA | **5 tools*** | Phase 1: Retrieval |
| **AnalystAgent** | Data Curator & Analyst | QC + processing + alignment + phylogenetics + quality assessment | **10 tools** | Phase 2-3: Curation & Analysis |
| **PrimerDesignAgent** | Primer Designer | Signature region discovery + Primer3 design + oligo QC | **6 tools** | Phase 4: Design |

\*DatabaseAgent: 5 tools active, 6 more planned (gget suite + advanced SRA)

**Architecture Rationale:**
- **Clear Pipeline**: Data flows linearly through specialized agents (Retrieve → Curate → Design)
- **Separation of Concerns**: Each agent has a single, focused responsibility
- **Balanced Workload**: 5 + 10 + 6 tools (21 active total, 27 including planned) - optimized distribution
- **Quality Gates**: AnalystAgent assesses data quality before passing to primer design
- **Scalable**: Easy to add tools to any agent without affecting others (6 database tools + 5 design tools planned)

**Complete Workflow Pipeline:**

```
User Request
    ↓
┌─────────────────────┐
│   Coordinator       │  Plans 4-phase workflow
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  DatabaseAgent      │  Phase 1: Data Retrieval (5 tools)
│  - get_sequences    │  • Retrieve from NCBI/BOLD/SILVA/UNITE
│  - get_taxonomy     │  • Verify species names
│  - get_neighbors    │  • Identify off-targets
└──────────┬──────────┘
           │ Raw sequences (.fasta files)
           ↓
┌─────────────────────┐
│  AnalystAgent       │  Phase 2: Complete Data Curation (10 tools)
│  STEP 1: QC         │  • Quality control (fasta_qc)
│  - process_sequences│  • Dereplicate, mask, detect chimeras
│  STEP 2: Alignment  │  • Multiple sequence alignment (MAFFT/MUSCLE)
│  - align_sequences  │  • Alignment cleaning (CIAlign)
│  STEP 3: Phylogeny  │  • Build trees, calculate distances
│  - build_phylogeny  │  • Assess evolutionary relationships
│  STEP 4: Assessment │  • Evaluate data quality
│  - Quality report   │  • Identify weak points
│  STEP 5: Candidates │  • Find conserved regions (>90% target)
│  - Region analysis  │  • Find variable regions (>30% off-target)
└──────────┬──────────┘
           │ Curated data + quality assessment + candidate regions
           ↓
┌─────────────────────┐
│ PrimerDesignAgent   │  Phase 4: Primer Design & QC (6 tools)
│  - Evaluate regions │  • Assess candidate regions
│  - Design strategy  │  • Recommend primer parameters
│  - Validation plan  │  • In-silico validation strategy
│  - Wet lab protocol│  • Comprehensive validation protocol
└──────────┬──────────┘
           │ Primer recommendations + validation protocol
           ↓
┌─────────────────────┐
│   Coordinator       │  Workflow Orchestration & Summary
│  - Synthesize       │  • Comprehensive workflow summary
│  - Report           │  • Document limitations
│  - Next steps       │  • Wet lab implementation guide
└─────────────────────┘
```

**Key Innovation - AnalystAgent as Data Curator:**
- Takes raw sequences from DatabaseAgent
- Performs **complete data curation pipeline**: QC → processing → alignment → phylogenetics
- Assesses data quality and identifies potential weak points
- Provides curated, analysis-ready data to PrimerDesignAgent
- This ensures high-quality input for primer design decisions

### 🛠️ MCP Tools (15 Tools Active, 6 Planned - Phases 1, 2 & 3 Complete)

#### **Database Server** (Phase 1 ✅ - 5 Tools Active, 6 Planned)
**Used by:** DatabaseAgent (Phase 1: Data Retrieval)

Access to multiple genomic databases and sequence retrieval:

**Currently Active (5 tools):**

1. **get_sequences** - Retrieve DNA/RNA sequences from NCBI, BOLD, SILVA, UNITE
2. **get_taxonomy** - Fetch detailed taxonomic information and verify species names
3. **get_neighbors** - Find taxonomically related species (potential off-targets)
4. **extract_sequence_columns** - Parse sequence metadata (accession, organism, location, etc.)
5. **search_sra_studies** - Search NCBI SRA database for sequencing projects

**Planned - Phase 1 Expansion (6 tools):**

6. **gget_ref** - Get reference genomes from Ensembl
7. **gget_search** - Search Ensembl for genes and transcripts
8. **gget_info** - Fetch detailed gene/transcript information
9. **gget_seq** - Retrieve nucleotide or amino acid sequences by ID
10. **get_sra_runinfo** - Get detailed metadata for SRA runs
11. **search_sra_cloud** - Query SRA via cloud SQL (BigQuery/Athena)

#### **Processing Server** (Phase 2 ✅ - 5 Tools)
**Used by:** AnalystAgent (Phase 2: Data Curation - Step 1: QC)

Quality control and sequence processing pipeline:

1. **fasta_qc** - Comprehensive quality control with filtering:
   - Filter by sequence length (min/max)
   - Filter by N-content percentage
   - Remove duplicate sequences
   - Generate detailed statistics

2. **dereplicate_sequences** - Advanced sequence clustering:
   - Remove exact duplicates (100% identity)
   - Cluster similar sequences (97-99% identity)
   - Per-species dereplication option
   - Maintains representative sequences

3. **mask_low_complexity** - Sequence masking:
   - DUST algorithm for low-complexity regions
   - Masks homopolymers and simple repeats
   - Prevents spurious alignments
   - Configurable threshold

4. **detect_chimeras** - Chimera detection:
   - UCHIME algorithm implementation
   - De novo chimera detection
   - Optional chimera removal
   - Abundance-based filtering

5. **process_sequences** - Unified QC pipeline:
   - Combines all processing steps
   - Sequential: QC → Dereplicate → Mask → Chimera detection
   - Single-command workflow
   - Comprehensive statistics tracking

#### **Alignment Server** (Phase 3 ✅ - 5 Tools)
**Used by:** AnalystAgent (Phase 2: Data Curation - Steps 2-3: Alignment & Phylogenetics)

Multiple sequence alignment and phylogenetic analysis:

1. **align_sequences** - Multiple sequence alignment:
   - Support for MAFFT, MUSCLE, Clustal Omega, gget_muscle
   - Configurable alignment strategies (linsi, ginsi, einsi for MAFFT)
   - Automatic algorithm selection
   - Returns aligned sequences with statistics

2. **process_alignment** - Alignment cleaning and assessment:
   - CIAlign integration for quality improvement
   - Gap-rich column removal
   - Divergent sequence detection
   - Alignment quality statistics

3. **build_phylogeny** - Phylogenetic tree construction:
   - Neighbor Joining (NJ) method
   - Maximum Likelihood (ML) support
   - Multiple distance models (p-distance, Jukes-Cantor, Kimura)
   - Bootstrap support
   - Newick format output

4. **calculate_distances** - Distance matrix calculation:
   - Pairwise distance calculations
   - Multiple evolutionary models
   - p-distance, Jukes-Cantor, Kimura 2-parameter
   - Matrix format output

5. **align_and_analyze** - Complete alignment pipeline:
   - Single-command workflow
   - Alignment + cleaning + phylogeny + distances
   - Configurable pipeline steps
   - Comprehensive analysis output

#### **Design Server** (Phase 4 ✅ Complete - 6 Tools)
**Used by:** PrimerDesignAgent (Phase 4: Primer Design & Validation)
**Container:** `ndiag-design-server`

Complete primer design pipeline with signature region discovery and Primer3 integration:

1. **find_signature_regions** - Automated candidate region discovery:
   - Sliding window analysis (150bp windows, 10bp steps)
   - Conservation scoring within target species (Shannon entropy)
   - Divergence scoring vs off-target species
   - GC content and complexity metrics
   - Returns ranked candidate regions

2. **analyze_specificity** - Specificity analysis:
   - Target vs off-target comparison
   - SNP identification for discrimination
   - Suitability scoring for primer design
   - Flags high-specificity regions

3. **rank_regions** - Multi-criteria ranking:
   - Composite scoring with configurable weights
   - Conservation (40%), Specificity (40%), Complexity (20%)
   - Returns prioritized candidate list
   - Customizable weighting schemes

4. **primer3_design** - Primer3 integration:
   - Full Primer3 wrapper with all parameters
   - Configurable constraints (size, Tm, GC, product size)
   - Returns multiple primer pairs per region
   - Default: 18-27bp, Tm 57-63°C, GC 40-60%

5. **oligo_qc** - Oligonucleotide quality control:
   - Tm calculation with salt correction
   - Secondary structure analysis (ViennaRNA)
   - Hairpin and homodimer detection
   - Pass/fail flags with quality metrics

6. **design_primers_complete** - End-to-end pipeline:
   - Orchestrates entire workflow automatically
   - Region discovery → specificity → ranking → Primer3 → QC
   - Returns only validated, high-quality primers
   - Recommended for automated workflows

**Dependencies:** primer3, ViennaRNA, BioPython, primer3-py

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

### Quick Integration Test

Test all three MCP servers (database, processing, and alignment):

```bash
# Quick standalone test
python3 test_processing_integration.py

# Expected output:
# ✓ Connected to MCP servers
# ✓ Total functions available: 21 (11 database + 5 processing + 5 alignment)
# ✓ fasta_qc call successful!
```

### Comprehensive Test Suite

Run all tests including function calling and individual tool tests:

```bash
# Complete test suite with 4 test suites:
# 1. Basic Function Calling
# 2. Processing MCP Integration
# 3. Alignment MCP Integration
# 4. Individual Processing Tools
python3 test_function_calling.py

# Expected output:
# ✅ PASS  Basic Function Calling
# ✅ PASS  Processing MCP Integration
# ✅ PASS  Alignment MCP Integration
# ✅ PASS  Individual Processing Tools
# Overall: 4/4 test suites passed
```

### Manual Testing

```bash
# Start the system
./start_interactive.sh

# Test with example requests
┌─[qPCR Assistant]
└─> Get 50 COI sequences for Salmo salar and run quality control
    with min_length=400 and max_n_percent=5.0

# Test processing workflow
┌─[qPCR Assistant]
└─> Retrieve sequences for E. coli, perform QC, and remove duplicates

# Verify task logs
┌─[qPCR Assistant]
└─> logs
```

### Unit Tests

```bash
# Test database MCP server
cd mcp_servers/database_server
python -m pytest tests/ -v

# Test processing MCP server
cd mcp_servers/processing_server
python -m pytest tests/ -v

# Test specific tool
python -m pytest tests/test_fasta_qc.py -v
```

### Integration Tests

```bash
# Test MCP bridge communication
cd autogen_app
python -m pytest tests/test_mcp_bridge.py -v

# Test agent collaboration
python -m pytest tests/test_multi_agent.py -v
```

### MCP Server Testing (Interactive)

```bash
# Test database server with MCP Inspector
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py
# Open http://localhost:6274

# Test processing server with MCP Inspector
cd mcp_servers/processing_server
npx @modelcontextprotocol/inspector python3 processing_mcp_server.py
# Open http://localhost:6274

# See comprehensive testing guide
cat docs/MCP_TESTING_GUIDE.md
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
NCBI_API_KEY=your-ncbi-key                    # Increases NCBI rate limits
LOG_LEVEL=INFO                                # DEBUG, INFO, WARNING, ERROR
MCP_DATABASE_SERVER=ndiag-database-server     # Database server container (Phase 1)
MCP_PROCESSING_SERVER=ndiag-processing-server # Processing server container (Phase 2)
MCP_ALIGNMENT_SERVER=ndiag-alignment-server   # Alignment server container (Phase 3)
MCP_DESIGN_SERVER=ndiag-design-server         # Design server container (Phase 4)
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
│  │  (Phase 1✅) │  │  (Phase 2✅) │  │  (Phase 3)   │  │
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
| **Phase 1** | Database | ✅ Complete | get_sequences, get_taxonomy, get_neighbors, extract_sequence_columns, search_sra_studies (5 tools) |
| **Phase 2** | Processing | ✅ Complete | fasta_qc, dereplicate_sequences, mask_low_complexity, detect_chimeras, process_sequences (5 tools) |
| **Phase 3** | Alignment | ✅ Complete | align_sequences, process_alignment, build_phylogeny, calculate_distances, align_and_analyze (5 tools) |
| **Phase 4** | Design | ✅ Complete | find_signature_regions, analyze_specificity, rank_regions, primer3_design, oligo_qc, design_primers_complete (6 tools) |
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
│   ├── processing_server/              # Phase 2: Sequence processing
│   │   ├── processing_mcp_server.py    # Server implementation
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

### Phase 5-6 Implementation
- ✅ ~~Alignment server~~ (COMPLETE - MAFFT/MUSCLE/Clustal Omega, phylogenetics)
- ✅ ~~Design server~~ (COMPLETE - signature regions, Primer3, oligo QC)
- Validation server (BLAST, in-silico PCR, literature search)
- Export server (report generation, provenance tracking)

### Infrastructure
- Sequence caching layer (Redis)
- Rate limiting across distributed instances
- Web UI (React/Vue frontend)
- REST API for programmatic access

### Development & Testing

For developers and contributors:

- 📘 **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Complete troubleshooting guide
- 🧪 **[MCP_TESTING_GUIDE.md](docs/MCP_TESTING_GUIDE.md)** - MCP server testing guide
- 📋 **[MCP_TESTING_QUICKREF.md](docs/MCP_TESTING_QUICKREF.md)** - Quick testing reference
- 📖 **[AUTOGEN_INTEGRATION.md](docs/AUTOGEN_INTEGRATION.md)** - AG2 architecture details
- 🗺️ **[road_map.md](road_map.md)** - Development roadmap

**Quick Test Commands:**
```bash
# Run integration test
python3 test_processing_integration.py

# Run comprehensive test suite
python3 test_function_calling.py

# Test MCP servers interactively
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py
```

## 📞 Support & Help

**Having issues?**
1. 📘 Check **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** for solutions to common problems
2. 📖 Read the **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** for detailed usage instructions
3. 🔍 Search existing [GitHub Issues](https://github.com/acefgin/mdk_mcp/issues)
4. 🐛 Open a new issue with logs and error messages

**For Developers:**
- **Claude Code**: See [CLAUDE.md](CLAUDE.md) for AI assistant guidance
- **Architecture**: Review [docs/AUTOGEN_INTEGRATION.md](docs/AUTOGEN_INTEGRATION.md)
- **Testing**: See [docs/MCP_TESTING_GUIDE.md](docs/MCP_TESTING_GUIDE.md)

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AG2** - Multi-agent framework (formerly Microsoft AutoGen)
- **Google Gemini** - Large language model with 1M context window
- **Model Context Protocol (MCP)** - Tool protocol by Anthropic
- **gget** - Genomic database access library
- **BioPython** - Bioinformatics utilities
- **seqkit** - Fast FASTA/Q file manipulation toolkit
- **vsearch** - Sequence clustering, dereplication, and chimera detection
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
