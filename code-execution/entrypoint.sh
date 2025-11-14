#!/bin/sh
set -e

# Entrypoint script for code-execution sandbox
# Fixes permissions on shared volumes and drops privileges to sandbox user

echo "🔧 Code Execution Sandbox - Starting..."

# Fix permissions on shared volumes
# This ensures the sandbox user can read/write to these directories
if [ -d "/workspace/data" ]; then
    echo "   • Fixing permissions on /workspace/data..."
    chown -R sandbox:sandbox /workspace/data 2>/dev/null || true
    chmod -R 775 /workspace/data 2>/dev/null || true
fi

if [ -d "/workspace/cache" ]; then
    echo "   • Fixing permissions on /workspace/cache..."
    chown -R sandbox:sandbox /workspace/cache 2>/dev/null || true
    chmod -R 775 /workspace/cache 2>/dev/null || true
fi

if [ -d "/workspace/results" ]; then
    echo "   • Fixing permissions on /workspace/results..."
    chown -R sandbox:sandbox /workspace/results 2>/dev/null || true
    chmod -R 775 /workspace/results 2>/dev/null || true
fi

if [ -d "/workspace" ]; then
    echo "   • Ensuring workspace base directory permissions..."
    chown sandbox:sandbox /workspace 2>/dev/null || true
    chmod 775 /workspace 2>/dev/null || true
fi

echo "   ✓ Permissions configured"

# If running as root, drop privileges to sandbox user
if [ "$(id -u)" = "0" ]; then
    echo "   • Dropping privileges to user 'sandbox'..."
    
    # Execute the command as sandbox user
    # If no command provided, start the MCP server
    if [ $# -eq 0 ]; then
        exec su-exec sandbox node dist/executor.js
    else
        exec su-exec sandbox "$@"
    fi
else
    # Already running as non-root, just execute
    echo "   • Running as user $(whoami)"
    if [ $# -eq 0 ]; then
        exec node dist/executor.js
    else
        exec "$@"
    fi
fi

