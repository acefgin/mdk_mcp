# Hooks for mdk_mcp

Claude Code hooks for automatic skill activation and file tracking in the mdk_mcp bioinformatics platform.

---

## Essential Hooks (Start Here)

### skill-activation-prompt (UserPromptSubmit)

**Purpose:** Automatically suggests relevant skills based on user prompts and file context

**Integration:**
```bash
# Already installed! Just need to add to settings.json
cd $CLAUDE_PROJECT_DIR/.claude/hooks
npm install  # Install TypeScript dependencies
```

**Add to `.claude/settings.json`:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.sh"
          }
        ]
      }
    ]
  }
}
```

**Customization:** ✅ None needed - reads `skill-rules.json` automatically

---

### post-tool-use-tracker (PostToolUse)

**Purpose:** Tracks file changes and provides context-specific reminders for mdk_mcp

**Features:**
- Auto-detects mdk_mcp structure (MCP servers, AG2 agents, tests, docs)
- Provides section-specific reminders
- Suggests next steps based on what was modified

**Add to `.claude/settings.json`:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.sh"
          }
        ]
      }
    ]
  }
}
```

**Customization:** ✅ None needed - auto-detects project structure

---

## Quick Setup

```bash
# 1. Navigate to project (replace with your path)
cd /path/to/mdk_mcp

# 2. Install hook dependencies
cd .claude/hooks
npm install

# 3. Create settings.json (see example below)
cd ..
cat > settings.json << 'EOF'
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-tracker.sh"
          }
        ]
      }
    ]
  }
}
EOF

# 4. Test hooks
cd ..
# Edit a file in mcp_servers/ and watch skills activate!
```

---

## How It Works

### Skill Activation Flow

1. **User types prompt**: "Add a new MCP tool for sequence alignment"
2. **UserPromptSubmit hook fires**:
   - Reads `.claude/skills/skill-rules.json`
   - Matches keywords: "MCP tool", "alignment"
   - Matches intent pattern: "(add|create).*?MCP.*?tool"
3. **Hook injects suggestion**:
   ```
   🎯 SKILL ACTIVATION CHECK
   📚 RECOMMENDED SKILLS:
     → mcp-server-dev
     → bioinformatics-workflow
   ```
4. **Claude loads skills** and applies patterns

### File Tracking Flow

1. **You edit**: `mcp_servers/database_server/database_mcp_server.py`
2. **PostToolUse hook fires**:
   - Detects file is in `database_server`
   - Identifies section: MCP Server
3. **Hook provides reminders**:
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

## Verification

After setup, verify hooks are working:

```bash
# 1. Check hooks are executable
ls -la .claude/hooks/*.sh
# Should show: -rwxr-xr-x

# 2. Validate skill-rules.json
cat .claude/skills/skill-rules.json | jq .
# Should parse without errors

# 3. Check hook dependencies
ls .claude/hooks/node_modules/
# Should show installed packages

# 4. Test by editing a file
# Edit any Python file in mcp_servers/ and watch for:
# - Skill suggestions when you mention "MCP tool"
# - File tracking message after edit completes
```

---

## Customization

### Adding New Skill Triggers

Edit `.claude/skills/skill-rules.json`:

```json
{
  "skills": {
    "your-custom-skill": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "high",
      "promptTriggers": {
        "keywords": ["your", "custom", "keywords"],
        "intentPatterns": [
          "(create|add).*?your.*?pattern"
        ]
      },
      "fileTriggers": {
        "pathPatterns": [
          "your/path/**/*.py"
        ]
      }
    }
  }
}
```

### Adding Section Detection

Edit `.claude/hooks/post-tool-use-tracker.sh`:

```bash
detect_mdk_structure() {
    local file="$1"
    
    # Add your custom detection
    if [[ "$file" == *"your_custom_dir/"* ]]; then
        echo "custom_section"
        return 0
    fi
    
    # ... existing code ...
}

# Add custom reminder
case "$section" in
    custom_section)
        echo "💡 Your Custom Section:"
        echo "  - Do something specific"
        ;;
esac
```

---

## Troubleshooting

### Hook not activating

**Check:**
```bash
# 1. Is settings.json valid?
cat .claude/settings.json | jq .

# 2. Are hooks executable?
ls -la .claude/hooks/*.sh

# 3. Are dependencies installed?
ls .claude/hooks/node_modules/

# 4. Test hook manually
echo '{"prompt": "add MCP tool"}' | .claude/hooks/skill-activation-prompt.sh
```

### Skills not suggesting

**Check:**
```bash
# 1. Is skill-rules.json valid?
cat .claude/skills/skill-rules.json | jq .

# 2. Do keywords match your prompt?
cat .claude/skills/skill-rules.json | jq '.skills."mcp-server-dev".promptTriggers.keywords'

# 3. Test pattern matching
echo '{"prompt": "create MCP server"}' | .claude/hooks/skill-activation-prompt.sh
```

---

## mdk_mcp-Specific Behavior

### MCP Server Detection

When you edit files in `mcp_servers/`, the hook:
- Identifies which server (database/processing/alignment/design)
- Reminds you to rebuild Docker container
- Suggests testing with MCP Inspector
- Reminds about updating tests

### AG2 Agent Detection

When you edit files in `autogen_app/`, the hook:
- Identifies AG2 agent modifications
- Reminds about agent collaboration testing
- Suggests verifying tool registration
- Prompts workflow coordination checks

### Test Detection

When you edit test files, the hook:
- Identifies test modifications
- Reminds to run pytest
- Suggests checking test coverage

---

## Next Steps

1. ✅ Hooks installed and configured
2. 📝 Edit a file in `mcp_servers/` to test
3. 💬 Type "create MCP tool" to see skill activation
4. 📚 Browse skills in `.claude/skills/` directory
5. 🎨 Add custom skills as needed

**Questions?** See main README in `.claude/` directory.

