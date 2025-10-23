# Processing MCP Server

**ndiag-processing-server** provides sequence processing capabilities through the Model Context Protocol (MCP).

## Features

- **Quality Control** - Filter sequences by length, N-content, and remove duplicates
- **Dereplication** - Remove duplicate/near-duplicate sequences via clustering
- **Low-Complexity Masking** - Mask repetitive regions using DUST algorithm
- **Chimera Detection** - Identify chimeric sequences using UCHIME
- **Unified Pipeline** - Combine multiple processing steps in a single workflow

## Available MCP Tools

### 1. fasta_qc
Quality control filtering for FASTA sequences.

**Parameters:**
- `fasta_content` (string, required): Input FASTA sequences
- `min_length` (integer, default: 100): Minimum sequence length
- `max_n_percent` (number, default: 5.0): Maximum percentage of N bases
- `remove_duplicates` (boolean, default: true): Remove exact duplicates

**Returns:** Cleaned FASTA + QC statistics

### 2. dereplicate_sequences
Remove duplicate or near-duplicate sequences using clustering.

**Parameters:**
- `fasta_content` (string, required): Input FASTA sequences
- `identity_threshold` (number, default: 0.97): Clustering identity threshold (0.0-1.0)
- `per_species` (boolean, default: true): Group by species before dereplication

**Returns:** Dereplicated FASTA + statistics

### 3. mask_low_complexity
Mask low-complexity regions and repeats using DUST algorithm.

**Parameters:**
- `fasta_content` (string, required): Input FASTA sequences
- `mask_repeats` (boolean, default: true): Mask repetitive regions
- `mask_homopolymers` (boolean, default: true): Mask homopolymer runs
- `min_complexity` (number, default: 1.5): Minimum complexity score

**Returns:** Masked FASTA (N's replace low-complexity regions) + statistics

### 4. detect_chimeras
Detect and remove chimeric sequences using UCHIME algorithm.

**Parameters:**
- `fasta_content` (string, required): Input FASTA sequences
- `reference_db` (string, default: "auto"): Reference database (auto/silva/unite)
- `abundance_threshold` (number, default: 2.0): Abundance skew threshold

**Returns:** Non-chimeric FASTA + detection statistics

### 5. process_sequences
Unified pipeline combining multiple processing steps.

**Parameters:**
- `fasta_content` (string, required): Input FASTA sequences
- `pipeline` (array, default: ["qc", "dereplicate"]): Processing steps to execute
- `qc_params` (object, optional): Parameters for QC step
- `derep_params` (object, optional): Parameters for dereplication step
- `mask_params` (object, optional): Parameters for masking step
- `chimera_params` (object, optional): Parameters for chimera detection step

**Returns:** Processed FASTA + cumulative statistics

## Quick Start

### Build and Run

```bash
# Build the container
docker build -t ndiag-processing-server:latest .

# Run with docker-compose (recommended)
docker-compose up --build

# Or run standalone
docker run -d --name ndiag-processing-server -i ndiag-processing-server:latest
```

### Example Usage

#### Basic QC
```json
{
  "tool": "fasta_qc",
  "arguments": {
    "fasta_content": ">seq1\nATGCATGC...",
    "min_length": 150,
    "max_n_percent": 3.0
  }
}
```

#### Dereplication
```json
{
  "tool": "dereplicate_sequences",
  "arguments": {
    "fasta_content": ">seq1\nATGCATGC...",
    "identity_threshold": 0.95
  }
}
```

#### Full Pipeline
```json
{
  "tool": "process_sequences",
  "arguments": {
    "fasta_content": ">seq1\nATGCATGC...",
    "pipeline": ["qc", "dereplicate", "mask", "chimera"],
    "qc_params": {"min_length": 150},
    "derep_params": {"identity_threshold": 0.97}
  }
}
```

## Technology Stack

### External Tools
- **seqkit** (v2.6.1+): Fast FASTA/Q manipulation and statistics
- **vsearch** (v2.25.0+): Clustering, dereplication, chimera detection, masking

### Python Libraries
- **BioPython** (v1.81+): Sequence parsing and manipulation
- **MCP** (v0.9.0+): Model Context Protocol framework

## Configuration

Environment variables (optional):

```bash
LOG_LEVEL=INFO                     # Logging level (DEBUG, INFO, WARNING, ERROR)
TEMP_DIR=/tmp/mcp_processing       # Temporary file directory
MAX_SEQUENCES=10000                # Maximum sequences to process
DEFAULT_MIN_LENGTH=100             # Default minimum sequence length
DEFAULT_MAX_N_PERCENT=5.0          # Default maximum N-content percentage
DEFAULT_IDENTITY_THRESHOLD=0.97    # Default clustering identity
```

## Integration with AG2

```python
from autogen_mcp_bridge import MCPClientBridge

# Initialize bridge
bridge = MCPClientBridge({
    "database": {"container": "ndiag-database-server", ...},
    "processing": {"container": "ndiag-processing-server", ...}
})

await bridge.start_servers()

# Get sequences from database
sequences = await bridge.call_tool("database", "get_sequences", {
    "taxon": "Salmo salar",
    "region": "COI",
    "max_results": 500
})

# Process sequences
cleaned = await bridge.call_tool("processing", "process_sequences", {
    "fasta_content": sequences,
    "pipeline": ["qc", "dereplicate", "mask"]
})
```

## Workflow Integration

```
Phase 1 (Database) → Phase 2 (Processing) → Phase 3 (Alignment)
     ↓                      ↓                       ↓
Retrieve sequences  →  Clean & filter  →  Ready for alignment
```

## Testing

```bash
# Run tests
cd /path/to/processing_server
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Performance

- **Typical QC**: 1000 sequences in <5 seconds
- **Dereplication**: 1000 sequences in <10 seconds
- **Chimera Detection**: 1000 sequences in <30 seconds
- **Full Pipeline**: 1000 sequences in <1 minute

## Troubleshooting

### seqkit not found
Ensure seqkit is in PATH or set `SEQKIT_PATH` environment variable.

### vsearch errors
Check vsearch version: `vsearch --version` (requires v2.25.0+)

### Memory issues
Reduce `MAX_SEQUENCES` or process in smaller batches.

## Architecture

Built following Phase 2 of the Neglected Diagnostics MCP roadmap:
- stdio-based MCP protocol
- Async/await for all operations
- Temporary file management for external tools
- Comprehensive error handling and logging
- Docker containerization with health checks

## Documentation

- **MCP Framework**: https://github.com/modelcontextprotocol
- **seqkit**: https://github.com/shenwei356/seqkit
- **vsearch**: https://github.com/torognes/vsearch
- **BioPython**: https://biopython.org

## License

MIT License - Part of the Neglected Diagnostics MCP project
