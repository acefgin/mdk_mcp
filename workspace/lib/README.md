# MCP Library

This directory contains the core library for the MCP (Model Context Protocol) code execution system. It provides standardized interfaces, base classes, and utilities for building robust, scalable MCP tools.

## Directory Structure

```
lib/
├── types/                      # TypeScript type definitions
│   ├── client.protocol.ts      # MCP JSON-RPC protocol types
│   ├── tool.schema.ts          # JSON Schema types
│   ├── tool.wrapper.ts         # Tool wrapper interfaces
│   ├── mcp.bridge.ts           # MCP bridge interfaces
│   └── index.ts                # Barrel export
│
├── errors.ts                   # Error classes and hierarchy
├── sanitizer.ts                # Input sanitization utilities
├── validator.ts                # JSON Schema validator
├── logger.ts                   # Structured logging system
├── config.ts                   # Configuration management
├── tool-wrapper.base.ts        # Base tool wrapper class
├── mcp-client.ts               # MCP client implementation
└── README.md                   # This file
```

## Core Concepts

### 1. Type System

The library uses TypeScript interfaces to define contracts between layers:

- **IToolWrapper**: Interface for tool wrappers that bridge JS to Python
- **IMCPBridge**: Interface for communication with Python MCP servers
- **IToolSchema**: JSON Schema definitions for validation
- **IMCPRequest/Response**: MCP protocol message types

See `types/` directory for all type definitions.

### 2. Tool Wrappers

Tool wrappers provide a standardized way to call Python MCP tools from JavaScript:

```typescript
import { getSequences } from './servers/database';

const result = await getSequences({
  taxon: "Salmo salar",
  region: "COI",
  max_results: 100
});
```

Each tool wrapper:
- Validates inputs against JSON Schema
- Sanitizes and coerces types
- Calls the Python MCP server
- Validates outputs
- Handles errors consistently

### 3. Validation

The library includes a JSON Schema validator that checks:
- Required fields
- Type correctness
- Range constraints (min/max for numbers, min/maxLength for strings)
- Pattern matching (regex)
- Array constraints (minItems, maxItems, uniqueItems)
- Enum values

```typescript
import { validator } from './lib/validator';

const result = validator.validate(data, schema);
if (!result.valid) {
  console.error(result.errors);
}
```

### 4. Error Handling

Standardized error hierarchy:

```
MCPError (base)
├── ValidationError         # Input/output validation failures
├── ExecutionError          # Tool execution failures
├── TimeoutError            # Timeout exceeded
├── TransportError          # Communication failures
├── ContainerError          # Docker container issues
├── SecurityError           # Security violations
└── OutputTooLargeError     # Output size limits
```

All errors include:
- Error code (MCP error codes)
- Descriptive message
- Additional context data
- Stack trace

### 5. Logging

Structured logging with multiple levels:

```typescript
import { logger } from './lib/logger';

logger.info('Operation completed', { duration: 1234 });
logger.error('Operation failed', error, { context: 'additional' });
```

Features:
- Log levels: DEBUG, INFO, WARN, ERROR
- Structured context objects
- Configurable destinations (stdout, stderr, file)
- Pretty printing option
- Automatic sensitive data redaction

### 6. Configuration

Centralized configuration management:

```typescript
import { config } from './lib/config';

const serverConfig = config.getServerConfig('database');
const timeout = config.executionConfig.timeout;
```

Configuration sources (in order of precedence):
1. Environment variables
2. Default values

Environment variables:
- `EXECUTION_TIMEOUT` - Code execution timeout (ms)
- `MAX_OUTPUT_SIZE` - Maximum output size (bytes)
- `LOG_LEVEL` - Logging level (DEBUG|INFO|WARN|ERROR)
- `TRANSPORT_TIMEOUT` - Transport timeout (ms)
- `CACHE_ENABLED` - Enable caching (true|false)

## Usage Examples

### Creating a Tool Wrapper

```typescript
import { ToolWrapperBase } from './lib/tool-wrapper.base';
import { IToolSchema } from './lib/types';
import { callMCPTool } from './lib/mcp-client';

interface MyToolInput {
  param1: string;
  param2?: number;
}

interface MyToolOutput {
  result: string;
}

class MyToolWrapper extends ToolWrapperBase<MyToolInput, MyToolOutput> {
  readonly toolName = "my_tool";
  readonly serverName = "my_server";
  
  readonly inputSchema: IToolSchema = {
    type: "object",
    properties: {
      param1: { type: "string", description: "First parameter" },
      param2: { type: "number", description: "Optional parameter" }
    },
    required: ["param1"]
  };
  
  readonly outputSchema: IToolSchema = {
    type: "object",
    properties: {
      result: { type: "string" }
    },
    required: ["result"]
  };
  
  async execute(input: MyToolInput): Promise<MyToolOutput> {
    return await callMCPTool(this.toolId, input);
  }
}

// Use the tool
const tool = new MyToolWrapper();
const result = await tool.executeWithValidation({
  param1: "value"
});
```

### Using the MCP Client

```typescript
import { MCPBridge } from './lib/mcp-bridge';

const bridge = new MCPBridge();

// Initialize connection
await bridge.initialize('database');

// List available tools
const tools = await bridge.listTools('database');

// Call a tool
const result = await bridge.callTool('database', 'get_sequences', {
  taxon: "Salmo salar"
});

// Health check
const health = await bridge.healthCheck('database');

// Close connection
await bridge.close('database');
```

### Error Handling

```typescript
import { ValidationError, ExecutionError, TimeoutError } from './lib/errors';
import { ErrorHandler } from './lib/errors';

const errorHandler = new ErrorHandler();

// With retry
try {
  const result = await errorHandler.withRetry(
    () => callSomeAPI(),
    {
      maxRetries: 3,
      backoffMs: 1000,
      shouldRetry: (error) => error instanceof TimeoutError
    }
  );
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Validation failed:', error.validationErrors);
  } else if (error instanceof TimeoutError) {
    console.error('Operation timed out');
  } else {
    console.error('Unexpected error:', error);
  }
}

// With timeout
try {
  const result = await errorHandler.withTimeout(
    () => longRunningOperation(),
    30000,
    'long operation'
  );
} catch (error) {
  if (error instanceof TimeoutError) {
    console.error('Operation timed out after 30s');
  }
}
```

### Input Sanitization

```typescript
import { InputSanitizer } from './lib/sanitizer';

// Sanitize strings
const clean = InputSanitizer.sanitizeString('  <script>alert("xss")</script>  ');
// Result: "scriptalert(xss)/script"

// Coerce types
const num = InputSanitizer.coerceNumber('123'); // 123
const bool = InputSanitizer.coerceBoolean('true'); // true
const arr = InputSanitizer.coerceArray('[1,2,3]'); // [1,2,3]

// Sanitize entire object
const sanitized = InputSanitizer.sanitize({
  name: '  John Doe  ',
  age: '30',
  active: 'true'
});
// Result: { name: 'John Doe', age: '30', active: 'true' }
// Note: Type coercion happens based on schema in tool wrapper
```

### Performance Tracking

```typescript
import { perf } from './lib/logger';

// Manual spans
perf.startSpan('operation');
// ... do work ...
const duration = perf.endSpan('operation');

// Async measurement
const result = await perf.measureAsync('fetchData', async () => {
  return await fetchData();
});

// Sync measurement
const result = perf.measure('compute', () => {
  return heavyComputation();
});
```

## Best Practices

### 1. Always Use Validation

```typescript
// Good ✅
const result = await tool.executeWithValidation(input);

// Bad ❌ - skips validation
const result = await tool.execute(input);
```

### 2. Handle Errors Appropriately

```typescript
// Good ✅
try {
  const result = await tool.execute(input);
} catch (error) {
  if (error instanceof ValidationError) {
    // Handle validation errors
  } else if (error instanceof ExecutionError) {
    // Handle execution errors
  } else {
    // Handle unexpected errors
  }
}

// Bad ❌ - swallow all errors
try {
  const result = await tool.execute(input);
} catch (error) {
  // Ignore
}
```

### 3. Use Structured Logging

```typescript
// Good ✅
logger.info('Operation completed', {
  tool: 'get_sequences',
  duration: 1234,
  resultCount: 100
});

// Bad ❌ - unstructured string
logger.info(`Operation completed for get_sequences in 1234ms with 100 results`);
```

### 4. Configure Timeouts Appropriately

```typescript
// Good ✅ - tool-specific timeout
await errorHandler.withTimeout(
  () => alignSequences(data),
  120000,  // 2 minutes for alignment
  'sequence alignment'
);

// Bad ❌ - one timeout for everything
await errorHandler.withTimeout(
  () => operation(),
  30000  // 30s might be too short/long
);
```

### 5. Use Type Guards

```typescript
// Good ✅
function isValidInput(input: unknown): input is MyToolInput {
  return typeof input === 'object' &&
         input !== null &&
         'param1' in input;
}

if (isValidInput(input)) {
  // TypeScript knows input is MyToolInput here
  const result = await tool.execute(input);
}

// Bad ❌ - type assertion without validation
const result = await tool.execute(input as MyToolInput);
```

## Testing

### Unit Tests

```typescript
import { describe, it, expect } from '@jest/globals';

describe('MyToolWrapper', () => {
  it('should validate correct input', () => {
    const tool = new MyToolWrapper();
    const result = tool.validateInput({ param1: 'value' });
    expect(result.valid).toBe(true);
  });
  
  it('should reject invalid input', () => {
    const tool = new MyToolWrapper();
    const result = tool.validateInput({});
    expect(result.valid).toBe(false);
  });
});
```

### Integration Tests

```typescript
import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';

describe('Tool Integration', () => {
  beforeAll(async () => {
    // Start services
  });
  
  afterAll(async () => {
    // Clean up
  });
  
  it('should execute tool successfully', async () => {
    const tool = new MyToolWrapper();
    const result = await tool.executeWithValidation({
      param1: 'value'
    });
    
    expect(result).toBeDefined();
    expect(result.result).toBeTruthy();
  });
});
```

## API Reference

See individual files for detailed API documentation:

- [Types](./types/README.md) - Type definitions
- [Errors](./errors.ts) - Error classes
- [Validator](./validator.ts) - Schema validation
- [Sanitizer](./sanitizer.ts) - Input sanitization
- [Logger](./logger.ts) - Logging system
- [Config](./config.ts) - Configuration
- [Tool Wrapper](./tool-wrapper.base.ts) - Base tool wrapper

## Contributing

When adding new functionality:

1. Define TypeScript interfaces first
2. Implement with proper error handling
3. Add unit tests
4. Update documentation
5. Follow existing patterns and conventions

## Version History

- **1.0.0** (2025-11-13) - Initial release
  - Core type system
  - Base tool wrapper class
  - Validation and sanitization
  - Error handling
  - Logging system
  - Configuration management

---

**Last Updated:** 2025-11-13  
**Version:** 1.0.0  
**Maintainer:** MCP Development Team

