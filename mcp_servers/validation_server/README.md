# Validation & Literature MCP Server

Phase 5 of the mdk_mcp (Neglected Diagnostics MCP) project: Primer validation through BLAST analysis, in-silico PCR simulation, coverage assessment, and literature search capabilities.

## Overview

The Validation Server provides comprehensive tools for validating designed primers and assays for molecular diagnostics. It integrates BLAST searching (both remote via gget and local via NCBI BLAST+), in-silico PCR simulation, coverage assessment, and PubMed literature search to ensure primer specificity, sensitivity, and evidence-based design.

**Key Capabilities:**
- Remote BLAST searches via gget (NCBI and Ensembl)
- Local BLAST searches with custom databases (NCBI BLAST+ 2.12.0+)
- BLAT searches for short exact matches
- In-silico PCR simulation with mismatch tolerance
- Coverage assessment (sensitivity/specificity)
- PubMed literature search for validation evidence
- Complete primer validation pipeline

**Integration**: Designed for use with AG2 (AutoGen) multi-agent systems for natural language-driven diagnostic tool development.

## Features

### 7 MCP Tools

1. **gget_blast** - Remote BLAST search via gget (NCBI/Ensembl)
2. **gget_blat** - Remote BLAT search for short exact matches
3. **blast_nt** - Local BLAST search against custom databases
4. **in_silico_pcr** - Simulate PCR amplification with primers
5. **assess_coverage** - Calculate sensitivity/specificity of primers
6. **search_pubmed** - Search PubMed for validation literature
7. **validate_primers_complete** - Complete validation pipeline

### Infrastructure

- **Docker**: Containerized deployment with NCBI BLAST+ 2.12.0+
- **NCBI Best Practices**: Follows [NCBI BLAST+ documentation](https://github.com/ncbi/blast_plus_docs) for database setup
- **stdio Transport**: MCP protocol over standard input/output
- **Python 3.10+**: Async/await patterns for concurrent operations
- **Testing**: Comprehensive pytest suite with 411 lines of tests

## Installation

### Prerequisites

- Docker and docker-compose
- (Optional) Node.js and npx for MCP Inspector testing
- (Optional) Local BLAST databases (nt/nr) for offline operation

### Quick Start

```bash
# Navigate to server directory
cd mcp_servers/validation_server

# Start with docker-compose (recommended)
docker-compose up --build -d

# Verify container is running
docker ps | grep ndiag-validation-server

# Check BLAST+ installation
docker exec ndiag-validation-server blastn -version
# Output: blastn: 2.12.0+

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python3 validation_mcp_server.py
# Open http://localhost:6274
```

### Configuration

The server uses environment variables for configuration. Copy `.env.template` to `.env` and customize:

```bash
cp .env.template .env
```

**Required Configuration:**
```bash
# NCBI Configuration (REQUIRED for PubMed and remote BLAST)
NCBI_EMAIL=your.email@example.com  # MUST set for NCBI compliance
NCBI_API_KEY=                       # OPTIONAL: Get from NCBI account settings
```

**Optional Configuration:**
```bash
# Server settings
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8004
LOG_LEVEL=INFO

# Processing limits
MAX_SEQUENCES=10000
MAX_FILE_SIZE_MB=200
MAX_QUERY_LENGTH=10000

# BLAST defaults
DEFAULT_BLAST_PROGRAM=blastn
DEFAULT_BLAST_DATABASE=nt
DEFAULT_BLAST_LIMIT=50
DEFAULT_BLAST_EVALUE=10.0

# In-silico PCR defaults
DEFAULT_MAX_MISMATCHES=2
DEFAULT_MIN_PRODUCT_SIZE=50
DEFAULT_MAX_PRODUCT_SIZE=500

# Coverage thresholds
VALIDATION_MIN_SENSITIVITY=0.90
VALIDATION_MIN_SPECIFICITY=0.95
VALIDATION_MAX_OFFTARGET_HITS=5
```

## BLAST Database Setup

The server supports both **remote BLAST** (default, no setup needed) and **local BLAST** (requires database download).

### Option 1: Remote BLAST (Default)

By default, the server uses remote BLAST via gget. No local databases are needed:

```python
# Automatically uses remote NCBI BLAST
result = await gget_blast_impl(
    sequence="ATCGATCGATCG",
    program="blastn",
    database="nt"
)
```

### Option 2: Local BLAST Databases

For high-throughput or offline operation, download local BLAST databases following [NCBI best practices](https://github.com/ncbi/blast_plus_docs).

#### Download Databases

```bash
# Download nt database (~70GB compressed, ~300GB uncompressed)
update_blastdb.pl --decompress nt

# Download nr database (~100GB compressed, ~400GB uncompressed)
update_blastdb.pl --decompress nr

# Store in recommended location
mkdir -p /data/blastdb
mv nt* nr* /data/blastdb/
```

#### Configure Docker Volume

Update `docker-compose.yml` to mount your local databases:

```yaml
services:
  validation-server:
    volumes:
      # Mount local BLAST databases (read-only)
      - /data/blastdb:/blastdb:ro
    environment:
      - BLASTDB=/blastdb
```

#### Environment Variable Setup

Use the standard NCBI `BLASTDB` environment variable:

```bash
# Option 1: Set BLASTDB path (recommended by NCBI)
BLASTDB=/blastdb

# Option 2: Set specific database paths
NT_DATABASE=/blastdb/nt
NR_DATABASE=/blastdb/nr
```

The server automatically detects local databases and uses them when available:

```python
# Automatically uses local nt database if available
result = await blast_nt_impl(
    query_file="sequences.fasta",
    database="nt",
    program="blastn"
)
```

### Directory Structure

Following NCBI recommendations, the container includes:

```
/blastdb           # Standard BLAST databases (nt, nr)
/blastdb_custom    # Custom databases
/queries           # Query sequences
/fasta             # FASTA inputs
/results/validation # Results output
```

## Tool Descriptions

### 1. gget_blast

Remote BLAST search via gget against NCBI or Ensembl databases.

**Parameters:**
- `sequence` (str, required): Query sequence to search
- `program` (str, optional): BLAST program (blastn, blastp, blastx, tblastn, tblastx). Default: blastn
- `database` (str, optional): Database to search (nt, nr, refseq_rna, etc.). Default: nt
- `limit` (int, optional): Maximum number of hits to return. Default: 50
- `expect` (float, optional): E-value threshold. Default: 10.0
- `low_comp_filt` (bool, optional): Use low complexity filter. Default: false

**Returns:** JSON with BLAST results including alignments, scores, and annotations

**Example:**
```json
{
  "sequence": "ATCGATCGATCGATCGATCGATCGATCG",
  "program": "blastn",
  "database": "nt",
  "limit": 10,
  "expect": 0.001
}
```

### 2. gget_blat

Remote BLAT search for short exact matches via gget.

**Parameters:**
- `sequence` (str, required): Query sequence
- `seqtype` (str, optional): Sequence type (DNA, protein, translated RNA, translated DNA). Default: DNA
- `assembly` (str, optional): Genome assembly (human, mouse, etc.). Default: human

**Returns:** JSON with BLAT alignment results

**Example:**
```json
{
  "sequence": "ATCGATCGATCGATCG",
  "seqtype": "DNA",
  "assembly": "human"
}
```

### 3. blast_nt

Local BLAST search against custom or standard databases using NCBI BLAST+.

**Parameters:**
- `query_file` (str, required): Path to query FASTA file
- `database` (str, optional): Database name or path. Default: nt
- `program` (str, optional): BLAST program (blastn, blastp, etc.). Default: blastn
- `evalue` (float, optional): E-value threshold. Default: 0.001
- `max_targets` (int, optional): Maximum target sequences. Default: 50
- `perc_identity` (float, optional): Minimum percent identity. Default: 90.0
- `output_format` (str, optional): Output format (json, xml, tabular). Default: json

**Returns:** BLAST results in specified format

**Example:**
```json
{
  "query_file": "/queries/primers.fasta",
  "database": "nt",
  "program": "blastn",
  "evalue": 0.001,
  "max_targets": 100,
  "perc_identity": 95.0
}
```

### 4. in_silico_pcr

Simulate PCR amplification with primer pair against template sequences.

**Parameters:**
- `forward_primer` (str, required): Forward primer sequence (5' to 3')
- `reverse_primer` (str, required): Reverse primer sequence (5' to 3')
- `template_fasta` (str, required): FASTA file or string with template sequences
- `max_mismatches` (int, optional): Maximum mismatches per primer. Default: 2
- `min_product_size` (int, optional): Minimum amplicon size (bp). Default: 50
- `max_product_size` (int, optional): Maximum amplicon size (bp). Default: 500
- `allow_internal_mismatches` (bool, optional): Allow mismatches in primer body. Default: true

**Returns:** JSON with predicted amplicons, binding sites, and product information

**Example:**
```json
{
  "forward_primer": "ATCGATCGATCGATCG",
  "reverse_primer": "GCTAGCTAGCTAGCTA",
  "template_fasta": ">template1\\nATCGATCGATCGATCGNNNNNNNNTAGCTAGCTAGCTAGC",
  "max_mismatches": 1,
  "min_product_size": 100,
  "max_product_size": 300
}
```

### 5. assess_coverage

Calculate sensitivity and specificity of primers against target and non-target databases.

**Parameters:**
- `forward_primer` (str, required): Forward primer sequence
- `reverse_primer` (str, required): Reverse primer sequence
- `target_fasta` (str, required): FASTA file with target species sequences
- `offtarget_fasta` (str, optional): FASTA file with non-target species sequences
- `max_mismatches` (int, optional): Maximum mismatches allowed. Default: 2
- `min_amplicon_size` (int, optional): Minimum amplicon size. Default: 50
- `max_amplicon_size` (int, optional): Maximum amplicon size. Default: 500
- `sensitivity_threshold` (float, optional): Minimum acceptable sensitivity. Default: 0.95
- `specificity_threshold` (float, optional): Minimum acceptable specificity. Default: 0.95

**Returns:** JSON with sensitivity, specificity, coverage statistics, and assessment

**Example:**
```json
{
  "forward_primer": "ATCGATCGATCGATCG",
  "reverse_primer": "GCTAGCTAGCTAGCTA",
  "target_fasta": "/data/salmonella_coi.fasta",
  "offtarget_fasta": "/data/bacteria_coi.fasta",
  "max_mismatches": 1,
  "sensitivity_threshold": 0.95,
  "specificity_threshold": 0.98
}
```

### 6. search_pubmed

Search PubMed for literature related to primers, genes, or organisms.

**Parameters:**
- `query` (str, required): PubMed search query
- `max_results` (int, optional): Maximum results to return. Default: 20
- `sort` (str, optional): Sort order (relevance, pub_date). Default: relevance

**Returns:** JSON with PubMed articles including titles, abstracts, authors, citations

**Example:**
```json
{
  "query": "(Salmonella[Organism] AND COI[Gene]) AND primer",
  "max_results": 10,
  "sort": "relevance"
}
```

### 7. validate_primers_complete

Complete validation pipeline combining BLAST, in-silico PCR, coverage, and literature search.

**Parameters:**
- `forward_primer` (str, required): Forward primer sequence
- `reverse_primer` (str, required): Reverse primer sequence
- `target_organism` (str, required): Target organism name
- `target_fasta` (str, optional): Target sequences FASTA file
- `offtarget_fasta` (str, optional): Off-target sequences FASTA file
- `blast_target` (bool, optional): Run BLAST against target sequences. Default: true
- `blast_offtarget` (bool, optional): Run BLAST for off-target hits. Default: true
- `run_in_silico_pcr` (bool, optional): Run in-silico PCR simulation. Default: true
- `assess_coverage` (bool, optional): Calculate coverage statistics. Default: true
- `search_literature` (bool, optional): Search PubMed for evidence. Default: true
- `max_mismatches` (int, optional): Maximum mismatches for PCR. Default: 2
- `sensitivity_threshold` (float, optional): Minimum sensitivity. Default: 0.90
- `specificity_threshold` (float, optional): Minimum specificity. Default: 0.95

**Returns:** Comprehensive validation report with all analysis results and assessment

**Example:**
```json
{
  "forward_primer": "ATCGATCGATCGATCG",
  "reverse_primer": "GCTAGCTAGCTAGCTA",
  "target_organism": "Salmonella enterica",
  "target_fasta": "/data/salmonella_sequences.fasta",
  "blast_target": true,
  "blast_offtarget": true,
  "run_in_silico_pcr": true,
  "assess_coverage": true,
  "search_literature": true
}
```

## Usage Examples

### Example 1: Remote BLAST Search

```bash
# Using MCP Inspector
npx @modelcontextprotocol/inspector python3 validation_mcp_server.py

# Call gget_blast tool
{
  "sequence": "ATGGCTAGCTAGCTAGCTAGCTAGCTAGCTAG",
  "program": "blastn",
  "database": "nt",
  "limit": 20,
  "expect": 0.001
}
```

### Example 2: In-silico PCR Simulation

```python
# Using AG2 agent
result = await mcp_bridge.call_tool(
    "validation",
    "in_silico_pcr",
    {
        "forward_primer": "ATCGATCGATCGATCG",
        "reverse_primer": "GCTAGCTAGCTAGCTA",
        "template_fasta": """>seq1
ATCGATCGATCGATCGNNNNNNNNNNNNNNNNNNNNTAGCTAGCTAGCTAGC
>seq2
ATCGATCGATCGATCGNNNNNNNNNNTAGCTAGCTAGCTAGC""",
        "max_mismatches": 1,
        "min_product_size": 100,
        "max_product_size": 300
    }
)

print(f"Found {result['num_amplicons']} predicted amplicons")
for amp in result['products']:
    print(f"  {amp['size']}bp: {amp['sequence']}")
```

### Example 3: Complete Primer Validation

```python
# Using AG2 agent
validation_result = await mcp_bridge.call_tool(
    "validation",
    "validate_primers_complete",
    {
        "forward_primer": "ATCGATCGATCGATCG",
        "reverse_primer": "GCTAGCTAGCTAGCTA",
        "target_organism": "Salmonella enterica",
        "target_fasta": "/data/salmonella_coi.fasta",
        "offtarget_fasta": "/data/bacteria_coi.fasta",
        "blast_target": True,
        "blast_offtarget": True,
        "run_in_silico_pcr": True,
        "assess_coverage": True,
        "search_literature": True,
        "max_mismatches": 1,
        "sensitivity_threshold": 0.95,
        "specificity_threshold": 0.98
    }
)

print(f"Validation: {validation_result['validation_summary']['overall_assessment']}")
print(f"Sensitivity: {validation_result['coverage']['sensitivity']:.2%}")
print(f"Specificity: {validation_result['coverage']['specificity']:.2%}")
```

### Example 4: Local BLAST with Custom Database

```bash
# Create custom database from FASTA
docker exec ndiag-validation-server makeblastdb \
  -in /queries/my_sequences.fasta \
  -dbtype nucl \
  -out /blastdb_custom/my_db

# Use custom database
{
  "query_file": "/queries/primers.fasta",
  "database": "/blastdb_custom/my_db",
  "program": "blastn",
  "evalue": 0.001,
  "max_targets": 100
}
```

## Testing

### Unit Tests

```bash
# Run pytest suite (411 lines of tests)
cd mcp_servers/validation_server
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_validation_server.py::TestValidationServer::test_in_silico_pcr_success -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Integration Testing

```bash
# Automated test script (pytest + Docker + MCP Inspector)
./test_mcp_server.sh validation

# This will:
# 1. Run unit tests with pytest
# 2. Build Docker container
# 3. Start container and verify health
# 4. Launch MCP Inspector for interactive testing
# 5. Open browser at http://localhost:6274
```

### Manual Testing with MCP Inspector

```bash
cd mcp_servers/validation_server

# Start Inspector
npx @modelcontextprotocol/inspector python3 validation_mcp_server.py

# Open http://localhost:6274 in browser
# 1. Click "Connect" to initialize MCP connection
# 2. Browse available tools in left panel
# 3. Select "gget_blast" or other tool
# 4. Fill in parameters in right panel
# 5. Click "Run" to execute
# 6. View results in output panel
```

## Integration with AG2

The validation server integrates with AG2 multi-agent systems for natural language primer validation.

### Bridge Configuration

Add to `autogen_app/autogen_mcp_bridge.py`:

```python
MCP_SERVERS = {
    "validation": {
        "container": "ndiag-validation-server",
        "script": "/app/validation_mcp_server.py",
        "description": "Primer validation, BLAST, in-silico PCR, coverage assessment, literature search"
    }
}
```

### Agent Creation

```python
from autogen import AssistantAgent

validation_agent = AssistantAgent(
    name="ValidationAgent",
    system_message="""You are a primer validation specialist. You validate designed primers using:
    - BLAST searches to check specificity
    - In-silico PCR to predict amplicons
    - Coverage assessment for sensitivity/specificity
    - PubMed searches for supporting literature

    Use the validation MCP server tools to perform comprehensive validation.
    Report validation results with sensitivity, specificity, and recommendations.""",
    llm_config={
        "config_list": config_list,
        "temperature": 0
    }
)

# Register validation tools
validation_tools = await mcp_bridge.get_tools("validation")
for tool in validation_tools:
    register_function(
        tool["function"],
        caller=validation_agent,
        executor=user_proxy
    )
```

### Multi-Agent Workflow

```python
# Example: Analyst triggers validation after primer design
analyst_agent.initiate_chat(
    validation_agent,
    message=f"""Please validate the following primers for {target_organism}:
    Forward: {forward_primer}
    Reverse: {reverse_primer}

    Check specificity against off-target species and assess coverage.
    """
)
```

## Troubleshooting

### Common Issues

**1. NCBI Email Warning**

```
WARNING: NCBI_EMAIL not set properly
```

**Solution:** Set a valid email in `.env` to comply with NCBI policies:
```bash
NCBI_EMAIL=your.email@example.com
```

**2. BLAST Database Not Found**

```
ERROR: BLAST database 'nt' not found
```

**Solution:** Either use remote BLAST (default) or download local databases:
```bash
# Option 1: Use remote BLAST (no setup needed)
# Just use gget_blast tool

# Option 2: Download local databases
update_blastdb.pl --decompress nt
# Mount in docker-compose.yml
```

**3. Rate Limiting from NCBI**

```
ERROR: HTTP 429 - Too Many Requests
```

**Solution:** Get an NCBI API key (increases rate limit from 3 to 10 req/sec):
```bash
# Get key from: https://www.ncbi.nlm.nih.gov/account/settings/
NCBI_API_KEY=your_api_key_here
```

**4. Container Won't Start**

```bash
# Check logs
docker-compose logs validation-server

# Check health
docker inspect --format='{{.State.Health.Status}}' ndiag-validation-server

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**5. MCP Inspector Connection Issues**

```bash
# Check if container is running
docker ps | grep ndiag-validation-server

# Test server directly
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | \
  docker exec -i ndiag-validation-server python3 /app/validation_mcp_server.py

# Check for port conflicts
netstat -tln | grep 6274
```

### Debug Mode

Enable detailed logging:

```bash
# In .env or docker-compose.yml
LOG_LEVEL=DEBUG

# Restart container
docker-compose restart validation-server

# View logs
docker-compose logs -f validation-server
```

## Performance Considerations

### Remote vs Local BLAST

**Remote BLAST (via gget):**
- ✅ No setup required
- ✅ Always up-to-date databases
- ✅ No storage requirements
- ❌ Slower (network latency)
- ❌ Rate limited (3-10 requests/sec)
- ❌ Requires internet connection

**Local BLAST (NCBI BLAST+):**
- ✅ Fast (no network latency)
- ✅ No rate limits
- ✅ Works offline
- ✅ Custom databases supported
- ❌ Requires ~300-400GB storage per database
- ❌ Manual database updates needed
- ❌ Setup complexity

**Recommendation:** Use remote BLAST for development and low-volume work. Use local BLAST for production or high-throughput validation.

### Rate Limiting Strategy

The server implements automatic rate limiting for NCBI API compliance:

```python
# Without API key: 3 requests/sec (0.34s delay)
# With API key: 10 requests/sec (0.11s delay)

# Automatically applied to:
# - gget_blast calls
# - search_pubmed calls
# - Any NCBI Entrez queries
```

### Optimization Tips

1. **Batch Queries**: Use `blast_nt` with multi-sequence FASTA files instead of individual queries
2. **Adjust E-value**: Higher E-values (e.g., 10.0) return more hits but slower
3. **Limit Results**: Use `limit` parameter to reduce result parsing time
4. **Cache Results**: Store BLAST results in `/results/validation` for reuse
5. **Use Local Databases**: For high-throughput, invest in local BLAST setup

## Directory Structure

```
mcp_servers/validation_server/
├── validation_mcp_server.py  # Main MCP server (1,229 lines, 7 tools)
├── config.py                  # Configuration management (165 lines)
├── requirements.txt           # Python dependencies (8 packages)
├── Dockerfile                 # Container with NCBI BLAST+ (72 lines)
├── docker-compose.yml         # Deployment configuration (52 lines)
├── entrypoint.sh             # Container startup script
├── .env.template             # Configuration template (64 lines)
├── .gitignore                # Git exclusions
├── mcp-server.json           # MCP manifest
├── README.md                 # This file
├── tests/
│   ├── __init__.py
│   └── test_validation_server.py  # Unit tests (411 lines)
└── results/                  # Output directory (mounted volume)
```

## Dependencies

### Python Packages

```
mcp>=0.9.0              # MCP SDK for tool exposure
gget>=0.28.0            # Remote BLAST/BLAT via gget
biopython>=1.81         # BioPython for Entrez (PubMed)
aiofiles>=23.0.0        # Async file I/O
```

### System Tools

```
ncbi-blast+ 2.12.0+     # NCBI BLAST+ suite (blastn, blastp, blastx, etc.)
python3.10+             # Python runtime
```

## References

### NCBI Resources

- [NCBI BLAST+ Documentation](https://github.com/ncbi/blast_plus_docs)
- [BLAST Database Download](https://ftp.ncbi.nlm.nih.gov/blast/db/)
- [NCBI API Usage Guidelines](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)

### Tools and Libraries

- [gget Documentation](https://pachterlab.github.io/gget/)
- [BioPython Tutorial](https://biopython.org/wiki/Documentation)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [AG2 (AutoGen) Documentation](https://microsoft.github.io/autogen/)

### Scientific Background

- Bushnell B. (2014). BBMap: A Fast, Accurate, Splice-Aware Aligner.
- Altschul SF, et al. (1990). "Basic local alignment search tool." J Mol Biol.
- Kent WJ. (2002). "BLAT—The BLAST-Like Alignment Tool." Genome Res.

## License

Part of the mdk_mcp project. See repository root for license information.

## Support

For issues, questions, or contributions:
- Project repository: https://github.com/yourusername/mdk_mcp
- MCP documentation: https://modelcontextprotocol.io/
- NCBI BLAST+ docs: https://github.com/ncbi/blast_plus_docs

---

**Phase 5 Implementation**: Validation & Literature Server
**Status**: ✅ Complete (7 tools, 1,229 lines of code, comprehensive testing)
**Next Phase**: Phase 6 - Export & Provenance Server
