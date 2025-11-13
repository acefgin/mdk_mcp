/**
 * Token Counter Utility
 *
 * Estimates token usage for benchmarking the code execution architecture.
 * Uses a simple heuristic: ~4 characters per token (GPT-4 average).
 */
export interface TokenCount {
    tokens: number;
    characters: number;
    method: string;
}
/**
 * Count tokens in a text string
 *
 * Uses a simple 4-char-per-token heuristic for estimation.
 * For production use, consider using tiktoken library for exact counts.
 *
 * @param text - Text to count tokens in
 * @returns Token count information
 */
export declare function countTokens(text: string): TokenCount;
/**
 * Count tokens in a JSON object
 *
 * @param data - JSON object to count
 * @returns Token count information
 */
export declare function countTokensInJSON(data: any): TokenCount;
/**
 * Count tokens in an array of tool definitions
 *
 * Simulates loading all tool schemas into context
 *
 * @param tools - Array of tool definitions
 * @returns Token count information
 */
export declare function countToolSchemaTokens(tools: any[]): TokenCount;
/**
 * Measure token usage for traditional approach
 *
 * In traditional approach, all tool definitions are loaded into context
 *
 * @param toolCount - Number of tools
 * @param avgToolSize - Average tool definition size in characters
 * @returns Estimated token count
 */
export declare function estimateTraditionalTokens(toolCount?: number, avgToolSize?: number): TokenCount;
/**
 * Measure token usage for code execution approach
 *
 * In code execution approach, only tool names are loaded initially,
 * full schemas are loaded on demand, and results are processed in code
 *
 * @param toolNames - Array of tool names (minimal metadata)
 * @param resultsSize - Size of results data in characters
 * @returns Estimated token count
 */
export declare function estimateCodeExecutionTokens(toolNames: string[], resultsSize?: number): TokenCount;
/**
 * Calculate token reduction percentage
 *
 * @param traditional - Token count for traditional approach
 * @param codeExecution - Token count for code execution approach
 * @returns Reduction percentage
 */
export declare function calculateReduction(traditional: TokenCount, codeExecution: TokenCount): number;
/**
 * Benchmark comparison
 */
export interface BenchmarkResult {
    traditional: TokenCount;
    codeExecution: TokenCount;
    reduction: number;
    savings: number;
    message: string;
}
/**
 * Run a comprehensive token usage benchmark
 *
 * @param scenario - Benchmark scenario name
 * @param toolCount - Number of tools available
 * @param toolsUsed - Number of tools actually used
 * @param dataSize - Size of result data in characters
 * @returns Benchmark results
 */
export declare function runBenchmark(scenario: string, toolCount?: number, toolsUsed?: number, dataSize?: number): BenchmarkResult;
/**
 * Pretty print benchmark results
 *
 * @param result - Benchmark result to print
 */
export declare function printBenchmark(result: BenchmarkResult): void;
//# sourceMappingURL=token-counter.d.ts.map