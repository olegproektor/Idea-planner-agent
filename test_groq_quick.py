#!/usr/bin/env python3
"""
Quick smoke test for Groq API integration.

This script tests the basic functionality of the GroqProvider class:
1. Check groq import
2. Check GROQ_API_KEY env var
3. Initialize client
4. Test Russian output ("Скажи Привет!")
5. Print tokens used
6. Exit 0 on success, 1 on failure

Usage:
    python test_groq_quick.py
    
Environment:
    GROQ_API_KEY: Your Groq API key
"""

import os
import sys
import time

# Test 1: Check groq import
try:
    print("📦 Test 1: Checking groq import...")
    from src.llm.groq_provider import GroqProvider
    print("✅ GroqProvider imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {str(e)}")
    sys.exit(1)

# Test 2: Check GROQ_API_KEY env var
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("❌ Test 2: GROQ_API_KEY environment variable not set")
    print("   Please set GROQ_API_KEY environment variable")
    sys.exit(1)
else:
    print("✅ Test 2: GROQ_API_KEY found")

# Test 3: Initialize client
try:
    print("🔧 Test 3: Initializing GroqProvider...")
    client = GroqProvider(api_key=groq_api_key)
    print(f"✅ Test 3: Client initialized with model: {client.model}")
except Exception as e:
    print(f"❌ Test 3: Initialization failed: {str(e)}")
    sys.exit(1)

# Test 4: Test Russian output
try:
    print("🤖 Test 4: Testing Russian output...")
    start_time = time.time()
    
    result = client.generate(
        prompt="Скажи Привет!",
        max_tokens=50,
        temperature=0.7
    )
    
    end_time = time.time()
    
    # Verify result structure
    required_keys = ['text', 'tokens_used', 'model', 'timestamp']
    missing_keys = [key for key in required_keys if key not in result]
    
    if missing_keys:
        print(f"❌ Test 4: Missing keys in result: {missing_keys}")
        sys.exit(1)
    
    # Print results
    print(f"✅ Test 4: Generation successful")
    print(f"   Generated: {result['text'][:100]}...")
    print(f"   Tokens used: {result['tokens_used']}")
    print(f"   Latency: {end_time - start_time:.2f}s")
    print(f"   Model: {result['model']}")
    
except Exception as e:
    print(f"❌ Test 4: Generation failed: {str(e)}")
    sys.exit(1)

# Test 5: Context manager support
try:
    print("🔄 Test 5: Testing context manager...")
    with GroqProvider(api_key=groq_api_key) as ctx_client:
        ctx_result = ctx_client.generate("Привет!", max_tokens=20)
    print("✅ Test 5: Context manager works")
except Exception as e:
    print(f"❌ Test 5: Context manager failed: {str(e)}")
    sys.exit(1)

# All tests passed
print("\n🎉 All tests passed! Groq API integration is working correctly.")
print("🚀 Ready for Task-007: Groq API Integration")
sys.exit(0)