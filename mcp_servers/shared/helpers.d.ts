/**
 * Helper Utilities for Context-Efficient Operations
 *
 * These utilities enable data processing within the execution environment
 * to keep large datasets out of the context window.
 *
 * Key Principles:
 * 1. Process data in-code, not through the model
 * 2. Return only summaries and statistics
 * 3. Use file system for large intermediate results
 * 4. Filter and transform before returning to context
 */
/**
 * FASTA sequence statistics
 */
export interface SequenceStats {
    count: number;
    totalLength: number;
    averageLength: number;
    minLength: number;
    maxLength: number;
    gcContent: number;
    nContent: number;
}
/**
 * File metadata
 */
export interface FileMetadata {
    path: string;
    size: number;
    lines: number;
    hash: string;
    created: Date;
}
/**
 * Parse FASTA content and return statistics (not the full sequences)
 *
 * @param fastaContent - FASTA format sequences
 * @returns Statistics summary
 *
 * @example
 * const sequences = await db.getSequences({ taxon: "Salmo salar", region: "COI" });
 * const stats = parseFastaStats(sequences);
 * // Returns: { count: 100, averageLength: 658, ... }
 * // Context usage: ~200 tokens instead of ~50,000 tokens
 */
export declare function parseFastaStats(fastaContent: string): SequenceStats;
/**
 * Filter FASTA sequences and save to file (keeps data out of context)
 *
 * @param fastaContent - FASTA format sequences
 * @param filter - Filter function
 * @param outputPath - Output file path
 * @returns Metadata about the filtered file
 *
 * @example
 * const sequences = await db.getSequences({ taxon: "Salmo salar", region: "COI" });
 * const metadata = await filterAndSave(
 *   sequences,
 *   seq => seq.length > 500 && seq.length < 800,
 *   '/workspace/data/filtered_sequences.fasta'
 * );
 * // Returns: { path: '...', size: 45123, lines: 200, ... }
 * // Context usage: ~150 tokens instead of ~30,000 tokens
 */
export declare function filterAndSave(fastaContent: string, filter: (sequence: string, header: string) => boolean, outputPath: string): Promise<FileMetadata>;
/**
 * Extract specific fields from FASTA headers
 *
 * @param fastaContent - FASTA format sequences
 * @param fields - Fields to extract (e.g., ['accession', 'organism'])
 * @returns Array of extracted field values
 *
 * @example
 * const sequences = await db.getSequences({ taxon: "Salmo salar", region: "COI" });
 * const accessions = extractFields(sequences, ['accession']);
 * // Returns: ['MT123456', 'MT123457', ...]
 * // Context usage: ~500 tokens instead of ~50,000 tokens
 */
export declare function extractFields(fastaContent: string, fields: string[]): Record<string, string>[];
/**
 * Summarize alignment quality metrics
 *
 * @param alignmentContent - Aligned sequences in FASTA format
 * @returns Quality metrics summary
 */
export declare function summarizeAlignment(alignmentContent: string): {
    sequences: number;
    length: number;
    gapPercentage: number;
    conservationScore: number;
    identityMatrix: number[][];
};
/**
 * Batch process sequences and return progress summary
 *
 * @param sequences - Array of sequences to process
 * @param processor - Processing function
 * @param batchSize - Number of sequences per batch
 * @returns Processing summary
 */
export declare function batchProcess<T, R>(sequences: T[], processor: (batch: T[]) => Promise<R[]>, batchSize?: number): Promise<{
    total: number;
    batches: number;
    processed: number;
    failed: number;
    results: R[];
}>;
/**
 * Cache result to file system
 *
 * @param key - Cache key
 * @param data - Data to cache
 * @param ttl - Time to live in seconds (optional)
 */
export declare function cacheResult(key: string, data: any, ttl?: number): Promise<string>;
/**
 * Retrieve cached result
 *
 * @param key - Cache key
 * @returns Cached data or null if not found/expired
 */
export declare function getCachedResult<T = any>(key: string): Promise<T | null>;
/**
 * Save large data to file and return metadata
 *
 * @param data - Data to save
 * @param filename - Output filename
 * @returns File metadata
 */
export declare function saveToFile(data: string, filename: string): Promise<FileMetadata>;
/**
 * Format bytes to human readable string
 */
export declare function formatBytes(bytes: number): string;
/**
 * Truncate large strings for context efficiency
 */
export declare function truncateForContext(data: string, maxLength?: number, showPreview?: boolean): string | {
    truncated: true;
    preview: string;
    size: number;
};
//# sourceMappingURL=helpers.d.ts.map