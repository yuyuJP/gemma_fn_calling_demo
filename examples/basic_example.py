#!/usr/bin/env python3
"""
Basic Gemma 3 Function Calling Example

This is the simplest possible example showing how Gemma 3 can call functions.
Perfect for understanding the core concept without distractions.

Run: python examples/basic_example.py
"""

import ollama
import json
from datetime import datetime

def get_time() -> str:
    """Simple function that returns current time."""
    return f"Current time: {datetime.now().strftime('%H:%M:%S')}"

def add_numbers(a: int, b: int) -> str:
    """Simple function that adds two numbers."""
    return f"{a} + {b} = {a + b}"

# System prompt that teaches Gemma 3 about function calling
SYSTEM_PROMPT = """You can call these functions:

1. get_time() - Returns current time
2. add_numbers(a, b) - Adds two numbers

To call a function, respond with JSON in this format:
{"tool_call": {"name": "function_name", "arguments": {"param": "value"}}}

Examples:
- {"tool_call": {"name": "get_time", "arguments": {}}}
- {"tool_call": {"name": "add_numbers", "arguments": {"a": 5, "b": 3}}}
"""

def extract_function_call(response: str):
    """Extract function call from Gemma's response."""
    try:
        if '{"tool_call":' in response:
            start = response.find('{"tool_call":')
            # Simple JSON extraction - find matching braces
            brace_count = 0
            end = start
            for i in range(start, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i
                        break
            
            json_str = response[start:end + 1]
            return json.loads(json_str)["tool_call"]
    except:
        pass
    return None

def execute_function(name: str, args: dict):
    """Execute the requested function."""
    if name == "get_time":
        return get_time()
    elif name == "add_numbers":
        return add_numbers(args.get("a", 0), args.get("b", 0))
    else:
        return f"Unknown function: {name}"

def simple_chat(user_message: str):
    """Simple chat with function calling."""
    client = ollama.Client()
    
    # Step 1: Send user message with system prompt
    response = client.chat(
        model="gemma3:12b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    
    gemma_response = response["message"]["content"]
    print(f"Gemma says: {gemma_response}")
    
    # Step 2: Check if Gemma wants to call a function
    function_call = extract_function_call(gemma_response)
    
    if function_call:
        # Step 3: Execute the function
        func_name = function_call["name"]
        func_args = function_call.get("arguments", {})
        
        print(f"Calling function: {func_name} with args: {func_args}")
        
        result = execute_function(func_name, func_args)
        print(f"Function result: {result}")
        
        # Step 4: Give result back to Gemma for final response
        final_response = client.chat(
            model="gemma3:12b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": gemma_response},
                {"role": "user", "content": f"Function result: {result}"}
            ]
        )
        
        return final_response["message"]["content"]
    else:
        # No function call needed
        return gemma_response

# Demo usage
if __name__ == "__main__":
    print("🚀 Basic Gemma 3 Function Calling Demo")
    print("=" * 40)
    
    test_cases = [
        "What time is it?",
        "What's 15 plus 27?", 
        "Hello, how are you?",  # No function call needed
        "Add 100 and 200"
    ]
    
    for question in test_cases:
        print(f"\nUser: {question}")
        print("-" * 20)
        
        try:
            answer = simple_chat(question)
            print(f"Final answer: {answer}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("=" * 40)