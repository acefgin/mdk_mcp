# Documentation Index

Complete guide to mdk_mcp documentation organized by audience and purpose.

## 📚 Documentation Map

```
docs/
├── USER_GUIDE.md              # Comprehensive user reference
├── QUICK_START.md             # 5-minute getting started
├── INTERACTIVE_MODE.md        # Interactive terminal guide
├── TROUBLESHOOTING.md         # Problem solving guide (NEW)
├── AUTOGEN_INTEGRATION.md     # Technical architecture
├── MCP_TESTING_GUIDE.md       # MCP server testing
├── MCP_TESTING_QUICKREF.md    # Quick testing reference
├── DEPLOYMENT.md              # Production deployment
└── archive/                   # Historical documentation
```

## 🎯 Quick Navigation

### For Users

**Getting Started:**
1. Start with [README.md](../README.md) - Overview and quick start
2. Follow [QUICK_START.md](QUICK_START.md) - 5-minute setup
3. Use [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) - Terminal interface guide
4. Reference [USER_GUIDE.md](USER_GUIDE.md) - Complete usage guide

**When Things Go Wrong:**
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** ← Start here for all problems
  - Container issues
  - Tool calling problems
  - Token limit errors
  - Permission errors
  - Network issues
  - Complete diagnostic procedures

### For Developers

**Architecture & Design:**
- [AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md) - AG2 multi-agent architecture
- [../CLAUDE.md](../CLAUDE.md) - Project structure and patterns
- [../road_map.md](../road_map.md) - Development roadmap

**Testing & Validation:**
- [MCP_TESTING_GUIDE.md](MCP_TESTING_GUIDE.md) - Complete MCP testing guide (741 lines)
- [MCP_TESTING_QUICKREF.md](MCP_TESTING_QUICKREF.md) - Quick command reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Debugging procedures

**Deployment:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [../docker-compose.autogen.yml](../docker-compose.autogen.yml) - Docker configuration
- [../kubernetes/](../kubernetes/) - Kubernetes manifests

## 📖 Document Descriptions

### User Documentation

#### README.md (Main)
**Purpose:** Project overview, quick start, feature highlights
**Length:** 650 lines
**Audience:** Everyone - first stop for all users
**Key Sections:**
- What is mdk_mcp?
- Quick start (3 steps)
- Key features (16 MCP tools)
- Example workflows
- Testing basics

#### USER_GUIDE.md
**Purpose:** Comprehensive usage reference
**Audience:** Users who want detailed instructions
**Coverage:**
- Complete tool catalog
- Workflow examples
- Configuration options
- Best practices

#### QUICK_START.md
**Purpose:** Fastest path from zero to working system
**Length:** ~5 minutes to complete
**Audience:** New users wanting immediate results

#### INTERACTIVE_MODE.md
**Purpose:** Complete guide to the terminal interface
**Audience:** Users of the interactive chat system
**Coverage:**
- Commands and shortcuts
- Workflow examples
- Log management
- Session control

### Problem-Solving Documentation

#### TROUBLESHOOTING.md (NEW)
**Purpose:** Solve common problems quickly
**Length:** ~350 lines
**Audience:** Anyone encountering issues
**Contents:**
- ✅ Container startup issues
- ✅ Tool calling problems
- ✅ Token limit errors
- ✅ Permission errors
- ✅ MCP server connection issues
- ✅ Network problems
- ✅ Complete diagnostic procedures
- ✅ Clean restart guide

**Moved from README.md:**
- All troubleshooting procedures
- Known issues section
- Current status section
- Debugging tips

### Technical Documentation

#### AUTOGEN_INTEGRATION.md
**Purpose:** Understand the AG2 multi-agent system
**Audience:** Developers working on AG2 integration
**Topics:**
- Agent architecture
- MCP bridge design
- Function calling patterns
- Message flow

#### MCP_TESTING_GUIDE.md
**Purpose:** Complete guide to testing MCP servers
**Length:** 741 lines (comprehensive)
**Audience:** Developers testing MCP implementations
**Methods:**
- MCP Inspector (UI)
- Command-line testing
- Automated scripts
- Integration testing

#### MCP_TESTING_QUICKREF.md
**Purpose:** Quick command reference
**Length:** Short, scannable
**Audience:** Developers who know what to do, need commands

#### DEPLOYMENT.md
**Purpose:** Production deployment procedures
**Audience:** DevOps, system administrators
**Topics:**
- Docker deployment
- Kubernetes setup
- Scaling strategies
- Monitoring

## 🔍 Finding What You Need

### By Symptom

**"Container won't start"**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md#container-wont-start)

**"Agents don't call tools"**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md#no-tool-calls-made)

**"Token limit error"**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md#workflow-fails-with-token-limit-error)

**"How do I use tool X?"**
→ [USER_GUIDE.md](USER_GUIDE.md)

**"What example requests can I try?"**
→ [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md#example-workflows)

### By Task

**"I want to design a qPCR assay"**
1. [README.md](../README.md) - Overview
2. [QUICK_START.md](QUICK_START.md) - Setup
3. [INTERACTIVE_MODE.md](INTERACTIVE_MODE.md) - Usage

**"I'm adding a new MCP tool"**
1. [CLAUDE.md](../CLAUDE.md) - Code structure
2. [MCP_TESTING_GUIDE.md](MCP_TESTING_GUIDE.md) - Testing procedures
3. [AUTOGEN_INTEGRATION.md](AUTOGEN_INTEGRATION.md) - Integration points

**"I'm deploying to production"**
1. [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Debugging
3. [../kubernetes/](../kubernetes/) - K8s manifests

## 📊 Documentation Statistics

| Document | Lines | Purpose | Audience |
|----------|-------|---------|----------|
| README.md | 650 | Overview & Quick Start | Everyone |
| USER_GUIDE.md | ~800 | Complete user reference | Users |
| TROUBLESHOOTING.md | ~350 | Problem solving | Everyone |
| MCP_TESTING_GUIDE.md | 741 | MCP testing | Developers |
| AUTOGEN_INTEGRATION.md | ~500 | AG2 architecture | Developers |
| INTERACTIVE_MODE.md | ~300 | Terminal interface | Users |
| QUICK_START.md | ~200 | Fast setup | New users |

**Total:** ~3,500 lines of documentation

## 🎨 Documentation Standards

### User-Facing Docs
- ✅ Clear, jargon-free language
- ✅ Step-by-step instructions
- ✅ Visual examples (code blocks, output samples)
- ✅ "Why" explanations alongside "How"
- ✅ Links to related sections

### Developer Docs
- ✅ Code examples with explanations
- ✅ Architecture diagrams (ASCII art)
- ✅ Design decisions documented
- ✅ Links to source code locations
- ✅ Testing procedures included

### Troubleshooting Docs
- ✅ Symptom → Solution format
- ✅ Copy-paste commands
- ✅ Expected output shown
- ✅ Root cause explanations
- ✅ "Still stuck?" escalation paths

## 🔄 Recent Changes

### October 23, 2025
**Reorganized documentation structure:**
- ✅ Created `TROUBLESHOOTING.md` with all problem-solving content
- ✅ Removed 115 lines of dev content from `README.md`
- ✅ Simplified `README.md` to focus on features and quick start
- ✅ Moved "Known Issues" to troubleshooting guide
- ✅ Moved "Current Status" details to roadmap
- ✅ Created this documentation index

**Benefits:**
- README.md is now cleaner and more user-focused
- Troubleshooting procedures are comprehensive and findable
- Clear separation between user and developer docs
- Easier to maintain and update

## 📝 Contributing to Docs

When adding or updating documentation:

1. **Choose the right file:**
   - User instructions → USER_GUIDE.md or INTERACTIVE_MODE.md
   - Problems/solutions → TROUBLESHOOTING.md
   - Architecture/design → AUTOGEN_INTEGRATION.md or CLAUDE.md
   - Testing → MCP_TESTING_GUIDE.md

2. **Follow the format:**
   - Use clear headers (##, ###)
   - Include code blocks with syntax highlighting
   - Show expected output
   - Add links to related sections

3. **Update this index:**
   - Add new documents to the map
   - Update line counts
   - Add navigation links

4. **Test your examples:**
   - All code samples should work
   - Commands should be copy-paste ready
   - Paths should be correct

---

**Need help finding something?** Check the navigation sections above or search for keywords in specific files.
