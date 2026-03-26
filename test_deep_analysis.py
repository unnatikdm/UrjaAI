#!/usr/bin/env python3

import requests
import json

# Test login to get token
login_url = "http://localhost:8000/auth/login"
login_data = {
    "username": "admin",
    "password": "urjaai123"
}

try:
    print("Testing login...")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print(f"✅ Login successful. Token: {token[:20]}...")
        
        # Test RAG status
        rag_status_url = "http://localhost:8000/rag/status"
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\nTesting RAG status...")
        rag_response = requests.get(rag_status_url, headers=headers)
        print(f"RAG Status Response: {rag_response.status_code}")
        if rag_response.status_code == 200:
            print(f"RAG Status: {rag_response.json()}")
        
        # Test deep recommendations
        deep_rec_url = "http://localhost:8000/rag/deep-recommendations"
        deep_rec_data = {
            "building_id": "admin_block",
            "temperature_offset": 0.0,
            "occupancy_multiplier": 1.0
        }
        
        print("\nTesting deep recommendations...")
        deep_response = requests.post(deep_rec_url, json=deep_rec_data, headers=headers)
        print(f"Deep Recs Response: {deep_response.status_code}")
        if deep_response.status_code == 200:
            result = deep_response.json()
            print(f"✅ Deep recommendations working! Found {len(result)} recommendations")
            for i, rec in enumerate(result[:2]):  # Show first 2
                print(f"  {i+1}. {rec.get('action', 'N/A')} - Priority: {rec.get('priority', 'N/A')}")
        else:
            print(f"❌ Error: {deep_response.text}")
            
    else:
        print(f"❌ Login failed: {login_response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
