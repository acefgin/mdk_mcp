---
description: Create comprehensive development documentation for mdk_mcp tasks
argument-hint: Describe your development task (e.g., "implement Primer3 design tool", "add BLAST validation server")
---

You are an elite technical documentation specialist for bioinformatics and MCP development. Create comprehensive, actionable documentation for: $ARGUMENTS

## Instructions

1. **Analyze the task** and understand its scope in the mdk_mcp context
2. **Examine relevant code** to understand current implementation state
3. **Create structured documentation** with:
   - Task Overview and Goals
   - Current State Analysis
   - Implementation Plan (phased approach)
   - Technical Specifications
   - MCP Tool Definitions (if applicable)
   - AG2 Agent Integration (if applicable)
   - Testing Strategy
   - Risk Assessment and Mitigation
   - Success Criteria
   - Timeline Estimates

4. **Create task management structure**:
   - Create directory: `dev/active/[task-slug]/` (relative to project root)
   - Generate three files:
     - `[task-slug]-plan.md` - The comprehensive technical plan
     - `[task-slug]-context.md` - Key files, dependencies, decisions
     - `[task-slug]-tasks.md` - Checklist format for tracking progress
   - Include "Last Updated: YYYY-MM-DD" in each file

## Quality Standards for mdk_mcp

### MCP Tool Documentation

If the task involves MCP tools, document:

**Tool Definition:**
```python
types.Tool(
    name="tool_name",
    description="[Clear, comprehensive description]",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "[string|integer|boolean|array]",
                "description": "[What this parameter does]",
                "default": "[default value if optional]"
            }
        },
        "required": ["[list required params]"]
    }
)
```

**Implementation Pattern:**
```python
async def tool_function(
    param1: str,
    param2: int = 100
) -> str:
    """
    [Docstring with Args, Returns, Examples]
    """
    try:
        # Implementation
        return "Success message"
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {str(e)}"
```

**Testing Requirements:**
- Unit tests with pytest
- MCP integration tests
- Happy path and error cases
- Example in README

### AG2 Agent Documentation

If the task involves agents, document:

**Agent Configuration:**
```python
agent = ConversableAgent(
    name="AgentName",
    system_message="[Detailed role and responsibilities]",
    llm_config={
        "config_list": config_list,
        "temperature": 0.0,
        "cache_seed": None
    },
    human_input_mode="NEVER",
    code_execution_config=False
)
```

**Tool Registration:**
```python
bridge.register_tools_for_agent(agent, "server_name")
```

**Workflow Integration:**
- How agent fits in the pipeline
- Which phase (1-4) it operates in
- Handoff patterns to other agents

### Bioinformatics Tool Documentation

If integrating bioinformatics tools:

**Tool Selection Justification:**
- Why this tool? (alternatives considered)
- Installation method (pip/conda/binary)
- Version requirements
- Docker integration

**Example: Primer3**
```
Tool: Primer3
Purpose: qPCR primer design with constraints
Installation: conda install -c bioconda primer3
Docker: RUN conda install -c bioconda primer3
Wrapper: primer3-py Python library
Version: ≥2.6.1
```

**BioPython Integration:**
- Which Bio modules needed
- Sequence format handling
- Error handling patterns

## Task Plan Structure

### 1. [task-slug]-plan.md

```markdown
# [Task Name] - Implementation Plan

**Date**: YYYY-MM-DD
**Phase**: [1-Database / 2-Processing / 3-Alignment / 4-Design / 5-Validation / 6-Export]
**Estimated Effort**: [hours/days/weeks]

## Executive Summary

[2-3 sentences: What are we building and why?]

## Current State

### What Exists
- [Current implementation details]
- [Related code/servers]

### What's Missing
- [Gap 1]
- [Gap 2]

### Dependencies
- [Server/agent/tool dependencies]
- [External library requirements]

## Goals

### Primary Goals
1. [Main objective]
2. [Secondary objective]

### Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

## Implementation Phases

### Phase 1: [Foundation] (X hours)

**Objectives:**
- [Specific objective]
- [Specific objective]

**Tasks:**
1. [Task 1.1]: [Description]
   - **Acceptance**: [How to verify complete]
   - **Files**: [Which files to create/modify]
   
2. [Task 1.2]: [Description]
   - **Acceptance**: [How to verify complete]
   - **Files**: [Which files to create/modify]

### Phase 2: [Core Implementation] (X hours)

[Same structure]

### Phase 3: [Testing & Documentation] (X hours)

[Same structure]

## Technical Specifications

### MCP Tools (if applicable)

#### Tool 1: [name]
```python
# Tool definition
types.Tool(
    name="[name]",
    description="[description]",
    inputSchema={...}
)
```

**Implementation:**
- Input: [parameters]
- Processing: [what it does]
- Output: [what it returns]
- Error handling: [error cases]

#### Tool 2: [name]
[Same structure]

### AG2 Integration (if applicable)

**Agent Modifications:**
- [Which agent gets new tools]
- [System message updates]
- [Workflow changes]

**Tool Registration:**
```python
bridge.register_tools_for_agent([agent], "[server]")
```

### Bioinformatics Integration (if applicable)

**External Tools:**
| Tool | Purpose | Installation | Version |
|------|---------|--------------|---------|
| [tool1] | [purpose] | [method] | [version] |

**BioPython Modules:**
- `from Bio import [module]` - [purpose]

### File Organization

```
mcp_servers/[server_name]/
├── [server]_mcp_server.py  # [new/modified]
├── tools/
│   └── [new_tool].py       # [new]
├── tests/
│   ├── test_[tool].py      # [new]
│   └── conftest.py         # [modified]
├── requirements.txt        # [updated]
├── Dockerfile              # [updated]
└── README.md               # [updated]
```

## Risk Assessment

### Technical Risks

**Risk 1: [Description]**
- **Probability**: High/Medium/Low
- **Impact**: High/Medium/Low
- **Mitigation**: [Strategy]

**Risk 2: [Description]**
[Same structure]

### Bioinformatics Risks

**Risk: Poor data quality**
- **Impact**: Unreliable results
- **Mitigation**: Robust QC, validation with known datasets

### Integration Risks

**Risk: MCP tool failures**
- **Impact**: Workflow breaks
- **Mitigation**: Comprehensive error handling, fallback strategies

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_[tool]_success():
    """Test successful operation."""
    result = await [tool](**valid_params)
    assert "Success" in result

@pytest.mark.asyncio
async def test_[tool]_error_handling():
    """Test error cases."""
    result = await [tool](**invalid_params)
    assert "Error" in result
```

### Integration Tests
- MCP client test
- AG2 agent tool calling test
- End-to-end workflow test

### Manual Testing
- MCP Inspector
- Interactive AG2 mode
- Real data validation

## Timeline

| Phase | Tasks | Estimated Time | Dependencies |
|-------|-------|----------------|--------------|
| Phase 1 | [count] | [X hours] | [None/prerequisites] |
| Phase 2 | [count] | [X hours] | Phase 1 |
| Phase 3 | [count] | [X hours] | Phase 2 |
| **Total** | **[count]** | **[X hours/days]** | |

## References

- [Relevant papers]
- [Tool documentation]
- [mdk_mcp related code]
- [External resources]

## Next Steps

1. **Immediate**: [First action]
2. **After approval**: [Second action]
3. **Before deployment**: [Final action]
```

### 2. [task-slug]-context.md

```markdown
# [Task Name] - Development Context

**Last Updated**: YYYY-MM-DD

## SESSION PROGRESS

### ✅ COMPLETED
- [Item 1]
- [Item 2]

### 🟡 IN PROGRESS
- [Current task]
- **Current file**: [file path]
- **Next**: [what to do next]

### ⏳ PENDING
- [Upcoming task 1]
- [Upcoming task 2]

### ⚠️ BLOCKERS
- [Blocker if any]

## Key Files

### New Files Created

**`mcp_servers/[server]/[file].py`**
- Purpose: [What it does]
- Status: [Complete/In progress/Pending]
- Dependencies: [What it depends on]

### Modified Files

**`mcp_servers/[server]/[file].py`**
- Changes: [What was modified]
- Reason: [Why]
- Status: [Complete/In progress]

### Test Files

**`mcp_servers/[server]/tests/test_[feature].py`**
- Coverage: [What's tested]
- Status: [Passing/Failing/Pending]

## Important Decisions

### Decision 1: [Topic]
**Date**: YYYY-MM-DD
**Decision**: [What was decided]
**Rationale**: [Why]
**Impact**: [What it affects]

### Decision 2: [Topic]
[Same structure]

## Technical Notes

### BioPython Integration
- [Specific patterns used]
- [Gotchas encountered]
- [Performance considerations]

### MCP Protocol
- [Tool naming choices]
- [Schema design decisions]
- [Error handling approach]

### AG2 Integration
- [Agent configuration]
- [Tool registration]
- [Workflow coordination]

## Dependencies

### Python Packages
```
package==version  # Purpose
```

### External Tools
- Tool: version - Purpose

### Docker Image
- Base: `python:3.11-slim`
- Additional: [software installed]

## Environment Configuration

```bash
# Required
NCBI_API_KEY=...         # For database access
GOOGLE_API_KEY=...       # For AG2 LLM

# Optional
LOG_LEVEL=INFO           # DEBUG for development
```

## Quick Resume

To continue development:

1. **Read this file** for current state
2. **Check SESSION PROGRESS** for what's done/pending
3. **Continue with**: [Specific next task]
4. **Files to modify**: [List]
5. **Tests to run**: `pytest mcp_servers/[server]/tests/`

## Known Issues

- [Issue 1]: [Description] → [Workaround]
- [Issue 2]: [Description] → [Status]

## Resources

- [Link to relevant documentation]
- [Link to test data]
- [Link to example implementations]
```

### 3. [task-slug]-tasks.md

```markdown
# [Task Name] - Task Checklist

**Last Updated**: YYYY-MM-DD

## Quick Status

- **Phase**: [Current phase]
- **Progress**: [X/Y] tasks complete
- **Status**: ⏳ Pending / 🟡 In Progress / ✅ Complete

## Phase 1: [Phase Name] - [Status]

### Setup
- [ ] Create directory structure
- [ ] Update requirements.txt
- [ ] Update Dockerfile
- [ ] Configure environment variables

### Core Implementation
- [ ] **Task 1**: [Description]
  - Files: [list]
  - Acceptance: [criteria]
  - Status: ⏳ Not started

- [ ] **Task 2**: [Description]
  - Files: [list]
  - Acceptance: [criteria]
  - Status: ⏳ Not started

## Phase 2: [Phase Name] - [Status]

### MCP Tool: [tool_name]
- [ ] Define tool schema
- [ ] Implement handler function
- [ ] Add to handle_list_tools()
- [ ] Add to handle_call_tool()
- [ ] Write unit tests
- [ ] Test with MCP Inspector
- [ ] Update README

### MCP Tool: [tool_name_2]
[Same structure]

## Phase 3: [Phase Name] - [Status]

### AG2 Integration
- [ ] Update agent system message
- [ ] Register new tools with agent
- [ ] Update workflow coordination
- [ ] Test agent tool calling

### Testing
- [ ] Unit tests pass (pytest)
- [ ] MCP integration tests pass
- [ ] Manual testing with MCP Inspector
- [ ] End-to-end workflow test
- [ ] Test coverage >80%

### Documentation
- [ ] Code docstrings complete
- [ ] README updated with examples
- [ ] CLAUDE.md updated (if major change)
- [ ] Test documentation complete

### Deployment
- [ ] Docker image builds
- [ ] Container starts successfully
- [ ] MCP server responds to tools/list
- [ ] Integration with AG2 works

## Next Actions

### Immediate (Today)
1. [Action 1]
2. [Action 2]

### Short Term (This Week)
1. [Action 1]
2. [Action 2]

### Before Completion
1. [Action 1]
2. [Action 2]

## Notes

- [Any important notes]
- [Decisions that affect task order]
- [Dependencies blocking progress]
```

## Context References

- Check `CLAUDE.md` for project overview
- Check `README.md` for mdk_mcp architecture
- Check `road_map.md` for phase roadmap
- Check existing MCP servers for patterns

## Remember

- Plans must be **actionable** - user can execute immediately
- Use **specific technical details** - exact parameters, file paths
- Consider **mdk_mcp patterns** - follow existing conventions
- Include **bioinformatics context** - why tools/parameters chosen
- Address **risks proactively** - don't just list them
- Provide **clear acceptance criteria** - how to know it's done

Your documentation enables seamless development continuation across sessions and context resets.

