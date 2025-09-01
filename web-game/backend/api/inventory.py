from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

inventory_router = APIRouter()

@inventory_router.get("/items")
async def get_inventory_items():
    """Get player inventory items"""
    return {
        "inventory": [
            {
                "id": "weapon_001",
                "name": "Shadow Monarch's Blade",
                "type": "weapon",
                "rarity": "legendary",
                "quantity": 1,
                "equipped": True,
                "stats": {"attack": 500, "critical": 25},
                "description": "The legendary blade of the Shadow Monarch",
                "image": "/images/shadow_blade.png"
            },
            {
                "id": "armor_001",
                "name": "Shadow Monarch's Coat",
                "type": "armor",
                "rarity": "legendary", 
                "quantity": 1,
                "equipped": True,
                "stats": {"defense": 300, "hp": 500},
                "description": "The protective coat of the Shadow Monarch",
                "image": "/images/shadow_coat.png"
            },
            {
                "id": "potion_hp",
                "name": "Health Potion",
                "type": "consumable",
                "rarity": "common",
                "quantity": 25,
                "equipped": False,
                "stats": {"heal": 500},
                "description": "Restores 500 HP",
                "image": "/images/health_potion.png"
            },
            {
                "id": "potion_mp",
                "name": "Mana Potion", 
                "type": "consumable",
                "rarity": "common",
                "quantity": 15,
                "equipped": False,
                "stats": {"mana": 300},
                "description": "Restores 300 MP",
                "image": "/images/mana_potion.png"
            }
        ],
        "capacity": 100,
        "used_slots": 42
    }

@inventory_router.post("/equip")
async def equip_item(item_data: dict):
    """Equip an item"""
    item_id = item_data.get("item_id")
    return {
        "success": True,
        "item_equipped": item_id,
        "stats_changed": {
            "attack": 50,
            "defense": 25
        },
        "message": f"Successfully equipped {item_id}!"
    }

@inventory_router.post("/use")
async def use_item(item_data: dict):
    """Use a consumable item"""
    item_id = item_data.get("item_id")
    return {
        "success": True,
        "item_used": item_id,
        "effect": "Restored 500 HP",
        "remaining_quantity": 24,
        "message": f"Successfully used {item_id}!"
    }
