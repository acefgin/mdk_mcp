# mdk_mcp - Neglected Diagnostics MCP Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![TypeScript 5.3+](https://img.shields.io/badge/typescript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![AG2](https://img.shields.io/badge/AG2-0.7.5-green.svg)](https://github.com/ag2ai/ag2)
[![MCP](https://img.shields.io/badge/MCP-2.0-purple.svg)](https://modelcontextprotocol.io)

An **MCP (Model Context Protocol)** based multi-agent AI system for designing species-specific qPCR assays for molecular diagnostics. The system uses AG2 (formerly AutoGen) to orchestrate specialized AI agents that collaborate to retrieve sequences, analyze data, and recommend primer design strategies.

**🚀 MCP 2.0 Migration!** Now featuring **code execution architecture** for 99.1% token reduction, 2.5x faster workflows, and 95.9% cost savings. Phase 5 complete with **34 total MCP tools** across 5 servers + TypeScript infrastructure.

## 🎯 What is mdk_mcp?

mdk_mcp is a **bioinformatics automation platform** that combines:
- **MCP Servers**: Modular bioinformatics tools (sequence retrieval, alignment, primer design)
- **AG2 Agents**: Collaborative AI agents with specialized roles
- **Interactive Interface**: Natural language chat for qPCR assay design
- **Task Logging**: Comprehensive workflow tracking and audit trails
- **Code Execution Architecture**: NEW - 99% token reduction with Node.js/TypeScript tools

## 🚀 MCP 2.0 Migration: Code Execution Architecture

**Status**: Phase 1 Infrastructure Complete ✅

The platform now supports **dual architecture**: Python MCP servers (production-ready) + Node.js/TypeScript tools (optimized for cost and performance).

### Why Code Execution?

**Traditional MCP** (Current Python servers):
```
Load all 34 tools → 150,000 tokens
Pass data through AI model → 50,000 tokens per dataset
Total: 200,000 tokens per workflow ($0.60 per analysis)
```

**Code Execution** (New TypeScript infrastructure):
```
Load tools on-demand → 400 tokens per tool
Process data in code → 200 tokens for summary
Total: 2,500 tokens per workflow ($0.008 per analysis)
```

### Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Token Usage** | 283,000 | 2,500 | **99.1% reduction** |
| **Cost per Analysis** | $0.92 | $0.04 | **95.9% reduction** |
| **Workflow Speed** | 37 seconds | 15 seconds | **2.5x faster** |
| **Dataset Limit** | 1,000 sequences | Unlimited | **No limits** |
| **Annual Savings** | — | — | **$886.50/year** |

### New Infrastructure Components

1. **Tool File Generator** (`mcp_servers/shared/tool-generator.ts`)
   - Automated type-safe TypeScript wrappers from MCP schemas
   - 445 lines, 45 unit tests

2. **MCP Code Execution Client** (`examples/mcp-client-demo.ts`)
   - Progressive tool discovery (99.7% token reduction)
   - Connection management with retry logic
   - 571 lines, 25 integration tests

3. **PII Tokenization System** (`examples/pii-tokenization-demo.ts`)
   - Zero PII exposure to AI models
   - 6 PII pattern types with audit logging
   - 350 lines, 40+ unit tests, complete security docs

4. **Skills Manager** (`examples/skills-manager-demo.ts`)
   - Context-aware workflow reuse
   - Automatic skill discovery and matching
   - 600 lines, 50+ unit tests

5. **Code Execution Sandbox** (`examples/executor-demo.ts`)
   - Docker-based isolation (7-layer security)
   - Network restrictions and resource limits
   - 700 lines, 60+ tests

**Documentation**: See `docs/MIGRATION_EXECUTIVE_SUMMARY.md`, `docs/TOKEN_COMPARISON.md`, and `docs/PHASE_1_COMPLETE.md` for complete details.

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

> **Note**: For **Claude Desktop integration**, see [🖥️ Claude Desktop Integration](#️-claude-desktop-integration-typescript-mcp-wrapper) below.

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

## 🖥️ Claude Desktop Integration (TypeScript MCP Wrapper)

### Overview

In addition to the AG2 multi-agent system, this project includes a **TypeScript MCP wrapper** that enables direct integration with Claude Desktop on Windows/Mac. This provides a lightweight, token-efficient way to access all bioinformatics tools directly from Claude Desktop.

### Quick Setup (2 Steps)

#### Step 1: Build TypeScript Workspace & Start Docker Containers

```bash
cd mdk_mcp

# Build the complete TypeScript workspace (client library + all server modules + MCP server)
npm run build:workspace

# Verify build succeeded (optional)
./scripts/verify-build.sh

# Start all Python MCP servers in Docker
docker-compose -f docker-compose.autogen.yml up -d

# Verify containers are running (should see 5 containers)
docker ps | grep ndiag
```

**What `npm run build:workspace` does:**
- **Compiles MCP client library**: `workspace/lib/mcp-client.ts` → `mcp-client.js` (Docker bridge)
- **Generates TypeScript tool wrappers**: 34 type-safe modules from Python MCP servers
- **Compiles all server modules**: database (11), processing (5), alignment (5), design (6), validation (7)
- **Compiles main MCP server**: `workspace/mcp-server.ts` → `mcp-server.js`
- **Total output**: 41 JavaScript files ready for Claude Desktop

**Docker containers:**
  - `ndiag-database-server` - Sequence retrieval (11 tools)
  - `ndiag-processing-server` - Quality control (5 tools)
  - `ndiag-alignment-server` - Sequence alignment (5 tools)
  - `ndiag-design-server` - Primer design (6 tools)
  - `ndiag-validation-server` - Validation tools (7 tools)

#### Step 2: Configure Claude Desktop

**For Windows + WSL2:**

Edit `C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mdk-typescript": {
      "command": "wsl",
      "args": [
        "-e",
        "bash",
        "-c",
        "cd /home/cxl/MDK_Design/mdk_mcp && node workspace/mcp-server.js"
      ],
      "env": {
        "DEBUG": "false"
      }
    }
  }
}
```

**For macOS/Linux:**

```json
{
  "mcpServers": {
    "mdk-typescript": {
      "command": "node",
      "args": [
        "/absolute/path/to/mdk_mcp/workspace/mcp-server.js"
      ],
      "env": {
        "DEBUG": "false"
      }
    }
  }
}
```

**Restart Claude Desktop**, then test:

```
What tools do you have from mdk-typescript?
```

### How It Works (Hybrid Execution Strategy)

```
┌─────────────────────────────────────────┐
│     Claude Desktop (Windows/Mac)        │
│   - User sends prompts                  │
│   - MCP client built-in                 │
└─────────────┬───────────────────────────┘
              │ stdio (JSON-RPC)
              │
┌─────────────▼───────────────────────────┐
│  TypeScript MCP Wrapper (Node.js)       │
│  workspace/mcp-server.js                │
│  - Progressive tool discovery (99% ↓)   │
│  - 34 tool definitions (~400 tokens)    │
│  - Hybrid execution:                    │
│    1. Try generated TypeScript module   │
│    2. Fallback to Docker bridge         │
└─────────────┬───────────────────────────┘
              │
              ├─[Generated Modules]─────────┐
              │                             │
┌─────────────▼───────────────────┐ ┌──────▼──────────────────────────┐
│ TypeScript Tool Modules (34)    │ │  Direct Docker Bridge           │
│ workspace/servers/*/            │ │  workspace/lib/mcp-client.js    │
│ - Type-safe wrappers            │ │  - Fallback for missing modules │
│ - Import mcp-client             │ │  - 100% tool coverage           │
│ - IDE autocomplete              │ └──────┬──────────────────────────┘
└─────────────┬───────────────────┘        │
              │                            │
              └────────────┬───────────────┘
                           │ docker exec (JSON-RPC)
                           │
         ┌─────────────────▼───────────────────────┐
         │  Python MCP Servers (Docker)            │
         │  - 5 specialized containers             │
         │  - 34 total tools                       │
         │  - Actual bioinformatics operations     │
         └─────────────┬───────────────────────────┘
                       │ API calls
                       │
         ┌─────────────▼───────────────────────────┐
         │  External Databases                     │
         │  NCBI, BOLD, SILVA, UNITE, SRA          │
         └─────────────────────────────────────────┘
```

### Available Tools (34 Total - 100% Coverage)

All tools from the Python MCP servers are now available! Tools use underscore naming (`category_toolName`) to comply with Claude Desktop requirements:

**Database Tools (11)**:
- `database_getSequences`, `database_getTaxonomy`, `database_ggetRef`
- `database_ggetSearch`, `database_ggetInfo`, `database_ggetSeq`
- `database_getNeighbors`, `database_searchSraStudies`
- `database_getSraRuninfo`, `database_searchSraCloud`, `database_extractSequenceColumns`

**Processing Tools (5)**:
- `processing_fastaQc`, `processing_dereplicateSequences`, `processing_detectChimeras`
- `processing_maskLowComplexity`, `processing_processSequences`

**Alignment Tools (5)**:
- `alignment_alignSequences`, `alignment_buildPhylogeny`, `alignment_processAlignment`
- `alignment_calculateDistances`, `alignment_alignAndAnalyze`

**Design Tools (6)**:
- `design_findSignatureRegions`, `design_primer3Design`, `design_analyzeSpecificity`
- `design_rankRegions`, `design_oligoQc`, `design_designPrimersComplete`

**Validation Tools (7)**:
- `validation_ggetBlast`, `validation_inSilicoPcr`, `validation_ggetBlat`
- `validation_blastNt`, `validation_assessCoverage`
- `validation_searchPubmed`, `validation_validatePrimersComplete`

### Benefits vs Traditional MCP

| Metric | Traditional MCP | TypeScript Wrapper | Improvement |
|--------|----------------|-------------------|-------------|
| **Initial Load** | 150,000 tokens | ~400 tokens/tool | **99.7% reduction** |
| **Tool Discovery** | All upfront | On-demand | Progressive |
| **Data Processing** | Through AI model | In code | Direct |
| **Cost per Analysis** | $0.92 | $0.04 | **95.9% savings** |
| **Speed** | 37 seconds | 15 seconds | **2.5x faster** |

### Testing & Troubleshooting

**Quick Test:**
```bash
# Verify setup
./test-mcp-server.sh

# Manual test
timeout 3s node workspace/mcp-server.js
# Should output: "✅ mdk-mcp-typescript v2.0.0 running on stdio"
```

**Documentation:**
- **Quick Start**: `QUICK_START_CLAUDE_DESKTOP.md`
- **Complete Guide**: `CLAUDE_DESKTOP_TESTING_GUIDE.md`
- **Testing Summary**: `TESTING_SUMMARY.md`
- **Start Here**: `START_HERE.md`

**Common Issues:**
- **No tools showing**: Check Claude Desktop logs at `%APPDATA%\Claude\logs\`
- **Connection errors**: Ensure Docker containers are running
- **Tool name errors**: All tool names use underscores (`_`), not dots (`.`)

---

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

### Claude Desktop Integration (NEW)

- **[docs/claude-desktop/START_HERE.md](docs/claude-desktop/START_HERE.md)** - Quick overview for Claude Desktop setup
- **[docs/BUILD_SYSTEM.md](docs/BUILD_SYSTEM.md)** - Complete build system documentation (mcp-client + all server modules)
- **[scripts/verify-build.sh](scripts/verify-build.sh)** - Automated build verification script
- **[COMPLETE_TOOL_CATALOG.md](COMPLETE_TOOL_CATALOG.md)** - All 34 tools with examples and testing prompts

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

## 🛠️ Dependencies and Versions

### Python Stack (Production MCP Servers)
- Python 3.11+
- MCP SDK ≥0.9.0
- gget ≥0.28.0
- BioPython ≥1.81
- pysradb ≥1.4.0
- primer3-py ≥1.1.0
- numpy ≥1.24.0
- pandas ≥2.0.0

### Node.js Stack (NEW - Code Execution Infrastructure)
- Node.js 20+
- TypeScript 5.3+
- MCP SDK 1.0.0
- Vitest 1.0.4 (testing)
- tsx 4.7.0 (TypeScript execution)

See `requirements.txt` files in server directories for Python dependencies and `package.json` for Node.js dependencies.

## 📂 Project Structure

```
mdk_mcp/
├── README.md                           # This file
├── CLAUDE.md                           # Project overview for Claude Code
├── package.json                        # Node.js dependencies (NEW - MCP 2.0)
├── tsconfig.json                       # TypeScript configuration (NEW)
├── vitest.config.ts                    # Test configuration (NEW)
├── start_interactive.sh                # One-command launcher
├── docker-compose.autogen.yml          # Docker Compose configuration
│
├── autogen_app/                        # AG2 application
│   ├── main.py                         # Main assistant with interactive interface (was: qpcr_assistant.py)
│   ├── lib/
│   │   ├── mcp_bridge.py              # MCP client bridge for AG2 (was: autogen_mcp_bridge.py)
│   │   └── resources.py               # Text resources (was: text_resources.py)
│   ├── gemini_client.py                # Gemini model client wrapper
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile                      # Container definition
│   ├── .env                            # API keys (create this)
│   ├── .env.template                   # Template for .env file
│   └── OAI_CONFIG_LIST.json            # Model configuration (Gemini + GPT-4)
│
├── mcp_servers/                        # MCP servers
│   ├── shared/                         # Shared utilities (NEW - TypeScript)
│   │   └── tool-generator.ts           # Automated tool wrapper generator
│   ├── database_server/                # Phase 1: Database access (Python)
│   │   ├── database_mcp_server.py      # Server implementation
│   │   ├── config.py                   # Configuration
│   │   ├── requirements.txt            # Dependencies
│   │   ├── Dockerfile                  # Container definition
│   │   ├── mcp-server.json             # MCP manifest
│   │   └── tests/                      # Unit tests
│   ├── processing_server/              # Phase 2: Sequence processing (Python)
│   ├── alignment_server/               # Phase 3: Alignment (Python)
│   ├── design_server/                  # Phase 4: Primer design (Python)
│   ├── validation_server/              # Phase 5: Validation (Python)
│   └── [future TypeScript servers...]  # Phase 6+: Code execution servers
│
├── examples/                           # TypeScript demos (NEW - MCP 2.0)
│   ├── database-tools-usage.ts         # Database tools demo
│   ├── executor-demo.ts                # Code execution sandbox demo
│   ├── generate-all-database-tools.ts  # Tool generation examples
│   ├── mcp-client-demo.ts              # MCP client integration
│   ├── pii-tokenization-demo.ts        # PII tokenization examples
│   ├── skills-manager-demo.ts          # Skills management demo
│   └── token-benchmark.ts              # Token usage benchmarks
│
├── tests/                              # TypeScript tests (NEW - MCP 2.0)
│   ├── unit/                           # Unit tests (executor, PII, skills, tools)
│   └── integration/                    # Integration tests (all servers, MCP client)
│
├── docs/                               # Documentation
│   ├── INDEX.md                        # Documentation index and navigation
│   ├── USER_GUIDE.md                   # Comprehensive user reference
│   ├── AUTOGEN_INTEGRATION.md          # AG2 integration architecture
│   ├── MIGRATION_EXECUTIVE_SUMMARY.md  # MCP 2.0 migration overview (NEW)
│   ├── TOKEN_COMPARISON.md             # Token usage benchmarks (NEW)
│   ├── SECURITY.md                     # PII tokenization security guide (NEW)
│   ├── PHASE_1_COMPLETE.md             # Infrastructure completion report (NEW)
│   └── MIGRATION_*.md                  # Migration task tracking docs (NEW)
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

### MCP 2.0 Migration (NEW - High Priority)
- 🚧 **Phase 2**: Database Server TypeScript Migration
  - Convert 11 Python tools to TypeScript
  - Implement code execution patterns
  - Token reduction validation
- 🚧 **Phase 3**: Skills Integration
  - Reusable workflow system
  - Common qPCR design skills
  - Context-aware suggestions
- 🚧 **Phases 4-6**: Remaining Server Migrations
  - Processing Server (5 tools)
  - Alignment Server (5 tools)
  - Design & Validation Servers (13 tools)

See `docs/MIGRATION_EXECUTIVE_SUMMARY.md` for complete 14-week roadmap.

### Python Server Implementation (Production)
- ✅ ~~Alignment server~~ (COMPLETE - MAFFT/MUSCLE/Clustal Omega, phylogenetics)
- ✅ ~~Design server~~ (COMPLETE - signature regions, Primer3, oligo QC)
- ✅ ~~Validation server~~ (COMPLETE - BLAST, in-silico PCR, literature search)
- 🚧 **Phase 6**: Export server (report generation, provenance tracking)

### Infrastructure
- Sequence caching layer (Redis) - Consider for TypeScript servers
- Rate limiting across distributed instances
- Web UI (React/Vue frontend) - Can leverage TypeScript stack
- REST API for programmatic access
- Code execution sandbox hardening (Phase 1 complete, monitoring needed)

### Development & Testing

For developers and contributors:

**Python Stack Documentation:**
- 📘 **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Complete troubleshooting guide
- 🧪 **[MCP_TESTING_GUIDE.md](docs/MCP_TESTING_GUIDE.md)** - MCP server testing guide
- 📋 **[MCP_TESTING_QUICKREF.md](docs/MCP_TESTING_QUICKREF.md)** - Quick testing reference
- 📖 **[AUTOGEN_INTEGRATION.md](docs/AUTOGEN_INTEGRATION.md)** - AG2 architecture details
- 🗺️ **[road_map.md](road_map.md)** - Development roadmap

**TypeScript Stack Documentation (NEW):**
- 🚀 **[MIGRATION_EXECUTIVE_SUMMARY.md](docs/MIGRATION_EXECUTIVE_SUMMARY.md)** - MCP 2.0 migration overview
- 📊 **[TOKEN_COMPARISON.md](docs/TOKEN_COMPARISON.md)** - Token usage benchmarks
- 🔒 **[SECURITY.md](docs/SECURITY.md)** - PII tokenization security guide
- ✅ **[PHASE_1_COMPLETE.md](docs/PHASE_1_COMPLETE.md)** - Infrastructure completion report
- 📋 **[MIGRATION_ACTION_ITEMS.md](docs/MIGRATION_ACTION_ITEMS.md)** - Detailed task breakdown

**Quick Test Commands:**
```bash
# Python integration tests
python3 test_processing_integration.py
python3 test_function_calling.py

# TypeScript tests (NEW)
npm test                    # Run all TypeScript tests
npm run test:coverage       # Coverage report
npm run demo:client         # MCP client demo
npm run benchmark           # Token usage benchmarks

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

### Frameworks & Platforms
- **AG2** - Multi-agent framework (formerly Microsoft AutoGen)
- **Google Gemini** - Large language model with 1M context window
- **Model Context Protocol (MCP)** - Tool protocol by Anthropic (Python SDK 0.9.0, Node.js SDK 1.0.0)
- **Node.js** - JavaScript runtime for code execution architecture
- **TypeScript** - Type-safe JavaScript for infrastructure components
- **Vitest** - Modern testing framework

### Bioinformatics Tools
- **gget** - Genomic database access library
- **BioPython** - Bioinformatics utilities
- **seqkit** - Fast FASTA/Q file manipulation toolkit
- **vsearch** - Sequence clustering, dereplication, and chimera detection
- **NCBI/BOLD/SILVA/UNITE** - Sequence databases
- **Primer3** - PCR primer design tool
- **NCBI BLAST+** - Sequence alignment and validation

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
