# Code Execution Sandbox for MCP

A secure, isolated code execution environment for the Model Context Protocol (MCP), designed for bioinformatics workflows with integrated database access, sequence processing, and file management capabilities.

## Features

### Core Capabilities

- **🔒 Secure Sandboxing**: Isolated VM execution with timeout enforcement and resource limits
- **🧬 Bioinformatics Tools**: Pre-loaded MCP servers for database, processing, alignment, design, and validation
- **📁 Filesystem Operations**: Copy files between local filesystem and container workspace
- **📚 Comprehensive Documentation**: Built-in docs for all available functions and workflows
- **⚡ Context Efficiency**: Helper functions to minimize token usage
- **🛡️ Error Handling**: Robust error reporting and validation

### Available MCP Tools

1. **execute_code** - Execute TypeScript/JavaScript in secure sandbox
2. **copy_file_to_workspace** - Import files into container workspace
3. **copy_file_from_workspace** - Export files from container workspace

## Quick Start

### 1. Build the Project

```bash
cd /home/cxl/MDK_Design/mdk_mcp/code-execution
npm install
npm run build
```

### 2. Basic Usage

#### Execute Code

```typescript
const result = await execute_code({
  code: `
    // Access database
    const sequences = await database.getSequences({
      taxon: "Salmo salar",
      region: "COI",
      source: "ncbi",
      max_results: 100
    });
    
    // Process data efficiently
    const stats = parseFastaStats(sequences);
    return stats;
  `
});
```

#### Copy Files Into Workspace

```typescript
const result = await copy_file_to_workspace({
  source_path: "/home/user/data/sequences.fasta",
  destination_path: "input/sequences.fasta"
});

console.log(result);
// { success: true, path: "/workspace/input/sequences.fasta" }
```

#### Copy Files From Workspace

```typescript
const result = await copy_file_from_workspace({
  workspace_path: "output/results.fasta",
  destination_path: "/home/user/results/processed.fasta"
});

console.log(result);
// { success: true, path: "/home/user/results/processed.fasta", size: 125600 }
```

## Configuration

### Environment Variables

- `EXECUTION_TIMEOUT`: Maximum execution time in milliseconds (default: 30000)
- `MAX_OUTPUT_SIZE`: Maximum output size in bytes (default: 1048576)
- `WORKSPACE_PATH`: Container workspace directory (default: /workspace)

### Example Configuration

```bash
export EXECUTION_TIMEOUT=60000
export MAX_OUTPUT_SIZE=2097152
export WORKSPACE_PATH=/workspace
```

## Architecture

### Directory Structure

```
code-execution/
├── src/
│   ├── executor.ts       # Main server implementation
│   ├── docs.ts          # MCP tools documentation
│   ├── helpers.js       # Context-efficient helper functions
│   └── helpers.d.ts     # TypeScript definitions
├── tests/
│   └── executor.test.ts # Test suite
├── dist/                # Compiled JavaScript
├── package.json
├── tsconfig.json
├── Dockerfile
└── README.md
```

### Workspace Structure

```
/workspace/
├── input/          # Imported data files
├── output/         # Results and exports
├── temp/           # Temporary files
├── config/         # Configuration files
├── databases/      # Reference databases
└── servers/        # MCP server modules
```

## Available MCP Servers

### Database Server
Access biological sequence databases (NCBI, BOLD, Ensembl, SILVA, UNITE)

```typescript
// Get COI sequences
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  max_results: 100
});

// Search Ensembl
const genes = await database.ggetSearch({
  searchwords: ["hemoglobin"],
  species: "salmo_salar"
});
```

### Processing Server
Quality control and sequence processing

```typescript
// Quality control
const qcResults = await processing.fastaQc({
  sequences: fastaString,
  min_length: 400,
  max_length: 800,
  check_ambiguous: true
});

// Dereplication
const dereplicated = await processing.dereplicateSequences({
  sequences: fastaString,
  similarity_threshold: 0.99
});
```

### Alignment Server
Multiple sequence alignment and phylogenetics

```typescript
// Align sequences
const aligned = await alignment.alignSequences({
  sequences: fastaString,
  algorithm: "mafft"
});

// Build phylogeny
const tree = await alignment.buildPhylogeny({
  alignment: alignedFasta,
  method: "fasttree"
});
```

### Design Server
Primer and probe design

```typescript
const primers = await design.designPrimersComplete({
  target_sequences: targetFasta,
  offtarget_sequences: offtargetFasta,
  primer_parameters: {
    primer_min_size: 18,
    primer_max_size: 25,
    primer_opt_size: 20
  }
});
```

### Validation Server
Primer validation and BLAST

```typescript
// BLAST search
const blastResults = await validation.ggetBlast({
  sequence: "ATCGATCGATCG",
  program: "blastn",
  database: "nt"
});

// In silico PCR
const pcrResults = await validation.inSilicoPcr({
  forward_primer: "ATCGATCG",
  reverse_primer: "CGATCGAT",
  sequences: testSequences
});
```

## Documentation System

### Access Documentation in Code

```typescript
// Quick start guide
console.log(docs.quickStart);

// Server-specific docs
console.log(docs.database);
console.log(docs.processing);
console.log(docs.filesystem);

// Function usage
console.log(docs.database.functions.getSequences.usage);

// Help
console.log(docs.help());
```

## Filesystem Operations

### Path Resolution

**Workspace paths** (relative to `/workspace`):
- Relative: `"input/data.fasta"` → `/workspace/input/data.fasta`
- Absolute: `"/workspace/input/data.fasta"` → `/workspace/input/data.fasta`

**Local paths** (must be absolute):
- Example: `"/home/user/data/sequences.fasta"`

### Common Workflow Pattern

```typescript
// 1. Import data
await copy_file_to_workspace({
  source_path: "/home/user/raw_data.fasta",
  destination_path: "input/raw_data.fasta"
});

// 2. Process in sandbox
const result = await execute_code({
  code: `
    const fs = require('fs').promises;
    const raw = await fs.readFile('/workspace/input/raw_data.fasta', 'utf-8');
    const processed = await processing.fastaQc({ sequences: raw });
    await fs.writeFile('/workspace/output/processed.fasta', processed);
    return { status: 'complete' };
  `
});

// 3. Export results
await copy_file_from_workspace({
  workspace_path: "output/processed.fasta",
  destination_path: "/home/user/results.fasta"
});
```

## Helper Functions

Context-efficient helpers to minimize token usage:

```typescript
// Parse FASTA statistics (returns summary only)
const stats = parseFastaStats(fastaString);
// Returns: { count, averageLength, gcContent, ... }

// Save to file (returns metadata only)
const metadata = await saveToFile(data, 'sequences.fasta');
// Returns: { path, size, lines, ... }

// Extract specific fields
const accessions = extractFields(fastaString, ['accession', 'organism']);
// Returns: [{ accession: 'ABC123', organism: 'Salmo salar' }, ...]

// Filter and save
const result = await filterAndSave(fastaString, (seq) => seq.length > 500, 'filtered.fasta');
```

## Security

### Sandbox Protections

- ✅ Isolated VM execution context
- ✅ Timeout enforcement (configurable)
- ✅ Output size limits
- ✅ Module whitelist (path, util, crypto)
- ✅ No access to dangerous modules (child_process, etc.)
- ✅ Filesystem access restricted to workspace

### Resource Limits

- **Execution Timeout**: 30 seconds (default), configurable
- **Max Output Size**: 1 MB (default), configurable
- **Memory**: Managed by Node.js VM
- **CPU**: Managed by container environment

## Testing

Run the test suite:

```bash
npm test
```

Run tests in watch mode:

```bash
npm run test:watch
```

### Test Coverage

- ✅ Basic code execution
- ✅ Async/await support
- ✅ Console logging
- ✅ Timeout enforcement
- ✅ Module restrictions
- ✅ Output size limits
- ✅ File system access
- ✅ Filesystem operations (copy to/from workspace)
- ✅ Error handling

## Development

### Build

```bash
npm run build
```

### Development Mode

```bash
npm run dev
```

### Type Checking

```bash
npm run typecheck
```

### Clean Build

```bash
npm run clean
npm run build
```

## Docker Integration

### Build Container

```bash
docker build -t code-execution-sandbox .
```

### Run Container

```bash
docker run -it \
  -v /path/to/workspace:/workspace \
  -e EXECUTION_TIMEOUT=30000 \
  -e MAX_OUTPUT_SIZE=1048576 \
  code-execution-sandbox
```

## Troubleshooting

### Common Issues

**Problem**: Code execution times out
**Solution**: Increase `EXECUTION_TIMEOUT` or optimize code

**Problem**: Output truncated
**Solution**: Increase `MAX_OUTPUT_SIZE` or use helper functions to reduce output

**Problem**: Module not found
**Solution**: Check if module is in the whitelist (path, util, crypto) or use pre-loaded MCP servers

**Problem**: File not found when copying
**Solution**: Ensure source path is absolute and file exists

**Problem**: Permission denied
**Solution**: Check file permissions and ensure workspace directory is writable

## Additional Resources

- **[FILESYSTEM_OPERATIONS.md](./FILESYSTEM_OPERATIONS.md)**: Detailed filesystem operations guide
- **[USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)**: Practical usage examples
- **[CHANGELOG.md](./CHANGELOG.md)**: Version history and changes

## Contributing

Contributions are welcome! Please ensure:

1. Tests pass (`npm test`)
2. Code follows TypeScript best practices
3. Documentation is updated
4. Security considerations are addressed

## License

MIT License

## Support

For issues, questions, or contributions:
- Check the documentation files in this directory
- Review the test suite for examples
- Examine the source code comments

