# Implementation Guide

## Overview

This guide shows how to implement new MCP tools and servers using the standardized interface architecture. It provides step-by-step instructions and complete code examples.

## Table of Contents

1. [Adding a New Tool to an Existing Server](#adding-a-new-tool)
2. [Creating a New MCP Server](#creating-a-new-server)
3. [Testing Your Implementation](#testing)
4. [Best Practices](#best-practices)

## Adding a New Tool to an Existing Server {#adding-a-new-tool}

### Step 1: Define the Python Tool Handler

Create a new file in your server's `tools/` directory:

**File:** `mcp_servers/database_server/tools/get_species_info.py`

```python
from typing import Optional
from pydantic import BaseModel, Field, validator
from mcp_servers.shared.types import (
    ToolHandler,
    ToolMetadata,
    ToolInput,
    ToolOutput,
    ValidationError,
    ExecutionError
)

# Define input schema using Pydantic
class GetSpeciesInfoInput(ToolInput):
    """Input schema for get_species_info tool"""
    
    species_name: str = Field(
        ...,
        description="Scientific name of the species",
        min_length=3,
        max_length=200
    )
    
    include_taxonomy: bool = Field(
        default=True,
        description="Include full taxonomic classification"
    )
    
    include_distribution: bool = Field(
        default=False,
        description="Include geographic distribution data"
    )
    
    @validator('species_name')
    def validate_species_name(cls, v):
        """Validate species name format"""
        v = v.strip()
        if not v:
            raise ValueError("Species name cannot be empty")
        
        # Basic validation for scientific name format
        parts = v.split()
        if len(parts) < 2:
            raise ValueError("Scientific name must have at least genus and species")
        
        return v


# Define output schema using Pydantic
class GetSpeciesInfoOutput(ToolOutput):
    """Output schema for get_species_info tool"""
    
    species_name: str = Field(..., description="Scientific name")
    common_name: Optional[str] = Field(None, description="Common name")
    taxonomy: Optional[dict] = Field(None, description="Taxonomic classification")
    distribution: Optional[list] = Field(None, description="Geographic distribution")
    sequence_count: int = Field(..., description="Number of available sequences")
    
    class Config:
        schema_extra = {
            "example": {
                "species_name": "Salmo salar",
                "common_name": "Atlantic salmon",
                "taxonomy": {
                    "kingdom": "Animalia",
                    "phylum": "Chordata",
                    "class": "Actinopterygii"
                },
                "sequence_count": 1543
            }
        }


# Implement the tool handler
class GetSpeciesInfoHandler(ToolHandler):
    """Handler for get_species_info tool"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_species_info",
            description="Retrieve comprehensive information about a species",
            version="1.0.0",
            category="database",
            tags=["species", "taxonomy", "information"],
            examples=[
                {
                    "description": "Get basic species info",
                    "input": {
                        "species_name": "Salmo salar",
                        "include_taxonomy": True,
                        "include_distribution": False
                    },
                    "output": {
                        "species_name": "Salmo salar",
                        "common_name": "Atlantic salmon",
                        "taxonomy": {
                            "kingdom": "Animalia",
                            "phylum": "Chordata"
                        },
                        "sequence_count": 1543
                    }
                }
            ]
        )
    
    @property
    def input_schema(self) -> dict:
        return GetSpeciesInfoInput.model_json_schema()
    
    @property
    def output_schema(self) -> dict:
        return GetSpeciesInfoOutput.model_json_schema()
    
    async def validate_input(self, input_data: dict) -> GetSpeciesInfoInput:
        """Validate input"""
        try:
            return GetSpeciesInfoInput(**input_data)
        except Exception as e:
            errors = []
            if hasattr(e, 'errors'):
                errors = [
                    {
                        "path": ".".join(str(loc) for loc in err.get("loc", [])),
                        "message": err.get("msg", ""),
                        "type": err.get("type", "")
                    }
                    for err in e.errors()
                ]
            raise ValidationError(f"Input validation failed: {str(e)}", errors)
    
    async def execute(self, input_data: GetSpeciesInfoInput) -> GetSpeciesInfoOutput:
        """Execute the tool logic"""
        try:
            # Import your service layer
            from ..services.species_service import get_species_info
            
            # Call service to fetch data
            species_data = await get_species_info(
                species_name=input_data.species_name,
                include_taxonomy=input_data.include_taxonomy,
                include_distribution=input_data.include_distribution
            )
            
            # Return validated output
            return GetSpeciesInfoOutput(**species_data)
        
        except Exception as e:
            raise ExecutionError(
                message=f"Failed to retrieve species info: {str(e)}",
                details=traceback.format_exc()
            )
    
    async def validate_output(self, output_data: Any) -> GetSpeciesInfoOutput:
        """Validate output"""
        if isinstance(output_data, GetSpeciesInfoOutput):
            return output_data
        
        try:
            return GetSpeciesInfoOutput(**output_data)
        except Exception as e:
            errors = []
            if hasattr(e, 'errors'):
                errors = [
                    {
                        "path": ".".join(str(loc) for loc in err.get("loc", [])),
                        "message": err.get("msg", ""),
                        "type": err.get("type", "")
                    }
                    for err in e.errors()
                ]
            raise ValidationError(f"Output validation failed: {str(e)}", errors)
```

### Step 2: Register the Tool in Your Server

**File:** `mcp_servers/database_server/database_mcp_server.py`

```python
from mcp.server import Server
from mcp_servers.shared.types import ServerRegistry, ServerConfig

# Import your tool handler
from .tools.get_species_info import GetSpeciesInfoHandler
# ... other imports

# Create server registry
config = ServerConfig(
    name="database",
    version="1.0.0",
    description="Database access and retrieval tools",
    capabilities={"tools": {}}
)

registry = ServerRegistry(config)

# Register all tools
registry.register_tool(GetSpeciesInfoHandler())
# ... register other tools

# Create MCP server
server = Server("database")

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

### Step 3: Generate TypeScript Wrapper

Run the tool generator:

```bash
cd /home/cxl/MDK_Design/mdk_mcp
npm run generate:tools -- --server database
```

This will automatically create:

**File:** `workspace/servers/database/get_species_info.ts`

```typescript
import { ToolWrapperBase } from '../../lib/tool-wrapper.base';
import { IToolSchema, IToolMetadata } from '../../lib/types';
import { callMCPTool } from '../../lib/mcp-client';

// TypeScript interfaces
export interface GetSpeciesInfoInput {
  species_name: string;
  include_taxonomy?: boolean;
  include_distribution?: boolean;
}

export interface GetSpeciesInfoOutput {
  species_name: string;
  common_name?: string;
  taxonomy?: Record<string, any>;
  distribution?: any[];
  sequence_count: number;
}

// Tool wrapper class
export class GetSpeciesInfoTool extends ToolWrapperBase<
  GetSpeciesInfoInput,
  GetSpeciesInfoOutput
> {
  readonly toolName = "get_species_info";
  readonly serverName = "database";
  
  readonly inputSchema: IToolSchema = {
    type: "object",
    properties: {
      species_name: {
        type: "string",
        description: "Scientific name of the species",
        minLength: 3,
        maxLength: 200
      },
      include_taxonomy: {
        type: "boolean",
        description: "Include full taxonomic classification",
        default: true
      },
      include_distribution: {
        type: "boolean",
        description: "Include geographic distribution data",
        default: false
      }
    },
    required: ["species_name"]
  };
  
  readonly outputSchema: IToolSchema = {
    type: "object",
    properties: {
      species_name: { type: "string" },
      common_name: { type: "string" },
      taxonomy: { type: "object" },
      distribution: { type: "array" },
      sequence_count: { type: "number" }
    },
    required: ["species_name", "sequence_count"]
  };
  
  async execute(input: GetSpeciesInfoInput): Promise<GetSpeciesInfoOutput> {
    const result = await callMCPTool(this.toolId, input);
    return result as GetSpeciesInfoOutput;
  }
}

// Convenience function export
export async function getSpeciesInfo(
  input: GetSpeciesInfoInput
): Promise<GetSpeciesInfoOutput> {
  const tool = new GetSpeciesInfoTool();
  return tool.executeWithValidation(input);
}
```

### Step 4: Test Your Tool

```typescript
// In code execution sandbox
const result = await database.getSpeciesInfo({
  species_name: "Salmo salar",
  include_taxonomy: true
});

console.log(result.common_name); // "Atlantic salmon"
console.log(result.sequence_count); // 1543
```

## Creating a New MCP Server {#creating-a-new-server}

### Step 1: Create Directory Structure

```bash
cd /home/cxl/MDK_Design/mdk_mcp/mcp_servers
mkdir -p new_server/{tools,services,tests}
touch new_server/__init__.py
touch new_server/tools/__init__.py
touch new_server/services/__init__.py
```

### Step 2: Create Server Configuration

**File:** `mcp_servers/new_server/config.py`

```python
from mcp_servers.shared.types import ServerConfig

SERVER_CONFIG = ServerConfig(
    name="new_server",
    version="1.0.0",
    description="Description of your new server",
    capabilities={
        "tools": {},
        "prompts": {},
        "resources": {}
    },
    protocol_version="2024-11-05"
)
```

### Step 3: Implement Your Tools

Follow [Step 1](#adding-a-new-tool) above to create tool handlers.

### Step 4: Create Main Server File

**File:** `mcp_servers/new_server/new_server_mcp_server.py`

```python
#!/usr/bin/env python3
"""
New Server MCP Server

Description of what this server does
"""

import asyncio
import logging
from mcp.server import Server
from mcp_servers.shared.types import ServerRegistry

from .config import SERVER_CONFIG
from .tools.my_tool import MyToolHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_server() -> tuple[Server, ServerRegistry]:
    """Create and configure MCP server"""
    
    # Create registry
    registry = ServerRegistry(SERVER_CONFIG)
    
    # Register tools
    try:
        registry.register_tool(MyToolHandler())
        # Add more tools here
        
        logger.info(f"Registered {len(registry.tools)} tools")
    except Exception as e:
        logger.error(f"Failed to register tools: {e}")
        raise
    
    # Create MCP server
    server = Server(SERVER_CONFIG.name)
    
    # Set up handlers
    @server.list_tools()
    async def handle_list_tools():
        """Handle tools/list request"""
        return registry.list_tools()
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        """Handle tools/call request"""
        logger.info(f"Calling tool: {name}")
        return await registry.call_tool(name, arguments)
    
    return server, registry


async def main():
    """Main entry point"""
    try:
        server, registry = create_server()
        
        logger.info(f"Starting {SERVER_CONFIG.name} server v{SERVER_CONFIG.version}")
        logger.info(f"Available tools: {', '.join(registry.list_tool_names())}")
        
        # Run server
        async with server:
            await server.run()
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 5: Create Dockerfile

**File:** `mcp_servers/new_server/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Set environment
ENV PYTHONUNBUFFERED=1

# Run server
CMD ["python3", "-m", "mcp_servers.new_server.new_server_mcp_server"]
```

### Step 6: Add to Docker Compose

**File:** `docker-compose.autogen.yml`

```yaml
services:
  # ... existing services ...
  
  new-server:
    build: ./mcp_servers/new_server
    container_name: ndiag-new-server
    volumes:
      - ./results:/results
      - ./data:/data
    networks:
      - mcp-network
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Step 7: Add Configuration

**File:** `workspace/lib/config.ts`

Add to the `servers` object:

```typescript
newServer: {
  name: 'new_server',
  container: 'ndiag-new-server',
  entrypoint: 'python3 /app/new_server_mcp_server.py',
  timeout: 30000,
  retries: 3,
  healthCheck: {
    enabled: true,
    interval: 60000,
    timeout: 5000
  }
}
```

### Step 8: Generate TypeScript Wrappers

```bash
npm run generate:tools -- --server new_server
```

### Step 9: Build and Start

```bash
docker-compose build new-server
docker-compose up -d new-server
```

## Testing Your Implementation {#testing}

### Python Unit Tests

**File:** `mcp_servers/database_server/tests/test_get_species_info.py`

```python
import pytest
from mcp_servers.database_server.tools.get_species_info import (
    GetSpeciesInfoHandler,
    GetSpeciesInfoInput,
    GetSpeciesInfoOutput
)
from mcp_servers.shared.types import ValidationError

@pytest.fixture
def handler():
    return GetSpeciesInfoHandler()


class TestGetSpeciesInfoHandler:
    """Test suite for get_species_info tool"""
    
    def test_metadata(self, handler):
        """Test tool metadata"""
        metadata = handler.metadata
        assert metadata.name == "get_species_info"
        assert metadata.version == "1.0.0"
        assert metadata.category == "database"
    
    def test_input_schema(self, handler):
        """Test input schema is valid"""
        schema = handler.input_schema
        assert "properties" in schema
        assert "species_name" in schema["properties"]
    
    @pytest.mark.asyncio
    async def test_validate_input_success(self, handler):
        """Test input validation with valid data"""
        input_data = {
            "species_name": "Salmo salar",
            "include_taxonomy": True
        }
        
        result = await handler.validate_input(input_data)
        assert isinstance(result, GetSpeciesInfoInput)
        assert result.species_name == "Salmo salar"
        assert result.include_taxonomy is True
    
    @pytest.mark.asyncio
    async def test_validate_input_missing_required(self, handler):
        """Test input validation fails with missing required field"""
        input_data = {
            "include_taxonomy": True
        }
        
        with pytest.raises(ValidationError) as exc_info:
            await handler.validate_input(input_data)
        
        assert "species_name" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_input_invalid_name(self, handler):
        """Test input validation fails with invalid species name"""
        input_data = {
            "species_name": "X"  # Too short
        }
        
        with pytest.raises(ValidationError):
            await handler.validate_input(input_data)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_execute(self, handler):
        """Integration test for tool execution"""
        input_data = GetSpeciesInfoInput(
            species_name="Salmo salar",
            include_taxonomy=True,
            include_distribution=False
        )
        
        result = await handler.execute(input_data)
        
        assert isinstance(result, GetSpeciesInfoOutput)
        assert result.species_name == "Salmo salar"
        assert result.sequence_count > 0
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, handler):
        """Test full execution pipeline"""
        input_data = {
            "species_name": "Salmo salar",
            "include_taxonomy": True
        }
        
        result = await handler.handle(input_data)
        
        assert isinstance(result, dict)
        assert "species_name" in result
        assert "sequence_count" in result
```

Run tests:

```bash
cd mcp_servers/database_server
pytest tests/ -v
```

### TypeScript Unit Tests

**File:** `workspace/servers/database/__tests__/get_species_info.test.ts`

```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';
import { GetSpeciesInfoTool } from '../get_species_info';
import { ValidationError } from '../../../lib/errors';

describe('GetSpeciesInfoTool', () => {
  let tool: GetSpeciesInfoTool;
  
  beforeEach(() => {
    tool = new GetSpeciesInfoTool();
  });
  
  describe('metadata', () => {
    it('should have correct tool name', () => {
      expect(tool.toolName).toBe('get_species_info');
    });
    
    it('should have correct server name', () => {
      expect(tool.serverName).toBe('database');
    });
    
    it('should have correct tool ID', () => {
      expect(tool.toolId).toBe('database__get_species_info');
    });
  });
  
  describe('input validation', () => {
    it('should validate correct input', () => {
      const input = {
        species_name: 'Salmo salar',
        include_taxonomy: true
      };
      
      const result = tool.validateInput(input);
      expect(result.valid).toBe(true);
      expect(result.data).toEqual(input);
    });
    
    it('should reject missing required fields', () => {
      const input = {
        include_taxonomy: true
      };
      
      const result = tool.validateInput(input);
      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors![0].path).toBe('species_name');
    });
  });
  
  describe('input sanitization', () => {
    it('should coerce types correctly', () => {
      const input = {
        species_name: 'Salmo salar',
        include_taxonomy: 'true' as any  // String instead of boolean
      };
      
      const sanitized = tool.sanitizeInput(input);
      expect(typeof sanitized.include_taxonomy).toBe('boolean');
      expect(sanitized.include_taxonomy).toBe(true);
    });
  });
});
```

Run tests:

```bash
cd workspace
npm test
```

### Integration Testing

Test the full stack:

```bash
# Start all services
docker-compose up -d

# Test tool call
echo '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_species_info",
    "arguments": {
      "species_name": "Salmo salar",
      "include_taxonomy": true
    }
  }
}' | docker exec -i ndiag-database-server python3 /app/database_mcp_server.py
```

## Best Practices {#best-practices}

### 1. Input Validation

- **Always validate** at both TypeScript and Python layers
- Use Pydantic validators for complex validation logic
- Provide clear, actionable error messages
- Use `@validator` decorators for field-specific validation

```python
@validator('email')
def validate_email(cls, v):
    if '@' not in v:
        raise ValueError('Invalid email format')
    return v.lower()
```

### 2. Error Handling

- Use specific error classes (`ValidationError`, `ExecutionError`, `TimeoutError`)
- Always include context in error messages
- Log errors at appropriate levels
- Never swallow exceptions silently

```python
try:
    result = await external_api_call()
except requests.Timeout:
    raise TimeoutError(30, "external API call")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise ExecutionError(str(e), traceback.format_exc())
```

### 3. Documentation

- Add JSDoc/docstrings to all public methods
- Provide usage examples in tool metadata
- Document expected input/output formats
- Keep documentation up-to-date with code changes

```python
@property
def metadata(self) -> ToolMetadata:
    return ToolMetadata(
        name="my_tool",
        description="Clear, concise description of what the tool does",
        examples=[
            {
                "description": "Common use case",
                "input": {...},
                "output": {...}
            }
        ]
    )
```

### 4. Testing

- Write unit tests for validation logic
- Write integration tests for full pipeline
- Test error cases, not just happy path
- Use fixtures and mocks appropriately
- Aim for >80% code coverage

### 5. Performance

- Cache expensive computations
- Use async/await for I/O operations
- Set appropriate timeouts
- Monitor execution time

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_computation(key: str):
    # ... expensive operation
    pass
```

### 6. Security

- Sanitize all inputs
- Never execute arbitrary code
- Use parameterized queries for databases
- Validate file paths to prevent directory traversal
- Log security-relevant events

```python
def sanitize_path(path: str) -> str:
    """Ensure path is within allowed directory"""
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(ALLOWED_DIR):
        raise SecurityError("Path outside allowed directory")
    return abs_path
```

### 7. Logging

- Use structured logging with context
- Log at appropriate levels (DEBUG, INFO, WARN, ERROR)
- Don't log sensitive data (passwords, tokens, etc.)
- Include relevant context (tool name, input IDs, etc.)

```python
logger.info(
    f"Tool {tool_name} completed",
    extra={
        "tool": tool_name,
        "duration_ms": duration,
        "input_id": input_id
    }
)
```

---

**Last Updated:** 2025-11-13  
**Version:** 1.0.0  
**Status:** Implementation Guide ✅

