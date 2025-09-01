from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import time
import random
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/gates", tags=["gates"])

# Gate models
class EnterGateRequest(BaseModel):
    gate_id: str

class GateActionRequest(BaseModel):
    action: str  # "explore", "fight", "rest", "exit"
    target: Optional[str] = None

class Gate(BaseModel):
    id: str
    name: str
    description: str
    rank: str  # E, D, C, B, A, S
    element: str
    max_floors: int
    stamina_cost: int
    rewards: Dict[str, Any]
    monsters: List[Dict[str, Any]]
    status: str = "available"  # available, occupied, cleared

# Gate definitions
GATES = {
    "shadow_dungeon": {
        "id": "shadow_dungeon",
        "name": "Shadow Dungeon",
        "description": "A dark dungeon filled with shadow creatures",
        "rank": "A",
        "element": "Dark",
        "max_floors": 10,
        "stamina_cost": 20,
        "rewards": {
            "gold": {"min": 5000, "max": 15000},
            "xp": {"min": 500, "max": 1500},
            "items": ["shadow_essence", "dark_crystal", "shadow_weapon"],
            "hunters": ["shadow_soldier", "shadow_mage"]
        },
        "monsters": [
            {"name": "Shadow Wolf", "hp": 500, "attack": 80, "defense": 40, "level": 25},
            {"name": "Dark Wraith", "hp": 800, "attack": 120, "defense": 60, "level": 30},
            {"name": "Shadow Lord", "hp": 1500, "attack": 200, "defense": 100, "level": 40}
        ]
    },
    "ice_cavern": {
        "id": "ice_cavern",
        "name": "Ice Cavern",
        "description": "Frozen caves with ice elementals",
        "rank": "B",
        "element": "Water",
        "max_floors": 8,
        "stamina_cost": 15,
        "rewards": {
            "gold": {"min": 3000, "max": 10000},
            "xp": {"min": 300, "max": 1000},
            "items": ["ice_shard", "frozen_core", "ice_weapon"],
            "hunters": ["ice_mage", "frost_warrior"]
        },
        "monsters": [
            {"name": "Ice Sprite", "hp": 300, "attack": 60, "defense": 30, "level": 20},
            {"name": "Frost Giant", "hp": 1000, "attack": 150, "defense": 80, "level": 35},
            {"name": "Ice Dragon", "hp": 2000, "attack": 250, "defense": 120, "level": 45}
        ]
    },
    "flame_tower": {
        "id": "flame_tower",
        "name": "Flame Tower",
        "description": "A burning tower with fire demons",
        "rank": "S",
        "element": "Fire",
        "max_floors": 15,
        "stamina_cost": 30,
        "rewards": {
            "gold": {"min": 10000, "max": 25000},
            "xp": {"min": 1000, "max": 2500},
            "items": ["flame_essence", "fire_crystal", "flame_weapon"],
            "hunters": ["flame_knight", "fire_demon"]
        },
        "monsters": [
            {"name": "Fire Imp", "hp": 400, "attack": 90, "defense": 45, "level": 30},
            {"name": "Flame Demon", "hp": 1200, "attack": 180, "defense": 90, "level": 40},
            {"name": "Inferno Lord", "hp": 3000, "attack": 350, "defense": 150, "level": 55}
        ]
    },
    "wind_valley": {
        "id": "wind_valley",
        "name": "Wind Valley",
        "description": "Windy valley with air elementals",
        "rank": "C",
        "element": "Wind",
        "max_floors": 6,
        "stamina_cost": 10,
        "rewards": {
            "gold": {"min": 2000, "max": 7000},
            "xp": {"min": 200, "max": 700},
            "items": ["wind_essence", "air_crystal", "wind_weapon"],
            "hunters": ["wind_archer", "storm_mage"]
        },
        "monsters": [
            {"name": "Wind Wisp", "hp": 200, "attack": 50, "defense": 25, "level": 15},
            {"name": "Storm Eagle", "hp": 600, "attack": 100, "defense": 50, "level": 25},
            {"name": "Wind Lord", "hp": 1200, "attack": 180, "defense": 80, "level": 35}
        ]
    },
    "earth_mines": {
        "id": "earth_mines",
        "name": "Earth Mines",
        "description": "Deep mines with earth golems",
        "rank": "B",
        "element": "Earth",
        "max_floors": 12,
        "stamina_cost": 18,
        "rewards": {
            "gold": {"min": 4000, "max": 12000},
            "xp": {"min": 400, "max": 1200},
            "items": ["earth_essence", "stone_crystal", "earth_weapon"],
            "hunters": ["earth_golem", "stone_warrior"]
        },
        "monsters": [
            {"name": "Rock Golem", "hp": 800, "attack": 70, "defense": 100, "level": 28},
            {"name": "Earth Elemental", "hp": 1000, "attack": 120, "defense": 120, "level": 35},
            {"name": "Mountain King", "hp": 2500, "attack": 200, "defense": 200, "level": 50}
        ]
    }
}

@router.get("/available")
async def get_available_gates():
    """Get all available gates"""
    return {"gates": list(GATES.values())}

@router.get("/player-progress")
async def get_player_gate_progress(current_user: dict = Depends(get_current_user)):
    """Get player's gate progress and current session"""
    db = await get_db_connection()
    cursor = await db.execute(
    "SELECT gate_progress, current_gate_session, stamina FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()

    if not result:
    raise HTTPException(status_code=404, detail="Player not found")

    gate_progress = json.loads(result[0] or '{}')
    current_session = json.loads(result[1] or '{}')
    stamina = result[2] or 100

    return {
    "gate_progress": gate_progress,
    "current_session": current_session,
    "stamina": stamina,
    "max_stamina": 100
    }

@router.post("/enter")
async def enter_gate(request: EnterGateRequest, current_user: dict = Depends(get_current_user)):
    """Enter a gate dungeon"""
    if request.gate_id not in GATES:
        raise HTTPException(status_code=404, detail="Gate not found")
    
    gate = GATES[request.gate_id]
    
    db = await get_db_connection()
    cursor = await db.execute(
    "SELECT stamina, current_gate_session FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    stamina = result[0] or 100
    current_session = json.loads(result[1] or '{}')
        
    # Check if already in a gate
    if current_session:
    raise HTTPException(status_code=400, detail="Already in a gate session")
        
    # Check stamina
    if stamina < gate["stamina_cost"]:
    raise HTTPException(status_code=400, detail="Not enough stamina")
        
    # Create new gate session
    new_session = {
    "gate_id": request.gate_id,
    "current_floor": 1,
    "start_time": int(time.time()),
    "hp": 100,  # Player HP in dungeon
    "mp": 100,  # Player MP in dungeon
    "inventory_found": {},
    "monsters_defeated": 0,
    "floors_cleared": 0,
    "status": "exploring"
    }
        
    # Deduct stamina
    new_stamina = stamina - gate["stamina_cost"]
        
    # Update database
    await db.execute(
    "UPDATE players SET current_gate_session = ?, stamina = ? WHERE id = ?",
    (json.dumps(new_session), new_stamina, current_user["player_id"])
    )
    await db.commit()
        
    return {
    "message": f"Entered {gate['name']}",
    "session": new_session,
    "stamina_remaining": new_stamina,
    "gate_info": gate
    }

@router.post("/action")
async def perform_gate_action(request: GateActionRequest, current_user: dict = Depends(get_current_user)):
    """Perform an action in the current gate"""
    db = await get_db_connection()
    cursor = await db.execute(
    "SELECT current_gate_session FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    current_session = json.loads(result[0] or '{}')
        
    if not current_session:
    raise HTTPException(status_code=400, detail="Not in a gate session")
        
    gate = GATES[current_session["gate_id"]]
        
    if request.action == "explore":
    return await handle_explore_action(current_session, gate, current_user["player_id"], db)
    elif request.action == "fight":
    return await handle_fight_action(current_session, gate, current_user["player_id"], db)
    elif request.action == "rest":
    return await handle_rest_action(current_session, gate, current_user["player_id"], db)
    elif request.action == "exit":
    return await handle_exit_action(current_session, gate, current_user["player_id"], db)
    else:
    raise HTTPException(status_code=400, detail="Invalid action")

async def handle_explore_action(session, gate, player_id, db):
    """Handle exploration action"""
    # Random encounter
    encounter_chance = random.random()
    
    if encounter_chance < 0.6:  # 60% chance of monster encounter
        monster = random.choice(gate["monsters"])
        session["status"] = "combat"
        session["current_monster"] = monster.copy()
        session["current_monster"]["current_hp"] = monster["hp"]
        
        result = {
            "action": "explore",
            "result": "monster_encounter",
            "monster": session["current_monster"],
            "message": f"You encountered a {monster['name']}!"
        }
    elif encounter_chance < 0.8:  # 20% chance of treasure
        treasure = random.choice(gate["rewards"]["items"])
        session["inventory_found"][treasure] = session["inventory_found"].get(treasure, 0) + 1
        
        result = {
            "action": "explore",
            "result": "treasure_found",
            "treasure": treasure,
            "message": f"You found {treasure}!"
        }
    else:  # 20% chance of nothing
        result = {
            "action": "explore",
            "result": "nothing",
            "message": "You found nothing of interest."
        }
    
    # Update session
    await db.execute(
        "UPDATE players SET current_gate_session = ? WHERE id = ?",
        (json.dumps(session), player_id)
    )
    await db.commit()
    
    result["session"] = session
    return result

async def handle_fight_action(session, gate, player_id, db):
    """Handle combat action"""
    if session["status"] != "combat" or "current_monster" not in session:
        raise HTTPException(status_code=400, detail="Not in combat")
    
    # Get player stats
    cursor = await db.execute(
        "SELECT attack, defense, level FROM players WHERE id = ?",
        (player_id,)
    )
    result = await cursor.fetchone()
    player_attack = result[0] or 10
    player_defense = result[1] or 10
    player_level = result[2] or 1
    
    monster = session["current_monster"]
    
    # Player attacks monster
    damage_to_monster = max(1, player_attack - monster["defense"] // 2)
    monster["current_hp"] -= damage_to_monster
    
    combat_log = [f"You deal {damage_to_monster} damage to {monster['name']}"]
    
    if monster["current_hp"] <= 0:
        # Monster defeated
        session["monsters_defeated"] += 1
        session["status"] = "exploring"
        del session["current_monster"]
        
        # Rewards
        xp_gained = random.randint(50, 150)
        gold_gained = random.randint(100, 500)
        
        combat_log.append(f"{monster['name']} defeated!")
        combat_log.append(f"Gained {xp_gained} XP and {gold_gained} gold")
        
        # Update player XP and gold
        await db.execute(
            "UPDATE players SET xp = xp + ?, gold = gold + ? WHERE id = ?",
            (xp_gained, gold_gained, player_id)
        )
        
        result = {
            "action": "fight",
            "result": "victory",
            "combat_log": combat_log,
            "rewards": {"xp": xp_gained, "gold": gold_gained}
        }
    else:
        # Monster attacks back
        damage_to_player = max(1, monster["attack"] - player_defense // 2)
        session["hp"] -= damage_to_player
        
        combat_log.append(f"{monster['name']} deals {damage_to_player} damage to you")
        
        if session["hp"] <= 0:
            # Player defeated - exit gate
            session = {}
            combat_log.append("You were defeated and forced to exit the gate!")
            
            result = {
                "action": "fight",
                "result": "defeat",
                "combat_log": combat_log,
                "message": "You were defeated!"
            }
        else:
            result = {
                "action": "fight",
                "result": "continue_combat",
                "combat_log": combat_log,
                "monster": monster
            }
    
    # Update session
    await db.execute(
        "UPDATE players SET current_gate_session = ? WHERE id = ?",
        (json.dumps(session), player_id)
    )
    await db.commit()
    
    result["session"] = session
    return result

async def handle_rest_action(session, gate, player_id, db):
    """Handle rest action"""
    # Restore some HP and MP
    hp_restored = min(20, 100 - session["hp"])
    mp_restored = min(15, 100 - session["mp"])
    
    session["hp"] = min(100, session["hp"] + hp_restored)
    session["mp"] = min(100, session["mp"] + mp_restored)
    
    await db.execute(
        "UPDATE players SET current_gate_session = ? WHERE id = ?",
        (json.dumps(session), player_id)
    )
    await db.commit()
    
    return {
        "action": "rest",
        "result": "rested",
        "hp_restored": hp_restored,
        "mp_restored": mp_restored,
        "message": f"You rest and recover {hp_restored} HP and {mp_restored} MP",
        "session": session
    }

async def handle_exit_action(session, gate, player_id, db):
    """Handle exit gate action"""
    # Calculate final rewards
    total_rewards = {
        "gold": session.get("monsters_defeated", 0) * 200,
        "xp": session.get("monsters_defeated", 0) * 100,
        "items": session.get("inventory_found", {})
    }
    
    # Give rewards to player
    if total_rewards["gold"] > 0:
        await db.execute(
            "UPDATE players SET gold = gold + ?, xp = xp + ? WHERE id = ?",
            (total_rewards["gold"], total_rewards["xp"], player_id)
        )
    
    # Add items to inventory
    if total_rewards["items"]:
        cursor = await db.execute("SELECT inventory FROM players WHERE id = ?", (player_id,))
        result = await cursor.fetchone()
        inventory = json.loads(result[0] or '{}')
        
        for item, quantity in total_rewards["items"].items():
            inventory[item] = inventory.get(item, 0) + quantity
        
        await db.execute(
            "UPDATE players SET inventory = ? WHERE id = ?",
            (json.dumps(inventory), player_id)
        )
    
    # Clear session
    await db.execute(
        "UPDATE players SET current_gate_session = ? WHERE id = ?",
        (json.dumps({}), player_id)
    )
    await db.commit()
    
    return {
        "action": "exit",
        "result": "exited",
        "message": f"You exit {gate['name']}",
        "final_rewards": total_rewards,
        "monsters_defeated": session.get("monsters_defeated", 0),
        "floors_cleared": session.get("floors_cleared", 0)
    }
