#!/usr/bin/env python3
"""
Database MCP Server for neglected-diagnostics project.

This server provides unified access to multiple biological databases including:
- NCBI (via gget and direct API)
- BOLD Systems
- SILVA
- UNITE
- SRA/BioProject data
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Union, Sequence
import traceback

import gget
import pandas as pd
import requests
from Bio import SeqIO, Entrez
from pysradb import SRAweb

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None

try:
    import boto3
except ImportError:
    boto3 = None

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure NCBI Entrez
if Config.NCBI_API_KEY:
    Entrez.api_key = Config.NCBI_API_KEY
Entrez.email = "ndiag-server@example.com"  # Required by NCBI

# Create the server instance
server = Server("ndiag-database-server")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List all available MCP tools."""
    return [
        # Core sequence retrieval
        types.Tool(
            name="get_sequences",
            description="Retrieve sequences from multiple databases",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon": {"type": "string", "description": "Taxon name or ID"},
                    "region": {
                        "type": "string", 
                        "enum": ["COI", "16S", "ITS", "mitogenome", "whole"],
                        "description": "Target genomic region"
                    },
                    "source": {
                        "type": "string",
                        "enum": ["gget", "ncbi", "bold", "silva", "unite"],
                        "default": "gget",
                        "description": "Database source"
                    },
                    "max_results": {"type": "integer", "default": 100},
                    "format": {
                        "type": "string",
                        "enum": ["fasta", "genbank"],
                        "default": "fasta"
                    }
                },
                "required": ["taxon"]
            }
        ),
        
        # gget tools
        types.Tool(
            name="gget_ref",
            description="Get reference genome information from Ensembl",
            inputSchema={
                "type": "object",
                "properties": {
                    "species": {"type": "string", "description": "Species name (e.g., 'homo_sapiens')"},
                    "which": {
                        "type": "string",
                        "enum": ["all", "gtf", "fasta"],
                        "default": "all"
                    },
                    "release": {"type": "integer", "description": "Ensembl release number"}
                },
                "required": ["species"]
            }
        ),
        
        types.Tool(
            name="gget_search",
            description="Search for genes in Ensembl database",
            inputSchema={
                "type": "object",
                "properties": {
                    "searchwords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search terms"
                    },
                    "species": {"type": "string", "description": "Species name"},
                    "id_type": {
                        "type": "string",
                        "enum": ["gene", "transcript"],
                        "default": "gene"
                    },
                    "andor": {
                        "type": "string",
                        "enum": ["and", "or"],
                        "default": "or"
                    }
                },
                "required": ["searchwords", "species"]
            }
        ),
        
        types.Tool(
            name="gget_info",
            description="Get detailed information about Ensembl IDs",
            inputSchema={
                "type": "object",
                "properties": {
                    "ens_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ensembl IDs"
                    },
                    "expand": {"type": "boolean", "default": False}
                },
                "required": ["ens_ids"]
            }
        ),
        
        types.Tool(
            name="gget_seq",
            description="Get sequences from Ensembl IDs",
            inputSchema={
                "type": "object",
                "properties": {
                    "ens_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ensembl IDs"
                    },
                    "translate": {"type": "boolean", "default": False},
                    "seqtype": {
                        "type": "string",
                        "enum": ["genomic", "transcript", "protein"],
                        "default": "transcript"
                    }
                },
                "required": ["ens_ids"]
            }
        ),
        
        # Taxonomic tools
        types.Tool(
            name="get_neighbors",
            description="Find taxonomic neighbors",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon": {"type": "string", "description": "Taxon name"},
                    "rank": {
                        "type": "string",
                        "enum": ["species", "genus", "family"],
                        "description": "Taxonomic rank"
                    },
                    "distance": {"type": "integer", "default": 1},
                    "common_misIDs": {"type": "boolean", "default": False}
                },
                "required": ["taxon", "rank"]
            }
        ),
        
        types.Tool(
            name="get_taxonomy",
            description="Get taxonomic information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Taxon name or accession"}
                },
                "required": ["query"]
            }
        ),
        
        # SRA/BioProject tools
        types.Tool(
            name="search_sra_studies",
            description="Search SRA studies and BioProjects",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Free text search query"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "organism": {"type": "string"},
                            "library_strategy": {
                                "type": "string",
                                "enum": ["AMPLICON", "RNA-Seq", "WGS", "METAGENOMIC"]
                            },
                            "platform": {
                                "type": "string",
                                "enum": ["ILLUMINA", "PACBIO", "OXFORD_NANOPORE"]
                            },
                            "submission_date_start": {"type": "string", "format": "date"},
                            "submission_date_end": {"type": "string", "format": "date"},
                            "min_read_length": {"type": "integer"},
                            "max_results": {"type": "integer", "default": 100}
                        }
                    },
                    "search_method": {
                        "type": "string",
                        "enum": ["entrez", "cloud_sql"],
                        "default": "entrez"
                    }
                },
                "required": ["query"]
            }
        ),
        
        types.Tool(
            name="get_sra_runinfo",
            description="Get detailed run information for SRA studies",
            inputSchema={
                "type": "object",
                "properties": {
                    "study_accession": {"type": "string", "description": "BioProject/SRA Study ID"},
                    "include_sample_metadata": {"type": "boolean", "default": True},
                    "format": {
                        "type": "string",
                        "enum": ["json", "tsv", "csv"],
                        "default": "json"
                    }
                },
                "required": ["study_accession"]
            }
        ),
        
        types.Tool(
            name="search_sra_cloud",
            description="Search SRA using cloud SQL (BigQuery/Athena)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_sql": {"type": "string", "description": "SQL query for BigQuery/Athena SRA tables"},
                    "platform": {
                        "type": "string",
                        "enum": ["bigquery", "athena"],
                        "default": "bigquery"
                    },
                    "max_rows": {"type": "integer", "default": 1000}
                },
                "required": ["query_sql"]
            }
        ),
        
        types.Tool(
            name="extract_sequence_columns",
            description="Extract specific columns from sequence records obtained from MCP server. Enhanced to extract comprehensive metadata from GenBank records including geographic location, collection dates, authors, and more.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequence_data": {
                        "type": "string", 
                        "description": "Raw sequence data from any MCP tool (JSON, FASTA, or GenBank format). GenBank format provides the most comprehensive metadata."
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["Id", "Accession", "Title", "Organism", "Length", "Database", "Marker", "Quality Score", "Country", "Create Date", "Collection Date", "Geographic Location", "Isolate", "Sequencing Technology", "Taxonomic Classification", "Authors", "Institution", "Gene", "Product", "Protein ID", "Taxon ID"],
                        "description": "List of columns to extract. Available columns: Id, Accession, Title, Organism, Length, Database, Marker, Quality Score, Country, Create Date, Collection Date, Geographic Location, Isolate, Sequencing Technology, Taxonomic Classification, Authors, Institution, Gene, Product, Protein ID, Taxon ID"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "csv", "tsv", "table"],
                        "default": "json",
                        "description": "Output format for extracted data"
                    }
                },
                "required": ["sequence_data"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        
        if name == "get_sequences":
            result = await get_sequences(**arguments)
        elif name == "gget_ref":
            result = await gget_ref(**arguments)
        elif name == "gget_search":
            result = await gget_search(**arguments)
        elif name == "gget_info":
            result = await gget_info(**arguments)
        elif name == "gget_seq":
            result = await gget_seq(**arguments)
        elif name == "get_neighbors":
            result = await get_neighbors(**arguments)
        elif name == "get_taxonomy":
            result = await get_taxonomy(**arguments)
        elif name == "search_sra_studies":
            result = await search_sra_studies(**arguments)
        elif name == "get_sra_runinfo":
            result = await get_sra_runinfo(**arguments)
        elif name == "search_sra_cloud":
            result = await search_sra_cloud(**arguments)
        elif name == "extract_sequence_columns":
            result = await extract_sequence_columns(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [types.TextContent(type="text", text=str(result))]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        logger.error(traceback.format_exc())
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

# Tool implementation functions
async def get_sequences(
    taxon: str,
    region: str = "COI",
    source: str = "gget",
    max_results: int = 100,
    format: str = "fasta"
) -> str:
    """Unified sequence retrieval from multiple sources."""
    
    max_results = min(max_results, Config.MAX_RESULTS_LIMIT)
    
    try:
        if source == "gget":
            # Use gget for Ensembl data
            search_terms = get_search_terms_for_region(region)
            # gget.search expects a string, so use the first search term
            search_term = search_terms[0] if search_terms else region
            search_result = gget.search(search_term, species=taxon.lower().replace(" ", "_"))
            
            if search_result.empty:
                return f"No results found for {taxon} {region} in Ensembl"
            
            # Get sequences for found IDs
            ens_ids = search_result.index.tolist()[:max_results]
            sequences = gget.seq(ens_ids, translate=False)
            
            result = format_sequences(sequences, format)
            
        elif source == "ncbi":
            result = await get_ncbi_sequences(taxon, region, max_results, format)
        elif source == "bold":
            result = await get_bold_sequences(taxon, region, max_results, format)
        elif source == "silva":
            result = await get_silva_sequences(taxon, region, max_results, format)
        elif source == "unite":
            result = await get_unite_sequences(taxon, region, max_results, format)
        else:
            raise ValueError(f"Unsupported source: {source}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_sequences: {str(e)}")
        return f"Error retrieving sequences: {str(e)}"

def get_search_terms_for_region(region: str) -> List[str]:
    """Get appropriate search terms for genomic regions."""
    region_terms = {
        "COI": ["COI", "cytochrome oxidase", "COX1"],
        "16S": ["16S", "ribosomal RNA", "rRNA"],
        "ITS": ["ITS", "internal transcribed spacer"],
        "mitogenome": ["mitochondrial", "mitogenome"],
        "whole": ["genome", "complete"]
    }
    return region_terms.get(region, [region])

async def gget_ref(
    species: str,
    which: str = "all",
    release: Optional[int] = None
) -> str:
    """Get reference genome information."""
    try:
        result = gget.ref(species=species, which=which, release=release)
        return str(result)
    except Exception as e:
        return f"Error in gget_ref: {str(e)}"

async def gget_search(
    searchwords: List[str],
    species: str,
    id_type: str = "gene",
    andor: str = "or"
) -> str:
    """Search Ensembl database."""
    try:
        result = gget.search(searchwords, species=species, id_type=id_type, andor=andor)
        return result.to_json(orient="records", indent=2)
    except Exception as e:
        return f"Error in gget_search: {str(e)}"

async def gget_info(
    ens_ids: List[str],
    expand: bool = False
) -> str:
    """Get detailed information about Ensembl IDs."""
    try:
        result = gget.info(ens_ids, expand=expand)
        return result.to_json(orient="records", indent=2)
    except Exception as e:
        return f"Error in gget_info: {str(e)}"

async def gget_seq(
    ens_ids: List[str],
    translate: bool = False,
    seqtype: str = "transcript"
) -> str:
    """Get sequences from Ensembl IDs."""
    try:
        result = gget.seq(ens_ids, translate=translate, seqtype=seqtype)
        return str(result)
    except Exception as e:
        return f"Error in gget_seq: {str(e)}"

async def get_neighbors(
    taxon: str,
    rank: str,
    distance: int = 1,
    common_misIDs: bool = False
) -> str:
    """Find taxonomic neighbors."""
    try:
        # Use NCBI taxonomy database
        search_handle = Entrez.esearch(db="taxonomy", term=taxon)
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        if not search_results["IdList"]:
            return f"No taxonomy found for {taxon}"
        
        tax_id = search_results["IdList"][0]
        
        # Get taxonomic information
        fetch_handle = Entrez.efetch(db="taxonomy", id=tax_id, retmode="xml")
        records = Entrez.read(fetch_handle)
        fetch_handle.close()
        
        result = {"taxon": taxon, "tax_id": tax_id, "neighbors": []}
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return f"Error in get_neighbors: {str(e)}"

async def get_taxonomy(query: str) -> str:
    """Get taxonomic information."""
    try:
        search_handle = Entrez.esearch(db="taxonomy", term=query)
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        if not search_results["IdList"]:
            return f"No taxonomy found for {query}"
        
        tax_id = search_results["IdList"][0]
        
        fetch_handle = Entrez.efetch(db="taxonomy", id=tax_id, retmode="xml")
        records = Entrez.read(fetch_handle)
        fetch_handle.close()
        
        return json.dumps(records, indent=2, default=str)
        
    except Exception as e:
        return f"Error in get_taxonomy: {str(e)}"

async def search_sra_studies(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    search_method: str = "entrez"
) -> str:
    """Search SRA studies."""
    try:
        if search_method == "entrez":
            # Build search query
            search_query = query
            if filters:
                if filters.get("organism"):
                    search_query += f' AND "{filters["organism"]}"[Organism]'
                if filters.get("library_strategy"):
                    search_query += f' AND "{filters["library_strategy"]}"[Strategy]'
            
            search_handle = Entrez.esearch(
                db="sra",
                term=search_query,
                retmax=filters.get("max_results", 100) if filters else 100
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            return json.dumps(search_results, indent=2)
        
        elif search_method == "cloud_sql":
            # Use pysradb for more advanced queries
            db = SRAweb()
            df = db.search_sra(query)
            return df.to_json(orient="records", indent=2)
            
    except Exception as e:
        return f"Error in search_sra_studies: {str(e)}"

async def get_sra_runinfo(
    study_accession: str,
    include_sample_metadata: bool = True,
    format: str = "json"
) -> str:
    """Get SRA run information."""
    try:
        db = SRAweb()
        df = db.sra_metadata(study_accession, detailed=include_sample_metadata)
        
        if format == "json":
            result = df.to_json(orient="records", indent=2)
        elif format == "csv":
            result = df.to_csv(index=False)
        elif format == "tsv":
            result = df.to_csv(index=False, sep="\t")
        else:
            result = str(df)
        
        return result
        
    except Exception as e:
        return f"Error in get_sra_runinfo: {str(e)}"

async def search_sra_cloud(
    query_sql: str,
    platform: str = "bigquery",
    max_rows: int = 1000
) -> str:
    """Search SRA using cloud SQL."""
    try:
        if platform == "bigquery" and bigquery and Config.GOOGLE_APPLICATION_CREDENTIALS:
            client = bigquery.Client()
            job_config = bigquery.QueryJobConfig(maximum_bytes_billed=10**9)  # 1GB limit
            
            query_job = client.query(query_sql, job_config=job_config)
            results = query_job.result(max_results=max_rows)
            
            df = results.to_dataframe()
            return df.to_json(orient="records", indent=2)
        
        elif platform == "athena":
            # AWS Athena implementation would go here
            return "Athena support not yet implemented"
        
        else:
            return "Cloud SQL platform not configured"
            
    except Exception as e:
        return f"Error in search_sra_cloud: {str(e)}"

async def get_ncbi_sequences(
    taxon: str,
    region: str,
    max_results: int,
    format: str
) -> str:
    """Get sequences from NCBI."""
    try:
        # Build search query based on region
        region_terms = {
            "COI": "COI OR cytochrome oxidase I OR COX1",
            "16S": "16S ribosomal RNA OR 16S rRNA",
            "ITS": "internal transcribed spacer OR ITS",
            "mitogenome": "mitochondrion complete genome",
            "whole": "complete genome"
        }
        
        search_term = f'"{taxon}"[Organism] AND ({region_terms.get(region, region)})'
        
        search_handle = Entrez.esearch(
            db="nucleotide",
            term=search_term,
            retmax=max_results
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        if not search_results["IdList"]:
            return f"No sequences found for {taxon} {region} in NCBI"
        
        # Fetch sequences
        fetch_handle = Entrez.efetch(
            db="nucleotide",
            id=search_results["IdList"],
            rettype="fasta" if format == "fasta" else "gb",
            retmode="text"
        )
        sequences = fetch_handle.read()
        fetch_handle.close()
        
        return sequences
        
    except Exception as e:
        return f"Error retrieving NCBI sequences: {str(e)}"

async def get_bold_sequences(
    taxon: str,
    region: str,
    max_results: int,
    format: str
) -> str:
    """Get sequences from BOLD Systems."""
    try:
        # BOLD API call
        url = f"{Config.BOLD_BASE_URL}/sequence"
        params = {
            "taxon": taxon,
            "marker": region,
            "format": "fasta"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        return response.text
        
    except Exception as e:
        return f"Error retrieving BOLD sequences: {str(e)}"

async def get_silva_sequences(
    taxon: str,
    region: str,
    max_results: int,
    format: str
) -> str:
    """Get sequences from SILVA database."""
    try:
        # This is a placeholder - actual SILVA API integration would be more complex
        return f"SILVA integration for {taxon} {region} not yet fully implemented"
        
    except Exception as e:
        return f"Error retrieving SILVA sequences: {str(e)}"

async def get_unite_sequences(
    taxon: str,
    region: str,
    max_results: int,
    format: str
) -> str:
    """Get sequences from UNITE database."""
    try:
        # This is a placeholder - actual UNITE API integration would be more complex
        return f"UNITE integration for {taxon} {region} not yet fully implemented"
        
    except Exception as e:
        return f"Error retrieving UNITE sequences: {str(e)}"

def format_sequences(sequences: Any, format: str) -> str:
    """Format sequences for output."""
    try:
        if format == "fasta":
            if isinstance(sequences, dict):
                fasta_lines = []
                for seq_id, seq in sequences.items():
                    fasta_lines.append(f">{seq_id}")
                    fasta_lines.append(str(seq))
                return "\n".join(fasta_lines)
            else:
                return str(sequences)
        else:
            return str(sequences)
    except Exception as e:
        return f"Error formatting sequences: {str(e)}"

async def extract_sequence_columns(
    sequence_data: str,
    columns: List[str] = ["Id", "Accession", "Title", "Organism", "Length", "Database", "Marker", "Quality Score", "Country", "Create Date", "Collection Date", "Geographic Location", "Isolate", "Sequencing Technology", "Taxonomic Classification", "Authors", "Institution", "Gene", "Product", "Protein ID", "Taxon ID"],
    output_format: str = "json"
) -> str:
    """Extract specific columns from sequence records."""
    try:
        extracted_records = []
        
        # Try to parse as JSON first
        try:
            data = json.loads(sequence_data)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = [data]
            else:
                records = []
        except json.JSONDecodeError:
            # Try to parse as FASTA or GenBank
            records = parse_sequence_text(sequence_data)
        
        # Extract requested columns from each record
        for record in records:
            extracted_record = {}
            
            for column in columns:
                value = extract_column_value(record, column, sequence_data)
                extracted_record[column] = value
            
            extracted_records.append(extracted_record)
        
        # Format output
        if output_format == "json":
            return json.dumps(extracted_records, indent=2)
        elif output_format == "csv":
            return format_as_csv(extracted_records, columns)
        elif output_format == "tsv":
            return format_as_tsv(extracted_records, columns)
        elif output_format == "table":
            return format_as_table(extracted_records, columns)
        else:
            return json.dumps(extracted_records, indent=2)
            
    except Exception as e:
        logger.error(f"Error in extract_sequence_columns: {str(e)}")
        return f"Error extracting columns: {str(e)}"

def parse_sequence_text(text: str) -> List[Dict[str, Any]]:
    """Parse FASTA or GenBank formatted text into records."""
    records = []
    
    # Try FASTA format first
    if text.startswith(">"):
        current_record = {}
        current_seq = []
        
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith(">"):
                # Save previous record
                if current_record:
                    current_record["sequence"] = "".join(current_seq)
                    current_record["Length"] = len(current_record["sequence"])
                    records.append(current_record)
                
                # Start new record
                header = line[1:]  # Remove >
                current_record = parse_fasta_header(header)
                current_seq = []
            elif line and not line.startswith(">"):
                current_seq.append(line)
        
        # Add last record
        if current_record:
            current_record["sequence"] = "".join(current_seq)
            current_record["Length"] = len(current_record["sequence"])
            records.append(current_record)
    
    # Try GenBank format
    elif "LOCUS" in text or "ACCESSION" in text:
        records = parse_genbank_text(text)
    
    return records

def parse_fasta_header(header: str) -> Dict[str, Any]:
    """Parse FASTA header to extract metadata."""
    record = {
        "Title": header,
        "Id": "",
        "Accession": "",
        "Organism": "",
        "Length": 0,
        "Database": "NCBI",  # Default for FASTA from NCBI
        "Marker": "",
        "Quality Score": "",
        "Country": "",
        "Create Date": ""
    }
    
    # Try to extract accession from common formats
    parts = header.split()
    if parts:
        # First part often contains ID/accession
        first_part = parts[0]
        record["Id"] = first_part
        record["Accession"] = first_part
        
        # Look for versioned accession patterns (e.g., PV570336.1)
        for part in parts:
            if "." in part and len(part) > 3:  # Likely versioned accession
                record["Accession"] = part
                record["Id"] = part
                break
    
    # Extract organism from title
    header_lower = header.lower()
    
    # Look for organism in brackets [Salmo salar]
    if "[" in header and "]" in header:
        start = header.rfind("[") + 1
        end = header.rfind("]")
        if start < end:
            record["Organism"] = header[start:end]
    else:
        # Try to extract organism from common patterns
        # Look for species names (Genus species pattern)
        import re
        species_pattern = r'\b([A-Z][a-z]+ [a-z]+)\b'
        species_match = re.search(species_pattern, header)
        if species_match:
            record["Organism"] = species_match.group(1)
    
    # Extract marker information from title
    if any(term in header_lower for term in ['coi', 'cytochrome oxidase', 'cox1', 'cytochrome c oxidase']):
        record["Marker"] = "COI"
    elif any(term in header_lower for term in ['16s', '16s ribosomal', '16s rrna']):
        record["Marker"] = "16S"
    elif any(term in header_lower for term in ['18s', '18s ribosomal', '18s rrna']):
        record["Marker"] = "18S"
    elif 'its' in header_lower:
        record["Marker"] = "ITS"
    elif 'rbcl' in header_lower:
        record["Marker"] = "rbcL"
    elif 'matk' in header_lower:
        record["Marker"] = "matK"
    
    # Try to extract country/location information
    countries = ['usa', 'canada', 'norway', 'japan', 'china', 'australia', 'brazil', 'chile', 'scotland', 'ireland', 'france', 'germany', 'italy', 'spain', 'portugal', 'uk', 'united kingdom', 'united states', 'new zealand', 'south africa', 'mexico', 'argentina', 'peru', 'ecuador', 'colombia', 'venezuela', 'russia', 'finland', 'sweden', 'denmark', 'iceland', 'greenland', 'alaska', 'california', 'florida', 'texas', 'washington', 'oregon', 'british columbia', 'ontario', 'quebec', 'atlantic', 'pacific', 'mediterranean']
    for country in countries:
        if country in header_lower:
            record["Country"] = country.title()
            break
    
    # Extract date if present (look for year patterns)
    import re
    year_match = re.search(r'\b(19|20)\d{2}\b', header)
    if year_match:
        record["Create Date"] = year_match.group(0)
    
    # Try to extract additional metadata from isolate/strain information
    if 'isolate' in header_lower:
        isolate_match = re.search(r'isolate\s+(\w+)', header, re.IGNORECASE)
        if isolate_match and not record["Country"]:
            # Sometimes isolate names contain location info
            isolate_name = isolate_match.group(1).lower()
            for country in countries:
                if country in isolate_name:
                    record["Country"] = country.title()
                    break
    
    return record

def parse_genbank_text(text: str) -> List[Dict[str, Any]]:
    """Parse GenBank formatted text to extract comprehensive metadata."""
    records = []
    current_record = {}
    current_section = ""
    
    lines = text.split("\n")
    for i, line in enumerate(lines):
        # Handle LOCUS line - start of new record
        if line.startswith("LOCUS"):
            if current_record:
                records.append(current_record)
            current_record = {
                "Database": "NCBI",
                "Id": "",
                "Accession": "",
                "Title": "",
                "Organism": "",
                "Length": 0,
                "Marker": "",
                "Quality Score": "",
                "Country": "",
                "Create Date": "",
                "Collection Date": "",
                "Geographic Location": "",
                "Isolate": "",
                "Sequencing Technology": "",
                "Taxonomic Classification": "",
                "Authors": "",
                "Institution": "",
                "Gene": "",
                "Product": "",
                "Protein ID": "",
                "Taxon ID": ""
            }
            parts = line.split()
            if len(parts) > 1:
                current_record["Id"] = parts[1]
                current_record["Accession"] = parts[1]
            if len(parts) > 2:
                try:
                    current_record["Length"] = int(parts[2])
                except:
                    pass
            # Extract date from LOCUS line (last part)
            if len(parts) > 6:
                current_record["Create Date"] = parts[-1]
                
        # Handle DEFINITION line(s)
        elif line.startswith("DEFINITION"):
            current_record["Title"] = line[12:].strip()
            current_section = "DEFINITION"
        elif current_section == "DEFINITION" and line.startswith("            "):
            current_record["Title"] += " " + line.strip()
            
        # Handle ACCESSION
        elif line.startswith("ACCESSION"):
            parts = line.split()
            if len(parts) > 1:
                current_record["Accession"] = parts[1]
                
        # Handle VERSION
        elif line.startswith("VERSION"):
            parts = line.split()
            if len(parts) > 1:
                current_record["Accession"] = parts[1]  # Use versioned accession
                current_record["Id"] = parts[1]
                
        # Handle SOURCE line
        elif line.startswith("SOURCE"):
            source_text = line[10:].strip()
            # Extract organism from parentheses
            if "(" in source_text and ")" in source_text:
                start = source_text.find("(") + 1
                end = source_text.find(")")
                current_record["Organism"] = source_text[start:end]
            current_section = "SOURCE"
            
        # Handle ORGANISM line and taxonomic classification
        elif line.strip().startswith("ORGANISM") and current_section == "SOURCE":
            organism = line.split("ORGANISM")[1].strip()
            if organism:
                current_record["Organism"] = organism
            current_section = "TAXONOMY"
        elif current_section == "TAXONOMY" and line.startswith("            "):
            # Collect taxonomic classification
            taxonomy = line.strip().rstrip(";")
            if current_record["Taxonomic Classification"]:
                current_record["Taxonomic Classification"] += "; " + taxonomy
            else:
                current_record["Taxonomic Classification"] = taxonomy
                
        # Handle REFERENCE section
        elif line.startswith("REFERENCE"):
            current_section = "REFERENCE"
        elif current_section == "REFERENCE" and line.strip().startswith("AUTHORS"):
            authors = line.split("AUTHORS")[1].strip()
            current_record["Authors"] = authors
        elif current_section == "REFERENCE" and line.strip().startswith("JOURNAL"):
            journal = line.split("JOURNAL")[1].strip()
            # Extract institution and location from journal
            if ")" in journal:
                # Look for institution pattern
                import re
                institution_match = re.search(r'([^,]+),\s*([^,]+),\s*([^,]+)\s*\d+,\s*([^)]+)', journal)
                if institution_match:
                    current_record["Institution"] = institution_match.group(1).strip()
                    location_parts = [institution_match.group(2), institution_match.group(3), institution_match.group(4)]
                    current_record["Country"] = location_parts[-1].strip()
                    
        # Handle COMMENT section for sequencing technology
        elif line.startswith("COMMENT"):
            current_section = "COMMENT"
        elif current_section == "COMMENT" and "Sequencing Technology" in line:
            tech = line.split("::")[-1].strip()
            current_record["Sequencing Technology"] = tech
            
        # Handle FEATURES section
        elif line.startswith("FEATURES"):
            current_section = "FEATURES"
        elif current_section == "FEATURES":
            # Extract source features
            if line.strip().startswith("/isolate="):
                isolate = line.split('=')[1].strip().strip('"')
                current_record["Isolate"] = isolate
            elif line.strip().startswith("/geo_loc_name="):
                geo_loc = line.split('=')[1].strip().strip('"')
                current_record["Geographic Location"] = geo_loc
                # Extract country from geographic location
                if ":" in geo_loc:
                    country = geo_loc.split(":")[0].strip()
                    current_record["Country"] = country
            elif line.strip().startswith("/collection_date="):
                collection_date = line.split('=')[1].strip().strip('"')
                current_record["Collection Date"] = collection_date
            elif line.strip().startswith("/gene="):
                gene = line.split('=')[1].strip().strip('"')
                current_record["Gene"] = gene
            elif line.strip().startswith("/product="):
                product = line.split('=')[1].strip().strip('"')
                current_record["Product"] = product
            elif line.strip().startswith("/protein_id="):
                protein_id = line.split('=')[1].strip().strip('"')
                current_record["Protein ID"] = protein_id
            elif line.strip().startswith("/db_xref="):
                # Extract taxon ID from db_xref
                xref = line.split('=')[1].strip().strip('"')
                if xref.startswith("taxon:"):
                    taxon_id = xref.replace("taxon:", "").strip()
                    current_record["Taxon ID"] = taxon_id
                
        # Reset section on new major section
        elif line.startswith(("KEYWORDS", "ORIGIN")):
            current_section = ""
            
    # Extract marker information from title and gene for each record
    for record in records:
        if record.get("Title") or record.get("Gene"):
            title_lower = (record.get("Title", "") + " " + record.get("Gene", "")).lower()
            if any(term in title_lower for term in ['coi', 'cytochrome oxidase', 'cox1', 'cytochrome c oxidase']):
                record["Marker"] = "COI"
            elif any(term in title_lower for term in ['16s', '16s ribosomal', '16s rrna']):
                record["Marker"] = "16S"
            elif any(term in title_lower for term in ['18s', '18s ribosomal', '18s rrna']):
                record["Marker"] = "18S"
            elif 'its' in title_lower:
                record["Marker"] = "ITS"
            elif 'rbcl' in title_lower:
                record["Marker"] = "rbcL"
            elif 'matk' in title_lower:
                record["Marker"] = "matK"
    
    if current_record:
        records.append(current_record)
    
    return records

def extract_column_value(record: Dict[str, Any], column: str, original_data: str) -> Any:
    """Extract a specific column value from a record."""
    
    # Direct mapping for common fields
    field_mappings = {
        "Id": ["id", "ID", "identifier", "seq_id", "gene_id", "ens_id"],
        "Accession": ["accession", "acc", "accession_number"],
        "Title": ["title", "description", "definition", "name"],
        "Organism": ["organism", "species", "taxon", "scientific_name"],
        "Length": ["length", "len", "sequence_length", "seq_length"],
        "Database": ["database", "db", "source", "provider"],
        "Marker": ["marker", "gene", "locus", "region"],
        "Quality Score": ["quality", "quality_score", "score", "phred_score"],
        "Country": ["country", "location", "geo_location", "isolation_source"],
        "Create Date": ["date", "create_date", "submission_date", "update_date"]
    }
    
    # Try direct field access first
    if column in record:
        return record[column]
    
    # Try mapped field names
    if column in field_mappings:
        for field_name in field_mappings[column]:
            if field_name in record:
                return record[field_name]
    
    # Special handling for specific columns
    if column == "Database":
        # Try to infer database from data source
        if "ensembl" in original_data.lower():
            return "Ensembl"
        elif "ncbi" in original_data.lower():
            return "NCBI"
        elif "bold" in original_data.lower():
            return "BOLD"
        elif "silva" in original_data.lower():
            return "SILVA"
        elif "unite" in original_data.lower():
            return "UNITE"
    
    elif column == "Length" and "sequence" in record:
        return len(record["sequence"])
    
    elif column == "Marker":
        # Try to infer marker from title or description
        title_lower = str(record.get("Title", "")).lower()
        if "coi" in title_lower or "cytochrome oxidase" in title_lower:
            return "COI"
        elif "16s" in title_lower:
            return "16S"
        elif "its" in title_lower:
            return "ITS"
    
    # Return empty string if not found
    return ""

def format_as_csv(records: List[Dict[str, Any]], columns: List[str]) -> str:
    """Format records as CSV."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()

def format_as_tsv(records: List[Dict[str, Any]], columns: List[str]) -> str:
    """Format records as TSV."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, delimiter='\t')
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()

def format_as_table(records: List[Dict[str, Any]], columns: List[str]) -> str:
    """Format records as a readable table."""
    if not records:
        return "No records found"
    
    # Calculate column widths
    widths = {}
    for col in columns:
        widths[col] = max(len(col), max(len(str(record.get(col, ""))) for record in records))
    
    # Create header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-" * len(header)
    
    # Create rows
    rows = []
    for record in records:
        row = " | ".join(str(record.get(col, "")).ljust(widths[col]) for col in columns)
        rows.append(row)
    
    return "\n".join([header, separator] + rows)

async def main():
    """Main server entry point."""
    Config.validate()
    
    # Log server startup
    logger.info("Starting ndiag-database-server MCP server")
    logger.info("Available tools: get_sequences, gget_*, get_neighbors, get_taxonomy, search_sra_*")
    
    try:
        # Run the server using stdio transport
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ndiag-database-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
