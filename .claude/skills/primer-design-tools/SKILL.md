---
name: primer-design-tools
description: Primer3, ViennaRNA, and qPCR primer design patterns for species-specific molecular diagnostics. Use when designing primers, analyzing secondary structures, calculating Tm, or discovering signature regions for qPCR assays.
---

# Primer Design Tools Guidelines for mdk_mcp

## Purpose

Establish consistent patterns for primer design in the mdk_mcp platform, specifically for Phase 4 (Design Server). Covers Primer3 integration, ViennaRNA secondary structure analysis, signature region discovery, and oligo quality control for qPCR assays.

## When to Use This Skill

Automatically activates when:
- Designing qPCR primers with Primer3
- Analyzing secondary structures with ViennaRNA
- Calculating melting temperature (Tm)
- Discovering signature regions in alignments
- Performing specificity analysis
- Quality control for oligonucleotides
- Working with the Design Server tools

---

## Quick Reference

### Design Server MCP Tools (Phase 4)

```python
# 1. Find signature regions
find_signature_regions(
    alignment_path="alignment.fasta",
    target_group=["species1", "species2"],
    off_target_group=["species3", "species4"],
    window_size=150,
    step_size=10,
    min_conservation=90.0,
    min_divergence=30.0
)

# 2. Analyze specificity
analyze_specificity(
    alignment_path="alignment.fasta",
    target_sequences=["seq1", "seq2"],
    off_target_sequences=["seq3", "seq4"],
    region_start=100,
    region_end=250
)

# 3. Rank candidate regions
rank_regions(
    regions=[...],
    weights={
        "conservation_score": 0.4,
        "divergence_score": 0.4,
        "complexity_score": 0.2
    }
)

# 4. Design primers with Primer3
primer3_design(
    sequence="ATGC...",
    target_region=(100, 150),
    primer_opt_size=20,
    primer_min_size=18,
    primer_max_size=27,
    primer_opt_tm=60.0,
    primer_min_tm=57.0,
    primer_max_tm=63.0,
    primer_opt_gc=50.0,
    primer_min_gc=40.0,
    primer_max_gc=60.0,
    product_size_range="80-150"
)

# 5. Quality control with ViennaRNA
oligo_qc(
    sequence="ATGCTAGCTA",
    check_hairpin=True,
    check_homodimer=True,
    check_heterodimer=True,
    temperature=37.0
)

# 6. Complete pipeline
design_primers_complete(
    alignment_path="alignment.fasta",
    target_group=["species1"],
    off_target_group=["species2"],
    num_primers=3
)
```

---

## Core Concepts

### 1. Signature Region Discovery

**Goal**: Find conserved regions in target species that are divergent from off-targets.

**Scoring Criteria**:
- **Conservation Score**: % identity within target group (target: >90%)
- **Divergence Score**: % difference from off-target group (target: >30%)
- **Complexity Score**: Sequence complexity (avoid repeats, homopolymers)
- **GC Content**: Optimal range 40-60%

**Pattern**:
```python
async def find_signature_regions_pattern(
    alignment_path: str,
    target_ids: list[str],
    off_target_ids: list[str]
) -> list[dict]:
    """
    Sliding window analysis to identify signature regions.

    Returns list of candidate regions with scores:
    {
        "start": 100,
        "end": 250,
        "conservation_score": 95.2,
        "divergence_score": 38.5,
        "complexity_score": 0.85,
        "gc_content": 52.3,
        "total_score": 89.7
    }
    """
    # 1. Load alignment
    alignment = AlignIO.read(alignment_path, "fasta")

    # 2. Sliding window analysis
    regions = []
    for start in range(0, len(alignment[0]), step_size):
        end = start + window_size
        window = alignment[:, start:end]

        # 3. Calculate scores
        conservation = calculate_conservation(window, target_ids)
        divergence = calculate_divergence(window, target_ids, off_target_ids)
        complexity = calculate_complexity(window)
        gc = calculate_gc_content(window)

        # 4. Filter candidates
        if conservation >= min_conservation and divergence >= min_divergence:
            regions.append({
                "start": start,
                "end": end,
                "conservation_score": conservation,
                "divergence_score": divergence,
                "complexity_score": complexity,
                "gc_content": gc,
                "total_score": weighted_score(conservation, divergence, complexity)
            })

    return sorted(regions, key=lambda x: x["total_score"], reverse=True)
```

### 2. Primer3 Integration

**Tool**: Primer3 (v2.6.1+)
**Python Wrapper**: primer3-py
**Purpose**: Design PCR primers with complex constraint satisfaction

#### ✅ GOOD: Complete Primer3 Configuration

```python
import primer3
import logging

logger = logging.getLogger(__name__)

async def design_primers_primer3(
    sequence: str,
    target_region: tuple[int, int] = None,
    num_return: int = 5,
    # Size constraints
    primer_opt_size: int = 20,
    primer_min_size: int = 18,
    primer_max_size: int = 27,
    # Tm constraints
    primer_opt_tm: float = 60.0,
    primer_min_tm: float = 57.0,
    primer_max_tm: float = 63.0,
    primer_max_tm_diff: float = 2.0,  # Max Tm difference between pair
    # GC constraints
    primer_opt_gc: float = 50.0,
    primer_min_gc: float = 40.0,
    primer_max_gc: float = 60.0,
    # Product size
    product_size_range: str = "80-150",
    # Secondary structure
    primer_max_hairpin_th: float = 47.0,  # ΔG threshold (kcal/mol)
    primer_max_self_any_th: float = 47.0,
    primer_max_self_end_th: float = 47.0,
    primer_pair_max_compl_any_th: float = 47.0,
    primer_pair_max_compl_end_th: float = 47.0
) -> dict:
    """
    Design primers using Primer3 with comprehensive constraints.

    Args:
        sequence: Template sequence (must be uppercase ATGC)
        target_region: Optional (start, length) tuple for target region
        num_return: Number of primer pairs to return

    Returns:
        Dictionary with primer results from Primer3
    """
    # Validate sequence
    if not sequence or not all(c in 'ATGCN' for c in sequence.upper()):
        raise ValueError("Sequence must contain only ATGCN characters")

    sequence = sequence.upper()

    # Build Primer3 input
    primer3_input = {
        'SEQUENCE_ID': 'candidate',
        'SEQUENCE_TEMPLATE': sequence,
        'PRIMER_NUM_RETURN': num_return,

        # Size constraints
        'PRIMER_OPT_SIZE': primer_opt_size,
        'PRIMER_MIN_SIZE': primer_min_size,
        'PRIMER_MAX_SIZE': primer_max_size,

        # Tm constraints
        'PRIMER_OPT_TM': primer_opt_tm,
        'PRIMER_MIN_TM': primer_min_tm,
        'PRIMER_MAX_TM': primer_max_tm,
        'PRIMER_PAIR_MAX_DIFF_TM': primer_max_tm_diff,

        # GC constraints
        'PRIMER_OPT_GC_PERCENT': primer_opt_gc,
        'PRIMER_MIN_GC': primer_min_gc,
        'PRIMER_MAX_GC': primer_max_gc,

        # Product size (list of ranges)
        'PRIMER_PRODUCT_SIZE_RANGE': [[int(x) for x in r.split('-')]
                                       for r in product_size_range.split(',')],

        # Secondary structure thresholds
        'PRIMER_MAX_HAIRPIN_TH': primer_max_hairpin_th,
        'PRIMER_MAX_SELF_ANY_TH': primer_max_self_any_th,
        'PRIMER_MAX_SELF_END_TH': primer_max_self_end_th,
        'PRIMER_PAIR_MAX_COMPL_ANY_TH': primer_pair_max_compl_any_th,
        'PRIMER_PAIR_MAX_COMPL_END_TH': primer_pair_max_compl_end_th,

        # Task
        'PRIMER_TASK': 'generic',
        'PRIMER_PICK_LEFT_PRIMER': 1,
        'PRIMER_PICK_INTERNAL_OLIGO': 0,
        'PRIMER_PICK_RIGHT_PRIMER': 1,
    }

    # Add target region if specified
    if target_region:
        start, length = target_region
        primer3_input['SEQUENCE_TARGET'] = [start, length]

    try:
        # Run Primer3
        logger.info(f"Running Primer3 on {len(sequence)} bp sequence...")
        result = primer3.bindings.design_primers(primer3_input)

        # Check for errors
        if 'PRIMER_ERROR' in result:
            error_msg = result['PRIMER_ERROR']
            logger.error(f"Primer3 error: {error_msg}")
            raise RuntimeError(f"Primer3 failed: {error_msg}")

        # Check if primers found
        num_returned = result.get('PRIMER_PAIR_NUM_RETURNED', 0)
        if num_returned == 0:
            logger.warning("Primer3 found no suitable primer pairs")
            return {
                "success": False,
                "message": "No suitable primers found. Try relaxing constraints.",
                "primer_pairs": []
            }

        logger.info(f"Primer3 returned {num_returned} primer pairs")
        return {
            "success": True,
            "num_returned": num_returned,
            "primer_pairs": parse_primer3_results(result),
            "raw_result": result
        }

    except Exception as e:
        logger.error(f"Primer3 execution failed: {e}")
        raise RuntimeError(f"Primer3 error: {e}")

def parse_primer3_results(result: dict) -> list[dict]:
    """Parse Primer3 output into structured format."""
    pairs = []
    num_pairs = result.get('PRIMER_PAIR_NUM_RETURNED', 0)

    for i in range(num_pairs):
        pair = {
            "rank": i + 1,
            "left_primer": {
                "sequence": result.get(f'PRIMER_LEFT_{i}_SEQUENCE', ''),
                "start": result.get(f'PRIMER_LEFT_{i}', [None, None])[0],
                "length": result.get(f'PRIMER_LEFT_{i}', [None, None])[1],
                "tm": result.get(f'PRIMER_LEFT_{i}_TM', None),
                "gc": result.get(f'PRIMER_LEFT_{i}_GC_PERCENT', None),
                "hairpin": result.get(f'PRIMER_LEFT_{i}_HAIRPIN_TH', None),
                "self_any": result.get(f'PRIMER_LEFT_{i}_SELF_ANY_TH', None),
                "self_end": result.get(f'PRIMER_LEFT_{i}_SELF_END_TH', None)
            },
            "right_primer": {
                "sequence": result.get(f'PRIMER_RIGHT_{i}_SEQUENCE', ''),
                "start": result.get(f'PRIMER_RIGHT_{i}', [None, None])[0],
                "length": result.get(f'PRIMER_RIGHT_{i}', [None, None])[1],
                "tm": result.get(f'PRIMER_RIGHT_{i}_TM', None),
                "gc": result.get(f'PRIMER_RIGHT_{i}_GC_PERCENT', None),
                "hairpin": result.get(f'PRIMER_RIGHT_{i}_HAIRPIN_TH', None),
                "self_any": result.get(f'PRIMER_RIGHT_{i}_SELF_ANY_TH', None),
                "self_end": result.get(f'PRIMER_RIGHT_{i}_SELF_END_TH', None)
            },
            "product": {
                "size": result.get(f'PRIMER_PAIR_{i}_PRODUCT_SIZE', None),
                "tm_diff": result.get(f'PRIMER_PAIR_{i}_DIFF_TM', None),
                "compl_any": result.get(f'PRIMER_PAIR_{i}_COMPL_ANY_TH', None),
                "compl_end": result.get(f'PRIMER_PAIR_{i}_COMPL_END_TH', None)
            },
            "penalty": result.get(f'PRIMER_PAIR_{i}_PENALTY', None)
        }
        pairs.append(pair)

    return pairs
```

#### ❌ BAD: Minimal Primer3 usage

```python
# ❌ Don't do this - missing critical constraints!
result = primer3.design_primers({
    'SEQUENCE_TEMPLATE': sequence
})
# No size constraints, no Tm constraints, no secondary structure checks!
```

### 3. ViennaRNA: Secondary Structure Analysis

**Tool**: ViennaRNA (v2.6.4)
**Purpose**: Predict RNA/DNA secondary structures and calculate thermodynamics

#### ✅ GOOD: ViennaRNA Integration for Oligo QC

```python
import subprocess
import asyncio
from typing import Optional

async def calculate_hairpin_tm(sequence: str, temp: float = 37.0) -> Optional[float]:
    """
    Calculate hairpin formation energy using ViennaRNA RNAfold.

    Args:
        sequence: DNA oligonucleotide sequence
        temp: Temperature in Celsius (default 37°C)

    Returns:
        ΔG in kcal/mol (more negative = more stable structure)
        Returns None if no structure predicted
    """
    try:
        # Run RNAfold (DNA mode)
        process = await asyncio.create_subprocess_exec(
            'RNAfold',
            '--noPS',  # Don't create PostScript output
            '--temp', str(temp),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate(input=sequence.encode())

        if process.returncode != 0:
            logger.error(f"RNAfold failed: {stderr.decode()}")
            return None

        # Parse output: "> sequence\n structure (energy)"
        output = stdout.decode().strip()
        lines = output.split('\n')

        if len(lines) < 2:
            return None

        # Extract energy from structure line
        # Format: ".(((...)))." (-3.40)
        structure_line = lines[1]
        if '(' in structure_line:
            energy_str = structure_line.split('(')[1].split(')')[0]
            energy = float(energy_str)
            logger.debug(f"Hairpin ΔG: {energy} kcal/mol")
            return energy

        return None  # No structure

    except Exception as e:
        logger.error(f"Hairpin calculation failed: {e}")
        return None

async def check_primer_dimers(
    primer1: str,
    primer2: str,
    temp: float = 37.0
) -> tuple[Optional[float], Optional[float]]:
    """
    Check for homodimer and heterodimer formation.

    Returns:
        (homodimer_dG, heterodimer_dG) in kcal/mol
    """
    # Homodimer: primer1 + reverse_complement(primer1)
    rc1 = reverse_complement(primer1)
    homodimer_dg = await calculate_duplex_energy(primer1, rc1, temp)

    # Heterodimer: primer1 + reverse_complement(primer2)
    rc2 = reverse_complement(primer2)
    heterodimer_dg = await calculate_duplex_energy(primer1, rc2, temp)

    return homodimer_dg, heterodimer_dg

async def calculate_duplex_energy(
    seq1: str,
    seq2: str,
    temp: float = 37.0
) -> Optional[float]:
    """Calculate duplex formation energy using ViennaRNA RNAduplex."""
    try:
        process = await asyncio.create_subprocess_exec(
            'RNAduplex',
            '--temp', str(temp),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Input: seq1\nseq2
        input_data = f"{seq1}\n{seq2}\n"
        stdout, stderr = await process.communicate(input=input_data.encode())

        if process.returncode != 0:
            return None

        # Parse output
        output = stdout.decode().strip()
        if '(' in output:
            energy_str = output.split('(')[1].split(')')[0]
            return float(energy_str)

        return None

    except Exception as e:
        logger.error(f"Duplex calculation failed: {e}")
        return None

def reverse_complement(seq: str) -> str:
    """Get reverse complement of DNA sequence."""
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(complement.get(base, 'N') for base in reversed(seq.upper()))
```

### 4. Melting Temperature (Tm) Calculation

**Methods**:
1. **Basic** (GC count): Tm = 4(G+C) + 2(A+T)
2. **Salt-adjusted** (nearest-neighbor): Use primer3 or BioPython
3. **Santa Lucia** (most accurate): Thermodynamic parameters

#### ✅ GOOD: Accurate Tm Calculation

```python
from Bio.SeqUtils import MeltingTemp as mt
from Bio.Seq import Seq

def calculate_tm_accurate(
    sequence: str,
    dna_conc: float = 50.0,  # nM primer concentration
    na_conc: float = 50.0,   # mM Na+ concentration
    mg_conc: float = 1.5,    # mM Mg2+ concentration
    dntp_conc: float = 0.2   # mM dNTP concentration
) -> dict:
    """
    Calculate accurate Tm using multiple methods.

    Returns dict with different Tm calculations and parameters.
    """
    seq = Seq(sequence.upper())

    # Method 1: Basic (Wallace rule)
    tm_basic = 4 * (seq.count('G') + seq.count('C')) + \
               2 * (seq.count('A') + seq.count('T'))

    # Method 2: Nearest-neighbor (salt-adjusted)
    tm_nn = mt.Tm_NN(
        seq,
        Na=na_conc,
        Mg=mg_conc,
        dNTPs=dntp_conc,
        nn_table=mt.DNA_NN4  # SantaLucia 2004 parameters
    )

    # Method 3: GC content adjusted
    tm_gc = mt.Tm_GC(seq, Na=na_conc)

    # Calculate GC content
    gc_content = (seq.count('G') + seq.count('C')) / len(seq) * 100

    return {
        "sequence": str(seq),
        "length": len(seq),
        "gc_content": round(gc_content, 2),
        "tm_basic": round(tm_basic, 2),
        "tm_nn_santaLucia": round(tm_nn, 2),
        "tm_gc_adjusted": round(tm_gc, 2),
        "recommended_tm": round(tm_nn, 2),  # Use NN as most accurate
        "parameters": {
            "primer_conc_nM": dna_conc,
            "Na_conc_mM": na_conc,
            "Mg_conc_mM": mg_conc,
            "dNTP_conc_mM": dntp_conc
        }
    }
```

### 5. Complete Quality Control Pipeline

#### ✅ GOOD: Comprehensive Oligo QC

```python
async def oligo_quality_control(
    sequence: str,
    oligo_type: str = "primer",  # primer, probe
    temp: float = 37.0
) -> dict:
    """
    Complete quality control for oligonucleotide.

    Checks:
    1. Length (18-27 bp for primers)
    2. GC content (40-60%)
    3. Tm (57-63°C optimal)
    4. 3' GC clamp (1-2 GC in last 5 bases)
    5. Poly-X runs (avoid >4 identical bases)
    6. Hairpin formation (ΔG > -3 kcal/mol)
    7. Self-dimer (ΔG > -6 kcal/mol)

    Returns:
        Dictionary with QC results and pass/fail status
    """
    results = {
        "sequence": sequence,
        "length": len(sequence),
        "checks": {},
        "warnings": [],
        "errors": [],
        "overall_pass": True
    }

    # 1. Length check
    if oligo_type == "primer":
        if 18 <= len(sequence) <= 27:
            results["checks"]["length"] = "✅ PASS"
        elif 16 <= len(sequence) < 18 or 27 < len(sequence) <= 30:
            results["checks"]["length"] = "⚠️  WARNING"
            results["warnings"].append(f"Length {len(sequence)} bp is suboptimal")
        else:
            results["checks"]["length"] = "❌ FAIL"
            results["errors"].append(f"Length {len(sequence)} bp out of range")
            results["overall_pass"] = False

    # 2. GC content
    gc_count = sequence.upper().count('G') + sequence.upper().count('C')
    gc_percent = (gc_count / len(sequence)) * 100
    results["gc_content"] = round(gc_percent, 2)

    if 40 <= gc_percent <= 60:
        results["checks"]["gc_content"] = "✅ PASS"
    elif 35 <= gc_percent < 40 or 60 < gc_percent <= 65:
        results["checks"]["gc_content"] = "⚠️  WARNING"
        results["warnings"].append(f"GC content {gc_percent:.1f}% is suboptimal")
    else:
        results["checks"]["gc_content"] = "❌ FAIL"
        results["errors"].append(f"GC content {gc_percent:.1f}% out of range")
        results["overall_pass"] = False

    # 3. Tm calculation
    tm_data = calculate_tm_accurate(sequence)
    results["tm"] = tm_data["recommended_tm"]

    if 57 <= tm_data["recommended_tm"] <= 63:
        results["checks"]["tm"] = "✅ PASS"
    elif 55 <= tm_data["recommended_tm"] < 57 or 63 < tm_data["recommended_tm"] <= 65:
        results["checks"]["tm"] = "⚠️  WARNING"
        results["warnings"].append(f"Tm {tm_data['recommended_tm']:.1f}°C is suboptimal")
    else:
        results["checks"]["tm"] = "❌ FAIL"
        results["errors"].append(f"Tm {tm_data['recommended_tm']:.1f}°C out of range")

    # 4. 3' GC clamp
    last_5 = sequence[-5:].upper()
    gc_in_last_5 = last_5.count('G') + last_5.count('C')
    results["gc_clamp"] = gc_in_last_5

    if 1 <= gc_in_last_5 <= 2:
        results["checks"]["gc_clamp"] = "✅ PASS"
    elif gc_in_last_5 == 0 or gc_in_last_5 == 3:
        results["checks"]["gc_clamp"] = "⚠️  WARNING"
        results["warnings"].append(f"GC clamp ({gc_in_last_5} GC) is suboptimal")
    else:
        results["checks"]["gc_clamp"] = "❌ FAIL"
        results["errors"].append(f"GC clamp ({gc_in_last_5} GC) problematic")

    # 5. Poly-X runs
    max_run = find_max_homopolymer(sequence)
    results["max_homopolymer"] = max_run

    if max_run <= 4:
        results["checks"]["homopolymer"] = "✅ PASS"
    elif max_run == 5:
        results["checks"]["homopolymer"] = "⚠️  WARNING"
        results["warnings"].append(f"Homopolymer run of {max_run}")
    else:
        results["checks"]["homopolymer"] = "❌ FAIL"
        results["errors"].append(f"Homopolymer run of {max_run} too long")
        results["overall_pass"] = False

    # 6. Hairpin formation
    hairpin_dg = await calculate_hairpin_tm(sequence, temp)
    results["hairpin_dg"] = hairpin_dg

    if hairpin_dg is None or hairpin_dg > -3.0:
        results["checks"]["hairpin"] = "✅ PASS"
    elif -3.0 >= hairpin_dg > -5.0:
        results["checks"]["hairpin"] = "⚠️  WARNING"
        results["warnings"].append(f"Hairpin ΔG = {hairpin_dg:.2f} kcal/mol")
    else:
        results["checks"]["hairpin"] = "❌ FAIL"
        results["errors"].append(f"Hairpin ΔG = {hairpin_dg:.2f} kcal/mol too stable")

    # 7. Self-dimer
    homodimer_dg, _ = await check_primer_dimers(sequence, sequence, temp)
    results["homodimer_dg"] = homodimer_dg

    if homodimer_dg is None or homodimer_dg > -6.0:
        results["checks"]["self_dimer"] = "✅ PASS"
    elif -6.0 >= homodimer_dg > -8.0:
        results["checks"]["self_dimer"] = "⚠️  WARNING"
        results["warnings"].append(f"Self-dimer ΔG = {homodimer_dg:.2f} kcal/mol")
    else:
        results["checks"]["self_dimer"] = "❌ FAIL"
        results["errors"].append(f"Self-dimer ΔG = {homodimer_dg:.2f} kcal/mol too stable")

    return results

def find_max_homopolymer(sequence: str) -> int:
    """Find longest homopolymer run."""
    if not sequence:
        return 0

    max_run = 1
    current_run = 1

    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i-1]:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    return max_run
```

---

## Design Server Workflow Integration

### Complete Pipeline Pattern

```python
async def design_qpcr_assay_complete(
    alignment_path: str,
    target_species: list[str],
    off_target_species: list[str],
    num_primers: int = 3
) -> dict:
    """
    End-to-end qPCR assay design pipeline.

    Steps:
    1. Find signature regions
    2. Analyze specificity
    3. Rank candidate regions
    4. Design primers for top regions
    5. Quality control
    6. Return best primers
    """
    results = {
        "target_species": target_species,
        "off_target_species": off_target_species,
        "signature_regions": [],
        "primer_sets": []
    }

    # Step 1: Find signature regions
    logger.info("Step 1: Finding signature regions...")
    regions = await find_signature_regions(
        alignment_path=alignment_path,
        target_group=target_species,
        off_target_group=off_target_species,
        window_size=150,
        step_size=10,
        min_conservation=90.0,
        min_divergence=30.0
    )

    if not regions:
        return {
            "success": False,
            "message": "No suitable signature regions found",
            "regions": []
        }

    results["signature_regions"] = regions[:10]  # Top 10
    logger.info(f"Found {len(regions)} signature regions")

    # Step 2: Design primers for top regions
    logger.info(f"Step 2: Designing primers for top {num_primers} regions...")

    for i, region in enumerate(regions[:num_primers]):
        logger.info(f"Designing primers for region {i+1}...")

        # Extract sequence for this region
        consensus_seq = extract_consensus(alignment_path, region["start"], region["end"])

        # Design with Primer3
        primer_result = await design_primers_primer3(
            sequence=consensus_seq,
            target_region=(25, 100),  # Focus on middle of region
            num_return=3
        )

        if not primer_result["success"]:
            logger.warning(f"No primers for region {i+1}")
            continue

        # Step 3: Quality control for each primer pair
        for pair in primer_result["primer_pairs"]:
            left_qc = await oligo_quality_control(pair["left_primer"]["sequence"])
            right_qc = await oligo_quality_control(pair["right_primer"]["sequence"])

            # Check heterodimer
            hetero_dg, _ = await check_primer_dimers(
                pair["left_primer"]["sequence"],
                pair["right_primer"]["sequence"]
            )

            pair["left_qc"] = left_qc
            pair["right_qc"] = right_qc
            pair["heterodimer_dg"] = hetero_dg
            pair["region"] = region

            # Overall pass?
            pair["overall_pass"] = (
                left_qc["overall_pass"] and
                right_qc["overall_pass"] and
                (hetero_dg is None or hetero_dg > -6.0)
            )

        results["primer_sets"].extend(primer_result["primer_pairs"])

    # Step 4: Rank final primer sets
    passing_primers = [p for p in results["primer_sets"] if p["overall_pass"]]

    if not passing_primers:
        logger.warning("No primer pairs passed QC")
        return {
            "success": False,
            "message": "No primers passed quality control",
            "primer_sets": results["primer_sets"]
        }

    # Sort by region score and primer penalty
    passing_primers.sort(
        key=lambda x: (x["region"]["total_score"], -x["penalty"]),
        reverse=True
    )

    results["primer_sets"] = passing_primers
    results["success"] = True
    results["message"] = f"Designed {len(passing_primers)} high-quality primer sets"

    logger.info(f"✅ Complete! {len(passing_primers)} primer sets passed QC")
    return results
```

---

## Common Patterns

### Pattern 1: Validate Primer Design Inputs

```python
def validate_primer_design_inputs(
    sequence: str,
    product_size_range: str,
    primer_size_range: tuple[int, int, int]
) -> None:
    """Validate inputs before Primer3 call."""
    # Check sequence
    if not sequence:
        raise ValueError("Sequence cannot be empty")

    if len(sequence) < 100:
        raise ValueError(f"Sequence too short ({len(sequence)} bp), need >100 bp")

    invalid_chars = set(sequence.upper()) - set('ATGCN')
    if invalid_chars:
        raise ValueError(f"Invalid characters in sequence: {invalid_chars}")

    # Check product size
    try:
        ranges = [tuple(map(int, r.split('-'))) for r in product_size_range.split(',')]
        for min_size, max_size in ranges:
            if min_size >= max_size:
                raise ValueError(f"Invalid product size range: {min_size}-{max_size}")
    except:
        raise ValueError(f"Invalid product_size_range format: {product_size_range}")

    # Check primer sizes
    min_size, opt_size, max_size = primer_size_range
    if not (min_size <= opt_size <= max_size):
        raise ValueError(f"Invalid primer size range: {primer_size_range}")
```

### Pattern 2: Format Primer Results for Output

```python
def format_primer_results(primers: list[dict], output_format: str = "table") -> str:
    """Format primer design results."""
    if output_format == "table":
        lines = ["=" * 80]
        lines.append("qPCR PRIMER DESIGN RESULTS")
        lines.append("=" * 80)

        for i, pair in enumerate(primers, 1):
            lines.append(f"\nPrimer Pair {i} (Penalty: {pair['penalty']:.2f})")
            lines.append("-" * 80)
            lines.append(f"Forward: 5'- {pair['left_primer']['sequence']} -3'")
            lines.append(f"  Position: {pair['left_primer']['start']}")
            lines.append(f"  Tm: {pair['left_primer']['tm']:.1f}°C")
            lines.append(f"  GC: {pair['left_primer']['gc']:.1f}%")
            lines.append(f"  Length: {pair['left_primer']['length']} bp")

            lines.append(f"\nReverse: 5'- {pair['right_primer']['sequence']} -3'")
            lines.append(f"  Position: {pair['right_primer']['start']}")
            lines.append(f"  Tm: {pair['right_primer']['tm']:.1f}°C")
            lines.append(f"  GC: {pair['right_primer']['gc']:.1f}%")
            lines.append(f"  Length: {pair['right_primer']['length']} bp")

            lines.append(f"\nProduct Size: {pair['product']['size']} bp")
            lines.append(f"Tm Difference: {pair['product']['tm_diff']:.2f}°C")

            if pair.get("overall_pass"):
                lines.append("\n✅ QC Status: PASS")
            else:
                lines.append("\n❌ QC Status: FAIL")

        return '\n'.join(lines)

    elif output_format == "csv":
        import csv
        from io import StringIO
        buffer = StringIO()
        writer = csv.writer(buffer)

        writer.writerow([
            "Rank", "Forward_Seq", "Forward_Tm", "Reverse_Seq", "Reverse_Tm",
            "Product_Size", "Tm_Diff", "QC_Pass"
        ])

        for i, pair in enumerate(primers, 1):
            writer.writerow([
                i,
                pair['left_primer']['sequence'],
                f"{pair['left_primer']['tm']:.1f}",
                pair['right_primer']['sequence'],
                f"{pair['right_primer']['tm']:.1f}",
                pair['product']['size'],
                f"{pair['product']['tm_diff']:.2f}",
                "PASS" if pair.get("overall_pass") else "FAIL"
            ])

        return buffer.getvalue()
```

---

## Testing Patterns

### Unit Test Template

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_find_signature_regions():
    """Test signature region discovery."""
    regions = await find_signature_regions(
        alignment_path="test_data/test_alignment.fasta",
        target_group=["seq1", "seq2"],
        off_target_group=["seq3", "seq4"],
        window_size=50,
        step_size=10,
        min_conservation=80.0,
        min_divergence=20.0
    )

    assert len(regions) > 0
    assert all("conservation_score" in r for r in regions)
    assert all(r["conservation_score"] >= 80.0 for r in regions)

@pytest.mark.asyncio
async def test_primer3_design():
    """Test Primer3 integration."""
    result = await design_primers_primer3(
        sequence="ATGC" * 50,  # 200 bp
        num_return=3
    )

    assert result["success"] == True
    assert result["num_returned"] > 0
    assert len(result["primer_pairs"]) > 0

@pytest.mark.asyncio
async def test_oligo_qc_pass():
    """Test oligo passing QC."""
    # Good primer
    result = await oligo_quality_control("ATGCTAGCTAGCTAGCTAG")  # 19 bp

    assert result["overall_pass"] == True
    assert result["checks"]["length"] == "✅ PASS"

@pytest.mark.asyncio
async def test_oligo_qc_fail():
    """Test oligo failing QC."""
    # Bad primer (too short, high homopolymer)
    result = await oligo_quality_control("AAAAAAAAAA")  # 10 bp, polyA

    assert result["overall_pass"] == False
    assert len(result["errors"]) > 0
```

---

## Common Gotchas

### ❌ AVOID: Not checking Primer3 errors

```python
# ❌ Bad
result = primer3.design_primers(input_dict)
primers = result['PRIMER_LEFT_0_SEQUENCE']  # May not exist!

# ✅ Good
result = primer3.design_primers(input_dict)
if 'PRIMER_ERROR' in result:
    raise RuntimeError(f"Primer3 error: {result['PRIMER_ERROR']}")
if result.get('PRIMER_PAIR_NUM_RETURNED', 0) == 0:
    return "No primers found"
```

### ❌ AVOID: Ignoring secondary structure

```python
# ❌ Bad - no structure checks
primers = design_primers(sequence)

# ✅ Good - check hairpins and dimers
primers = design_primers(sequence)
for pair in primers:
    hairpin_dg = check_hairpin(pair['left'])
    if hairpin_dg < -3.0:
        # Reject or flag
```

### ❌ AVOID: Using incorrect Tm calculations

```python
# ❌ Bad - basic formula only
tm = 4 * (gc_count) + 2 * (at_count)

# ✅ Good - nearest-neighbor with salt correction
tm = mt.Tm_NN(seq, Na=50, Mg=1.5, dNTPs=0.2)
```

---

## Quick Command Reference

```python
# Find signature regions
regions = await find_signature_regions(alignment, targets, off_targets)

# Design with Primer3
result = await design_primers_primer3(sequence, target_region=(50, 100))

# Check secondary structure
hairpin_dg = await calculate_hairpin_tm(primer_seq)
homodimer_dg, heterodimer_dg = await check_primer_dimers(fwd, rev)

# Calculate Tm
tm_data = calculate_tm_accurate(primer_seq)

# Quality control
qc_result = await oligo_quality_control(primer_seq)

# Complete pipeline
assay = await design_qpcr_assay_complete(alignment, targets, off_targets)
```

---

## Remember

- **Validate inputs** before calling Primer3 (sequence, ranges)
- **Check Primer3 errors** - tool may fail or return 0 primers
- **Use nearest-neighbor Tm** with salt correction (not basic formula)
- **Always check secondary structures** (hairpins, dimers)
- **QC thresholds**: Tm 57-63°C, GC 40-60%, length 18-27bp
- **Test with real data** - synthetic sequences may behave differently
- **ViennaRNA async calls** - use asyncio.create_subprocess_exec
- **Signature regions**: balance conservation (>90%) vs divergence (>30%)
- **Document assumptions** - salt concentrations, temperature, etc.

Your primer design code should be **robust, well-validated, and production-ready** for diagnostic qPCR assay development.
