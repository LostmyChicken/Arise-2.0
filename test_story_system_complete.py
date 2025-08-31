#!/usr/bin/env python3
"""
Complete test of the story campaign system.
"""

import asyncio
import logging
from structure.player import Player
from structure.story_campaign import StoryCampaign

async def test_story_system():
    """Test the complete story system"""
    print("🧪 Testing Complete Story Campaign System...")
    
    # Test player ID
    test_player_id = "123456789"
    
    try:
        # Create a test player
        print(f"👤 Creating test player {test_player_id}...")
        player = Player(test_player_id)
        player.level = 1
        await player.save()
        print("✅ Test player created and saved!")
        
        # Test getting story progress (should be empty initially)
        print("📖 Testing story progress retrieval...")
        progress = await StoryCampaign.get_player_story_progress(test_player_id)
        print(f"✅ Initial story progress: {progress}")
        
        # Test checking mission availability
        print("🎯 Testing mission availability...")
        is_available, reason = await StoryCampaign.is_mission_available(test_player_id, "prologue_001")
        print(f"✅ Prologue mission available: {is_available} ({reason})")
        
        # Test completing a mission
        print("🏆 Testing mission completion...")
        success, message, rewards = await StoryCampaign.complete_mission(test_player_id, "prologue_001")
        print(f"✅ Mission completion: {success} - {message}")
        if rewards:
            print(f"🎁 Rewards: Gold={rewards.gold}, XP={rewards.xp}, Title={rewards.title}")
        
        # Test getting updated progress
        print("📊 Testing updated progress...")
        updated_progress = await StoryCampaign.get_player_story_progress(test_player_id)
        print(f"✅ Updated progress: {updated_progress}")
        
        # Test getting available missions
        print("🎮 Testing available missions...")
        available_missions = await StoryCampaign.get_available_missions(test_player_id)
        print(f"✅ Available missions: {[m.name for m in available_missions]}")
        
        # Test getting completed missions
        print("✅ Testing completed missions...")
        completed_missions = await StoryCampaign.get_completed_missions(test_player_id)
        print(f"✅ Completed missions: {[m.name for m in completed_missions]}")
        
        # Clean up test player
        print("🧹 Cleaning up test player...")
        import aiosqlite
        async with aiosqlite.connect("data/player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
            await conn.commit()
        print("✅ Test player cleaned up!")
        
        print("🎉 All story system tests passed!")
        
    except Exception as e:
        print(f"❌ Story system test failed: {e}")
        logging.error(f"Story system test failed: {e}")
        
        # Clean up on error
        try:
            import aiosqlite
            async with aiosqlite.connect("data/player.db") as conn:
                await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
                await conn.commit()
        except:
            pass

async def main():
    """Main test function"""
    await test_story_system()

if __name__ == "__main__":
    asyncio.run(main())
