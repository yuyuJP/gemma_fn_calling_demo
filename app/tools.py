from datetime import datetime
import random
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

def random_joke() -> str:
    """Return a canned dad joke."""
    jokes = [
        "I told my computer I needed a break, and it said ‘no problem — I’ll go to sleep.’",
        "Why do programmers prefer dark mode? Because light attracts bugs.",
    ]
    return random.choice(jokes)

# WMS Data Analysis Tools

def load_storage_data(storage_type: str, data_dir: str = "data") -> Dict[str, Any]:
    """Load storage data (class_based, dedicated, hybrid, or random)."""
    try:
        file_mapping = {
            "class_based": "Class_Based_Storage.csv",
            "dedicated": "Dedicated_Storage.csv", 
            "hybrid": "Hybrid_Storage.csv",
            "random": "Random_Storage.csv"
        }
        
        if storage_type not in file_mapping:
            return {"error": f"Invalid storage type. Must be one of: {list(file_mapping.keys())}"}
        
        file_path = os.path.join(data_dir, file_mapping[storage_type])
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        df = pd.read_csv(file_path)
        return {
            "storage_type": storage_type,
            "data_loaded": True,
            "records": len(df),
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
    except Exception as e:
        return {"error": f"Failed to load {storage_type} storage data: {str(e)}"}

def load_customer_orders(data_dir: str = "data", date_filter: Optional[str] = None) -> Dict[str, Any]:
    """Load customer orders with optional date filtering."""
    try:
        file_path = os.path.join(data_dir, "Customer_Order.csv")
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        df = pd.read_csv(file_path)
        
        if date_filter:
            try:
                df['creationDate'] = pd.to_datetime(df['creationDate'])
                df = df[df['creationDate'].dt.date == pd.to_datetime(date_filter).date()]
            except Exception as e:
                return {"error": f"Date filtering failed: {str(e)}"}
        
        return {
            "data_loaded": True,
            "total_orders": len(df),
            "unique_customers": df['codCustomer'].nunique() if 'codCustomer' in df.columns else 0,
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
    except Exception as e:
        return {"error": f"Failed to load customer orders: {str(e)}"}

def load_picking_waves(data_dir: str = "data", wave_numbers: Optional[List[int]] = None) -> Dict[str, Any]:
    """Load picking wave data for specified waves."""
    try:
        file_path = os.path.join(data_dir, "Picking_Wave.csv")
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        df = pd.read_csv(file_path)
        
        if wave_numbers:
            df = df[df['waveNumber'].isin(wave_numbers)]
        
        return {
            "data_loaded": True,
            "total_waves": df['waveNumber'].nunique() if 'waveNumber' in df.columns else 0,
            "total_picks": len(df),
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
    except Exception as e:
        return {"error": f"Failed to load picking waves: {str(e)}"}

def load_product_catalog(data_dir: str = "data") -> Dict[str, Any]:
    """Load product reference data with ABC classifications."""
    try:
        file_path = os.path.join(data_dir, "Product.csv")
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        df = pd.read_csv(file_path)
        
        abc_distribution = df['ABCCOD'].value_counts().to_dict() if 'ABCCOD' in df.columns else {}
        
        return {
            "data_loaded": True,
            "total_products": len(df),
            "abc_distribution": abc_distribution,
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
    except Exception as e:
        return {"error": f"Failed to load product catalog: {str(e)}"}

def load_spatial_data(data_dir: str = "data") -> Dict[str, Any]:
    """Load 3D warehouse coordinates and location mappings."""
    try:
        storage_file = os.path.join(data_dir, "Storage_Location.csv")
        support_file = os.path.join(data_dir, "Support_Points.csv")
        
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
            support_df = pd.read_csv(support_file)
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

def parse_encoded_storage(location: str, encoded_columns: List[str]) -> Dict[str, Any]:
    """Parse encoded product details from storage columns (product_code;quantity)."""
    try:
        products = {}
        
        for col_data in encoded_columns:
            if col_data and isinstance(col_data, str) and ';' in col_data:
                try:
                    code, qty = col_data.split(';', 1)
                    products[code.strip()] = int(qty.strip())
                except (ValueError, IndexError):
                    continue
        
        return {
            "location": location,
            "products": products,
            "total_products": len(products),
            "total_quantity": sum(products.values())
        }
        
    except Exception as e:
        return {"error": f"Failed to parse encoded storage: {str(e)}"}

def calculate_storage_utilization(storage_type: str, data_dir: str = "data") -> Dict[str, Any]:
    """Calculate utilization rates for different storage strategies."""
    try:
        storage_data_result = load_storage_data(storage_type, data_dir)
        
        if "error" in storage_data_result:
            return storage_data_result
        
        file_mapping = {
            "class_based": "Class_Based_Storage.csv",
            "dedicated": "Dedicated_Storage.csv",
            "hybrid": "Hybrid_Storage.csv", 
            "random": "Random_Storage.csv"
        }
        
        file_path = os.path.join(data_dir, file_mapping[storage_type])
        df = pd.read_csv(file_path)
        
        total_locations = len(df)
        occupied_locations = 0
        total_products_stored = 0
        
        location_col = 'Location' if 'Location' in df.columns else 'originalLocation'
        
        for _, row in df.iterrows():
            encoded_columns = []
            for i in range(1, 19):
                col_name = f'col_{i}'
                if col_name in df.columns and pd.notna(row[col_name]):
                    encoded_columns.append(str(row[col_name]))
            
            if encoded_columns:
                parsed = parse_encoded_storage(row[location_col], encoded_columns)
                if "error" not in parsed and parsed['products']:
                    occupied_locations += 1
                    total_products_stored += parsed['total_quantity']
        
        utilization_rate = occupied_locations / total_locations if total_locations > 0 else 0
        
        return {
            "storage_type": storage_type,
            "total_locations": total_locations,
            "occupied_locations": occupied_locations,
            "utilization_rate": round(utilization_rate, 3),
            "total_products_stored": total_products_stored,
            "avg_products_per_location": round(total_products_stored / occupied_locations, 2) if occupied_locations > 0 else 0
        }
        
    except Exception as e:
        return {"error": f"Failed to calculate storage utilization: {str(e)}"}

def analyze_picking_distances(wave_number: int, data_dir: str = "data") -> Dict[str, Any]:
    """Calculate total picking distances for a wave using 3D coordinates."""
    try:
        waves_file = os.path.join(data_dir, "Picking_Wave.csv")
        spatial_file = os.path.join(data_dir, "Storage_Location.csv")
        
        if not os.path.exists(waves_file):
            return {"error": f"Picking waves file not found: {waves_file}"}
        if not os.path.exists(spatial_file):
            return {"error": f"Spatial data file not found: {spatial_file}"}
        
        waves_df = pd.read_csv(waves_file)
        spatial_df = pd.read_csv(spatial_file)
        
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

def analyze_operator_performance(data_dir: str = "data") -> Dict[str, Any]:
    """Comprehensive operator performance analysis."""
    try:
        orders_file = os.path.join(data_dir, "Customer_Order.csv")
        waves_file = os.path.join(data_dir, "Picking_Wave.csv")
        
        if not os.path.exists(orders_file):
            return {"error": f"Orders file not found: {orders_file}"}
        if not os.path.exists(waves_file):
            return {"error": f"Waves file not found: {waves_file}"}
        
        orders_df = pd.read_csv(orders_file)
        waves_df = pd.read_csv(waves_file)
        
        if 'operator' not in orders_df.columns or 'operator' not in waves_df.columns:
            return {"error": "Operator column not found in data files"}
        
        operator_stats = []
        
        for operator in orders_df['operator'].unique():
            if pd.isna(operator):
                continue
                
            op_orders = orders_df[orders_df['operator'] == operator]
            op_waves = waves_df[waves_df['operator'] == operator]
            
            total_items = op_orders['quantity (units)'].sum() if 'quantity (units)' in op_orders.columns else 0
            total_orders = len(op_orders)
            avg_wave_size = op_waves['quantityToPick (units)'].mean() if 'quantityToPick (units)' in op_waves.columns and len(op_waves) > 0 else 0
            
            distances = []
            for wave_num in op_waves['waveNumber'].unique():
                if pd.notna(wave_num):
                    dist_result = analyze_picking_distances(int(wave_num), data_dir)
                    if "error" not in dist_result and dist_result['avg_distance_per_pick'] > 0:
                        distances.append(dist_result['avg_distance_per_pick'])
            
            avg_distance = np.mean(distances) if distances else 0
            efficiency_score = (total_items / avg_distance) if avg_distance > 0 else total_items
            
            operator_stats.append({
                "operator": str(operator),
                "total_items_picked": int(total_items),
                "total_orders": total_orders,
                "total_waves": len(op_waves),
                "avg_wave_size": round(float(avg_wave_size), 2),
                "avg_picking_distance": round(avg_distance, 2),
                "efficiency_score": round(efficiency_score, 2)
            })
        
        operator_stats.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        return {
            "analysis_complete": True,
            "total_operators": len(operator_stats),
            "operator_performance": operator_stats[:10]  # Top 10 performers
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze operator performance: {str(e)}"}

def analyze_product_demand(data_dir: str = "data") -> Dict[str, Any]:
    """Analyze product demand based on customer orders."""
    try:
        orders_file = os.path.join(data_dir, "Customer_Order.csv")
        
        if not os.path.exists(orders_file):
            return {"error": f"Orders file not found: {orders_file}"}
        
        orders_df = pd.read_csv(orders_file)
        
        if 'Reference' not in orders_df.columns or 'quantity (units)' not in orders_df.columns:
            return {"error": "Required columns (Reference, quantity) not found in orders data"}
        
        demand_analysis = orders_df.groupby('Reference')['quantity (units)'].agg([
            'sum', 'count', 'mean'
        ]).round(2)
        
        demand_analysis.columns = ['total_demand', 'order_frequency', 'avg_quantity_per_order']
        demand_analysis = demand_analysis.sort_values('total_demand', ascending=False)
        
        top_products = demand_analysis.head(10).reset_index().to_dict('records')
        
        return {
            "analysis_complete": True,
            "total_products": len(demand_analysis),
            "top_10_products_by_demand": top_products,
            "total_demand_across_all_products": int(demand_analysis['total_demand'].sum())
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze product demand: {str(e)}"}
