from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from services.player_service import player_service
from services.database_service import update_player_status

router = APIRouter()

class StatUpgrade(BaseModel):
    stat: str  # attack, defense, hp, mp, precision
    points: int

class ItemEquip(BaseModel):
    slot: str
    item_id: Optional[str] = None

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