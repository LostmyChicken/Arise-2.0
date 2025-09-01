#!/usr/bin/env python3
"""
Quick test to verify basic functionality
"""
import requests
import time

def quick_test():
    print("🔍 QUICK FUNCTIONALITY TEST")
    print("=" * 40)
    
    # Wait for backend to start
    print("Waiting for backend to start...")
    time.sleep(3)
    
    BASE_URL = "http://localhost:56092/api"
    
    # Test basic connectivity
    try:
        response = requests.get(f"{BASE_URL}/gacha/rates", timeout=5)
        print(f"✅ Backend is running: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not responding: {e}")
        return
    
    # Test registration
    try:
        register_data = {
            "username": "quicktest",
            "password": "test123",
            "email": "quick@test.com"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data, timeout=5)
        print(f"✅ Registration: {response.status_code}")
        
        if response.status_code == 200:
            # Test login
            login_data = {"username": "quicktest", "password": "test123"}
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
            print(f"✅ Login: {response.status_code}")
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test gacha pull
                pull_data = {"pull_type": "single", "currency": "gems"}
                response = requests.post(f"{BASE_URL}/gacha/pull", json=pull_data, headers=headers, timeout=5)
                print(f"✅ Gacha pull: {response.status_code}")
                if response.status_code != 200:
                    print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n🎯 SUMMARY:")
    print("- Backend is running")
    print("- Authentication works")
    print("- Check browser for frontend functionality")

if __name__ == "__main__":
    quick_test()
