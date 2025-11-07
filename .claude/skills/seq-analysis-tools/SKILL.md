---
name: seq-analysis-tools
description: CLI bioinformatics tool integration patterns for seqkit, vsearch, MAFFT, MUSCLE, and Clustal Omega. Use when working with subprocess calls to bioinformatics tools, parameter tuning, or output parsing.
---

# Sequence Analysis Tools Integration Guidelines

## Purpose

Establish consistent patterns for integrating CLI bioinformatics tools in mdk_mcp MCP servers. Covers subprocess management, async execution, parameter optimization, and output parsing for seqkit, vsearch, MAFFT, MUSCLE, and Clustal Omega.

## When to Use This Skill

Automatically activates when:
- Running seqkit, vsearch, MAFFT, MUSCLE, or Clustal Omega
- Working with subprocess calls to CLI tools
- Parsing tool output
- Handling tool exit codes and errors
- Optimizing tool parameters

---

## Core Tools Overview

### Used in mdk_mcp:

| Tool | Server | Purpose | Version |
|------|--------|---------|---------|
| **seqkit** | Processing | FASTA/Q manipulation, statistics | 2.6.1 |
| **vsearch** | Processing | Clustering, dereplication, masking | 2.25.0 |
| **MAFFT** | Alignment | Multiple sequence alignment | 7.505 |
| **MUSCLE** | Alignment | Multiple sequence alignment | 5.1 |
| **Clustal Omega** | Alignment | Multiple sequence alignment | 1.2.4 |

---

## Pattern 1: Async Subprocess Execution

### ✅ GOOD: Proper Async Subprocess Pattern

```python
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def run_tool_async(
    command: list[str],
    input_file: str = None,
    output_file: str = None,
    stdin_data: bytes = None,
    timeout: int = 300
) -> tuple[int, str, str]:
    """
    Run bioinformatics tool asynchronously.

    Args:
        command: Command and arguments as list
        input_file: Optional input file path
        output_file: Optional output file path
        stdin_data: Optional data to pass via stdin
        timeout: Timeout in seconds (default 300)

    Returns:
        Tuple of (return_code, stdout, stderr)

    Raises:
        asyncio.TimeoutError: If tool execution exceeds timeout
        RuntimeError: If tool returns non-zero exit code
    """
    # Validate input file exists
    if input_file and not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Build full command
    full_command = command.copy()
    if input_file:
        full_command.append(input_file)

    logger.info(f"Running: {' '.join(full_command)}")

    try:
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=asyncio.subprocess.PIPE if stdin_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for completion with timeout
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=stdin_data),
            timeout=timeout
        )

        # Decode output
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')

        # Check exit code
        if process.returncode != 0:
            logger.error(f"Tool failed with exit code {process.returncode}")
            logger.error(f"STDERR: {stderr_str}")
            raise RuntimeError(
                f"Tool execution failed (exit {process.returncode}): {stderr_str}"
            )

        # Save output if file specified
        if output_file:
            Path(output_file).write_text(stdout_str)
            logger.info(f"Output saved to: {output_file}")

        logger.info(f"Tool completed successfully")
        return process.returncode, stdout_str, stderr_str

    except asyncio.TimeoutError:
        logger.error(f"Tool exceeded timeout of {timeout}s")
        process.kill()
        raise asyncio.TimeoutError(f"Tool execution timed out after {timeout}s")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### ❌ BAD: Blocking Subprocess

```python
# ❌ Don't do this - blocks async event loop!
import subprocess
result = subprocess.run(['mafft', input_file], capture_output=True)
```

---

## Tool 1: seqkit Integration

**Purpose**: Fast FASTA/Q manipulation and statistics
**Location**: Processing Server
**Documentation**: https://bioinf.shenwei.me/seqkit/

### Common seqkit Commands

#### 1. FASTA Statistics

```python
async def seqkit_stats(fasta_path: str) -> dict:
    """
    Get sequence statistics using seqkit stats.

    Returns dict with: num_seqs, sum_len, min_len, avg_len, max_len
    """
    command = ['seqkit', 'stats', '-T', '-a', fasta_path]
    # -T: tabular output
    # -a: all stats

    returncode, stdout, stderr = await run_tool_async(command)

    # Parse tabular output
    lines = stdout.strip().split('\n')
    if len(lines) < 2:
        raise ValueError("Invalid seqkit stats output")

    header = lines[0].split('\t')
    values = lines[1].split('\t')

    stats = dict(zip(header, values))

    return {
        'file': stats.get('file'),
        'format': stats.get('format'),
        'type': stats.get('type'),
        'num_seqs': int(stats.get('num_seqs', 0)),
        'sum_len': int(stats.get('sum_len', 0)),
        'min_len': int(stats.get('min_len', 0)),
        'avg_len': float(stats.get('avg_len', 0.0)),
        'max_len': int(stats.get('max_len', 0))
    }
```

#### 2. Filter by Length

```python
async def seqkit_filter_length(
    input_path: str,
    output_path: str,
    min_length: int = None,
    max_length: int = None
) -> str:
    """Filter sequences by length."""
    command = ['seqkit', 'seq']

    if min_length:
        command.extend(['-m', str(min_length)])  # --min-len
    if max_length:
        command.extend(['-M', str(max_length)])  # --max-len

    command.extend(['-o', output_path, input_path])

    returncode, stdout, stderr = await run_tool_async(command)

    # Count filtered sequences
    stats = await seqkit_stats(output_path)
    return f"Filtered: {stats['num_seqs']} sequences kept"
```

#### 3. Remove Duplicates

```python
async def seqkit_rmdup(
    input_path: str,
    output_path: str,
    by_name: bool = False,
    by_seq: bool = True
) -> str:
    """Remove duplicate sequences."""
    command = ['seqkit', 'rmdup']

    if by_name:
        command.append('-n')  # by ID/name
    if by_seq:
        command.append('-s')  # by sequence

    command.extend(['-o', output_path, input_path])

    returncode, stdout, stderr = await run_tool_async(command)

    # Parse stats from stderr
    # seqkit outputs stats to stderr
    match = re.search(r'(\d+) duplicated records removed', stderr)
    removed = int(match.group(1)) if match else 0

    return f"Removed {removed} duplicate sequences"
```

---

## Tool 2: vsearch Integration

**Purpose**: Clustering, dereplication, chimera detection, masking
**Location**: Processing Server
**Documentation**: https://github.com/torognes/vsearch

### Common vsearch Commands

#### 1. Dereplicate (Exact Duplicates)

```python
async def vsearch_dereplicate(
    input_path: str,
    output_path: str,
    min_unique_size: int = 1
) -> str:
    """
    Dereplicate sequences (exact matches).

    Args:
        input_path: Input FASTA
        output_path: Output FASTA
        min_unique_size: Min abundance to keep (default 1)

    Returns:
        Summary message
    """
    command = [
        'vsearch',
        '--derep_fulllength', input_path,
        '--output', output_path,
        '--minuniquesize', str(min_unique_size),
        '--strand', 'both',  # Check both strands
        '--fasta_width', '0',  # No line wrapping
        '--sizeout'  # Add size annotations
    ]

    returncode, stdout, stderr = await run_tool_async(command, timeout=600)

    # Parse vsearch output (in stderr)
    match = re.search(r'(\d+) unique sequences', stderr)
    unique = int(match.group(1)) if match else 0

    return f"Dereplicated: {unique} unique sequences"
```

#### 2. Clustering

```python
async def vsearch_cluster(
    input_path: str,
    output_centroids: str,
    output_uc: str = None,
    identity: float = 0.97
) -> str:
    """
    Cluster sequences by similarity.

    Args:
        input_path: Input FASTA (sorted by length recommended)
        output_centroids: Output file for cluster centroids
        output_uc: Optional UC file for cluster assignments
        identity: Identity threshold (0.0-1.0, default 0.97)

    Returns:
        Clustering summary
    """
    command = [
        'vsearch',
        '--cluster_fast', input_path,
        '--id', str(identity),
        '--centroids', output_centroids,
        '--strand', 'both',
        '--fasta_width', '0'
    ]

    if output_uc:
        command.extend(['--uc', output_uc])

    returncode, stdout, stderr = await run_tool_async(command, timeout=900)

    # Parse clustering stats
    match = re.search(r'(\d+) clusters', stderr)
    clusters = int(match.group(1)) if match else 0

    return f"Clustered into {clusters} clusters at {identity*100}% identity"
```

#### 3. Chimera Detection (UCHIME)

```python
async def vsearch_uchime(
    input_path: str,
    output_nonchimeras: str,
    output_chimeras: str = None,
    reference_db: str = None
) -> str:
    """
    Detect chimeric sequences using UCHIME algorithm.

    Args:
        input_path: Input FASTA
        output_nonchimeras: Output for non-chimeric sequences
        output_chimeras: Optional output for chimeric sequences
        reference_db: Optional reference database (use denovo if None)

    Returns:
        Detection summary
    """
    if reference_db:
        # Reference-based detection
        command = [
            'vsearch',
            '--uchime_ref', input_path,
            '--db', reference_db,
            '--nonchimeras', output_nonchimeras,
            '--fasta_width', '0'
        ]
    else:
        # De novo detection
        command = [
            'vsearch',
            '--uchime_denovo', input_path,
            '--nonchimeras', output_nonchimeras,
            '--fasta_width', '0'
        ]

    if output_chimeras:
        command.extend(['--chimeras', output_chimeras])

    returncode, stdout, stderr = await run_tool_async(command, timeout=600)

    # Parse chimera stats
    match = re.search(r'(\d+) chimeras', stderr)
    chimeras = int(match.group(1)) if match else 0

    return f"Detected {chimeras} chimeric sequences"
```

#### 4. DUST Masking

```python
async def vsearch_maskfasta(
    input_path: str,
    output_path: str,
    dust_threshold: int = None
) -> str:
    """
    Mask low-complexity regions using DUST algorithm.

    Args:
        input_path: Input FASTA
        output_path: Output FASTA with masked regions
        dust_threshold: DUST threshold (default: vsearch default)

    Returns:
        Masking summary
    """
    command = [
        'vsearch',
        '--maskfasta', input_path,
        '--output', output_path,
        '--fasta_width', '0'
    ]

    if dust_threshold is not None:
        command.extend(['--dust', str(dust_threshold)])

    returncode, stdout, stderr = await run_tool_async(command)

    return f"Masked low-complexity regions → {output_path}"
```

---

## Tool 3: MAFFT Integration

**Purpose**: Fast and accurate multiple sequence alignment
**Location**: Alignment Server
**Documentation**: https://mafft.cbrc.jp/alignment/software/

### MAFFT Strategies

| Strategy | Command | Use Case | Speed | Accuracy |
|----------|---------|----------|-------|----------|
| Auto | `--auto` | General purpose | Fast | Good |
| FFT-NS-2 | `--retree 2` | Many sequences (>10K) | Fastest | Lower |
| L-INS-i | `--localpair --maxiterate 1000` | <200 seqs, conserved | Slow | Highest |
| G-INS-i | `--globalpair --maxiterate 1000` | <200 seqs, global align | Slow | Highest |
| E-INS-i | `--genafpair --maxiterate 1000` | Multiple domains | Slowest | Highest |

### MAFFT Execution Patterns

#### 1. Auto Strategy (Recommended Default)

```python
async def mafft_align_auto(
    input_path: str,
    output_path: str,
    threads: int = 4
) -> str:
    """
    Align sequences using MAFFT auto strategy.

    Auto selects best strategy based on:
    - Number of sequences
    - Sequence length
    - Similarity

    Args:
        input_path: Input FASTA (unaligned)
        output_path: Output FASTA (aligned)
        threads: Number of CPU threads (default 4)

    Returns:
        Alignment summary
    """
    command = [
        'mafft',
        '--auto',
        '--thread', str(threads),
        '--quiet',  # Less verbose output
        input_path
    ]

    returncode, stdout, stderr = await run_tool_async(
        command,
        output_file=output_path,
        timeout=1800  # 30 minutes
    )

    # Count sequences
    seq_count = stdout.count('>')
    return f"Aligned {seq_count} sequences using MAFFT auto"
```

#### 2. High Accuracy (L-INS-i)

```python
async def mafft_align_linsi(
    input_path: str,
    output_path: str,
    max_iterate: int = 1000,
    threads: int = 4
) -> str:
    """
    High-accuracy alignment for <200 sequences.

    Uses L-INS-i strategy: local pairwise alignment.
    Best for conserved regions.
    """
    command = [
        'mafft',
        '--localpair',
        '--maxiterate', str(max_iterate),
        '--thread', str(threads),
        '--quiet',
        input_path
    ]

    returncode, stdout, stderr = await run_tool_async(
        command,
        output_file=output_path,
        timeout=3600  # 1 hour for high accuracy
    )

    seq_count = stdout.count('>')
    return f"High-accuracy alignment: {seq_count} sequences (L-INS-i)"
```

#### 3. Fast for Large Datasets

```python
async def mafft_align_fast(
    input_path: str,
    output_path: str,
    threads: int = 4
) -> str:
    """
    Fast alignment for >1000 sequences.

    Uses FFT-NS-2 strategy (progressive method).
    """
    command = [
        'mafft',
        '--retree', '2',
        '--maxiterate', '0',  # No iterative refinement
        '--thread', str(threads),
        '--quiet',
        input_path
    ]

    returncode, stdout, stderr = await run_tool_async(
        command,
        output_file=output_path,
        timeout=1800
    )

    seq_count = stdout.count('>')
    return f"Fast alignment: {seq_count} sequences (FFT-NS-2)"
```

---

## Tool 4: MUSCLE Integration

**Purpose**: Multiple sequence alignment (v5 with Super5 algorithm)
**Location**: Alignment Server
**Documentation**: https://drive5.com/muscle5/

### MUSCLE v5 Execution

```python
async def muscle_align(
    input_path: str,
    output_path: str,
    strategy: str = 'default',
    threads: int = 4
) -> str:
    """
    Align sequences using MUSCLE v5.

    Args:
        input_path: Input FASTA (unaligned)
        output_path: Output FASTA (aligned)
        strategy: 'default', 'fast', or 'accurate'
        threads: Number of threads

    Returns:
        Alignment summary
    """
    # MUSCLE v5 uses different syntax
    command = ['muscle']

    if strategy == 'fast':
        # Fast alignment (1-2 iterations)
        command.extend([
            '-align', input_path,
            '-output', output_path,
            '-threads', str(threads)
        ])
    elif strategy == 'accurate':
        # More iterations for accuracy
        command.extend([
            '-align', input_path,
            '-output', output_path,
            '-perturb', '0',  # Ensemble alignment
            '-perm', 'abc',  # Permutation strategy
            '-threads', str(threads)
        ])
    else:
        # Default (balanced)
        command.extend([
            '-align', input_path,
            '-output', output_path,
            '-threads', str(threads)
        ])

    returncode, stdout, stderr = await run_tool_async(
        command,
        timeout=1800
    )

    # Count sequences in output
    with open(output_path) as f:
        seq_count = sum(1 for line in f if line.startswith('>'))

    return f"MUSCLE aligned {seq_count} sequences ({strategy} strategy)"
```

---

## Tool 5: Clustal Omega Integration

**Purpose**: General-purpose multiple sequence alignment
**Location**: Alignment Server
**Documentation**: http://www.clustal.org/omega/

### Clustal Omega Execution

```python
async def clustalo_align(
    input_path: str,
    output_path: str,
    iterations: int = 0,
    threads: int = 4,
    output_format: str = 'fasta'
) -> str:
    """
    Align sequences using Clustal Omega.

    Args:
        input_path: Input FASTA (unaligned)
        output_path: Output alignment
        iterations: Number of iterations (0=no iteration, 1-5 recommended)
        threads: Number of threads
        output_format: 'fasta', 'clustal', 'phylip', etc.

    Returns:
        Alignment summary
    """
    command = [
        'clustalo',
        '--infile', input_path,
        '--outfile', output_path,
        '--outfmt', output_format,
        '--threads', str(threads),
        '--force',  # Overwrite output
        '--verbose'
    ]

    if iterations > 0:
        command.extend(['--iter', str(iterations)])

    returncode, stdout, stderr = await run_tool_async(
        command,
        timeout=1800
    )

    # Parse output
    seq_count = 0
    with open(output_path) as f:
        seq_count = sum(1 for line in f if line.startswith('>'))

    return f"Clustal Omega aligned {seq_count} sequences"
```

---

## Error Handling Patterns

### Pattern 1: Tool Not Found

```python
async def check_tool_available(tool_name: str) -> bool:
    """Check if bioinformatics tool is available."""
    try:
        process = await asyncio.create_subprocess_exec(
            'which', tool_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode == 0
    except Exception:
        return False

# Usage
if not await check_tool_available('mafft'):
    raise RuntimeError("MAFFT not found. Install with: conda install -c bioconda mafft")
```

### Pattern 2: Timeout Handling

```python
try:
    result = await asyncio.wait_for(
        run_tool_async(command, input_file),
        timeout=300
    )
except asyncio.TimeoutError:
    logger.error(f"Tool exceeded 300s timeout")
    # Clean up partial output
    if output_file and Path(output_file).exists():
        Path(output_file).unlink()
    raise RuntimeError(
        "Tool execution timed out. "
        "Try: 1) smaller input, 2) faster strategy, 3) increase timeout"
    )
```

### Pattern 3: Parse Tool Errors

```python
def parse_tool_error(stderr: str, tool: str) -> str:
    """Extract meaningful error from tool stderr."""
    common_errors = {
        'out of memory': 'Insufficient memory. Reduce input size or increase RAM.',
        'invalid format': 'Input file format invalid. Check FASTA formatting.',
        'no sequences': 'No valid sequences found in input.',
        'permission denied': 'Permission error. Check file permissions.',
    }

    for pattern, suggestion in common_errors.items():
        if pattern in stderr.lower():
            return f"{tool} error: {suggestion}"

    # Return last non-empty line of stderr
    lines = [l for l in stderr.split('\n') if l.strip()]
    return f"{tool} error: {lines[-1] if lines else 'Unknown error'}"
```

---

## Performance Optimization

### 1. Choose Right Tool for Data Size

```python
def select_alignment_tool(num_sequences: int, avg_length: int) -> dict:
    """Recommend alignment tool based on data size."""
    if num_sequences < 50:
        return {
            'tool': 'mafft',
            'strategy': 'linsi',
            'reason': 'High accuracy for small datasets'
        }
    elif num_sequences < 500:
        return {
            'tool': 'mafft',
            'strategy': 'auto',
            'reason': 'Balanced speed/accuracy'
        }
    elif num_sequences < 10000:
        return {
            'tool': 'muscle',
            'strategy': 'fast',
            'reason': 'Good for medium datasets'
        }
    else:
        return {
            'tool': 'mafft',
            'strategy': 'retree2',
            'reason': 'Fastest for large datasets'
        }
```

### 2. Parallel Processing

```python
async def process_multiple_files(
    input_files: list[str],
    tool_func,
    max_concurrent: int = 4
) -> list[str]:
    """Process multiple files in parallel with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(input_file):
        async with semaphore:
            return await tool_func(input_file)

    tasks = [process_with_semaphore(f) for f in input_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

---

## Testing Patterns

### Unit Test Template

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
@patch('asyncio.create_subprocess_exec')
async def test_mafft_align(mock_subprocess):
    """Test MAFFT alignment with mocked subprocess."""
    # Mock process
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(
        return_value=(b">seq1\nATGC\n>seq2\nGCTA\n", b"MAFFT v7.505")
    )
    mock_subprocess.return_value = mock_process

    # Call function
    result = await mafft_align_auto("input.fasta", "output.fasta")

    # Verify
    assert "Aligned" in result
    assert "2 sequences" in result
    mock_subprocess.assert_called_once()
    args = mock_subprocess.call_args[0]
    assert 'mafft' in args
    assert '--auto' in args
```

---

## Quick Command Reference

```python
# seqkit
await seqkit_stats("sequences.fasta")
await seqkit_filter_length("input.fasta", "output.fasta", min_length=400)
await seqkit_rmdup("input.fasta", "output.fasta", by_seq=True)

# vsearch
await vsearch_dereplicate("input.fasta", "derep.fasta", min_unique_size=2)
await vsearch_cluster("input.fasta", "centroids.fasta", identity=0.97)
await vsearch_uchime("input.fasta", "nonchimeras.fasta")
await vsearch_maskfasta("input.fasta", "masked.fasta")

# MAFFT
await mafft_align_auto("unaligned.fasta", "aligned.fasta", threads=8)
await mafft_align_linsi("seqs.fasta", "aligned.fasta")  # High accuracy
await mafft_align_fast("many_seqs.fasta", "aligned.fasta")  # Fast

# MUSCLE
await muscle_align("input.fasta", "aligned.fasta", strategy="accurate")

# Clustal Omega
await clustalo_align("input.fasta", "aligned.fasta", iterations=2, threads=8)
```

---

## Remember

- **Always use async subprocess** - Don't block the event loop
- **Set appropriate timeouts** - Large datasets take time
- **Check exit codes** - Non-zero = failure
- **Parse stderr** - Most tools output logs to stderr
- **Validate input** - Check files exist before running
- **Clean up on error** - Remove partial output files
- **Choose right tool** - Match tool to data size
- **Test with real data** - Synthetic data may behave differently
- **Document parameters** - Why these settings?

Your CLI tool integration should be **async, robust, and production-ready** for the mdk_mcp bioinformatics pipeline.
