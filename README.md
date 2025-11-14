# mdk_mcp - Bioinformatics Tools for qPCR Assay Design

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![MCP](https://img.shields.io/badge/MCP-2.0-purple.svg)](https://modelcontextprotocol.io)

**AI-powered bioinformatics platform** for designing species-specific qPCR primers using the Model Context Protocol (MCP). Access 34 specialized tools for sequence retrieval, alignment, and primer design through natural language.

## 🎯 What Can You Do?

- **Retrieve sequences** from NCBI, BOLD, SILVA, UNITE databases
- **Analyze and align** sequences with quality control
- **Design primers** with automatic signature region detection
- **Validate primers** with BLAST and in-silico PCR
- Use via **Claude Desktop** (lightweight) or **Interactive Terminal** (full automation)

## 🚀 Quick Start

Choose your preferred method:

### Option 1: Claude Desktop Integration (Recommended)

**Best for:** Individual use, quick access to tools, Windows/Mac users

[Jump to detailed guide →](#-option-1-claude-desktop-detailed-guide)

### Option 2: Interactive Terminal with AI Agents

**Best for:** Automated workflows, batch processing, research projects

[Jump to detailed guide →](#-option-2-interactive-terminal-detailed-guide)

---

## 📋 Option 1: Claude Desktop (Detailed Guide)

Use all 34 bioinformatics tools directly from Claude Desktop.

### Prerequisites

- **Docker Desktop** installed and running
- **Claude Desktop** (Windows or Mac)
- **WSL2** (Windows only) - [Install guide](https://learn.microsoft.com/en-us/windows/wsl/install)
- **Node.js 20+** - [Download](https://nodejs.org/)

### Step-by-Step Setup (Fresh Installation)

#### 1. Clone Repository

```bash
# Open terminal (WSL on Windows, Terminal on Mac/Linux)
git clone https://github.com/acefgin/mdk_mcp.git
cd mdk_mcp
```

#### 2. Build TypeScript Components

```bash
# Install dependencies
npm install

# Build everything (takes 1-2 minutes)
npm run build

# Expected output:
# ✅ Successfully generated 34 tools across 5 servers!
# ✓ Build complete
```

**What gets built:**
- MCP client library (Docker communication bridge)
- 34 TypeScript tool wrappers (type-safe interfaces)
- Main MCP server for Claude Desktop
- Helper utilities and modules

#### 3. Build Code Execution Sandbox Container

**Important:** The code-execution-sandbox packages workspace scripts directly into the image, so it must be built AFTER the TypeScript workspace is compiled.

```bash
# Build the container image (packages workspace scripts inside)
docker build -f code-execution/Dockerfile -t code-execution-sandbox .

# Expected output:
# Successfully built code-execution-sandbox
# Container includes: /workspace/servers, /workspace/lib, /workspace/types
```

#### 4. Start MCP Server Containers

**⚠️ CRITICAL:** The code-execution-sandbox needs these MCP server containers to execute tool calls (database, processing, alignment, design, validation). They MUST be running!

```bash
# Start all MCP server containers
npm run docker:up

# Wait 10-15 seconds for initialization
```

**Why are these containers needed?**
- The code-execution-sandbox communicates with MCP servers via Docker
- Each tool call (database.getSequences, processing.fastaQc, etc.) runs in its respective container
- Without these containers, code execution will fail with "Cannot connect to Docker daemon"

**Verify code-execution-sandbox is ready:**
```bash
# Test the container
docker run --rm -i --name test-code-exec \
  -e EXECUTION_TIMEOUT=30000 \
  -e MAX_OUTPUT_SIZE=1048576 \
  -e WORKSPACE_PATH=/workspace \
  code-execution-sandbox

# Expected output (press Ctrl+C after seeing):
# Starting Code Execution Sandbox...
# Loaded MCP servers: alignment, database, design, processing, validation
# Code Execution Sandbox ready
```

**If you started all containers, verify they're running:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"

# Should show (if using docker:up):
# code-execution-sandbox    Up (healthy)
# ndiag-validation-server   Up (healthy)  
# ndiag-design-server       Up
# ndiag-alignment-server    Up
# ndiag-processing-server   Up
# ndiag-database-server     Up
# qpcr-assistant            Up
```

#### 5. Configure Claude Desktop

**Windows (WSL2):**

1. Press `Win + R`, type `%APPDATA%\Claude`, press Enter
2. Open or create `claude_desktop_config.json`
3. Add this configuration (replace `YOUR_USERNAME` with your WSL username):

```json
{
  "mcpServers": {
    "mdk-ts-mcp": {
      "command": "wsl",
      "args": [
        "-e",
        "bash",
        "-c",
        "cd /home/YOUR_USERNAME/mdk_mcp && node workspace/mcp-server.js"
      ],
      "env": {
        "DEBUG": "false"
      }
    },
    "code-execution-sandbox": {
      "command": "wsl",
      "args": [
        "-e",
        "bash",
        "-c",
        "docker run --rm -i --name code-execution-sandbox --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock -e EXECUTION_TIMEOUT=30000 -e MAX_OUTPUT_SIZE=1048576 -e WORKSPACE_PATH=/workspace code-execution-sandbox"
      ]
    }
  }
}
```

**⚠️ Important Notes:**
- **No workspace mount needed** - Scripts are now packaged in the container image
- **Docker socket mount required** - Enables communication with MCP server containers
- Container is self-contained and portable

**macOS/Linux:**

1. Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `~/.config/Claude/claude_desktop_config.json` (Linux)
2. Add this configuration (replace with your actual path):

```json
{
  "mcpServers": {
    "mdk-ts-mcp": {
      "command": "node",
      "args": [
        "/absolute/path/to/mdk_mcp/workspace/mcp-server.js"
      ],
      "env": {
        "DEBUG": "false"
      }
    },
    "code-execution-sandbox": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--name", "code-execution-sandbox",
        "--mount", "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock",
        "-e", "EXECUTION_TIMEOUT=30000",
        "-e", "MAX_OUTPUT_SIZE=1048576",
        "-e", "WORKSPACE_PATH=/workspace",
        "code-execution-sandbox"
      ]
    }
  }
}
```

**⚠️ Important Notes:**
- **No workspace mount needed** - Scripts are now packaged in the container image
- **Docker socket mount required** - Enables communication with MCP server containers
- Container is self-contained and portable

#### 6. Restart Claude Desktop

- Quit Claude Desktop completely
- Start Claude Desktop again
- Look for the 🔌 icon in the bottom-right corner

#### 7. Test the Connection

In Claude Desktop, try:

```
What MCP tools do you have available?
```

You should see **35 tools** listed across 6 categories:
- **database** (11 tools) - Sequence retrieval
- **processing** (5 tools) - Quality control  
- **alignment** (5 tools) - Sequence alignment
- **design** (6 tools) - Primer design
- **validation** (7 tools) - Primer validation
- **execute_code** (1 tool) - Code execution sandbox

### What is the Code Execution Sandbox?

The `code-execution-sandbox` provides a **secure Docker environment** for executing JavaScript/TypeScript code with access to all MCP tool modules. This enables:

**🎯 Context-Efficient Data Processing:**
```
Traditional: Load 100 sequences into context → 50,000 tokens
Code Execution: Process in code, return summary → 200 tokens
Result: 99.6% token reduction
```

**Key Benefits:**
- ✅ **99%+ token reduction** - Process data in code, not through the AI
- ✅ **Unlimited dataset size** - No context window limits
- ✅ **Secure isolation** - Docker-based sandbox with resource limits
- ✅ **Helper functions** - Pre-built utilities for FASTA processing, statistics, etc.
- ✅ **Direct tool access** - Import and use all MCP tools directly

**Example Usage:**
```javascript
// Instead of loading all sequences into context:
// "Get 1000 COI sequences and show me all of them" → 150,000 tokens ❌

// Process in the execution sandbox:
"Execute code to retrieve 1000 COI sequences for Salmo salar,
calculate statistics (count, avg length, GC content),
and return only the summary."

// Claude will use execute_code tool:
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI", 
  max_results: 1000
});

const stats = parseFastaStats(sequences);
return stats; 
// Returns: { count: 1000, avgLength: 658, gcContent: 48.2% }
// Context usage: ~300 tokens ✅
```

**When to use Code Execution:**
- Processing large sequence datasets (>100 sequences)
- Calculating statistics without loading raw data
- Filtering/transforming data before analysis
- Batch processing multiple tool calls
- Complex data manipulation workflows

### Example Usage in Claude Desktop

**Basic tool usage:**
```
Get 50 COI sequences for Salmo salar from NCBI,
filter for sequences longer than 400bp,
and show me basic statistics.
```

Claude will automatically:
1. Call `database_getSequences` to retrieve sequences
2. Call `processing_fastaQc` for quality control
3. Return statistics and save results

**Code execution (for large datasets):**
```
Execute code to retrieve 500 COI sequences for both 
Salmo salar and Oncorhynchus mykiss, calculate sequence 
statistics for each species, and compare GC content.
```

Claude will:
1. Use `execute_code` tool to run code in the sandbox
2. Process all data within the sandbox
3. Return only the comparison results (not raw sequences)
4. Save ~100,000 tokens vs traditional approach

### Troubleshooting

**No tools showing up:**
```bash
# Check if containers are running
docker ps | grep ndiag

# Check if build was successful
ls -l workspace/mcp-server.js

# Test MCP server manually
node workspace/mcp-server.js
# Should output: ✅ mdk-mcp-typescript v2.0.0 running on stdio
```

**Connection errors:**
```bash
# View Claude Desktop logs (Windows)
# Open: %APPDATA%\Claude\logs\mcp*.log

# Restart Docker containers
npm run docker:down
npm run docker:up
```

**Tool execution errors:**
```bash
# Check container logs
docker logs ndiag-database-server
docker logs ndiag-processing-server

# Check code execution sandbox
docker logs code-execution-sandbox

# Rebuild code execution sandbox if needed
cd code-execution
npm run build
docker build -t code-execution-sandbox .
```

**Code execution not working:**
```bash
# Verify code-execution-sandbox image exists
docker images | grep code-execution-sandbox

# If missing or outdated, rebuild (from project root):
# 1. First ensure workspace is built
npm run build:workspace

# 2. Then rebuild container with packaged scripts
docker build -f code-execution/Dockerfile -t code-execution-sandbox .

# Test manually (no mount needed - scripts are inside)
docker run --rm -i --name test-exec \
  -e WORKSPACE_PATH=/workspace \
  code-execution-sandbox
# Expected: "Loaded MCP servers: alignment, database, design, processing, validation"
# Press Ctrl+C after seeing "Code Execution Sandbox ready"
```

**After updating workspace scripts:**
```bash
# When you modify workspace TypeScript files, rebuild:
cd /home/cxl/MDK_Design/mdk_mcp

# 1. Rebuild TypeScript
npm run build:workspace

# 2. Rebuild container image (packages new scripts)
docker build -f code-execution/Dockerfile -t code-execution-sandbox .

# 3. Restart Claude Desktop to use new image
```

---

## 📋 Option 2: Interactive Terminal (Detailed Guide)

Use AI agents that automatically orchestrate complex qPCR design workflows.

### Prerequisites

- **Docker Desktop** installed and running
- **LLM API Key**: Get one of these:
  - **Google Gemini API** (recommended - free tier) - [Get key](https://makersuite.google.com/app/apikey)
  - **OpenAI API** (GPT-4) - [Get key](https://platform.openai.com/api-keys)

### Step-by-Step Setup (Fresh Installation)

#### 1. Clone Repository

```bash
git clone https://github.com/acefgin/mdk_mcp.git
cd mdk_mcp
```

#### 2. Configure API Keys

Create the configuration file:

```bash
# For Google Gemini (Recommended - Free tier, 1M context window)
echo "GOOGLE_API_KEY=your-actual-api-key-here" > autogen_app/.env

# Or for OpenAI GPT-4
echo "OPENAI_API_KEY=sk-your-actual-key-here" > autogen_app/.env

# Or use both (system tries Gemini first)
echo "GOOGLE_API_KEY=your-gemini-key" > autogen_app/.env
echo "OPENAI_API_KEY=your-openai-key" >> autogen_app/.env

# Optional: NCBI API key (higher rate limits for sequence retrieval)
echo "NCBI_API_KEY=your-ncbi-key" >> autogen_app/.env
```

**⚠️ Important:** Replace `your-actual-api-key-here` with your real API key!

#### 3. Start the System

```bash
# Make the script executable (first time only)
chmod +x start_interactive.sh

# Start everything with one command
./start_interactive.sh
```

**What happens:**
1. Creates `/results` directory for output files
2. Builds Docker images (takes 5-10 minutes first time)
3. Starts 7 containers (MCP servers + qPCR assistant)
4. Waits for services to initialize
5. Opens interactive chat interface

**Expected output:**
```
╔══════════════════════════════════════════════════════════════════════════╗
║               qPCR ASSISTANT - Interactive Mode Launcher                 ║
╚══════════════════════════════════════════════════════════════════════════╝

🔧 Setting up environment...
   ✓ Environment configured

🔍 Checking environment configuration...
   ✓ Environment configuration found

🚀 Starting qPCR Assistant system...
   • Building containers (may take a few minutes on first run)...
   ✓ Containers building and starting...
   ✓ All containers started successfully

🎉 qPCR Assistant is ready!

┌─[qPCR Assistant]
└─> _
```

#### 4. Try Your First Request

Type naturally - the AI agents will understand:

**Simple example:**
```
┌─[qPCR Assistant]
└─> Get 100 COI sequences for Salmo salar and show me basic statistics
```

**Complex example:**
```
┌─[qPCR Assistant]
└─> Design a qPCR assay to identify Atlantic salmon (Salmo salar)
    and distinguish it from rainbow trout (Oncorhynchus mykiss).
    Target the COI region for aquaculture verification.
```

**Watch the agents work:**
```
🚀 STARTING WORKFLOW

[Coordinator] Planning workflow...
  Phase 1: Retrieve sequences
  Phase 2: Quality control  
  Phase 3: Alignment analysis
  Phase 4: Primer design

[DatabaseAgent] Retrieving sequences...
  ✓ Retrieved 100 sequences for Salmo salar
  ✓ Retrieved 100 sequences for Oncorhynchus mykiss

[AnalystAgent] Analyzing sequences...
  ✓ Quality control: 87 sequences passed
  ✓ Alignment complete
  ✓ Found 3 signature regions

[PrimerDesignAgent] Designing primers...
  ✓ Designed 5 primer pairs
  ✓ Validation complete

✓ WORKFLOW COMPLETED in 45 seconds
Results saved to /results/task_20251113_150530.json
```

#### 5. Built-in Commands

```
┌─[qPCR Assistant]
└─> help     # Show example requests and usage guide
└─> logs     # View task history  
└─> clear    # Clear screen
└─> exit     # Exit (or press Ctrl+D)
```

#### 6. View Results

Results are saved in the `./results` directory:

```bash
# List all results
ls -lh ./results/

# View task summary
cat ./results/task_*_summary.txt

# View detailed JSON log
cat ./results/task_*.json | jq

# Copy sequences to your machine
cp ./results/sequences/*.fasta ~/my-analysis/
```

### Managing the System

**Reconnect to running session:**
```bash
./start_interactive.sh
# Choose option 1: Attach to existing session
```

**Stop all containers:**
```bash
docker compose -f docker-compose.autogen.yml down
```

**View logs:**
```bash
# View specific container
docker logs qpcr-assistant
docker logs ndiag-database-server

# Follow logs in real-time
docker logs -f qpcr-assistant

# View all logs
docker compose -f docker-compose.autogen.yml logs
```

**Restart with fresh build:**
```bash
./start_interactive.sh
# Choose option 2: Restart with fresh build
```

### Troubleshooting

**"API key not found" error:**
```bash
# Verify .env file exists and has correct format
cat autogen_app/.env

# Should show:
# GOOGLE_API_KEY=your-key-here
# or
# OPENAI_API_KEY=sk-your-key-here

# Re-create if needed
echo "GOOGLE_API_KEY=your-actual-key" > autogen_app/.env
```

**Container failed to start:**
```bash
# Check container status
docker ps -a | grep ndiag

# View error logs
docker logs ndiag-database-server
docker logs qpcr-assistant

# Restart everything
docker compose -f docker-compose.autogen.yml down
./start_interactive.sh
```

**Agents not responding:**
```bash
# Check API key is valid
# For Gemini: https://makersuite.google.com/app/apikey
# For OpenAI: https://platform.openai.com/api-keys

# Check rate limits
# Gemini free tier: 60 requests/minute
# OpenAI: Depends on your plan

# View agent logs
docker logs qpcr-assistant | grep -i error
```

---

## 📚 Available Tools (35 Total)

### Tool Categories

All tools use underscore naming (`category_toolName`):

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

**Code Execution (1)**:
- `execute_code` - Run JavaScript/TypeScript code in secure Docker sandbox with access to all MCP tools

### Detailed Tool Documentation

For complete tool descriptions, parameters, and examples, see:
- **[COMPLETE_TOOL_CATALOG.md](COMPLETE_TOOL_CATALOG.md)** - All 34 bioinformatics tools with testing prompts
- **[docs/architecture/CODE_EXECUTION_ARCHITECTURE.md](docs/architecture/CODE_EXECUTION_ARCHITECTURE.md)** - Complete code execution architecture explanation
- **[code-execution/FIX_SUMMARY.md](code-execution/FIX_SUMMARY.md)** - Code execution sandbox setup
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - Comprehensive user guide

---

## ✨ What Makes This Special?

### 🧠 Token-Efficient Architecture

Traditional MCP loads all tools upfront (150,000 tokens). This platform uses **progressive tool discovery** - loading only what you need (400 tokens per tool).

**Result:** 99.1% token reduction, 2.5x faster, 95.9% cost savings

From retrieval → QC → alignment → primer design → validation in one workflow.

### 🤖 AI Agent Orchestration (Interactive Mode)

Four specialized agents collaborate automatically:
- **Coordinator** - Plans workflows
- **DatabaseAgent** - Retrieves sequences  
- **AnalystAgent** - QC, alignment, phylogenetics
- **PrimerDesignAgent** - Primer design & validation

### 🐳 Containerized Deployment

All services run in Docker containers with automatic permission management and health checks.

---

## 📖 Documentation & Support

### 📚 User Guides
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - Complete user manual
- **[COMPLETE_TOOL_CATALOG.md](COMPLETE_TOOL_CATALOG.md)** - All 34 tools with examples
- **[docs/INTERACTIVE_MODE.md](docs/INTERACTIVE_MODE.md)** - Interactive terminal guide
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - 5-minute quick start

### 🔧 Technical Documentation
- **[CLAUDE.md](CLAUDE.md)** - Project overview and development guide
- **[docs/AUTOGEN_INTEGRATION.md](docs/AUTOGEN_INTEGRATION.md)** - AG2 integration details
- **[docs/BUILD_SYSTEM.md](docs/BUILD_SYSTEM.md)** - Build system documentation
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[road_map.md](road_map.md)** - Development roadmap

### 💬 Get Help
- 📘 Check **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** for common issues
- 🔍 Search [GitHub Issues](https://github.com/acefgin/mdk_mcp/issues)
- 🐛 [Open a new issue](https://github.com/acefgin/mdk_mcp/issues/new) with error logs

---

## 🤝 Contributing

Contributions welcome! See `docs/MIGRATION_EXECUTIVE_SUMMARY.md` for the MCP 2.0 roadmap.

**High Priority Areas:**
- TypeScript server migrations (processing, alignment, design)
- Skills integration for reusable workflows
- Web UI development
- Documentation improvements

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

### Frameworks
- **AG2** - Multi-agent framework
- **MCP** - Model Context Protocol by Anthropic
- **Google Gemini** - LLM with 1M context window  
- **Node.js/TypeScript** - Runtime and type system

### Bioinformatics Tools
- **gget** - Genomic database access
- **BioPython** - Bioinformatics utilities
- **seqkit, vsearch** - Sequence processing
- **MAFFT, MUSCLE** - Multiple sequence alignment
- **Primer3** - PCR primer design
- **NCBI BLAST+** - Sequence validation
- **NCBI/BOLD/SILVA/UNITE** - Sequence databases

---

**Ready to design qPCR assays?**

```bash
# Claude Desktop: Follow setup guide above
# Interactive Terminal:
./start_interactive.sh
```

🧬 Welcome to AI-powered molecular diagnostics!
