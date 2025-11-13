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

import { exec, spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

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
  tokenizer?: any; // PIITokenizer instance (optional)
}

/**
 * Enhanced MCP Client with progressive tool disclosure
 */
export class MCPClient {
  private config: MCPClientConfig;
  private schemaCache: Map<string, ToolInfo[]> = new Map();
  private descriptionCache: Map<string, ToolInfo[]> = new Map();
  private nameCache: Map<string, string[]> = new Map();

  constructor(config: MCPClientConfig) {
    this.config = {
      cacheSchemas: true,
      ...config,
    };
  }

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
  async searchTools(
    query: string,
    detailLevel: DetailLevel = 'name'
  ): Promise<ToolSearchResult[]> {
    const results: ToolSearchResult[] = [];
    const regex = new RegExp(query, 'i');

    for (const [serverName, serverConfig] of Object.entries(this.config.servers)) {
      if (serverConfig.enabled === false) {
        continue;
      }

      let tools: ToolInfo[];

      // Use cached data if available
      if (detailLevel === 'name' && this.nameCache.has(serverName)) {
        const names = this.nameCache.get(serverName)!;
        tools = names
          .filter(name => regex.test(name))
          .map(name => ({ name }));
      } else if (detailLevel === 'description' && this.descriptionCache.has(serverName)) {
        tools = this.descriptionCache.get(serverName)!
          .filter(tool => regex.test(tool.name) || regex.test(tool.description || ''));
      } else if (detailLevel === 'full' && this.schemaCache.has(serverName)) {
        tools = this.schemaCache.get(serverName)!
          .filter(tool => regex.test(tool.name) || regex.test(tool.description || ''));
      } else {
        // Fetch from server
        tools = await this.fetchTools(serverName, serverConfig.container, detailLevel);
      }

      if (tools.length > 0) {
        results.push({
          server: serverName,
          tools,
        });
      }
    }

    return results;
  }

  /**
   * Get all available tool names from a specific server
   *
   * @param serverName - Name of the MCP server
   * @returns Array of tool names
   */
  async getToolNames(serverName: string): Promise<string[]> {
    const serverConfig = this.config.servers[serverName];
    if (!serverConfig) {
      throw new Error(`Server '${serverName}' not found in configuration`);
    }

    // Check cache first
    if (this.nameCache.has(serverName)) {
      return this.nameCache.get(serverName)!;
    }

    // Fetch from server
    const tools = await this.fetchTools(serverName, serverConfig.container, 'name');
    const names = tools.map(t => t.name);

    // Cache the names
    if (this.config.cacheSchemas) {
      this.nameCache.set(serverName, names);
    }

    return names;
  }

  /**
   * Get tool descriptions from a specific server
   *
   * @param serverName - Name of the MCP server
   * @returns Array of tools with descriptions
   */
  async getToolDescriptions(serverName: string): Promise<ToolInfo[]> {
    const serverConfig = this.config.servers[serverName];
    if (!serverConfig) {
      throw new Error(`Server '${serverName}' not found in configuration`);
    }

    // Check cache first
    if (this.descriptionCache.has(serverName)) {
      return this.descriptionCache.get(serverName)!;
    }

    // Fetch from server
    const tools = await this.fetchTools(serverName, serverConfig.container, 'description');

    // Cache the descriptions
    if (this.config.cacheSchemas) {
      this.descriptionCache.set(serverName, tools);
    }

    return tools;
  }

  /**
   * Get full tool schema from a specific server
   *
   * @param serverName - Name of the MCP server
   * @param toolName - Optional: specific tool name
   * @returns Full tool schemas
   */
  async getToolSchema(serverName: string, toolName?: string): Promise<ToolInfo[]> {
    const serverConfig = this.config.servers[serverName];
    if (!serverConfig) {
      throw new Error(`Server '${serverName}' not found in configuration`);
    }

    // Check cache first
    if (this.schemaCache.has(serverName)) {
      const cached = this.schemaCache.get(serverName)!;
      if (toolName) {
        const tool = cached.find(t => t.name === toolName);
        return tool ? [tool] : [];
      }
      return cached;
    }

    // Fetch from server
    const tools = await this.fetchTools(serverName, serverConfig.container, 'full');

    // Cache the schemas
    if (this.config.cacheSchemas) {
      this.schemaCache.set(serverName, tools);
    }

    if (toolName) {
      const tool = tools.find(t => t.name === toolName);
      return tool ? [tool] : [];
    }

    return tools;
  }

  /**
   * Call an MCP tool
   *
   * @param serverName - Name of the MCP server
   * @param toolName - Name of the tool
   * @param args - Tool arguments
   * @param timeout - Execution timeout in milliseconds
   * @returns Tool result
   */
  async callTool<T = any>(
    serverName: string,
    toolName: string,
    args: Record<string, any>,
    timeout: number = 30000
  ): Promise<T> {
    const serverConfig = this.config.servers[serverName];
    if (!serverConfig) {
      throw new Error(`Server '${serverName}' not found in configuration`);
    }

    // Apply PII tokenization if configured
    let processedArgs = args;
    if (this.config.tokenizer) {
      processedArgs = this.config.tokenizer.tokenize(args);
    }

    // Build MCP request
    const initRequest = JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'mcp-client',
          version: '1.0.0',
        },
      },
    });

    const toolRequest = JSON.stringify({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: processedArgs,
      },
    });

    // Execute via docker exec
    const requests = [initRequest, toolRequest].join('\n');
    const command = `echo '${requests.replace(/'/g, "'\\''")}' | docker exec -i ${serverConfig.container} python3 -`;

    try {
      const { stdout } = await execAsync(command, {
        timeout,
        maxBuffer: 10 * 1024 * 1024, // 10MB
      });

      // Parse response (second line is the tool result)
      const lines = stdout.trim().split('\n');
      const toolResponse = JSON.parse(lines[1] || '{}');

      if (toolResponse.error) {
        throw new Error(toolResponse.error.message || 'Tool execution failed');
      }

      // Extract result from content
      const content = toolResponse.result?.content?.[0];
      if (!content || content.type !== 'text') {
        throw new Error('Invalid tool response format');
      }

      let result = content.text;

      // Try to parse as JSON if possible
      try {
        result = JSON.parse(result);
      } catch {
        // Not JSON, return as string
      }

      // Apply PII detokenization if configured
      if (this.config.tokenizer) {
        result = this.config.tokenizer.detokenize(result);
      }

      return result as T;
    } catch (error: any) {
      throw new Error(`Tool call failed: ${error.message}`);
    }
  }

  /**
   * Fetch tools from an MCP server
   *
   * @private
   */
  private async fetchTools(
    serverName: string,
    containerName: string,
    detailLevel: DetailLevel
  ): Promise<ToolInfo[]> {
    // Build MCP request
    const initRequest = JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'mcp-client',
          version: '1.0.0',
        },
      },
    });

    const listRequest = JSON.stringify({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/list',
      params: {},
    });

    // Execute via docker exec
    const requests = [initRequest, listRequest].join('\n');
    const command = `echo '${requests.replace(/'/g, "'\\''")}' | docker exec -i ${containerName} python3 -`;

    try {
      const { stdout } = await execAsync(command, {
        timeout: 10000,
        maxBuffer: 10 * 1024 * 1024,
      });

      // Parse response
      const lines = stdout.trim().split('\n');
      const listResponse = JSON.parse(lines[1] || '{}');

      if (listResponse.error) {
        throw new Error(listResponse.error.message || 'Failed to list tools');
      }

      const tools = listResponse.result?.tools || [];

      // Filter based on detail level
      return tools.map((tool: any) => {
        switch (detailLevel) {
          case 'name':
            return { name: tool.name };
          case 'description':
            return {
              name: tool.name,
              description: tool.description,
            };
          case 'full':
            return {
              name: tool.name,
              description: tool.description,
              inputSchema: tool.inputSchema,
            };
        }
      });
    } catch (error: any) {
      console.error(`Failed to fetch tools from ${serverName}:`, error.message);
      return [];
    }
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.nameCache.clear();
    this.descriptionCache.clear();
    this.schemaCache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    servers: number;
    namesCached: number;
    descriptionsCached: number;
    schemasCached: number;
  } {
    return {
      servers: Object.keys(this.config.servers).length,
      namesCached: this.nameCache.size,
      descriptionsCached: this.descriptionCache.size,
      schemasCached: this.schemaCache.size,
    };
  }
}

/**
 * Legacy function for backward compatibility
 */
export async function callMCPTool<T = any>(
  toolId: string,
  params: Record<string, any>,
  timeout: number = 30000
): Promise<T> {
  // Parse toolId (format: "server__tool")
  const [serverName, toolName] = toolId.split('__');

  if (!serverName || !toolName) {
    throw new Error('Invalid toolId format. Expected: "server__tool"');
  }

  // Create a temporary client
  const client = new MCPClient({
    servers: {
      [serverName]: {
        container: `ndiag-${serverName}-server`,
      },
    },
  });

  return client.callTool<T>(serverName, toolName, params, timeout);
}

/**
 * Container mapping for checking container status
 */
const CONTAINER_MAP: Record<string, string> = {
  database: 'ndiag-database-server',
  processing: 'ndiag-processing-server',
  alignment: 'ndiag-alignment-server',
  design: 'ndiag-design-server',
  validation: 'ndiag-validation-server',
};

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
export async function checkContainers(): Promise<string[]> {
  const missing: string[] = [];

  for (const [, containerName] of Object.entries(CONTAINER_MAP)) {
    const isRunning = await isContainerRunning(containerName);
    if (!isRunning) {
      missing.push(containerName);
    }
  }

  return missing;
}

/**
 * Check if a Docker container is running
 *
 * @param containerName - Docker container name
 * @returns True if container is running, false otherwise
 */
async function isContainerRunning(containerName: string): Promise<boolean> {
  return new Promise((resolve) => {
    const proc = spawn('docker', ['ps', '--filter', `name=${containerName}`, '--format', '{{.Names}}']);

    let stdout = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.on('close', () => {
      resolve(stdout.includes(containerName));
    });

    proc.on('error', () => {
      resolve(false);
    });
  });
}
