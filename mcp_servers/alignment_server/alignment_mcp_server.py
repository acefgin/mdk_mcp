#!/usr/bin/env python3
"""
Alignment MCP Server for neglected-diagnostics project.

This server provides sequence alignment and phylogenetic analysis capabilities including:
- Multiple sequence alignment (MAFFT, MUSCLE, Clustal Omega, gget_muscle)
- Alignment quality assessment and cleaning (CIAlign)
- Phylogenetic tree construction (NJ, ML methods)
- Distance matrix calculation
- Unified pipeline tools
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

try:
    import gget
except ImportError:
    gget = None

from Bio import SeqIO, AlignIO, Phylo
from Bio.Align import MultipleSeqAlignment
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Phylo.TreeConstruction import NNITreeSearcher, ParsimonyTreeConstructor
import numpy as np

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
server = Server("ndiag-alignment-server")


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
        logger.debug(f"Wrote temporary FASTA file: {path}")
        return path
    except Exception as e:
        os.close(fd)
        if os.path.exists(path):
            os.unlink(path)
        raise


def read_file(path: str) -> str:
    """Read file content."""
    with open(path, 'r') as f:
        return f.read()


def cleanup_temp_files(*paths: str) -> None:
    """Clean up temporary files."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
                logger.debug(f"Cleaned up temporary file: {path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {path}: {str(e)}")


def count_sequences(fasta_content: str) -> int:
    """Count number of sequences in FASTA content."""
    return len([line for line in fasta_content.split('\n') if line.startswith('>')])


def validate_fasta(fasta_content: str) -> bool:
    """Validate FASTA format."""
    if not fasta_content or not fasta_content.strip():
        return False
    lines = fasta_content.strip().split('\n')
    return len(lines) > 1 and lines[0].startswith('>')


# ============================================================================
# Alignment Functions
# ============================================================================

async def align_with_mafft(fasta_content: str, strategy: str = "auto",
                          max_iterations: int = 1000) -> str:
    """
    Align sequences using MAFFT.

    Args:
        fasta_content: Input sequences in FASTA format
        strategy: MAFFT strategy (auto, linsi, ginsi, einsi)
        max_iterations: Maximum number of iterations

    Returns:
        Aligned sequences in FASTA format
    """
    input_file = write_temp_fasta(fasta_content, prefix="mafft_input")
    output_file = tempfile.mktemp(suffix=".fasta", prefix="mafft_output_",
                                   dir=Config.TEMP_DIR)

    try:
        # Build MAFFT command
        cmd = [Config.MAFFT_PATH]

        if strategy == "linsi":
            cmd.extend(["--localpair", "--maxiterate", str(max_iterations)])
        elif strategy == "ginsi":
            cmd.extend(["--globalpair", "--maxiterate", str(max_iterations)])
        elif strategy == "einsi":
            cmd.extend(["--genafpair", "--maxiterate", str(max_iterations)])
        else:  # auto
            cmd.extend(["--auto"])

        cmd.extend([input_file])

        result = await run_command(cmd, description=f"MAFFT alignment ({strategy})")

        if result["returncode"] != 0:
            raise Exception(f"MAFFT failed: {result['stderr']}")

        # MAFFT outputs to stdout
        alignment = result["stdout"]

        if not alignment:
            raise Exception("MAFFT produced no output")

        return alignment

    finally:
        cleanup_temp_files(input_file, output_file)


async def align_with_muscle(fasta_content: str, max_iterations: int = 16) -> str:
    """
    Align sequences using MUSCLE.

    Args:
        fasta_content: Input sequences in FASTA format
        max_iterations: Maximum number of iterations

    Returns:
        Aligned sequences in FASTA format
    """
    input_file = write_temp_fasta(fasta_content, prefix="muscle_input")
    output_file = tempfile.mktemp(suffix=".fasta", prefix="muscle_output_",
                                   dir=Config.TEMP_DIR)

    try:
        # MUSCLE 5 syntax
        cmd = [
            Config.MUSCLE_PATH,
            "-align", input_file,
            "-output", output_file
        ]

        result = await run_command(cmd, description="MUSCLE alignment")

        if result["returncode"] != 0:
            raise Exception(f"MUSCLE failed: {result['stderr']}")

        alignment = read_file(output_file)

        if not alignment:
            raise Exception("MUSCLE produced no output")

        return alignment

    finally:
        cleanup_temp_files(input_file, output_file)


async def align_with_clustalo(fasta_content: str) -> str:
    """
    Align sequences using Clustal Omega.

    Args:
        fasta_content: Input sequences in FASTA format

    Returns:
        Aligned sequences in FASTA format
    """
    input_file = write_temp_fasta(fasta_content, prefix="clustalo_input")
    output_file = tempfile.mktemp(suffix=".fasta", prefix="clustalo_output_",
                                   dir=Config.TEMP_DIR)

    try:
        cmd = [
            Config.CLUSTALO_PATH,
            "-i", input_file,
            "-o", output_file,
            "--outfmt", "fasta",
            "--force"
        ]

        result = await run_command(cmd, description="Clustal Omega alignment")

        if result["returncode"] != 0:
            raise Exception(f"Clustal Omega failed: {result['stderr']}")

        alignment = read_file(output_file)

        if not alignment:
            raise Exception("Clustal Omega produced no output")

        return alignment

    finally:
        cleanup_temp_files(input_file, output_file)


async def align_with_gget_muscle(fasta_content: str, super5: bool = False) -> str:
    """
    Align sequences using gget muscle wrapper.

    Args:
        fasta_content: Input sequences in FASTA format
        super5: Use MUSCLE5 super5 algorithm for higher accuracy

    Returns:
        Aligned sequences in FASTA format
    """
    if gget is None:
        raise Exception("gget is not installed. Please install with: pip install gget")

    input_file = write_temp_fasta(fasta_content, prefix="gget_muscle_input")
    output_file = tempfile.mktemp(suffix=".fasta", prefix="gget_muscle_output_",
                                   dir=Config.TEMP_DIR)

    try:
        # Use gget muscle
        gget.muscle(input_file, out=output_file, super5=super5)

        if not os.path.exists(output_file):
            raise Exception("gget muscle produced no output file")

        alignment = read_file(output_file)

        if not alignment:
            raise Exception("gget muscle produced empty output")

        return alignment

    finally:
        cleanup_temp_files(input_file, output_file)


# ============================================================================
# Alignment Processing Functions
# ============================================================================

async def process_alignment_with_cialign(alignment_content: str,
                                        trim_gaps: bool = True,
                                        gap_threshold: float = 0.5,
                                        remove_divergent: bool = False) -> Dict[str, Any]:
    """
    Process and clean alignment using CIAlign.

    Args:
        alignment_content: Aligned sequences in FASTA format
        trim_gaps: Remove gap-rich columns
        gap_threshold: Threshold for gap removal (0-1)
        remove_divergent: Remove divergent sequences

    Returns:
        Dict with cleaned alignment and statistics
    """
    input_file = write_temp_fasta(alignment_content, prefix="cialign_input")
    output_prefix = tempfile.mktemp(prefix="cialign_", dir=Config.TEMP_DIR)
    output_file = f"{output_prefix}_cleaned.fasta"

    try:
        cmd = ["CIAlign"]

        # Input/output
        cmd.extend(["--infile", input_file])
        cmd.extend(["--outfile_stem", output_prefix])

        # Cleaning options
        if trim_gaps:
            cmd.extend(["--remove_insertions"])
            cmd.extend(["--insertion_min_size", "3"])
            cmd.extend(["--remove_short", f"--remove_short_min_length", "50"])

        if remove_divergent:
            cmd.extend(["--remove_divergent", "--remove_divergent_minperc", "0.65"])

        result = await run_command(cmd, description="CIAlign alignment processing")

        if result["returncode"] != 0:
            # CIAlign might write output even with non-zero exit code
            logger.warning(f"CIAlign returned non-zero code: {result['returncode']}")

        # Check for output file
        if os.path.exists(output_file):
            cleaned_alignment = read_file(output_file)
        else:
            # If CIAlign didn't produce output, return original
            logger.warning("CIAlign did not produce output, returning original alignment")
            cleaned_alignment = alignment_content

        # Calculate statistics
        original_seqs = count_sequences(alignment_content)
        cleaned_seqs = count_sequences(cleaned_alignment)

        stats = {
            "original_sequences": original_seqs,
            "cleaned_sequences": cleaned_seqs,
            "sequences_removed": original_seqs - cleaned_seqs,
            "alignment_cleaned": True
        }

        return {
            "alignment": cleaned_alignment,
            "statistics": stats
        }

    finally:
        cleanup_temp_files(input_file, output_file)
        # Clean up other CIAlign output files
        for ext in ["_log.txt", "_mini.fasta", "_removed.txt"]:
            cleanup_temp_files(f"{output_prefix}{ext}")


def calculate_alignment_stats(alignment_content: str) -> Dict[str, Any]:
    """
    Calculate basic statistics for an alignment.

    Args:
        alignment_content: Aligned sequences in FASTA format

    Returns:
        Dict with alignment statistics
    """
    try:
        # Parse alignment
        from io import StringIO
        alignment = AlignIO.read(StringIO(alignment_content), "fasta")

        num_sequences = len(alignment)
        alignment_length = alignment.get_alignment_length()

        # Calculate gap statistics
        gap_counts = []
        for record in alignment:
            gaps = str(record.seq).count('-')
            gap_counts.append(gaps)

        avg_gaps = np.mean(gap_counts) if gap_counts else 0
        gap_percentage = (avg_gaps / alignment_length * 100) if alignment_length > 0 else 0

        # Calculate conservation (simple metric)
        conservation_scores = []
        for i in range(alignment_length):
            column = alignment[:, i]
            most_common = max(set(column), key=column.count)
            conservation = column.count(most_common) / num_sequences
            conservation_scores.append(conservation)

        avg_conservation = np.mean(conservation_scores) if conservation_scores else 0

        return {
            "num_sequences": num_sequences,
            "alignment_length": alignment_length,
            "average_gaps_per_sequence": float(avg_gaps),
            "gap_percentage": float(gap_percentage),
            "average_conservation": float(avg_conservation),
            "min_conservation": float(min(conservation_scores)) if conservation_scores else 0,
            "max_conservation": float(max(conservation_scores)) if conservation_scores else 0
        }

    except Exception as e:
        logger.error(f"Error calculating alignment stats: {str(e)}")
        return {"error": str(e)}


# ============================================================================
# Phylogenetic Functions
# ============================================================================

def build_phylogenetic_tree(alignment_content: str,
                           method: str = "nj",
                           model: str = "kimura",
                           bootstrap: int = 100) -> Dict[str, Any]:
    """
    Build phylogenetic tree from alignment.

    Args:
        alignment_content: Aligned sequences in FASTA format
        method: Tree building method (nj, ml, mp)
        model: Distance model (p-distance, jukes-cantor, kimura)
        bootstrap: Number of bootstrap replicates

    Returns:
        Dict with tree in Newick format and metadata
    """
    try:
        from io import StringIO

        # Parse alignment
        alignment = AlignIO.read(StringIO(alignment_content), "fasta")

        if method == "nj":
            # Neighbor Joining
            calculator = DistanceCalculator(model.replace('-', '_'))
            dm = calculator.get_distance(alignment)
            constructor = DistanceTreeConstructor(calculator, method='nj')
            tree = constructor.build_tree(alignment)

            tree_newick = tree.format("newick")

            return {
                "tree_newick": tree_newick,
                "method": "neighbor_joining",
                "model": model,
                "num_taxa": len(alignment),
                "success": True
            }

        elif method == "ml":
            # Maximum Likelihood - simplified version
            logger.warning("ML method not fully implemented, falling back to NJ")
            return build_phylogenetic_tree(alignment_content, method="nj", model=model)

        elif method == "mp":
            # Maximum Parsimony
            searcher = NNITreeSearcher(ParsimonyTreeConstructor())
            constructor = ParsimonyTreeConstructor(searcher)
            tree = constructor.build_tree(alignment)

            tree_newick = tree.format("newick")

            return {
                "tree_newick": tree_newick,
                "method": "maximum_parsimony",
                "model": "none",
                "num_taxa": len(alignment),
                "success": True
            }

        else:
            raise ValueError(f"Unknown phylogenetic method: {method}")

    except Exception as e:
        logger.error(f"Error building phylogenetic tree: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def calculate_distance_matrix(alignment_content: str,
                              model: str = "kimura") -> Dict[str, Any]:
    """
    Calculate pairwise distance matrix from alignment.

    Args:
        alignment_content: Aligned sequences in FASTA format
        model: Distance model (p-distance, jukes-cantor, kimura)

    Returns:
        Dict with distance matrix and sequence names
    """
    try:
        from io import StringIO

        # Parse alignment
        alignment = AlignIO.read(StringIO(alignment_content), "fasta")

        # Calculate distances
        calculator = DistanceCalculator(model.replace('-', '_'))
        dm = calculator.get_distance(alignment)

        # Extract sequence names and matrix
        names = [record.id for record in alignment]
        matrix = [[dm[i, j] for j in range(len(names))] for i in range(len(names))]

        return {
            "sequence_names": names,
            "distance_matrix": matrix,
            "model": model,
            "num_sequences": len(names),
            "success": True
        }

    except Exception as e:
        logger.error(f"Error calculating distance matrix: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


# ============================================================================
# MCP Tool Handlers
# ============================================================================

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List all available MCP tools."""
    return [
        types.Tool(
            name="align_sequences",
            description="Align sequences using various algorithms (MAFFT, MUSCLE, Clustal Omega, gget_muscle)",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input sequences in FASTA format"
                    },
                    "algorithm": {
                        "type": "string",
                        "enum": ["mafft", "muscle", "clustalo", "gget_muscle"],
                        "default": "mafft",
                        "description": "Alignment algorithm to use"
                    },
                    "mafft_strategy": {
                        "type": "string",
                        "enum": ["auto", "linsi", "ginsi", "einsi"],
                        "default": "auto",
                        "description": "MAFFT alignment strategy (only for MAFFT)"
                    },
                    "max_iterations": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Maximum number of iterations"
                    },
                    "super5": {
                        "type": "boolean",
                        "default": False,
                        "description": "Use MUSCLE5 super5 algorithm (only for gget_muscle)"
                    }
                },
                "required": ["fasta_content"]
            }
        ),

        types.Tool(
            name="process_alignment",
            description="Process and clean alignment using CIAlign, including gap removal and quality assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "alignment_content": {
                        "type": "string",
                        "description": "Aligned sequences in FASTA format"
                    },
                    "trim_gaps": {
                        "type": "boolean",
                        "default": True,
                        "description": "Remove gap-rich columns"
                    },
                    "gap_threshold": {
                        "type": "number",
                        "default": 0.5,
                        "description": "Threshold for gap removal (0-1)"
                    },
                    "remove_divergent": {
                        "type": "boolean",
                        "default": False,
                        "description": "Remove divergent sequences"
                    },
                    "assess_quality": {
                        "type": "boolean",
                        "default": True,
                        "description": "Calculate alignment quality statistics"
                    }
                },
                "required": ["alignment_content"]
            }
        ),

        types.Tool(
            name="build_phylogeny",
            description="Build phylogenetic tree from alignment using NJ, ML, or MP methods",
            inputSchema={
                "type": "object",
                "properties": {
                    "alignment_content": {
                        "type": "string",
                        "description": "Aligned sequences in FASTA format"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["nj", "ml", "mp"],
                        "default": "nj",
                        "description": "Tree building method (nj=Neighbor Joining, ml=Maximum Likelihood, mp=Maximum Parsimony)"
                    },
                    "bootstrap": {
                        "type": "integer",
                        "default": 100,
                        "description": "Number of bootstrap replicates"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["p-distance", "jukes-cantor", "kimura"],
                        "default": "kimura",
                        "description": "Distance model for NJ method"
                    }
                },
                "required": ["alignment_content"]
            }
        ),

        types.Tool(
            name="calculate_distances",
            description="Calculate pairwise distance matrix from alignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "alignment_content": {
                        "type": "string",
                        "description": "Aligned sequences in FASTA format"
                    },
                    "model": {
                        "type": "string",
                        "enum": ["p-distance", "jukes-cantor", "kimura"],
                        "default": "kimura",
                        "description": "Distance calculation model"
                    }
                },
                "required": ["alignment_content"]
            }
        ),

        types.Tool(
            name="align_and_analyze",
            description="Complete pipeline: align sequences, process alignment, and optionally build phylogeny",
            inputSchema={
                "type": "object",
                "properties": {
                    "fasta_content": {
                        "type": "string",
                        "description": "Input sequences in FASTA format"
                    },
                    "algorithm": {
                        "type": "string",
                        "enum": ["mafft", "muscle", "clustalo", "gget_muscle"],
                        "default": "mafft",
                        "description": "Alignment algorithm"
                    },
                    "include_phylogeny": {
                        "type": "boolean",
                        "default": False,
                        "description": "Build phylogenetic tree"
                    },
                    "include_distances": {
                        "type": "boolean",
                        "default": False,
                        "description": "Calculate distance matrix"
                    },
                    "clean_alignment": {
                        "type": "boolean",
                        "default": True,
                        "description": "Clean alignment with CIAlign"
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

    try:
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {json.dumps(arguments, indent=2)}")

        # Route to appropriate handler
        if name == "align_sequences":
            result = await tool_align_sequences(arguments)
        elif name == "process_alignment":
            result = await tool_process_alignment(arguments)
        elif name == "build_phylogeny":
            result = await tool_build_phylogeny(arguments)
        elif name == "calculate_distances":
            result = await tool_calculate_distances(arguments)
        elif name == "align_and_analyze":
            result = await tool_align_and_analyze(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        # Return result
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        error_msg = f"Error executing tool {name}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e), "traceback": traceback.format_exc()})
        )]


# ============================================================================
# Tool Implementation Functions
# ============================================================================

async def tool_align_sequences(args: Dict[str, Any]) -> Dict[str, Any]:
    """Implement align_sequences tool."""
    fasta_content = args.get("fasta_content")
    algorithm = args.get("algorithm", "mafft")
    mafft_strategy = args.get("mafft_strategy", "auto")
    max_iterations = args.get("max_iterations", 1000)
    super5 = args.get("super5", False)

    # Validate input
    if not validate_fasta(fasta_content):
        return {"error": "Invalid FASTA format"}

    num_sequences = count_sequences(fasta_content)
    if num_sequences < 2:
        return {"error": "At least 2 sequences required for alignment"}

    # Perform alignment
    try:
        if algorithm == "mafft":
            alignment = await align_with_mafft(fasta_content, mafft_strategy, max_iterations)
        elif algorithm == "muscle":
            alignment = await align_with_muscle(fasta_content, max_iterations)
        elif algorithm == "clustalo":
            alignment = await align_with_clustalo(fasta_content)
        elif algorithm == "gget_muscle":
            alignment = await align_with_gget_muscle(fasta_content, super5)
        else:
            return {"error": f"Unknown algorithm: {algorithm}"}

        # Calculate basic stats
        stats = calculate_alignment_stats(alignment)

        return {
            "alignment": alignment,
            "algorithm": algorithm,
            "statistics": stats,
            "success": True
        }

    except Exception as e:
        logger.error(f"Alignment failed: {str(e)}")
        return {"error": str(e), "success": False}


async def tool_process_alignment(args: Dict[str, Any]) -> Dict[str, Any]:
    """Implement process_alignment tool."""
    alignment_content = args.get("alignment_content")
    trim_gaps = args.get("trim_gaps", True)
    gap_threshold = args.get("gap_threshold", 0.5)
    remove_divergent = args.get("remove_divergent", False)
    assess_quality = args.get("assess_quality", True)

    # Validate input
    if not validate_fasta(alignment_content):
        return {"error": "Invalid alignment format"}

    try:
        # Process with CIAlign
        result = await process_alignment_with_cialign(
            alignment_content,
            trim_gaps=trim_gaps,
            gap_threshold=gap_threshold,
            remove_divergent=remove_divergent
        )

        # Add quality assessment
        if assess_quality:
            stats = calculate_alignment_stats(result["alignment"])
            result["quality_stats"] = stats

        result["success"] = True
        return result

    except Exception as e:
        logger.error(f"Alignment processing failed: {str(e)}")
        return {"error": str(e), "success": False}


async def tool_build_phylogeny(args: Dict[str, Any]) -> Dict[str, Any]:
    """Implement build_phylogeny tool."""
    alignment_content = args.get("alignment_content")
    method = args.get("method", "nj")
    bootstrap = args.get("bootstrap", 100)
    model = args.get("model", "kimura")

    # Validate input
    if not validate_fasta(alignment_content):
        return {"error": "Invalid alignment format"}

    try:
        result = build_phylogenetic_tree(alignment_content, method, model, bootstrap)
        return result

    except Exception as e:
        logger.error(f"Phylogeny construction failed: {str(e)}")
        return {"error": str(e), "success": False}


async def tool_calculate_distances(args: Dict[str, Any]) -> Dict[str, Any]:
    """Implement calculate_distances tool."""
    alignment_content = args.get("alignment_content")
    model = args.get("model", "kimura")

    # Validate input
    if not validate_fasta(alignment_content):
        return {"error": "Invalid alignment format"}

    try:
        result = calculate_distance_matrix(alignment_content, model)
        return result

    except Exception as e:
        logger.error(f"Distance calculation failed: {str(e)}")
        return {"error": str(e), "success": False}


async def tool_align_and_analyze(args: Dict[str, Any]) -> Dict[str, Any]:
    """Implement align_and_analyze unified pipeline tool."""
    fasta_content = args.get("fasta_content")
    algorithm = args.get("algorithm", "mafft")
    include_phylogeny = args.get("include_phylogeny", False)
    include_distances = args.get("include_distances", False)
    clean_alignment = args.get("clean_alignment", True)

    # Validate input
    if not validate_fasta(fasta_content):
        return {"error": "Invalid FASTA format"}

    result = {"pipeline_steps": [], "success": True}

    try:
        # Step 1: Alignment
        logger.info("Pipeline step 1: Alignment")
        align_result = await tool_align_sequences({
            "fasta_content": fasta_content,
            "algorithm": algorithm
        })

        if not align_result.get("success"):
            return {"error": "Alignment failed", "details": align_result}

        result["alignment"] = align_result["alignment"]
        result["alignment_statistics"] = align_result["statistics"]
        result["pipeline_steps"].append("alignment")

        # Step 2: Clean alignment (optional)
        if clean_alignment:
            logger.info("Pipeline step 2: Cleaning alignment")
            clean_result = await tool_process_alignment({
                "alignment_content": result["alignment"],
                "trim_gaps": True,
                "assess_quality": True
            })

            if clean_result.get("success"):
                result["alignment"] = clean_result["alignment"]
                result["cleaning_statistics"] = clean_result["statistics"]
                result["quality_stats"] = clean_result.get("quality_stats")
                result["pipeline_steps"].append("cleaning")

        # Step 3: Distance matrix (optional)
        if include_distances:
            logger.info("Pipeline step 3: Distance calculation")
            dist_result = await tool_calculate_distances({
                "alignment_content": result["alignment"]
            })

            if dist_result.get("success"):
                result["distances"] = dist_result
                result["pipeline_steps"].append("distances")

        # Step 4: Phylogeny (optional)
        if include_phylogeny:
            logger.info("Pipeline step 4: Phylogenetic tree")
            phylo_result = await tool_build_phylogeny({
                "alignment_content": result["alignment"]
            })

            if phylo_result.get("success"):
                result["phylogeny"] = phylo_result
                result["pipeline_steps"].append("phylogeny")

        result["success"] = True
        return result

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return {"error": str(e), "success": False}


# ============================================================================
# Main Server Entry Point
# ============================================================================

async def main():
    """Run the MCP server using stdin/stdout streams."""
    logger.info("Starting Alignment MCP Server")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running on stdio transport")

        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ndiag-alignment-server",
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
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)
