"""
Title System for Solo Leveling Bot
Manages player titles from story campaign and other achievements
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from structure.player import Player
# StoryCampaign import removed to avoid circular dependencies

class TitleCategory(Enum):
    """Categories for organizing titles"""
    STORY = "story"
    ACHIEVEMENT = "achievement"
    RANK = "rank"
    SPECIAL = "special"
    EVENT = "event"
    GUILD = "guild"

class TitleRarity(Enum):
    """Title rarity levels"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"

@dataclass
class Title:
    """Individual title data"""
    id: str
    name: str
    description: str
    category: TitleCategory
    rarity: TitleRarity
    unlock_condition: str
    emoji: str = "🏆"
    color: int = 0x00ff00  # Default green color
    hidden: bool = False  # Whether title is hidden until unlocked
    
    def get_display_name(self) -> str:
        """Get formatted display name with emoji"""
        return f"{self.emoji} {self.name}"
    
    def get_rarity_color(self) -> int:
        """Get color based on rarity"""
        rarity_colors = {
            TitleRarity.COMMON: 0x808080,      # Gray
            TitleRarity.UNCOMMON: 0x00ff00,    # Green
            TitleRarity.RARE: 0x0080ff,        # Blue
            TitleRarity.EPIC: 0x8000ff,        # Purple
            TitleRarity.LEGENDARY: 0xff8000,   # Orange
            TitleRarity.MYTHIC: 0xff0080       # Pink
        }
        return rarity_colors.get(self.rarity, 0x00ff00)

class TitleManager:
    """Manages all player titles"""
    
    # All available titles in the system
    TITLES = {
        # STORY CAMPAIGN TITLES (from story_campaign.py)
        "novice_hunter": Title(
            id="novice_hunter",
            name="Novice Hunter",
            description="Completed your first dungeon as an E-rank hunter.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.COMMON,
            unlock_condition="Complete prologue_001",
            emoji="🔰",
            color=0x808080
        ),
        
        "licensed_hunter": Title(
            id="licensed_hunter",
            name="Licensed Hunter",
            description="Officially registered with the Hunter's Association.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.COMMON,
            unlock_condition="Complete prologue_002",
            emoji="📜",
            color=0x808080
        ),
        
        "survivor": Title(
            id="survivor",
            name="Survivor",
            description="Survived the deadly double dungeon incident.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.UNCOMMON,
            unlock_condition="Complete double_dungeon_001",
            emoji="💀",
            color=0x00ff00
        ),
        
        "system_user": Title(
            id="system_user",
            name="System User",
            description="Awakened to the mysterious System's power.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.RARE,
            unlock_condition="Complete double_dungeon_002",
            emoji="⚡",
            color=0x0080ff
        ),
        
        "reawakened_hunter": Title(
            id="reawakened_hunter",
            name="Reawakened Hunter",
            description="Successfully reawakened and proved your new strength.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.RARE,
            unlock_condition="Complete reawakening_001",
            emoji="🌟",
            color=0x0080ff
        ),
        
        "temple_conqueror": Title(
            id="temple_conqueror",
            name="Temple Conqueror",
            description="Conquered the mysterious Cartenon Temple.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.EPIC,
            unlock_condition="Complete cartenon_001",
            emoji="🏛️",
            color=0x8000ff
        ),
        
        "temple_master": Title(
            id="temple_master",
            name="Temple Master",
            description="Mastered the ancient secrets of the Cartenon Temple.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.EPIC,
            unlock_condition="Complete cartenon_002",
            emoji="🔮",
            color=0x8000ff
        ),
        
        "castle_challenger": Title(
            id="castle_challenger",
            name="Castle Challenger",
            description="Dared to challenge the Demon Castle's defenses.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.EPIC,
            unlock_condition="Complete demon_castle_001",
            emoji="🏰",
            color=0x8000ff
        ),
        
        "demon_slayer": Title(
            id="demon_slayer",
            name="Demon Slayer",
            description="Defeated the Demon King in his own throne room.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.LEGENDARY,
            unlock_condition="Complete demon_castle_002",
            emoji="⚔️",
            color=0xff8000
        ),
        
        "red_gate_hero": Title(
            id="red_gate_hero",
            name="Red Gate Hero",
            description="Saved trapped hunters from a deadly Red Gate.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.LEGENDARY,
            unlock_condition="Complete red_gate_001",
            emoji="🚪",
            color=0xff8000
        ),
        
        "shadow_monarch": Title(
            id="shadow_monarch",
            name="Shadow Monarch",
            description="Awakened as the true Shadow Monarch, ruler of the dead.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete shadow_monarch_001",
            emoji="👑",
            color=0xff0080
        ),
        
        "island_liberator": Title(
            id="island_liberator",
            name="Island Liberator",
            description="Liberated Jeju Island from the giant ant invasion.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.LEGENDARY,
            unlock_condition="Complete jeju_island_001",
            emoji="🏝️",
            color=0xff8000
        ),
        
        "ant_king_master": Title(
            id="ant_king_master",
            name="Ant King Master",
            description="Defeated and extracted the mighty Ant King Beru.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete jeju_island_002",
            emoji="🐜",
            color=0xff0080
        ),
        
        "monarch_slayer": Title(
            id="monarch_slayer",
            name="Monarch Slayer",
            description="Defeated a fellow Monarch in single combat.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete monarchs_war_001",
            emoji="⚡",
            color=0xff0080
        ),
        
        "frost_conqueror": Title(
            id="frost_conqueror",
            name="Frost Conqueror",
            description="Conquered the Ice Monarch in the frozen wastelands.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete monarchs_war_002",
            emoji="❄️",
            color=0xff0080
        ),
        
        "dragon_slayer": Title(
            id="dragon_slayer",
            name="Dragon Slayer",
            description="Slayed the mighty Dragon Emperor, strongest of all Monarchs.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete monarchs_war_003",
            emoji="🐉",
            color=0xff0080
        ),
        
        "truth_seeker": Title(
            id="truth_seeker",
            name="Truth Seeker",
            description="Discovered the truth behind the System and its creator.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete final_battle_001",
            emoji="🔍",
            color=0xff0080
        ),
        
        "world_savior": Title(
            id="world_savior",
            name="World Savior",
            description="Made the ultimate sacrifice to save both worlds.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete final_battle_002",
            emoji="🌍",
            color=0xff0080
        ),
        
        "eternal_shadow_monarch": Title(
            id="eternal_shadow_monarch",
            name="Eternal Shadow Monarch",
            description="Achieved the ultimate power and eternal vigilance over both worlds.",
            category=TitleCategory.STORY,
            rarity=TitleRarity.MYTHIC,
            unlock_condition="Complete final_battle_003",
            emoji="♾️",
            color=0xff0080
        ),
        
        # ACHIEVEMENT TITLES (placeholders for future implementation)
        "first_steps": Title(
            id="first_steps",
            name="First Steps",
            description="Reached level 10 for the first time.",
            category=TitleCategory.ACHIEVEMENT,
            rarity=TitleRarity.COMMON,
            unlock_condition="Reach level 10",
            emoji="👶",
            color=0x808080
        ),
        
        "veteran_hunter": Title(
            id="veteran_hunter",
            name="Veteran Hunter",
            description="Reached level 50, proving your experience.",
            category=TitleCategory.ACHIEVEMENT,
            rarity=TitleRarity.UNCOMMON,
            unlock_condition="Reach level 50",
            emoji="🎖️",
            color=0x00ff00
        ),
        
        "elite_hunter": Title(
            id="elite_hunter",
            name="Elite Hunter",
            description="Reached level 100, joining the elite ranks.",
            category=TitleCategory.ACHIEVEMENT,
            rarity=TitleRarity.RARE,
            unlock_condition="Reach level 100",
            emoji="💎",
            color=0x0080ff
        ),
        
        # RANK TITLES (placeholders for future implementation)
        "e_rank_hunter": Title(
            id="e_rank_hunter",
            name="E-Rank Hunter",
            description="The starting rank for all hunters.",
            category=TitleCategory.RANK,
            rarity=TitleRarity.COMMON,
            unlock_condition="Default starting title",
            emoji="🔰",
            color=0x808080
        ),
        
        "s_rank_hunter": Title(
            id="s_rank_hunter",
            name="S-Rank Hunter",
            description="Achieved the prestigious S-Rank status.",
            category=TitleCategory.RANK,
            rarity=TitleRarity.LEGENDARY,
            unlock_condition="Reach S-Rank",
            emoji="⭐",
            color=0xff8000
        ),
        
        # SPECIAL TITLES (placeholders for future implementation)
        "beta_tester": Title(
            id="beta_tester",
            name="Beta Tester",
            description="Participated in the bot's beta testing phase.",
            category=TitleCategory.SPECIAL,
            rarity=TitleRarity.RARE,
            unlock_condition="Special event participation",
            emoji="🧪",
            color=0x0080ff,
            hidden=True
        )
    }

    @classmethod
    async def get_player_titles(cls, player_id: str) -> Dict[str, bool]:
        """Get all titles for a player"""
        try:
            player = await Player.get(player_id)
            if not player:
                return {}

            # Get titles from player data
            if hasattr(player, 'titles') and player.titles:
                if isinstance(player.titles, str):
                    try:
                        return json.loads(player.titles)
                    except json.JSONDecodeError:
                        return {}
                elif isinstance(player.titles, dict):
                    return player.titles
            return {}
        except Exception as e:
            logging.error(f"Error getting titles for player {player_id}: {e}")
            return {}

    @classmethod
    async def get_player_active_title(cls, player_id: str) -> Optional[str]:
        """Get player's currently active title"""
        try:
            player = await Player.get(player_id)
            if not player:
                return None

            return getattr(player, 'active_title', None)
        except Exception as e:
            logging.error(f"Error getting active title for player {player_id}: {e}")
            return None

    @classmethod
    async def set_player_active_title(cls, player_id: str, title_id: str) -> bool:
        """Set player's active title"""
        try:
            player = await Player.get(player_id)
            if not player:
                return False

            # Check if player has this title
            player_titles = await cls.get_player_titles(player_id)
            if title_id not in player_titles or not player_titles[title_id]:
                return False

            # Check if title exists
            if title_id not in cls.TITLES:
                return False

            # Set active title
            player.active_title = title_id
            await player.save()
            return True
        except Exception as e:
            logging.error(f"Error setting active title for player {player_id}: {e}")
            return False

    @classmethod
    async def unlock_title(cls, player_id: str, title_id: str) -> bool:
        """Unlock a title for a player"""
        try:
            player = await Player.get(player_id)
            if not player:
                return False

            # Check if title exists
            if title_id not in cls.TITLES:
                return False

            # Get current titles
            player_titles = await cls.get_player_titles(player_id)

            # Unlock the title
            player_titles[title_id] = True

            # Ensure player has titles attribute
            if not hasattr(player, 'titles'):
                player.titles = {}

            # Update player data
            player.titles = player_titles
            await player.save()
            return True
        except Exception as e:
            logging.error(f"Error unlocking title {title_id} for player {player_id}: {e}")
            return False

    @classmethod
    async def check_and_unlock_story_titles(cls, player_id: str) -> List[str]:
        """Check and unlock story titles based on completed missions"""
        try:
            unlocked_titles = []

            # Get player's story progress directly from player data
            player = await Player.get(player_id)
            if not player:
                return []

            story_progress = getattr(player, 'story_progress', {})

            # Check each story title
            for title_id, title in cls.TITLES.items():
                if title.category != TitleCategory.STORY:
                    continue

                # Extract mission ID from unlock condition
                if "Complete " in title.unlock_condition:
                    mission_id = title.unlock_condition.replace("Complete ", "")

                    # Check if mission is completed
                    if mission_id in story_progress and story_progress[mission_id].get("completed", False):
                        # Check if player already has this title
                        player_titles = await cls.get_player_titles(player_id)
                        if title_id not in player_titles or not player_titles[title_id]:
                            # Unlock the title
                            if await cls.unlock_title(player_id, title_id):
                                unlocked_titles.append(title_id)

            return unlocked_titles
        except Exception as e:
            logging.error(f"Error checking story titles for player {player_id}: {e}")
            return []

    @classmethod
    async def get_unlocked_titles(cls, player_id: str) -> List[Title]:
        """Get all unlocked titles for a player"""
        try:
            player_titles = await cls.get_player_titles(player_id)
            unlocked = []

            for title_id, is_unlocked in player_titles.items():
                if is_unlocked and title_id in cls.TITLES:
                    unlocked.append(cls.TITLES[title_id])

            return unlocked
        except Exception as e:
            logging.error(f"Error getting unlocked titles for player {player_id}: {e}")
            return []

    @classmethod
    async def get_titles_by_category(cls, player_id: str, category: TitleCategory) -> List[Tuple[Title, bool]]:
        """Get all titles in a category with unlock status"""
        try:
            player_titles = await cls.get_player_titles(player_id)
            category_titles = []

            for title_id, title in cls.TITLES.items():
                if title.category == category:
                    is_unlocked = player_titles.get(title_id, False)
                    # Only show non-hidden titles or unlocked hidden titles
                    if not title.hidden or is_unlocked:
                        category_titles.append((title, is_unlocked))

            # Sort by rarity and name
            category_titles.sort(key=lambda x: (x[0].rarity.value, x[0].name))
            return category_titles
        except Exception as e:
            logging.error(f"Error getting titles by category for player {player_id}: {e}")
            return []

    @classmethod
    def get_title_by_id(cls, title_id: str) -> Optional[Title]:
        """Get a title by its ID"""
        return cls.TITLES.get(title_id)

    @classmethod
    async def get_title_display_for_profile(cls, player_id: str) -> str:
        """Get formatted title display for profile"""
        try:
            active_title_id = await cls.get_player_active_title(player_id)
            if not active_title_id:
                return ""

            title = cls.get_title_by_id(active_title_id)
            if not title:
                return ""

            return title.get_display_name()
        except Exception as e:
            logging.error(f"Error getting title display for player {player_id}: {e}")
            return ""
