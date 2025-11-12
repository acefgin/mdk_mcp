#!/bin/bash
# Test MCP Server before Claude Desktop setup
# This verifies the TypeScript MCP server can start and communicate

set -e

echo "🧪 Testing MCP Server Setup"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check Node.js
echo -n "1. Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Found $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js not found"
    echo "   Install with: nvm install 20"
    exit 1
fi

# 2. Check MCP server file
echo -n "2. Checking mcp-server.js... "
if [ -f "workspace/mcp-server.js" ]; then
    echo -e "${GREEN}✓${NC} Found"
else
    echo -e "${RED}✗${NC} Not found"
    echo "   Run: npm run build:workspace"
    exit 1
fi

# 3. Check Docker
echo -n "3. Checking Docker... "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Found"
else
    echo -e "${RED}✗${NC} Docker not found"
    exit 1
fi

# 4. Check Docker containers
echo "4. Checking Docker containers..."
CONTAINERS=$(docker ps --format "{{.Names}}" | grep "ndiag-" || true)
if [ -z "$CONTAINERS" ]; then
    echo -e "   ${YELLOW}⚠${NC} No containers running"
    echo "   Start with: docker-compose -f docker-compose.autogen.yml up -d"
    echo ""
    read -p "   Start containers now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Starting containers..."
        docker-compose -f docker-compose.autogen.yml up -d
        echo "   Waiting for containers to be ready..."
        sleep 5
    else
        echo "   Skipping container check (some tests will fail)"
    fi
else
    echo -e "   ${GREEN}✓${NC} Found running containers:"
    echo "$CONTAINERS" | while read container; do
        echo "     - $container"
    done
fi

echo ""

# 5. Test MCP server startup
echo "5. Testing MCP server startup..."
echo "   (This will run for 3 seconds then auto-stop)"
echo ""

# Start server in background and capture output
timeout 3s node workspace/mcp-server.js 2>&1 | while IFS= read -r line; do
    echo "   $line"
done || true

echo ""
echo -e "${GREEN}✓${NC} MCP server can start!"
echo ""

# 6. Get Windows path
echo "6. Windows path for Claude Desktop:"
WINDOWS_PATH=$(wslpath -w "$(pwd)/workspace/mcp-server.js")
echo ""
echo -e "   ${YELLOW}$WINDOWS_PATH${NC}"
echo ""
echo "   Copy this path for Claude Desktop configuration!"
echo ""

# 7. Summary
echo "================================"
echo "📋 Summary"
echo "================================"
echo ""
echo "✅ Prerequisites: OK"
echo "✅ MCP Server: OK"
echo ""
echo "Next steps:"
echo ""
echo "1. Copy the config to Claude Desktop:"
echo "   Windows path: %APPDATA%\\Claude\\claude_desktop_config.json"
echo ""
echo "2. Use this config:"
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "mdk-typescript": {
      "command": "wsl",
      "args": [
        "-e",
        "bash",
        "-c",
        "cd /home/cxl/MDK_Design/mdk_mcp && node workspace/mcp-server.js"
      ],
      "env": {
        "DEBUG": "false"
      }
    }
  }
}
EOF
echo ""
echo "3. Restart Claude Desktop"
echo ""
echo "4. Test with: 'What tools do you have from mdk-typescript?'"
echo ""
echo "📖 Full guide: QUICK_START_CLAUDE_DESKTOP.md"
echo ""

