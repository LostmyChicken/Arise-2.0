from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json

from services.player_service import player_service

router = APIRouter()

class StoryProgress(BaseModel):
    arc: int
    mission: int

@router.get("/progress/{player_id}")
async def get_story_progress(player_id: str):
    """Get player's story progress"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        story_progress = player.get("story_progress", {
            "current_arc": 1,
            "current_mission": 1,
            "completed_arcs": []
        })
        
        return {"story_progress": story_progress}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get story progress: {str(e)}"
        )

@router.get("/arcs")
async def get_story_arcs():
    """Get all story arcs and missions"""
    try:
        # This would load from the original Discord bot's story system
        story_arcs = {
            "1": {
                "name": "The Weakest Hunter",
                "description": "Sung Jin-Woo's journey begins as the weakest E-rank hunter.",
                "missions": [
                    {
                        "id": 1,
                        "name": "First Dungeon",
                        "description": "Enter your first E-rank dungeon and survive.",
                        "requirements": {"level": 1},
                        "rewards": {"xp": 100, "gold": 200, "ticket": 1},
                        "enemies": ["goblin", "slime"]
                    },
                    {
                        "id": 2,
                        "name": "The Double Dungeon",
                        "description": "Discover the mysterious double dungeon.",
                        "requirements": {"level": 3},
                        "rewards": {"xp": 200, "gold": 400, "ticket": 2},
                        "enemies": ["stone_statue", "knight_statue"]
                    }
                ]
            },
            "2": {
                "name": "The System",
                "description": "Jin-Woo awakens to the mysterious leveling system.",
                "missions": [
                    {
                        "id": 1,
                        "name": "Daily Quests",
                        "description": "Complete your first daily quest from the system.",
                        "requirements": {"level": 5, "completed_arcs": [1]},
                        "rewards": {"xp": 300, "gold": 600, "ticket": 2},
                        "enemies": ["enhanced_goblin"]
                    }
                ]
            },
            "3": {
                "name": "Instant Dungeon",
                "description": "Jin-Woo discovers the instant dungeon feature.",
                "missions": [
                    {
                        "id": 1,
                        "name": "First Instant Dungeon",
                        "description": "Clear your first instant dungeon.",
                        "requirements": {"level": 10, "completed_arcs": [1, 2]},
                        "rewards": {"xp": 500, "gold": 1000, "ticket": 3},
                        "enemies": ["dungeon_wolf", "alpha_wolf"]
                    }
                ]
            }
        }
        
        return {"story_arcs": story_arcs}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get story arcs: {str(e)}"
        )

@router.post("/start-mission/{player_id}")
async def start_story_mission(player_id: str, mission_data: StoryProgress):
    """Start a story mission"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        story_progress = player.get("story_progress", {
            "current_arc": 1,
            "current_mission": 1,
            "completed_arcs": []
        })
        
        # Get story arcs
        arcs_response = await get_story_arcs()
        story_arcs = arcs_response["story_arcs"]
        
        # Validate mission exists
        arc_key = str(mission_data.arc)
        if arc_key not in story_arcs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story arc not found"
            )
        
        arc = story_arcs[arc_key]
        if mission_data.mission > len(arc["missions"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story mission not found"
            )
        
        mission = arc["missions"][mission_data.mission - 1]
        
        # Check requirements
        requirements = mission.get("requirements", {})
        
        # Check level requirement
        if player["level"] < requirements.get("level", 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Level {requirements['level']} required"
            )
        
        # Check completed arcs requirement
        required_arcs = requirements.get("completed_arcs", [])
        completed_arcs = story_progress.get("completed_arcs", [])
        
        for required_arc in required_arcs:
            if required_arc not in completed_arcs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Must complete arc {required_arc} first"
                )
        
        # Check if mission is already available
        current_arc = story_progress.get("current_arc", 1)
        current_mission = story_progress.get("current_mission", 1)
        
        if mission_data.arc > current_arc or (mission_data.arc == current_arc and mission_data.mission > current_mission):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mission not yet available"
            )
        
        return {
            "message": "Story mission started",
            "arc": mission_data.arc,
            "mission": mission_data.mission,
            "mission_data": mission,
            "battle_required": True  # Most story missions require battles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start story mission: {str(e)}"
        )

@router.post("/complete-mission/{player_id}")
async def complete_story_mission(player_id: str, mission_data: StoryProgress):
    """Complete a story mission and award rewards"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        # Get story arcs
        arcs_response = await get_story_arcs()
        story_arcs = arcs_response["story_arcs"]
        
        # Get mission data
        arc_key = str(mission_data.arc)
        arc = story_arcs[arc_key]
        mission = arc["missions"][mission_data.mission - 1]
        
        # Award rewards
        rewards = mission.get("rewards", {})
        
        if "xp" in rewards:
            await player_service.add_xp(player_id, rewards["xp"])
        
        if "gold" in rewards:
            await player_service.add_gold(player_id, rewards["gold"])
        
        if "ticket" in rewards:
            current_tickets = player.get("ticket", 0)
            await player_service.update_player(player_id, {
                "ticket": current_tickets + rewards["ticket"]
            })
        
        # Update story progress
        story_progress = player.get("story_progress", {
            "current_arc": 1,
            "current_mission": 1,
            "completed_arcs": []
        })
        
        # Check if this completes the arc
        if mission_data.mission >= len(arc["missions"]):
            # Arc completed
            completed_arcs = story_progress.get("completed_arcs", [])
            if mission_data.arc not in completed_arcs:
                completed_arcs.append(mission_data.arc)
            
            # Move to next arc
            story_progress.update({
                "current_arc": mission_data.arc + 1,
                "current_mission": 1,
                "completed_arcs": completed_arcs
            })
        else:
            # Move to next mission in same arc
            story_progress.update({
                "current_arc": mission_data.arc,
                "current_mission": mission_data.mission + 1,
                "completed_arcs": story_progress.get("completed_arcs", [])
            })
        
        await player_service.update_player(player_id, {
            "story_progress": story_progress
        })
        
        return {
            "message": "Story mission completed",
            "rewards": rewards,
            "new_progress": story_progress
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete story mission: {str(e)}"
        )

@router.get("/current-mission/{player_id}")
async def get_current_mission(player_id: str):
    """Get player's current available mission"""
    try:
        player = await player_service.get_player(player_id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found"
            )
        
        story_progress = player.get("story_progress", {
            "current_arc": 1,
            "current_mission": 1,
            "completed_arcs": []
        })
        
        # Get story arcs
        arcs_response = await get_story_arcs()
        story_arcs = arcs_response["story_arcs"]
        
        current_arc = story_progress.get("current_arc", 1)
        current_mission = story_progress.get("current_mission", 1)
        
        arc_key = str(current_arc)
        if arc_key not in story_arcs:
            return {
                "message": "Story completed!",
                "current_mission": None
            }
        
        arc = story_arcs[arc_key]
        if current_mission > len(arc["missions"]):
            return {
                "message": "Arc completed, waiting for next arc",
                "current_mission": None
            }
        
        mission = arc["missions"][current_mission - 1]
        
        return {
            "current_arc": current_arc,
            "current_mission": current_mission,
            "arc_name": arc["name"],
            "mission_data": mission
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current mission: {str(e)}"
        )

# Export router
story_router = router