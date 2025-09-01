#!/usr/bin/env python3
"""
Debug the limit break issue where materials are consumed but tier doesn't increase
"""
import asyncio
import json
from structure.player import Player

async def debug_limit_break_issue():
    """Debug the limit break issue"""
    print("🔍 Debugging Limit Break Issue...")
    
    # You'll need to replace this with your actual player ID
    player_id = input("Enter your Discord user ID: ").strip()
    
    try:
        # Get player data
        player = await Player.get(player_id)
        if not player:
            print("❌ Player not found")
            return
        
        print(f"✅ Found player: {player_id}")
        
        # Check Kim Chul data
        hunters = player.get_hunters()
        kim_chul_id = "kim_chul"  # Assuming this is the ID
        
        if kim_chul_id not in hunters:
            print(f"❌ Kim Chul not found in hunters")
            print(f"Available hunters: {list(hunters.keys())}")
            
            # Try to find Kim Chul with different possible IDs
            possible_ids = ["kim_chul", "kimchul", "kim_chul_hunter", "chul"]
            for possible_id in possible_ids:
                if possible_id in hunters:
                    kim_chul_id = possible_id
                    print(f"✅ Found Kim Chul with ID: {kim_chul_id}")
                    break
            else:
                # Let user specify the correct ID
                print("Available hunters:")
                for i, hunter_id in enumerate(hunters.keys(), 1):
                    hunter_data = hunters[hunter_id]
                    level = hunter_data.get('level', 1)
                    tier = hunter_data.get('tier', 0)
                    print(f"  {i}. {hunter_id} (Level {level}, Tier {tier})")
                
                choice = input("Enter the number of Kim Chul or the exact ID: ").strip()
                if choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(hunters):
                        kim_chul_id = list(hunters.keys())[choice_idx]
                else:
                    kim_chul_id = choice
        
        if kim_chul_id not in hunters:
            print(f"❌ Could not find Kim Chul with ID: {kim_chul_id}")
            return
        
        kim_chul_data = hunters[kim_chul_id]
        print(f"\n📊 Kim Chul Current Data:")
        print(f"  ID: {kim_chul_id}")
        print(f"  Level: {kim_chul_data.get('level', 1)}")
        print(f"  Tier: {kim_chul_data.get('tier', 0)}")
        print(f"  XP: {kim_chul_data.get('xp', 0)}")
        print(f"  Full data: {kim_chul_data}")
        
        # Check shards
        shard_key = f"s_{kim_chul_id}"
        inventory = player.get_inventory()
        
        print(f"\n🔍 Checking Shards:")
        print(f"  Looking for shard key: {shard_key}")
        
        if shard_key in inventory:
            shard_data = inventory[shard_key]
            if isinstance(shard_data, dict):
                shard_count = shard_data.get('quantity', shard_data.get('level', 0))
            else:
                shard_count = shard_data
            print(f"  ✅ Found shards: {shard_count}")
        else:
            print(f"  ❌ No shards found")
            # Look for alternative shard keys
            shard_keys = [k for k in inventory.keys() if 'kim' in k.lower() or 'chul' in k.lower()]
            if shard_keys:
                print(f"  Possible shard keys: {shard_keys}")
        
        # Check cubes
        print(f"\n🧊 Checking Cubes:")
        cube_attrs = ['fcube', 'icube', 'wcube', 'ecube', 'lcube', 'dcube']
        for cube_attr in cube_attrs:
            count = getattr(player, cube_attr, 0)
            print(f"  {cube_attr}: {count}")
        
        # Check if there are any cube items in inventory
        cube_items = {k: v for k, v in inventory.items() if 'cube' in k.lower()}
        if cube_items:
            print(f"  Cube items in inventory: {len(cube_items)}")
            for k, v in list(cube_items.items())[:5]:  # Show first 5
                if isinstance(v, dict):
                    quantity = v.get('quantity', v.get('level', v.get('amount', 0)))
                else:
                    quantity = v
                print(f"    {k}: {quantity}")
        
        # Test limit break requirements
        print(f"\n🌟 Limit Break Analysis:")
        current_level = kim_chul_data.get('level', 1)
        current_tier = kim_chul_data.get('tier', 0)
        
        limit_break_caps = [10, 20, 40, 60, 80, 100]
        shard_requirements = [1, 1, 2, 2, 4]
        cube_requirements = [5, 10, 20, 40, 60]
        
        print(f"  Current Level: {current_level}")
        print(f"  Current Tier: {current_tier}")
        
        if current_tier >= len(limit_break_caps) - 1:
            print(f"  ❌ Already at maximum tier!")
        else:
            required_level = limit_break_caps[current_tier]
            print(f"  Required Level for Limit Break: {required_level}")
            print(f"  Level Requirement Met: {'✅' if current_level >= required_level else '❌'}")
            
            if current_tier < len(shard_requirements):
                required_shards = shard_requirements[current_tier]
                print(f"  Required Shards: {required_shards}")
                
                if shard_key in inventory:
                    shard_data = inventory[shard_key]
                    if isinstance(shard_data, dict):
                        current_shards = shard_data.get('quantity', shard_data.get('level', 0))
                    else:
                        current_shards = shard_data
                    print(f"  Current Shards: {current_shards}")
                    print(f"  Shard Requirement Met: {'✅' if current_shards >= required_shards else '❌'}")
                else:
                    print(f"  Current Shards: 0")
                    print(f"  Shard Requirement Met: ❌")
            
            if current_tier < len(cube_requirements):
                required_cubes = cube_requirements[current_tier]
                print(f"  Required Cubes: {required_cubes}")
                
                # Check Kim Chul's element type
                try:
                    from structure.heroes import HeroManager
                    kim_chul_obj = await HeroManager.get(kim_chul_id)
                    if kim_chul_obj:
                        class_type = getattr(kim_chul_obj, 'classType', 'Fire')
                        print(f"  Kim Chul Element: {class_type}")
                        
                        cube_mapping = {
                            'Fire': 'fcube',
                            'Water': 'icube', 
                            'Wind': 'wcube',
                            'Earth': 'ecube',
                            'Light': 'lcube',
                            'Dark': 'dcube'
                        }
                        
                        cube_attr = cube_mapping.get(class_type, 'fcube')
                        current_cubes = getattr(player, cube_attr, 0)
                        print(f"  Required Cube Type: {cube_attr} ({class_type})")
                        print(f"  Current Cubes: {current_cubes}")
                        print(f"  Cube Requirement Met: {'✅' if current_cubes >= required_cubes else '❌'}")
                    else:
                        print(f"  ❌ Could not load Kim Chul hero data")
                except Exception as e:
                    print(f"  ❌ Error checking hero data: {e}")
        
        # Simulate what should happen in limit break
        print(f"\n🔧 Limit Break Simulation:")
        if current_tier < len(limit_break_caps) - 1:
            new_tier = current_tier + 1
            new_level_cap = limit_break_caps[new_tier]
            print(f"  After Limit Break:")
            print(f"    New Tier: {current_tier} → {new_tier}")
            print(f"    New Level Cap: {limit_break_caps[current_tier]} → {new_level_cap}")
            
            # Check if we can manually fix the tier
            fix_choice = input(f"\nWould you like me to manually fix Kim Chul's tier to {new_tier}? (y/n): ").strip().lower()
            if fix_choice == 'y':
                print("🔧 Manually fixing Kim Chul's tier...")
                kim_chul_data['tier'] = new_tier
                await player.save()
                print(f"✅ Kim Chul's tier has been manually set to {new_tier}")
                print("Please check in-game to confirm the fix worked.")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main debug function"""
    await debug_limit_break_issue()

if __name__ == "__main__":
    asyncio.run(main())
