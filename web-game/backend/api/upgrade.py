from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/upgrade", tags=["upgrade"])

# Upgrade models
class UpgradeRequest(BaseModel):
    item_type: str  # "hunter" or "weapon"
    item_id: str
    upgrade_type: str  # "level", "limit_break", "awaken"

class SacrificeRequest(BaseModel):
    sacrifice_items: List[Dict[str, Any]]
    target_item_id: str
    target_item_type: str

# Upgrade costs and materials
UPGRADE_COSTS = {
    "level": {
        1: {"gold": 1000, "stones": 10},
        2: {"gold": 2000, "stones": 20},
        3: {"gold": 3000, "stones": 30},
        4: {"gold": 5000, "stones": 50},
        5: {"gold": 8000, "stones": 80},
        6: {"gold": 12000, "stones": 120},
        7: {"gold": 18000, "stones": 180},
        8: {"gold": 25000, "stones": 250},
        9: {"gold": 35000, "stones": 350},
        10: {"gold": 50000, "stones": 500}
    },
    "limit_break": {
        1: {"gold": 100000, "diamonds": 50, "crystals": 10},
        2: {"gold": 200000, "diamonds": 100, "crystals": 20},
        3: {"gold": 300000, "diamonds": 150, "crystals": 30},
        4: {"gold": 500000, "diamonds": 250, "crystals": 50},
        5: {"gold": 1000000, "diamonds": 500, "crystals": 100}
    },
    "awaken": {
        1: {"gold": 500000, "diamonds": 200, "tos": 50},
        2: {"gold": 1000000, "diamonds": 400, "tos": 100},
        3: {"gold": 2000000, "diamonds": 800, "tos": 200}
    }
}

def load_hunters_data():
    """Load hunters data"""
    with open("data/hunters.json", 'r') as f:
        return json.load(f)

def load_items_data():
    """Load items data"""
    items_file = os.path.join("data", "items.json")
    if os.path.exists(items_file):
        with open(items_file, 'r') as f:
            return json.load(f)
    return []

def calculate_upgrade_stats(base_stats: Dict[str, int], level: int, limit_break: int, awaken: int) -> Dict[str, int]:
    """Calculate upgraded stats"""
    multiplier = 1.0
    
    # Level multiplier (10% per level)
    multiplier += (level - 1) * 0.1
    
    # Limit break multiplier (25% per limit break)
    multiplier += limit_break * 0.25
    
    # Awaken multiplier (50% per awaken)
    multiplier += awaken * 0.5
    
    upgraded_stats = {}
    for stat, value in base_stats.items():
        if isinstance(value, (int, float)):
            upgraded_stats[stat] = int(value * multiplier)
        else:
            upgraded_stats[stat] = value
    
    return upgraded_stats

@router.get("/costs")
async def get_upgrade_costs():
    """Get upgrade costs for all types"""
    return {"costs": UPGRADE_COSTS}

@router.get("/player-items")
async def get_player_upgradeable_items(current_user: dict = Depends(get_current_user)):
    """Get player's items that can be upgraded"""
    db = await get_db_connection()
    cursor = await db.execute(
    "SELECT hunters, inventory, equipped FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()

    if not result:
    raise HTTPException(status_code=404, detail="Player not found")

    hunters = json.loads(result[0] or '{}')
    inventory = json.loads(result[1] or '{}')
    equipped = json.loads(result[2] or '{}')

    # Load game data
    hunters_data = load_hunters_data()
    items_data = load_items_data()

    upgradeable_items = {
    "hunters": [],
    "weapons": []
    }

    # Process hunters
    for hunter_id, hunter_info in hunters.items():
    hunter_data = next((h for h in hunters_data if h["id"] == hunter_id), None)
    if hunter_data:
    level = hunter_info.get("level", 1)
    limit_break = hunter_info.get("limit_break", 0)
    awaken = hunter_info.get("awaken", 0)

    base_stats = {
    "health": hunter_data.get("health", 100),
    "attack": hunter_data.get("attack", 10),
    "defense": hunter_data.get("defense", 10)
    }

    current_stats = calculate_upgrade_stats(base_stats, level, limit_break, awaken)

    upgradeable_items["hunters"].append({
    "id": hunter_id,
    "name": hunter_data["name"],
    "rarity": hunter_data["rarity"],
    "level": level,
    "limit_break": limit_break,
    "awaken": awaken,
    "base_stats": base_stats,
    "current_stats": current_stats,
    "can_level_up": level < 10,
    "can_limit_break": limit_break < 5 and level >= 10,
    "can_awaken": awaken < 3 and limit_break >= 3
    })

    # Process weapons (from inventory)
    for item_id, quantity in inventory.items():
    if quantity > 0:
    item_data = next((i for i in items_data if i.get("id") == item_id), None)
    if item_data and item_data.get("type") == "weapon":
    # Get upgrade info (stored separately or default)
    level = 1  # Default level
    limit_break = 0
    awaken = 0

    base_stats = {
    "attack": item_data.get("attack", 10),
    "defense": item_data.get("defense", 5)
    }

    current_stats = calculate_upgrade_stats(base_stats, level, limit_break, awaken)

    upgradeable_items["weapons"].append({
    "id": item_id,
    "name": item_data["name"],
    "rarity": item_data.get("rarity", "Common"),
    "level": level,
    "limit_break": limit_break,
    "awaken": awaken,
    "base_stats": base_stats,
    "current_stats": current_stats,
    "quantity": quantity,
    "can_level_up": level < 10,
    "can_limit_break": limit_break < 5 and level >= 10,
    "can_awaken": awaken < 3 and limit_break >= 3
    })

    return upgradeable_items

@router.post("/upgrade-item")
async def upgrade_item(request: UpgradeRequest, current_user: dict = Depends(get_current_user)):
    """Upgrade an item or hunter"""
    db = await get_db_connection()
    # Get player data
    cursor = await db.execute(
    "SELECT hunters, inventory, gold, diamonds, stones, crystals, tos FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    hunters = json.loads(result[0] or '{}')
    inventory = json.loads(result[1] or '{}')
    gold = result[2] or 0
    diamonds = result[3] or 0
    stones = result[4] or 0
    crystals = result[5] or 0
    tos = result[6] or 0
        
    # Find the item to upgrade
    if request.item_type == "hunter":
    if request.item_id not in hunters:
    raise HTTPException(status_code=404, detail="Hunter not found")
            
    item_info = hunters[request.item_id]
    else:
    if request.item_id not in inventory or inventory[request.item_id] <= 0:
    raise HTTPException(status_code=404, detail="Item not found")
            
    # For weapons, we need to track upgrade info separately
    item_info = {"level": 1, "limit_break": 0, "awaken": 0}
        
    current_level = item_info.get("level", 1)
    current_limit_break = item_info.get("limit_break", 0)
    current_awaken = item_info.get("awaken", 0)
        
    # Determine upgrade costs
    if request.upgrade_type == "level":
    if current_level >= 10:
    raise HTTPException(status_code=400, detail="Already at max level")
    costs = UPGRADE_COSTS["level"][current_level + 1]
            
    elif request.upgrade_type == "limit_break":
    if current_limit_break >= 5:
    raise HTTPException(status_code=400, detail="Already at max limit break")
    if current_level < 10:
    raise HTTPException(status_code=400, detail="Must be level 10 to limit break")
    costs = UPGRADE_COSTS["limit_break"][current_limit_break + 1]
            
    elif request.upgrade_type == "awaken":
    if current_awaken >= 3:
    raise HTTPException(status_code=400, detail="Already at max awaken")
    if current_limit_break < 3:
    raise HTTPException(status_code=400, detail="Must be limit break 3+ to awaken")
    costs = UPGRADE_COSTS["awaken"][current_awaken + 1]
    else:
    raise HTTPException(status_code=400, detail="Invalid upgrade type")
        
    # Check if player has enough resources
    if costs.get("gold", 0) > gold:
    raise HTTPException(status_code=400, detail="Not enough gold")
    if costs.get("diamonds", 0) > diamonds:
    raise HTTPException(status_code=400, detail="Not enough diamonds")
    if costs.get("stones", 0) > stones:
    raise HTTPException(status_code=400, detail="Not enough stones")
    if costs.get("crystals", 0) > crystals:
    raise HTTPException(status_code=400, detail="Not enough crystals")
    if costs.get("tos", 0) > tos:
    raise HTTPException(status_code=400, detail="Not enough shadow traces")
        
    # Perform the upgrade
    if request.upgrade_type == "level":
    item_info["level"] = current_level + 1
    elif request.upgrade_type == "limit_break":
    item_info["limit_break"] = current_limit_break + 1
    elif request.upgrade_type == "awaken":
    item_info["awaken"] = current_awaken + 1
        
    # Deduct costs
    new_gold = gold - costs.get("gold", 0)
    new_diamonds = diamonds - costs.get("diamonds", 0)
    new_stones = stones - costs.get("stones", 0)
    new_crystals = crystals - costs.get("crystals", 0)
    new_tos = tos - costs.get("tos", 0)
        
    # Update database
    if request.item_type == "hunter":
    hunters[request.item_id] = item_info
    await db.execute(
    "UPDATE players SET hunters = ?, gold = ?, diamonds = ?, stones = ?, crystals = ?, tos = ? WHERE id = ?",
    (json.dumps(hunters), new_gold, new_diamonds, new_stones, new_crystals, new_tos, current_user["player_id"])
    )
    else:
    # For weapons, we'd need a separate upgrade tracking system
    # For now, just deduct resources
    await db.execute(
    "UPDATE players SET gold = ?, diamonds = ?, stones = ?, crystals = ?, tos = ? WHERE id = ?",
    (new_gold, new_diamonds, new_stones, new_crystals, new_tos, current_user["player_id"])
    )
        
    await db.commit()
        
    return {
    "message": f"Successfully upgraded {request.item_id}",
    "upgrade_type": request.upgrade_type,
    "new_level": item_info.get("level", 1),
    "new_limit_break": item_info.get("limit_break", 0),
    "new_awaken": item_info.get("awaken", 0),
    "costs_paid": costs,
    "remaining_resources": {
    "gold": new_gold,
    "diamonds": new_diamonds,
    "stones": new_stones,
    "crystals": new_crystals,
    "tos": new_tos
    }
    }

@router.post("/sacrifice")
async def sacrifice_items(request: SacrificeRequest, current_user: dict = Depends(get_current_user)):
    """Sacrifice items to gain resources or upgrade materials"""
    db = await get_db_connection()
    cursor = await db.execute(
    "SELECT inventory, hunters, gold, stones, crystals FROM players WHERE id = ?",
    (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
    raise HTTPException(status_code=404, detail="Player not found")
        
    inventory = json.loads(result[0] or '{}')
    hunters = json.loads(result[1] or '{}')
    gold = result[2] or 0
    stones = result[3] or 0
    crystals = result[4] or 0
        
    # Calculate sacrifice rewards
    total_gold_reward = 0
    total_stones_reward = 0
    total_crystals_reward = 0
        
    for sacrifice_item in request.sacrifice_items:
    item_id = sacrifice_item["id"]
    quantity = sacrifice_item["quantity"]
    item_type = sacrifice_item["type"]
            
    if item_type == "hunter":
    if item_id not in hunters:
    raise HTTPException(status_code=400, detail=f"Hunter {item_id} not found")
    # Remove hunter and give rewards based on rarity
    del hunters[item_id]
    total_gold_reward += 50000  # Base reward for sacrificing hunter
    total_stones_reward += 100
    total_crystals_reward += 10
                
    else:  # item/weapon
    if item_id not in inventory or inventory[item_id] < quantity:
    raise HTTPException(status_code=400, detail=f"Not enough {item_id}")
                
    inventory[item_id] -= quantity
    if inventory[item_id] <= 0:
    del inventory[item_id]
                
    # Rewards based on quantity
    total_gold_reward += quantity * 1000
    total_stones_reward += quantity * 5
    total_crystals_reward += quantity * 1
        
    # Update resources
    new_gold = gold + total_gold_reward
    new_stones = stones + total_stones_reward
    new_crystals = crystals + total_crystals_reward
        
    # Update database
    await db.execute(
    "UPDATE players SET inventory = ?, hunters = ?, gold = ?, stones = ?, crystals = ? WHERE id = ?",
    (json.dumps(inventory), json.dumps(hunters), new_gold, new_stones, new_crystals, current_user["player_id"])
    )
    await db.commit()
        
    return {
    "message": "Items sacrificed successfully",
    "rewards": {
    "gold": total_gold_reward,
    "stones": total_stones_reward,
    "crystals": total_crystals_reward
    },
    "new_totals": {
    "gold": new_gold,
    "stones": new_stones,
    "crystals": new_crystals
    }
    }
