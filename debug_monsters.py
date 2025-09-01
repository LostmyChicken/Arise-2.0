#!/usr/bin/env python3
"""
Debug monsters endpoint
"""
import requests
import time
import json

def debug_monsters():
    print("🐉 DEBUGGING MONSTERS")
    print("=" * 30)
    
    BASE_URL = "http://localhost:56092/api"
    
    # Wait for backend
    time.sleep(2)
    
    # Create test user
    username = f"monstertest_{int(time.time())}"
    register_data = {
        "username": username,
        "password": "test123",
        "email": f"{username}@test.com"
    }
    
    try:
        # Register and login
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=5)
        login_data = {"username": username, "password": "test123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test monsters endpoint
        response = requests.get(f"{BASE_URL}/battle/monsters", headers=headers, timeout=5)
        print(f"Monsters endpoint: {response.status_code}")
        
        if response.status_code == 200:
            monsters = response.json()
            print(f"Monsters data: {json.dumps(monsters, indent=2)}")
        else:
            print(f"Error: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_monsters()
