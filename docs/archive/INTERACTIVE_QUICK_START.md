# qPCR Assistant - Interactive Mode Quick Start

## 🚀 One-Line Start

```bash
./start_interactive.sh
```

That's it! The script will:
1. Check your API key configuration
2. Build and start containers
3. Attach you to the interactive chat interface

## 📝 Manual Start (Alternative)

```bash
# 1. Start containers
docker compose -f docker-compose.autogen.yml up -d

# 2. Attach to interactive session
docker attach qpcr-assistant
```

## 💬 Using the Interface

### Submit a Request

Just type naturally:

```
┌─[qPCR Assistant]
└─> Design a qPCR assay to identify Atlantic salmon (Salmo salar)
    and distinguish it from rainbow trout (Oncorhynchus mykiss).
    Target: COI region for aquaculture verification.
```

Press Enter. Watch agents collaborate in real-time!

### Available Commands

| Command | Action |
|---------|--------|
| Type naturally | Submit qPCR design request |
| `help` | Show usage examples |
| `logs` | View recent task logs |
| `clear` | Clear screen |
| `exit` or `quit` | Exit assistant |
| `Ctrl+C` | Interrupt current workflow |
| `Ctrl+P, Ctrl+Q` | Detach (keeps running) |

## 📊 Real-Time Progress

You'll see:

```
🚀 STARTING WORKFLOW
═══════════════════════════════════════════════════════════════════════════

[Coordinator] Planning workflow...
  Step 1: Retrieve COI sequences for Salmo salar
  Step 2: Retrieve COI sequences for Oncorhynchus mykiss
  Step 3: Analyze for signature regions
  Step 4: Recommend primer design strategy

[DatabaseAgent] Calling tool: get_sequences
  Arguments: taxon="Salmo salar", region="COI", max_results=100
  ✓ Retrieved 100 sequences (292,015 characters)

[AnalystAgent] Analyzing sequences...
  • Identified 15 conserved regions in target
  • Found 3 signature regions unique to Salmo salar
  • Recommending primers in signature region 2 (position 450-470)

═══════════════════════════════════════════════════════════════════════════
✓ WORKFLOW COMPLETED
═══════════════════════════════════════════════════════════════════════════

Task log saved to /results/task_20251001_181530.json

┌─[qPCR Assistant]
└─>
```

## 🔄 Multiple Requests

Submit as many as you want in one session:

```
┌─[qPCR Assistant]
└─> [First request about salmon]
[Workflow completes]

┌─[qPCR Assistant]
└─> [Second request about bacteria]
[Workflow completes]

┌─[qPCR Assistant]
└─> [Third request about fungi]
[Workflow completes]

┌─[qPCR Assistant]
└─> logs
[View all task logs]

┌─[qPCR Assistant]
└─> exit
👋 Goodbye!
```

## 📋 Example Requests

### Species Identification
```
Design a qPCR assay to identify Atlantic salmon (Salmo salar)
and distinguish it from rainbow trout (Oncorhynchus mykiss).
Target: COI region for aquaculture verification.
```

### Pathogen Detection
```
Design a qPCR assay to detect Mycobacterium tuberculosis
in clinical samples with specificity against other Mycobacterium species.
```

### Environmental Monitoring
```
Design qPCR for invasive zebra mussels (Dreissena polymorpha)
in eDNA samples for early detection in waterways.
```

## 🛑 Stopping and Detaching

### Exit Cleanly
```
┌─[qPCR Assistant]
└─> exit
```

### Detach Without Stopping
Press: `Ctrl+P` then `Ctrl+Q`

Container keeps running. Reconnect anytime:
```bash
docker attach qpcr-assistant
```

### Stop Everything
```bash
docker compose -f docker-compose.autogen.yml down
```

## 📁 Viewing Task Logs

### Inside Session
```
┌─[qPCR Assistant]
└─> logs
```

### From Host Machine
```bash
# List all logs
docker exec qpcr-assistant ls -lh /results

# View latest summary
docker exec qpcr-assistant cat \
  $(docker exec qpcr-assistant ls -t /results/*_summary.txt | head -1)

# Copy to local machine
docker cp qpcr-assistant:/results ./qpcr_logs
```

## ⚠️ Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs qpcr-assistant

# Verify API key
cat autogen_app/.env | grep OPENAI_API_KEY

# Rebuild from scratch
docker compose -f docker-compose.autogen.yml down
docker compose -f docker-compose.autogen.yml up --build -d
```

### Can't Attach

```bash
# Verify container is running
docker ps | grep qpcr-assistant

# Start if needed
docker compose -f docker-compose.autogen.yml up -d

# Then attach
docker attach qpcr-assistant
```

### Workflow Interrupted

Press `Ctrl+C` to stop current workflow.
You can immediately submit a new request.

## 💡 Pro Tips

1. **Be Specific**: Include target species, off-targets, genomic region
2. **Watch Progress**: Agents show what they're doing in real-time
3. **Review Logs**: Type `logs` to see previous workflows
4. **Multiple Sessions**: Open multiple terminal windows, each can attach
5. **Detach Safely**: Use `Ctrl+P, Ctrl+Q` to keep container running

## 📖 More Documentation

- **INTERACTIVE_MODE.md** - Complete interactive mode guide
- **USER_GUIDE.md** - Detailed user guide with all features
- **QUICK_START.md** - Original quick start guide
- **INTERACTION_REFERENCE.md** - Quick reference card

## 🎯 Next Steps

1. Start the assistant: `./start_interactive.sh`
2. Try the example requests
3. Check your task logs: `logs` command
4. Submit your own custom requests
5. Explore the multi-agent collaboration

---

**Ready?**

```bash
./start_interactive.sh
```

Welcome to qPCR assay design with AI! 🧬
