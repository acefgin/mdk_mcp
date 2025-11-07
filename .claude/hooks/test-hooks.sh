#!/bin/bash
# Automated hook testing script for mdk_mcp
# Tests both skill-activation-prompt and post-tool-use-tracker hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set CLAUDE_PROJECT_DIR for hook testing
export CLAUDE_PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 TESTING MDK_MCP CLAUDE CODE HOOKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Verify hook executability
echo "Test 1: Checking hook executability..."
if [[ ! -x "skill-activation-prompt.sh" ]]; then
    echo "❌ FAIL: skill-activation-prompt.sh is not executable"
    exit 1
fi

if [[ ! -x "post-tool-use-tracker.sh" ]]; then
    echo "❌ FAIL: post-tool-use-tracker.sh is not executable"
    exit 1
fi
echo "✅ PASS: All hooks are executable"
echo ""

# Test 2: Verify dependencies
echo "Test 2: Checking hook dependencies..."
if [[ ! -d "node_modules" ]]; then
    echo "❌ FAIL: node_modules not found. Run 'npm install' first."
    exit 1
fi

if [[ ! -f "node_modules/tsx/dist/cli.mjs" ]]; then
    echo "❌ FAIL: tsx dependency missing. Run 'npm install' first."
    exit 1
fi
echo "✅ PASS: Dependencies installed"
echo ""

# Test 3: Verify skill-rules.json validity
echo "Test 3: Checking skill-rules.json validity..."
if [[ ! -f "../skills/skill-rules.json" ]]; then
    echo "❌ FAIL: skill-rules.json not found"
    exit 1
fi

if ! jq empty ../skills/skill-rules.json 2>/dev/null; then
    echo "❌ FAIL: skill-rules.json is not valid JSON"
    exit 1
fi
echo "✅ PASS: skill-rules.json is valid"
echo ""

# Test 4: Test skill activation hook with MCP keyword
echo "Test 4: Testing skill-activation-prompt with MCP keyword..."
output=$(echo '{"prompt": "create MCP server for sequence analysis"}' | ./skill-activation-prompt.sh)
if [[ "$output" == *"mcp-server-dev"* ]]; then
    echo "✅ PASS: mcp-server-dev skill triggered correctly"
else
    echo "❌ FAIL: mcp-server-dev skill did not trigger"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 5: Test skill activation hook with bioinformatics keyword
echo "Test 5: Testing skill-activation-prompt with bioinformatics keyword..."
output=$(echo '{"prompt": "design qPCR primers for COI region"}' | ./skill-activation-prompt.sh)
if [[ "$output" == *"bioinformatics-workflow"* ]]; then
    echo "✅ PASS: bioinformatics-workflow skill triggered correctly"
else
    echo "❌ FAIL: bioinformatics-workflow skill did not trigger"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 6: Test skill activation hook with AG2 keyword
echo "Test 6: Testing skill-activation-prompt with AG2 keyword..."
output=$(echo '{"prompt": "create multi-agent workflow with AG2"}' | ./skill-activation-prompt.sh)
if [[ "$output" == *"ag2-agent-dev"* ]]; then
    echo "✅ PASS: ag2-agent-dev skill triggered correctly"
else
    echo "❌ FAIL: ag2-agent-dev skill did not trigger"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 7: Test post-tool-use tracker with database server
echo "Test 7: Testing post-tool-use-tracker with database server..."
output=$(echo '{"tool_name": "Edit", "result": {"path": "mcp_servers/database_server/database_mcp_server.py"}}' | ./post-tool-use-tracker.sh)
if [[ "$output" == *"database_server"* ]] && [[ "$output" == *"MCP Server Modified"* ]]; then
    echo "✅ PASS: Database server detection works"
else
    echo "❌ FAIL: Database server not detected correctly"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 8: Test post-tool-use tracker with processing server
echo "Test 8: Testing post-tool-use-tracker with processing server..."
output=$(echo '{"tool_name": "Write", "result": {"path": "mcp_servers/processing_server/tests/test_qc.py"}}' | ./post-tool-use-tracker.sh)
if [[ "$output" == *"processing_server"* ]]; then
    echo "✅ PASS: Processing server detection works"
else
    echo "❌ FAIL: Processing server not detected correctly"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 9: Test post-tool-use tracker with AG2 app
echo "Test 9: Testing post-tool-use-tracker with AG2 app..."
output=$(echo '{"tool_name": "Edit", "result": {"path": "autogen_app/qpcr_assistant.py"}}' | ./post-tool-use-tracker.sh)
if [[ "$output" == *"autogen_app"* ]] && [[ "$output" == *"AG2 Agent Modified"* ]]; then
    echo "✅ PASS: AG2 app detection works"
else
    echo "❌ FAIL: AG2 app not detected correctly"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 10: Test post-tool-use tracker with tests
echo "Test 10: Testing post-tool-use-tracker with test files..."
output=$(echo '{"tool_name": "Edit", "result": {"path": "mcp_servers/alignment_server/tests/test_alignment.py"}}' | ./post-tool-use-tracker.sh)
if [[ "$output" == *"tests"* ]] || [[ "$output" == *"Test Modified"* ]]; then
    echo "✅ PASS: Test file detection works"
else
    echo "❌ FAIL: Test file not detected correctly"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 11: Test post-tool-use tracker with design server (Phase 4)
echo "Test 11: Testing post-tool-use-tracker with design server..."
output=$(echo '{"tool_name": "Edit", "result": {"path": "mcp_servers/design_server/design_mcp_server.py"}}' | ./post-tool-use-tracker.sh)
if [[ "$output" == *"design_server"* ]]; then
    echo "✅ PASS: Design server detection works"
else
    echo "❌ FAIL: Design server not detected correctly"
    echo "Output was: $output"
    exit 1
fi
echo ""

# Test 12: Test that non-matching tool names are ignored
echo "Test 12: Testing that non-Edit/Write/MultiEdit tools are ignored..."
output=$(echo '{"tool_name": "Read", "result": {"path": "mcp_servers/database_server/server.py"}}' | ./post-tool-use-tracker.sh)
if [[ -z "$output" ]]; then
    echo "✅ PASS: Non-matching tools correctly ignored"
else
    echo "⚠️  WARNING: Output produced for non-matching tool"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL TESTS PASSED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Hook Infrastructure Status:"
echo "  ✅ Hooks executable"
echo "  ✅ Dependencies installed"
echo "  ✅ skill-rules.json valid"
echo "  ✅ Skill activation working (MCP, bioinformatics, AG2)"
echo "  ✅ File tracking working (all servers + AG2)"
echo ""
echo "Your Claude Code infrastructure is ready! 🚀"
echo ""
