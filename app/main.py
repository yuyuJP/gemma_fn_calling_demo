from fastmcp import FastMCP
from tools import (
    get_time, random_joke,
    load_storage_data, load_customer_orders, load_picking_waves,
    load_product_catalog, load_spatial_data, parse_encoded_storage,
    calculate_storage_utilization, analyze_picking_distances,
    analyze_operator_performance, analyze_product_demand
)

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

# WMS Data Analysis Tools
@mcp.tool()
def load_storage_data_tool(storage_type: str, data_dir: str = "data") -> str:
    """Load storage data (class_based, dedicated, hybrid, or random)."""
    result = load_storage_data(storage_type, data_dir)
    return str(result)

@mcp.tool()
def load_customer_orders_tool(data_dir: str = "data", date_filter: str = None) -> str:
    """Load customer orders with optional date filtering."""
    result = load_customer_orders(data_dir, date_filter)
    return str(result)

@mcp.tool()
def load_picking_waves_tool(data_dir: str = "data", wave_numbers: str = None) -> str:
    """Load picking wave data. wave_numbers should be comma-separated integers."""
    wave_list = None
    if wave_numbers:
        try:
            wave_list = [int(w.strip()) for w in wave_numbers.split(',')]
        except ValueError:
            return str({"error": "Invalid wave numbers format. Use comma-separated integers."})
    
    result = load_picking_waves(data_dir, wave_list)
    return str(result)

@mcp.tool()
def load_product_catalog_tool(data_dir: str = "data") -> str:
    """Load product reference data with ABC classifications."""
    result = load_product_catalog(data_dir)
    return str(result)

@mcp.tool()
def load_spatial_data_tool(data_dir: str = "data") -> str:
    """Load 3D warehouse coordinates and location mappings."""
    result = load_spatial_data(data_dir)
    return str(result)

@mcp.tool()
def parse_encoded_storage_tool(location: str, encoded_columns: str) -> str:
    """Parse encoded product details. encoded_columns should be comma-separated values."""
    try:
        columns_list = [col.strip() for col in encoded_columns.split(',') if col.strip()]
        result = parse_encoded_storage(location, columns_list)
        return str(result)
    except Exception as e:
        return str({"error": f"Failed to parse encoded columns: {str(e)}"})

@mcp.tool()
def calculate_storage_utilization_tool(storage_type: str, data_dir: str = "data") -> str:
    """Calculate utilization rates for different storage strategies."""
    result = calculate_storage_utilization(storage_type, data_dir)
    return str(result)

@mcp.tool()
def analyze_picking_distances_tool(wave_number: int, data_dir: str = "data") -> str:
    """Calculate total picking distances for a wave using 3D coordinates."""
    result = analyze_picking_distances(wave_number, data_dir)
    return str(result)

@mcp.tool()
def analyze_operator_performance_tool(data_dir: str = "data") -> str:
    """Comprehensive operator performance analysis."""
    result = analyze_operator_performance(data_dir)
    return str(result)

@mcp.tool()
def analyze_product_demand_tool(data_dir: str = "data") -> str:
    """Analyze product demand based on customer orders."""
    result = analyze_product_demand(data_dir)
    return str(result)

if __name__ == "__main__":
    mcp.run()
