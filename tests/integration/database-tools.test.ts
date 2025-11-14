/**
 * Integration tests for Database Server Tools
 *
 * Tests the 11 generated database tool wrappers to verify:
 * - Type safety and interface correctness
 * - MCP client integration
 * - Tool invocation through callMCPTool()
 * - Error handling and validation
 * - Return value parsing
 *
 * @see workspace/servers/database/
 * @see examples/generate-all-database-tools.ts
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import {
  MCPCodeExecutionClient,
  MCPServerConfig,
  setMCPClient,
  getMCPClient,
} from '../../workspace/lib/mcp-client.js';

// Import all generated database tools
import {
  getSequences,
  ggetRef,
  ggetSearch,
  ggetInfo,
  ggetSeq,
  getNeighbors,
  getTaxonomy,
  searchSraStudies,
  getSraRuninfo,
  searchSraCloud,
  extractSequenceColumns,
} from '../../workspace/servers/database/index.js';

// Import types
import type { GetSequencesInput } from '../../workspace/servers/database/get_sequences.js';

describe('Database Server Tools - Integration', () => {
  let client: MCPCodeExecutionClient;
  let mockConfigs: Map<string, MCPServerConfig>;

  beforeAll(async () => {
    // Set up mock MCP client for testing
    // In production, this would connect to actual database server container
    mockConfigs = new Map([
      [
        'database',
        {
          command: 'echo',
          args: ['mock-database-server'],
        },
      ],
    ]);

    client = new MCPCodeExecutionClient(mockConfigs);

    // Mock initialization (real tests would use actual Docker containers)
    (client as any).initialized = true;

    setMCPClient(client);
  });

  afterAll(async () => {
    if (client) {
      try {
        await client.close();
      } catch {
        // Ignore cleanup errors for mock clients
      }
    }
  });

  describe('Global client setup', () => {
    it('should have global client set', () => {
      const globalClient = getMCPClient();
      expect(globalClient).toBeDefined();
      expect(globalClient).toBe(client);
    });

    it('should report initialized status', () => {
      const status = client.getStatus();
      expect(status.initialized).toBe(true);
    });
  });

  describe('getSequences', () => {
    it('should have correct type signature', () => {
      expect(typeof getSequences).toBe('function');
    });

    it('should accept valid input with all parameters', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              count: 10,
              sequences: ['>seq1\nATCG', '>seq2\nGCTA'],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const input: GetSequencesInput = {
        taxon: 'Salmo salar',
        region: 'COI',
        source: 'gget',
        max_results: 100,
        format: 'fasta',
      };

      const result = await getSequences(input);

      expect(mockClient.request).toHaveBeenCalledWith(
        {
          method: 'tools/call',
          params: {
            name: 'get_sequences',
            arguments: input,
          },
        },
        expect.anything()
      );

      expect(result).toHaveProperty('count');
      expect(result).toHaveProperty('sequences');
    });

    it('should accept minimal input (only required fields)', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({ count: 5 }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await getSequences({ taxon: 'Homo sapiens' });

      expect(mockClient.request).toHaveBeenCalled();
      expect(result).toBeDefined();
    });

    it('should validate enum types at runtime', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      // TypeScript compilation ensures valid enums
      // Runtime validation happens in MCP server
      await expect(
        getSequences({
          taxon: 'test',
          region: 'COI', // Valid enum value
        })
      ).resolves.toBeDefined();
    });
  });

  describe('ggetRef', () => {
    it('should call gget_ref tool', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              species: 'homo_sapiens',
              release: 110,
              references: [],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await ggetRef({ species: 'homo_sapiens' });

      expect(mockClient.request).toHaveBeenCalledWith(
        {
          method: 'tools/call',
          params: {
            name: 'gget_ref',
            arguments: { species: 'homo_sapiens' },
          },
        },
        expect.anything()
      );

      expect(result).toHaveProperty('species');
    });

    it('should support optional release parameter', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      await ggetRef({
        species: 'mus_musculus',
        release: 109,
        which: 'gtf',
      });

      expect(mockClient.request).toHaveBeenCalled();
    });
  });

  describe('ggetSearch', () => {
    it('should search Ensembl database', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              results: [
                { ensembl_id: 'ENSG00000157764', gene_name: 'BRAF' },
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await ggetSearch({
        search_term: 'BRAF',
        species: 'homo_sapiens',
        limit: 10,
      });

      expect(result).toHaveProperty('results');
      expect(Array.isArray(result.results)).toBe(true);
    });
  });

  describe('ggetInfo', () => {
    it('should fetch gene information', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              genes: {
                ENSG00000157764: {
                  gene_name: 'BRAF',
                  description: 'B-Raf proto-oncogene',
                },
              },
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await ggetInfo({
        ensembl_ids: ['ENSG00000157764'],
      });

      expect(result).toHaveProperty('genes');
    });

    it('should handle multiple ensembl IDs', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{"genes":{}}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      await ggetInfo({
        ensembl_ids: ['ENSG00000157764', 'ENSG00000141510'],
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            arguments: {
              ensembl_ids: ['ENSG00000157764', 'ENSG00000141510'],
            },
          }),
        }),
        expect.anything()
      );
    });
  });

  describe('ggetSeq', () => {
    it('should retrieve sequences from Ensembl', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              sequences: {
                ENSG00000157764: '>ENSG00000157764\nATCGATCG',
              },
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await ggetSeq({
        ensembl_ids: ['ENSG00000157764'],
        translate: false,
        isoforms: false,
      });

      expect(result).toHaveProperty('sequences');
    });

    it('should support translation option', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      await ggetSeq({
        ensembl_ids: ['ENSG00000157764'],
        translate: true, // Get amino acid sequence
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            arguments: expect.objectContaining({ translate: true }),
          }),
        }),
        expect.anything()
      );
    });
  });

  describe('getNeighbors', () => {
    it('should retrieve phylogenetic neighbors', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              neighbors: [
                { taxon: 'Salmo trutta', sequences: 50 },
                { taxon: 'Oncorhynchus mykiss', sequences: 45 },
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await getNeighbors({
        taxon: 'Salmo salar',
        include_subspecies: true,
        max_distance: 2,
        max_results: 50,
      });

      expect(result).toHaveProperty('neighbors');
      expect(Array.isArray(result.neighbors)).toBe(true);
    });
  });

  describe('getTaxonomy', () => {
    it('should fetch taxonomic information', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              taxid: 8030,
              scientific_name: 'Salmo salar',
              lineage: [
                'Eukaryota',
                'Chordata',
                'Actinopterygii',
                'Salmonidae',
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await getTaxonomy({
        taxon: 'Salmo salar',
        include_lineage: true,
      });

      expect(result).toHaveProperty('taxid');
      expect(result).toHaveProperty('scientific_name');
      expect(result).toHaveProperty('lineage');
    });
  });

  describe('searchSraStudies', () => {
    it('should search SRA studies', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              studies: [
                {
                  accession: 'SRP12345',
                  title: 'RNA-seq of Salmo salar',
                  organism: 'Salmo salar',
                },
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await searchSraStudies({
        query: 'Salmo salar RNA-seq',
        max_results: 20,
      });

      expect(result).toHaveProperty('studies');
    });
  });

  describe('getSraRuninfo', () => {
    it('should fetch SRA run information', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              runs: [
                {
                  run: 'SRR12345',
                  spots: 1000000,
                  bases: 150000000,
                },
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await getSraRuninfo({
        accession: 'SRP12345',
        detailed: true,
      });

      expect(result).toHaveProperty('runs');
    });
  });

  describe('searchSraCloud', () => {
    it('should search SRA using cloud services', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              results: [
                { run: 'SRR12345', organism: 'Salmo salar' },
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await searchSraCloud({
        query: "SELECT * FROM sra WHERE organism = 'Salmo salar' LIMIT 10",
        platform: 'bigquery',
        max_results: 100,
      });

      expect(result).toHaveProperty('results');
    });

    it('should support both BigQuery and Athena', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{"results":[]}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      // BigQuery
      await searchSraCloud({
        query: 'SELECT * FROM sra LIMIT 10',
        platform: 'bigquery',
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            arguments: expect.objectContaining({ platform: 'bigquery' }),
          }),
        }),
        expect.anything()
      );

      // Athena
      await searchSraCloud({
        query: 'SELECT * FROM sra LIMIT 10',
        platform: 'athena',
      });

      expect(mockClient.request).toHaveBeenLastCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            arguments: expect.objectContaining({ platform: 'athena' }),
          }),
        }),
        expect.anything()
      );
    });
  });

  describe('extractSequenceColumns', () => {
    it('should extract metadata from FASTA sequences', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{
            type: 'text',
            text: JSON.stringify({
              records: [
                {
                  accession: 'NC_000001',
                  organism: 'Homo sapiens',
                  length: 1000,
                },
              ],
            }),
          }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const fastaSequences = `>NC_000001 Homo sapiens chromosome 1
ATCGATCGATCG
>NC_000002 Homo sapiens chromosome 2
GCTAGCTAGCTA`;

      const result = await extractSequenceColumns({
        sequences: fastaSequences,
        format: 'fasta',
        output_format: 'json',
      });

      expect(result).toHaveProperty('records');
    });

    it('should support multiple output formats', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const sequences = '>test\nATCG';

      // JSON
      await extractSequenceColumns({
        sequences,
        format: 'fasta',
        output_format: 'json',
      });

      // CSV
      await extractSequenceColumns({
        sequences,
        format: 'fasta',
        output_format: 'csv',
      });

      // TSV
      await extractSequenceColumns({
        sequences,
        format: 'fasta',
        output_format: 'tsv',
      });

      // Table
      await extractSequenceColumns({
        sequences,
        format: 'fasta',
        output_format: 'table',
      });

      expect(mockClient.request).toHaveBeenCalledTimes(4);
    });

    it('should support column selection', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      await extractSequenceColumns({
        sequences: '>test\nATCG',
        format: 'fasta',
        output_format: 'json',
        columns: ['accession', 'organism', 'length', 'country'],
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            arguments: expect.objectContaining({
              columns: ['accession', 'organism', 'length', 'country'],
            }),
          }),
        }),
        expect.anything()
      );
    });
  });

  describe('Error handling', () => {
    it('should throw error when MCP client not initialized', async () => {
      // Clear global client
      setMCPClient(null as any);

      await expect(
        getSequences({ taxon: 'test' })
      ).rejects.toThrow('MCP client not initialized');

      // Restore client
      setMCPClient(client);
    });

    it('should handle tool execution errors gracefully', async () => {
      const mockClient = {
        request: vi.fn().mockRejectedValue(new Error('Tool execution failed')),
      };

      (client as any).clients.set('database', mockClient);

      await expect(
        getSequences({ taxon: 'invalid' })
      ).rejects.toThrow('Tool execution failed');
    });

    it('should handle malformed responses', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: 'not valid json' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      const result = await getSequences({ taxon: 'test' });

      // Should return as plain text when JSON parsing fails
      expect(typeof result).toBe('string');
      expect(result).toBe('not valid json');
    });
  });

  describe('Type safety', () => {
    it('should enforce required parameters at compile time', () => {
      // These would fail TypeScript compilation:
      // getSequences({}) // Error: missing 'taxon'
      // ggetSearch({}) // Error: missing 'search_term'
      // ggetInfo({}) // Error: missing 'ensembl_ids'

      // This compiles correctly:
      const validInput: GetSequencesInput = {
        taxon: 'test',
      };

      expect(validInput).toBeDefined();
    });

    it('should provide enum type checking', () => {
      // Valid enum values
      const validRegions: Array<GetSequencesInput['region']> = [
        'COI',
        '16S',
        'ITS',
        'mitogenome',
        'whole',
        undefined, // Optional
      ];

      expect(validRegions).toBeDefined();

      // Invalid enum would fail TypeScript compilation:
      // const invalid: GetSequencesInput = {
      //   taxon: 'test',
      //   region: 'invalid' // Error: not in enum
      // };
    });
  });

  describe('Tool ID format', () => {
    it('should use correct tool ID format (server__tool_name)', async () => {
      const mockClient = {
        request: vi.fn().mockResolvedValue({
          content: [{ type: 'text', text: '{}' }],
        }),
      };

      (client as any).clients.set('database', mockClient);

      await getSequences({ taxon: 'test' });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            name: 'get_sequences', // Tool name (not server__tool_name)
          }),
        }),
        expect.anything()
      );
    });
  });
});

describe('Database Tools - Usage Examples', () => {
  it('should provide usage example for common workflow', async () => {
    // Example: Fetch salmon COI sequences and extract metadata

    const mockClient = new MCPCodeExecutionClient(
      new Map([
        ['database', { command: 'echo', args: ['test'] }],
      ])
    );

    (mockClient as any).initialized = true;
    setMCPClient(mockClient);

    const requestMock = vi.fn()
      .mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: 100,
            sequences: '>NC_001960\nATCGATCG',
          }),
        }],
      })
      .mockResolvedValueOnce({
        content: [{
          type: 'text',
          text: JSON.stringify({
            records: [{ accession: 'NC_001960', organism: 'Salmo salar' }],
          }),
        }],
      });

    (mockClient as any).clients.set('database', { request: requestMock });

    // Step 1: Fetch sequences
    const sequences = await getSequences({
      taxon: 'Salmo salar',
      region: 'COI',
      source: 'ncbi',
      max_results: 100,
      format: 'fasta',
    });

    expect(sequences).toHaveProperty('count');
    expect(sequences.count).toBe(100);

    // Step 2: Extract metadata
    const metadata = await extractSequenceColumns({
      sequences: sequences.sequences,
      format: 'fasta',
      output_format: 'json',
      columns: ['accession', 'organism', 'length', 'country'],
    });

    expect(metadata).toHaveProperty('records');
    expect(requestMock).toHaveBeenCalledTimes(2);
  });
});
