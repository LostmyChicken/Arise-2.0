from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import random

market_router = APIRouter()

class MarketItem(BaseModel):
    id: str
    name: str
    type: str
    rarity: str
    price: int
    seller: str
    description: str
    stats: Dict[str, Any]

@market_router.get("/items")
async def get_market_items():
    """Get items available in the market"""
    return {
        "items": [
            {
                "id": "sword_001",
                "name": "Demon King's Blade",
                "type": "weapon",
                "rarity": "legendary",
                "price": 50000,
                "seller": "Shadow Merchant",
                "description": "A blade forged in the depths of hell",
                "stats": {"attack": 200, "critical": 15},
                "image": "/images/demon_blade.png"
            },
            {
                "id": "armor_001", 
                "name": "Dragon Scale Armor",
                "type": "armor",
                "rarity": "epic",
                "price": 35000,
                "seller": "Ancient Trader",
                "description": "Armor made from ancient dragon scales",
                "stats": {"defense": 150, "hp": 300},
                "image": "/images/dragon_armor.png"
            },
            {
                "id": "potion_001",
                "name": "Greater Health Potion",
                "type": "consumable",
                "rarity": "rare",
                "price": 500,
                "seller": "Alchemist Guild",
                "description": "Restores 1000 HP instantly",
                "stats": {"heal": 1000},
                "image": "/images/health_potion.png"
            }
        ],
        "player_gold": 125000
    }

@market_router.post("/buy")
async def buy_item(item_data: dict):
    """Buy an item from the market"""
    item_id = item_data.get("item_id")
    return {
        "success": True,
        "message": f"Successfully purchased item {item_id}",
        "remaining_gold": 120000,
        "item_added": True
    }

@market_router.post("/sell")
async def sell_item(item_data: dict):
    """Sell an item to the market"""
    item_id = item_data.get("item_id")
    price = item_data.get("price", 1000)
    return {
        "success": True,
        "message": f"Successfully sold item {item_id} for {price} gold",
        "gold_earned": price
    }
