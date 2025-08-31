from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List
import random
import json

from services.player_service import player_service

router = APIRouter()

class GachaPull(BaseModel):
    pull_type: str  # single, multi
    gacha_type: str  # hunter, weapon, mixed

@router.post("/pull/{player_id}")
async def gacha_pull(player_id: str, pull_data: GachaPull):
    """Perform a gacha pull"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        # Determine number of pulls
        num_pulls = 10 if pull_data.pull_type == "multi" else 1
        ticket_cost = 10 if pull_data.pull_type == "multi" else 1
        
        # Check if player has enough tickets
        if player["ticket"] < ticket_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough tickets"
            )
        
        # Perform pulls
        results = []
        for _ in range(num_pulls):
            if pull_data.gacha_type == "hunter":
                result = await pull_hunter(player_id)
            elif pull_data.gacha_type == "weapon":
                result = await pull_weapon(player_id)
            else:  # mixed
                result = await pull_mixed(player_id)
            
            results.append(result)
        
        # Deduct tickets
        await player_service.update_player(player_id, {
            "ticket": player["ticket"] - ticket_cost
        })
        
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
        
        return {
            "results": results,
            "tickets_spent": ticket_cost,
            "remaining_tickets": player["ticket"] - ticket_cost
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
    
    # Sample hunter pool
    hunters = {
        "common": [
            {"id": "basic_hunter", "name": "Basic Hunter", "rarity": "Common"},
            {"id": "trainee_hunter", "name": "Trainee Hunter", "rarity": "Common"},
        ],
        "rare": [
            {"id": "skilled_hunter", "name": "Skilled Hunter", "rarity": "Rare"},
            {"id": "veteran_hunter", "name": "Veteran Hunter", "rarity": "Rare"},
        ],
        "epic": [
            {"id": "cha_haein", "name": "Cha Hae-In", "rarity": "Epic"},
            {"id": "baek_yoonho", "name": "Baek Yoon-Ho", "rarity": "Epic"},
        ],
        "legendary": [
            {"id": "sung_jinwoo", "name": "Sung Jin-Woo", "rarity": "Legendary"},
            {"id": "thomas_andre", "name": "Thomas Andre", "rarity": "Legendary"},
        ]
    }
    
    rarity = determine_rarity()
    hunter = random.choice(hunters[rarity])
    
    return {
        "type": "hunter",
        "id": hunter["id"],
        "name": hunter["name"],
        "rarity": hunter["rarity"],
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