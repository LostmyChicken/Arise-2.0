#!/usr/bin/env python3
"""
Test the title system functionality.
"""

import asyncio
import logging
from structure.player import Player
from structure.title_system import TitleManager, TitleCategory

async def test_title_system():
    """Test the title system"""
    print("🧪 Testing Title System...")
    
    # Test player ID
    test_player_id = "111222333"
    
    try:
        # Create a test player
        print(f"👤 Creating test player {test_player_id}...")
        player = Player(test_player_id)
        player.level = 25
        player.gold = 50000
        
        # Add some story progress to unlock titles
        player.story_progress = {
            "prologue_001": {"completed": True, "completed_at": 1234567890},
            "prologue_002": {"completed": True, "completed_at": 1234567891},
            "double_dungeon_001": {"completed": True, "completed_at": 1234567892},
            "double_dungeon_002": {"completed": True, "completed_at": 1234567893}
        }
        
        await player.save()
        print("✅ Test player created!")
        
        # Test title system components
        print("🏆 Testing title system components...")
        
        # Test getting player titles (should be empty initially)
        player_titles = await TitleManager.get_player_titles(test_player_id)
        print(f"✅ Initial player titles: {len(player_titles)} titles")
        
        # Test checking and unlocking story titles
        print("📖 Testing story title unlocking...")
        newly_unlocked = await TitleManager.check_and_unlock_story_titles(test_player_id)
        print(f"✅ Newly unlocked titles: {len(newly_unlocked)}")
        
        for title_id in newly_unlocked:
            title = TitleManager.get_title_by_id(title_id)
            if title:
                print(f"   - {title.get_display_name()}: {title.description}")
        
        # Test getting unlocked titles
        unlocked_titles = await TitleManager.get_unlocked_titles(test_player_id)
        print(f"✅ Total unlocked titles: {len(unlocked_titles)}")
        
        # Test setting active title
        if unlocked_titles:
            first_title = unlocked_titles[0]
            print(f"🎯 Testing title activation: {first_title.name}")
            
            success = await TitleManager.set_player_active_title(test_player_id, first_title.id)
            print(f"✅ Title activation successful: {success}")
            
            # Test getting active title
            active_title_id = await TitleManager.get_player_active_title(test_player_id)
            print(f"✅ Active title ID: {active_title_id}")
            
            # Test title display for profile
            title_display = await TitleManager.get_title_display_for_profile(test_player_id)
            print(f"✅ Profile title display: '{title_display}'")
        
        # Test getting titles by category
        print("📋 Testing title categories...")
        
        categories = [TitleCategory.STORY, TitleCategory.ACHIEVEMENT, TitleCategory.RANK]
        for category in categories:
            category_titles = await TitleManager.get_titles_by_category(test_player_id, category)
            unlocked_count = sum(1 for _, is_unlocked in category_titles if is_unlocked)
            print(f"✅ {category.value.title()} titles: {unlocked_count}/{len(category_titles)} unlocked")
        
        # Test title data structure
        print("🔍 Testing title data structure...")
        
        # Test different title rarities
        rarity_counts = {}
        for title_id, title in TitleManager.TITLES.items():
            rarity = title.rarity.value
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
        
        print("✅ Title rarity distribution:")
        for rarity, count in rarity_counts.items():
            print(f"   - {rarity.title()}: {count} titles")
        
        # Test title categories
        category_counts = {}
        for title_id, title in TitleManager.TITLES.items():
            category = title.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("✅ Title category distribution:")
        for category, count in category_counts.items():
            print(f"   - {category.title()}: {count} titles")
        
        # Test specific story titles
        print("📚 Testing specific story titles...")
        
        story_titles_to_check = [
            "novice_hunter",
            "system_user", 
            "shadow_monarch",
            "world_savior",
            "eternal_shadow_monarch"
        ]
        
        for title_id in story_titles_to_check:
            title = TitleManager.get_title_by_id(title_id)
            if title:
                print(f"✅ {title.name}:")
                print(f"   - Rarity: {title.rarity.value}")
                print(f"   - Category: {title.category.value}")
                print(f"   - Color: #{title.get_rarity_color():06x}")
                print(f"   - Unlock: {title.unlock_condition}")
        
        # Test title unlocking manually
        print("🔓 Testing manual title unlocking...")
        
        # Try to unlock an achievement title manually
        achievement_title_id = "first_steps"
        unlock_success = await TitleManager.unlock_title(test_player_id, achievement_title_id)
        print(f"✅ Manual unlock successful: {unlock_success}")
        
        if unlock_success:
            # Set it as active
            set_success = await TitleManager.set_player_active_title(test_player_id, achievement_title_id)
            print(f"✅ Set as active: {set_success}")
            
            # Check display
            new_display = await TitleManager.get_title_display_for_profile(test_player_id)
            print(f"✅ New profile display: '{new_display}'")
        
        # Test player data persistence
        print("💾 Testing data persistence...")
        
        # Reload player and check titles persist
        reloaded_player = await Player.get(test_player_id)
        if reloaded_player:
            print(f"✅ Player reloaded successfully")
            print(f"✅ Titles data: {len(reloaded_player.titles) if hasattr(reloaded_player, 'titles') else 0} titles")
            print(f"✅ Active title: {getattr(reloaded_player, 'active_title', 'None')}")
        
        # Clean up test player
        print("🧹 Cleaning up test data...")
        import aiosqlite
        async with aiosqlite.connect("new_player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
            await conn.commit()
        print("✅ Test data cleaned up!")
        
        print("🎉 Title system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Title system test failed: {e}")
        logging.error(f"Title system test failed: {e}")
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
    await test_title_system()

if __name__ == "__main__":
    asyncio.run(main())
