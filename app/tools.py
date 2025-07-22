#!/usr/bin/env python3
"""
Clean tools module with essential WMS functions and utilities.
"""

from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
import ollama
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import os


def _normalize_timezone_with_llm(user_input: str) -> str:
    """Use LLM to convert user timezone input to proper IANA timezone identifier."""
    
    # Get available timezones for context
    available_zones = list(available_timezones())
    
    # Create a prompt for the LLM to normalize timezone
    prompt = f"""Convert the user's timezone input to a proper IANA timezone identifier.

User input: "{user_input}"

Available IANA timezone identifiers include examples like:
- Asia/Tokyo, Asia/Shanghai, Asia/Kolkata
- America/New_York, America/Los_Angeles, America/Chicago
- Europe/London, Europe/Paris, Europe/Berlin
- Australia/Sydney, Australia/Melbourne
- UTC

Rules:
1. If the input is already a valid IANA timezone (like "Asia/Tokyo"), return it exactly
2. Convert city/country names to proper IANA format (e.g., "Tokyo" → "Asia/Tokyo")
3. Convert abbreviations (e.g., "JST" → "Asia/Tokyo", "EST" → "America/New_York")
4. Handle misspellings (e.g., "T0kyo" → "Asia/Tokyo")
5. If unclear or invalid, return "UTC"

Respond with ONLY the IANA timezone identifier, nothing else."""

    try:
        client = ollama.Client()
        response = client.chat(
            model="gemma3:12b",
            messages=[{"role": "user", "content": prompt}]
        )
        
        normalized_tz = response["message"]["content"].strip()
        
        # Validate the result is a real timezone
        if normalized_tz in available_zones:
            return normalized_tz
        else:
            return "UTC"  # Fallback if LLM returns invalid timezone
            
    except Exception:
        return "UTC"  # Fallback if LLM call fails


def get_time(timezone: str = "UTC") -> str:
    """Return current time string for a specific timezone."""
    try:
        # Use LLM to normalize timezone input
        normalized_tz = _normalize_timezone_with_llm(timezone)
        
        # Get current time in the normalized timezone
        tz = ZoneInfo(normalized_tz)
        current_time = datetime.now(tz)
        
        # Format time nicely
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"Current time in {timezone} ({normalized_tz}): {formatted_time}"
        
    except Exception as e:
        # Fallback to UTC if anything goes wrong
        utc_time = datetime.now(ZoneInfo("UTC"))
        return f"Error getting time for '{timezone}'. Current UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"


def load_customer_orders(data_dir: str = "data", date_filter: Optional[str] = None) -> Dict[str, Any]:
    """Load customer orders with optional date filtering."""
    try:
        file_path = os.path.join(data_dir, "Customer_Order.csv")
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        df = pd.read_csv(file_path, sep=';', encoding='utf-8-sig')
        
        if date_filter:
            try:
                df['creationDate'] = pd.to_datetime(df['creationDate'])
                # Parse date_filter with multiple format attempts
                filter_date = None
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                
                for fmt in date_formats:
                    try:
                        filter_date = pd.to_datetime(date_filter, format=fmt).date()
                        break
                    except:
                        continue
                
                if filter_date is None:
                    # Try pandas' flexible parsing as fallback
                    filter_date = pd.to_datetime(date_filter).date()
                
                df = df[df['creationDate'].dt.date == filter_date]
            except Exception as e:
                return {"error": f"Date filtering failed: {str(e)}. Please use format YYYY-MM-DD or MM/DD/YYYY"}
        
        return {
            "data_loaded": True,
            "total_orders": len(df),
            "unique_customers": df['codCustomer'].nunique() if 'codCustomer' in df.columns else 0,
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
    except Exception as e:
        return {"error": f"Failed to load customer orders: {str(e)}"}


def load_spatial_data(data_dir: str = "data") -> Dict[str, Any]:
    """Load 3D warehouse coordinates and location mappings."""
    try:
        storage_file = os.path.join(data_dir, "Storage_Location.csv")
        support_file = os.path.join(data_dir, "Support_Points_Navigation.csv")
        
        result = {"data_loaded": True}
        
        if os.path.exists(storage_file):
            storage_df = pd.read_csv(storage_file)
            result["storage_locations"] = {
                "records": len(storage_df),
                "columns": list(storage_df.columns),
                "coordinate_range": {
                    "x": {"min": int(storage_df['x'].min()), "max": int(storage_df['x'].max())} if 'x' in storage_df.columns else None,
                    "y": {"min": int(storage_df['y'].min()), "max": int(storage_df['y'].max())} if 'y' in storage_df.columns else None,
                    "z": {"min": int(storage_df['z'].min()), "max": int(storage_df['z'].max())} if 'z' in storage_df.columns else None
                }
            }
        
        if os.path.exists(support_file):
            # Support_Points has complex format, try to read it
            try:
                support_df = pd.read_csv(support_file, sep=';', encoding='utf-8-sig')
            except:
                # Fallback: create empty dataframe if file format is problematic
                support_df = pd.DataFrame({"points_specified": [], "labels": []})
            result["support_points"] = {
                "records": len(support_df),
                "columns": list(support_df.columns),
                "sample_points": support_df.head(3).to_dict('records') if len(support_df) > 0 else []
            }
        
        if "storage_locations" not in result and "support_points" not in result:
            return {"error": "No spatial data files found"}
            
        return result
        
    except Exception as e:
        return {"error": f"Failed to load spatial data: {str(e)}"}


def analyze_picking_distances(wave_number: int, data_dir: str = "data") -> Dict[str, Any]:
    """Calculate total picking distances for a wave using 3D coordinates."""
    try:
        waves_file = os.path.join(data_dir, "Picking_Wave.csv")
        spatial_file = os.path.join(data_dir, "Storage_Location.csv")
        
        if not os.path.exists(waves_file):
            return {"error": f"Picking waves file not found: {waves_file}"}
        if not os.path.exists(spatial_file):
            return {"error": f"Spatial data file not found: {spatial_file}"}
        
        waves_df = pd.read_csv(waves_file, sep=';', encoding='utf-8-sig')
        spatial_df = pd.read_csv(spatial_file)  # Storage_Location.csv uses comma delimiter
        
        wave_data = waves_df[waves_df['waveNumber'] == wave_number]
        
        if wave_data.empty:
            return {"error": f"No data found for wave number {wave_number}"}
        
        coordinates = []
        locations_processed = []
        
        for _, row in wave_data.iterrows():
            if 'locations' in row and pd.notna(row['locations']):
                locations = str(row['locations']).split(',')
                
                for location in locations:
                    location = location.strip()
                    loc_coords = spatial_df[spatial_df['originalLocation'] == location]
                    
                    if not loc_coords.empty:
                        coord = loc_coords.iloc[0]
                        coordinates.append([
                            int(coord['x']) if 'x' in coord and pd.notna(coord['x']) else 0,
                            int(coord['y']) if 'y' in coord and pd.notna(coord['y']) else 0,
                            int(coord['z']) if 'z' in coord and pd.notna(coord['z']) else 0
                        ])
                        locations_processed.append(location)
        
        if len(coordinates) < 2:
            return {
                "wave_number": wave_number,
                "total_picking_distance": 0,
                "locations_count": len(coordinates),
                "message": "Insufficient location data for distance calculation"
            }
        
        total_distance = 0
        for i in range(1, len(coordinates)):
            manhattan_dist = sum(abs(coordinates[i][j] - coordinates[i-1][j]) for j in range(3))
            total_distance += manhattan_dist
        
        avg_distance = total_distance / (len(coordinates) - 1) if len(coordinates) > 1 else 0
        
        return {
            "wave_number": wave_number,
            "total_picking_distance": total_distance,
            "locations_count": len(coordinates),
            "locations_processed": locations_processed,
            "avg_distance_per_pick": round(avg_distance, 2)
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze picking distances: {str(e)}"}


def analyze_daily_operator_distances(data_dir: str = "data", target_date: Optional[str] = None) -> Dict[str, Any]:
    """Calculate total walking distances for operators on a specific day."""
    try:
        orders_file = os.path.join(data_dir, "Customer_Order.csv")
        waves_file = os.path.join(data_dir, "Picking_Wave.csv")
        
        if not os.path.exists(orders_file):
            return {"error": f"Orders file not found: {orders_file}"}
        if not os.path.exists(waves_file):
            return {"error": f"Waves file not found: {waves_file}"}
        
        orders_df = pd.read_csv(orders_file, sep=';', encoding='utf-8-sig')
        waves_df = pd.read_csv(waves_file, sep=';', encoding='utf-8-sig')
        
        # Parse dates
        orders_df['creationDate'] = pd.to_datetime(orders_df['creationDate'], format='%d/%m/%Y %H:%M')
        orders_df['date'] = orders_df['creationDate'].dt.date
        
        # If no target date specified, use the most recent date with significant activity
        if target_date is None:
            date_counts = orders_df['date'].value_counts()
            target_date = str(date_counts.index[0])  # Most active date
        
        # Filter to target date with robust parsing
        try:
            # Parse target_date with multiple format attempts
            target_date_parsed = None
            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
            
            for fmt in date_formats:
                try:
                    target_date_parsed = pd.to_datetime(target_date, format=fmt).date()
                    break
                except:
                    continue
            
            if target_date_parsed is None:
                # Try pandas' flexible parsing as fallback
                target_date_parsed = pd.to_datetime(target_date).date()
            
            daily_orders = orders_df[orders_df['date'] == target_date_parsed]
        except Exception as e:
            return {"error": f"Date parsing failed for '{target_date}': {str(e)}. Please use format YYYY-MM-DD or MM/DD/YYYY"}
        
        if daily_orders.empty:
            return {"error": f"No orders found for date {target_date}"}
        
        # Get waves for this date
        daily_wave_numbers = daily_orders['waveNumber'].unique()
        daily_waves = waves_df[waves_df['waveNumber'].isin(daily_wave_numbers)]
        
        operator_stats = []
        
        for operator in daily_orders['operator'].unique():
            if pd.isna(operator):
                continue
            
            op_orders = daily_orders[daily_orders['operator'] == operator]
            op_waves = daily_waves[daily_waves['operator'] == operator]
            
            total_distance = 0
            total_picks = 0
            processed_waves = 0
            
            for wave_num in op_waves['waveNumber'].unique():
                if pd.notna(wave_num):
                    dist_result = analyze_picking_distances(int(wave_num), data_dir)
                    if "error" not in dist_result and 'total_picking_distance' in dist_result:
                        total_distance += dist_result['total_picking_distance']
                        total_picks += dist_result['locations_count']
                        processed_waves += 1
            
            total_items = op_orders['quantity (units)'].sum()
            
            operator_stats.append({
                "operator": str(operator),
                "total_walking_distance": total_distance,
                "total_picks": total_picks,
                "total_items": int(total_items),
                "total_orders": len(op_orders),
                "processed_waves": processed_waves,
                "avg_distance_per_pick": round(total_distance / total_picks, 2) if total_picks > 0 else 0
            })
        
        # Sort by total walking distance
        operator_stats.sort(key=lambda x: x['total_walking_distance'], reverse=True)
        
        return {
            "analysis_date": target_date,
            "analysis_complete": True,
            "total_operators": len(operator_stats),
            "total_orders_analyzed": len(daily_orders),
            "total_waves_analyzed": len(daily_wave_numbers),
            "operator_distances": operator_stats
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze daily operator distances: {str(e)}"}


def analyze_product_demand(data_dir: str = "data", start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Analyze product demand based on customer orders over a date range."""
    try:
        orders_file = os.path.join(data_dir, "Customer_Order.csv")
        
        if not os.path.exists(orders_file):
            return {"error": f"Orders file not found: {orders_file}"}
        
        orders_df = pd.read_csv(orders_file, sep=';', encoding='utf-8-sig')
        
        if 'Reference' not in orders_df.columns or 'quantity (units)' not in orders_df.columns:
            return {"error": "Required columns (Reference, quantity) not found in orders data"}
        
        # Parse dates for filtering
        if 'creationDate' in orders_df.columns:
            orders_df['creationDate'] = pd.to_datetime(orders_df['creationDate'], format='%d/%m/%Y %H:%M')
            orders_df['date'] = orders_df['creationDate'].dt.date
            
            # Apply date filtering if specified
            if start_date or end_date:
                try:
                    # Parse dates with multiple format attempts
                    def parse_date(date_str):
                        if date_str is None:
                            return None
                        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                        for fmt in date_formats:
                            try:
                                return pd.to_datetime(date_str, format=fmt).date()
                            except:
                                continue
                        # Try pandas' flexible parsing as fallback
                        return pd.to_datetime(date_str).date()
                    
                    start_parsed = parse_date(start_date) if start_date else orders_df['date'].min()
                    end_parsed = parse_date(end_date) if end_date else orders_df['date'].max()
                    
                    # If only one date provided, use it as both start and end
                    if start_date and not end_date:
                        end_parsed = start_parsed
                    elif end_date and not start_date:
                        start_parsed = end_parsed
                    
                    orders_df = orders_df[(orders_df['date'] >= start_parsed) & (orders_df['date'] <= end_parsed)]
                    
                    if orders_df.empty:
                        return {"error": f"No orders found in date range {start_parsed} to {end_parsed}"}
                        
                except Exception as e:
                    return {"error": f"Date parsing failed: {str(e)}. Please use format YYYY-MM-DD or MM/DD/YYYY"}
        
        demand_analysis = orders_df.groupby('Reference')['quantity (units)'].agg([
            'sum', 'count', 'mean'
        ]).round(2)
        
        demand_analysis.columns = ['total_demand', 'order_frequency', 'avg_quantity_per_order']
        demand_analysis = demand_analysis.sort_values('total_demand', ascending=False)
        
        top_products = demand_analysis.head(10).reset_index().to_dict('records')
        
        # Add date range info to result
        date_info = {}
        if start_date or end_date:
            date_info["date_range"] = {
                "start_date": str(start_parsed) if 'start_parsed' in locals() else None,
                "end_date": str(end_parsed) if 'end_parsed' in locals() else None,
                "total_orders_in_range": len(orders_df)
            }
        
        return {
            "analysis_complete": True,
            "total_products": len(demand_analysis),
            "top_10_products_by_demand": top_products,
            "total_demand_across_all_products": int(demand_analysis['total_demand'].sum()),
            **date_info
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze product demand: {str(e)}"}


def analyze_sales_trends_tool(data_dir: str = "data", date_start: Optional[str] = None, 
                             date_end: Optional[str] = None, granularity: str = "daily", 
                             metric: str = "quantity") -> Dict[str, Any]:
    """
    Analyze sales trends over time with temporal patterns and growth analysis.
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional)
        granularity: Time aggregation level ("daily", "weekly", "monthly")
        metric: Analysis metric ("quantity", "orders", "unique_products")
    
    Returns:
        Dictionary with trend analysis results including temporal patterns and growth rates
    """
    try:
        csv_file = os.path.join(data_dir, "Customer_Order.csv")
        if not os.path.exists(csv_file):
            return {"error": f"Customer_Order.csv not found in {data_dir}"}
        
        # Load customer orders data
        orders_df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
        
        # Parse creation date
        orders_df['creationDate'] = pd.to_datetime(orders_df['creationDate'], format='%d/%m/%Y %H:%M')
        orders_df['date'] = orders_df['creationDate'].dt.date
        
        # Apply date filtering if specified
        if date_start or date_end:
            def parse_date(date_str):
                if date_str is None:
                    return None
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
                for fmt in date_formats:
                    try:
                        return pd.to_datetime(date_str, format=fmt).date()
                    except:
                        continue
                return pd.to_datetime(date_str).date()
            
            start_parsed = parse_date(date_start) if date_start else orders_df['date'].min()
            end_parsed = parse_date(date_end) if date_end else orders_df['date'].max()
            
            orders_df = orders_df[(orders_df['date'] >= start_parsed) & (orders_df['date'] <= end_parsed)]
            
            if orders_df.empty:
                return {"error": f"No orders found in date range {start_parsed} to {end_parsed}"}
        
        # Set up time grouping based on granularity
        if granularity == "daily":
            orders_df['period'] = orders_df['creationDate'].dt.date
        elif granularity == "weekly":
            orders_df['period'] = orders_df['creationDate'].dt.to_period('W').astype(str)
        elif granularity == "monthly":
            orders_df['period'] = orders_df['creationDate'].dt.to_period('M').astype(str)
        else:
            return {"error": "Granularity must be 'daily', 'weekly', or 'monthly'"}
        
        # Calculate metrics based on selected metric type
        if metric == "quantity":
            trend_data = orders_df.groupby('period')['quantity (units)'].sum().reset_index()
            metric_name = "total_quantity"
        elif metric == "orders":
            trend_data = orders_df.groupby('period')['orderNumber'].nunique().reset_index()
            metric_name = "total_orders"
        elif metric == "unique_products":
            trend_data = orders_df.groupby('period')['Reference'].nunique().reset_index()
            metric_name = "unique_products"
        else:
            return {"error": "Metric must be 'quantity', 'orders', or 'unique_products'"}
        
        trend_data.columns = ['period', metric_name]
        trend_data = trend_data.sort_values('period')
        
        # Calculate growth rates
        trend_data['growth_rate'] = trend_data[metric_name].pct_change() * 100
        trend_data['growth_rate'] = trend_data['growth_rate'].round(2)
        
        # Calculate summary statistics
        total_value = trend_data[metric_name].sum()
        avg_value = trend_data[metric_name].mean()
        max_period = trend_data.loc[trend_data[metric_name].idxmax(), 'period']
        min_period = trend_data.loc[trend_data[metric_name].idxmin(), 'period']
        
        # Identify trends
        overall_trend = "stable"
        if len(trend_data) >= 2:
            first_half = trend_data[metric_name].iloc[:len(trend_data)//2].mean()
            second_half = trend_data[metric_name].iloc[len(trend_data)//2:].mean()
            if second_half > first_half * 1.1:
                overall_trend = "increasing"
            elif second_half < first_half * 0.9:
                overall_trend = "decreasing"
        
        # Convert trend data to records for JSON serialization
        trend_records = trend_data.to_dict('records')
        
        return {
            "analysis_complete": True,
            "analysis_parameters": {
                "granularity": granularity,
                "metric": metric,
                "date_range": f"{orders_df['date'].min()} to {orders_df['date'].max()}",
                "total_periods": len(trend_data)
            },
            "summary_statistics": {
                f"total_{metric}": int(total_value),
                f"average_per_period": round(avg_value, 2),
                "peak_period": str(max_period),
                "lowest_period": str(min_period),
                "overall_trend": overall_trend
            },
            "trend_data": trend_records,
            "insights": [
                f"Analysis covers {len(trend_data)} {granularity} periods",
                f"Peak {metric} occurred in {max_period}",
                f"Overall trend is {overall_trend}",
                f"Average growth rate: {trend_data['growth_rate'].mean():.2f}%" if len(trend_data) > 1 else "Insufficient data for growth rate"
            ]
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze sales trends: {str(e)}"}


def analyze_customer_behavior_tool(data_dir: str = "data", date_start: Optional[str] = None,
                                 date_end: Optional[str] = None, customer_segment: str = "all",
                                 min_orders: int = 1) -> Dict[str, Any]:
    """
    Analyze customer purchasing patterns and loyalty behavior.
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional)
        customer_segment: Customer segment to analyze ("all", "top_customers", "new_customers")
        min_orders: Minimum orders threshold for active customers (default: 1)
    
    Returns:
        Dictionary with customer behavior analysis including segmentation and loyalty metrics
    """
    try:
        csv_file = os.path.join(data_dir, "Customer_Order.csv")
        if not os.path.exists(csv_file):
            return {"error": f"Customer_Order.csv not found in {data_dir}"}
        
        # Load customer orders data
        orders_df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
        
        # Parse creation date
        orders_df['creationDate'] = pd.to_datetime(orders_df['creationDate'], format='%d/%m/%Y %H:%M')
        orders_df['date'] = orders_df['creationDate'].dt.date
        
        # Apply date filtering if specified
        if date_start or date_end:
            def parse_date(date_str):
                if date_str is None:
                    return None
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
                for fmt in date_formats:
                    try:
                        return pd.to_datetime(date_str, format=fmt).date()
                    except:
                        continue
                return pd.to_datetime(date_str).date()
            
            start_parsed = parse_date(date_start) if date_start else orders_df['date'].min()
            end_parsed = parse_date(date_end) if date_end else orders_df['date'].max()
            
            orders_df = orders_df[(orders_df['date'] >= start_parsed) & (orders_df['date'] <= end_parsed)]
            
            if orders_df.empty:
                return {"error": f"No orders found in date range {start_parsed} to {end_parsed}"}
        
        # Customer-level analysis
        customer_stats = orders_df.groupby('codCustomer').agg({
            'orderNumber': 'nunique',
            'quantity (units)': 'sum',
            'Reference': 'nunique',
            'creationDate': ['min', 'max']
        }).round(2)
        
        customer_stats.columns = ['total_orders', 'total_quantity', 'unique_products', 'first_order_date', 'last_order_date']
        
        # Calculate customer metrics
        customer_stats['avg_quantity_per_order'] = (customer_stats['total_quantity'] / customer_stats['total_orders']).round(2)
        customer_stats['days_active'] = (customer_stats['last_order_date'] - customer_stats['first_order_date']).dt.days
        customer_stats['order_frequency'] = (customer_stats['total_orders'] / (customer_stats['days_active'] + 1)).round(4)
        
        # Filter by minimum orders threshold
        active_customers = customer_stats[customer_stats['total_orders'] >= min_orders]
        
        # Customer segmentation
        if customer_segment == "top_customers":
            # Top 10% by total quantity
            threshold = active_customers['total_quantity'].quantile(0.9)
            segment_customers = active_customers[active_customers['total_quantity'] >= threshold]
        elif customer_segment == "new_customers":
            # Customers with only 1-2 orders
            segment_customers = active_customers[active_customers['total_orders'] <= 2]
        else:
            segment_customers = active_customers
        
        # Calculate segment statistics
        total_customers = len(segment_customers)
        avg_orders_per_customer = segment_customers['total_orders'].mean()
        avg_quantity_per_customer = segment_customers['total_quantity'].mean()
        
        # Top customers by different metrics
        top_by_orders = segment_customers.nlargest(10, 'total_orders')[['total_orders', 'total_quantity']].reset_index()
        top_by_quantity = segment_customers.nlargest(10, 'total_quantity')[['total_orders', 'total_quantity']].reset_index()
        
        # Order size distribution
        order_sizes = orders_df.groupby('orderNumber')['quantity (units)'].sum()
        size_distribution = {
            "single_item_orders": len(order_sizes[order_sizes == 1]),
            "small_orders_2_5": len(order_sizes[(order_sizes >= 2) & (order_sizes <= 5)]),
            "medium_orders_6_10": len(order_sizes[(order_sizes >= 6) & (order_sizes <= 10)]),
            "large_orders_10_plus": len(order_sizes[order_sizes > 10])
        }
        
        # Purchase frequency analysis
        frequency_segments = {
            "single_purchase": len(segment_customers[segment_customers['total_orders'] == 1]),
            "occasional_2_5": len(segment_customers[(segment_customers['total_orders'] >= 2) & (segment_customers['total_orders'] <= 5)]),
            "regular_6_10": len(segment_customers[(segment_customers['total_orders'] >= 6) & (segment_customers['total_orders'] <= 10)]),
            "frequent_10_plus": len(segment_customers[segment_customers['total_orders'] > 10])
        }
        
        return {
            "analysis_complete": True,
            "analysis_parameters": {
                "customer_segment": customer_segment,
                "min_orders_threshold": min_orders,
                "date_range": f"{orders_df['date'].min()} to {orders_df['date'].max()}",
                "total_customers_analyzed": total_customers
            },
            "customer_summary": {
                "total_active_customers": total_customers,
                "avg_orders_per_customer": round(avg_orders_per_customer, 2),
                "avg_quantity_per_customer": round(avg_quantity_per_customer, 2),
                "avg_order_frequency": round(segment_customers['order_frequency'].mean(), 4)
            },
            "top_customers_by_orders": top_by_orders.to_dict('records'),
            "top_customers_by_quantity": top_by_quantity.to_dict('records'),
            "order_size_distribution": size_distribution,
            "purchase_frequency_segments": frequency_segments,
            "insights": [
                f"Analyzed {total_customers} customers in '{customer_segment}' segment",
                f"Average customer places {avg_orders_per_customer:.1f} orders",
                f"Most loyal customer has {segment_customers['total_orders'].max()} orders",
                f"{frequency_segments['single_purchase']} customers ({frequency_segments['single_purchase']/total_customers*100:.1f}%) made only one purchase",
                f"Top customer ordered {segment_customers['total_quantity'].max()} total units"
            ]
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze customer behavior: {str(e)}"}


def analyze_product_sales_trends_tool(data_dir: str = "data", date_start: Optional[str] = None,
                                    date_end: Optional[str] = None, product_references: Optional[List[str]] = None,
                                    include_sizes: bool = True) -> Dict[str, Any]:
    """
    Analyze product-specific sales performance and trends over time.
    
    Args:
        data_dir: Directory containing CSV files (default: "data")
        date_start: Start date for analysis (YYYY-MM-DD format, optional)
        date_end: End date for analysis (YYYY-MM-DD format, optional)
        product_references: Specific product references to analyze (optional, analyzes all if None)
        include_sizes: Include size-based analysis in results (default: True)
    
    Returns:
        Dictionary with product sales trends including performance ranking and lifecycle analysis
    """
    try:
        csv_file = os.path.join(data_dir, "Customer_Order.csv")
        if not os.path.exists(csv_file):
            return {"error": f"Customer_Order.csv not found in {data_dir}"}
        
        # Load customer orders data
        orders_df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')
        
        # Parse creation date
        orders_df['creationDate'] = pd.to_datetime(orders_df['creationDate'], format='%d/%m/%Y %H:%M')
        orders_df['date'] = orders_df['creationDate'].dt.date
        orders_df['year_month'] = orders_df['creationDate'].dt.to_period('M').astype(str)
        
        # Apply date filtering if specified
        if date_start or date_end:
            def parse_date(date_str):
                if date_str is None:
                    return None
                date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
                for fmt in date_formats:
                    try:
                        return pd.to_datetime(date_str, format=fmt).date()
                    except:
                        continue
                return pd.to_datetime(date_str).date()
            
            start_parsed = parse_date(date_start) if date_start else orders_df['date'].min()
            end_parsed = parse_date(date_end) if date_end else orders_df['date'].max()
            
            orders_df = orders_df[(orders_df['date'] >= start_parsed) & (orders_df['date'] <= end_parsed)]
            
            if orders_df.empty:
                return {"error": f"No orders found in date range {start_parsed} to {end_parsed}"}
        
        # Filter by specific products if requested
        if product_references:
            orders_df = orders_df[orders_df['Reference'].isin(product_references)]
            if orders_df.empty:
                return {"error": f"No orders found for specified product references: {product_references}"}
        
        # Product performance analysis
        product_stats = orders_df.groupby('Reference').agg({
            'quantity (units)': ['sum', 'mean', 'count'],
            'orderNumber': 'nunique',
            'creationDate': ['min', 'max'],
            'codCustomer': 'nunique'
        }).round(2)
        
        product_stats.columns = ['total_quantity', 'avg_quantity_per_order', 'total_order_lines', 
                               'unique_orders', 'first_sale_date', 'last_sale_date', 'unique_customers']
        
        # Calculate product velocity metrics
        product_stats['days_in_market'] = (product_stats['last_sale_date'] - product_stats['first_sale_date']).dt.days + 1
        product_stats['daily_velocity'] = (product_stats['total_quantity'] / product_stats['days_in_market']).round(3)
        product_stats['order_frequency'] = (product_stats['total_order_lines'] / product_stats['days_in_market']).round(3)
        product_stats['customer_reach'] = product_stats['unique_customers']
        
        # Product lifecycle classification
        def classify_lifecycle(row):
            days = row['days_in_market']
            velocity = row['daily_velocity']
            recent_activity = (orders_df['date'].max() - row['last_sale_date']).days
            
            if days < 30:
                return "introduction"
            elif velocity > product_stats['daily_velocity'].quantile(0.75) and recent_activity < 30:
                return "growth"
            elif velocity < product_stats['daily_velocity'].quantile(0.25) or recent_activity > 60:
                return "decline"
            else:
                return "maturity"
        
        product_stats['lifecycle_stage'] = product_stats.apply(classify_lifecycle, axis=1)
        
        # Monthly trend analysis for top products
        top_products = product_stats.nlargest(10, 'total_quantity').index.tolist()
        monthly_trends = {}
        
        for product in top_products[:5]:  # Top 5 for detailed trends
            product_monthly = orders_df[orders_df['Reference'] == product].groupby('year_month')['quantity (units)'].sum()
            monthly_trends[product] = {
                'monthly_data': product_monthly.to_dict(),
                'trend_direction': 'stable'
            }
            
            # Calculate trend direction
            if len(product_monthly) >= 3:
                first_third = product_monthly.iloc[:len(product_monthly)//3].mean()
                last_third = product_monthly.iloc[-len(product_monthly)//3:].mean()
                if last_third > first_third * 1.2:
                    monthly_trends[product]['trend_direction'] = 'increasing'
                elif last_third < first_third * 0.8:
                    monthly_trends[product]['trend_direction'] = 'decreasing'
        
        # Size analysis if requested
        size_analysis = {}
        if include_sizes:
            size_stats = orders_df.groupby(['Reference', 'Size (US)'])['quantity (units)'].sum().reset_index()
            popular_sizes_per_product = {}
            
            for product in top_products[:10]:
                product_sizes = size_stats[size_stats['Reference'] == product].nlargest(3, 'quantity (units)')
                if not product_sizes.empty:
                    popular_sizes_per_product[product] = product_sizes[['Size (US)', 'quantity (units)']].to_dict('records')
            
            # Overall size distribution
            overall_size_dist = orders_df.groupby('Size (US)')['quantity (units)'].sum().nlargest(10)
            size_analysis = {
                'popular_sizes_per_product': popular_sizes_per_product,
                'overall_popular_sizes': overall_size_dist.to_dict()
            }
        
        # Performance ranking
        top_by_quantity = product_stats.nlargest(15, 'total_quantity')[
            ['total_quantity', 'unique_customers', 'daily_velocity', 'lifecycle_stage']
        ].reset_index()
        
        top_by_velocity = product_stats.nlargest(15, 'daily_velocity')[
            ['total_quantity', 'daily_velocity', 'unique_customers', 'lifecycle_stage']
        ].reset_index()
        
        # Lifecycle distribution
        lifecycle_dist = product_stats['lifecycle_stage'].value_counts().to_dict()
        
        # Product correlation analysis (simplified)
        # Find products often ordered together
        order_products = orders_df.groupby('orderNumber')['Reference'].apply(list).reset_index()
        frequently_together = {}
        
        for product in top_products[:5]:
            related_products = {}
            product_orders = order_products[order_products['Reference'].apply(lambda x: product in x)]
            
            for order_refs in product_orders['Reference']:
                for other_product in order_refs:
                    if other_product != product:
                        related_products[other_product] = related_products.get(other_product, 0) + 1
            
            if related_products:
                top_related = sorted(related_products.items(), key=lambda x: x[1], reverse=True)[:3]
                frequently_together[product] = [{'product': p, 'co_occurrence_count': c} for p, c in top_related]
        
        return {
            "analysis_complete": True,
            "analysis_parameters": {
                "date_range": f"{orders_df['date'].min()} to {orders_df['date'].max()}",
                "products_analyzed": len(product_stats),
                "specific_products_filter": product_references if product_references else "All products",
                "include_sizes": include_sizes
            },
            "summary_statistics": {
                "total_products": len(product_stats),
                "total_quantity_sold": int(product_stats['total_quantity'].sum()),
                "avg_product_velocity": round(product_stats['daily_velocity'].mean(), 3),
                "most_popular_product": product_stats['total_quantity'].idxmax(),
                "fastest_moving_product": product_stats['daily_velocity'].idxmax()
            },
            "performance_ranking": {
                "top_products_by_quantity": top_by_quantity.to_dict('records'),
                "top_products_by_velocity": top_by_velocity.to_dict('records')
            },
            "lifecycle_analysis": {
                "lifecycle_distribution": lifecycle_dist,
                "introduction_stage_products": len(product_stats[product_stats['lifecycle_stage'] == 'introduction']),
                "growth_stage_products": len(product_stats[product_stats['lifecycle_stage'] == 'growth']),
                "maturity_stage_products": len(product_stats[product_stats['lifecycle_stage'] == 'maturity']),
                "decline_stage_products": len(product_stats[product_stats['lifecycle_stage'] == 'decline'])
            },
            "monthly_trends": monthly_trends,
            "size_analysis": size_analysis if include_sizes else {},
            "product_correlation": frequently_together,
            "insights": [
                f"Analyzed {len(product_stats)} products across {len(orders_df)} order lines",
                f"Top product '{product_stats['total_quantity'].idxmax()}' sold {product_stats['total_quantity'].max()} units",
                f"Fastest moving product '{product_stats['daily_velocity'].idxmax()}' averages {product_stats['daily_velocity'].max():.2f} units/day",
                f"Lifecycle distribution: {lifecycle_dist.get('growth', 0)} growing, {lifecycle_dist.get('maturity', 0)} mature, {lifecycle_dist.get('decline', 0)} declining",
                f"Average product reaches {product_stats['unique_customers'].mean():.1f} unique customers",
                f"Product velocity ranges from {product_stats['daily_velocity'].min():.3f} to {product_stats['daily_velocity'].max():.3f} units/day"
            ]
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze product sales trends: {str(e)}"}