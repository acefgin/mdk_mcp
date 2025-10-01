FROM python:3.11-slim

LABEL description="AutoGen qPCR Assistant - Multi-agent system for qPCR primer design"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY autogen_mcp_bridge.py .
COPY qpcr_assistant.py .

# Create results directory
RUN mkdir -p /results

# Expose Streamlit port (if using UI)
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_DATABASE_SERVER=ndiag-database-server

# Keep container running for interactive access via docker exec
# Don't auto-start the interactive mode - let user control via start_interactive.sh
CMD ["tail", "-f", "/dev/null"]
