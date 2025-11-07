#!/bin/bash
# Post-tool-use tracker for mdk_mcp Python project
# Tracks file changes after Edit/Write/MultiEdit operations

# Auto-detect project structure
detect_mdk_structure() {
    local file="$1"
    
    # Check if file is in mcp_servers
    if [[ "$file" == *"mcp_servers/"* ]]; then
        if [[ "$file" == *"/database_server/"* ]]; then
            echo "database_server"
        elif [[ "$file" == *"/processing_server/"* ]]; then
            echo "processing_server"
        elif [[ "$file" == *"/alignment_server/"* ]]; then
            echo "alignment_server"
        elif [[ "$file" == *"/design_server/"* ]]; then
            echo "design_server"
        else
            echo "mcp_server"
        fi
        return 0
    fi
    
    # Check if file is in autogen_app
    if [[ "$file" == *"autogen_app/"* ]]; then
        echo "autogen_app"
        return 0
    fi
    
    # Check if file is in docs
    if [[ "$file" == *"docs/"* ]]; then
        echo "docs"
        return 0
    fi
    
    # Check if file is in tests
    if [[ "$file" == *"tests/"* ]] || [[ "$file" == *"test_"* ]]; then
        echo "tests"
        return 0
    fi
    
    # Default: root
    echo "root"
    return 0
}

# Read JSON input from stdin
input=$(cat)

# Extract tool name and file path
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.result.path // .result.filePath // empty')

# Only process Edit, Write, and MultiEdit operations
if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" && "$tool_name" != "MultiEdit" ]]; then
    exit 0
fi

# Skip if no file path
if [[ -z "$file_path" || "$file_path" == "null" ]]; then
    exit 0
fi

# Detect which part of mdk_mcp was modified
section=$(detect_mdk_structure "$file_path")

# Output tracking message
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 FILE CHANGE TRACKED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "File: $file_path"
echo "Section: $section"
echo ""

# Provide context-specific reminders
case "$section" in
    database_server|processing_server|alignment_server|design_server)
        echo "💡 MCP Server Modified:"
        echo "  - Rebuild container: docker-compose build $section"
        echo "  - Test with MCP Inspector"
        echo "  - Update tests if tool schema changed"
        ;;
    autogen_app)
        echo "💡 AG2 Agent Modified:"
        echo "  - Test agent collaboration"
        echo "  - Verify tool registration"
        echo "  - Check workflow coordination"
        ;;
    tests)
        echo "💡 Test Modified:"
        echo "  - Run pytest to verify"
        echo "  - Check test coverage"
        ;;
    docs)
        echo "💡 Documentation Modified:"
        echo "  - Verify formatting"
        echo "  - Update related docs if needed"
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0

