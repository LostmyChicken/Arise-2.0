from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

skills_router = APIRouter()

@skills_router.get("/list")
async def get_skills_list():
    """Get list of available skills"""
    return {
        "skills": [
            {
                "id": "shadow_extraction",
                "name": "Shadow Extraction",
                "type": "unique",
                "level": 5,
                "max_level": 10,
                "mp_cost": 100,
                "cooldown": 30,
                "description": "Extract shadows from defeated enemies",
                "effects": {"summon_shadow": True, "duration": 300},
                "image": "/images/shadow_extraction.png"
            },
            {
                "id": "shadow_exchange",
                "name": "Shadow Exchange",
                "type": "unique", 
                "level": 3,
                "max_level": 5,
                "mp_cost": 50,
                "cooldown": 10,
                "description": "Instantly swap positions with a shadow",
                "effects": {"teleport": True, "range": 50},
                "image": "/images/shadow_exchange.png"
            },
            {
                "id": "rulers_authority",
                "name": "Ruler's Authority",
                "type": "unique",
                "level": 7,
                "max_level": 10,
                "mp_cost": 200,
                "cooldown": 60,
                "description": "Control objects with telekinetic force",
                "effects": {"telekinesis": True, "damage_multiplier": 2.5},
                "image": "/images/rulers_authority.png"
            },
            {
                "id": "stealth",
                "name": "Stealth",
                "type": "common",
                "level": 8,
                "max_level": 10,
                "mp_cost": 30,
                "cooldown": 5,
                "description": "Become invisible for a short time",
                "effects": {"invisible": True, "duration": 15},
                "image": "/images/stealth.png"
            }
        ]
    }

@skills_router.post("/upgrade")
async def upgrade_skill(skill_data: dict):
    """Upgrade a skill"""
    skill_id = skill_data.get("skill_id")
    return {
        "success": True,
        "skill_id": skill_id,
        "new_level": 6,
        "cost": 5000,
        "message": f"Successfully upgraded {skill_id} to level 6!"
    }

@skills_router.post("/use")
async def use_skill(skill_data: dict):
    """Use a skill in battle"""
    skill_id = skill_data.get("skill_id")
    target = skill_data.get("target")
    return {
        "success": True,
        "skill_used": skill_id,
        "damage_dealt": random.randint(500, 1500),
        "mp_consumed": 100,
        "effects_applied": ["shadow_bind"],
        "message": f"Successfully used {skill_id}!"
    }
