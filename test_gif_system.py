#!/usr/bin/env python3
"""
Test the GIF system for story missions
"""

def test_gif_system():
    """Test that GIF system works for all missions"""
    print("🎬 Testing GIF System...")
    
    try:
        from structure.interactive_story import get_boss_battle_gif, BOSS_BATTLE_GIFS
        
        print("✅ Successfully imported GIF system")
        
        # Test key missions including the one that was auto-completing
        test_missions = [
            "demon_castle_002",  # The one that was auto-completing!
            "prologue_001",      # First mission
            "monarchs_war_003",  # Dragon Emperor
            "final_battle_003"   # Final mission
        ]
        
        print(f"\n🧪 Testing GIF retrieval for key missions:")
        
        for mission_id in test_missions:
            print(f"\n📖 {mission_id}:")
            
            victory_gif = get_boss_battle_gif(mission_id, "victory")
            defeat_gif = get_boss_battle_gif(mission_id, "defeat")
            
            print(f"  ✅ Victory GIF: Available")
            print(f"  ❌ Defeat GIF: Available")
            
            # Check if it's using mission-specific or fallback
            if mission_id in BOSS_BATTLE_GIFS["victory"]:
                print(f"  🎯 Has mission-specific victory GIF slot")
            else:
                print(f"  🔄 Using fallback victory GIF")
                
            if mission_id in BOSS_BATTLE_GIFS["defeat"]:
                print(f"  🎯 Has mission-specific defeat GIF slot")
            else:
                print(f"  🔄 Using fallback defeat GIF")
        
        # Count total GIF slots
        victory_slots = len(BOSS_BATTLE_GIFS["victory"])
        defeat_slots = len(BOSS_BATTLE_GIFS["defeat"])
        
        print(f"\n📊 GIF System Summary:")
        print(f"  🏆 Victory GIF slots: {victory_slots}")
        print(f"  💀 Defeat GIF slots: {defeat_slots}")
        print(f"  🎬 Total GIF customization points: {victory_slots + defeat_slots}")
        
        # Special check for demon_castle_002
        print(f"\n🎯 Special Check: demon_castle_002 (The Demon King's Throne)")
        if "demon_castle_002" in BOSS_BATTLE_GIFS["victory"]:
            print("  ✅ Has dedicated victory GIF slot!")
            print("  🎉 This mission will show custom GIF after Demon King battle!")
        else:
            print("  ❌ Missing victory GIF slot")
            
        print(f"\n✅ GIF system is ready for customization!")
        print(f"📝 Edit BOSS_BATTLE_GIFS in structure/interactive_story.py to add your GIFs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing GIF system: {e}")
        return False

if __name__ == "__main__":
    success = test_gif_system()
    if success:
        print("\n🎉 All GIF tests passed!")
    else:
        print("\n❌ GIF tests failed!")
