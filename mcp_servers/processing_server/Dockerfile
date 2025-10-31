FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install seqkit
RUN wget -O /tmp/seqkit.tar.gz \
    https://github.com/shenwei356/seqkit/releases/download/v2.6.1/seqkit_linux_amd64.tar.gz \
    && tar -xzf /tmp/seqkit.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/seqkit \
    && rm /tmp/seqkit.tar.gz

# Install vsearch
RUN wget -O /tmp/vsearch.tar.gz \
    https://github.com/torognes/vsearch/releases/download/v2.25.0/vsearch-2.25.0-linux-x86_64.tar.gz \
    && tar -xzf /tmp/vsearch.tar.gz -C /tmp/ \
    && cp /tmp/vsearch-2.25.0-linux-x86_64/bin/vsearch /usr/local/bin/ \
    && chmod +x /usr/local/bin/vsearch \
    && rm -rf /tmp/vsearch*

# Verify installations
RUN seqkit version && vsearch --version

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY processing_mcp_server.py /app/
COPY config.py /app/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user and directories
RUN useradd -m -u 1000 mcp
RUN mkdir -p /tmp/mcp_processing /results/sequences

# Expose port (if needed for HTTP transport in future)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD seqkit version || exit 1

# Use entrypoint script to handle permissions and privilege dropping
ENTRYPOINT ["/entrypoint.sh"]

# Default: keep container running for docker exec
CMD ["tail", "-f", "/dev/null"]
