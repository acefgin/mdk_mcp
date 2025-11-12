#!/bin/bash

# Stop all Python MCP servers

echo "🛑 Stopping Python MCP Servers"
echo "==============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDS_FILE="$PROJECT_ROOT/.python-server-pids"

# Check if using PM2
if command -v pm2 &> /dev/null; then
    PM2_LIST=$(pm2 list | grep -c "mcp-")
    if [ "$PM2_LIST" -gt 0 ]; then
        echo "Stopping PM2 servers..."
        pm2 stop all
        pm2 delete all
        echo -e "${GREEN}✅ All PM2 servers stopped${NC}"
        exit 0
    fi
fi

# Stop servers using PID file
if [ -f "$PIDS_FILE" ]; then
    while IFS=':' read -r pid name; do
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Stopping $name (PID: $pid)..."
            kill "$pid"
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${RED}⚠️  $name not running (PID: $pid)${NC}"
        fi
    done < "$PIDS_FILE"
    
    rm "$PIDS_FILE"
    echo ""
    echo -e "${GREEN}✅ All servers stopped${NC}"
else
    echo -e "${RED}No PID file found. Searching for running servers...${NC}"
    
    # Try to find and kill Python MCP servers
    pkill -f "mcp_servers.*mcp_server"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Servers stopped${NC}"
    else
        echo -e "${RED}No running servers found${NC}"
    fi
fi

echo ""

