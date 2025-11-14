/**
 * Type definitions for Code Execution Sandbox
 * 
 * These types provide IntelliSense and type checking for code
 * executed in the sandbox environment.
 * 
 * @module sandbox
 * @version 1.0.0
 * 
 * Usage:
 * ```typescript
 * /// <reference path="/workspace/types/sandbox.d.ts" />
 * 
 * // Now you get full type checking!
 * const sequences = await database.getSequences({
 *   taxon: "Salmo salar",
 *   region: "COI"
 * });
 * ```
 */

// =============================================================================
// DATABASE MODULE
// =============================================================================

declare const database: {
  /**
   * Retrieve DNA sequences from the database
   * @param args Query parameters
   * @returns FASTA-formatted sequences
   */
  getSequences(args: {
    taxon: string;
    region: string;
    max_results?: number;
    include_metadata?: boolean;
  }): Promise<string>;

  /**
   * Get reference genome information using gget
   * @param args Species and reference type
   * @returns Reference genome data
   */
  ggetRef(args: {
    species: string;
    which?: 'vertebrate' | 'all';
    release?: number;
  }): Promise<string>;

  /**
   * Search genomic databases using gget
   * @param args Search parameters
   * @returns Search results
   */
  ggetSearch(args: {
    searchwords: string[];
    species?: string;
    limit?: number;
  }): Promise<string>;

  /**
   * Extract specific columns from sequence data
   * @param args Column extraction parameters
   * @returns Extracted column data
   */
  extractSequenceColumns(args: {
    data: string;
    columns: string[];
    format?: 'csv' | 'tsv' | 'json';
  }): Promise<string>;
};

// =============================================================================
// PROCESSING MODULE
// =============================================================================

declare const processing: {
  /**
   * Perform quality control on FASTA sequences
   * @param args QC parameters
   * @returns QC report
   */
  fastaQc(args: {
    fasta_content: string;
    min_length?: number;
    max_length?: number;
    max_n_percent?: number;
  }): Promise<string>;

  /**
   * Filter sequences based on criteria
   * @param args Filter parameters
   * @returns Filtered FASTA
   */
  filterSequences(args: {
    fasta_content: string;
    min_length?: number;
    max_length?: number;
    min_gc?: number;
    max_gc?: number;
  }): Promise<string>;

  /**
   * Convert between sequence formats
   * @param args Conversion parameters
   * @returns Converted sequences
   */
  convertFormat(args: {
    input_content: string;
    input_format: 'fasta' | 'genbank' | 'fastq';
    output_format: 'fasta' | 'genbank' | 'fastq';
  }): Promise<string>;
};

// =============================================================================
// ALIGNMENT MODULE
// =============================================================================

declare const alignment: {
  /**
   * Perform multiple sequence alignment
   * @param args Alignment parameters
   * @returns Aligned sequences in FASTA format
   */
  alignSequences(args: {
    fasta_content: string;
    algorithm: 'mafft' | 'muscle' | 'clustalo';
    strategy?: 'auto' | 'fast' | 'accurate';
    threads?: number;
  }): Promise<string>;

  /**
   * Clean and process alignments using CIAlign
   * @param args Processing parameters
   * @returns Cleaned alignment
   */
  processAlignment(args: {
    alignment_content: string;
    remove_divergent?: boolean;
    remove_insertions?: boolean;
    crop_ends?: boolean;
  }): Promise<string>;

  /**
   * Build phylogenetic tree
   * @param args Tree building parameters
   * @returns Newick format tree
   */
  buildTree(args: {
    alignment_content: string;
    method: 'nj' | 'ml' | 'mp';
    bootstrap?: number;
  }): Promise<string>;

  /**
   * Calculate pairwise identity matrix
   * @param args Identity calculation parameters
   * @returns Identity matrix
   */
  calculateIdentity(args: {
    alignment_content: string;
    format?: 'matrix' | 'pairwise';
  }): Promise<string>;
};

// =============================================================================
// DESIGN MODULE
// =============================================================================

declare const design: {
  /**
   * Design primers using Primer3
   * @param args Primer design parameters
   * @returns Primer pairs with properties
   */
  primer3Design(args: {
    sequence: string;
    primer_size?: number;
    primer_min_size?: number;
    primer_max_size?: number;
    primer_min_tm?: number;
    primer_max_tm?: number;
    primer_opt_tm?: number;
    product_size?: [number, number];
    num_return?: number;
  }): Promise<{
    forward: string;
    reverse: string;
    tm: { forward: number; reverse: number };
    gc: { forward: number; reverse: number };
    product_size: number;
  }>;

  /**
   * Find signature regions for taxon-specific primers
   * @param args Signature region parameters
   * @returns Candidate signature regions
   */
  findSignatureRegions(args: {
    target_alignment: string;
    offtarget_sequences: string;
    window_size?: number;
    step_size?: number;
    min_conservation?: number;
    min_specificity?: number;
  }): Promise<Array<{
    position: number;
    sequence: string;
    conservation: number;
    specificity: number;
  }>>;

  /**
   * Design qPCR assay (primers + probe)
   * @param args qPCR design parameters
   * @returns Complete qPCR assay
   */
  designQpcrAssay(args: {
    sequence: string;
    amplicon_size?: [number, number];
    probe_required?: boolean;
  }): Promise<{
    forward_primer: string;
    reverse_primer: string;
    probe?: string;
    amplicon_size: number;
    tm: { forward: number; reverse: number; probe?: number };
  }>;
};

// =============================================================================
// VALIDATION MODULE
// =============================================================================

declare const validation: {
  /**
   * BLAST sequences using gget
   * @param args BLAST parameters
   * @returns BLAST results
   */
  ggetBlast(args: {
    sequence: string;
    database?: 'nt' | 'nr' | 'refseq_rna';
    limit?: number;
    expect_threshold?: number;
  }): Promise<string>;

  /**
   * Validate primer properties (Tm, GC, dimers)
   * @param args Primer validation parameters
   * @returns Validation report
   */
  validatePrimers(args: {
    forward_primer: string;
    reverse_primer: string;
    probe?: string;
  }): Promise<{
    tm: { forward: number; reverse: number; probe?: number };
    gc: { forward: number; reverse: number; probe?: number };
    dimers: {
      self_dimer: boolean;
      hetero_dimer: boolean;
      hairpin: boolean;
    };
    issues: string[];
  }>;

  /**
   * Complete primer validation (properties + specificity)
   * @param args Complete validation parameters
   * @returns Comprehensive validation report
   */
  validatePrimersComplete(args: {
    forward_primer: string;
    reverse_primer: string;
    target_taxon: string;
    probe?: string;
  }): Promise<{
    properties: any;
    blast: {
      hits: number;
      target_hits: number;
      offtarget_hits: number;
    };
    specificity: number;
    sensitivity: number;
    recommendation: 'pass' | 'warning' | 'fail';
  }>;
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Parse FASTA and return statistics instead of full sequences
 * @param fasta FASTA-formatted sequences
 * @returns Sequence statistics
 */
declare function parseFastaStats(fasta: string): {
  count: number;
  totalLength: number;
  averageLength: number;
  minLength: number;
  maxLength: number;
  gcContent: number;
  nContent: number;
};

/**
 * Filter sequences and save to file
 * @param fasta FASTA sequences
 * @param filterFn Filter function
 * @param filepath Output file path
 * @returns File metadata
 */
declare function filterAndSave(
  fasta: string,
  filterFn: (sequence: string, header: string) => boolean,
  filepath: string
): Promise<{
  path: string;
  size: number;
  lines: number;
  hash: string;
  created: string;
}>;

/**
 * Extract specific fields from FASTA headers
 * @param fasta FASTA sequences
 * @param fields Fields to extract
 * @returns Array of extracted values
 */
declare function extractFields(
  fasta: string,
  fields: string[]
): string[];

/**
 * Summarize alignment quality
 * @param alignment Aligned sequences
 * @returns Alignment summary
 */
declare function summarizeAlignment(alignment: string): {
  sequences: number;
  length: number;
  gapPercentage: number;
  conservationScore: number;
  identityMatrix: number[][];
};

/**
 * Process large datasets in batches
 * @param items Array of items to process
 * @param processFn Processing function for each batch
 * @param batchSize Number of items per batch
 * @returns Batch processing result
 */
declare function batchProcess<T, R>(
  items: T[],
  processFn: (batch: T[]) => Promise<R>,
  batchSize: number
): Promise<{
  total: number;
  processed: number;
  failed: number;
  results: R[];
}>;

/**
 * Cache result with TTL
 * @param key Cache key
 * @param value Value to cache
 * @param ttlSeconds Time to live in seconds
 */
declare function cacheResult(
  key: string,
  value: any,
  ttlSeconds: number
): Promise<void>;

/**
 * Get cached result
 * @param key Cache key
 * @returns Cached value or null
 */
declare function getCachedResult<T>(key: string): Promise<T | null>;

/**
 * Save data to file and return metadata
 * @param data Data to save
 * @param filename Output filename
 * @param options Save options
 * @returns File metadata
 */
declare function saveToFile(
  data: string,
  filename: string,
  options?: {
    ttlSeconds?: number;
    compress?: boolean;
    tags?: string[];
  }
): Promise<{
  path: string;
  size: number;
  hash: string;
  created: string;
  expiresAt?: string;
  compressed?: boolean;
  tags?: string[];
}>;

/**
 * Format bytes to human-readable string
 * @param bytes Byte count
 * @returns Formatted string (e.g., "2.5 MB")
 */
declare function formatBytes(bytes: number): string;

/**
 * Truncate string for context window
 * @param str String to truncate
 * @param maxBytes Maximum bytes
 * @returns Truncated string
 */
declare function truncateForContext(str: string, maxBytes: number): string;

/**
 * Clean up old files
 * @param directory Directory to clean
 * @param options Cleanup options
 */
declare function cleanupFiles(
  directory: string,
  options: {
    olderThanDays?: number;
    tags?: string[];
    keepNewestGB?: number;
  }
): Promise<{
  filesDeleted: number;
  bytesFreed: number;
}>;

// =============================================================================
// NODE.JS MODULES (WHITELISTED)
// =============================================================================

/**
 * File system module (limited operations)
 */
declare const fs: {
  readFile(path: string, encoding: string): Promise<string>;
  writeFile(path: string, data: string): Promise<void>;
  readdir(path: string): Promise<string[]>;
  stat(path: string): Promise<{ size: number; mtime: Date }>;
  unlink(path: string): Promise<void>;
  mkdir(path: string, options?: { recursive: boolean }): Promise<void>;
};

/**
 * Path utilities
 */
declare const path: {
  join(...paths: string[]): string;
  basename(path: string): string;
  dirname(path: string): string;
  extname(path: string): string;
  resolve(...paths: string[]): string;
};

/**
 * Crypto utilities
 */
declare const crypto: {
  createHash(algorithm: string): {
    update(data: string): { digest(encoding: string): string };
  };
  randomUUID(): string;
};

// =============================================================================
// CONSOLE (ALWAYS AVAILABLE)
// =============================================================================

declare const console: {
  log(...args: any[]): void;
  error(...args: any[]): void;
  warn(...args: any[]): void;
  info(...args: any[]): void;
  debug(...args: any[]): void;
};

