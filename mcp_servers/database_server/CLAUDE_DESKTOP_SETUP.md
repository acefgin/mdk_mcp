# Claude Desktop Setup Guide

This guide explains how to use the ndiag-database-server MCP with Claude Desktop.

## Prerequisites

- Docker and Docker Compose installed
- Claude Desktop installed
- **No need to keep the container running** - Claude Desktop will start it on demand

## Step 1: Build the Docker Image

Build the Docker image so Claude Desktop can use it:

```bash
# Navigate to the database_server directory
cd /home/cxl/MDK_Design/mdk_mcp/mcp_servers/database_server

# Build the image
docker build -t ndiag-database-server:latest .
```

Verify the image exists:
```bash
docker images | grep ndiag-database-server
```

## Step 2: Configure Claude Desktop

### Windows/WSL2 Setup (Recommended)

Copy the contents of `claude_desktop_config.json` to your Claude Desktop configuration file.

**Location of Claude Desktop config file:**
- **Windows**: `C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

If you already have other MCP servers configured, **merge** the "ndiag-database-server" entry into your existing "mcpServers" object (don't replace the entire file).

### Basic Configuration (Windows/WSL2)

```json
{
  "mcpServers": {
    "ndiag-database-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--name",
        "ndiag-database-server-mcp",
        "-v",
        "\\\\wsl.localhost\\Ubuntu\\home\\cxl\\MDK_Design\\mdk_mcp\\mcp_servers\\database_server\\temp:/tmp/mcp_cache",
        "-e",
        "PYTHONUNBUFFERED=1",
        "-e",
        "MCP_SERVER_NAME=ndiag-database-server",
        "-e",
        "LOG_LEVEL=INFO",
        "ndiag-database-server:latest",
        "python",
        "database_mcp_server.py"
      ]
    }
  }
}
```

**Important Notes:**
- `docker run` starts a fresh container each time Claude Desktop needs it
- `--rm` automatically removes the container when it exits
- `-i` enables interactive mode for stdio communication
- The volume path uses Windows UNC format for WSL2: `\\wsl.localhost\Ubuntu\...`
- Update the WSL distribution name if you're not using Ubuntu

### Configuration with API Keys (Advanced)

To add API keys for enhanced database access:

```json
{
  "mcpServers": {
    "ndiag-database-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--name",
        "ndiag-database-server-mcp",
        "-v",
        "\\\\wsl.localhost\\Ubuntu\\home\\cxl\\MDK_Design\\mdk_mcp\\mcp_servers\\database_server\\temp:/tmp/mcp_cache",
        "-e",
        "PYTHONUNBUFFERED=1",
        "-e",
        "MCP_SERVER_NAME=ndiag-database-server",
        "-e",
        "LOG_LEVEL=INFO",
        "-e",
        "NCBI_API_KEY=your-ncbi-api-key-here",
        "-e",
        "MAX_RESULTS_LIMIT=10000",
        "ndiag-database-server:latest",
        "python",
        "database_mcp_server.py"
      ]
    }
  }
}
```

### Linux/macOS Native Setup

For Linux or macOS (not WSL), use standard paths:

```json
{
  "mcpServers": {
    "ndiag-database-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--name",
        "ndiag-database-server-mcp",
        "-v",
        "/absolute/path/to/mcp_servers/database_server/temp:/tmp/mcp_cache",
        "-e",
        "PYTHONUNBUFFERED=1",
        "-e",
        "MCP_SERVER_NAME=ndiag-database-server",
        "-e",
        "LOG_LEVEL=INFO",
        "ndiag-database-server:latest",
        "python",
        "database_mcp_server.py"
      ]
    }
  }
}
```

## Step 3: Restart Claude Desktop

After modifying the configuration:

1. **Quit Claude Desktop completely** (not just close the window)
2. **Restart Claude Desktop**

## Step 4: Verify the Connection

In Claude Desktop, you should now be able to use the database server tools:

- `get_sequences` - Retrieve sequences from NCBI, BOLD, SILVA, UNITE
- `gget_search` - Search Ensembl genes
- `gget_seq` - Get sequences from Ensembl
- `get_taxonomy` - Get taxonomic information
- `search_sra_studies` - Search SRA/BioProject data
- `extract_sequence_columns` - Extract specific columns from sequence data

## Troubleshooting

### Image not found
If Claude Desktop can't find the image:
```bash
# Check if the image exists
docker images | grep ndiag-database-server

# If missing, rebuild it
cd /home/cxl/MDK_Design/mdk_mcp/mcp_servers/database_server
docker build -t ndiag-database-server:latest .
```

### Volume path issues (Windows/WSL2)
If you get volume mount errors:
- Verify your WSL distribution name: `wsl -l -v`
- Update the path in config: `\\wsl.localhost\<YourDistro>\...`
- Or use Docker Desktop's WSL integration settings

### MCP server not responding
Test the Docker command manually:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
docker run --rm -i --name test-ndiag \
  -e PYTHONUNBUFFERED=1 \
  -e MCP_SERVER_NAME=ndiag-database-server \
  ndiag-database-server:latest python database_mcp_server.py
```

You should see a JSON response with server info.

### Permission issues
Ensure Docker is running and accessible:
```bash
docker info
docker ps
```

### Container name conflict
If you get "name already in use":
```bash
# Remove any stuck container
docker rm -f ndiag-database-server-mcp
```

## Available Tools

Once configured, you can ask Claude to:

1. **Search for sequences**: "Get COI sequences for Salmo salar from NCBI"
2. **Search genes**: "Search for cytochrome oxidase genes in human using Ensembl"
3. **Get taxonomy**: "Get the taxonomic classification for Escherichia coli"
4. **Search SRA**: "Find amplicon sequencing studies for malaria parasites"
5. **Extract data**: "Extract the accession numbers and organism names from these sequences"

## Container Management

### View running MCP containers
```bash
docker ps | grep ndiag-database-server-mcp
```

### View logs from a running session
Since containers are ephemeral (--rm flag), logs are only available while running. You can test manually to see logs:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
docker run --rm -i --name test-logs \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=DEBUG \
  ndiag-database-server:latest python database_mcp_server.py
```

### Rebuild after code updates
```bash
cd /home/cxl/MDK_Design/mdk_mcp/mcp_servers/database_server
docker build -t ndiag-database-server:latest .
```

After rebuilding, restart Claude Desktop to use the new image.

### Remove old/unused images
```bash
docker images | grep ndiag-database-server
docker rmi <old-image-id>
```

## Notes

- The MCP server uses **stdio transport** (standard input/output) for communication
- Claude Desktop **starts a fresh container** each time it needs the server
- The `--rm` flag automatically removes the container when the session ends
- The `-i` flag enables interactive mode for stdio communication
- **No need to keep containers running** - they're started on demand
- Changes to the code require rebuilding the Docker image
- API keys can be added as `-e` environment variables in the config

