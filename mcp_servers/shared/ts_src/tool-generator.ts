/**
 * Tool File Generator for MCP 2.0 Migration
 *
 * Generates TypeScript filesystem API from Python MCP server definitions.
 * This enables progressive tool disclosure, reducing token usage by 99.7%.
 *
 * @see MIGRATION_PLAN.md Phase 1.1
 */

import { writeFile, mkdir, copyFile } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

/**
 * Tool definition from Python MCP server
 */
export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: any;
  outputSchema?: any;
}

/**
 * Generator configuration
 */
export interface GeneratorConfig {
  serverName: string;
  tools: ToolDefinition[];
  outputDir: string;
  includeReadme?: boolean;
  includeTypes?: boolean;
}

/**
 * Tool File Generator
 *
 * Generates filesystem-based tool APIs from MCP tool definitions.
 *
 * Usage:
 * ```typescript
 * const generator = new ToolFileGenerator();
 * await generator.generateToolFiles('database', tools, './workspace/servers');
 * ```
 */
export class ToolFileGenerator {
  /**
   * Copy base infrastructure files to workspace
   * 
   * Copies mcp-client.ts and mcp-server.ts from mcp_servers/shared/ to workspace/
   * 
   * @param outputDir - Output directory (e.g., './workspace')
   */
  async copyBaseFiles(outputDir: string): Promise<void> {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = dirname(__filename);
    // When running from dist, go up to shared dir then into ts_src
    const sharedDir = join(__dirname, "..", "ts_src");

    // Create lib directory
    const libDir = join(outputDir, "lib");
    await mkdir(libDir, { recursive: true });

    // Copy mcp-client.ts
    const mcpClientSrc = join(sharedDir, "mcp-client.ts");
    const mcpClientDest = join(libDir, "mcp-client.ts");
    await copyFile(mcpClientSrc, mcpClientDest);
    console.log(`  ✓ Copied mcp-client.ts to ${libDir}/`);

    // Copy mcp-server.ts
    const mcpServerSrc = join(sharedDir, "mcp-server.ts");
    const mcpServerDest = join(outputDir, "mcp-server.ts");
    await copyFile(mcpServerSrc, mcpServerDest);
    console.log(`  ✓ Copied mcp-server.ts to ${outputDir}/`);
  }

  /**
   * Generate all tool files for a server
   *
   * Creates:
   * - Individual tool files (toolName.ts)
   * - Barrel export (index.ts)
   * - Server documentation (README.md)
   *
   * @param serverName - Name of the MCP server (e.g., 'database')
   * @param tools - Array of tool definitions
   * @param outputDir - Output directory for generated files
   */
  async generateToolFiles(
    serverName: string,
    tools: ToolDefinition[],
    outputDir: string
  ): Promise<void> {
    const serverDir = join(outputDir, "servers", serverName);

    // Create server directory
    await mkdir(serverDir, { recursive: true });

    console.log(`\n📁 Generating ${tools.length} tools for ${serverName} server...`);

    // Generate individual tool files
    let successCount = 0;
    for (const tool of tools) {
      try {
        const toolFile = this.generateToolFile(tool, serverName);
        const fileName = tool.name + ".ts";
        const filePath = join(serverDir, fileName);

        await writeFile(filePath, toolFile);
        console.log(`  ✓ Generated ${fileName}`);
        successCount++;
      } catch (error) {
        console.error(`  ✗ Failed to generate ${tool.name}:`, error);
      }
    }

    // Generate index.ts (barrel export)
    const indexFile = this.generateIndexFile(tools);
    await writeFile(join(serverDir, "index.ts"), indexFile);
    console.log(`  ✓ Generated index.ts`);

    // Generate README.md
    const readme = this.generateReadme(serverName, tools);
    await writeFile(join(serverDir, "README.md"), readme);
    console.log(`  ✓ Generated README.md`);

    console.log(`\n✅ Successfully generated ${successCount}/${tools.length} tools`);
    console.log(`📂 Output: ${serverDir}\n`);
  }

  /**
   * Generate TypeScript file for a single tool
   *
   * @param tool - Tool definition
   * @param serverName - Server name for tool ID
   * @returns TypeScript source code
   */
  private generateToolFile(tool: ToolDefinition, serverName: string): string {
    const functionName = this.snakeToCamel(tool.name);
    const typeName = this.capitalize(functionName);

    // Generate input interface
    const inputInterface = this.generateTypeScriptInterface(
      tool.inputSchema,
      `${typeName}Input`
    );

    // Generate output interface if schema provided
    const outputInterface = tool.outputSchema
      ? this.generateTypeScriptInterface(tool.outputSchema, `${typeName}Output`)
      : '';

    // Determine return type
    const returnType = tool.outputSchema ? `${typeName}Output` : 'any';

    return `/**
 * ${tool.description}
 *
 * Generated from MCP server: ${serverName}
 *
 * @see ${serverName}_mcp_server.py
 */
import { callMCPTool } from "../../lib/mcp-client.js";

${inputInterface}

${outputInterface}

/**
 * ${tool.description}
 *
 * @param input - Tool input parameters
 * @returns Tool execution result
 *
 * @example
 * \`\`\`typescript
 * import { ${functionName} } from './servers/${serverName}';
 *
 * const result = await ${functionName}({
 *   // ... input parameters
 * });
 * \`\`\`
 */
export async function ${functionName}(
  input: ${typeName}Input
): Promise<${returnType}> {
  // Sanitize input: convert string numbers to actual numbers
  const sanitized: any = { ...input };
  for (const [key, value] of Object.entries(sanitized)) {
    // Convert string numbers to numbers (e.g., "10" -> 10)
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (trimmed !== '' && !isNaN(Number(trimmed))) {
        sanitized[key] = Number(trimmed);
      }
    }
  }
  
  return callMCPTool<${returnType}>(
    '${serverName}__${tool.name}',
    sanitized
  );
}
`;
  }

  /**
   * Generate barrel export (index.ts)
   *
   * @param tools - Array of tool definitions
   * @returns TypeScript source code
   */
  private generateIndexFile(tools: ToolDefinition[]): string {
    const exports = tools
      .map((t) => {
        const fileName = t.name;
        const functionName = this.snakeToCamel(t.name);
        return `export { ${functionName} } from './${fileName}.js';`;
      })
      .join("\n");

    return `/**
 * Auto-generated MCP server tools
 *
 * This file provides barrel exports for all tools in this server.
 *
 * Usage:
 * \`\`\`typescript
 * // Import all tools
 * import * as database from './servers/database';
 * const seqs = await database.getSequences({ ... });
 *
 * // Or import individual tools
 * import { getSequences } from './servers/database';
 * const seqs = await getSequences({ ... });
 * \`\`\`
 *
 * @generated
 * @see tool-generator.ts
 */

${exports}
`;
  }

  /**
   * Generate README.md for server
   *
   * @param serverName - Server name
   * @param tools - Array of tool definitions
   * @returns Markdown content
   */
  private generateReadme(serverName: string, tools: ToolDefinition[]): string {
    const toolList = tools
      .map((t) => {
        const functionName = this.snakeToCamel(t.name);
        return `- \`${functionName}\`: ${t.description}`;
      })
      .join("\n");

    const exampleTool = tools[0] || { name: 'example_tool', description: 'Example tool' };
    const exampleFunctionName = this.snakeToCamel(exampleTool.name);

    return `# ${this.capitalize(serverName)} Server

**Generated**: ${new Date().toISOString()}
**Tools**: ${tools.length}
**Source**: ${serverName}_mcp_server.py

## Overview

This server provides ${tools.length} tools for ${serverName}-related operations in the MCP 2.0 architecture.

## Available Tools

${toolList}

## Usage

### Import all tools

\`\`\`typescript
import * as ${serverName} from './servers/${serverName}';

// Use any tool
const result = await ${serverName}.${exampleFunctionName}({ ... });
\`\`\`

### Import specific tools

\`\`\`typescript
import { ${exampleFunctionName} } from './servers/${serverName}';

const result = await ${exampleFunctionName}({ ... });
\`\`\`

## Example

\`\`\`typescript
import * as ${serverName} from './servers/${serverName}';

// Example usage
const result = await ${serverName}.${exampleFunctionName}({
  // ... input parameters
});

console.log(result);
\`\`\`

## Token Efficiency

**Traditional approach**: Load all tools upfront (~${tools.length * 3500} tokens)

**Code execution approach**: Load on demand (~400 tokens per tool)

**Reduction**: ~99% fewer tokens

## See Also

- [MCP 2.0 Architecture](../../docs/MCP_2.0_ARCHITECTURE_SUMMARY.md)
- [Migration Plan](../../docs/MIGRATION_PLAN.md)
- [Tool Generator](../../mcp_servers/shared/tool-generator.ts)

---

*Auto-generated by tool-generator.ts*
`;
  }

  /**
   * Generate TypeScript interface from JSON schema
   *
   * @param schema - JSON schema object
   * @param name - Interface name
   * @returns TypeScript interface definition
   */
  private generateTypeScriptInterface(schema: any, name: string): string {
    if (!schema || schema.type !== "object") {
      return `export type ${name} = any;`;
    }

    const properties = Object.entries(schema.properties || {})
      .map(([key, prop]: [string, any]) => {
        const optional = !schema.required?.includes(key) ? "?" : "";
        const type = this.schemaTypeToTS(prop);
        const comment = prop.description ? `  /** ${prop.description} */\n` : "";
        return `${comment}  ${key}${optional}: ${type};`;
      })
      .join("\n");

    return `export interface ${name} {
${properties}
}`;
  }

  /**
   * Convert JSON schema type to TypeScript type
   *
   * @param prop - JSON schema property
   * @returns TypeScript type string
   */
  private schemaTypeToTS(prop: any): string {
    // Handle enum types
    if (prop.enum) {
      return prop.enum.map((e: any) => `"${e}"`).join(" | ");
    }

    // Handle array types
    if (prop.type === "array") {
      const itemType = prop.items ? this.schemaTypeToTS(prop.items) : "any";
      return `${itemType}[]`;
    }

    // Handle object types
    if (prop.type === "object") {
      if (prop.properties) {
        // Inline interface for nested objects
        const props = Object.entries(prop.properties)
          .map(([k, v]: [string, any]) => {
            const optional = !prop.required?.includes(k) ? "?" : "";
            return `${k}${optional}: ${this.schemaTypeToTS(v)}`;
          })
          .join("; ");
        return `{ ${props} }`;
      }
      return "Record<string, any>";
    }

    // Primitive types
    const typeMap: Record<string, string> = {
      string: "string",
      integer: "number",
      number: "number",
      boolean: "boolean",
      null: "null",
    };

    return typeMap[prop.type] || "any";
  }

  /**
   * Convert snake_case to camelCase
   *
   * @param str - Snake case string
   * @returns Camel case string
   */
  private snakeToCamel(str: string): string {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
  }

  /**
   * Capitalize first letter
   *
   * @param str - Input string
   * @returns Capitalized string
   */
  private capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}

/**
 * CLI entry point for tool generator
 */
export async function main() {
  const args = process.argv.slice(2);

  if (args.length < 6) {
    console.error(`
Usage: node tool-generator.js --server <name> --input <path> --output <dir>

Options:
  --server <name>   Server name (e.g., 'database')
  --input <path>    Path to Python MCP server file
  --output <dir>    Output directory for generated files

Example:
  node tool-generator.js \\
    --server database \\
    --input mcp_servers/database_server/database_mcp_server.py \\
    --output workspace/servers/
`);
    process.exit(1);
  }

  const serverIdx = args.indexOf('--server');
  const inputIdx = args.indexOf('--input');
  const outputIdx = args.indexOf('--output');

  if (serverIdx === -1 || inputIdx === -1 || outputIdx === -1) {
    console.error('Error: Missing required arguments');
    process.exit(1);
  }

  const serverName = args[serverIdx + 1];
  const inputPath = args[inputIdx + 1];
  const outputDir = args[outputIdx + 1];

  console.log(`\n🔧 Tool Generator`);
  console.log(`Server: ${serverName}`);
  console.log(`Input: ${inputPath}`);
  console.log(`Output: ${outputDir}`);

  // TODO: Parse Python MCP server file to extract tool definitions
  // For now, this would need to be implemented based on the Python server structure

  console.log('\n⚠️  Note: Python parsing not yet implemented');
  console.log('Please extract tool definitions manually and pass to generateToolFiles()');
  console.log('\nExample:');
  console.log(`
const generator = new ToolFileGenerator();
const tools = [
  {
    name: 'get_sequences',
    description: 'Fetch sequences from multiple databases',
    inputSchema: { type: 'object', properties: { ... } }
  },
  // ... more tools
];

await generator.generateToolFiles('${serverName}', tools, '${outputDir}');
`);
}

// Run CLI if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}
