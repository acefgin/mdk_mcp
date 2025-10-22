#!/bin/bash
# Setup script for common MCP servers in Claude Code
# Usage: ./setup_mcp_servers.sh

set -e

COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}Claude Code MCP Server Setup${COLOR_RESET}"
echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
echo ""

# Check Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${COLOR_RED}✗ Node.js not found${COLOR_RESET}"
    echo "Please install Node.js v16 or higher"
    exit 1
fi

echo -e "${COLOR_GREEN}✓ Node.js $(node --version) found${COLOR_RESET}"

# Check npx is available
if ! command -v npx &> /dev/null; then
    echo -e "${COLOR_RED}✗ npx not found${COLOR_RESET}"
    exit 1
fi

echo -e "${COLOR_GREEN}✓ npx found${COLOR_RESET}"
echo ""

# Check if .mcp.json exists
if [ -f ".mcp.json" ]; then
    echo -e "${COLOR_YELLOW}⚠ .mcp.json already exists${COLOR_RESET}"
    read -p "Do you want to backup and create new? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .mcp.json .mcp.json.backup
        echo -e "${COLOR_GREEN}✓ Backed up to .mcp.json.backup${COLOR_RESET}"
    else
        echo "Exiting without changes"
        exit 0
    fi
fi

echo -e "${COLOR_BLUE}Creating .mcp.json configuration...${COLOR_RESET}"
echo ""

# Start building the configuration
cat > .mcp.json <<'EOF'
{
  "mcpServers": {
EOF

# Ask about Brave Search
echo -e "${COLOR_BLUE}=== Brave Search (Web Search) ===${COLOR_RESET}"
echo "Provides web search capabilities"
echo "Requires API key from: https://brave.com/search/api/"
read -p "Enable Brave Search? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter Brave API key: " BRAVE_KEY
    cat >> .mcp.json <<EOF
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "$BRAVE_KEY"
      }
    },
EOF
    echo -e "${COLOR_GREEN}✓ Brave Search configured${COLOR_RESET}"
fi
echo ""

# Ask about Fetch
echo -e "${COLOR_BLUE}=== Fetch (Web Content Retrieval) ===${COLOR_RESET}"
echo "Fetches and converts web pages to markdown"
echo "No API key required"
read -p "Enable Fetch? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat >> .mcp.json <<'EOF'
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    },
EOF
    echo -e "${COLOR_GREEN}✓ Fetch configured${COLOR_RESET}"
fi
echo ""

# Ask about GitHub
echo -e "${COLOR_BLUE}=== GitHub Integration ===${COLOR_RESET}"
echo "Repository management and code operations"
echo "Requires Personal Access Token from: https://github.com/settings/tokens"
read -p "Enable GitHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter GitHub token (ghp_...): " GITHUB_TOKEN
    cat >> .mcp.json <<EOF
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_TOKEN"
      }
    },
EOF
    echo -e "${COLOR_GREEN}✓ GitHub configured${COLOR_RESET}"
fi
echo ""

# Ask about Filesystem
echo -e "${COLOR_BLUE}=== Filesystem Access ===${COLOR_RESET}"
echo "Safe file operations in specified directories"
read -p "Enable Filesystem? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter directory paths (space-separated): " DIRS
    DIRS_ARRAY=($DIRS)
    DIRS_JSON=$(printf ',"%s"' "${DIRS_ARRAY[@]}")
    DIRS_JSON=${DIRS_JSON:1} # Remove leading comma

    cat >> .mcp.json <<EOF
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"$DIRS_JSON]
    },
EOF
    echo -e "${COLOR_GREEN}✓ Filesystem configured${COLOR_RESET}"
fi
echo ""

# Ask about project MCP servers
echo -e "${COLOR_BLUE}=== Project MCP Servers ===${COLOR_RESET}"
echo "Add this project's database and processing servers"
read -p "Enable project MCP servers? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    PROJECT_DIR=$(pwd)

    # Check if servers exist
    if [ -f "$PROJECT_DIR/mcp_servers/database_server/database_mcp_server.py" ]; then
        cat >> .mcp.json <<EOF
    "ndiag-database": {
      "command": "python3",
      "args": ["$PROJECT_DIR/mcp_servers/database_server/database_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "TEMP_DIR": "/tmp/mcp_cache"
      }
    },
EOF
        echo -e "${COLOR_GREEN}✓ Database server configured${COLOR_RESET}"
    fi

    if [ -f "$PROJECT_DIR/mcp_servers/processing_server/processing_mcp_server.py" ]; then
        cat >> .mcp.json <<EOF
    "ndiag-processing": {
      "command": "python3",
      "args": ["$PROJECT_DIR/mcp_servers/processing_server/processing_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "TEMP_DIR": "/tmp/mcp_processing"
      }
    },
EOF
        echo -e "${COLOR_GREEN}✓ Processing server configured${COLOR_RESET}"
    fi
fi
echo ""

# Remove trailing comma and close JSON
sed -i '$ s/,$//' .mcp.json
cat >> .mcp.json <<'EOF'
  }
}
EOF

echo ""
echo -e "${COLOR_GREEN}========================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}✓ MCP Configuration Complete!${COLOR_RESET}"
echo -e "${COLOR_GREEN}========================================${COLOR_RESET}"
echo ""
echo "Configuration saved to: .mcp.json"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code to load the configuration"
echo "  2. Type '/mcp' in Claude Code to verify servers are loaded"
echo "  3. Try using the servers in conversation"
echo ""
echo "Example usage:"
echo "  You: @brave-search Search for MCP documentation"
echo "  You: @fetch Fetch https://example.com"
echo "  You: @github List my repositories"
echo ""
echo "Documentation: docs/CLAUDE_CODE_MCP_SETUP.md"
echo ""
echo -e "${COLOR_BLUE}Security Note:${COLOR_RESET}"
echo "  Your .mcp.json contains API keys!"
echo "  Add to .gitignore to avoid committing secrets:"
echo "  echo '.mcp.json' >> .gitignore"
