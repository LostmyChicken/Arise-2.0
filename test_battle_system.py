#!/usr/bin/env python3
"""
Test the battle system specifically
"""
import requests
import time
import json

def test_battle_system():
    print("⚔️ TESTING BATTLE SYSTEM")
    print("=" * 40)
    
    BASE_URL = "http://localhost:56092/api"
    
    # Wait for backend
    time.sleep(2)
    
    # Create test user
    username = f"battletest_{int(time.time())}"
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
        
        # Test battle monsters endpoint
        print("\n2. Testing battle monsters...")
        response = requests.get(f"{BASE_URL}/battle/monsters", headers=headers, timeout=5)
        print(f"   Monsters: {response.status_code}")
        
        if response.status_code == 200:
            monsters = response.json()
            print(f"   Found {len(monsters)} monsters")
            if monsters:
                print(f"   First monster: {monsters[0].get('name', 'Unknown')}")
        else:
            print(f"   Error: {response.text}")
            return
        
        # Test starting a battle
        print("\n3. Testing battle start...")
        battle_data = {"monster_id": "goblin", "battle_type": "pve"}
        response = requests.post(f"{BASE_URL}/battle/start", json=battle_data, headers=headers, timeout=5)
        print(f"   Battle Start: {response.status_code}")
        
        if response.status_code == 200:
            battle_result = response.json()
            print(f"   Battle started successfully!")
            print(f"   Battle ID: {battle_result.get('battle_id', 'Unknown')}")
            
            if 'battle_state' in battle_result:
                battle_state = battle_result['battle_state']
                player = battle_state.get('player', {})
                enemy = battle_state.get('enemy', {})
                print(f"   Player HP: {player.get('hp', 'Unknown')}")
                print(f"   Enemy HP: {enemy.get('hp', 'Unknown')}")
                print(f"   Enemy Name: {enemy.get('name', 'Unknown')}")
                
                # Test battle action
                print("\n4. Testing battle action...")
                action_data = {
                    "battle_id": battle_result.get('battle_id'),
                    "action": "attack"
                }
                response = requests.post(f"{BASE_URL}/battle/action", json=action_data, headers=headers, timeout=5)
                print(f"   Battle Action: {response.status_code}")
                
                if response.status_code == 200:
                    action_result = response.json()
                    print(f"   Action successful!")
                    if 'damage' in action_result:
                        print(f"   Damage dealt: {action_result['damage']}")
                    if 'battle_state' in action_result:
                        new_enemy_hp = action_result['battle_state'].get('enemy', {}).get('hp', 'Unknown')
                        print(f"   Enemy HP after attack: {new_enemy_hp}")
                else:
                    print(f"   Action Error: {response.text}")
            
        else:
            print(f"   Battle Start Error: {response.text}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_battle_system()
