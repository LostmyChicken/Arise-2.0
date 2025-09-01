from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/skills", tags=["skills"])

# Skill models
class Skill(BaseModel):
    id: str
    name: str
    description: str
    type: str  # Basic, QTE, Ultimate
    element: str  # Fire, Water, Earth, Wind, Light, Dark
    cost: int  # Skill points required
    prerequisites: List[str] = []
    effects: Dict[str, Any] = {}
    cooldown: int = 0
    charges: int = 1

class SkillLearnRequest(BaseModel):
    skill_id: str

class SkillUpgradeRequest(BaseModel):
    skill_id: str
    upgrade_level: int

# Load skills data
def load_skills_data():
    """Load skills from JSON file or create default skills"""
    skills_file = os.path.join("data", "skills.json")
    if os.path.exists(skills_file):
        with open(skills_file, 'r') as f:
            return json.load(f)
    
    # Default skills based on Discord bot
    return {
        "basic_attack": {
            "id": "basic_attack",
            "name": "Basic Attack",
            "description": "A simple physical attack",
            "type": "Basic",
            "element": "Physical",
            "cost": 0,
            "prerequisites": [],
            "effects": {"damage_multiplier": 1.0, "accuracy": 90},
            "cooldown": 0,
            "charges": 999
        },
        "shadow_extraction": {
            "id": "shadow_extraction",
            "name": "Shadow Extraction",
            "description": "Extract shadows from defeated enemies",
            "type": "Ultimate",
            "element": "Dark",
            "cost": 10,
            "prerequisites": ["basic_attack"],
            "effects": {"shadow_chance": 25, "power_boost": 1.5},
            "cooldown": 5,
            "charges": 3
        },
        "precision_strike": {
            "id": "precision_strike",
            "name": "Precision Strike",
            "description": "A highly accurate attack with increased critical chance",
            "type": "QTE",
            "element": "Physical",
            "cost": 5,
            "prerequisites": ["basic_attack"],
            "effects": {"accuracy": 95, "crit_chance": 30, "damage_multiplier": 1.3},
            "cooldown": 3,
            "charges": 5
        },
        "flame_burst": {
            "id": "flame_burst",
            "name": "Flame Burst",
            "description": "Unleash a burst of fire damage",
            "type": "Basic",
            "element": "Fire",
            "cost": 3,
            "prerequisites": [],
            "effects": {"damage_multiplier": 1.2, "burn_chance": 20},
            "cooldown": 2,
            "charges": 8
        },
        "ice_shield": {
            "id": "ice_shield",
            "name": "Ice Shield",
            "description": "Create a protective ice barrier",
            "type": "Basic",
            "element": "Water",
            "cost": 4,
            "prerequisites": [],
            "effects": {"defense_boost": 1.5, "duration": 3},
            "cooldown": 4,
            "charges": 6
        },
        "wind_dash": {
            "id": "wind_dash",
            "name": "Wind Dash",
            "description": "Quick movement with wind magic",
            "type": "QTE",
            "element": "Wind",
            "cost": 2,
            "prerequisites": [],
            "effects": {"evasion_boost": 2.0, "speed_boost": 1.8},
            "cooldown": 2,
            "charges": 10
        },
        "earth_slam": {
            "id": "earth_slam",
            "name": "Earth Slam",
            "description": "Powerful ground-based attack",
            "type": "Ultimate",
            "element": "Earth",
            "cost": 8,
            "prerequisites": ["basic_attack"],
            "effects": {"damage_multiplier": 2.0, "stun_chance": 40},
            "cooldown": 6,
            "charges": 4
        },
        "light_heal": {
            "id": "light_heal",
            "name": "Light Heal",
            "description": "Restore health with light magic",
            "type": "Basic",
            "element": "Light",
            "cost": 3,
            "prerequisites": [],
            "effects": {"heal_amount": 200, "heal_percentage": 15},
            "cooldown": 3,
            "charges": 7
        },
        "shadow_step": {
            "id": "shadow_step",
            "name": "Shadow Step",
            "description": "Move through shadows to avoid attacks",
            "type": "QTE",
            "element": "Dark",
            "cost": 4,
            "prerequisites": [],
            "effects": {"evasion_boost": 3.0, "counter_chance": 25},
            "cooldown": 4,
            "charges": 5
        },
        "monarch_authority": {
            "id": "monarch_authority",
            "name": "Monarch's Authority",
            "description": "Ultimate shadow monarch power",
            "type": "Ultimate",
            "element": "Dark",
            "cost": 20,
            "prerequisites": ["shadow_extraction", "shadow_step"],
            "effects": {"damage_multiplier": 3.0, "all_stats_boost": 2.0, "duration": 5},
            "cooldown": 10,
            "charges": 1
        }
    }

@router.get("/")
async def get_all_skills():
    """Get all available skills"""
    skills = load_skills_data()
    return {"skills": list(skills.values())}

@router.get("/player")
async def get_player_skills(current_user: dict = Depends(get_current_user)):
    """Get player's learned skills and skill points"""
    db = await get_db_connection()
    # Get player's learned skills
    cursor = await db.execute(
    "SELECT learned_skills, skill_points FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()

    if not result:
    raise HTTPException(status_code=404, detail="Player not found")

    learned_skills = json.loads(result[0] or '{}')
    skill_points = result[1] or 0

    # Get all available skills
    all_skills = load_skills_data()

    return {
    "learned_skills": learned_skills,
    "skill_points": skill_points,
    "available_skills": list(all_skills.values())
    }

@router.post("/learn")
async def learn_skill(request: SkillLearnRequest, current_user: dict = Depends(get_current_user)):
    """Learn a new skill"""
    skills_data = load_skills_data()
    
    if request.skill_id not in skills_data:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    skill = skills_data[request.skill_id]
    
    db = await get_db_connection()
    # Get player data
    cursor = await db.execute(
    "SELECT learned_skills, skill_points FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    learned_skills = json.loads(result[0] or '{}')
    skill_points = result[1] or 0
        
    # Check if already learned
    if request.skill_id in learned_skills:
    raise HTTPException(status_code=400, detail="Skill already learned")
        
    # Check skill points
    if skill_points < skill["cost"]:
    raise HTTPException(status_code=400, detail="Not enough skill points")
        
    # Check prerequisites
    for prereq in skill["prerequisites"]:
    if prereq not in learned_skills:
    raise HTTPException(status_code=400, detail=f"Missing prerequisite: {prereq}")
        
    # Learn the skill
    learned_skills[request.skill_id] = {
    "level": 1,
    "charges": skill["charges"],
    "max_charges": skill["charges"],
    "cooldown_end": 0
    }
        
    new_skill_points = skill_points - skill["cost"]
        
    # Update database
    await db.execute(
    "UPDATE players SET learned_skills = ?, skill_points = ? WHERE id = ?",
    (json.dumps(learned_skills), new_skill_points, current_user["player_id"])
    )
    await db.commit()
        
    return {
    "message": f"Successfully learned {skill['name']}",
    "learned_skills": learned_skills,
    "skill_points": new_skill_points
    }

@router.post("/use")
async def use_skill(skill_id: str, current_user: dict = Depends(get_current_user)):
    """Use a skill in battle"""
    skills_data = load_skills_data()
    
    if skill_id not in skills_data:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    skill = skills_data[skill_id]
    current_time = int(time.time())
    
    db = await get_db_connection()
    # Get player's learned skills
    cursor = await db.execute(
    "SELECT learned_skills FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    learned_skills = json.loads(result[0] or '{}')
        
    if skill_id not in learned_skills:
    raise HTTPException(status_code=400, detail="Skill not learned")
        
    player_skill = learned_skills[skill_id]
        
    # Check cooldown
    if current_time < player_skill.get("cooldown_end", 0):
    remaining = player_skill["cooldown_end"] - current_time
    raise HTTPException(status_code=400, detail=f"Skill on cooldown for {remaining} seconds")
        
    # Check charges
    if player_skill.get("charges", 0) <= 0:
    raise HTTPException(status_code=400, detail="No charges remaining")
        
    # Use the skill
    player_skill["charges"] -= 1
    player_skill["cooldown_end"] = current_time + skill["cooldown"]
        
    # Update database
    await db.execute(
    "UPDATE players SET learned_skills = ? WHERE id = ?",
    (json.dumps(learned_skills), current_user["player_id"])
    )
    await db.commit()
        
    return {
    "message": f"Used {skill['name']}",
    "skill_effects": skill["effects"],
    "remaining_charges": player_skill["charges"],
    "cooldown_end": player_skill["cooldown_end"]
    }

@router.post("/reset-cooldowns")
async def reset_skill_cooldowns(current_user: dict = Depends(get_current_user)):
    """Reset all skill cooldowns (admin or premium feature)"""
    db = await get_db_connection()
    cursor = await db.execute(
    "SELECT learned_skills FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    learned_skills = json.loads(result[0] or '{}')
        
    # Reset all cooldowns
    for skill_id in learned_skills:
    learned_skills[skill_id]["cooldown_end"] = 0
        
    await db.execute(
    "UPDATE players SET learned_skills = ? WHERE id = ?",
    (json.dumps(learned_skills), current_user["player_id"])
    )
    await db.commit()
        
    return {"message": "All skill cooldowns reset"}
