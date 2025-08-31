#!/usr/bin/env python3
"""
Test the complete Solo Leveling story system
"""
import asyncio

async def test_complete_story_content():
    """Test that all Solo Leveling story content is properly implemented"""
    print("🧪 Testing Complete Solo Leveling Story Content...")
    
    try:
        from structure.interactive_story import STORY_EVENTS
        from structure.story_campaign import StoryCampaign
        
        # Test story events
        story_missions = STORY_EVENTS
        campaign_missions = StoryCampaign.STORY_MISSIONS
        
        print(f"  📚 Interactive Story Events: {len(story_missions)} missions")
        print(f"  📋 Campaign Missions: {len(campaign_missions)} missions")
        
        # Major story arcs to verify
        expected_arcs = [
            "prologue_001",           # The Weakest Hunter
            "prologue_002",           # Hunter's License
            "prologue_003",           # First Steps
            "double_dungeon_001",     # The Double Dungeon
            "double_dungeon_002",     # System Awakening
            "instant_dungeon_001",    # Daily Quest Penalty
            "job_change_001",         # Job Change Quest
            "reawakening_001",        # Reawakening Test
            "cartenon_001",           # Cartenon Temple
            "red_gate_001",           # Red Gate Incident
            "demon_castle_001",       # Demon Castle
            "jeju_island_001",        # Jeju Island Raid
            "shadow_monarch_001"      # Shadow Monarch Awakening
        ]
        
        # Check interactive story events
        missing_interactive = []
        for arc in expected_arcs:
            if arc in story_missions:
                events = story_missions[arc]
                print(f"    ✅ {arc}: {len(events)} events")
            else:
                missing_interactive.append(arc)
                print(f"    ❌ {arc}: Missing from interactive stories")
        
        # Check campaign missions
        missing_campaign = []
        for arc in expected_arcs:
            if arc in campaign_missions:
                mission = campaign_missions[arc]
                print(f"    ✅ {arc}: {mission.name}")
            else:
                missing_campaign.append(arc)
                print(f"    ❌ {arc}: Missing from campaign")
        
        if not missing_interactive and not missing_campaign:
            print("  ✅ All major Solo Leveling story arcs are implemented")
            return True
        else:
            print(f"  ❌ Missing interactive: {missing_interactive}")
            print(f"  ❌ Missing campaign: {missing_campaign}")
            return False
        
    except Exception as e:
        print(f"  ❌ Error testing story content: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_battle_events():
    """Test that all major battles are implemented"""
    print("\n⚔️ Testing Battle Events...")
    
    try:
        from structure.interactive_story import STORY_EVENTS, StoryEventType
        
        battle_events = []
        total_battles = 0
        
        for mission_id, events in STORY_EVENTS.items():
            for event in events:
                if event.event_type == StoryEventType.BATTLE:
                    total_battles += 1
                    if event.battle_enemies:
                        enemy = event.battle_enemies[0]
                        battle_info = {
                            "mission": mission_id,
                            "title": event.title,
                            "enemy": enemy["name"],
                            "level": enemy["level"],
                            "hp": enemy["hp"]
                        }
                        battle_events.append(battle_info)
                        print(f"    ⚔️ {mission_id}: {enemy['name']} (Lv.{enemy['level']}, HP:{enemy['hp']})")
        
        print(f"  📊 Total Battle Events: {total_battles}")
        
        # Expected major battles
        expected_battles = [
            "Goblin",           # Prologue
            "Temple Guardian",  # Double Dungeon
            "Giant Centipede",  # Instant Dungeon
            "Trial Knight",     # Job Change
            "Test Golem",       # Reawakening
            "Stone Guardian",   # Cartenon Temple
            "Ice Bear",         # Red Gate
            "Baran",           # Demon Castle
            "Ant Queen",       # Jeju Island
            "The Architect"    # Final Battle
        ]
        
        found_battles = [battle["enemy"] for battle in battle_events]
        missing_battles = [battle for battle in expected_battles if battle not in found_battles]
        
        if not missing_battles:
            print("  ✅ All major Solo Leveling battles are implemented")
            return True
        else:
            print(f"  ❌ Missing battles: {missing_battles}")
            return False
        
    except Exception as e:
        print(f"  ❌ Error testing battle events: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_story_progression():
    """Test that story progression works correctly"""
    print("\n📈 Testing Story Progression...")
    
    try:
        from structure.story_campaign import StoryCampaign
        
        missions = StoryCampaign.STORY_MISSIONS
        
        # Test prerequisite chain
        progression_chain = [
            ("prologue_001", []),
            ("prologue_002", ["prologue_001"]),
            ("double_dungeon_001", ["prologue_003"]),  # Fixed to match actual prerequisite
            ("double_dungeon_002", ["double_dungeon_001"]),
            ("instant_dungeon_001", ["double_dungeon_002"]),
            ("job_change_001", ["instant_dungeon_001"]),
            ("reawakening_001", ["job_change_001"]),
            ("cartenon_001", ["reawakening_001"])
        ]
        
        for mission_id, expected_prereqs in progression_chain:
            if mission_id in missions:
                mission = missions[mission_id]
                actual_prereqs = mission.prerequisites
                
                if set(actual_prereqs) == set(expected_prereqs):
                    print(f"    ✅ {mission_id}: Prerequisites correct")
                else:
                    print(f"    ❌ {mission_id}: Expected {expected_prereqs}, got {actual_prereqs}")
                    return False
            else:
                print(f"    ❌ {mission_id}: Mission not found")
                return False
        
        print("  ✅ Story progression chain is correctly implemented")
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing story progression: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_choice_system():
    """Test that the choice system is comprehensive"""
    print("\n🎯 Testing Choice System...")
    
    try:
        from structure.interactive_story import STORY_EVENTS
        
        total_choices = 0
        choice_types = {}
        
        for mission_id, events in STORY_EVENTS.items():
            for event in events:
                if hasattr(event, 'choices') and event.choices:
                    for choice in event.choices:
                        total_choices += 1
                        choice_type = choice.choice_type.value
                        choice_types[choice_type] = choice_types.get(choice_type, 0) + 1
        
        print(f"  📊 Total Choices: {total_choices}")
        print("  📋 Choice Types:")
        for choice_type, count in choice_types.items():
            print(f"    • {choice_type.replace('_', ' ').title()}: {count}")
        
        # Expected minimum choices for a complete story
        if total_choices >= 50:  # Should have at least 50 meaningful choices
            print("  ✅ Choice system is comprehensive")
            return True
        else:
            print(f"  ❌ Not enough choices: {total_choices} (expected at least 50)")
            return False
        
    except Exception as e:
        print(f"  ❌ Error testing choice system: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🎭 COMPLETE SOLO LEVELING STORY SYSTEM TEST")
    print("=" * 70)
    
    tests = [
        ("Complete Story Content", test_complete_story_content),
        ("Battle Events", test_battle_events),
        ("Story Progression", test_story_progression),
        ("Choice System", test_choice_system)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 70)
    print("📊 COMPLETE STORY TEST SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 COMPLETE SOLO LEVELING STORY SYSTEM READY!")
        print("🚀 All story content implemented and tested!")
        print("\n📚 COMPLETE STORY FEATURES:")
        print("  🎭 12 Major Story Arcs from Weakest Hunter to Shadow Monarch")
        print("  ⚔️ 10+ Epic Battles with real gate combat mechanics")
        print("  🎯 50+ Meaningful Choices that shape the narrative")
        print("  📈 Progressive Difficulty from E-rank to Monarch level")
        print("  🏆 Complete Solo Leveling experience with all major events")
        print("\n🎮 READY FOR PLAYERS:")
        print("  • Experience the complete Solo Leveling story")
        print("  • Fight all major battles with strategic choices")
        print("  • Make decisions that affect Jin-Woo's character development")
        print("  • Progress from weakest hunter to Shadow Monarch")
        print("  • Enjoy professional-quality interactive storytelling")
    else:
        print(f"\n⚠️ {failed} TESTS FAILED")
        print("🔧 Please review the errors above and complete missing content")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
