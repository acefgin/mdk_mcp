---
name: biopython-dev
description: BioPython best practices for sequence parsing, database access, phylogenetics, and file I/O. Use when working with SeqIO, Entrez, Phylo, AlignIO, or any BioPython modules for bioinformatics data processing.
---

# BioPython Development Guidelines for mdk_mcp

## Purpose

Establish consistent BioPython usage patterns across all mdk_mcp MCP servers. BioPython is used extensively for sequence parsing (FASTA/GenBank), NCBI Entrez queries, phylogenetic analysis, and alignment I/O.

## When to Use This Skill

Automatically activates when:
- Parsing FASTA or GenBank files with SeqIO
- Querying NCBI databases with Entrez
- Building or manipulating phylogenetic trees with Phylo
- Reading/writing alignments with AlignIO
- Creating or manipulating Seq/SeqRecord objects
- Working with sequence metadata extraction
- Implementing any bioinformatics file I/O

---

## Quick Reference

### Common BioPython Imports

```python
# Sequence I/O
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

# NCBI Database Access
from Bio import Entrez

# Phylogenetics
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor

# Alignment I/O
from Bio import AlignIO
from Bio.Align import MultipleSeqAlignment

# Alphabet (deprecated in BioPython 1.78+, avoid using)
# from Bio.Alphabet import IUPAC  # ❌ Don't use!
```

---

## Core Patterns

### 1. SeqIO: Safe Sequence Parsing

#### ✅ GOOD: Proper error handling with file validation

```python
from Bio import SeqIO
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

async def parse_fasta_safe(fasta_path: str) -> list[SeqRecord]:
    """
    Safely parse FASTA file with comprehensive error handling.

    Args:
        fasta_path: Path to FASTA file

    Returns:
        List of SeqRecord objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid format
    """
    # Validate file exists
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    if path.stat().st_size == 0:
        raise ValueError(f"FASTA file is empty: {fasta_path}")

    try:
        # Parse sequences
        sequences = list(SeqIO.parse(fasta_path, "fasta"))

        if not sequences:
            raise ValueError(f"No valid sequences found in {fasta_path}")

        logger.info(f"Parsed {len(sequences)} sequences from {fasta_path}")
        return sequences

    except Exception as e:
        logger.error(f"Error parsing FASTA: {e}")
        raise ValueError(f"Invalid FASTA format in {fasta_path}: {e}")
```

#### ❌ BAD: No error handling

```python
# ❌ Don't do this!
def parse_fasta_bad(fasta_path: str):
    sequences = list(SeqIO.parse(fasta_path, "fasta"))  # Can crash!
    return sequences  # Might be empty!
```

### 2. SeqIO: Writing Sequences

#### ✅ GOOD: Async file writing with proper formatting

```python
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
import aiofiles
from pathlib import Path

async def write_fasta_async(
    sequences: list[SeqRecord],
    output_path: str,
    wrap_width: int = 80
) -> str:
    """
    Write sequences to FASTA file asynchronously.

    Args:
        sequences: List of SeqRecord objects
        output_path: Output file path
        wrap_width: Line width for sequence wrapping (default 80)

    Returns:
        Success message with file path and count
    """
    if not sequences:
        raise ValueError("Cannot write empty sequence list")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # SeqIO.write is synchronous, so we write to temp string first
    from io import StringIO
    buffer = StringIO()
    SeqIO.write(sequences, buffer, "fasta")
    fasta_content = buffer.getvalue()

    # Then write async
    async with aiofiles.open(output_path, 'w') as f:
        await f.write(fasta_content)

    logger.info(f"Wrote {len(sequences)} sequences to {output_path}")
    return f"✓ Saved {len(sequences)} sequences → {output_path}"
```

### 3. Entrez: NCBI Database Queries

#### ✅ GOOD: Rate-limited queries with proper error handling

```python
from Bio import Entrez
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ALWAYS set your email (required by NCBI)
Entrez.email = "your_email@example.com"  # ← CRITICAL!
Entrez.api_key = None  # Set from environment if available

# Rate limiting: 3 requests/second without API key, 10/sec with key
RATE_LIMIT_DELAY = 0.34 if not Entrez.api_key else 0.11

async def entrez_search_async(
    database: str,
    term: str,
    max_results: int = 100,
    retries: int = 3
) -> list[str]:
    """
    Search NCBI database with rate limiting and retries.

    Args:
        database: NCBI database (nuccore, protein, taxonomy, etc.)
        term: Search query
        max_results: Maximum results to return
        retries: Number of retry attempts on failure

    Returns:
        List of NCBI IDs

    Raises:
        RuntimeError: If all retries fail
    """
    for attempt in range(retries):
        try:
            # Rate limit
            await asyncio.sleep(RATE_LIMIT_DELAY)

            # Execute search (blocking call, use run_in_executor for true async)
            handle = Entrez.esearch(
                db=database,
                term=term,
                retmax=max_results,
                usehistory="y"
            )
            record = Entrez.read(handle)
            handle.close()

            id_list = record.get("IdList", [])
            logger.info(f"Found {len(id_list)} results for query: {term}")
            return id_list

        except Exception as e:
            logger.warning(f"Entrez search attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise RuntimeError(f"Entrez search failed after {retries} attempts: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    return []

async def entrez_fetch_async(
    database: str,
    id_list: list[str],
    rettype: str = "fasta",
    retmode: str = "text"
) -> str:
    """
    Fetch records from NCBI with rate limiting.

    Args:
        database: NCBI database name
        id_list: List of IDs to fetch
        rettype: Return type (fasta, gb, xml, etc.)
        retmode: Return mode (text, xml, etc.)

    Returns:
        Raw response data as string
    """
    if not id_list:
        return ""

    # Rate limit
    await asyncio.sleep(RATE_LIMIT_DELAY)

    try:
        handle = Entrez.efetch(
            db=database,
            id=",".join(id_list),
            rettype=rettype,
            retmode=retmode
        )
        data = handle.read()
        handle.close()

        logger.info(f"Fetched {len(id_list)} records from {database}")
        return data

    except Exception as e:
        logger.error(f"Entrez fetch failed: {e}")
        raise RuntimeError(f"Failed to fetch records: {e}")
```

#### ❌ BAD: No rate limiting, no error handling

```python
# ❌ Don't do this!
def search_ncbi_bad(query: str):
    # No email set - NCBI will reject!
    # No rate limiting - will get IP banned!
    # No error handling - will crash!
    handle = Entrez.esearch(db="nuccore", term=query)
    return Entrez.read(handle)
```

### 4. GenBank Format Parsing

#### ✅ GOOD: Safe GenBank parsing with metadata extraction

```python
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

def extract_genbank_metadata(record: SeqRecord) -> dict:
    """
    Extract comprehensive metadata from GenBank record.

    Args:
        record: BioPython SeqRecord from GenBank file

    Returns:
        Dictionary of metadata fields
    """
    metadata = {
        "accession": record.id,
        "description": record.description,
        "sequence_length": len(record.seq),
        "topology": record.annotations.get("topology", "linear"),
        "molecule_type": record.annotations.get("molecule_type", "DNA"),
        "organism": record.annotations.get("organism", "Unknown"),
        "taxonomy": record.annotations.get("taxonomy", []),
        "keywords": record.annotations.get("keywords", []),
        "references": []
    }

    # Extract features
    for feature in record.features:
        if feature.type == "source":
            qualifiers = feature.qualifiers
            metadata["country"] = qualifiers.get("country", [""])[0]
            metadata["collection_date"] = qualifiers.get("collection_date", [""])[0]
            metadata["isolate"] = qualifiers.get("isolate", [""])[0]
            metadata["strain"] = qualifiers.get("strain", [""])[0]

    # Extract references
    for ref in record.annotations.get("references", []):
        metadata["references"].append({
            "title": ref.title,
            "authors": ref.authors,
            "journal": ref.journal
        })

    return metadata

async def parse_genbank_safe(genbank_path: str) -> list[SeqRecord]:
    """Parse GenBank file with error handling."""
    try:
        records = list(SeqIO.parse(genbank_path, "genbank"))
        if not records:
            raise ValueError(f"No records in GenBank file: {genbank_path}")
        return records
    except Exception as e:
        logger.error(f"GenBank parsing failed: {e}")
        raise ValueError(f"Invalid GenBank format: {e}")
```

### 5. Phylo: Phylogenetic Trees

#### ✅ GOOD: Safe tree construction and manipulation

```python
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio import AlignIO
from io import StringIO
import logging

logger = logging.getLogger(__name__)

async def build_nj_tree(
    alignment_path: str,
    distance_model: str = "identity"
) -> str:
    """
    Build Neighbor-Joining phylogenetic tree from alignment.

    Args:
        alignment_path: Path to alignment file (FASTA format)
        distance_model: Distance calculation model (identity, blastn, trans)

    Returns:
        Newick format tree string
    """
    try:
        # Load alignment
        alignment = AlignIO.read(alignment_path, "fasta")

        if len(alignment) < 3:
            raise ValueError("Need at least 3 sequences for tree building")

        # Calculate distance matrix
        calculator = DistanceCalculator(distance_model)
        distance_matrix = calculator.get_distance(alignment)

        # Build tree
        constructor = DistanceTreeConstructor(calculator, 'nj')
        tree = constructor.build_tree(alignment)

        # Convert to Newick string
        tree_io = StringIO()
        Phylo.write(tree, tree_io, "newick")
        newick_tree = tree_io.getvalue()

        logger.info(f"Built NJ tree with {len(alignment)} taxa")
        return newick_tree

    except Exception as e:
        logger.error(f"Tree building failed: {e}")
        raise RuntimeError(f"Failed to build phylogenetic tree: {e}")

def parse_newick_tree(newick_string: str):
    """Parse Newick format tree string."""
    try:
        tree_io = StringIO(newick_string)
        tree = Phylo.read(tree_io, "newick")
        return tree
    except Exception as e:
        raise ValueError(f"Invalid Newick format: {e}")

def get_tree_info(tree) -> dict:
    """Extract tree information."""
    return {
        "total_terminals": tree.count_terminals(),
        "depth": tree.depth(),
        "is_bifurcating": tree.is_bifurcating(),
        "total_branch_length": tree.total_branch_length()
    }
```

### 6. AlignIO: Alignment I/O

#### ✅ GOOD: Safe alignment reading and format conversion

```python
from Bio import AlignIO
from Bio.Align import MultipleSeqAlignment
from pathlib import Path

async def read_alignment_safe(
    alignment_path: str,
    format: str = "fasta"
) -> MultipleSeqAlignment:
    """
    Safely read alignment file.

    Args:
        alignment_path: Path to alignment file
        format: Alignment format (fasta, clustal, phylip, nexus, stockholm)

    Returns:
        MultipleSeqAlignment object
    """
    path = Path(alignment_path)
    if not path.exists():
        raise FileNotFoundError(f"Alignment file not found: {alignment_path}")

    try:
        alignment = AlignIO.read(alignment_path, format)

        if len(alignment) == 0:
            raise ValueError("Alignment is empty")

        logger.info(f"Read alignment: {len(alignment)} sequences, {alignment.get_alignment_length()} columns")
        return alignment

    except Exception as e:
        logger.error(f"Alignment reading failed: {e}")
        raise ValueError(f"Invalid alignment format ({format}): {e}")

async def convert_alignment_format(
    input_path: str,
    output_path: str,
    input_format: str = "fasta",
    output_format: str = "clustal"
) -> str:
    """
    Convert alignment between formats.

    Supported formats: fasta, clustal, phylip, nexus, stockholm, maf
    """
    try:
        alignment = await read_alignment_safe(input_path, input_format)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write in new format
        AlignIO.write(alignment, output_path, output_format)

        logger.info(f"Converted {input_format} → {output_format}: {output_path}")
        return f"✓ Converted alignment → {output_path}"

    except Exception as e:
        logger.error(f"Alignment conversion failed: {e}")
        raise RuntimeError(f"Failed to convert alignment: {e}")
```

---

## Common Patterns for mdk_mcp

### Pattern 1: Sequence Retrieval + Parsing Pipeline

```python
async def retrieve_and_parse_sequences(
    taxon: str,
    gene: str,
    max_results: int = 100
) -> tuple[list[SeqRecord], str]:
    """
    Complete pipeline: search NCBI → fetch → parse → save.

    Returns:
        Tuple of (sequence list, output file path)
    """
    # 1. Search NCBI
    query = f"{taxon}[Organism] AND {gene}[Gene]"
    id_list = await entrez_search_async("nuccore", query, max_results)

    if not id_list:
        raise ValueError(f"No sequences found for {taxon} {gene}")

    # 2. Fetch sequences
    fasta_data = await entrez_fetch_async("nuccore", id_list, "fasta", "text")

    # 3. Parse sequences
    from io import StringIO
    sequences = list(SeqIO.parse(StringIO(fasta_data), "fasta"))

    # 4. Save to file
    timestamp = datetime.now().strftime("%Y%m%d")
    taxon_clean = taxon.replace(" ", "_")
    output_path = f"/results/sequences/{taxon_clean}_{gene}_{timestamp}.fasta"

    await write_fasta_async(sequences, output_path)

    return sequences, output_path
```

### Pattern 2: Quality Filtering Sequences

```python
def filter_sequences_by_quality(
    sequences: list[SeqRecord],
    min_length: int = 400,
    max_n_percent: float = 5.0
) -> list[SeqRecord]:
    """
    Filter sequences by length and N-content.

    Args:
        sequences: Input sequences
        min_length: Minimum sequence length
        max_n_percent: Maximum percentage of N bases

    Returns:
        Filtered sequence list
    """
    filtered = []

    for record in sequences:
        seq_str = str(record.seq).upper()
        seq_len = len(seq_str)

        # Length filter
        if seq_len < min_length:
            logger.debug(f"Filtered {record.id}: too short ({seq_len} bp)")
            continue

        # N-content filter
        n_count = seq_str.count('N')
        n_percent = (n_count / seq_len) * 100

        if n_percent > max_n_percent:
            logger.debug(f"Filtered {record.id}: high N-content ({n_percent:.1f}%)")
            continue

        filtered.append(record)

    logger.info(f"Quality filtering: {len(sequences)} → {len(filtered)} sequences")
    return filtered
```

### Pattern 3: Extract Metadata to CSV

```python
import csv
from Bio.SeqRecord import SeqRecord

async def export_metadata_to_csv(
    sequences: list[SeqRecord],
    output_path: str
) -> str:
    """
    Export sequence metadata to CSV.

    Extracts: ID, description, length, organism, country, date
    """
    import aiofiles
    from io import StringIO

    # Prepare rows
    rows = []
    for record in sequences:
        # Parse description
        parts = record.description.split("|")
        organism = "Unknown"

        if len(parts) > 1:
            # Try to extract organism from description
            for part in parts:
                if "[" in part and "]" in part:
                    organism = part[part.find("[")+1:part.find("]")]
                    break

        row = {
            "Accession": record.id,
            "Description": record.description[:100],  # Truncate
            "Length": len(record.seq),
            "Organism": organism,
            "GC_Content": round(GC(record.seq), 2) if len(record.seq) > 0 else 0
        }
        rows.append(row)

    # Write CSV
    csv_buffer = StringIO()
    fieldnames = ["Accession", "Description", "Length", "Organism", "GC_Content"]
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    async with aiofiles.open(output_path, 'w') as f:
        await f.write(csv_buffer.getvalue())

    logger.info(f"Exported metadata for {len(sequences)} sequences → {output_path}")
    return output_path
```

---

## Error Handling Best Practices

### 1. Always Validate Input Files

```python
from pathlib import Path

def validate_sequence_file(file_path: str, format: str = "fasta") -> None:
    """Validate sequence file before processing."""
    path = Path(file_path)

    # Check exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check not empty
    if path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")

    # Check extension
    expected_ext = {
        "fasta": [".fasta", ".fa", ".fna"],
        "genbank": [".gb", ".gbk", ".genbank"],
        "clustal": [".aln"],
        "phylip": [".phy"]
    }

    if format in expected_ext:
        if path.suffix.lower() not in expected_ext[format]:
            logger.warning(f"Unexpected extension for {format}: {path.suffix}")
```

### 2. Handle Empty Results Gracefully

```python
async def safe_sequence_operation(sequences: list[SeqRecord]) -> str:
    """Always check for empty results."""
    if not sequences:
        return "⚠️  No sequences to process"

    if len(sequences) < 3:
        return f"⚠️  Only {len(sequences)} sequences found (may be insufficient for analysis)"

    # Proceed with operation
    result = await process_sequences(sequences)
    return f"✓ Processed {len(sequences)} sequences successfully"
```

### 3. Provide Informative Error Messages

```python
def format_bioppython_error(error: Exception, context: str) -> str:
    """Format BioPython errors with context."""
    error_type = type(error).__name__

    return f"""
❌ BioPython Error: {error_type}
Context: {context}
Details: {str(error)}

Possible causes:
- Invalid file format
- Corrupted data
- Missing required fields
- Incompatible BioPython version

Suggestion: Verify file format and content
"""
```

---

## Performance Tips

### 1. Use Generators for Large Files

```python
def parse_large_fasta_generator(fasta_path: str):
    """Memory-efficient parsing for huge FASTA files."""
    for record in SeqIO.parse(fasta_path, "fasta"):
        yield record  # Don't load all into memory

# Usage:
for record in parse_large_fasta_generator("huge_file.fasta"):
    process_record(record)
```

### 2. Batch Entrez Queries

```python
async def fetch_sequences_batched(id_list: list[str], batch_size: int = 100):
    """Fetch in batches to avoid timeout."""
    sequences = []

    for i in range(0, len(id_list), batch_size):
        batch = id_list[i:i+batch_size]
        data = await entrez_fetch_async("nuccore", batch, "fasta")
        batch_seqs = list(SeqIO.parse(StringIO(data), "fasta"))
        sequences.extend(batch_seqs)

        logger.info(f"Fetched batch {i//batch_size + 1}/{(len(id_list) + batch_size - 1)//batch_size}")

    return sequences
```

---

## Testing BioPython Code

### Unit Test Template

```python
import pytest
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

@pytest.fixture
def sample_sequences():
    """Create test sequences."""
    return [
        SeqRecord(Seq("ATGCATGC"), id="seq1", description="Test sequence 1"),
        SeqRecord(Seq("GCTAGCTA"), id="seq2", description="Test sequence 2")
    ]

@pytest.mark.asyncio
async def test_parse_fasta(tmp_path):
    """Test FASTA parsing."""
    # Create temp FASTA file
    fasta_path = tmp_path / "test.fasta"
    with open(fasta_path, 'w') as f:
        f.write(">seq1\nATGC\n>seq2\nGCTA\n")

    # Parse
    sequences = await parse_fasta_safe(str(fasta_path))

    assert len(sequences) == 2
    assert sequences[0].id == "seq1"
    assert str(sequences[0].seq) == "ATGC"

@pytest.mark.asyncio
async def test_parse_empty_fasta(tmp_path):
    """Test error handling for empty FASTA."""
    fasta_path = tmp_path / "empty.fasta"
    fasta_path.touch()  # Create empty file

    with pytest.raises(ValueError, match="empty"):
        await parse_fasta_safe(str(fasta_path))
```

---

## Common Gotchas

### ❌ AVOID: Bio.Alphabet (Deprecated)

```python
# ❌ OLD (deprecated in BioPython 1.78+)
from Bio.Alphabet import IUPAC
seq = Seq("ATGC", IUPAC.unambiguous_dna)

# ✅ NEW (BioPython 1.78+)
from Bio.Seq import Seq
seq = Seq("ATGC")  # No alphabet needed!
```

### ❌ AVOID: Modifying Seq Objects Directly

```python
# ❌ Seq objects are immutable!
seq = Seq("ATGC")
seq[0] = "G"  # TypeError!

# ✅ Create new Seq
seq = Seq("ATGC")
new_seq = Seq("G" + str(seq)[1:])
```

### ❌ AVOID: Forgetting Entrez.email

```python
# ❌ Will get rejected by NCBI!
from Bio import Entrez
handle = Entrez.esearch(db="nuccore", term="human")

# ✅ Always set email first
from Bio import Entrez
Entrez.email = "your_email@example.com"  # REQUIRED!
handle = Entrez.esearch(db="nuccore", term="human")
```

---

## Integration with mdk_mcp MCP Servers

### Database Server (Phase 1)

BioPython used for:
- `get_sequences`: Entrez queries + SeqIO parsing
- `get_neighbors`: Entrez ELink queries
- `extract_sequence_columns`: SeqRecord metadata extraction

### Processing Server (Phase 2)

BioPython used for:
- `fasta_qc`: SeqIO parsing + quality filtering
- Sequence length/N-content validation

### Alignment Server (Phase 3)

BioPython used for:
- `build_phylogeny`: Phylo tree construction
- `calculate_distances`: Distance matrix calculation
- AlignIO for alignment reading/writing

---

## Quick Command Reference

```python
# Parse FASTA
sequences = list(SeqIO.parse("file.fasta", "fasta"))

# Write FASTA
SeqIO.write(sequences, "output.fasta", "fasta")

# Search NCBI
handle = Entrez.esearch(db="nuccore", term="query", retmax=100)
record = Entrez.read(handle)

# Fetch sequences
handle = Entrez.efetch(db="nuccore", id="12345", rettype="fasta")
data = handle.read()

# Parse GenBank
records = list(SeqIO.parse("file.gb", "genbank"))

# Read alignment
alignment = AlignIO.read("alignment.fasta", "fasta")

# Build NJ tree
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
calculator = DistanceCalculator('identity')
constructor = DistanceTreeConstructor(calculator, 'nj')
tree = constructor.build_tree(alignment)
```

---

## Remember

- **Always set `Entrez.email`** before any NCBI queries
- **Use async patterns** for file I/O (aiofiles)
- **Validate input files** before parsing
- **Handle empty results** gracefully
- **Use rate limiting** for Entrez queries (0.34s delay without API key)
- **Log operations** at INFO level for debugging
- **Provide context** in error messages
- **Test with real data** (not just synthetic sequences)
- **Check BioPython version** (1.78+ recommended)

Your BioPython code should be **robust, async-compatible, and production-ready** for the mdk_mcp bioinformatics pipeline.
