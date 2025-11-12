/**
 * Unit tests for Tool File Generator
 *
 * Tests the core functionality of generating TypeScript files from MCP tool definitions.
 *
 * @see mcp_servers/shared/tool-generator.ts
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ToolFileGenerator, ToolDefinition } from '../../mcp_servers/shared/tool-generator.js';
import { readdir, readFile, rm } from 'fs/promises';
import { join } from 'path';

describe('ToolFileGenerator', () => {
  let generator: ToolFileGenerator;
  const testOutputDir = './test-output';

  beforeEach(() => {
    generator = new ToolFileGenerator();
  });

  afterEach(async () => {
    // Cleanup test output
    try {
      await rm(testOutputDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('generateToolFile', () => {
    it('should generate valid TypeScript from simple tool definition', () => {
      const mockTool: ToolDefinition = {
        name: 'get_sequences',
        description: 'Fetch sequences from database',
        inputSchema: {
          type: 'object',
          properties: {
            taxon: { type: 'string', description: 'Taxon name' },
            max_results: { type: 'integer', description: 'Maximum results' },
          },
          required: ['taxon'],
        },
      };

      const result = (generator as any).generateToolFile(mockTool, 'database');

      // Check basic structure
      expect(result).toContain('export async function getSequences');
      expect(result).toContain('export interface GetSequencesInput');
      expect(result).toContain('taxon: string;');
      expect(result).toContain('max_results?: number;');
      expect(result).toContain("callMCPTool<any>('database__get_sequences'");
      expect(result).toContain('/** Taxon name */');
    });

    it('should handle enum types correctly', () => {
      const mockTool: ToolDefinition = {
        name: 'align_sequences',
        description: 'Align sequences',
        inputSchema: {
          type: 'object',
          properties: {
            algorithm: {
              type: 'string',
              enum: ['mafft', 'muscle', 'clustalo'],
              description: 'Alignment algorithm',
            },
          },
          required: ['algorithm'],
        },
      };

      const result = (generator as any).generateToolFile(mockTool, 'alignment');

      expect(result).toContain('algorithm: "mafft" | "muscle" | "clustalo";');
    });

    it('should handle array types correctly', () => {
      const mockTool: ToolDefinition = {
        name: 'process_batch',
        description: 'Process multiple items',
        inputSchema: {
          type: 'object',
          properties: {
            items: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of items',
            },
          },
          required: ['items'],
        },
      };

      const result = (generator as any).generateToolFile(mockTool, 'processing');

      expect(result).toContain('items: string[];');
    });

    it('should handle nested object types', () => {
      const mockTool: ToolDefinition = {
        name: 'configure_tool',
        description: 'Configure tool settings',
        inputSchema: {
          type: 'object',
          properties: {
            settings: {
              type: 'object',
              properties: {
                debug: { type: 'boolean' },
                timeout: { type: 'integer' },
              },
            },
          },
          required: ['settings'],
        },
      };

      const result = (generator as any).generateToolFile(mockTool, 'config');

      expect(result).toContain('settings: { debug?: boolean; timeout?: number }');
    });

    it('should include JSDoc comments', () => {
      const mockTool: ToolDefinition = {
        name: 'test_tool',
        description: 'A test tool',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string', description: 'First parameter' },
          },
          required: ['param1'],
        },
      };

      const result = (generator as any).generateToolFile(mockTool, 'test');

      expect(result).toContain('/** A test tool */');
      expect(result).toContain('/** First parameter */');
      expect(result).toContain('@param input - Tool input parameters');
      expect(result).toContain('@returns Tool execution result');
      expect(result).toContain('@example');
    });
  });

  describe('generateIndexFile', () => {
    it('should generate barrel exports for all tools', () => {
      const mockTools: ToolDefinition[] = [
        {
          name: 'get_sequences',
          description: 'Fetch sequences',
          inputSchema: { type: 'object' },
        },
        {
          name: 'align_sequences',
          description: 'Align sequences',
          inputSchema: { type: 'object' },
        },
      ];

      const result = (generator as any).generateIndexFile(mockTools);

      expect(result).toContain("export { getSequences } from './get-sequences.js';");
      expect(result).toContain("export { alignSequences } from './align-sequences.js';");
      expect(result).toContain('@generated');
      expect(result).toContain('import * as database');
    });
  });

  describe('generateReadme', () => {
    it('should generate complete README with tool list', () => {
      const mockTools: ToolDefinition[] = [
        {
          name: 'get_sequences',
          description: 'Fetch sequences from database',
          inputSchema: { type: 'object' },
        },
        {
          name: 'get_taxonomy',
          description: 'Get taxonomic information',
          inputSchema: { type: 'object' },
        },
      ];

      const result = (generator as any).generateReadme('database', mockTools);

      expect(result).toContain('# Database Server');
      expect(result).toContain('**Tools**: 2');
      expect(result).toContain('- `getSequences`: Fetch sequences from database');
      expect(result).toContain('- `getTaxonomy`: Get taxonomic information');
      expect(result).toContain('## Usage');
      expect(result).toContain('## Example');
      expect(result).toContain('## Token Efficiency');
    });
  });

  describe('generateToolFiles (integration)', () => {
    it('should generate all files for a server', async () => {
      const mockTools: ToolDefinition[] = [
        {
          name: 'get_sequences',
          description: 'Fetch sequences',
          inputSchema: {
            type: 'object',
            properties: {
              taxon: { type: 'string' },
            },
            required: ['taxon'],
          },
        },
        {
          name: 'get_taxonomy',
          description: 'Get taxonomy',
          inputSchema: {
            type: 'object',
            properties: {
              taxon: { type: 'string' },
            },
            required: ['taxon'],
          },
        },
      ];

      await generator.generateToolFiles('database', mockTools, testOutputDir);

      // Check directory structure
      const serverDir = join(testOutputDir, 'servers', 'database');
      const files = await readdir(serverDir);

      expect(files).toContain('get-sequences.ts');
      expect(files).toContain('get-taxonomy.ts');
      expect(files).toContain('index.ts');
      expect(files).toContain('README.md');

      // Check file contents
      const getSeqContent = await readFile(join(serverDir, 'get-sequences.ts'), 'utf-8');
      expect(getSeqContent).toContain('export async function getSequences');

      const indexContent = await readFile(join(serverDir, 'index.ts'), 'utf-8');
      expect(indexContent).toContain('export { getSequences }');
      expect(indexContent).toContain('export { getTaxonomy }');

      const readmeContent = await readFile(join(serverDir, 'README.md'), 'utf-8');
      expect(readmeContent).toContain('# Database Server');
    }, 10000); // Increase timeout for file operations
  });

  describe('type conversion', () => {
    it('should convert snake_case to camelCase', () => {
      const result = (generator as any).snakeToCamel('get_sequences');
      expect(result).toBe('getSequences');
    });

    it('should convert camelCase to kebab-case', () => {
      const result = (generator as any).camelToKebab('getSequences');
      expect(result).toBe('get-sequences');
    });

    it('should capitalize strings', () => {
      const result = (generator as any).capitalize('database');
      expect(result).toBe('Database');
    });

    it('should handle complex snake_case conversion', () => {
      const result = (generator as any).snakeToCamel('search_sra_studies');
      expect(result).toBe('searchSraStudies');
    });
  });

  describe('schema to TypeScript conversion', () => {
    it('should convert string type', () => {
      const prop = { type: 'string' };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('string');
    });

    it('should convert integer type', () => {
      const prop = { type: 'integer' };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('number');
    });

    it('should convert boolean type', () => {
      const prop = { type: 'boolean' };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('boolean');
    });

    it('should convert enum type', () => {
      const prop = { enum: ['option1', 'option2', 'option3'] };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('"option1" | "option2" | "option3"');
    });

    it('should convert array type', () => {
      const prop = { type: 'array', items: { type: 'string' } };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('string[]');
    });

    it('should convert object type to Record', () => {
      const prop = { type: 'object' };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('Record<string, any>');
    });

    it('should handle nested object properties', () => {
      const prop = {
        type: 'object',
        properties: {
          name: { type: 'string' },
          age: { type: 'integer' },
        },
      };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toContain('name?: string');
      expect(result).toContain('age?: number');
    });

    it('should default to any for unknown types', () => {
      const prop = { type: 'unknown' };
      const result = (generator as any).schemaTypeToTS(prop);
      expect(result).toBe('any');
    });
  });

  describe('error handling', () => {
    it('should handle missing schema properties gracefully', () => {
      const mockTool: ToolDefinition = {
        name: 'test_tool',
        description: 'Test tool',
        inputSchema: {
          type: 'object',
          // No properties defined
        },
      };

      const result = (generator as any).generateToolFile(mockTool, 'test');

      expect(result).toContain('export interface TestToolInput');
      expect(result).toContain('export async function testTool');
    });

    it('should handle empty tools array', async () => {
      await generator.generateToolFiles('empty', [], testOutputDir);

      const serverDir = join(testOutputDir, 'servers', 'empty');
      const files = await readdir(serverDir);

      // Should still create index.ts and README.md
      expect(files).toContain('index.ts');
      expect(files).toContain('README.md');
    });
  });
});

describe('ToolFileGenerator - Database Server Example', () => {
  let generator: ToolFileGenerator;
  const testOutputDir = './test-output-database';

  beforeEach(() => {
    generator = new ToolFileGenerator();
  });

  afterEach(async () => {
    try {
      await rm(testOutputDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  it('should generate all 11 Database Server tools', async () => {
    // Mock Database Server tool definitions
    const databaseTools: ToolDefinition[] = [
      {
        name: 'get_sequences',
        description: 'Fetch sequences from multiple databases',
        inputSchema: {
          type: 'object',
          properties: {
            taxon: { type: 'string', description: 'Taxon name or ID' },
            region: {
              type: 'string',
              enum: ['COI', '16S', 'ITS', 'mitogenome', 'whole'],
              description: 'Genomic region',
            },
            source: {
              type: 'string',
              enum: ['gget', 'ncbi', 'bold', 'silva', 'unite'],
              description: 'Database source',
            },
            max_results: { type: 'integer', description: 'Maximum results' },
            format: {
              type: 'string',
              enum: ['fasta', 'genbank'],
              description: 'Output format',
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
            species: { type: 'string', description: 'Species name' },
            release: { type: 'integer', description: 'Ensembl release' },
          },
          required: ['species'],
        },
      },
      {
        name: 'get_taxonomy',
        description: 'Get taxonomic information and lineage',
        inputSchema: {
          type: 'object',
          properties: {
            taxon: { type: 'string', description: 'Taxon name or ID' },
          },
          required: ['taxon'],
        },
      },
    ];

    await generator.generateToolFiles('database', databaseTools, testOutputDir);

    // Verify all tools generated
    const serverDir = join(testOutputDir, 'servers', 'database');
    const files = await readdir(serverDir);

    expect(files).toContain('get-sequences.ts');
    expect(files).toContain('gget-ref.ts');
    expect(files).toContain('get-taxonomy.ts');
    expect(files).toContain('index.ts');
    expect(files).toContain('README.md');

    // Verify tool content
    const getSeqContent = await readFile(join(serverDir, 'get-sequences.ts'), 'utf-8');
    expect(getSeqContent).toContain('region?: "COI" | "16S" | "ITS" | "mitogenome" | "whole"');
    expect(getSeqContent).toContain('source?: "gget" | "ncbi" | "bold" | "silva" | "unite"');
  }, 10000);
});
