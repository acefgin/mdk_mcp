#!/bin/bash
# Quick test script for MCP servers using Inspector
# Usage: ./test_mcp_server.sh [database|processing]

set -e

SERVER_TYPE="${1:-database}"
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}MCP Server Testing Script${COLOR_RESET}"
echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
echo ""

# Check Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${COLOR_RED}✗ Node.js not found${COLOR_RESET}"
    echo "Please install Node.js v22.7.5 or higher"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 22 ]; then
    echo -e "${COLOR_YELLOW}⚠ Node.js version is ${NODE_VERSION}, recommend v22+${COLOR_RESET}"
fi

echo -e "${COLOR_GREEN}✓ Node.js $(node --version) found${COLOR_RESET}"

# Check npx is available
if ! command -v npx &> /dev/null; then
    echo -e "${COLOR_RED}✗ npx not found${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_GREEN}✓ npx found${COLOR_RESET}"
echo ""

# Check for existing inspector processes
if lsof -i :6274 &> /dev/null || lsof -i :6277 &> /dev/null; then
    echo -e "${COLOR_YELLOW}⚠ Inspector ports (6274, 6277) are already in use${COLOR_RESET}"
    echo "Existing inspector processes found:"
    ps aux | grep -E "inspector|6274|6277" | grep -v grep | head -5
    echo ""
    read -p "Kill existing inspector processes? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing existing inspector processes..."
        pkill -f "@modelcontextprotocol/inspector" || true
        sleep 2
        echo -e "${COLOR_GREEN}✓ Cleaned up existing processes${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}✗ Cannot start inspector while ports are in use${COLOR_RESET}"
        echo "Please manually kill the processes or use different ports"
        exit 1
    fi
    echo ""
fi

case "$SERVER_TYPE" in
  database)
    echo -e "${COLOR_BLUE}Testing Database Server${COLOR_RESET}"
    echo "=========================================="

    cd mcp_servers/database_server || exit 1

    # Check Python dependencies
    echo "Checking Python dependencies..."
    if python3 -c "import gget, Bio, pysradb" 2>/dev/null; then
        echo -e "${COLOR_GREEN}✓ Python dependencies OK${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}⚠ Installing dependencies...${COLOR_RESET}"
        pip install -r requirements.txt
    fi

    # Check syntax
    echo "Checking Python syntax..."
    if python3 -m py_compile database_mcp_server.py config.py; then
        echo -e "${COLOR_GREEN}✓ Python syntax OK${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}✗ Syntax errors found${COLOR_RESET}"
        exit 1
    fi

    echo ""
    echo -e "${COLOR_BLUE}Testing server communication...${COLOR_RESET}"
    
    # Test server by sending a direct MCP request
    TEST_OUTPUT=$(timeout 5 python3 << 'EOF' 2>&1
import asyncio
import json
import sys

async def test_server():
    proc = await asyncio.create_subprocess_exec(
        "python3", "database_mcp_server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Send initialize request
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    proc.stdin.write((json.dumps(init_req) + "\n").encode())
    await proc.stdin.drain()
    
    # Read response
    response = await asyncio.wait_for(proc.stdout.readline(), timeout=3)
    init_result = json.loads(response.decode())
    
    if not init_result.get("result"):
        print(f"ERROR: Init failed: {init_result}")
        proc.kill()
        return False
    
    # Send tools/list request
    tools_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    proc.stdin.write((json.dumps(tools_req) + "\n").encode())
    await proc.stdin.drain()
    
    # Read response
    response = await asyncio.wait_for(proc.stdout.readline(), timeout=3)
    tools_result = json.loads(response.decode())
    
    if tools_result.get("result") and tools_result["result"].get("tools"):
        tools = tools_result["result"]["tools"]
        print(f"✓ Server responded with {len(tools)} tools:")
        for tool in tools[:5]:
            print(f"  - {tool['name']}")
        if len(tools) > 5:
            print(f"  ... and {len(tools) - 5} more")
    else:
        print(f"ERROR: Tools list failed: {tools_result}")
        proc.kill()
        return False
    
    proc.kill()
    return True

try:
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
)
    TEST_EXIT=$?
    
    if [ $TEST_EXIT -ne 0 ]; then
        echo -e "${COLOR_RED}✗ Server test failed${COLOR_RESET}"
        echo "$TEST_OUTPUT"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check Python dependencies: python3 -c 'import gget, Bio, pysradb'"
        echo "  2. Check server directly: python3 database_mcp_server.py"
        echo "  3. Check logs for errors"
        exit 1
    fi
    
    echo "$TEST_OUTPUT"

    echo ""
    echo -e "${COLOR_GREEN}========================================${COLOR_RESET}"
    echo -e "${COLOR_GREEN}Database Server Ready for Testing!${COLOR_RESET}"
    echo -e "${COLOR_GREEN}========================================${COLOR_RESET}"
    echo ""
    echo "To launch UI mode, run:"
    echo -e "${COLOR_YELLOW}  cd mcp_servers/database_server${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}  npx @modelcontextprotocol/inspector python3 database_mcp_server.py${COLOR_RESET}"
    echo ""
    echo "Then open: http://localhost:6274"
    ;;

  processing)
    echo -e "${COLOR_BLUE}Testing Processing Server${COLOR_RESET}"
    echo "=========================================="

    cd mcp_servers/processing_server || exit 1

    # Check Python dependencies
    echo "Checking Python dependencies..."
    if python3 -c "import Bio" 2>/dev/null; then
        echo -e "${COLOR_GREEN}✓ Python dependencies OK${COLOR_RESET}"
    else
        echo -e "${COLOR_YELLOW}⚠ Installing dependencies...${COLOR_RESET}"
        pip install -r requirements.txt
    fi

    # Check external tools
    echo "Checking external tools..."
    TOOLS_OK=true

    if command -v seqkit &> /dev/null; then
        echo -e "${COLOR_GREEN}✓ seqkit $(seqkit version 2>&1 | head -1) found${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}✗ seqkit not found${COLOR_RESET}"
        TOOLS_OK=false
    fi

    if command -v vsearch &> /dev/null; then
        echo -e "${COLOR_GREEN}✓ vsearch $(vsearch --version 2>&1 | head -1) found${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}✗ vsearch not found${COLOR_RESET}"
        TOOLS_OK=false
    fi

    if [ "$TOOLS_OK" = false ]; then
        echo ""
        echo -e "${COLOR_YELLOW}⚠ External tools missing${COLOR_RESET}"
        echo "Options:"
        echo "  1. Install tools manually (see docs/MCP_TESTING_GUIDE.md)"
        echo "  2. Use Docker (recommended):"
        echo -e "     ${COLOR_YELLOW}docker-compose up --build${COLOR_RESET}"
        echo ""
        exit 1
    fi

    # Check syntax
    echo "Checking Python syntax..."
    if python3 -m py_compile processing_mcp_server.py config.py; then
        echo -e "${COLOR_GREEN}✓ Python syntax OK${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}✗ Syntax errors found${COLOR_RESET}"
        exit 1
    fi

    echo ""
    echo -e "${COLOR_BLUE}Listing available tools...${COLOR_RESET}"
    
    # Capture inspector output and check for errors
    INSPECTOR_OUTPUT=$(npx @modelcontextprotocol/inspector \
      --method tools/list \
      python3 processing_mcp_server.py 2>&1)
    INSPECTOR_EXIT=$?
    
    if [ $INSPECTOR_EXIT -ne 0 ] || echo "$INSPECTOR_OUTPUT" | grep -q "PORT IS IN USE\|error\|Error"; then
        echo -e "${COLOR_RED}✗ Inspector failed to start${COLOR_RESET}"
        echo "$INSPECTOR_OUTPUT" | head -10
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check if ports 6274, 6277 are available: lsof -i :6274 -i :6277"
        echo "  2. Kill existing inspector: pkill -f inspector"
        echo "  3. Check Python server directly: python3 processing_mcp_server.py --help"
        exit 1
    fi
    
    echo "$INSPECTOR_OUTPUT" | head -20

    echo ""
    echo -e "${COLOR_GREEN}========================================${COLOR_RESET}"
    echo -e "${COLOR_GREEN}Processing Server Ready for Testing!${COLOR_RESET}"
    echo -e "${COLOR_GREEN}========================================${COLOR_RESET}"
    echo ""
    echo "To launch UI mode, run:"
    echo -e "${COLOR_YELLOW}  cd mcp_servers/processing_server${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}  npx @modelcontextprotocol/inspector python3 processing_mcp_server.py${COLOR_RESET}"
    echo ""
    echo "Then open: http://localhost:6274"
    ;;

  *)
    echo -e "${COLOR_RED}✗ Unknown server type: $SERVER_TYPE${COLOR_RESET}"
    echo "Usage: $0 [database|processing]"
    exit 1
    ;;
esac

echo ""
echo "For detailed testing instructions, see:"
echo "  docs/MCP_TESTING_GUIDE.md"
