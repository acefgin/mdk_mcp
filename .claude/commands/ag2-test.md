---
description: Run comprehensive AG2 multi-agent workflow tests
argument-hint: Test mode (quick, full, agent, bridge) or specific workflow name
---

You are an AG2 multi-agent testing specialist. Run comprehensive test suite for: **$ARGUMENTS**

## Instructions

Execute the following testing workflow for the AG2 qPCR assistant system:

### Step 1: Validate Test Mode

Valid test modes:
- `quick` - Fast validation (config + unit tests only)
- `full` - Complete testing (all steps below)
- `agent` - Agent-specific tests (initialization + collaboration)
- `bridge` - MCP bridge tests (connection + tool registration)
- `workflow:<name>` - Test specific workflow (e.g., `workflow:salmo-salar`)

If invalid mode provided, list valid options and exit.

### Step 2: Check Environment Configuration

**API Key Validation**:
```bash
cd autogen_app

# Check if OAI_CONFIG_LIST.json exists
if [ ! -f OAI_CONFIG_LIST.json ]; then
    echo "❌ ERROR: OAI_CONFIG_LIST.json not found"
    echo "Create from template: cp OAI_CONFIG_LIST.template.json OAI_CONFIG_LIST.json"
    exit 1
fi

# Validate JSON format
cat OAI_CONFIG_LIST.json | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Invalid JSON in OAI_CONFIG_LIST.json"
    exit 1
fi

# Check for placeholder API key
if grep -q "your-api-key-here" OAI_CONFIG_LIST.json; then
    echo "⚠️  WARNING: API key appears to be placeholder"
    echo "Please update OAI_CONFIG_LIST.json with valid API key"
fi
```

**Report**:
- ✅ OAI_CONFIG_LIST.json exists
- ✅ JSON is valid
- ✅/⚠️ API key configured

### Step 3: Run Unit Tests with pytest

Execute AG2 component tests:

```bash
cd autogen_app
pytest tests/ -v --tb=short
```

**Report**:
- Total tests run
- Passed / Failed / Skipped
- Test duration
- Any failures with stack traces

**Exit early if**:
- Mode is `quick` - stop here and generate report

### Step 4: Check Docker Build

Verify AG2 containers can be built:

```bash
# Build qPCR assistant container
docker-compose -f docker-compose.autogen.yml build qpcr-assistant

# Check build success
if [ $? -eq 0 ]; then
    echo "✅ qPCR assistant container built successfully"
    docker images | grep qpcr-assistant | awk '{print "Image size: " $7}'
else
    echo "❌ Container build failed"
    exit 1
fi
```

**Report**:
- Build success/failure
- Image size
- Build duration
- Any build warnings

### Step 5: Test MCP Server Connectivity

Verify all required MCP servers are accessible:

```bash
# Start MCP servers
docker-compose up -d database_server processing_server alignment_server

# Wait for startup
sleep 5

# Check container health
for server in database_server processing_server alignment_server; do
    if docker ps | grep -q $server; then
        echo "✅ $server running"
    else
        echo "❌ $server failed to start"
    fi
done
```

**Report**:
- Database server: Running/Failed
- Processing server: Running/Failed
- Alignment server: Running/Failed

**Exit early if**:
- Mode is `bridge` and servers failed - cannot test bridge without servers

### Step 6: Test Agent Initialization

Test AG2 agent creation and registration:

```bash
cd autogen_app

# Run agent initialization test
python3 -c "
from qpcr_assistant import create_agents
import asyncio

async def test_agents():
    try:
        agents = await create_agents()
        print(f'✅ Created {len(agents)} agents')
        for name, agent in agents.items():
            print(f'  → {name}: {type(agent).__name__}')
        return True
    except Exception as e:
        print(f'❌ Agent initialization failed: {e}')
        return False

result = asyncio.run(test_agents())
exit(0 if result else 1)
"
```

**Expected Agents**:
- `coordinator` - UserProxyAgent
- `database_agent` - AssistantAgent (Database Specialist)
- `analyst_agent` - AssistantAgent (Processing + Alignment Specialist)
- `designer_agent` - AssistantAgent (Primer Design Specialist)

**Report**:
- Total agents created
- Agent types and roles
- Initialization success/failure

**Exit early if**:
- Mode is `agent` - stop here after agent tests

### Step 7: Test MCP Bridge Integration

Test MCPClientBridge connection and tool registration:

```bash
cd autogen_app

# Run bridge test
python3 -c "
from autogen_mcp_bridge import MCPClientBridge
import asyncio

async def test_bridge():
    try:
        # Initialize bridge with server configs
        bridge = MCPClientBridge({
            'database': {
                'container': 'database_server',
                'python_path': 'python3',
                'server_path': 'mcp_servers/database_server/database_mcp_server.py'
            },
            'processing': {
                'container': 'processing_server',
                'python_path': 'python3',
                'server_path': 'mcp_servers/processing_server/processing_mcp_server.py'
            },
            'alignment': {
                'container': 'alignment_server',
                'python_path': 'python3',
                'server_path': 'mcp_servers/alignment_server/alignment_mcp_server.py'
            }
        })

        # Start servers
        await bridge.start_servers()
        print('✅ MCP bridge initialized')

        # List tools from each server
        for server_name in ['database', 'processing', 'alignment']:
            tools = await bridge.list_tools(server_name)
            print(f'  → {server_name}: {len(tools)} tools')
            for tool in tools[:3]:  # Show first 3
                print(f'    • {tool[\"name\"]}')

        # Cleanup
        await bridge.shutdown()
        return True
    except Exception as e:
        print(f'❌ MCP bridge test failed: {e}')
        return False

result = asyncio.run(test_bridge())
exit(0 if result else 1)
"
```

**Expected Tools**:
- Database server: 11 tools (get_sequences, gget_ref, gget_search, etc.)
- Processing server: 5 tools (fasta_qc, dereplicate_sequences, etc.)
- Alignment server: 5 tools (align_sequences, build_phylogeny, etc.)

**Report**:
- Bridge initialization: Success/Failed
- Database tools: Count
- Processing tools: Count
- Alignment tools: Count
- Total tools registered: Sum

**Exit early if**:
- Mode is `bridge` - stop here after bridge tests

### Step 8: Test Multi-Agent Collaboration

Test agent communication and group chat:

```bash
cd autogen_app

# Run collaboration test
python3 -c "
from qpcr_assistant import create_agents, setup_group_chat
import asyncio

async def test_collaboration():
    try:
        agents = await create_agents()
        group_chat, manager = setup_group_chat(agents)

        print('✅ Group chat configured')
        print(f'  → Agents: {len(group_chat.agents)}')
        print(f'  → Manager: {type(manager).__name__}')

        # Test simple message routing
        test_message = 'Hello, can you help with a qPCR assay?'
        # Note: Don't actually send message in test, just verify setup

        return True
    except Exception as e:
        print(f'❌ Collaboration test failed: {e}')
        return False

result = asyncio.run(test_collaboration())
exit(0 if result else 1)
"
```

**Report**:
- Group chat: Configured/Failed
- Agents in group: Count
- Manager type: GroupChatManager
- Message routing: Ready

### Step 9: Run Sample Workflow (Full Mode Only)

Test end-to-end qPCR design workflow:

**For mode `full` or `workflow:<name>`**:

```bash
cd autogen_app

# Run sample workflow
python3 -c "
from qpcr_assistant import main
import asyncio

async def test_workflow():
    try:
        # Simple test query
        query = 'Design primers for Salmo salar COI with 5 sequences'

        print(f'🧪 Testing workflow: {query}')
        print('⏳ This may take 30-60 seconds...')

        # Run with timeout
        result = await asyncio.wait_for(
            main(query),
            timeout=120
        )

        print('✅ Workflow completed successfully')
        return True
    except asyncio.TimeoutError:
        print('⚠️  Workflow timed out (>120s)')
        return False
    except Exception as e:
        print(f'❌ Workflow failed: {e}')
        return False

result = asyncio.run(test_workflow())
exit(0 if result else 1)
"
```

**Report**:
- Workflow execution: Success/Timeout/Failed
- Duration: Seconds
- Files generated: Count and locations
- Agent collaboration: Observed interactions

### Step 10: Generate Test Report

Create comprehensive markdown report in `test-results/ag2-test-report-YYYYMMDD.md`:

```markdown
# AG2 Multi-Agent Test Results

**Date**: YYYY-MM-DD HH:MM:SS
**Test Mode**: [quick|full|agent|bridge|workflow]
**Duration**: X.XX seconds

---

## Environment Configuration

- ✅ OAI_CONFIG_LIST.json: Valid
- ✅ API Key: Configured
- ✅ Docker: Available

## Unit Tests

- **Total Tests**: X
- **Passed**: X
- **Failed**: X
- **Skipped**: X
- **Duration**: X.XXs

### Failed Tests
[If any, show stack traces]

## Docker Build

- **Status**: ✅ Success / ❌ Failed
- **Image Size**: XXX MB
- **Build Duration**: X.XXs

## MCP Server Connectivity

- **Database Server**: ✅ Running / ❌ Failed
- **Processing Server**: ✅ Running / ❌ Failed
- **Alignment Server**: ✅ Running / ❌ Failed

## Agent Initialization

- **Status**: ✅ Success / ❌ Failed
- **Agents Created**: X
  - coordinator: UserProxyAgent
  - database_agent: AssistantAgent
  - analyst_agent: AssistantAgent
  - designer_agent: AssistantAgent

## MCP Bridge Integration

- **Status**: ✅ Success / ❌ Failed
- **Database Tools**: XX tools
- **Processing Tools**: XX tools
- **Alignment Tools**: XX tools
- **Total Tools Registered**: XX

## Multi-Agent Collaboration

- **Status**: ✅ Success / ❌ Failed
- **Group Chat**: Configured
- **Agents in Group**: X
- **Manager**: GroupChatManager

## Sample Workflow (Full Mode Only)

- **Status**: ✅ Success / ⚠️ Timeout / ❌ Failed
- **Duration**: XX.XXs
- **Files Generated**: X files

---

## Overall Status

✅ **PASS** - All tests passed
⚠️  **PARTIAL** - Some tests failed
❌ **FAIL** - Critical tests failed

## Recommendations

[If failures occurred:]
- Fix failed unit tests
- Check Docker logs: `docker-compose -f docker-compose.autogen.yml logs`
- Verify API key in OAI_CONFIG_LIST.json
- Ensure MCP servers are running
- Check network connectivity between containers

[If all passed:]
- ✅ AG2 system ready for use
- ✅ All agents operational
- ✅ MCP bridge functioning
- ✅ Multi-agent collaboration working

## Next Steps

- Run interactive session: `./start_interactive.sh`
- Test with custom queries
- Monitor agent logs for issues
- Check file outputs in `sequences/` directory
```

## Important Notes

1. **Stop on Critical Failures**:
   - If environment check fails → exit immediately
   - If unit tests fail → report but continue
   - If Docker build fails → stop (cannot test further)
   - If MCP servers fail → skip bridge tests

2. **Test Isolation**:
   - Each test should be independent
   - Clean up resources after each test
   - Don't leave containers running

3. **Timing**:
   - Quick mode: ~30 seconds
   - Agent/Bridge mode: ~60 seconds
   - Full mode: ~2-3 minutes (includes workflow)

4. **Error Handling**:
   - Capture all errors with stack traces
   - Provide actionable recommendations
   - Include relevant log snippets

5. **Report Location**:
   - Save to `test-results/ag2-test-report-YYYYMMDD-HHMMSS.md`
   - Create directory if it doesn't exist
   - Include timestamp for multiple runs

## Usage Examples

```bash
# Quick validation (config + unit tests only)
/ag2-test quick

# Full comprehensive test suite
/ag2-test full

# Test agent initialization and collaboration
/ag2-test agent

# Test MCP bridge integration
/ag2-test bridge

# Test specific workflow
/ag2-test workflow:salmo-salar
```

## Verification Commands

After testing, verify the system is clean:

```bash
# Check no containers left running
docker ps | grep -E "(qpcr|database|processing|alignment)"

# Clean up test artifacts
docker-compose -f docker-compose.autogen.yml down
docker-compose down

# Check test results
ls -lh test-results/ag2-test-report-*.md
```

---

**Final Output**: Provide concise summary to user with:
- Overall test status (PASS/PARTIAL/FAIL)
- Key metrics (tests passed, agents created, tools registered)
- Location of detailed report
- Any critical issues found
- Recommended next steps
