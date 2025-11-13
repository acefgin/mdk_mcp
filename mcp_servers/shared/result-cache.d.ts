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
    maxSize?: number;
    maxEntries?: number;
    defaultTTL?: number;
    persistPath?: string;
    enablePersistence?: boolean;
}
/**
 * Result Cache Manager
 *
 * Provides efficient caching for bioinformatics results with SHA256-based
 * content-addressable storage.
 */
export declare class ResultCache<T = any> {
    private cache;
    private stats;
    private config;
    constructor(config?: CacheConfig);
    /**
     * Generate SHA256 cache key from data
     *
     * @param data - Data to generate key from (will be stringified)
     * @returns SHA256 hash as hex string
     *
     * @example
     * const key = cache.generateKey({ taxon: 'Salmo salar', region: 'COI' });
     */
    generateKey(data: any): string;
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
    set(key: string, data: T, ttl?: number, metadata?: Record<string, any>): void;
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
    get(key: string): T | null;
    /**
     * Check if a key exists in cache
     *
     * @param key - Cache key
     * @returns True if key exists and not expired
     */
    has(key: string): boolean;
    /**
     * Delete a cache entry
     *
     * @param key - Cache key
     * @returns True if entry was deleted
     */
    delete(key: string): boolean;
    /**
     * Clear all cache entries
     */
    clear(): void;
    /**
     * Get cache statistics
     *
     * @returns Cache statistics object
     */
    getStats(): CacheStats;
    /**
     * Get all cache keys
     *
     * @returns Array of cache keys
     */
    keys(): string[];
    /**
     * Get cache entry metadata
     *
     * @param key - Cache key
     * @returns Entry metadata or null
     */
    getMetadata(key: string): Record<string, any> | null;
    /**
     * Clean expired entries
     *
     * @returns Number of entries removed
     */
    cleanExpired(): number;
    /**
     * Persist cache to disk
     *
     * @param path - File path (optional, uses config path by default)
     */
    persist(path?: string): Promise<void>;
    /**
     * Load cache from disk
     *
     * @param path - File path (optional, uses config path by default)
     */
    load(path?: string): Promise<void>;
    /**
     * Check if an entry is expired
     *
     * @private
     */
    private isExpired;
    /**
     * Evict entries if needed to make room
     *
     * @private
     */
    private evictIfNeeded;
    /**
     * Evict least recently used entry
     *
     * @private
     */
    private evictLRU;
    /**
     * Calculate size of data in bytes
     *
     * @private
     */
    private calculateSize;
    /**
     * Update hit rate statistic
     *
     * @private
     */
    private updateHitRate;
}
/**
 * Specialized cache for phylogenetic trees
 */
export declare class PhylogeneticTreeCache extends ResultCache<any> {
    /**
     * Cache a phylogenetic tree with alignment-based key
     *
     * @param alignment - Alignment data (will be hashed for key)
     * @param tree - Phylogenetic tree result
     * @param method - Tree construction method
     * @param ttl - Time to live in seconds
     */
    cacheTree(alignment: string, tree: any, method: string, ttl?: number): void;
    /**
     * Get cached phylogenetic tree
     *
     * @param alignment - Alignment data
     * @param method - Tree construction method
     * @returns Cached tree or null
     */
    getTree(alignment: string, method: string): any | null;
}
/**
 * Specialized cache for alignment results
 */
export declare class AlignmentCache extends ResultCache<string> {
    /**
     * Cache an alignment with sequence-based key
     *
     * @param sequences - Input sequences (will be hashed for key)
     * @param alignment - Alignment result
     * @param algorithm - Alignment algorithm used
     * @param params - Algorithm parameters
     * @param ttl - Time to live in seconds
     */
    cacheAlignment(sequences: string, alignment: string, algorithm: string, params?: Record<string, any>, ttl?: number): void;
    /**
     * Get cached alignment
     *
     * @param sequences - Input sequences
     * @param algorithm - Alignment algorithm
     * @param params - Algorithm parameters
     * @returns Cached alignment or null
     */
    getAlignment(sequences: string, algorithm: string, params?: Record<string, any>): string | null;
}
export declare function getDefaultCache(): ResultCache;
export declare function getPhylogeneticTreeCache(): PhylogeneticTreeCache;
export declare function getAlignmentCache(): AlignmentCache;
//# sourceMappingURL=result-cache.d.ts.map