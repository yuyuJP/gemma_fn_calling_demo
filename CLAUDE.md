# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demonstration of function calling with Gemma models using FastMCP (Model Control Protocol). The project implements an AI agent that can call tools with automatic retry logic when tool calls fail or have errors.

**Quick Start**: For a simple introduction to Gemma 3 function calling, see the `examples/` directory which contains standalone demos without MCP complexity.

## Architecture

- **MCP Server**: `app/main.py` defines tools using FastMCP decorators
- **MCP Client**: `app/mcp_client.py` handles communication between Ollama and MCP server
- **Chat Server**: `app/chat_server.py` provides HTTP API that integrates MCP client with Ollama
- **Tool System**: Tools are defined in `app/tools.py` and registered via `@mcp.tool()` decorators

### Key Components

- **MCPOllamaClient**: Manages MCP server connection and tool calling integration
- **Retry Mechanism**: Built into `chat_with_tools()` method with `MAX_LOOPS` safety valve
- **Tool Discovery**: MCP server exposes available tools through `list_tools()` API
- **JSON Tool Calls**: Uses structured JSON format for tool calling: `{"tool_call": {"name": "...", "arguments": {...}}}`

## Common Commands

### Running the MCP Server (standalone)
```bash
python app/main.py
```

### Running the Chat Server (recommended)
```bash
python app/chat_server.py
# Server runs on http://localhost:8001
```

### Running Simple Examples
```bash
# Basic function calling demo (no MCP)
python examples/basic_example.py

# Interactive function calling demo
python examples/simple_function_calling.py
```

### Running Tests

#### All Tests (Recommended)
```bash
python tests/run_all_tests.py
```

#### Individual Test Categories
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

#### Using pytest
```bash
python -m pytest tests/ -v
```

## Configuration

- Model configuration in `app/config.py` (currently set to "gemma3:12b")
- Retry limits controlled by `MAX_LOOPS` constant
- MCP client automatically discovers tools and generates system prompts

## Testing

The test suite is organized into categories:

- **`test_ollama.py`**: Tests basic Ollama connectivity and model availability
- **`test_timezone.py`**: Tests intelligent timezone normalization functionality  
- **`test_mcp.py`**: Tests MCP server connection and tool discovery
- **`test_tool_call.py`**: Tests end-to-end tool calling with MCP client
- **`test_retry.py`**: Integration tests using HTTP API (requires server running)
- **`run_all_tests.py`**: Master test runner for all categories

Integration tests use the HTTP API endpoint at `http://localhost:8001/v1/chat` and require the chat server to be running.