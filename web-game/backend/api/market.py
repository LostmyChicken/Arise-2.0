from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import time
import random
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/market", tags=["market"])

# Market models
class PurchaseRequest(BaseModel):
    item_id: str
    quantity: int = 1

class SellRequest(BaseModel):
    item_id: str
    quantity: int

class ShopItem(BaseModel):
    id: str
    name: str
    description: str
    type: str  # weapon, consumable, material, hunter
    rarity: str
    price: Dict[str, int]  # currency: amount
    stock: int  # -1 for unlimited
    daily_limit: int  # -1 for no limit
    requirements: Dict[str, Any] = {}  # level, achievements, etc.

# Shop inventory
SHOP_ITEMS = {
    # Basic Items
    "health_potion": {
        "id": "health_potion",
        "name": "Health Potion",
        "description": "Restores 100 HP",
        "type": "consumable",
        "rarity": "Common",
        "price": {"gold": 500},
        "stock": -1,
        "daily_limit": 10,
        "requirements": {}
    },
    "mana_potion": {
        "id": "mana_potion",
        "name": "Mana Potion",
        "description": "Restores 50 MP",
        "type": "consumable",
        "rarity": "Common",
        "price": {"gold": 300},
        "stock": -1,
        "daily_limit": 10,
        "requirements": {}
    },
    
    # Materials
    "iron_ore": {
        "id": "iron_ore",
        "name": "Iron Ore",
        "description": "Basic crafting material",
        "type": "material",
        "rarity": "Common",
        "price": {"gold": 100},
        "stock": -1,
        "daily_limit": 50,
        "requirements": {}
    },
    "magic_crystal": {
        "id": "magic_crystal",
        "name": "Magic Crystal",
        "description": "Rare crafting material",
        "type": "material",
        "rarity": "Rare",
        "price": {"gold": 2000, "crystals": 5},
        "stock": 20,
        "daily_limit": 5,
        "requirements": {"level": 10}
    },
    
    # Weapons
    "iron_sword": {
        "id": "iron_sword",
        "name": "Iron Sword",
        "description": "A sturdy iron sword (+15 Attack)",
        "type": "weapon",
        "rarity": "Common",
        "price": {"gold": 5000},
        "stock": -1,
        "daily_limit": 3,
        "requirements": {"level": 5}
    },
    "flame_blade": {
        "id": "flame_blade",
        "name": "Flame Blade",
        "description": "A sword imbued with fire magic (+25 Attack)",
        "type": "weapon",
        "rarity": "Rare",
        "price": {"gold": 15000, "crystals": 10},
        "stock": 10,
        "daily_limit": 1,
        "requirements": {"level": 15}
    },
    
    # Premium Items
    "premium_ticket": {
        "id": "premium_ticket",
        "name": "Premium Summon Ticket",
        "description": "Guaranteed SR+ hunter summon",
        "type": "consumable",
        "rarity": "Legendary",
        "price": {"diamonds": 300},
        "stock": 5,
        "daily_limit": 1,
        "requirements": {"level": 20}
    },
    
    # Boosts
    "xp_boost": {
        "id": "xp_boost",
        "name": "XP Boost (1 Hour)",
        "description": "Double XP gain for 1 hour",
        "type": "consumable",
        "rarity": "Rare",
        "price": {"diamonds": 50},
        "stock": -1,
        "daily_limit": 3,
        "requirements": {}
    },
    "gold_boost": {
        "id": "gold_boost",
        "name": "Gold Boost (1 Hour)",
        "description": "Double gold gain for 1 hour",
        "type": "consumable",
        "rarity": "Rare",
        "price": {"diamonds": 50},
        "stock": -1,
        "daily_limit": 3,
        "requirements": {}
    }
}

@router.get("/shop")
async def get_shop_items():
    """Get all shop items"""
    try:
        # Return all shop items with default availability
        available_items = []

        for item_data in SHOP_ITEMS.values():
            available_items.append({
                **item_data,
                "can_purchase": True,
                "remaining_daily": item_data["daily_limit"] if item_data["daily_limit"] > 0 else -1,
                "purchased_today": 0
            })

        return {"items": available_items}
    except Exception as e:
        print(f"Shop error: {e}")
        return {"items": []}

@router.post("/purchase")
async def purchase_item(request: PurchaseRequest, current_user: dict = Depends(get_current_user)):
    """Purchase an item from the shop"""
    if request.item_id not in SHOP_ITEMS:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = SHOP_ITEMS[request.item_id]
    
    db = await get_db_connection()
    # Get player data
    cursor = await db.execute(
        "SELECT level, gold, diamonds, crystals, stones, inventory, daily_purchases FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    player_level = result[0] or 1
    gold = result[1] or 0
    diamonds = result[2] or 0
    crystals = result[3] or 0
    stones = result[4] or 0
    inventory = json.loads(result[5] or '{}')
    daily_purchases = json.loads(result[6] or '{}')
        
    # Check requirements
    if item["requirements"].get("level", 0) > player_level:
        raise HTTPException(status_code=400, detail="Level requirement not met")
        
    # Check daily limit
    current_date = time.strftime("%Y-%m-%d")
    daily_key = f"{current_date}_{request.item_id}"
    purchased_today = daily_purchases.get(daily_key, 0)
        
    if item["daily_limit"] > 0 and purchased_today + request.quantity > item["daily_limit"]:
        raise HTTPException(status_code=400, detail="Daily purchase limit exceeded")
        
    # Check stock
    if item["stock"] > 0 and request.quantity > item["stock"]:
        raise HTTPException(status_code=400, detail="Not enough stock")
        
    # Calculate total cost
    total_cost = {}
    for currency, price in item["price"].items():
        total_cost[currency] = price * request.quantity
        
    # Check if player has enough currency
    player_currencies = {
        "gold": gold,
        "diamonds": diamonds,
        "crystals": crystals,
        "stones": stones
    }
        
    for currency, cost in total_cost.items():
        if player_currencies.get(currency, 0) < cost:
            raise HTTPException(status_code=400, detail=f"Not enough {currency}")
        
    # Deduct currency
    new_gold = gold - total_cost.get("gold", 0)
    new_diamonds = diamonds - total_cost.get("diamonds", 0)
    new_crystals = crystals - total_cost.get("crystals", 0)
    new_stones = stones - total_cost.get("stones", 0)
        
    # Add item to inventory
    inventory[request.item_id] = inventory.get(request.item_id, 0) + request.quantity
        
    # Update daily purchases
    daily_purchases[daily_key] = purchased_today + request.quantity
        
    # Update database
    await db.execute("""
        UPDATE players 
        SET gold = ?, diamonds = ?, crystals = ?, stones = ?, 
            inventory = ?, daily_purchases = ?
        WHERE id = ?
    """, (
        new_gold, new_diamonds, new_crystals, new_stones,
        json.dumps(inventory), json.dumps(daily_purchases),
        current_user["player_id"]
    ))
    await db.commit()
        
    return {
        "message": f"Successfully purchased {request.quantity}x {item['name']}",
        "item": item,
        "quantity": request.quantity,
        "total_cost": total_cost,
        "remaining_currency": {
            "gold": new_gold,
            "diamonds": new_diamonds,
            "crystals": new_crystals,
            "stones": new_stones
        }
    }

@router.post("/sell")
async def sell_item(request: SellRequest, current_user: dict = Depends(get_current_user)):
    """Sell an item from inventory"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT inventory, gold FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    inventory = json.loads(result[0] or '{}')
    gold = result[1] or 0
        
    # Check if player has the item
    if request.item_id not in inventory or inventory[request.item_id] < request.quantity:
        raise HTTPException(status_code=400, detail="Not enough items to sell")
        
    # Calculate sell price (50% of shop price, gold only)
    base_price = 100  # Default sell price
    if request.item_id in SHOP_ITEMS:
        shop_item = SHOP_ITEMS[request.item_id]
        base_price = shop_item["price"].get("gold", 100) // 2
        
    total_gold = base_price * request.quantity
        
    # Remove items from inventory
    inventory[request.item_id] -= request.quantity
    if inventory[request.item_id] <= 0:
        del inventory[request.item_id]
        
    # Add gold
    new_gold = gold + total_gold
        
    # Update database
    await db.execute(
        "UPDATE players SET inventory = ?, gold = ? WHERE id = ?",
        (json.dumps(inventory), new_gold, current_user["player_id"])
    )
    await db.commit()
        
    return {
        "message": f"Successfully sold {request.quantity}x {request.item_id}",
        "gold_earned": total_gold,
        "new_gold_total": new_gold
    }

@router.get("/daily-deals")
async def get_daily_deals():
    """Get special daily deals with discounts"""
    # Generate random daily deals
    random.seed(int(time.time() // 86400))  # Same deals for the whole day
    
    deal_items = random.sample(list(SHOP_ITEMS.keys()), 3)
    deals = []
    
    for item_id in deal_items:
        item = SHOP_ITEMS[item_id].copy()
        discount = random.randint(20, 50)  # 20-50% discount
        
        # Apply discount to prices
        discounted_price = {}
        for currency, price in item["price"].items():
            discounted_price[currency] = int(price * (100 - discount) / 100)
        
        deals.append({
            **item,
            "original_price": item["price"],
            "discounted_price": discounted_price,
            "discount_percent": discount
        })
    
    return {"deals": deals}

@router.get("/player-sales")
async def get_player_sales(current_user: dict = Depends(get_current_user)):
    """Get items that other players are selling (player marketplace)"""
    # This would be a more complex system in production
    # For now, return empty list
    return {"sales": [], "message": "Player marketplace coming soon!"}

@router.get("/purchase-history")
async def get_purchase_history(current_user: dict = Depends(get_current_user)):
    """Get player's purchase history"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT daily_purchases FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    daily_purchases = json.loads(result[0] or '{}')
        
    # Format purchase history
    history = []
    for key, quantity in daily_purchases.items():
        if "_" in key:
            date, item_id = key.split("_", 1)
            history.append({
                "date": date,
                "item_id": item_id,
                "quantity": quantity,
                "item_name": SHOP_ITEMS.get(item_id, {}).get("name", item_id)
            })
        
    # Sort by date (most recent first)
    history.sort(key=lambda x: x["date"], reverse=True)
        
    return {"history": history[:50]}  # Last 50 purchases
