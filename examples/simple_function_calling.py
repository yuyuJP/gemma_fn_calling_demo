#!/usr/bin/env python3
"""
Simple Gemma 3 Function Calling Example

This example demonstrates the core function calling capability of Gemma 3
without the complexity of MCP or complex architectures. It shows:
1. How to prompt Gemma 3 for function calling
2. JSON parsing from model responses
3. Function execution and response handling
4. Simple retry logic for robust interaction

Run: python examples/simple_function_calling.py
"""

import ollama
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

# Simple tool functions
def get_current_time(timezone: str = "UTC") -> str:
    """Get current time. For demo purposes, just returns current UTC time with timezone label."""
    current_time = datetime.utcnow()
    return f"Current time in {timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S')} {timezone}"

def calculate(expression: str) -> str:
    """Safely calculate simple math expressions."""
    try:
        # Only allow basic math operations for safety
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        
        result = eval(expression)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"

def get_weather(city: str) -> str:
    """Mock weather function for demo purposes."""
    # In real implementation, this would call a weather API
    weather_data = {
        "tokyo": "Sunny, 22°C",
        "london": "Cloudy, 15°C", 
        "new york": "Rainy, 18°C",
        "paris": "Partly cloudy, 19°C"
    }
    
    city_lower = city.lower()
    if city_lower in weather_data:
        return f"Weather in {city}: {weather_data[city_lower]}"
    else:
        return f"Weather data not available for {city}"

# Available tools registry
AVAILABLE_TOOLS = {
    "get_current_time": {
        "function": get_current_time,
        "description": "Get current time for a given timezone",
        "parameters": {
            "timezone": {"type": "string", "description": "Timezone (e.g., 'UTC', 'JST', 'EST')", "default": "UTC"}
        }
    },
    "calculate": {
        "function": calculate,
        "description": "Calculate simple math expressions",
        "parameters": {
            "expression": {"type": "string", "description": "Math expression to calculate (e.g., '2 + 2', '10 * 5')"}
        }
    },
    "get_weather": {
        "function": get_weather,
        "description": "Get weather information for a city",
        "parameters": {
            "city": {"type": "string", "description": "City name (e.g., 'Tokyo', 'London', 'New York')"}
        }
    }
}

def create_system_prompt() -> str:
    """Create system prompt that teaches Gemma 3 how to call functions."""
    
    # Build tool descriptions
    tool_descriptions = []
    for name, info in AVAILABLE_TOOLS.items():
        params = ", ".join([f"{p}: {details['description']}" for p, details in info["parameters"].items()])
        tool_descriptions.append(f"- {name}({params}): {info['description']}")
    
    return f"""You have access to these tools:
{chr(10).join(tool_descriptions)}

When you need to use a tool, respond with a JSON object in this exact format:
{{"tool_call": {{"name": "tool_name", "arguments": {{"param1": "value1", "param2": "value2"}}}}}}

Examples:
- To get time: {{"tool_call": {{"name": "get_current_time", "arguments": {{"timezone": "JST"}}}}}}
- To calculate: {{"tool_call": {{"name": "calculate", "arguments": {{"expression": "15 * 3"}}}}}}
- To get weather: {{"tool_call": {{"name": "get_weather", "arguments": {{"city": "Tokyo"}}}}}}

After calling a tool, I'll provide the result and you should give a helpful response to the user.
If you don't need to use any tools, respond normally without JSON.
"""

def extract_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """Extract tool call JSON from Gemma 3 response."""
    try:
        # Look for the tool_call pattern
        if '{"tool_call":' not in text:
            return None
        
        # Find the start of JSON
        start = text.find('{"tool_call":')
        if start == -1:
            return None
        
        # Find matching closing brace by counting braces
        brace_count = 0
        end = start
        
        for i in range(start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i
                    break
        
        # Extract and parse JSON
        json_str = text[start:end + 1]
        parsed = json.loads(json_str)
        
        return parsed.get("tool_call")
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to parse tool call: {e}")
        return None

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool function with given arguments."""
    if tool_name not in AVAILABLE_TOOLS:
        return f"Error: Unknown tool '{tool_name}'"
    
    tool_info = AVAILABLE_TOOLS[tool_name]
    function = tool_info["function"]
    
    try:
        # Call function with arguments
        result = function(**arguments)
        return result
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

def chat_with_tools(user_message: str, model: str = "gemma3:12b", max_iterations: int = 3) -> str:
    """Main chat function that handles tool calling with Gemma 3."""
    
    client = ollama.Client()
    
    # Initialize conversation
    conversation = [
        {"role": "system", "content": create_system_prompt()},
        {"role": "user", "content": user_message}
    ]
    
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")
        
        # Get response from Gemma 3
        try:
            response = client.chat(model=model, messages=conversation)
            assistant_response = response["message"]["content"]
            print(f"Gemma 3 says: {assistant_response}")
            
        except Exception as e:
            return f"Error communicating with model: {str(e)}"
        
        # Check if this is a tool call
        tool_call = extract_tool_call(assistant_response)
        
        if tool_call is None:
            # No tool call, this is the final response
            print("No tool call detected. Conversation complete.")
            return assistant_response
        
        # Execute the tool call
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        print(f"Tool call detected: {tool_name} with args {arguments}")
        
        tool_result = execute_tool(tool_name, arguments)
        print(f"Tool result: {tool_result}")
        
        # Add the interaction to conversation history
        conversation.extend([
            {"role": "assistant", "content": assistant_response},
            {"role": "user", "content": f"Tool result: {tool_result}"}
        ])
        
        # Continue to next iteration for final response
    
    return "Maximum iterations reached without final response."

def main():
    """Interactive demo of Gemma 3 function calling."""
    
    print("🤖 Gemma 3 Function Calling Demo")
    print("=" * 40)
    print("Available tools: get_current_time, calculate, get_weather")
    print("Type 'quit' to exit")
    print()
    
    # Example queries to try
    examples = [
        "What time is it in Tokyo?",
        "Calculate 15 * 24 + 7",
        "What's the weather like in London?",
        "What's 2+2 and what time is it in New York?"
    ]
    
    print("Try these examples:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print(f"\nProcessing: {user_input}")
            print("-" * 40)
            
            # Get response with tool calling
            response = chat_with_tools(user_input)
            
            print(f"\nFinal Response: {response}")
            print("=" * 40)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()