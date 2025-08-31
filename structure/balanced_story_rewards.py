"""
Balanced Story Reward System for Solo Leveling
Ensures fair, achievable rewards that don't break game balance
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from structure.story_campaign import StoryReward, StoryChapter, StoryDifficulty

class BalancedRewardCalculator:
    """Calculates balanced rewards for story missions"""
    
    # Base reward multipliers by difficulty
    DIFFICULTY_MULTIPLIERS = {
        StoryDifficulty.NORMAL: 1.0,
        StoryDifficulty.HARD: 1.5,
        StoryDifficulty.NIGHTMARE: 2.0
    }
    
    # BALANCED chapter progression multipliers (much more reasonable)
    CHAPTER_MULTIPLIERS = {
        StoryChapter.PROLOGUE: 1.0,
        StoryChapter.DOUBLE_DUNGEON: 1.1,      # Reduced from 1.2 to 1.1
        StoryChapter.FIRST_REAWAKENING: 1.2,   # Reduced from 1.4 to 1.2
        StoryChapter.CARTENON_TEMPLE: 1.3,     # Reduced from 1.6 to 1.3
        StoryChapter.DEMON_CASTLE: 1.4,        # Reduced from 1.8 to 1.4
        StoryChapter.RED_GATE: 1.5,            # Reduced from 2.0 to 1.5
        StoryChapter.SHADOW_MONARCH: 1.6,      # Reduced from 2.2 to 1.6
        StoryChapter.JEJU_ISLAND: 1.7,         # Reduced from 2.4 to 1.7
        StoryChapter.MONARCHS_WAR: 1.8,        # Reduced from 2.6 to 1.8
        StoryChapter.FINAL_BATTLE: 2.0         # Reduced from 3.0 to 2.0
    }
    
    @classmethod
    def calculate_balanced_rewards(
        cls, 
        level_requirement: int, 
        chapter: StoryChapter, 
        difficulty: StoryDifficulty,
        is_major_milestone: bool = False
    ) -> StoryReward:
        """Calculate balanced rewards for a story mission"""
        
        # BALANCED base rewards (much more reasonable)
        base_gold = level_requirement * 25  # Reduced from 100 to 25
        base_xp = level_requirement * 15    # Reduced from 50 to 15
        base_diamonds = max(1, level_requirement // 20)  # Reduced from //5 to //20
        base_tickets = max(1, level_requirement // 20)   # Reduced from //10 to //20
        base_stat_points = max(1, level_requirement // 20)  # Reduced from //5 to //20
        base_skill_points = max(1, level_requirement // 30)  # Reduced from //10 to //30
        
        # Apply difficulty multiplier
        difficulty_mult = cls.DIFFICULTY_MULTIPLIERS[difficulty]
        
        # Apply chapter multiplier
        chapter_mult = cls.CHAPTER_MULTIPLIERS[chapter]
        
        # Calculate final rewards
        final_gold = int(base_gold * difficulty_mult * chapter_mult)
        final_xp = int(base_xp * difficulty_mult * chapter_mult)
        final_diamonds = int(base_diamonds * difficulty_mult * chapter_mult)
        final_tickets = int(base_tickets * difficulty_mult * chapter_mult)
        final_stat_points = int(base_stat_points * difficulty_mult)
        final_skill_points = int(base_skill_points * difficulty_mult)
        
        # BALANCED major milestone bonus (reduced)
        if is_major_milestone:
            final_gold = int(final_gold * 1.3)        # Reduced from 1.5 to 1.3
            final_xp = int(final_xp * 1.3)            # Reduced from 1.5 to 1.3
            final_diamonds = int(final_diamonds * 1.5) # Reduced from 2 to 1.5
            final_stat_points = int(final_stat_points * 1.5)  # Reduced from 2 to 1.5
            final_skill_points = int(final_skill_points * 1.5) # Reduced from 2 to 1.5
        
        # STRICT caps to prevent economy breaking (much more reasonable)
        final_gold = min(final_gold, 5000)      # Max 5k gold per mission (was 50k!)
        final_xp = min(final_xp, 2000)          # Max 2k XP per mission (was 25k!)
        final_diamonds = min(final_diamonds, 25) # Max 25 diamonds per mission (was 100!)
        final_tickets = min(final_tickets, 10)   # Max 10 tickets per mission (was 50!)
        final_stat_points = min(final_stat_points, 5)   # Max 5 stat points per mission (was 25!)
        final_skill_points = min(final_skill_points, 3)  # Max 3 skill points per mission (was 15!)
        
        return StoryReward(
            gold=final_gold,
            xp=final_xp,
            diamonds=final_diamonds,
            tickets=final_tickets,
            stat_points=final_stat_points,
            skill_points=final_skill_points
        )
    
    @classmethod
    def get_progression_rewards(cls, chapter: StoryChapter) -> Dict[str, List[str]]:
        """Get appropriate progression rewards for each chapter"""
        
        chapter_rewards = {
            StoryChapter.PROLOGUE: {
                "items": [],  # No items for prologue - just story progression
                "hunters": [],
                "shadows": [],
                "unlocks": ["daily_quests", "basic_training", "weapon_upgrade"]
            },

            StoryChapter.DOUBLE_DUNGEON: {
                "items": [],  # No items - focus on story progression
                "hunters": [],
                "shadows": [],
                "unlocks": ["system_awakening", "leveling_system", "stat_allocation"]
            },

            StoryChapter.FIRST_REAWAKENING: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": [],
                "unlocks": ["shadow_extraction", "advanced_dungeons", "hunter_association"]
            },
            
            StoryChapter.CARTENON_TEMPLE: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": ["igris"],  # Use actual shadow ID (lowercase)
                "unlocks": ["advanced_magic", "temple_rewards", "priest_magic"]
            },

            StoryChapter.DEMON_CASTLE: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": ["tusk"],  # Use actual shadow ID (lowercase)
                "unlocks": ["demon_extraction", "castle_access", "demon_army"]
            },

            StoryChapter.RED_GATE: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": [],
                "unlocks": ["shadow_exchange", "red_gate_mastery", "emergency_response"]
            },

            StoryChapter.SHADOW_MONARCH: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": ["tank"],  # Use actual shadow ID (lowercase)
                "unlocks": ["monarch_powers", "shadow_army", "unlimited_growth"]
            },

            StoryChapter.JEJU_ISLAND: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": [],
                "unlocks": ["ant_army", "island_mastery", "hive_mind"]
            },

            StoryChapter.MONARCHS_WAR: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": [],
                "unlocks": ["monarch_battle", "beast_powers", "ice_powers", "dragon_powers"]
            },

            StoryChapter.FINAL_BATTLE: {
                "items": [],  # No items - story progression only
                "hunters": [],
                "shadows": [],
                "unlocks": ["time_mastery", "world_savior", "eternal_power", "legend_status"]
            }
        }
        
        return chapter_rewards.get(chapter, {
            "items": [],
            "hunters": [],
            "shadows": [],
            "unlocks": []
        })
    
    @classmethod
    def create_balanced_mission_reward(
        cls,
        level_requirement: int,
        chapter: StoryChapter,
        difficulty: StoryDifficulty,
        is_major_milestone: bool = False,
        custom_title: str = None
    ) -> StoryReward:
        """Create a complete balanced reward for a mission"""
        
        # Calculate base rewards
        base_rewards = cls.calculate_balanced_rewards(
            level_requirement, chapter, difficulty, is_major_milestone
        )
        
        # Get progression rewards
        progression = cls.get_progression_rewards(chapter)
        
        # Select appropriate items based on mission level
        items = []
        if level_requirement <= 10:
            items = progression["items"][:1]  # 1 item for early missions
        elif level_requirement <= 30:
            items = progression["items"][:2]  # 2 items for mid missions
        else:
            items = progression["items"]      # All items for late missions
        
        # Select hunters/shadows based on chapter progression
        hunters = []
        shadows = []
        
        if chapter.value in ["first_reawakening", "cartenon_temple", "demon_castle"]:
            hunters = progression["hunters"][:1]
            shadows = progression["shadows"][:1]
        elif chapter.value in ["red_gate", "shadow_monarch", "jeju_island"]:
            hunters = progression["hunters"][:1]
            shadows = progression["shadows"][:2]
        elif chapter.value in ["monarchs_war", "final_battle"]:
            hunters = progression["hunters"]
            shadows = progression["shadows"]
        
        # Create final reward
        return StoryReward(
            gold=base_rewards.gold,
            xp=base_rewards.xp,
            diamonds=base_rewards.diamonds,
            tickets=base_rewards.tickets,
            stat_points=base_rewards.stat_points,
            skill_points=base_rewards.skill_points,
            items=items,
            hunters=hunters,
            shadows=shadows,
            title=custom_title
        )

# Balanced mission rewards for all story missions
BALANCED_MISSION_REWARDS = {
    # PROLOGUE CHAPTER
    "prologue_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=1,
        chapter=StoryChapter.PROLOGUE,
        difficulty=StoryDifficulty.NORMAL,
        custom_title="Novice Hunter"
    ),
    
    "prologue_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=5,
        chapter=StoryChapter.PROLOGUE,
        difficulty=StoryDifficulty.NORMAL,
        is_major_milestone=True,
        custom_title="Licensed Hunter"
    ),
    
    "prologue_003": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=8,
        chapter=StoryChapter.PROLOGUE,
        difficulty=StoryDifficulty.NORMAL,
        custom_title="Trained Hunter"
    ),
    
    # DOUBLE DUNGEON CHAPTER
    "double_dungeon_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=10,
        chapter=StoryChapter.DOUBLE_DUNGEON,
        difficulty=StoryDifficulty.HARD,
        custom_title="Survivor"
    ),
    
    "double_dungeon_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=10,
        chapter=StoryChapter.DOUBLE_DUNGEON,
        difficulty=StoryDifficulty.HARD,
        is_major_milestone=True,
        custom_title="System User"
    ),
    
    # REAWAKENING CHAPTER
    "reawakening_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=20,
        chapter=StoryChapter.FIRST_REAWAKENING,
        difficulty=StoryDifficulty.NORMAL,
        is_major_milestone=True,
        custom_title="Reawakened Hunter"
    ),
    
    # CARTENON TEMPLE CHAPTER
    "cartenon_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=30,
        chapter=StoryChapter.CARTENON_TEMPLE,
        difficulty=StoryDifficulty.HARD,
        custom_title="Temple Conqueror"
    ),
    
    "cartenon_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=32,
        chapter=StoryChapter.CARTENON_TEMPLE,
        difficulty=StoryDifficulty.HARD,
        is_major_milestone=True,
        custom_title="Temple Master"
    ),
    
    # DEMON CASTLE CHAPTER
    "demon_castle_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=40,
        chapter=StoryChapter.DEMON_CASTLE,
        difficulty=StoryDifficulty.HARD,
        custom_title="Castle Challenger"
    ),
    
    "demon_castle_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=45,
        chapter=StoryChapter.DEMON_CASTLE,
        difficulty=StoryDifficulty.NIGHTMARE,
        is_major_milestone=True,
        custom_title="Demon Slayer"
    ),
    
    # RED GATE CHAPTER
    "red_gate_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=50,
        chapter=StoryChapter.RED_GATE,
        difficulty=StoryDifficulty.NIGHTMARE,
        is_major_milestone=True,
        custom_title="Red Gate Hero"
    ),
    
    # SHADOW MONARCH CHAPTER
    "shadow_monarch_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=60,
        chapter=StoryChapter.SHADOW_MONARCH,
        difficulty=StoryDifficulty.NIGHTMARE,
        is_major_milestone=True,
        custom_title="Shadow Monarch"
    ),
    
    # JEJU ISLAND CHAPTER
    "jeju_island_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=70,
        chapter=StoryChapter.JEJU_ISLAND,
        difficulty=StoryDifficulty.NIGHTMARE,
        custom_title="Island Liberator"
    ),
    
    "jeju_island_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=72,
        chapter=StoryChapter.JEJU_ISLAND,
        difficulty=StoryDifficulty.NIGHTMARE,
        is_major_milestone=True,
        custom_title="Ant King Master"
    ),
    
    # MONARCHS WAR CHAPTER
    "monarchs_war_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=80,
        chapter=StoryChapter.MONARCHS_WAR,
        difficulty=StoryDifficulty.NIGHTMARE,
        custom_title="Monarch Slayer"
    ),
    
    "monarchs_war_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=82,
        chapter=StoryChapter.MONARCHS_WAR,
        difficulty=StoryDifficulty.NIGHTMARE,
        custom_title="Frost Conqueror"
    ),
    
    "monarchs_war_003": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=85,
        chapter=StoryChapter.MONARCHS_WAR,
        difficulty=StoryDifficulty.NIGHTMARE,
        is_major_milestone=True,
        custom_title="Dragon Slayer"
    ),
    
    # FINAL BATTLE CHAPTER
    "final_battle_001": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=90,
        chapter=StoryChapter.FINAL_BATTLE,
        difficulty=StoryDifficulty.NIGHTMARE,
        custom_title="Truth Seeker"
    ),
    
    "final_battle_002": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=95,
        chapter=StoryChapter.FINAL_BATTLE,
        difficulty=StoryDifficulty.NIGHTMARE,
        is_major_milestone=True,
        custom_title="World Savior"
    ),
    
    "final_battle_003": BalancedRewardCalculator.create_balanced_mission_reward(
        level_requirement=100,
        chapter=StoryChapter.FINAL_BATTLE,
        difficulty=StoryDifficulty.NORMAL,
        is_major_milestone=True,
        custom_title="Eternal Shadow Monarch"
    )
}
