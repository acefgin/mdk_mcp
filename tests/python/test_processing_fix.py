#!/usr/bin/env python3
"""
Test script to verify that processing MCP tools are now being called properly.

This script tests the fix for the issue where DatabaseAgent was terminating
after sequence retrieval without calling processing tools.

Expected behavior AFTER fix:
1. Retrieve sequences for target species
2. Retrieve sequences for off-target species  
3. Call processing tools (process_sequences or fasta_qc) for each species
4. Only terminate after processing is complete

Run this test:
    python test_processing_fix.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Add autogen_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'autogen_app'))

from qpcr_assistant import QPCRAssistant
from dotenv import load_dotenv

def load_config():
    """Load API configuration."""
    # Load environment variables
    env_file = os.path.join(os.path.dirname(__file__), "autogen_app", ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
    
    # Load config
    config_file = os.path.join(os.path.dirname(__file__), "autogen_app", "OAI_CONFIG_LIST.json")
    if not os.path.exists(config_file):
        print(f"ERROR: Config file not found: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config_list = json.load(f)
    
    # Resolve environment variables
    for config in config_list:
        api_key = config.get("api_key", "")
        if isinstance(api_key, str) and api_key.startswith("env:"):
            env_var = api_key[4:]
            actual_key = os.getenv(env_var)
            if actual_key:
                config["api_key"] = actual_key
            else:
                config["api_key"] = None
    
    # Filter out configs with missing API keys
    config_list = [cfg for cfg in config_list if cfg.get("api_key")]
    
    if not config_list:
        print("ERROR: No valid API keys found in config")
        sys.exit(1)
    
    return config_list

def analyze_results(log_file):
    """Analyze the workflow log to check if processing was called."""
    print("\n" + "="*80)
    print("ANALYZING WORKFLOW RESULTS")
    print("="*80 + "\n")
    
    if not os.path.exists(log_file):
        print(f"ERROR: Log file not found: {log_file}")
        return False
    
    with open(log_file, 'r') as f:
        log_data = json.load(f)
    
    tool_calls = log_data.get("tool_calls", [])
    
    print(f"Total tool calls: {len(tool_calls)}\n")
    
    # Categorize tool calls
    retrieval_calls = []
    processing_calls = []
    other_calls = []
    
    for tc in tool_calls:
        tool = tc.get("tool")
        if tool == "get_sequences":
            retrieval_calls.append(tc)
        elif tool in ["fasta_qc", "process_sequences", "dereplicate_sequences", 
                      "mask_low_complexity", "detect_chimeras"]:
            processing_calls.append(tc)
        else:
            other_calls.append(tc)
    
    print("Tool Call Breakdown:")
    print(f"  - Retrieval (get_sequences): {len(retrieval_calls)}")
    print(f"  - Processing: {len(processing_calls)}")
    print(f"  - Other: {len(other_calls)}")
    print()
    
    # Show detailed tool calls
    print("Detailed Tool Calls:")
    for i, tc in enumerate(tool_calls, 1):
        tool = tc.get("tool")
        success = "✓" if tc.get("success") else "✗"
        args = tc.get("arguments", {})
        taxon = args.get("taxon", args.get("fasta_file", "N/A"))
        print(f"  {i}. {success} {tool} - {taxon}")
    print()
    
    # Analyze termination
    termination_info = log_data.get("termination_info", {})
    term_reason = termination_info.get("termination_reason", "UNKNOWN")
    
    print(f"Termination Reason: {term_reason}")
    print(f"Total Messages: {log_data.get('statistics', {}).get('total_messages', 0)}")
    print()
    
    # Verdict
    print("="*80)
    print("TEST VERDICT:")
    print("="*80)
    
    success = True
    
    if len(retrieval_calls) == 0:
        print("❌ FAIL: No sequences were retrieved")
        success = False
    else:
        print(f"✓ PASS: {len(retrieval_calls)} retrieval calls made")
    
    if len(processing_calls) == 0:
        print("❌ FAIL: No processing tools were called")
        print("   This indicates the bug is NOT fixed - processing is still being skipped")
        success = False
    else:
        print(f"✓ PASS: {len(processing_calls)} processing calls made")
        print("   Processing tools are now being called correctly!")
    
    # Check that processing happened AFTER retrieval
    if retrieval_calls and processing_calls:
        last_retrieval_idx = max(i for i, tc in enumerate(tool_calls) if tc.get("tool") == "get_sequences")
        first_processing_idx = min(i for i, tc in enumerate(tool_calls) if tc.get("tool") in 
                                   ["fasta_qc", "process_sequences", "dereplicate_sequences", 
                                    "mask_low_complexity", "detect_chimeras"])
        
        if first_processing_idx > last_retrieval_idx:
            print("✓ PASS: Processing called AFTER retrieval (correct order)")
        else:
            print("⚠ WARNING: Processing called BEFORE all retrievals completed")
    
    print()
    
    if success:
        print("🎉 SUCCESS: The processing fix is working correctly!")
        print("   - Sequences retrieved ✓")
        print("   - Sequences processed ✓")
        print("   - Workflow completed in correct order ✓")
    else:
        print("❌ FAILURE: The processing bug is still present")
        print("   Please review the fix implementation")
    
    print()
    return success

def main():
    """Run the test."""
    print("\n" + "="*80)
    print("PROCESSING MCP TOOL CALLING FIX - VERIFICATION TEST")
    print("="*80 + "\n")
    
    print("This test will:")
    print("1. Initialize the qPCR Assistant with the fixed system messages")
    print("2. Run a workflow that requires sequence retrieval AND processing")
    print("3. Verify that processing tools are called before termination")
    print()
    
    # Load config
    print("Loading configuration...")
    config_list = load_config()
    print(f"✓ Loaded {len(config_list)} API configuration(s)")
    print()
    
    # Create assistant with test results directory (avoid permission issues)
    print("Initializing qPCR Assistant...")
    import tempfile
    test_results_dir = os.path.join(os.path.dirname(__file__), "test_results")
    os.makedirs(test_results_dir, exist_ok=True)
    assistant = QPCRAssistant(config_list, log_dir=test_results_dir, model_name="gpt-4o")
    
    try:
        assistant.initialize()
        print("✓ Assistant initialized successfully")
        print()
        
        # Test workflow
        print("="*80)
        print("RUNNING TEST WORKFLOW")
        print("="*80 + "\n")
        
        test_request = """I need to design a qPCR assay with the following specifications:

Target Species: Salmo salar
Off-Target Species: Oncorhynchus mykiss
Genomic Region: COI
Application: environmental monitoring

Please:
1. Retrieve sequences for the target species
2. Retrieve sequences for off-target species
3. Process the sequences through quality control
4. Provide a summary of the processed data
"""
        
        print("Test Request:")
        print(test_request)
        print()
        print("Running workflow...")
        print("-" * 80)
        
        # Run workflow
        messages = assistant.run_workflow(test_request)
        
        print("-" * 80)
        print(f"✓ Workflow completed with {len(messages)} messages")
        print()
        
        # Find the log file
        test_results_dir = os.path.join(os.path.dirname(__file__), "test_results")
        if not os.path.exists(test_results_dir):
            print(f"ERROR: Test results directory not found: {test_results_dir}")
            return False
            
        log_files = sorted([f for f in os.listdir(test_results_dir) if f.startswith("task_") and f.endswith(".json")])
        if not log_files:
            print("ERROR: No log files found")
            return False
        
        latest_log = os.path.join(test_results_dir, log_files[-1])
        print(f"Log file: {latest_log}")
        
        # Analyze results
        success = analyze_results(latest_log)
        
        return success
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return False
    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("Shutting down assistant...")
        assistant.shutdown()
        print("✓ Shutdown complete")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

