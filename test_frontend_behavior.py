#!/usr/bin/env python3

import requests
import json

def test_frontend_behavior():
    print("=== Testing Frontend Behavior ===")
    
    # Test 1: Check if frontend is using mock or real API
    print("1. Testing if frontend uses mock data...")
    
    # Try to access a regular endpoint without auth
    try:
        buildings_response = requests.get("http://localhost:8000/buildings", timeout=5)
        if buildings_response.status_code == 200:
            print("✅ Backend is accessible for buildings")
            buildings = buildings_response.json().get("buildings", [])
            print(f"   Available buildings: {buildings}")
        else:
            print(f"❌ Buildings endpoint failed: {buildings_response.status_code}")
    except Exception as e:
        print(f"❌ Buildings endpoint error: {e}")
        return
    
    # Test 2: Simulate exact frontend flow
    print("\n2. Simulating frontend login flow...")
    
    try:
        # Login like frontend does
        login_data = {"username": "admin", "password": "urjaai123"}
        login_response = requests.post("http://localhost:8000/auth/login", json=login_data, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Frontend login would fail: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
        
        token = login_response.json().get("access_token")
        print("✅ Frontend login simulation successful")
        
        # Create headers like frontend does
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test 3: Try the exact deep recommendations call
        print("\n3. Testing deep recommendations like frontend...")
        
        # Test with different building IDs that frontend might use
        test_cases = [
            "admin_block",
            "main_library", 
            "engineering_block",
            "",  # Empty building ID
            None,  # Null building ID
            "undefined"
        ]
        
        for building_id in test_cases:
            if building_id is None:
                print(f"   Testing with None building_id...")
                payload = {}
            else:
                print(f"   Testing with '{building_id}'...")
                payload = {"building_id": building_id}
            
            try:
                response = requests.post(
                    "http://localhost:8000/rag/deep-recommendations",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                print(f"      Status: {response.status_code}")
                if response.status_code == 404:
                    print(f"      ❌ 404 Error - Response: {response.text[:100]}")
                elif response.status_code == 200:
                    data = response.json()
                    print(f"      ✅ Success - {len(data)} recommendations")
                else:
                    print(f"      ⚠️  Other error: {response.text[:100]}")
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}")
        
        # Test 4: Check if there are any routing issues
        print("\n4. Checking API routing...")
        
        # Test if RAG router is properly registered
        endpoints_to_test = [
            "/rag/status",
            "/rag/deep-recommendations", 
            "/rag/chat",
            "/docs",
            "/buildings"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                if endpoint == "/rag/status":
                    response = requests.get(f"http://localhost:8000{endpoint}", headers=headers, timeout=5)
                elif endpoint == "/rag/deep-recommendations":
                    response = requests.post(f"http://localhost:8000{endpoint}", 
                                       json={"building_id": "admin_block"}, headers=headers, timeout=5)
                elif endpoint == "/buildings":
                    response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                else:
                    response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                
                print(f"   {endpoint}: {response.status_code}")
                
            except Exception as e:
                print(f"   {endpoint}: Error - {e}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_frontend_behavior()
