/**
 * Generate TypeScript Tool Files for Database Server
 *
 * This script generates typed tool wrappers for all 11 database server tools.
 *
 * Usage:
 * ```bash
 * npx tsx examples/generate-all-database-tools.ts
 * ```
 */

import { ToolFileGenerator, type ToolDefinition } from '../mcp_servers/shared/tool-generator.js';
import * as path from 'path';

/**
 * Database Server Tool Definitions (11 tools)
 */
const databaseTools: ToolDefinition[] = [
  // 1. get_sequences - Core sequence retrieval
  {
    name: 'get_sequences',
    description: 'Retrieve sequences from multiple databases (NCBI, BOLD, SILVA, UNITE)',
    inputSchema: {
      type: 'object',
      properties: {
        taxon: {
          type: 'string',
          description: 'Taxon name or ID (e.g., "Salmo salar", "NCBI:txid8030")',
        },
        region: {
          type: 'string',
          enum: ['COI', '16S', 'ITS', 'mitogenome', 'whole'],
          description: 'Target genomic region',
        },
        source: {
          type: 'string',
          enum: ['gget', 'ncbi', 'bold', 'silva', 'unite'],
          default: 'gget',
          description: 'Database source',
        },
        max_results: {
          type: 'integer',
          default: 100,
          description: 'Maximum number of sequences to retrieve',
        },
        format: {
          type: 'string',
          enum: ['fasta', 'genbank'],
          default: 'fasta',
          description: 'Output format',
        },
      },
      required: ['taxon'],
    },
  },

  // 2. gget_ref - Reference genome information
  {
    name: 'gget_ref',
    description: 'Get reference genome information from Ensembl database',
    inputSchema: {
      type: 'object',
      properties: {
        species: {
          type: 'string',
          description: 'Species name or Ensembl ID (e.g., "homo_sapiens", "mus_musculus")',
        },
        release: {
          type: 'integer',
          description: 'Ensembl release version (optional, uses latest if not specified)',
        },
        which: {
          type: 'string',
          enum: ['all', 'gtf', 'cdna', 'dna', 'cds', 'ncrna', 'pep'],
          default: 'all',
          description: 'Type of reference data to retrieve',
        },
      },
      required: ['species'],
    },
  },

  // 3. gget_search - Search Ensembl database
  {
    name: 'gget_search',
    description: 'Search the Ensembl database for genes and transcripts',
    inputSchema: {
      type: 'object',
      properties: {
        search_term: {
          type: 'string',
          description: 'Gene name, Ensembl ID, or keyword to search for',
        },
        species: {
          type: 'string',
          default: 'homo_sapiens',
          description: 'Species to search in',
        },
        limit: {
          type: 'integer',
          default: 10,
          description: 'Maximum number of results',
        },
      },
      required: ['search_term'],
    },
  },

  // 4. gget_info - Gene/transcript information
  {
    name: 'gget_info',
    description: 'Get detailed information about genes or transcripts from Ensembl',
    inputSchema: {
      type: 'object',
      properties: {
        ensembl_ids: {
          type: 'array',
          items: { type: 'string' },
          description: 'List of Ensembl IDs (genes or transcripts)',
        },
      },
      required: ['ensembl_ids'],
    },
  },

  // 5. gget_seq - Sequence retrieval from Ensembl
  {
    name: 'gget_seq',
    description: 'Retrieve nucleotide or amino acid sequences from Ensembl',
    inputSchema: {
      type: 'object',
      properties: {
        ensembl_ids: {
          type: 'array',
          items: { type: 'string' },
          description: 'List of Ensembl IDs',
        },
        translate: {
          type: 'boolean',
          default: false,
          description: 'Return amino acid translation instead of nucleotides',
        },
        isoforms: {
          type: 'boolean',
          default: false,
          description: 'Include all isoforms',
        },
      },
      required: ['ensembl_ids'],
    },
  },

  // 6. get_neighbors - Get phylogenetic neighbors
  {
    name: 'get_neighbors',
    description: 'Get phylogenetically related sequences from NCBI',
    inputSchema: {
      type: 'object',
      properties: {
        taxon: {
          type: 'string',
          description: 'Target taxon name or ID',
        },
        include_subspecies: {
          type: 'boolean',
          default: true,
          description: 'Include subspecies in results',
        },
        max_distance: {
          type: 'integer',
          default: 2,
          description: 'Maximum taxonomic distance (1=genus, 2=family, 3=order)',
        },
        max_results: {
          type: 'integer',
          default: 50,
          description: 'Maximum sequences per neighbor taxon',
        },
      },
      required: ['taxon'],
    },
  },

  // 7. get_taxonomy - Taxonomic information
  {
    name: 'get_taxonomy',
    description: 'Get taxonomic information and lineage from NCBI Taxonomy',
    inputSchema: {
      type: 'object',
      properties: {
        taxon: {
          type: 'string',
          description: 'Taxon name or NCBI taxonomy ID',
        },
        include_lineage: {
          type: 'boolean',
          default: true,
          description: 'Include full taxonomic lineage',
        },
      },
      required: ['taxon'],
    },
  },

  // 8. search_sra_studies - Search SRA studies
  {
    name: 'search_sra_studies',
    description: 'Search SRA (Sequence Read Archive) for studies and experiments',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query (organism name, keyword, etc.)',
        },
        max_results: {
          type: 'integer',
          default: 20,
          description: 'Maximum number of studies to return',
        },
      },
      required: ['query'],
    },
  },

  // 9. get_sra_runinfo - SRA run information
  {
    name: 'get_sra_runinfo',
    description: 'Get detailed run information for SRA accessions',
    inputSchema: {
      type: 'object',
      properties: {
        accession: {
          type: 'string',
          description: 'SRA accession (SRR, SRP, SRX, or BioProject ID)',
        },
        detailed: {
          type: 'boolean',
          default: false,
          description: 'Include detailed metadata',
        },
      },
      required: ['accession'],
    },
  },

  // 10. search_sra_cloud - Search SRA in cloud (BigQuery/Athena)
  {
    name: 'search_sra_cloud',
    description: 'Search SRA metadata using cloud services (BigQuery or Athena)',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'SQL-like query for SRA metadata',
        },
        platform: {
          type: 'string',
          enum: ['bigquery', 'athena'],
          default: 'bigquery',
          description: 'Cloud platform to use',
        },
        max_results: {
          type: 'integer',
          default: 100,
          description: 'Maximum number of results',
        },
      },
      required: ['query'],
    },
  },

  // 11. extract_sequence_columns - Extract metadata from sequences
  {
    name: 'extract_sequence_columns',
    description: 'Parse FASTA/GenBank files and extract metadata into structured format',
    inputSchema: {
      type: 'object',
      properties: {
        sequences: {
          type: 'string',
          description: 'FASTA or GenBank formatted sequences',
        },
        format: {
          type: 'string',
          enum: ['fasta', 'genbank'],
          default: 'fasta',
          description: 'Input sequence format',
        },
        output_format: {
          type: 'string',
          enum: ['json', 'csv', 'tsv', 'table'],
          default: 'json',
          description: 'Output format for metadata',
        },
        columns: {
          type: 'array',
          items: {
            type: 'string',
            enum: [
              'accession',
              'organism',
              'length',
              'description',
              'definition',
              'geographic_location',
              'collection_date',
              'collected_by',
              'identified_by',
              'country',
              'lat_lon',
              'specimen_voucher',
              'culture_collection',
              'isolate',
              'strain',
              'mol_type',
              'organelle',
              'gene',
              'product',
              'authors',
            ],
          },
          description: 'Specific columns to extract (extracts all if not specified)',
        },
      },
      required: ['sequences'],
    },
  },
];

/**
 * Main function
 */
async function main() {
  console.log('🔧 Generating Database Server Tools\n');
  console.log(`Total tools: ${databaseTools.length}\n`);

  // Initialize generator
  const generator = new ToolFileGenerator();

  // Output directory
  const outputDir = path.join(process.cwd(), 'workspace', 'servers', 'database');

  try {
    // Generate all tool files
    await generator.generateToolFiles('database', databaseTools, outputDir);

    console.log('\n✅ Generation complete!\n');
    console.log('Next steps:');
    console.log('  1. Review generated files in workspace/servers/database/');
    console.log('  2. Run typecheck: npm run typecheck');
    console.log('  3. Import tools: import * as database from "./workspace/servers/database";');
    console.log('  4. Use tools: await database.getSequences({ taxon: "Salmo salar" });\n');
  } catch (error: any) {
    console.error('❌ Generation failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { databaseTools };
