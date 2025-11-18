#!/usr/bin/env node
/**
 * Test script to verify tool-generator handles filters correctly
 * 
 * This script tests the updated tool-generator.ts with the database server's
 * get_sequences tool, which includes the complex filters parameter.
 */

import { ToolFileGenerator } from '../mcp_servers/shared/dist/tool-generator.js';

const testTool = {
  name: 'get_sequences',
  description: 'Retrieve sequences from multiple databases with advanced filtering',
  inputSchema: {
    type: 'object',
    properties: {
      taxon: {
        type: 'string',
        description: 'Taxon name or ID'
      },
      region: {
        type: 'string',
        enum: ['COI', '16S', 'ITS', 'mitogenome', 'whole'],
        description: 'Target genomic region'
      },
      source: {
        type: 'string',
        enum: ['gget', 'ncbi', 'bold', 'silva', 'unite'],
        default: 'gget',
        description: 'Database source'
      },
      max_results: {
        type: 'integer',
        default: 100,
        description: 'Maximum number of results'
      },
      format: {
        type: 'string',
        enum: ['fasta', 'genbank'],
        default: 'fasta',
        description: 'Output format'
      },
      filters: {
        type: 'object',
        description: 'Advanced filtering options',
        properties: {
          min_length: {
            type: 'integer',
            description: 'Minimum sequence length in base pairs'
          },
          max_length: {
            type: 'integer',
            description: 'Maximum sequence length in base pairs'
          },
          completeness: {
            type: 'string',
            enum: ['complete', 'partial', 'any'],
            default: 'any',
            description: 'Sequence completeness level'
          },
          upload_date_start: {
            type: 'string',
            format: 'date',
            description: 'Start date for upload/submission (YYYY-MM-DD)'
          },
          upload_date_end: {
            type: 'string',
            format: 'date',
            description: 'End date for upload/submission (YYYY-MM-DD)'
          },
          country: {
            type: 'string',
            description: 'Filter by country/geographic location'
          },
          has_geo_location: {
            type: 'boolean',
            description: 'Only include sequences with geographic location data'
          },
          quality_filter: {
            type: 'string',
            enum: ['high', 'medium', 'any'],
            default: 'any',
            description: 'Sequence quality threshold'
          },
          exclude_predicted: {
            type: 'boolean',
            default: false,
            description: 'Exclude predicted/inferred sequences'
          },
          exclude_environmental: {
            type: 'boolean',
            default: false,
            description: 'Exclude environmental/uncultured samples'
          }
        }
      }
    },
    required: ['taxon']
  }
};

async function main() {
  console.log('🧪 Testing tool-generator with filters...\n');

  const generator = new ToolFileGenerator();
  
  // Test directory
  const testOutput = './test-output';
  
  try {
    await generator.generateToolFiles('database', [testTool], testOutput);
    
    console.log('\n✅ Test completed successfully!');
    console.log('\n📁 Generated files:');
    console.log(`   - ${testOutput}/servers/database/get_sequences.ts`);
    console.log(`   - ${testOutput}/servers/database/index.ts`);
    console.log(`   - ${testOutput}/servers/database/README.md`);
    console.log('\n💡 Check the generated get_sequences.ts to see:');
    console.log('   - GetSequencesFilters interface (extracted nested object)');
    console.log('   - GetSequencesInput interface (using filters: GetSequencesFilters)');
    console.log('   - All filter properties with descriptions');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error);
    process.exit(1);
  }
}

main();

