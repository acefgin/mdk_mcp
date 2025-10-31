FROM python:3.11-slim

# Add MCP server metadata labels for Docker MCP Toolkit
LABEL mcp.server.name="ndiag-database-server" \
      mcp.server.version="1.0.0" \
      mcp.server.description="Database MCP Server for biological databases (NCBI, BOLD, SILVA, UNITE, SRA)" \
      mcp.server.author="neglected-diagnostics team" \
      mcp.server.capabilities="tools,logging" \
      mcp.server.protocol="stdio" \
      mcp.server.manifest="/app/mcp-server.json"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install EDirect tools for NCBI (as root, will be accessible to all users)
RUN curl -s https://ftp.ncbi.nlm.nih.gov/entrez/entrezdirect/install-edirect.sh | bash
ENV PATH="/root/edirect:${PATH}"

# Create non-root user
RUN useradd -m -u 1000 mcp

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server code and manifest
COPY database_mcp_server.py .
COPY config.py .
COPY mcp-server.json .

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create directory for temporary files
RUN mkdir -p /tmp/mcp_cache /results/sequences

# Set environment variables
ENV PYTHONPATH="/app"
ENV MCP_SERVER_NAME="ndiag-database-server"
ENV MCP_SERVER_VERSION="1.0.0"
ENV TEMP_DIR="/tmp/mcp_cache"
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8000

# Use entrypoint script to handle permissions and privilege dropping
ENTRYPOINT ["/entrypoint.sh"]

# Default: keep container running for docker exec
CMD ["tail", "-f", "/dev/null"]
