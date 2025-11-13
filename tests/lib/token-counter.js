"use strict";
/**
 * Token Counter Utility
 *
 * Estimates token usage for benchmarking the code execution architecture.
 * Uses a simple heuristic: ~4 characters per token (GPT-4 average).
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.countTokens = countTokens;
exports.countTokensInJSON = countTokensInJSON;
exports.countToolSchemaTokens = countToolSchemaTokens;
exports.estimateTraditionalTokens = estimateTraditionalTokens;
exports.estimateCodeExecutionTokens = estimateCodeExecutionTokens;
exports.calculateReduction = calculateReduction;
exports.runBenchmark = runBenchmark;
exports.printBenchmark = printBenchmark;
/**
 * Count tokens in a text string
 *
 * Uses a simple 4-char-per-token heuristic for estimation.
 * For production use, consider using tiktoken library for exact counts.
 *
 * @param text - Text to count tokens in
 * @returns Token count information
 */
function countTokens(text) {
    var characters = text.length;
    // GPT-4 averages ~4 characters per token
    var tokens = Math.ceil(characters / 4);
    return {
        tokens: tokens,
        characters: characters,
        method: 'heuristic (4 chars/token)',
    };
}
/**
 * Count tokens in a JSON object
 *
 * @param data - JSON object to count
 * @returns Token count information
 */
function countTokensInJSON(data) {
    var json = JSON.stringify(data, null, 2);
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
function countToolSchemaTokens(tools) {
    var toolsJSON = JSON.stringify(tools, null, 2);
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
function estimateTraditionalTokens(toolCount, avgToolSize) {
    if (toolCount === void 0) { toolCount = 34; }
    if (avgToolSize === void 0) { avgToolSize = 2000; }
    var totalChars = toolCount * avgToolSize;
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
function estimateCodeExecutionTokens(toolNames, resultsSize) {
    if (resultsSize === void 0) { resultsSize = 500; }
    // Tool names only (name + brief description)
    var toolNamesSize = toolNames.reduce(function (sum, name) { return sum + name.length + 50; }, 0);
    // Results summary (not full data)
    var totalChars = toolNamesSize + resultsSize;
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
function calculateReduction(traditional, codeExecution) {
    return ((traditional.tokens - codeExecution.tokens) / traditional.tokens) * 100;
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
function runBenchmark(scenario, toolCount, toolsUsed, dataSize) {
    if (toolCount === void 0) { toolCount = 34; }
    if (toolsUsed === void 0) { toolsUsed = 5; }
    if (dataSize === void 0) { dataSize = 10000; }
    // Traditional: All tools loaded + full data in context
    var avgToolSize = 2000; // Average tool schema size
    var traditional = estimateTraditionalTokens(toolCount, avgToolSize);
    traditional.tokens += Math.ceil(dataSize / 4); // Add full data
    traditional.characters += dataSize;
    // Code execution: Only tool names + summary
    var toolNames = Array.from({ length: toolsUsed }, function (_, i) { return "tool_".concat(i); });
    var summarySize = 500; // Summary instead of full data
    var codeExecution = estimateCodeExecutionTokens(toolNames, summarySize);
    var reduction = calculateReduction(traditional, codeExecution);
    var savings = traditional.tokens - codeExecution.tokens;
    return {
        traditional: traditional,
        codeExecution: codeExecution,
        reduction: reduction,
        savings: savings,
        message: "".concat(scenario, ": ").concat(reduction.toFixed(1), "% reduction (").concat(traditional.tokens, " \u2192 ").concat(codeExecution.tokens, " tokens)"),
    };
}
/**
 * Pretty print benchmark results
 *
 * @param result - Benchmark result to print
 */
function printBenchmark(result) {
    console.log("\n".concat('='.repeat(60)));
    console.log(result.message);
    console.log("".concat('='.repeat(60)));
    console.log("Traditional:     ".concat(result.traditional.tokens.toLocaleString(), " tokens (").concat(result.traditional.characters.toLocaleString(), " chars)"));
    console.log("Code Execution:  ".concat(result.codeExecution.tokens.toLocaleString(), " tokens (").concat(result.codeExecution.characters.toLocaleString(), " chars)"));
    console.log("Reduction:       ".concat(result.reduction.toFixed(2), "%"));
    console.log("Tokens Saved:    ".concat(result.savings.toLocaleString()));
    console.log("".concat('='.repeat(60), "\n"));
}
//# sourceMappingURL=token-counter.js.map