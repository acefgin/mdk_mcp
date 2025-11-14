#!/bin/bash

# Start all Python MCP servers required for TypeScript wrappers
# These servers must be running for the TypeScript MCP server to work

set -e

echo "🐍 Starting Python MCP Servers"
echo "==============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
echo ""

# Check if pm2 is available (optional)
USE_PM2=false
if command -v pm2 &> /dev/null; then
    echo -e "${BLUE}📦 PM2 detected - will use for process management${NC}"
    USE_PM2=true
else
    echo -e "${YELLOW}⚠️  PM2 not found - will start servers in background${NC}"
    echo -e "${YELLOW}   Install with: npm install -g pm2${NC}"
fi

echo ""

# Server configurations
declare -a SERVERS=(
    "database:mcp_servers.database_server.database_mcp_server"
    "processing:mcp_servers.processing_server.processing_mcp_server"
    "alignment:mcp_servers.alignment_server.alignment_mcp_server"
    "design:mcp_servers.design_server.design_mcp_server"
    "validation:mcp_servers.validation_server.validation_mcp_server"
)

if [ "$USE_PM2" = true ]; then
    # Use PM2 for process management
    echo -e "${BLUE}Starting servers with PM2...${NC}"
    echo ""
    
    for server in "${SERVERS[@]}"; do
        IFS=':' read -r name module <<< "$server"
        
        echo -e "${BLUE}Starting $name server...${NC}"
        pm2 start python3 --name "mcp-$name" -- -m "$module"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ $name server started${NC}"
        else
            echo -e "${RED}❌ Failed to start $name server${NC}"
        fi
        echo ""
    done
    
    echo -e "${GREEN}✅ All servers started with PM2${NC}"
    echo ""
    echo -e "${BLUE}📊 Server Status:${NC}"
    pm2 list
    echo ""
    echo -e "${BLUE}📝 View logs:${NC}"
    echo -e "   pm2 logs"
    echo ""
    echo -e "${BLUE}🛑 Stop all servers:${NC}"
    echo -e "   pm2 stop all"
    echo -e "   pm2 delete all"
    
else
    # Start servers in background without PM2
    echo -e "${BLUE}Starting servers in background...${NC}"
    echo ""
    
    PIDS_FILE="$PROJECT_ROOT/.python-server-pids"
    > "$PIDS_FILE"  # Clear PIDs file
    
    for server in "${SERVERS[@]}"; do
        IFS=':' read -r name module <<< "$server"
        
        LOG_FILE="$PROJECT_ROOT/logs/mcp-$name.log"
        mkdir -p "$PROJECT_ROOT/logs"
        
        echo -e "${BLUE}Starting $name server...${NC}"
        nohup python3 -m "$module" > "$LOG_FILE" 2>&1 &
        PID=$!
        
        # Store PID
        echo "$PID:$name" >> "$PIDS_FILE"
        
        # Wait a moment to see if it starts
        sleep 1
        
        if ps -p $PID > /dev/null; then
            echo -e "${GREEN}✅ $name server started (PID: $PID)${NC}"
            echo -e "   Log: $LOG_FILE"
        else
            echo -e "${RED}❌ Failed to start $name server${NC}"
        fi
        echo ""
    done
    
    echo -e "${GREEN}✅ All servers started${NC}"
    echo ""
    echo -e "${BLUE}📝 View logs:${NC}"
    echo -e "   tail -f logs/mcp-*.log"
    echo ""
    echo -e "${BLUE}🛑 Stop all servers:${NC}"
    echo -e "   ./stop-python-servers.sh"
    echo ""
    echo -e "${BLUE}📊 Check server status:${NC}"
    echo -e "   ./check-python-servers.sh"
fi

echo ""
echo "==============================="
echo -e "${GREEN}🎉 Python MCP servers running!${NC}"
echo "==============================="
echo ""
echo -e "${BLUE}Next step:${NC}"
echo -e "  Run the TypeScript MCP server or test with Claude Desktop"
echo ""

