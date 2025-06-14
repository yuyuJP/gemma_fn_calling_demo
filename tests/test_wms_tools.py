#!/usr/bin/env python3
"""
Test suite for WMS (Warehouse Management System) analysis tools.
This module tests the various WMS data analysis functions including
storage utilization, picking distances, and operator performance.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import tempfile

# Add the app directory to the path so we can import tools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from tools import (
    load_storage_data, load_customer_orders, load_picking_waves,
    load_product_catalog, load_spatial_data, parse_encoded_storage,
    calculate_storage_utilization, analyze_picking_distances,
    analyze_operator_performance, analyze_product_demand
)

class TestWMSTools(unittest.TestCase):
    """Test cases for WMS analysis tools."""
    
    def setUp(self):
        """Set up test data directory."""
        self.test_data_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test data directory."""
        import shutil
        shutil.rmtree(self.test_data_dir, ignore_errors=True)
    
    def create_test_csv(self, filename, data):
        """Helper method to create test CSV files."""
        file_path = os.path.join(self.test_data_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        return file_path
    
    def test_parse_encoded_storage(self):
        """Test parsing of encoded storage data."""
        location = "A1-01-01"
        encoded_columns = ["PROD001;50", "PROD002;25", "", "PROD003;10"]
        
        result = parse_encoded_storage(location, encoded_columns)
        
        self.assertEqual(result["location"], location)
        self.assertEqual(result["products"], {"PROD001": 50, "PROD002": 25, "PROD003": 10})
        self.assertEqual(result["total_products"], 3)
        self.assertEqual(result["total_quantity"], 85)
    
    def test_parse_encoded_storage_empty(self):
        """Test parsing of empty encoded storage data."""
        location = "A1-01-02"
        encoded_columns = ["", None, ""]
        
        result = parse_encoded_storage(location, encoded_columns)
        
        self.assertEqual(result["location"], location)
        self.assertEqual(result["products"], {})
        self.assertEqual(result["total_products"], 0)
        self.assertEqual(result["total_quantity"], 0)
    
    def test_parse_encoded_storage_invalid_format(self):
        """Test parsing of malformed encoded storage data."""
        location = "A1-01-03"
        encoded_columns = ["PROD001;50", "INVALID_FORMAT", "PROD003;abc"]
        
        result = parse_encoded_storage(location, encoded_columns)
        
        # Should only parse valid entries
        self.assertEqual(result["products"], {"PROD001": 50})
        self.assertEqual(result["total_products"], 1)
        self.assertEqual(result["total_quantity"], 50)
    
    def test_load_storage_data_file_not_found(self):
        """Test loading storage data when file doesn't exist."""
        result = load_storage_data("class_based", self.test_data_dir)
        
        self.assertIn("error", result)
        self.assertIn("File not found", result["error"])
    
    def test_load_storage_data_invalid_type(self):
        """Test loading storage data with invalid storage type."""
        result = load_storage_data("invalid_type", self.test_data_dir)
        
        self.assertIn("error", result)
        self.assertIn("Invalid storage type", result["error"])
    
    def test_load_storage_data_success(self):
        """Test successful loading of storage data."""
        # Create test data
        test_data = {
            "Location": ["A1-01-01", "A1-01-02"],
            "ABCCOD": ["A", "B"],
            "col_1": ["PROD001;50", ""],
            "col_2": ["PROD002;25", "PROD003;10"]
        }
        self.create_test_csv("Class_Based_Storage.csv", test_data)
        
        result = load_storage_data("class_based", self.test_data_dir)
        
        self.assertTrue(result["data_loaded"])
        self.assertEqual(result["storage_type"], "class_based")
        self.assertEqual(result["records"], 2)
        self.assertIn("Location", result["columns"])
    
    def test_load_customer_orders_success(self):
        """Test successful loading of customer orders."""
        # Create test data
        test_data = {
            "codCustomer": ["CUST001", "CUST002"],
            "orderNumber": [1001, 1002],
            "Reference": ["PROD001", "PROD002"],
            "quantity (units)": [5, 10],
            "operator": ["OP1", "OP2"],
            "creationDate": ["2024-01-01", "2024-01-02"]
        }
        self.create_test_csv("Customer_Order.csv", test_data)
        
        result = load_customer_orders(self.test_data_dir)
        
        self.assertTrue(result["data_loaded"])
        self.assertEqual(result["total_orders"], 2)
        self.assertEqual(result["unique_customers"], 2)
    
    def test_load_picking_waves_success(self):
        """Test successful loading of picking waves."""
        # Create test data
        test_data = {
            "waveNumber": [1001, 1001, 1002],
            "reference": ["PROD001", "PROD002", "PROD003"],
            "quantityToPick (units)": [5, 10, 3],
            "operator": ["OP1", "OP1", "OP2"],
            "locations": ["A1-01-01", "A1-01-02", "A1-02-01"]
        }
        self.create_test_csv("Picking_Wave.csv", test_data)
        
        result = load_picking_waves(self.test_data_dir, [1001])
        
        self.assertTrue(result["data_loaded"])
        self.assertEqual(result["total_waves"], 1)
        self.assertEqual(result["total_picks"], 2)  # Only wave 1001 records
    
    def test_load_product_catalog_success(self):
        """Test successful loading of product catalog."""
        # Create test data
        test_data = {
            "Reference": ["PROD001", "PROD002", "PROD003"],
            "ABCCOD": ["A", "B", "A"],
            "Sector": ["Electronics", "Clothing", "Electronics"]
        }
        self.create_test_csv("Product.csv", test_data)
        
        result = load_product_catalog(self.test_data_dir)
        
        self.assertTrue(result["data_loaded"])
        self.assertEqual(result["total_products"], 3)
        self.assertEqual(result["abc_distribution"], {"A": 2, "B": 1})
    
    def test_load_spatial_data_success(self):
        """Test successful loading of spatial data."""
        # Create storage location test data
        storage_data = {
            "originalLocation": ["A1-01-01", "A1-01-02"],
            "x": [10, 15],
            "y": [20, 25],
            "z": [0, 0]
        }
        self.create_test_csv("Storage_Location.csv", storage_data)
        
        # Create support points test data
        support_data = {
            "points_specified": ["(10,20,0)", "(15,25,0)"],
            "labels": ["Point1", "Point2"]
        }
        self.create_test_csv("Support_Points.csv", support_data)
        
        result = load_spatial_data(self.test_data_dir)
        
        self.assertTrue(result["data_loaded"])
        self.assertIn("storage_locations", result)
        self.assertIn("support_points", result)
        self.assertEqual(result["storage_locations"]["records"], 2)
        self.assertEqual(result["support_points"]["records"], 2)
    
    def test_calculate_storage_utilization(self):
        """Test storage utilization calculation."""
        # Create test storage data
        test_data = {
            "Location": ["A1-01-01", "A1-01-02", "A1-01-03"],
            "ABCCOD": ["A", "B", "A"],
            "col_1": ["PROD001;50", "", "PROD003;30"],
            "col_2": ["PROD002;25", "", ""],
            "col_3": ["", "", ""]
        }
        self.create_test_csv("Class_Based_Storage.csv", test_data)
        
        result = calculate_storage_utilization("class_based", self.test_data_dir)
        
        self.assertEqual(result["storage_type"], "class_based")
        self.assertEqual(result["total_locations"], 3)
        self.assertEqual(result["occupied_locations"], 2)  # 2 locations have products
        self.assertAlmostEqual(result["utilization_rate"], 0.667, places=2)
        self.assertEqual(result["total_products_stored"], 105)  # 50+25+30
    
    def test_analyze_picking_distances_insufficient_data(self):
        """Test picking distance analysis with insufficient location data."""
        # Create minimal wave data
        wave_data = {
            "waveNumber": [1001],
            "locations": ["A1-01-01"]
        }
        self.create_test_csv("Picking_Wave.csv", wave_data)
        
        # Create spatial data
        spatial_data = {
            "originalLocation": ["A1-01-01"],
            "x": [10],
            "y": [20],
            "z": [0]
        }
        self.create_test_csv("Storage_Location.csv", spatial_data)
        
        result = analyze_picking_distances(1001, self.test_data_dir)
        
        self.assertEqual(result["wave_number"], 1001)
        self.assertEqual(result["total_picking_distance"], 0)
        self.assertEqual(result["locations_count"], 1)
        self.assertIn("Insufficient location data", result["message"])

    def test_analyze_product_demand(self):
        """Test product demand analysis."""
        # Create test order data
        test_data = {
            "Reference": ["PROD001", "PROD001", "PROD002", "PROD003"],
            "quantity (units)": [10, 5, 20, 3],
            "codCustomer": ["CUST001", "CUST002", "CUST001", "CUST003"]
        }
        self.create_test_csv("Customer_Order.csv", test_data)
        
        result = analyze_product_demand(self.test_data_dir)
        
        self.assertTrue(result["analysis_complete"])
        self.assertEqual(result["total_products"], 3)
        self.assertEqual(result["total_demand_across_all_products"], 38)
        
        # Top product should be PROD002 with 20 total demand
        top_product = result["top_10_products_by_demand"][0]
        self.assertEqual(top_product["Reference"], "PROD002")
        self.assertEqual(top_product["total_demand"], 20.0)

def main():
    """Run the WMS tools test suite."""
    print("Testing WMS (Warehouse Management System) Analysis Tools...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWMSTools)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All WMS tools tests passed!")
    else:
        print("❌ Some WMS tools tests failed")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)