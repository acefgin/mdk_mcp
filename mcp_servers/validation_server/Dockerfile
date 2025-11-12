FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and BLAST+
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    ncbi-blast+ \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Verify BLAST installation
RUN which blastn && blastn -version

# Set up NCBI BLAST+ recommended directory structure
# See: https://github.com/ncbi/blast_plus_docs
ENV BLASTDB=/blastdb
ENV BLASTDB_CUSTOM=/blastdb_custom

RUN mkdir -p $BLASTDB \
    $BLASTDB_CUSTOM \
    /queries \
    /fasta \
    /results/validation \
    /tmp/mcp_validation/blast_cache

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY validation_mcp_server.py /app/
COPY config.py /app/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 mcp

# Set proper ownership for BLAST directories
RUN chown -R mcp:mcp \
    $BLASTDB \
    $BLASTDB_CUSTOM \
    /queries \
    /fasta \
    /results \
    /tmp/mcp_validation

# Expose port (if needed for HTTP transport in future)
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD blastn -version || exit 1

# Use entrypoint script to handle permissions and privilege dropping
ENTRYPOINT ["/entrypoint.sh"]

# Default: keep container running for docker exec
CMD ["tail", "-f", "/dev/null"]
