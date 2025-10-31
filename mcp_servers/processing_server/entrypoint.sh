#!/bin/bash
set -e

# Entrypoint script for processing MCP server
# Fixes permissions on shared volumes and drops privileges to mcp user

echo "🔧 Processing MCP Server - Starting..."

# Fix permissions on shared volumes
if [ -d "/results" ]; then
    echo "   • Fixing permissions on /results..."
    chown -R mcp:mcp /results 2>/dev/null || true
    chmod -R 775 /results 2>/dev/null || true
fi

if [ -d "/tmp/mcp_cache" ]; then
    echo "   • Fixing permissions on /tmp/mcp_cache..."
    chown -R mcp:mcp /tmp/mcp_cache 2>/dev/null || true
    chmod -R 775 /tmp/mcp_cache 2>/dev/null || true
fi

echo "   ✓ Permissions configured"

# Drop privileges to mcp user if running as root
if [ "$(id -u)" = "0" ]; then
    echo "   • Dropping privileges to user 'mcp'..."
    if [ $# -eq 0 ]; then
        exec gosu mcp python3 /app/processing_mcp_server.py
    else
        exec gosu mcp "$@"
    fi
else
    echo "   • Running as user $(whoami)"
    if [ $# -eq 0 ]; then
        exec python3 /app/processing_mcp_server.py
    else
        exec "$@"
    fi
fi

