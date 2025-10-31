FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and alignment tools
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    mafft \
    clustalo \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install MUSCLE v5
RUN wget -O /usr/local/bin/muscle \
    https://github.com/rcedgar/muscle/releases/download/5.1.0/muscle5.1.linux_intel64 \
    && chmod +x /usr/local/bin/muscle

# Verify installations
RUN mafft --version && \
    clustalo --version && \
    muscle -version

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY alignment_mcp_server.py /app/
COPY config.py /app/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user and directories
RUN useradd -m -u 1000 mcp
RUN mkdir -p /tmp/mcp_alignment /results/sequences

# Expose port (if needed for HTTP transport in future)
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD mafft --version || exit 1

# Use entrypoint script to handle permissions and privilege dropping
ENTRYPOINT ["/entrypoint.sh"]

# Default: keep container running for docker exec
CMD ["tail", "-f", "/dev/null"]
