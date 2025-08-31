from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import time

from services.database_service import db_service
from services.player_service import player_service

router = APIRouter()

class GuildCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class GuildJoin(BaseModel):
    guild_id: str

@router.post("/create/{player_id}")
async def create_guild(player_id: str, guild_data: GuildCreate):
    """Create a new guild"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        if player.get("guild_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player is already in a guild"
            )
        
        # Check if guild name is taken
        query = "SELECT id FROM guilds WHERE name = ?"
        existing = await db_service.execute_query('guilds', query, (guild_data.name,))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guild name already taken"
            )
        
        # Create guild
        guild_id = f"guild_{int(time.time())}_{player_id[:8]}"
        guild_info = {
            "id": guild_id,
            "name": guild_data.name,
            "description": guild_data.description,
            "leader_id": player_id,
            "members": [player_id],
            "level": 1,
            "xp": 0,
            "bank_gold": 0,
            "created_at": int(time.time())
        }
        
        # Insert guild into database
        query = """
            INSERT INTO guilds (id, name, description, leader_id, members, level, xp, bank_gold, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await db_service.execute_query('guilds', query, (
            guild_id,
            guild_data.name,
            guild_data.description,
            player_id,
            json.dumps([player_id]),
            1,
            0,
            0,
            int(time.time())
        ))
        
        # Update player's guild_id
        await player_service.update_player(player_id, {"guild_id": guild_id})
        
        return {
            "message": "Guild created successfully",
            "guild": guild_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create guild: {str(e)}"
        )

@router.get("/info/{guild_id}")
async def get_guild_info(guild_id: str):
    """Get guild information"""
    try:
        query = "SELECT * FROM guilds WHERE id = ?"
        result = await db_service.execute_query('guilds', query, (guild_id,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guild not found"
            )
        
        guild_row = result[0]
        guild_info = {
            "id": guild_row[0],
            "name": guild_row[1],
            "description": guild_row[2],
            "leader_id": guild_row[3],
            "members": json.loads(guild_row[4]) if guild_row[4] else [],
            "level": guild_row[5],
            "xp": guild_row[6],
            "bank_gold": guild_row[7],
            "created_at": guild_row[8]
        }
        
        # Get member details
        member_details = []
        for member_id in guild_info["members"]:
            member = await player_service.get_player(member_id)
            if member:
                member_details.append({
                    "id": member_id,
                    "username": member.get("username", "Unknown"),
                    "level": member["level"],
                    "last_active": member.get("last_active", 0)
                })
        
        guild_info["member_details"] = member_details
        
        return {"guild": guild_info}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get guild info: {str(e)}"
        )

@router.post("/join/{player_id}")
async def join_guild(player_id: str, join_data: GuildJoin):
    """Join a guild"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        if player.get("guild_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player is already in a guild"
            )
        
        # Get guild info
        query = "SELECT * FROM guilds WHERE id = ?"
        result = await db_service.execute_query('guilds', query, (join_data.guild_id,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guild not found"
            )
        
        guild_row = result[0]
        members = json.loads(guild_row[4]) if guild_row[4] else []
        
        # Check if guild is full (max 50 members)
        if len(members) >= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guild is full"
            )
        
        # Add player to guild
        members.append(player_id)
        
        # Update guild members
        query = "UPDATE guilds SET members = ? WHERE id = ?"
        await db_service.execute_query('guilds', query, (json.dumps(members), join_data.guild_id))
        
        # Update player's guild_id
        await player_service.update_player(player_id, {"guild_id": join_data.guild_id})
        
        return {
            "message": "Joined guild successfully",
            "guild_id": join_data.guild_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join guild: {str(e)}"
        )

@router.post("/leave/{player_id}")
async def leave_guild(player_id: str):
    """Leave current guild"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        guild_id = player.get("guild_id")
        if not guild_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player is not in a guild"
            )
        
        # Get guild info
        query = "SELECT * FROM guilds WHERE id = ?"
        result = await db_service.execute_query('guilds', query, (guild_id,))
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guild not found"
            )
        
        guild_row = result[0]
        leader_id = guild_row[3]
        members = json.loads(guild_row[4]) if guild_row[4] else []
        
        # Check if player is the leader
        if player_id == leader_id:
            if len(members) > 1:
                # Transfer leadership to another member
                new_leader = next(member for member in members if member != player_id)
                query = "UPDATE guilds SET leader_id = ? WHERE id = ?"
                await db_service.execute_query('guilds', query, (new_leader, guild_id))
            else:
                # Delete guild if leader is the only member
                query = "DELETE FROM guilds WHERE id = ?"
                await db_service.execute_query('guilds', query, (guild_id,))
        
        # Remove player from guild members
        if player_id in members:
            members.remove(player_id)
            query = "UPDATE guilds SET members = ? WHERE id = ?"
            await db_service.execute_query('guilds', query, (json.dumps(members), guild_id))
        
        # Update player's guild_id
        await player_service.update_player(player_id, {"guild_id": None})
        
        return {"message": "Left guild successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to leave guild: {str(e)}"
        )

@router.get("/list")
async def list_guilds(limit: int = 20, offset: int = 0):
    """List all guilds"""
    try:
        query = """
            SELECT id, name, description, leader_id, members, level, xp, created_at
            FROM guilds 
            ORDER BY level DESC, xp DESC 
            LIMIT ? OFFSET ?
        """
        
        results = await db_service.execute_query('guilds', query, (limit, offset))
        
        guilds = []
        for row in results:
            members = json.loads(row[4]) if row[4] else []
            guilds.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "leader_id": row[3],
                "member_count": len(members),
                "level": row[5],
                "xp": row[6],
                "created_at": row[7]
            })
        
        return {"guilds": guilds}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list guilds: {str(e)}"
        )

@router.get("/my-guild/{player_id}")
async def get_my_guild(player_id: str):
    """Get player's current guild"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        guild_id = player.get("guild_id")
        if not guild_id:
            return {"guild": None, "message": "Player is not in a guild"}
        
        # Get guild info
        guild_response = await get_guild_info(guild_id)
        return guild_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player's guild: {str(e)}"
        )

# Export router
guild_router = router