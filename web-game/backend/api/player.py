from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time

from services.player_service import player_service
from services.database_service import update_player_status
from services.auth_service import get_current_user

router = APIRouter()

class StatUpgrade(BaseModel):
    stat: str  # attack, defense, hp, mp, precision
    points: int

class ItemEquip(BaseModel):
    slot: str
    item_id: Optional[str] = None

@router.get("/profile")
async def get_current_player_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile data"""
    try:
        player = await player_service.get_player(current_user["player_id"])
        if not player:
            # Create player if doesn't exist
            print(f"🔧 Creating missing player profile for {current_user['player_id']}")
            player = await player_service.create_new_player(
                current_user["player_id"],
                current_user["username"]
            )
            # Refresh player data from database after creation
            player = await player_service.get_player(current_user["player_id"]) or player

        # Return comprehensive profile data
        profile = {
            "id": player["id"],
            "username": player.get("username", current_user["username"]),
            "level": player.get("level", 1),
            "xp": player.get("xp", 0),
            "stats": {
                "attack": player.get("attack", 15),
                "defense": player.get("defense", 12),
                "hp": player.get("hp", 150),
                "mp": player.get("mp", 75),
                "precision": player.get("precision", 10)
            },
            "resources": {
                "gold": player.get("gold", 10000),
                "diamonds": player.get("diamond", 100),  # Map to frontend naming
                "stones": player.get("stone", 50),       # Map to frontend naming
                "tickets": player.get("ticket", 10),     # Map to frontend naming
                "crystals": player.get("crystals", 25)
            },
            "points": {
                "skillPoints": player.get("skillPoints", 3)
            },
            "progress": {
                "story_progress": player.get("story_progress", {"current_arc": 1, "current_mission": 1, "completed_arcs": []}),
                "arena_rank": player.get("arena_rank", 0),
                "arena_points": player.get("arena_points", 0),
                "login_streak": player.get("login_streak", 0)
            },
            "inventory_count": len(player.get("inventory", {})),
            "hunters_count": len(player.get("hunters", {})),
            "guild_id": player.get("guild_id"),
            "last_active": int(time.time())  # Current timestamp since last_active column doesn't exist
        }

        return {"profile": profile}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving profile: {str(e)}"
        )

@router.get("/profile/{player_id}")
async def get_player_profile(player_id: str):
    """Get player profile data"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        # Return essential profile data
        profile = {
            "id": player["id"],
            "username": player.get("username", "Unknown"),
            "level": player["level"],
            "xp": player["xp"],
            "stats": {
                "attack": player["attack"],
                "defense": player["defense"],
                "hp": player["hp"],
                "mp": player["mp"],
                "precision": player["precision"]
            },
            "resources": {
                "gold": player["gold"],
                "diamond": player["diamond"],
                "stone": player["stone"],
                "ticket": player["ticket"],
                "crystals": player["crystals"]
            },
            "points": {
                "statPoints": player["statPoints"],
                "skillPoints": player["skillPoints"]
            },
            "equipped": player.get("equipped", {}),
            "current_title": player.get("current_title"),
            "guild_id": player.get("guild_id"),
            "achievements": player.get("achievements", []),
            "story_progress": player.get("story_progress", {})
        }
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player profile: {str(e)}"
        )

@router.get("/stats/{player_id}")
async def get_player_stats(player_id: str):
    """Get detailed player stats including equipment bonuses"""
    try:
        stats = await player_service.get_player_stats(player_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player stats: {str(e)}"
        )

@router.get("/inventory/{player_id}")
async def get_player_inventory(player_id: str):
    """Get player inventory"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        return {
            "inventory": player.get("inventory", {}),
            "equipped": player.get("equipped", {}),
            "hunters": player.get("hunters", {}),
            "shadows": player.get("shadows", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player inventory: {str(e)}"
        )

@router.post("/upgrade-stat/{player_id}")
async def upgrade_stat(player_id: str, upgrade: StatUpgrade):
    """Upgrade a player stat using stat points"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        # Validate stat name
        valid_stats = ["attack", "defense", "hp", "mp", "precision"]
        if upgrade.stat not in valid_stats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stat. Must be one of: {valid_stats}"
            )
        
        # Check if player has enough stat points
        if player["statPoints"] < upgrade.points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stat points"
            )
        
        # Calculate stat increase (different multipliers for different stats)
        stat_multipliers = {
            "attack": 1,
            "defense": 1,
            "hp": 10,  # HP increases by 10 per point
            "mp": 2,   # MP increases by 2 per point
            "precision": 1
        }
        
        stat_increase = upgrade.points * stat_multipliers[upgrade.stat]
        
        # Update player stats
        updates = {
            upgrade.stat: player[upgrade.stat] + stat_increase,
            "statPoints": player["statPoints"] - upgrade.points
        }
        
        await player_service.update_player(player_id, updates)
        
        return {
            "message": f"Upgraded {upgrade.stat} by {stat_increase}",
            "stat": upgrade.stat,
            "increase": stat_increase,
            "points_spent": upgrade.points,
            "remaining_points": updates["statPoints"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upgrade stat: {str(e)}"
        )

@router.post("/equip/{player_id}")
async def equip_item(player_id: str, equip_data: ItemEquip):
    """Equip or unequip an item"""
    try:
        success = await player_service.equip_item(player_id, equip_data.slot, equip_data.item_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to equip item"
            )
        
        action = "equipped" if equip_data.item_id else "unequipped"
        return {
            "message": f"Item {action} successfully",
            "slot": equip_data.slot,
            "item_id": equip_data.item_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to equip item: {str(e)}"
        )

@router.post("/add-xp/{player_id}")
async def add_experience(player_id: str, xp_amount: int):
    """Add XP to player (for testing/admin purposes)"""
    try:
        result = await player_service.add_xp(player_id, xp_amount)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add XP: {str(e)}"
        )

@router.post("/add-gold/{player_id}")
async def add_gold(player_id: str, gold_amount: int):
    """Add gold to player (for testing/admin purposes)"""
    try:
        success = await player_service.add_gold(player_id, gold_amount)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        return {
            "message": f"Added {gold_amount} gold to player",
            "gold_added": gold_amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add gold: {str(e)}"
        )

@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """Get player leaderboard"""
    try:
        # This is a simplified leaderboard - in production you'd want proper ranking
        from services.database_service import db_service
        
        query = """
            SELECT id, username, level, attack, defense, hp, gold
            FROM players 
            ORDER BY level DESC, xp DESC 
            LIMIT ?
        """
        
        results = await db_service.execute_query('players', query, (limit,))
        
        leaderboard = []
        for i, row in enumerate(results):
            leaderboard.append({
                "rank": i + 1,
                "player_id": row[0],
                "username": row[1] if row[1] else "Unknown",
                "level": row[2],
                "attack": row[3],
                "defense": row[4],
                "hp": row[5],
                "gold": row[6]
            })
        
        return {"leaderboard": leaderboard}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leaderboard: {str(e)}"
        )

# Export router
player_router = router