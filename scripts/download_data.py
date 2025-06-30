#!/usr/bin/env python3
"""
Data Download Script for WMS Dataset

Downloads the Warehouse Management System dataset from Mendeley Data.
Source: Javier Rubio-Herrero (2024), "Warehouse Management System Dataset", 
        Mendeley Data, V1, DOI: 10.17632/pf2w725pw3.1
"""

import os
import sys
import zipfile
import urllib.request
from pathlib import Path


def download_dataset():
    """Download and extract the WMS dataset."""
    
    # Dataset information
    dataset_url = "https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/pf2w725pw3-1.zip"
    zip_filename = "pf2w725pw3-1.zip"
    
    # Get the project root directory (parent of scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    print(f"Downloading WMS dataset...")
    print(f"Source: {dataset_url}")
    print(f"Target directory: {data_dir}")
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    zip_path = data_dir / zip_filename
    
    try:
        # Download the ZIP file
        print(f"Downloading {zip_filename}...")
        urllib.request.urlretrieve(dataset_url, zip_path)
        print(f"Downloaded {zip_path}")
        
        # Extract the ZIP file
        print(f"Extracting {zip_filename}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print(f"Extracted to {data_dir}")
        
        # Clean up ZIP file
        zip_path.unlink()
        print(f"Removed {zip_filename}")
        
        # Rename folders/files with spaces to use underscores
        print(f"Renaming files and folders with spaces...")
        renamed_count = 0
        for item_path in data_dir.rglob("*"):
            if " " in item_path.name:
                new_name = item_path.name.replace(" ", "_")
                new_path = item_path.parent / new_name
                item_path.rename(new_path)
                print(f"  Renamed: {item_path.name} -> {new_name}")
                renamed_count += 1
        
        if renamed_count > 0:
            print(f"Renamed {renamed_count} items with spaces")
        else:
            print("No items with spaces found")
        
        # List extracted files
        print(f"\nExtracted files:")
        for file_path in sorted(data_dir.glob("*")):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  {file_path.name} ({size_mb:.2f} MB)")
        
        print(f"\nDataset successfully downloaded and extracted to: {data_dir}")
        print(f"You can now use the WMS analysis tools with this data.")
        
    except Exception as e:
        print(f"Error downloading dataset: {e}", file=sys.stderr)
        # Clean up partially downloaded file
        if zip_path.exists():
            zip_path.unlink()
        sys.exit(1)


if __name__ == "__main__":
    download_dataset()