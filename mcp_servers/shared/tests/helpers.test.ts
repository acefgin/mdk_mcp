/**
 * Tests for Context-Efficient Helper Utilities
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { promises as fs } from 'fs';
import path from 'path';
import {
  parseFastaStats,
  filterAndSave,
  extractFields,
  summarizeAlignment,
  batchProcess,
  cacheResult,
  getCachedResult,
  saveToFile,
  formatBytes,
  truncateForContext,
} from '../helpers';

describe('Context-Efficient Helpers', () => {
  const testDataDir = '/tmp/test-helpers';

  beforeAll(async () => {
    await fs.mkdir(testDataDir, { recursive: true });
  });

  afterAll(async () => {
    await fs.rm(testDataDir, { recursive: true, force: true });
  });

  describe('parseFastaStats', () => {
    it('should parse FASTA and return statistics', () => {
      const fasta = `>seq1
ATCGATCGATCG
>seq2
GCTAGCTAGCTA
>seq3
AAAAAAAAAA`;

      const stats = parseFastaStats(fasta);

      expect(stats.count).toBe(3);
      expect(stats.totalLength).toBe(34);
      expect(stats.averageLength).toBeCloseTo(11.33, 2);
      expect(stats.minLength).toBe(10);
      expect(stats.maxLength).toBe(12);
      expect(stats.gcContent).toBeGreaterThan(0);
      expect(stats.nContent).toBe(0);
    });

    it('should handle empty FASTA', () => {
      const stats = parseFastaStats('');

      expect(stats.count).toBe(0);
      expect(stats.totalLength).toBe(0);
      expect(stats.averageLength).toBe(0);
    });

    it('should calculate GC content correctly', () => {
      const fasta = `>seq1
GGGGCCCC`;

      const stats = parseFastaStats(fasta);

      expect(stats.gcContent).toBe(100);
    });

    it('should calculate N content correctly', () => {
      const fasta = `>seq1
NNNNATCG`;

      const stats = parseFastaStats(fasta);

      expect(stats.nContent).toBe(50);
    });

    it('should handle sequences with newlines', () => {
      const fasta = `>seq1
ATCG
ATCG
ATCG`;

      const stats = parseFastaStats(fasta);

      expect(stats.count).toBe(1);
      expect(stats.totalLength).toBe(12);
    });
  });

  describe('filterAndSave', () => {
    it('should filter sequences and save to file', async () => {
      const fasta = `>seq1
ATCGATCGATCGATCG
>seq2
AAAA
>seq3
GCTAGCTAGCTAGCTA`;

      const outputPath = path.join(testDataDir, 'filtered.fasta');
      const metadata = await filterAndSave(
        fasta,
        seq => seq.length > 10,
        outputPath
      );

      expect(metadata.path).toBe(outputPath);
      expect(metadata.lines).toBe(4); // 2 sequences * 2 lines each
      expect(metadata.size).toBeGreaterThan(0);
      expect(metadata.hash).toBeDefined();

      // Verify file content
      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('seq1');
      expect(content).toContain('seq3');
      expect(content).not.toContain('seq2');
    });

    it('should create output directory if needed', async () => {
      const fasta = `>seq1
ATCG`;

      const outputPath = path.join(testDataDir, 'nested/dir/output.fasta');
      const metadata = await filterAndSave(fasta, () => true, outputPath);

      expect(metadata.path).toBe(outputPath);

      // Verify directory was created
      const dirExists = await fs
        .access(path.dirname(outputPath))
        .then(() => true)
        .catch(() => false);
      expect(dirExists).toBe(true);
    });

    it('should handle filter function with header', async () => {
      const fasta = `>seq1|taxon=fish
ATCGATCG
>seq2|taxon=bird
GCTAGCTA
>seq3|taxon=fish
AAAAAAAA`;

      const outputPath = path.join(testDataDir, 'fish_only.fasta');
      const metadata = await filterAndSave(
        fasta,
        (seq, header) => header.includes('fish'),
        outputPath
      );

      const content = await fs.readFile(outputPath, 'utf-8');
      expect(content).toContain('seq1');
      expect(content).toContain('seq3');
      expect(content).not.toContain('seq2');
    });
  });

  describe('extractFields', () => {
    it('should extract fields from FASTA headers', () => {
      const fasta = `>seq1|accession=ABC123|organism=Fish
ATCG
>seq2|accession=DEF456|organism=Bird
GCTA`;

      const fields = extractFields(fasta, ['accession', 'organism']);

      expect(fields).toHaveLength(2);
      expect(fields[0]).toEqual({
        accession: 'ABC123',
        organism: 'Fish',
      });
      expect(fields[1]).toEqual({
        accession: 'DEF456',
        organism: 'Bird',
      });
    });

    it('should handle different header formats', () => {
      const fasta = `>seq1 accession:XYZ789 [organism=Mouse]
ATCG`;

      const fields = extractFields(fasta, ['accession', 'organism']);

      expect(fields).toHaveLength(1);
      expect(fields[0].accession).toBe('XYZ789');
      expect(fields[0].organism).toBe('Mouse');
    });

    it('should handle missing fields', () => {
      const fasta = `>seq1|accession=ABC123
ATCG`;

      const fields = extractFields(fasta, ['accession', 'organism']);

      expect(fields).toHaveLength(1);
      expect(fields[0].accession).toBe('ABC123');
      expect(fields[0].organism).toBe('');
    });
  });

  describe('summarizeAlignment', () => {
    it('should summarize alignment quality', () => {
      const alignment = `>seq1
ATCG-ATCG
>seq2
ATCG-ATCG
>seq3
ATCGGATCG`;

      const summary = summarizeAlignment(alignment);

      expect(summary.sequences).toBe(3);
      expect(summary.length).toBe(9);
      expect(summary.gapPercentage).toBeGreaterThan(0);
      expect(summary.conservationScore).toBeGreaterThan(0);
      expect(summary.identityMatrix).toBeDefined();
      expect(summary.identityMatrix.length).toBeGreaterThan(0);
    });

    it('should handle perfect conservation', () => {
      const alignment = `>seq1
ATCGATCG
>seq2
ATCGATCG
>seq3
ATCGATCG`;

      const summary = summarizeAlignment(alignment);

      expect(summary.conservationScore).toBe(100);
    });

    it('should calculate identity matrix', () => {
      const alignment = `>seq1
AAAA
>seq2
AAAA
>seq3
TTTT`;

      const summary = summarizeAlignment(alignment);

      expect(summary.identityMatrix).toBeDefined();
      expect(summary.identityMatrix[0][1]).toBe(100); // seq1 vs seq2
      expect(summary.identityMatrix[0][2]).toBe(0); // seq1 vs seq3
    });

    it('should handle empty alignment', () => {
      const summary = summarizeAlignment('');

      expect(summary.sequences).toBe(0);
      expect(summary.length).toBe(0);
    });
  });

  describe('batchProcess', () => {
    it('should process items in batches', async () => {
      const items = Array.from({ length: 250 }, (_, i) => i);

      const result = await batchProcess(
        items,
        async batch => batch.map(n => n * 2),
        100
      );

      expect(result.total).toBe(250);
      expect(result.batches).toBe(3);
      expect(result.processed).toBe(250);
      expect(result.failed).toBe(0);
      expect(result.results).toHaveLength(250);
      expect(result.results[0]).toBe(0);
      expect(result.results[249]).toBe(498);
    });

    it('should handle batch failures', async () => {
      const items = Array.from({ length: 100 }, (_, i) => i);

      const result = await batchProcess(
        items,
        async batch => {
          if (batch[0] === 50) {
            throw new Error('Batch failed');
          }
          return batch.map(n => n * 2);
        },
        50
      );

      expect(result.total).toBe(100);
      expect(result.batches).toBe(2);
      expect(result.processed).toBe(50);
      expect(result.failed).toBe(50);
    });

    it('should use custom batch size', async () => {
      const items = Array.from({ length: 100 }, (_, i) => i);

      const result = await batchProcess(
        items,
        async batch => batch.map(n => n),
        25
      );

      expect(result.batches).toBe(4);
    });
  });

  describe('cacheResult and getCachedResult', () => {
    it('should cache and retrieve results', async () => {
      const key = 'test-key-1';
      const data = { value: 'test data' };

      const cachePath = await cacheResult(key, data);
      expect(cachePath).toContain(key.substring(0, 8));

      const retrieved = await getCachedResult(key);
      expect(retrieved).toEqual(data);
    });

    it('should handle cache misses', async () => {
      const result = await getCachedResult('nonexistent-key');
      expect(result).toBeNull();
    });

    it('should respect TTL', async () => {
      const key = 'test-key-ttl';
      const data = { value: 'expires soon' };

      await cacheResult(key, data, 1); // 1 second TTL

      // Immediate retrieval should work
      const immediate = await getCachedResult(key);
      expect(immediate).toEqual(data);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 1100));

      const expired = await getCachedResult(key);
      expect(expired).toBeNull();
    });

    it('should handle complex data types', async () => {
      const key = 'test-key-complex';
      const data = {
        array: [1, 2, 3],
        nested: { foo: 'bar' },
        number: 42,
        boolean: true,
      };

      await cacheResult(key, data);
      const retrieved = await getCachedResult(key);

      expect(retrieved).toEqual(data);
    });
  });

  describe('saveToFile', () => {
    it('should save data to file and return metadata', async () => {
      const data = 'Test file content';
      const filename = 'test-save.txt';

      const metadata = await saveToFile(data, filename);

      expect(metadata.path).toContain(filename);
      expect(metadata.size).toBe(data.length);
      expect(metadata.lines).toBe(1);
      expect(metadata.hash).toBeDefined();

      // Verify file exists
      const exists = await fs
        .access(metadata.path)
        .then(() => true)
        .catch(() => false);
      expect(exists).toBe(true);
    });

    it('should create nested directories', async () => {
      const data = 'Nested file';
      const filename = 'nested/path/file.txt';

      const metadata = await saveToFile(data, filename);

      expect(metadata.path).toContain(filename);
    });
  });

  describe('formatBytes', () => {
    it('should format bytes correctly', () => {
      expect(formatBytes(0)).toBe('0 B');
      expect(formatBytes(1024)).toBe('1 KB');
      expect(formatBytes(1024 * 1024)).toBe('1 MB');
      expect(formatBytes(1024 * 1024 * 1024)).toBe('1 GB');
      expect(formatBytes(1536)).toBe('1.5 KB');
    });
  });

  describe('truncateForContext', () => {
    it('should not truncate short strings', () => {
      const data = 'short string';
      const result = truncateForContext(data, 100);

      expect(result).toBe(data);
    });

    it('should truncate long strings with preview', () => {
      const data = 'x'.repeat(2000);
      const result = truncateForContext(data, 1000);

      expect(result).toHaveProperty('truncated', true);
      expect(result).toHaveProperty('preview');
      expect(result).toHaveProperty('size', 2000);

      if (typeof result === 'object') {
        expect(result.preview.length).toBeLessThan(data.length);
      }
    });

    it('should truncate without preview when requested', () => {
      const data = 'y'.repeat(2000);
      const result = truncateForContext(data, 1000, false);

      expect(result).toHaveProperty('truncated', true);
      expect(result).toHaveProperty('size', 2000);

      if (typeof result === 'object') {
        expect(result.preview).toBe('');
      }
    });
  });

  describe('Token Reduction Verification', () => {
    it('should demonstrate token reduction with parseFastaStats', () => {
      // Generate large FASTA
      let fasta = '';
      for (let i = 0; i < 1000; i++) {
        fasta += `>seq${i}|accession=ABC${i}|organism=Test\n`;
        fasta += 'ATCG'.repeat(150) + '\n';
      }

      const fullSize = fasta.length;
      const stats = parseFastaStats(fasta);
      const statsSize = JSON.stringify(stats).length;

      const reduction = ((1 - statsSize / fullSize) * 100).toFixed(2);

      console.log('\nToken Reduction: parseFastaStats');
      console.log(`  Full FASTA: ${fullSize} chars (~${Math.ceil(fullSize / 4)} tokens)`);
      console.log(`  Statistics: ${statsSize} chars (~${Math.ceil(statsSize / 4)} tokens)`);
      console.log(`  Reduction: ${reduction}%`);

      expect(statsSize).toBeLessThan(fullSize * 0.01); // At least 99% reduction
    });
  });
});
