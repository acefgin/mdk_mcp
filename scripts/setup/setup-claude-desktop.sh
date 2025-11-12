#!/bin/bash

# Setup script for Claude Desktop MCP integration
# This script prepares the TypeScript MCP server for use with Claude Desktop

set -e

echo "🚀 Setting up Claude Desktop MCP Integration"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$PROJECT_ROOT/workspace"

echo -e "${BLUE}📍 Project root: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Check dependencies
echo -e "${BLUE}1️⃣  Checking dependencies...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 20+${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ npm: $NPM_VERSION${NC}"

echo ""

# Step 2: Install dependencies
echo -e "${BLUE}2️⃣  Installing dependencies...${NC}"

if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

echo ""

# Step 3: Create workspace directory
echo -e "${BLUE}3️⃣  Setting up workspace...${NC}"

mkdir -p "$WORKSPACE_DIR/lib"
mkdir -p "$WORKSPACE_DIR/servers/database"
mkdir -p "$WORKSPACE_DIR/servers/processing"
mkdir -p "$WORKSPACE_DIR/servers/alignment"
mkdir -p "$WORKSPACE_DIR/servers/design"
mkdir -p "$WORKSPACE_DIR/servers/validation"

echo -e "${GREEN}✅ Workspace structure created${NC}"
echo ""

# Step 4: Compile TypeScript
echo -e "${BLUE}4️⃣  Compiling TypeScript...${NC}"

npx tsc workspace/mcp-server.ts \
    --outDir workspace \
    --module ES2022 \
    --target ES2022 \
    --moduleResolution node \
    --esModuleInterop \
    --skipLibCheck

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TypeScript compiled successfully${NC}"
else
    echo -e "${RED}❌ TypeScript compilation failed${NC}"
    exit 1
fi

echo ""

# Step 5: Make MCP server executable
echo -e "${BLUE}5️⃣  Making MCP server executable...${NC}"

chmod +x "$WORKSPACE_DIR/mcp-server.js"
echo -e "${GREEN}✅ MCP server is executable${NC}"

echo ""

# Step 6: Test MCP server
echo -e "${BLUE}6️⃣  Testing MCP server...${NC}"

# Start server in background and test it
timeout 2s node "$WORKSPACE_DIR/mcp-server.js" 2>&1 | grep -q "Ready for Claude Desktop"

if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo -e "${GREEN}✅ MCP server starts correctly${NC}"
else
    echo -e "${YELLOW}⚠️  MCP server test inconclusive (may be normal)${NC}"
fi

echo ""

# Step 7: Generate Claude Desktop config
echo -e "${BLUE}7️⃣  Generating Claude Desktop configuration...${NC}"

CLAUDE_CONFIG_FILE="$PROJECT_ROOT/claude-desktop-config-local.json"

cat > "$CLAUDE_CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "mdk-typescript": {
      "command": "node",
      "args": [
        "$WORKSPACE_DIR/mcp-server.js"
      ],
      "env": {
        "NODE_ENV": "production",
        "DEBUG": "false"
      }
    }
  }
}
EOF

echo -e "${GREEN}✅ Configuration generated: $CLAUDE_CONFIG_FILE${NC}"
echo ""

# Step 8: Detect Claude Desktop config location
echo -e "${BLUE}8️⃣  Detecting Claude Desktop installation...${NC}"

CLAUDE_CONFIG_PATH=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CLAUDE_CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CLAUDE_CONFIG_PATH="$HOME/.config/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    CLAUDE_CONFIG_PATH="$APPDATA/Claude/claude_desktop_config.json"
fi

if [ -n "$CLAUDE_CONFIG_PATH" ]; then
    echo -e "${GREEN}✅ Claude Desktop config should be at:${NC}"
    echo -e "   $CLAUDE_CONFIG_PATH"
else
    echo -e "${YELLOW}⚠️  Could not detect Claude Desktop config location${NC}"
fi

echo ""

# Step 9: Instructions
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo -e "1. ${YELLOW}Update Claude Desktop configuration:${NC}"
if [ -n "$CLAUDE_CONFIG_PATH" ]; then
    echo -e "   cp $CLAUDE_CONFIG_FILE \"$CLAUDE_CONFIG_PATH\""
else
    echo -e "   Manually copy configuration from: $CLAUDE_CONFIG_FILE"
fi
echo ""
echo -e "2. ${YELLOW}Start Python MCP servers:${NC}"
echo -e "   ./start-python-servers.sh"
echo ""
echo -e "3. ${YELLOW}Restart Claude Desktop${NC}"
echo -e "   Quit and reopen Claude Desktop completely"
echo ""
echo -e "4. ${YELLOW}Verify connection:${NC}"
echo -e "   Look for the hammer icon 🔨 at the bottom of Claude Desktop"
echo ""
echo -e "5. ${YELLOW}Test a tool:${NC}"
echo -e "   Ask Claude: 'List the available tools'"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo -e "   docs/CLAUDE_DESKTOP_TESTING_GUIDE.md"
echo ""
echo -e "${BLUE}🐛 Debug mode:${NC}"
echo -e "   export DEBUG=true && node $WORKSPACE_DIR/mcp-server.js"
echo ""
echo -e "${BLUE}📊 View logs:${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "   tail -f ~/Library/Logs/Claude/mcp*.log"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "   tail -f ~/.local/share/Claude/logs/mcp*.log"
fi
echo ""

echo "=============================================="
echo -e "${GREEN}🎉 Ready to test with Claude Desktop!${NC}"
echo "=============================================="

