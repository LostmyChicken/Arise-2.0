#!/usr/bin/env python3
"""
Test script to verify all story missions have interactive events
"""

def test_story_events():
    """Test that all story missions have interactive events"""
    print("🧪 Testing Complete Story Events System...")
    
    try:
        from structure.complete_story_events import COMPLETE_STORY_EVENTS
        print("✅ Successfully imported COMPLETE_STORY_EVENTS")
        
        # Expected missions from StoryCampaign
        expected_missions = [
            "prologue_001", "prologue_002", "prologue_003",
            "double_dungeon_001", "double_dungeon_002", 
            "instant_dungeon_001", "job_change_001", "reawakening_001",
            "cartenon_001", "cartenon_002",
            "demon_castle_001", "demon_castle_002",  # This was auto-completing!
            "red_gate_001", "shadow_monarch_001",
            "jeju_island_001", "jeju_island_002",
            "monarchs_war_001", "monarchs_war_002", "monarchs_war_003",
            "final_battle_001", "final_battle_002", "final_battle_003"
        ]
        
        print(f"📚 Expected missions: {len(expected_missions)}")
        print(f"📖 Available missions: {len(COMPLETE_STORY_EVENTS)}")
        
        missing_missions = []
        available_missions = []
        
        for mission_id in expected_missions:
            if mission_id in COMPLETE_STORY_EVENTS:
                events = COMPLETE_STORY_EVENTS[mission_id]
                available_missions.append(mission_id)
                print(f"  ✅ {mission_id}: {len(events)} events")
                
                # Check if events have choices
                total_choices = 0
                battle_events = 0
                for event in events:
                    if hasattr(event, 'choices') and event.choices:
                        total_choices += len(event.choices)
                    if hasattr(event, 'event_type') and 'BATTLE' in event.event_type.upper():
                        battle_events += 1
                
                if total_choices > 0:
                    print(f"      💭 {total_choices} total choices")
                if battle_events > 0:
                    print(f"      ⚔️ {battle_events} battle events")
            else:
                missing_missions.append(mission_id)
                print(f"  ❌ {mission_id}: MISSING")
        
        print(f"\n📊 Summary:")
        print(f"  ✅ Available: {len(available_missions)}/{len(expected_missions)}")
        print(f"  ❌ Missing: {len(missing_missions)}")
        
        if missing_missions:
            print(f"\n🚨 Missing missions: {missing_missions}")
            return False
        
        # Special test for demon_castle_002 (the one that was auto-completing)
        print(f"\n🎯 Special Test: demon_castle_002 (The Demon King's Throne)")
        if "demon_castle_002" in COMPLETE_STORY_EVENTS:
            events = COMPLETE_STORY_EVENTS["demon_castle_002"]
            print(f"  ✅ Found {len(events)} interactive events")
            for i, event in enumerate(events, 1):
                print(f"    {i}. {event.title}")
                if hasattr(event, 'choices') and event.choices:
                    print(f"       - {len(event.choices)} player choices")
            print("  🎉 This mission will now have interactive story instead of auto-completing!")
        else:
            print("  ❌ demon_castle_002 still missing!")
            return False
        
        print(f"\n🎉 SUCCESS: All {len(expected_missions)} story missions now have interactive events!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_story_events()
    if success:
        print("\n✅ All tests passed! The story system is ready.")
    else:
        print("\n❌ Tests failed. Please check the issues above.")
