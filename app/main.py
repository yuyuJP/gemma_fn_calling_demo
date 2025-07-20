#!/usr/bin/env python3
"""
Clean MCP server with essential WMS tools only.
"""

from fastmcp import FastMCP
from tools import (
    get_time,
    analyze_daily_operator_distances,
    load_spatial_data,
    analyze_product_demand,
    load_customer_orders,
    analyze_picking_distances
)

mcp = FastMCP("WarehouseAnalysis")

# Essential Tools
@mcp.tool()
def get_time_tool(timezone: str = "UTC") -> str:
    """Get current time for a given timezone."""
    return get_time(timezone)

@mcp.tool()
def analyze_operator_distances(data_dir: str = "data", target_date: str = None) -> str:
    """Find which warehouse operator walked the longest distance. Analyzes daily walking distances."""
    result = analyze_daily_operator_distances(data_dir, target_date)
    return str(result)

@mcp.tool()
def get_warehouse_layout(data_dir: str = "data") -> str:
    """Get warehouse layout and storage location information."""
    result = load_spatial_data(data_dir)
    return str(result)

@mcp.tool()
def analyze_product_popularity(data_dir: str = "data") -> str:
    """Find which products are most popular and in highest demand."""
    result = analyze_product_demand(data_dir)
    return str(result)

@mcp.tool()
def load_orders_data(data_dir: str = "data", date_filter: str = None) -> str:
    """Load customer orders with optional date filtering."""
    result = load_customer_orders(data_dir, date_filter)
    return str(result)

@mcp.tool()
def analyze_wave_distances(wave_number: int, data_dir: str = "data") -> str:
    """Calculate picking distances for a specific wave."""
    result = analyze_picking_distances(wave_number, data_dir)
    return str(result)

if __name__ == "__main__":
    mcp.run()