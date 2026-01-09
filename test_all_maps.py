#!/usr/bin/env python3
"""
Test script for generating all 4 weather map types.
"""

import json
import requests

API_BASE = "http://localhost:8000"

def test_generate_all_maps():
    """Test generating all 4 map types."""
    print("🗺️  Testing /generate/all endpoint...")
    print("=" * 60)
    
    # Load meteo data
    with open("meteo.json", "r") as f:
        meteo_data = json.load(f)
    
    # Send request
    response = requests.post(
        f"{API_BASE}/generate/all",
        json=meteo_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Successfully generated {result['count']} maps for country: {result['country']}")
        print("\n📁 Generated files:")
        for map_type, path in result['generated_files'].items():
            print(f"   {map_type:10s} -> {path}")
        return True
    else:
        print(f"\n❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Server is running: {response.json()}\n")
    except requests.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python app.py")
        exit(1)
    
    success = test_generate_all_maps()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 All maps generated successfully!")
        print("\nView the generated files in:")
        print("   meteo/dz/[today's date]/")
    else:
        print("\n⚠️  Test failed")
        exit(1)
