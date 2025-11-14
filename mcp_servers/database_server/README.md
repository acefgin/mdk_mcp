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
- `get_sequences` - Retrieve sequences from multiple databases **with advanced filtering**
- `extract_sequence_columns` - Extract specific columns (Id, Accession, Title, Organism, Length, Database, Marker, Quality Score, Country, Create Date, etc.) with multiple output formats (JSON, CSV, TSV, Table)
- `get_taxonomy` - Get taxonomic information
- `gget_search` - Search Ensembl genes
- `search_sra_studies` - Search SRA/BioProject data

### Advanced Filtering (NEW!)

The `get_sequences` tool now supports comprehensive filtering options:

| Filter | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `min_length` | integer | Minimum sequence length in base pairs | `600`, `1400`, `15000` |
| `max_length` | integer | Maximum sequence length in base pairs | `700`, `2000`, `20000` |
| `completeness` | string | Sequence completeness level | `complete`, `partial`, `any` |
| `upload_date_start` | string | Start date for upload/submission | `2020-01-01`, `2023/06/15` |
| `upload_date_end` | string | End date for upload/submission | `2024-12-31`, `2024/11/14` |
| `country` | string | Filter by country/location | `Norway`, `USA`, `Japan` |
| `has_geo_location` | boolean | Require geographic location data | `true`, `false` |
| `quality_filter` | string | Sequence quality threshold | `high` (RefSeq), `medium`, `any` |
| `exclude_predicted` | boolean | Exclude predicted/inferred sequences | `true`, `false` |
| `exclude_environmental` | boolean | Exclude environmental/uncultured samples | `true`, `false` |

**Filter Support by Database:**
- **NCBI**: Full support (server-side + post-retrieval filtering)
- **BOLD**: Partial support (country via API, others post-retrieval)
- **gget/Ensembl**: Post-retrieval filtering only
- **SILVA/UNITE**: Post-retrieval filtering when implemented

## Quick Start

```bash
# Build and run the container
docker build -t ndiag-database-server:latest .
docker run -d --name ndiag-database-server -i ndiag-database-server:latest

# Or use docker-compose
cp env.template .env  # Add NCBI_API_KEY if available
docker-compose up --build
```

### Basic sequence retrieval

```json
# Get sequences without filters
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Salmo salar",
    "region": "COI",
    "source": "ncbi",
    "max_results": 10
  }
}
```

### Advanced filtering examples

```json
# Example 1: Filter by sequence length (COI genes typically 600-700 bp)
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Salmo salar",
    "region": "COI",
    "source": "ncbi",
    "max_results": 50,
    "filters": {
      "min_length": 600,
      "max_length": 700,
      "completeness": "complete"
    }
  }
}

# Example 2: Filter by completeness and quality
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Homo sapiens",
    "region": "whole",
    "source": "ncbi",
    "max_results": 10,
    "filters": {
      "completeness": "complete",
      "quality_filter": "high",
      "exclude_predicted": true
    }
  }
}

# Example 3: Filter by date and location
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Thunnus thynnus",
    "region": "COI",
    "source": "ncbi",
    "max_results": 100,
    "filters": {
      "upload_date_start": "2020-01-01",
      "upload_date_end": "2024-12-31",
      "country": "Norway",
      "has_geo_location": true
    }
  }
}

# Example 4: Exclude environmental samples
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Bacteria",
    "region": "16S",
    "source": "ncbi",
    "max_results": 50,
    "filters": {
      "min_length": 1400,
      "exclude_environmental": true,
      "quality_filter": "medium"
    }
  }
}

# Example 5: Complete mitochondrial genomes only
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Salmonidae",
    "region": "mitogenome",
    "source": "ncbi",
    "max_results": 20,
    "filters": {
      "completeness": "complete",
      "min_length": 15000,
      "quality_filter": "high"
    }
  }
}
```

### Extract and format sequence metadata

```json
# Step 1: Get filtered sequences
{
  "tool": "get_sequences",
  "arguments": {
    "taxon": "Salmo salar",
    "region": "COI",
    "source": "ncbi",
    "max_results": 10,
    "format": "genbank",
    "filters": {
      "min_length": 600,
      "has_geo_location": true
    }
  }
}

# Step 2: Extract specific columns
{
  "tool": "extract_sequence_columns",
  "arguments": {
    "sequence_data": "<result_from_step_1>",
    "columns": ["Id", "Accession", "Organism", "Length", "Country", "Collection Date", "Marker"],
    "output_format": "csv"
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
