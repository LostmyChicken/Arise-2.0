from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import random
import time
import sqlite3
from pathlib import Path

from services.player_service import player_service
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/training", tags=["training"])

# Load real skills data from Discord bot
def load_skills_data():
    """Load skills data from SQLite database"""
    try:
        # Try multiple possible paths for the skills database
        possible_paths = [
            Path("web-game/backend/data/skills.db"),
            Path("backend/data/skills.db"),
            Path("data/skills.db"),
            Path("../data/skills.db")
        ]
        
        for db_path in possible_paths:
            if db_path.exists():
                print(f"Loading skills data from: {db_path}")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM skills")
                rows = cursor.fetchall()
                
                skills = {}
                for row in rows:
                    skill = {
                        "id": row[0],
                        "type": row[1],
                        "name": row[2],
                        "effects": row[3],
                        "damage": row[4],
                        "mp_cost": row[5],
                        "element": row[6],
                        "character_id": row[7],
                        "level": row[8] if len(row) > 8 else 1
                    }
                    skills[row[0]] = skill
                
                conn.close()
                print(f"Loaded {len(skills)} skills from database")
                return skills
                
    except Exception as e:
        print(f"Error loading skills data: {e}")
    
    # Fallback skills data
    return {
        "basic_attack": {
            "id": "basic_attack",
            "type": "Basic",
            "name": "Basic Attack",
            "effects": "DAMAGE",
            "damage": 100,
            "mp_cost": 0,
            "element": "PHYSICAL",
            "character_id": "default",
            "level": 1
        }
    }

SKILLS_DATA = load_skills_data()

# Training models
class TrainingRequest(BaseModel):
    training_type: str  # "stats", "skills", "combat"
    target: Optional[str] = None  # specific stat or skill to train
    duration: int = 1  # training duration in hours

class SkillUpgradeRequest(BaseModel):
    skill_id: str
    upgrade_type: str = "level"  # "level", "damage", "efficiency"

@router.get("/options")
async def get_training_options(current_user: dict = Depends(get_current_user)):
    """Get available training options"""
    return {
        "stat_training": {
            "attack": {
                "name": "Attack Training",
                "description": "Increase your attack power",
                "cost": {"gold": 1000, "time_hours": 1},
                "stat_gain": {"attack": 5}
            },
            "defense": {
                "name": "Defense Training", 
                "description": "Increase your defense",
                "cost": {"gold": 1000, "time_hours": 1},
                "stat_gain": {"defense": 5}
            },
            "hp": {
                "name": "Endurance Training",
                "description": "Increase your HP",
                "cost": {"gold": 1200, "time_hours": 1},
                "stat_gain": {"hp": 50}
            },
            "mp": {
                "name": "Mana Training",
                "description": "Increase your MP",
                "cost": {"gold": 1200, "time_hours": 1},
                "stat_gain": {"mp": 30}
            },
            "precision": {
                "name": "Precision Training",
                "description": "Increase your precision",
                "cost": {"gold": 1500, "time_hours": 2},
                "stat_gain": {"precision": 3}
            }
        },
        "skill_training": {
            skill_id: {
                "name": skill["name"],
                "description": f"Train {skill['name']} skill",
                "type": skill["type"],
                "element": skill["element"],
                "current_level": skill["level"],
                "upgrade_cost": {
                    "gold": skill["level"] * 2000,
                    "crystals": skill["level"] * 10,
                    "time_hours": skill["level"]
                }
            }
            for skill_id, skill in list(SKILLS_DATA.items())[:10]  # Show first 10 skills
        },
        "combat_training": {
            "sparring": {
                "name": "Sparring Practice",
                "description": "Practice combat against training dummies",
                "cost": {"gold": 500, "time_hours": 1},
                "rewards": {"experience": 100, "combat_skill": 2}
            },
            "dungeon_simulation": {
                "name": "Dungeon Simulation",
                "description": "Practice in simulated dungeon environments",
                "cost": {"gold": 2000, "time_hours": 3},
                "rewards": {"experience": 500, "all_stats": 2}
            }
        }
    }

@router.post("/start")
async def start_training(
    request: TrainingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a training session"""
    try:
        player_id = current_user["user_id"]
        
        # Get player data
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Calculate training costs and rewards
        training_cost = calculate_training_cost(request.training_type, request.target, request.duration)
        
        # Check if player has enough resources
        if player.get("gold", 0) < training_cost.get("gold", 0):
            raise HTTPException(status_code=400, detail="Not enough gold")
        
        if player.get("crystals", 0) < training_cost.get("crystals", 0):
            raise HTTPException(status_code=400, detail="Not enough crystals")
        
        # Deduct costs
        updates = {
            "gold": player["gold"] - training_cost.get("gold", 0),
            "crystals": player["crystals"] - training_cost.get("crystals", 0)
        }
        
        # Calculate training completion time
        completion_time = int(time.time()) + (request.duration * 3600)  # Convert hours to seconds
        
        # Apply training results immediately for demo (in real game, this would be delayed)
        training_results = calculate_training_results(request.training_type, request.target, request.duration)
        
        # Update player stats
        for stat, gain in training_results.get("stat_gains", {}).items():
            current_value = player.get(stat, 0)
            updates[stat] = current_value + gain
        
        # Update player
        await player_service.update_player(player_id, updates)
        
        return {
            "success": True,
            "message": f"Training started: {request.training_type}",
            "training_id": f"training_{int(time.time())}",
            "completion_time": completion_time,
            "cost": training_cost,
            "expected_results": training_results,
            "status": "completed"  # Instant completion for demo
        }
        
    except Exception as e:
        print(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def calculate_training_cost(training_type: str, target: str, duration: int) -> Dict[str, int]:
    """Calculate the cost of training"""
    base_costs = {
        "stats": {"gold": 1000, "crystals": 0},
        "skills": {"gold": 2000, "crystals": 10},
        "combat": {"gold": 1500, "crystals": 5}
    }
    
    cost = base_costs.get(training_type, {"gold": 1000, "crystals": 0}).copy()
    
    # Scale cost by duration
    for resource in cost:
        cost[resource] *= duration
    
    # Special costs for specific targets
    if target == "precision":
        cost["gold"] *= 2
        cost["crystals"] += 5
    
    return cost

def calculate_training_results(training_type: str, target: str, duration: int) -> Dict[str, Any]:
    """Calculate training results"""
    results = {"stat_gains": {}, "skill_improvements": {}, "experience": 0}
    
    if training_type == "stats" and target:
        base_gains = {
            "attack": 5,
            "defense": 5,
            "hp": 50,
            "mp": 30,
            "precision": 3
        }
        
        if target in base_gains:
            # Add some randomness to training results
            base_gain = base_gains[target]
            actual_gain = base_gain + random.randint(-2, 5)  # ±2 to +5 variation
            results["stat_gains"][target] = actual_gain * duration
    
    elif training_type == "skills" and target and target in SKILLS_DATA:
        # Skill training results
        skill = SKILLS_DATA[target]
        results["skill_improvements"][target] = {
            "level_increase": 1,
            "damage_increase": skill["damage"] // 10,
            "efficiency_increase": 5
        }
    
    elif training_type == "combat":
        # Combat training gives balanced stat increases
        results["stat_gains"] = {
            "attack": random.randint(2, 5) * duration,
            "defense": random.randint(2, 5) * duration,
            "hp": random.randint(20, 40) * duration,
            "precision": random.randint(1, 3) * duration
        }
        results["experience"] = 100 * duration
    
    return results

@router.get("/skills")
async def get_available_skills(current_user: dict = Depends(get_current_user)):
    """Get all available skills for training"""
    return {
        "skills": [
            {
                "id": skill_id,
                "name": skill["name"],
                "type": skill["type"],
                "element": skill["element"],
                "damage": skill["damage"],
                "mp_cost": skill["mp_cost"],
                "level": skill["level"],
                "effects": skill["effects"],
                "character_id": skill["character_id"]
            }
            for skill_id, skill in SKILLS_DATA.items()
        ]
    }

@router.post("/upgrade-skill")
async def upgrade_skill(
    request: SkillUpgradeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upgrade a specific skill"""
    try:
        player_id = current_user["user_id"]
        
        if request.skill_id not in SKILLS_DATA:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        skill = SKILLS_DATA[request.skill_id]
        
        # Calculate upgrade cost
        upgrade_cost = {
            "gold": skill["level"] * 2000,
            "crystals": skill["level"] * 10
        }
        
        # Get player data
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Check resources
        if player.get("gold", 0) < upgrade_cost["gold"]:
            raise HTTPException(status_code=400, detail="Not enough gold")
        
        if player.get("crystals", 0) < upgrade_cost["crystals"]:
            raise HTTPException(status_code=400, detail="Not enough crystals")
        
        # Deduct costs and apply upgrade
        updates = {
            "gold": player["gold"] - upgrade_cost["gold"],
            "crystals": player["crystals"] - upgrade_cost["crystals"]
        }
        
        await player_service.update_player(player_id, updates)
        
        # Update skill level (in a real implementation, this would be stored per player)
        SKILLS_DATA[request.skill_id]["level"] += 1
        SKILLS_DATA[request.skill_id]["damage"] = int(SKILLS_DATA[request.skill_id]["damage"] * 1.1)
        
        return {
            "success": True,
            "message": f"Skill {skill['name']} upgraded to level {SKILLS_DATA[request.skill_id]['level']}",
            "skill": SKILLS_DATA[request.skill_id],
            "cost": upgrade_cost
        }
        
    except Exception as e:
        print(f"Skill upgrade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
