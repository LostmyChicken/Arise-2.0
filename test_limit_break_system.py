#!/usr/bin/env python3
"""
Test the limit break system functionality.
"""

import asyncio
import logging
from structure.player import Player

async def test_limit_break_system():
    """Test the limit break system"""
    print("🧪 Testing Limit Break System...")
    
    # Test player ID
    test_player_id = "777888999"
    
    try:
        # Create a test player with items ready for limit break
        print(f"👤 Creating test player {test_player_id}...")
        player = Player(test_player_id)
        player.level = 50
        player.gold = 500000
        
        # Add hunters at level cap ready for limit break
        player.hunters = {
            "sung_jinwoo": {"level": 10, "tier": 0, "xp": 0},  # At tier 0 cap (10)
            "cha_hae_in": {"level": 20, "tier": 1, "xp": 0}   # At tier 1 cap (20)
        }
        
        # Add weapons at level cap
        player.inventory = {
            "demon_sword": {"level": 10, "tier": 0, "xp": 0},  # At tier 0 cap (10)
            "knight_armor": {"level": 20, "tier": 1, "xp": 0}, # At tier 1 cap (20)
            # Add shards for limit breaking
            "s_sung_jinwoo": {"quantity": 5},  # Enough shards
            "s_cha_hae_in": {"quantity": 3},   # Enough shards
            "s_demon_sword": {"quantity": 2},  # Enough shards
            "s_knight_armor": {"quantity": 2}  # Enough shards
        }
        
        # Add plenty of cubes for limit breaking
        player.icube = 50   # Water cubes
        player.fcube = 50   # Fire cubes
        player.dcube = 50   # Dark cubes
        player.wcube = 50   # Wind cubes
        player.lcube = 50   # Light cubes
        player.ecube = 50   # Earth cubes
        
        await player.save()
        print("✅ Test player created with items ready for limit break!")
        
        # Test limit break system components
        print("🌟 Testing limit break system components...")
        
        from commands.upgrade import UpgradeActionsView, LimitBreakButton
        
        # Mock upgrade cog
        class MockUpgradeCog:
            async def show_upgrade_details(self, interaction, item_type, item_id):
                print(f"✅ show_upgrade_details called after limit break: {item_type}, {item_id}")
                return True
        
        mock_cog = MockUpgradeCog()
        
        # Create a mock user
        class MockUser:
            def __init__(self, user_id):
                self.id = user_id
        
        mock_user = MockUser(int(test_player_id))
        
        # Test UpgradeActionsView creation with limit break button
        print("🔧 Testing UpgradeActionsView with limit break...")
        
        # Test for hunter (should have limit break button)
        hunter_view = UpgradeActionsView(mock_user, mock_cog, "hunter", "sung_jinwoo")
        has_limit_break_button = any(isinstance(child, LimitBreakButton) for child in hunter_view.children)
        print(f"✅ Hunter view has limit break button: {has_limit_break_button}")
        
        # Test for weapon (should have limit break button)
        weapon_view = UpgradeActionsView(mock_user, mock_cog, "weapon", "demon_sword")
        has_limit_break_button = any(isinstance(child, LimitBreakButton) for child in weapon_view.children)
        print(f"✅ Weapon view has limit break button: {has_limit_break_button}")
        
        # Test for shadow (should NOT have limit break button)
        shadow_view = UpgradeActionsView(mock_user, mock_cog, "shadow", "igris")
        has_limit_break_button = any(isinstance(child, LimitBreakButton) for child in shadow_view.children)
        print(f"✅ Shadow view has limit break button: {has_limit_break_button} (should be False)")
        
        # Test limit break requirements checking
        print("📋 Testing limit break requirements...")
        
        # Test limit break caps
        limit_break_caps = [10, 20, 40, 60, 80, 100]
        shard_requirements = [1, 1, 2, 2, 4]
        cube_requirements = [5, 10, 20, 40, 60]
        
        print(f"✅ Limit break caps: {limit_break_caps}")
        print(f"✅ Shard requirements: {shard_requirements}")
        print(f"✅ Cube requirements: {cube_requirements}")
        
        # Test requirement checking for sung_jinwoo (tier 0 -> tier 1)
        hunter_data = player.hunters["sung_jinwoo"]
        current_level = hunter_data.get('level', 1)
        tier = hunter_data.get('tier', 0)
        level_cap = limit_break_caps[tier]
        
        print(f"📊 Sung Jin-Woo status:")
        print(f"   Level: {current_level}, Tier: {tier}, Cap: {level_cap}")
        print(f"   At level cap: {current_level >= level_cap}")
        print(f"   Can limit break: {tier < len(limit_break_caps) - 1}")
        
        # Check shard requirements
        shard_key = f"s_sung_jinwoo"
        current_shards = 0
        if shard_key in player.inventory:
            shard_data = player.inventory[shard_key]
            if isinstance(shard_data, dict):
                current_shards = shard_data.get('quantity', 0)
            else:
                current_shards = shard_data
        
        required_shards = shard_requirements[tier]
        print(f"   Shards: {current_shards}/{required_shards} ({'✅' if current_shards >= required_shards else '❌'})")
        
        # Check cube requirements (assuming Fire element for sung_jinwoo)
        required_cubes = cube_requirements[tier]
        current_cubes = player.fcube  # Fire cubes
        print(f"   Fire Cubes: {current_cubes}/{required_cubes} ({'✅' if current_cubes >= required_cubes else '❌'})")
        
        # Test limit break simulation
        print("🚀 Testing limit break simulation...")
        
        if (current_level >= level_cap and 
            tier < len(limit_break_caps) - 1 and 
            current_shards >= required_shards and 
            current_cubes >= required_cubes):
            
            print("✅ All requirements met for limit break!")
            
            # Simulate limit break
            new_tier = tier + 1
            new_level_cap = limit_break_caps[new_tier]
            
            print(f"🌟 Limit break simulation:")
            print(f"   Old tier: {tier} -> New tier: {new_tier}")
            print(f"   Old cap: {level_cap} -> New cap: {new_level_cap}")
            print(f"   Materials used: {required_shards} shards, {required_cubes} cubes")
            
        else:
            print("❌ Requirements not met for limit break")
            if current_level < level_cap:
                print(f"   - Need level {level_cap}, currently {current_level}")
            if current_shards < required_shards:
                print(f"   - Need {required_shards} shards, have {current_shards}")
            if current_cubes < required_cubes:
                print(f"   - Need {required_cubes} cubes, have {current_cubes}")
        
        # Test comprehensive cube counting function
        print("🧊 Testing comprehensive cube counting...")
        
        from commands.upgrade import get_comprehensive_cube_count
        
        # Test different cube types
        cube_types = [
            ("Fire", "fcube"),
            ("Water", "icube"), 
            ("Wind", "wcube"),
            ("Dark", "dcube"),
            ("Light", "lcube"),
            ("Earth", "ecube")
        ]
        
        for class_type, cube_attr in cube_types:
            comprehensive_count = get_comprehensive_cube_count(player, cube_attr, class_type)
            direct_count = getattr(player, cube_attr, 0)
            print(f"   {class_type}: Direct={direct_count}, Comprehensive={comprehensive_count}")
        
        # Clean up test player
        print("🧹 Cleaning up test data...")
        import aiosqlite
        async with aiosqlite.connect("new_player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
            await conn.commit()
        print("✅ Test data cleaned up!")
        
        print("🎉 Limit break system test completed!")
        
    except Exception as e:
        print(f"❌ Limit break system test failed: {e}")
        logging.error(f"Limit break system test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up on error
        try:
            import aiosqlite
            async with aiosqlite.connect("new_player.db") as conn:
                await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
                await conn.commit()
        except:
            pass

async def main():
    """Main test function"""
    await test_limit_break_system()

if __name__ == "__main__":
    asyncio.run(main())
