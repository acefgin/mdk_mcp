# Claude Code MCP Server Setup Guide

This guide explains how to enable MCP (Model Context Protocol) servers for Claude Code, including popular servers like web search, GitHub integration, and more.

## 🎯 What are MCP Servers?

MCP servers give Claude Code secure, controlled access to external tools and data sources through the Model Context Protocol. They enable capabilities like:
- 🌐 **Web Search** - Search and fetch web content
- 🐙 **GitHub Integration** - Repository management and code reviews
- 📁 **File System Access** - Safe file operations
- 🗄️ **Database Queries** - Connect to PostgreSQL, MySQL, etc.
- 🔧 **Custom Tools** - Your own MCP servers

## 📍 Configuration Scopes

MCP servers can be configured at three levels:

### 1. **User Scope** (Recommended for personal tools)
- Available across all projects
- Private to your account
- Good for personal utility servers
- Configure via: `claude mcp add ...`

### 2. **Project Scope**
- Shared with team via `.mcp.json` in project root
- Checked into version control
- Requires user approval before use
- Team can collaborate with same tools

### 3. **Local Scope**
- Private to current project
- Not shared with team
- Default configuration

---

## 🚀 Quick Setup

### Using CLI (Easiest)

```bash
# Add a server with CLI
claude mcp add --transport <type> <name> <command/url>

# Examples below
```

### Using JSON Configuration

Create or edit `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "API_KEY": "your-key-here"
      }
    }
  }
}
```

---

## 🌐 Setting Up Web Search (Brave Search)

**Required**: Brave Search API key from https://brave.com/search/api/

### Option 1: CLI Setup
```bash
# Add Brave Search server
claude mcp add --transport stdio brave-search \
  --env BRAVE_API_KEY=your_api_key_here \
  -- npx -y @modelcontextprotocol/server-brave-search
```

### Option 2: JSON Configuration

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Usage in Claude Code
```
You: Search for "MCP protocol documentation"
Claude: [Uses Brave Search to find relevant results]
```

---

## 📄 Setting Up Web Fetch (URL Content)

Fetch and convert web pages to markdown.

### Option 1: CLI Setup
```bash
# Add Fetch server (using uvx)
claude mcp add --transport stdio fetch -- uvx mcp-server-fetch

# Or using npx
claude mcp add --transport stdio fetch -- npx -y @modelcontextprotocol/server-fetch
```

### Option 2: JSON Configuration

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

**Alternative with npx**:
```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### Usage
```
You: Fetch content from https://example.com/article
Claude: [Retrieves and converts the page to markdown]
```

---

## 🐙 Setting Up GitHub Integration

**Required**: GitHub Personal Access Token

### Get GitHub Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" (classic)
3. Select scopes:
   - `repo` - Full repository access
   - `read:org` - Read organization data
   - `user` - Read user data
4. Copy the token

### Option 1: CLI Setup
```bash
# Add GitHub server
claude mcp add --transport stdio github \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here \
  -- npx -y @modelcontextprotocol/server-github
```

### Option 2: JSON Configuration

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

### Usage
```
You: Check open pull requests in my repository
Claude: [Lists PRs from your GitHub repositories]

You: Create an issue in repo-name about bug XYZ
Claude: [Creates issue on GitHub]
```

---

## 📁 Setting Up File System Access

Safe file operations within specified directories.

### CLI Setup
```bash
# Allow access to specific directories
claude mcp add --transport stdio filesystem \
  -- npx -y @modelcontextprotocol/server-filesystem /path/to/directory
```

### JSON Configuration

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/user/projects",
        "/home/user/documents"
      ]
    }
  }
}
```

---

## 🔧 Setting Up Git Repository Access

Read, search, and manipulate Git repositories.

### JSON Configuration

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "/path/to/repo"]
    }
  }
}
```

**Multiple repositories**:
```json
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": [
        "mcp-server-git",
        "--repository", "/path/to/repo1",
        "--repository", "/path/to/repo2"
      ]
    }
  }
}
```

---

## 🗄️ Setting Up Database Access (PostgreSQL)

### Required: PostgreSQL connection string

### JSON Configuration

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/dbname"
      }
    }
  }
}
```

---

## 🏢 Setting Up Your Own MCP Servers

### Example: Database Server (from this project)

```json
{
  "mcpServers": {
    "ndiag-database": {
      "command": "python3",
      "args": ["/home/raycifeng/mdk_mcp/mcp_servers/database_server/database_mcp_server.py"],
      "env": {
        "NCBI_API_KEY": "your_ncbi_key",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Example: Processing Server (from this project)

```json
{
  "mcpServers": {
    "ndiag-processing": {
      "command": "python3",
      "args": ["/home/raycifeng/mdk_mcp/mcp_servers/processing_server/processing_mcp_server.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "TEMP_DIR": "/tmp/mcp_processing"
      }
    }
  }
}
```

---

## 📝 Complete Example Configuration

Here's a `.mcp.json` with multiple servers:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "YOUR_BRAVE_API_KEY"
      }
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_GITHUB_TOKEN"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${HOME}/projects"
      ]
    },
    "git": {
      "command": "uvx",
      "args": [
        "mcp-server-git",
        "--repository", "${HOME}/projects/repo1",
        "--repository", "${HOME}/projects/repo2"
      ]
    }
  }
}
```

**Note**: Environment variables like `${HOME}` are automatically expanded.

---

## 🔐 Security Best Practices

### 1. **API Keys in Environment Variables**

Don't commit API keys to version control. Use environment variables:

**Set in your shell**:
```bash
export BRAVE_API_KEY="your_key"
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_your_token"
```

**Reference in `.mcp.json`**:
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  }
}
```

### 2. **Use `.gitignore` for Sensitive Configs**

If your `.mcp.json` contains secrets, add to `.gitignore`:
```
.mcp.json
.mcp.local.json
```

### 3. **Project vs User Scope**

- **User scope**: For personal API keys
- **Project scope**: For team-shared configurations (without secrets)

---

## 🧪 Testing Your MCP Servers

### 1. **Check Server Status**

In Claude Code, type:
```
/mcp
```

This shows all configured MCP servers and their status.

### 2. **Test a Server**

Try using it in conversation:
```
You: @fetch-server Fetch content from https://example.com
Claude: [Should fetch and display content]
```

### 3. **Debug Connection Issues**

Check logs:
```bash
# Linux
tail -f ~/.config/ClaudeCode/logs/mcp-*.log

# Check if command works standalone
npx -y @modelcontextprotocol/server-fetch
```

---

## 📚 Available Official MCP Servers

| Server | Purpose | Package | API Key Required |
|--------|---------|---------|------------------|
| **Brave Search** | Web search | `@modelcontextprotocol/server-brave-search` | ✅ Yes |
| **Fetch** | Web content | `@modelcontextprotocol/server-fetch` | ❌ No |
| **GitHub** | Repository mgmt | `@modelcontextprotocol/server-github` | ✅ Yes |
| **Filesystem** | File operations | `@modelcontextprotocol/server-filesystem` | ❌ No |
| **Git** | Git repos | `mcp-server-git` | ❌ No |
| **PostgreSQL** | Database | `@modelcontextprotocol/server-postgres` | ✅ Yes (connection) |
| **Google Maps** | Maps data | `@modelcontextprotocol/server-googlemaps` | ✅ Yes |
| **Slack** | Slack integration | `@modelcontextprotocol/server-slack` | ✅ Yes |

See https://github.com/modelcontextprotocol/servers for complete list.

---

## 🔧 Troubleshooting

### "Server failed to start"

**Check**:
1. Command is correct: `npx -y @modelcontextprotocol/server-name`
2. Node.js is installed: `node --version`
3. Python is installed (for Python servers): `python3 --version`

**Try running manually**:
```bash
npx -y @modelcontextprotocol/server-fetch
# Should start without errors
```

### "Authentication failed"

**Check**:
1. API key is correct
2. API key has required permissions
3. Environment variable is set correctly

**Test API key**:
```bash
# Test Brave API
curl -H "X-Subscription-Token: YOUR_KEY" \
  "https://api.search.brave.com/res/v1/web/search?q=test"

# Test GitHub token
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user
```

### "Server not found"

**Check**:
1. `.mcp.json` is in correct location (project root)
2. JSON syntax is valid: `cat .mcp.json | python -m json.tool`
3. Claude Code has been restarted

### "Permission denied"

**Check**:
1. File paths are accessible
2. Python scripts are executable: `chmod +x script.py`
3. Directories exist: `mkdir -p /tmp/mcp_cache`

---

## 📖 Additional Resources

- **MCP Documentation**: https://modelcontextprotocol.io
- **MCP Servers Repository**: https://github.com/modelcontextprotocol/servers
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code/mcp.md
- **Your Project MCP Servers**:
  - Database Server: `mcp_servers/database_server/README.md`
  - Processing Server: `mcp_servers/processing_server/README.md`

---

## 🎯 Quick Start Checklist

- [ ] Create `.mcp.json` in your project root
- [ ] Add Brave Search with API key for web search
- [ ] Add Fetch server for web content
- [ ] Add GitHub integration with token
- [ ] Add your custom MCP servers
- [ ] Test with `/mcp` command in Claude Code
- [ ] Try using servers in conversation

**Pro Tip**: Start with just Fetch server (no API key required) to test the setup works!

---

**Happy MCP Configuration! 🚀**
