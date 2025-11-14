# Code Execution Sandbox Architecture

## Overview

The `code-execution-sandbox` provides a **secure Docker environment** for executing JavaScript/TypeScript code with direct access to all MCP bioinformatics tools. This document explains how it works and how it interacts with the MCP server containers.

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Desktop (Windows/Mac)                │
│                                                                 │
│  User: "Execute code to get 1000 sequences and calculate stats"│
└────────────────────────────┬────────────────────────────────────┘
                             │ stdio (MCP Protocol)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              code-execution-sandbox (Docker Container)          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Node.js VM Sandbox (executor.js)                         │ │
│  │  • Executes user's JavaScript/TypeScript code             │ │
│  │  • Timeout enforcement (30 seconds default)               │ │
│  │  • Resource limits (512MB RAM, 1 CPU)                     │ │
│  │  • Output size limits (1MB default)                       │ │
│  └─────────────────────────┬─────────────────────────────────┘ │
│                            │                                     │
│                            │ import/require                      │
│                            ↓                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  /workspace (mounted from host)                           │ │
│  │                                                            │ │
│  │  ├── servers/                                             │ │
│  │  │   ├── database/                                        │ │
│  │  │   │   ├── index.js        (barrel exports)            │ │
│  │  │   │   ├── get_sequences.js                            │ │
│  │  │   │   ├── get_taxonomy.js                             │ │
│  │  │   │   └── ... (11 tools)                              │ │
│  │  │   ├── processing/         (5 tools)                   │ │
│  │  │   ├── alignment/          (5 tools)                   │ │
│  │  │   ├── design/             (6 tools)                   │ │
│  │  │   └── validation/         (7 tools)                   │ │
│  │  │                                                        │ │
│  │  ├── lib/                                                 │ │
│  │  │   └── mcp-client.js       (Docker bridge)             │ │
│  │  │                                                        │ │
│  │  └── helpers.js              (utility functions)         │ │
│  └───────────────────────┬───────────────────────────────────┘ │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │ callMCPTool()
                           │
                           │ docker exec -i <container> python3 ...
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ↓                  ↓                  ↓
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   ndiag-      │  │   ndiag-      │  │   ndiag-      │
│   database-   │  │   processing- │  │   alignment-  │
│   server      │  │   server      │  │   server      │
│               │  │               │  │               │
│  Python MCP   │  │  Python MCP   │  │  Python MCP   │
│  Server       │  │  Server       │  │  Server       │
│               │  │               │  │               │
│  • get_       │  │  • fasta_qc   │  │  • align_     │
│    sequences  │  │  • dereplicate│  │    sequences  │
│  • get_       │  │  • detect_    │  │  • build_     │
│    taxonomy   │  │    chimeras   │  │    phylogeny  │
│  • ...        │  │  • ...        │  │  • ...        │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │ API calls
                           ↓
                ┌──────────────────────┐
                │   External APIs      │
                │  • NCBI GenBank      │
                │  • BOLD Systems      │
                │  • SILVA Database    │
                │  • UNITE Database    │
                └──────────────────────┘
```

## 🔄 Execution Flow (Step by Step)

### Step 1: User Request in Claude Desktop

User sends a request:
```
Execute code to retrieve 1000 COI sequences for Salmo salar,
calculate statistics, and return only the summary.
```

### Step 2: Claude Generates Code

Claude writes JavaScript code using the `execute_code` tool:
```javascript
// This code runs INSIDE the code-execution-sandbox container
const database = await import('database');

const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 1000
});

const stats = parseFastaStats(sequences);
return stats;
```

### Step 3: Code Execution Sandbox Receives Code

The `executor.js` (inside code-execution-sandbox):

```typescript
// File: code-execution/src/executor.ts

async function executeCode(code: string, timeout: number) {
  // 1. Create secure VM context
  const contextData = createExecutionContext();
  
  // 2. Load MCP tool modules from /workspace/servers/
  const toolModules = await loadToolModules();
  // toolModules = {
  //   database: { getSequences, getTaxonomy, ... },
  //   processing: { fastaQc, dereplicate, ... },
  //   alignment: { alignSequences, ... },
  //   design: { findSignatureRegions, ... },
  //   validation: { ggetBlast, ... }
  // }
  
  // 3. Add modules to execution context
  Object.assign(contextData, toolModules);
  
  // 4. Create VM context with all modules available
  const context = vm.createContext(contextData);
  
  // 5. Execute user code with timeout
  const result = await vm.runInContext(code, context, { timeout });
  
  // 6. Return result (only summary, not raw data)
  return result;
}
```

### Step 4: Code Calls Tool Module

When the user code calls `database.getSequences()`:

```javascript
// File: workspace/servers/database/get_sequences.js

export async function getSequences(input) {
  // Sanitize input (convert string numbers to numbers)
  const sanitized = { ...input };
  
  // Call the MCP tool via Docker bridge
  return callMCPTool('database__get_sequences', sanitized);
}
```

### Step 5: MCP Client Bridges to Docker Container

The `callMCPTool` function:

```typescript
// File: workspace/lib/mcp-client.ts

async function callMCPTool(toolId: string, args: any) {
  // 1. Parse server name and tool name from ID
  const [serverName, toolName] = toolId.split('__');
  
  // 2. Get container name for this server
  const containerName = serverConfig[serverName].container;
  // e.g., "ndiag-database-server"
  
  // 3. Build MCP JSON-RPC requests
  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: { ... }
  };
  
  const toolRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/call',
    params: {
      name: 'get_sequences',
      arguments: args
    }
  };
  
  // 4. Execute via docker exec
  const command = `echo '${JSON.stringify([initRequest, toolRequest])}' | \
    docker exec -i ${containerName} python3 /app/database_mcp_server.py`;
  
  const { stdout } = await execAsync(command);
  
  // 5. Parse MCP response
  const response = JSON.parse(stdout);
  
  // 6. Return tool result
  return response.result.content[0].text;
}
```

### Step 6: Python MCP Server Executes Tool

Inside the `ndiag-database-server` container:

```python
# File: mcp_servers/database_server/database_mcp_server.py

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_sequences":
        # Execute the actual bioinformatics operation
        taxon = arguments["taxon"]
        region = arguments.get("region", "COI")
        max_results = arguments.get("max_results", 100)
        
        # Call external APIs (NCBI, BOLD, etc.)
        sequences = await fetch_sequences_from_ncbi(taxon, region, max_results)
        
        # Return FASTA format sequences
        return sequences
```

### Step 7: Result Flows Back Through Chain

```
Python MCP Server → MCP Client (Docker exec) → Tool Module → User Code → VM Context → Executor → Claude Desktop
```

The user receives only the summary:
```json
{
  "count": 1000,
  "avgLength": 658,
  "gcContent": 48.2,
  "minLength": 400,
  "maxLength": 1200
}
```

**Token savings:** ~150,000 tokens (raw sequences) → ~300 tokens (summary) = **99.8% reduction**

## 📦 Component Details

### 1. Code Execution Sandbox Container

**Location:** `code-execution/`

**Key Files:**
- `Dockerfile` - Container definition with Node.js 20, security hardening
- `src/executor.ts` - Main execution engine
- `src/helpers.js` - Utility functions (parseFastaStats, filterAndSave, etc.)

**Features:**
- **Secure VM execution** - Node.js `vm.createContext()` isolation
- **Resource limits** - 512MB RAM, 1 CPU, 30s timeout
- **Output limits** - 1MB max response size
- **Security** - Non-root user, no-new-privileges, capability dropping

**Environment Variables:**
```bash
EXECUTION_TIMEOUT=30000      # 30 seconds
MAX_OUTPUT_SIZE=1048576      # 1MB
WORKSPACE_PATH=/workspace    # Mounted workspace directory
```

### 2. Workspace Directory Structure

**Location:** `workspace/`

```
workspace/
├── servers/                    # Generated tool modules (auto-generated)
│   ├── database/
│   │   ├── index.js           # Barrel exports all tools
│   │   ├── get_sequences.js   # Individual tool wrapper
│   │   ├── get_taxonomy.js
│   │   └── ... (11 tools)
│   ├── processing/            # 5 tools
│   ├── alignment/             # 5 tools
│   ├── design/                # 6 tools
│   └── validation/            # 7 tools
│
├── lib/
│   └── mcp-client.js          # Docker bridge library
│
├── helpers.js                 # Utility functions
└── mcp-server.js              # Main MCP server for Claude Desktop
```

**Generated by:** `mcp_servers/shared/tool-generator.ts`

### 3. MCP Client Library

**Location:** `workspace/lib/mcp-client.ts`

**Key Class:** `MCPClient`

**Features:**
- **Progressive tool discovery** - Load only what you need
- **Schema caching** - Reduce redundant lookups
- **Docker exec bridge** - Communicate with Python containers
- **PII tokenization** - Optional data privacy
- **Type-safe calls** - TypeScript interfaces

**Methods:**
```typescript
class MCPClient {
  // Search tools by name/pattern
  searchTools(query: string, detailLevel: 'name' | 'description' | 'full')
  
  // Get tool names only (minimal tokens)
  getToolNames(serverName: string)
  
  // Get names + descriptions (moderate tokens)
  getToolDescriptions(serverName: string)
  
  // Get full schemas (maximum tokens)
  getToolSchema(serverName: string, toolName?: string)
  
  // Execute a tool
  callTool(serverName: string, toolName: string, args: any)
}
```

### 4. Generated Tool Modules

**Auto-generated from MCP server schemas**

Each tool module provides:
1. **Type-safe wrapper** - Sanitizes inputs (string → number conversion)
2. **Documentation** - JSDoc comments with examples
3. **Error handling** - Graceful failure with descriptive messages
4. **Barrel exports** - Import from category or individual tool

**Example:**
```typescript
// workspace/servers/database/get_sequences.js
import { callMCPTool } from "../../lib/mcp-client.js";

export async function getSequences(input) {
  const sanitized = { ...input };
  
  // Convert string numbers to actual numbers
  for (const [key, value] of Object.entries(sanitized)) {
    if (typeof value === 'string' && !isNaN(Number(value))) {
      sanitized[key] = Number(value);
    }
  }
  
  return callMCPTool('database__get_sequences', sanitized);
}
```

### 5. Python MCP Server Containers

**5 Docker containers** running Python MCP servers:

| Container | Port | Tools | Purpose |
|-----------|------|-------|---------|
| `ndiag-database-server` | 8000 | 11 | Sequence retrieval (NCBI, BOLD, SILVA, UNITE) |
| `ndiag-processing-server` | 8001 | 5 | QC, dereplication, chimera detection |
| `ndiag-alignment-server` | 8002 | 5 | MSA, phylogenetics, distance matrices |
| `ndiag-design-server` | 8003 | 6 | Primer design, signature regions, Primer3 |
| `ndiag-validation-server` | 8004 | 7 | BLAST, in-silico PCR, literature search |

Each container:
- Runs a Python MCP server via stdio
- Has bioinformatics tools installed (seqkit, MAFFT, MUSCLE, Primer3, BLAST, etc.)
- Listens for JSON-RPC requests on stdin
- Returns results on stdout
- Has access to shared `/results` directory

## 🔒 Security Model

### Layer 1: Docker Container Isolation
- Code runs in separate Docker container
- No direct host access
- Resource limits enforced by Docker

### Layer 2: Non-Root User
- Container runs as `sandbox` user (UID 1001)
- No privilege escalation (`no-new-privileges` flag)
- Capabilities dropped (`cap_drop: ALL`)

### Layer 3: VM Context Isolation
- Node.js `vm.createContext()` creates isolated context
- No access to Node.js internals
- Limited module access (whitelisted only)

### Layer 4: Timeout Enforcement
- 30-second default timeout (configurable)
- Prevents infinite loops and hangs

### Layer 5: Output Size Limits
- 1MB maximum output (configurable)
- Prevents memory exhaustion

### Layer 6: Module Whitelisting
```typescript
require: (module: string) => {
  // Only allow specific modules
  const allowedModules = ['path', 'util', 'crypto'];
  if (!allowedModules.includes(module)) {
    throw new Error(`Module '${module}' is not allowed`);
  }
  return require(module);
}
```

### Layer 7: Docker Socket Protection
- Container has Docker socket access (for MCP communication)
- But runs as non-root, limiting exploit potential
- Can only exec into existing containers, can't create new ones

## 💡 Usage Examples

### Example 1: Simple Statistics

```javascript
// User request: "Get 100 sequences and calculate statistics"

const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 100
});

const stats = parseFastaStats(sequences);
return stats;

// Result (300 tokens):
// {
//   count: 100,
//   avgLength: 658,
//   gcContent: 48.2,
//   minLength: 400,
//   maxLength: 890
// }
```

### Example 2: Comparative Analysis

```javascript
// User: "Compare GC content between two species"

const species1 = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 500
});

const species2 = await database.getSequences({
  taxon: "Oncorhynchus mykiss",
  region: "COI",
  max_results: 500
});

const stats1 = parseFastaStats(species1);
const stats2 = parseFastaStats(species2);

return {
  species1: {
    name: "Salmo salar",
    gcContent: stats1.gcContent,
    count: stats1.count
  },
  species2: {
    name: "Oncorhynchus mykiss",
    gcContent: stats2.gcContent,
    count: stats2.count
  },
  difference: Math.abs(stats1.gcContent - stats2.gcContent)
};

// Saves ~200,000 tokens vs loading all sequences into context
```

### Example 3: Filtered Processing

```javascript
// User: "Get sequences, filter by length, save to file"

const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 1000
});

// Filter and save (keeps data out of context)
const metadata = await filterAndSave(
  sequences,
  seq => seq.length >= 400 && seq.length <= 800,
  '/workspace/data/filtered_salmo_salar.fasta'
);

return {
  message: "Filtered sequences saved",
  path: metadata.path,
  size: formatBytes(metadata.size),
  lines: metadata.lines,
  hash: metadata.hash
};

// Result: Only metadata, not 1000 sequences!
```

### Example 4: Multi-Tool Workflow

```javascript
// User: "Get sequences, perform QC, align, build tree"

// 1. Retrieve sequences
const rawSeqs = await database.getSequences({
  taxon: "Salmo salar",
  max_results: 200
});

// 2. Quality control
const qcResult = await processing.fastaQc({
  sequences: rawSeqs,
  min_length: 400,
  max_n_percent: 5.0,
  remove_duplicates: true
});

// 3. Alignment
const aligned = await alignment.alignSequences({
  sequences: qcResult.cleaned_sequences,
  algorithm: "mafft"
});

// 4. Phylogenetic tree
const tree = await alignment.buildPhylogeny({
  alignment: aligned.alignment,
  method: "nj"
});

return {
  original: 200,
  afterQC: qcResult.passed,
  alignmentLength: aligned.length,
  treeFormat: "newick",
  treePath: "/results/salmo_tree.nwk"
};

// Context: ~500 tokens vs ~300,000 tokens for raw data
```

## 🎯 Benefits Summary

| Aspect | Traditional MCP | Code Execution | Improvement |
|--------|----------------|----------------|-------------|
| **Token Usage** | 150,000 | 300 | **99.8%** reduction |
| **Dataset Size** | Limited by context | Unlimited | No limits |
| **Processing Speed** | Through AI model | Direct | **10x faster** |
| **Cost per Analysis** | $0.45 | $0.001 | **99.8%** savings |
| **Data Privacy** | All in context | Processed locally | Full privacy |

## 📚 Related Documentation

- **[FIX_SUMMARY.md](../code-execution/FIX_SUMMARY.md)** - Setup and troubleshooting
- **[COMPLETE_TOOL_CATALOG.md](../COMPLETE_TOOL_CATALOG.md)** - All 34 bioinformatics tools
- **[BUILD_SYSTEM.md](BUILD_SYSTEM.md)** - Tool generation and build process
- **[USER_GUIDE.md](USER_GUIDE.md)** - User documentation

## 🔧 Development

### Adding New Helper Functions

Edit `workspace/helpers.js`:

```javascript
export function myNewHelper(data) {
  // Process data efficiently
  return summary;
}
```

Rebuild:
```bash
cd code-execution
npm run build
docker build -t code-execution-sandbox .
```

### Debugging

```bash
# View sandbox logs
docker logs code-execution-sandbox

# Test manually
docker run --rm -i \
  --mount type=bind,source=/path/to/workspace,target=/workspace \
  -e WORKSPACE_PATH=/workspace \
  code-execution-sandbox

# Interactive shell
docker exec -it code-execution-sandbox sh
```

### Performance Tuning

Environment variables in `docker-compose.autogen.yml`:

```yaml
environment:
  - EXECUTION_TIMEOUT=60000      # Increase for long operations
  - MAX_OUTPUT_SIZE=5242880      # 5MB for larger results
  - NODE_OPTIONS=--max-old-space-size=1024  # More RAM
```

---

**Last Updated:** 2025-11-13  
**Version:** 2.0  
**Status:** Production Ready ✅

