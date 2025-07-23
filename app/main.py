#!/usr/bin/env python3
"""
Clean MCP server with essential WMS tools only.
"""

from fastmcp import FastMCP
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from config import DEFAULT_TIMEZONE
from tools import (
    get_time,
    analyze_daily_operator_distances,
    load_spatial_data,
    analyze_product_demand,
    load_customer_orders,
    analyze_picking_distances,
    analyze_business_sales_trends_tool,
    get_top_customers_tool,
    analyze_customer_segments_tool,
    analyze_product_sales_trends_tool
)

mcp = FastMCP("WarehouseAnalysis")

# Essential Tools
@mcp.tool()
def get_current_time_tool(timezone: str = DEFAULT_TIMEZONE) -> str:
    """Get current time for a given timezone (default: Asia/Tokyo)."""
    return get_time(timezone)

@mcp.tool()
def analyze_operator_distances(data_dir: str = "data", target_date: str = None) -> str:
    """Find which warehouse operator walked the longest distance. Analyzes daily walking distances.
    
    Args:
        data_dir: Directory containing CSV data files (default: "data")
        target_date: Specific date to analyze in YYYY-MM-DD format (default: None for most recent date)
    """
    result = analyze_daily_operator_distances(data_dir, target_date)
    return str(result)

@mcp.tool()
def get_warehouse_layout(data_dir: str = "data") -> str:
    """Get warehouse layout and storage location information."""
    result = load_spatial_data(data_dir)
    return str(result)

@mcp.tool()
def get_most_popular_products(data_dir: str = "data", start_date: str = None, end_date: str = None) -> str:
    """🥇 SIMPLE PRODUCT RANKING: Find which products are most popular with basic demand metrics.
    
    **PURPOSE**: Quick, lightweight product popularity queries for simple ranking needs.
    **BEST FOR**: "Which products sell most?", "Show top products", "What are our bestsellers?", "most popular items"
    
    Args:
        data_dir: Directory containing CSV data files (default: "data")
        start_date: Start date for analysis in YYYY-MM-DD format (optional)
        end_date: End date for analysis in YYYY-MM-DD format (optional)
        
    **Returns**: Simple ranking list with basic demand metrics (quantity, frequency, avg per order).
    **Use instead of analyze_product_sales_trends for**: Simple popularity questions without lifecycle/performance analysis.
    """
    result = analyze_product_demand(data_dir, start_date, end_date)
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

@mcp.tool()
def analyze_business_sales_trends(data_dir: str = "data", date_start: str = None, 
                                 date_end: str = None, granularity: str = "daily", 
                                 metric: str = "quantity") -> str:
    """📈 BUSINESS-WIDE TEMPORAL ANALYSIS: Analyze overall business sales trends over time with growth patterns and seasonality.
    
    **PURPOSE**: Company-wide sales pattern analysis focusing on time-based trends and growth rates across all products.
    **BEST FOR**: "How is the business trending?", "Show overall growth patterns", "Weekly/monthly business performance"
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional) 
        granularity: Time aggregation level ("daily", "weekly", "monthly")
        metric: Analysis metric ("quantity", "orders", "unique_products")
        
    **Returns**: Business-wide time-series analysis with growth rates, trend direction, peak periods.
    **Use instead of analyze_product_sales_trends for**: Overall business trends, not individual product performance.
    """
    result = analyze_business_sales_trends_tool(data_dir, date_start, date_end, granularity, metric)
    return str(result)

@mcp.tool()
def get_top_customers(data_dir: str = "data", date_start: str = None,
                     date_end: str = None, ranking_by: str = "quantity",
                     top_count: int = 20, min_orders: int = 1) -> str:
    """🏆 TOP CUSTOMER RANKING: Get ranked list of top customers by different metrics.
    
    **PURPOSE**: Customer ranking and identification for sales focus and relationship management.
    **BEST FOR**: "Who are our top customers?", "Show best customers by orders", "Customer leaderboard"
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional)
        ranking_by: Ranking metric ("quantity", "orders", "frequency", "products")
        top_count: Number of top customers to return (default: 20)
        min_orders: Minimum orders threshold for active customers (default: 1)
        
    **Returns**: Ranked customer list with detailed metrics and contribution analysis.
    **Use instead of analyze_customer_segments for**: Customer identification and ranking needs.
    """
    result = get_top_customers_tool(data_dir, date_start, date_end, ranking_by, top_count, min_orders)
    return str(result)

@mcp.tool()
def analyze_customer_segments(data_dir: str = "data", date_start: str = None,
                            date_end: str = None, customer_segment: str = "all",
                            customer_references: str = None, min_orders: int = 1) -> str:
    """👥 CUSTOMER SEGMENTATION ANALYSIS: Analyze customer behavior patterns, loyalty, and purchasing habits.
    
    **PURPOSE**: Customer segmentation, loyalty analysis, and behavioral pattern identification.
    **BEST FOR**: "Customer behavior analysis", "Loyalty segmentation", "Retention metrics", "Customer lifecycle"
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional)
        customer_segment: Customer segment ("all", "top_customers", "new_customers")
        customer_references: Comma-separated customer IDs to analyze (optional, leave empty/null to analyze ALL customers)
        min_orders: Minimum orders threshold for active customers (default: 1)
        
    **Returns**: Customer segmentation analysis with loyalty classification, retention metrics, and behavioral patterns.
    **Use instead of get_top_customers for**: Understanding customer behavior and segmentation patterns.
    
    Note: To analyze ALL customers, leave customer_references empty/null.
          To analyze specific customers, provide comma-separated customer IDs like "CUST001,CUST002,CUST003".
    """
    # Parse customer references if provided
    customer_list = None
    if customer_references and customer_references.strip():
        customer_list = [ref.strip() for ref in customer_references.split(',')]
    
    result = analyze_customer_segments_tool(data_dir, date_start, date_end, customer_segment, customer_list, min_orders)
    return str(result)

@mcp.tool()
def analyze_product_sales_trends(data_dir: str = "data", date_start: str = None,
                               date_end: str = None, product_references: str = None,
                               include_sizes: bool = True) -> str:
    """🎯 ADVANCED PRODUCT INTELLIGENCE: Comprehensive product portfolio management and lifecycle analysis.
    
    **PURPOSE**: Deep product performance analytics with lifecycle stages, velocity metrics, and correlations.
    **BEST FOR**: "Product lifecycle analysis", "Performance optimization", "Cross-selling opportunities", "Portfolio management"
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional)
        product_references: Comma-separated product references to analyze (optional, leave empty/null to analyze ALL products)
        include_sizes: Include size-based analysis in results (default: true)
        
    **Returns**: Comprehensive product analytics including velocity, lifecycle stages, customer reach, 
               correlations, size analysis, and performance rankings.
    **Use instead of analyze_product_popularity for**: Advanced product management requiring detailed metrics.
    
    Note: To analyze ALL products and get top performers, leave product_references empty/null.
          To analyze specific products, provide comma-separated product codes like "8N10W9,WRRW1W,I1KDJ0".
    """
    # Parse product references if provided
    product_list = None
    if product_references and product_references.strip():
        product_list = [ref.strip() for ref in product_references.split(',')]
    
    result = analyze_product_sales_trends_tool(data_dir, date_start, date_end, product_list, include_sizes)
    return str(result)

if __name__ == "__main__":
    mcp.run()