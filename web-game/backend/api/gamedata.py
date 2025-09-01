from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import os
from services.auth_service import get_current_user
from services.database_service import get_db_connection

router = APIRouter(prefix="/gamedata", tags=["gamedata"])

# Game data models
class Hunter(BaseModel):
    id: str
    name: str
    rarity: str
    classType: str
    type: str
    image: str
    description: str
    health: int
    attack: int
    defense: int
    speed: int
    mp: int
    age: int
    gender: str
    country: str
    weapon: str
    guild: str
    rank: str

class Item(BaseModel):
    id: str
    name: str
    type: str
    rarity: str
    description: str
    attack: Optional[int] = None
    defense: Optional[int] = None
    health: Optional[int] = None
    mp: Optional[int] = None
    speed: Optional[int] = None
    image: Optional[str] = None

def load_hunters_data():
    """Load all hunters from JSON file"""
    hunters_file = os.path.join("data", "hunters.json")
    if os.path.exists(hunters_file):
        with open(hunters_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_items_data():
    """Load all items from JSON file"""
    items_file = os.path.join("data", "items.json")
    if os.path.exists(items_file):
        with open(items_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_images_data():
    """Load image mappings from JSON file"""
    images_file = os.path.join("data", "images.json")
    if os.path.exists(images_file):
        with open(images_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@router.get("/hunters")
async def get_all_hunters():
    """Get all available hunters"""
    hunters = load_hunters_data()
    return {"hunters": hunters, "total": len(hunters)}

@router.get("/hunters/{hunter_id}")
async def get_hunter(hunter_id: str):
    """Get specific hunter by ID"""
    hunters = load_hunters_data()
    hunter = next((h for h in hunters if h["id"] == hunter_id), None)
    
    if not hunter:
        raise HTTPException(status_code=404, detail="Hunter not found")
    
    return {"hunter": hunter}

@router.get("/hunters/rarity/{rarity}")
async def get_hunters_by_rarity(rarity: str):
    """Get hunters by rarity (SSR, SR, R, N)"""
    hunters = load_hunters_data()
    filtered_hunters = [h for h in hunters if h["rarity"].upper() == rarity.upper()]
    
    return {"hunters": filtered_hunters, "total": len(filtered_hunters)}

@router.get("/hunters/class/{class_type}")
async def get_hunters_by_class(class_type: str):
    """Get hunters by class type"""
    hunters = load_hunters_data()
    filtered_hunters = [h for h in hunters if h["classType"].lower() == class_type.lower()]
    
    return {"hunters": filtered_hunters, "total": len(filtered_hunters)}

@router.get("/items")
async def get_all_items():
    """Get all available items"""
    items = load_items_data()
    return {"items": items, "total": len(items)}

@router.get("/items/{item_id}")
async def get_item(item_id: str):
    """Get specific item by ID"""
    items = load_items_data()
    item = next((i for i in items if i.get("id") == item_id), None)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"item": item}

@router.get("/items/type/{item_type}")
async def get_items_by_type(item_type: str):
    """Get items by type (weapon, armor, consumable, etc.)"""
    items = load_items_data()
    filtered_items = [i for i in items if i.get("type", "").lower() == item_type.lower()]
    
    return {"items": filtered_items, "total": len(filtered_items)}

@router.get("/images")
async def get_image_mappings():
    """Get all image URL mappings"""
    images = load_images_data()
    return {"images": images}

@router.get("/stats")
async def get_game_stats():
    """Get overall game statistics"""
    hunters = load_hunters_data()
    items = load_items_data()
    
    # Calculate hunter statistics
    hunter_stats = {
        "total_hunters": len(hunters),
        "by_rarity": {},
        "by_class": {},
        "by_type": {},
        "by_rank": {}
    }
    
    for hunter in hunters:
        # Rarity stats
        rarity = hunter.get("rarity", "Unknown")
        hunter_stats["by_rarity"][rarity] = hunter_stats["by_rarity"].get(rarity, 0) + 1
        
        # Class stats
        class_type = hunter.get("classType", "Unknown")
        hunter_stats["by_class"][class_type] = hunter_stats["by_class"].get(class_type, 0) + 1
        
        # Type stats
        hunter_type = hunter.get("type", "Unknown")
        hunter_stats["by_type"][hunter_type] = hunter_stats["by_type"].get(hunter_type, 0) + 1
        
        # Rank stats
        rank = hunter.get("rank", "Unknown")
        hunter_stats["by_rank"][rank] = hunter_stats["by_rank"].get(rank, 0) + 1
    
    # Calculate item statistics
    item_stats = {
        "total_items": len(items),
        "by_type": {},
        "by_rarity": {}
    }
    
    for item in items:
        # Type stats
        item_type = item.get("type", "Unknown")
        item_stats["by_type"][item_type] = item_stats["by_type"].get(item_type, 0) + 1
        
        # Rarity stats
        rarity = item.get("rarity", "Unknown")
        item_stats["by_rarity"][rarity] = item_stats["by_rarity"].get(rarity, 0) + 1
    
    return {
        "hunters": hunter_stats,
        "items": item_stats
    }

@router.get("/gacha-rates")
async def get_gacha_rates():
    """Get gacha pull rates based on actual hunter data"""
    hunters = load_hunters_data()
    
    # Count hunters by rarity
    rarity_counts = {}
    for hunter in hunters:
        rarity = hunter.get("rarity", "N")
        rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
    
    # Calculate rates (these match your Discord bot rates)
    rates = {
        "SSR": {"rate": 1.0, "count": rarity_counts.get("SSR", 0)},
        "SR": {"rate": 5.0, "count": rarity_counts.get("SR", 0)},
        "R": {"rate": 20.0, "count": rarity_counts.get("R", 0)},
        "N": {"rate": 74.0, "count": rarity_counts.get("N", 0)}
    }
    
    return {"rates": rates, "total_hunters": len(hunters)}

@router.get("/player-collection")
async def get_player_collection(current_user: dict = Depends(get_current_user)):
    """Get player's collection progress"""
    db = await get_db_connection()
    cursor = await db.execute(
        "SELECT hunters, inventory FROM players WHERE id = ?",
        (current_user["player_id"],)
    )
    result = await cursor.fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    player_hunters = json.loads(result[0] or '{}')
    player_inventory = json.loads(result[1] or '{}')
        
    # Load all game data
    all_hunters = load_hunters_data()
    all_items = load_items_data()
        
    # Calculate collection progress
    collection_stats = {
        "hunters": {
            "owned": len(player_hunters),
            "total": len(all_hunters),
            "percentage": round((len(player_hunters) / len(all_hunters)) * 100, 1) if all_hunters else 0,
            "by_rarity": {}
        },
        "items": {
            "owned": len([item for item, qty in player_inventory.items() if qty > 0]),
            "total": len(all_items),
            "percentage": 0,
            "by_type": {}
        }
    }
        
    # Hunter collection by rarity
    for hunter in all_hunters:
        rarity = hunter.get("rarity", "N")
        if rarity not in collection_stats["hunters"]["by_rarity"]:
            collection_stats["hunters"]["by_rarity"][rarity] = {"owned": 0, "total": 0}
            
        collection_stats["hunters"]["by_rarity"][rarity]["total"] += 1
        if hunter["id"] in player_hunters:
            collection_stats["hunters"]["by_rarity"][rarity]["owned"] += 1
        
    # Calculate percentages for each rarity
    for rarity_data in collection_stats["hunters"]["by_rarity"].values():
        if rarity_data["total"] > 0:
            rarity_data["percentage"] = round((rarity_data["owned"] / rarity_data["total"]) * 100, 1)
        else:
            rarity_data["percentage"] = 0
        
    # Item collection by type
    owned_items = [item for item, qty in player_inventory.items() if qty > 0]
    for item in all_items:
        item_type = item.get("type", "Unknown")
        if item_type not in collection_stats["items"]["by_type"]:
            collection_stats["items"]["by_type"][item_type] = {"owned": 0, "total": 0}
            
        collection_stats["items"]["by_type"][item_type]["total"] += 1
        if item.get("id") in owned_items:
            collection_stats["items"]["by_type"][item_type]["owned"] += 1
        
    # Calculate item collection percentage
    if all_items:
        collection_stats["items"]["percentage"] = round((len(owned_items) / len(all_items)) * 100, 1)
        
    return {"collection": collection_stats}

@router.get("/search")
async def search_game_data(query: str, type: str = "all"):
    """Search hunters and items by name or description"""
    results = {"hunters": [], "items": []}
    query_lower = query.lower()
    
    if type in ["all", "hunters"]:
        hunters = load_hunters_data()
        for hunter in hunters:
            if (query_lower in hunter.get("name", "").lower() or 
                query_lower in hunter.get("description", "").lower() or
                query_lower in hunter.get("classType", "").lower() or
                query_lower in hunter.get("type", "").lower()):
                results["hunters"].append(hunter)
    
    if type in ["all", "items"]:
        items = load_items_data()
        for item in items:
            if (query_lower in item.get("name", "").lower() or 
                query_lower in item.get("description", "").lower() or
                query_lower in item.get("type", "").lower()):
                results["items"].append(item)
    
    return {
        "query": query,
        "results": results,
        "total_found": len(results["hunters"]) + len(results["items"])
    }

@router.get("/random-hunter")
async def get_random_hunter(rarity: Optional[str] = None):
    """Get a random hunter, optionally filtered by rarity"""
    import random
    
    hunters = load_hunters_data()
    
    if rarity:
        hunters = [h for h in hunters if h.get("rarity", "").upper() == rarity.upper()]
    
    if not hunters:
        raise HTTPException(status_code=404, detail="No hunters found")
    
    random_hunter = random.choice(hunters)
    return {"hunter": random_hunter}

@router.get("/featured")
async def get_featured_content():
    """Get featured hunters and items (rotates daily)"""
    import random
    import time
    
    # Use date as seed for consistent daily rotation
    random.seed(int(time.time() // 86400))
    
    hunters = load_hunters_data()
    items = load_items_data()
    
    # Select featured content
    featured_hunters = random.sample(hunters, min(5, len(hunters)))
    featured_items = random.sample(items, min(5, len(items)))
    
    return {
        "featured_hunters": featured_hunters,
        "featured_items": featured_items,
        "rotation_date": time.strftime("%Y-%m-%d")
    }
