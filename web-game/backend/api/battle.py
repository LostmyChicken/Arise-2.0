from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import random
import uuid
import time
from pathlib import Path

from services.database_service import db_service
from services.player_service import player_service
from services.auth_service import get_current_user

router = APIRouter()

# Load real enemy data from Discord bot
def load_enemy_data():
    """Load enemy data from JSON file"""
    try:
        # Try multiple possible paths
        possible_paths = [
            Path("backend/data/enemy.json"),
            Path("data/enemy.json"),
            Path("../data/enemy.json"),
            Path("web-game/backend/data/enemy.json")
        ]

        for enemy_path in possible_paths:
            if enemy_path.exists():
                print(f"Loading enemy data from: {enemy_path}")
                with open(enemy_path, 'r') as f:
                    data = json.load(f)
                    print(f"Loaded {len(data)} enemies from file")
                    return data

    except Exception as e:
        print(f"Error loading enemy data: {e}")

    print("Using fallback enemy data")
    # Fallback to default enemies if file not found
    return [
        {
            "id": "goblin",
            "name": "Goblin",
            "attack": 8,
            "defense": 3,
            "hp": 50,
            "image": "🧌",
            "element": "earth",
            "tier": 1
        }
    ]

ENEMY_DATA = load_enemy_data()

class BattleStart(BaseModel):
    battle_type: str  # pve, pvp, world_boss
    opponent_id: Optional[str] = None  # For PvP or specific enemy
    difficulty: Optional[str] = "normal"  # easy, normal, hard

class BattleAction(BaseModel):
    battle_id: str
    action_type: str  # attack, skill, item, defend
    skill_id: Optional[str] = None
    item_id: Optional[str] = None

@router.get("/monsters")
async def get_available_monsters():
    """Get list of available monsters for battle using real enemy data"""

    # Convert enemy data to monster format for frontend
    monsters = []
    for enemy in ENEMY_DATA[:10]:  # Limit to first 10 enemies for now
        monsters.append({
            "id": enemy.get("id", "unknown"),
            "name": enemy.get("name", "Unknown Enemy"),
            "level": enemy.get("tier", 1) * 5,  # Convert tier to level
            "hp": enemy.get("hp", 100),
            "attack": enemy.get("attack", 10),
            "defense": enemy.get("defense", 5),
            "xp_reward": enemy.get("hp", 100) // 4,  # XP based on HP
            "gold_reward": enemy.get("hp", 100) // 2,  # Gold based on HP
            "image": enemy.get("image", "👹"),
            "element": enemy.get("element", "neutral"),
            "tier": enemy.get("tier", 1)
        })

    # Add some default monsters if no enemy data loaded
    if not monsters:
        monsters = [
            {
                "id": "goblin",
                "name": "Goblin",
                "level": 1,
                "hp": 50,
                "attack": 8,
                "defense": 3,
                "xp_reward": 25,
                "gold_reward": 50,
                "image": "🧌",
                "element": "earth",
                "tier": 1
            }
        ]

    return {"monsters": monsters}

@router.post("/start")
async def start_battle(battle_data: BattleStart, player_id: str):
    """Start a new battle"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        battle_id = str(uuid.uuid4())
        
        if battle_data.battle_type == "pve":
            # Create PvE battle against random enemy
            enemy = await generate_random_enemy(player["level"], battle_data.difficulty)
            battle_state = {
                "id": battle_id,
                "type": "pve",
                "player": {
                    "id": player_id,
                    "name": player.get("username", "Unknown"),
                    "level": player["level"],
                    "hp": player["hp"],
                    "max_hp": player["hp"],
                    "mp": player["mp"],
                    "max_mp": player["mp"],
                    "attack": player["attack"],
                    "defense": player["defense"]
                },
                "enemy": enemy,
                "turn": "player",
                "turn_count": 1,
                "status": "active",
                "created_at": int(time.time())
            }
        
        elif battle_data.battle_type == "pvp":
            if not battle_data.opponent_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Opponent ID required for PvP battles"
                )
            
            opponent = await player_service.get_player(battle_data.opponent_id)
            if not opponent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Opponent not found"
                )
            
            battle_state = {
                "id": battle_id,
                "type": "pvp",
                "player1": {
                    "id": player_id,
                    "name": player.get("username", "Unknown"),
                    "level": player["level"],
                    "hp": player["hp"],
                    "max_hp": player["hp"],
                    "mp": player["mp"],
                    "max_mp": player["mp"],
                    "attack": player["attack"],
                    "defense": player["defense"]
                },
                "player2": {
                    "id": battle_data.opponent_id,
                    "name": opponent.get("username", "Unknown"),
                    "level": opponent["level"],
                    "hp": opponent["hp"],
                    "max_hp": opponent["hp"],
                    "mp": opponent["mp"],
                    "max_mp": opponent["mp"],
                    "attack": opponent["attack"],
                    "defense": opponent["defense"]
                },
                "turn": "player1",
                "turn_count": 1,
                "status": "active",
                "created_at": int(time.time())
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid battle type"
            )
        
        # Save battle to database
        await save_battle(battle_id, battle_state)
        
        return {
            "battle_id": battle_id,
            "battle_state": battle_state,
            "message": "Battle started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start battle: {str(e)}"
        )

@router.post("/action")
async def battle_action(action: BattleAction, player_id: str):
    """Perform a battle action"""
    try:
        # Load battle state
        battle_state = await load_battle(action.battle_id)
        if not battle_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Battle not found"
            )
        
        if battle_state["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Battle is not active"
            )
        
        # Validate it's the player's turn
        if battle_state["type"] == "pve":
            if battle_state["turn"] != "player":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not your turn"
                )
        elif battle_state["type"] == "pvp":
            current_player = "player1" if battle_state["turn"] == "player1" else "player2"
            if battle_state[current_player]["id"] != player_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not your turn"
                )
        
        # Process the action
        result = await process_battle_action(battle_state, action, player_id)
        
        # Save updated battle state
        await save_battle(action.battle_id, battle_state)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process battle action: {str(e)}"
        )

@router.get("/state/{battle_id}")
async def get_battle_state(battle_id: str):
    """Get current battle state"""
    try:
        battle_state = await load_battle(battle_id)
        if not battle_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Battle not found"
            )
        
        return {"battle_state": battle_state}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get battle state: {str(e)}"
        )

@router.get("/history/{player_id}")
async def get_battle_history(player_id: str, limit: int = 10):
    """Get player's battle history"""
    try:
        query = """
            SELECT * FROM battle_history 
            WHERE winner_id = ? OR loser_id = ?
            ORDER BY completed_at DESC 
            LIMIT ?
        """
        
        results = await db_service.execute_query('battles', query, (player_id, player_id, limit))
        
        history = []
        for row in results:
            history.append({
                "battle_id": row[1],
                "winner_id": row[2],
                "loser_id": row[3],
                "battle_type": row[4],
                "duration": row[5],
                "rewards": json.loads(row[6]) if row[6] else {},
                "completed_at": row[7]
            })
        
        return {"battle_history": history}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get battle history: {str(e)}"
        )

# Helper functions
async def generate_random_enemy(player_level: int, difficulty: str = "normal"):
    """Generate a random enemy based on player level and difficulty"""
    
    difficulty_multipliers = {
        "easy": 0.8,
        "normal": 1.0,
        "hard": 1.3
    }
    
    multiplier = difficulty_multipliers.get(difficulty, 1.0)
    
    # Base enemy stats scaled to player level
    base_level = max(1, player_level + random.randint(-2, 2))
    
    enemy_types = [
        {"name": "Goblin", "hp_mult": 0.8, "attack_mult": 0.9, "defense_mult": 0.7},
        {"name": "Orc", "hp_mult": 1.2, "attack_mult": 1.1, "defense_mult": 1.0},
        {"name": "Skeleton", "hp_mult": 0.9, "attack_mult": 1.0, "defense_mult": 0.8},
        {"name": "Troll", "hp_mult": 1.5, "attack_mult": 1.2, "defense_mult": 1.3}
    ]
    
    enemy_type = random.choice(enemy_types)
    
    return {
        "name": enemy_type["name"],
        "level": base_level,
        "hp": int(base_level * 50 * enemy_type["hp_mult"] * multiplier),
        "max_hp": int(base_level * 50 * enemy_type["hp_mult"] * multiplier),
        "attack": int(base_level * 8 * enemy_type["attack_mult"] * multiplier),
        "defense": int(base_level * 6 * enemy_type["defense_mult"] * multiplier),
        "xp_reward": int(base_level * 25 * multiplier),
        "gold_reward": int(base_level * 50 * multiplier)
    }

async def process_battle_action(battle_state: Dict, action: BattleAction, player_id: str):
    """Process a battle action and update battle state"""
    
    if action.action_type == "attack":
        return await process_attack(battle_state, player_id)
    elif action.action_type == "skill":
        return await process_skill(battle_state, player_id, action.skill_id)
    elif action.action_type == "defend":
        return await process_defend(battle_state, player_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action type"
        )

async def process_attack(battle_state: Dict, player_id: str):
    """Process a basic attack"""
    
    if battle_state["type"] == "pve":
        # Player attacks enemy
        player = battle_state["player"]
        enemy = battle_state["enemy"]
        
        # Calculate damage
        damage = max(1, player["attack"] - enemy["defense"] + random.randint(-5, 5))
        enemy["hp"] = max(0, enemy["hp"] - damage)
        
        result = {
            "action": "attack",
            "attacker": player["name"],
            "target": enemy["name"],
            "damage": damage,
            "target_hp": enemy["hp"],
            "battle_state": battle_state
        }
        
        # Check if enemy is defeated
        if enemy["hp"] <= 0:
            battle_state["status"] = "completed"
            battle_state["winner"] = player_id
            
            # Award rewards
            await player_service.add_xp(player_id, enemy["xp_reward"])
            await player_service.add_gold(player_id, enemy["gold_reward"])
            
            result["battle_ended"] = True
            result["winner"] = player_id
            result["rewards"] = {
                "xp": enemy["xp_reward"],
                "gold": enemy["gold_reward"]
            }
        else:
            # Enemy's turn
            battle_state["turn"] = "enemy"
            
            # Enemy attacks back
            enemy_damage = max(1, enemy["attack"] - player["defense"] + random.randint(-3, 3))
            player["hp"] = max(0, player["hp"] - enemy_damage)
            
            result["enemy_action"] = {
                "action": "attack",
                "damage": enemy_damage,
                "player_hp": player["hp"]
            }
            
            # Check if player is defeated
            if player["hp"] <= 0:
                battle_state["status"] = "completed"
                battle_state["winner"] = "enemy"
                result["battle_ended"] = True
                result["winner"] = "enemy"
            else:
                battle_state["turn"] = "player"
        
        battle_state["turn_count"] += 1
        return result
    
    # TODO: Implement PvP attack logic
    return {"message": "PvP not implemented yet"}

async def process_skill(battle_state: Dict, player_id: str, skill_id: str):
    """Process a skill action"""
    # TODO: Implement skill system
    return {"message": "Skill system not implemented yet"}

async def process_defend(battle_state: Dict, player_id: str):
    """Process a defend action"""
    # TODO: Implement defend action
    return {"message": "Defend action not implemented yet"}

async def save_battle(battle_id: str, battle_state: Dict):
    """Save battle state to database"""
    query = """
        INSERT OR REPLACE INTO active_battles (id, battle_type, players, battle_data, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    
    players = []
    if battle_state["type"] == "pve":
        players = [battle_state["player"]["id"]]
    elif battle_state["type"] == "pvp":
        players = [battle_state["player1"]["id"], battle_state["player2"]["id"]]
    
    await db_service.execute_query('battles', query, (
        battle_id,
        battle_state["type"],
        json.dumps(players),
        json.dumps(battle_state)
    ))

async def load_battle(battle_id: str) -> Optional[Dict]:
    """Load battle state from database"""
    query = "SELECT battle_data FROM active_battles WHERE id = ?"
    result = await db_service.execute_query('battles', query, (battle_id,))
    
    if result:
        return json.loads(result[0][0])
    return None

# Export router
battle_router = router