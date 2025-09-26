# Database MCP Server

**ndiag-database-server** provides unified access to multiple biological databases through the Model Context Protocol (MCP).

## Supported Databases

- **NCBI** - Nucleotide and Gene databases
- **BOLD** - Barcode of Life Data System (COI sequences)
- **SILVA** - Curated ribosomal RNA sequences
- **UNITE** - Fungal ITS sequences
- **Ensembl** - Gene information via gget integration

## Available MCP Tools

### Core Tools
- `get_sequences` - Retrieve sequences from multiple databases
- `extract_sequence_columns` - **NEW**: Extract specific columns (Id, Accession, Title, Organism, Length, Database, Marker, Quality Score, Country, Create Date) with multiple output formats (JSON, CSV, TSV, Table)
- `get_taxonomy` - Get taxonomic information
- `gget_search` - Search Ensembl genes
- `search_sra_studies` - Search SRA/BioProject data

## Quick Start

```bash
# Build and run the container
docker build -t ndiag-database-server:latest .
docker run -d --name ndiag-database-server -i ndiag-database-server:latest

# Or use docker-compose
cp env.template .env  # Add NCBI_API_KEY if available
docker-compose up --build
```

### Get sequences and extract columns

```json
# Step 1: Get sequences
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Salmo salar",
    "region": "COI",
    "source": "ncbi",
    "max_results": 10
  }
}

# Step 2: Extract specific columns
{
  "tool": "extract_sequence_columns",
  "arguments": {
    "sequence_data": "<result_from_step_1>",
    "columns": ["Id", "Accession", "Title", "Organism", "Length", "Database", "Marker"],
    "output_format": "json"
  }
}
```

### Search Ensembl genes

```json
{
  "tool": "gget_search",
  "arguments": {
    "searchwords": ["COI", "cytochrome oxidase"],
    "species": "homo_sapiens"
  }
}
```

## Configuration

Optional environment variables:
- `NCBI_API_KEY` - For higher NCBI rate limits
- `LOG_LEVEL` - Logging level (default: INFO)

## Frontend Integration

Use with the Streamlit frontend for enhanced multi-database search with interactive column extraction and download capabilities.

## Architecture

Built with MCP Framework, gget, BioPython, and pysradb for unified biological database access.
