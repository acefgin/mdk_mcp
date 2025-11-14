# MCP Tools Usage Skill

## Overview

This skill documents how to properly use the MCP (Model Context Protocol) bioinformatics tools through both direct TypeScript/JavaScript wrappers and the code-execution sandbox.

## Architecture Context

Reference: `docs/architecture/INTERFACE_ARCHITECTURE_SUMMARY.md`

The system has 5 layers:
1. **Client Layer** - Claude Desktop, API clients
2. **Execution Sandbox** - Node.js VM for code execution
3. **Tool Wrappers** - TypeScript interfaces to MCP servers
4. **MCP Server Containers** - Python servers in Docker
5. **Tool Implementations** - Python bioinformatics logic

## Two Methods of Tool Access

### Method 1: Direct TypeScript Wrappers (`workspace/servers/`)

```typescript
// Import from generated wrappers
import { getSequences } from './workspace/servers/database/index.js';

const sequences = await getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  max_results: 100
});
```

**When to use:**
- Building applications
- Direct integration with TypeScript/Node.js code
- Need type safety

### Method 2: Code Execution Sandbox (`code-execution`)

```typescript
// Via execute_code tool
const result = await executeCode(`
  const sequences = await database.getSequences({
    taxon: "Salmo salar",
    region: "COI",
    source: "ncbi",
    max_results: 100
  });
  
  // Process and return summary (not raw data!)
  return parseFastaStats(sequences);
`);
```

**When to use:**
- Interactive exploration with Claude
- Context-efficient data processing
- Need helper functions (parseFastaStats, saveToFile, etc.)

## Critical: Database Source Selection

### ⚠️ Most Important Rule

**For MITOCHONDRIAL genes (COI, 16S mtDNA, mitogenomes), NEVER use `source: "gget"` (Ensembl)!**

### Source Selection Guide

```typescript
// ✅ CORRECT: COI (mitochondrial) from NCBI
const coi = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",        // ← NCBI for mitochondrial
  max_results: 100
});

// ✅ CORRECT: COI barcoding from BOLD
const barcode = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "bold",        // ← BOLD specializes in COI
  max_results: 100
});

// ✅ CORRECT: Nuclear genes from Ensembl
const nuclear = await database.getSequences({
  taxon: "homo_sapiens",
  region: "whole",
  source: "gget",        // ← Ensembl for nuclear genomes
  max_results: 10
});

// ❌ WRONG: COI from Ensembl (will return unrelated results!)
const wrong = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "gget",        // ← WRONG! Ensembl doesn't have COI
  max_results: 100
});
```

### Database Source Table

| Target Gene/Region | Correct Source | Why |
|-------------------|----------------|-----|
| COI (cytochrome oxidase I) | `"ncbi"` or `"bold"` | Mitochondrial gene |
| 16S mtDNA | `"ncbi"` | Mitochondrial rRNA |
| Mitogenomes | `"ncbi"` | Complete mitochondrial genomes |
| 16S/18S rRNA (bacterial) | `"silva"` | Specialized bacterial database |
| ITS (fungal) | `"unite"` | Specialized fungal database |
| Nuclear genes | `"gget"` (Ensembl) | Reference genomes |
| General sequences | `"ncbi"` | Most comprehensive |

## Available Tools by Server

### Database Server (11 tools)

```typescript
// 1. Get sequences - PRIMARY TOOL
const sequences = await database.getSequences({
  taxon: string,           // "Salmo salar"
  region?: string,         // "COI", "16S", "ITS", "mitogenome", "whole"
  source?: string,         // "ncbi", "bold", "gget", "silva", "unite"
  max_results?: number,    // default: 100
  format?: string          // "fasta" or "genbank"
});

// 2. Search Ensembl for genes
const genes = await database.ggetSearch({
  searchwords: string[],   // ["hemoglobin", "alpha"]
  species: string,         // "salmo_salar" (use underscores!)
  id_type?: string,        // "gene" or "transcript"
  andor?: string          // "and" or "or"
});

// 3. Get sequences by Ensembl ID
const seqs = await database.ggetSeq({
  ens_ids: string[],       // ["ENSSSAG00000000269"]
  translate?: boolean,     // false
  seqtype?: string        // "genomic", "transcript", "protein"
});

// 4. Get reference genome info
const ref = await database.ggetRef({
  species: string,         // "homo_sapiens"
  which?: string,         // "all", "gtf", "fasta"
  release?: number        // Ensembl release
});

// 5. Get gene info
const info = await database.ggetInfo({
  ens_ids: string[],      // Ensembl IDs
  expand?: boolean        // Include transcripts
});

// 6. Get taxonomy
const taxonomy = await database.getTaxonomy({
  query: string           // "Salmo salar" or accession
});

// 7. Find taxonomic neighbors
const neighbors = await database.getNeighbors({
  taxon: string,
  rank: string,           // "species", "genus", "family"
  distance?: number,
  common_misIDs?: boolean
});

// 8. Search SRA studies
const sra = await database.searchSraStudies({
  query: string,
  filters?: object,
  search_method?: string
});

// 9. Get SRA run info
const runinfo = await database.getSraRuninfo({
  study_accession: string,
  include_sample_metadata?: boolean,
  format?: string
});

// 10. Search SRA cloud
const cloud = await database.searchSraCloud({
  query_sql: string,
  platform?: string,
  max_rows?: number
});

// 11. Extract metadata from sequences
const metadata = await database.extractSequenceColumns({
  sequence_data: string,    // FASTA or GenBank
  columns?: string[],       // ["Accession", "Organism", "Country"]
  output_format?: string   // "json", "csv", "tsv", "table"
});
```

### Processing Server (5 tools)

```typescript
// 1. Quality control
const qc = await processing.fastaQc({
  sequences: string,        // FASTA format
  min_length?: number,
  max_length?: number,
  check_ambiguous?: boolean
});

// 2. Dereplicate sequences
const dedup = await processing.dereplicateSequences({
  sequences: string,
  similarity_threshold?: number,  // 0.99
  method?: string                // "vsearch" or "cd-hit"
});

// 3. Mask low complexity
const masked = await processing.maskLowComplexity({
  sequences: string,
  method?: string
});

// 4. Detect chimeras
const chimeras = await processing.detectChimeras({
  sequences: string,
  method?: string
});

// 5. Complete processing pipeline
const processed = await processing.processSequences({
  sequences: string,
  qc_params?: object,
  dereplicate?: boolean,
  mask?: boolean,
  chimera_check?: boolean
});
```

### Alignment Server (5 tools)

```typescript
// 1. Align sequences
const aligned = await alignment.alignSequences({
  sequences: string,
  algorithm?: string,     // "mafft", "muscle", "clustalo"
  options?: object
});

// 2. Process alignment
const cleaned = await alignment.processAlignment({
  alignment: string,
  trim?: boolean,
  threshold?: number
});

// 3. Build phylogenetic tree
const tree = await alignment.buildPhylogeny({
  alignment: string,
  method?: string,       // "fasttree", "iqtree", "raxml"
  model?: string
});

// 4. Calculate distances
const distances = await alignment.calculateDistances({
  alignment: string,
  model?: string
});

// 5. Complete alignment pipeline
const result = await alignment.alignAndAnalyze({
  sequences: string,
  algorithm?: string,
  build_tree?: boolean,
  calculate_distances?: boolean
});
```

### Design Server (6 tools)

```typescript
// 1. Find signature regions
const regions = await design.findSignatureRegions({
  target_sequences: string,
  offtarget_sequences: string,
  min_length?: number,
  max_length?: number
});

// 2. Design primers with Primer3
const primers = await design.primer3Design({
  sequence: string,
  parameters?: object
});

// 3. Analyze specificity
const specificity = await design.analyzeSpecificity({
  primers: object,
  target_sequences: string,
  offtarget_sequences: string
});

// 4. Rank candidate regions
const ranked = await design.rankRegions({
  regions: array,
  criteria?: object
});

// 5. Oligonucleotide QC
const qc = await design.oligoQc({
  oligos: array,
  check_tm?: boolean,
  check_secondary?: boolean,
  check_dimers?: boolean
});

// 6. Complete primer design pipeline
const complete = await design.designPrimersComplete({
  target_sequences: string,
  offtarget_sequences: string,
  primer_parameters?: object
});
```

### Validation Server (7 tools)

```typescript
// 1. BLAST search
const blast = await validation.ggetBlast({
  sequence: string,
  program?: string,      // "blastn", "blastp", "blastx"
  database?: string,     // "nt", "nr"
  limit?: number
});

// 2. In silico PCR
const pcr = await validation.inSilicoPcr({
  forward_primer: string,
  reverse_primer: string,
  sequences: string,
  max_amplicon_size?: number
});

// 3. BLAT search
const blat = await validation.ggetBlat({
  sequence: string,
  assembly?: string
});

// 4. BLAST against nucleotide database
const blastn = await validation.blastNt({
  sequence: string,
  filters?: object
});

// 5. Assess coverage
const coverage = await validation.assessCoverage({
  primers: object,
  sequences: string,
  threshold?: number
});

// 6. Search PubMed
const papers = await validation.searchPubmed({
  query: string,
  max_results?: number
});

// 7. Complete validation pipeline
const validated = await validation.validatePrimersComplete({
  primers: object,
  target_sequences: string,
  offtarget_sequences: string
});
```

## Context-Efficient Patterns

### Pattern 1: Use Helper Functions

```typescript
// ❌ BAD: Returns full sequences to context (50,000+ tokens)
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  max_results: 100
});
return sequences;  // DON'T DO THIS!

// ✅ GOOD: Process and return statistics only (200 tokens)
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  max_results: 100
});
const stats = parseFastaStats(sequences);
return stats;  // Returns: { count: 100, averageLength: 658, ... }
```

### Pattern 2: Save to File

```typescript
// ✅ GOOD: Save data to file, return metadata only
const sequences = await database.getSequences({...});
const metadata = await saveToFile(sequences, 'coi_sequences.fasta');
return metadata;  // { path: '...', size: 65432, lines: 200, ... }
```

### Pattern 3: Extract Specific Fields

```typescript
// ✅ GOOD: Extract only needed information
const sequences = await database.getSequences({...});
const accessions = extractFields(sequences, ['accession', 'organism']);
return accessions;  // [{ accession: 'MT123', organism: 'Salmo salar' }, ...]
```

### Pattern 4: Use extractSequenceColumns

```typescript
// ✅ GOOD: Get structured metadata
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  format: "genbank",  // GenBank has more metadata!
  max_results: 50
});

const metadata = await database.extractSequenceColumns({
  sequence_data: sequences,
  columns: ["Accession", "Organism", "Country", "Collection Date"],
  output_format: "json"
});

return metadata;  // Structured metadata only
```

## Common Workflows

### Workflow 1: Retrieve and Analyze COI Barcodes

```typescript
// Step 1: Get COI sequences from BOLD
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "bold",  // ← Specialized for COI barcoding
  max_results: 100
});

// Step 2: Quality control
const qc = await processing.fastaQc({
  sequences: sequences,
  min_length: 400,
  max_length: 800
});

// Step 3: Extract statistics (context-efficient)
const stats = parseFastaStats(sequences);

return { stats, qc };
```

### Workflow 2: Design Species-Specific Primers

```typescript
// Step 1: Get target species sequences
const target = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  max_results: 50
});

// Step 2: Get related species (off-targets)
const neighbors = await database.getNeighbors({
  taxon: "Salmo salar",
  rank: "genus",
  distance: 1
});

// Step 3: Get off-target sequences
const offtarget = await database.getSequences({
  taxon: "Salmo trutta",  // Close relative
  region: "COI",
  source: "ncbi",
  max_results: 50
});

// Step 4: Design primers
const primers = await design.designPrimersComplete({
  target_sequences: target,
  offtarget_sequences: offtarget,
  primer_parameters: {
    primer_opt_size: 20,
    primer_opt_tm: 60
  }
});

// Step 5: Validate
const validation = await validation.validatePrimersComplete({
  primers: primers,
  target_sequences: target,
  offtarget_sequences: offtarget
});

return { primers, validation };
```

### Workflow 3: Phylogenetic Analysis

```typescript
// Step 1: Get sequences
const sequences = await database.getSequences({
  taxon: "Salmonidae",  // Family
  region: "COI",
  source: "ncbi",
  max_results: 50
});

// Step 2: Complete alignment and phylogeny
const result = await alignment.alignAndAnalyze({
  sequences: sequences,
  algorithm: "mafft",
  build_tree: true,
  calculate_distances: true
});

// Step 3: Save tree to file, return metadata
const treeFile = await saveToFile(result.tree, 'phylogeny.newick');
const distFile = await saveToFile(JSON.stringify(result.distances), 'distances.json');

return {
  sequenceCount: result.sequence_count,
  alignmentLength: result.alignment_length,
  treeFile: treeFile,
  distancesFile: distFile
};
```

## Error Handling Patterns

```typescript
try {
  const sequences = await database.getSequences({
    taxon: "Salmo salar",
    region: "COI",
    source: "ncbi"
  });
  
  return parseFastaStats(sequences);
  
} catch (error) {
  // Check for specific error types
  if (error.message.includes("No sequences found")) {
    return {
      success: false,
      error: "No sequences available for this species",
      suggestion: "Try a different taxon or database source"
    };
  }
  
  if (error.message.includes("timeout")) {
    return {
      success: false,
      error: "Database query timed out",
      suggestion: "Reduce max_results or try again later"
    };
  }
  
  // Generic error
  return {
    success: false,
    error: error.message,
    suggestion: "Check input parameters and try again"
  };
}
```

## Documentation Access in Code

```typescript
// In code-execution sandbox, use docs object:

// Show quick start guide
console.log(docs.quickStart);

// Show database function usage
console.log(docs.database.functions.getSequences.usage);

// Show all database functions
console.log(Object.keys(docs.database.functions));

// Show source selection guide
console.log(docs.database.functions.getSequences.sourceGuide);
```

## Best Practices

### ✅ DO

1. **Always specify `source`** for `getSequences()` - don't rely on defaults
2. **Use NCBI or BOLD for mitochondrial genes** (COI, 16S mtDNA, etc.)
3. **Use helper functions** to keep data out of context
4. **Extract metadata** instead of returning full sequences
5. **Save large data to files** and return metadata only
6. **Use GenBank format** when you need comprehensive metadata
7. **Check documentation** via `docs` object in code-execution sandbox
8. **Handle errors gracefully** with informative messages

### ❌ DON'T

1. **Don't use Ensembl (gget) for mitochondrial genes**
2. **Don't return full sequences** to context (use stats/metadata instead)
3. **Don't forget to specify species format** ("salmo_salar" for Ensembl)
4. **Don't ignore error messages** - they often indicate wrong parameters
5. **Don't fetch more data than needed** - use max_results appropriately
6. **Don't skip validation** - use QC tools before analysis

## Troubleshooting

### Problem: No sequences returned from getSequences

**Possible causes:**
1. Wrong `source` - using Ensembl for mitochondrial genes
2. Typo in taxon name
3. Region not available in that database

**Solution:**
```typescript
// Try different sources
const sources = ["ncbi", "bold", "gget"];
for (const source of sources) {
  const seqs = await database.getSequences({
    taxon: "Salmo salar",
    region: "COI",
    source: source,
    max_results: 10
  });
  console.log(`${source}: ${parseFastaStats(seqs).count} sequences`);
}
```

### Problem: Context window filling up

**Solution:** Use helper functions and file operations

```typescript
// Instead of returning sequences:
const metadata = await saveToFile(sequences, 'temp.fasta');
return metadata;  // Only ~100 tokens instead of 50,000+
```

### Problem: Tool execution timeout

**Solution:** Reduce data size or use batching

```typescript
// Split into smaller batches
const batch1 = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  max_results: 50  // Smaller batches
});
```

## Related Documentation

- Interface Architecture: `docs/architecture/INTERFACE_ARCHITECTURE_SUMMARY.md`
- Workspace README: `workspace/README.md`
- Code Execution Sandbox: `code-execution/README.md`
- Database Server: `mcp_servers/database_server/README.md`

## Version

**Version:** 1.0.0  
**Last Updated:** 2025-11-14  
**Status:** ✅ Active

