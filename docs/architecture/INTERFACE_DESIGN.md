# Interface Design Architecture

## Overview

This document defines the robust interface contracts between all layers of the MCP code execution system, ensuring consistency, type safety, and maintainability across the entire stack.

## 🏗️ Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 1: Client Layer (Claude Desktop)                             │
│ Protocol: MCP JSON-RPC 2.0 over stdio                              │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ IClientProtocol
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 2: Execution Sandbox (Node.js VM)                            │
│ Interface: IExecutionContext                                        │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ IToolModule
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 3: Tool Wrappers (TypeScript/JavaScript)                     │
│ Interface: IToolWrapper, IServerModule                              │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ IMCPBridge
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 4: MCP Server Containers (Docker + Python)                   │
│ Protocol: MCP JSON-RPC 2.0 via docker exec                         │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │ IMCPToolHandler
                                      ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 5: Python Tool Implementation                                │
│ Interface: IToolImplementation                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Core Interface Definitions

### 1. Layer 1-2: Client to Execution Sandbox

#### IClientProtocol
```typescript
// Location: code-execution/src/types/client.protocol.ts

/**
 * Standard MCP JSON-RPC 2.0 protocol for client communication
 */
interface IMCPRequest {
  jsonrpc: "2.0";
  id: number | string;
  method: string;
  params?: Record<string, unknown>;
}

interface IMCPResponse {
  jsonrpc: "2.0";
  id: number | string;
  result?: unknown;
  error?: IMCPError;
}

interface IMCPError {
  code: number;
  message: string;
  data?: unknown;
}

/**
 * Execute code tool request
 */
interface IExecuteCodeRequest extends IMCPRequest {
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
interface IExecuteCodeResponse extends IMCPResponse {
  result: {
    content: Array<{
      type: "text";
      text: string;
    }>;
    isError?: boolean;
  };
}

/**
 * Standard error codes
 */
enum MCPErrorCode {
  ParseError = -32700,
  InvalidRequest = -32600,
  MethodNotFound = -32601,
  InvalidParams = -32602,
  InternalError = -32603,
  ExecutionTimeout = -32001,
  ExecutionError = -32002,
  OutputTooLarge = -32003,
  SecurityViolation = -32004,
}
```

### 2. Layer 2: Execution Context

#### IExecutionContext
```typescript
// Location: code-execution/src/types/execution.context.ts

/**
 * Execution context provided to user code
 */
interface IExecutionContext {
  // Helper functions
  parseFastaStats: typeof parseFastaStats;
  filterAndSave: typeof filterAndSave;
  formatBytes: typeof formatBytes;
  
  // Dynamic tool modules (loaded at runtime)
  [serverName: string]: IServerModule;
}

/**
 * Server module interface (e.g., database, processing, alignment)
 */
interface IServerModule {
  [toolName: string]: IToolFunction;
}

/**
 * Tool function signature
 */
type IToolFunction<TInput = unknown, TOutput = unknown> = (
  input: TInput
) => Promise<TOutput>;

/**
 * Execution result
 */
interface IExecutionResult {
  success: boolean;
  data?: unknown;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
  stats: {
    executionTime: number;
    memoryUsed: number;
    outputSize: number;
  };
}

/**
 * Execution options
 */
interface IExecutionOptions {
  timeout: number;
  maxOutputSize: number;
  workspacePath: string;
  allowedModules: string[];
  enablePIITokenization: boolean;
}
```

### 3. Layer 3: Tool Wrappers

#### IToolWrapper
```typescript
// Location: workspace/lib/types/tool.wrapper.ts

/**
 * Standard tool wrapper interface
 */
interface IToolWrapper<TInput = unknown, TOutput = unknown> {
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
   * Sanitize input (type coercion, etc.)
   */
  sanitizeInput(input: unknown): TInput;
}

/**
 * Tool schema (JSON Schema subset)
 */
interface IToolSchema {
  type: "object";
  properties: Record<string, ISchemaProperty>;
  required?: string[];
  additionalProperties?: boolean;
}

interface ISchemaProperty {
  type: "string" | "number" | "boolean" | "array" | "object";
  description?: string;
  enum?: unknown[];
  items?: ISchemaProperty;
  properties?: Record<string, ISchemaProperty>;
  default?: unknown;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
}

/**
 * Validation result
 */
interface IValidationResult<T = unknown> {
  valid: boolean;
  data?: T;
  errors?: Array<{
    path: string;
    message: string;
    expected: string;
    received: unknown;
  }>;
}

/**
 * Tool metadata
 */
interface IToolMetadata {
  name: string;
  description: string;
  category: string;
  version: string;
  author?: string;
  tags?: string[];
  examples?: Array<{
    description: string;
    input: unknown;
    output: unknown;
  }>;
}
```

#### IServerModule (Extended)
```typescript
// Location: workspace/lib/types/server.module.ts

/**
 * Server module interface with metadata
 */
interface IServerModuleDefinition {
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
   * Container configuration
   */
  readonly container: IContainerConfig;
  
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

interface IContainerConfig {
  name: string;
  image: string;
  port?: number;
  entrypoint: string;
  healthCheck?: IHealthCheck;
}

interface IHealthCheck {
  command: string;
  interval: number;
  timeout: number;
  retries: number;
}
```

### 4. Layer 3-4: MCP Bridge

#### IMCPBridge
```typescript
// Location: workspace/lib/types/mcp.bridge.ts

/**
 * MCP bridge interface for communicating with Python containers
 */
interface IMCPBridge {
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
   * Close connection
   */
  close(serverName: string): Promise<void>;
}

interface IInitializeResult {
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

interface IToolCallResult {
  content: Array<{
    type: "text" | "image" | "resource";
    text?: string;
    data?: string;
    mimeType?: string;
  }>;
  isError: boolean;
}

interface IToolInfo {
  name: string;
  description: string;
  inputSchema: IToolSchema;
}

interface IHealthStatus {
  status: "healthy" | "unhealthy" | "degraded";
  message?: string;
  lastChecked: string;
}
```

#### IMCPTransport
```typescript
// Location: workspace/lib/types/mcp.transport.ts

/**
 * Transport layer for MCP communication
 */
interface IMCPTransport {
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
}

/**
 * Docker exec transport (current implementation)
 */
interface IDockerExecTransport extends IMCPTransport {
  containerName: string;
  entrypoint: string;
  timeout: number;
}

/**
 * HTTP transport (future option)
 */
interface IHTTPTransport extends IMCPTransport {
  baseUrl: string;
  headers?: Record<string, string>;
  timeout: number;
}

/**
 * WebSocket transport (future option)
 */
interface IWebSocketTransport extends IMCPTransport {
  url: string;
  reconnect: boolean;
  reconnectDelay: number;
}

interface ITransportStats {
  requestsSent: number;
  requestsFailed: number;
  averageLatency: number;
  lastError?: string;
}
```

### 5. Layer 4-5: Python MCP Server

#### IMCPToolHandler (Python)
```python
# Location: mcp_servers/shared/types/tool_handler.py

from typing import Any, Dict, Optional, List, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolInput(BaseModel):
    """Base class for tool input validation"""
    pass

class ToolOutput(BaseModel):
    """Base class for tool output validation"""
    pass

class ToolMetadata(BaseModel):
    """Tool metadata"""
    name: str
    description: str
    version: str
    category: str
    tags: List[str] = []
    examples: List[Dict[str, Any]] = []

class ToolHandler(ABC):
    """Abstract base class for tool handlers"""
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Get tool metadata"""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for input validation"""
        pass
    
    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for output validation"""
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> ToolInput:
        """Validate and parse input"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """Execute the tool logic"""
        pass
    
    @abstractmethod
    async def validate_output(self, output_data: Any) -> ToolOutput:
        """Validate and parse output"""
        pass
    
    async def handle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Full execution pipeline with validation"""
        # 1. Validate input
        validated_input = await self.validate_input(input_data)
        
        # 2. Execute
        result = await self.execute(validated_input)
        
        # 3. Validate output
        validated_output = await self.validate_output(result)
        
        # 4. Return as dict
        return validated_output.model_dump()

class ToolError(Exception):
    """Base exception for tool errors"""
    def __init__(self, message: str, code: int = -32000, data: Optional[Any] = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)

class ValidationError(ToolError):
    """Input/output validation error"""
    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        super().__init__(message, code=-32602, data={"errors": errors})

class ExecutionError(ToolError):
    """Tool execution error"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, code=-32000, data={"details": details})

class TimeoutError(ToolError):
    """Tool execution timeout"""
    def __init__(self, timeout: int):
        super().__init__(
            f"Tool execution exceeded timeout of {timeout}s",
            code=-32001
        )
```

#### IServerRegistry (Python)
```python
# Location: mcp_servers/shared/types/server_registry.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import mcp.types as types

@dataclass
class ServerConfig:
    """Server configuration"""
    name: str
    version: str
    description: str
    capabilities: Dict[str, Any]
    tools: Dict[str, ToolHandler]

class ServerRegistry:
    """Central registry for MCP servers"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.tools: Dict[str, ToolHandler] = {}
    
    def register_tool(self, handler: ToolHandler) -> None:
        """Register a tool handler"""
        name = handler.metadata.name
        if name in self.tools:
            raise ValueError(f"Tool {name} already registered")
        self.tools[name] = handler
    
    def get_tool(self, name: str) -> Optional[ToolHandler]:
        """Get tool handler by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[types.Tool]:
        """List all tools as MCP Tool objects"""
        return [
            types.Tool(
                name=handler.metadata.name,
                description=handler.metadata.description,
                inputSchema=handler.input_schema
            )
            for handler in self.tools.values()
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> types.CallToolResult:
        """Call a tool by name"""
        handler = self.get_tool(name)
        if not handler:
            raise ToolError(f"Tool {name} not found", code=-32601)
        
        try:
            result = await handler.handle(arguments)
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=str(result)
                    )
                ]
            )
        except ToolError as e:
            raise
        except Exception as e:
            raise ExecutionError(
                message=f"Tool execution failed: {str(e)}",
                details=traceback.format_exc()
            )
```

## 🔄 Standard Patterns

### Pattern 1: Tool Registration

#### TypeScript (Tool Wrapper)
```typescript
// Location: workspace/servers/database/get_sequences.ts

import { ToolWrapper } from '../../lib/tool-wrapper';
import { callMCPTool } from '../../lib/mcp-client';

// Input/Output interfaces
interface GetSequencesInput {
  taxon: string;
  region?: string;
  max_results?: number;
  include_metadata?: boolean;
}

interface GetSequencesOutput {
  sequences: string;
  count: number;
  format: "fasta";
}

// Tool wrapper implementation
export class GetSequencesTool extends ToolWrapper<GetSequencesInput, GetSequencesOutput> {
  readonly toolName = "get_sequences";
  readonly serverName = "database";
  
  readonly inputSchema = {
    type: "object" as const,
    properties: {
      taxon: {
        type: "string" as const,
        description: "Scientific name of organism"
      },
      region: {
        type: "string" as const,
        description: "Gene region (e.g., COI, 16S)",
        default: "COI"
      },
      max_results: {
        type: "number" as const,
        description: "Maximum sequences to retrieve",
        minimum: 1,
        maximum: 10000,
        default: 100
      },
      include_metadata: {
        type: "boolean" as const,
        description: "Include sequence metadata",
        default: false
      }
    },
    required: ["taxon"]
  };
  
  readonly outputSchema = {
    type: "object" as const,
    properties: {
      sequences: {
        type: "string" as const,
        description: "FASTA formatted sequences"
      },
      count: {
        type: "number" as const,
        description: "Number of sequences"
      },
      format: {
        type: "string" as const,
        enum: ["fasta"]
      }
    },
    required: ["sequences", "count", "format"]
  };
  
  async execute(input: GetSequencesInput): Promise<GetSequencesOutput> {
    // Sanitize input
    const sanitized = this.sanitizeInput(input);
    
    // Validate input
    const validation = this.validateInput(sanitized);
    if (!validation.valid) {
      throw new ValidationError("Invalid input", validation.errors!);
    }
    
    // Call MCP tool
    const result = await callMCPTool(this.toolId, validation.data);
    
    // Validate output
    const outputValidation = this.validateOutput(result);
    if (!outputValidation.valid) {
      throw new ValidationError("Invalid output", outputValidation.errors!);
    }
    
    return outputValidation.data!;
  }
}

// Export convenience function
export const getSequences = (input: GetSequencesInput) => 
  new GetSequencesTool().execute(input);
```

#### Python (Tool Handler)
```python
# Location: mcp_servers/database_server/tools/get_sequences.py

from typing import Optional
from pydantic import BaseModel, Field, validator
from mcp_servers.shared.types.tool_handler import (
    ToolHandler, ToolMetadata, ToolInput, ToolOutput, ValidationError
)
from ..services.sequence_fetcher import fetch_sequences

class GetSequencesInput(ToolInput):
    """Input schema for get_sequences tool"""
    taxon: str = Field(..., description="Scientific name of organism")
    region: str = Field("COI", description="Gene region (e.g., COI, 16S)")
    max_results: int = Field(
        100,
        ge=1,
        le=10000,
        description="Maximum sequences to retrieve"
    )
    include_metadata: bool = Field(
        False,
        description="Include sequence metadata"
    )
    
    @validator('taxon')
    def validate_taxon(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Taxon cannot be empty")
        return v.strip()

class GetSequencesOutput(ToolOutput):
    """Output schema for get_sequences tool"""
    sequences: str = Field(..., description="FASTA formatted sequences")
    count: int = Field(..., description="Number of sequences")
    format: str = Field("fasta", description="Output format")

class GetSequencesHandler(ToolHandler):
    """Handler for get_sequences tool"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_sequences",
            description="Retrieve DNA sequences from public databases",
            version="1.0.0",
            category="database",
            tags=["sequences", "ncbi", "bold", "retrieval"],
            examples=[
                {
                    "description": "Get 100 COI sequences for Salmo salar",
                    "input": {
                        "taxon": "Salmo salar",
                        "region": "COI",
                        "max_results": 100
                    },
                    "output": {
                        "sequences": ">seq1\nACGT...",
                        "count": 100,
                        "format": "fasta"
                    }
                }
            ]
        )
    
    @property
    def input_schema(self) -> dict:
        return GetSequencesInput.schema()
    
    @property
    def output_schema(self) -> dict:
        return GetSequencesOutput.schema()
    
    async def validate_input(self, input_data: dict) -> GetSequencesInput:
        try:
            return GetSequencesInput(**input_data)
        except Exception as e:
            raise ValidationError(f"Input validation failed: {str(e)}", [])
    
    async def execute(self, input_data: GetSequencesInput) -> GetSequencesOutput:
        # Call service layer
        sequences = await fetch_sequences(
            taxon=input_data.taxon,
            region=input_data.region,
            max_results=input_data.max_results,
            include_metadata=input_data.include_metadata
        )
        
        return GetSequencesOutput(
            sequences=sequences.to_fasta(),
            count=len(sequences),
            format="fasta"
        )
    
    async def validate_output(self, output_data: Any) -> GetSequencesOutput:
        if isinstance(output_data, GetSequencesOutput):
            return output_data
        try:
            return GetSequencesOutput(**output_data)
        except Exception as e:
            raise ValidationError(f"Output validation failed: {str(e)}", [])
```

### Pattern 2: Error Handling

#### Standard Error Hierarchy
```typescript
// Location: workspace/lib/errors.ts

/**
 * Base error class for all MCP errors
 */
export class MCPError extends Error {
  constructor(
    message: string,
    public code: number,
    public data?: unknown
  ) {
    super(message);
    this.name = this.constructor.name;
  }
  
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      data: this.data
    };
  }
}

export class ValidationError extends MCPError {
  constructor(message: string, public errors: IValidationError[]) {
    super(message, -32602, { errors });
  }
}

export class ExecutionError extends MCPError {
  constructor(message: string, details?: string) {
    super(message, -32000, { details });
  }
}

export class TimeoutError extends MCPError {
  constructor(timeout: number) {
    super(`Execution timeout after ${timeout}ms`, -32001);
  }
}

export class TransportError extends MCPError {
  constructor(message: string, transportType: string) {
    super(message, -32003, { transportType });
  }
}

export class ContainerError extends MCPError {
  constructor(message: string, containerName: string) {
    super(message, -32004, { containerName });
  }
}

/**
 * Error handler with retry logic
 */
export class ErrorHandler {
  async withRetry<T>(
    fn: () => Promise<T>,
    options: {
      maxRetries: number;
      backoff: number;
      shouldRetry: (error: Error) => boolean;
    }
  ): Promise<T> {
    let lastError: Error;
    
    for (let i = 0; i <= options.maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        
        if (i === options.maxRetries || !options.shouldRetry(lastError)) {
          throw lastError;
        }
        
        await this.delay(options.backoff * Math.pow(2, i));
      }
    }
    
    throw lastError!;
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### Pattern 3: Logging & Observability

```typescript
// Location: workspace/lib/logger.ts

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

export interface ILogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

export class Logger {
  constructor(
    private component: string,
    private minLevel: LogLevel = LogLevel.INFO
  ) {}
  
  debug(message: string, context?: Record<string, unknown>) {
    this.log(LogLevel.DEBUG, message, context);
  }
  
  info(message: string, context?: Record<string, unknown>) {
    this.log(LogLevel.INFO, message, context);
  }
  
  warn(message: string, context?: Record<string, unknown>) {
    this.log(LogLevel.WARN, message, context);
  }
  
  error(message: string, error?: Error, context?: Record<string, unknown>) {
    this.log(LogLevel.ERROR, message, {
      ...context,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } : undefined
    });
  }
  
  private log(level: LogLevel, message: string, context?: Record<string, unknown>) {
    if (level < this.minLevel) return;
    
    const entry: ILogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message: `[${this.component}] ${message}`,
      context
    };
    
    // Output to stderr for logging
    console.error(JSON.stringify(entry));
  }
}

/**
 * Performance tracking
 */
export class PerformanceTracker {
  private spans: Map<string, number> = new Map();
  
  startSpan(name: string) {
    this.spans.set(name, Date.now());
  }
  
  endSpan(name: string): number {
    const start = this.spans.get(name);
    if (!start) return 0;
    
    const duration = Date.now() - start;
    this.spans.delete(name);
    return duration;
  }
  
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    this.startSpan(name);
    try {
      return await fn();
    } finally {
      const duration = this.endSpan(name);
      logger.debug(`Performance: ${name} took ${duration}ms`);
    }
  }
}

const logger = new Logger('MCP-System');
export const perf = new PerformanceTracker();
```

### Pattern 4: Configuration Management

```typescript
// Location: workspace/lib/config.ts

export interface IServerConfig {
  name: string;
  container: string;
  entrypoint: string;
  port?: number;
  timeout: number;
  retries: number;
  healthCheck: {
    enabled: boolean;
    interval: number;
  };
}

export interface ISystemConfig {
  execution: {
    timeout: number;
    maxOutputSize: number;
    allowedModules: string[];
  };
  transport: {
    type: "docker-exec" | "http" | "websocket";
    timeout: number;
  };
  logging: {
    level: LogLevel;
    destination: "stdout" | "stderr" | "file";
  };
  servers: Record<string, IServerConfig>;
}

export class ConfigManager {
  private static instance: ConfigManager;
  private config: ISystemConfig;
  
  private constructor() {
    this.config = this.loadConfig();
  }
  
  static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }
  
  private loadConfig(): ISystemConfig {
    // Load from environment variables
    return {
      execution: {
        timeout: parseInt(process.env.EXECUTION_TIMEOUT || "30000"),
        maxOutputSize: parseInt(process.env.MAX_OUTPUT_SIZE || "1048576"),
        allowedModules: (process.env.ALLOWED_MODULES || "").split(",")
      },
      transport: {
        type: (process.env.TRANSPORT_TYPE || "docker-exec") as any,
        timeout: parseInt(process.env.TRANSPORT_TIMEOUT || "30000")
      },
      logging: {
        level: parseInt(process.env.LOG_LEVEL || "1"),
        destination: (process.env.LOG_DESTINATION || "stderr") as any
      },
      servers: {
        database: {
          name: "database",
          container: "ndiag-database-server",
          entrypoint: "python3 /app/database_mcp_server.py",
          timeout: 30000,
          retries: 3,
          healthCheck: {
            enabled: true,
            interval: 60000
          }
        },
        processing: {
          name: "processing",
          container: "ndiag-processing-server",
          entrypoint: "python3 /app/processing_mcp_server.py",
          timeout: 60000,
          retries: 3,
          healthCheck: {
            enabled: true,
            interval: 60000
          }
        },
        alignment: {
          name: "alignment",
          container: "ndiag-alignment-server",
          entrypoint: "python3 /app/alignment_mcp_server.py",
          timeout: 120000,
          retries: 3,
          healthCheck: {
            enabled: true,
            interval: 60000
          }
        },
        design: {
          name: "design",
          container: "ndiag-design-server",
          entrypoint: "python3 /app/design_mcp_server.py",
          timeout: 60000,
          retries: 3,
          healthCheck: {
            enabled: true,
            interval: 60000
          }
        },
        validation: {
          name: "validation",
          container: "ndiag-validation-server",
          entrypoint: "python3 /app/validation_mcp_server.py",
          timeout: 60000,
          retries: 3,
          healthCheck: {
            enabled: true,
            interval: 60000
          }
        }
      }
    };
  }
  
  getServerConfig(serverName: string): IServerConfig {
    const config = this.config.servers[serverName];
    if (!config) {
      throw new Error(`Server ${serverName} not configured`);
    }
    return config;
  }
  
  get executionConfig() {
    return this.config.execution;
  }
  
  get transportConfig() {
    return this.config.transport;
  }
  
  get loggingConfig() {
    return this.config.logging;
  }
}
```

## 🧪 Testing Patterns

### Unit Testing (Tool Wrapper)
```typescript
// Location: workspace/servers/database/__tests__/get_sequences.test.ts

import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { GetSequencesTool } from '../get_sequences';
import { ValidationError } from '../../../lib/errors';

describe('GetSequencesTool', () => {
  let tool: GetSequencesTool;
  
  beforeEach(() => {
    tool = new GetSequencesTool();
  });
  
  describe('input validation', () => {
    it('should validate correct input', () => {
      const input = {
        taxon: "Salmo salar",
        region: "COI",
        max_results: 100
      };
      
      const result = tool.validateInput(input);
      expect(result.valid).toBe(true);
      expect(result.data).toEqual(input);
    });
    
    it('should reject missing required fields', () => {
      const input = {
        region: "COI"
      };
      
      const result = tool.validateInput(input);
      expect(result.valid).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors![0].path).toBe('taxon');
    });
    
    it('should sanitize string numbers', () => {
      const input = {
        taxon: "Salmo salar",
        max_results: "100" as any
      };
      
      const sanitized = tool.sanitizeInput(input);
      expect(typeof sanitized.max_results).toBe('number');
      expect(sanitized.max_results).toBe(100);
    });
  });
  
  describe('output validation', () => {
    it('should validate correct output', () => {
      const output = {
        sequences: ">seq1\nACGT",
        count: 1,
        format: "fasta"
      };
      
      const result = tool.validateOutput(output);
      expect(result.valid).toBe(true);
    });
  });
});
```

### Integration Testing (MCP Bridge)
```typescript
// Location: workspace/lib/__tests__/mcp-bridge.integration.test.ts

import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import { MCPBridge } from '../mcp-bridge';
import { execAsync } from '../utils';

describe('MCPBridge Integration', () => {
  let bridge: MCPBridge;
  
  beforeAll(async () => {
    bridge = new MCPBridge();
    
    // Ensure containers are running
    const { stdout } = await execAsync('docker ps --format "{{.Names}}"');
    const containers = stdout.trim().split('\n');
    expect(containers).toContain('ndiag-database-server');
  });
  
  afterAll(async () => {
    await bridge.close('database');
  });
  
  it('should initialize connection', async () => {
    const result = await bridge.initialize('database');
    expect(result.protocolVersion).toBe('2024-11-05');
    expect(result.serverInfo.name).toBe('database');
  });
  
  it('should list tools', async () => {
    const tools = await bridge.listTools('database');
    expect(tools.length).toBeGreaterThan(0);
    expect(tools.some(t => t.name === 'get_sequences')).toBe(true);
  });
  
  it('should call tool successfully', async () => {
    const result = await bridge.callTool('database', 'get_sequences', {
      taxon: "Salmo salar",
      max_results: 10
    });
    
    expect(result.isError).toBe(false);
    expect(result.content).toHaveLength(1);
    expect(result.content[0].type).toBe('text');
  });
  
  it('should handle tool errors', async () => {
    await expect(
      bridge.callTool('database', 'get_sequences', {
        // Missing required field
        region: "COI"
      })
    ).rejects.toThrow(ValidationError);
  });
  
  it('should perform health check', async () => {
    const health = await bridge.healthCheck('database');
    expect(health.status).toBe('healthy');
  });
});
```

### Python Unit Testing
```python
# Location: mcp_servers/database_server/tests/test_get_sequences.py

import pytest
from mcp_servers.database_server.tools.get_sequences import (
    GetSequencesHandler,
    GetSequencesInput,
    GetSequencesOutput
)
from mcp_servers.shared.types.tool_handler import ValidationError

@pytest.fixture
def handler():
    return GetSequencesHandler()

class TestGetSequencesHandler:
    def test_input_validation_success(self, handler):
        input_data = {
            "taxon": "Salmo salar",
            "region": "COI",
            "max_results": 100
        }
        
        result = await handler.validate_input(input_data)
        assert isinstance(result, GetSequencesInput)
        assert result.taxon == "Salmo salar"
    
    def test_input_validation_failure(self, handler):
        input_data = {
            "region": "COI"  # Missing required taxon
        }
        
        with pytest.raises(ValidationError):
            await handler.validate_input(input_data)
    
    def test_input_sanitization(self, handler):
        input_data = {
            "taxon": "  Salmo salar  ",  # Extra whitespace
            "max_results": 100
        }
        
        result = await handler.validate_input(input_data)
        assert result.taxon == "Salmo salar"  # Trimmed
    
    @pytest.mark.integration
    async def test_execute(self, handler):
        input_data = GetSequencesInput(
            taxon="Salmo salar",
            region="COI",
            max_results=10
        )
        
        result = await handler.execute(input_data)
        assert isinstance(result, GetSequencesOutput)
        assert result.count <= 10
        assert result.format == "fasta"
```

## 📊 Versioning Strategy

### Semantic Versioning
```typescript
// Location: workspace/lib/version.ts

export interface IVersion {
  major: number;
  minor: number;
  patch: number;
}

export class VersionManager {
  static parse(version: string): IVersion {
    const parts = version.split('.').map(Number);
    return {
      major: parts[0] || 0,
      minor: parts[1] || 0,
      patch: parts[2] || 0
    };
  }
  
  static isCompatible(required: string, actual: string): boolean {
    const req = this.parse(required);
    const act = this.parse(actual);
    
    // Major version must match
    if (req.major !== act.major) return false;
    
    // Minor version must be >= required
    if (act.minor < req.minor) return false;
    
    // Patch version doesn't matter for compatibility
    return true;
  }
  
  static toString(version: IVersion): string {
    return `${version.major}.${version.minor}.${version.patch}`;
  }
}

/**
 * Tool version metadata
 */
export interface IToolVersion {
  toolName: string;
  version: IVersion;
  deprecated: boolean;
  deprecationMessage?: string;
  replacedBy?: string;
}
```

## 🚀 Extension Mechanisms

### Adding a New Server

#### 1. Define Server Configuration
```typescript
// Location: workspace/config/servers/new-server.config.ts

export const newServerConfig: IServerConfig = {
  name: "phylogenetics",
  container: "ndiag-phylogenetics-server",
  entrypoint: "python3 /app/phylogenetics_mcp_server.py",
  timeout: 120000,
  retries: 3,
  healthCheck: {
    enabled: true,
    interval: 60000
  }
};
```

#### 2. Create Python MCP Server
```python
# Location: mcp_servers/phylogenetics_server/phylogenetics_mcp_server.py

from mcp.server import Server
from mcp_servers.shared.types.server_registry import ServerRegistry, ServerConfig
from .tools.build_tree import BuildTreeHandler
from .tools.calculate_distance import CalculateDistanceHandler

# Create server registry
config = ServerConfig(
    name="phylogenetics",
    version="1.0.0",
    description="Phylogenetic analysis tools",
    capabilities={"tools": {}},
    tools={}
)

registry = ServerRegistry(config)

# Register tools
registry.register_tool(BuildTreeHandler())
registry.register_tool(CalculateDistanceHandler())

# Create MCP server
server = Server("phylogenetics")

@server.list_tools()
async def handle_list_tools():
    return registry.list_tools()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    return await registry.call_tool(name, arguments)

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

#### 3. Generate Tool Wrappers
```bash
# Run tool generator
npm run generate:tools -- --server phylogenetics
```

#### 4. Update docker-compose
```yaml
# Add to docker-compose.autogen.yml
phylogenetics-server:
  build: ./mcp_servers/phylogenetics_server
  container_name: ndiag-phylogenetics-server
  volumes:
    - ./results:/results
  networks:
    - mcp-network
```

### Adding a New Tool

#### 1. Implement Python Handler
```python
# Location: mcp_servers/database_server/tools/new_tool.py

class NewToolHandler(ToolHandler):
    # Implement required methods...
    pass
```

#### 2. Register in Server
```python
# Location: mcp_servers/database_server/database_mcp_server.py

from .tools.new_tool import NewToolHandler

registry.register_tool(NewToolHandler())
```

#### 3. Regenerate Wrappers
```bash
npm run generate:tools -- --server database
```

## 📈 Performance Optimization

### Caching Strategy
```typescript
// Location: workspace/lib/cache.ts

export interface ICacheEntry<T> {
  value: T;
  expires: number;
}

export class Cache<T> {
  private store: Map<string, ICacheEntry<T>> = new Map();
  
  constructor(private ttl: number = 60000) {}
  
  set(key: string, value: T): void {
    this.store.set(key, {
      value,
      expires: Date.now() + this.ttl
    });
  }
  
  get(key: string): T | undefined {
    const entry = this.store.get(key);
    if (!entry) return undefined;
    
    if (Date.now() > entry.expires) {
      this.store.delete(key);
      return undefined;
    }
    
    return entry.value;
  }
  
  has(key: string): boolean {
    return this.get(key) !== undefined;
  }
  
  clear(): void {
    this.store.clear();
  }
}

// Schema caching
export const schemaCache = new Cache<IToolSchema>(300000); // 5 minutes

// Tool list caching
export const toolListCache = new Cache<IToolInfo[]>(600000); // 10 minutes
```

### Connection Pooling
```typescript
// Location: workspace/lib/connection-pool.ts

export class ConnectionPool {
  private connections: Map<string, IMCPBridge> = new Map();
  private maxConnections: number = 5;
  
  async getConnection(serverName: string): Promise<IMCPBridge> {
    let connection = this.connections.get(serverName);
    
    if (!connection || !connection.isConnected()) {
      connection = await this.createConnection(serverName);
      this.connections.set(serverName, connection);
    }
    
    return connection;
  }
  
  private async createConnection(serverName: string): Promise<IMCPBridge> {
    const bridge = new MCPBridge();
    await bridge.initialize(serverName);
    return bridge;
  }
  
  async closeAll(): Promise<void> {
    for (const [serverName, connection] of this.connections) {
      await connection.close(serverName);
    }
    this.connections.clear();
  }
}
```

## 🔐 Security Best Practices

### Input Sanitization
```typescript
// Location: workspace/lib/sanitizer.ts

export class InputSanitizer {
  /**
   * Remove dangerous characters from strings
   */
  static sanitizeString(input: string): string {
    return input
      .replace(/[<>]/g, '') // Remove HTML tags
      .replace(/[`$]/g, '') // Remove shell metacharacters
      .trim();
  }
  
  /**
   * Coerce string numbers to actual numbers
   */
  static coerceNumber(input: unknown): number | undefined {
    if (typeof input === 'number') return input;
    if (typeof input === 'string' && !isNaN(Number(input))) {
      return Number(input);
    }
    return undefined;
  }
  
  /**
   * Sanitize entire input object
   */
  static sanitize<T extends Record<string, unknown>>(input: T): T {
    const result: any = {};
    
    for (const [key, value] of Object.entries(input)) {
      if (typeof value === 'string') {
        result[key] = this.sanitizeString(value);
      } else if (typeof value === 'object' && value !== null) {
        result[key] = this.sanitize(value as any);
      } else {
        result[key] = value;
      }
    }
    
    return result;
  }
}
```

## 📝 Documentation Generation

### Auto-generate API Docs
```typescript
// Location: scripts/generate-docs.ts

import { IToolWrapper } from '../workspace/lib/types/tool.wrapper';

export class DocGenerator {
  static generateMarkdown(tool: IToolWrapper): string {
    return `
# ${tool.toolName}

${tool.metadata?.description || 'No description'}

## Input Schema

\`\`\`json
${JSON.stringify(tool.inputSchema, null, 2)}
\`\`\`

## Output Schema

\`\`\`json
${JSON.stringify(tool.outputSchema, null, 2)}
\`\`\`

## Examples

${tool.metadata?.examples?.map(ex => `
### ${ex.description}

**Input:**
\`\`\`json
${JSON.stringify(ex.input, null, 2)}
\`\`\`

**Output:**
\`\`\`json
${JSON.stringify(ex.output, null, 2)}
\`\`\`
`).join('\n') || 'No examples available'}
    `.trim();
  }
}
```

---

**Last Updated:** 2025-11-13  
**Version:** 1.0.0  
**Status:** Design Document ✅

