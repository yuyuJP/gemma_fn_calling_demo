import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
try:
    from .mcp_client import create_mcp_client
except ImportError:
    from mcp_client import create_mcp_client

# Global client instance
mcp_client = None

class ChatHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/v1/chat":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                user_message = request_data.get('user_message', '')
                if not user_message:
                    self.send_error(400, "Missing user_message")
                    return
                
                # Run async chat function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(mcp_client.chat_with_tools(user_message))
                loop.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response_data = json.dumps({"response": response})
                self.wfile.write(response_data.encode('utf-8'))
                
            except Exception as e:
                self.send_error(500, f"Chat error: {str(e)}")
        else:
            self.send_error(404, "Not found")
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "mcp_connected": mcp_client is not None,
                "available_tools": list(mcp_client.available_tools.keys()) if mcp_client else []
            }
            self.wfile.write(json.dumps(health_data).encode('utf-8'))
        else:
            self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        return  # Suppress default logging

async def initialize_mcp_client():
    """Initialize MCP client."""
    global mcp_client
    try:
        mcp_client = await create_mcp_client("app/main.py")
        print("MCP client connected successfully")
        print(f"Available tools: {list(mcp_client.available_tools.keys())}")
    except Exception as e:
        print(f"Failed to connect MCP client: {e}")
        raise

def run_server(port=8001):
    """Run the HTTP server."""
    # Initialize MCP client
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_mcp_client())
    loop.close()
    
    # Start HTTP server
    server = HTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"Server running on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_server()