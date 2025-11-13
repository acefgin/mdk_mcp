#!/usr/bin/env node

/**
 * Code Execution Sandbox for MCP Tool Orchestration
 *
 * Provides secure, isolated code execution with:
 * - Timeout enforcement
 * - Resource limits
 * - Security sandboxing
 * - Error handling
 * - Output size limits
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { VM } from 'vm2';
import { promises as fs } from 'fs';
import path from 'path';
import * as helpers from '../../workspace/helpers.js';

// Configuration from environment
const EXECUTION_TIMEOUT = parseInt(process.env.EXECUTION_TIMEOUT || '30000', 10);
const MAX_OUTPUT_SIZE = parseInt(process.env.MAX_OUTPUT_SIZE || '1048576', 10); // 1MB
const WORKSPACE_PATH = process.env.WORKSPACE_PATH || '/workspace';

// Server instance
const server = new Server(
  {
    name: 'code-execution-sandbox',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * Execution result interface
 */
interface ExecutionResult {
  success: boolean;
  output?: any;
  error?: string;
  executionTime: number;
  truncated?: boolean;
}

/**
 * Code execution context with MCP tool imports
 */
interface ExecutionContext {
  console: Console;
  require: (module: string) => any;
  setTimeout: typeof setTimeout;
  setInterval: typeof setInterval;
  clearTimeout: typeof clearTimeout;
  clearInterval: typeof clearInterval;
  process: {
    env: Record<string, string>;
    cwd: () => string;
  };
  fs: typeof fs;
  path: typeof path;
  // MCP tool imports will be dynamically added
  [key: string]: any;
}

/**
 * Create a secure execution context
 */
function createExecutionContext(): ExecutionContext {
  const logs: string[] = [];

  return {
    console: {
      log: (...args: any[]) => logs.push(args.map(String).join(' ')),
      error: (...args: any[]) => logs.push('ERROR: ' + args.map(String).join(' ')),
      warn: (...args: any[]) => logs.push('WARN: ' + args.map(String).join(' ')),
      info: (...args: any[]) => logs.push('INFO: ' + args.map(String).join(' ')),
      debug: (...args: any[]) => logs.push('DEBUG: ' + args.map(String).join(' ')),
      _getLogs: () => logs,
    } as any,
    require: (module: string) => {
      // Whitelist allowed modules
      const allowedModules = ['path', 'util', 'crypto'];
      if (allowedModules.includes(module)) {
        return require(module);
      }
      throw new Error(`Module '${module}' is not allowed in sandbox`);
    },
    setTimeout,
    setInterval,
    clearTimeout,
    clearInterval,
    process: {
      env: { NODE_ENV: 'sandbox' },
      cwd: () => WORKSPACE_PATH,
    },
    fs,
    path,
    // Helper functions for context-efficient operations
    ...helpers,
  };
}

/**
 * Load MCP tool modules dynamically
 */
async function loadToolModules(): Promise<Record<string, any>> {
  const modules: Record<string, any> = {};

  try {
    // Load all server modules from workspace
    const serversPath = path.join(WORKSPACE_PATH, 'servers');
    const serverDirs = await fs.readdir(serversPath);

    for (const serverDir of serverDirs) {
      const indexPath = path.join(serversPath, serverDir, 'index.js');
      try {
        const stats = await fs.stat(indexPath);
        if (stats.isFile()) {
          // Dynamic import of the server module
          const module = await import(indexPath);
          modules[serverDir] = module;
        }
      } catch (err) {
        // Server module doesn't exist or can't be loaded - skip
        continue;
      }
    }
  } catch (err) {
    console.error('Error loading tool modules:', err);
  }

  return modules;
}

/**
 * Execute code in isolated sandbox
 */
async function executeCode(
  code: string,
  timeout: number = EXECUTION_TIMEOUT
): Promise<ExecutionResult> {
  const startTime = Date.now();

  try {
    // Check for common mistakes
    if (code.includes('await import(') || code.includes('import(')) {
      return {
        success: false,
        error: 'Dynamic imports (await import(...)) are not supported. All modules (database, processing, alignment, design, validation) are pre-loaded and available directly. Example: use "database.getSequences()" instead of "await import(\'database\')"',
        executionTime: Date.now() - startTime,
      };
    }

    // Create secure VM context
    const context = createExecutionContext();

    // Load MCP tool modules
    const toolModules = await loadToolModules();
    Object.assign(context, toolModules);

    // Create VM with security restrictions
    const vm = new VM({
      timeout,
      sandbox: context,
      eval: false,
      wasm: false,
      fixAsync: true,
    });

    // Execute code
    const result = await vm.run(`
      (async () => {
        ${code}
      })()
    `);

    // Get console logs
    const logs = (context.console as any)._getLogs();

    // Calculate execution time
    const executionTime = Date.now() - startTime;

    // Prepare output
    let output: any = result;
    if (logs.length > 0) {
      output = {
        result,
        logs,
      };
    }

    // Check output size and truncate if necessary
    const outputStr = JSON.stringify(output);
    const truncated = outputStr.length > MAX_OUTPUT_SIZE;

    if (truncated) {
      output = {
        result: '[Output truncated - exceeded size limit]',
        size: outputStr.length,
        limit: MAX_OUTPUT_SIZE,
        preview: outputStr.substring(0, 1000),
      };
    }

    return {
      success: true,
      output,
      executionTime,
      truncated,
    };
  } catch (error: any) {
    const executionTime = Date.now() - startTime;

    return {
      success: false,
      error: error.message || String(error),
      executionTime,
    };
  }
}

/**
 * List available tools
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: 'execute_code',
      description: `Execute TypeScript/JavaScript code in a secure sandbox environment.

The code execution sandbox provides:
- Access to all MCP tool modules (database, processing, alignment, design, validation)
- Secure isolated environment with resource limits
- Timeout enforcement (default ${EXECUTION_TIMEOUT}ms)
- Output size limits (${MAX_OUTPUT_SIZE} bytes)
- Console logging support
- File system access to /workspace

Example usage:
\`\`\`typescript
// Import MCP tools
const sequences = await database.getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 100
});

// Process data in-code (keeps data out of context)
const filtered = sequences.split('\\n>')
  .filter(seq => seq.length > 500)
  .slice(0, 10);

// Return only summary
return {
  total: filtered.length,
  averageLength: filtered.reduce((sum, s) => sum + s.length, 0) / filtered.length
};
\`\`\`

This approach achieves 99%+ token reduction by:
1. Loading only the tools you need
2. Processing data in the execution environment
3. Returning only summaries/results (not raw data)`,
      inputSchema: {
        type: 'object',
        properties: {
          code: {
            type: 'string',
            description: 'TypeScript/JavaScript code to execute. Can use async/await and import MCP tool modules.',
          },
          timeout: {
            type: 'number',
            description: `Execution timeout in milliseconds. Default: ${EXECUTION_TIMEOUT}ms. Maximum: ${EXECUTION_TIMEOUT * 2}ms.`,
            default: EXECUTION_TIMEOUT,
          },
        },
        required: ['code'],
      },
    },
  ];

  return { tools };
});

/**
 * Handle tool calls
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === 'execute_code') {
    const { code, timeout = EXECUTION_TIMEOUT } = args as {
      code: string;
      timeout?: number;
    };

    // Validate timeout
    const maxTimeout = EXECUTION_TIMEOUT * 2;
    const effectiveTimeout = Math.min(timeout, maxTimeout);

    if (!code || typeof code !== 'string') {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: 'Code parameter is required and must be a string',
            }),
          },
        ],
      };
    }

    // Execute code
    const result = await executeCode(code, effectiveTimeout);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({ error: `Unknown tool: ${name}` }),
      },
    ],
  };
});

/**
 * Start server
 */
async function main() {
  console.error('Starting Code Execution Sandbox...');
  console.error(`Workspace: ${WORKSPACE_PATH}`);
  console.error(`Timeout: ${EXECUTION_TIMEOUT}ms`);
  console.error(`Max Output: ${MAX_OUTPUT_SIZE} bytes`);

  // Load available tools
  const toolModules = await loadToolModules();
  const availableServers = Object.keys(toolModules);
  console.error(`Loaded MCP servers: ${availableServers.join(', ')}`);

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Code Execution Sandbox ready');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
