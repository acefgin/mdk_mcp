/**
 * TypeScript type definitions for database server tools
 * 
 * @module database/types
 * @version 1.1.0
 * 
 * Usage:
 * ```typescript
 * import type { SequenceFilters, GetSequencesInput } from './servers/database/types';
 * ```
 */

/**
 * Advanced filtering options for sequence retrieval
 * 
 * These filters allow precise control over sequence retrieval from biological databases.
 * Filters are applied either server-side (NCBI) or post-retrieval (other sources).
 * 
 * @see FILTERING_GUIDE.md for detailed usage examples
 */
export interface SequenceFilters {
  /**
   * Minimum sequence length in base pairs
   * 
   * @example
   * ```typescript
   * min_length: 600  // For standard COI barcodes
   * min_length: 1400 // For full-length 16S rRNA
   * min_length: 15000 // For complete mitochondrial genomes
   * ```
   */
  min_length?: number;

  /**
   * Maximum sequence length in base pairs
   * 
   * @example
   * ```typescript
   * max_length: 700   // For standard COI barcodes
   * max_length: 2000  // For extended sequences
   * max_length: 20000 // Upper bound for mitogenomes
   * ```
   */
  max_length?: number;

  /**
   * Sequence completeness level
   * 
   * - `complete`: Only complete genomes/genes/sequences
   * - `partial`: Only partial sequences
   * - `any`: No filtering (default)
   * 
   * @example
   * ```typescript
   * completeness: "complete" // Only complete sequences
   * completeness: "partial"  // Only partial sequences
   * completeness: "any"      // All sequences
   * ```
   */
  completeness?: "complete" | "partial" | "any";

  /**
   * Start date for upload/submission
   * 
   * Format: YYYY-MM-DD or YYYY/MM/DD
   * 
   * @example
   * ```typescript
   * upload_date_start: "2020-01-01" // Sequences from 2020 onwards
   * upload_date_start: "2023/06/15" // Alternative format
   * ```
   */
  upload_date_start?: string;

  /**
   * End date for upload/submission
   * 
   * Format: YYYY-MM-DD or YYYY/MM/DD
   * 
   * @example
   * ```typescript
   * upload_date_end: "2024-12-31" // Sequences until end of 2024
   * upload_date_end: "2024/11/14" // Alternative format
   * ```
   */
  upload_date_end?: string;

  /**
   * Filter by country or geographic location
   * 
   * Case-insensitive partial match against country field
   * 
   * @example
   * ```typescript
   * country: "Norway"
   * country: "USA"
   * country: "Japan"
   * country: "Atlantic" // Matches Atlantic Ocean samples
   * ```
   */
  country?: string;

  /**
   * Only include sequences with geographic location data
   * 
   * When true, filters out sequences lacking location metadata
   * 
   * @example
   * ```typescript
   * has_geo_location: true  // Require location data
   * has_geo_location: false // No filtering
   * ```
   */
  has_geo_location?: boolean;

  /**
   * Sequence quality threshold
   * 
   * - `high`: RefSeq or reviewed sequences only (highest quality)
   * - `medium`: Exclude predicted/unverified sequences
   * - `any`: No quality filtering (default)
   * 
   * @example
   * ```typescript
   * quality_filter: "high"   // RefSeq only
   * quality_filter: "medium" // Exclude predicted
   * quality_filter: "any"    // All sequences
   * ```
   */
  quality_filter?: "high" | "medium" | "any";

  /**
   * Exclude predicted or inferred sequences
   * 
   * Removes sequences marked as predicted, model, or hypothetical
   * 
   * @example
   * ```typescript
   * exclude_predicted: true  // Remove predicted sequences
   * exclude_predicted: false // Keep all sequences
   * ```
   */
  exclude_predicted?: boolean;

  /**
   * Exclude environmental or uncultured samples
   * 
   * Removes sequences from environmental DNA or uncultured organisms
   * 
   * @example
   * ```typescript
   * exclude_environmental: true  // Remove environmental samples
   * exclude_environmental: false // Keep all samples
   * ```
   */
  exclude_environmental?: boolean;
}

/**
 * Input parameters for get_sequences tool
 */
export interface GetSequencesInput {
  /**
   * Taxon name or taxonomic ID
   * 
   * @example
   * ```typescript
   * taxon: "Salmo salar"      // Scientific name
   * taxon: "Salmonidae"       // Family name
   * taxon: "Actinopterygii"   // Class name
   * taxon: "8030"             // NCBI Taxonomy ID
   * ```
   */
  taxon: string;

  /**
   * Genomic region to retrieve
   * 
   * - `COI`: Cytochrome oxidase I (barcode region)
   * - `16S`: 16S ribosomal RNA
   * - `ITS`: Internal transcribed spacer
   * - `mitogenome`: Complete mitochondrial genome
   * - `whole`: Whole genome
   * 
   * @default "COI"
   */
  region?: "COI" | "16S" | "ITS" | "mitogenome" | "whole";

  /**
   * Database source
   * 
   * - `gget`: Ensembl via gget
   * - `ncbi`: NCBI Nucleotide database (best filter support)
   * - `bold`: BOLD Systems (COI barcodes)
   * - `silva`: SILVA rRNA database
   * - `unite`: UNITE fungal ITS database
   * 
   * @default "gget"
   */
  source?: "gget" | "ncbi" | "bold" | "silva" | "unite";

  /**
   * Maximum number of sequences to return
   * 
   * @default 100
   * @maximum 10000
   */
  max_results?: number;

  /**
   * Output format
   * 
   * - `fasta`: FASTA format (sequence + header)
   * - `genbank`: GenBank format (full metadata)
   * 
   * @default "fasta"
   */
  format?: "fasta" | "genbank";

  /**
   * Advanced filtering options
   * 
   * See {@link SequenceFilters} for detailed documentation
   * 
   * @example
   * ```typescript
   * filters: {
   *   min_length: 600,
   *   max_length: 700,
   *   completeness: "complete",
   *   country: "Norway",
   *   quality_filter: "high"
   * }
   * ```
   */
  filters?: SequenceFilters;
}

/**
 * Filter support by database source
 * 
 * Indicates which filters are supported natively vs post-retrieval
 */
export interface FilterSupport {
  /** Database source name */
  source: "ncbi" | "bold" | "gget" | "silva" | "unite";
  /** Length filters supported */
  length: "server" | "post" | "none";
  /** Completeness filter supported */
  completeness: "server" | "post" | "none";
  /** Date filters supported */
  dates: "server" | "post" | "none";
  /** Geographic filters supported */
  geography: "server" | "post" | "none";
  /** Quality filters supported */
  quality: "server" | "post" | "none";
}

/**
 * Filter support matrix for all database sources
 */
export const FILTER_SUPPORT: FilterSupport[] = [
  {
    source: "ncbi",
    length: "server",
    completeness: "server",
    dates: "server",
    geography: "server",
    quality: "server",
  },
  {
    source: "bold",
    length: "post",
    completeness: "post",
    dates: "none",
    geography: "server",
    quality: "post",
  },
  {
    source: "gget",
    length: "post",
    completeness: "post",
    dates: "none",
    geography: "none",
    quality: "post",
  },
  {
    source: "silva",
    length: "none",
    completeness: "none",
    dates: "none",
    geography: "none",
    quality: "none",
  },
  {
    source: "unite",
    length: "none",
    completeness: "none",
    dates: "none",
    geography: "none",
    quality: "none",
  },
];

/**
 * Common sequence length ranges for different genomic regions
 */
export const SEQUENCE_LENGTH_RANGES = {
  /** Standard COI barcode region */
  COI: { min: 600, max: 700, typical: 658 },
  /** Full-length 16S rRNA */
  "16S": { min: 1400, max: 1550, typical: 1500 },
  /** Full-length 18S rRNA */
  "18S": { min: 1700, max: 1900, typical: 1800 },
  /** ITS region (highly variable) */
  ITS: { min: 200, max: 800, typical: 500 },
  /** Mitochondrial genomes (vertebrates) */
  mitogenome: { min: 15000, max: 20000, typical: 16500 },
} as const;

/**
 * Quality level descriptions
 */
export const QUALITY_LEVELS = {
  high: "RefSeq or reviewed sequences (highest quality)",
  medium: "Exclude predicted/unverified sequences",
  any: "No quality filtering (default)",
} as const;

/**
 * Type guard to check if filters are provided
 */
export function hasFilters(
  input: GetSequencesInput
): input is GetSequencesInput & { filters: SequenceFilters } {
  return input.filters !== undefined && Object.keys(input.filters).length > 0;
}

/**
 * Validate filter values
 * 
 * @throws Error if filter values are invalid
 */
export function validateFilters(filters: SequenceFilters): void {
  if (filters.min_length !== undefined && filters.min_length < 0) {
    throw new Error("min_length must be non-negative");
  }

  if (filters.max_length !== undefined && filters.max_length < 0) {
    throw new Error("max_length must be non-negative");
  }

  if (
    filters.min_length !== undefined &&
    filters.max_length !== undefined &&
    filters.min_length > filters.max_length
  ) {
    throw new Error("min_length cannot be greater than max_length");
  }

  if (filters.upload_date_start && !isValidDate(filters.upload_date_start)) {
    throw new Error(
      "upload_date_start must be in YYYY-MM-DD or YYYY/MM/DD format"
    );
  }

  if (filters.upload_date_end && !isValidDate(filters.upload_date_end)) {
    throw new Error(
      "upload_date_end must be in YYYY-MM-DD or YYYY/MM/DD format"
    );
  }
}

/**
 * Check if date string is valid
 */
function isValidDate(dateStr: string): boolean {
  const patterns = [
    /^\d{4}-\d{2}-\d{2}$/, // YYYY-MM-DD
    /^\d{4}\/\d{2}\/\d{2}$/, // YYYY/MM/DD
  ];

  if (!patterns.some((pattern) => pattern.test(dateStr))) {
    return false;
  }

  const date = new Date(dateStr.replace(/\//g, "-"));
  return !isNaN(date.getTime());
}

