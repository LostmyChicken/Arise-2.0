from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import random
from services.database_service import db_service
from services.auth_service import get_current_user

player_router = APIRouter()

class PlayerStats(BaseModel):
    player_id: str
    username: str
    level: int
    xp: int
    xp_needed: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    attack: int
    defense: int
    agility: int
    intelligence: int
    gold: int
    rank: str
    guild_id: Optional[str] = None
    title: Optional[str] = None

@player_router.get("/stats")
async def get_player_stats():
    """Get player statistics"""
    # Default player stats for demo
    return {
        "player_id": "demo_player",
        "username": "Shadow Monarch",
        "level": 25,
        "xp": 15750,
        "xp_needed": 20000,
        "hp": 2500,
        "max_hp": 2500,
        "mp": 1200,
        "max_mp": 1200,
        "attack": 850,
        "defense": 650,
        "agility": 720,
        "intelligence": 580,
        "gold": 125000,
        "rank": "S-Rank",
        "guild_id": "shadow_guild",
        "title": "The Shadow Monarch",
        "stats": {
            "battles_won": 1247,
            "battles_lost": 23,
            "dungeons_cleared": 89,
            "monsters_defeated": 3456,
            "rare_items_found": 67,
            "legendary_items_found": 12
        }
    }

@player_router.get("/profile")
async def get_player_profile():
    """Get complete player profile"""
    return {
        "player_id": "demo_player",
        "username": "Shadow Monarch",
        "level": 25,
        "rank": "S-Rank",
        "guild": "Shadow Legion",
        "title": "The Shadow Monarch",
        "avatar": "/images/sung_jinwoo.png",
        "achievements": [
            {"id": "first_kill", "name": "First Blood", "description": "Defeat your first monster"},
            {"id": "level_10", "name": "Rising Hunter", "description": "Reach level 10"},
            {"id": "s_rank", "name": "Elite Hunter", "description": "Achieve S-Rank status"}
        ],
        "recent_activity": [
            {"type": "battle", "description": "Defeated Iron Knight", "timestamp": "2025-08-31T10:30:00Z"},
            {"type": "level_up", "description": "Reached level 25", "timestamp": "2025-08-31T09:15:00Z"},
            {"type": "gacha", "description": "Summoned Legendary Hunter", "timestamp": "2025-08-31T08:45:00Z"}
        ]
    }

@player_router.post("/level-up")
async def level_up_player():
    """Level up the player"""
    return {
        "success": True,
        "new_level": 26,
        "stats_gained": {
            "hp": 100,
            "mp": 50,
            "attack": 25,
            "defense": 20
        },
        "message": "Congratulations! You've reached level 26!"
    }
