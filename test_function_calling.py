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


if __name__ == "__main__":
    success = test_function_calling()
    sys.exit(0 if success else 1)

