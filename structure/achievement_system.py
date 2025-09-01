import json
import logging
import aiosqlite
import time
from typing import Dict, List, Optional, Any
from enum import Enum

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("achievements", "achievements.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "achievements.db"

DATABASE_PATH = get_database_path()

class AchievementCategory(Enum):
    """Achievement categories"""
    COMBAT = "Combat"
    PROGRESSION = "Progression"
    COLLECTION = "Collection"
    SOCIAL = "Social"
    EXPLORATION = "Exploration"
    SPECIAL = "Special"

class AchievementRarity(Enum):
    """Achievement rarity levels"""
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    MYTHIC = "Mythic"

class Achievement:
    """Individual achievement definition"""
    
    def __init__(self, achievement_id: str, name: str, description: str, category: AchievementCategory, 
                 rarity: AchievementRarity, requirements: Dict, rewards: Dict, hidden: bool = False):
        self.id = achievement_id
        self.name = name
        self.description = description
        self.category = category
        self.rarity = rarity
        self.requirements = requirements
        self.rewards = rewards
        self.hidden = hidden

class AchievementSystem:
    """
    Solo Leveling style Achievement System
    """
    
    # Predefined achievements
    ACHIEVEMENTS = {
        # Progression Achievements
        "first_steps": Achievement(
            "first_steps", "First Steps", "Reach level 5",
            AchievementCategory.PROGRESSION, AchievementRarity.COMMON,
            {"level": 5}, {"gold": 1000, "title": "Novice Hunter"}
        ),
        "rising_hunter": Achievement(
            "rising_hunter", "Rising Hunter", "Reach level 25",
            AchievementCategory.PROGRESSION, AchievementRarity.RARE,
            {"level": 25}, {"gold": 5000, "stat_points": 10, "title": "Rising Hunter"}
        ),
        "veteran_hunter": Achievement(
            "veteran_hunter", "Veteran Hunter", "Reach level 50",
            AchievementCategory.PROGRESSION, AchievementRarity.EPIC,
            {"level": 50}, {"gold": 15000, "stat_points": 25, "title": "Veteran Hunter"}
        ),
        "elite_hunter": Achievement(
            "elite_hunter", "Elite Hunter", "Reach level 100",
            AchievementCategory.PROGRESSION, AchievementRarity.LEGENDARY,
            {"level": 100}, {"gold": 50000, "stat_points": 50, "title": "Elite Hunter"}
        ),
        
        # Combat Achievements
        "first_blood": Achievement(
            "first_blood", "First Blood", "Win your first battle",
            AchievementCategory.COMBAT, AchievementRarity.COMMON,
            {"battles_won": 1}, {"gold": 500, "title": "Warrior"}
        ),
        "battle_tested": Achievement(
            "battle_tested", "Battle Tested", "Win 100 battles",
            AchievementCategory.COMBAT, AchievementRarity.RARE,
            {"battles_won": 100}, {"gold": 10000, "stat_points": 15}
        ),
        "war_machine": Achievement(
            "war_machine", "War Machine", "Win 1000 battles",
            AchievementCategory.COMBAT, AchievementRarity.EPIC,
            {"battles_won": 1000}, {"gold": 25000, "stat_points": 30, "title": "War Machine"}
        ),
        "shadow_monarch": Achievement(
            "shadow_monarch", "Shadow Monarch", "Collect 50 shadows",
            AchievementCategory.COLLECTION, AchievementRarity.LEGENDARY,
            {"shadows_collected": 50}, {"gold": 100000, "stat_points": 100, "title": "Shadow Monarch"}
        ),
        
        # Collection Achievements
        "collector": Achievement(
            "collector", "Collector", "Obtain 25 different items",
            AchievementCategory.COLLECTION, AchievementRarity.COMMON,
            {"unique_items": 25}, {"gold": 2000, "title": "Collector"}
        ),
        "hoarder": Achievement(
            "hoarder", "Hoarder", "Obtain 100 different items",
            AchievementCategory.COLLECTION, AchievementRarity.RARE,
            {"unique_items": 100}, {"gold": 8000, "stat_points": 20}
        ),
        "master_collector": Achievement(
            "master_collector", "Master Collector", "Obtain 250 different items",
            AchievementCategory.COLLECTION, AchievementRarity.EPIC,
            {"unique_items": 250}, {"gold": 20000, "stat_points": 40, "title": "Master Collector"}
        ),
        
        # Social Achievements
        "guild_member": Achievement(
            "guild_member", "Guild Member", "Join a guild",
            AchievementCategory.SOCIAL, AchievementRarity.COMMON,
            {"guild_joined": True}, {"gold": 1500, "title": "Guild Member"}
        ),
        "team_player": Achievement(
            "team_player", "Team Player", "Complete 10 party activities",
            AchievementCategory.SOCIAL, AchievementRarity.RARE,
            {"party_activities": 10}, {"gold": 5000, "stat_points": 10}
        ),
        
        # Exploration Achievements
        "dungeon_crawler": Achievement(
            "dungeon_crawler", "Dungeon Crawler", "Clear 10 dungeons",
            AchievementCategory.EXPLORATION, AchievementRarity.COMMON,
            {"dungeons_cleared": 10}, {"gold": 3000, "title": "Dungeon Crawler"}
        ),
        "dungeon_master": Achievement(
            "dungeon_master", "Dungeon Master", "Clear 100 dungeons",
            AchievementCategory.EXPLORATION, AchievementRarity.EPIC,
            {"dungeons_cleared": 100}, {"gold": 25000, "stat_points": 35, "title": "Dungeon Master"}
        ),
        
        # Special Achievements
        "lucky_hunter": Achievement(
            "lucky_hunter", "Lucky Hunter", "Get 10 rare drops in a row",
            AchievementCategory.SPECIAL, AchievementRarity.MYTHIC,
            {"consecutive_rare_drops": 10}, {"gold": 200000, "stat_points": 200, "title": "Blessed by RNG"}, True
        ),
        "speed_demon": Achievement(
            "speed_demon", "Speed Demon", "Complete daily quests 30 days in a row",
            AchievementCategory.SPECIAL, AchievementRarity.LEGENDARY,
            {"daily_streak": 30}, {"gold": 75000, "stat_points": 75, "title": "Speed Demon"}
        )
    }
    
    @classmethod
    async def initialize(cls):
        """Initialize the achievement database"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_achievements (
                    player_id TEXT,
                    achievement_id TEXT,
                    unlocked_at TEXT,
                    progress TEXT DEFAULT '{}',
                    PRIMARY KEY (player_id, achievement_id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS achievement_progress (
                    player_id TEXT PRIMARY KEY,
                    level INTEGER DEFAULT 1,
                    battles_won INTEGER DEFAULT 0,
                    shadows_collected INTEGER DEFAULT 0,
                    unique_items INTEGER DEFAULT 0,
                    dungeons_cleared INTEGER DEFAULT 0,
                    party_activities INTEGER DEFAULT 0,
                    daily_streak INTEGER DEFAULT 0,
                    consecutive_rare_drops INTEGER DEFAULT 0,
                    guild_joined INTEGER DEFAULT 0,
                    total_damage_dealt INTEGER DEFAULT 0,
                    total_xp_gained INTEGER DEFAULT 0
                )
            """)
            await db.commit()
    
    @classmethod
    async def update_progress(cls, player_id: str, **kwargs):
        """Update player's achievement progress"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get current progress
            cursor = await db.execute(
                "SELECT * FROM achievement_progress WHERE player_id = ?",
                (player_id,)
            )
            result = await cursor.fetchone()
            await cursor.close()
            
            if result:
                # Update existing record
                update_fields = []
                update_values = []
                for key, value in kwargs.items():
                    if key in ['level', 'battles_won', 'shadows_collected', 'unique_items', 
                              'dungeons_cleared', 'party_activities', 'daily_streak', 
                              'consecutive_rare_drops', 'guild_joined', 'total_damage_dealt', 'total_xp_gained']:
                        update_fields.append(f"{key} = ?")
                        update_values.append(value)
                
                if update_fields:
                    update_values.append(player_id)
                    await db.execute(
                        f"UPDATE achievement_progress SET {', '.join(update_fields)} WHERE player_id = ?",
                        update_values
                    )
            else:
                # Create new record
                await db.execute("""
                    INSERT INTO achievement_progress (player_id, level, battles_won, shadows_collected, 
                    unique_items, dungeons_cleared, party_activities, daily_streak, consecutive_rare_drops, 
                    guild_joined, total_damage_dealt, total_xp_gained)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_id,
                    kwargs.get('level', 1),
                    kwargs.get('battles_won', 0),
                    kwargs.get('shadows_collected', 0),
                    kwargs.get('unique_items', 0),
                    kwargs.get('dungeons_cleared', 0),
                    kwargs.get('party_activities', 0),
                    kwargs.get('daily_streak', 0),
                    kwargs.get('consecutive_rare_drops', 0),
                    kwargs.get('guild_joined', 0),
                    kwargs.get('total_damage_dealt', 0),
                    kwargs.get('total_xp_gained', 0)
                ))
            
            await db.commit()
            
            # Check for new achievements
            return await cls.check_achievements(player_id)
    
    @classmethod
    async def check_achievements(cls, player_id: str) -> List[Achievement]:
        """Check if player has unlocked any new achievements"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get player progress
            cursor = await db.execute(
                "SELECT * FROM achievement_progress WHERE player_id = ?",
                (player_id,)
            )
            progress_result = await cursor.fetchone()
            await cursor.close()
            
            if not progress_result:
                return []
            
            # Get already unlocked achievements
            cursor = await db.execute(
                "SELECT achievement_id FROM player_achievements WHERE player_id = ?",
                (player_id,)
            )
            unlocked = {row[0] for row in await cursor.fetchall()}
            await cursor.close()
            
            # Convert progress to dict
            progress_keys = ['player_id', 'level', 'battles_won', 'shadows_collected', 'unique_items', 
                           'dungeons_cleared', 'party_activities', 'daily_streak', 'consecutive_rare_drops', 
                           'guild_joined', 'total_damage_dealt', 'total_xp_gained']
            progress = dict(zip(progress_keys, progress_result))
            
            # Check each achievement
            newly_unlocked = []
            for achievement_id, achievement in cls.ACHIEVEMENTS.items():
                if achievement_id in unlocked:
                    continue
                
                # Check if requirements are met
                requirements_met = True
                for req_key, req_value in achievement.requirements.items():
                    if req_key in progress:
                        if isinstance(req_value, bool):
                            if not (progress[req_key] >= 1 if req_value else progress[req_key] == 0):
                                requirements_met = False
                                break
                        else:
                            if progress[req_key] < req_value:
                                requirements_met = False
                                break
                    else:
                        requirements_met = False
                        break
                
                if requirements_met:
                    # Unlock achievement
                    await db.execute("""
                        INSERT INTO player_achievements (player_id, achievement_id, unlocked_at)
                        VALUES (?, ?, ?)
                    """, (player_id, achievement_id, str(time.time())))
                    await db.commit()
                    newly_unlocked.append(achievement)
            
            return newly_unlocked
    
    @classmethod
    async def get_player_achievements(cls, player_id: str) -> Dict:
        """Get player's achievement data"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get unlocked achievements
            cursor = await db.execute("""
                SELECT achievement_id, unlocked_at FROM player_achievements 
                WHERE player_id = ? ORDER BY unlocked_at DESC
            """, (player_id,))
            unlocked_data = await cursor.fetchall()
            await cursor.close()
            
            # Get progress
            cursor = await db.execute(
                "SELECT * FROM achievement_progress WHERE player_id = ?",
                (player_id,)
            )
            progress_result = await cursor.fetchone()
            await cursor.close()
            
            unlocked = {}
            for achievement_id, unlocked_at in unlocked_data:
                if achievement_id in cls.ACHIEVEMENTS:
                    unlocked[achievement_id] = {
                        'achievement': cls.ACHIEVEMENTS[achievement_id],
                        'unlocked_at': unlocked_at
                    }
            
            progress = {}
            if progress_result:
                progress_keys = ['player_id', 'level', 'battles_won', 'shadows_collected', 'unique_items', 
                               'dungeons_cleared', 'party_activities', 'daily_streak', 'consecutive_rare_drops', 
                               'guild_joined', 'total_damage_dealt', 'total_xp_gained']
                progress = dict(zip(progress_keys, progress_result))
            
            return {
                'unlocked': unlocked,
                'progress': progress,
                'total_unlocked': len(unlocked),
                'total_available': len(cls.ACHIEVEMENTS)
            }
    
    @classmethod
    def get_achievement_by_id(cls, achievement_id: str) -> Optional[Achievement]:
        """Get achievement by ID"""
        return cls.ACHIEVEMENTS.get(achievement_id)
    
    @classmethod
    def get_achievements_by_category(cls, category: AchievementCategory) -> List[Achievement]:
        """Get achievements by category"""
        return [ach for ach in cls.ACHIEVEMENTS.values() if ach.category == category]
    
    @classmethod
    def get_rarity_color(cls, rarity: AchievementRarity) -> int:
        """Get Discord color for achievement rarity"""
        colors = {
            AchievementRarity.COMMON: 0x808080,     # Gray
            AchievementRarity.RARE: 0x0080FF,       # Blue
            AchievementRarity.EPIC: 0x8000FF,       # Purple
            AchievementRarity.LEGENDARY: 0xFFD700,  # Gold
            AchievementRarity.MYTHIC: 0xFF6B35      # Orange-Red
        }
        return colors.get(rarity, 0x808080)
