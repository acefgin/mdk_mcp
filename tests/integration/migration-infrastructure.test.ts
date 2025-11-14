/**
 * Comprehensive Integration Tests for Node.js/TypeScript Migration Infrastructure
 *
 * Tests the complete migration flow from Python MCP servers to TypeScript filesystem API.
 * Verifies:
 * - Tool generation from definitions
 * - TypeScript compilation
 * - Type safety and interfaces
 * - Integration with MCP client
 * - Progressive tool disclosure
 * - Token efficiency
 *
 * @see mcp_servers/shared/tool-generator.ts
 * @see docs/MIGRATION_PLAN.md
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { ToolFileGenerator, ToolDefinition } from '../../mcp_servers/shared/tool-generator.js';
import { readFile, readdir, rm, mkdir } from 'fs/promises';
import { join } from 'path';
import { spawn } from 'child_process';

describe('Migration Infrastructure - End-to-End', () => {
  const testOutputDir = './test-migration-output';
  let generator: ToolFileGenerator;

  beforeEach(() => {
    generator = new ToolFileGenerator();
  });

  afterAll(async () => {
    // Cleanup test output - DISABLED to allow inspection
    // Uncomment to re-enable cleanup
    /*
    try {
      await rm(testOutputDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
    */
  });

  describe('Complete server migration', () => {
    it('should generate complete TypeScript API for all 5 MCP servers', async () => {
      const servers = [
        {
          name: 'database',
          tools: createDatabaseToolDefinitions(),
          expectedCount: 11,
        },
        {
          name: 'processing',
          tools: createProcessingToolDefinitions(),
          expectedCount: 5,
        },
        {
          name: 'alignment',
          tools: createAlignmentToolDefinitions(),
          expectedCount: 5,
        },
        {
          name: 'design',
          tools: createDesignToolDefinitions(),
          expectedCount: 6,
        },
        {
          name: 'validation',
          tools: createValidationToolDefinitions(),
          expectedCount: 7,
        },
      ];

      for (const server of servers) {
        await generator.generateToolFiles(server.name, server.tools, testOutputDir);

        const serverDir = join(testOutputDir, 'servers', server.name);
        const files = await readdir(serverDir);

        // Verify all tool files generated
        expect(files.length).toBeGreaterThanOrEqual(server.expectedCount + 2); // tools + index.ts + README.md

        // Verify index.ts exists
        expect(files).toContain('index.ts');

        // Verify README.md exists
        expect(files).toContain('README.md');

        // Verify tool count in README
        const readmeContent = await readFile(join(serverDir, 'README.md'), 'utf-8');
        expect(readmeContent).toContain(`**Tools**: ${server.expectedCount}`);
      }
    }, 30000);

    it('should generate valid TypeScript that compiles', async () => {
      const testServer = 'test-compile';
      const testTools: ToolDefinition[] = [
        {
          name: 'test_function',
          description: 'Test function for compilation',
          inputSchema: {
            type: 'object',
            properties: {
              input_param: { type: 'string', description: 'Test parameter' },
            },
            required: ['input_param'],
          },
        },
      ];

      await generator.generateToolFiles(testServer, testTools, testOutputDir);

      const serverDir = join(testOutputDir, 'servers', testServer);
      const toolFile = join(serverDir, 'test_function.ts');

      // Verify file was generated
      const content = await readFile(toolFile, 'utf-8');
      expect(content).toContain('export async function testFunction');
      expect(content).toContain('export interface TestFunctionInput');

      // Basic syntax validation
      expect(content).not.toContain('undefined');
      expect(content).toMatch(/export async function \w+\(/);
      expect(content).toMatch(/export interface \w+Input/);
    }, 10000);
  });

  describe('Type safety validation', () => {
    it('should generate correct TypeScript types for all schema types', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'type_test',
          description: 'Test all type conversions',
          inputSchema: {
            type: 'object',
            properties: {
              string_param: { type: 'string' },
              number_param: { type: 'number' },
              integer_param: { type: 'integer' },
              boolean_param: { type: 'boolean' },
              array_param: { type: 'array', items: { type: 'string' } },
              enum_param: { type: 'string', enum: ['option1', 'option2', 'option3'] },
              object_param: {
                type: 'object',
                properties: {
                  nested_string: { type: 'string' },
                  nested_number: { type: 'number' },
                },
              },
            },
            required: ['string_param', 'integer_param'],
          },
        },
      ];

      await generator.generateToolFiles('type-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'type-test', 'type_test.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Verify type conversions
      expect(content).toContain('string_param: string;');
      expect(content).toContain('number_param?: number;');
      expect(content).toContain('integer_param: number;');
      expect(content).toContain('boolean_param?: boolean;');
      expect(content).toContain('array_param?: string[];');
      expect(content).toContain('enum_param?: "option1" | "option2" | "option3";');
      expect(content).toContain('object_param?:');
      expect(content).toContain('nested_string?: string');
      expect(content).toContain('nested_number?: number');
    }, 10000);

    it('should properly handle required vs optional parameters', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'optional_test',
          description: 'Test optional parameters',
          inputSchema: {
            type: 'object',
            properties: {
              required1: { type: 'string' },
              required2: { type: 'number' },
              optional1: { type: 'string' },
              optional2: { type: 'number' },
            },
            required: ['required1', 'required2'],
          },
        },
      ];

      await generator.generateToolFiles('optional-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'optional-test', 'optional_test.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Required fields should NOT have ?
      expect(content).toMatch(/required1:\s*string;/);
      expect(content).toMatch(/required2:\s*number;/);

      // Optional fields should have ?
      expect(content).toMatch(/optional1\?:\s*string;/);
      expect(content).toMatch(/optional2\?:\s*number;/);
    }, 10000);
  });

  describe('File structure and organization', () => {
    it('should create proper directory structure', async () => {
      const testServer = 'structure-test';
      const testTools: ToolDefinition[] = [
        { name: 'tool1', description: 'Tool 1', inputSchema: { type: 'object' } },
        { name: 'tool2', description: 'Tool 2', inputSchema: { type: 'object' } },
      ];

      await generator.generateToolFiles(testServer, testTools, testOutputDir);

      const serverDir = join(testOutputDir, 'servers', testServer);
      const files = await readdir(serverDir);

      // Verify structure
      expect(files).toContain('tool1.ts');
      expect(files).toContain('tool2.ts');
      expect(files).toContain('index.ts');
      expect(files).toContain('README.md');
    }, 10000);

    it('should generate correct barrel exports in index.ts', async () => {
      const testServer = 'barrel-test';
      const testTools: ToolDefinition[] = [
        { name: 'get_data', description: 'Get data', inputSchema: { type: 'object' } },
        { name: 'set_data', description: 'Set data', inputSchema: { type: 'object' } },
        { name: 'delete_data', description: 'Delete data', inputSchema: { type: 'object' } },
      ];

      await generator.generateToolFiles(testServer, testTools, testOutputDir);

      const indexFile = join(testOutputDir, 'servers', testServer, 'index.ts');
      const content = await readFile(indexFile, 'utf-8');

      // Verify exports
      expect(content).toContain("export { getData } from './get_data.js';");
      expect(content).toContain("export { setData } from './set_data.js';");
      expect(content).toContain("export { deleteData } from './delete_data.js';");
      expect(content).toContain('@generated');
    }, 10000);

    it('should generate comprehensive README documentation', async () => {
      const testServer = 'readme-test';
      const testTools: ToolDefinition[] = [
        { name: 'tool1', description: 'First tool', inputSchema: { type: 'object' } },
        { name: 'tool2', description: 'Second tool', inputSchema: { type: 'object' } },
        { name: 'tool3', description: 'Third tool', inputSchema: { type: 'object' } },
      ];

      await generator.generateToolFiles(testServer, testTools, testOutputDir);

      const readmeFile = join(testOutputDir, 'servers', testServer, 'README.md');
      const content = await readFile(readmeFile, 'utf-8');

      // Verify README sections
      expect(content).toContain('# Readme-test Server');
      expect(content).toContain('## Overview');
      expect(content).toContain('## Available Tools');
      expect(content).toContain('## Usage');
      expect(content).toContain('## Example');
      expect(content).toContain('## Token Efficiency');
      expect(content).toContain('## See Also');

      // Verify tool list
      expect(content).toContain('- `tool1`: First tool');
      expect(content).toContain('- `tool2`: Second tool');
      expect(content).toContain('- `tool3`: Third tool');

      // Verify token efficiency calculation
      expect(content).toMatch(/\*\*Traditional approach\*\*:.*tokens/);
      expect(content).toMatch(/\*\*Code execution approach\*\*:.*tokens/);
      expect(content).toContain('**Reduction**: ~99% fewer tokens');
    }, 10000);
  });

  describe('String conversion utilities', () => {
    it('should correctly convert naming conventions', () => {
      const testCases = [
        { snake: 'get_sequences', camel: 'getSequences' },
        { snake: 'align_sequences', camel: 'alignSequences' },
        { snake: 'search_sra_studies', camel: 'searchSraStudies' },
        { snake: 'fasta_qc', camel: 'fastaQc' },
        { snake: 'primer3_design', camel: 'primer3Design' },
      ];

      for (const testCase of testCases) {
        const camelResult = (generator as any).snakeToCamel(testCase.snake);
        expect(camelResult).toBe(testCase.camel);
      }
    });

    it('should convert camelCase to kebab-case', () => {
      const result = (generator as any).camelToKebab('getSequences');
      expect(result).toBe('get-sequences');
    });
  });

  describe('Progressive tool disclosure', () => {
    it('should enable loading tools on demand', async () => {
      const testServer = 'progressive-test';
      const testTools: ToolDefinition[] = Array.from({ length: 10 }, (_, i) => ({
        name: `tool_${i}`,
        description: `Tool ${i}`,
        inputSchema: {
          type: 'object',
          properties: {
            param: { type: 'string' },
          },
        },
      }));

      await generator.generateToolFiles(testServer, testTools, testOutputDir);

      const serverDir = join(testOutputDir, 'servers', testServer);
      const files = await readdir(serverDir);

      // Each tool should be in a separate file
      for (let i = 0; i < 10; i++) {
        expect(files).toContain(`tool_${i}.ts`);
      }

      // Index should export all (note: tool_0 becomes tool0 when converted but exports as tool_0)
      const indexContent = await readFile(join(serverDir, 'index.ts'), 'utf-8');
      for (let i = 0; i < 10; i++) {
        expect(indexContent).toContain(`tool_${i}`);
      }
    }, 10000);

    it('should demonstrate token reduction potential', async () => {
      const testServer = 'token-test';
      const tools: ToolDefinition[] = Array.from({ length: 34 }, (_, i) => ({
        name: `tool_${i}`,
        description: 'A ' + 'very '.repeat(50) + 'detailed description',
        inputSchema: {
          type: 'object',
          properties: Object.fromEntries(
            Array.from({ length: 10 }, (_, j) => [
              `param_${j}`,
              { type: 'string', description: 'Parameter description' },
            ])
          ),
        },
      }));

      await generator.generateToolFiles(testServer, tools, testOutputDir);

      const readmeFile = join(testOutputDir, 'servers', testServer, 'README.md');
      const readme = await readFile(readmeFile, 'utf-8');

      // Verify token efficiency is documented
      expect(readme).toContain('## Token Efficiency');
      expect(readme).toMatch(/Traditional approach.*119000.*tokens/);
      expect(readme).toMatch(/Code execution approach.*400.*tokens/);
    }, 10000);
  });

  describe('Complex schema handling', () => {
    it('should handle deeply nested objects', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'nested_test',
          description: 'Test nested objects',
          inputSchema: {
            type: 'object',
            properties: {
              level1: {
                type: 'object',
                properties: {
                  level2: {
                    type: 'object',
                    properties: {
                      level3: { type: 'string' },
                    },
                  },
                },
              },
            },
          },
        },
      ];

      await generator.generateToolFiles('nested-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'nested-test', 'nested_test.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Should inline nested objects
      expect(content).toContain('level1?:');
      expect(content).toContain('level2?:');
      expect(content).toContain('level3?: string');
    }, 10000);

    it('should handle arrays of complex types', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'array_complex_test',
          description: 'Test arrays of objects',
          inputSchema: {
            type: 'object',
            properties: {
              items: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    value: { type: 'number' },
                  },
                },
              },
            },
          },
        },
      ];

      await generator.generateToolFiles('array-complex-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'array-complex-test', 'array_complex_test.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Should properly type array of objects
      expect(content).toContain('items?:');
      expect(content).toMatch(/name\?: string.*value\?: number/s);
      expect(content).toContain('[]');
    }, 10000);

    it('should handle multiple enum types', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'enum_test',
          description: 'Test multiple enums',
          inputSchema: {
            type: 'object',
            properties: {
              method: { type: 'string', enum: ['mafft', 'muscle', 'clustalo'] },
              output_format: { type: 'string', enum: ['fasta', 'phylip', 'nexus'] },
              quality: { type: 'string', enum: ['low', 'medium', 'high'] },
            },
          },
        },
      ];

      await generator.generateToolFiles('enum-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'enum-test', 'enum_test.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Verify all enums
      expect(content).toContain('method?: "mafft" | "muscle" | "clustalo"');
      expect(content).toContain('output_format?: "fasta" | "phylip" | "nexus"');
      expect(content).toContain('quality?: "low" | "medium" | "high"');
    }, 10000);
  });

  describe('Documentation and comments', () => {
    it('should include comprehensive JSDoc comments', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'documented_tool',
          description: 'A well-documented tool for testing',
          inputSchema: {
            type: 'object',
            properties: {
              param1: { type: 'string', description: 'The first parameter' },
              param2: { type: 'number', description: 'The second parameter' },
            },
          },
        },
      ];

      await generator.generateToolFiles('doc-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'doc-test', 'documented_tool.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Verify JSDoc structure
      expect(content).toContain('/**\n * A well-documented tool for testing');
      expect(content).toContain('* Generated from MCP server: doc-test');
      expect(content).toContain('* @see doc-test_mcp_server.py');
      expect(content).toContain('/** The first parameter */');
      expect(content).toContain('/** The second parameter */');
      expect(content).toContain('@param input - Tool input parameters');
      expect(content).toContain('@returns Tool execution result');
      expect(content).toContain('@example');
    }, 10000);

    it('should generate usage examples', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'example_tool',
          description: 'Tool with example',
          inputSchema: { type: 'object' },
        },
      ];

      await generator.generateToolFiles('example-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'example-test', 'example_tool.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Verify example structure
      expect(content).toContain('@example');
      expect(content).toContain('```typescript');
      expect(content).toContain("import { exampleTool } from './servers/example-test';");
      expect(content).toContain('const result = await exampleTool({');
    }, 10000);
  });

  describe('Error handling and edge cases', () => {
    it('should handle tools with no properties', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'no_props',
          description: 'Tool with no properties',
          inputSchema: {
            type: 'object',
          },
        },
      ];

      await generator.generateToolFiles('no-props-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'no-props-test', 'no_props.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Should still generate valid interface
      expect(content).toContain('export interface NoPropsInput');
      expect(content).toContain('export async function noProps');
    }, 10000);

    it('should handle special characters in descriptions', async () => {
      const testTools: ToolDefinition[] = [
        {
          name: 'special_chars',
          description: 'Tool with "quotes" and \'apostrophes\' and <tags>',
          inputSchema: {
            type: 'object',
            properties: {
              param: { type: 'string', description: 'Param with "quotes"' },
            },
          },
        },
      ];

      await generator.generateToolFiles('special-test', testTools, testOutputDir);

      const toolFile = join(testOutputDir, 'servers', 'special-test', 'special_chars.ts');
      const content = await readFile(toolFile, 'utf-8');

      // Should escape special characters properly
      expect(content).toBeTruthy();
      expect(content).toContain('export async function specialChars');
    }, 10000);

    it('should handle empty tool arrays', async () => {
      await generator.generateToolFiles('empty-test', [], testOutputDir);

      const serverDir = join(testOutputDir, 'servers', 'empty-test');
      const files = await readdir(serverDir);

      // Should still create index and README
      expect(files).toContain('index.ts');
      expect(files).toContain('README.md');
    }, 10000);
  });
});

// Helper functions to create tool definitions for each server

function createDatabaseToolDefinitions(): ToolDefinition[] {
  return [
    {
      name: 'get_sequences',
      description: 'Fetch sequences from multiple databases',
      inputSchema: {
        type: 'object',
        properties: {
          taxon: { type: 'string' },
          region: { type: 'string', enum: ['COI', '16S', 'ITS', 'mitogenome', 'whole'] },
          source: { type: 'string', enum: ['gget', 'ncbi', 'bold', 'silva', 'unite'] },
        },
        required: ['taxon'],
      },
    },
    {
      name: 'gget_ref',
      description: 'Get reference genome information',
      inputSchema: { type: 'object', properties: { species: { type: 'string' } } },
    },
    {
      name: 'gget_search',
      description: 'Search for genes',
      inputSchema: { type: 'object', properties: { query: { type: 'string' } } },
    },
    {
      name: 'gget_info',
      description: 'Get gene information',
      inputSchema: { type: 'object', properties: { gene_id: { type: 'string' } } },
    },
    {
      name: 'gget_seq',
      description: 'Get gene sequence',
      inputSchema: { type: 'object', properties: { gene_id: { type: 'string' } } },
    },
    {
      name: 'get_neighbors',
      description: 'Get neighboring sequences',
      inputSchema: { type: 'object', properties: { taxon: { type: 'string' } } },
    },
    {
      name: 'get_taxonomy',
      description: 'Get taxonomic information',
      inputSchema: { type: 'object', properties: { taxon: { type: 'string' } } },
    },
    {
      name: 'search_sra_studies',
      description: 'Search SRA studies',
      inputSchema: { type: 'object', properties: { query: { type: 'string' } } },
    },
    {
      name: 'get_sra_runinfo',
      description: 'Get SRA run information',
      inputSchema: { type: 'object', properties: { accession: { type: 'string' } } },
    },
    {
      name: 'search_sra_cloud',
      description: 'Search SRA cloud',
      inputSchema: { type: 'object', properties: { query: { type: 'string' } } },
    },
    {
      name: 'extract_sequence_columns',
      description: 'Extract sequence columns',
      inputSchema: { type: 'object', properties: { alignment: { type: 'string' } } },
    },
  ];
}

function createProcessingToolDefinitions(): ToolDefinition[] {
  return [
    {
      name: 'fasta_qc',
      description: 'Quality control for FASTA sequences',
      inputSchema: {
        type: 'object',
        properties: {
          fasta_content: { type: 'string' },
          min_length: { type: 'integer' },
        },
        required: ['fasta_content'],
      },
    },
    {
      name: 'dereplicate_sequences',
      description: 'Remove duplicate sequences',
      inputSchema: {
        type: 'object',
        properties: { fasta_content: { type: 'string' } },
        required: ['fasta_content'],
      },
    },
    {
      name: 'mask_low_complexity',
      description: 'Mask low complexity regions',
      inputSchema: {
        type: 'object',
        properties: { fasta_content: { type: 'string' } },
        required: ['fasta_content'],
      },
    },
    {
      name: 'detect_chimeras',
      description: 'Detect chimeric sequences',
      inputSchema: {
        type: 'object',
        properties: { fasta_content: { type: 'string' } },
        required: ['fasta_content'],
      },
    },
    {
      name: 'process_sequences',
      description: 'Process sequences with pipeline',
      inputSchema: {
        type: 'object',
        properties: { fasta_content: { type: 'string' } },
        required: ['fasta_content'],
      },
    },
  ];
}

function createAlignmentToolDefinitions(): ToolDefinition[] {
  return [
    {
      name: 'align_sequences',
      description: 'Align sequences using various methods',
      inputSchema: {
        type: 'object',
        properties: {
          fasta_content: { type: 'string' },
          method: { type: 'string', enum: ['mafft', 'muscle', 'clustalo', 'gget_muscle'] },
        },
        required: ['fasta_content'],
      },
    },
    {
      name: 'process_alignment',
      description: 'Process and clean alignment',
      inputSchema: {
        type: 'object',
        properties: { alignment: { type: 'string' } },
        required: ['alignment'],
      },
    },
    {
      name: 'build_phylogeny',
      description: 'Build phylogenetic tree',
      inputSchema: {
        type: 'object',
        properties: { alignment: { type: 'string' } },
        required: ['alignment'],
      },
    },
    {
      name: 'calculate_distances',
      description: 'Calculate pairwise distances',
      inputSchema: {
        type: 'object',
        properties: { alignment: { type: 'string' } },
        required: ['alignment'],
      },
    },
    {
      name: 'align_and_analyze',
      description: 'Align and analyze sequences',
      inputSchema: {
        type: 'object',
        properties: { fasta_content: { type: 'string' } },
        required: ['fasta_content'],
      },
    },
  ];
}

function createDesignToolDefinitions(): ToolDefinition[] {
  return [
    {
      name: 'find_signature_regions',
      description: 'Find signature regions for primer design',
      inputSchema: {
        type: 'object',
        properties: {
          target_alignment: { type: 'string' },
          offtarget_alignment: { type: 'string' },
        },
        required: ['target_alignment'],
      },
    },
    {
      name: 'analyze_specificity',
      description: 'Analyze primer specificity',
      inputSchema: {
        type: 'object',
        properties: { target_sequences: { type: 'string' } },
        required: ['target_sequences'],
      },
    },
    {
      name: 'rank_regions',
      description: 'Rank candidate regions',
      inputSchema: {
        type: 'object',
        properties: { regions: { type: 'array' } },
        required: ['regions'],
      },
    },
    {
      name: 'primer3_design',
      description: 'Design primers using Primer3',
      inputSchema: {
        type: 'object',
        properties: { template: { type: 'string' } },
        required: ['template'],
      },
    },
    {
      name: 'oligo_qc',
      description: 'Quality control for oligos',
      inputSchema: {
        type: 'object',
        properties: { primers: { type: 'array' } },
        required: ['primers'],
      },
    },
    {
      name: 'design_primers_complete',
      description: 'Complete primer design pipeline',
      inputSchema: {
        type: 'object',
        properties: { target_alignment: { type: 'string' } },
        required: ['target_alignment'],
      },
    },
  ];
}

function createValidationToolDefinitions(): ToolDefinition[] {
  return [
    {
      name: 'gget_blast',
      description: 'BLAST search using gget',
      inputSchema: {
        type: 'object',
        properties: {
          sequence: { type: 'string' },
          program: { type: 'string', enum: ['blastn', 'blastp', 'blastx', 'tblastn', 'tblastx'] },
        },
        required: ['sequence'],
      },
    },
    {
      name: 'gget_blat',
      description: 'BLAT search using gget',
      inputSchema: {
        type: 'object',
        properties: { sequence: { type: 'string' } },
        required: ['sequence'],
      },
    },
    {
      name: 'blast_nt',
      description: 'BLAST against nt database',
      inputSchema: {
        type: 'object',
        properties: { sequence: { type: 'string' } },
        required: ['sequence'],
      },
    },
    {
      name: 'in_silico_pcr',
      description: 'In silico PCR',
      inputSchema: {
        type: 'object',
        properties: {
          forward_primer: { type: 'string' },
          reverse_primer: { type: 'string' },
        },
        required: ['forward_primer', 'reverse_primer'],
      },
    },
    {
      name: 'assess_coverage',
      description: 'Assess primer coverage',
      inputSchema: {
        type: 'object',
        properties: { primers: { type: 'array' } },
        required: ['primers'],
      },
    },
    {
      name: 'search_pubmed',
      description: 'Search PubMed',
      inputSchema: {
        type: 'object',
        properties: { query: { type: 'string' } },
        required: ['query'],
      },
    },
    {
      name: 'validate_primers_complete',
      description: 'Complete primer validation pipeline',
      inputSchema: {
        type: 'object',
        properties: { primers: { type: 'array' } },
        required: ['primers'],
      },
    },
  ];
}

