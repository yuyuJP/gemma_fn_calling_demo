from fastmcp import FastMCP
from tools import get_time, random_joke

mcp = FastMCP("GemmaRetryDemo")

# Register tools with MCP
@mcp.tool()
def get_time_tool(timezone: str = "UTC") -> str: 
    """Get current time for a given timezone."""
    return get_time(timezone)

@mcp.tool()
def random_joke_tool() -> str: 
    """Get a random programming joke."""
    return random_joke()

if __name__ == "__main__":
    mcp.run()
