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
export function countTokens(text: string): TokenCount {
  const characters = text.length;
  // GPT-4 averages ~4 characters per token
  const tokens = Math.ceil(characters / 4);

  return {
    tokens,
    characters,
    method: 'heuristic (4 chars/token)',
  };
}

/**
 * Count tokens in a JSON object
 *
 * @param data - JSON object to count
 * @returns Token count information
 */
export function countTokensInJSON(data: any): TokenCount {
  const json = JSON.stringify(data, null, 2);
  return countTokens(json);
}

/**
 * Count tokens in an array of tool definitions
 *
 * Simulates loading all tool schemas into context
 *
 * @param tools - Array of tool definitions
 * @returns Token count information
 */
export function countToolSchemaTokens(tools: any[]): TokenCount {
  const toolsJSON = JSON.stringify(tools, null, 2);
  return countTokens(toolsJSON);
}

/**
 * Measure token usage for traditional approach
 *
 * In traditional approach, all tool definitions are loaded into context
 *
 * @param toolCount - Number of tools
 * @param avgToolSize - Average tool definition size in characters
 * @returns Estimated token count
 */
export function estimateTraditionalTokens(
  toolCount: number = 34,
  avgToolSize: number = 2000
): TokenCount {
  const totalChars = toolCount * avgToolSize;
  return {
    tokens: Math.ceil(totalChars / 4),
    characters: totalChars,
    method: 'traditional (all tools loaded)',
  };
}

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
export function estimateCodeExecutionTokens(
  toolNames: string[],
  resultsSize: number = 500
): TokenCount {
  // Tool names only (name + brief description)
  const toolNamesSize = toolNames.reduce((sum, name) => sum + name.length + 50, 0);

  // Results summary (not full data)
  const totalChars = toolNamesSize + resultsSize;

  return {
    tokens: Math.ceil(totalChars / 4),
    characters: totalChars,
    method: 'code execution (progressive loading + summaries)',
  };
}

/**
 * Calculate token reduction percentage
 *
 * @param traditional - Token count for traditional approach
 * @param codeExecution - Token count for code execution approach
 * @returns Reduction percentage
 */
export function calculateReduction(
  traditional: TokenCount,
  codeExecution: TokenCount
): number {
  return ((traditional.tokens - codeExecution.tokens) / traditional.tokens) * 100;
}

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
export function runBenchmark(
  scenario: string,
  toolCount: number = 34,
  toolsUsed: number = 5,
  dataSize: number = 10000
): BenchmarkResult {
  // Traditional: All tools loaded + full data in context
  const avgToolSize = 2000; // Average tool schema size
  const traditional = estimateTraditionalTokens(toolCount, avgToolSize);
  traditional.tokens += Math.ceil(dataSize / 4); // Add full data
  traditional.characters += dataSize;

  // Code execution: Only tool names + summary
  const toolNames = Array.from({ length: toolsUsed }, (_, i) => `tool_${i}`);
  const summarySize = 500; // Summary instead of full data
  const codeExecution = estimateCodeExecutionTokens(toolNames, summarySize);

  const reduction = calculateReduction(traditional, codeExecution);
  const savings = traditional.tokens - codeExecution.tokens;

  return {
    traditional,
    codeExecution,
    reduction,
    savings,
    message: `${scenario}: ${reduction.toFixed(1)}% reduction (${traditional.tokens} → ${codeExecution.tokens} tokens)`,
  };
}

/**
 * Pretty print benchmark results
 *
 * @param result - Benchmark result to print
 */
export function printBenchmark(result: BenchmarkResult): void {
  console.log(`\n${'='.repeat(60)}`);
  console.log(result.message);
  console.log(`${'='.repeat(60)}`);
  console.log(`Traditional:     ${result.traditional.tokens.toLocaleString()} tokens (${result.traditional.characters.toLocaleString()} chars)`);
  console.log(`Code Execution:  ${result.codeExecution.tokens.toLocaleString()} tokens (${result.codeExecution.characters.toLocaleString()} chars)`);
  console.log(`Reduction:       ${result.reduction.toFixed(2)}%`);
  console.log(`Tokens Saved:    ${result.savings.toLocaleString()}`);
  console.log(`${'='.repeat(60)}\n`);
}
