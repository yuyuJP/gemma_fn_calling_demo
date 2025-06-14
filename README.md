# Gemma Function Calling Demo

**Languages**: **English** | [日本語](README.ja.md)

A demonstration of function calling with Gemma models using FastMCP (Model Control Protocol). This project implements an AI agent that can call tools with automatic retry logic when tool calls fail or have errors.

## Quick Start

For a simple introduction to Gemma 3 function calling, see the `examples/` directory which contains standalone demos without MCP complexity.

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Gemma 3 model pulled: `ollama pull gemma3:12b`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gemma_fn_calling_demo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure Ollama is running with Gemma 3:
```bash
ollama run gemma3:12b
```

## Usage

### Simple Examples (Recommended for Learning)

Start with the standalone examples that demonstrate core concepts:

```bash
# Basic function calling demo (no MCP)
python examples/basic_example.py

# Interactive function calling demo
python examples/simple_function_calling.py
```

### Full MCP Integration

For the complete MCP-based system:

1. **Start the MCP Server** (in one terminal):
```bash
python app/main.py
```

2. **Start the Chat Server** (in another terminal):
```bash
python app/chat_server.py
# Server runs on http://localhost:8001
```

3. **Test the API**:
```bash
curl -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is it?"}'
```

## Example Usage

### Time Query
```
User: What time is it?
Gemma: {"tool_call": {"name": "get_time", "arguments": {}}}
Function result: Current time: 14:30:25
Final answer: The current time is 14:30:25.
```

### Math Calculation
```
User: What's 15 plus 27?
Gemma: {"tool_call": {"name": "add_numbers", "arguments": {"a": 15, "b": 27}}}
Function result: 15 + 27 = 42
Final answer: 15 plus 27 equals 42.
```

### Tool Discovery
The system automatically discovers available tools through the MCP protocol and includes them in the model's system prompt.

## Architecture

- **MCP Server**: `app/main.py` defines tools using FastMCP decorators
- **MCP Client**: `app/mcp_client.py` handles communication between Ollama and MCP server
- **Chat Server**: `app/chat_server.py` provides HTTP API that integrates MCP client with Ollama
- **Tool System**: Tools are defined in `app/tools.py` and registered via `@mcp.tool()` decorators

### Key Features

- **Automatic Retry**: Built-in retry mechanism with configurable `MAX_LOOPS` safety valve
- **Tool Discovery**: MCP server exposes available tools through `list_tools()` API
- **JSON Tool Calls**: Uses structured JSON format: `{"tool_call": {"name": "...", "arguments": {...}}}`
- **Error Handling**: Robust error handling with detailed logging

## Testing

Run all tests:
```bash
python tests/run_all_tests.py
```

Or run individual test categories:
```bash
# Test Ollama connectivity
python tests/test_ollama.py

# Test timezone functionality  
python tests/test_timezone.py

# Test MCP connection
python tests/test_mcp.py

# Test tool calling
python tests/test_tool_call.py

# Test HTTP API (requires server running)
python tests/test_retry.py
```

Using pytest:
```bash
python -m pytest tests/ -v
```

## Configuration

- Model configuration in `app/config.py` (currently set to "gemma3:12b")
- Retry limits controlled by `MAX_LOOPS` constant
- MCP client automatically discovers tools and generates system prompts

## Troubleshooting

### Model Not Responding
- Ensure Ollama is running: `ollama list`
- Check model availability: `ollama run gemma3:12b`

### JSON Parsing Errors
- The model sometimes generates malformed JSON
- The examples include robust parsing with error handling
- Consider retry logic for production use

### Connection Issues
- Verify MCP server is running on the expected port
- Check firewall settings if running on different machines
- Ensure all dependencies are installed correctly

## Learning Path

1. **Start with examples**: Run `examples/basic_example.py` to understand core concepts
2. **Try interactive demo**: Run `examples/simple_function_calling.py` for hands-on experience
3. **Explore MCP integration**: Study the `app/` directory for production patterns
4. **Run tests**: Use the test suite to understand validation patterns
5. **Read documentation**: Check `article_plots/` for deeper insights

## Key Differences from OpenAI

- Gemma 3 uses JSON-in-text format instead of structured function calling
- Requires explicit prompt engineering for tool awareness
- Uses conversation history for context management
- Needs custom JSON parsing logic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license information here]