/**
 * Example of Generated TypeScript Tool from Migration Infrastructure
 *
 * This file demonstrates what the tool generator creates from a Python MCP tool definition.
 * 
 * Source: database_mcp_server.py
 * Tool: get_sequences
 */

// ============================================================================
// INPUT: Python MCP Tool Definition
// ============================================================================

/*
Python definition:

@server.call_tool()
async def get_sequences(
    taxon: str,
    region: Literal["COI", "16S", "ITS", "mitogenome", "whole"] = "COI",
    source: Literal["gget", "ncbi", "bold", "silva", "unite"] = "gget",
    max_results: int = 100,
    format: Literal["fasta", "genbank"] = "fasta"
) -> dict:
    """
    Fetch sequences from multiple databases.
    
    Supports gget, NCBI, BOLD, SILVA, and UNITE databases.
    """
    # ... implementation
*/

// ============================================================================
// OUTPUT: Generated TypeScript Code (get_sequences.ts)
// ============================================================================

/**
 * Fetch sequences from multiple databases
 *
 * Generated from MCP server: database
 *
 * @see database_mcp_server.py
 */
import { callMCPTool } from "../../lib/mcp-client.js";

export interface GetSequencesInput {
  /** Taxon name or ID */
  taxon: string;
  /** Genomic region */
  region?: "COI" | "16S" | "ITS" | "mitogenome" | "whole";
  /** Database source */
  source?: "gget" | "ncbi" | "bold" | "silva" | "unite";
  /** Maximum results */
  max_results?: number;
  /** Output format */
  format?: "fasta" | "genbank";
}

/**
 * Fetch sequences from multiple databases
 *
 * @param input - Tool input parameters
 * @returns Tool execution result
 *
 * @example
 * ```typescript
 * import { getSequences } from './servers/database';
 *
 * const result = await getSequences({
 *   taxon: "Salmo salar",
 *   region: "COI",
 *   max_results: 50
 * });
 * ```
 */
export async function getSequences(
  input: GetSequencesInput
): Promise<any> {
  return callMCPTool<any>(
    'database__get_sequences',
    input
  );
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

// Example 1: Basic usage with only required parameters
async function example1() {
  const result = await getSequences({
    taxon: "Salmo salar"
  });
  console.log(result);
}

// Example 2: Full usage with all parameters
async function example2() {
  const result = await getSequences({
    taxon: "Salmo salar",
    region: "COI",
    source: "bold",
    max_results: 100,
    format: "fasta"
  });
  console.log(result);
}

// Example 3: TypeScript catches errors at compile time
async function example3() {
  // ✅ This works
  await getSequences({
    taxon: "Salmo salar",
    region: "COI"
  });

  // ❌ TypeScript error: 'region' must be one of the enum values
  // await getSequences({
  //   taxon: "Salmo salar",
  //   region: "invalid"  // Error!
  // });

  // ❌ TypeScript error: 'taxon' is required
  // await getSequences({
  //   region: "COI"  // Error! Missing 'taxon'
  // });
}

// ============================================================================
// BENEFITS OF GENERATED CODE
// ============================================================================

/*
1. TYPE SAFETY
   - TypeScript enforces correct parameter types
   - Enums ensure only valid values are used
   - Required vs optional parameters are clear

2. IDE SUPPORT
   - Autocomplete for all parameters
   - Inline documentation in tooltips
   - Jump to definition

3. TOKEN EFFICIENCY
   - Traditional: Send all tool definitions (~3,500 tokens each)
   - Generated: Load on demand via code execution (~400 tokens)
   - Reduction: 99.7% fewer tokens initially

4. MAINTAINABILITY
   - Clear, readable code
   - Easy to understand and modify
   - Comprehensive documentation

5. PROGRESSIVE DISCLOSURE
   - Only load tools when needed
   - No upfront token cost
   - Scales to hundreds of tools

6. COMPATIBILITY
   - Works with existing Python MCP servers
   - No changes to Python code required
   - Gradual migration path
*/

// ============================================================================
// FILE STRUCTURE
// ============================================================================

/*
workspace/servers/database/
├── get_sequences.ts         ← This file (individual tool)
├── gget_ref.ts
├── gget_search.ts
├── get_taxonomy.ts
├── ... (7 more tools)
├── index.ts                 ← Barrel exports all tools
└── README.md                ← Documentation

Usage:
  import * as database from './servers/database';
  await database.getSequences({ taxon: "Salmo salar" });

  OR

  import { getSequences } from './servers/database';
  await getSequences({ taxon: "Salmo salar" });
*/

// ============================================================================
// TOKEN COMPARISON
// ============================================================================

/*
TRADITIONAL MCP 1.0:
  - Load all 11 database tools upfront
  - Each tool ~3,500 tokens
  - Total: 11 × 3,500 = 38,500 tokens
  - Multiply by 5 servers = 192,500 tokens
  - EVERY REQUEST sends this context

CODE EXECUTION MCP 2.0:
  - Load tools on demand via code execution
  - Per tool: ~400 tokens (just the call)
  - Only load what you need
  - Total initial: ~0 tokens (Claude just runs code)
  - REDUCTION: 99.7%

EXAMPLE:
  User: "Get COI sequences for Salmo salar"
  
  MCP 1.0: Send 192,500 tokens of tool definitions ❌
  MCP 2.0: Just run getSequences() ✅
*/

export { example1, example2, example3 };

