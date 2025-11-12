/**
 * Generate All MCP Server Tools
 * 
 * Generates TypeScript wrappers for all 5 MCP servers:
 * - Database (11 tools)
 * - Processing (5 tools)
 * - Alignment (5 tools)
 * - Design (6 tools)
 * - Validation (7 tools)
 * 
 * Usage:
 * ```bash
 * npx tsx examples/generate-all-tools.ts
 * ```
 */

import { ToolFileGenerator, ToolDefinition } from '../mcp_servers/shared/tool-generator.js';

// Import tool definitions
import { databaseTools } from './generate-database-tools.js';

// ========================================
// PROCESSING TOOLS
// ========================================
const processingTools: ToolDefinition[] = [
  {
    name: 'fasta_qc',
    description: 'Quality control for FASTA sequences',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'FASTA format sequences' },
        min_length: { type: 'integer', description: 'Minimum sequence length', default: 100 },
        max_n_percent: { type: 'number', description: 'Maximum N percentage', default: 5.0 },
        remove_duplicates: { type: 'boolean', description: 'Remove duplicates', default: false },
      },
      required: ['fasta_content'],
    },
  },
  {
    name: 'dereplicate_sequences',
    description: 'Remove duplicate or highly similar sequences',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'FASTA format sequences' },
        identity_threshold: { type: 'number', description: 'Sequence identity threshold', default: 0.97 },
      },
      required: ['fasta_content'],
    },
  },
  {
    name: 'mask_low_complexity',
    description: 'Mask low-complexity regions in sequences',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'FASTA format sequences' },
        method: { type: 'string', enum: ['dust', 'seg'], description: 'Masking method', default: 'dust' },
        window: { type: 'integer', description: 'Window size' },
        threshold: { type: 'number', description: 'Complexity threshold' },
      },
      required: ['fasta_content'],
    },
  },
  {
    name: 'detect_chimeras',
    description: 'Detect chimeric sequences using UCHIME algorithm',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'FASTA format sequences' },
        reference_db: { type: 'string', description: 'Reference database', default: 'auto' },
      },
      required: ['fasta_content'],
    },
  },
  {
    name: 'process_sequences',
    description: 'Complete QC pipeline - combines all processing steps',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'FASTA format sequences' },
        min_length: { type: 'integer', description: 'Minimum sequence length', default: 100 },
        max_n_percent: { type: 'number', description: 'Maximum N percentage', default: 5.0 },
        remove_duplicates: { type: 'boolean', description: 'Remove duplicates', default: true },
        mask_complexity: { type: 'boolean', description: 'Mask low complexity', default: false },
        detect_chimeras: { type: 'boolean', description: 'Detect chimeras', default: false },
      },
      required: ['fasta_content'],
    },
  },
];

// ========================================
// ALIGNMENT TOOLS
// ========================================
const alignmentTools: ToolDefinition[] = [
  {
    name: 'align_sequences',
    description: 'Align sequences using MAFFT, MUSCLE, or Clustal Omega',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'Unaligned sequences in FASTA format' },
        method: { type: 'string', enum: ['mafft', 'muscle', 'clustalo'], description: 'Alignment method', default: 'mafft' },
        strategy: { type: 'string', enum: ['auto', 'fast', 'accurate'], description: 'Alignment strategy', default: 'auto' },
      },
      required: ['fasta_content'],
    },
  },
  {
    name: 'process_alignment',
    description: 'Clean and assess alignment quality',
    inputSchema: {
      type: 'object',
      properties: {
        alignment: { type: 'string', description: 'Aligned sequences in FASTA format' },
        remove_gaps: { type: 'boolean', description: 'Remove gap-only columns', default: true },
        remove_divergent: { type: 'boolean', description: 'Remove divergent sequences', default: false },
        divergence_threshold: { type: 'number', description: 'Divergence threshold', default: 0.5 },
      },
      required: ['alignment'],
    },
  },
  {
    name: 'build_phylogeny',
    description: 'Build phylogenetic tree from alignment',
    inputSchema: {
      type: 'object',
      properties: {
        alignment: { type: 'string', description: 'Aligned sequences in FASTA format' },
        method: { type: 'string', enum: ['nj', 'upgma', 'ml'], description: 'Tree building method', default: 'nj' },
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
        alignment: { type: 'string', description: 'Aligned sequences in FASTA format' },
        model: { type: 'string', enum: ['p-distance', 'jc69', 'k2p'], description: 'Distance model', default: 'p-distance' },
      },
      required: ['alignment'],
    },
  },
  {
    name: 'align_and_analyze',
    description: 'Complete alignment pipeline - align, clean, build tree, calculate distances',
    inputSchema: {
      type: 'object',
      properties: {
        fasta_content: { type: 'string', description: 'Unaligned sequences in FASTA format' },
        method: { type: 'string', enum: ['mafft', 'muscle', 'clustalo'], description: 'Alignment method', default: 'mafft' },
        build_tree: { type: 'boolean', description: 'Build phylogenetic tree', default: true },
        calculate_distances: { type: 'boolean', description: 'Calculate distances', default: true },
      },
      required: ['fasta_content'],
    },
  },
];

// ========================================
// DESIGN TOOLS
// ========================================
const designTools: ToolDefinition[] = [
  {
    name: 'find_signature_regions',
    description: 'Find signature regions for specific primer design',
    inputSchema: {
      type: 'object',
      properties: {
        target_alignment: { type: 'string', description: 'Target species alignment' },
        offtarget_alignment: { type: 'string', description: 'Off-target species alignment' },
        window_size: { type: 'integer', description: 'Analysis window size', default: 100 },
        min_conservation: { type: 'number', description: 'Minimum conservation threshold', default: 0.9 },
      },
      required: ['target_alignment'],
    },
  },
  {
    name: 'primer3_design',
    description: 'Design primers using Primer3',
    inputSchema: {
      type: 'object',
      properties: {
        template: { type: 'string', description: 'DNA template sequence' },
        target_region: { type: 'array', items: { type: 'integer' }, description: 'Target region [start, end]' },
        primer_size: { type: 'array', items: { type: 'integer' }, description: 'Primer size range [min, opt, max]', default: [18, 20, 25] },
      },
      required: ['template'],
    },
  },
  {
    name: 'analyze_specificity',
    description: 'Analyze target vs off-target specificity for primer design',
    inputSchema: {
      type: 'object',
      properties: {
        target_alignment: { type: 'string', description: 'Target species alignment' },
        offtarget_alignment: { type: 'string', description: 'Off-target species alignment' },
        window_size: { type: 'integer', description: 'Analysis window size', default: 100 },
      },
      required: ['target_alignment'],
    },
  },
  {
    name: 'rank_regions',
    description: 'Rank candidate regions for primer design',
    inputSchema: {
      type: 'object',
      properties: {
        regions: { type: 'array', items: { type: 'object' }, description: 'Candidate regions with metrics' },
        weights: {
          type: 'object',
          description: 'Weighting for different criteria',
          properties: {
            conservation: { type: 'number', default: 0.4 },
            specificity: { type: 'number', default: 0.4 },
            complexity: { type: 'number', default: 0.2 },
          }
        },
      },
      required: ['regions'],
    },
  },
  {
    name: 'oligo_qc',
    description: 'Quality control for oligonucleotides - Tm, secondary structure, dimers',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: { type: 'string', description: 'Oligonucleotide sequence' },
        check_hairpin: { type: 'boolean', description: 'Check for hairpins', default: true },
        check_homodimer: { type: 'boolean', description: 'Check for homodimers', default: true },
        salt_concentration: { type: 'number', description: 'Salt concentration (mM)', default: 50 },
      },
      required: ['sequence'],
    },
  },
  {
    name: 'design_primers_complete',
    description: 'Complete primer design pipeline - find regions, design, and QC',
    inputSchema: {
      type: 'object',
      properties: {
        target_alignment: { type: 'string', description: 'Target species alignment' },
        offtarget_alignment: { type: 'string', description: 'Off-target species alignment' },
        num_primer_pairs: { type: 'integer', description: 'Number of primer pairs', default: 5 },
        product_size_range: { type: 'array', items: { type: 'integer' }, description: 'Product size range [min, max]', default: [100, 300] },
      },
      required: ['target_alignment'],
    },
  },
];

// ========================================
// VALIDATION TOOLS
// ========================================
const validationTools: ToolDefinition[] = [
  {
    name: 'gget_blast',
    description: 'BLAST search using gget (NCBI BLAST)',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: { type: 'string', description: 'Query sequence' },
        program: { type: 'string', enum: ['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx'], description: 'BLAST program', default: 'blastn' },
        database: { type: 'string', description: 'BLAST database', default: 'nt' },
        limit: { type: 'integer', description: 'Maximum number of hits', default: 50 },
      },
      required: ['sequence'],
    },
  },
  {
    name: 'in_silico_pcr',
    description: 'Perform in silico PCR with primers',
    inputSchema: {
      type: 'object',
      properties: {
        forward_primer: { type: 'string', description: 'Forward primer sequence' },
        reverse_primer: { type: 'string', description: 'Reverse primer sequence' },
        database_sequences: { type: 'string', description: 'Target sequences in FASTA format' },
        max_product_size: { type: 'integer', description: 'Maximum amplicon size', default: 2000 },
      },
      required: ['forward_primer', 'reverse_primer', 'database_sequences'],
    },
  },
  {
    name: 'gget_blat',
    description: 'BLAT search using gget for fast alignment',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: { type: 'string', description: 'Query sequence' },
        seqtype: { type: 'string', enum: ['DNA', 'protein', 'translated RNA', 'translated DNA'], description: 'Sequence type', default: 'DNA' },
        assembly: { type: 'string', description: 'Genome assembly', default: 'human' },
      },
      required: ['sequence'],
    },
  },
  {
    name: 'blast_nt',
    description: 'BLAST against NCBI nucleotide database',
    inputSchema: {
      type: 'object',
      properties: {
        sequence: { type: 'string', description: 'Query sequence' },
        database: { type: 'string', description: 'BLAST database', default: 'nt' },
        evalue: { type: 'number', description: 'E-value threshold', default: 0.001 },
        max_hits: { type: 'integer', description: 'Maximum hits', default: 50 },
      },
      required: ['sequence'],
    },
  },
  {
    name: 'assess_coverage',
    description: 'Assess taxonomic coverage of primers',
    inputSchema: {
      type: 'object',
      properties: {
        forward_primer: { type: 'string', description: 'Forward primer sequence' },
        reverse_primer: { type: 'string', description: 'Reverse primer sequence' },
        target_taxa: { type: 'array', items: { type: 'string' }, description: 'Target taxa list' },
        offtarget_taxa: { type: 'array', items: { type: 'string' }, description: 'Off-target taxa list' },
      },
      required: ['forward_primer', 'reverse_primer', 'target_taxa'],
    },
  },
  {
    name: 'search_pubmed',
    description: 'Search PubMed for related literature',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        max_results: { type: 'integer', description: 'Maximum results', default: 10 },
        filter_primers: { type: 'boolean', description: 'Filter for primer-related papers', default: false },
      },
      required: ['query'],
    },
  },
  {
    name: 'validate_primers_complete',
    description: 'Complete primer validation pipeline - BLAST, in silico PCR, coverage',
    inputSchema: {
      type: 'object',
      properties: {
        forward_primer: { type: 'string', description: 'Forward primer sequence' },
        reverse_primer: { type: 'string', description: 'Reverse primer sequence' },
        target_taxa: { type: 'array', items: { type: 'string' }, description: 'Target taxa' },
        offtarget_taxa: { type: 'array', items: { type: 'string' }, description: 'Off-target taxa' },
        reference_sequences: { type: 'string', description: 'Reference sequences in FASTA' },
      },
      required: ['forward_primer', 'reverse_primer', 'reference_sequences'],
    },
  },
];

/**
 * Generate all server tools
 */
async function main() {
  console.log('🚀 Generating All MCP Server Tools\n');
  console.log('═══════════════════════════════════════════════════════\n');

  const generator = new ToolFileGenerator();

  // Copy base infrastructure files
  console.log('📋 Copying base infrastructure files...\n');
  try {
    await generator.copyBaseFiles('./workspace');
  } catch (error) {
    console.error('\n❌ Error copying base files:', error);
    process.exit(1);
  }

  const servers = [
    { name: 'database', tools: databaseTools },
    { name: 'processing', tools: processingTools },
    { name: 'alignment', tools: alignmentTools },
    { name: 'design', tools: designTools },
    { name: 'validation', tools: validationTools },
  ];

  let totalTools = 0;

  for (const server of servers) {
    try {
      await generator.generateToolFiles(
        server.name,
        server.tools,
        './workspace'
      );
      totalTools += server.tools.length;
    } catch (error) {
      console.error(`\n❌ Error generating ${server.name} tools:`, error);
      process.exit(1);
    }
  }

  console.log('═══════════════════════════════════════════════════════');
  console.log(`\n✅ Successfully generated ${totalTools} tools across 5 servers!`);
  console.log('\n📝 Next steps:');
  console.log('  1. Run: npm run build:workspace');
  console.log('  2. Restart Claude Desktop');
  console.log('  3. Test: All 34 tools should now work via generated modules!');
  console.log('\n📊 Generated modules:');
  console.log('  - workspace/lib/mcp-client.ts (MCP bridge)');
  console.log('  - workspace/servers/database/ (11 tools)');
  console.log('  - workspace/servers/processing/ (5 tools)');
  console.log('  - workspace/servers/alignment/ (5 tools)');
  console.log('  - workspace/servers/design/ (6 tools)');
  console.log('  - workspace/servers/validation/ (7 tools)');
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { processingTools, alignmentTools, designTools, validationTools };

