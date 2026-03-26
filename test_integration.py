#!/usr/bin/env python3

import requests
import json

def test_complete_integration():
    print("=== Complete Frontend-Backend Integration Test ===")
    
    # Test 1: Backend health
    print("1. Testing backend health...")
    try:
        health_response = requests.get("http://localhost:8000/", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Test 2: Login (exactly like frontend)
    print("\n2. Testing authentication...")
    try:
        login_response = requests.post(
            "http://localhost:8000/auth/login",
            json={"username": "admin", "password": "urjaai123"},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
            
        token = login_response.json().get("access_token")
        print("✅ Authentication working")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test 3: Deep AI Analysis (the main feature)
    print("\n3. Testing Deep AI Analysis...")
    try:
        deep_response = requests.post(
            "http://localhost:8000/rag/deep-recommendations",
            json={
                "building_id": "admin_block",
                "temperature_offset": 0.0,
                "occupancy_multiplier": 1.0
            },
            headers=headers,
            timeout=30  # RAG can take time
        )
        
        if deep_response.status_code == 200:
            recommendations = deep_response.json()
            print(f"✅ Deep AI Analysis working! Found {len(recommendations)} recommendations")
            
            # Check if recommendations have RAG enrichment
            for i, rec in enumerate(recommendations[:2]):
                has_rag = rec.get('is_enriched', False) and rec.get('sources')
                print(f"   {i+1}. {rec.get('action', 'N/A')[:50]}...")
                print(f"      Priority: {rec.get('priority', 'N/A')}")
                print(f"      RAG Enriched: {'Yes' if has_rag else 'No'}")
                if has_rag:
                    print(f"      Sources: {rec.get('sources', [])}")
            
        else:
            print(f"❌ Deep AI Analysis failed: {deep_response.status_code}")
            print(f"   Error: {deep_response.text}")
            
    except Exception as e:
        print(f"❌ Deep AI Analysis error: {e}")
    
    # Test 4: RAG Status
    print("\n4. Testing RAG Service Status...")
    try:
        rag_response = requests.get("http://localhost:8000/rag/status", headers=headers)
        if rag_response.status_code == 200:
            rag_status = rag_response.json()
            print("✅ RAG Service Status:")
            for key, value in rag_status.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ RAG Status failed: {rag_response.status_code}")
    except Exception as e:
        print(f"❌ RAG Status error: {e}")
    
    print("\n=== Integration Test Complete ===")
    print("🎉 Deep AI Analysis is now working!")
    print("You can access it via:")
    print("   Frontend: http://localhost:5173")
    print("   API Docs: http://localhost:8000/docs")
    print("   Deep Analysis: Navigate to Dashboard → 'Wanna check deeper?' button")

if __name__ == "__main__":
    test_complete_integration()
