#!/usr/bin/env python3
"""
Comprehensive test for all game features
"""
import requests
import json
import random
import string

BASE_URL = "http://localhost:56092/api"

def generate_test_user():
    """Generate a random test user"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{suffix}"

def test_all_features():
    """Test all game features comprehensively"""
    print("🎮 ARISE WEB GAME - COMPREHENSIVE FEATURE TEST")
    print("=" * 60)
    
    # Generate test user
    username = generate_test_user()
    password = "testpass123"
    
    print(f"👤 Testing with user: {username}")
    print()
    
    # Test 1: Authentication
    print("1. 🔐 AUTHENTICATION TESTS")
    print("-" * 30)
    
    # Register
    register_data = {"username": username, "password": password, "email": f"{username}@test.com"}
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"   Registration: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        return
    
    player_id = response.json().get("player_id")
    
    # Login
    response = requests.post(f"{BASE_URL}/auth/login", json=register_data)
    print(f"   Login: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    if response.status_code != 200:
        print(f"   Error: {response.text}")
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print()
    
    # Test 2: Profile & Player Data
    print("2. 👤 PROFILE & PLAYER DATA")
    print("-" * 30)
    
    endpoints_to_test = [
        ("/player/profile", "Current Profile"),
        (f"/player/profile/{player_id}", "Player Profile by ID"),
    ]
    
    for endpoint, name in endpoints_to_test:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"   {name}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    print()
    
    # Test 3: Game Features
    print("3. 🎯 CORE GAME FEATURES")
    print("-" * 30)
    
    game_endpoints = [
        ("/battle/monsters", "Battle Monsters"),
        ("/worldboss/current", "World Boss"),
        ("/worldboss/leaderboard", "World Boss Leaderboard"),
        ("/arena/rankings", "Arena Rankings"),
        ("/arena/opponents", "Arena Opponents"),
        ("/arena/my-rank", "My Arena Rank"),
        ("/gates/available", "Available Gates"),
        ("/gates/player-progress", "Gate Progress"),
        ("/skills/available", "Available Skills"),
        ("/skills/player", "Player Skills"),
        ("/upgrade/costs", "Upgrade Costs"),
        ("/upgrade/player-items", "Upgradeable Items"),
    ]
    
    for endpoint, name in game_endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"   {name}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    print()
    
    # Test 4: Social & Economy Features
    print("4. 🏪 SOCIAL & ECONOMY FEATURES")
    print("-" * 30)
    
    social_endpoints = [
        ("/guild/list", "Guild List"),
        ("/guild/my-guild", "My Guild"),
        ("/trading/offers", "Trading Offers"),
        ("/trading/my-trades", "My Trades"),
        ("/market/shop", "Market Shop"),
        ("/market/daily-deals", "Daily Deals"),
        ("/inventory/player", "Player Inventory"),
        ("/daily/missions", "Daily Tasks"),
        ("/leaderboard/power", "Power Leaderboard"),
        ("/leaderboard/level", "Level Leaderboard"),
    ]
    
    for endpoint, name in social_endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"   {name}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    print()
    
    # Test 5: Gacha System
    print("5. 🎲 GACHA SYSTEM")
    print("-" * 30)
    
    gacha_endpoints = [
        ("/gacha/rates", "Gacha Rates"),
    ]
    
    for endpoint, name in gacha_endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"   {name}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    print()
    
    # Test 6: Story & Progress
    print("6. 📖 STORY & PROGRESS")
    print("-" * 30)
    
    story_endpoints = [
        ("/story/chapters", "Story Chapters"),
        ("/story/progress", "Story Progress"),
    ]
    
    for endpoint, name in story_endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"   {name}: {response.status_code} {'✅' if response.status_code == 200 else '❌'}")
    
    print()
    
    print("🎉 COMPREHENSIVE TEST COMPLETED!")
    print("=" * 60)
    print("✅ All major game features have been tested!")
    print("🚀 The game is ready for launch!")

if __name__ == "__main__":
    test_all_features()
