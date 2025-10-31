# Design MCP Server

## Overview

The **Design MCP Server** provides comprehensive primer design and signature region discovery capabilities for the neglected-diagnostics project. This server implements Phase 4 of the project roadmap, enabling species-specific qPCR primer design through signature region identification, Primer3 integration, and rigorous quality control.

## Features

### 6 MCP Tools

1. **`find_signature_regions`** - Signature region discovery
   - Sliding window analysis of alignments
   - Identifies regions conserved within target species
   - Detects divergence from off-target species
   - Configurable conservation and divergence thresholds

2. **`analyze_specificity`** - Specificity scoring
   - Analyzes candidate regions for primer suitability
   - Calculates specificity scores based on target/off-target comparison
   - Identifies potential SNPs for discrimination
   - Flags regions suitable for primer design

3. **`rank_regions`** - Multi-criteria ranking
   - Composite scoring with configurable weights
   - Considers conservation, specificity, and complexity
   - Returns prioritized list of candidate regions
   - Customizable weighting schemes

4. **`primer3_design`** - Primer3 integration
   - Full Primer3 wrapper for qPCR primer design
   - Configurable constraints (size, Tm, GC content, product size)
   - Supports targeted and genome-wide design
   - Returns multiple primer pairs per region

5. **`oligo_qc`** - Oligonucleotide quality control
   - Melting temperature (Tm) calculation
   - Secondary structure analysis (hairpins, dimers)
   - GC content and complexity assessment
   - Homopolymer detection
   - Pass/fail flags with recommendations

6. **`design_primers_complete`** - End-to-end pipeline
   - Orchestrates entire workflow automatically
   - Region discovery → specificity → ranking → Primer3 → QC
   - Returns only validated, high-quality primer pairs
   - Recommended for automated workflows

## Installation & Usage

### Docker Deployment (Recommended)

```bash
cd mcp_servers/design_server

# Build image
docker build -t ndiag-design-server:latest .

# Run with docker-compose
docker-compose up --build

# Or run standalone
docker run -d --name ndiag-design-server -i ndiag-design-server:latest
```

### Testing with MCP Inspector

```bash
# Interactive UI mode
npx @modelcontextprotocol/inspector python3 design_mcp_server.py
# Open http://localhost:6274

# CLI mode
npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 design_mcp_server.py
```

### Unit Tests

```bash
# Run pytest
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## Tool Examples

### 1. Find Signature Regions

```json
{
  "tool": "find_signature_regions",
  "arguments": {
    "alignment_content": ">target1\nATGCGATCGAT...\n>target2\nATGCGATCGAT...\n>offtarget1\nATGCGTTCGAT...",
    "target_sequences": ["target"],
    "window_size": 150,
    "step_size": 10,
    "min_conservation": 0.8,
    "min_divergence": 0.3
  }
}
```

**Response:**
```json
{
  "success": true,
  "num_candidates": 5,
  "regions": [
    {
      "start": 100,
      "end": 250,
      "conservation": 0.92,
      "divergence": 0.45,
      "gc_content": 52.3,
      "complexity": 0.78,
      "consensus_sequence": "ATGCGATC..."
    }
  ]
}
```

### 2. Complete Pipeline (Recommended)

```json
{
  "tool": "design_primers_complete",
  "arguments": {
    "alignment_content": ">target1\nATGC...\n>offtarget1\nATGC...",
    "target_sequences": ["target"],
    "offtarget_sequences": ["offtarget"],
    "primer_constraints": {
      "primer_size": [18, 22, 27],
      "tm": [57, 60, 63],
      "product_size": [80, 150, 300],
      "num_return": 5
    },
    "region_params": {
      "window_size": 150,
      "min_conservation": 0.85,
      "min_divergence": 0.35
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "pipeline_steps": {
    "regions_found": 8,
    "regions_analyzed": 8,
    "regions_ranked": 8,
    "primers_designed": 5,
    "primers_recommended": 3
  },
  "recommended_primers": [
    {
      "pair_id": 0,
      "forward_sequence": "ATGCGATCGATCGATC",
      "reverse_sequence": "CGATCGATCGATCGAT",
      "forward_tm": 59.5,
      "reverse_tm": 60.2,
      "product_size": 120,
      "qc_results": {
        "both_pass": true
      },
      "recommended": true
    }
  ]
}
```

### 3. Oligo Quality Control

```json
{
  "tool": "oligo_qc",
  "arguments": {
    "sequence": "ATGCGATCGATCGATCGAT",
    "salt_mM": 50.0,
    "mg_mM": 2.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "sequence": "ATGCGATCGATCGATCGAT",
  "length": 19,
  "gc_content": 52.63,
  "tm": 58.3,
  "complexity": 0.85,
  "max_homopolymer": 2,
  "hairpin_tm": 25.4,
  "homodimer_tm": 32.1,
  "qc_pass": true,
  "flags": []
}
```

## Configuration

### Environment Variables

Set via `.env` file or docker-compose.yml:

```bash
# Server settings
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8003

# Processing limits
MAX_SEQUENCES=10000
MAX_FILE_SIZE_MB=200

# Region discovery defaults
DEFAULT_WINDOW_SIZE=150
DEFAULT_STEP_SIZE=10
DEFAULT_MIN_CONSERVATION=0.8
DEFAULT_MIN_DIVERGENCE=0.3

# Primer design defaults
DEFAULT_PRIMER_SIZE_MIN=18
DEFAULT_PRIMER_SIZE_OPT=22
DEFAULT_PRIMER_SIZE_MAX=27
DEFAULT_PRIMER_TM_MIN=57.0
DEFAULT_PRIMER_TM_OPT=60.0
DEFAULT_PRIMER_TM_MAX=63.0
DEFAULT_PRIMER_GC_MIN=40.0
DEFAULT_PRIMER_GC_OPT=50.0
DEFAULT_PRIMER_GC_MAX=60.0

# Logging
LOG_LEVEL=INFO
```

## Dependencies

### System Tools
- **primer3** - Primer design engine
- **ViennaRNA** - RNA/DNA secondary structure prediction

### Python Libraries
- **mcp** ≥0.9.0 - MCP SDK
- **biopython** ≥1.81 - Sequence manipulation
- **primer3-py** ≥1.1.0 - Python wrapper for Primer3
- **numpy** ≥1.24.0 - Numerical computing
- **pandas** ≥2.0.0 - Data structures
- **scipy** ≥1.10.0 - Scientific computing

## Algorithm Details

### Signature Region Discovery

1. **Sliding Window Analysis**
   - Window slides across alignment with configurable size and step
   - Default: 150bp windows, 10bp steps

2. **Conservation Scoring**
   - Calculates per-column conservation within target group
   - Uses nucleotide frequency analysis
   - Minimum threshold: 80% (configurable)

3. **Divergence Scoring**
   - Compares target vs off-target groups
   - Identifies discriminatory positions
   - Minimum threshold: 30% (configurable)

4. **Quality Metrics**
   - GC content (target: 40-60%)
   - Sequence complexity (avoids repeats)
   - Consensus sequence generation

### Multi-Criteria Ranking

Composite score = (Conservation × 0.4) + (Specificity × 0.4) + (Complexity × 0.2)

Weights are configurable and automatically normalized.

### Primer Design

1. **Primer3 Integration**
   - Full parameter customization
   - Multiple primer pairs per region
   - Penalty-based optimization

2. **Quality Control**
   - Tm calculation with salt correction
   - Hairpin detection (ViennaRNA)
   - Homodimer analysis
   - GC content validation
   - Homopolymer detection

## Integration with AG2

The Design MCP Server integrates with the AG2 multi-agent system through the `MCPClientBridge`:

```python
from autogen_mcp_bridge import MCPClientBridge

# Initialize bridge with design server
bridge = MCPClientBridge({
    "design": {
        "container": "ndiag-design-server",
        "transport": "stdio"
    }
})

await bridge.start_servers()

# Design primers via AG2 agents
primers = await bridge.call_tool("design", "design_primers_complete", {
    "alignment_content": alignment_data,
    "target_sequences": ["Salmo_salar"],
    "offtarget_sequences": ["Oncorhynchus"]
})
```

## Architecture

```
design_server/
├── design_mcp_server.py    # Main server (1200+ lines)
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml       # Local deployment
├── entrypoint.sh           # Entrypoint script
├── mcp-server.json         # MCP manifest
├── .env.template           # Environment template
├── .gitignore              # Git ignore rules
├── tests/
│   ├── __init__.py
│   └── test_design_server.py  # Unit tests
└── README.md               # This file
```

## Performance

- **Signature Region Discovery**: ~1-5 seconds for 100 sequences, 1000bp alignment
- **Primer3 Design**: ~0.1-0.5 seconds per region
- **Complete Pipeline**: ~5-15 seconds for typical workflows
- **Memory**: ~100-500MB depending on alignment size

## Troubleshooting

### Common Issues

1. **Primer3 not found**
   ```bash
   # Verify primer3 installation
   docker exec ndiag-design-server primer3_core --version
   ```

2. **ViennaRNA errors**
   ```bash
   # Check RNAfold
   docker exec ndiag-design-server RNAfold --version
   ```

3. **Python import errors**
   ```bash
   # Reinstall dependencies
   docker exec ndiag-design-server pip3 install -r /app/requirements.txt
   ```

4. **No signature regions found**
   - Lower `min_conservation` threshold (try 0.7)
   - Lower `min_divergence` threshold (try 0.2)
   - Increase `window_size` (try 200)
   - Verify target/off-target sequence IDs are correct

## Known Limitations

- **Maximum alignment length**: 50,000 bp (configurable via `MAX_ALIGNMENT_LENGTH`)
- **Maximum sequences**: 10,000 (configurable via `MAX_SEQUENCES`)
- **Primer3 constraints**: Limited to Primer3's capabilities
- **ViennaRNA**: Secondary structure predictions are estimates

## Future Enhancements

- [ ] Multiple alignment format support (Stockholm, Phylip)
- [ ] BLAST-based specificity validation
- [ ] Multi-threading for large alignments
- [ ] Primer dimer checking across all primer pairs
- [ ] Export to primer databases (PrimerBank, etc.)

## License

MIT License - see project root for details

## Support

For issues or questions:
1. Check the project's main README
2. Review test cases in `tests/`
3. Check MCP Inspector output for debugging
4. Open an issue on the project repository

## Version History

- **0.1.0** (2025-10-31) - Initial implementation
  - 6 MCP tools implemented
  - Primer3 and ViennaRNA integration
  - Complete end-to-end pipeline
  - Unit tests and documentation
