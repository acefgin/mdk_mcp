# Build System Documentation

## Overview

The `npm run build:workspace` command orchestrates the complete build process for the MDK MCP TypeScript wrapper, generating all necessary JavaScript modules from TypeScript sources.

## Build Architecture

```
npm run build:workspace
├── build:lib          → Compiles MCP client library
├── build:servers      → Generates & compiles all server modules  
└── build:mcp-server   → Compiles main MCP server
```

## Build Steps

### 1. Build MCP Client Library (`build:lib`)

**Command:**
```bash
tsc workspace/lib/mcp-client.ts --outDir workspace/lib --module ES2022 --target ES2022 --moduleResolution node --esModuleInterop --skipLibCheck --declaration
```

**Inputs:**
- `workspace/lib/mcp-client.ts` (162 lines)

**Outputs:**
- `workspace/lib/mcp-client.js` - Compiled JavaScript
- `workspace/lib/mcp-client.d.ts` - Type declarations

**Purpose:**
The MCP client library provides the `callMCPTool()` function that bridges TypeScript modules to Python MCP servers via Docker exec. All generated tool modules depend on this library.

---

### 2. Build Server Modules (`build:servers`)

**Command:**
```bash
npm run generate-tools:all && cd workspace && tsc servers/**/*.ts --module ES2022 --target ES2022 --moduleResolution node --esModuleInterop --skipLibCheck && cd ..
```

**Process:**
1. **Generate TypeScript Tool Wrappers** (`generate-tools:all`)
   - Runs `tsx examples/generate-all-tools.ts`
   - Reads tool definitions from Python MCP server files
   - Creates TypeScript wrappers for each tool
   - Generates barrel exports (`index.ts`)
   - Creates README.md for each server

2. **Compile TypeScript to JavaScript**
   - Compiles all `*.ts` files in `workspace/servers/`
   - Preserves directory structure
   - Generates ES2022 modules

**Inputs:**
- `mcp_servers/database_mcp_server.py` (11 tools)
- `mcp_servers/processing_mcp_server.py` (5 tools)
- `mcp_servers/alignment_mcp_server.py` (5 tools)
- `mcp_servers/design_mcp_server.py` (6 tools)
- `mcp_servers/validation_mcp_server.py` (7 tools)

**Generated TypeScript Files:**
```
workspace/servers/
├── database/
│   ├── get_sequences.ts
│   ├── gget_ref.ts
│   ├── get_taxonomy.ts
│   ├── ... (8 more tools)
│   ├── index.ts (barrel export)
│   └── README.md
├── processing/
│   ├── fasta_qc.ts
│   ├── dereplicate_sequences.ts
│   ├── detect_chimeras.ts
│   ├── mask_low_complexity.ts
│   ├── process_sequences.ts
│   ├── index.ts
│   └── README.md
├── alignment/
│   ├── align_sequences.ts
│   ├── build_phylogeny.ts
│   ├── ... (3 more tools)
│   ├── index.ts
│   └── README.md
├── design/
│   ├── find_signature_regions.ts
│   ├── primer3_design.ts
│   ├── ... (4 more tools)
│   ├── index.ts
│   └── README.md
└── validation/
    ├── gget_blast.ts
    ├── in_silico_pcr.ts
    ├── ... (5 more tools)
    ├── index.ts
    └── README.md
```

**Compiled JavaScript Files:**
- 34 tool modules (*.js)
- 5 index.js barrel exports
- All preserve import paths to `../../lib/mcp-client.js`

---

### 3. Build MCP Server (`build:mcp-server`)

**Command:**
```bash
tsc workspace/mcp-server.ts --outDir workspace --module ES2022 --target ES2022 --moduleResolution node --esModuleInterop --skipLibCheck
```

**Inputs:**
- `workspace/mcp-server.ts` (921 lines)

**Outputs:**
- `workspace/mcp-server.js` (855 lines)

**Purpose:**
The main MCP server that:
- Implements MCP protocol (stdio transport)
- Exposes 34 tools to Claude Desktop
- Uses hybrid execution strategy:
  1. Attempts to load generated TypeScript module
  2. Falls back to direct Docker bridge if module unavailable
- Handles JSON-RPC communication

---

## Build Output Summary

After running `npm run build:workspace`:

```
workspace/
├── lib/
│   ├── mcp-client.ts (source)
│   ├── mcp-client.js (compiled)
│   └── mcp-client.d.ts (types)
├── servers/
│   ├── database/
│   │   ├── *.ts (34 source files across all servers)
│   │   └── *.js (34 compiled modules)
│   ├── processing/
│   ├── alignment/
│   ├── design/
│   └── validation/
├── mcp-server.ts (source)
└── mcp-server.js (compiled)
```

**Total Files Generated:** 41 JavaScript files
- 1 mcp-client.js
- 34 tool modules
- 5 index.js barrel exports  
- 1 mcp-server.js

---

## Tool Execution Flow

### Hybrid Execution Strategy

When Claude Desktop calls a tool (e.g., `processing_fastaQc`):

```typescript
// 1. Parse tool name
const [serverName, ...functionParts] = 'processing_fastaQc'.split('_');
// serverName = 'processing'
// functionName = 'fastaQc'

// 2. Try generated module first
try {
  const module = await import('./servers/processing/index.js');
  if (module.fastaQc) {
    return await module.fastaQc(args);  // Calls mcp-client.callMCPTool()
  }
} catch (error) {
  // 3. Fall back to direct Docker bridge
  return await callPythonMCPServer('processing', 'fasta_qc', args);
}
```

### Why Hybrid?

1. **Generated modules provide:**
   - Type safety
   - IDE autocomplete
   - Consistent API
   - Centralized communication layer

2. **Docker fallback ensures:**
   - 100% tool coverage
   - Graceful degradation
   - No dependency failures
   - Reliability

---

## Development Workflow

### Making Changes

**1. Update Python MCP Server:**
```bash
# Edit tool in Python
vim mcp_servers/processing_mcp_server.py

# Regenerate TypeScript wrappers
npm run generate-tools:all
```

**2. Update MCP Client:**
```bash
# Edit client library
vim workspace/lib/mcp-client.ts

# Rebuild just the client
npm run build:lib
```

**3. Update Main Server:**
```bash
# Edit server logic
vim workspace/mcp-server.ts

# Rebuild just the server
npm run build:mcp-server
```

**4. Rebuild Everything:**
```bash
# After major changes
npm run build:workspace
```

### Testing After Build

**1. Verify Server Starts:**
```bash
node workspace/mcp-server.js
# Should show: ✅ mdk-mcp-typescript v2.0.0 running on stdio
#             📊 Tools available: 34
```

**2. Test Module Imports:**
```bash
# Test that modules load
node -e "import('./workspace/servers/processing/index.js').then(m => console.log(Object.keys(m)))"

# Should output: ['dereplicateSequences', 'detectChimeras', 'fastaQc', ...]
```

**3. Test in Claude Desktop:**
- Restart Claude Desktop
- Open chat
- Type: "List available tools" or use the 🔌 icon
- Should show all 34 tools

---

## Troubleshooting

### Build Fails with "Cannot find module"

**Cause:** TypeScript compiler creating nested directories

**Solution:** The build script now runs `tsc` from within `workspace/` directory:
```bash
cd workspace && tsc servers/**/*.ts ...
```

### Server Shows Wrong Number of Tools

**Cause:** Old compiled files or incomplete build

**Solution:**
```bash
# Clean and rebuild
rm -rf workspace/servers/*/index.js workspace/lib/*.js workspace/mcp-server.js
npm run build:workspace
```

### Module Import Fails in Runtime

**Cause:** Generated modules can't find `mcp-client.js`

**Solution:** Ensure `build:lib` runs before `build:servers`:
```json
"build:workspace": "npm run build:lib && npm run build:servers && npm run build:mcp-server"
```

### Tools Listed but Execution Fails

**Cause:** Hybrid execution not working

**Fix:** The server automatically falls back to Docker bridge. Check:
1. Docker containers are running: `docker ps`
2. Debug mode: `DEBUG=true node workspace/mcp-server.js`

---

## Configuration

### TypeScript Compiler Options

All build steps use consistent TypeScript configuration:

```typescript
{
  module: "ES2022",           // Modern ES modules
  target: "ES2022",           // Modern JavaScript features
  moduleResolution: "node",   // Node.js resolution
  esModuleInterop: true,      // Interop with CommonJS
  skipLibCheck: true,         // Speed up compilation
  declaration: true           // Generate .d.ts (lib only)
}
```

### Package.json Scripts Reference

```json
{
  "generate-tools:all": "tsx examples/generate-all-tools.ts",
  "build:lib": "tsc workspace/lib/mcp-client.ts --outDir workspace/lib ...",
  "build:servers": "npm run generate-tools:all && cd workspace && tsc servers/**/*.ts ...",
  "build:mcp-server": "tsc workspace/mcp-server.ts --outDir workspace ...",
  "build:workspace": "npm run build:lib && npm run build:servers && npm run build:mcp-server"
}
```

---

## Performance

### Build Times (typical)

- `build:lib`: ~1-2 seconds
- `build:servers`: ~5-8 seconds (includes generation + compilation)
- `build:mcp-server`: ~2-3 seconds
- **Total**: ~10-15 seconds

### Optimization Tips

1. **Partial builds:** Only rebuild what changed
2. **Skip generation:** If Python tools unchanged, compile TypeScript directly
3. **Watch mode:** Use `tsc --watch` for development

---

## Integration with Claude Desktop

After successful build, Claude Desktop configuration:

```json
{
  "mcpServers": {
    "mdk-mcp": {
      "command": "node",
      "args": [
        "/home/cxl/MDK_Design/mdk_mcp/workspace/mcp-server.js"
      ],
      "env": {
        "DEBUG": "false"
      }
    }
  }
}
```

**Note:** Use Windows path format when configuring from Windows:
```
\\\\wsl.localhost\\Ubuntu\\home\\cxl\\MDK_Design\\mdk_mcp\\workspace\\mcp-server.js
```

---

## Summary

The `npm run build:workspace` command provides a complete, automated build system that:

✅ **Compiles** the MCP client library with type declarations  
✅ **Generates** 34 TypeScript tool wrappers from Python sources  
✅ **Compiles** all server modules to JavaScript  
✅ **Builds** the main MCP server  
✅ **Validates** module structure and imports  
✅ **Enables** hybrid execution (TypeScript + Docker fallback)

**Result:** A production-ready TypeScript MCP wrapper that exposes all 34 bioinformatics tools to Claude Desktop with full type safety and graceful degradation.

---

**For more information:**
- [Quick Start Guide](./claude-desktop/START_HERE.md)
- [Complete Tool Catalog](../COMPLETE_TOOL_CATALOG.md)
- [README](../README.md)

