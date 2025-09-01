#!/usr/bin/env python3
"""
Test frontend-backend connectivity and authentication
"""
import requests
import json

BASE_URL = "http://localhost:56092/api"

def test_frontend_backend():
    print("🔍 TESTING FRONTEND-BACKEND CONNECTIVITY")
    print("=" * 50)
    
    # Test 1: Basic API connectivity
    print("1. Testing basic API connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/gacha/rates")
        print(f"   Gacha rates endpoint: {response.status_code} ✅")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print()
    
    # Test 2: Authentication flow
    print("2. Testing authentication flow...")
    
    # Register a test user
    register_data = {
        "username": "frontend_test",
        "password": "test123",
        "email": "test@test.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"   Registration: {response.status_code}")
        
        if response.status_code == 200:
            player_id = response.json().get("player_id")
            print(f"   Player ID: {player_id}")
        else:
            print(f"   Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return
    
    # Login
    login_data = {
        "username": "frontend_test",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Login: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"   Token received: {token[:20]}...")
            
            # Test authenticated endpoint
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test gacha pull
            pull_data = {"pull_type": "single"}
            response = requests.post(f"{BASE_URL}/gacha/pull", json=pull_data, headers=headers)
            print(f"   Gacha pull: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Gacha pull successful!")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ❌ Gacha pull failed: {response.text}")
                
        else:
            print(f"   Login failed: {response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    print()
    print("3. Testing other POST endpoints...")
    
    # Test other POST endpoints
    endpoints_to_test = [
        ("/arena/battle", {"opponent_id": "test_opponent"}),
        ("/skills/learn", {"skill_id": "fireball"}),
        ("/upgrade/upgrade", {"item_id": "sword_1", "upgrade_type": "level"}),
    ]
    
    for endpoint, data in endpoints_to_test:
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {endpoint}: {response.status_code} {status}")
        except Exception as e:
            print(f"   {endpoint}: ❌ Error: {e}")
    
    print()
    print("🎉 FRONTEND-BACKEND CONNECTIVITY TEST COMPLETED!")

if __name__ == "__main__":
    test_frontend_backend()
