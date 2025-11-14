/**
 * Tool Wrapper Types
 * 
 * Standard interfaces for tool wrappers that bridge JavaScript/TypeScript
 * code to Python MCP servers
 */

import { IToolSchema, IValidationResult } from './tool.schema.js';

/**
 * Tool metadata
 */
export interface IToolMetadata {
  name: string;
  description: string;
  category: string;
  version: string;
  author?: string;
  tags?: string[];
  examples?: IToolExample[];
  deprecated?: boolean;
  deprecationMessage?: string;
  replacedBy?: string;
}

/**
 * Tool usage example
 */
export interface IToolExample {
  description: string;
  input: unknown;
  output: unknown;
  notes?: string;
}

/**
 * Standard tool wrapper interface
 */
export interface IToolWrapper<TInput = unknown, TOutput = unknown> {
  /**
   * Tool name (must match MCP server tool name)
   */
  readonly toolName: string;
  
  /**
   * Server name (database, processing, alignment, etc.)
   */
  readonly serverName: string;
  
  /**
   * Full tool ID (serverName__toolName)
   */
  readonly toolId: string;
  
  /**
   * Tool metadata
   */
  readonly metadata?: IToolMetadata;
  
  /**
   * Input schema (JSON Schema)
   */
  readonly inputSchema: IToolSchema;
  
  /**
   * Output schema (JSON Schema)
   */
  readonly outputSchema: IToolSchema;
  
  /**
   * Execute the tool
   */
  execute(input: TInput): Promise<TOutput>;
  
  /**
   * Validate input against schema
   */
  validateInput(input: unknown): IValidationResult<TInput>;
  
  /**
   * Validate output against schema
   */
  validateOutput(output: unknown): IValidationResult<TOutput>;
  
  /**
   * Sanitize input (type coercion, trimming, etc.)
   */
  sanitizeInput(input: unknown): TInput;
}

/**
 * Server module interface
 */
export interface IServerModule {
  /**
   * Server name
   */
  readonly name: string;
  
  /**
   * Server version
   */
  readonly version: string;
  
  /**
   * Server description
   */
  readonly description: string;
  
  /**
   * Available tools
   */
  readonly tools: Map<string, IToolWrapper>;
  
  /**
   * Get tool by name
   */
  getTool(name: string): IToolWrapper | undefined;
  
  /**
   * List all tool names
   */
  listTools(): string[];
  
  /**
   * Search tools by query
   */
  searchTools(query: string): IToolWrapper[];
  
  /**
   * Get tool schemas
   */
  getSchemas(): Record<string, IToolSchema>;
}

/**
 * Container configuration
 */
export interface IContainerConfig {
  name: string;
  image: string;
  port?: number;
  entrypoint: string;
  healthCheck?: IHealthCheck;
}

/**
 * Health check configuration
 */
export interface IHealthCheck {
  command: string;
  interval: number;
  timeout: number;
  retries: number;
}

