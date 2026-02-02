#!/usr/bin/env python
"""Test script for API status endpoint"""

import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:5000"

def test_api_status():
    """Test API status endpoints"""
    
    print("Testing API Status Endpoints")
    print("=" * 50)
    
    # Test 1: Get current status
    print("\n1. Testing GET /api/status/")
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/api/status/")
        data = json.loads(response.read().decode())
        print(f"   Status Code: {response.status}")
        print(f"   Response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Toggle API status
    print("\n2. Testing POST /api/status/toggle")
    try:
        data = json.dumps({"toggled_by": "test_script"}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/status/toggle",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read().decode())
        print(f"   Status Code: {response.status}")
        print(f"   Response: {json.dumps(response_data, indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Get status after toggle
    print("\n3. Testing GET /api/status/ (after toggle)")
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/api/status/")
        data = json.loads(response.read().decode())
        print(f"   Status Code: {response.status}")
        print(f"   Response: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Toggle back to enabled
    print("\n4. Testing POST /api/status/toggle (toggle back)")
    try:
        data = json.dumps({"toggled_by": "test_script"}).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/status/toggle",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read().decode())
        print(f"   Status Code: {response.status}")
        print(f"   Response: {json.dumps(response_data, indent=2)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("API Status Tests Complete")

if __name__ == "__main__":
    test_api_status()
