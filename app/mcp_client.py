import asyncio
import json
import ollama
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
try:
    from .config import MODEL_NAME, MAX_LOOPS
except ImportError:
    from config import MODEL_NAME, MAX_LOOPS

class MCPOllamaClient:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.ollama_client = ollama.Client()
        self.available_tools = {}
    
    async def get_tools_info(self):
        """Get tools info from MCP server."""
        server_params = StdioServerParameters(
            command="python", 
            args=[self.server_script_path]
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    
                    tools_info = {}
                    for tool in tools_result.tools:
                        tools_info[tool.name] = {
                            'description': tool.description,
                            'input_schema': tool.inputSchema
                        }
                    
                    return tools_info
        except Exception as e:
            print(f"Error getting tools info: {e}")
            return {}
    
    async def connect(self):
        """Connect and get available tools."""
        self.available_tools = await self.get_tools_info()
        return self.available_tools
    
    def create_system_prompt(self) -> str:
        """Create system prompt with available tools information."""
        tools_info = []
        for name, info in self.available_tools.items():
            tools_info.append(f"- {name}: {info['description']}")
        
        return f"""You have access to these tools:
{chr(10).join(tools_info)}

When you need to use a tool, respond with a JSON object in this format:
{{"tool_call": {{"name": "tool_name", "arguments": {{...}}}}}}

After calling a tool, use the result to provide a helpful response to the user.
If you don't need to use any tools, respond normally without the JSON format.
"""
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via MCP and return the result."""
        server_params = StdioServerParameters(
            command="python", 
            args=[self.server_script_path]
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    # Convert result content to string if it's not already
                    if hasattr(result.content, '__iter__') and not isinstance(result.content, str):
                        content_str = str(result.content[0].text) if result.content else ""
                    else:
                        content_str = str(result.content)
                    return {"success": True, "result": content_str}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def chat_with_tools(self, user_message: str) -> str:
        """Handle a chat message with potential tool calling."""
        if not self.available_tools:
            return "Error: No tools available"
        
        system_prompt = self.create_system_prompt()
        history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        for attempt in range(MAX_LOOPS):
            try:
                # Get response from Ollama
                response = self.ollama_client.chat(
                    model=MODEL_NAME,
                    messages=history
                )
                
                assistant_msg = response["message"]["content"]
                
                # Check if it's a tool call
                tool_call = self.extract_tool_call(assistant_msg)
                
                if not tool_call:
                    # No tool call, return the response
                    return assistant_msg
                
                # Execute the tool call
                tool_result = await self.call_tool(
                    tool_call["name"], 
                    tool_call["arguments"]
                )
                
                # Add the interaction to history
                history.extend([
                    {"role": "assistant", "content": assistant_msg},
                    {
                        "role": "user", 
                        "content": f"Tool result: {tool_result['result'] if tool_result['success'] else 'Error: ' + tool_result['error']}"
                    }
                ])
                
                # Continue to let the model respond with the tool result
                # Don't break here - let it generate a final response
                continue
                    
            except Exception as e:
                return f"Error: {str(e)}"
        
        return "Sorry, I couldn't complete that request after several attempts."
    
    def extract_tool_call(self, text: str) -> Dict[str, Any] | None:
        """Extract tool call from assistant message."""
        try:
            # Look for JSON with tool_call structure
            if '{"tool_call":' in text:
                start = text.find('{"tool_call":')
                end = text.find('}', start)
                if end != -1:
                    # Find the matching closing brace
                    brace_count = 0
                    for i in range(start, len(text)):
                        if text[i] == '{':
                            brace_count += 1
                        elif text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i
                                break
                    
                    json_str = text[start:end+1]
                    parsed = json.loads(json_str)
                    return parsed["tool_call"]
        except (json.JSONDecodeError, KeyError):
            pass
        
        return None

async def create_mcp_client(server_script_path: str = "app/main.py") -> MCPOllamaClient:
    """Create and connect an MCP client."""
    client = MCPOllamaClient(server_script_path)
    await client.connect()
    return client