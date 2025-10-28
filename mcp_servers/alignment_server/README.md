# Alignment MCP Server

**Phase 3** of the neglected-diagnostics MCP architecture: Sequence alignment and phylogenetic analysis.

## Overview

This MCP server provides comprehensive alignment and phylogenetic analysis capabilities for the neglected-diagnostics project. It supports multiple alignment algorithms (MAFFT, MUSCLE, Clustal Omega, gget_muscle), alignment quality processing with CIAlign, phylogenetic tree construction, and distance matrix calculations.

## Features

### 5 MCP Tools

1. **align_sequences** - Multiple sequence alignment with choice of algorithms
2. **process_alignment** - Alignment cleaning and quality assessment with CIAlign
3. **build_phylogeny** - Phylogenetic tree construction (NJ, ML, MP methods)
4. **calculate_distances** - Pairwise distance matrix calculation
5. **align_and_analyze** - Complete unified pipeline

### Supported Algorithms

- **MAFFT** - Fast and accurate alignment (strategies: auto, linsi, ginsi, einsi)
- **MUSCLE v5** - High-throughput alignment
- **Clustal Omega** - General-purpose MSA
- **gget_muscle** - gget wrapper for MUSCLE with additional features

### Quality Processing

- **CIAlign** integration for alignment cleaning
- Gap removal and trimming
- Divergent sequence detection
- Alignment statistics and quality metrics

### Phylogenetic Analysis

- **Neighbor Joining (NJ)** - Fast distance-based trees
- **Maximum Likelihood (ML)** - Statistical phylogenetic inference
- **Maximum Parsimony (MP)** - Character-based tree building
- Multiple distance models: p-distance, Jukes-Cantor, Kimura

## Quick Start

### Build and Run with Docker Compose

```bash
cd mcp_servers/alignment_server

# Build the container
docker-compose up --build -d

# Check container status
docker ps | grep alignment
```

### Run Standalone Container

```bash
# Build image
docker build -t ndiag-alignment-server:latest .

# Run container
docker run -d --name ndiag-alignment-server -i ndiag-alignment-server:latest
```

## Usage Examples

### 1. Simple Alignment (MAFFT)

```json
{
  "tool": "align_sequences",
  "arguments": {
    "fasta_content": ">seq1\nATCGATCG\n>seq2\nATCGTTTT\n>seq3\nATCGGGGG",
    "algorithm": "mafft",
    "mafft_strategy": "auto"
  }
}
```

**Response:**
```json
{
  "alignment": ">seq1\nATCG-ATCG\n>seq2\nATCG-TTTT\n>seq3\nATCG-GGGG",
  "algorithm": "mafft",
  "statistics": {
    "num_sequences": 3,
    "alignment_length": 9,
    "average_gaps_per_sequence": 1.0,
    "average_conservation": 0.89
  },
  "success": true
}
```

### 2. High-Accuracy Alignment with MAFFT L-INS-i

```json
{
  "tool": "align_sequences",
  "arguments": {
    "fasta_content": "<your sequences>",
    "algorithm": "mafft",
    "mafft_strategy": "linsi",
    "max_iterations": 1000
  }
}
```

### 3. Process and Clean Alignment

```json
{
  "tool": "process_alignment",
  "arguments": {
    "alignment_content": "<aligned sequences>",
    "trim_gaps": true,
    "gap_threshold": 0.5,
    "remove_divergent": true,
    "assess_quality": true
  }
}
```

**Response:**
```json
{
  "alignment": "<cleaned alignment>",
  "statistics": {
    "original_sequences": 100,
    "cleaned_sequences": 95,
    "sequences_removed": 5
  },
  "quality_stats": {
    "num_sequences": 95,
    "alignment_length": 450,
    "average_conservation": 0.92
  },
  "success": true
}
```

### 4. Build Phylogenetic Tree

```json
{
  "tool": "build_phylogeny",
  "arguments": {
    "alignment_content": "<aligned sequences>",
    "method": "nj",
    "model": "kimura",
    "bootstrap": 100
  }
}
```

**Response:**
```json
{
  "tree_newick": "((seq1:0.1,seq2:0.15):0.2,seq3:0.3);",
  "method": "neighbor_joining",
  "model": "kimura",
  "num_taxa": 3,
  "success": true
}
```

### 5. Calculate Distance Matrix

```json
{
  "tool": "calculate_distances",
  "arguments": {
    "alignment_content": "<aligned sequences>",
    "model": "kimura"
  }
}
```

**Response:**
```json
{
  "sequence_names": ["seq1", "seq2", "seq3"],
  "distance_matrix": [
    [0.0, 0.15, 0.25],
    [0.15, 0.0, 0.30],
    [0.25, 0.30, 0.0]
  ],
  "model": "kimura",
  "num_sequences": 3,
  "success": true
}
```

### 6. Complete Pipeline (align + clean + phylogeny)

```json
{
  "tool": "align_and_analyze",
  "arguments": {
    "fasta_content": "<unaligned sequences>",
    "algorithm": "mafft",
    "include_phylogeny": true,
    "include_distances": true,
    "clean_alignment": true
  }
}
```

**Response:**
```json
{
  "pipeline_steps": ["alignment", "cleaning", "distances", "phylogeny"],
  "alignment": "<final cleaned alignment>",
  "alignment_statistics": {...},
  "cleaning_statistics": {...},
  "quality_stats": {...},
  "distances": {...},
  "phylogeny": {...},
  "success": true
}
```

## Tool Reference

### align_sequences

Align sequences using various algorithms.

**Parameters:**
- `fasta_content` (string, required) - Input sequences in FASTA format
- `algorithm` (string, default: "mafft") - Algorithm: mafft, muscle, clustalo, gget_muscle
- `mafft_strategy` (string, default: "auto") - MAFFT strategy: auto, linsi, ginsi, einsi
- `max_iterations` (integer, default: 1000) - Maximum iterations
- `super5` (boolean, default: false) - Use MUSCLE5 super5 algorithm (gget_muscle only)

### process_alignment

Process and clean alignment using CIAlign.

**Parameters:**
- `alignment_content` (string, required) - Aligned sequences in FASTA format
- `trim_gaps` (boolean, default: true) - Remove gap-rich columns
- `gap_threshold` (number, default: 0.5) - Gap removal threshold (0-1)
- `remove_divergent` (boolean, default: false) - Remove divergent sequences
- `assess_quality` (boolean, default: true) - Calculate quality statistics

### build_phylogeny

Build phylogenetic tree from alignment.

**Parameters:**
- `alignment_content` (string, required) - Aligned sequences in FASTA format
- `method` (string, default: "nj") - Method: nj, ml, mp
- `bootstrap` (integer, default: 100) - Number of bootstrap replicates
- `model` (string, default: "kimura") - Distance model: p-distance, jukes-cantor, kimura

### calculate_distances

Calculate pairwise distance matrix from alignment.

**Parameters:**
- `alignment_content` (string, required) - Aligned sequences in FASTA format
- `model` (string, default: "kimura") - Distance model: p-distance, jukes-cantor, kimura

### align_and_analyze

Complete pipeline: align, process, and optionally analyze.

**Parameters:**
- `fasta_content` (string, required) - Input sequences in FASTA format
- `algorithm` (string, default: "mafft") - Alignment algorithm
- `include_phylogeny` (boolean, default: false) - Build phylogenetic tree
- `include_distances` (boolean, default: false) - Calculate distance matrix
- `clean_alignment` (boolean, default: true) - Clean alignment with CIAlign

## Configuration

Configuration is managed via environment variables (see `.env.template`):

```bash
# Logging
LOG_LEVEL=INFO

# Temporary files
TEMP_DIR=/tmp/mcp_alignment

# Processing limits
MAX_SEQUENCES=10000
MAX_FILE_SIZE_MB=200

# Tool paths
MAFFT_PATH=mafft
MUSCLE_PATH=muscle
CLUSTALO_PATH=clustalo

# Alignment defaults
DEFAULT_MAFFT_STRATEGY=auto
DEFAULT_MAX_ITERATIONS=1000
DEFAULT_GAP_THRESHOLD=0.5

# Phylogeny defaults
DEFAULT_PHYLO_METHOD=nj
DEFAULT_BOOTSTRAP=100
DEFAULT_DISTANCE_MODEL=kimura
```

## Testing

### Run Unit Tests

```bash
cd mcp_servers/alignment_server
python3 -m pytest tests/ -v
```

### Test with MCP Inspector (Interactive)

```bash
# Install MCP Inspector (if not already installed)
npm install -g @modelcontextprotocol/inspector

# Run inspector
cd mcp_servers/alignment_server
npx @modelcontextprotocol/inspector python3 alignment_mcp_server.py

# Open browser to http://localhost:6274
```

### Test with Automated Script

```bash
# From project root
./test_mcp_server.sh alignment
```

## Dependencies

### System Dependencies
- **mafft** >= 7.0 - Multiple sequence alignment
- **muscle** >= 5.0 - Alternative alignment algorithm
- **clustalo** >= 1.2 - Clustal Omega alignment
- **Python 3.11+** - Runtime environment

### Python Dependencies
- **mcp** >= 0.9.0 - Model Context Protocol framework
- **biopython** >= 1.81 - Sequence analysis and phylogenetics
- **gget** >= 0.28.0 - Genomics data access
- **numpy** >= 1.24.0 - Numerical computing
- **pandas** >= 2.0.0 - Data manipulation
- **ete3** >= 3.1.2 - Tree visualization and manipulation
- **dendropy** >= 4.6.0 - Phylogenetic computing
- **cialign** >= 1.0.0 - Alignment cleaning

## Architecture

The alignment server follows the standard MCP server pattern:

```
alignment_mcp_server.py     # Main server with tool handlers
├── Helper Functions
│   ├── run_command()       # Async subprocess execution
│   ├── write_temp_fasta()  # File I/O utilities
│   └── validate_fasta()    # Input validation
├── Alignment Functions
│   ├── align_with_mafft()
│   ├── align_with_muscle()
│   ├── align_with_clustalo()
│   └── align_with_gget_muscle()
├── Processing Functions
│   ├── process_alignment_with_cialign()
│   └── calculate_alignment_stats()
├── Phylogenetic Functions
│   ├── build_phylogenetic_tree()
│   └── calculate_distance_matrix()
└── Tool Handlers
    ├── handle_list_tools()
    ├── handle_call_tool()
    └── tool_*() implementations
```

## Integration with AG2

The alignment server is designed to work seamlessly with the AG2 multi-agent system:

```python
from autogen_mcp_bridge import MCPClientBridge

# Initialize bridge with alignment server
bridge = MCPClientBridge({
    "alignment": {
        "container": "ndiag-alignment-server",
        "command": ["python3", "alignment_mcp_server.py"]
    }
})

# Call alignment tool from AG2 agents
result = await bridge.call_tool("alignment", "align_sequences", {
    "fasta_content": sequences,
    "algorithm": "mafft"
})
```

## Troubleshooting

### Issue: MAFFT fails with "command not found"

**Solution:** Ensure MAFFT is installed in the container:
```bash
docker exec -it ndiag-alignment-server mafft --version
```

### Issue: CIAlign produces no output

**Solution:** CIAlign may return non-zero exit codes even on success. The server handles this gracefully and returns the original alignment if CIAlign fails.

### Issue: Out of memory during alignment

**Solution:** Increase Docker memory limits in docker-compose.yml:
```yaml
services:
  alignment-server:
    deploy:
      resources:
        limits:
          memory: 4G
```

### Issue: Phylogenetic tree building fails

**Solution:** Ensure your alignment has at least 3 sequences and is properly formatted. Check alignment statistics first with `process_alignment`.

## Performance Notes

- **MAFFT** is generally fastest for large alignments (use "auto" strategy)
- **MAFFT L-INS-i** (linsi) provides highest accuracy but is slower
- **MUSCLE v5** is good balance between speed and accuracy
- **Clustal Omega** is well-suited for very large datasets (>1000 sequences)

## Roadmap

This is Phase 3 of the 6-phase MCP architecture:

- ✅ **Phase 1**: Database Integration (completed)
- ✅ **Phase 2**: Sequence Processing (completed)
- ✅ **Phase 3**: Alignment & Phylogenetics (current)
- 📋 **Phase 4**: Design & Primers (planned)
- 📋 **Phase 5**: Validation & Literature (planned)
- 📋 **Phase 6**: Export & Provenance (planned)

## Contributing

When adding new alignment algorithms or phylogenetic methods:

1. Add the implementation function in the appropriate section
2. Register the tool in `handle_list_tools()`
3. Add handler case in `handle_call_tool()`
4. Write tests in `tests/`
5. Update this README with usage examples

## License

MIT License - See project root for details

## Support

For issues and questions:
- File issues at: https://github.com/your-repo/issues
- See main project documentation: `../../README.md`
- Review testing guide: `../../docs/MCP_TESTING_GUIDE.md`
