#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.tools import get_time

def test_timezone_normalization():
    """Test that timezone normalization works correctly."""
    test_cases = [
        "Tokyo",
        "T0kyo",  # with zero instead of 'o'
        "JST",
        "New York", 
        "London",
        "Asia/Tokyo",  # already correct
        "UTC"
    ]
    
    for tz in test_cases:
        print(f"Testing: '{tz}'")
        result = get_time(tz)
        print(f"Result: {result}\n")
        
        # Basic assertions
        assert result is not None
        assert len(result) > 0

def test_misspelled_timezone():
    """Test that misspelled timezones are handled correctly."""
    result = get_time("T0kyo")  # zero instead of 'o'
    assert "Asia/Tokyo" in result
    print(f"Misspelled timezone test passed: {result}")

if __name__ == "__main__":
    test_timezone_normalization()
    test_misspelled_timezone()
    print("All timezone tests passed!")