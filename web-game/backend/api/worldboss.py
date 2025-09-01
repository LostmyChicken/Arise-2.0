from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import time
import random
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from services.auth_service import get_current_user
from services.database_service import get_db_connection
from services.player_service import player_service

router = APIRouter(prefix="/worldboss", tags=["worldboss"])

# Load real boss data from Discord bot
def load_boss_data():
    """Load boss data from SQLite database"""
    try:
        # Try multiple possible paths for the bosses database
        possible_paths = [
            Path("web-game/backend/data/bosses.db"),
            Path("backend/data/bosses.db"),
            Path("data/bosses.db"),
            Path("../data/bosses.db")
        ]

        for db_path in possible_paths:
            if db_path.exists():
                print(f"Loading boss data from: {db_path}")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM bosses")
                rows = cursor.fetchall()

                bosses = []
                for row in rows:
                    boss = {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "image": row[3],
                        "attack": row[4],
                        "defense": row[5],
                        "health": row[6],
                        "speed": row[7],
                        "precision": row[8],
                        "rarity": row[9],
                        "class": row[10],
                        "weaknessClass": row[11]
                    }
                    bosses.append(boss)

                conn.close()
                print(f"Loaded {len(bosses)} bosses from database")
                return bosses

    except Exception as e:
        print(f"Error loading boss data: {e}")

    # Fallback boss data if database not found
    return [
        {
            "id": "shadow_monarch",
            "name": "Shadow Monarch",
            "description": "The ultimate shadow boss",
            "image": "https://via.placeholder.com/300x300",
            "attack": 5000,
            "defense": 3000,
            "health": 100000,
            "speed": 200,
            "precision": 150,
            "rarity": "SSR",
            "class": "Dark",
            "weaknessClass": "Light"
        }
    ]

BOSS_DATA = load_boss_data()

# World Boss models
class AttackBossRequest(BaseModel):
    damage: int
    skill_used: Optional[str] = None

class WorldBoss(BaseModel):
    id: str
    name: str
    description: str
    max_hp: int
    current_hp: int
    level: int
    element: str
    image: str
    spawn_time: int
    despawn_time: int
    participants: Dict[str, Dict[str, Any]] = {}
    rewards: Dict[str, Any] = {}
    status: str = "active"  # active, defeated, despawned

# World Boss data
WORLD_BOSSES = {
    "shadow_monarch": {
        "id": "shadow_monarch",
        "name": "Shadow Monarch",
        "description": "The ultimate shadow ruler has awakened",
        "max_hp": 10000000,
        "level": 100,
        "element": "Dark",
        "image": "/images/shadow_monarch.png",
        "rewards": {
            "gold": {"min": 100000, "max": 500000},
            "diamonds": {"min": 100, "max": 500},
            "crystals": {"min": 50, "max": 200},
            "tos": {"min": 100, "max": 1000},
            "rare_items": ["shadow_essence", "monarch_fragment", "dark_crystal"]
        }
    },
    "ice_monarch": {
        "id": "ice_monarch",
        "name": "Ice Monarch",
        "description": "Frozen ruler of the eternal winter",
        "max_hp": 8000000,
        "level": 90,
        "element": "Water",
        "image": "/images/ice_monarch.png",
        "rewards": {
            "gold": {"min": 80000, "max": 400000},
            "diamonds": {"min": 80, "max": 400},
            "crystals": {"min": 40, "max": 160},
            "tos": {"min": 80, "max": 800},
            "rare_items": ["ice_essence", "frozen_heart", "ice_crystal"]
        }
    },
    "flame_monarch": {
        "id": "flame_monarch",
        "name": "Flame Monarch",
        "description": "Burning sovereign of endless fire",
        "max_hp": 9000000,
        "level": 95,
        "element": "Fire",
        "image": "/images/flame_monarch.png",
        "rewards": {
            "gold": {"min": 90000, "max": 450000},
            "diamonds": {"min": 90, "max": 450},
            "crystals": {"min": 45, "max": 180},
            "tos": {"min": 90, "max": 900},
            "rare_items": ["flame_essence", "burning_core", "fire_crystal"]
        }
    },
    "beast_monarch": {
        "id": "beast_monarch",
        "name": "Beast Monarch",
        "description": "Primal ruler of all monsters",
        "max_hp": 12000000,
        "level": 110,
        "element": "Earth",
        "image": "/images/beast_monarch.png",
        "rewards": {
            "gold": {"min": 120000, "max": 600000},
            "diamonds": {"min": 120, "max": 600},
            "crystals": {"min": 60, "max": 240},
            "tos": {"min": 120, "max": 1200},
            "rare_items": ["beast_essence", "primal_fang", "earth_crystal"]
        }
    }
}

# Global world boss state (in production, this would be in Redis or database)
current_world_boss = None
boss_spawn_cooldown = 3600  # 1 hour between bosses

def spawn_world_boss():
    """Spawn a random world boss"""
    global current_world_boss
    
    if current_world_boss and current_world_boss["status"] == "active":
        return current_world_boss
    
    # Use real boss data if available, otherwise fallback to predefined bosses
    current_time = int(time.time())

    if BOSS_DATA:
        # Select random boss from real Discord bot data
        boss_template = random.choice(BOSS_DATA)
        current_world_boss = {
            "id": boss_template["id"],
            "name": boss_template["name"],
            "description": boss_template["description"],
            "max_hp": boss_template["health"] * 100,  # Scale up for world boss
            "current_hp": boss_template["health"] * 100,
            "level": 50 + (boss_template["health"] // 1000),  # Level based on health
            "element": boss_template["class"],
            "image": boss_template["image"],
            "attack": boss_template["attack"],
            "defense": boss_template["defense"],
            "speed": boss_template["speed"],
            "precision": boss_template["precision"],
            "rarity": boss_template["rarity"],
            "class": boss_template["class"],
            "weaknessClass": boss_template["weaknessClass"],
            "spawn_time": current_time,
            "despawn_time": current_time + 3600,  # 1 hour to defeat
            "participants": {},
            "status": "active"
        }
    else:
        # Fallback to predefined bosses
        boss_id = random.choice(list(WORLD_BOSSES.keys()))
        boss_template = WORLD_BOSSES[boss_id].copy()
        current_world_boss = {
            **boss_template,
            "current_hp": boss_template["max_hp"],
            "spawn_time": current_time,
            "despawn_time": current_time + 1800,  # 30 minutes to defeat
            "participants": {},
            "status": "active"
        }
    
    return current_world_boss

def calculate_boss_damage(player_attack: int, boss_defense: int, skill_multiplier: float = 1.0) -> int:
    """Calculate damage dealt to world boss"""
    base_damage = max(1, player_attack - boss_defense // 2)
    final_damage = int(base_damage * skill_multiplier * random.uniform(0.8, 1.2))
    return max(1, final_damage)

@router.get("/current")
async def get_current_world_boss():
    """Get current active world boss"""
    global current_world_boss
    current_time = int(time.time())
    
    # Check if boss should despawn
    if current_world_boss and current_time > current_world_boss["despawn_time"]:
        current_world_boss["status"] = "despawned"
        current_world_boss = None
    
    # Spawn new boss if none active
    if not current_world_boss:
        # Check cooldown (simplified - in production use proper scheduling)
        spawn_world_boss()
    
    if current_world_boss:
        return {
            "boss": current_world_boss,
            "time_remaining": max(0, current_world_boss["despawn_time"] - current_time),
            "hp_percentage": (current_world_boss["current_hp"] / current_world_boss["max_hp"]) * 100
        }
    
    return {"boss": None, "message": "No world boss currently active"}

@router.post("/attack")
async def attack_world_boss(request: AttackBossRequest, current_user: dict = Depends(get_current_user)):
    """Attack the current world boss"""
    global current_world_boss
    
    if not current_world_boss or current_world_boss["status"] != "active":
        raise HTTPException(status_code=404, detail="No active world boss")
    
    current_time = int(time.time())
    if current_time > current_world_boss["despawn_time"]:
        current_world_boss["status"] = "despawned"
        raise HTTPException(status_code=400, detail="World boss has despawned")
    
    db = await get_db_connection()
    # Get player stats
    cursor = await db.execute(
        "SELECT attack, level, learned_skills FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    player_attack = result[0] or 10
    player_level = result[1] or 1
    learned_skills = json.loads(result[2] or '{}')
        
    # Calculate damage
    skill_multiplier = 1.0
    if request.skill_used and request.skill_used in learned_skills:
        # Apply skill multiplier (simplified)
        skill_multiplier = 1.5
        
    boss_defense = current_world_boss["level"] * 10
    damage_dealt = calculate_boss_damage(player_attack, boss_defense, skill_multiplier)
        
    # Apply damage to boss
    current_world_boss["current_hp"] = max(0, current_world_boss["current_hp"] - damage_dealt)
        
    # Track player participation
    player_id = current_user["player_id"]
    if player_id not in current_world_boss["participants"]:
        current_world_boss["participants"][player_id] = {
            "username": current_user["username"],
            "total_damage": 0,
            "attacks": 0,
            "last_attack": current_time
        }
        
    current_world_boss["participants"][player_id]["total_damage"] += damage_dealt
    current_world_boss["participants"][player_id]["attacks"] += 1
    current_world_boss["participants"][player_id]["last_attack"] = current_time
        
    # Check if boss is defeated
    boss_defeated = current_world_boss["current_hp"] <= 0
    if boss_defeated:
        current_world_boss["status"] = "defeated"
        # Distribute rewards
        await distribute_boss_rewards(current_world_boss)
        
    return {
        "damage_dealt": damage_dealt,
        "boss_hp_remaining": current_world_boss["current_hp"],
        "boss_defeated": boss_defeated,
        "your_total_damage": current_world_boss["participants"][player_id]["total_damage"],
        "hp_percentage": (current_world_boss["current_hp"] / current_world_boss["max_hp"]) * 100
    }

async def distribute_boss_rewards(boss_data: Dict[str, Any]):
    """Distribute rewards to all participants"""
    if not boss_data["participants"]:
        return
    
    total_damage = sum(p["total_damage"] for p in boss_data["participants"].values())
    rewards_template = boss_data["rewards"]
    
    db = await get_db_connection()
    for player_id, participation in boss_data["participants"].items():
        # Calculate reward based on participation
        damage_percentage = participation["total_damage"] / total_damage if total_damage > 0 else 0
        participation_bonus = min(2.0, 0.5 + damage_percentage * 1.5)  # 0.5x to 2x multiplier
            
        # Calculate rewards
        gold_reward = int(random.randint(
            rewards_template["gold"]["min"],
            rewards_template["gold"]["max"]
        ) * participation_bonus)
            
        diamonds_reward = int(random.randint(
            rewards_template["diamonds"]["min"],
            rewards_template["diamonds"]["max"]
        ) * participation_bonus)
            
        crystals_reward = int(random.randint(
            rewards_template["crystals"]["min"],
            rewards_template["crystals"]["max"]
        ) * participation_bonus)
            
        tos_reward = int(random.randint(
            rewards_template["tos"]["min"],
            rewards_template["tos"]["max"]
        ) * participation_bonus)
            
        # Give rare item chance
        rare_item = None
        if random.random() < 0.3 * participation_bonus:  # 30% base chance
            rare_item = random.choice(rewards_template["rare_items"])
            
        # Update player resources
        await db.execute("""
            UPDATE players 
            SET gold = gold + ?, diamonds = diamonds + ?, crystals = crystals + ?, tos = tos + ?
            WHERE id = ?
        """, (gold_reward, diamonds_reward, crystals_reward, tos_reward, player_id))
            
        # Add rare item to inventory if obtained
        if rare_item:
            cursor = await db.execute("SELECT inventory FROM players WHERE id = ?", (player_id,))
            result = await cursor.fetchone()
            if result:
                inventory = json.loads(result[0] or '{}')
                inventory[rare_item] = inventory.get(rare_item, 0) + 1
                await db.execute(
                    "UPDATE players SET inventory = ? WHERE id = ?",
                    (json.dumps(inventory), player_id)
                )
        
    await db.commit()

@router.get("/leaderboard")
async def get_world_boss_leaderboard():
    """Get current world boss damage leaderboard"""
    global current_world_boss
    
    if not current_world_boss or not current_world_boss["participants"]:
        return {"leaderboard": [], "message": "No active world boss or participants"}
    
    # Sort participants by damage
    leaderboard = []
    for player_id, participation in current_world_boss["participants"].items():
        leaderboard.append({
            "player_id": player_id,
            "username": participation["username"],
            "total_damage": participation["total_damage"],
            "attacks": participation["attacks"],
            "last_attack": participation["last_attack"]
        })
    
    leaderboard.sort(key=lambda x: x["total_damage"], reverse=True)
    
    return {
        "boss_name": current_world_boss["name"],
        "leaderboard": leaderboard[:50],  # Top 50
        "total_participants": len(leaderboard)
    }

@router.get("/history")
async def get_world_boss_history(current_user: dict = Depends(get_current_user)):
    """Get player's world boss participation history"""
    # In production, this would query a proper history table
    return {
        "message": "World boss history feature coming soon",
        "recent_battles": []
    }

@router.post("/admin/spawn")
async def admin_spawn_boss(boss_id: str, current_user: dict = Depends(get_current_user)):
    """Admin command to spawn specific world boss"""
    # Add admin check here
    global current_world_boss
    
    if boss_id not in WORLD_BOSSES:
        raise HTTPException(status_code=404, detail="Boss not found")
    
    boss_template = WORLD_BOSSES[boss_id].copy()
    current_time = int(time.time())
    
    current_world_boss = {
        **boss_template,
        "current_hp": boss_template["max_hp"],
        "spawn_time": current_time,
        "despawn_time": current_time + 1800,
        "participants": {},
        "status": "active"
    }
    
    return {"message": f"Spawned {boss_template['name']}", "boss": current_world_boss}
