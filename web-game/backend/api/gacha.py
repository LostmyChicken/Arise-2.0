from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
import random
import json
import os
from pathlib import Path

from services.player_service import player_service
from services.auth_service import get_current_user

router = APIRouter()

class GachaPull(BaseModel):
    pull_type: str  # single, ten
    currency: str   # gems, tickets

# Load hunters data
def load_hunters_data():
    """Load hunters data from JSON file"""
    try:
        hunters_path = Path("backend/data/hunters.json")
        if hunters_path.exists():
            with open(hunters_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading hunters data: {e}")

    # Fallback mock data
    return [
        {
            "id": "sung_jinwoo",
            "name": "Sung Jin-Woo",
            "rarity": "SSR",
            "classType": "Dark",
            "type": "Assassin",
            "image": "https://files.catbox.moe/example.jpg",
            "health": 2500,
            "attack": 1200,
            "defense": 800
        }
    ]

HUNTERS_DATA = load_hunters_data()

@router.post("/pull")
async def gacha_pull(pull_data: GachaPull, current_user: dict = Depends(get_current_user)):
    """Perform a gacha pull"""
    try:
        player_id = current_user["player_id"]
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        # Determine number of pulls and cost
        num_pulls = 10 if pull_data.pull_type == "ten" else 1

        # Define costs (matching your Discord bot)
        costs = {
            'single': {'gems': 300, 'tickets': 1},
            'ten': {'gems': 2700, 'tickets': 10}
        }

        cost = costs[pull_data.pull_type][pull_data.currency]

        # Check if player has enough resources
        if pull_data.currency == 'gems':
            current_amount = player.get('diamond', 0)  # Backend uses 'diamond'
        else:  # tickets
            current_amount = player.get('ticket', 0)   # Backend uses 'ticket'

        if current_amount < cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient {pull_data.currency}"
            )
        
        # Perform pulls (always pull hunters for now)
        results = []
        for _ in range(num_pulls):
            result = await pull_hunter(player_id)
            results.append(result)
        
        # Deduct cost from player resources
        new_amount = current_amount - cost
        field_name = 'diamond' if pull_data.currency == 'gems' else 'ticket'

        # Update player resources
        update_data = {field_name: new_amount}
        await player_service.update_player(player_id, update_data)
        
        # Add items to player inventory
        for result in results:
            if result["type"] == "hunter":
                hunters = player.get("hunters", {})
                hunter_id = result["id"]
                if hunter_id in hunters:
                    hunters[hunter_id]["copies"] = hunters[hunter_id].get("copies", 1) + 1
                else:
                    hunters[hunter_id] = {
                        "id": hunter_id,
                        "name": result["name"],
                        "rarity": result["rarity"],
                        "copies": 1,
                        "level": 1
                    }
                await player_service.update_player(player_id, {"hunters": hunters})
            
            elif result["type"] == "weapon" or result["type"] == "item":
                await player_service.add_item(player_id, result["id"], 1)
        
        # Return format expected by frontend
        if pull_data.pull_type == "single":
            return {
                "result": results[0],
                "remaining_currency": new_amount
            }
        else:
            return {
                "results": results,
                "remaining_currency": new_amount
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform gacha pull: {str(e)}"
        )

@router.get("/rates")
async def get_gacha_rates():
    """Get gacha pull rates"""
    return {
        "rates": {
            "common": 60,
            "rare": 25,
            "epic": 12,
            "legendary": 3
        },
        "pity_system": {
            "legendary_pity": 100,
            "epic_pity": 20
        }
    }

@router.get("/history/{player_id}")
async def get_gacha_history(player_id: str, limit: int = 20):
    """Get player's gacha history"""
    try:
        # This would be stored in a gacha_history table in a real implementation
        # For now, return empty history
        return {
            "history": [],
            "total_pulls": 0,
            "pity_counter": 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gacha history: {str(e)}"
        )

# Helper functions
async def pull_hunter(player_id: str) -> Dict[str, Any]:
    """Pull a random hunter"""
    
    # Determine rarity based on rates (matching Discord bot)
    rand = random.random()
    if rand < 0.03:  # 3% Legendary (SSR)
        target_rarity = "SSR"
    elif rand < 0.15:  # 12% Epic (SR)
        target_rarity = "SR"
    elif rand < 0.40:  # 25% Rare (R)
        target_rarity = "R"
    else:  # 60% Common (N)
        target_rarity = "N"

    # Filter hunters by rarity from real data
    available_hunters = [h for h in HUNTERS_DATA if h.get('rarity', 'N') == target_rarity]
    if not available_hunters:
        # Fallback to any hunter if no hunters of target rarity
        available_hunters = HUNTERS_DATA

    # Select random hunter
    hunter = random.choice(available_hunters)
    
    return {
        "type": "hunter",
        "id": hunter.get("id", f"hunter_{random.randint(1, 100)}"),
        "name": hunter.get("name", f"Hunter {random.randint(1, 100)}"),
        "rarity": hunter.get("rarity", target_rarity),
        "classType": hunter.get("classType", "Dark"),
        "hunterType": hunter.get("type", "Assassin"),
        "image": hunter.get("image", "https://via.placeholder.com/150"),
        "health": hunter.get("health", 1000),
        "attack": hunter.get("attack", 500),
        "defense": hunter.get("defense", 300),
        "is_new": True  # TODO: Check if player already has this hunter
    }

async def pull_weapon(player_id: str) -> Dict[str, Any]:
    """Pull a random weapon"""
    
    # Sample weapon pool
    weapons = {
        "common": [
            {"id": "iron_sword", "name": "Iron Sword", "rarity": "Common"},
            {"id": "wooden_bow", "name": "Wooden Bow", "rarity": "Common"},
        ],
        "rare": [
            {"id": "steel_sword", "name": "Steel Sword", "rarity": "Rare"},
            {"id": "magic_staff", "name": "Magic Staff", "rarity": "Rare"},
        ],
        "epic": [
            {"id": "demon_sword", "name": "Demon Sword", "rarity": "Epic"},
            {"id": "dragon_bow", "name": "Dragon Bow", "rarity": "Epic"},
        ],
        "legendary": [
            {"id": "shadow_blade", "name": "Shadow Blade", "rarity": "Legendary"},
            {"id": "rulers_authority", "name": "Ruler's Authority", "rarity": "Legendary"},
        ]
    }
    
    rarity = determine_rarity()
    weapon = random.choice(weapons[rarity])
    
    return {
        "type": "weapon",
        "id": weapon["id"],
        "name": weapon["name"],
        "rarity": weapon["rarity"],
        "is_new": True
    }

async def pull_mixed(player_id: str) -> Dict[str, Any]:
    """Pull either a hunter or weapon"""
    if random.random() < 0.6:  # 60% chance for hunter
        return await pull_hunter(player_id)
    else:  # 40% chance for weapon
        return await pull_weapon(player_id)

def determine_rarity() -> str:
    """Determine rarity based on rates"""
    rand = random.random() * 100
    
    if rand < 3:  # 3%
        return "legendary"
    elif rand < 15:  # 12%
        return "epic"
    elif rand < 40:  # 25%
        return "rare"
    else:  # 60%
        return "common"

# Export router
gacha_router = router