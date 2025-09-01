#!/usr/bin/env python3
"""
Test with a completely fresh user
"""
import requests
import json
import random
import string

BASE_URL = "http://localhost:56092"

def generate_random_user():
    """Generate a random user for testing"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return {
        "username": f"user_{random_suffix}",
        "email": f"test_{random_suffix}@example.com",
        "password": "testpass123"
    }

def test_fresh_user():
    print("🧪 Testing with Fresh User")
    print("=" * 40)
    
    # Generate random user
    user = generate_random_user()
    print(f"👤 Testing with user: {user['username']}")
    
    print("\n1. Registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code in [200, 201]:
            print("✅ Registration successful!")
            
            print("\n2. Login...")
            login_data = {
                "username": user["username"],
                "password": user["password"]
            }
            
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
            print(f"   Status: {login_response.status_code}")
            print(f"   Response: {login_response.text[:200]}...")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get('access_token')
                print("✅ Login successful!")
                print(f"   Token: {token[:50]}...")
                
                print("\n3. Profile Test...")
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{BASE_URL}/api/player/profile", headers=headers)
                print(f"   Status: {profile_response.status_code}")
                print(f"   Response: {profile_response.text[:300]}...")
                
                if profile_response.status_code == 200:
                    print("✅ Profile loaded successfully!")
                    profile_data = profile_response.json()
                    profile = profile_data.get('profile', {})
                    print(f"   Level: {profile.get('level')}")
                    print(f"   Gold: {profile.get('resources', {}).get('gold')}")
                    print(f"   Username: {profile.get('username')}")
                else:
                    print("❌ Profile failed")
            else:
                print("❌ Login failed")
        else:
            print("❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fresh_user()
