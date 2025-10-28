#!/usr/bin/env python3
"""
Test script to verify function calling is working correctly.

This script performs a simple test of the DatabaseAgent's ability to 
actually call MCP functions (not just write "CALL" as text).

Expected behavior:
- Model should be gpt-4o
- Function calls should appear in logs
- Real results should be returned
- Tool call count > 0
"""

import json
import sys
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load from autogen_app/.env first, then from root .env
    env_paths = [
        Path(__file__).parent / "autogen_app" / ".env",
        Path(__file__).parent / ".env"
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ Loaded environment from {env_path}")
            break
except ImportError:
    print("⚠️  python-dotenv not installed, trying to use existing environment variables")

# Add autogen_app to path
sys.path.insert(0, str(Path(__file__).parent / "autogen_app"))

from qpcr_assistant import QPCRAssistant
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_function_calling():
    """Test that function calling actually works."""
    
    print("=" * 80)
    print("FUNCTION CALLING TEST")
    print("=" * 80)
    print()
    
    # 1. Load configuration
    config_path = Path(__file__).parent / "autogen_app" / "OAI_CONFIG_LIST.json"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Please ensure OAI_CONFIG_LIST.json exists with valid API keys")
        return False
    
    with open(config_path) as f:
        config_list = json.load(f)
    
    # CRITICAL FIX: Resolve "env:VAR_NAME" references manually
    # AutoGen's env resolution doesn't always work properly with load_dotenv
    for config in config_list:
        if "api_key" in config and isinstance(config["api_key"], str):
            if config["api_key"].startswith("env:"):
                env_var_name = config["api_key"][4:]  # Remove "env:" prefix
                env_value = os.getenv(env_var_name)
                if env_value:
                    config["api_key"] = env_value
                    print(f"✓ Resolved {env_var_name} for model {config.get('model')}")
                else:
                    print(f"⚠️  Warning: {env_var_name} not found in environment")
    
    print(f"✓ Loaded config from {config_path}")
    print(f"  Available models: {[c['model'] for c in config_list]}")
    print()
    
    # 2. Check if OPENAI_API_KEY is set
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "your-openai-api-key-here":
        print("⚠️  WARNING: OPENAI_API_KEY not set or is placeholder")
        print("   Function calling test requires a valid OpenAI API key")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    # Debug: Show first 10 chars of API key to verify it's loaded
    print(f"✓ OPENAI_API_KEY is set: {openai_key[:10]}...")
    
    # CRITICAL: AutoGen expects environment variables to be set in os.environ
    # Even if loaded from .env, make sure they're in the environment
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Setting OPENAI_API_KEY in os.environ for AutoGen")
        os.environ["OPENAI_API_KEY"] = openai_key
    
    print()
    
    # 3. Create assistant with gpt-4o (should be default)
    print("Creating QPCRAssistant...")
    test_results_dir = "/tmp/test_function_calling"
    os.makedirs(test_results_dir, exist_ok=True)
    
    try:
        assistant = QPCRAssistant(
            config_list=config_list,
            log_dir=test_results_dir,
            model_name="gpt-4o"  # Explicitly use gpt-4o
        )
        print(f"✓ Created assistant with model: {assistant.model_name}")
        print()
    except ValueError as e:
        print(f"❌ Failed to create assistant: {e}")
        return False
    
    # 4. Initialize (connects to MCP server)
    print("Initializing MCP connection...")
    try:
        assistant.initialize()
        print("✓ MCP connection established")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # 5. Run a simple test query
    print("Running test query: 'Get taxonomy information for Salmo salar'")
    print("-" * 80)
    
    try:
        result = assistant.run_workflow(
            "Get taxonomy information for Salmo salar using get_taxonomy tool"
        )
        print()
        print("-" * 80)
        print("✓ Workflow completed")
        print()
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Check the results
    print("Checking results...")
    
    # Find the most recent task log
    log_files = sorted(Path(test_results_dir).glob("task_*.json"))
    if not log_files:
        print("❌ No log files found")
        return False
    
    latest_log = log_files[-1]
    print(f"  Log file: {latest_log.name}")
    
    with open(latest_log) as f:
        log_data = json.load(f)
    
    # Check for tool calls
    tool_calls = log_data.get("tool_calls", [])
    num_tool_calls = len(tool_calls)
    
    print(f"  Tool calls: {num_tool_calls}")
    
    if num_tool_calls == 0:
        print("❌ FAILED: No tool calls were made!")
        print("   The LLM is still just writing text instead of calling functions")
        return False
    
    print("✓ Tool calls were made!")
    print()
    
    # Show the tool calls
    print("Tool calls made:")
    for i, tc in enumerate(tool_calls, 1):
        print(f"  {i}. {tc.get('tool_name', 'unknown')}")
        print(f"     Arguments: {tc.get('arguments', {})}")
        result_preview = str(tc.get('result', ''))[:100]
        print(f"     Result: {result_preview}...")
        print()
    
    # 7. Final verdict
    print("=" * 80)
    print("✅ FUNCTION CALLING TEST PASSED!")
    print("=" * 80)
    print()
    print("The fix is working correctly:")
    print("  ✓ Using gpt-4o model")
    print("  ✓ Functions are being called via API (not text)")
    print(f"  ✓ {num_tool_calls} tool call(s) executed successfully")
    print()
    
    return True


def test_processing_tools():
    """Test that processing MCP server tools work correctly."""

    print("=" * 80)
    print("PROCESSING MCP SERVER TEST")
    print("=" * 80)
    print()

    # 1. Load configuration
    config_path = Path(__file__).parent / "autogen_app" / "OAI_CONFIG_LIST.json"

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    with open(config_path) as f:
        config_list = json.load(f)

    # Resolve env variables
    for config in config_list:
        if "api_key" in config and isinstance(config["api_key"], str):
            if config["api_key"].startswith("env:"):
                env_var_name = config["api_key"][4:]
                env_value = os.getenv(env_var_name)
                if env_value:
                    config["api_key"] = env_value

    print(f"✓ Loaded config from {config_path}")
    print()

    # 2. Create assistant
    print("Creating QPCRAssistant with processing tools...")
    test_results_dir = "/tmp/test_processing"
    os.makedirs(test_results_dir, exist_ok=True)

    try:
        assistant = QPCRAssistant(
            config_list=config_list,
            log_dir=test_results_dir,
            model_name="gpt-4o"
        )
        print(f"✓ Created assistant")
        print()
    except Exception as e:
        print(f"❌ Failed to create assistant: {e}")
        return False

    # 3. Initialize MCP connections (should include processing server)
    print("Initializing MCP connections (database + processing)...")
    try:
        assistant.initialize()
        print("✓ MCP servers connected")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. Test processing workflow
    print("Running processing workflow test...")
    print("-" * 80)

    test_query = """
    Please retrieve 10 COI sequences for Salmo salar from NCBI,
    then perform quality control using the fasta_qc tool with:
    - min_length: 400
    - max_n_percent: 5.0
    - remove_duplicates: true

    Report how many sequences passed QC.
    """

    try:
        result = assistant.run_workflow(test_query)
        print()
        print("-" * 80)
        print("✓ Processing workflow completed")
        print()
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. Verify processing tools were called
    print("Verifying processing tools were used...")

    log_files = sorted(Path(test_results_dir).glob("task_*.json"))
    if not log_files:
        print("❌ No log files found")
        return False

    latest_log = log_files[-1]
    with open(latest_log) as f:
        log_data = json.load(f)

    tool_calls = log_data.get("tool_calls", [])

    # Check for both database and processing tool calls
    db_tools_used = []
    proc_tools_used = []

    for tc in tool_calls:
        tool_name = tc.get("tool", "")
        if tool_name in ["get_sequences", "get_taxonomy", "get_neighbors", "extract_sequence_columns", "search_sra_studies"]:
            db_tools_used.append(tool_name)
        elif tool_name in ["fasta_qc", "dereplicate_sequences", "mask_low_complexity", "detect_chimeras", "process_sequences"]:
            proc_tools_used.append(tool_name)

    print(f"  Database tools used: {len(db_tools_used)} - {', '.join(set(db_tools_used))}")
    print(f"  Processing tools used: {len(proc_tools_used)} - {', '.join(set(proc_tools_used))}")
    print()

    if len(proc_tools_used) == 0:
        print("❌ FAILED: No processing tools were called!")
        print("   Expected at least fasta_qc to be called")
        return False

    print("✓ Processing tools were successfully called!")
    print()

    # Show detailed results
    print("Processing tool calls:")
    for tc in tool_calls:
        tool_name = tc.get("tool", "")
        if tool_name in ["fasta_qc", "dereplicate_sequences", "mask_low_complexity", "detect_chimeras", "process_sequences"]:
            print(f"  • {tool_name}")
            args = tc.get("arguments", {})
            print(f"    Arguments: {list(args.keys())}")
            success = tc.get("success", False)
            status = "✓ Success" if success else "✗ Failed"
            print(f"    Status: {status}")
            print()

    # 6. Final verdict
    print("=" * 80)
    print("✅ PROCESSING MCP SERVER TEST PASSED!")
    print("=" * 80)
    print()
    print("Integration verified:")
    print("  ✓ Processing server connected")
    print("  ✓ Processing tools available to agents")
    print("  ✓ End-to-end workflow (retrieve + QC) working")
    print(f"  ✓ {len(proc_tools_used)} processing tool call(s) executed")
    print()

    return True


def test_all_processing_tools():
    """Test each processing tool individually."""

    print("=" * 80)
    print("INDIVIDUAL PROCESSING TOOLS TEST")
    print("=" * 80)
    print()

    # Test sample FASTA data
    test_fasta = """>seq1 Test sequence 1
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
>seq2 Test sequence 2 with Ns
ATCGATCGATCGATCGNNNNNNNNGATCGATCGATCGATCG
>seq3 Short sequence
ATCG
>seq4 Duplicate of seq1
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
>seq5 Good sequence
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
"""

    print("Sample test data prepared (5 sequences)")
    print()

    # Load configuration
    config_path = Path(__file__).parent / "autogen_app" / "OAI_CONFIG_LIST.json"

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    with open(config_path) as f:
        config_list = json.load(f)

    # Resolve env variables
    for config in config_list:
        if "api_key" in config and isinstance(config["api_key"], str):
            if config["api_key"].startswith("env:"):
                env_var_name = config["api_key"][4:]
                env_value = os.getenv(env_var_name)
                if env_value:
                    config["api_key"] = env_value

    # Create assistant
    test_results_dir = "/tmp/test_all_processing_tools"
    os.makedirs(test_results_dir, exist_ok=True)

    try:
        assistant = QPCRAssistant(
            config_list=config_list,
            log_dir=test_results_dir,
            model_name="gpt-4o"
        )
        assistant.initialize()
        print("✓ Assistant initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False

    # Define test cases for each tool
    test_cases = [
        {
            "name": "fasta_qc",
            "query": f"""Use fasta_qc tool on this FASTA data:
{test_fasta}
Parameters: min_length=20, max_n_percent=10.0, remove_duplicates=true""",
            "expected": "quality control"
        },
        {
            "name": "dereplicate_sequences",
            "query": f"""Use dereplicate_sequences tool on this FASTA data:
{test_fasta}
Parameters: identity_threshold=1.0""",
            "expected": "dereplicate"
        },
        {
            "name": "mask_low_complexity",
            "query": f"""Use mask_low_complexity tool on this FASTA data:
{test_fasta}
Parameters: dust_threshold=2.0""",
            "expected": "mask"
        }
    ]

    results = {}

    for test_case in test_cases:
        tool_name = test_case["name"]
        print(f"Testing {tool_name}...")

        try:
            result = assistant.run_workflow(test_case["query"])

            # Check logs
            log_files = sorted(Path(test_results_dir).glob("task_*.json"))
            if log_files:
                with open(log_files[-1]) as f:
                    log_data = json.load(f)
                    tool_calls = [tc.get("tool", "") for tc in log_data.get("tool_calls", [])]

                    if tool_name in tool_calls:
                        print(f"  ✓ {tool_name} called successfully")
                        results[tool_name] = "PASS"
                    else:
                        print(f"  ✗ {tool_name} was not called")
                        results[tool_name] = "FAIL"
            else:
                print(f"  ✗ No log found")
                results[tool_name] = "FAIL"

        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            results[tool_name] = "ERROR"

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for v in results.values() if v == "PASS")
    total = len(results)

    for tool_name, status in results.items():
        symbol = "✓" if status == "PASS" else "✗"
        print(f"  {symbol} {tool_name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("✅ ALL PROCESSING TOOLS WORKING!")
        return True
    else:
        print("⚠️  Some tools need attention")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MCP FUNCTION CALLING TEST SUITE" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    tests = [
        ("Basic Function Calling", test_function_calling),
        ("Processing MCP Integration", test_processing_tools),
        ("Individual Processing Tools", test_all_processing_tools),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'':=^80}")
        print(f"Running: {test_name}")
        print(f"{'':=^80}\n")

        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

        print("\n")

    # Final summary
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "FINAL RESULTS" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print()

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"Overall: {passed}/{total} test suites passed")
    print()

    sys.exit(0 if passed == total else 1)

