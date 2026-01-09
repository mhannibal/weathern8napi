#!/usr/bin/env python3
"""
Test script for the Weather Map API.

Usage:
    1. Start the server: python app.py
    2. Run this script: python test_api.py
"""

import json
import requests
import sys

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing /health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_countries():
    """Test countries endpoint."""
    print("\n🔍 Testing /countries endpoint...")
    response = requests.get(f"{API_BASE}/countries")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_generate_map():
    """Test map generation with meteo.json data."""
    print("\n🔍 Testing /generate/raw endpoint...")
    
    # Load meteo data
    with open("meteo.json", "r") as f:
        meteo_data = json.load(f)
    
    # Send request
    response = requests.post(
        f"{API_BASE}/generate/raw",
        json=meteo_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        # Save the image
        output_file = "api_test_output.png"
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        # Check for saved path in headers
        saved_path = response.headers.get("X-Saved-Path")
        if saved_path:
            print(f"   📁 Server saved to: {saved_path}")
        
        print(f"   ✅ Image saved to: {output_file}")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False

def test_generate_with_options():
    """Test map generation with custom options."""
    print("\n🔍 Testing /generate endpoint with custom title...")
    
    # Load meteo data
    with open("meteo.json", "r") as f:
        meteo_data = json.load(f)
    
    # Send request with wrapper
    payload = {
        "meteo_data": meteo_data,
        "title": "Algeria Weather - Custom Title Test",
        "day_index": 0
    }
    
    response = requests.post(
        f"{API_BASE}/generate",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        output_file = "api_test_custom_output.png"
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        # Check for saved path in headers
        saved_path = response.headers.get("X-Saved-Path")
        if saved_path:
            print(f"   📁 Server saved to: {saved_path}")
        
        print(f"   ✅ Image saved to: {output_file}")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False

def main():
    print("=" * 50)
    print("Weather Map API Test Suite")
    print("=" * 50)
    
    try:
        # Test root endpoint
        response = requests.get(f"{API_BASE}/")
        print(f"\n📡 API Root: {response.json()}")
    except requests.ConnectionError:
        print("\n❌ Cannot connect to API. Make sure the server is running:")
        print("   python app.py")
        sys.exit(1)
    
    results = []
    
    results.append(("Health Check", test_health()))
    results.append(("Countries List", test_countries()))
    results.append(("Generate Map (Raw)", test_generate_map()))
    results.append(("Generate Map (Options)", test_generate_with_options()))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️ Some tests failed"))
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
