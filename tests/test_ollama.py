#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import ollama
from app.config import MODEL_NAME

def test_ollama_connection():
    """Test basic Ollama connectivity."""
    print(f"Testing Ollama with model: {MODEL_NAME}")
    
    try:
        client = ollama.Client()
        
        # Test basic chat
        response = client.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": "Hello, respond with just 'OK'"}
            ]
        )
        
        content = response['message']['content']
        print(f"Ollama response: {content}")
        
        assert response is not None
        assert len(content) > 0
        
        return True
        
    except Exception as e:
        print(f"Ollama test failed: {e}")
        print("Make sure Ollama is running and gemma3:12b model is available")
        print("Try: ollama pull gemma3:12b")
        return False

if __name__ == "__main__":
    if test_ollama_connection():
        print("Ollama test PASSED")
    else:
        print("Ollama test FAILED")