# Testing the AutoGen qPCR Assistant Prototype

Complete guide to test the AutoGen-powered multi-agent system with MCP servers.

## Prerequisites

1. **Docker and Docker Compose** installed
   ```bash
   docker --version  # Should be 20.10+
   docker-compose --version  # Should be 1.29+
   ```

2. **OpenAI API Key**
   - Get from https://platform.openai.com/api-keys
   - Requires GPT-4 access for best results

3. **(Optional) NCBI API Key**
   - Get from https://www.ncbi.nlm.nih.gov/account/settings/
   - Provides higher rate limits (10 requests/sec vs 3/sec)

## Quick Test Setup

### Step 1: Configure Environment

```bash
# Navigate to project root
cd /home/raycifeng/mdk_mcp

# Create environment file
cp autogen_app/.env.template autogen_app/.env

# Edit and add your OpenAI API key
nano autogen_app/.env
```

**In `.env` file, set**:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
NCBI_API_KEY=your-ncbi-key-here  # Optional
```

### Step 2: Build and Start Services

```bash
# Build all Docker images
docker-compose -f docker-compose.autogen.yml build

# Start services in background
docker-compose -f docker-compose.autogen.yml up -d

# Check status
docker-compose -f docker-compose.autogen.yml ps
```

**Expected Output**:
```
NAME                    STATUS    PORTS
ndiag-database-server   Up
qpcr-assistant          Up        0.0.0.0:8501->8501/tcp
```

### Step 3: Verify MCP Server is Running

```bash
# Check database server logs
docker logs ndiag-database-server

# Should see:
# "Starting ndiag-database-server MCP server"
# "Available tools: get_sequences, gget_*, ..."

# Test MCP server directly
docker exec -i ndiag-database-server python -c "
import asyncio
from database_mcp_server import handle_list_tools

async def test():
    tools = await handle_list_tools()
    print(f'✅ MCP Server operational with {len(tools)} tools')

asyncio.run(test())
"
```

## Test Scenarios

### Test 1: Basic MCP Bridge Connection

**Purpose**: Verify AutoGen can communicate with MCP server

```bash
# Create test script
cat > /tmp/test_bridge.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/app')

from autogen_mcp_bridge import MCPClientBridge

async def test_bridge():
    print("🧪 Testing MCP Bridge Connection...")

    # Initialize bridge
    bridge = MCPClientBridge({
        "database": {
            "container": "ndiag-database-server",
            "command": ["python", "/app/database_mcp_server.py"]
        }
    })

    # Start servers
    await bridge.start_servers()
    print("✅ Bridge connected to MCP servers")

    # List available tools
    tools = await bridge.list_tools("database")
    print(f"✅ Found {len(tools)} MCP tools:")
    for tool in tools[:3]:
        print(f"   - {tool['name']}: {tool['description'][:60]}...")

    # Test a simple tool call
    print("\n🧪 Testing get_taxonomy tool...")
    result = await bridge.call_tool(
        "database",
        "get_taxonomy",
        {"query": "Homo sapiens"}
    )
    print(f"✅ Tool call successful! Result length: {len(str(result))} chars")

    # Cleanup
    await bridge.shutdown()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_bridge())
EOF

# Run test in qpcr-assistant container
docker exec -i qpcr-assistant python /tmp/test_bridge.py
```

**Expected Output**:
```
🧪 Testing MCP Bridge Connection...
✅ Bridge connected to MCP servers
✅ Found 12 MCP tools:
   - get_sequences: Retrieve sequences from multiple databases
   - get_taxonomy: Get detailed taxonomic information
   - gget_search: Search for genes in Ensembl database
🧪 Testing get_taxonomy tool...
✅ Tool call successful! Result length: 450 chars
✅ All tests passed!
```

### Test 2: AutoGen Agent Workflow (Simplified)

**Purpose**: Test AutoGen agents calling MCP tools

```bash
# Create simplified test (no OpenAI API needed for this test)
cat > /tmp/test_workflow.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/app')

from autogen_mcp_bridge import MCPClientBridge, create_autogen_functions

async def test_workflow():
    print("🧪 Testing AutoGen Workflow Components...")

    # Initialize bridge
    bridge = MCPClientBridge({
        "database": {
            "container": "ndiag-database-server",
            "command": ["python", "/app/database_mcp_server.py"]
        }
    })
    await bridge.start_servers()

    # Get AutoGen function definitions
    functions = create_autogen_functions(["database"])
    print(f"✅ Created {len(functions)} AutoGen function definitions")

    # Simulate what Database Agent would do
    print("\n🧪 Simulating Database Agent workflow...")

    # Step 1: Get sequences
    print("   1. Retrieving COI sequences for Salmo salar...")
    sequences = await bridge.call_tool(
        "database",
        "get_sequences",
        {
            "taxon": "Salmo salar",
            "region": "COI",
            "source": "ncbi",
            "max_results": 5
        }
    )
    print(f"   ✅ Retrieved sequences ({len(str(sequences))} chars)")

    # Step 2: Get taxonomy
    print("   2. Getting taxonomy information...")
    taxonomy = await bridge.call_tool(
        "database",
        "get_taxonomy",
        {"query": "Salmo salar"}
    )
    print(f"   ✅ Retrieved taxonomy ({len(str(taxonomy))} chars)")

    # Step 3: Find neighbors (off-targets)
    print("   3. Finding taxonomic neighbors (off-targets)...")
    neighbors = await bridge.call_tool(
        "database",
        "get_neighbors",
        {
            "taxon": "Salmo salar",
            "rank": "genus",
            "distance": 1
        }
    )
    print(f"   ✅ Found neighbors ({len(str(neighbors))} chars)")

    await bridge.shutdown()
    print("\n✅ Workflow test completed successfully!")
    print("\n💡 The AutoGen agents would use these tools to design qPCR assays")

if __name__ == "__main__":
    asyncio.run(test_workflow())
EOF

# Run workflow test
docker exec -i qpcr-assistant python /tmp/test_workflow.py
```

**Expected Output**:
```
🧪 Testing AutoGen Workflow Components...
✅ Created 5 AutoGen function definitions
🧪 Simulating Database Agent workflow...
   1. Retrieving COI sequences for Salmo salar...
   ✅ Retrieved sequences (2340 chars)
   2. Getting taxonomy information...
   ✅ Retrieved taxonomy (680 chars)
   3. Finding taxonomic neighbors (off-targets)...
   ✅ Found neighbors (450 chars)
✅ Workflow test completed successfully!
💡 The AutoGen agents would use these tools to design qPCR assays
```

### Test 3: Full AutoGen Multi-Agent System

**Purpose**: Test complete AutoGen conversation (requires OpenAI API key)

**Important**: This will use OpenAI API and incur costs (~$0.01-0.05 per run with GPT-4)

```bash
# Create interactive test
cat > /tmp/test_autogen_full.py << 'EOF'
import asyncio
import os
import sys
sys.path.insert(0, '/app')

from qpcr_assistant import QPCRAssistant

async def test_full_system():
    print("🧪 Testing Full AutoGen Multi-Agent System...")
    print("⚠️  This will use OpenAI API (requires API key)\n")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set!")
        print("   Set it in autogen_app/.env")
        return

    print("✅ OpenAI API key found\n")

    # Create assistant
    assistant = QPCRAssistant(api_key)

    try:
        # Initialize
        print("Initializing qPCR Assistant...")
        await assistant.initialize()
        print("✅ Assistant ready!\n")

        # Test request
        user_request = """
I need to design a qPCR assay to identify Atlantic salmon (Salmo salar).

Please:
1. Retrieve COI sequences for Salmo salar
2. Identify potential off-target species
3. Summarize findings

Keep the analysis brief for testing purposes.
"""

        print("📝 User Request:")
        print(user_request)
        print("\n🤖 Starting AutoGen workflow...\n")
        print("=" * 60)

        # Run workflow
        await assistant.run_workflow(user_request)

        print("=" * 60)
        print("\n✅ AutoGen workflow completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await assistant.shutdown()
        print("\n🏁 Test complete")

if __name__ == "__main__":
    asyncio.run(test_full_system())
EOF

# Run full test (requires OpenAI API key)
docker exec -i qpcr-assistant python /tmp/test_autogen_full.py
```

**Expected Output** (abbreviated):
```
🧪 Testing Full AutoGen Multi-Agent System...
✅ OpenAI API key found

Initializing qPCR Assistant...
MCP servers connected
✅ Assistant ready!

📝 User Request:
[... request shown ...]

🤖 Starting AutoGen workflow...
============================================================

User (to chat_manager):
I need to design a qPCR assay...

------------------------------------------------------------

Coordinator (to chat_manager):
I understand you need to design a qPCR assay for Atlantic salmon...
Let me coordinate with the Database Agent...

------------------------------------------------------------

DatabaseAgent (to chat_manager):
I'll retrieve the sequences now...
[calls get_sequences function]

------------------------------------------------------------

[... agent conversation continues ...]

============================================================
✅ AutoGen workflow completed!
🏁 Test complete
```

## Interactive Testing

### Manual Tool Testing

```bash
# Enter the qpcr-assistant container
docker exec -it qpcr-assistant bash

# Inside container, test individual tools
python3 << 'EOF'
import asyncio
from autogen_mcp_bridge import MCPClientBridge

async def test():
    bridge = MCPClientBridge({
        "database": {
            "container": "ndiag-database-server",
            "command": ["python", "/app/database_mcp_server.py"]
        }
    })
    await bridge.start_servers()

    # Test different queries
    result = await bridge.call_tool("database", "get_sequences", {
        "taxon": "Oncorhynchus mykiss",  # Rainbow trout
        "region": "COI",
        "max_results": 3
    })
    print("Sequences:", result[:200], "...")

    await bridge.shutdown()

asyncio.run(test())
EOF
```

### View Live Logs

```bash
# Terminal 1: Watch database server
docker logs -f ndiag-database-server

# Terminal 2: Watch qPCR assistant
docker logs -f qpcr-assistant

# Terminal 3: Run tests
docker exec -i qpcr-assistant python /tmp/test_workflow.py
```

## Troubleshooting

### Issue: MCP Server Not Starting

```bash
# Check logs
docker logs ndiag-database-server

# Rebuild if needed
docker-compose -f docker-compose.autogen.yml build database-server
docker-compose -f docker-compose.autogen.yml up -d database-server

# Verify Python dependencies
docker exec -i ndiag-database-server pip list | grep -E "(mcp|gget|biopython)"
```

### Issue: Bridge Connection Fails

```bash
# Test Docker exec access
docker exec -i ndiag-database-server echo "Connection OK"

# Test Python import
docker exec -i ndiag-database-server python -c "from database_mcp_server import handle_list_tools; print('Import OK')"

# Check network
docker network inspect ndiag-network
```

### Issue: OpenAI API Errors

```bash
# Verify API key is set
docker exec qpcr-assistant env | grep OPENAI_API_KEY

# Test API key validity
docker exec -i qpcr-assistant python -c "
import openai
import os
openai.api_key = os.getenv('OPENAI_API_KEY')
try:
    # Try a simple completion
    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'test'}],
        max_tokens=5
    )
    print('✅ API key valid')
except Exception as e:
    print(f'❌ API error: {e}')
"
```

### Issue: Rate Limits

```bash
# If hitting NCBI rate limits, add API key
# Edit autogen_app/.env and add:
NCBI_API_KEY=your_ncbi_api_key

# Restart services
docker-compose -f docker-compose.autogen.yml restart
```

## Performance Testing

### Test Response Times

```bash
cat > /tmp/benchmark.py << 'EOF'
import asyncio
import time
import sys
sys.path.insert(0, '/app')

from autogen_mcp_bridge import MCPClientBridge

async def benchmark():
    bridge = MCPClientBridge({
        "database": {
            "container": "ndiag-database-server",
            "command": ["python", "/app/database_mcp_server.py"]
        }
    })
    await bridge.start_servers()

    # Benchmark different tools
    tools = [
        ("get_taxonomy", {"query": "Salmo salar"}),
        ("get_sequences", {"taxon": "Salmo salar", "region": "COI", "max_results": 5}),
        ("get_neighbors", {"taxon": "Salmo salar", "rank": "genus"}),
    ]

    print("🏃 Performance Benchmark\n")

    for tool_name, args in tools:
        start = time.time()
        result = await bridge.call_tool("database", tool_name, args)
        elapsed = time.time() - start
        print(f"{tool_name:20s}: {elapsed:6.2f}s (result: {len(str(result)):6d} chars)")

    await bridge.shutdown()

asyncio.run(benchmark())
EOF

docker exec -i qpcr-assistant python /tmp/benchmark.py
```

## Cleanup

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.autogen.yml down

# Stop and remove volumes
docker-compose -f docker-compose.autogen.yml down -v
```

### Remove Test Files

```bash
docker exec qpcr-assistant rm -f /tmp/test_*.py /tmp/benchmark.py
```

## Next Steps

After successful testing:

1. **Extend Workflows**: Add more complex qPCR design scenarios
2. **Add Phases 2-6**: Implement processing, alignment, design servers
3. **Build UI**: Create Streamlit interface for scientists
4. **Deploy to K8s**: Use kubernetes manifests for production
5. **Monitor Performance**: Set up logging and metrics

## Test Checklist

- [ ] Environment configured (.env with API keys)
- [ ] Docker services running
- [ ] MCP server accessible
- [ ] Bridge connection test passes
- [ ] Workflow simulation passes
- [ ] (Optional) Full AutoGen test passes
- [ ] Response times acceptable (<10s per tool)
- [ ] No errors in logs

## Getting Help

If tests fail:
1. Check logs: `docker logs ndiag-database-server` and `docker logs qpcr-assistant`
2. Verify network: `docker network inspect ndiag-network`
3. Test MCP directly: Run the verification commands above
4. Review documentation: `AUTOGEN_INTEGRATION.md`, `DEPLOYMENT.md`
5. Check API keys are valid

**Happy Testing! 🧪**
