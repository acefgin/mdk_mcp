#!/usr/bin/env python3
"""
Design MCP Server for neglected-diagnostics project.

This server provides primer design and signature region discovery capabilities including:
- Signature region identification in alignments
- Specificity analysis for target vs off-target discrimination
- Multi-criteria region ranking
- Primer3 integration for qPCR primer design
- Oligonucleotide quality control
- End-to-end primer design pipeline
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import subprocess
from typing import Any, Dict, List, Optional, Union, Tuple
import traceback
from pathlib import Path
from collections import Counter
import math

try:
    import primer3
except ImportError:
    primer3 = None

from Bio import SeqIO, AlignIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Align import MultipleSeqAlignment
import numpy as np
import pandas as pd

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
server = Server("ndiag-design-server")


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_shannon_entropy(column: List[str]) -> float:
    """
    Calculate Shannon entropy for an alignment column.

    Args:
        column: List of characters in the alignment column

    Returns:
        Shannon entropy value (0 = perfectly conserved, higher = more variable)
    """
    # Filter out gaps
    bases = [c for c in column if c != '-']
    if not bases:
        return 0.0

    counts = Counter(bases)
    total = len(bases)
    entropy = 0.0

    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


def calculate_conservation(column: List[str]) -> float:
    """
    Calculate conservation score for an alignment column.

    Args:
        column: List of characters in the alignment column

    Returns:
        Conservation score (0-1, where 1 = perfectly conserved)
    """
    # Filter out gaps
    bases = [c.upper() for c in column if c != '-' and c != 'N']
    if not bases:
        return 0.0

    counts = Counter(bases)
    most_common_count = counts.most_common(1)[0][1]
    return most_common_count / len(bases)


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage."""
    seq_upper = sequence.upper()
    gc_count = seq_upper.count('G') + seq_upper.count('C')
    total = len([b for b in seq_upper if b in 'ATGC'])
    return (gc_count / total * 100) if total > 0 else 0.0


def calculate_complexity(sequence: str) -> float:
    """
    Calculate sequence complexity score (0-1).
    Based on nucleotide diversity and repeat content.
    """
    if not sequence:
        return 0.0

    seq_upper = sequence.upper().replace('-', '')
    if len(seq_upper) < 4:
        return 0.0

    # Nucleotide diversity
    counts = Counter(seq_upper)
    total = len(seq_upper)
    diversity = sum((count / total) ** 2 for count in counts.values())
    diversity_score = 1 - diversity

    # Check for simple repeats (dinucleotide, trinucleotide)
    max_repeat_fraction = 0.0
    for kmer_size in [2, 3]:
        if len(seq_upper) >= kmer_size:
            kmers = [seq_upper[i:i+kmer_size] for i in range(len(seq_upper) - kmer_size + 1)]
            kmer_counts = Counter(kmers)
            if kmers:
                max_kmer_count = max(kmer_counts.values())
                repeat_fraction = max_kmer_count / len(kmers)
                max_repeat_fraction = max(max_repeat_fraction, repeat_fraction)

    repeat_score = 1 - max_repeat_fraction

    # Combined complexity score
    complexity = (diversity_score * 0.6) + (repeat_score * 0.4)
    return complexity


def calculate_tm_basic(sequence: str, salt_conc: float = 50.0) -> float:
    """
    Calculate basic melting temperature using nearest-neighbor method.
    Simplified version - for production use primer3's calculation.

    Args:
        sequence: Oligonucleotide sequence
        salt_conc: Salt concentration in mM

    Returns:
        Estimated Tm in Celsius
    """
    if primer3:
        return primer3.calc_tm(sequence, mv_conc=salt_conc)

    # Fallback: Basic Wallace rule for short oligos
    seq_upper = sequence.upper()
    gc = seq_upper.count('G') + seq_upper.count('C')
    at = seq_upper.count('A') + seq_upper.count('T')

    if len(sequence) < 14:
        # Wallace rule
        tm = (at * 2) + (gc * 4)
    else:
        # Modified formula for longer sequences
        tm = 64.9 + 41 * (gc - 16.4) / len(sequence)

    # Salt correction (simplified)
    tm += 16.6 * math.log10(salt_conc / 1000.0)

    return tm


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


# ============================================================================
# Core Analysis Functions
# ============================================================================

async def find_signature_regions_impl(
    alignment_content: str,
    target_sequences: List[str],
    window_size: int = 150,
    step_size: int = 10,
    min_conservation: float = 0.8,
    min_divergence: float = 0.3
) -> Dict[str, Any]:
    """
    Find signature regions in an alignment that are conserved within
    target group but divergent from off-target group.

    Args:
        alignment_content: Alignment in FASTA format
        target_sequences: List of sequence IDs for target group
        window_size: Size of sliding window
        step_size: Step size for sliding window
        min_conservation: Minimum conservation within target group
        min_divergence: Minimum divergence from off-target group

    Returns:
        Dict with candidate regions and their scores
    """
    logger.info(f"Finding signature regions (window={window_size}, step={step_size})")

    try:
        # Parse alignment
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(alignment_content)
            temp_file = f.name

        try:
            alignment = AlignIO.read(temp_file, "fasta")
        finally:
            os.unlink(temp_file)

        # Separate target and off-target sequences
        target_seqs = []
        offtarget_seqs = []

        for record in alignment:
            is_target = any(target_id in record.id for target_id in target_sequences)
            if is_target:
                target_seqs.append(record)
            else:
                offtarget_seqs.append(record)

        if not target_seqs:
            return {
                "success": False,
                "error": "No target sequences found in alignment"
            }

        if not offtarget_seqs:
            logger.warning("No off-target sequences found, analyzing target group only")

        alignment_length = alignment.get_alignment_length()
        candidate_regions = []

        # Sliding window analysis
        for start in range(0, alignment_length - window_size + 1, step_size):
            end = start + window_size

            # Extract window from both groups
            target_window = [str(seq.seq[start:end]) for seq in target_seqs]
            offtarget_window = [str(seq.seq[start:end]) for seq in offtarget_seqs] if offtarget_seqs else []

            # Calculate conservation in target group
            target_conservation_scores = []
            for pos in range(window_size):
                column = [window[pos] for window in target_window if pos < len(window)]
                if column:
                    target_conservation_scores.append(calculate_conservation(column))

            avg_target_conservation = np.mean(target_conservation_scores) if target_conservation_scores else 0.0

            # Calculate divergence from off-target group
            if offtarget_window:
                divergence_scores = []
                for pos in range(window_size):
                    target_col = [window[pos] for window in target_window if pos < len(window)]
                    offtarget_col = [window[pos] for window in offtarget_window if pos < len(window)]

                    if target_col and offtarget_col:
                        # Calculate how different the columns are
                        target_consensus = Counter([c for c in target_col if c != '-']).most_common(1)
                        offtarget_consensus = Counter([c for c in offtarget_col if c != '-']).most_common(1)

                        if target_consensus and offtarget_consensus:
                            target_base = target_consensus[0][0]
                            offtarget_base = offtarget_consensus[0][0]

                            if target_base != offtarget_base:
                                divergence_scores.append(1.0)
                            else:
                                # Calculate proportion of differences
                                target_prop = target_consensus[0][1] / len([c for c in target_col if c != '-'])
                                offtarget_prop = offtarget_consensus[0][1] / len([c for c in offtarget_col if c != '-'])
                                divergence_scores.append(abs(target_prop - offtarget_prop))

                avg_divergence = np.mean(divergence_scores) if divergence_scores else 0.0
            else:
                avg_divergence = 1.0  # No off-target, can't calculate divergence

            # Get consensus sequence for the region
            consensus_seq = ""
            for pos in range(window_size):
                column = [window[pos] for window in target_window if pos < len(window)]
                bases = [c for c in column if c != '-']
                if bases:
                    consensus_seq += Counter(bases).most_common(1)[0][0]
                else:
                    consensus_seq += 'N'

            # Calculate additional metrics
            gc_content = calculate_gc_content(consensus_seq)
            complexity = calculate_complexity(consensus_seq)

            # Filter candidates
            if avg_target_conservation >= min_conservation and avg_divergence >= min_divergence:
                candidate_regions.append({
                    "start": start,
                    "end": end,
                    "conservation": round(avg_target_conservation, 3),
                    "divergence": round(avg_divergence, 3),
                    "gc_content": round(gc_content, 2),
                    "complexity": round(complexity, 3),
                    "consensus_sequence": consensus_seq,
                    "length": window_size
                })

        logger.info(f"Found {len(candidate_regions)} candidate signature regions")

        return {
            "success": True,
            "num_candidates": len(candidate_regions),
            "regions": candidate_regions,
            "target_count": len(target_seqs),
            "offtarget_count": len(offtarget_seqs),
            "alignment_length": alignment_length
        }

    except Exception as e:
        logger.error(f"Error in find_signature_regions: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_specificity_impl(
    candidate_regions: List[Dict[str, Any]],
    target_group: List[str],
    offtarget_group: List[str]
) -> Dict[str, Any]:
    """
    Analyze specificity of candidate regions.

    Args:
        candidate_regions: List of candidate region dicts from find_signature_regions
        target_group: List of target sequence IDs
        offtarget_group: List of off-target sequence IDs

    Returns:
        Dict with specificity-scored regions
    """
    logger.info(f"Analyzing specificity for {len(candidate_regions)} regions")

    try:
        scored_regions = []

        for region in candidate_regions:
            # Calculate specificity score based on existing metrics
            # Higher conservation in target + higher divergence from off-target = higher specificity
            conservation = region.get('conservation', 0.0)
            divergence = region.get('divergence', 0.0)
            complexity = region.get('complexity', 0.0)

            # Specificity score (0-1)
            specificity_score = (conservation * 0.5) + (divergence * 0.5)

            # Check for potential SNPs (regions with high divergence)
            has_potential_snps = divergence > 0.5

            scored_region = {
                **region,
                "specificity_score": round(specificity_score, 3),
                "has_potential_snps": has_potential_snps,
                "suitable_for_primers": specificity_score >= 0.6 and complexity >= 0.5
            }

            scored_regions.append(scored_region)

        # Sort by specificity score
        scored_regions.sort(key=lambda x: x['specificity_score'], reverse=True)

        logger.info(f"Specificity analysis complete. Top score: {scored_regions[0]['specificity_score'] if scored_regions else 0}")

        return {
            "success": True,
            "num_regions": len(scored_regions),
            "regions": scored_regions,
            "high_specificity_count": sum(1 for r in scored_regions if r['specificity_score'] >= 0.7)
        }

    except Exception as e:
        logger.error(f"Error in analyze_specificity: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def rank_regions_impl(
    scored_regions: List[Dict[str, Any]],
    weighting: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Rank regions using multi-criteria scoring.

    Args:
        scored_regions: List of scored region dicts
        weighting: Dict with weights for conservation, specificity, complexity

    Returns:
        Dict with ranked regions
    """
    logger.info(f"Ranking {len(scored_regions)} regions")

    # Default weights
    if weighting is None:
        weighting = {
            "conservation": Config.DEFAULT_WEIGHT_CONSERVATION,
            "specificity": Config.DEFAULT_WEIGHT_SPECIFICITY,
            "complexity": Config.DEFAULT_WEIGHT_COMPLEXITY
        }

    try:
        # Normalize weights
        total_weight = sum(weighting.values())
        if total_weight == 0:
            total_weight = 1.0
        normalized_weights = {k: v/total_weight for k, v in weighting.items()}

        ranked_regions = []

        for region in scored_regions:
            conservation = region.get('conservation', 0.0)
            specificity = region.get('specificity_score', 0.0)
            complexity = region.get('complexity', 0.0)

            # Calculate composite score
            composite_score = (
                conservation * normalized_weights.get('conservation', 0.4) +
                specificity * normalized_weights.get('specificity', 0.4) +
                complexity * normalized_weights.get('complexity', 0.2)
            )

            ranked_region = {
                **region,
                "composite_score": round(composite_score, 3),
                "rank": 0  # Will be set after sorting
            }

            ranked_regions.append(ranked_region)

        # Sort by composite score
        ranked_regions.sort(key=lambda x: x['composite_score'], reverse=True)

        # Assign ranks
        for i, region in enumerate(ranked_regions, 1):
            region['rank'] = i

        logger.info(f"Ranking complete. Top score: {ranked_regions[0]['composite_score'] if ranked_regions else 0}")

        return {
            "success": True,
            "num_regions": len(ranked_regions),
            "regions": ranked_regions,
            "weights_used": normalized_weights,
            "top_regions": ranked_regions[:10]  # Return top 10
        }

    except Exception as e:
        logger.error(f"Error in rank_regions: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def primer3_design_impl(
    template_fasta: str,
    target_regions: Optional[List[List[int]]] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Design primers using Primer3.

    Args:
        template_fasta: Template sequence in FASTA format
        target_regions: List of [start, end] positions for target regions
        constraints: Dict with primer design constraints

    Returns:
        Dict with designed primers
    """
    logger.info("Designing primers with Primer3")

    if not primer3:
        return {
            "success": False,
            "error": "primer3-py library not available"
        }

    try:
        # Parse template sequence
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(template_fasta)
            temp_file = f.name

        try:
            records = list(SeqIO.parse(temp_file, "fasta"))
        finally:
            os.unlink(temp_file)

        if not records:
            return {
                "success": False,
                "error": "No sequences found in template FASTA"
            }

        template_seq = str(records[0].seq).upper()

        # Set up Primer3 parameters
        if constraints is None:
            constraints = {}

        # Build sequence args
        seq_args = {
            'SEQUENCE_ID': records[0].id,
            'SEQUENCE_TEMPLATE': template_seq,
        }

        # Add target regions if specified
        if target_regions:
            seq_args['SEQUENCE_TARGET'] = target_regions

        # Build global args with defaults from config
        primer_size = constraints.get('primer_size', [
            Config.DEFAULT_PRIMER_SIZE_MIN,
            Config.DEFAULT_PRIMER_SIZE_OPT,
            Config.DEFAULT_PRIMER_SIZE_MAX
        ])

        tm_range = constraints.get('tm', [
            Config.DEFAULT_PRIMER_TM_MIN,
            Config.DEFAULT_PRIMER_TM_OPT,
            Config.DEFAULT_PRIMER_TM_MAX
        ])

        gc_range = constraints.get('gc_content', [
            Config.DEFAULT_PRIMER_GC_MIN,
            Config.DEFAULT_PRIMER_GC_OPT,
            Config.DEFAULT_PRIMER_GC_MAX
        ])

        product_size = constraints.get('product_size', [
            Config.DEFAULT_PRODUCT_SIZE_MIN,
            Config.DEFAULT_PRODUCT_SIZE_OPT,
            Config.DEFAULT_PRODUCT_SIZE_MAX
        ])

        global_args = {
            'PRIMER_OPT_SIZE': primer_size[1] if len(primer_size) > 1 else 22,
            'PRIMER_MIN_SIZE': primer_size[0] if len(primer_size) > 0 else 18,
            'PRIMER_MAX_SIZE': primer_size[2] if len(primer_size) > 2 else 27,
            'PRIMER_OPT_TM': tm_range[1] if len(tm_range) > 1 else 60.0,
            'PRIMER_MIN_TM': tm_range[0] if len(tm_range) > 0 else 57.0,
            'PRIMER_MAX_TM': tm_range[2] if len(tm_range) > 2 else 63.0,
            'PRIMER_MIN_GC': gc_range[0] if len(gc_range) > 0 else 40.0,
            'PRIMER_OPT_GC_PERCENT': gc_range[1] if len(gc_range) > 1 else 50.0,
            'PRIMER_MAX_GC': gc_range[2] if len(gc_range) > 2 else 60.0,
            'PRIMER_PRODUCT_SIZE_RANGE': [[product_size[0], product_size[2]]],
            'PRIMER_NUM_RETURN': constraints.get('num_return', 5),
        }

        # Run Primer3
        result = primer3.design_primers(seq_args, global_args)

        # Parse results
        num_returned = result.get('PRIMER_PAIR_NUM_RETURNED', 0)

        primers = []
        for i in range(num_returned):
            primer_pair = {
                "pair_id": i,
                "forward_sequence": result.get(f'PRIMER_LEFT_{i}_SEQUENCE', ''),
                "reverse_sequence": result.get(f'PRIMER_RIGHT_{i}_SEQUENCE', ''),
                "forward_tm": result.get(f'PRIMER_LEFT_{i}_TM', 0),
                "reverse_tm": result.get(f'PRIMER_RIGHT_{i}_TM', 0),
                "forward_gc": result.get(f'PRIMER_LEFT_{i}_GC_PERCENT', 0),
                "reverse_gc": result.get(f'PRIMER_RIGHT_{i}_GC_PERCENT', 0),
                "product_size": result.get(f'PRIMER_PAIR_{i}_PRODUCT_SIZE', 0),
                "forward_start": result.get(f'PRIMER_LEFT_{i}', [0, 0])[0],
                "reverse_start": result.get(f'PRIMER_RIGHT_{i}', [0, 0])[0],
                "penalty": result.get(f'PRIMER_PAIR_{i}_PENALTY', 0),
            }
            primers.append(primer_pair)

        logger.info(f"Primer3 designed {num_returned} primer pairs")

        return {
            "success": True,
            "num_primers": num_returned,
            "primers": primers,
            "template_id": records[0].id,
            "template_length": len(template_seq)
        }

    except Exception as e:
        logger.error(f"Error in primer3_design: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def oligo_qc_impl(
    sequence: str,
    salt_mM: float = 50.0,
    mg_mM: float = 2.0,
    oligo_conc_nM: float = 250.0
) -> Dict[str, Any]:
    """
    Perform quality control checks on oligonucleotide.

    Args:
        sequence: Oligonucleotide sequence
        salt_mM: Salt concentration in mM
        mg_mM: Magnesium concentration in mM
        oligo_conc_nM: Oligonucleotide concentration in nM

    Returns:
        Dict with QC metrics
    """
    logger.info(f"Running oligo QC for sequence of length {len(sequence)}")

    try:
        seq_upper = sequence.upper()

        # Basic metrics
        length = len(seq_upper)
        gc_content = calculate_gc_content(seq_upper)
        complexity = calculate_complexity(seq_upper)

        # Calculate Tm
        if primer3:
            tm = primer3.calc_tm(seq_upper, mv_conc=salt_mM, dv_conc=mg_mM, dntp_conc=0.0, dna_conc=oligo_conc_nM)
            hairpin = primer3.calc_hairpin(seq_upper, mv_conc=salt_mM, dv_conc=mg_mM)
            homodimer = primer3.calc_homodimer(seq_upper, mv_conc=salt_mM, dv_conc=mg_mM)

            hairpin_tm = hairpin.tm if hasattr(hairpin, 'tm') else 0.0
            homodimer_tm = homodimer.tm if hasattr(homodimer, 'tm') else 0.0
        else:
            tm = calculate_tm_basic(seq_upper, salt_mM)
            hairpin_tm = 0.0
            homodimer_tm = 0.0

        # Check for runs
        max_run = 0
        current_run = 1
        for i in range(1, len(seq_upper)):
            if seq_upper[i] == seq_upper[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1

        # Quality flags
        flags = []
        if gc_content < 40 or gc_content > 60:
            flags.append("GC_OUT_OF_RANGE")
        if complexity < 0.5:
            flags.append("LOW_COMPLEXITY")
        if max_run >= 4:
            flags.append("LONG_HOMOPOLYMER")
        if hairpin_tm > Config.DEFAULT_MAX_HAIRPIN_TM:
            flags.append("HAIRPIN_RISK")
        if homodimer_tm > Config.DEFAULT_MAX_DIMER_TM:
            flags.append("DIMER_RISK")
        if length < 18 or length > 30:
            flags.append("LENGTH_SUBOPTIMAL")

        qc_pass = len(flags) == 0

        result = {
            "success": True,
            "sequence": sequence,
            "length": length,
            "gc_content": round(gc_content, 2),
            "tm": round(tm, 2),
            "complexity": round(complexity, 3),
            "max_homopolymer": max_run,
            "hairpin_tm": round(hairpin_tm, 2),
            "homodimer_tm": round(homodimer_tm, 2),
            "qc_pass": qc_pass,
            "flags": flags
        }

        logger.info(f"Oligo QC complete. Pass: {qc_pass}")

        return result

    except Exception as e:
        logger.error(f"Error in oligo_qc: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


async def design_primers_complete_impl(
    alignment_content: str,
    target_sequences: List[str],
    offtarget_sequences: Optional[List[str]] = None,
    primer_constraints: Optional[Dict[str, Any]] = None,
    region_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Complete end-to-end primer design pipeline.

    Args:
        alignment_content: Alignment in FASTA format
        target_sequences: List of target sequence IDs
        offtarget_sequences: Optional list of off-target sequence IDs
        primer_constraints: Primer3 constraints
        region_params: Parameters for region discovery

    Returns:
        Dict with complete primer design results
    """
    logger.info("Running complete primer design pipeline")

    try:
        # Step 1: Find signature regions
        if region_params is None:
            region_params = {}

        window_size = region_params.get('window_size', Config.DEFAULT_WINDOW_SIZE)
        step_size = region_params.get('step_size', Config.DEFAULT_STEP_SIZE)
        min_conservation = region_params.get('min_conservation', Config.DEFAULT_MIN_CONSERVATION)
        min_divergence = region_params.get('min_divergence', Config.DEFAULT_MIN_DIVERGENCE)

        regions_result = await find_signature_regions_impl(
            alignment_content=alignment_content,
            target_sequences=target_sequences,
            window_size=window_size,
            step_size=step_size,
            min_conservation=min_conservation,
            min_divergence=min_divergence
        )

        if not regions_result.get('success'):
            return regions_result

        candidate_regions = regions_result.get('regions', [])

        if not candidate_regions:
            return {
                "success": False,
                "error": "No signature regions found matching criteria"
            }

        # Step 2: Analyze specificity
        target_group = target_sequences
        offtarget_group = offtarget_sequences if offtarget_sequences else []

        specificity_result = await analyze_specificity_impl(
            candidate_regions=candidate_regions,
            target_group=target_group,
            offtarget_group=offtarget_group
        )

        if not specificity_result.get('success'):
            return specificity_result

        scored_regions = specificity_result.get('regions', [])

        # Step 3: Rank regions
        ranking_result = await rank_regions_impl(scored_regions=scored_regions)

        if not ranking_result.get('success'):
            return ranking_result

        ranked_regions = ranking_result.get('regions', [])
        top_regions = ranked_regions[:5]  # Use top 5 regions for primer design

        # Step 4: Design primers for top regions
        # Get consensus sequence from alignment for template
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(alignment_content)
            temp_file = f.name

        try:
            alignment = AlignIO.read(temp_file, "fasta")
        finally:
            os.unlink(temp_file)

        # Create consensus sequence
        consensus_seq = ""
        alignment_length = alignment.get_alignment_length()
        for pos in range(alignment_length):
            column = [str(seq.seq[pos]) for seq in alignment]
            bases = [c for c in column if c != '-']
            if bases:
                consensus_seq += Counter(bases).most_common(1)[0][0]
            else:
                consensus_seq += 'N'

        # Create template FASTA
        template_fasta = f">consensus\n{consensus_seq}\n"

        # Prepare target regions for Primer3
        target_regions_list = [[region['start'], region['length']] for region in top_regions]

        primers_result = await primer3_design_impl(
            template_fasta=template_fasta,
            target_regions=target_regions_list,
            constraints=primer_constraints
        )

        if not primers_result.get('success'):
            return primers_result

        primers = primers_result.get('primers', [])

        # Step 5: QC each primer
        qc_results = []
        for i, primer_pair in enumerate(primers):
            forward_qc = await oligo_qc_impl(primer_pair['forward_sequence'])
            reverse_qc = await oligo_qc_impl(primer_pair['reverse_sequence'])

            qc_results.append({
                "pair_id": i,
                "forward_qc": forward_qc,
                "reverse_qc": reverse_qc,
                "both_pass": forward_qc.get('qc_pass', False) and reverse_qc.get('qc_pass', False)
            })

        # Combine results
        final_primers = []
        for primer, qc in zip(primers, qc_results):
            final_primers.append({
                **primer,
                "qc_results": qc,
                "recommended": qc['both_pass']
            })

        # Filter to recommended primers
        recommended_primers = [p for p in final_primers if p['recommended']]

        logger.info(f"Pipeline complete. {len(recommended_primers)} recommended primer pairs")

        return {
            "success": True,
            "pipeline_steps": {
                "regions_found": len(candidate_regions),
                "regions_analyzed": len(scored_regions),
                "regions_ranked": len(ranked_regions),
                "primers_designed": len(primers),
                "primers_recommended": len(recommended_primers)
            },
            "top_regions": top_regions,
            "primers": final_primers,
            "recommended_primers": recommended_primers
        }

    except Exception as e:
        logger.error(f"Error in design_primers_complete: {str(e)}")
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
            name="find_signature_regions",
            description="Find signature regions in an alignment that are conserved within target species but divergent from off-target species. Uses sliding window analysis to identify candidate primer design regions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alignment_content": {
                        "type": "string",
                        "description": "Multiple sequence alignment in FASTA format"
                    },
                    "target_sequences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of sequence IDs or patterns for target group"
                    },
                    "window_size": {
                        "type": "integer",
                        "description": "Size of sliding window in base pairs",
                        "default": 150
                    },
                    "step_size": {
                        "type": "integer",
                        "description": "Step size for sliding window",
                        "default": 10
                    },
                    "min_conservation": {
                        "type": "number",
                        "description": "Minimum conservation score within target group (0-1)",
                        "default": 0.8
                    },
                    "min_divergence": {
                        "type": "number",
                        "description": "Minimum divergence from off-target group (0-1)",
                        "default": 0.3
                    }
                },
                "required": ["alignment_content", "target_sequences"]
            }
        ),
        types.Tool(
            name="analyze_specificity",
            description="Analyze specificity of candidate regions by comparing conservation within target group versus divergence from off-target group. Identifies potential SNPs and suitable primer binding sites.",
            inputSchema={
                "type": "object",
                "properties": {
                    "candidate_regions": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of candidate region objects from find_signature_regions"
                    },
                    "target_group": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of target sequence IDs"
                    },
                    "offtarget_group": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of off-target sequence IDs"
                    }
                },
                "required": ["candidate_regions", "target_group", "offtarget_group"]
            }
        ),
        types.Tool(
            name="rank_regions",
            description="Rank candidate regions using multi-criteria scoring with configurable weights for conservation, specificity, and complexity. Returns prioritized list for primer design.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scored_regions": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of scored region objects from analyze_specificity"
                    },
                    "weighting": {
                        "type": "object",
                        "properties": {
                            "conservation": {"type": "number", "default": 0.4},
                            "specificity": {"type": "number", "default": 0.4},
                            "complexity": {"type": "number", "default": 0.2}
                        },
                        "description": "Weights for scoring criteria (will be normalized)"
                    }
                },
                "required": ["scored_regions"]
            }
        ),
        types.Tool(
            name="primer3_design",
            description="Design qPCR primers using Primer3. Supports configurable constraints for primer size, Tm, GC content, and product size. Can target specific regions or design genome-wide.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_fasta": {
                        "type": "string",
                        "description": "Template sequence in FASTA format"
                    },
                    "target_regions": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"}
                        },
                        "description": "List of [start, length] positions for target regions"
                    },
                    "constraints": {
                        "type": "object",
                        "properties": {
                            "primer_size": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "[min, opt, max] primer sizes",
                                "default": [18, 22, 27]
                            },
                            "tm": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "[min, opt, max] melting temperatures",
                                "default": [57, 60, 63]
                            },
                            "gc_content": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "[min, opt, max] GC percentages",
                                "default": [40, 50, 60]
                            },
                            "product_size": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "[min, opt, max] product sizes",
                                "default": [80, 150, 300]
                            },
                            "num_return": {
                                "type": "integer",
                                "description": "Number of primer pairs to return",
                                "default": 5
                            }
                        },
                        "description": "Primer3 design constraints"
                    }
                },
                "required": ["template_fasta"]
            }
        ),
        types.Tool(
            name="oligo_qc",
            description="Perform quality control checks on oligonucleotides including Tm calculation, secondary structure analysis (hairpins, dimers), GC content, and complexity assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Oligonucleotide sequence to check"
                    },
                    "salt_mM": {
                        "type": "number",
                        "description": "Salt (Na+) concentration in mM",
                        "default": 50.0
                    },
                    "mg_mM": {
                        "type": "number",
                        "description": "Magnesium (Mg2+) concentration in mM",
                        "default": 2.0
                    },
                    "oligo_conc_nM": {
                        "type": "number",
                        "description": "Oligonucleotide concentration in nM",
                        "default": 250.0
                    }
                },
                "required": ["sequence"]
            }
        ),
        types.Tool(
            name="design_primers_complete",
            description="End-to-end primer design pipeline that combines region discovery, specificity analysis, ranking, Primer3 design, and QC. Recommended for complete automated primer design workflows.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alignment_content": {
                        "type": "string",
                        "description": "Multiple sequence alignment in FASTA format"
                    },
                    "target_sequences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of target sequence IDs or patterns"
                    },
                    "offtarget_sequences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of off-target sequence IDs"
                    },
                    "primer_constraints": {
                        "type": "object",
                        "description": "Primer3 design constraints (same as primer3_design tool)"
                    },
                    "region_params": {
                        "type": "object",
                        "properties": {
                            "window_size": {"type": "integer", "default": 150},
                            "step_size": {"type": "integer", "default": 10},
                            "min_conservation": {"type": "number", "default": 0.8},
                            "min_divergence": {"type": "number", "default": 0.3}
                        },
                        "description": "Parameters for signature region discovery"
                    }
                },
                "required": ["alignment_content", "target_sequences"]
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
        if name == "find_signature_regions":
            result = await find_signature_regions_impl(**arguments)

        elif name == "analyze_specificity":
            result = await analyze_specificity_impl(**arguments)

        elif name == "rank_regions":
            result = await rank_regions_impl(**arguments)

        elif name == "primer3_design":
            result = await primer3_design_impl(**arguments)

        elif name == "oligo_qc":
            result = await oligo_qc_impl(**arguments)

        elif name == "design_primers_complete":
            result = await design_primers_complete_impl(**arguments)

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
    logger.info("Starting Design MCP Server...")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ndiag-design-server",
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
