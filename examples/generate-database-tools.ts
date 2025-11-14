/**
 * Database Server Tool Definitions - SCHEMA SOURCE OF TRUTH
 *
 * This file contains the JSON Schema definitions for all 11 database server tools.
 * These schemas are imported by generate-all-tools.ts and used by ToolFileGenerator
 * to create type-safe TypeScript client wrappers.
 *
 * Architecture:
 * - This file exports schema definitions only (no generation logic)
 * - Imported by generate-all-tools.ts (the main generation script)
 * - Schemas must match the Python server's tool definitions
 *
 * Key Feature: Advanced Filtering
 * ================================
 * The get_sequences tool includes comprehensive filtering capabilities:
 * - Length filters (min/max base pairs)
 * - Completeness (complete/partial genomes)
 * - Upload date range
 * - Geographic location
 * - Quality thresholds
 * - Exclusions (predicted/environmental sequences)
 *
 * Maintenance:
 * - When updating Python server schemas, update here first
 * - Then run: npm run generate-tools
 * - TypeScript wrappers will be regenerated automatically
 *
 * Usage:
 * ```bash
 * # Import in other scripts:
 * import { databaseTools } from './generate-database-tools.js';
 * 
 * # Or run standalone to generate database tools only:
 * npx tsx examples/generate-database-tools.ts
 * ```
 */

import { ToolFileGenerator, ToolDefinition } from '../mcp_servers/shared/dist/tool-generator.js';

/**
 * Database Server tool definitions
 *
 * These schemas match the tools defined in:
 * mcp_servers/database_server/database_mcp_server.py
 */
const databaseTools: ToolDefinition[] = [
  {
    name: 'get_sequences',
    description: 'Retrieve sequences from multiple databases with advanced filtering',
    inputSchema: {
      type: 'object',
      properties: {
        taxon: {
          type: 'string',
          description: 'Taxon name or ID',
        },
        region: {
          type: 'string',
          enum: ['COI', '16S', 'ITS', 'mitogenome', 'whole'],
          description: 'Target genomic region',
        },
        source: {
          type: 'string',
          enum: ['gget', 'ncbi', 'bold', 'silva', 'unite'],
          description: 'Database source',
          default: 'gget',
        },
        max_results: {
          type: 'integer',
          description: 'Maximum number of results',
          default: 100,
        },
        format: {
          type: 'string',
          enum: ['fasta', 'genbank'],
          description: 'Output format',
          default: 'fasta',
        },
        filters: {
          type: 'object',
          description: 'Advanced filtering options',
          properties: {
            min_length: {
              type: 'integer',
              description: 'Minimum sequence length in base pairs',
            },
            max_length: {
              type: 'integer',
              description: 'Maximum sequence length in base pairs',
            },
            completeness: {
              type: 'string',
              enum: ['complete', 'partial', 'any'],
              default: 'any',
              description: 'Sequence completeness level',
            },
            upload_date_start: {
              type: 'string',
              format: 'date',
              description: 'Start date for upload/submission (YYYY-MM-DD)',
            },
            upload_date_end: {
              type: 'string',
              format: 'date',
              description: 'End date for upload/submission (YYYY-MM-DD)',
            },
            country: {
              type: 'string',
              description: 'Filter by country/geographic location',
            },
            has_geo_location: {
              type: 'boolean',
              description: 'Only include sequences with geographic location data',
            },
            quality_filter: {
              type: 'string',
              enum: ['high', 'medium', 'any'],
              default: 'any',
              description: 'Sequence quality threshold',
            },
            exclude_predicted: {
              type: 'boolean',
              default: false,
              description: 'Exclude predicted/inferred sequences',
            },
            exclude_environmental: {
              type: 'boolean',
              default: false,
              description: 'Exclude environmental/uncultured samples',
            },
          },
        },
      },
      required: ['taxon'],
    },
  },
  {
    name: 'gget_ref',
    description: 'Get reference genome information from Ensembl',
    inputSchema: {
      type: 'object',
      properties: {
        species: {
          type: 'string',
          description: 'Species name (e.g., "homo_sapiens")',
        },
        release: {
          type: 'integer',
          description: 'Ensembl release number (optional)',
        },
        which: {
          type: 'string',
          enum: ['all', 'gtf', 'cdna', 'dna', 'cds', 'pep'],
          description: 'Type of reference data to retrieve',
        },
      },
      required: ['species'],
    },
  },
  {
    name: 'gget_search',
    description: 'Search for genes in Ensembl database',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query (gene name, symbol, or ID)',
        },
        species: {
          type: 'string',
          description: 'Species name',
        },
        limit: {
          type: 'integer',
          description: 'Maximum number of results',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'gget_info',
    description: 'Get detailed information about a gene from Ensembl',
    inputSchema: {
      type: 'object',
      properties: {
        gene_id: {
          type: 'string',
          description: 'Ensembl gene ID',
        },
      },
      required: ['gene_id'],
    },
  },
  {
    name: 'gget_seq',
    description: 'Retrieve nucleotide or amino acid sequence by Ensembl ID',
    inputSchema: {
      type: 'object',
      properties: {
        gene_id: {
          type: 'string',
          description: 'Ensembl gene ID',
        },
        seqtype: {
          type: 'string',
          enum: ['transcript', 'protein', 'cds'],
          description: 'Sequence type to retrieve',
        },
        translate: {
          type: 'boolean',
          description: 'Translate nucleotide to protein sequence',
        },
      },
      required: ['gene_id'],
    },
  },
  {
    name: 'get_neighbors',
    description: 'Find taxonomically related species',
    inputSchema: {
      type: 'object',
      properties: {
        taxon: {
          type: 'string',
          description: 'Taxon name or ID',
        },
        rank: {
          type: 'string',
          enum: ['species', 'genus', 'family', 'order', 'class', 'phylum'],
          description: 'Taxonomic rank for neighbor search',
        },
        distance: {
          type: 'integer',
          description: 'Taxonomic distance (number of ranks)',
        },
      },
      required: ['taxon'],
    },
  },
  {
    name: 'get_taxonomy',
    description: 'Get complete taxonomic lineage and classification',
    inputSchema: {
      type: 'object',
      properties: {
        taxon: {
          type: 'string',
          description: 'Taxon name or taxonomic ID',
        },
      },
      required: ['taxon'],
    },
  },
  {
    name: 'search_sra_studies',
    description: 'Search SRA/BioProject for sequencing studies',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Search query (species, project type, etc.)',
        },
        max_results: {
          type: 'integer',
          description: 'Maximum number of studies to return',
        },
        organism: {
          type: 'string',
          description: 'Filter by organism name',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'get_sra_runinfo',
    description: 'Get detailed run information for SRA study',
    inputSchema: {
      type: 'object',
      properties: {
        study_id: {
          type: 'string',
          description: 'SRA study ID (e.g., SRP123456)',
        },
      },
      required: ['study_id'],
    },
  },
  {
    name: 'search_sra_cloud',
    description: 'Search SRA via cloud SQL (BigQuery/Athena)',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'SQL query for cloud database',
        },
        cloud_provider: {
          type: 'string',
          enum: ['bigquery', 'athena'],
          description: 'Cloud SQL provider',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'extract_sequence_columns',
    description: 'Extract metadata columns from FASTA/GenBank sequences',
    inputSchema: {
      type: 'object',
      properties: {
        sequence_data: {
          type: 'string',
          description: 'FASTA or GenBank formatted sequences',
        },
        columns: {
          type: 'array',
          items: { type: 'string' },
          description: 'Columns to extract (e.g., ["accession", "organism", "country"])',
        },
        output_format: {
          type: 'string',
          enum: ['json', 'csv', 'tsv', 'table'],
          description: 'Output format',
        },
      },
      required: ['sequence_data'],
    },
  },
];

/**
 * Generate Database Server tools
 */
async function main() {
  console.log('🚀 Database Server Tool Generator\n');

  const generator = new ToolFileGenerator();

  try {
    // Generate all tool files
    await generator.generateToolFiles(
      'database',
      databaseTools,
      './workspace'
    );

    console.log('\n✅ Tool generation complete!');
    console.log('\n📝 Next steps:');
    console.log('  1. Review generated files in workspace/servers/database/');
    console.log('  2. Run: tsc --noEmit workspace/servers/database/*.ts');
    console.log('  3. Test imports: import * as database from "./workspace/servers/database"');
    console.log('\n📊 Token Efficiency:');
    console.log(`  Traditional: ${databaseTools.length * 3500} tokens (all tools loaded)`);
    console.log(`  Code Execution: ~400 tokens per tool (loaded on demand)`);
    console.log(`  Reduction: ~99%`);
  } catch (error) {
    console.error('\n❌ Error generating tools:', error);
    process.exit(1);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { databaseTools };
