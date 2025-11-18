/**
 * MCP Tools Documentation for Code Execution Sandbox
 * 
 * This module provides comprehensive documentation for all available MCP tools.
 * Use `docs.database`, `docs.processing`, etc. to see available functions and usage.
 */

/**
 * Database Server Documentation
 * 
 * Access biological sequence databases (NCBI, BOLD, Ensembl, SILVA, UNITE)
 */
export const database = {
  name: "Database Server",
  description: "Retrieve sequences and metadata from multiple biological databases",
  
  functions: {
    getSequences: {
      description: "Fetch sequences from multiple databases with advanced filtering",
      usage: `
// IMPORTANT: Choose the right source for your target region!

// BASIC USAGE - For MITOCHONDRIAL genes (COI, 16S mtDNA, etc.):
const coiSeqs = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",                    // COI, 16S, ITS, mitogenome
  source: "ncbi",                   // ← KEY: Use "ncbi" or "bold" for mitochondrial genes
  max_results: 100,
  format: "fasta"                   // or "genbank"
});

// ADVANCED FILTERING - Filter complete mitochondrial genomes:
const completeGenomes = await database.getSequences({
  taxon: "Salmo salar",
  region: "mitogenome",
  source: "ncbi",
  format: "fasta",
  filters: {
    min_length: 15000,              // ← Filter by sequence length (bp)
    max_length: 18000,
    completeness: "complete",       // ← "complete", "partial", or "any"
    quality_filter: "high"          // ← "high", "medium", or "any"
  }
});

// ADVANCED FILTERING - Filter by date and location:
const recentSequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  filters: {
    upload_date_start: "2020-01-01",  // ← Filter by upload date (YYYY-MM-DD)
    upload_date_end: "2024-12-31",
    country: "Norway",                // ← Filter by country
    has_geo_location: true,           // ← Only sequences with GPS coordinates
    exclude_environmental: true       // ← Exclude uncultured/environmental samples
  }
});

// ADVANCED FILTERING - High-quality COI barcodes:
const qualityBarcodes = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "bold",                   // ← BOLD specializes in COI barcodes
  filters: {
    min_length: 600,                // Typical barcode length
    max_length: 700,
    quality_filter: "high",
    exclude_predicted: true,        // ← Exclude computationally predicted sequences
    exclude_environmental: true
  }
});

// For NUCLEAR genes - Use Ensembl (default "gget"):
const nuclearGene = await database.getSequences({
  taxon: "Salmo salar",
  region: "whole",
  source: "gget",                   // ← Ensembl for nuclear genomes
  max_results: 10
});

// For 16S rRNA (bacterial) - Use SILVA:
const rRNA = await database.getSequences({
  taxon: "Escherichia coli",
  region: "16S",
  source: "silva",                  // ← SILVA for 16S rRNA
  max_results: 50
});

// For fungal ITS - Use UNITE:
const its = await database.getSequences({
  taxon: "Saccharomyces cerevisiae",
  region: "ITS",
  source: "unite",                  // ← UNITE for fungal ITS
  max_results: 50
});
`,
      parameters: {
        taxon: "Species name (e.g., 'Salmo salar')",
        region: "Target region: 'COI', '16S', 'ITS', 'mitogenome', 'whole'",
        source: "Database: 'ncbi' (default), 'bold', 'gget' (Ensembl), 'silva', 'unite'",
        max_results: "Number of sequences (default: 100)",
        format: "'fasta' (default) or 'genbank'",
        filters: "Optional: Advanced filtering options (see filterOptions below)"
      },
      filterOptions: {
        min_length: "Minimum sequence length in base pairs (number)",
        max_length: "Maximum sequence length in base pairs (number)",
        completeness: "'complete', 'partial', or 'any' - Sequence completeness level",
        upload_date_start: "Start date for upload/submission (YYYY-MM-DD)",
        upload_date_end: "End date for upload/submission (YYYY-MM-DD)",
        country: "Filter by country/geographic location (string)",
        has_geo_location: "Only include sequences with GPS coordinates (boolean)",
        quality_filter: "'high', 'medium', or 'any' - Sequence quality threshold",
        exclude_predicted: "Exclude predicted/inferred sequences (boolean)",
        exclude_environmental: "Exclude environmental/uncultured samples (boolean)"
      },
      filterSupport: {
        ncbi: "✓ All filters supported (server-side filtering)",
        bold: "⚠ Length, date filters (post-retrieval filtering)",
        gget: "⚠ Limited filter support",
        silva: "⚠ Length filters only (post-retrieval)",
        unite: "⚠ Length filters only (post-retrieval)"
      },
      returns: "FASTA or GenBank format sequences as string",
      sourceGuide: {
        "ncbi": "✓ Mitochondrial genes (COI, 16S mtDNA), all sequences, best filter support",
        "bold": "✓ COI barcoding sequences (specialized), partial filter support",
        "gget": "✓ Nuclear genes, reference genomes (Ensembl)",
        "silva": "✓ 16S/18S rRNA (bacterial/archaeal), basic filters",
        "unite": "✓ ITS (fungal sequences), basic filters"
      },
      examples: {
        completeGenomes: {
          description: "Get only complete mitochondrial genomes",
          code: `await database.getSequences({
  taxon: "Salmo salar",
  region: "mitogenome",
  source: "ncbi",
  filters: { min_length: 15000, completeness: "complete" }
})`
        },
        highQualityCOI: {
          description: "Get high-quality COI barcodes from recent submissions",
          code: `await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "bold",
  filters: {
    min_length: 600,
    max_length: 700,
    quality_filter: "high",
    upload_date_start: "2020-01-01",
    exclude_environmental: true
  }
})`
        },
        geographicFilter: {
          description: "Get sequences from specific country with coordinates",
          code: `await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  filters: {
    country: "Norway",
    has_geo_location: true
  }
})`
        }
      }
    },
    
    ggetSearch: {
      description: "Search Ensembl database for genes",
      usage: `
// Search for genes by keywords
const results = await database.ggetSearch({
  searchwords: ["hemoglobin", "alpha"],
  species: "salmo_salar",          // Use underscores!
  id_type: "gene",                 // or "transcript"
  andor: "and"                     // "and" or "or"
});

// Results are JSON array with ensembl_id, gene_name, description
const ids = results.map(r => r.ensembl_id);
`,
      parameters: {
        searchwords: "Array of search terms",
        species: "Species name with underscores (e.g., 'homo_sapiens')",
        id_type: "'gene' or 'transcript'",
        andor: "'and' or 'or' for combining search terms"
      },
      returns: "JSON array of matching genes with Ensembl IDs"
    },
    
    ggetSeq: {
      description: "Get sequences by Ensembl ID",
      usage: `
// Get sequences for specific Ensembl IDs
const sequences = await database.ggetSeq({
  ens_ids: ["ENSSSAG00000000269", "ENSSSAG00000000905"],
  translate: false,               // true for protein translation
  seqtype: "transcript"           // "genomic", "transcript", or "protein"
});
`,
      parameters: {
        ens_ids: "Array of Ensembl IDs",
        translate: "Boolean: translate to protein (default: false)",
        seqtype: "'genomic', 'transcript', or 'protein'"
      },
      returns: "FASTA format sequences"
    },
    
    getTaxonomy: {
      description: "Get taxonomic information",
      usage: `
const taxonomy = await database.getTaxonomy({
  query: "Salmo salar"
});
// Returns full taxonomic lineage
`,
      parameters: {
        query: "Taxon name or accession"
      },
      returns: "JSON with taxonomic lineage"
    },
    
    extractSequenceColumns: {
      description: "Extract metadata from FASTA/GenBank sequences",
      usage: `
// Get sequences first
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  source: "ncbi",
  format: "genbank",              // GenBank has more metadata!
  max_results: 50
});

// Extract specific columns
const metadata = await database.extractSequenceColumns({
  sequence_data: sequences,
  columns: ["Accession", "Organism", "Length", "Country", "Collection Date"],
  output_format: "json"           // "json", "csv", "tsv", or "table"
});
`,
      parameters: {
        sequence_data: "Raw sequence data (FASTA or GenBank)",
        columns: "Array of columns to extract",
        output_format: "'json', 'csv', 'tsv', or 'table'"
      },
      availableColumns: [
        "Id", "Accession", "Title", "Organism", "Length", "Database", 
        "Marker", "Quality Score", "Country", "Create Date", "Collection Date",
        "Geographic Location", "Isolate", "Sequencing Technology",
        "Taxonomic Classification", "Authors", "Institution", "Gene",
        "Product", "Protein ID", "Taxon ID"
      ]
    }
  }
};

/**
 * Processing Server Documentation
 * 
 * Quality control and processing for sequence data
 */
export const processing = {
  name: "Processing Server",
  description: "Quality control, deduplication, and sequence processing",
  
  functions: {
    fastaQc: {
      description: "Perform quality control on FASTA sequences",
      usage: `
const qcResults = await processing.fastaQc({
  sequences: fastaString,
  min_length: 400,
  max_length: 800,
  check_ambiguous: true
});
`,
      parameters: {
        sequences: "FASTA format sequences",
        min_length: "Minimum sequence length",
        max_length: "Maximum sequence length",
        check_ambiguous: "Check for ambiguous bases"
      }
    },
    
    dereplicateSequences: {
      description: "Remove duplicate or highly similar sequences",
      usage: `
const dereplicated = await processing.dereplicateSequences({
  sequences: fastaString,
  similarity_threshold: 0.99,     // 99% similarity threshold
  method: "vsearch"               // or "cd-hit"
});
`
    }
  }
};

/**
 * Alignment Server Documentation
 */
export const alignment = {
  name: "Alignment Server",
  description: "Multiple sequence alignment and phylogenetic analysis",
  
  functions: {
    alignSequences: {
      description: "Align sequences using MAFFT, MUSCLE, or Clustal Omega",
      usage: `
const aligned = await alignment.alignSequences({
  sequences: fastaString,
  algorithm: "mafft",             // "mafft", "muscle", or "clustalo"
  options: {
    auto: true                    // MAFFT auto-select algorithm
  }
});
`
    },
    
    buildPhylogeny: {
      description: "Build phylogenetic tree from alignment",
      usage: `
const tree = await alignment.buildPhylogeny({
  alignment: alignedFasta,
  method: "fasttree",             // "fasttree", "iqtree", or "raxml"
  model: "GTR+G"                  // Evolutionary model
});
`
    }
  }
};

/**
 * Design Server Documentation
 */
export const design = {
  name: "Design Server",
  description: "Primer and probe design for diagnostics",
  
  functions: {
    designPrimersComplete: {
      description: "Complete primer design pipeline",
      usage: `
const primers = await design.designPrimersComplete({
  target_sequences: targetFasta,
  offtarget_sequences: offtargetFasta,
  primer_parameters: {
    primer_min_size: 18,
    primer_max_size: 25,
    primer_opt_size: 20,
    primer_min_tm: 58,
    primer_max_tm: 62,
    primer_opt_tm: 60
  }
});
`
    }
  }
};

/**
 * Validation Server Documentation
 */
export const validation = {
  name: "Validation Server",
  description: "Validate primers using BLAST and in silico PCR",
  
  functions: {
    ggetBlast: {
      description: "BLAST search using NCBI",
      usage: `
const blastResults = await validation.ggetBlast({
  sequence: "ATCGATCGATCG",
  program: "blastn",              // "blastn", "blastp", "blastx"
  database: "nt",                 // "nt", "nr", etc.
  limit: 50
});
`
    },
    
    inSilicoPcr: {
      description: "Perform in silico PCR",
      usage: `
const pcrResults = await validation.inSilicoPcr({
  forward_primer: "ATCGATCG",
  reverse_primer: "CGATCGAT",
  sequences: testSequences,
  max_amplicon_size: 1000
});
`
    }
  }
};

/**
 * Filesystem Operations Documentation
 */
export const filesystem = {
  name: "Filesystem Operations",
  description: "Copy files between local filesystem and container workspace",
  
  functions: {
    copyToWorkspace: {
      description: "Copy a file from local filesystem into container workspace",
      usage: `
// Copy input data into workspace for processing
await fs.copyFile(
  "/home/user/data/sequences.fasta",
  "/workspace/input/sequences.fasta"
);

// Or use relative path (resolved relative to /workspace)
await fs.copyFile(
  "/home/user/config.json",
  "config/settings.json"  // → /workspace/config/settings.json
);
`,
      useCases: [
        "Import sequence data for analysis",
        "Transfer configuration files",
        "Load reference databases",
        "Copy scripts or code files"
      ]
    },
    
    copyFromWorkspace: {
      description: "Copy a file from container workspace to local filesystem",
      usage: `
// Export results from workspace
await fs.copyFile(
  "/workspace/output/results.txt",
  "/home/user/results/analysis.txt"
);

// Or use relative workspace path
await fs.copyFile(
  "output/aligned.fasta",  // → /workspace/output/aligned.fasta
  "/home/user/data/aligned_output.fasta"
);
`,
      useCases: [
        "Export analysis results",
        "Save processed sequences",
        "Extract generated reports",
        "Backup important data"
      ]
    }
  },
  
  note: `All file operations support both absolute and relative paths.
Relative paths in workspace are resolved relative to /workspace directory.`
};

/**
 * Quick Reference Guide
 */
export const quickStart = `
QUICK START GUIDE - Common Workflows
====================================

1. GET COI SEQUENCES (Mitochondrial Barcoding):
   ────────────────────────────────────────────
   const sequences = await database.getSequences({
     taxon: "Salmo salar",
     region: "COI",
     source: "ncbi",        // ← IMPORTANT: Use NCBI or BOLD for COI!
     max_results: 100
   });

2. ADVANCED FILTERING (NEW!) - Filter at Database Level:
   ─────────────────────────────────────────────────────
   // Get only complete mitochondrial genomes (15-18kb)
   const completeGenomes = await database.getSequences({
     taxon: "Salmo salar",
     region: "mitogenome",
     source: "ncbi",
     filters: {
       min_length: 15000,           // ← Filter by length
       max_length: 18000,
       completeness: "complete",    // ← Complete genomes only
       quality_filter: "high"       // ← High quality only
     }
   });
   
   // Get high-quality COI barcodes from recent years
   const recentBarcodes = await database.getSequences({
     taxon: "Salmo salar",
     region: "COI",
     source: "bold",
     filters: {
       min_length: 600,
       max_length: 700,
       upload_date_start: "2020-01-01",
       quality_filter: "high",
       exclude_environmental: true
     }
   });
   
   // Filter by geographic location
   const norwegianSeqs = await database.getSequences({
     taxon: "Salmo salar",
     region: "COI",
     source: "ncbi",
     filters: {
       country: "Norway",
       has_geo_location: true
     }
   });

3. PROCESS DATA EFFICIENTLY (avoid large context):
   ────────────────────────────────────────────────
   // Use helpers to keep data out of context
   const stats = parseFastaStats(sequences);
   // Returns only statistics, not full sequences
   
   // Or save to file in workspace
   const metadata = await saveToFile(sequences, 'sequences.fasta');
   // Returns only file metadata

4. COPY FILES TO/FROM WORKSPACE:
   ──────────────────────────────
   // Import data from local filesystem
   await fs.copyFile("/home/user/data.fasta", "input/data.fasta");
   
   // Export results to local filesystem
   await fs.copyFile("output/results.txt", "/home/user/results.txt");

5. EXTRACT METADATA:
   ──────────────────
   const metadata = await database.extractSequenceColumns({
     sequence_data: sequences,
     columns: ["Accession", "Organism", "Country"],
     output_format: "json"
   });

6. SEARCH FOR GENES (Nuclear Genomes):
   ───────────────────────────────────
   const genes = await database.ggetSearch({
     searchwords: ["hemoglobin"],
     species: "salmo_salar"    // Use underscores!
   });

DATABASE SOURCE SELECTION:
═════════════════════════
┌─────────────────┬───────────────────────────┬──────────────────────┐
│ For...          │ Use source...             │ Filter Support       │
├─────────────────┼───────────────────────────┼──────────────────────┤
│ COI (mtDNA)     │ "ncbi" or "bold"         │ ✓ All filters (ncbi) │
│ 16S mtDNA       │ "ncbi"                    │ ✓ All filters        │
│ ITS (fungi)     │ "unite"                   │ ⚠ Basic filters      │
│ 16S rRNA (bact) │ "silva"                   │ ⚠ Basic filters      │
│ Nuclear genes   │ "gget" (Ensembl)         │ ⚠ Limited            │
│ Mitogenomes     │ "ncbi"                    │ ✓ All filters        │
└─────────────────┴───────────────────────────┴──────────────────────┘

ADVANCED FILTER OPTIONS:
═══════════════════════
┌───────────────────────┬─────────────────────────────────────────┐
│ Filter                │ Description                             │
├───────────────────────┼─────────────────────────────────────────┤
│ min_length            │ Minimum sequence length (bp)            │
│ max_length            │ Maximum sequence length (bp)            │
│ completeness          │ "complete", "partial", or "any"         │
│ upload_date_start     │ Start date (YYYY-MM-DD)                 │
│ upload_date_end       │ End date (YYYY-MM-DD)                   │
│ country               │ Filter by country name                  │
│ has_geo_location      │ Require GPS coordinates (boolean)       │
│ quality_filter        │ "high", "medium", or "any"              │
│ exclude_predicted     │ Exclude predicted sequences (boolean)   │
│ exclude_environmental │ Exclude environmental samples (boolean) │
└───────────────────────┴─────────────────────────────────────────┘

HELPER FUNCTIONS (for context efficiency):
═════════════════════════════════════════
- parseFastaStats(fasta)         → Get statistics only
- filterAndSave(fasta, fn, path) → Filter & save to file
- saveToFile(data, filename)     → Save & return metadata
- extractFields(fasta, fields)   → Extract specific fields
`;

/**
 * Helper: Display available documentation
 */
export function help(topic?: string): string {
  if (!topic) {
    return `
Available documentation topics:
  - docs.database       : Database access (NCBI, BOLD, Ensembl, etc.)
  - docs.processing     : Sequence processing and QC
  - docs.alignment      : Multiple sequence alignment
  - docs.design         : Primer design
  - docs.validation     : Primer validation
  - docs.filesystem     : Copy files to/from workspace
  - docs.quickStart     : Quick start guide and common workflows

Usage: docs.database, docs.filesystem, docs.quickStart, etc.
`;
  }
  
  return "Documentation not found. Try: docs.database, docs.processing, docs.filesystem, etc.";
}

// Export default with all documentation
export default {
  database,
  processing,
  alignment,
  design,
  validation,
  filesystem,
  quickStart,
  help
};

