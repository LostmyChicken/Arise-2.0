#!/usr/bin/env python3
"""
Test gacha with proper authentication
"""
import requests
import json

BASE_URL = "http://localhost:56092/api"

def test_gacha_with_auth():
    print("🎲 TESTING GACHA WITH PROPER AUTHENTICATION")
    print("=" * 50)
    
    # Step 1: Register and login
    register_data = {
        "username": "gacha_test",
        "password": "test123",
        "email": "gacha@test.com"
    }
    
    print("1. Registering user...")
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"   Registration: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Registration failed: {response.text}")
        return
    
    print("2. Logging in...")
    login_data = {
        "username": "gacha_test",
        "password": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Login: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ Login failed: {response.text}")
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✅ Token received")
    
    print("3. Testing gacha pulls...")
    
    # Test different gacha pull combinations
    test_cases = [
        {"pull_type": "single", "currency": "gems"},
        {"pull_type": "single", "currency": "tickets"},
        {"pull_type": "ten", "currency": "gems"},
        {"pull_type": "ten", "currency": "tickets"},
    ]
    
    for i, pull_data in enumerate(test_cases, 1):
        print(f"   Test {i}: {pull_data['pull_type']} pull with {pull_data['currency']}")
        
        try:
            response = requests.post(f"{BASE_URL}/gacha/pull", json=pull_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ Success! Got {len(result.get('results', [result.get('result', [])]))} items")
            else:
                print(f"      ❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print()
    print("4. Testing other POST endpoints...")
    
    # Test other endpoints that might be failing
    other_tests = [
        ("/arena/battle", {"opponent_id": "test_opponent"}),
        ("/skills/learn", {"skill_id": "fireball"}),
        ("/gates/action", {"gate_id": "gate_1", "action": "enter"}),
    ]
    
    for endpoint, data in other_tests:
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {endpoint}: {response.status_code} {status}")
            if response.status_code != 200:
                print(f"      Error: {response.text}")
        except Exception as e:
            print(f"   {endpoint}: ❌ Error: {e}")
    
    print()
    print("🎉 GACHA AUTHENTICATION TEST COMPLETED!")

if __name__ == "__main__":
    test_gacha_with_auth()
