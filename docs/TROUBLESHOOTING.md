# Troubleshooting Guide

This guide helps resolve common issues when working with the mdk_mcp system.

## 🔧 Common Issues

### Container Won't Start

**Symptoms:**
- Container exits immediately
- No logs appear
- Can't attach to container

**Solutions:**

```bash
# Check container status
docker ps -a | grep qpcr-assistant

# Check logs for errors
docker logs qpcr-assistant --tail 50

# Verify API key is set
cat autogen_app/.env | grep API_KEY

# Check for environment variable issues
docker logs qpcr-assistant 2>&1 | grep -i "api key"

# Rebuild from scratch
docker compose -f docker-compose.autogen.yml down
docker compose -f docker-compose.autogen.yml build --no-cache
docker compose -f docker-compose.autogen.yml up -d
```

### No Tool Calls Made

**Symptoms:**
- Agents respond but don't call MCP tools
- No "ToolCall" messages in logs
- Results are generic/fabricated

**Solutions:**

```bash
# Verify MCP server connection
docker logs qpcr-assistant 2>&1 | grep "MCP servers connected"

# Check for tool call attempts
docker logs qpcr-assistant 2>&1 | grep "ToolCall"

# Verify function schemas loaded
docker logs qpcr-assistant 2>&1 | grep "function schemas"

# Test database server directly
docker logs ndiag-database-server --tail 20

# Test processing server directly
docker logs ndiag-processing-server --tail 20

# Check MCP bridge initialization
docker logs qpcr-assistant 2>&1 | grep "MCPClientBridge"
```

**Common Causes:**
1. **Wrong model**: Ensure using gpt-4o or gemini-2.5-flash-lite (not gpt-3.5-turbo)
2. **API key issues**: Verify API keys are valid and have proper permissions
3. **MCP servers not running**: Check `docker ps` shows both servers
4. **Function map mismatch**: Ensure function schemas match registered handlers

### Workflow Fails with Token Limit Error

**Error Message:**
```
RateLimitError: Requested 73859 tokens, Limit 10000
```

**Solutions:**

1. **Switch to Gemini** (Recommended):
```bash
# Add to autogen_app/.env
GOOGLE_API_KEY=your-google-api-key
```

2. **Reduce sequence count:**
```
# Instead of:
Get 500 COI sequences...

# Use:
Get 50 COI sequences...
```

3. **Check model configuration:**
```bash
# Verify using Gemini or GPT-4
cat autogen_app/OAI_CONFIG_LIST.json
```

### Can't Attach to Container

**Symptoms:**
- `docker attach` returns "No such container"
- Container shows as "Exited"

**Solutions:**

```bash
# Check if container is running
docker ps | grep qpcr-assistant

# If not running, start it
docker compose -f docker-compose.autogen.yml up -d

# Wait for initialization (check logs)
docker logs -f qpcr-assistant

# Once initialized, attach
docker attach qpcr-assistant

# Alternative: Start in interactive mode
./start_interactive.sh
```

### MCP Server Connection Fails

**Error Message:**
```
Failed to connect to processing: Expecting value: line 1 column 1 (char 0)
```

**Solutions:**

1. **Check Python path in container:**
```bash
# Test if python3 exists
docker exec ndiag-processing-server which python3

# If error, verify Dockerfile uses python3
```

2. **Check server is responding:**
```bash
# Test processing server manually
docker exec -i ndiag-processing-server python3 /app/processing_mcp_server.py <<< \
'{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}'
```

3. **Verify container is running:**
```bash
docker ps | grep -E "database-server|processing-server"
```

4. **Check logs for startup errors:**
```bash
docker logs ndiag-database-server
docker logs ndiag-processing-server
```

### Permission Denied Errors

**Error Message:**
```
[Errno 13] Permission denied: '/tmp/mcp_cache/...'
```

**Solutions:**

```bash
# Fix processing server cache permissions
docker exec -u root ndiag-processing-server chown -R mcp:mcp /tmp/mcp_cache

# Fix database server cache permissions
docker exec -u root ndiag-database-server chown -R mcp:mcp /tmp/mcp_cache

# Restart services
docker compose -f docker-compose.autogen.yml restart
```

### Sequence Files Not Saved

**Symptoms:**
- No files in `/results/sequences/`
- Sequences retrieved but not written to disk

**Solutions:**

```bash
# Check results directory exists
docker exec qpcr-assistant ls -la /results

# Check permissions
docker exec qpcr-assistant ls -la /results/sequences

# Create directory if missing
docker exec qpcr-assistant mkdir -p /results/sequences

# Check logs for save errors
docker logs qpcr-assistant 2>&1 | grep -i "save\|write\|file"
```

### Agent Communication Issues

**Symptoms:**
- Agents don't respond to each other
- Workflow hangs indefinitely
- No progress after initial message

**Solutions:**

```bash
# Check for timeout errors
docker logs qpcr-assistant 2>&1 | grep -i "timeout"

# Verify max_round setting
docker logs qpcr-assistant 2>&1 | grep "max_round"

# Check for infinite loops
docker logs qpcr-assistant 2>&1 | tail -100

# Restart with fresh state
docker compose -f docker-compose.autogen.yml restart qpcr-assistant
```

## 🧪 Testing & Validation

### Validate Installation

```bash
# 1. Check all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected output:
# ndiag-database-server    Up (healthy)
# ndiag-processing-server  Up (healthy)
# qpcr-assistant          Up

# 2. Run integration test
python3 test_processing_integration.py

# 3. Run comprehensive test suite
python3 test_function_calling.py
```

### Test Individual Components

```bash
# Test database MCP server
cd mcp_servers/database_server
python -m pytest tests/ -v

# Test processing MCP server
cd mcp_servers/processing_server
python -m pytest tests/ -v

# Test MCP bridge
cd autogen_app
python -m pytest tests/test_mcp_bridge.py -v
```

### Manual Tool Testing

```bash
# Test with MCP Inspector (Database)
cd mcp_servers/database_server
npx @modelcontextprotocol/inspector python3 database_mcp_server.py
# Open http://localhost:6274

# Test with MCP Inspector (Processing)
cd mcp_servers/processing_server
npx @modelcontextprotocol/inspector python3 processing_mcp_server.py
# Open http://localhost:6274
```

## 📊 Debugging Tips

### Enable Debug Logging

```bash
# Add to autogen_app/.env
LOG_LEVEL=DEBUG

# Restart services
docker compose -f docker-compose.autogen.yml restart

# View debug logs
docker logs -f qpcr-assistant
```

### Inspect Task Logs

```bash
# View all task logs
docker exec qpcr-assistant ls -lh /results

# View latest task
docker exec qpcr-assistant cat /results/task_*.json | tail -1 | jq .

# Extract tool calls from logs
docker exec qpcr-assistant cat /results/task_*.json | jq '.tool_calls'

# Check for errors in logs
docker exec qpcr-assistant cat /results/task_*.json | jq '.errors'
```

### Check Network Connectivity

```bash
# Test if containers can communicate
docker exec qpcr-assistant ping -c 3 ndiag-database-server
docker exec qpcr-assistant ping -c 3 ndiag-processing-server

# Check network setup
docker network inspect ndiag-network
```

### Monitor Resource Usage

```bash
# Check container resource usage
docker stats

# Check disk space
docker exec qpcr-assistant df -h

# Check memory usage
docker exec qpcr-assistant free -h
```

## 🔄 Clean Restart Process

If all else fails, perform a clean restart:

```bash
# 1. Stop all services
docker compose -f docker-compose.autogen.yml down

# 2. Remove volumes (optional - deletes cached data)
docker volume rm mdk_mcp_database_cache
docker volume rm mdk_mcp_processing_cache

# 3. Rebuild images
docker compose -f docker-compose.autogen.yml build --no-cache

# 4. Start fresh
docker compose -f docker-compose.autogen.yml up -d

# 5. Verify startup
docker logs -f qpcr-assistant
```

## 📞 Getting Help

If you've tried these solutions and still have issues:

1. **Check Documentation**:
   - [USER_GUIDE.md](USER_GUIDE.md) - Comprehensive user guide
   - [MCP_TESTING_GUIDE.md](MCP_TESTING_GUIDE.md) - MCP testing guide
   - [AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md) - AG2 architecture

2. **Collect Diagnostic Info**:
```bash
# Save all logs
docker logs qpcr-assistant > qpcr_assistant.log 2>&1
docker logs ndiag-database-server > database_server.log 2>&1
docker logs ndiag-processing-server > processing_server.log 2>&1

# Save configuration
cat autogen_app/.env > config.txt
cat autogen_app/OAI_CONFIG_LIST.json >> config.txt

# Create archive
tar czf mdk_mcp_debug.tar.gz *.log config.txt
```

3. **Report Issue**:
   - GitHub Issues: https://github.com/acefgin/mdk_mcp/issues
   - Include: logs, error messages, steps to reproduce
   - Redact API keys before sharing!

## 🐛 Known Issues & Limitations

### Resolved Issues

- ✅ **Token Limit** - Fixed by integrating Gemini 2.5 Flash Lite (1M context)
- ✅ **Function Calling** - Fixed by ensuring gpt-4o/gemini model usage
- ✅ **Python Path** - Fixed by using `python3` instead of `python` in containers

### Current Limitations

1. **SILVA/UNITE Databases**: Placeholder implementations (planned for future)
2. **No Caching Layer**: Sequences re-downloaded on each request (Redis planned)
3. **Single User**: Interactive mode supports one user at a time
4. **No Web UI**: Command-line only (web interface planned)

### Future Enhancements

See [road_map.md](../road_map.md) for planned features:
- Phase 3: Alignment & Phylogenetics
- Phase 4: Primer Design
- Phase 5: Validation
- Phase 6: Export & Reporting

---

**Still stuck?** Check [CLAUDE.md](../CLAUDE.md) for development guidance or open a GitHub issue with logs attached.
