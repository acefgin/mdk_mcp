# MCP Server Testing Guide

This guide explains how to test the Neglected Diagnostics MCP servers using the MCP Inspector tool.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MCP Inspector Overview](#mcp-inspector-overview)
3. [Testing Methods](#testing-methods)
4. [Testing Database Server](#testing-database-server)
5. [Testing Processing Server](#testing-processing-server)
6. [CLI Testing](#cli-testing)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

---

## Prerequisites

### Required Software

1. **Node.js** (v22.7.5 or higher)
   ```bash
   node --version  # Should be v22.7.5+
   ```

2. **Docker** (for running MCP servers)
   ```bash
   docker --version
   ```

3. **Python 3.11+** (for Python-based MCP servers)
   ```bash
   python3 --version
   ```

### Installation Check

```bash
# Verify npx is available
npx --version

# MCP Inspector will be installed automatically when you run it
npx @modelcontextprotocol/inspector --help
```

---

## MCP Inspector Overview

**MCP Inspector** is an official tool for testing and debugging Model Context Protocol servers.

### Key Features

- 🔍 **Interactive UI** - Visual interface for exploring tools, resources, and prompts
- 🖥️ **CLI Mode** - Command-line testing for automation
- 🔄 **Live Testing** - Test tools with real-time feedback
- 📊 **Request/Response Logging** - See detailed server communication
- 🐛 **Debug Mode** - Monitor server logs and errors

### Two Modes

1. **UI Mode** (Interactive)
   - Web-based interface at http://localhost:6274
   - Best for manual testing and exploration
   - Visualize server capabilities

2. **CLI Mode** (Automated)
   - Command-line tool invocation
   - Best for scripting and CI/CD
   - Quick verification of specific tools

---

## Testing Methods

### Method 1: Testing via Docker Container (Recommended)

This method tests the containerized MCP server as it will run in production.

**Steps:**

1. **Start the MCP server container**
   ```bash
   cd mcp_servers/database_server
   docker-compose up --build -d
   ```

2. **Attach to the container with MCP Inspector**
   ```bash
   # Connect to the running container's stdio
   docker exec -i ndiag-database-server python3 /app/database_mcp_server.py
   ```

3. **Use Inspector with Docker exec**
   ```bash
   # This is more complex - see Method 2 for easier testing
   ```

### Method 2: Testing Local Python Server (Easier for Development)

Test the server directly without Docker for faster iteration.

**Steps:**

1. **Install dependencies locally**
   ```bash
   cd mcp_servers/database_server
   pip install -r requirements.txt
   ```

2. **Launch MCP Inspector with local server**
   ```bash
   # UI Mode - Interactive testing
   npx @modelcontextprotocol/inspector python3 database_mcp_server.py

   # This will:
   # 1. Start your MCP server
   # 2. Launch Inspector UI at http://localhost:6274
   # 3. Connect them together
   ```

3. **Open your browser**
   - Navigate to http://localhost:6274
   - You should see the Inspector UI with your server connected

### Method 3: Testing with uvx (Python Package)

If your server is packaged as a Python package:

```bash
npx @modelcontextprotocol/inspector uvx your-mcp-package
```

---

## Testing Database Server

### Setup

```bash
cd mcp_servers/database_server

# Option 1: Install dependencies locally
pip install -r requirements.txt

# Option 2: Build Docker image
docker build -t ndiag-database-server:latest .
```

### Launch Inspector (Local Mode)

```bash
# Start Inspector with database server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py
```

### Using the Inspector UI

1. **Open Browser**: Navigate to http://localhost:6274

2. **Verify Connection**: Check that the server name "ndiag-database-server" appears

3. **Explore Tools Tab**:
   - You should see 11 tools listed:
     - get_sequences
     - gget_ref
     - gget_search
     - gget_info
     - gget_seq
     - get_neighbors
     - get_taxonomy
     - search_sra_studies
     - get_sra_runinfo
     - search_sra_cloud
     - extract_sequence_columns

### Example: Testing `get_sequences` Tool

1. **Select Tool**: Click on "get_sequences" in the Tools tab

2. **Fill Parameters**:
   ```json
   {
     "taxon": "Salmo salar",
     "region": "COI",
     "source": "ncbi",
     "max_results": 5,
     "format": "fasta"
   }
   ```

3. **Execute**: Click "Run Tool"

4. **View Results**: Check the response pane for FASTA sequences

**Expected Output**:
```
>NC_001960.1 Salmo salar mitochondrion, complete genome
ATGCGATCGATCG...
>AF154850.1 Salmo salar cytochrome oxidase subunit I
GCTAGCTAGCTAG...
...
```

### Example: Testing `extract_sequence_columns` Tool

1. **Select Tool**: Click on "extract_sequence_columns"

2. **Fill Parameters**:
   ```json
   {
     "sequence_data": ">seq1|ACC123|Salmo salar\nATGC\n>seq2|ACC456|Oncorhynchus\nGCTA",
     "columns": ["Id", "Accession", "Organism"],
     "output_format": "json"
   }
   ```

3. **Execute**: Click "Run Tool"

4. **View Results**: Check JSON output with extracted metadata

### CLI Testing - Database Server

```bash
# Test getting sequences (CLI mode)
npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name get_sequences \
  python3 database_mcp_server.py <<EOF
{
  "taxon": "Homo sapiens",
  "region": "whole",
  "source": "gget",
  "max_results": 3
}
EOF
```

---

## Testing Processing Server

### Setup

```bash
cd mcp_servers/processing_server

# Install Python dependencies
pip install -r requirements.txt

# System dependencies (seqkit and vsearch)
# These need to be installed on your system or use Docker
```

### Launch Inspector (Docker Mode Recommended)

Since the processing server requires seqkit and vsearch, Docker is easier:

```bash
# Build the container
docker-compose up --build -d

# For local testing, ensure seqkit and vsearch are installed:
# - seqkit: https://github.com/shenwei356/seqkit/releases
# - vsearch: https://github.com/torognes/vsearch/releases
```

### Launch Inspector (Local Mode - if tools installed)

```bash
npx @modelcontextprotocol/inspector python3 processing_mcp_server.py
```

### Using the Inspector UI

1. **Open Browser**: http://localhost:6274

2. **Verify Connection**: Check "ndiag-processing-server" appears

3. **Explore Tools Tab**:
   - fasta_qc
   - dereplicate_sequences
   - mask_low_complexity
   - detect_chimeras
   - process_sequences

### Example: Testing `fasta_qc` Tool

1. **Select Tool**: Click on "fasta_qc"

2. **Fill Parameters**:
   ```json
   {
     "fasta_content": ">seq1 test sequence 1\nATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC\n>seq2 test sequence 2\nGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA\n>seq3 short sequence\nATGC\n>seq4 sequence with Ns\nATGCNNNNNNNNATGC",
     "min_length": 20,
     "max_n_percent": 5.0,
     "remove_duplicates": true
   }
   ```

3. **Execute**: Click "Run Tool"

4. **View Results**:
   ```json
   {
     "cleaned_fasta": ">seq1...\n>seq2...",
     "stats": {
       "input_sequences": 4,
       "output_sequences": 2,
       "filtered_by_length": 1,
       "filtered_by_n_content": 1
     }
   }
   ```

### Example: Testing `process_sequences` Pipeline

1. **Select Tool**: Click on "process_sequences"

2. **Fill Parameters**:
   ```json
   {
     "fasta_content": ">seq1\nATGCATGCATGCATGCATGCATGCATGC\n>seq2\nATGCATGCATGCATGCATGCATGCATGC\n>seq3\nGCTAGCTAGCTAGCTAGCTAGCTAGCTA\n>seq4\nAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
     "pipeline": ["qc", "dereplicate", "mask"],
     "qc_params": {
       "min_length": 20,
       "remove_duplicates": true
     },
     "derep_params": {
       "identity_threshold": 0.97
     }
   }
   ```

3. **Execute**: Click "Run Tool"

4. **View Results**: Check the processed FASTA and statistics for each step

---

## CLI Testing

### Basic CLI Tool Testing

Test a tool without the UI:

```bash
# Syntax
npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name <tool_name> \
  python3 <server_script.py> <<EOF
{
  "param1": "value1",
  "param2": "value2"
}
EOF
```

### List Available Tools

```bash
# Database Server
npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 mcp_servers/database_server/database_mcp_server.py

# Processing Server
npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 mcp_servers/processing_server/processing_mcp_server.py
```

### Example: CLI Test Database Server

```bash
cd mcp_servers/database_server

# Test get_taxonomy tool
npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name get_taxonomy \
  python3 database_mcp_server.py <<EOF
{
  "query": "Salmo salar"
}
EOF
```

### Example: CLI Test Processing Server

```bash
cd mcp_servers/processing_server

# Test fasta_qc tool
npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name fasta_qc \
  python3 processing_mcp_server.py <<EOF
{
  "fasta_content": ">seq1\nATGCATGCATGCATGCATGC\n>seq2\nGCTA",
  "min_length": 10,
  "max_n_percent": 5.0
}
EOF
```

---

## Troubleshooting

### Issue: "Cannot find module '@modelcontextprotocol/inspector'"

**Solution**:
```bash
# Update npm
npm install -g npm@latest

# Try running with -y flag
npx -y @modelcontextprotocol/inspector --help
```

### Issue: "Server connection failed"

**Possible causes**:

1. **Python dependencies missing**
   ```bash
   pip install -r requirements.txt
   ```

2. **Server script has syntax errors**
   ```bash
   python3 -m py_compile server_script.py
   ```

3. **Environment variables not set**
   ```bash
   # Check config.py for required variables
   export LOG_LEVEL=INFO
   export TEMP_DIR=/tmp/mcp_cache
   ```

### Issue: "Tool execution failed"

**Debug steps**:

1. **Check server logs**:
   ```bash
   # Run server with debug logging
   LOG_LEVEL=DEBUG python3 database_mcp_server.py
   ```

2. **Verify tool parameters**:
   - Check that all required parameters are provided
   - Check parameter types (string, number, boolean, array)

3. **Test dependencies**:
   ```bash
   # Database server
   python3 -c "import gget; import Bio; print('Dependencies OK')"

   # Processing server
   seqkit version
   vsearch --version
   python3 -c "import Bio; print('BioPython OK')"
   ```

### Issue: "Port 6274 already in use"

**Solution**:
```bash
# Find and kill the process using the port
lsof -ti:6274 | xargs kill -9

# Or specify a different port (if supported)
PORT=6275 npx @modelcontextprotocol/inspector python3 server.py
```

### Issue: "seqkit/vsearch not found" (Processing Server)

**Solution**:

Option 1 - Use Docker (recommended):
```bash
cd mcp_servers/processing_server
docker-compose up --build
```

Option 2 - Install tools locally:
```bash
# Install seqkit
wget https://github.com/shenwei356/seqkit/releases/download/v2.6.1/seqkit_linux_amd64.tar.gz
tar -xzf seqkit_linux_amd64.tar.gz
sudo mv seqkit /usr/local/bin/

# Install vsearch
wget https://github.com/torognes/vsearch/releases/download/v2.25.0/vsearch-2.25.0-linux-x86_64.tar.gz
tar -xzf vsearch-2.25.0-linux-x86_64.tar.gz
sudo cp vsearch-2.25.0-linux-x86_64/bin/vsearch /usr/local/bin/

# Verify installations
seqkit version
vsearch --version
```

### Issue: "NCBI API rate limit exceeded"

**Solution**:
```bash
# Get a free API key from NCBI
# https://www.ncbi.nlm.nih.gov/account/settings/

# Set the environment variable
export NCBI_API_KEY="your_api_key_here"

# Or add to .env file
echo "NCBI_API_KEY=your_api_key_here" >> mcp_servers/database_server/.env
```

---

## Advanced Usage

### Testing with Docker Compose

If you have multiple MCP servers running:

```bash
# Start all servers
docker-compose -f docker-compose.yml up -d

# Test database server via docker exec
docker exec -i ndiag-database-server python3 /app/database_mcp_server.py

# Test processing server via docker exec
docker exec -i ndiag-processing-server python3 /app/processing_mcp_server.py
```

### Custom Configuration for Testing

Create a test-specific configuration:

```bash
# Database server test config
cat > test_config.env <<EOF
LOG_LEVEL=DEBUG
MAX_RESULTS_DEFAULT=5
TEMP_DIR=/tmp/test_cache
EOF

# Run with test config
env $(cat test_config.env) npx @modelcontextprotocol/inspector python3 database_mcp_server.py
```

### Automated Testing Script

Create a script for CI/CD:

```bash
#!/bin/bash
# test_mcp_servers.sh

set -e

echo "Testing Database Server..."
cd mcp_servers/database_server
pip install -r requirements.txt

npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 database_mcp_server.py > /tmp/db_tools.json

# Check if expected tools are present
if grep -q "get_sequences" /tmp/db_tools.json; then
    echo "✓ Database server tools OK"
else
    echo "✗ Database server tools missing"
    exit 1
fi

echo "Testing Processing Server..."
cd ../processing_server
pip install -r requirements.txt

# Check if external tools are available
if ! command -v seqkit &> /dev/null; then
    echo "✗ seqkit not found - install or use Docker"
    exit 1
fi

if ! command -v vsearch &> /dev/null; then
    echo "✗ vsearch not found - install or use Docker"
    exit 1
fi

npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 processing_mcp_server.py > /tmp/proc_tools.json

if grep -q "fasta_qc" /tmp/proc_tools.json; then
    echo "✓ Processing server tools OK"
else
    echo "✗ Processing server tools missing"
    exit 1
fi

echo "✅ All MCP servers tested successfully!"
```

### Integration Testing Workflow

Test the complete pipeline:

```bash
# 1. Start database server
cd mcp_servers/database_server
docker-compose up -d

# 2. Get sequences (database server)
SEQUENCES=$(npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name get_sequences \
  python3 database_mcp_server.py <<EOF
{
  "taxon": "Salmo salar",
  "region": "COI",
  "max_results": 10
}
EOF
)

# 3. Process sequences (processing server)
cd ../processing_server
docker-compose up -d

npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name fasta_qc \
  python3 processing_mcp_server.py <<EOF
{
  "fasta_content": "$SEQUENCES",
  "min_length": 100
}
EOF
```

---

## Best Practices

### 1. Start Simple
- Test with small datasets first
- Use 5-10 sequences for initial tests
- Verify basic functionality before scaling

### 2. Use UI for Exploration
- UI mode is great for understanding tool parameters
- See what's possible with each tool
- Experiment with different parameter combinations

### 3. Use CLI for Automation
- CLI mode for regression testing
- Integrate into CI/CD pipelines
- Script repetitive test scenarios

### 4. Monitor Logs
- Always check server logs during testing
- Set `LOG_LEVEL=DEBUG` for detailed information
- Look for warnings about rate limits or missing data

### 5. Test Error Handling
- Try invalid parameters
- Test with missing required fields
- Verify error messages are helpful

### 6. Performance Testing
- Test with realistic dataset sizes
- Monitor memory usage
- Check processing times

---

## Quick Reference

### Start Inspector (UI Mode)
```bash
npx @modelcontextprotocol/inspector python3 <server_script.py>
# Then open http://localhost:6274
```

### List Tools (CLI Mode)
```bash
npx @modelcontextprotocol/inspector \
  --method tools/list \
  python3 <server_script.py>
```

### Call Tool (CLI Mode)
```bash
npx @modelcontextprotocol/inspector \
  --method tools/call \
  --tool-name <tool_name> \
  python3 <server_script.py> <<EOF
{
  "param": "value"
}
EOF
```

### Check Server Health
```bash
# Run server directly to see if it starts
python3 <server_script.py>
# Should see: "Starting <Server Name> MCP Server"
```

---

## Resources

- **MCP Inspector GitHub**: https://github.com/modelcontextprotocol/inspector
- **MCP Documentation**: https://modelcontextprotocol.io
- **Project Documentation**: See `docs/` directory
- **Database Server README**: `mcp_servers/database_server/README.md`
- **Processing Server README**: `mcp_servers/processing_server/README.md`

---

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review server-specific README files
3. Check server logs with `LOG_LEVEL=DEBUG`
4. Verify all dependencies are installed
5. Open an issue on the project repository

Happy Testing! 🧪
