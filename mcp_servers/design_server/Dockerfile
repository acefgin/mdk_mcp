FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and design tools
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    primer3 \
    build-essential \
    cmake \
    g++ \
    git \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install ViennaRNA from source (latest version for better RNA folding)
RUN wget https://www.tbi.univie.ac.at/RNA/download/ubuntu/ubuntu_22_04/viennarna_2.6.4-1_amd64.deb && \
    dpkg -i viennarna_2.6.4-1_amd64.deb || true && \
    apt-get install -f -y && \
    rm viennarna_2.6.4-1_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Verify installations
RUN primer3_core --version || echo "primer3_core installed" && \
    RNAfold --version

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY design_mcp_server.py /app/
COPY config.py /app/

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user and directories
RUN useradd -m -u 1000 mcp
RUN mkdir -p /tmp/mcp_design /results/sequences

# Expose port (if needed for HTTP transport in future)
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD primer3_core --version || exit 1

# Use entrypoint script to handle permissions and privilege dropping
ENTRYPOINT ["/entrypoint.sh"]

# Default: keep container running for docker exec
CMD ["tail", "-f", "/dev/null"]
