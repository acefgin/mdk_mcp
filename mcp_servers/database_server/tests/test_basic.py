#!/usr/bin/env python3
"""
Basic tests for the database MCP server.
"""

import json
import time
import requests
import subprocess
import sys
from typing import Dict, Any

def test_server_health():
    """Test if the server is responding to health checks."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server health check passed")
            return True
        else:
            print("❌ Server health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_mcp_tools_list():
    """Test listing available MCP tools."""
    try:
        # This would typically be done through MCP protocol
        # For now, we'll test if the server is running
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ MCP server is accessible")
            return True
        else:
            print("❌ MCP server not accessible")
            return False
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def run_basic_tests():
    """Run all basic tests."""
    print("🧪 Running basic tests for ndiag-database-server")
    print("=" * 50)
    
    tests = [
        ("Server Health Check", test_server_health),
        ("MCP Tools Access", test_mcp_tools_list),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = run_basic_tests()
    sys.exit(exit_code)
