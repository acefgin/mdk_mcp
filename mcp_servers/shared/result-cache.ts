/**
 * Result Caching System
 *
 * Provides SHA256-based caching for expensive bioinformatics operations
 * like phylogenetic tree construction and large alignments.
 *
 * Features:
 * - SHA256-based cache keys for content-addressable storage
 * - TTL (Time To Live) support with automatic expiration
 * - Size limits with LRU (Least Recently Used) eviction
 * - Persistent storage to file system
 * - Cache statistics and management
 * - Specialized caching for phylogenetic trees and alignments
 */

import crypto from 'crypto';
import { promises as fs } from 'fs';

/**
 * Cache entry metadata
 */
interface CacheEntry<T> {
  key: string;
  data: T;
  timestamp: number;
  accessCount: number;
  lastAccessed: number;
  ttl?: number;
  size: number;
  metadata?: Record<string, any>;
}

/**
 * Cache statistics
 */
export interface CacheStats {
  totalEntries: number;
  totalSize: number;
  hits: number;
  misses: number;
  evictions: number;
  hitRate: number;
  oldestEntry: number | null;
  newestEntry: number | null;
}

/**
 * Cache configuration
 */
export interface CacheConfig {
  maxSize?: number; // Maximum cache size in bytes (default: 100MB)
  maxEntries?: number; // Maximum number of entries (default: 1000)
  defaultTTL?: number; // Default TTL in seconds (default: 3600 = 1 hour)
  persistPath?: string; // Path for persistent storage
  enablePersistence?: boolean; // Whether to persist cache to disk
}

/**
 * Result Cache Manager
 *
 * Provides efficient caching for bioinformatics results with SHA256-based
 * content-addressable storage.
 */
export class ResultCache<T = any> {
  private cache: Map<string, CacheEntry<T>> = new Map();
  private stats: CacheStats = {
    totalEntries: 0,
    totalSize: 0,
    hits: 0,
    misses: 0,
    evictions: 0,
    hitRate: 0,
    oldestEntry: null,
    newestEntry: null,
  };
  private config: Required<CacheConfig>;

  constructor(config: CacheConfig = {}) {
    this.config = {
      maxSize: config.maxSize ?? 100 * 1024 * 1024, // 100MB
      maxEntries: config.maxEntries ?? 1000,
      defaultTTL: config.defaultTTL ?? 3600, // 1 hour
      persistPath: config.persistPath ?? '/workspace/cache/result-cache.json',
      enablePersistence: config.enablePersistence ?? true,
    };
  }

  /**
   * Generate SHA256 cache key from data
   *
   * @param data - Data to generate key from (will be stringified)
   * @returns SHA256 hash as hex string
   *
   * @example
   * const key = cache.generateKey({ taxon: 'Salmo salar', region: 'COI' });
   */
  generateKey(data: any): string {
    const json = JSON.stringify(data);
    return crypto.createHash('sha256').update(json).digest('hex');
  }

  /**
   * Set a cache entry
   *
   * @param key - Cache key
   * @param data - Data to cache
   * @param ttl - Time to live in seconds (optional)
   * @param metadata - Additional metadata (optional)
   *
   * @example
   * cache.set('alignment_key', alignmentResult, 7200); // Cache for 2 hours
   */
  set(key: string, data: T, ttl?: number, metadata?: Record<string, any>): void {
    const size = this.calculateSize(data);

    // Check if adding this entry would exceed limits
    if (size > this.config.maxSize) {
      throw new Error(`Entry size (${size} bytes) exceeds max cache size (${this.config.maxSize} bytes)`);
    }

    // Evict entries if necessary
    this.evictIfNeeded(size);

    // Create entry
    const entry: CacheEntry<T> = {
      key,
      data,
      timestamp: Date.now(),
      accessCount: 0,
      lastAccessed: Date.now(),
      ttl: ttl ?? this.config.defaultTTL,
      size,
      metadata,
    };

    // Remove old entry if exists
    if (this.cache.has(key)) {
      const oldEntry = this.cache.get(key)!;
      this.stats.totalSize -= oldEntry.size;
      this.stats.totalEntries--;
    }

    // Add new entry
    this.cache.set(key, entry);
    this.stats.totalSize += size;
    this.stats.totalEntries++;

    // Update stats
    if (this.stats.oldestEntry === null || entry.timestamp < this.stats.oldestEntry) {
      this.stats.oldestEntry = entry.timestamp;
    }
    if (this.stats.newestEntry === null || entry.timestamp > this.stats.newestEntry) {
      this.stats.newestEntry = entry.timestamp;
    }
  }

  /**
   * Get a cache entry
   *
   * @param key - Cache key
   * @returns Cached data or null if not found/expired
   *
   * @example
   * const result = cache.get('alignment_key');
   * if (result) {
   *   // Use cached result
   * }
   */
  get(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      this.stats.misses++;
      this.updateHitRate();
      return null;
    }

    // Check if expired
    if (this.isExpired(entry)) {
      this.cache.delete(key);
      this.stats.totalSize -= entry.size;
      this.stats.totalEntries--;
      this.stats.misses++;
      this.updateHitRate();
      return null;
    }

    // Update access stats
    entry.accessCount++;
    entry.lastAccessed = Date.now();
    this.stats.hits++;
    this.updateHitRate();

    return entry.data;
  }

  /**
   * Check if a key exists in cache
   *
   * @param key - Cache key
   * @returns True if key exists and not expired
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    if (this.isExpired(entry)) {
      this.cache.delete(key);
      this.stats.totalSize -= entry.size;
      this.stats.totalEntries--;
      return false;
    }

    return true;
  }

  /**
   * Delete a cache entry
   *
   * @param key - Cache key
   * @returns True if entry was deleted
   */
  delete(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;

    this.cache.delete(key);
    this.stats.totalSize -= entry.size;
    this.stats.totalEntries--;
    return true;
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.stats.totalEntries = 0;
    this.stats.totalSize = 0;
    this.stats.oldestEntry = null;
    this.stats.newestEntry = null;
  }

  /**
   * Get cache statistics
   *
   * @returns Cache statistics object
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Get all cache keys
   *
   * @returns Array of cache keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache entry metadata
   *
   * @param key - Cache key
   * @returns Entry metadata or null
   */
  getMetadata(key: string): Record<string, any> | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    return {
      timestamp: entry.timestamp,
      accessCount: entry.accessCount,
      lastAccessed: entry.lastAccessed,
      ttl: entry.ttl,
      size: entry.size,
      age: Date.now() - entry.timestamp,
      ...entry.metadata,
    };
  }

  /**
   * Clean expired entries
   *
   * @returns Number of entries removed
   */
  cleanExpired(): number {
    let removed = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (this.isExpired(entry)) {
        this.cache.delete(key);
        this.stats.totalSize -= entry.size;
        this.stats.totalEntries--;
        removed++;
      }
    }

    return removed;
  }

  /**
   * Persist cache to disk
   *
   * @param path - File path (optional, uses config path by default)
   */
  async persist(path?: string): Promise<void> {
    if (!this.config.enablePersistence) {
      return;
    }

    const persistPath = path || this.config.persistPath;

    try {
      // Ensure directory exists
      await fs.mkdir(require('path').dirname(persistPath), { recursive: true });

      // Serialize cache
      const data = {
        version: '1.0',
        timestamp: Date.now(),
        stats: this.stats,
        entries: Array.from(this.cache.entries()).map(([, entry]) => ({
          ...entry,
        })),
      };

      // Write to file
      await fs.writeFile(persistPath, JSON.stringify(data, null, 2), 'utf-8');
    } catch (error: any) {
      console.error(`Failed to persist cache: ${error.message}`);
    }
  }

  /**
   * Load cache from disk
   *
   * @param path - File path (optional, uses config path by default)
   */
  async load(path?: string): Promise<void> {
    if (!this.config.enablePersistence) {
      return;
    }

    const persistPath = path || this.config.persistPath;

    try {
      const data = JSON.parse(await fs.readFile(persistPath, 'utf-8'));

      if (!data.version || !data.entries) {
        throw new Error('Invalid cache format');
      }

      // Clear existing cache
      this.clear();

      // Load entries
      for (const entryData of data.entries) {
        const entry: CacheEntry<T> = {
          key: entryData.key,
          data: entryData.data,
          timestamp: entryData.timestamp,
          accessCount: entryData.accessCount,
          lastAccessed: entryData.lastAccessed,
          ttl: entryData.ttl,
          size: entryData.size,
          metadata: entryData.metadata,
        };

        // Skip expired entries
        if (!this.isExpired(entry)) {
          this.cache.set(entry.key, entry);
          this.stats.totalSize += entry.size;
          this.stats.totalEntries++;
        }
      }

      // Restore stats
      if (data.stats) {
        this.stats.hits = data.stats.hits || 0;
        this.stats.misses = data.stats.misses || 0;
        this.stats.evictions = data.stats.evictions || 0;
        this.updateHitRate();
      }
    } catch (error: any) {
      // File doesn't exist or invalid - start with empty cache
      console.error(`Failed to load cache: ${error.message}`);
    }
  }

  /**
   * Check if an entry is expired
   *
   * @private
   */
  private isExpired(entry: CacheEntry<T>): boolean {
    if (!entry.ttl) return false;

    const age = (Date.now() - entry.timestamp) / 1000; // Age in seconds
    return age > entry.ttl;
  }

  /**
   * Evict entries if needed to make room
   *
   * @private
   */
  private evictIfNeeded(newEntrySize: number): void {
    // Check if we need to evict by size
    while (
      this.cache.size > 0 &&
      (this.stats.totalSize + newEntrySize > this.config.maxSize ||
        this.stats.totalEntries >= this.config.maxEntries)
    ) {
      this.evictLRU();
    }
  }

  /**
   * Evict least recently used entry
   *
   * @private
   */
  private evictLRU(): void {
    let lruKey: string | null = null;
    let lruTime = Infinity;

    // Find least recently used entry
    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < lruTime) {
        lruTime = entry.lastAccessed;
        lruKey = key;
      }
    }

    // Evict entry
    if (lruKey) {
      const entry = this.cache.get(lruKey)!;
      this.cache.delete(lruKey);
      this.stats.totalSize -= entry.size;
      this.stats.totalEntries--;
      this.stats.evictions++;
    }
  }

  /**
   * Calculate size of data in bytes
   *
   * @private
   */
  private calculateSize(data: any): number {
    const json = JSON.stringify(data);
    return Buffer.byteLength(json, 'utf-8');
  }

  /**
   * Update hit rate statistic
   *
   * @private
   */
  private updateHitRate(): void {
    const total = this.stats.hits + this.stats.misses;
    this.stats.hitRate = total > 0 ? this.stats.hits / total : 0;
  }
}

/**
 * Specialized cache for phylogenetic trees
 */
export class PhylogeneticTreeCache extends ResultCache<any> {
  /**
   * Cache a phylogenetic tree with alignment-based key
   *
   * @param alignment - Alignment data (will be hashed for key)
   * @param tree - Phylogenetic tree result
   * @param method - Tree construction method
   * @param ttl - Time to live in seconds
   */
  cacheTree(
    alignment: string,
    tree: any,
    method: string,
    ttl: number = 7200
  ): void {
    const key = this.generateKey({ alignment, method });
    this.set(key, tree, ttl, { method, type: 'phylogenetic_tree' });
  }

  /**
   * Get cached phylogenetic tree
   *
   * @param alignment - Alignment data
   * @param method - Tree construction method
   * @returns Cached tree or null
   */
  getTree(alignment: string, method: string): any | null {
    const key = this.generateKey({ alignment, method });
    return this.get(key);
  }
}

/**
 * Specialized cache for alignment results
 */
export class AlignmentCache extends ResultCache<string> {
  /**
   * Cache an alignment with sequence-based key
   *
   * @param sequences - Input sequences (will be hashed for key)
   * @param alignment - Alignment result
   * @param algorithm - Alignment algorithm used
   * @param params - Algorithm parameters
   * @param ttl - Time to live in seconds
   */
  cacheAlignment(
    sequences: string,
    alignment: string,
    algorithm: string,
    params: Record<string, any> = {},
    ttl: number = 3600
  ): void {
    const key = this.generateKey({ sequences, algorithm, params });
    this.set(key, alignment, ttl, { algorithm, params, type: 'alignment' });
  }

  /**
   * Get cached alignment
   *
   * @param sequences - Input sequences
   * @param algorithm - Alignment algorithm
   * @param params - Algorithm parameters
   * @returns Cached alignment or null
   */
  getAlignment(
    sequences: string,
    algorithm: string,
    params: Record<string, any> = {}
  ): string | null {
    const key = this.generateKey({ sequences, algorithm, params });
    return this.get(key);
  }
}

/**
 * Create singleton cache instances
 */
let defaultCache: ResultCache | null = null;
let phyloCache: PhylogeneticTreeCache | null = null;
let alignCache: AlignmentCache | null = null;

export function getDefaultCache(): ResultCache {
  if (!defaultCache) {
    defaultCache = new ResultCache();
  }
  return defaultCache;
}

export function getPhylogeneticTreeCache(): PhylogeneticTreeCache {
  if (!phyloCache) {
    phyloCache = new PhylogeneticTreeCache({
      maxSize: 200 * 1024 * 1024, // 200MB for trees
      defaultTTL: 7200, // 2 hours
      persistPath: '/workspace/cache/phylo-cache.json',
    });
  }
  return phyloCache;
}

export function getAlignmentCache(): AlignmentCache {
  if (!alignCache) {
    alignCache = new AlignmentCache({
      maxSize: 500 * 1024 * 1024, // 500MB for alignments
      defaultTTL: 3600, // 1 hour
      persistPath: '/workspace/cache/alignment-cache.json',
    });
  }
  return alignCache;
}
