# Project Structure & Build System

## Overview

This document describes the reorganized project structure with proper TypeScript source management and Python infrastructure organization.

## Directory Structure

```
mdk_mcp/
├── mcp_servers/
│   ├── shared/
│   │   ├── ts_src/                    # TypeScript source files
│   │   │   ├── types/                 # Type definitions
│   │   │   ├── helpers.ts
│   │   │   ├── mcp-client.ts
│   │   │   ├── pii-tokenizer.ts
│   │   │   ├── result-cache.ts
│   │   │   └── tool-generator.ts
│   │   ├── dist/                      # Compiled JavaScript (git ignored)
│   │   ├── py_infra/                  # Python infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── types/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tool_handler.py
│   │   │   │   └── server_registry.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       ├── logging.py
│   │   │       └── validation.py
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── database_server/
│   │   ├── ts_src/                    # TypeScript tools (if any)
│   │   ├── dist/                      # Compiled JavaScript
│   │   ├── tools/                     # Python tools
│   │   ├── services/                  # Python services
│   │   ├── tests/                     # Python tests
│   │   ├── database_mcp_server.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── processing_server/             # Same structure as database_server
│   ├── alignment_server/
│   ├── design_server/
│   └── validation_server/
│
├── workspace/
│   ├── lib/
│   │   ├── types/                     # TypeScript types
│   │   ├── *.ts                       # TypeScript source
│   │   └── README.md
│   ├── servers/                       # Generated tool wrappers
│   │   ├── database/
│   │   ├── processing/
│   │   ├── alignment/
│   │   ├── design/
│   │   └── validation/
│   └── helpers.js
│
├── code-execution/
│   ├── src/                           # TypeScript source
│   ├── dist/                          # Compiled JavaScript
│   ├── Dockerfile
│   └── package.json
│
├── package.json                       # Root package.json
├── tsconfig.json                      # Root TypeScript config
├── tsconfig.base.json                 # Base config for all projects
└── build.sh                           # Build script
```

## Build System

### NPM Scripts

The root `package.json` defines these scripts:

- `npm run build` - Build all TypeScript projects
- `npm run build:shared` - Build shared infrastructure
- `npm run build:workspace` - Build workspace library
- `npm run build:code-execution` - Build code execution sandbox
- `npm run clean` - Clean all build artifacts
- `npm run type-check` - Type check without emitting
- `npm test` - Run all tests

### Build Process

1. **Clean** - Remove all `dist/` directories
2. **Compile TypeScript** - Compile all `.ts` files to `.js`
3. **Copy Assets** - Copy non-TS files (`.json`, `.md`, etc.)
4. **Generate Wrappers** - Generate tool wrappers from MCP servers

## TypeScript Configuration

### Base Configuration

All projects extend from `tsconfig.base.json` for consistency.

### Project References

Projects use TypeScript project references for:
- Faster incremental builds
- Better IDE support
- Proper dependency management

## Python Infrastructure

### py_infra Structure

The `py_infra` folder contains reusable Python infrastructure:

- **types/** - Base classes and interfaces
  - `tool_handler.py` - ToolHandler base class
  - `server_registry.py` - ServerRegistry class
  
- **utils/** - Utility functions
  - `logging.py` - Logging utilities
  - `validation.py` - Validation utilities

### Usage in Servers

Each MCP server imports from `py_infra`:

```python
from mcp_servers.shared.py_infra.types import ToolHandler, ServerRegistry
from mcp_servers.shared.py_infra.utils import setup_logging
```

## Fresh Clone Setup

After cloning the repository:

```bash
# 1. Install dependencies
npm install

# 2. Build all TypeScript
npm run build

# 3. Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Build Docker images
docker-compose build

# 6. Start services
docker-compose up -d
```

## Development Workflow

### Adding New TypeScript Code

1. Add `.ts` files to appropriate `ts_src/` directory
2. Import types from `types/` directory
3. Run `npm run build` to compile
4. Test the compiled JavaScript

### Adding New Python Tool

1. Create tool in `tools/` directory
2. Extend `ToolHandler` from `py_infra`
3. Register in server
4. Run tool generator to create TS wrapper
5. Test

### Modifying Shared Infrastructure

1. Modify files in `mcp_servers/shared/ts_src/` or `py_infra/`
2. Run `npm run build:shared`
3. Restart affected services
4. Run tests

## Git Configuration

### .gitignore

```gitignore
# TypeScript build artifacts
dist/
*.js
*.js.map
*.d.ts

# Keep specific JS files
!jest.config.js
!vitest.config.js

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/

# Dependencies
node_modules/

# IDE
.vscode/
.idea/

# Logs
*.log

# Results
results/*
!results/.gitkeep
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Node dependencies
        run: npm ci
      
      - name: Build TypeScript
        run: npm run build
      
      - name: Type check
        run: npm run type-check
      
      - name: Run tests
        run: npm test
      
      - name: Install Python dependencies
        run: pip install -r requirements.txt
      
      - name: Run Python tests
        run: pytest
```

---

**Last Updated:** 2025-11-13  
**Version:** 1.0.0

