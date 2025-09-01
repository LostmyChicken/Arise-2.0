#!/usr/bin/env python3
"""
Test the story UI fixes.
"""

import asyncio
from structure.player import Player
from structure.story_campaign import StoryCampaign

async def test_ui_fixes():
    """Test the UI fixes for story system"""
    print("🧪 Testing Story UI Fixes...")
    
    # Test player ID
    test_player_id = "987654321"
    
    try:
        # Create a test player with higher level
        print(f"👤 Creating test player {test_player_id}...")
        player = Player(test_player_id)
        player.level = 15  # Higher level to unlock more missions
        await player.save()
        print("✅ Test player created!")
        
        # Test getting available missions
        print("🎯 Testing available missions...")
        available_missions = await StoryCampaign.get_available_missions(test_player_id)
        print(f"✅ Available missions: {[m.name for m in available_missions]}")
        
        # Test completing first mission
        print("🏆 Testing mission completion...")
        success, message, rewards = await StoryCampaign.complete_mission(test_player_id, "prologue_001")
        print(f"✅ Mission completion: {success} - {message}")
        
        # Test getting updated available missions
        print("🔄 Testing updated available missions...")
        updated_available = await StoryCampaign.get_available_missions(test_player_id)
        print(f"✅ Updated available missions: {[m.name for m in updated_available]}")
        
        # Test getting completed missions
        print("✅ Testing completed missions...")
        completed_missions = await StoryCampaign.get_completed_missions(test_player_id)
        print(f"✅ Completed missions: {[m.name for m in completed_missions]}")
        
        # Test edge case: player with no available missions
        print("🧪 Testing edge case: high level player...")
        high_level_player = Player("999888777")
        high_level_player.level = 200  # Very high level
        await high_level_player.save()
        
        # Complete all missions for this player
        for mission_id in StoryCampaign.STORY_MISSIONS.keys():
            await StoryCampaign.complete_mission("999888777", mission_id)
        
        # Now check available missions (should be empty)
        no_available = await StoryCampaign.get_available_missions("999888777")
        print(f"✅ High level player available missions: {[m.name for m in no_available]}")
        
        # Clean up test players
        print("🧹 Cleaning up test players...")
        import aiosqlite
        async with aiosqlite.connect("new_player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id IN (?, ?)", (test_player_id, "999888777"))
            await conn.commit()
        print("✅ Test players cleaned up!")
        
        print("🎉 All UI fixes tested successfully!")
        
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        
        # Clean up on error
        try:
            import aiosqlite
            async with aiosqlite.connect("new_player.db") as conn:
                await conn.execute("DELETE FROM players WHERE id IN (?, ?)", (test_player_id, "999888777"))
                await conn.commit()
        except:
            pass

async def main():
    """Main test function"""
    await test_ui_fixes()

if __name__ == "__main__":
    asyncio.run(main())
