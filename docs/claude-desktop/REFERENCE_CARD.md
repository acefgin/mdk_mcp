# Testing Reference Card - Quick Commands

## 🚀 Setup (One Time)

```bash
./setup.sh
cp config/claude-desktop.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## ⚡ Daily Testing Workflow

```bash
# 1. Start Python servers
./start.sh

# 2. Test MCP server
npm run start:mcp:debug

# 3. Restart Claude Desktop (Cmd+Q, then reopen)

# 4. Test in Claude:
#    "List the available tools"
#    "Get COI sequences for Salmo salar"

# 5. Stop when done
./stop.sh
```

## 📊 Check Server Status

```bash
# Check if Python servers are running
ps aux | grep "mcp_server" | grep -v grep

# Check TypeScript MCP server
DEBUG=true node workspace/mcp-server.js
# (Ctrl+C to stop)

# View Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log  # macOS
tail -f ~/.local/share/Claude/logs/mcp*.log  # Linux
```

## 🐛 Common Issues & Fixes

### Issue: No hammer icon in Claude Desktop

```bash
# Fix 1: Check config location
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Fix 2: Verify path in config is correct
# Should be absolute path to workspace/mcp-server.js

# Fix 3: Restart Claude Desktop completely
# Quit (Cmd+Q), don't just close window
```

### Issue: Tools listed but don't work

```bash
# Fix 1: Check Python servers are running
ps aux | grep "mcp_server"

# Fix 2: Restart Python servers
./stop.sh
./start.sh

# Fix 3: Check for errors in logs
tail -f logs/mcp-*.log
```

### Issue: TypeScript compilation errors

```bash
# Fix 1: Install dependencies
npm install

# Fix 2: Recompile
npm run build:workspace

# Fix 3: Check Node version
node --version  # Should be 20+
```

### Issue: MCP server won't start

```bash
# Fix 1: Check for syntax errors
npx tsc workspace/mcp-server.ts --noEmit

# Fix 2: Test manually
DEBUG=true node workspace/mcp-server.js

# Fix 3: Check permissions
chmod +x workspace/mcp-server.js
```

## 📝 Test Checklist

- [ ] `npm test` - All tests pass
- [ ] `./setup.sh` - Setup completes
- [ ] `./start.sh` - All 5 servers start
- [ ] Claude Desktop shows hammer icon 🔨
- [ ] "List tools" works in Claude
- [ ] At least one tool executes successfully
- [ ] No errors in logs

## 🎯 Success Indicators

✅ Hammer icon visible in Claude Desktop  
✅ Tools list returns 34 tools  
✅ database.getSequences executes  
✅ processing.fastaQc executes  
✅ alignment.alignSequences executes  
✅ No Python errors in logs  
✅ Token usage < 10,000 initially

## 📈 Performance Monitoring

```bash
# Token usage (check Claude Desktop)
# Traditional: ~119,000 tokens
# Your setup: ~5,000 tokens
# Reduction: 95%+

# Monitor execution time
DEBUG=true npm run start:mcp
# Check "[METRICS]" lines in output

# Check Python server logs
tail -f logs/mcp-*.log
```

## 🔧 Useful Commands

```bash
# Run migration tests
npm run test:migration

# Compile workspace
npm run build:workspace

# Start MCP with debug
npm run start:mcp:debug

# Start Python servers
npm run start:python
# or: ./start.sh

# Stop Python servers
npm run stop:python
# or: ./stop.sh

# View all logs
tail -f logs/*.log
```

## 📚 Documentation Quick Links

- **Quick Start**: `docs/claude-desktop/QUICKSTART.md`
- **Full Guide**: `docs/claude-desktop/TESTING_GUIDE.md`
- **Test Results**: `docs/migration/TEST_SUMMARY.md`
- **Architecture**: `docs/architecture/MCP_2.0_SUMMARY.md`

## 🆘 Emergency Reset

```bash
# Stop everything
./stop.sh
pkill -f "workspace/mcp-server"

# Clean and rebuild
rm -rf workspace/*.js
npm run build:workspace

# Restart from scratch
./setup.sh
./start.sh
# Restart Claude Desktop
```

## 💡 Pro Tips

1. **Use PM2** for Python servers: `npm install -g pm2`
2. **Keep logs visible** while testing: `tail -f ~/Library/Logs/Claude/mcp*.log`
3. **Test incrementally**: One tool at a time
4. **Check timestamps** in logs to match errors to actions
5. **Restart Claude** after every config change

## 🎓 Example Test Conversations

### Test 1: List Tools
```
You: List the available tools
Claude: I have access to 34 tools...
```

### Test 2: Database Query
```
You: Get COI sequences for Salmo salar from BOLD
Claude: I'll use database.getSequences...
```

### Test 3: Quality Control
```
You: Run quality control on this FASTA:
>seq1
ATCGATCGATCG

Claude: I'll use processing.fastaQc...
```

### Test 4: Complete Workflow
```
You: I need to:
1. Get COI sequences for Salmo salar
2. Check their quality
3. Align them
4. Design primers

Claude: I'll help you through each step...
```

## 🔍 Debug Checklist

When something goes wrong, check in this order:

1. **Node.js version**: `node --version` (need 20+)
2. **Python servers**: `ps aux | grep mcp_server`
3. **TypeScript compiled**: `ls workspace/mcp-server.js`
4. **Config correct**: `cat config/claude-desktop.json`
5. **Claude logs**: `tail ~/Library/Logs/Claude/mcp*.log`
6. **Python logs**: `tail logs/mcp-*.log`
7. **Test manually**: `DEBUG=true npm run start:mcp`

## 📞 Getting Help

1. Check `docs/claude-desktop/TESTING_GUIDE.md` troubleshooting section
2. Review Claude Desktop logs for error messages
3. Test MCP server in isolation with DEBUG=true
4. Verify Python servers respond correctly
5. Check all file paths are absolute paths

---

**Keep this card handy while testing!**

*Last Updated: November 12, 2025*

