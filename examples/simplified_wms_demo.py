#!/usr/bin/env python3
"""
Simplified WMS demo using fewer, better-named tools for natural language interaction.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the MCP client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp_client import MCPOllamaClient


async def test_natural_questions():
    """Test natural questions with simplified tool set."""
    
    # Use the cleaned main server (now has only essential tools)
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "main.py")
    client = MCPOllamaClient(server_path)
    
    print("🏭 Simplified WMS Demo - Natural Language")
    print("=" * 50)
    print("Using only 5 essential tools with clear purposes")
    
    try:
        # Connect to the simplified MCP server
        tools = await client.connect()
        print(f"✅ Connected to simplified server with {len(tools)} tools")
        
        # Show available tools
        print("\n📋 Available tools:")
        for name, info in tools.items():
            print(f"   - {name}: {info['description']}")
        
        # Natural questions to test date handling
        questions = [
            # "List the top 3 customers and analyze their behavior."
            # "Which products were most popular in September 2023?",
            # "How are sales trending through April and September 2023?",
            "List 5 most popular items on September 2023."
        ]
        
        print(f"\n🤔 Testing natural language questions...")
        print("-" * 50)
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ Question {i}: {question}")
            print("🤖 AI Response:")
            
            try:
                response = await client.chat_with_tools(question)
                print(f"   {response}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            if i < len(questions):
                print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        print("\n🔌 Simplified demo complete")


async def main():
    """Main function."""
    print("🎯 Testing Natural Language with Simplified Tool Set")
    print()
    
    await test_natural_questions()


if __name__ == "__main__":
    asyncio.run(main())