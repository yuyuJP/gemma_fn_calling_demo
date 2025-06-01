#!/usr/bin/env python3
"""
Master test runner for all test categories.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_sync_tests():
    """Run synchronous tests."""
    print("=" * 50)
    print("RUNNING SYNCHRONOUS TESTS")
    print("=" * 50)
    
    # Test Ollama connection
    print("\n1. Testing Ollama Connection:")
    try:
        from tests.test_ollama import test_ollama_connection
        if test_ollama_connection():
            print("✅ Ollama test PASSED")
            ollama_passed = True
        else:
            print("❌ Ollama test FAILED")
            ollama_passed = False
    except Exception as e:
        print(f"❌ Ollama test ERROR: {e}")
        ollama_passed = False
    
    # Test timezone functionality
    print("\n2. Testing Timezone Functionality:")
    try:
        from tests.test_timezone import test_timezone_normalization, test_misspelled_timezone
        test_timezone_normalization()
        test_misspelled_timezone()
        print("✅ Timezone tests PASSED")
        timezone_passed = True
    except Exception as e:
        print(f"❌ Timezone test FAILED: {e}")
        timezone_passed = False
    
    return ollama_passed and timezone_passed

async def run_async_tests():
    """Run asynchronous tests."""
    print("\n" + "=" * 50)
    print("RUNNING ASYNCHRONOUS TESTS")
    print("=" * 50)
    
    # Test MCP connection
    print("\n3. Testing MCP Connection:")
    try:
        from tests.test_mcp import test_mcp_connection
        if await test_mcp_connection():
            print("✅ MCP test PASSED")
            mcp_passed = True
        else:
            print("❌ MCP test FAILED")
            mcp_passed = False
    except Exception as e:
        print(f"❌ MCP test ERROR: {e}")
        mcp_passed = False
    
    # Test tool calling
    print("\n4. Testing Tool Calling:")
    try:
        from tests.test_tool_call import run_all_tests
        await run_all_tests()
        print("✅ Tool calling tests completed")
        tool_passed = True
    except Exception as e:
        print(f"❌ Tool calling test ERROR: {e}")
        tool_passed = False
    
    return mcp_passed and tool_passed

def run_integration_tests():
    """Run integration tests (requires server)."""
    print("\n" + "=" * 50)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 50)
    print("NOTE: These tests require the chat server to be running.")
    print("Start server with: python app/chat_server.py")
    
    try:
        from tests.test_retry import run_all_tests
        if run_all_tests():
            print("✅ Integration tests PASSED")
            return True
        else:
            print("❌ Integration tests FAILED")
            return False
    except Exception as e:
        print(f"❌ Integration test ERROR: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 GEMMA FUNCTION CALLING DEMO - TEST SUITE")
    print("=" * 60)
    
    # Run sync tests
    sync_passed = run_sync_tests()
    
    # Run async tests
    async_passed = await run_async_tests()
    
    # Run integration tests
    integration_passed = run_integration_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"Synchronous tests:  {'✅ PASSED' if sync_passed else '❌ FAILED'}")
    print(f"Asynchronous tests: {'✅ PASSED' if async_passed else '❌ FAILED'}")
    print(f"Integration tests:  {'✅ PASSED' if integration_passed else '❌ FAILED'}")
    
    all_passed = sync_passed and async_passed and integration_passed
    print(f"\nOverall result: {'🎉 ALL TESTS PASSED' if all_passed else '💥 SOME TESTS FAILED'}")
    
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())