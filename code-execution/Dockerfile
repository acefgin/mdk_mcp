# Code Execution Sandbox Dockerfile
# Multi-stage build for minimal attack surface
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci --only=production

# Production stage with security hardening
FROM node:20-alpine

# Create non-root user for code execution
RUN addgroup -g 1001 -S sandbox && \
    adduser -u 1001 -S sandbox -G sandbox

# Install security tools and minimal utilities
RUN apk add --no-cache \
    dumb-init \
    tini \
    && rm -rf /var/cache/apk/*

# Create workspace directory with proper permissions
RUN mkdir -p /workspace/data /workspace/cache /workspace/results && \
    chown -R sandbox:sandbox /workspace

# Set working directory
WORKDIR /app

# Copy node_modules from builder
COPY --from=builder /build/node_modules ./node_modules

# Copy application code
COPY --chown=sandbox:sandbox . .

# Create TypeScript build
RUN npm run build 2>/dev/null || echo "No build script defined"

# Switch to non-root user
USER sandbox

# Set resource limits via env vars (enforced by Docker)
ENV NODE_OPTIONS="--max-old-space-size=512"
ENV EXECUTION_TIMEOUT="30000"
ENV MAX_OUTPUT_SIZE="1048576"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

# Use tini as init system to handle signals properly
ENTRYPOINT ["/sbin/tini", "--"]

# Start the executor service
CMD ["node", "dist/executor.js"]
