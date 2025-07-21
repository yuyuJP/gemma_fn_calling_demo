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