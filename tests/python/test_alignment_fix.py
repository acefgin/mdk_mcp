#!/usr/bin/env python3
"""
Quick test to verify alignment tools are properly registered in AG2 agents.
This test checks that the fix for the infinite loop issue is working.
"""
import sys
import os
sys.path.insert(0, '/home/raycifeng/mdk_mcp/autogen_app')

from autogen_mcp_bridge import create_autogen_functions

def test_alignment_tools_registered():
    """Verify that alignment tools are included in function schemas."""
    print("Testing alignment tool registration...")

    # Test 1: Check that database and processing tools exist
    db_functions = create_autogen_functions(["database"])
    print(f"✓ Database functions: {len(db_functions)} tools")
    db_names = [f['name'] for f in db_functions]
    print(f"  Tools: {db_names}")
    assert "get_sequences" in db_names, "Database tools missing!"

    proc_functions = create_autogen_functions(["processing"])
    print(f"✓ Processing functions: {len(proc_functions)} tools")
    proc_names = [f['name'] for f in proc_functions]
    print(f"  Tools: {proc_names}")
    assert "process_sequences" in proc_names, "Processing tools missing!"

    # Test 2: Check that alignment tools are NOW included (this was the bug!)
    align_functions = create_autogen_functions(["alignment"])
    print(f"✓ Alignment functions: {len(align_functions)} tools")
    align_names = [f['name'] for f in align_functions]
    print(f"  Tools: {align_names}")

    expected_alignment_tools = [
        "align_sequences",
        "process_alignment",
        "build_phylogeny",
        "calculate_distances",
        "align_and_analyze"
    ]

    for tool in expected_alignment_tools:
        assert tool in align_names, f"Alignment tool '{tool}' missing!"

    print(f"✓ All {len(expected_alignment_tools)} alignment tools found!")

    # Test 3: Check combined function list (what AnalystAgent will receive)
    combined_functions = create_autogen_functions(["processing", "alignment"])
    combined_names = [f['name'] for f in combined_functions]
    print(f"✓ Combined (processing + alignment): {len(combined_functions)} tools")
    print(f"  Tools: {combined_names}")

    # Verify AnalystAgent has all processing + alignment tools (10 total)
    expected_count = 5 + 5  # 5 processing + 5 alignment
    assert len(combined_functions) == expected_count, \
        f"Expected {expected_count} tools, got {len(combined_functions)}"

    print("\n" + "="*60)
    print("✅ SUCCESS! All alignment tools are properly registered.")
    print("="*60)
    print("\nThe infinite loop bug should be FIXED:")
    print("  • AnalystAgent now has access to 10 tools (5 processing + 5 alignment)")
    print("  • Workflow can progress: Retrieve → Process → Align → Phylogeny")
    print("  • No more getting stuck after processing step")
    print("\nRoot cause was: alignment function schemas were missing from")
    print("create_autogen_functions() in autogen_mcp_bridge.py")

    return True

if __name__ == "__main__":
    try:
        test_alignment_tools_registered()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
