#!/usr/bin/env python3
"""
Validation MCP Server for neglected-diagnostics project.

This server provides primer validation and literature research capabilities including:
- BLAST validation (gget and local)
- BLAT genomic mapping
- In-silico PCR simulation
- Primer coverage assessment
- PubMed literature search
- End-to-end validation pipeline
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import subprocess
import re
import time
from typing import Any, Dict, List, Optional, Union, Tuple
import traceback
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

try:
    import gget
except ImportError:
    gget = None

from Bio import SeqIO, Entrez
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import pandas as pd

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from config import Config

# Configure logging (to stderr)
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration
Config.validate()

# Configure Entrez
Entrez.email = Config.NCBI_EMAIL
Entrez.tool = Config.NCBI_TOOL_NAME
if Config.NCBI_API_KEY:
    Entrez.api_key = Config.NCBI_API_KEY
    logger.info("Using NCBI API key for enhanced rate limits")

# Create the server instance
server = Server("ndiag-validation-server")

# Rate limiting for NCBI API
_last_ncbi_request_time = 0

async def rate_limit_ncbi():
    """Enforce NCBI API rate limits."""
    global _last_ncbi_request_time
    current_time = time.time()
    elapsed = current_time - _last_ncbi_request_time
    required_delay = Config.EFFECTIVE_REQUEST_DELAY

    if elapsed < required_delay:
        await asyncio.sleep(required_delay - elapsed)

    _last_ncbi_request_time = time.time()


# ============================================================================
# Helper Functions
# ============================================================================

async def run_command(cmd: List[str], input_data: Optional[str] = None,
                     description: str = "") -> Dict[str, Any]:
    """
    Run an external command asynchronously.

    Args:
        cmd: Command and arguments as list
        input_data: Optional stdin input
        description: Command description for logging

    Returns:
        Dict with stdout, stderr, returncode
    """
    logger.info(f"Running command: {description}")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate(
            input=input_data.encode() if input_data else None
        )

        result = {
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
            "returncode": proc.returncode
        }

        if proc.returncode != 0:
            logger.error(f"Command failed: {description}")
            logger.error(f"stderr: {result['stderr']}")
        else:
            logger.info(f"Command succeeded: {description}")

        return result

    except Exception as e:
        logger.error(f"Command exception: {description} - {str(e)}")
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def reverse_complement(sequence: str) -> str:
    """Calculate reverse complement of DNA sequence."""
    complement = str.maketrans('ATGCatgc', 'TACGtacg')
    return sequence.translate(complement)[::-1]


def find_primer_matches(primer: str, template: str, max_mismatches: int = 2) -> List[Dict[str, Any]]:
    """
    Find primer binding sites in template sequence.

    Args:
        primer: Primer sequence
        template: Template DNA sequence
        max_mismatches: Maximum allowed mismatches

    Returns:
        List of match dictionaries with position, strand, mismatches
    """
    matches = []
    primer_len = len(primer)
    primer_upper = primer.upper()
    template_upper = template.upper()

    # Search forward strand
    for i in range(len(template_upper) - primer_len + 1):
        window = template_upper[i:i + primer_len]
        mismatches = sum(1 for a, b in zip(primer_upper, window) if a != b)

        if mismatches <= max_mismatches:
            matches.append({
                "position": i,
                "strand": "+",
                "mismatches": mismatches,
                "matched_sequence": window
            })

    # Search reverse strand (reverse complement)
    primer_rc = reverse_complement(primer_upper)
    for i in range(len(template_upper) - primer_len + 1):
        window = template_upper[i:i + primer_len]
        mismatches = sum(1 for a, b in zip(primer_rc, window) if a != b)

        if mismatches <= max_mismatches:
            matches.append({
                "position": i,
                "strand": "-",
                "mismatches": mismatches,
                "matched_sequence": window
            })

    return matches


# ============================================================================
# Core Implementation Functions
# ============================================================================

async def gget_blast_impl(
    sequence: str,
    program: str = "blastn",
    database: str = "nt",
    limit: int = 50,
    expect: float = 10.0,
    low_comp_filt: bool = False
) -> Dict[str, Any]:
    """
    Run BLAST search using gget.

    Args:
        sequence: Query sequence
        program: BLAST program (blastn, blastp, blastx, tblastn, tblastx)
        database: BLAST database (nt, nr, refseq_rna, refseq_protein)
        limit: Maximum number of hits to return
        expect: E-value threshold
        low_comp_filt: Enable low complexity filtering

    Returns:
        Dict with BLAST results
    """
    logger.info(f"Running gget BLAST: program={program}, database={database}")

    if not gget:
        return {
            "success": False,
            "error": "gget library not available. Install with: pip install gget"
        }

    try:
        # Rate limit NCBI requests
        await rate_limit_ncbi()

        # Run gget BLAST
        results = gget.blast(
            sequence=sequence,
            program=program,
            database=database,
            limit=limit,
            expect=expect,
            low_comp_filt=low_comp_filt
        )

        if results is None or (isinstance(results, pd.DataFrame) and results.empty):
            return {
                "success": True,
                "num_hits": 0,
                "hits": [],
                "message": "No BLAST hits found"
            }

        # Convert DataFrame to dict
        if isinstance(results, pd.DataFrame):
            hits = results.to_dict('records')
        else:
            hits = results

        logger.info(f"BLAST returned {len(hits)} hits")

        return {
            "success": True,
            "num_hits": len(hits),
            "hits": hits,
            "query_length": len(sequence),
            "program": program,
            "database": database
        }

    except Exception as e:
        logger.error(f"Error in gget_blast: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def gget_blat_impl(
    sequence: str,
    seqtype: str = "DNA",
    assembly: str = "human"
) -> Dict[str, Any]:
    """
    Run BLAT search using gget.

    Args:
        sequence: Query sequence
        seqtype: Sequence type (DNA, protein, translated RNA, translated DNA)
        assembly: Genome assembly (human, mouse, etc.)

    Returns:
        Dict with BLAT results
    """
    logger.info(f"Running gget BLAT: seqtype={seqtype}, assembly={assembly}")

    if not gget:
        return {
            "success": False,
            "error": "gget library not available. Install with: pip install gget"
        }

    try:
        # Rate limit requests
        await rate_limit_ncbi()

        # Run gget BLAT
        results = gget.blat(
            sequence=sequence,
            seqtype=seqtype,
            assembly=assembly
        )

        if results is None or (isinstance(results, pd.DataFrame) and results.empty):
            return {
                "success": True,
                "num_hits": 0,
                "hits": [],
                "message": "No BLAT hits found"
            }

        # Convert DataFrame to dict
        if isinstance(results, pd.DataFrame):
            hits = results.to_dict('records')
        else:
            hits = results

        logger.info(f"BLAT returned {len(hits)} hits")

        return {
            "success": True,
            "num_hits": len(hits),
            "hits": hits,
            "query_length": len(sequence),
            "seqtype": seqtype,
            "assembly": assembly
        }

    except Exception as e:
        logger.error(f"Error in gget_blat: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def blast_nt_impl(
    query_fasta: str,
    perc_identity: float = 90.0,
    max_targets: int = 50,
    evalue: float = 0.001
) -> Dict[str, Any]:
    """
    Run local BLAST against nt database.

    Args:
        query_fasta: Query sequences in FASTA format
        perc_identity: Minimum percent identity
        max_targets: Maximum number of target sequences
        evalue: E-value threshold

    Returns:
        Dict with BLAST results
    """
    logger.info(f"Running local BLAST: identity={perc_identity}%, max_targets={max_targets}")

    try:
        # Check if local BLAST is available
        if not Config.use_local_blast("nt"):
            return {
                "success": False,
                "error": "Local BLAST database not configured. Use gget_blast for remote BLAST."
            }

        # Write query to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(query_fasta)
            query_file = f.name

        # Prepare output file
        output_file = tempfile.mktemp(suffix='.blast.txt')

        try:
            # Run BLAST
            db_path = Config.get_blast_db_path("nt")
            cmd = [
                Config.BLASTN_PATH,
                "-query", query_file,
                "-db", db_path,
                "-out", output_file,
                "-outfmt", "6",  # Tabular format
                "-perc_identity", str(perc_identity),
                "-max_target_seqs", str(max_targets),
                "-evalue", str(evalue)
            ]

            result = await run_command(cmd, description="Local BLAST")

            if result["returncode"] != 0:
                return {
                    "success": False,
                    "error": f"BLAST failed: {result['stderr']}"
                }

            # Parse BLAST output
            hits = []
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            fields = line.strip().split('\t')
                            if len(fields) >= 12:
                                hits.append({
                                    "query_id": fields[0],
                                    "subject_id": fields[1],
                                    "percent_identity": float(fields[2]),
                                    "alignment_length": int(fields[3]),
                                    "mismatches": int(fields[4]),
                                    "gap_opens": int(fields[5]),
                                    "query_start": int(fields[6]),
                                    "query_end": int(fields[7]),
                                    "subject_start": int(fields[8]),
                                    "subject_end": int(fields[9]),
                                    "evalue": float(fields[10]),
                                    "bit_score": float(fields[11])
                                })

            logger.info(f"Local BLAST returned {len(hits)} hits")

            return {
                "success": True,
                "num_hits": len(hits),
                "hits": hits,
                "database": "nt (local)",
                "parameters": {
                    "perc_identity": perc_identity,
                    "max_targets": max_targets,
                    "evalue": evalue
                }
            }

        finally:
            # Cleanup temp files
            if os.path.exists(query_file):
                os.unlink(query_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    except Exception as e:
        logger.error(f"Error in blast_nt: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def in_silico_pcr_impl(
    forward_primer: str,
    reverse_primer: str,
    template_fasta: str,
    max_mismatches: int = 2
) -> Dict[str, Any]:
    """
    Simulate PCR amplification in silico.

    Args:
        forward_primer: Forward primer sequence
        reverse_primer: Reverse primer sequence
        template_fasta: Template sequences in FASTA format
        max_mismatches: Maximum allowed mismatches per primer

    Returns:
        Dict with predicted PCR products
    """
    logger.info(f"Running in-silico PCR: F={len(forward_primer)}bp, R={len(reverse_primer)}bp")

    try:
        # Parse template sequences
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(template_fasta)
            temp_file = f.name

        try:
            templates = list(SeqIO.parse(temp_file, "fasta"))
        finally:
            os.unlink(temp_file)

        if not templates:
            return {
                "success": False,
                "error": "No sequences found in template FASTA"
            }

        all_products = []

        for template in templates:
            template_seq = str(template.seq).upper()
            template_id = template.id

            # Find forward primer binding sites
            forward_matches = find_primer_matches(forward_primer, template_seq, max_mismatches)

            # Find reverse primer binding sites (on reverse strand)
            reverse_matches = find_primer_matches(reverse_primer, template_seq, max_mismatches)

            # Pair up forward and reverse matches
            products = []
            for fwd in forward_matches:
                for rev in reverse_matches:
                    # Valid product: forward on + strand, reverse on - strand, forward before reverse
                    if fwd["strand"] == "+" and rev["strand"] == "-" and fwd["position"] < rev["position"]:
                        amplicon_start = fwd["position"]
                        amplicon_end = rev["position"] + len(reverse_primer)
                        amplicon_size = amplicon_end - amplicon_start

                        # Check if product size is reasonable
                        if Config.DEFAULT_MIN_PRODUCT_SIZE <= amplicon_size <= Config.DEFAULT_MAX_PRODUCT_SIZE:
                            products.append({
                                "template_id": template_id,
                                "forward_position": fwd["position"],
                                "reverse_position": rev["position"],
                                "forward_mismatches": fwd["mismatches"],
                                "reverse_mismatches": rev["mismatches"],
                                "total_mismatches": fwd["mismatches"] + rev["mismatches"],
                                "amplicon_size": amplicon_size,
                                "amplicon_sequence": template_seq[amplicon_start:amplicon_end]
                            })

            if products:
                all_products.extend(products)

        logger.info(f"In-silico PCR predicted {len(all_products)} products")

        return {
            "success": True,
            "num_templates": len(templates),
            "num_products": len(all_products),
            "products": all_products,
            "primers": {
                "forward": forward_primer,
                "reverse": reverse_primer
            }
        }

    except Exception as e:
        logger.error(f"Error in in_silico_pcr: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def assess_coverage_impl(
    primers: Dict[str, str],
    target_panel: str,
    offtarget_panel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assess primer coverage across target and off-target panels.

    Args:
        primers: Dict with 'forward' and 'reverse' primer sequences
        target_panel: FASTA file with target sequences
        offtarget_panel: Optional FASTA file with off-target sequences

    Returns:
        Dict with coverage statistics
    """
    logger.info("Assessing primer coverage")

    try:
        forward_primer = primers.get("forward")
        reverse_primer = primers.get("reverse")

        if not forward_primer or not reverse_primer:
            return {
                "success": False,
                "error": "Both forward and reverse primers required"
            }

        # Run in-silico PCR on target panel
        target_result = await in_silico_pcr_impl(
            forward_primer=forward_primer,
            reverse_primer=reverse_primer,
            template_fasta=target_panel,
            max_mismatches=Config.DEFAULT_MAX_MISMATCHES
        )

        if not target_result.get("success"):
            return target_result

        # Calculate target statistics
        target_templates = set()
        for product in target_result.get("products", []):
            target_templates.add(product["template_id"])

        num_target_templates = target_result.get("num_templates", 0)
        num_amplified_targets = len(target_templates)
        sensitivity = num_amplified_targets / num_target_templates if num_target_templates > 0 else 0

        coverage_result = {
            "success": True,
            "target_coverage": {
                "total_sequences": num_target_templates,
                "amplified_sequences": num_amplified_targets,
                "sensitivity": round(sensitivity, 3),
                "failed_sequences": num_target_templates - num_amplified_targets
            }
        }

        # Run in-silico PCR on off-target panel if provided
        if offtarget_panel:
            offtarget_result = await in_silico_pcr_impl(
                forward_primer=forward_primer,
                reverse_primer=reverse_primer,
                template_fasta=offtarget_panel,
                max_mismatches=Config.DEFAULT_MAX_MISMATCHES
            )

            if offtarget_result.get("success"):
                offtarget_templates = set()
                for product in offtarget_result.get("products", []):
                    offtarget_templates.add(product["template_id"])

                num_offtarget_templates = offtarget_result.get("num_templates", 0)
                num_amplified_offtargets = len(offtarget_templates)
                specificity = (num_offtarget_templates - num_amplified_offtargets) / num_offtarget_templates if num_offtarget_templates > 0 else 1.0

                coverage_result["offtarget_coverage"] = {
                    "total_sequences": num_offtarget_templates,
                    "amplified_sequences": num_amplified_offtargets,
                    "specificity": round(specificity, 3),
                    "cross_reactive_sequences": num_amplified_offtargets
                }

        # Determine pass/fail
        passes_sensitivity = sensitivity >= Config.VALIDATION_MIN_SENSITIVITY
        passes_specificity = True
        if offtarget_panel:
            offtarget_spec = coverage_result.get("offtarget_coverage", {}).get("specificity", 1.0)
            passes_specificity = offtarget_spec >= Config.VALIDATION_MIN_SPECIFICITY

        coverage_result["validation_pass"] = passes_sensitivity and passes_specificity
        coverage_result["issues"] = []
        if not passes_sensitivity:
            coverage_result["issues"].append(f"Low sensitivity: {sensitivity:.1%} < {Config.VALIDATION_MIN_SENSITIVITY:.1%}")
        if not passes_specificity:
            coverage_result["issues"].append(f"Low specificity: {offtarget_spec:.1%} < {Config.VALIDATION_MIN_SPECIFICITY:.1%}")

        logger.info(f"Coverage assessment complete: sensitivity={sensitivity:.1%}, validation_pass={coverage_result['validation_pass']}")

        return coverage_result

    except Exception as e:
        logger.error(f"Error in assess_coverage: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def search_pubmed_impl(
    query: str,
    max_results: int = 20,
    filters: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Search PubMed for literature.

    Args:
        query: Search query string
        max_results: Maximum number of results to return
        filters: Optional filters (publication_date, journal, species)

    Returns:
        Dict with PubMed search results
    """
    logger.info(f"Searching PubMed: query='{query}'")

    try:
        # Rate limit
        await rate_limit_ncbi()

        # Build search term
        search_term = query
        if filters:
            if "publication_date" in filters:
                search_term += f" AND {filters['publication_date']}[PDAT]"
            if "journal" in filters:
                search_term += f" AND {filters['journal']}[Journal]"
            if "species" in filters:
                search_term += f" AND {filters['species']}[Organism]"

        # Search PubMed
        handle = Entrez.esearch(
            db="pubmed",
            term=search_term,
            retmax=max_results,
            sort=Config.DEFAULT_PUBMED_SORT
        )
        search_results = Entrez.read(handle)
        handle.close()

        id_list = search_results.get("IdList", [])

        if not id_list:
            return {
                "success": True,
                "num_results": 0,
                "articles": [],
                "message": "No PubMed articles found"
            }

        # Rate limit before fetching
        await rate_limit_ncbi()

        # Fetch article details
        handle = Entrez.efetch(
            db="pubmed",
            id=id_list,
            rettype="medline",
            retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()

        # Parse records
        articles = []
        for record in records.get("PubmedArticle", []):
            article_data = record.get("MedlineCitation", {})
            article_info = article_data.get("Article", {})

            # Extract title
            title = article_info.get("ArticleTitle", "No title")

            # Extract abstract
            abstract_data = article_info.get("Abstract", {})
            abstract_texts = abstract_data.get("AbstractText", [])
            abstract = " ".join(str(text) for text in abstract_texts) if abstract_texts else "No abstract available"

            # Extract authors
            authors_data = article_info.get("AuthorList", [])
            authors = []
            for author in authors_data[:5]:  # First 5 authors
                if isinstance(author, dict):
                    last_name = author.get("LastName", "")
                    fore_name = author.get("ForeName", "")
                    if last_name:
                        authors.append(f"{last_name}, {fore_name}" if fore_name else last_name)

            # Extract PMID
            pmid = article_data.get("PMID", "")

            # Extract publication date
            pub_date = article_info.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            year = pub_date.get("Year", "")
            month = pub_date.get("Month", "")
            pub_date_str = f"{year}-{month}" if year and month else year

            articles.append({
                "pmid": str(pmid),
                "title": title,
                "authors": authors,
                "publication_date": pub_date_str,
                "abstract": abstract[:500] + "..." if len(abstract) > 500 else abstract,  # Truncate long abstracts
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })

        logger.info(f"PubMed search returned {len(articles)} articles")

        return {
            "success": True,
            "num_results": len(articles),
            "articles": articles,
            "query": search_term
        }

    except Exception as e:
        logger.error(f"Error in search_pubmed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def validate_primers_complete_impl(
    primers: Dict[str, str],
    target_panel: str,
    offtarget_panel: Optional[str] = None,
    include_literature: bool = True,
    literature_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete end-to-end primer validation pipeline.

    Args:
        primers: Dict with 'forward' and 'reverse' primer sequences
        target_panel: FASTA file with target sequences
        offtarget_panel: Optional FASTA file with off-target sequences
        include_literature: Whether to search literature
        literature_query: Optional custom literature search query

    Returns:
        Dict with complete validation results
    """
    logger.info("Running complete primer validation pipeline")

    try:
        forward_primer = primers.get("forward")
        reverse_primer = primers.get("reverse")

        if not forward_primer or not reverse_primer:
            return {
                "success": False,
                "error": "Both forward and reverse primers required"
            }

        validation_results = {
            "success": True,
            "primers": primers,
            "validation_steps": {}
        }

        # Step 1: BLAST forward primer
        logger.info("Step 1: BLASTing forward primer")
        fwd_blast = await gget_blast_impl(
            sequence=forward_primer,
            program="blastn",
            database="nt",
            limit=20,
            expect=1000.0  # Lenient e-value for primers
        )
        validation_results["validation_steps"]["forward_blast"] = fwd_blast

        # Step 2: BLAST reverse primer
        logger.info("Step 2: BLASTing reverse primer")
        rev_blast = await gget_blast_impl(
            sequence=reverse_primer,
            program="blastn",
            database="nt",
            limit=20,
            expect=1000.0
        )
        validation_results["validation_steps"]["reverse_blast"] = rev_blast

        # Step 3: In-silico PCR on target panel
        logger.info("Step 3: Running in-silico PCR")
        pcr_result = await in_silico_pcr_impl(
            forward_primer=forward_primer,
            reverse_primer=reverse_primer,
            template_fasta=target_panel,
            max_mismatches=Config.DEFAULT_MAX_MISMATCHES
        )
        validation_results["validation_steps"]["in_silico_pcr"] = pcr_result

        # Step 4: Coverage assessment
        logger.info("Step 4: Assessing coverage")
        coverage_result = await assess_coverage_impl(
            primers=primers,
            target_panel=target_panel,
            offtarget_panel=offtarget_panel
        )
        validation_results["validation_steps"]["coverage_assessment"] = coverage_result

        # Step 5: Literature search (optional)
        if include_literature and literature_query:
            logger.info("Step 5: Searching literature")
            lit_result = await search_pubmed_impl(
                query=literature_query,
                max_results=Config.DEFAULT_PUBMED_MAX_RESULTS
            )
            validation_results["validation_steps"]["literature_search"] = lit_result

        # Generate summary
        validation_pass = coverage_result.get("validation_pass", False)
        sensitivity = coverage_result.get("target_coverage", {}).get("sensitivity", 0)
        specificity = 1.0
        if "offtarget_coverage" in coverage_result:
            specificity = coverage_result["offtarget_coverage"].get("specificity", 1.0)

        num_products = pcr_result.get("num_products", 0)
        fwd_blast_hits = fwd_blast.get("num_hits", 0)
        rev_blast_hits = rev_blast.get("num_hits", 0)

        validation_results["summary"] = {
            "validation_pass": validation_pass,
            "sensitivity": round(sensitivity, 3),
            "specificity": round(specificity, 3),
            "pcr_products": num_products,
            "forward_blast_hits": fwd_blast_hits,
            "reverse_blast_hits": rev_blast_hits,
            "issues": coverage_result.get("issues", []),
            "recommendation": "PASS" if validation_pass else "FAIL"
        }

        logger.info(f"Validation complete: {validation_results['summary']['recommendation']}")

        return validation_results

    except Exception as e:
        logger.error(f"Error in validate_primers_complete: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# MCP Server Handlers
# ============================================================================

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """
    List all available tools provided by this server.
    """
    return [
        types.Tool(
            name="gget_blast",
            description="Run BLAST search using gget for quick remote BLAST queries. Supports multiple BLAST programs (blastn, blastp, blastx, tblastn, tblastx) and databases (nt, nr, refseq). Ideal for validating primer specificity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Query sequence (DNA or protein)"
                    },
                    "program": {
                        "type": "string",
                        "enum": ["blastn", "blastp", "blastx", "tblastn", "tblastx"],
                        "description": "BLAST program to use",
                        "default": "blastn"
                    },
                    "database": {
                        "type": "string",
                        "enum": ["nt", "nr", "refseq_rna", "refseq_protein"],
                        "description": "BLAST database to search",
                        "default": "nt"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of hits to return",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 250
                    },
                    "expect": {
                        "type": "number",
                        "description": "E-value threshold",
                        "default": 10.0
                    },
                    "low_comp_filt": {
                        "type": "boolean",
                        "description": "Enable low complexity filtering",
                        "default": False
                    }
                },
                "required": ["sequence"]
            }
        ),
        types.Tool(
            name="gget_blat",
            description="Run BLAT search using gget for fast genomic location mapping. Returns chromosomal coordinates and alignment details. Useful for finding primer binding locations in reference genomes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Query sequence"
                    },
                    "seqtype": {
                        "type": "string",
                        "enum": ["DNA", "protein", "translated%20RNA", "translated%20DNA"],
                        "description": "Sequence type",
                        "default": "DNA"
                    },
                    "assembly": {
                        "type": "string",
                        "description": "Genome assembly (e.g., 'human', 'mouse')",
                        "default": "human"
                    }
                },
                "required": ["sequence"]
            }
        ),
        types.Tool(
            name="blast_nt",
            description="Run local BLAST against nt or custom databases with fine-grained control. Requires local BLAST installation and databases. Provides more control than remote BLAST but requires infrastructure setup.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_fasta": {
                        "type": "string",
                        "description": "Query sequences in FASTA format"
                    },
                    "perc_identity": {
                        "type": "number",
                        "description": "Minimum percent identity",
                        "default": 90.0,
                        "minimum": 0,
                        "maximum": 100
                    },
                    "max_targets": {
                        "type": "integer",
                        "description": "Maximum number of target sequences",
                        "default": 50
                    },
                    "evalue": {
                        "type": "number",
                        "description": "E-value threshold",
                        "default": 0.001
                    }
                },
                "required": ["query_fasta"]
            }
        ),
        types.Tool(
            name="in_silico_pcr",
            description="Simulate PCR amplification in silico. Finds primer binding sites in template sequences and predicts amplicon sizes. Allows configurable mismatches for realistic PCR simulation. Essential for validating primer design.",
            inputSchema={
                "type": "object",
                "properties": {
                    "forward_primer": {
                        "type": "string",
                        "description": "Forward primer sequence (5' to 3')"
                    },
                    "reverse_primer": {
                        "type": "string",
                        "description": "Reverse primer sequence (5' to 3')"
                    },
                    "template_fasta": {
                        "type": "string",
                        "description": "Template sequences in FASTA format"
                    },
                    "max_mismatches": {
                        "type": "integer",
                        "description": "Maximum allowed mismatches per primer",
                        "default": 2,
                        "minimum": 0,
                        "maximum": 5
                    }
                },
                "required": ["forward_primer", "reverse_primer", "template_fasta"]
            }
        ),
        types.Tool(
            name="assess_coverage",
            description="Assess primer coverage across target and off-target sequence panels. Calculates sensitivity (% targets amplified) and specificity (% off-targets not amplified). Reports pass/fail based on configurable thresholds.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primers": {
                        "type": "object",
                        "properties": {
                            "forward": {"type": "string"},
                            "reverse": {"type": "string"}
                        },
                        "required": ["forward", "reverse"],
                        "description": "Primer pair sequences"
                    },
                    "target_panel": {
                        "type": "string",
                        "description": "FASTA file content with target sequences"
                    },
                    "offtarget_panel": {
                        "type": "string",
                        "description": "Optional FASTA file content with off-target sequences"
                    }
                },
                "required": ["primers", "target_panel"]
            }
        ),
        types.Tool(
            name="search_pubmed",
            description="Search PubMed for literature related to primers, targets, or methods. Supports filtering by publication date, journal, and species. Returns article titles, abstracts, authors, and PubMed links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string (supports PubMed search syntax)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "filters": {
                        "type": "object",
                        "properties": {
                            "publication_date": {
                                "type": "string",
                                "description": "Publication date filter (e.g., '2020:2025[PDAT]')"
                            },
                            "journal": {
                                "type": "string",
                                "description": "Journal name filter"
                            },
                            "species": {
                                "type": "string",
                                "description": "Species name filter"
                            }
                        },
                        "description": "Optional search filters"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="validate_primers_complete",
            description="End-to-end primer validation pipeline combining all validation steps. BLASTs primers, runs in-silico PCR, assesses coverage, and searches literature. Generates comprehensive validation report with pass/fail recommendation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primers": {
                        "type": "object",
                        "properties": {
                            "forward": {"type": "string"},
                            "reverse": {"type": "string"}
                        },
                        "required": ["forward", "reverse"],
                        "description": "Primer pair sequences"
                    },
                    "target_panel": {
                        "type": "string",
                        "description": "FASTA file content with target sequences"
                    },
                    "offtarget_panel": {
                        "type": "string",
                        "description": "Optional FASTA file content with off-target sequences"
                    },
                    "include_literature": {
                        "type": "boolean",
                        "description": "Whether to search literature",
                        "default": True
                    },
                    "literature_query": {
                        "type": "string",
                        "description": "Custom literature search query (optional)"
                    }
                },
                "required": ["primers", "target_panel"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """
    Handle tool execution requests.
    """
    logger.info(f"Tool called: {name}")
    logger.debug(f"Arguments: {json.dumps(arguments, indent=2)}")

    try:
        if name == "gget_blast":
            result = await gget_blast_impl(**arguments)

        elif name == "gget_blat":
            result = await gget_blat_impl(**arguments)

        elif name == "blast_nt":
            result = await blast_nt_impl(**arguments)

        elif name == "in_silico_pcr":
            result = await in_silico_pcr_impl(**arguments)

        elif name == "assess_coverage":
            result = await assess_coverage_impl(**arguments)

        elif name == "search_pubmed":
            result = await search_pubmed_impl(**arguments)

        elif name == "validate_primers_complete":
            result = await validate_primers_complete_impl(**arguments)

        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}"
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in handle_call_tool for {name}: {str(e)}")
        logger.error(traceback.format_exc())
        error_result = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Run the MCP server using stdio transport."""
    logger.info("Starting Validation MCP Server...")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ndiag-validation-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
