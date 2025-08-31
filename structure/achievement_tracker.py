"""
Real-time achievement tracking system
Tracks player actions and awards achievements automatically
"""

import logging
from typing import Optional, Dict, Any
from structure.player import Player

class AchievementTracker:
    """Tracks and awards achievements in real-time"""
    
    @staticmethod
    async def track_level_up(player: Player, new_level: int):
        """Track level-based achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        level_achievements = {
            10: "level_10",
            25: "level_25", 
            50: "level_50",
            75: "level_75",
            100: "level_100"
        }
        
        for required_level, achievement_id in level_achievements.items():
            if new_level >= required_level and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Level {required_level} Reached",
                    "description": f"Reached level {required_level}",
                    "progress": new_level,
                    "max_progress": required_level
                })
    
    @staticmethod
    async def track_combat_victory(player: Player, opponent_type: str = "player"):
        """Track combat-related achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        # First victory achievement
        if "first_victory" not in player.achievements:
            await AchievementTracker._award_achievement(player, "first_victory", {
                "name": "First Victory",
                "description": "Won your first battle",
                "progress": 1,
                "max_progress": 1
            })
        
        # Combat milestone achievements based on level (proxy for combat experience)
        combat_achievements = {
            10: "combat_veteran",
            25: "battle_master", 
            50: "war_hero"
        }
        
        for required_level, achievement_id in combat_achievements.items():
            if player.level >= required_level and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Combat Achievement",
                    "description": f"Proven combat prowess",
                    "progress": 1,
                    "max_progress": 1
                })
    
    @staticmethod
    async def track_gacha_pull(player: Player, pulls_count: int = 1):
        """Track gacha-related achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        total_pulls = getattr(player, 'gacha', 0)
        
        gacha_achievements = {
            10: "gacha_novice",
            50: "gacha_enthusiast", 
            100: "gacha_addict",
            500: "gacha_master"
        }
        
        for required_pulls, achievement_id in gacha_achievements.items():
            if total_pulls >= required_pulls and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Gacha Achievement",
                    "description": f"Performed {required_pulls} gacha pulls",
                    "progress": total_pulls,
                    "max_progress": required_pulls
                })
    
    @staticmethod
    async def track_collection(player: Player, item_type: str = "item"):
        """Track collection-related achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        if item_type == "item":
            # Count inventory items
            item_count = 0
            if hasattr(player, 'inventory') and player.inventory:
                for k, v in player.inventory.items():
                    if not k.startswith('s_'):  # Skip shards
                        try:
                            if isinstance(v, dict):
                                quantity = v.get('quantity', 0)
                            elif isinstance(v, int):
                                quantity = v
                            else:
                                quantity = 0
                            
                            if quantity > 0:
                                item_count += 1
                        except Exception:
                            continue
            
            collection_achievements = {
                10: "collector_10",
                25: "collector_25",
                50: "collector_50", 
                100: "collector_100"
            }
            
            for required_items, achievement_id in collection_achievements.items():
                if item_count >= required_items and achievement_id not in player.achievements:
                    await AchievementTracker._award_achievement(player, achievement_id, {
                        "name": f"Item Collector",
                        "description": f"Collected {required_items} different items",
                        "progress": item_count,
                        "max_progress": required_items
                    })
        
        elif item_type == "hunter":
            # Count hunters
            hunter_count = 0
            if hasattr(player, 'hunters') and player.hunters:
                for k, v in player.hunters.items():
                    try:
                        if isinstance(v, dict):
                            quantity = v.get('quantity', 0)
                            level = v.get('level', 0)
                            if quantity > 0 or level > 0:
                                hunter_count += 1
                        elif isinstance(v, int):
                            if v > 0:
                                hunter_count += 1
                    except Exception:
                        continue
            
            hunter_achievements = {
                5: "hunter_collector_5",
                15: "hunter_collector_15",
                30: "hunter_collector_30",
                50: "hunter_collector_50"
            }
            
            for required_hunters, achievement_id in hunter_achievements.items():
                if hunter_count >= required_hunters and achievement_id not in player.achievements:
                    await AchievementTracker._award_achievement(player, achievement_id, {
                        "name": f"Hunter Collector",
                        "description": f"Collected {required_hunters} different hunters",
                        "progress": hunter_count,
                        "max_progress": required_hunters
                    })
    
    @staticmethod
    async def track_guild_join(player: Player, guild_name: str):
        """Track guild-related achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        if "guild_member" not in player.achievements:
            await AchievementTracker._award_achievement(player, "guild_member", {
                "name": "Guild Member",
                "description": f"Joined guild: {guild_name}",
                "progress": 1,
                "max_progress": 1
            })
    
    @staticmethod
    async def track_guild_leadership(player: Player, guild_name: str):
        """Track guild leadership achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        if "guild_leader" not in player.achievements:
            await AchievementTracker._award_achievement(player, "guild_leader", {
                "name": "Guild Leader",
                "description": f"Became leader of guild: {guild_name}",
                "progress": 1,
                "max_progress": 1
            })
    
    @staticmethod
    async def track_wealth(player: Player):
        """Track wealth-related achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        gold = getattr(player, 'gold', 0)
        
        wealth_achievements = {
            1000: "wealthy_1k",
            10000: "wealthy_10k",
            100000: "wealthy_100k",
            1000000: "wealthy_1m"
        }
        
        for required_gold, achievement_id in wealth_achievements.items():
            if gold >= required_gold and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Wealth Achievement",
                    "description": f"Accumulated {required_gold:,} gold",
                    "progress": gold,
                    "max_progress": required_gold
                })
    
    @staticmethod
    async def track_daily_quest(player: Player):
        """Track daily quest achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        if "daily_warrior" not in player.achievements:
            await AchievementTracker._award_achievement(player, "daily_warrior", {
                "name": "Daily Warrior",
                "description": "Completed daily quests",
                "progress": 1,
                "max_progress": 1
            })
    
    @staticmethod
    async def track_arena_participation(player: Player):
        """Track arena achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        arena_achievements = {
            5: "arena_fighter",
            15: "arena_champion",
            30: "arena_legend"
        }
        
        for required_level, achievement_id in arena_achievements.items():
            if player.level >= required_level and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Arena Achievement",
                    "description": f"Arena prowess demonstrated",
                    "progress": 1,
                    "max_progress": 1
                })
    
    @staticmethod
    async def track_gate_exploration(player: Player):
        """Track gate exploration achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        gate_achievements = {
            5: "gate_explorer",
            20: "gate_master",
            40: "dimension_walker"
        }
        
        for required_level, achievement_id in gate_achievements.items():
            if player.level >= required_level and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Gate Achievement",
                    "description": f"Dimensional exploration mastery",
                    "progress": 1,
                    "max_progress": 1
                })
    
    @staticmethod
    async def track_raid_participation(player: Player):
        """Track raid achievements"""
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
        
        raid_achievements = {
            10: "raid_participant",
            25: "raid_veteran",
            50: "raid_legend"
        }
        
        for required_level, achievement_id in raid_achievements.items():
            if player.level >= required_level and achievement_id not in player.achievements:
                await AchievementTracker._award_achievement(player, achievement_id, {
                    "name": f"Raid Achievement",
                    "description": f"Raid mastery demonstrated",
                    "progress": 1,
                    "max_progress": 1
                })
    
    @staticmethod
    async def _award_achievement(player: Player, achievement_id: str, achievement_data: Dict[str, Any]):
        """Internal method to award an achievement"""
        try:
            player.achievements[achievement_id] = {
                "unlocked": True,
                "progress": achievement_data.get("progress", 1),
                "max_progress": achievement_data.get("max_progress", 1),
                "unlocked_at": "real_time",
                "name": achievement_data.get("name", achievement_id),
                "description": achievement_data.get("description", "Achievement unlocked")
            }
            
            # Save player data
            await player.save()
            
            logging.info(f"Achievement '{achievement_id}' awarded to player {player.id}")
            
        except Exception as e:
            logging.error(f"Error awarding achievement '{achievement_id}' to player {player.id}: {e}")
