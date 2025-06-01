#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.mcp_client import create_mcp_client

async def test_tool_call():
    """Test basic tool calling functionality."""
    try:
        print("Creating MCP client...")
        client = await create_mcp_client("app/main.py")
        
        # Test a tool call request
        response = await client.chat_with_tools("What time is it in Tokyo?")
        print(f"Tokyo time response: {response}")
        
        assert response is not None
        assert len(response) > 0
        assert "Tokyo" in response or "JST" in response
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_misspelled_tool_call():
    """Test tool calling with misspelled timezone."""
    try:
        client = await create_mcp_client("app/main.py")
        response = await client.chat_with_tools("Time in T0kyo pls")  # zero instead of 'o'
        print(f"Misspelled Tokyo response: {response}")
        
        assert response is not None
        assert "Tokyo" in response or "JST" in response
        
        return True
        
    except Exception as e:
        print(f"Error in misspelled test: {e}")
        return False

async def test_joke_tool():
    """Test the random joke tool."""
    try:
        client = await create_mcp_client("app/main.py")
        response = await client.chat_with_tools("Tell me a joke")
        print(f"Joke response: {response}")
        
        assert response is not None
        assert len(response) > 0
        
        return True
        
    except Exception as e:
        print(f"Error in joke test: {e}")
        return False

async def run_all_tests():
    """Run all tool call tests."""
    tests = [
        ("Basic tool call", test_tool_call()),
        ("Misspelled timezone", test_misspelled_tool_call()),
        ("Joke tool", test_joke_tool())
    ]
    
    results = []
    for name, test_coro in tests:
        print(f"\n--- Running {name} ---")
        result = await test_coro
        results.append((name, result))
        print(f"{name}: {'PASSED' if result else 'FAILED'}")
    
    print(f"\n--- Test Results ---")
    for name, result in results:
        print(f"{name}: {'PASSED' if result else 'FAILED'}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())