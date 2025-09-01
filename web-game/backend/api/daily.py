from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import time
from datetime import datetime, timedelta
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/daily", tags=["daily"])

# Daily models
class Mission(BaseModel):
    id: str
    name: str
    description: str
    type: str  # battle, gacha, login, upgrade, etc.
    target: int  # target amount
    progress: int = 0
    completed: bool = False
    rewards: Dict[str, Any]
    expires_at: int

class DailyReward(BaseModel):
    day: int
    rewards: Dict[str, Any]
    claimed: bool = False

# Daily missions templates
DAILY_MISSIONS = {
    "battle_wins": {
        "name": "Battle Victor",
        "description": "Win {target} battles",
        "type": "battle",
        "target": 3,
        "rewards": {"gold": 2000, "xp": 300, "crystals": 5}
    },
    "gacha_pulls": {
        "name": "Summoner",
        "description": "Perform {target} gacha pulls",
        "type": "gacha",
        "target": 5,
        "rewards": {"gold": 1500, "tickets": 2, "crystals": 3}
    },
    "gates_cleared": {
        "name": "Gate Explorer",
        "description": "Clear {target} gate floors",
        "type": "gates",
        "target": 10,
        "rewards": {"gold": 3000, "stamina": 20, "crystals": 8}
    },
    "skills_used": {
        "name": "Skill Master",
        "description": "Use skills {target} times",
        "type": "skills",
        "target": 15,
        "rewards": {"gold": 1000, "skill_points": 2, "crystals": 4}
    },
    "upgrades_done": {
        "name": "Enhancement Expert",
        "description": "Upgrade items {target} times",
        "type": "upgrade",
        "target": 2,
        "rewards": {"gold": 2500, "stones": 50, "crystals": 6}
    },
    "worldboss_damage": {
        "name": "Boss Hunter",
        "description": "Deal {target} damage to world bosses",
        "type": "worldboss",
        "target": 50000,
        "rewards": {"gold": 5000, "tos": 20, "crystals": 10}
    },
    "arena_battles": {
        "name": "Arena Warrior",
        "description": "Fight {target} arena battles",
        "type": "arena",
        "target": 3,
        "rewards": {"gold": 2000, "arena_points": 50, "crystals": 7}
    }
}

# Daily login rewards (7-day cycle)
DAILY_LOGIN_REWARDS = [
    {"day": 1, "rewards": {"gold": 1000, "crystals": 5}},
    {"day": 2, "rewards": {"gold": 1500, "stones": 20}},
    {"day": 3, "rewards": {"gold": 2000, "tickets": 3}},
    {"day": 4, "rewards": {"gold": 2500, "crystals": 10}},
    {"day": 5, "rewards": {"gold": 3000, "tos": 10}},
    {"day": 6, "rewards": {"gold": 4000, "diamonds": 50}},
    {"day": 7, "rewards": {"gold": 5000, "crystals": 20, "premiumT": 1}}
]

def get_daily_reset_time():
    """Get the next daily reset time (UTC midnight)"""
    now = datetime.utcnow()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int(tomorrow.timestamp())

def generate_daily_missions():
    """Generate random daily missions"""
    import random
    
    # Select 3-5 random missions
    mission_keys = random.sample(list(DAILY_MISSIONS.keys()), random.randint(3, 5))
    missions = []
    reset_time = get_daily_reset_time()
    
    for i, key in enumerate(mission_keys):
        template = DAILY_MISSIONS[key].copy()
        mission = Mission(
            id=f"daily_{key}_{int(time.time())}",
            name=template["name"],
            description=template["description"].format(target=template["target"]),
            type=template["type"],
            target=template["target"],
            rewards=template["rewards"],
            expires_at=reset_time
        )
        missions.append(mission)
    
    return missions

@router.get("/missions")
async def get_daily_missions(current_user: dict = Depends(get_current_user)):
    """Get current daily missions for the player"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT daily_missions, last_mission_reset FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    daily_missions = json.loads(result[0] or '[]')
    last_reset = result[1] or 0
    current_time = int(time.time())
    reset_time = get_daily_reset_time()
        
    # Check if missions need to be reset (new day)
    if current_time >= last_reset + 86400 or not daily_missions:
        # Generate new missions
        new_missions = generate_daily_missions()
        daily_missions = [mission.dict() for mission in new_missions]
            
        # Update database
        await db.execute(
            "UPDATE players SET daily_missions = ?, last_mission_reset = ? WHERE id = ?",
            (json.dumps(daily_missions), current_time, current_user["player_id"])
        )
        await db.commit()
        
    return {"missions": daily_missions, "reset_time": reset_time}

@router.post("/missions/{mission_id}/claim")
async def claim_mission_reward(mission_id: str, current_user: dict = Depends(get_current_user)):
    """Claim reward for completed mission"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT daily_missions FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    daily_missions = json.loads(result[0] or '[]')
        
    # Find the mission
    mission = None
    mission_index = None
    for i, m in enumerate(daily_missions):
        if m["id"] == mission_id:
            mission = m
            mission_index = i
            break
        
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    if not mission["completed"]:
        raise HTTPException(status_code=400, detail="Mission not completed")
        
    if mission.get("claimed", False):
        raise HTTPException(status_code=400, detail="Reward already claimed")
        
    # Mark as claimed
    daily_missions[mission_index]["claimed"] = True
        
    # Give rewards
    rewards = mission["rewards"]
    update_query = "UPDATE players SET daily_missions = ?"
    update_params = [json.dumps(daily_missions)]
        
    for resource, amount in rewards.items():
        if resource in ["gold", "diamonds", "stones", "crystals", "tos", "tickets", "premiumT", "xp", "skill_points"]:
            update_query += f", {resource} = COALESCE({resource}, 0) + ?"
            update_params.append(amount)
        
    update_query += " WHERE id = ?"
    update_params.append(current_user["player_id"])
        
    await db.execute(update_query, update_params)
    await db.commit()
        
    return {
        "message": "Mission reward claimed!",
        "rewards": rewards
    }

@router.post("/missions/progress")
async def update_mission_progress(mission_type: str, amount: int = 1, current_user: dict = Depends(get_current_user)):
    """Update progress for missions of a specific type"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT daily_missions FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        return {"message": "Player not found"}
        
    daily_missions = json.loads(result[0] or '[]')
    updated = False
        
    # Update progress for matching missions
    for mission in daily_missions:
        if mission["type"] == mission_type and not mission["completed"]:
            mission["progress"] = min(mission["progress"] + amount, mission["target"])
            if mission["progress"] >= mission["target"]:
                mission["completed"] = True
            updated = True
        
    if updated:
        await db.execute(
            "UPDATE players SET daily_missions = ? WHERE id = ?",
            (json.dumps(daily_missions), current_user["player_id"])
        )
        await db.commit()
        
    return {"message": "Mission progress updated"}

@router.get("/login-rewards")
async def get_login_rewards(current_user: dict = Depends(get_current_user)):
    """Get daily login rewards status"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT login_streak, last_login_reward, created_at FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    login_streak = result[0] or 0
    last_login_reward = result[1] or 0
    created_at = result[2]
        
    current_time = int(time.time())
    today_start = current_time - (current_time % 86400)
        
    # Check if player can claim today's reward
    can_claim = last_login_reward < today_start
        
    # Calculate current day in cycle (1-7)
    current_day = (login_streak % 7) + 1 if can_claim else ((login_streak - 1) % 7) + 1
        
    return {
        "login_streak": login_streak,
        "current_day": current_day,
        "can_claim": can_claim,
        "rewards": DAILY_LOGIN_REWARDS,
        "next_reward": DAILY_LOGIN_REWARDS[current_day - 1] if can_claim else None
    }

@router.post("/login-rewards/claim")
async def claim_login_reward(current_user: dict = Depends(get_current_user)):
    """Claim daily login reward"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT login_streak, last_login_reward FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    login_streak = result[0] or 0
    last_login_reward = result[1] or 0
        
    current_time = int(time.time())
    today_start = current_time - (current_time % 86400)
        
    # Check if player can claim today's reward
    if last_login_reward >= today_start:
        raise HTTPException(status_code=400, detail="Already claimed today's reward")
        
    # Increment streak
    new_streak = login_streak + 1
    current_day = ((new_streak - 1) % 7) + 1
        
    # Get rewards for current day
    day_rewards = DAILY_LOGIN_REWARDS[current_day - 1]["rewards"]
        
    # Update player data
    update_query = "UPDATE players SET login_streak = ?, last_login_reward = ?"
    update_params = [new_streak, current_time]
        
    for resource, amount in day_rewards.items():
        if resource in ["gold", "diamonds", "stones", "crystals", "tos", "tickets", "premiumT"]:
            update_query += f", {resource} = COALESCE({resource}, 0) + ?"
            update_params.append(amount)
        
    update_query += " WHERE id = ?"
    update_params.append(current_user["player_id"])
        
    await db.execute(update_query, update_params)
    await db.commit()
        
    return {
        "message": f"Day {current_day} login reward claimed!",
        "rewards": day_rewards,
        "new_streak": new_streak,
        "next_day": (current_day % 7) + 1
    }

@router.get("/weekly-missions")
async def get_weekly_missions(current_user: dict = Depends(get_current_user)):
    """Get weekly missions (more challenging, better rewards)"""
    # Weekly missions would be similar to daily but with higher targets and better rewards
    weekly_missions = [
        {
            "id": "weekly_battles",
            "name": "Weekly Warrior",
            "description": "Win 20 battles this week",
            "type": "battle",
            "target": 20,
            "progress": 0,
            "rewards": {"gold": 10000, "diamonds": 100, "crystals": 50},
            "expires_at": int(time.time()) + 604800  # 7 days
        },
        {
            "id": "weekly_gates",
            "name": "Gate Master",
            "description": "Clear 50 gate floors this week",
            "type": "gates",
            "target": 50,
            "progress": 0,
            "rewards": {"gold": 15000, "tos": 100, "crystals": 75},
            "expires_at": int(time.time()) + 604800
        }
    ]
    
    return {"missions": weekly_missions}

@router.get("/achievements")
async def get_achievements(current_user: dict = Depends(get_current_user)):
    """Get player achievements"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT achievements FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    achievements = json.loads(result[0] or '{}') if result else {}
        
    # Define available achievements
    all_achievements = {
        "first_battle": {"name": "First Victory", "description": "Win your first battle", "reward": {"gold": 1000}},
        "battle_veteran": {"name": "Battle Veteran", "description": "Win 100 battles", "reward": {"gold": 10000, "crystals": 50}},
        "gacha_addict": {"name": "Summoning Addict", "description": "Perform 100 gacha pulls", "reward": {"tickets": 10}},
        "gate_explorer": {"name": "Gate Explorer", "description": "Clear 10 different gates", "reward": {"stamina": 50}},
        "skill_master": {"name": "Skill Master", "description": "Learn 10 skills", "reward": {"skill_points": 10}},
        "arena_champion": {"name": "Arena Champion", "description": "Reach top 10 in arena", "reward": {"arena_points": 500}},
        "collector": {"name": "Collector", "description": "Own 50 different items", "reward": {"inventory_slots": 20}},
        "hunter_master": {"name": "Hunter Master", "description": "Own 20 different hunters", "reward": {"hunter_slots": 10}}
    }
        
    return {
        "achievements": achievements,
        "available_achievements": all_achievements
    }
