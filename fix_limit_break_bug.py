#!/usr/bin/env python3
"""
Fix the limit break bug by restoring materials and fixing tier
"""
import asyncio
import json
from structure.player import Player

async def fix_limit_break_bug():
    """Fix the limit break bug for a specific player"""
    print("🔧 Limit Break Bug Fix Tool")
    print("=" * 40)
    
    # Get player ID
    player_id = input("Enter your Discord user ID: ").strip()
    
    try:
        # Get player data
        player = await Player.get(player_id)
        if not player:
            print("❌ Player not found")
            return
        
        print(f"✅ Found player: {player_id}")
        
        # Get Kim Chul data
        hunters = player.get_hunters()
        inventory = player.get_inventory()
        
        # Find Kim Chul
        kim_chul_id = None
        possible_ids = ["kim_chul", "kimchul", "kim_chul_hunter", "chul"]
        
        for possible_id in possible_ids:
            if possible_id in hunters:
                kim_chul_id = possible_id
                break
        
        if not kim_chul_id:
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
            print(f"❌ Could not find Kim Chul")
            return
        
        kim_chul_data = hunters[kim_chul_id]
        current_tier = kim_chul_data.get('tier', 0)
        current_level = kim_chul_data.get('level', 1)
        
        print(f"\n📊 Current Kim Chul Status:")
        print(f"  ID: {kim_chul_id}")
        print(f"  Level: {current_level}")
        print(f"  Tier: {current_tier}")
        
        # Determine what the fix should be
        print(f"\n🔍 Analyzing the issue...")
        
        # If Kim Chul is at level 10+ and tier 0, he should be tier 1
        limit_break_caps = [10, 20, 40, 60, 80, 100]
        shard_requirements = [1, 1, 2, 2, 4]
        cube_requirements = [5, 10, 20, 40, 60]
        
        expected_tier = current_tier
        for i, cap in enumerate(limit_break_caps[:-1]):  # Don't check the last cap
            if current_level >= cap and current_tier <= i:
                expected_tier = i + 1
                break
        
        if expected_tier > current_tier:
            print(f"🔧 Issue detected: Kim Chul should be tier {expected_tier} based on level {current_level}")
            
            # Ask for confirmation
            fix_tier = input(f"Fix Kim Chul's tier from {current_tier} to {expected_tier}? (y/n): ").strip().lower()
            if fix_tier == 'y':
                kim_chul_data['tier'] = expected_tier
                print(f"✅ Fixed Kim Chul's tier to {expected_tier}")
        
        # Ask about restoring materials
        print(f"\n💎 Material Restoration:")
        restore_materials = input("Do you want to restore the consumed materials? (y/n): ").strip().lower()
        
        if restore_materials == 'y':
            # Restore shards
            shard_key = f"s_{kim_chul_id}"
            
            # Determine how many shards to restore based on the tier that was attempted
            attempted_tier = current_tier if expected_tier <= current_tier else expected_tier - 1
            if attempted_tier < len(shard_requirements):
                shards_to_restore = shard_requirements[attempted_tier]
                
                print(f"🔧 Restoring {shards_to_restore} {kim_chul_id} shards...")
                
                if shard_key in inventory:
                    if isinstance(inventory[shard_key], dict):
                        inventory[shard_key]['quantity'] = inventory[shard_key].get('quantity', 0) + shards_to_restore
                    else:
                        inventory[shard_key] = inventory[shard_key] + shards_to_restore
                else:
                    inventory[shard_key] = {"quantity": shards_to_restore}
                
                print(f"✅ Restored {shards_to_restore} shards")
            
            # Restore cubes
            if attempted_tier < len(cube_requirements):
                cubes_to_restore = cube_requirements[attempted_tier]
                
                # Determine Kim Chul's element
                try:
                    from structure.heroes import HeroManager
                    kim_chul_obj = await HeroManager.get(kim_chul_id)
                    if kim_chul_obj:
                        class_type = getattr(kim_chul_obj, 'classType', 'Fire')
                        
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
                        
                        print(f"🔧 Restoring {cubes_to_restore} {class_type} cubes ({cube_attr})...")
                        setattr(player, cube_attr, current_cubes + cubes_to_restore)
                        print(f"✅ Restored {cubes_to_restore} {class_type} cubes")
                    else:
                        print(f"⚠️ Could not determine Kim Chul's element, defaulting to Fire cubes")
                        player.fcube = getattr(player, 'fcube', 0) + cubes_to_restore
                        print(f"✅ Restored {cubes_to_restore} Fire cubes")
                except Exception as e:
                    print(f"⚠️ Error determining element, defaulting to Fire cubes: {e}")
                    player.fcube = getattr(player, 'fcube', 0) + cubes_to_restore
                    print(f"✅ Restored {cubes_to_restore} Fire cubes")
        
        # Save changes
        print(f"\n💾 Saving changes...")
        await player.save()
        print(f"✅ All changes saved successfully!")
        
        # Show final status
        print(f"\n📊 Final Kim Chul Status:")
        print(f"  Level: {kim_chul_data.get('level', 1)}")
        print(f"  Tier: {kim_chul_data.get('tier', 0)}")
        
        # Show restored materials
        if restore_materials == 'y':
            shard_key = f"s_{kim_chul_id}"
            if shard_key in inventory:
                if isinstance(inventory[shard_key], dict):
                    shard_count = inventory[shard_key].get('quantity', 0)
                else:
                    shard_count = inventory[shard_key]
                print(f"  Shards: {shard_count}")
            
            # Show cube counts
            cube_attrs = ['fcube', 'icube', 'wcube', 'ecube', 'lcube', 'dcube']
            cube_names = ['Fire', 'Water', 'Wind', 'Earth', 'Light', 'Dark']
            for cube_attr, cube_name in zip(cube_attrs, cube_names):
                count = getattr(player, cube_attr, 0)
                if count > 0:
                    print(f"  {cube_name} Cubes: {count}")
        
        print(f"\n🎉 Fix completed! Please check your Kim Chul in-game.")
        print(f"If the issue persists, there may be a deeper problem with the limit break system.")
        
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main fix function"""
    await fix_limit_break_bug()

if __name__ == "__main__":
    asyncio.run(main())
