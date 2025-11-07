#!/bin/bash
set -e

# Create necessary directories with proper permissions
mkdir -p /tmp/mcp_validation /tmp/mcp_validation/blast_cache /results/validation
chown -R mcp:mcp /tmp/mcp_validation /results/validation

# If running as root, drop privileges
if [ "$(id -u)" = "0" ]; then
    # Run command as mcp user
    exec gosu mcp "$@"
else
    # Already non-root, just execute command
    exec "$@"
fi
