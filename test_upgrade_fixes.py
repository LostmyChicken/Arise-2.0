#!/usr/bin/env python3
"""
Test the upgrade system fixes.
"""

import asyncio
import logging
from structure.player import Player

async def test_upgrade_fixes():
    """Test the upgrade system fixes"""
    print("🧪 Testing Upgrade System Fixes...")
    
    # Test player ID
    test_player_id = "888999000"
    
    try:
        # Create a test player with some items
        print(f"👤 Creating test player {test_player_id}...")
        player = Player(test_player_id)
        player.level = 25
        player.gold = 100000
        
        # Add some test hunters and items
        player.hunters = {
            "sung_jinwoo": {"level": 5, "tier": 1},
            "cha_hae_in": {"level": 3, "tier": 0}
        }
        
        player.inventory = {
            "demon_sword": {"level": 2, "tier": 1},
            "knight_armor": {"level": 1, "tier": 0}
        }
        
        player.shadows = {
            "igris": {"level": 4},
            "tank": {"level": 2}
        }
        
        # Add some cubes for testing
        player.icube = 10  # Water cubes
        player.fcube = 15  # Fire cubes
        player.dcube = 8   # Dark cubes
        player.wcube = 12  # Wind cubes
        player.lcube = 5   # Light cubes
        player.tos = 20    # Traces of Shadow
        
        await player.save()
        print("✅ Test player created with items!")
        
        # Test the upgrade system components
        print("🔧 Testing upgrade system components...")
        
        # Test UpgradeItemSelect creation
        from commands.upgrade import UpgradeItemSelect, UpgradeItemSelectView, UpgradeTypeSelectView, UpgradeAllItemsView
        
        # Mock upgrade cog
        class MockUpgradeCog:
            async def show_upgrade_details(self, interaction, item_type, item_id):
                print(f"✅ show_upgrade_details called with: {item_type}, {item_id}")
                return True
        
        mock_cog = MockUpgradeCog()
        
        # Test UpgradeItemSelectView creation
        print("📋 Testing UpgradeItemSelectView...")
        import discord
        
        # Create a mock user
        class MockUser:
            def __init__(self, user_id):
                self.id = user_id
        
        mock_user = MockUser(int(test_player_id))
        
        # Test creating the view with upgrade_cog
        item_select_view = UpgradeItemSelectView(mock_user, "hunter", mock_cog)
        print("✅ UpgradeItemSelectView created successfully!")
        
        # Test that upgrade_cog is properly set
        assert item_select_view.upgrade_cog is not None, "upgrade_cog should not be None"
        assert item_select_view.select_menu.upgrade_cog is not None, "select_menu.upgrade_cog should not be None"
        print("✅ upgrade_cog properly set in views!")
        
        # Test UpgradeTypeSelectView creation
        print("🎯 Testing UpgradeTypeSelectView...")
        type_select_view = UpgradeTypeSelectView(mock_user, mock_cog)
        assert type_select_view.upgrade_cog is not None, "UpgradeTypeSelectView.upgrade_cog should not be None"
        print("✅ UpgradeTypeSelectView created successfully!")
        
        # Test UpgradeAllItemsView creation
        print("📊 Testing UpgradeAllItemsView...")
        all_items_view = UpgradeAllItemsView(mock_user, player, mock_cog)
        assert all_items_view.upgrade_cog is not None, "UpgradeAllItemsView.upgrade_cog should not be None"
        print("✅ UpgradeAllItemsView created successfully!")
        
        # Test populate_items method
        print("🔍 Testing populate_items...")
        await item_select_view.populate_items()
        
        # Check if options were populated
        if item_select_view.select_menu.options:
            print(f"✅ Found {len(item_select_view.select_menu.options)} hunter options!")
            for option in item_select_view.select_menu.options[:3]:  # Show first 3
                print(f"   - {option.label}: {option.description}")
        else:
            print("⚠️ No hunter options found (this might be expected if no hunters exist)")
        
        # Test with different item types
        print("🗡️ Testing weapon selection...")
        weapon_view = UpgradeItemSelectView(mock_user, "weapon", mock_cog)
        await weapon_view.populate_items()
        
        if weapon_view.select_menu.options:
            print(f"✅ Found {len(weapon_view.select_menu.options)} weapon options!")
        else:
            print("⚠️ No weapon options found")
        
        print("👻 Testing shadow selection...")
        shadow_view = UpgradeItemSelectView(mock_user, "shadow", mock_cog)
        await shadow_view.populate_items()
        
        if shadow_view.select_menu.options:
            print(f"✅ Found {len(shadow_view.select_menu.options)} shadow options!")
        else:
            print("⚠️ No shadow options found")
        
        # Clean up test player
        print("🧹 Cleaning up test data...")
        import aiosqlite
        async with aiosqlite.connect("new_player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
            await conn.commit()
        print("✅ Test data cleaned up!")
        
        print("🎉 All upgrade system fixes tested successfully!")
        
    except Exception as e:
        print(f"❌ Upgrade system test failed: {e}")
        logging.error(f"Upgrade system test failed: {e}")
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
    await test_upgrade_fixes()

if __name__ == "__main__":
    asyncio.run(main())
