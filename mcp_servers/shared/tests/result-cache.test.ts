/**
 * Tests for Result Caching System
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  ResultCache,
  PhylogeneticTreeCache,
  AlignmentCache,
  CacheStats,
} from '../result-cache';

describe('ResultCache', () => {
  let cache: ResultCache<any>;

  beforeEach(() => {
    cache = new ResultCache({
      maxSize: 1024 * 1024, // 1MB
      maxEntries: 100,
      defaultTTL: 3600,
      enablePersistence: false,
    });
  });

  afterEach(() => {
    cache.clear();
  });

  describe('Basic Operations', () => {
    it('should set and get cache entries', () => {
      cache.set('key1', { data: 'value1' });
      const result = cache.get('key1');

      expect(result).toEqual({ data: 'value1' });
    });

    it('should return null for non-existent keys', () => {
      const result = cache.get('nonexistent');
      expect(result).toBeNull();
    });

    it('should check if key exists', () => {
      cache.set('key1', { data: 'value1' });

      expect(cache.has('key1')).toBe(true);
      expect(cache.has('nonexistent')).toBe(false);
    });

    it('should delete cache entries', () => {
      cache.set('key1', { data: 'value1' });
      expect(cache.has('key1')).toBe(true);

      const deleted = cache.delete('key1');
      expect(deleted).toBe(true);
      expect(cache.has('key1')).toBe(false);
    });

    it('should return false when deleting non-existent key', () => {
      const deleted = cache.delete('nonexistent');
      expect(deleted).toBe(false);
    });

    it('should clear all entries', () => {
      cache.set('key1', { data: 'value1' });
      cache.set('key2', { data: 'value2' });

      expect(cache.getStats().totalEntries).toBe(2);

      cache.clear();

      expect(cache.getStats().totalEntries).toBe(0);
    });
  });

  describe('Key Generation', () => {
    it('should generate consistent SHA256 keys', () => {
      const data = { taxon: 'Salmo salar', region: 'COI' };
      const key1 = cache.generateKey(data);
      const key2 = cache.generateKey(data);

      expect(key1).toBe(key2);
      expect(key1).toMatch(/^[a-f0-9]{64}$/); // SHA256 hex
    });

    it('should generate different keys for different data', () => {
      const key1 = cache.generateKey({ a: 1 });
      const key2 = cache.generateKey({ a: 2 });

      expect(key1).not.toBe(key2);
    });

    it('should be order-sensitive for objects', () => {
      const key1 = cache.generateKey({ a: 1, b: 2 });
      const key2 = cache.generateKey({ b: 2, a: 1 });

      // JSON.stringify is order-dependent
      expect(key1).not.toBe(key2);
    });
  });

  describe('TTL (Time To Live)', () => {
    it('should respect TTL for cache entries', async () => {
      cache.set('key1', { data: 'value1' }, 1); // 1 second TTL

      expect(cache.get('key1')).toEqual({ data: 'value1' });

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 1100));

      expect(cache.get('key1')).toBeNull();
    });

    it('should use default TTL when not specified', () => {
      cache.set('key1', { data: 'value1' });

      const metadata = cache.getMetadata('key1');
      expect(metadata?.ttl).toBe(3600); // Default from config
    });

    it('should clean expired entries', async () => {
      cache.set('key1', { data: 'value1' }, 1); // 1 second TTL
      cache.set('key2', { data: 'value2' }, 100); // 100 seconds TTL

      expect(cache.getStats().totalEntries).toBe(2);

      // Wait for first entry to expire
      await new Promise(resolve => setTimeout(resolve, 1100));

      const removed = cache.cleanExpired();
      expect(removed).toBe(1);
      expect(cache.getStats().totalEntries).toBe(1);
      expect(cache.has('key2')).toBe(true);
    });
  });

  describe('Size Limits', () => {
    it('should track cache size', () => {
      const largeData = { data: 'x'.repeat(10000) };
      cache.set('key1', largeData);

      const stats = cache.getStats();
      expect(stats.totalSize).toBeGreaterThan(10000);
    });

    it('should reject entries larger than max cache size', () => {
      const hugeData = { data: 'x'.repeat(2 * 1024 * 1024) }; // 2MB

      expect(() => {
        cache.set('key1', hugeData);
      }).toThrow('exceeds max cache size');
    });

    it('should evict LRU entries when size limit reached', () => {
      // Fill cache to near capacity
      for (let i = 0; i < 50; i++) {
        cache.set(`key${i}`, { data: 'x'.repeat(20000) });
      }

      const statsBefore = cache.getStats();
      expect(statsBefore.evictions).toBeGreaterThan(0);
    });
  });

  describe('Entry Limits', () => {
    it('should evict LRU entries when entry limit reached', () => {
      // Create cache with small entry limit
      const smallCache = new ResultCache({
        maxEntries: 10,
        enablePersistence: false,
      });

      // Add more entries than limit
      for (let i = 0; i < 15; i++) {
        smallCache.set(`key${i}`, { data: i });
      }

      const stats = smallCache.getStats();
      expect(stats.totalEntries).toBeLessThanOrEqual(10);
      expect(stats.evictions).toBeGreaterThan(0);
    });
  });

  describe('LRU Eviction', () => {
    it('should evict least recently accessed entries', () => {
      const smallCache = new ResultCache({
        maxEntries: 3,
        enablePersistence: false,
      });

      // Add 3 entries
      smallCache.set('key1', { data: 1 });
      smallCache.set('key2', { data: 2 });
      smallCache.set('key3', { data: 3 });

      // Access key1 and key2 (making key3 LRU)
      smallCache.get('key1');
      smallCache.get('key2');

      // Add new entry (should evict key3)
      smallCache.set('key4', { data: 4 });

      expect(smallCache.has('key1')).toBe(true);
      expect(smallCache.has('key2')).toBe(true);
      expect(smallCache.has('key3')).toBe(false);
      expect(smallCache.has('key4')).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should track cache statistics', () => {
      cache.set('key1', { data: 'value1' });
      cache.set('key2', { data: 'value2' });

      cache.get('key1'); // Hit
      cache.get('key1'); // Hit
      cache.get('nonexistent'); // Miss

      const stats = cache.getStats();

      expect(stats.totalEntries).toBe(2);
      expect(stats.hits).toBe(2);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBeCloseTo(0.667, 2);
    });

    it('should track oldest and newest entries', () => {
      cache.set('key1', { data: 'value1' });
      const stats1 = cache.getStats();
      expect(stats1.oldestEntry).toBe(stats1.newestEntry);

      // Add another entry
      cache.set('key2', { data: 'value2' });
      const stats2 = cache.getStats();
      expect(stats2.oldestEntry).toBeLessThan(stats2.newestEntry!);
    });

    it('should have zero hit rate initially', () => {
      const stats = cache.getStats();
      expect(stats.hitRate).toBe(0);
    });
  });

  describe('Metadata', () => {
    it('should store and retrieve entry metadata', () => {
      cache.set('key1', { data: 'value1' }, 3600, { author: 'test', version: 1 });

      const metadata = cache.getMetadata('key1');

      expect(metadata).toBeDefined();
      expect(metadata?.author).toBe('test');
      expect(metadata?.version).toBe(1);
      expect(metadata?.timestamp).toBeDefined();
      expect(metadata?.size).toBeGreaterThan(0);
    });

    it('should return null for non-existent key metadata', () => {
      const metadata = cache.getMetadata('nonexistent');
      expect(metadata).toBeNull();
    });

    it('should track access count', () => {
      cache.set('key1', { data: 'value1' });

      cache.get('key1');
      cache.get('key1');
      cache.get('key1');

      const metadata = cache.getMetadata('key1');
      expect(metadata?.accessCount).toBe(3);
    });

    it('should track last accessed time', () => {
      cache.set('key1', { data: 'value1' });

      const metadata1 = cache.getMetadata('key1');
      const lastAccessed1 = metadata1?.lastAccessed;

      // Wait a bit
      setTimeout(() => {}, 10);

      cache.get('key1');

      const metadata2 = cache.getMetadata('key1');
      const lastAccessed2 = metadata2?.lastAccessed;

      expect(lastAccessed2).toBeGreaterThanOrEqual(lastAccessed1!);
    });
  });

  describe('Keys', () => {
    it('should list all cache keys', () => {
      cache.set('key1', { data: 'value1' });
      cache.set('key2', { data: 'value2' });
      cache.set('key3', { data: 'value3' });

      const keys = cache.keys();

      expect(keys).toHaveLength(3);
      expect(keys).toContain('key1');
      expect(keys).toContain('key2');
      expect(keys).toContain('key3');
    });

    it('should return empty array for empty cache', () => {
      const keys = cache.keys();
      expect(keys).toHaveLength(0);
    });
  });

  describe('Complex Data Types', () => {
    it('should cache arrays', () => {
      const data = [1, 2, 3, 4, 5];
      cache.set('key1', data);

      const result = cache.get('key1');
      expect(result).toEqual(data);
    });

    it('should cache nested objects', () => {
      const data = {
        user: {
          name: 'Alice',
          metadata: {
            age: 30,
            roles: ['admin', 'user'],
          },
        },
      };

      cache.set('key1', data);

      const result = cache.get('key1');
      expect(result).toEqual(data);
    });
  });
});

describe('PhylogeneticTreeCache', () => {
  let treeCache: PhylogeneticTreeCache;

  beforeEach(() => {
    treeCache = new PhylogeneticTreeCache({
      maxSize: 10 * 1024 * 1024, // 10MB
      enablePersistence: false,
    });
  });

  afterEach(() => {
    treeCache.clear();
  });

  it('should cache phylogenetic trees', () => {
    const alignment = '>seq1\nATCG\n>seq2\nATGC';
    const tree = {
      newick: '(seq1:0.1,seq2:0.2);',
      method: 'neighbor_joining',
    };

    treeCache.cacheTree(alignment, tree, 'neighbor_joining');

    const cached = treeCache.getTree(alignment, 'neighbor_joining');
    expect(cached).toEqual(tree);
  });

  it('should return different trees for different methods', () => {
    const alignment = '>seq1\nATCG\n>seq2\nATGC';
    const njTree = { newick: '(seq1:0.1,seq2:0.2);', method: 'nj' };
    const mlTree = { newick: '(seq1:0.15,seq2:0.25);', method: 'ml' };

    treeCache.cacheTree(alignment, njTree, 'neighbor_joining');
    treeCache.cacheTree(alignment, mlTree, 'maximum_likelihood');

    expect(treeCache.getTree(alignment, 'neighbor_joining')).toEqual(njTree);
    expect(treeCache.getTree(alignment, 'maximum_likelihood')).toEqual(mlTree);
  });

  it('should return null for non-cached trees', () => {
    const alignment = '>seq1\nATCG';
    const tree = treeCache.getTree(alignment, 'neighbor_joining');

    expect(tree).toBeNull();
  });

  it('should use longer default TTL', () => {
    const alignment = '>seq1\nATCG';
    const tree = { newick: '(seq1:0.1);' };

    treeCache.cacheTree(alignment, tree, 'nj');

    const key = treeCache.generateKey({ alignment, method: 'nj' });
    const metadata = treeCache.getMetadata(key);

    expect(metadata?.ttl).toBe(7200); // 2 hours
  });
});

describe('AlignmentCache', () => {
  let alignCache: AlignmentCache;

  beforeEach(() => {
    alignCache = new AlignmentCache({
      maxSize: 10 * 1024 * 1024, // 10MB
      enablePersistence: false,
    });
  });

  afterEach(() => {
    alignCache.clear();
  });

  it('should cache alignment results', () => {
    const sequences = '>seq1\nATCG\n>seq2\nATGC';
    const alignment = '>seq1\nA-TCG\n>seq2\nAT-GC';

    alignCache.cacheAlignment(sequences, alignment, 'mafft');

    const cached = alignCache.getAlignment(sequences, 'mafft');
    expect(cached).toBe(alignment);
  });

  it('should distinguish by algorithm parameters', () => {
    const sequences = '>seq1\nATCG\n>seq2\nATGC';
    const alignment1 = '>seq1\nA-TCG\n>seq2\nAT-GC';
    const alignment2 = '>seq1\nATCG-\n>seq2\nATGC-';

    alignCache.cacheAlignment(sequences, alignment1, 'mafft', { strategy: 'auto' });
    alignCache.cacheAlignment(sequences, alignment2, 'mafft', { strategy: 'linsi' });

    expect(alignCache.getAlignment(sequences, 'mafft', { strategy: 'auto' })).toBe(
      alignment1
    );
    expect(alignCache.getAlignment(sequences, 'mafft', { strategy: 'linsi' })).toBe(
      alignment2
    );
  });

  it('should return null for non-cached alignments', () => {
    const sequences = '>seq1\nATCG';
    const alignment = alignCache.getAlignment(sequences, 'mafft');

    expect(alignment).toBeNull();
  });

  it('should distinguish between different algorithms', () => {
    const sequences = '>seq1\nATCG\n>seq2\nATGC';
    const mafftAlignment = '>seq1\nA-TCG\n>seq2\nAT-GC';
    const muscleAlignment = '>seq1\nATCG-\n>seq2\nATGC-';

    alignCache.cacheAlignment(sequences, mafftAlignment, 'mafft');
    alignCache.cacheAlignment(sequences, muscleAlignment, 'muscle');

    expect(alignCache.getAlignment(sequences, 'mafft')).toBe(mafftAlignment);
    expect(alignCache.getAlignment(sequences, 'muscle')).toBe(muscleAlignment);
  });
});

describe('Cache Integration', () => {
  it('should handle workflow with multiple cache types', () => {
    const phyloCache = new PhylogeneticTreeCache({ enablePersistence: false });
    const alignCache = new AlignmentCache({ enablePersistence: false });

    // Workflow: sequences → alignment → tree
    const sequences = '>seq1\nATCGATCG\n>seq2\nATGCATGC\n>seq3\nAAGGCCTT';
    const alignment = '>seq1\nATCG-ATCG\n>seq2\nATGC-ATGC\n>seq3\nAAGG-CCTT';
    const tree = { newick: '((seq1,seq2),seq3);', method: 'nj' };

    // Cache alignment
    alignCache.cacheAlignment(sequences, alignment, 'mafft');

    // Cache tree
    phyloCache.cacheTree(alignment, tree, 'neighbor_joining');

    // Retrieve from cache
    const cachedAlignment = alignCache.getAlignment(sequences, 'mafft');
    expect(cachedAlignment).toBe(alignment);

    const cachedTree = phyloCache.getTree(alignment, 'neighbor_joining');
    expect(cachedTree).toEqual(tree);
  });
});
