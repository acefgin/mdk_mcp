# Code Execution Sandbox Dockerfile
# Multi-stage build for minimal attack surface
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files from code-execution directory
COPY code-execution/package.json code-execution/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production

# Production stage with security hardening
FROM node:20-alpine

# Create non-root user for code execution
RUN addgroup -g 1001 -S sandbox && \
    adduser -u 1001 -S sandbox -G sandbox

# Install security tools, minimal utilities, Docker CLI, and su-exec for privilege dropping
RUN apk add --no-cache \
    dumb-init \
    tini \
    docker-cli \
    su-exec \
    && rm -rf /var/cache/apk/*

# Create docker group with same GID as host (110) and add sandbox user to it
# This allows sandbox user to access Docker socket
RUN addgroup -g 110 docker 2>/dev/null || true && \
    addgroup sandbox docker

# Create workspace directory with proper permissions
RUN mkdir -p /workspace/data /workspace/cache /workspace/results && \
    chown -R sandbox:sandbox /workspace

# Set working directory
WORKDIR /app

# Copy node_modules from builder
COPY --from=builder /build/node_modules ./node_modules

# Copy application code from code-execution directory
COPY --chown=sandbox:sandbox code-execution/ .

# Create TypeScript build
RUN npm run build 2>/dev/null || echo "No build script defined"

# Copy workspace scripts (MCP tool modules, libraries, and types)
# These are now packaged into the image instead of being mounted at runtime
COPY --chown=sandbox:sandbox workspace/servers /workspace/servers
COPY --chown=sandbox:sandbox workspace/lib /workspace/lib
COPY --chown=sandbox:sandbox workspace/types /workspace/types

# Copy entrypoint script (as root, make executable)
COPY code-execution/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Don't switch to non-root user yet - entrypoint will do it after fixing permissions

# Set resource limits via env vars (enforced by Docker)
ENV NODE_OPTIONS="--max-old-space-size=512"
ENV EXECUTION_TIMEOUT="30000"
ENV MAX_OUTPUT_SIZE="1048576"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

# Use entrypoint script to fix permissions and drop privileges
# Tini handles signal forwarding
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]

# Start the executor service (entrypoint will run this as sandbox user)
CMD []
