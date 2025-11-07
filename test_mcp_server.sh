#!/bin/bash
# MCP Server Docker Test Script with Inspector Launch
# Usage: ./test_mcp_server.sh [database|processing|alignment|design|validation]

set -e

SERVER_TYPE="${1:-database}"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${BLUE}Testing ${SERVER_TYPE} MCP Server (Docker)${RESET}"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${RESET}"
    exit 1
fi

# Check Node.js and npx for Inspector
if ! command -v npx &> /dev/null; then
    echo -e "${RED}✗ npx not found (needed for MCP Inspector)${RESET}"
    exit 1
fi

# Set server directory and container name
case "$SERVER_TYPE" in
  database)
    SERVER_DIR="mcp_servers/database_server"
    CONTAINER_NAME="ndiag-database-server"
    SERVER_SCRIPT="/app/database_mcp_server.py"
    ;;
  processing)
    SERVER_DIR="mcp_servers/processing_server"
    CONTAINER_NAME="ndiag-processing-server"
    SERVER_SCRIPT="/app/processing_mcp_server.py"
    ;;
  alignment)
    SERVER_DIR="mcp_servers/alignment_server"
    CONTAINER_NAME="ndiag-alignment-server"
    SERVER_SCRIPT="/app/alignment_mcp_server.py"
    ;;
  design)
    SERVER_DIR="mcp_servers/design_server"
    CONTAINER_NAME="ndiag-design-server"
    SERVER_SCRIPT="/app/design_mcp_server.py"
    ;;
  validation)
    SERVER_DIR="mcp_servers/validation_server"
    CONTAINER_NAME="ndiag-validation-server"
    SERVER_SCRIPT="/app/validation_mcp_server.py"
    ;;
  *)
    echo -e "${RED}✗ Unknown server: $SERVER_TYPE${RESET}"
    echo "Usage: $0 [database|processing|alignment|design|validation]"
    exit 1
    ;;
esac

cd "$SERVER_DIR" || exit 1

# Kill any existing Inspector processes
echo "Cleaning up old Inspector processes..."
pkill -f "@modelcontextprotocol/inspector" 2>/dev/null || true
rm -f /tmp/mcp_*_wrapper.sh /tmp/inspector_output.log 2>/dev/null || true
sleep 1

# Cleanup, build, and start
echo "Preparing container..."
docker-compose down 2>/dev/null || true
docker-compose build --quiet
docker-compose up -d
sleep 3

# Verify container is running
if docker ps | grep -q "$CONTAINER_NAME"; then
    STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_NAME")
    if [ "$STATUS" = "running" ]; then
        echo -e "${GREEN}✓ Container running and ready${RESET}"
        echo ""
        echo -e "${GREEN}========================================${RESET}"
        echo -e "${GREEN}✅ ${SERVER_TYPE} Server: PASSED${RESET}"
        echo -e "${GREEN}========================================${RESET}"
        echo ""
        
        # Create wrapper script for Inspector to connect to Docker container
        WRAPPER_SCRIPT="/tmp/mcp_${SERVER_TYPE}_wrapper.sh"
        cat > "$WRAPPER_SCRIPT" << 'WRAPPER_EOF'
#!/bin/bash
exec docker exec -i CONTAINER_NAME_PLACEHOLDER python3 SERVER_SCRIPT_PLACEHOLDER "$@"
WRAPPER_EOF
        # Replace placeholders with actual values
        sed -i "s|CONTAINER_NAME_PLACEHOLDER|$CONTAINER_NAME|g" "$WRAPPER_SCRIPT"
        sed -i "s|SERVER_SCRIPT_PLACEHOLDER|$SERVER_SCRIPT|g" "$WRAPPER_SCRIPT"
        chmod +x "$WRAPPER_SCRIPT"
        
        # Show wrapper script for debugging
        echo -e "${BLUE}Created wrapper script:${RESET}"
        cat "$WRAPPER_SCRIPT"
        echo ""
        
        echo -e "${BLUE}Starting MCP Inspector...${RESET}"
        echo ""
        echo -e "${YELLOW}Inspector will open at: http://localhost:6274${RESET}"
        echo -e "${YELLOW}Wait for 'Inspector running' message, then browser will open${RESET}"
        echo -e "${YELLOW}Press Ctrl+C to stop the Inspector${RESET}"
        echo ""
        
        # Launch Inspector in background and capture its output
        echo -e "${BLUE}Launching Inspector UI...${RESET}"
        # Disable auth for simpler local development
        DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector "$WRAPPER_SCRIPT" > /tmp/inspector_output.log 2>&1 &
        INSPECTOR_PID=$!
        
        # Wait for Inspector to be ready (check for "Inspector running" or port 6274)
        echo "Waiting for Inspector to start..."
        for i in {1..30}; do
            if netstat -tln 2>/dev/null | grep -q ':6274 ' || ss -tln 2>/dev/null | grep -q ':6274 '; then
                echo -e "${GREEN}✓ Inspector is ready${RESET}"
                sleep 2  # Give it 2 more seconds to fully initialize
                break
            fi
            if [ $i -eq 30 ]; then
                echo -e "${RED}✗ Inspector failed to start${RESET}"
                cat /tmp/inspector_output.log
                kill $INSPECTOR_PID 2>/dev/null
                rm -f "$WRAPPER_SCRIPT"
                exit 1
            fi
            sleep 1
        done
        
        # Now open browser with cache-busting parameter
        echo ""
        TIMESTAMP=$(date +%s)
        if grep -qi microsoft /proc/version 2>/dev/null; then
            # Running in WSL - use Windows browser
            echo -e "${GREEN}✓ Opening in Windows browser (fresh session)${RESET}"
            cmd.exe /c start "http://localhost:6274/?t=$TIMESTAMP" 2>/dev/null
        elif command -v xdg-open &> /dev/null; then
            # Linux native
            xdg-open "http://localhost:6274/?t=$TIMESTAMP" 2>/dev/null &
        elif command -v open &> /dev/null; then
            # macOS
            open "http://localhost:6274/?t=$TIMESTAMP" 2>/dev/null &
        fi
        
        # Bring Inspector to foreground and wait for it
        wait $INSPECTOR_PID
        
        # Cleanup on exit
        echo ""
        echo "Cleaning up..."
        rm -f "$WRAPPER_SCRIPT"
        exit 0
    else
        echo -e "${RED}✗ Container status: $STATUS${RESET}"
    fi
else
    echo -e "${RED}✗ Container not found${RESET}"
fi

# Failure - show logs
docker-compose logs --tail=20
docker-compose down
exit 1
