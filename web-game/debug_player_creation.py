#!/usr/bin/env python3
"""
Debug player creation to see what's happening
"""
import requests
import time

def debug_player_creation():
    print("🔍 DEBUGGING PLAYER CREATION")
    print("=" * 40)
    
    BASE_URL = "http://localhost:56092/api"
    
    # Create a unique test user
    username = f"debug_{int(time.time())}"
    register_data = {
        "username": username,
        "password": "test123",
        "email": f"{username}@test.com"
    }
    
    print(f"Creating user: {username}")
    
    try:
        # Register
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=5)
        print(f"Registration: {response.status_code}")
        
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            # Login
            login_data = {"username": username, "password": "test123"}
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
            print(f"Login: {response.status_code}")
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Get profile immediately after creation
                response = requests.get(f"{BASE_URL}/player/profile", headers=headers, timeout=5)
                print(f"Profile: {response.status_code}")
                
                if response.status_code == 200:
                    profile = response.json()
                    print("Profile data:")
                    for key, value in profile.items():
                        if key in ['gold', 'diamond', 'stone', 'ticket', 'crystals', 'level', 'xp']:
                            print(f"  {key}: {value}")
                else:
                    print(f"Profile error: {response.text}")
            else:
                print(f"Login error: {response.text}")
        else:
            print(f"Registration error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_player_creation()
