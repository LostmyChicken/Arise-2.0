#!/usr/bin/env python3
"""
Test script to verify Discord bot data integration
"""
import requests
import json

BASE_URL = "http://localhost:56092"

def test_api_endpoints():
    """Test all major API endpoints"""
    
    print("🧪 Testing Arise Web Game API Integration")
    print("=" * 50)
    
    # Test basic endpoints that don't require auth
    endpoints_no_auth = [
        "/api/gamedata/hunters",
        "/api/gamedata/items", 
        "/api/gamedata/stats",
        "/api/gamedata/gacha-rates",
        "/api/battle/monsters",
        "/api/story/chapters",
        "/api/gacha/rates",
        "/api/market/shop",
        "/api/market/daily-deals",
        "/api/arena/rankings",
        "/api/gates/available"
    ]
    
    print("\n📡 Testing Public Endpoints:")
    for endpoint in endpoints_no_auth:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint} - {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if endpoint == "/api/gamedata/hunters":
                    print(f"   📊 Found {len(data.get('hunters', []))} hunters")
                elif endpoint == "/api/gamedata/items":
                    print(f"   📊 Found {len(data.get('items', []))} items")
                elif endpoint == "/api/battle/monsters":
                    print(f"   📊 Found {len(data.get('monsters', []))} monsters")
                elif endpoint == "/api/story/chapters":
                    print(f"   📊 Found {len(data.get('chapters', []))} story chapters")
                elif endpoint == "/api/market/shop":
                    print(f"   📊 Found {len(data.get('items', []))} shop items")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Connection Error: {e}")
    
    print("\n🎮 Testing Game Data Integration:")
    
    # Test hunter data specifically
    try:
        response = requests.get(f"{BASE_URL}/api/gamedata/hunters")
        if response.status_code == 200:
            hunters = response.json().get('hunters', [])
            if hunters:
                print(f"✅ Hunter data loaded: {len(hunters)} hunters")
                
                # Check for key hunters
                hunter_names = [h.get('name', '') for h in hunters]
                key_hunters = ['Sung Jin-Woo', 'Cha Hae-In', 'Thomas Andre']
                found_key = [name for name in key_hunters if name in hunter_names]
                print(f"   📊 Key hunters found: {found_key}")
                
                # Check rarities
                rarities = {}
                for hunter in hunters:
                    rarity = hunter.get('rarity', 'Unknown')
                    rarities[rarity] = rarities.get(rarity, 0) + 1
                print(f"   📊 Hunter rarities: {rarities}")
            else:
                print("❌ No hunter data found")
        else:
            print(f"❌ Hunter data endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Hunter data test failed: {e}")
    
    # Test gacha rates
    try:
        response = requests.get(f"{BASE_URL}/api/gamedata/gacha-rates")
        if response.status_code == 200:
            rates = response.json().get('rates', {})
            print(f"✅ Gacha rates loaded: {rates}")
        else:
            print(f"❌ Gacha rates failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Gacha rates test failed: {e}")
    
    print("\n🔐 Testing Authentication Flow:")
    
    # Test registration (with a test user)
    test_user = {
        "username": "testuser123",
        "email": "test@example.com", 
        "password": "testpass123"
    }
    
    try:
        # Try to register
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        if response.status_code in [200, 201]:
            print("✅ Registration endpoint working")
            
            # Try to login
            login_data = {
                "username": test_user["username"],
                "password": test_user["password"]
            }
            
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data.get('access_token')
                print("✅ Login endpoint working")
                
                # Test authenticated endpoint
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{BASE_URL}/api/player/profile", headers=headers)
                
                if profile_response.status_code == 200:
                    profile = profile_response.json().get('profile', {})
                    print("✅ Authenticated profile endpoint working")
                    print(f"   📊 Starting resources: Gold={profile.get('resources', {}).get('gold', 0)}, Diamonds={profile.get('resources', {}).get('diamonds', 0)}")
                else:
                    print(f"❌ Profile endpoint failed: {profile_response.status_code}")
            else:
                print(f"❌ Login failed: {login_response.status_code}")
        elif response.status_code == 400:
            print("⚠️  Registration endpoint working (user may already exist)")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("✅ = Working correctly")
    print("❌ = Needs attention") 
    print("⚠️  = Warning/Expected behavior")
    print("\n🚀 If most endpoints show ✅, your Discord bot conversion is working!")

if __name__ == "__main__":
    test_api_endpoints()
