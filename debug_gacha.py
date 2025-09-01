#!/usr/bin/env python3
"""
Debug gacha system specifically
"""
import requests
import time
import json

def debug_gacha():
    print("🎲 DEBUGGING GACHA SYSTEM")
    print("=" * 40)
    
    BASE_URL = "http://localhost:56092/api"
    
    # Wait for backend
    time.sleep(3)
    
    # Create test user
    username = f"gachatest_{int(time.time())}"
    register_data = {
        "username": username,
        "password": "test123",
        "email": f"{username}@test.com"
    }
    
    try:
        # Register and login
        print("1. Creating test user...")
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=5)
        print(f"   Registration: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return
        
        # Login
        login_data = {"username": username, "password": "test123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
        print(f"   Login: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check profile first
        print("\n2. Checking profile...")
        response = requests.get(f"{BASE_URL}/player/profile", headers=headers, timeout=5)
        print(f"   Profile: {response.status_code}")
        
        if response.status_code == 200:
            profile = response.json()
            print(f"   Resources: Gold={profile.get('gold', 0)}, Gems={profile.get('diamond', 0)}")
        else:
            print(f"   Profile Error: {response.text}")
        
        # Test gacha rates first
        print("\n3. Testing gacha rates...")
        response = requests.get(f"{BASE_URL}/gacha/rates", headers=headers, timeout=5)
        print(f"   Rates: {response.status_code}")
        
        if response.status_code == 200:
            rates = response.json()
            print(f"   Rates data: {json.dumps(rates, indent=2)}")
        else:
            print(f"   Rates Error: {response.text}")
        
        # Now test gacha pull with detailed error info
        print("\n4. Testing gacha pull...")
        pull_data = {"pull_type": "single", "currency": "gems"}
        response = requests.post(f"{BASE_URL}/gacha/pull", json=pull_data, headers=headers, timeout=10)
        print(f"   Gacha Pull: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   SUCCESS! Got: {json.dumps(result, indent=2)}")
        else:
            print(f"   FAILED! Error: {response.text}")
            
            # Try to get more detailed error info
            try:
                error_data = response.json()
                print(f"   Detailed error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw error: {response.text}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    debug_gacha()
