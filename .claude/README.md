# Claude Code Infrastructure for mdk_mcp

**Custom Claude Code infrastructure for the mdk_mcp bioinformatics platform**

Adapted from the production-tested Claude Code infrastructure template, specifically customized for Python-based MCP server development and AG2 multi-agent bioinformatics workflows.

---

## 🎯 What This Provides

### Auto-Activating Skills
Skills that automatically suggest themselves based on what you're working on:
- 🔧 **mcp-server-dev** - MCP server development patterns
- 🤖 **ag2-agent-dev** - AG2 multi-agent orchestration
- 🐍 **python-dev-guidelines** - Python async/await best practices
- 🧬 **bioinformatics-workflow** - Sequence analysis workflows
- 🐳 **docker-container-dev** - Container and deployment patterns
- 🧪 **testing-and-qa** - pytest and MCP testing strategies

### Specialized Agents
Autonomous agents for complex tasks:
- 📋 **mcp-tool-reviewer** - Review MCP tool implementations
- 🧬 **qpcr-workflow-planner** - Plan comprehensive qPCR workflows

### Smart Hooks
- ✅ **skill-activation-prompt** - Auto-suggests skills based on context
- ✅ **post-tool-use-tracker** - Tracks changes and provides reminders

### Slash Commands
- 📝 **/dev-docs** - Create comprehensive development documentation

---

## 🚀 Quick Start

### 1. Install Hook Dependencies

```bash
cd /home/cxl/MDK_Design/mdk_mcp/.claude/hooks
npm install
```

### 2. Verify Installation

```bash
# Check hooks are executable
ls -la .claude/hooks/*.sh
# Should show: -rwxr-xr-x

# Validate skill-rules.json
cat .claude/skills/skill-rules.json | jq .
# Should parse without errors
```

### 3. Test the Infrastructure

**Edit a Python file in `mcp_servers/`:**
```bash
# Open any MCP server file
# Type: "Add a new MCP tool for sequence alignment"
# Watch the skill-activation-prompt suggest relevant skills!
```

**Edit is tracked:**
```
📝 FILE CHANGE TRACKED
File: mcp_servers/database_server/database_mcp_server.py
Section: database_server

💡 MCP Server Modified:
  - Rebuild container: docker-compose build database_server
  - Test with MCP Inspector
  - Update tests if tool schema changed
```

---

## 📦 What's Included

### Skills (7)

| Skill | Purpose | Priority | Triggers |
|-------|---------|----------|----------|
| **mcp-server-dev** | MCP tool patterns | High | "MCP tool", "MCP server", editing `*_mcp_server.py` |
| **ag2-agent-dev** | AG2 agent patterns | High | "agent", "AG2", editing `autogen_app/*.py` |
| **python-dev-guidelines** | Python best practices | High | "python", "async", editing `*.py` |
| **bioinformatics-workflow** | Sequence analysis | High | "qPCR", "primer", "sequence", "alignment" |
| **docker-container-dev** | Containerization | Medium | "Docker", editing `Dockerfile`, `docker-compose.yml` |
| **testing-and-qa** | Testing patterns | Medium | "test", "pytest", editing `test_*.py` |
| **skill-developer** | Skill creation | High | "create skill", "skill system" |

### Hooks (2)

| Hook | Type | Essential? | Purpose |
|------|------|-----------|---------|
| **skill-activation-prompt** | UserPromptSubmit | ✅ YES | Auto-suggests skills |
| **post-tool-use-tracker** | PostToolUse | ✅ YES | Tracks file changes |

### Agents (2)

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| **mcp-tool-reviewer** | Review MCP implementations | After implementing/modifying tools |
| **qpcr-workflow-planner** | Plan qPCR workflows | Before starting new assay design |

### Commands (1)

| Command | Purpose |
|---------|---------|
| **/dev-docs [task]** | Create dev documentation |

---

## 🎨 How It Works

### Skill Auto-Activation

```
You type: "Add a new MCP tool for BLAST validation"
           ↓
UserPromptSubmit hook fires
           ↓
Reads skill-rules.json
  - Matches keyword: "MCP tool"
  - Matches intent: "(add|create).*?MCP.*?tool"
  - Checks open files: mcp_servers/
           ↓
Injects suggestion:
  🎯 SKILL ACTIVATION CHECK
  📚 RECOMMENDED SKILLS:
    → mcp-server-dev
    → bioinformatics-workflow
           ↓
Claude loads skills and applies patterns!
```

### File Change Tracking

```
You edit: mcp_servers/database_server/database_mcp_server.py
           ↓
PostToolUse hook fires
           ↓
Detects section: database_server
           ↓
Provides context-specific reminders:
  💡 MCP Server Modified:
    - Rebuild container: docker-compose build database_server
    - Test with MCP Inspector
    - Update tests if tool schema changed
```

---

## 📖 Documentation

### For Skills
- **[.claude/skills/mcp-server-dev/SKILL.md](skills/mcp-server-dev/SKILL.md)** - MCP development guide
- **[.claude/skills/ag2-agent-dev/SKILL.md](skills/ag2-agent-dev/SKILL.md)** - AG2 agent patterns

### For Hooks
- **[.claude/hooks/README.md](hooks/README.md)** - Hook setup and customization

### For Agents
- **[.claude/agents/mcp-tool-reviewer.md](agents/mcp-tool-reviewer.md)** - Tool review agent
- **[.claude/agents/qpcr-workflow-planner.md](agents/qpcr-workflow-planner.md)** - Workflow planning agent

---

## 💡 Usage Examples

### Example 1: Implementing a New MCP Tool

**Scenario**: You want to add a BLAST validation tool

1. **Type your intent**:
   ```
   "I need to add a BLAST validation tool to the validation server"
   ```

2. **Skill activates**:
   ```
   🎯 SKILL ACTIVATION CHECK
   📚 RECOMMENDED SKILLS:
     → mcp-server-dev
   ```

3. **Claude loads mcp-server-dev skill** and applies patterns:
   - Suggests tool definition structure
   - Recommends async/await patterns
   - Guides input schema design
   - Reminds about error handling
   - Suggests testing approach

4. **After editing**, post-tool-use-tracker provides reminders:
   ```
   💡 MCP Server Modified:
     - Rebuild container: docker-compose build validation_server
     - Test with MCP Inspector
     - Update tests if tool schema changed
   ```

### Example 2: Planning a qPCR Workflow

1. **Use the agent**:
   ```
   "Use the qpcr-workflow-planner agent to plan an assay for detecting 
   Salmo salar and distinguishing it from Oncorhynchus mykiss using COI"
   ```

2. **Agent generates comprehensive plan**:
   - Data retrieval strategy
   - QC and processing pipeline
   - Alignment and phylogenetics approach
   - Primer design parameters
   - Validation strategy
   - Risk assessment
   - Timeline estimates

3. **Plan saved** to `./dev/active/qpcr-salmo-salar-coi-plan.md`

### Example 3: Reviewing MCP Tool Implementation

1. **Use the agent**:
   ```
   "Use the mcp-tool-reviewer agent to review the get_sequences tool 
   in the database server"
   ```

2. **Agent performs comprehensive review**:
   - MCP protocol compliance
   - Code quality (async patterns, type hints)
   - BioPython integration
   - Error handling
   - Testing coverage
   - Documentation quality

3. **Review saved** with prioritized findings:
   - Critical issues (must fix)
   - Important improvements (should fix)
   - Minor suggestions (nice to have)

### Example 4: Creating Development Documentation

1. **Use slash command**:
   ```
   /dev-docs implement Primer3 design tool in design server
   ```

2. **Claude generates**:
   - `dev/active/implement-primer3-design/implement-primer3-design-plan.md`
   - `dev/active/implement-primer3-design/implement-primer3-design-context.md`
   - `dev/active/implement-primer3-design/implement-primer3-design-tasks.md`

3. **Documentation includes**:
   - Technical specifications
   - MCP tool schemas
   - Implementation phases
   - Testing strategy
   - Risk assessment

---

## 🔧 Customization

### Adding New Skill Triggers

Edit `.claude/skills/skill-rules.json`:

```json
{
  "skills": {
    "your-skill-name": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "high",
      "promptTriggers": {
        "keywords": ["your", "keywords"],
        "intentPatterns": ["(create|add).*?your.*?pattern"]
      },
      "fileTriggers": {
        "pathPatterns": ["your/path/**/*.py"]
      }
    }
  }
}
```

### Adding Custom Section Detection

Edit `.claude/hooks/post-tool-use-tracker.sh`:

```bash
detect_mdk_structure() {
    # Add custom detection
    if [[ "$file" == *"your_custom_dir/"* ]]; then
        echo "custom_section"
        return 0
    fi
}
```

---

## 🎯 Project-Specific Patterns

### MCP Server Structure

```
mcp_servers/<server_name>/
├── <server_name>_mcp_server.py  # Main server
├── config.py                     # Configuration
├── requirements.txt              # Dependencies
├── Dockerfile                    # Container
├── tests/                        # Test suite
└── README.md                     # Documentation
```

**Skills activated when editing**:
- `mcp-server-dev` - Protocol patterns
- `python-dev-guidelines` - Python best practices
- `testing-and-qa` - When editing tests

### AG2 Agent Structure

```
autogen_app/
├── qpcr_assistant.py         # Multi-agent system
├── autogen_mcp_bridge.py     # MCP bridge
├── OAI_CONFIG_LIST.json      # LLM config
└── requirements.txt           # Dependencies
```

**Skills activated when editing**:
- `ag2-agent-dev` - Agent patterns
- `python-dev-guidelines` - Python best practices

### Bioinformatics Workflow

When you mention bioinformatics terms:
- "sequence", "FASTA", "alignment" → `bioinformatics-workflow`
- "qPCR", "primer", "assay" → `bioinformatics-workflow`
- "phylogeny", "taxonomy" → `bioinformatics-workflow`

---

## ✅ Verification

After setup, verify everything works:

```bash
# 1. Hooks are executable
ls -la .claude/hooks/*.sh
# Expected: -rwxr-xr-x

# 2. skill-rules.json is valid
cat .claude/skills/skill-rules.json | jq .
# Expected: No errors

# 3. Dependencies installed
ls .claude/hooks/node_modules/
# Expected: Packages present

# 4. Test skill activation
# Edit mcp_servers/database_server/database_mcp_server.py
# Type: "add MCP tool"
# Expected: Skill suggestions appear

# 5. Test file tracking
# Make an edit to any Python file
# Expected: Post-tool-use message with reminders
```

---

## 🐛 Troubleshooting

### Skills not activating

**Check:**
1. Is `skill-rules.json` valid JSON?
2. Do keywords match your prompt?
3. Are hooks executable?
4. Are dependencies installed?

**Test manually:**
```bash
echo '{"prompt": "create MCP server"}' | .claude/hooks/skill-activation-prompt.sh
```

### Hooks not running

**Check:**
1. Is `settings.json` valid JSON?
2. Are hooks marked executable (`chmod +x`)?
3. Are paths correct in settings.json?

**Verify:**
```bash
cat .claude/settings.json | jq .
ls -la .claude/hooks/*.sh
```

---

## 📊 Statistics

**Total Components:**
- 7 Skills (covering all mdk_mcp development areas)
- 2 Essential Hooks (auto-activation + tracking)
- 2 Specialized Agents (review + planning)
- 1 Slash Command (dev docs)

**Customization Level:**
- ✅ Fully adapted for Python/MCP/AG2 development
- ✅ Tailored for bioinformatics workflows
- ✅ mdk_mcp project structure detection
- ✅ Context-specific reminders

**Integration Time:**
- ✅ ~5 minutes (install dependencies)
- ✅ ~0 minutes (works out of box after npm install)

---

## 🎓 Learning Resources

### MCP Development
- Read `skills/mcp-server-dev/SKILL.md` for comprehensive guide
- Review existing MCP servers in `mcp_servers/` for patterns
- Test with MCP Inspector: `npx @modelcontextprotocol/inspector python3 server.py`

### AG2 Agent Development
- Read `skills/ag2-agent-dev/SKILL.md` for patterns
- Review `autogen_app/qpcr_assistant.py` for examples
- Check AG2 docs: https://docs.ag2.ai

### Bioinformatics Workflows
- Review `CLAUDE.md` for mdk_mcp architecture
- Check `road_map.md` for project phases
- See `README.md` for tool catalog

---

## 🤝 Contributing

To add new skills or agents:

1. **Create skill** in `.claude/skills/[skill-name]/SKILL.md`
2. **Add triggers** to `.claude/skills/skill-rules.json`
3. **Test activation** by editing files and typing keywords
4. **Document patterns** in skill resource files

Follow the existing skill structure:
- Main SKILL.md < 500 lines
- Resource files for deep dives
- Clear examples and patterns
- Quick reference sections

---

## 📝 Next Steps

1. ✅ Dependencies installed
2. 📝 Try editing a file in `mcp_servers/`
3. 💬 Type "create MCP tool" and watch skills activate
4. 🤖 Use agents for reviews and planning
5. 📖 Browse skills for development patterns

**Questions?** Check individual README files in each directory or review skill documentation.

---

**Adapted from**: [Claude Code Infrastructure Template](https://github.com/acefgin/claude-code-infra-template)  
**Customized for**: mdk_mcp bioinformatics platform (Python, MCP, AG2, BioPython)  
**License**: MIT

