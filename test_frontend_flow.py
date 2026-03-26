#!/usr/bin/env python3

import requests
import json

# Test the exact flow the frontend uses
def test_frontend_flow():
    print("=== Testing Frontend Flow ===")
    
    # Step 1: Login
    login_url = "http://localhost:8000/auth/login"
    login_data = {
        "username": "admin",
        "password": "urjaai123"
    }
    
    try:
        print("1. Testing login...")
        login_response = requests.post(login_url, json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
            
        token = login_response.json().get("access_token")
        print(f"✅ Login successful")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Step 2: Get buildings (frontend does this first)
        print("\n2. Getting buildings...")
        buildings_response = requests.get("http://localhost:8000/buildings", headers=headers)
        if buildings_response.status_code == 200:
            buildings = buildings_response.json().get("buildings", [])
            print(f"✅ Buildings found: {buildings}")
            building_id = buildings[0] if buildings else "admin_block"
        else:
            print(f"❌ Buildings failed: {buildings_response.text}")
            building_id = "admin_block"
        
        # Step 3: Test deep recommendations exactly like frontend
        print(f"\n3. Testing deep recommendations for {building_id}...")
        deep_rec_url = "http://localhost:8000/rag/deep-recommendations"
        deep_rec_data = {
            "building_id": building_id,
            "temperature_offset": 0.0,
            "occupancy_multiplier": 1.0
        }
        
        deep_response = requests.post(deep_rec_url, json=deep_rec_data, headers=headers)
        print(f"Status: {deep_response.status_code}")
        print(f"Response: {deep_response.text[:500]}...")
        
        if deep_response.status_code == 200:
            result = deep_response.json()
            print(f"✅ Deep recommendations working! Found {len(result)} recommendations")
            for i, rec in enumerate(result[:2]):
                print(f"  {i+1}. {rec.get('action', 'N/A')}")
                print(f"     Priority: {rec.get('priority', 'N/A')}")
                print(f"     Savings: {rec.get('savings_kwh', 'N/A')} kWh")
        else:
            print(f"❌ Deep recommendations failed")
            
        # Step 4: Test regular recommendations (frontend fallback)
        print(f"\n4. Testing regular recommendations...")
        reg_rec_url = "http://localhost:8000/recommendations"
        reg_rec_data = {
            "building_id": building_id,
            "temperature_offset": 0.0,
            "occupancy_multiplier": 1.0
        }
        
        reg_response = requests.post(reg_rec_url, json=reg_rec_data, headers=headers)
        print(f"Regular recommendations status: {reg_response.status_code}")
        
        if reg_response.status_code == 200:
            reg_result = reg_response.json()
            print(f"✅ Regular recommendations working: {len(reg_result)} found")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_frontend_flow()
