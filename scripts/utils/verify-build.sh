#!/bin/bash
##################################################
# Build Verification Script
# Verifies npm run build:workspace completed successfully
##################################################

set -e

echo "🔍 Verifying Build System"
echo "═══════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

WORKSPACE_DIR="workspace"
ERRORS=0

# Check function
check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✓${NC} $1"
  else
    echo -e "${RED}✗${NC} $1 (MISSING)"
    ((ERRORS++))
  fi
}

check_dir() {
  if [ -d "$1" ]; then
    echo -e "${GREEN}✓${NC} $1/"
  else
    echo -e "${RED}✗${NC} $1/ (MISSING)"
    ((ERRORS++))
  fi
}

# 1. Check MCP Client Library
echo "1️⃣  MCP Client Library"
check_file "$WORKSPACE_DIR/lib/mcp-client.ts"
check_file "$WORKSPACE_DIR/lib/mcp-client.js"
check_file "$WORKSPACE_DIR/lib/mcp-client.d.ts"
echo ""

# 2. Check Server Directories
echo "2️⃣  Server Directories"
check_dir "$WORKSPACE_DIR/servers/database"
check_dir "$WORKSPACE_DIR/servers/processing"
check_dir "$WORKSPACE_DIR/servers/alignment"
check_dir "$WORKSPACE_DIR/servers/design"
check_dir "$WORKSPACE_DIR/servers/validation"
echo ""

# 3. Check Index Files
echo "3️⃣  Server Index Files (Barrel Exports)"
check_file "$WORKSPACE_DIR/servers/database/index.ts"
check_file "$WORKSPACE_DIR/servers/database/index.js"
check_file "$WORKSPACE_DIR/servers/processing/index.ts"
check_file "$WORKSPACE_DIR/servers/processing/index.js"
check_file "$WORKSPACE_DIR/servers/alignment/index.ts"
check_file "$WORKSPACE_DIR/servers/alignment/index.js"
check_file "$WORKSPACE_DIR/servers/design/index.ts"
check_file "$WORKSPACE_DIR/servers/design/index.js"
check_file "$WORKSPACE_DIR/servers/validation/index.ts"
check_file "$WORKSPACE_DIR/servers/validation/index.js"
echo ""

# 4. Check MCP Server
echo "4️⃣  Main MCP Server"
check_file "$WORKSPACE_DIR/mcp-server.ts"
check_file "$WORKSPACE_DIR/mcp-server.js"
echo ""

# 5. Count generated files
echo "5️⃣  File Counts"

TS_TOOL_COUNT=$(find "$WORKSPACE_DIR/servers" -type f -name "*.ts" ! -name "index.ts" ! -name "README.md" | wc -l)
JS_TOOL_COUNT=$(find "$WORKSPACE_DIR/servers" -type f -name "*.js" ! -name "index.js" | wc -l)
TOTAL_JS=$(find "$WORKSPACE_DIR" -name "*.js" | wc -l)

echo -e "  • TypeScript tool modules: ${GREEN}$TS_TOOL_COUNT${NC} (expected: 34)"
echo -e "  • JavaScript tool modules: ${GREEN}$JS_TOOL_COUNT${NC} (expected: 34)"
echo -e "  • Total JavaScript files: ${GREEN}$TOTAL_JS${NC} (expected: 41)"

if [ "$TS_TOOL_COUNT" -ne 34 ]; then
  echo -e "  ${RED}✗ Incorrect TypeScript tool count${NC}"
  ((ERRORS++))
fi

if [ "$JS_TOOL_COUNT" -ne 34 ]; then
  echo -e "  ${RED}✗ Incorrect JavaScript tool count${NC}"
  ((ERRORS++))
fi

echo ""

# 6. Verify no nested directories
echo "6️⃣  Directory Structure"
if [ -d "$WORKSPACE_DIR/servers/servers" ]; then
  echo -e "  ${RED}✗ Nested servers/ directory found (build error)${NC}"
  ((ERRORS++))
else
  echo -e "  ${GREEN}✓${NC} No nested directories"
fi

if [ -d "$WORKSPACE_DIR/servers/lib" ]; then
  echo -e "  ${RED}✗ Nested lib/ directory found (build error)${NC}"
  ((ERRORS++))
else
  echo -e "  ${GREEN}✓${NC} No nested lib/ directory"
fi

echo ""

# 7. Test module imports
echo "7️⃣  Module Import Tests"

# Test mcp-client import
if node -e "import('./workspace/lib/mcp-client.js').then(() => console.log('✓ mcp-client.js')).catch(e => { console.error('✗ mcp-client.js:', e.message); process.exit(1); })" 2>&1 | grep -q "✓"; then
  echo -e "  ${GREEN}✓${NC} mcp-client.js imports successfully"
else
  echo -e "  ${RED}✗${NC} mcp-client.js import failed"
  ((ERRORS++))
fi

# Test each server module
for server in database processing alignment design validation; do
  if node -e "import('./workspace/servers/$server/index.js').then(m => { 
    const exports = Object.keys(m); 
    if (exports.length > 0) {
      console.log('✓ $server: ' + exports.length + ' exports');
    } else {
      console.error('✗ $server: no exports');
      process.exit(1);
    }
  }).catch(e => { 
    console.error('✗ $server:', e.message); 
    process.exit(1); 
  })" 2>&1 | grep -q "✓"; then
    EXPORT_COUNT=$(node -e "import('./workspace/servers/$server/index.js').then(m => console.log(Object.keys(m).length))" 2>&1)
    echo -e "  ${GREEN}✓${NC} $server/index.js imports successfully ($EXPORT_COUNT exports)"
  else
    echo -e "  ${RED}✗${NC} $server/index.js import failed"
    ((ERRORS++))
  fi
done

echo ""

# 8. Test MCP server startup
echo "8️⃣  MCP Server Startup Test"

timeout 2s node "$WORKSPACE_DIR/mcp-server.js" 2>&1 | head -5 > /tmp/mcp-test.log || true

if grep -q "mdk-mcp-typescript" /tmp/mcp-test.log && grep -q "34" /tmp/mcp-test.log; then
  echo -e "  ${GREEN}✓${NC} Server starts successfully"
  echo -e "  ${GREEN}✓${NC} Reports 34 tools"
  cat /tmp/mcp-test.log | sed 's/^/    /'
else
  echo -e "  ${RED}✗${NC} Server startup failed or wrong tool count"
  cat /tmp/mcp-test.log | sed 's/^/    /'
  ((ERRORS++))
fi

rm -f /tmp/mcp-test.log

echo ""

# 9. Summary
echo "═══════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
  echo -e "${GREEN}✅ Build Verification PASSED${NC}"
  echo ""
  echo "All components verified successfully:"
  echo "  • MCP client library compiled"
  echo "  • 34 tool modules generated and compiled"
  echo "  • 5 server modules with barrel exports"
  echo "  • Main MCP server compiled"
  echo "  • All modules import successfully"
  echo "  • Server starts and reports 34 tools"
  echo ""
  echo "🚀 Ready for Claude Desktop integration!"
  exit 0
else
  echo -e "${RED}❌ Build Verification FAILED${NC}"
  echo ""
  echo "Found $ERRORS error(s). Please:"
  echo "  1. Run: npm run build:workspace"
  echo "  2. Check for compilation errors"
  echo "  3. Re-run this script"
  exit 1
fi

