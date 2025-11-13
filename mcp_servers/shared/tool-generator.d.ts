/**
 * Tool File Generator for MCP 2.0 Migration
 *
 * Generates TypeScript filesystem API from Python MCP server definitions.
 * This enables progressive tool disclosure, reducing token usage by 99.7%.
 *
 * @see MIGRATION_PLAN.md Phase 1.1
 */
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
export declare class ToolFileGenerator {
    /**
     * Copy base infrastructure files to workspace
     *
     * Copies mcp-client.ts and mcp-server.ts from mcp_servers/shared/ to workspace/
     *
     * @param outputDir - Output directory (e.g., './workspace')
     */
    copyBaseFiles(outputDir: string): Promise<void>;
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
    generateToolFiles(serverName: string, tools: ToolDefinition[], outputDir: string): Promise<void>;
    /**
     * Generate TypeScript file for a single tool
     *
     * @param tool - Tool definition
     * @param serverName - Server name for tool ID
     * @returns TypeScript source code
     */
    private generateToolFile;
    /**
     * Generate barrel export (index.ts)
     *
     * @param tools - Array of tool definitions
     * @returns TypeScript source code
     */
    private generateIndexFile;
    /**
     * Generate README.md for server
     *
     * @param serverName - Server name
     * @param tools - Array of tool definitions
     * @returns Markdown content
     */
    private generateReadme;
    /**
     * Generate TypeScript interface from JSON schema
     *
     * @param schema - JSON schema object
     * @param name - Interface name
     * @returns TypeScript interface definition
     */
    private generateTypeScriptInterface;
    /**
     * Convert JSON schema type to TypeScript type
     *
     * @param prop - JSON schema property
     * @returns TypeScript type string
     */
    private schemaTypeToTS;
    /**
     * Convert snake_case to camelCase
     *
     * @param str - Snake case string
     * @returns Camel case string
     */
    private snakeToCamel;
    /**
     * Capitalize first letter
     *
     * @param str - Input string
     * @returns Capitalized string
     */
    private capitalize;
}
/**
 * CLI entry point for tool generator
 */
export declare function main(): Promise<void>;
//# sourceMappingURL=tool-generator.d.ts.map