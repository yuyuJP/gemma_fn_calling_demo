#!/usr/bin/env python3
"""
Integration tests for the HTTP API endpoint.
Requires the chat server to be running on localhost:8001.
"""

import requests
import json
import sys
import os

def chat(msg):
    """Send a chat message to the HTTP API."""
    try:
        r = requests.post("http://localhost:8001/v1/chat",
                          json={"user_message": msg}, timeout=30)
        r.raise_for_status()
        response_data = r.json()
        return response_data.get("response", "")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to chat server on localhost:8001")
        print("Make sure to run: python app/chat_server.py")
        raise

def test_bad_timezone_then_retry():
    """Test that misspelled timezone gets corrected through retry logic."""
    reply = chat("Time in T0kyo pls")   # zero instead of 'o'
    assert "Asia/Tokyo" in reply or "Tokyo" in reply or "JST" in reply
    print(f"Retry test passed: {reply}")

def test_basic_chat():
    """Test basic chat functionality."""
    reply = chat("Hello")
    assert reply is not None
    assert len(reply) > 0
    print(f"Basic chat test passed: {reply}")

def test_tool_calling():
    """Test tool calling through HTTP API."""
    reply = chat("What time is it in London?")
    assert "London" in reply or "GMT" in reply or "BST" in reply
    print(f"Tool calling test passed: {reply}")

def test_joke_tool():
    """Test joke tool through HTTP API."""
    reply = chat("Tell me a programming joke")
    assert reply is not None
    assert len(reply) > 0
    print(f"Joke test passed: {reply}")

def run_all_tests():
    """Run all HTTP API tests."""
    tests = [
        ("Basic chat", test_basic_chat),
        ("Tool calling", test_tool_calling),
        ("Joke tool", test_joke_tool),
        ("Retry with misspelled timezone", test_bad_timezone_then_retry)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- Running {name} ---")
        try:
            test_func()
            results.append((name, True))
            print(f"{name}: PASSED")
        except Exception as e:
            results.append((name, False))
            print(f"{name}: FAILED - {e}")
    
    print(f"\n--- Test Results ---")
    for name, result in results:
        print(f"{name}: {'PASSED' if result else 'FAILED'}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    run_all_tests()
