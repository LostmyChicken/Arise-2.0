from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import time
import random
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/arena", tags=["arena"])

# Arena models
class ArenaChallenge(BaseModel):
    target_player_id: str

class ArenaMatch(BaseModel):
    id: str
    challenger_id: str
    challenger_username: str
    defender_id: str
    defender_username: str
    challenger_power: int
    defender_power: int
    winner_id: Optional[str]
    rewards: Dict[str, Any]
    created_at: int
    completed_at: Optional[int]
    status: str  # pending, in_progress, completed

# Arena rankings and matches storage
arena_rankings: List[Dict[str, Any]] = []
active_matches: Dict[str, ArenaMatch] = {}

def calculate_power_level(stats: Dict[str, int]) -> int:
    """Calculate total power level from player stats"""
    return (stats.get('attack', 0) + 
            stats.get('defense', 0) + 
            stats.get('hp', 0) + 
            stats.get('mp', 0) + 
            stats.get('precision', 0))

def simulate_battle(challenger_power: int, defender_power: int) -> Dict[str, Any]:
    """Simulate an arena battle"""
    # Base win chance is 50%, modified by power difference
    power_diff = challenger_power - defender_power
    win_chance = 0.5 + (power_diff / (max(challenger_power, defender_power) * 4))
    win_chance = max(0.1, min(0.9, win_chance))  # Clamp between 10% and 90%
    
    challenger_wins = random.random() < win_chance
    
    # Calculate damage dealt (for rewards)
    if challenger_wins:
        damage_dealt = random.randint(int(challenger_power * 0.8), challenger_power)
        damage_taken = random.randint(int(defender_power * 0.3), int(defender_power * 0.7))
    else:
        damage_dealt = random.randint(int(challenger_power * 0.3), int(challenger_power * 0.7))
        damage_taken = random.randint(int(defender_power * 0.8), defender_power)
    
    return {
        "challenger_wins": challenger_wins,
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "battle_duration": random.randint(30, 180)  # seconds
    }

@router.get("/rankings")
async def get_arena_rankings():
    """Get current arena rankings"""
    try:
        db = await get_db_connection()
        cursor = await db.execute("""
            SELECT id, level, attack, defense, hp, mp, precision, gold, diamond
            FROM players
            ORDER BY (attack + defense + hp + mp + precision) DESC
            LIMIT 50
        """)
        results = await cursor.fetchall()

        rankings = []
        rank = 1
        for row in results:
            power_level = calculate_power_level({
                'attack': row[2],
                'defense': row[3],
                'hp': row[4],
                'mp': row[5],
                'precision': row[6]
            })

            # Calculate arena points based on power level and level
            arena_points = (power_level // 10) + (row[1] * 50)

            rankings.append({
                "rank": rank,
                "player_id": row[0],
                "username": f"Hunter_{row[0][:8]}",  # Generate username from ID
                "level": row[1],
                "power_level": power_level,
                "arena_points": arena_points,
                "last_active": int(time.time()) - random.randint(0, 3600),
                "stats": {
                    "attack": row[2],
                    "defense": row[3],
                    "hp": row[4],
                    "mp": row[5],
                    "precision": row[6]
                }
            })
            rank += 1

        await db.close()
        return {"rankings": rankings}

    except Exception as e:
        print(f"Arena rankings error: {e}")
        # Enhanced mock rankings with Solo Leveling characters
        return {
            "rankings": [
                {
                    "rank": 1,
                    "player_id": "shadow_monarch_001",
                    "username": "Shadow Monarch",
                    "level": 100,
                    "power_level": 25000,
                    "arena_points": 5000,
                    "last_active": int(time.time()) - 300,
                    "stats": {"attack": 5000, "defense": 4000, "hp": 8000, "mp": 4000, "precision": 4000}
                },
                {
                    "rank": 2,
                    "player_id": "sung_jinwoo_002",
                    "username": "Sung Jin-Woo",
                    "level": 95,
                    "power_level": 23000,
                    "arena_points": 4750,
                    "last_active": int(time.time()) - 600,
                    "stats": {"attack": 4800, "defense": 3800, "hp": 7500, "mp": 3900, "precision": 3900}
                },
                {
                    "rank": 3,
                    "player_id": "cha_haein_003",
                    "username": "Cha Hae-In",
                    "level": 90,
                    "power_level": 21000,
                    "arena_points": 4500,
                    "last_active": int(time.time()) - 900,
                    "stats": {"attack": 4500, "defense": 3500, "hp": 7000, "mp": 3000, "precision": 3000}
                }
            ]
        }

@router.get("/my-rank")
async def get_my_arena_rank(current_user: dict = Depends(get_current_user)):
    """Get current user's arena rank and stats"""
    db = await get_db_connection()
    cursor = await db.execute("""
    SELECT arena_rank, arena_points, attack, defense, hp, mp, precision,
    (SELECT COUNT(*) FROM players WHERE arena_rank > 0 AND arena_rank < 
    (SELECT arena_rank FROM players WHERE id = ?)) + 1 as current_rank
    FROM players WHERE id = ?
    """, (current_user["player_id"], current_user["player_id"]))
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    power_level = calculate_power_level({
    'attack': result[2],
    'defense': result[3],
    'hp': result[4],
    'mp': result[5],
    'precision': result[6]
    })
        
    return {
    "arena_rank": result[0] or 0,
    "arena_points": result[1] or 0,
    "power_level": power_level,
    "current_rank": result[7] if result[0] else 0
    }

@router.get("/opponents")
async def get_arena_opponents(current_user: dict = Depends(get_current_user)):
    """Get list of potential arena opponents"""
    db = await get_db_connection()
    # Get current player's rank and power
    cursor = await db.execute("""
    SELECT arena_rank, arena_points, attack, defense, hp, mp, precision
    FROM players WHERE id = ?
    """, (current_user["player_id"],))
    player_result = await cursor.fetchone()
        
    if not player_result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    player_rank = player_result[0] or 999999
    player_power = calculate_power_level({
    'attack': player_result[2],
    'defense': player_result[3],
    'hp': player_result[4],
    'mp': player_result[5],
    'precision': player_result[6]
    })
        
    # Find opponents within reasonable rank range
    rank_range = max(50, player_rank // 10)  # Dynamic range based on rank
        
    cursor = await db.execute("""
    SELECT id, username, level, arena_rank, arena_points, 
    attack, defense, hp, mp, precision, last_login
    FROM players 
    WHERE id != ? 
    AND arena_rank > 0 
    AND arena_rank BETWEEN ? AND ?
    AND last_login > ?
    ORDER BY RANDOM()
    LIMIT 10
    """, (
    current_user["player_id"],
    max(1, player_rank - rank_range),
    player_rank + rank_range,
    int(time.time()) - 604800  # Active within last week
    ))
        
    opponents = []
    for row in cursor:
    opponent_power = calculate_power_level({
    'attack': row[5],
    'defense': row[6],
    'hp': row[7],
    'mp': row[8],
    'precision': row[9]
    })
            
    # Calculate win chance
    power_diff = player_power - opponent_power
    win_chance = 0.5 + (power_diff / (max(player_power, opponent_power) * 4))
    win_chance = max(0.1, min(0.9, win_chance))
            
    opponents.append({
    "player_id": row[0],
    "username": row[1],
    "level": row[2],
    "arena_rank": row[3],
    "arena_points": row[4],
    "power_level": opponent_power,
    "win_chance": round(win_chance * 100, 1),
    "last_active": row[10]
    })
        
    return {"opponents": opponents}

@router.post("/challenge")
async def challenge_player(challenge: ArenaChallenge, current_user: dict = Depends(get_current_user)):
    """Challenge another player to arena combat"""
    if challenge.target_player_id == current_user["player_id"]:
        raise HTTPException(status_code=400, detail="Cannot challenge yourself")
    
    db = await get_db_connection()
    # Get both players' data
    cursor = await db.execute("""
    SELECT username, level, attack, defense, hp, mp, precision, arena_rank, arena_points
    FROM players WHERE id = ?
    """, (current_user["player_id"],))
    challenger_result = await cursor.fetchone()
        
    cursor = await db.execute("""
    SELECT username, level, attack, defense, hp, mp, precision, arena_rank, arena_points
    FROM players WHERE id = ?
    """, (challenge.target_player_id,))
    defender_result = await cursor.fetchone()
        
    if not challenger_result or not defender_result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    challenger_power = calculate_power_level({
    'attack': challenger_result[2],
    'defense': challenger_result[3],
    'hp': challenger_result[4],
    'mp': challenger_result[5],
    'precision': challenger_result[6]
    })
        
    defender_power = calculate_power_level({
    'attack': defender_result[2],
    'defense': defender_result[3],
    'hp': defender_result[4],
    'mp': defender_result[5],
    'precision': defender_result[6]
    })
        
    # Simulate the battle
    battle_result = simulate_battle(challenger_power, defender_power)
        
    # Calculate rewards
    base_points = 25
    power_bonus = abs(challenger_power - defender_power) // 100
        
    if battle_result["challenger_wins"]:
    challenger_points = base_points + power_bonus
    defender_points = -max(5, base_points // 2)
    winner_id = current_user["player_id"]
            
    # Gold and XP rewards for winner
    gold_reward = random.randint(1000, 5000) + power_bonus * 10
    xp_reward = random.randint(100, 500) + power_bonus * 5
            
    rewards = {
    "winner": {
    "gold": gold_reward,
    "xp": xp_reward,
    "arena_points": challenger_points
    },
    "loser": {
    "arena_points": defender_points
    }
    }
    else:
    challenger_points = -max(5, base_points // 2)
    defender_points = base_points + power_bonus
    winner_id = challenge.target_player_id
            
    rewards = {
    "winner": {
    "arena_points": defender_points
    },
    "loser": {
    "arena_points": challenger_points
    }
    }
        
    # Update arena points
    await db.execute("""
    UPDATE players 
    SET arena_points = COALESCE(arena_points, 0) + ?
    WHERE id = ?
    """, (challenger_points, current_user["player_id"]))
        
    await db.execute("""
    UPDATE players 
    SET arena_points = COALESCE(arena_points, 0) + ?
    WHERE id = ?
    """, (defender_points, challenge.target_player_id))
        
    # Give rewards to winner
    if battle_result["challenger_wins"]:
    await db.execute("""
    UPDATE players 
    SET gold = gold + ?, xp = xp + ?
    WHERE id = ?
    """, (rewards["winner"]["gold"], rewards["winner"]["xp"], current_user["player_id"]))
        
    await db.commit()
        
    # Update rankings (simplified - in production, use proper ranking system)
    await update_arena_rankings(db)
        
    return {
    "battle_result": battle_result,
    "winner_id": winner_id,
    "rewards": rewards,
    "challenger_power": challenger_power,
    "defender_power": defender_power,
    "message": "Victory!" if battle_result["challenger_wins"] else "Defeat!"
    }

async def update_arena_rankings(db):
    """Update arena rankings based on points"""
    cursor = await db.execute("""
        SELECT id, arena_points FROM players 
        WHERE arena_points > 0 
        ORDER BY arena_points DESC
    """)
    results = await cursor.fetchall()
    
    for rank, (player_id, points) in enumerate(results, 1):
        await db.execute("""
            UPDATE players SET arena_rank = ? WHERE id = ?
        """, (rank, player_id))
    
    await db.commit()

@router.get("/history")
async def get_arena_history(current_user: dict = Depends(get_current_user)):
    """Get arena battle history for current user"""
    # In production, this would query a proper battle history table
    user_matches = [match for match in active_matches.values() 
                   if match.challenger_id == current_user["player_id"] or 
                      match.defender_id == current_user["player_id"]]
    
    # Sort by completion time
    history = sorted([match for match in user_matches if match.status == "completed"],
                    key=lambda x: x.completed_at or 0, reverse=True)
    
    return {"matches": history[:20]}  # Last 20 matches

@router.get("/rewards")
async def get_arena_rewards():
    """Get information about arena rewards and ranking tiers"""
    return {
        "ranking_tiers": {
            "Bronze": {"min_points": 0, "max_points": 999, "daily_rewards": {"gold": 1000, "crystals": 5}},
            "Silver": {"min_points": 1000, "max_points": 2499, "daily_rewards": {"gold": 2000, "crystals": 10}},
            "Gold": {"min_points": 2500, "max_points": 4999, "daily_rewards": {"gold": 3000, "crystals": 15}},
            "Platinum": {"min_points": 5000, "max_points": 9999, "daily_rewards": {"gold": 5000, "crystals": 25}},
            "Diamond": {"min_points": 10000, "max_points": 19999, "daily_rewards": {"gold": 8000, "crystals": 40}},
            "Master": {"min_points": 20000, "max_points": 999999, "daily_rewards": {"gold": 12000, "crystals": 60}}
        },
        "battle_rewards": {
            "win": {"base_points": 25, "gold_range": [1000, 5000], "xp_range": [100, 500]},
            "loss": {"points_lost": -12}
        }
    }
