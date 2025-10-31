#!/bin/bash
set -e

# Entrypoint script for database MCP server
# Fixes permissions on shared volumes and drops privileges to mcp user

echo "🔧 Database MCP Server - Starting..."

# Fix permissions on shared volumes
# This ensures the mcp user can read/write to these directories
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

# If running as root, drop privileges to mcp user
if [ "$(id -u)" = "0" ]; then
    echo "   • Dropping privileges to user 'mcp'..."
    
    # Execute the command as mcp user
    # If no command provided, start the MCP server
    if [ $# -eq 0 ]; then
        exec gosu mcp python /app/database_mcp_server.py
    else
        exec gosu mcp "$@"
    fi
else
    # Already running as non-root, just execute
    echo "   • Running as user $(whoami)"
    if [ $# -eq 0 ]; then
        exec python /app/database_mcp_server.py
    else
        exec "$@"
    fi
fi

