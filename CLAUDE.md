# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a demonstration of function calling with Gemma models using FastMCP (Model Control Protocol). The project implements an AI agent that can call tools with automatic retry logic when tool calls fail or have errors.

The project includes comprehensive **WMS (Warehouse Management System) analysis tools** for processing CSV data including storage utilization, picking optimization, and operator performance analysis.

**Quick Start**: For a simple introduction to Gemma 3 function calling, see the `examples/` directory which contains standalone demos without MCP complexity.

## Architecture

- **MCP Server**: `app/main.py` defines tools using FastMCP decorators
- **MCP Client**: `app/mcp_client.py` handles communication between Ollama and MCP server
- **Chat Server**: `app/chat_server.py` provides HTTP API that integrates MCP client with Ollama
- **Tool System**: Tools are defined in `app/tools.py` and registered via `@mcp.tool()` decorators
- **WMS Analysis**: Warehouse management tools for CSV data processing, storage optimization, and performance analysis

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

### WMS Data Analysis
The system includes tools for analyzing warehouse management data from CSV files:
- **Storage Types**: class_based, dedicated, hybrid, random storage analysis
- **Data Formats**: Supports encoded product data (product_code;quantity format)
- **Spatial Analysis**: 3D coordinate-based picking distance calculations
- **Performance Metrics**: Operator efficiency and product demand analysis

Place your CSV files in a `data/` directory with the following expected filenames:
- `Class_Based_Storage.csv`, `Dedicated_Storage.csv`, `Hybrid_Storage.csv`, `Random_Storage.csv`
- `Customer_Order.csv`, `Picking_Wave.csv`, `Product.csv`
- `Storage_Location.csv`, `Support_Points.csv`

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

# Test WMS analysis tools
python tests/test_wms_tools.py
```

#### Using pytest
```bash
python -m pytest tests/ -v
```

## Configuration

- Model configuration in `app/config.py` (currently set to "gemma3:12b")
- Retry limits controlled by `MAX_LOOPS` constant
- MCP client automatically discovers tools and generates system prompts
- WMS data directory can be specified in tool calls (default: `data/`)

## Available WMS Tools

The system provides 10 specialized warehouse management analysis tools:

### Data Loading Tools
- `load_storage_data_tool(storage_type, data_dir)` - Load storage data by type
- `load_customer_orders_tool(data_dir, date_filter)` - Load customer orders
- `load_picking_waves_tool(data_dir, wave_numbers)` - Load picking wave data
- `load_product_catalog_tool(data_dir)` - Load product catalog with ABC classifications
- `load_spatial_data_tool(data_dir)` - Load 3D warehouse coordinates

### Analysis Tools
- `parse_encoded_storage_tool(location, encoded_columns)` - Parse product_code;quantity format
- `calculate_storage_utilization_tool(storage_type, data_dir)` - Calculate storage efficiency
- `analyze_picking_distances_tool(wave_number, data_dir)` - Calculate 3D picking distances
- `analyze_operator_performance_tool(data_dir)` - Operator efficiency analysis
- `analyze_product_demand_tool(data_dir)` - Product demand analysis

## Testing

The test suite is organized into categories:

- **`test_ollama.py`**: Tests basic Ollama connectivity and model availability
- **`test_timezone.py`**: Tests intelligent timezone normalization functionality  
- **`test_mcp.py`**: Tests MCP server connection and tool discovery
- **`test_tool_call.py`**: Tests end-to-end tool calling with MCP client
- **`test_retry.py`**: Integration tests using HTTP API (requires server running)
- **`test_wms_tools.py`**: Comprehensive WMS analysis tools testing (13 test cases)
- **`run_all_tests.py`**: Master test runner for all categories

Integration tests use the HTTP API endpoint at `http://localhost:8001/v1/chat` and require the chat server to be running.

### WMS Testing Notes
- WMS tests create temporary CSV files for testing
- Tests cover encoded data parsing, storage utilization, spatial analysis, and error handling
- All WMS tests are designed to run independently without requiring actual CSV data files