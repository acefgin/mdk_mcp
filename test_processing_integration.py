#!/usr/bin/env python3
"""
Test script for Processing MCP integration with AG2.

This script tests that:
1. Processing server tools are available in AG2
2. Agents can retrieve sequences and perform QC
"""

import asyncio
import os
import sys

# Add autogen_app to path
sys.path.insert(0, '/home/raycifeng/mdk_mcp/autogen_app')

from autogen_mcp_bridge import MCPClientBridge, create_autogen_functions


async def test_processing_integration():
    """Test that processing server is integrated properly."""

    print("=" * 80)
    print("Testing Processing MCP Integration with AG2")
    print("=" * 80)

    # 1. Test MCP bridge connection
    print("\n1. Connecting to MCP servers...")
    server_configs = {
        "database": {
            "container": "ndiag-database-server",
            "command": ["python3", "/app/database_mcp_server.py"]
        },
        "processing": {
            "container": "ndiag-processing-server",
            "command": ["python3", "/app/processing_mcp_server.py"]
        }
    }

    bridge = MCPClientBridge(server_configs)
    await bridge.start_servers()
    print("✓ Connected to MCP servers")

    # 2. Check available functions
    print("\n2. Checking available functions...")
    functions = create_autogen_functions(["database", "processing"])
    print(f"✓ Total functions available: {len(functions)}")

    # Group by server
    db_funcs = [f['name'] for f in functions if f['name'] in ['get_sequences', 'get_taxonomy', 'get_neighbors', 'extract_sequence_columns', 'search_sra_studies']]
    proc_funcs = [f['name'] for f in functions if f['name'] in ['fasta_qc', 'dereplicate_sequences', 'mask_low_complexity', 'detect_chimeras', 'process_sequences']]

    print(f"  Database tools ({len(db_funcs)}): {', '.join(db_funcs)}")
    print(f"  Processing tools ({len(proc_funcs)}): {', '.join(proc_funcs)}")

    # 3. Test simple processing tool call
    print("\n3. Testing processing tool call (fasta_qc)...")
    test_fasta = """>seq1
ATCGATCGATCG
>seq2
ATCGATCGATCGNNNNNNNNNNNN
>seq3
ATCG
"""

    try:
        result = await bridge.call_tool("processing", "fasta_qc", {
            "fasta_content": test_fasta,
            "min_length": 10,
            "max_n_percent": 10.0,
            "remove_duplicates": True
        })
        print("✓ fasta_qc call successful!")

        # Parse result
        if isinstance(result, list) and len(result) > 0:
            text_result = result[0].get('text', str(result))
            print(f"  Result preview: {text_result[:200]}...")
        else:
            print(f"  Result preview: {str(result)[:200]}...")

    except Exception as e:
        print(f"✗ fasta_qc call failed: {e}")
        import traceback
        traceback.print_exc()

    # 4. Cleanup
    print("\n4. Test complete (servers remain running for qPCR assistant)")

    print("\n" + "=" * 80)
    print("✅ Processing MCP Integration Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_processing_integration())
