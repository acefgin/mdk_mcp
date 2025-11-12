/**
 * Generate TypeScript Tool Files for Remaining Servers
 *
 * This script generates typed tool wrappers for all remaining MCP server tools:
 * - Processing Server (5 tools)
 * - Alignment Server (5 tools)
 * - Design Server (6 tools)
 * - Validation Server (7 tools)
 *
 * Total: 23 tools
 *
 * Usage:
 * ```bash
 * npx tsx examples/generate-all-remaining-tools.ts
 * ```
 */

import { ToolFileGenerator, type ToolDefinition } from '../mcp_servers/shared/tool-generator.js';
import * as path from 'path';

/**
 * Processing Server Tool Definitions (5 tools)
 */
const processingTools: ToolDefinition[] = [
  {
    name: 'fasta_qc',
    description: 'Perform quality control on FASTA sequences: filter by length, N-content, and remove duplicates',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        min_length: {
          type: 'integer',
          default: 100,
          description: 'Minimum sequence length',
        },
        max_n_percent: {
          type: 'number',
          default: 5.0,
          description: 'Maximum percentage of N bases allowed',
        },
        remove_duplicates: {
          type: 'boolean',
          default: true,
          description: 'Remove duplicate sequences',
        },
      },
      required: ['fasta_content'],
    },
  },

  {
    name: 'dereplicate_sequences',
    description: 'Remove duplicate or near-duplicate sequences using clustering',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        identity_threshold: {
          type: 'number',
          default: 0.97,
          description: 'Identity threshold for clustering (0.0-1.0)',
        },
        per_species: {
          type: 'boolean',
          default: true,
          description: 'Group by species before dereplication',
        },
      },
      required: ['fasta_content'],
    },
  },

  {
    name: 'mask_low_complexity',
    description: 'Mask low-complexity regions and repeats using DUST algorithm',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        mask_repeats: {
          type: 'boolean',
          default: true,
          description: 'Mask repetitive regions',
        },
        mask_homopolymers: {
          type: 'boolean',
          default: true,
          description: 'Mask homopolymer runs',
        },
        min_complexity: {
          type: 'number',
          default: 1.5,
          description: 'Minimum complexity score',
        },
      },
      required: ['fasta_content'],
    },
  },

  {
    name: 'detect_chimeras',
    description: 'Detect and remove chimeric sequences using UCHIME algorithm',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        reference_db: {
          type: 'string',
          enum: ['auto', 'silva', 'unite'],
          default: 'auto',
          description: 'Reference database for chimera detection',
        },
        abundance_threshold: {
          type: 'number',
          default: 2.0,
          description: 'Abundance skew threshold',
        },
      },
      required: ['fasta_content'],
    },
  },

  {
    name: 'process_sequences',
    description: 'Process sequences through a unified pipeline combining multiple steps',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        run_id: {
          type: 'string',
          description: 'Run ID for organizing output files (optional)',
        },
        pipeline: {
          type: 'array',
          items: {
            type: 'string',
            enum: ['qc', 'dereplicate', 'mask', 'chimera'],
          },
          default: ['qc', 'dereplicate', 'mask', 'chimera'],
          description: 'List of processing steps to execute in order',
        },
        qc_params: {
          type: 'object',
          description: 'Parameters for QC step',
        },
        derep_params: {
          type: 'object',
          description: 'Parameters for dereplication step',
        },
        mask_params: {
          type: 'object',
          description: 'Parameters for masking step',
        },
        chimera_params: {
          type: 'object',
          description: 'Parameters for chimera detection step',
        },
      },
      required: ['fasta_content'],
    },
  },
];

/**
 * Alignment Server Tool Definitions (5 tools)
 */
const alignmentTools: ToolDefinition[] = [
  {
    name: 'align_sequences',
    description: 'Perform multiple sequence alignment using MAFFT, MUSCLE, or Clustal Omega',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        method: {
          type: 'string',
          enum: ['mafft', 'muscle', 'clustalo', 'gget_muscle'],
          default: 'mafft',
          description: 'Alignment algorithm to use',
        },
        strategy: {
          type: 'string',
          enum: ['auto', 'linsi', 'ginsi', 'einsi', 'fftns', 'fftnsi'],
          default: 'auto',
          description: 'MAFFT alignment strategy (for MAFFT only)',
        },
        threads: {
          type: 'integer',
          default: 4,
          description: 'Number of threads to use',
        },
      },
      required: ['fasta_content'],
    },
  },

  {
    name: 'process_alignment',
    description: 'Clean and process alignment using CIAlign: remove gaps, poorly aligned sequences, and calculate quality metrics',
    inputSchema: {
      type: 'object',
      properties: {
        alignment: {
          type: 'string',
          description: 'Input alignment in FASTA format',
        },
        remove_divergent: {
          type: 'boolean',
          default: true,
          description: 'Remove highly divergent sequences',
        },
        remove_insertions: {
          type: 'boolean',
          default: true,
          description: 'Remove insertion columns',
        },
        crop_ends: {
          type: 'boolean',
          default: true,
          description: 'Crop poorly aligned ends',
        },
      },
      required: ['alignment'],
    },
  },

  {
    name: 'build_phylogeny',
    description: 'Build phylogenetic tree from alignment using BioPython (Neighbor Joining, Maximum Likelihood, or Maximum Parsimony)',
    inputSchema: {
      type: 'object',
      properties: {
        alignment: {
          type: 'string',
          description: 'Input alignment in FASTA format',
        },
        method: {
          type: 'string',
          enum: ['nj', 'ml', 'mp'],
          default: 'nj',
          description: 'Tree building method (nj=Neighbor Joining, ml=Maximum Likelihood, mp=Maximum Parsimony)',
        },
        bootstrap: {
          type: 'integer',
          default: 0,
          description: 'Number of bootstrap replicates (0 = no bootstrap)',
        },
      },
      required: ['alignment'],
    },
  },

  {
    name: 'calculate_distances',
    description: 'Calculate pairwise distance matrix from alignment',
    inputSchema: {
      type: 'object',
      properties: {
        alignment: {
          type: 'string',
          description: 'Input alignment in FASTA format',
        },
        model: {
          type: 'string',
          enum: ['identity', 'jukes-cantor', 'kimura'],
          default: 'identity',
          description: 'Evolutionary distance model',
        },
        format: {
          type: 'string',
          enum: ['matrix', 'phylip', 'json'],
          default: 'matrix',
          description: 'Output format',
        },
      },
      required: ['alignment'],
    },
  },

  {
    name: 'align_and_analyze',
    description: 'Complete pipeline: align sequences, clean alignment, and build phylogeny',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: {
          type: 'string',
          description: 'Input FASTA sequences',
        },
        run_id: {
          type: 'string',
          description: 'Run ID for organizing output files (optional)',
        },
        align_method: {
          type: 'string',
          enum: ['mafft', 'muscle', 'clustalo'],
          default: 'mafft',
          description: 'Alignment algorithm',
        },
        tree_method: {
          type: 'string',
          enum: ['nj', 'ml', 'mp'],
          default: 'nj',
          description: 'Tree building method',
        },
        clean_alignment: {
          type: 'boolean',
          default: true,
          description: 'Clean alignment with CIAlign',
        },
      },
      required: ['fasta_content'],
    },
  },
];

/**
 * Design Server Tool Definitions (6 tools)
 */
const designTools: ToolDefinition[] = [
  {
    name: 'find_signature_regions',
    description: 'Identify signature regions with high target conservation and off-target divergence',
    inputSchema: {
      type: 'object',
      properties: {
        target_alignment: {
          type: 'string',
          description: 'Target species alignment in FASTA format',
        },
        offtarget_alignment: {
          type: 'string',
          description: 'Off-target species alignment in FASTA format (optional)',
        },
        window_size: {
          type: 'integer',
          default: 100,
          description: 'Sliding window size for analysis',
        },
        step_size: {
          type: 'integer',
          default: 10,
          description: 'Step size for sliding window',
        },
        min_conservation: {
          type: 'number',
          default: 0.9,
          description: 'Minimum conservation threshold within target species',
        },
      },
      required: ['target_alignment'],
    },
  },

  {
    name: 'analyze_specificity',
    description: 'Analyze sequence specificity for target vs off-target discrimination',
    inputSchema: {
      type: 'object',
      properties: {
        target_sequences: {
          type: 'string',
          description: 'Target sequences in FASTA format',
        },
        offtarget_sequences: {
          type: 'string',
          description: 'Off-target sequences in FASTA format',
        },
        method: {
          type: 'string',
          enum: ['kmer', 'alignment', 'entropy'],
          default: 'kmer',
          description: 'Specificity analysis method',
        },
      },
      required: ['target_sequences'],
    },
  },

  {
    name: 'rank_regions',
    description: 'Rank candidate regions by multiple criteria (conservation, specificity, complexity)',
    inputSchema: {
      type: 'object',
      properties: {
        regions: {
          type: 'array',
          items: { type: 'object' },
          description: 'List of candidate regions from find_signature_regions',
        },
        weights: {
          type: 'object',
          description: 'Weights for ranking criteria (conservation, specificity, complexity)',
        },
        top_n: {
          type: 'integer',
          default: 10,
          description: 'Number of top regions to return',
        },
      },
      required: ['regions'],
    },
  },

  {
    name: 'primer3_design',
    description: 'Design primers using Primer3 with specified constraints',
    inputSchema: {
      type: 'object',
      properties: {
        template: {
          type: 'string',
          description: 'Template sequence',
        },
        target_region: {
          type: 'array',
          items: { type: 'integer' },
          description: 'Target region [start, length]',
        },
        primer_size: {
          type: 'array',
          items: { type: 'integer' },
          default: [18, 20, 25],
          description: 'Primer size [min, opt, max]',
        },
        primer_tm: {
          type: 'array',
          items: { type: 'number' },
          default: [57.0, 60.0, 63.0],
          description: 'Primer Tm [min, opt, max]',
        },
        product_size: {
          type: 'array',
          items: { type: 'integer' },
          default: [75, 150],
          description: 'Product size range [min, max]',
        },
        num_return: {
          type: 'integer',
          default: 5,
          description: 'Number of primer pairs to return',
        },
      },
      required: ['template'],
    },
  },

  {
    name: 'oligo_qc',
    description: 'Quality control for primers/oligos: check Tm, secondary structures (hairpins, dimers), GC content',
    inputSchema: {
      type: 'object',
      properties: {
        primers: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              sequence: { type: 'string' },
            },
          },
          description: 'List of primers to check',
        },
        check_hairpins: {
          type: 'boolean',
          default: true,
          description: 'Check for hairpin structures',
        },
        check_dimers: {
          type: 'boolean',
          default: true,
          description: 'Check for primer dimers',
        },
        max_hairpin_tm: {
          type: 'number',
          default: 45.0,
          description: 'Maximum allowed hairpin Tm',
        },
      },
      required: ['primers'],
    },
  },

  {
    name: 'design_primers_complete',
    description: 'Complete pipeline: find signature regions, design primers with Primer3, and perform QC',
    inputSchema: {
      type: 'object',
      properties: {
        target_alignment: {
          type: 'string',
          description: 'Target species alignment in FASTA format',
        },
        offtarget_alignment: {
          type: 'string',
          description: 'Off-target species alignment (optional)',
        },
        run_id: {
          type: 'string',
          description: 'Run ID for organizing output files (optional)',
        },
        num_primer_pairs: {
          type: 'integer',
          default: 5,
          description: 'Number of primer pairs to design',
        },
        primer_size_range: {
          type: 'array',
          items: { type: 'integer' },
          default: [18, 25],
          description: 'Primer size range [min, max]',
        },
        product_size_range: {
          type: 'array',
          items: { type: 'integer' },
          default: [75, 150],
          description: 'Product size range [min, max]',
        },
      },
      required: ['target_alignment'],
    },
  },
];

/**
 * Validation Server Tool Definitions (7 tools)
 */
const validationTools: ToolDefinition[] = [
  {
    name: 'gget_blast',
    description: 'Perform remote BLAST search via gget against NCBI or Ensembl databases',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: {
          type: 'string',
          description: 'Query sequence (nucleotide or protein)',
        },
        program: {
          type: 'string',
          enum: ['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx'],
          default: 'blastn',
          description: 'BLAST program',
        },
        database: {
          type: 'string',
          default: 'nt',
          description: 'BLAST database (nt, nr, refseq_rna, etc.)',
        },
        limit: {
          type: 'integer',
          default: 50,
          description: 'Maximum number of results',
        },
        expect: {
          type: 'number',
          default: 10.0,
          description: 'E-value threshold',
        },
      },
      required: ['sequence'],
    },
  },

  {
    name: 'gget_blat',
    description: 'Perform BLAT search via gget for short exact matches',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: {
          type: 'string',
          description: 'Query sequence',
        },
        assembly: {
          type: 'string',
          default: 'human',
          description: 'Genome assembly (human, mouse, etc.)',
        },
      },
      required: ['sequence'],
    },
  },

  {
    name: 'blast_nt',
    description: 'Perform local BLAST search against NT database (requires local BLAST+ installation and BLASTDB)',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: {
          type: 'string',
          description: 'Query sequence',
        },
        database: {
          type: 'string',
          default: 'nt',
          description: 'Local BLAST database name',
        },
        evalue: {
          type: 'number',
          default: 0.001,
          description: 'E-value threshold',
        },
        max_hits: {
          type: 'integer',
          default: 100,
          description: 'Maximum number of hits',
        },
        word_size: {
          type: 'integer',
          default: 11,
          description: 'Word size for BLAST',
        },
      },
      required: ['sequence'],
    },
  },

  {
    name: 'in_silico_pcr',
    description: 'Simulate PCR amplification with primer pair against sequence database',
    inputSchema: {
      type: 'object',
      properties: {
        forward_primer: {
          type: 'string',
          description: 'Forward primer sequence',
        },
        reverse_primer: {
          type: 'string',
          description: 'Reverse primer sequence',
        },
        database_sequences: {
          type: 'string',
          description: 'Target sequences in FASTA format',
        },
        max_product_size: {
          type: 'integer',
          default: 2000,
          description: 'Maximum amplicon size',
        },
        mismatch_tolerance: {
          type: 'integer',
          default: 1,
          description: 'Number of mismatches allowed',
        },
      },
      required: ['forward_primer', 'reverse_primer', 'database_sequences'],
    },
  },

  {
    name: 'assess_coverage',
    description: 'Assess primer coverage (sensitivity and specificity) against target and off-target sequences',
    inputSchema: {
      type: 'object',
      properties: {
        primers: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              forward: { type: 'string' },
              reverse: { type: 'string' },
            },
          },
          description: 'Primer pairs to assess',
        },
        target_sequences: {
          type: 'string',
          description: 'Target sequences in FASTA format',
        },
        offtarget_sequences: {
          type: 'string',
          description: 'Off-target sequences in FASTA format (optional)',
        },
        mismatch_tolerance: {
          type: 'integer',
          default: 1,
          description: 'Mismatches allowed for binding',
        },
      },
      required: ['primers', 'target_sequences'],
    },
  },

  {
    name: 'search_pubmed',
    description: 'Search PubMed/Entrez for literature validation of primers or targets',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'PubMed search query',
        },
        max_results: {
          type: 'integer',
          default: 20,
          description: 'Maximum number of results',
        },
        retmode: {
          type: 'string',
          enum: ['xml', 'json', 'text'],
          default: 'json',
          description: 'Return format',
        },
      },
      required: ['query'],
    },
  },

  {
    name: 'validate_primers_complete',
    description: 'Complete validation pipeline: BLAST specificity, in-silico PCR, coverage assessment, and literature search',
    inputSchema: {
      type: 'object',
      properties: {
        primers: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              forward: { type: 'string' },
              reverse: { type: 'string' },
            },
          },
          description: 'Primer pairs to validate',
        },
        target_sequences: {
          type: 'string',
          description: 'Target sequences in FASTA format',
        },
        offtarget_sequences: {
          type: 'string',
          description: 'Off-target sequences (optional)',
        },
        run_id: {
          type: 'string',
          description: 'Run ID for organizing output files (optional)',
        },
        organism: {
          type: 'string',
          description: 'Target organism for literature search',
        },
      },
      required: ['primers', 'target_sequences'],
    },
  },
];

/**
 * Generate all tool files for a server
 */
async function generateServerTools(
  serverName: string,
  tools: ToolDefinition[],
  outputDir: string
): Promise<void> {
  console.log(`\n🔧 Generating ${serverName} Server Tools`);
  console.log(`   Tools: ${tools.length}`);
  console.log(`   Output: ${outputDir}\n`);

  const generator = new ToolFileGenerator();
  await generator.generateToolFiles(serverName, tools, outputDir);

  console.log(`✅ ${serverName} server tools generated\n`);
}

/**
 * Main function
 */
async function main() {
  console.log('\n═══════════════════════════════════════════════════');
  console.log('    GENERATING ALL REMAINING SERVER TOOLS');
  console.log('═══════════════════════════════════════════════════\n');
  console.log('Total tools: 23');
  console.log('  - Processing: 5 tools');
  console.log('  - Alignment: 5 tools');
  console.log('  - Design: 6 tools');
  console.log('  - Validation: 7 tools');
  console.log('═══════════════════════════════════════════════════');

  const baseDir = path.join(process.cwd(), 'workspace', 'servers');

  try {
    // Generate Processing Server tools
    await generateServerTools(
      'processing',
      processingTools,
      path.join(baseDir, 'processing')
    );

    // Generate Alignment Server tools
    await generateServerTools(
      'alignment',
      alignmentTools,
      path.join(baseDir, 'alignment')
    );

    // Generate Design Server tools
    await generateServerTools(
      'design',
      designTools,
      path.join(baseDir, 'design')
    );

    // Generate Validation Server tools
    await generateServerTools(
      'validation',
      validationTools,
      path.join(baseDir, 'validation')
    );

    console.log('\n═══════════════════════════════════════════════════');
    console.log('    ✅ GENERATION COMPLETE!');
    console.log('═══════════════════════════════════════════════════\n');

    console.log('Generated files:');
    console.log('  workspace/servers/processing/   (5 tools + index + README)');
    console.log('  workspace/servers/alignment/    (5 tools + index + README)');
    console.log('  workspace/servers/design/       (6 tools + index + README)');
    console.log('  workspace/servers/validation/   (7 tools + index + README)\n');

    console.log('Next steps:');
    console.log('  1. Run typecheck: npm run typecheck');
    console.log('  2. Run tests: npm test');
    console.log('  3. Import tools:');
    console.log('     import * as processing from "./workspace/servers/processing";');
    console.log('     import * as alignment from "./workspace/servers/alignment";');
    console.log('     import * as design from "./workspace/servers/design";');
    console.log('     import * as validation from "./workspace/servers/validation";\n');
  } catch (error: any) {
    console.error('\n❌ Generation failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { processingTools, alignmentTools, designTools, validationTools };
