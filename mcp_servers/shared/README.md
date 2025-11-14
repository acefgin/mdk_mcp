# Shared MCP Infrastructure

## Overview

This directory contains shared infrastructure used across all MCP servers in the system.

## Structure

```
shared/
├── ts_src/                    # TypeScript source files
│   ├── types/                 # Type definitions
│   ├── helpers.ts
│   ├── mcp-client.ts
│   ├── pii-tokenizer.ts
│   ├── result-cache.ts
│   ├── tool-generator.ts
│   └── index.ts               # Main export
│
├── dist/                      # Compiled JavaScript (generated)
│
├── py_infra/                  # Python infrastructure
│   ├── types/                 # Base classes
│   │   ├── tool_handler.py
│   │   └── server_registry.py
│   └── utils/                 # Utility functions
│       ├── logging.py
│       └── validation.py
│
├── tests/                     # Test files
├── tsconfig.json              # TypeScript configuration
├── package.json               # NPM package configuration
└── README.md                  # This file
```

## TypeScript Infrastructure

### Building

```bash
# Build once
npm run build

# Watch mode (rebuild on changes)
npm run build:watch

# Clean build artifacts
npm run clean

# Type check without emitting
npm run type-check
```

### Usage

Import from the compiled JavaScript:

```typescript
import { MCPClient } from '@mdk-mcp/shared/mcp-client';
import { ToolGenerator } from '@mdk-mcp/shared/tool-generator';
import type { IToolWrapper, IToolSchema } from '@mdk-mcp/shared/types';
```

Or import from the source (for development):

```typescript
import { MCPClient } from './ts_src/mcp-client.js';
```

## Python Infrastructure

### Structure

The `py_infra` directory contains reusable Python base classes and utilities.

### Usage

Import in your MCP server:

```python
from mcp_servers.shared.py_infra.types import (
    ToolHandler,
    ToolMetadata,
    ToolInput,
    ToolOutput,
    ServerRegistry,
    ServerConfig
)

from mcp_servers.shared.py_infra.utils import (
    setup_logging,
    validate_schema
)
```

### Base Classes

#### ToolHandler

Abstract base class for all tools:

```python
from mcp_servers.shared.py_infra.types import ToolHandler

class MyTool(ToolHandler):
    @property
    def metadata(self):
        return ToolMetadata(
            name="my_tool",
            description="My tool description",
            version="1.0.0",
            category="database"
        )
    
    @property
    def input_schema(self):
        return {...}
    
    async def validate_input(self, input_data):
        # Validation logic
        pass
    
    async def execute(self, input_data):
        # Execution logic
        pass
    
    async def validate_output(self, output_data):
        # Output validation
        pass
```

#### ServerRegistry

Central registry for managing tools:

```python
from mcp_servers.shared.py_infra.types import ServerRegistry, ServerConfig

config = ServerConfig(
    name="my_server",
    version="1.0.0",
    description="My MCP server"
)

registry = ServerRegistry(config)
registry.register_tool(MyTool())
```

## Testing

### TypeScript Tests

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch
```

### Python Tests

```bash
# From the project root
pytest mcp_servers/shared/tests/
```

## Development

### Adding New TypeScript Code

1. Create files in `ts_src/`
2. Export from `ts_src/index.ts` if needed
3. Run `npm run build`
4. Import from other projects

### Adding New Python Infrastructure

1. Create files in `py_infra/`
2. Add imports to `__init__.py` if needed
3. Import from MCP servers

### Type Definitions

Type definitions are in `ts_src/types/`:
- `client.protocol.ts` - MCP protocol types
- `tool.schema.ts` - JSON Schema types
- `tool.wrapper.ts` - Tool wrapper interfaces
- `mcp.bridge.ts` - MCP bridge interfaces

## Dependencies

### TypeScript

- `@modelcontextprotocol/sdk` - MCP SDK
- TypeScript 5.3+
- Node.js 18+

### Python

- `mcp` - MCP Python SDK
- `pydantic` - Data validation
- Python 3.11+

## Best Practices

1. **Always build after changes** - Run `npm run build` after modifying TypeScript
2. **Use type imports** - Import types with `import type { ... }`
3. **Export from index** - Export public APIs from `index.ts`
4. **Document changes** - Update this README when adding new infrastructure
5. **Test your code** - Write tests for new functionality

## Troubleshooting

### TypeScript Compilation Errors

```bash
# Clean and rebuild
npm run clean
npm run build
```

### Import Errors

Make sure to:
- Use `.js` extension in imports (for ESM)
- Build the project before importing
- Check `package.json` exports

### Python Import Errors

Make sure to:
- Install the package in editable mode: `pip install -e .`
- Add `__init__.py` files to all directories
- Use absolute imports from `mcp_servers.shared.py_infra`

---

**Last Updated:** 2025-11-13  
**Version:** 1.0.0  
**Maintainer:** MDK Development Team

