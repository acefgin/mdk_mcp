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
import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';
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
export function parseFastaStats(fastaContent) {
    const entries = fastaContent
        .split(/\n>/)
        .map(entry => entry.trim())
        .filter(entry => entry.length > 0);
    if (entries.length === 0) {
        return {
            count: 0,
            totalLength: 0,
            averageLength: 0,
            minLength: 0,
            maxLength: 0,
            gcContent: 0,
            nContent: 0,
        };
    }
    let totalLength = 0;
    let minLength = Infinity;
    let maxLength = 0;
    let totalGC = 0;
    let totalN = 0;
    let totalBases = 0;
    for (const entry of entries) {
        // Skip the header line
        const lines = entry.split('\n');
        const sequence = lines.slice(1).join('').toUpperCase();
        const length = sequence.length;
        totalLength += length;
        minLength = Math.min(minLength, length);
        maxLength = Math.max(maxLength, length);
        // Count GC and N
        const gcCount = (sequence.match(/[GC]/g) || []).length;
        const nCount = (sequence.match(/N/g) || []).length;
        totalGC += gcCount;
        totalN += nCount;
        totalBases += length;
    }
    return {
        count: entries.length,
        totalLength,
        averageLength: totalLength / entries.length,
        minLength: minLength === Infinity ? 0 : minLength,
        maxLength,
        gcContent: totalBases > 0 ? (totalGC / totalBases) * 100 : 0,
        nContent: totalBases > 0 ? (totalN / totalBases) * 100 : 0,
    };
}
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
export async function filterAndSave(fastaContent, filter, outputPath) {
    const entries = fastaContent
        .split(/\n>/)
        .map((entry, idx) => {
        const trimmed = entry.trim();
        // Add back the '>' for non-first entries
        return idx === 0 ? trimmed : '>' + trimmed;
    })
        .filter(entry => entry.length > 0);
    let outputContent = '';
    let linesCount = 0;
    for (const entry of entries) {
        const lines = entry.split('\n');
        const header = lines[0].replace(/^>/, '');
        const sequence = lines.slice(1).join('').toUpperCase();
        if (filter(sequence, header)) {
            outputContent += `>${header}\n${sequence}\n`;
            linesCount += 2;
        }
    }
    // Ensure directory exists
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    // Write to file
    await fs.writeFile(outputPath, outputContent, 'utf-8');
    // Get file stats
    const stats = await fs.stat(outputPath);
    // Calculate hash
    const hash = crypto.createHash('sha256').update(outputContent).digest('hex');
    return {
        path: outputPath,
        size: stats.size,
        lines: linesCount,
        hash: hash.substring(0, 16),
        created: stats.birthtime,
    };
}
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
export function extractFields(fastaContent, fields) {
    const entries = fastaContent
        .split(/\n>/)
        .map(entry => entry.trim())
        .filter(entry => entry.length > 0);
    const results = [];
    for (const entry of entries) {
        const lines = entry.split('\n');
        const header = lines[0].replace(/^>/, '');
        const record = {};
        for (const field of fields) {
            // Try different header formats
            const patterns = [
                new RegExp(`${field}[=:]([^\\s|]+)`, 'i'),
                new RegExp(`\\|${field}\\|([^\\s|]+)`, 'i'),
                new RegExp(`\\[${field}=([^\\]]+)\\]`, 'i'),
            ];
            let value = '';
            for (const pattern of patterns) {
                const match = header.match(pattern);
                if (match) {
                    value = match[1];
                    break;
                }
            }
            record[field] = value;
        }
        results.push(record);
    }
    return results;
}
/**
 * Summarize alignment quality metrics
 *
 * @param alignmentContent - Aligned sequences in FASTA format
 * @returns Quality metrics summary
 */
export function summarizeAlignment(alignmentContent) {
    const entries = alignmentContent
        .split(/\n>/)
        .map(entry => entry.trim())
        .filter(entry => entry.length > 0);
    if (entries.length === 0) {
        return {
            sequences: 0,
            length: 0,
            gapPercentage: 0,
            conservationScore: 0,
            identityMatrix: [],
        };
    }
    // Extract sequences
    const sequences = entries.map(entry => {
        const lines = entry.split('\n');
        return lines.slice(1).join('').toUpperCase();
    });
    const alignmentLength = sequences[0].length;
    let totalGaps = 0;
    // Count gaps
    for (const seq of sequences) {
        totalGaps += (seq.match(/-/g) || []).length;
    }
    // Calculate conservation score
    let conservedPositions = 0;
    for (let i = 0; i < alignmentLength; i++) {
        const column = sequences.map(seq => seq[i]);
        const uniqueBases = new Set(column.filter(base => base !== '-'));
        if (uniqueBases.size === 1) {
            conservedPositions++;
        }
    }
    // Calculate pairwise identity matrix (sample for large sets)
    const sampleSize = Math.min(10, sequences.length);
    const identityMatrix = [];
    for (let i = 0; i < sampleSize; i++) {
        const row = [];
        for (let j = 0; j < sampleSize; j++) {
            if (i === j) {
                row.push(100);
            }
            else {
                const seq1 = sequences[i];
                const seq2 = sequences[j];
                let matches = 0;
                let compared = 0;
                for (let k = 0; k < alignmentLength; k++) {
                    if (seq1[k] !== '-' && seq2[k] !== '-') {
                        compared++;
                        if (seq1[k] === seq2[k]) {
                            matches++;
                        }
                    }
                }
                const identity = compared > 0 ? (matches / compared) * 100 : 0;
                row.push(Math.round(identity * 10) / 10);
            }
        }
        identityMatrix.push(row);
    }
    return {
        sequences: sequences.length,
        length: alignmentLength,
        gapPercentage: (totalGaps / (sequences.length * alignmentLength)) * 100,
        conservationScore: (conservedPositions / alignmentLength) * 100,
        identityMatrix,
    };
}
/**
 * Batch process sequences and return progress summary
 *
 * @param sequences - Array of sequences to process
 * @param processor - Processing function
 * @param batchSize - Number of sequences per batch
 * @returns Processing summary
 */
export async function batchProcess(sequences, processor, batchSize = 100) {
    const results = [];
    let processed = 0;
    let failed = 0;
    const batches = Math.ceil(sequences.length / batchSize);
    for (let i = 0; i < batches; i++) {
        const start = i * batchSize;
        const end = Math.min(start + batchSize, sequences.length);
        const batch = sequences.slice(start, end);
        try {
            const batchResults = await processor(batch);
            results.push(...batchResults);
            processed += batch.length;
        }
        catch (error) {
            console.error(`Batch ${i + 1} failed:`, error);
            failed += batch.length;
        }
    }
    return {
        total: sequences.length,
        batches,
        processed,
        failed,
        results,
    };
}
/**
 * Cache result to file system
 *
 * @param key - Cache key
 * @param data - Data to cache
 * @param ttl - Time to live in seconds (optional)
 */
export async function cacheResult(key, data, ttl) {
    const cacheDir = '/workspace/cache';
    await fs.mkdir(cacheDir, { recursive: true });
    const hash = crypto.createHash('sha256').update(key).digest('hex');
    const cachePath = path.join(cacheDir, `${hash}.json`);
    const cacheData = {
        key,
        data,
        created: Date.now(),
        ttl,
    };
    await fs.writeFile(cachePath, JSON.stringify(cacheData), 'utf-8');
    return cachePath;
}
/**
 * Retrieve cached result
 *
 * @param key - Cache key
 * @returns Cached data or null if not found/expired
 */
export async function getCachedResult(key) {
    const cacheDir = '/workspace/cache';
    const hash = crypto.createHash('sha256').update(key).digest('hex');
    const cachePath = path.join(cacheDir, `${hash}.json`);
    try {
        const content = await fs.readFile(cachePath, 'utf-8');
        const cacheData = JSON.parse(content);
        // Check TTL
        if (cacheData.ttl) {
            const age = (Date.now() - cacheData.created) / 1000;
            if (age > cacheData.ttl) {
                // Expired
                await fs.unlink(cachePath).catch(() => { });
                return null;
            }
        }
        return cacheData.data;
    }
    catch (error) {
        return null;
    }
}
/**
 * Save large data to file and return metadata
 *
 * @param data - Data to save
 * @param filename - Output filename
 * @returns File metadata
 */
export async function saveToFile(data, filename) {
    const outputPath = path.join('/workspace/data', filename);
    await fs.mkdir(path.dirname(outputPath), { recursive: true });
    await fs.writeFile(outputPath, data, 'utf-8');
    const stats = await fs.stat(outputPath);
    const lines = data.split('\n').length;
    const hash = crypto
        .createHash('sha256')
        .update(data)
        .digest('hex')
        .substring(0, 16);
    return {
        path: outputPath,
        size: stats.size,
        lines,
        hash,
        created: stats.birthtime,
    };
}
/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes) {
    if (bytes === 0)
        return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
}
/**
 * Truncate large strings for context efficiency
 */
export function truncateForContext(data, maxLength = 1000, showPreview = true) {
    if (data.length <= maxLength) {
        return data;
    }
    if (!showPreview) {
        return {
            truncated: true,
            preview: '',
            size: data.length,
        };
    }
    return {
        truncated: true,
        preview: data.substring(0, maxLength) + '...',
        size: data.length,
    };
}
//# sourceMappingURL=helpers.js.map