#!/usr/bin/env python3
"""
Processing MCP Server for neglected-diagnostics project.

This server provides sequence processing capabilities including:
- Quality control and filtering (seqkit)
- Dereplication (vsearch)
- Low-complexity masking (vsearch DUST)
- Chimera detection (vsearch UCHIME)
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import subprocess
from typing import Any, Dict, List, Optional, Union
import traceback
from pathlib import Path

from Bio import SeqIO
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

# Validate configuration
Config.validate()

# Create the server instance
server = Server("ndiag-processing-server")


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
        logger.error(f"Command execution error: {description}: {str(e)}")
        raise


def write_temp_fasta(fasta_content: str, prefix: str = "temp") -> str:
    """Write FASTA content to temporary file and return path."""
    fd, path = tempfile.mkstemp(suffix=".fasta", prefix=f"{prefix}_",
                                 dir=Config.TEMP_DIR)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(fasta_content)
        return path
    except Exception as e:
        os.close(fd)
        if os.path.exists(path):
            os.unlink(path)
        raise


def read_temp_file(path: str) -> str:
    """Read content from temporary file."""
    with open(path, 'r') as f:
        return f.read()


def cleanup_temp_files(*paths: str):
    """Remove temporary files."""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
                logger.debug(f"Cleaned up temp file: {path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {path}: {e}")


def count_sequences(fasta_content: str) -> int:
    """Count number of sequences in FASTA content."""
    return fasta_content.count('>')


def clean_sequences(fasta_content: str) -> str:
    """
    Clean sequences by removing gap characters and invalid characters.
    
    Removes:
    - Gap characters: - (dash)
    - Ambiguous padding: . (dot)
    - Whitespace within sequences
    
    Args:
        fasta_content: Input FASTA content
        
    Returns:
        Cleaned FASTA content
    """
    lines = fasta_content.strip().split('\n')
    cleaned_lines = []
    
    for line in lines:
        if line.startswith('>'):
            # Header line - keep as is
            cleaned_lines.append(line)
        else:
            # Sequence line - remove gap characters and invalid chars
            cleaned_seq = line.replace('-', '').replace('.', '').replace(' ', '').replace('\t', '')
            if cleaned_seq:  # Only add non-empty sequences
                cleaned_lines.append(cleaned_seq)
    
    return '\n'.join(cleaned_lines)


def parse_seqkit_stats(stats_output: str) -> Dict[str, Any]:
    """Parse seqkit stats output into structured format."""
    lines = stats_output.strip().split('\n')
    if len(lines) < 2:
        return {}

    # Parse header and data
    headers = lines[0].split()
    values = lines[1].split()

    result = {}
    for i, header in enumerate(headers):
        if i < len(values):
            result[header] = values[i]

    return result


# ============================================================================
# Tool Implementations
# ============================================================================

async def fasta_qc_impl(
    fasta_content: str,
    min_length: int = Config.DEFAULT_MIN_LENGTH,
    max_n_percent: float = Config.DEFAULT_MAX_N_PERCENT,
    remove_duplicates: bool = True
) -> Dict[str, Any]:
    """
    Perform quality control on FASTA sequences.

    Uses seqkit for filtering by length and BioPython for N-content filtering.

    Args:
        fasta_content: Input FASTA sequences
        min_length: Minimum sequence length
        max_n_percent: Maximum percentage of N bases allowed
        remove_duplicates: Remove duplicate sequences

    Returns:
        Dict with cleaned FASTA and statistics
    """
    logger.info(f"Starting QC: min_length={min_length}, max_n_percent={max_n_percent}")

    input_file = None
    output_file = None

    try:
        # Count input sequences
        input_count = count_sequences(fasta_content)
        logger.info(f"Input sequences: {input_count}")

        # Write input to temp file
        input_file = write_temp_fasta(fasta_content, "qc_input")
        output_file = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)

        # Step 1: Filter by length using seqkit
        cmd = [
            Config.SEQKIT_PATH, "seq",
            "-m", str(min_length),  # min length
            "-o", output_file,
            input_file
        ]

        result = await run_command(cmd, description="seqkit length filter")
        if result["returncode"] != 0:
            return {
                "error": f"seqkit failed: {result['stderr']}",
                "cleaned_fasta": "",
                "stats": {}
            }

        # Step 2: Filter by N-content using BioPython
        filtered_records = []
        n_filtered_count = 0

        with open(output_file, 'r') as f:
            for record in SeqIO.parse(f, "fasta"):
                seq_str = str(record.seq).upper()
                n_count = seq_str.count('N')
                n_percent = (n_count / len(seq_str)) * 100 if len(seq_str) > 0 else 0

                if n_percent <= max_n_percent:
                    filtered_records.append(record)
                else:
                    n_filtered_count += 1

        logger.info(f"Filtered {n_filtered_count} sequences by N-content")

        # Step 3: Remove duplicates if requested
        if remove_duplicates and filtered_records:
            # Write filtered records to temp file
            temp_dedup_input = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)
            SeqIO.write(filtered_records, temp_dedup_input, "fasta")

            temp_dedup_output = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)

            cmd = [
                Config.SEQKIT_PATH, "rmdup",
                "-s",  # by sequence
                "-o", temp_dedup_output,
                temp_dedup_input
            ]

            result = await run_command(cmd, description="seqkit remove duplicates")

            if result["returncode"] == 0:
                with open(temp_dedup_output, 'r') as f:
                    filtered_records = list(SeqIO.parse(f, "fasta"))

            cleanup_temp_files(temp_dedup_input, temp_dedup_output)

        # Generate output FASTA
        if filtered_records:
            output_fasta_file = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)
            SeqIO.write(filtered_records, output_fasta_file, "fasta")

            with open(output_fasta_file, 'r') as f:
                cleaned_fasta = f.read()

            cleanup_temp_files(output_fasta_file)
        else:
            cleaned_fasta = ""

        output_count = len(filtered_records)

        # Get statistics using seqkit stats
        if cleaned_fasta:
            temp_stats_file = write_temp_fasta(cleaned_fasta, "stats")
            cmd = [Config.SEQKIT_PATH, "stats", temp_stats_file]
            result = await run_command(cmd, description="seqkit stats")

            stats = parse_seqkit_stats(result["stdout"]) if result["returncode"] == 0 else {}
            cleanup_temp_files(temp_stats_file)
        else:
            stats = {}

        # Add QC-specific stats
        stats.update({
            "input_sequences": input_count,
            "output_sequences": output_count,
            "filtered_by_length": input_count - count_sequences(read_temp_file(output_file)),
            "filtered_by_n_content": n_filtered_count,
            "duplicates_removed": count_sequences(read_temp_file(output_file)) - n_filtered_count - output_count if remove_duplicates else 0
        })

        return {
            "cleaned_fasta": cleaned_fasta,
            "stats": stats,
            "success": True
        }

    except Exception as e:
        logger.error(f"QC error: {str(e)}\n{traceback.format_exc()}")
        return {
            "error": str(e),
            "cleaned_fasta": "",
            "stats": {}
        }
    finally:
        cleanup_temp_files(input_file, output_file)


async def dereplicate_sequences_impl(
    fasta_content: str,
    identity_threshold: float = Config.DEFAULT_IDENTITY_THRESHOLD,
    per_species: bool = True
) -> Dict[str, Any]:
    """
    Remove duplicate or near-duplicate sequences using vsearch.

    Args:
        fasta_content: Input FASTA sequences
        identity_threshold: Identity threshold for clustering (0.0-1.0)
        per_species: Group by species before dereplication

    Returns:
        Dict with dereplicated FASTA and statistics
    """
    logger.info(f"Dereplication: identity={identity_threshold}, per_species={per_species}")

    input_file = None
    output_file = None

    try:
        input_count = count_sequences(fasta_content)
        logger.info(f"Input sequences: {input_count}")

        # Write input to temp file
        input_file = write_temp_fasta(fasta_content, "derep_input")
        output_file = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)

        # Use vsearch for dereplication/clustering
        cmd = [
            Config.VSEARCH_PATH,
            "--cluster_fast", input_file,
            "--id", str(identity_threshold),
            "--centroids", output_file,
            "--sizeout",  # Add size annotations
            "--strand", "both"  # Check both strands
        ]

        result = await run_command(cmd, description=f"vsearch clustering at {identity_threshold}")

        if result["returncode"] != 0:
            return {
                "error": f"vsearch failed: {result['stderr']}",
                "dereplicated_fasta": "",
                "stats": {}
            }

        # Read dereplicated sequences
        dereplicated_fasta = read_temp_file(output_file)
        output_count = count_sequences(dereplicated_fasta)

        stats = {
            "input_sequences": input_count,
            "output_sequences": output_count,
            "duplicates_removed": input_count - output_count,
            "identity_threshold": identity_threshold,
            "reduction_percent": round((1 - output_count/input_count) * 100, 2) if input_count > 0 else 0
        }

        logger.info(f"Dereplication complete: {input_count} -> {output_count} sequences")

        return {
            "dereplicated_fasta": dereplicated_fasta,
            "stats": stats,
            "success": True
        }

    except Exception as e:
        logger.error(f"Dereplication error: {str(e)}\n{traceback.format_exc()}")
        return {
            "error": str(e),
            "dereplicated_fasta": "",
            "stats": {}
        }
    finally:
        cleanup_temp_files(input_file, output_file)


async def mask_low_complexity_impl(
    fasta_content: str,
    mask_repeats: bool = True,
    mask_homopolymers: bool = True,
    min_complexity: float = Config.DEFAULT_MIN_COMPLEXITY
) -> Dict[str, Any]:
    """
    Mask low-complexity regions using vsearch DUST algorithm.

    Args:
        fasta_content: Input FASTA sequences
        mask_repeats: Mask repetitive regions
        mask_homopolymers: Mask homopolymer runs
        min_complexity: Minimum complexity score (not directly used by DUST)

    Returns:
        Dict with masked FASTA and statistics
    """
    logger.info(f"Masking: repeats={mask_repeats}, homopolymers={mask_homopolymers}")

    input_file = None
    output_file = None

    try:
        input_count = count_sequences(fasta_content)

        # Write input to temp file
        input_file = write_temp_fasta(fasta_content, "mask_input")
        output_file = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)

        # Use vsearch maskfasta with DUST algorithm
        cmd = [
            Config.VSEARCH_PATH,
            "--maskfasta", input_file,
            "--output", output_file,
            "--qmask", "dust",  # Use DUST algorithm
            "--hardmask"  # Replace with N instead of lowercase
        ]

        result = await run_command(cmd, description="vsearch DUST masking")

        if result["returncode"] != 0:
            return {
                "error": f"vsearch masking failed: {result['stderr']}",
                "masked_fasta": "",
                "stats": {}
            }

        # Read masked sequences
        masked_fasta = read_temp_file(output_file)

        # Calculate masking statistics
        masked_bases = 0
        total_bases = 0

        for record in SeqIO.parse(output_file, "fasta"):
            seq_str = str(record.seq).upper()
            masked_bases += seq_str.count('N')
            total_bases += len(seq_str)

        mask_percent = round((masked_bases / total_bases) * 100, 2) if total_bases > 0 else 0

        stats = {
            "input_sequences": input_count,
            "output_sequences": count_sequences(masked_fasta),
            "masked_bases": masked_bases,
            "total_bases": total_bases,
            "masked_percent": mask_percent
        }

        logger.info(f"Masking complete: {mask_percent}% of bases masked")

        return {
            "masked_fasta": masked_fasta,
            "stats": stats,
            "success": True
        }

    except Exception as e:
        logger.error(f"Masking error: {str(e)}\n{traceback.format_exc()}")
        return {
            "error": str(e),
            "masked_fasta": "",
            "stats": {}
        }
    finally:
        cleanup_temp_files(input_file, output_file)


async def detect_chimeras_impl(
    fasta_content: str,
    reference_db: str = "auto",
    abundance_threshold: float = Config.DEFAULT_ABUNDANCE_SKEW
) -> Dict[str, Any]:
    """
    Detect chimeric sequences using vsearch UCHIME.

    Args:
        fasta_content: Input FASTA sequences
        reference_db: Reference database ("auto" for de novo detection)
        abundance_threshold: Abundance skew threshold for chimera detection

    Returns:
        Dict with non-chimeric FASTA and detection statistics
    """
    logger.info(f"Chimera detection: reference={reference_db}, threshold={abundance_threshold}")

    input_file = None
    output_file = None
    chimera_file = None

    try:
        input_count = count_sequences(fasta_content)

        # Write input to temp file
        input_file = write_temp_fasta(fasta_content, "chimera_input")
        output_file = tempfile.mktemp(suffix=".fasta", dir=Config.TEMP_DIR)
        chimera_file = tempfile.mktemp(suffix=".txt", dir=Config.TEMP_DIR)

        # Use vsearch for de novo chimera detection
        cmd = [
            Config.VSEARCH_PATH,
            "--uchime_denovo", input_file,
            "--nonchimeras", output_file,
            "--uchimeout", chimera_file,
            "--abskew", str(abundance_threshold)
        ]

        result = await run_command(cmd, description="vsearch UCHIME chimera detection")

        if result["returncode"] != 0:
            return {
                "error": f"vsearch chimera detection failed: {result['stderr']}",
                "non_chimeric_fasta": "",
                "stats": {}
            }

        # Read non-chimeric sequences
        non_chimeric_fasta = read_temp_file(output_file) if os.path.exists(output_file) else ""
        output_count = count_sequences(non_chimeric_fasta)

        # Parse chimera detection results
        chimeras_detected = input_count - output_count

        stats = {
            "input_sequences": input_count,
            "non_chimeric_sequences": output_count,
            "chimeras_detected": chimeras_detected,
            "chimera_percent": round((chimeras_detected / input_count) * 100, 2) if input_count > 0 else 0,
            "abundance_threshold": abundance_threshold
        }

        logger.info(f"Chimera detection complete: {chimeras_detected} chimeras found")

        return {
            "non_chimeric_fasta": non_chimeric_fasta,
            "stats": stats,
            "success": True
        }

    except Exception as e:
        logger.error(f"Chimera detection error: {str(e)}\n{traceback.format_exc()}")
        return {
            "error": str(e),
            "non_chimeric_fasta": "",
            "stats": {}
        }
    finally:
        cleanup_temp_files(input_file, output_file, chimera_file)


async def process_sequences_impl(
    fasta_content: str,
    pipeline: List[str] = None,
    qc_params: Dict[str, Any] = None,
    derep_params: Dict[str, Any] = None,
    mask_params: Dict[str, Any] = None,
    chimera_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process sequences through a unified pipeline.

    Args:
        fasta_content: Input FASTA sequences
        pipeline: List of processing steps (qc, dereplicate, mask, chimera)
                 Default: ["qc", "dereplicate", "mask", "chimera"] (full comprehensive QC)
        qc_params: Parameters for QC step
        derep_params: Parameters for dereplication step
        mask_params: Parameters for masking step
        chimera_params: Parameters for chimera detection step

    Returns:
        Dict with processed FASTA and cumulative statistics
    """
    if pipeline is None:
        pipeline = ["qc", "dereplicate", "mask", "chimera"]

    logger.info(f"Processing pipeline: {pipeline}")

    # CRITICAL FIX: Clean sequences first to remove gap characters and invalid chars
    logger.info("Pre-processing: Cleaning sequences (removing gap characters)")
    fasta_content = clean_sequences(fasta_content)
    logger.info(f"After cleaning: {count_sequences(fasta_content)} sequences")

    # Initialize parameters with defaults
    qc_params = qc_params or {}
    derep_params = derep_params or {}
    mask_params = mask_params or {}
    chimera_params = chimera_params or {}

    current_fasta = fasta_content
    all_stats = {
        "input_sequences": count_sequences(fasta_content),
        "pipeline": pipeline,
        "steps": []
    }

    try:
        # Execute pipeline steps in order
        for step in pipeline:
            logger.info(f"Executing pipeline step: {step}")

            if step == "qc":
                result = await fasta_qc_impl(current_fasta, **qc_params)
                if "error" in result:
                    return result
                current_fasta = result["cleaned_fasta"]
                all_stats["steps"].append({"qc": result["stats"]})

            elif step == "dereplicate":
                result = await dereplicate_sequences_impl(current_fasta, **derep_params)
                if "error" in result:
                    return result
                current_fasta = result["dereplicated_fasta"]
                all_stats["steps"].append({"dereplicate": result["stats"]})

            elif step == "mask":
                result = await mask_low_complexity_impl(current_fasta, **mask_params)
                if "error" in result:
                    return result
                current_fasta = result["masked_fasta"]
                all_stats["steps"].append({"mask": result["stats"]})

            elif step == "chimera":
                result = await detect_chimeras_impl(current_fasta, **chimera_params)
                if "error" in result:
                    return result
                current_fasta = result["non_chimeric_fasta"]
                all_stats["steps"].append({"chimera": result["stats"]})

            else:
                logger.warning(f"Unknown pipeline step: {step}")

        all_stats["output_sequences"] = count_sequences(current_fasta)
        all_stats["total_removed"] = all_stats["input_sequences"] - all_stats["output_sequences"]
        all_stats["retention_percent"] = round(
            (all_stats["output_sequences"] / all_stats["input_sequences"]) * 100, 2
        ) if all_stats["input_sequences"] > 0 else 0

        logger.info(f"Pipeline complete: {all_stats['input_sequences']} -> {all_stats['output_sequences']} sequences")

        return {
            "processed_fasta": current_fasta,
            "stats": all_stats,
            "success": True
        }

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}\n{traceback.format_exc()}")
        return {
            "error": str(e),
            "processed_fasta": "",
            "stats": all_stats
        }


# ============================================================================
# MCP Tool Handlers
# ============================================================================

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List all available MCP tools."""
    return [
        types.Tool(
            name="fasta_qc",
            description="Perform quality control on FASTA sequences: filter by length, N-content, and remove duplicates",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input FASTA sequences"
                    },
                    "min_length": {
                        "type": "integer",
                        "default": Config.DEFAULT_MIN_LENGTH,
                        "description": "Minimum sequence length"
                    },
                    "max_n_percent": {
                        "type": "number",
                        "default": Config.DEFAULT_MAX_N_PERCENT,
                        "description": "Maximum percentage of N bases allowed"
                    },
                    "remove_duplicates": {
                        "type": "boolean",
                        "default": True,
                        "description": "Remove duplicate sequences"
                    }
                },
                "required": ["fasta_content"]
            }
        ),

        types.Tool(
            name="dereplicate_sequences",
            description="Remove duplicate or near-duplicate sequences using clustering",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input FASTA sequences"
                    },
                    "identity_threshold": {
                        "type": "number",
                        "default": Config.DEFAULT_IDENTITY_THRESHOLD,
                        "description": "Identity threshold for clustering (0.0-1.0)"
                    },
                    "per_species": {
                        "type": "boolean",
                        "default": True,
                        "description": "Group by species before dereplication"
                    }
                },
                "required": ["fasta_content"]
            }
        ),

        types.Tool(
            name="mask_low_complexity",
            description="Mask low-complexity regions and repeats using DUST algorithm",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input FASTA sequences"
                    },
                    "mask_repeats": {
                        "type": "boolean",
                        "default": True,
                        "description": "Mask repetitive regions"
                    },
                    "mask_homopolymers": {
                        "type": "boolean",
                        "default": True,
                        "description": "Mask homopolymer runs"
                    },
                    "min_complexity": {
                        "type": "number",
                        "default": Config.DEFAULT_MIN_COMPLEXITY,
                        "description": "Minimum complexity score"
                    }
                },
                "required": ["fasta_content"]
            }
        ),

        types.Tool(
            name="detect_chimeras",
            description="Detect and remove chimeric sequences using UCHIME algorithm",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input FASTA sequences"
                    },
                    "reference_db": {
                        "type": "string",
                        "enum": ["auto", "silva", "unite"],
                        "default": "auto",
                        "description": "Reference database for chimera detection"
                    },
                    "abundance_threshold": {
                        "type": "number",
                        "default": Config.DEFAULT_ABUNDANCE_SKEW,
                        "description": "Abundance skew threshold"
                    }
                },
                "required": ["fasta_content"]
            }
        ),

        types.Tool(
            name="process_sequences",
            description="Process sequences through a unified pipeline combining multiple steps",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input FASTA sequences"
                    },
                    "pipeline": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["qc", "dereplicate", "mask", "chimera"]
                        },
                        "default": ["qc", "dereplicate", "mask", "chimera"],
                        "description": "List of processing steps to execute in order. Default is full comprehensive QC pipeline."
                    },
                    "qc_params": {
                        "type": "object",
                        "description": "Parameters for QC step"
                    },
                    "derep_params": {
                        "type": "object",
                        "description": "Parameters for dereplication step"
                    },
                    "mask_params": {
                        "type": "object",
                        "description": "Parameters for masking step"
                    },
                    "chimera_params": {
                        "type": "object",
                        "description": "Parameters for chimera detection step"
                    }
                },
                "required": ["fasta_content"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool execution requests."""
    logger.info(f"Tool called: {name}")
    logger.debug(f"Arguments: {json.dumps(arguments, indent=2)}")

    try:
        if name == "fasta_qc":
            result = await fasta_qc_impl(**arguments)
        elif name == "dereplicate_sequences":
            result = await dereplicate_sequences_impl(**arguments)
        elif name == "mask_low_complexity":
            result = await mask_low_complexity_impl(**arguments)
        elif name == "detect_chimeras":
            result = await detect_chimeras_impl(**arguments)
        elif name == "process_sequences":
            result = await process_sequences_impl(**arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        # CRITICAL FIX: If result contains an error, raise an exception
        # This ensures the MCP protocol sets isError: True
        if "error" in result and result["error"]:
            error_msg = result["error"]
            logger.error(f"Tool {name} returned error: {error_msg}")
            raise RuntimeError(error_msg)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logger.error(f"Tool execution error: {name}: {str(e)}\n{traceback.format_exc()}")
        # Return error as exception to set isError: True
        raise RuntimeError(f"Tool {name} failed: {str(e)}")


# ============================================================================
# Server Main
# ============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting Processing MCP Server")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ndiag-processing-server",
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
        logger.error(f"Server error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
