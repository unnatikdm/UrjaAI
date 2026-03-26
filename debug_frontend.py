#!/usr/bin/env python3

import requests
import json

# Test what happens when we access the deep recommendations page
# Simulate the exact flow the frontend would use

def debug_frontend_issue():
    print("=== Debugging Frontend 404 Issue ===")
    
    # Step 1: Check if frontend is actually using real API
    print("1. Checking frontend environment...")
    try:
        # Try to access frontend's health or config
        response = requests.get("http://localhost:5173/", timeout=5)
        print(f"Frontend accessible: {response.status_code == 200}")
    except:
        print("❌ Frontend not accessible")
        return
    
    # Step 2: Test login and get token
    print("\n2. Getting authentication token...")
    try:
        login_response = requests.post(
            "http://localhost:8000/auth/login",
            json={"username": "admin", "password": "urjaai123"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
            
        token = login_response.json().get("access_token")
        print(f"✅ Got token: {token[:20]}...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 3: Test the exact endpoint that's failing
    print("\n3. Testing /rag/deep-recommendations endpoint...")
    try:
        deep_response = requests.post(
            "http://localhost:8000/rag/deep-recommendations",
            json={"building_id": "admin_block"},
            headers=headers
        )
        
        print(f"Status Code: {deep_response.status_code}")
        print(f"Response: {deep_response.text[:200]}...")
        
        if deep_response.status_code == 404:
            print("❌ 404 Error - Endpoint not found!")
            print("Checking available endpoints...")
            
            # Test if RAG router is properly registered
            try:
                rag_status = requests.get("http://localhost:8000/rag/status", headers=headers)
                print(f"RAG Status endpoint: {rag_status.status_code}")
            except:
                print("❌ RAG status endpoint also not found")
                
            # Check all available endpoints
            try:
                docs_response = requests.get("http://localhost:8000/docs")
                print(f"API Docs accessible: {docs_response.status_code == 200}")
            except:
                print("❌ API docs not accessible")
                
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    # Step 4: Check if buildingId is the issue
    print("\n4. Testing with different building IDs...")
    test_buildings = ["admin_block", "main_library", "engineering_block", "invalid_building"]
    
    for building_id in test_buildings:
        try:
            response = requests.post(
                "http://localhost:8000/rag/deep-recommendations",
                json={"building_id": building_id},
                headers=headers
            )
            print(f"Building '{building_id}': {response.status_code}")
        except Exception as e:
            print(f"Building '{building_id}': Error - {e}")

if __name__ == "__main__":
    debug_frontend_issue()
