/**
 * MCP Bridge Types
 * 
 * Interfaces for bridging between the execution sandbox and Python MCP servers
 */

import { IMCPRequest, IMCPResponse } from './client.protocol.js';
import { IToolSchema } from './tool.schema.js';

/**
 * MCP bridge interface for communicating with Python containers
 */
export interface IMCPBridge {
  /**
   * Initialize connection to MCP server
   */
  initialize(serverName: string): Promise<IInitializeResult>;
  
  /**
   * Call a tool on the MCP server
   */
  callTool(
    serverName: string,
    toolName: string,
    args: unknown
  ): Promise<IToolCallResult>;
  
  /**
   * List available tools on server
   */
  listTools(serverName: string): Promise<IToolInfo[]>;
  
  /**
   * Get tool schema
   */
  getToolSchema(
    serverName: string,
    toolName: string
  ): Promise<IToolSchema>;
  
  /**
   * Health check
   */
  healthCheck(serverName: string): Promise<IHealthStatus>;
  
  /**
   * Check if connected
   */
  isConnected(serverName?: string): boolean;
  
  /**
   * Close connection
   */
  close(serverName: string): Promise<void>;
  
  /**
   * Close all connections
   */
  closeAll(): Promise<void>;
}

/**
 * Initialize result
 */
export interface IInitializeResult {
  protocolVersion: string;
  serverInfo: {
    name: string;
    version: string;
  };
  capabilities: {
    tools?: Record<string, unknown>;
    prompts?: Record<string, unknown>;
    resources?: Record<string, unknown>;
  };
}

/**
 * Tool call result
 */
export interface IToolCallResult {
  content: Array<{
    type: "text" | "image" | "resource";
    text?: string;
    data?: string;
    mimeType?: string;
  }>;
  isError: boolean;
}

/**
 * Tool information
 */
export interface IToolInfo {
  name: string;
  description: string;
  inputSchema: IToolSchema;
}

/**
 * Health status
 */
export interface IHealthStatus {
  status: "healthy" | "unhealthy" | "degraded";
  message?: string;
  lastChecked: string;
  responseTime?: number;
}

/**
 * Transport layer interface
 */
export interface IMCPTransport {
  /**
   * Send request to MCP server
   */
  send(request: IMCPRequest): Promise<IMCPResponse>;
  
  /**
   * Send batch of requests
   */
  sendBatch(requests: IMCPRequest[]): Promise<IMCPResponse[]>;
  
  /**
   * Check if transport is connected
   */
  isConnected(): boolean;
  
  /**
   * Get transport statistics
   */
  getStats(): ITransportStats;
  
  /**
   * Close transport
   */
  close(): Promise<void>;
}

/**
 * Transport statistics
 */
export interface ITransportStats {
  requestsSent: number;
  requestsFailed: number;
  averageLatency: number;
  lastError?: string;
  lastRequestTime?: string;
}

/**
 * Docker exec transport configuration
 */
export interface IDockerExecTransportConfig {
  containerName: string;
  entrypoint: string;
  timeout: number;
}

/**
 * HTTP transport configuration
 */
export interface IHTTPTransportConfig {
  baseUrl: string;
  headers?: Record<string, string>;
  timeout: number;
}

/**
 * WebSocket transport configuration
 */
export interface IWebSocketTransportConfig {
  url: string;
  reconnect: boolean;
  reconnectDelay: number;
  maxReconnectAttempts: number;
}

/**
 * Transport type
 */
export type TransportType = "docker-exec" | "http" | "websocket";

/**
 * Transport configuration
 */
export type TransportConfig = 
  | { type: "docker-exec"; config: IDockerExecTransportConfig }
  | { type: "http"; config: IHTTPTransportConfig }
  | { type: "websocket"; config: IWebSocketTransportConfig };

