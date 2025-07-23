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

TOOL SELECTION:
- "most popular", "top products", "bestsellers" → get_most_popular_products
- "business sales trends", "growth patterns", "overall trends" → analyze_business_sales_trends  
- "advanced product analytics", "product lifecycle" → analyze_product_sales_trends
- "top customers", "best customers", "customer ranking" → get_top_customers
- "customer behavior", "loyalty analysis", "customer segments" → analyze_customer_segments

DATE RESOLUTION REQUIREMENT:
⏰ Call get_current_time_tool() FIRST ONLY for RELATIVE time periods (not specific dates):
- RELATIVE (call get_current_time_tool): "past month", "last week", "recent trends", "this quarter", "over the past X days", "lately", "recently"  
- SPECIFIC (do NOT call get_current_time_tool): "September 2023", "October 2023", "January 15th", "Q1 2023", "2023-10-01"

🔧 IMPORTANT: get_current_time_tool() only accepts timezone parameter and returns current time.
   After getting current time, YOU must calculate the actual date range for relative periods.
   Example: For "past month", call get_current_time_tool(), then calculate start_date and end_date yourself.

TOOL-SPECIFIC NOTES:
- For get_most_popular_products: Use for "top 5", "most popular", "bestsellers" - returns ranked list
- For analyze_product_sales_trends: Set product_references to null for all products analysis, or specific codes like "8N10W9,WRRW1W,I1KDJ0"
- For get_top_customers: Use ranking_by parameter ("quantity", "orders", "frequency", "products") and set top_count for number of customers
- For analyze_customer_segments: Set customer_references to null for all customers analysis, or specific IDs like "CUST001,CUST002,CUST003"
- NEVER use descriptive text like "top_5_customers" in customer_references - use null for all customers or specific IDs only
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
                print(f"🔧 TOOL CALL: {tool_call['name']} with arguments: {tool_call['arguments']}")
                tool_result = await self.call_tool(
                    tool_call["name"], 
                    tool_call["arguments"]
                )
                print(f"🔧 TOOL RESULT: {'✅ Success' if tool_result.get('success') else '❌ Failed'}")
                if not tool_result.get('success'):
                    print(f"🔧 ERROR: {tool_result.get('error', 'Unknown error')}")
                
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
                # Try to parse the entire text as JSON first
                try:
                    # Clean the text and fix Python-style booleans/None to JSON style
                    clean_text = text.strip().rstrip('\n').rstrip()
                    # Replace Python-style values with JSON-style values
                    clean_text = clean_text.replace('True', 'true').replace('False', 'false').replace('None', 'null')
                    
                    parsed = json.loads(clean_text)
                    if "tool_call" in parsed:
                        return parsed["tool_call"]
                except json.JSONDecodeError as e:
                    # Fall back to the original method
                    pass
                
                # Original method with brace counting
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