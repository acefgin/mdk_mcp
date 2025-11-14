/**
 * Client Protocol Types
 * 
 * Standard MCP JSON-RPC 2.0 protocol definitions for client-server communication
 */

/**
 * Standard MCP JSON-RPC 2.0 request
 */
export interface IMCPRequest {
  jsonrpc: "2.0";
  id: number | string;
  method: string;
  params?: Record<string, unknown>;
}

/**
 * Standard MCP JSON-RPC 2.0 response
 */
export interface IMCPResponse {
  jsonrpc: "2.0";
  id: number | string;
  result?: unknown;
  error?: IMCPError;
}

/**
 * Standard MCP error object
 */
export interface IMCPError {
  code: number;
  message: string;
  data?: unknown;
}

/**
 * Execute code tool request
 */
export interface IExecuteCodeRequest extends IMCPRequest {
  method: "tools/call";
  params: {
    name: "execute_code";
    arguments: {
      code: string;
      language: "javascript" | "typescript";
      timeout?: number;
      maxOutputSize?: number;
    };
  };
}

/**
 * Execute code tool response
 */
export interface IExecuteCodeResponse extends IMCPResponse {
  result: {
    content: Array<{
      type: "text";
      text: string;
    }>;
    isError?: boolean;
  };
}

/**
 * Standard MCP error codes
 */
export enum MCPErrorCode {
  ParseError = -32700,
  InvalidRequest = -32600,
  MethodNotFound = -32601,
  InvalidParams = -32602,
  InternalError = -32603,
  
  // Custom error codes (starting from -32000)
  ExecutionTimeout = -32001,
  ExecutionError = -32002,
  OutputTooLarge = -32003,
  SecurityViolation = -32004,
  ValidationError = -32005,
  TransportError = -32006,
  ContainerError = -32007,
}

/**
 * MCP initialize request
 */
export interface IInitializeRequest extends IMCPRequest {
  method: "initialize";
  params: {
    protocolVersion: string;
    capabilities: {
      roots?: { listChanged?: boolean };
      sampling?: Record<string, unknown>;
    };
    clientInfo: {
      name: string;
      version: string;
    };
  };
}

/**
 * MCP initialize response
 */
export interface IInitializeResponse extends IMCPResponse {
  result: {
    protocolVersion: string;
    capabilities: {
      tools?: Record<string, unknown>;
      prompts?: Record<string, unknown>;
      resources?: Record<string, unknown>;
    };
    serverInfo: {
      name: string;
      version: string;
    };
  };
}

/**
 * MCP tools/list request
 */
export interface IListToolsRequest extends IMCPRequest {
  method: "tools/list";
  params?: {
    cursor?: string;
  };
}

/**
 * MCP tools/list response
 */
export interface IListToolsResponse extends IMCPResponse {
  result: {
    tools: Array<{
      name: string;
      description: string;
      inputSchema: Record<string, unknown>;
    }>;
    nextCursor?: string;
  };
}

/**
 * MCP tools/call request
 */
export interface ICallToolRequest extends IMCPRequest {
  method: "tools/call";
  params: {
    name: string;
    arguments: Record<string, unknown>;
  };
}

/**
 * MCP tools/call response
 */
export interface ICallToolResponse extends IMCPResponse {
  result: {
    content: Array<{
      type: "text" | "image" | "resource";
      text?: string;
      data?: string;
      mimeType?: string;
    }>;
    isError?: boolean;
  };
}

