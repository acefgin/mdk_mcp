# Project Folder Structure

## Overview

Organized structure for the MDK MCP project with clear separation of concerns.

## Proposed Structure

```
mdk_mcp/
├── docs/                           # All documentation
│   ├── guides/                     # User guides
│   │   ├── QUICKSTART.md
│   │   ├── USER_GUIDE.md
│   │   └── TROUBLESHOOTING.md
│   │
│   ├── claude-desktop/             # Claude Desktop specific
│   │   ├── TESTING_GUIDE.md
│   │   ├── SETUP_GUIDE.md
│   │   ├── REFERENCE_CARD.md
│   │   └── SUMMARY.md
│   │
│   ├── migration/                  # Migration docs
│   │   ├── PLAN.md
│   │   ├── EXECUTIVE_SUMMARY.md
│   │   ├── ACTION_ITEMS.md
│   │   ├── TASK_TICKETS.md
│   │   └── TESTING.md
│   │
│   ├── architecture/               # Architecture docs
│   │   ├── MCP_2.0_SUMMARY.md
│   │   ├── TOKEN_COMPARISON.md
│   │   └── AUTOGEN_INTEGRATION.md
│   │
│   └── api/                        # API documentation
│       ├── README_MODELS.md
│       └── SECURITY.md
│
├── scripts/                        # All executable scripts
│   ├── setup/                      # Setup scripts
│   │   ├── setup-claude-desktop.sh
│   │   ├── setup-mcp-servers.sh
│   │   └── install-dependencies.sh
│   │
│   ├── server/                     # Server management
│   │   ├── start-python-servers.sh
│   │   ├── stop-python-servers.sh
│   │   ├── restart-servers.sh
│   │   └── check-servers.sh
│   │
│   ├── testing/                    # Test scripts
│   │   ├── test-migration.sh
│   │   ├── test-all.sh
│   │   └── test-mcp-server.sh
│   │
│   └── utils/                      # Utility scripts
│       └── start-interactive.sh
│
├── config/                         # Configuration files
│   ├── claude-desktop.json         # Claude Desktop config
│   ├── mcp.json                    # MCP config
│   └── environments/               # Environment configs
│       ├── development.env
│       ├── production.env
│       └── testing.env
│
├── workspace/                      # Generated TypeScript code
│   ├── lib/                        # Shared libraries
│   │   └── mcp-client.ts
│   │
│   ├── servers/                    # Generated server wrappers
│   │   ├── database/
│   │   ├── processing/
│   │   ├── alignment/
│   │   ├── design/
│   │   └── validation/
│   │
│   └── mcp-server.ts               # Main MCP server
│
├── mcp_servers/                    # Python MCP servers
│   ├── shared/                     # Shared code
│   │   └── tool-generator.ts
│   │
│   ├── database_server/
│   ├── processing_server/
│   ├── alignment_server/
│   ├── design_server/
│   └── validation_server/
│
├── tests/                          # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── examples/                       # Example code
│   └── demos/
│
├── logs/                          # Log files (gitignored)
│   ├── mcp-database.log
│   ├── mcp-processing.log
│   └── ...
│
├── tmp/                           # Temporary files (gitignored)
│
├── results/                       # Test/analysis results
│
└── Root files:
    ├── README.md                  # Main readme
    ├── package.json               # Node dependencies
    ├── tsconfig.json              # TypeScript config
    ├── vitest.config.ts           # Test config
    └── .gitignore                 # Git ignore
```

## Benefits

1. **Clear Separation** - Each type of file has its place
2. **Easy Navigation** - Logical grouping makes finding files easy
3. **Scalable** - Easy to add new components
4. **Standard** - Follows common project conventions
5. **Clean Root** - Minimal files in root directory

## Migration Plan

See `scripts/organize-codebase.sh` for automated migration.

