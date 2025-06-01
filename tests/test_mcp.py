#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.mcp_client import create_mcp_client

async def test_mcp_connection():
    """Test MCP client connection and tool discovery."""
    try:
        print("Creating MCP client...")
        client = await create_mcp_client("app/main.py")
        print(f"Client created successfully!")
        print(f"Available tools: {list(client.available_tools.keys())}")
        
        # Test a simple chat
        response = await client.chat_with_tools("Hello!")
        print(f"Chat response: {response}")
        
        assert client.available_tools is not None
        assert len(client.available_tools) > 0
        assert response is not None
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if asyncio.run(test_mcp_connection()):
        print("MCP test PASSED")
    else:
        print("MCP test FAILED")