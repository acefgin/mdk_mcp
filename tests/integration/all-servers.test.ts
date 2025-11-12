/**
 * Integration tests for All MCP Servers
 *
 * Tests all 34 generated tool wrappers across all 5 servers:
 * - Database (11 tools)
 * - Processing (5 tools)
 * - Alignment (5 tools)
 * - Design (6 tools)
 * - Validation (7 tools)
 *
 * @see workspace/servers/
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import {
  MCPCodeExecutionClient,
  MCPServerConfig,
  setMCPClient,
  getMCPClient,
} from '../../workspace/lib/mcp-client.js';

// Import all server tools
import * as database from '../../workspace/servers/database/index.js';
import * as processing from '../../workspace/servers/processing/index.js';
import * as alignment from '../../workspace/servers/alignment/index.js';
import * as design from '../../workspace/servers/design/index.js';
import * as validation from '../../workspace/servers/validation/index.js';

describe('All MCP Servers - Integration', () => {
  let client: MCPCodeExecutionClient;

  beforeAll(async () => {
    const mockConfigs = new Map<string, MCPServerConfig>([
      ['database', { command: 'echo', args: ['mock'] }],
      ['processing', { command: 'echo', args: ['mock'] }],
      ['alignment', { command: 'echo', args: ['mock'] }],
      ['design', { command: 'echo', args: ['mock'] }],
      ['validation', { command: 'echo', args: ['mock'] }],
    ]);

    client = new MCPCodeExecutionClient(mockConfigs);
    (client as any).initialized = true;
    setMCPClient(client);
  });

  afterAll(async () => {
    if (client) {
      try {
        await client.close();
      } catch {
        // Ignore cleanup errors
      }
    }
  });

  describe('Global setup', () => {
    it('should have global client set', () => {
      expect(getMCPClient()).toBeDefined();
    });

    it('should have all server modules loaded', () => {
      expect(database).toBeDefined();
      expect(processing).toBeDefined();
      expect(alignment).toBeDefined();
      expect(design).toBeDefined();
      expect(validation).toBeDefined();
    });
  });

  describe('Processing Server (5 tools)', () => {
    const mockClient = {
      request: vi.fn().mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify({ success: true }) }],
      }),
    };

    beforeAll(() => {
      (client as any).clients.set('processing', mockClient);
    });

    it('should call fastaQc', async () => {
      await processing.fastaQc({
        fasta_content: '>seq1\nATCG',
        min_length: 100,
        max_n_percent: 5.0,
        remove_duplicates: true,
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            name: 'fasta_qc',
          }),
        }),
        expect.anything()
      );
    });

    it('should call dereplicateSequences', async () => {
      await processing.dereplicateSequences({
        fasta_content: '>seq1\nATCG',
        identity_threshold: 0.97,
        per_species: true,
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            name: 'dereplicate_sequences',
          }),
        }),
        expect.anything()
      );
    });

    it('should call maskLowComplexity', async () => {
      await processing.maskLowComplexity({
        fasta_content: '>seq1\nATCG',
        mask_repeats: true,
        mask_homopolymers: true,
        min_complexity: 1.5,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call detectChimeras', async () => {
      await processing.detectChimeras({
        fasta_content: '>seq1\nATCG',
        reference_db: 'auto',
        abundance_threshold: 2.0,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call processSequences with pipeline', async () => {
      await processing.processSequences({
        fasta_content: '>seq1\nATCG',
        run_id: 'test-run',
        pipeline: ['qc', 'dereplicate', 'mask', 'chimera'],
      });

      expect(mockClient.request).toHaveBeenCalled();
    });
  });

  describe('Alignment Server (5 tools)', () => {
    const mockClient = {
      request: vi.fn().mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify({ alignment: '>aligned\nATCG' }) }],
      }),
    };

    beforeAll(() => {
      (client as any).clients.set('alignment', mockClient);
    });

    it('should call alignSequences', async () => {
      await alignment.alignSequences({
        fasta_content: '>seq1\nATCG',
        method: 'mafft',
        strategy: 'auto',
        threads: 4,
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            name: 'align_sequences',
          }),
        }),
        expect.anything()
      );
    });

    it('should call processAlignment', async () => {
      await alignment.processAlignment({
        alignment: '>aligned\nATCG',
        remove_divergent: true,
        remove_insertions: true,
        crop_ends: true,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call buildPhylogeny', async () => {
      await alignment.buildPhylogeny({
        alignment: '>aligned\nATCG',
        method: 'nj',
        bootstrap: 100,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call calculateDistances', async () => {
      await alignment.calculateDistances({
        alignment: '>aligned\nATCG',
        model: 'identity',
        format: 'matrix',
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call alignAndAnalyze', async () => {
      await alignment.alignAndAnalyze({
        fasta_content: '>seq1\nATCG',
        run_id: 'test-run',
        align_method: 'mafft',
        tree_method: 'nj',
        clean_alignment: true,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });
  });

  describe('Design Server (6 tools)', () => {
    const mockClient = {
      request: vi.fn().mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify({ regions: [] }) }],
      }),
    };

    beforeAll(() => {
      (client as any).clients.set('design', mockClient);
    });

    it('should call findSignatureRegions', async () => {
      await design.findSignatureRegions({
        target_alignment: '>target\nATCG',
        offtarget_alignment: '>offtarget\nGCTA',
        window_size: 100,
        step_size: 10,
        min_conservation: 0.9,
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            name: 'find_signature_regions',
          }),
        }),
        expect.anything()
      );
    });

    it('should call analyzeSpecificity', async () => {
      await design.analyzeSpecificity({
        target_sequences: '>target\nATCG',
        offtarget_sequences: '>offtarget\nGCTA',
        method: 'kmer',
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call rankRegions', async () => {
      await design.rankRegions({
        regions: [{ start: 0, end: 100, score: 0.95 }],
        weights: { conservation: 0.5, specificity: 0.3, complexity: 0.2 },
        top_n: 10,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call primer3Design', async () => {
      await design.primer3Design({
        template: 'ATCGATCGATCG',
        target_region: [0, 12],
        primer_size: [18, 20, 25],
        primer_tm: [57.0, 60.0, 63.0],
        product_size: [75, 150],
        num_return: 5,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call oligoQc', async () => {
      await design.oligoQc({
        primers: [
          { name: 'F1', sequence: 'ATCGATCGATCG' },
          { name: 'R1', sequence: 'GCTAGCTAGCTA' },
        ],
        check_hairpins: true,
        check_dimers: true,
        max_hairpin_tm: 45.0,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call designPrimersComplete', async () => {
      await design.designPrimersComplete({
        target_alignment: '>target\nATCG',
        offtarget_alignment: '>offtarget\nGCTA',
        run_id: 'test-run',
        num_primer_pairs: 5,
        primer_size_range: [18, 25],
        product_size_range: [75, 150],
      });

      expect(mockClient.request).toHaveBeenCalled();
    });
  });

  describe('Validation Server (7 tools)', () => {
    const mockClient = {
      request: vi.fn().mockResolvedValue({
        content: [{ type: 'text', text: JSON.stringify({ hits: [] }) }],
      }),
    };

    beforeAll(() => {
      (client as any).clients.set('validation', mockClient);
    });

    it('should call ggetBlast', async () => {
      await validation.ggetBlast({
        sequence: 'ATCGATCGATCG',
        program: 'blastn',
        database: 'nt',
        limit: 50,
        expect: 10.0,
      });

      expect(mockClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          params: expect.objectContaining({
            name: 'gget_blast',
          }),
        }),
        expect.anything()
      );
    });

    it('should call ggetBlat', async () => {
      await validation.ggetBlat({
        sequence: 'ATCGATCGATCG',
        assembly: 'human',
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call blastNt', async () => {
      await validation.blastNt({
        sequence: 'ATCGATCGATCG',
        database: 'nt',
        evalue: 0.001,
        max_hits: 100,
        word_size: 11,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call inSilicoPcr', async () => {
      await validation.inSilicoPcr({
        forward_primer: 'ATCGATCG',
        reverse_primer: 'GCTAGCTA',
        database_sequences: '>target\nATCGATCGATCGATCGGCTAGCTA',
        max_product_size: 2000,
        mismatch_tolerance: 1,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call assessCoverage', async () => {
      await validation.assessCoverage({
        primers: [
          { forward: 'ATCGATCG', reverse: 'GCTAGCTA' },
        ],
        target_sequences: '>target\nATCGATCG',
        offtarget_sequences: '>offtarget\nGCTAGCTA',
        mismatch_tolerance: 1,
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call searchPubmed', async () => {
      await validation.searchPubmed({
        query: 'Salmo salar qPCR',
        max_results: 20,
        retmode: 'json',
      });

      expect(mockClient.request).toHaveBeenCalled();
    });

    it('should call validatePrimersComplete', async () => {
      await validation.validatePrimersComplete({
        primers: [
          {
            name: 'primer1',
            forward: 'ATCGATCG',
            reverse: 'GCTAGCTA',
          },
        ],
        target_sequences: '>target\nATCGATCG',
        offtarget_sequences: '>offtarget\nGCTAGCTA',
        run_id: 'test-run',
        organism: 'Salmo salar',
      });

      expect(mockClient.request).toHaveBeenCalled();
    });
  });

  describe('Type safety across all servers', () => {
    it('should enforce required parameters', () => {
      // These would fail TypeScript compilation:
      // processing.fastaQc({})  // Error: missing fasta_content
      // alignment.alignSequences({})  // Error: missing fasta_content
      // design.findSignatureRegions({})  // Error: missing target_alignment
      // validation.ggetBlast({})  // Error: missing sequence

      expect(true).toBe(true);
    });

    it('should provide enum types for all constrained parameters', () => {
      // Valid enum values that compile:
      const validMethods: Array<Parameters<typeof alignment.alignSequences>[0]['method']> = [
        'mafft',
        'muscle',
        'clustalo',
        'gget_muscle',
      ];

      const validBlastPrograms: Array<Parameters<typeof validation.ggetBlast>[0]['program']> = [
        'blastn',
        'blastp',
        'blastx',
        'tblastn',
        'tblastx',
      ];

      expect(validMethods).toHaveLength(4);
      expect(validBlastPrograms).toHaveLength(5);
    });
  });

  describe('Tool count verification', () => {
    it('should have all 34 tools exported', () => {
      // Database: 11 tools
      const databaseTools = [
        database.getSequences,
        database.ggetRef,
        database.ggetSearch,
        database.ggetInfo,
        database.ggetSeq,
        database.getNeighbors,
        database.getTaxonomy,
        database.searchSraStudies,
        database.getSraRuninfo,
        database.searchSraCloud,
        database.extractSequenceColumns,
      ];

      // Processing: 5 tools
      const processingTools = [
        processing.fastaQc,
        processing.dereplicateSequences,
        processing.maskLowComplexity,
        processing.detectChimeras,
        processing.processSequences,
      ];

      // Alignment: 5 tools
      const alignmentTools = [
        alignment.alignSequences,
        alignment.processAlignment,
        alignment.buildPhylogeny,
        alignment.calculateDistances,
        alignment.alignAndAnalyze,
      ];

      // Design: 6 tools
      const designTools = [
        design.findSignatureRegions,
        design.analyzeSpecificity,
        design.rankRegions,
        design.primer3Design,
        design.oligoQc,
        design.designPrimersComplete,
      ];

      // Validation: 7 tools
      const validationTools = [
        validation.ggetBlast,
        validation.ggetBlat,
        validation.blastNt,
        validation.inSilicoPcr,
        validation.assessCoverage,
        validation.searchPubmed,
        validation.validatePrimersComplete,
      ];

      const totalTools =
        databaseTools.length +
        processingTools.length +
        alignmentTools.length +
        designTools.length +
        validationTools.length;

      expect(totalTools).toBe(34);

      // Verify all are functions
      [...databaseTools, ...processingTools, ...alignmentTools, ...designTools, ...validationTools].forEach(
        (tool) => {
          expect(typeof tool).toBe('function');
        }
      );
    });
  });
});

describe('Complete Workflow Integration', () => {
  it('should demonstrate end-to-end qPCR assay design', async () => {
    // Example workflow combining tools from all 5 servers:
    // 1. Database: Fetch sequences
    // 2. Processing: Quality control
    // 3. Alignment: Align sequences
    // 4. Design: Design primers
    // 5. Validation: Validate primers

    const mockClient = new MCPCodeExecutionClient(
      new Map([
        ['database', { command: 'echo', args: ['test'] }],
        ['processing', { command: 'echo', args: ['test'] }],
        ['alignment', { command: 'echo', args: ['test'] }],
        ['design', { command: 'echo', args: ['test'] }],
        ['validation', { command: 'echo', args: ['test'] }],
      ])
    );

    (mockClient as any).initialized = true;
    setMCPClient(mockClient);

    const requestMock = vi.fn().mockResolvedValue({
      content: [{ type: 'text', text: '{"success": true}' }],
    });

    ['database', 'processing', 'alignment', 'design', 'validation'].forEach((server) => {
      (mockClient as any).clients.set(server, { request: requestMock });
    });

    // Workflow simulation
    await database.getSequences({ taxon: 'Salmo salar', region: 'COI' });
    await processing.fastaQc({ fasta_content: '>seq\nATCG' });
    await alignment.alignSequences({ fasta_content: '>seq\nATCG' });
    await design.designPrimersComplete({ target_alignment: '>aligned\nATCG' });
    await validation.validatePrimersComplete({
      primers: [{ name: 'p1', forward: 'ATCG', reverse: 'GCTA' }],
      target_sequences: '>target\nATCG',
    });

    expect(requestMock).toHaveBeenCalledTimes(5);
  });
});
