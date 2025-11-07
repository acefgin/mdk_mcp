---
description: Run comprehensive MCP server tests (unit + integration + Inspector)
argument-hint: Server name (database, processing, alignment, design) or "all"
---

You are an MCP server testing specialist. Run comprehensive test suite for: **$ARGUMENTS**

## Instructions

Execute the following testing workflow for the specified MCP server(s):

### Step 1: Validate Server Name

Valid servers:
- `database` - Database Server (Phase 1)
- `processing` - Processing Server (Phase 2)
- `alignment` - Alignment Server (Phase 3)
- `design` - Design Server (Phase 4)
- `all` - Run tests for all servers

If invalid server name provided, list valid options and exit.

### Step 2: Run Unit Tests with pytest

For each server, execute:

```bash
cd mcp_servers/<server>_server
pytest tests/ -v --tb=short
```

**Report**:
- Total tests run
- Passed / Failed / Skipped
- Test duration
- Any failures with stack traces

### Step 3: Check Docker Build

Verify server can be containerized:

```bash
cd mcp_servers/<server>_server
docker build -t ndiag-<server>-server:test .
```

**Report**:
- Build success/failure
- Image size
- Build duration
- Any build warnings

### Step 4: Test MCP Inspector Integration

Launch server and test with MCP Inspector:

```bash
cd mcp_servers/<server>_server
docker-compose up -d
sleep 5  # Wait for startup

# Test tools/list
docker exec ndiag-<server>-server python3 -c "
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    params = StdioServerParameters(
        command='python3',
        args=['<server>_mcp_server.py']
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f'✅ Found {len(tools.tools)} tools')
            for tool in tools.tools:
                print(f'  - {tool.name}')

asyncio.run(test())
"

docker-compose down
```

**Report**:
- Number of tools exposed
- Tool names list
- Any connection errors

### Step 5: Run Sample Tool Call

Execute a representative tool call to verify functionality:

**Database Server**:
```bash
# Test get_sequences tool
docker exec ndiag-database-server python3 -c "
import asyncio
from database_mcp_server import get_sequences
result = asyncio.run(get_sequences('Escherichia coli', '16S', 'ncbi', 5))
print(result)
"
```

**Processing Server**:
```bash
# Test fasta_qc tool
docker exec ndiag-processing-server python3 -c "
import asyncio
from processing_mcp_server import fasta_qc
result = asyncio.run(fasta_qc('test_data/sample.fasta', 100, 5.0))
print(result)
"
```

**Alignment Server**:
```bash
# Test align_sequences tool
docker exec ndiag-alignment-server python3 -c "
import asyncio
from alignment_mcp_server import align_sequences
result = asyncio.run(align_sequences('test_data/sequences.fasta', 'mafft'))
print(result)
"
```

**Design Server**:
```bash
# Test find_signature_regions tool
docker exec ndiag-design-server python3 -c "
import asyncio
from design_mcp_server import find_signature_regions
result = asyncio.run(find_signature_regions('test_data/alignment.fasta', ['target'], ['offtarget']))
print(result)
"
```

**Report**:
- Tool execution success/failure
- Output summary
- Execution time

### Step 6: Generate Test Summary

Create comprehensive summary:

```markdown
# MCP Server Test Results: <SERVER_NAME>

**Date**: YYYY-MM-DD HH:MM
**Status**: ✅ PASS | ⚠️  WARNING | ❌ FAIL

## Unit Tests (pytest)
- **Total Tests**: X
- **Passed**: X ✅
- **Failed**: X ❌
- **Skipped**: X ⏭️
- **Duration**: X.XX seconds
- **Coverage**: XX%

<details>
<summary>Failed Tests (if any)</summary>

```
[Stack traces for failed tests]
```
</details>

## Docker Build
- **Status**: ✅ Success | ❌ Failed
- **Image Size**: XXX MB
- **Build Time**: X.X seconds
- **Warnings**: [List any warnings]

## MCP Integration
- **Tools Exposed**: X
- **Tools List**:
  1. tool_name_1
  2. tool_name_2
  ...
- **Connection**: ✅ Success | ❌ Failed

## Sample Tool Execution
- **Tool**: <tool_name>
- **Status**: ✅ Success | ❌ Failed
- **Output**: <summary>
- **Duration**: X.XX seconds

## Overall Assessment
- **Unit Tests**: ✅ | ⚠️  | ❌
- **Docker**: ✅ | ❌
- **MCP Protocol**: ✅ | ❌
- **Functionality**: ✅ | ❌

**Overall Status**: ✅ PASS | ⚠️  NEEDS ATTENTION | ❌ FAIL

## Recommendations
[List any issues found and suggested fixes]

## Next Steps
[What to do based on results]
```

Save to: `test-results/<server>-test-report-YYYYMMDD.md`

## Special Cases

### Testing All Servers ("all")

Run Steps 2-6 for each server sequentially:
1. database
2. processing
3. alignment
4. design

Generate combined summary showing status of all servers.

### Handling Test Failures

If tests fail:
1. **Capture full stack trace**
2. **Identify root cause** (dependency missing, logic error, etc.)
3. **Suggest fix** based on error type
4. **Re-run after fix** to verify

### Quick Test Mode

For rapid iteration, support `--quick` flag:
```bash
# Only run unit tests, skip Docker and integration
pytest tests/ -v
```

## Test Data Requirements

Ensure test data exists:
- `mcp_servers/<server>/test_data/` directory
- Sample FASTA files
- Sample alignment files (for alignment/design servers)
- Mock data for external API calls

If missing, generate or download test data.

## Output Guidelines

**Be concise but complete**:
- ✅ Clear pass/fail indicators
- 📊 Numeric summaries (X/Y tests passed)
- 🔍 Details only for failures
- 💡 Actionable recommendations
- 📝 Save full report to file

**Don't overwhelm with**:
- Full output of passing tests
- Verbose Docker logs (unless error)
- Redundant information

## Integration with CI/CD

This command provides foundation for automated testing pipeline:
```bash
# In CI pipeline
./test-mcp.sh all --quick
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi
```

## Example Usage

```bash
# Test single server
/test-mcp database

# Test all servers
/test-mcp all

# Quick test (pytest only)
/test-mcp processing --quick
```

## Remember

- **Run tests BEFORE pushing code**
- **Fix failures immediately** - don't accumulate technical debt
- **Update tests when adding features**
- **Check test coverage** - aim for >80%
- **Mock external dependencies** - tests should be fast and isolated
- **Document test data requirements**

Your test execution should be **thorough, fast, and provide actionable feedback**.
