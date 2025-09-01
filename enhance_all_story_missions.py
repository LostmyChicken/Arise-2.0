#!/usr/bin/env python3
"""
Script to enhance all story missions to have 5-10 choices per event
"""

# Enhanced choice templates for different story contexts
CHOICE_TEMPLATES = {
    "EMOTIONAL": [
        {"text": "Express your feelings openly", "emoji": "💭", "consequences": {"emotional_openness": 2, "vulnerability": 1}},
        {"text": "Keep your emotions private", "emoji": "🤐", "consequences": {"emotional_control": 2, "privacy": 1}},
        {"text": "Channel emotions into determination", "emoji": "🔥", "consequences": {"determination": 2, "emotional_strength": 1}},
        {"text": "Seek comfort from others", "emoji": "🤗", "consequences": {"social_support": 2, "trust": 1}},
        {"text": "Use humor to cope", "emoji": "😄", "consequences": {"resilience": 2, "positivity": 1}},
    ],
    
    "COMBAT": [
        {"text": "Attack aggressively", "emoji": "⚔️", "consequences": {"aggression": 2, "combat_skill": 1}},
        {"text": "Focus on defense", "emoji": "🛡️", "consequences": {"defense": 2, "caution": 1}},
        {"text": "Use tactical approach", "emoji": "🎯", "consequences": {"strategy": 2, "intelligence": 1}},
        {"text": "Try to intimidate", "emoji": "😤", "consequences": {"intimidation": 2, "presence": 1}},
        {"text": "Look for weaknesses", "emoji": "🔍", "consequences": {"observation": 2, "analytical": 1}},
        {"text": "Use environment", "emoji": "🌍", "consequences": {"creativity": 2, "adaptability": 1}},
        {"text": "Coordinate with team", "emoji": "👥", "consequences": {"teamwork": 2, "leadership": 1}},
    ],
    
    "SOCIAL": [
        {"text": "Be friendly and approachable", "emoji": "😊", "consequences": {"charisma": 2, "likability": 1}},
        {"text": "Maintain professional distance", "emoji": "🤝", "consequences": {"professionalism": 2, "respect": 1}},
        {"text": "Show genuine interest", "emoji": "🤔", "consequences": {"empathy": 2, "understanding": 1}},
        {"text": "Assert your position", "emoji": "💪", "consequences": {"confidence": 2, "authority": 1}},
        {"text": "Listen more than speak", "emoji": "👂", "consequences": {"wisdom": 2, "patience": 1}},
        {"text": "Ask thoughtful questions", "emoji": "❓", "consequences": {"curiosity": 2, "intelligence": 1}},
        {"text": "Share personal experience", "emoji": "📖", "consequences": {"openness": 2, "trust_building": 1}},
    ],
    
    "EXPLORATION": [
        {"text": "Investigate thoroughly", "emoji": "🔍", "consequences": {"thoroughness": 2, "discovery": 1}},
        {"text": "Proceed with caution", "emoji": "🚶‍♂️", "consequences": {"caution": 2, "safety": 1}},
        {"text": "Move quickly", "emoji": "🏃‍♂️", "consequences": {"speed": 2, "efficiency": 1}},
        {"text": "Look for hidden paths", "emoji": "🗺️", "consequences": {"exploration": 2, "creativity": 1}},
        {"text": "Mark your route", "emoji": "📍", "consequences": {"preparation": 2, "planning": 1}},
        {"text": "Study the environment", "emoji": "🌿", "consequences": {"knowledge": 2, "observation": 1}},
        {"text": "Trust your instincts", "emoji": "💫", "consequences": {"intuition": 2, "confidence": 1}},
    ],
    
    "MORAL": [
        {"text": "Do what's right", "emoji": "⚖️", "consequences": {"morality": 3, "righteousness": 2}},
        {"text": "Consider all perspectives", "emoji": "🤷‍♂️", "consequences": {"wisdom": 2, "understanding": 2}},
        {"text": "Prioritize the greater good", "emoji": "🌍", "consequences": {"altruism": 3, "sacrifice": 1}},
        {"text": "Protect the innocent", "emoji": "🛡️", "consequences": {"protection": 3, "heroism": 2}},
        {"text": "Seek justice", "emoji": "⚖️", "consequences": {"justice": 3, "determination": 2}},
        {"text": "Show mercy", "emoji": "🕊️", "consequences": {"compassion": 3, "forgiveness": 2}},
        {"text": "Stand by your principles", "emoji": "💎", "consequences": {"integrity": 3, "strength": 2}},
    ],
    
    "STRATEGIC": [
        {"text": "Analyze the situation", "emoji": "🧠", "consequences": {"analysis": 2, "intelligence": 1}},
        {"text": "Plan multiple contingencies", "emoji": "📋", "consequences": {"planning": 3, "preparation": 2}},
        {"text": "Gather more information", "emoji": "📊", "consequences": {"knowledge": 2, "patience": 1}},
        {"text": "Act on instinct", "emoji": "⚡", "consequences": {"intuition": 2, "boldness": 1}},
        {"text": "Consult with others", "emoji": "👥", "consequences": {"collaboration": 2, "wisdom_seeking": 1}},
        {"text": "Take calculated risks", "emoji": "🎲", "consequences": {"courage": 2, "strategic_thinking": 1}},
        {"text": "Wait for the right moment", "emoji": "⏰", "consequences": {"patience": 2, "timing": 2}},
    ]
}

def generate_enhanced_choices(base_choices, context_type, event_theme):
    """Generate 5-10 enhanced choices based on context"""
    enhanced_choices = []
    
    # Keep original choices if they're good
    for choice in base_choices:
        enhanced_choices.append(choice)
    
    # Add more choices from templates
    template_choices = CHOICE_TEMPLATES.get(context_type, CHOICE_TEMPLATES["SOCIAL"])
    
    # Add choices until we have 5-10 total
    choice_count = len(enhanced_choices)
    needed_choices = max(5 - choice_count, 0)
    
    for i in range(min(needed_choices, len(template_choices))):
        template = template_choices[i]
        enhanced_choice = {
            "id": f"enhanced_{i+1}",
            "text": template["text"],
            "description": f"A {context_type.lower()} approach to the situation",
            "choice_type": context_type,
            "consequences": template["consequences"],
            "emoji": template["emoji"]
        }
        enhanced_choices.append(enhanced_choice)
    
    return enhanced_choices[:10]  # Cap at 10 choices

# Mission enhancement mapping
MISSION_ENHANCEMENTS = {
    "prologue_002": "EMOTIONAL",
    "prologue_003": "COMBAT", 
    "double_dungeon_001": "EXPLORATION",
    "double_dungeon_002": "STRATEGIC",
    "instant_dungeon_001": "COMBAT",
    "job_change_001": "STRATEGIC",
    "reawakening_001": "EMOTIONAL",
    "cartenon_001": "EXPLORATION",
    "cartenon_002": "STRATEGIC",
    "demon_castle_001": "COMBAT",
    "red_gate_001": "MORAL",
    "shadow_monarch_001": "STRATEGIC",
    "jeju_island_001": "COMBAT",
    "jeju_island_002": "EMOTIONAL",
    "monarchs_war_001": "COMBAT",
    "monarchs_war_002": "COMBAT", 
    "monarchs_war_003": "COMBAT",
    "final_battle_001": "STRATEGIC",
    "final_battle_002": "MORAL"
}

print("🎮 STORY MISSION ENHANCEMENT GUIDE")
print("=" * 50)
print()
print("✅ ALREADY ENHANCED (5-10 choices per event):")
print("  📖 prologue_001: 8-9 choices per event")
print("  👑 demon_castle_002: 9-10 choices per event") 
print("  🌟 final_battle_003: 10 choices per event")
print()
print("⚠️  MISSIONS NEEDING ENHANCEMENT:")
for mission_id, context in MISSION_ENHANCEMENTS.items():
    print(f"  📝 {mission_id}: Enhance with {context} choices")
print()
print("🔧 ENHANCEMENT STRATEGY:")
print("  1. Each event should have 5-10 meaningful choices")
print("  2. Choices should reflect different personality approaches")
print("  3. Consequences should affect character development")
print("  4. Maintain story coherence and Solo Leveling theme")
print()
print("📊 TARGET RESULTS:")
print("  🎯 22 missions × 5-10 choices per event = 500+ total choices")
print("  🎮 Highly interactive Solo Leveling experience")
print("  ⭐ Every player decision matters and shapes the story")
print()
print("✨ This will create the most interactive Solo Leveling story system ever!")
