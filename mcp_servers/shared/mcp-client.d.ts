/**
 * Enhanced MCP Client with Progressive Tool Disclosure
 *
 * Provides:
 * - Progressive tool discovery (name → description → full schema)
 * - Schema caching to reduce token usage
 * - Docker-based communication with MCP servers
 * - Type-safe tool calling
 * - PII tokenization support (optional)
 */
/**
 * Detail levels for tool disclosure
 */
export type DetailLevel = 'name' | 'description' | 'full';
/**
 * Tool information at different detail levels
 */
export interface ToolInfo {
    name: string;
    description?: string;
    inputSchema?: any;
}
/**
 * Tool search result
 */
export interface ToolSearchResult {
    server: string;
    tools: ToolInfo[];
}
/**
 * Server configuration
 */
export interface ServerConfig {
    container: string;
    enabled?: boolean;
}
/**
 * MCP Client configuration
 */
export interface MCPClientConfig {
    servers: Record<string, ServerConfig>;
    cacheSchemas?: boolean;
    tokenizer?: any;
}
/**
 * Enhanced MCP Client with progressive tool disclosure
 */
export declare class MCPClient {
    private config;
    private schemaCache;
    private descriptionCache;
    private nameCache;
    constructor(config: MCPClientConfig);
    /**
     * Search for tools across all servers with specified detail level
     *
     * @param query - Search query (regex pattern or keyword)
     * @param detailLevel - Level of detail to return
     * @returns Matching tools from all servers
     *
     * @example
     * // Get only tool names (minimal tokens)
     * const names = await client.searchTools('sequence', 'name');
     *
     * // Get names and descriptions (moderate tokens)
     * const withDesc = await client.searchTools('align', 'description');
     *
     * // Get full schemas (maximum tokens, use sparingly)
     * const full = await client.searchTools('primer', 'full');
     */
    searchTools(query: string, detailLevel?: DetailLevel): Promise<ToolSearchResult[]>;
    /**
     * Get all available tool names from a specific server
     *
     * @param serverName - Name of the MCP server
     * @returns Array of tool names
     */
    getToolNames(serverName: string): Promise<string[]>;
    /**
     * Get tool descriptions from a specific server
     *
     * @param serverName - Name of the MCP server
     * @returns Array of tools with descriptions
     */
    getToolDescriptions(serverName: string): Promise<ToolInfo[]>;
    /**
     * Get full tool schema from a specific server
     *
     * @param serverName - Name of the MCP server
     * @param toolName - Optional: specific tool name
     * @returns Full tool schemas
     */
    getToolSchema(serverName: string, toolName?: string): Promise<ToolInfo[]>;
    /**
     * Call an MCP tool
     *
     * @param serverName - Name of the MCP server
     * @param toolName - Name of the tool
     * @param args - Tool arguments
     * @param timeout - Execution timeout in milliseconds
     * @returns Tool result
     */
    callTool<T = any>(serverName: string, toolName: string, args: Record<string, any>, timeout?: number): Promise<T>;
    /**
     * Fetch tools from an MCP server
     *
     * @private
     */
    private fetchTools;
    /**
     * Clear all caches
     */
    clearCache(): void;
    /**
     * Get cache statistics
     */
    getCacheStats(): {
        servers: number;
        namesCached: number;
        descriptionsCached: number;
        schemasCached: number;
    };
}
/**
 * Legacy function for backward compatibility
 */
export declare function callMCPTool<T = any>(toolId: string, params: Record<string, any>, timeout?: number): Promise<T>;
/**
 * Check which Docker containers are not running
 *
 * @returns Array of missing container names
 *
 * @example
 * const missing = await checkContainers();
 * if (missing.length > 0) {
 *   console.error(`Missing containers: ${missing.join(', ')}`);
 * }
 */
export declare function checkContainers(): Promise<string[]>;
//# sourceMappingURL=mcp-client.d.ts.map