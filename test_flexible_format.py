#!/usr/bin/env python3
"""
Test the API with wrapped JSON format (the format that was causing 422 error).
"""

import json
import requests

API_BASE = "http://localhost:8000"

# Load meteo data
with open("meteo.json") as f:
    meteo_data = json.load(f)

# Test 1: Direct format (should work)
print("Test 1: Direct JSON array format")
print("=" * 60)
response = requests.post(
    f"{API_BASE}/generate/all",
    json=meteo_data
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Direct format works!")
else:
    print(f"❌ Error: {response.text[:200]}")

# Test 2: Wrapped format with string (the problematic format)
print("\n\nTest 2: Wrapped format with JSON string")
print("=" * 60)
wrapped_data = {
    "json": json.dumps(meteo_data)
}
response = requests.post(
    f"{API_BASE}/generate/all",
    json=wrapped_data
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"✅ Wrapped format works! Generated {result['count']} maps")
else:
    print(f"❌ Error: {response.text[:200]}")

# Test 3: Wrapped format with object
print("\n\nTest 3: Wrapped format with JSON object")
print("=" * 60)
wrapped_data_obj = {
    "json": meteo_data
}
response = requests.post(
    f"{API_BASE}/generate/all",
    json=wrapped_data_obj
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"✅ Wrapped object format works! Generated {result['count']} maps")
else:
    print(f"❌ Error: {response.text[:200]}")

print("\n" + "=" * 60)
print("All format tests completed!")
