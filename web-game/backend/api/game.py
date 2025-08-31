from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import os

router = APIRouter()

class GameData(BaseModel):
    data_type: str  # items, hunters, enemies, etc.

@router.get("/items")
async def get_all_items():
    """Get all game items"""
    try:
        # Load items from the original Discord bot data
        items_path = "../../items.json"
        if os.path.exists(items_path):
            with open(items_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
            return {"items": items}
        else:
            # Fallback sample items
            return {
                "items": {
                    "basic_sword": {
                        "name": "Basic Sword",
                        "type": "Weapon",
                        "rarity": "Common",
                        "attack": 15,
                        "description": "A simple iron sword for beginners."
                    },
                    "leather_armor": {
                        "name": "Leather Armor",
                        "type": "Armor",
                        "rarity": "Common",
                        "defense": 10,
                        "description": "Basic leather protection."
                    }
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load items: {str(e)}"
        )

@router.get("/hunters")
async def get_all_hunters():
    """Get all game hunters"""
    try:
        # Load hunters from the original Discord bot data
        hunters_path = "../../hunters.json"
        if os.path.exists(hunters_path):
            with open(hunters_path, 'r', encoding='utf-8') as f:
                hunters = json.load(f)
            return {"hunters": hunters}
        else:
            # Fallback sample hunters
            return {
                "hunters": {
                    "sung_jinwoo": {
                        "name": "Sung Jin-Woo",
                        "class": "Shadow Monarch",
                        "rarity": "Legendary",
                        "attack": 100,
                        "defense": 80,
                        "hp": 1000,
                        "skills": ["Shadow Exchange", "Ruler's Authority"],
                        "image": "https://example.com/jinwoo.png"
                    },
                    "cha_haein": {
                        "name": "Cha Hae-In",
                        "class": "S-Rank Hunter",
                        "rarity": "Epic",
                        "attack": 85,
                        "defense": 70,
                        "hp": 800,
                        "skills": ["Sword Dance", "Mana Burst"],
                        "image": "https://example.com/chahaein.png"
                    }
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load hunters: {str(e)}"
        )

@router.get("/enemies")
async def get_all_enemies():
    """Get all game enemies"""
    try:
        # Load enemies from the original Discord bot data
        enemies_path = "../../enemy.json"
        if os.path.exists(enemies_path):
            with open(enemies_path, 'r', encoding='utf-8') as f:
                enemies = json.load(f)
            return {"enemies": enemies}
        else:
            # Fallback sample enemies
            return {
                "enemies": {
                    "goblin": {
                        "name": "Goblin",
                        "level": 5,
                        "hp": 100,
                        "attack": 20,
                        "defense": 10,
                        "xp_reward": 25,
                        "gold_reward": 50
                    },
                    "orc": {
                        "name": "Orc",
                        "level": 15,
                        "hp": 300,
                        "attack": 45,
                        "defense": 25,
                        "xp_reward": 75,
                        "gold_reward": 150
                    }
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load enemies: {str(e)}"
        )

@router.get("/story-missions")
async def get_story_missions():
    """Get all story missions"""
    try:
        # Load story missions from the original Discord bot data
        story_path = "../../story_missions.json"
        if os.path.exists(story_path):
            with open(story_path, 'r', encoding='utf-8') as f:
                story = json.load(f)
            return {"story_missions": story}
        else:
            # Fallback sample story
            return {
                "story_missions": {
                    "arc_1": {
                        "name": "The Weakest Hunter",
                        "missions": [
                            {
                                "id": 1,
                                "name": "First Dungeon",
                                "description": "Enter your first E-rank dungeon",
                                "requirements": {"level": 1},
                                "rewards": {"xp": 100, "gold": 200}
                            }
                        ]
                    }
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load story missions: {str(e)}"
        )

@router.get("/skills")
async def get_all_skills():
    """Get all available skills"""
    try:
        # This would load from the original bot's skill system
        return {
            "skills": {
                "basic_attack": {
                    "name": "Basic Attack",
                    "type": "Basic",
                    "cost": 0,
                    "damage_multiplier": 1.0,
                    "description": "A standard attack"
                },
                "power_strike": {
                    "name": "Power Strike",
                    "type": "QTE",
                    "cost": 10,
                    "damage_multiplier": 1.5,
                    "description": "A powerful strike that deals extra damage"
                },
                "shadow_exchange": {
                    "name": "Shadow Exchange",
                    "type": "Ultimate",
                    "cost": 50,
                    "damage_multiplier": 3.0,
                    "description": "Teleport behind enemy and strike"
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load skills: {str(e)}"
        )

@router.get("/emojis")
async def get_game_emojis():
    """Get game emojis/icons"""
    try:
        # Load emojis from the original Discord bot data
        emojis_path = "../../emojis.json"
        if os.path.exists(emojis_path):
            with open(emojis_path, 'r', encoding='utf-8') as f:
                emojis = json.load(f)
            return {"emojis": emojis}
        else:
            # Fallback sample emojis (using Unicode)
            return {
                "emojis": {
                    "gold": "🪙",
                    "diamond": "💎",
                    "xp": "⭐",
                    "attack": "⚔️",
                    "defense": "🛡️",
                    "hp": "❤️",
                    "mp": "💙",
                    "ticket": "🎫"
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load emojis: {str(e)}"
        )

@router.get("/config")
async def get_game_config():
    """Get game configuration"""
    try:
        return {
            "config": {
                "max_level": 100,
                "xp_per_level": 100,
                "stat_points_per_level": 10,
                "skill_points_per_level": 5,
                "gacha_rates": {
                    "common": 60,
                    "rare": 25,
                    "epic": 12,
                    "legendary": 3
                },
                "daily_rewards": {
                    "gold": 1000,
                    "tickets": 1,
                    "xp": 500
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load config: {str(e)}"
        )

# Export router
game_router = router