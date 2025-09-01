#!/usr/bin/env python3
"""
Fix authentication and profile issues
"""
import requests
import json

BASE_URL = "http://localhost:56092"

def test_and_fix_auth():
    print("🔧 Testing and Fixing Authentication Issues")
    print("=" * 50)
    
    # Test user credentials
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    print("\n1. Testing Registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        if response.status_code in [200, 201]:
            print("✅ Registration successful")
        elif response.status_code == 400:
            print("⚠️  User already exists, proceeding to login...")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    print("\n2. Testing Login...")
    try:
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('access_token')
            player_id = token_data.get('player_id')
            print(f"✅ Login successful - Player ID: {player_id}")
            
            # Test authenticated endpoints
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\n3. Testing Profile Endpoint...")
            profile_response = requests.get(f"{BASE_URL}/api/player/profile", headers=headers)
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print("✅ Profile loaded successfully!")
                print(f"   📊 Level: {profile.get('profile', {}).get('level', 'N/A')}")
                print(f"   💰 Gold: {profile.get('profile', {}).get('resources', {}).get('gold', 'N/A')}")
                print(f"   💎 Diamonds: {profile.get('profile', {}).get('resources', {}).get('diamonds', 'N/A')}")
                
                # Test other endpoints
                print("\n4. Testing Other Endpoints...")
                endpoints_to_test = [
                    ("/api/battle/monsters", "Battle Monsters"),
                    ("/api/gacha/rates", "Gacha Rates"),
                    ("/api/story/chapters", "Story Chapters"),
                    ("/api/market/shop", "Market Shop")
                ]
                
                for endpoint, name in endpoints_to_test:
                    try:
                        test_response = requests.get(f"{BASE_URL}{endpoint}", headers=headers if 'player' in endpoint else None)
                        status = "✅" if test_response.status_code == 200 else "❌"
                        print(f"   {status} {name}: {test_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ {name}: Error - {e}")
                
                print("\n🎉 Authentication is working correctly!")
                print("🔧 If you're still having issues in the browser:")
                print("   1. Clear browser cache and localStorage")
                print("   2. Try logging out and back in")
                print("   3. Check browser console for errors")
                
            else:
                print(f"❌ Profile failed: {profile_response.status_code} - {profile_response.text}")
                
                # Try the old profile endpoint
                print("   🔧 Trying alternative profile endpoint...")
                alt_response = requests.get(f"{BASE_URL}/api/player/profile/{player_id}", headers=headers)
                if alt_response.status_code == 200:
                    print("   ✅ Alternative profile endpoint works")
                else:
                    print(f"   ❌ Alternative profile also failed: {alt_response.status_code}")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Login error: {e}")

if __name__ == "__main__":
    test_and_fix_auth()
