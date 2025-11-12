/**
 * MCP Client Library
 * 
 * Provides `callMCPTool()` function that bridges TypeScript modules to Python MCP servers via Docker exec.
 * 
 * This enables generated tool wrappers to communicate with Python MCP servers running in Docker containers.
 * 
 * @module mcp-client
 */

import { spawn } from 'child_process';

/**
 * Container mapping for MCP servers
 * Maps server name to Docker container name
 */
const CONTAINER_MAP: Record<string, string> = {
  database: 'ndiag-database-server',
  processing: 'ndiag-processing-server',
  alignment: 'ndiag-alignment-server',
  design: 'ndiag-design-server',
  validation: 'ndiag-validation-server',
};

/**
 * Call an MCP tool in a Python server via Docker exec
 * 
 * @param toolId - Full tool ID in format "serverName__toolName" (e.g., "database__get_sequences")
 * @param params - Tool input parameters
 * @param timeout - Timeout in milliseconds (default: 30000)
 * @returns Tool execution result
 * 
 * @throws Error if tool call fails or times out
 * 
 * @example
 * ```typescript
 * import { callMCPTool } from './lib/mcp-client.js';
 * 
 * const result = await callMCPTool('database__get_sequences', {
 *   taxon: 'Salmo salar',
 *   region: 'COI',
 *   max_results: 50
 * });
 * ```
 */
export async function callMCPTool<T = any>(
  toolId: string,
  params: Record<string, any>,
  timeout: number = 30000
): Promise<T> {
  // Parse tool ID: "serverName__toolName"
  const [serverName, toolName] = toolId.split('__');
  
  if (!serverName || !toolName) {
    throw new Error(`Invalid tool ID format: ${toolId}. Expected format: "serverName__toolName"`);
  }

  // Get container name
  const containerName = CONTAINER_MAP[serverName];
  if (!containerName) {
    throw new Error(`Unknown server: ${serverName}. Available: ${Object.keys(CONTAINER_MAP).join(', ')}`);
  }

  // Create JSON-RPC requests (initialize + tool call)
  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: {
        name: 'mdk-mcp-client',
        version: '2.0.0'
      }
    }
  };

  const toolRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/call',
    params: {
      name: toolName,  // Use snake_case tool name without server prefix
      arguments: params,
    },
  };

  // Execute docker exec command with both requests
  const result = await dockerExec(containerName, [initRequest, toolRequest], timeout);
  
  return result as T;
}

/**
 * Execute command in Docker container via stdin/stdout
 * 
 * @param containerName - Docker container name
 * @param requests - JSON-RPC request object(s) - single request or array for multiple
 * @param timeout - Timeout in milliseconds
 * @returns JSON-RPC response result
 * 
 * @throws Error if Docker exec fails or times out
 */
async function dockerExec(
  containerName: string,
  requests: any | any[],
  timeout: number
): Promise<any> {
  return new Promise((resolve, reject) => {
    // Determine the server module name from container name
    // e.g., ndiag-database-server -> database_mcp_server.py
    const serverName = containerName.replace('ndiag-', '').replace('-server', '');
    const moduleName = `${serverName}_mcp_server.py`;
    
    // Spawn docker exec process
    const proc = spawn('docker', [
      'exec',
      '-i',
      containerName,
      'python',
      moduleName,
    ]);

    let stdout = '';
    let stderr = '';
    let timeoutId: NodeJS.Timeout;

    // Set timeout
    timeoutId = setTimeout(() => {
      proc.kill();
      reject(new Error(`Tool call timed out after ${timeout}ms`));
    }, timeout);

    // Collect stdout
    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    // Collect stderr (but don't fail on it - servers log to stderr)
    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    // Handle process completion
    proc.on('close', (code) => {
      clearTimeout(timeoutId);

      if (code !== 0) {
        reject(new Error(`Docker exec failed with code ${code}: ${stderr}`));
        return;
      }

      // Parse JSON-RPC responses (filter out log lines)
      try {
        const lines = stdout.trim().split('\n').filter(line => line.startsWith('{'));
        
        // For multiple requests, find the last tool call response
        const requestArray = Array.isArray(requests) ? requests : [requests];
        const toolCallId = requestArray[requestArray.length - 1].id;
        
        // Find the response for our tool call
        let toolResponse: any = null;
        for (const line of lines) {
          const response = JSON.parse(line);
          if (response.id === toolCallId) {
            toolResponse = response;
            break;
          }
        }

        if (!toolResponse) {
          reject(new Error('Tool response not found in output'));
          return;
        }

        if (toolResponse.error) {
          reject(new Error(`MCP tool error: ${toolResponse.error.message}`));
          return;
        }

        if (!toolResponse.result) {
          reject(new Error('MCP tool response missing result'));
          return;
        }

        // Extract text content from result
        const content = toolResponse.result.content?.[0]?.text;
        if (!content) {
          reject(new Error('No content in tool response'));
          return;
        }

        resolve(content);
      } catch (error: any) {
        reject(new Error(`Failed to parse MCP response: ${error.message}. Output: ${stdout}`));
      }
    });

    // Handle process errors
    proc.on('error', (error) => {
      clearTimeout(timeoutId);
      reject(new Error(`Failed to spawn docker exec: ${error.message}`));
    });

    // Send JSON-RPC request(s) via stdin
    const requestArray = Array.isArray(requests) ? requests : [requests];
    for (const req of requestArray) {
      proc.stdin.write(JSON.stringify(req) + '\n');
    }
    proc.stdin.end();
  });
}

/**
 * Check if all required Docker containers are running
 * 
 * @returns Array of missing container names (empty if all are running)
 * 
 * @example
 * ```typescript
 * const missing = await checkContainers();
 * if (missing.length > 0) {
 *   console.error(`Missing containers: ${missing.join(', ')}`);
 * }
 * ```
 */
export async function checkContainers(): Promise<string[]> {
  const missing: string[] = [];

  for (const [serverName, containerName] of Object.entries(CONTAINER_MAP)) {
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

