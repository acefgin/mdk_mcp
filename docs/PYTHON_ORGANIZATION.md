# Python Code Organization Plan

## Current State Analysis

### Python Files Found

#### ✅ Well Organized (mcp_servers/)
```
mcp_servers/
├── database_server/
│   ├── database_mcp_server.py
│   ├── config.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_basic.py
│       ├── test_gget_tools.py
│       ├── test_integration.py
│       ├── test_mcp_client.py
│       ├── test_sequence_tools.py
│       └── test_taxonomy_sra_tools.py
│
├── processing_server/
│   ├── processing_mcp_server.py
│   ├── config.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_basic.py
│
├── alignment_server/
│   ├── alignment_mcp_server.py
│   ├── config.py
│   └── tests/
│       ├── __init__.py
│       └── test_alignment_server.py
│
├── design_server/
│   ├── design_mcp_server.py
│   ├── config.py
│   └── tests/
│       ├── __init__.py
│       └── test_design_server.py
│
└── validation_server/
    ├── validation_mcp_server.py
    ├── config.py
    └── tests/
        ├── __init__.py
        └── test_validation_server.py
```

#### ❌ Needs Organization (Root Level)
```
./ (root)
├── test_function_calling.py          → Move to tests/python/
├── test_alignment_fix.py              → Move to tests/python/
├── test_processing_fix.py             → Move to tests/python/
└── test_processing_integration.py     → Move to tests/python/
```

#### ⚠️ Needs Better Structure (autogen_app/)
```
autogen_app/
├── qpcr_assistant.py                  → Rename to main.py or keep
├── autogen_mcp_bridge.py              → Move to lib/
└── text_resources.py                  → Move to lib/ or resources/
```

## Proposed Organization

### New Structure

```
mdk_mcp/
├── mcp_servers/                       # Python MCP Servers (KEEP AS IS)
│   ├── shared/                        # Shared Python utilities
│   │   ├── __init__.py
│   │   ├── base_server.py            # (if exists)
│   │   └── utils.py                  # (if exists)
│   │
│   ├── database_server/               # ✅ Already organized
│   ├── processing_server/             # ✅ Already organized
│   ├── alignment_server/              # ✅ Already organized
│   ├── design_server/                 # ✅ Already organized
│   └── validation_server/             # ✅ Already organized
│
├── autogen_app/                       # AutoGen Application (REORGANIZE)
│   ├── __init__.py                    # Make it a proper package
│   ├── main.py                        # Main entry point (qpcr_assistant.py)
│   │
│   ├── lib/                          # Library code
│   │   ├── __init__.py
│   │   ├── mcp_bridge.py             # autogen_mcp_bridge.py
│   │   └── resources.py              # text_resources.py
│   │
│   ├── config/                       # AutoGen config (if needed)
│   │   └── __init__.py
│   │
│   └── tests/                        # AutoGen tests
│       ├── __init__.py
│       └── test_autogen.py
│
├── tests/                            # Test Suites
│   ├── unit/                         # TypeScript unit tests ✅
│   │   └── tool-generator.test.ts
│   │
│   ├── integration/                  # TypeScript integration tests ✅
│   │   └── migration-infrastructure.test.ts
│   │
│   ├── python/                       # Python tests (NEW)
│   │   ├── __init__.py
│   │   ├── test_function_calling.py  # From root
│   │   ├── test_alignment_fix.py     # From root
│   │   ├── test_processing_fix.py    # From root
│   │   └── test_processing_integration.py  # From root
│   │
│   └── e2e/                          # End-to-end tests
│       └── (future tests)
│
├── scripts/                          # Shell Scripts
│   ├── python/                       # Python-specific scripts (NEW)
│   │   ├── run_tests.sh
│   │   ├── lint.sh
│   │   └── format.sh
│   │
│   └── ...
│
└── config/                           # Configuration
    ├── python/                       # Python configs (NEW)
    │   ├── pytest.ini                # pytest configuration
    │   ├── pyproject.toml            # Python project config
    │   └── requirements.txt          # Python dependencies
    │
    └── ...
```

## Migration Steps

### Step 1: Create New Directories
```bash
mkdir -p tests/python
mkdir -p autogen_app/lib
mkdir -p autogen_app/tests
mkdir -p scripts/python
mkdir -p config/python
```

### Step 2: Move Root-Level Python Tests
```bash
# Move test files from root to tests/python/
mv test_function_calling.py tests/python/
mv test_alignment_fix.py tests/python/
mv test_processing_fix.py tests/python/
mv test_processing_integration.py tests/python/

# Create __init__.py
touch tests/python/__init__.py
```

### Step 3: Reorganize autogen_app/
```bash
# Create structure
mkdir -p autogen_app/lib
touch autogen_app/__init__.py
touch autogen_app/lib/__init__.py

# Rename and move files
mv autogen_app/qpcr_assistant.py autogen_app/main.py
mv autogen_app/autogen_mcp_bridge.py autogen_app/lib/mcp_bridge.py
mv autogen_app/text_resources.py autogen_app/lib/resources.py
```

### Step 4: Add Python Configuration Files
```bash
# Create pytest configuration
cat > config/python/pytest.ini << 'EOF'
[pytest]
testpaths = tests/python mcp_servers
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
EOF

# Create requirements.txt (if not exists)
cat > config/python/requirements.txt << 'EOF'
# Python MCP Server Dependencies
mcp>=0.1.0
aiohttp>=3.8.0
gget>=0.28.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
# Add other dependencies...
EOF
```

### Step 5: Update Import Statements
- Update any imports in moved files
- Fix relative imports in autogen_app/

### Step 6: Add Python Scripts
```bash
# Test runner
cat > scripts/python/run_tests.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
pytest tests/python/ -v
EOF
chmod +x scripts/python/run_tests.sh

# Linter
cat > scripts/python/lint.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
python -m pylint mcp_servers/ autogen_app/ tests/python/
EOF
chmod +x scripts/python/lint.sh
```

## Benefits

### 1. Clear Organization
- All Python tests in `tests/python/`
- All MCP servers in `mcp_servers/`
- AutoGen app properly packaged in `autogen_app/`

### 2. Maintainability
- Easy to find Python code
- Clear separation from TypeScript code
- Standard Python project structure

### 3. Scalability
- Easy to add new servers
- Easy to add new tests
- Easy to add new AutoGen components

### 4. Professional Structure
- Follows Python best practices
- Uses proper package structure
- Clear imports and dependencies

### 5. Better Testing
- Separate Python and TypeScript tests
- Easy to run Python-specific tests
- Clear test organization

## File Summary

### Files to Move
| Current Location | New Location | Reason |
|-----------------|-------------|--------|
| `test_function_calling.py` | `tests/python/` | Python test file |
| `test_alignment_fix.py` | `tests/python/` | Python test file |
| `test_processing_fix.py` | `tests/python/` | Python test file |
| `test_processing_integration.py` | `tests/python/` | Python test file |
| `autogen_app/qpcr_assistant.py` | `autogen_app/main.py` | Main entry point |
| `autogen_app/autogen_mcp_bridge.py` | `autogen_app/lib/mcp_bridge.py` | Library code |
| `autogen_app/text_resources.py` | `autogen_app/lib/resources.py` | Resources |

### Files to Create
- `tests/python/__init__.py`
- `autogen_app/__init__.py`
- `autogen_app/lib/__init__.py`
- `config/python/pytest.ini`
- `config/python/requirements.txt`
- `scripts/python/run_tests.sh`
- `scripts/python/lint.sh`

### Files to Keep (Already Organized)
- All files in `mcp_servers/*/` - Already well organized
- All TypeScript tests in `tests/unit/` and `tests/integration/`

## Post-Organization Structure

```
mdk_mcp/
├── mcp_servers/          # ✅ Python MCP Servers (organized)
├── autogen_app/          # ✅ AutoGen App (organized)
│   ├── main.py
│   └── lib/
├── tests/
│   ├── unit/             # ✅ TypeScript tests
│   ├── integration/      # ✅ TypeScript tests
│   └── python/           # ✅ Python tests (NEW)
├── scripts/
│   └── python/           # ✅ Python scripts (NEW)
├── config/
│   └── python/           # ✅ Python config (NEW)
└── Root (clean!)         # ✅ No Python test files
```

## Verification Checklist

After organization:
- [ ] No `.py` files in root (except setup scripts if needed)
- [ ] All Python tests in `tests/python/`
- [ ] AutoGen app properly packaged
- [ ] All imports working correctly
- [ ] Python tests run successfully: `pytest tests/python/`
- [ ] MCP server tests still work: `pytest mcp_servers/`
- [ ] AutoGen app still runs: `python autogen_app/main.py`

## Quick Commands

```bash
# Run Python tests
pytest tests/python/ -v

# Run MCP server tests
pytest mcp_servers/ -v

# Run all Python tests
pytest -v

# Lint Python code
pylint mcp_servers/ autogen_app/ tests/python/

# Format Python code
black mcp_servers/ autogen_app/ tests/python/

# Run AutoGen app
python -m autogen_app.main
```

---

**Generated:** 2025-11-12  
**Status:** Ready for implementation  
**Script:** `scripts/organize-python.sh`

