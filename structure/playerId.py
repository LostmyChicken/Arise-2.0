import json
import os
from pathlib import Path

from structure.player import Player

PLAYER_IDS_FILE = Path("player_ids.json")

class PlayerIdManager:
    @staticmethod
    async def initialize_ids():
        """Initialize the JSON file with current player IDs from database"""
        if not PLAYER_IDS_FILE.parent.exists():
            PLAYER_IDS_FILE.parent.mkdir(parents=True)
        
        ids = await Player.get_all_player_ids()
        with open(PLAYER_IDS_FILE, 'w') as f:
            json.dump({"player_ids": ids}, f)

    @staticmethod
    async def get_all_ids():
        """Get all player IDs from JSON file"""
        if not PLAYER_IDS_FILE.exists():
            await PlayerIdManager.initialize_ids()
        
        with open(PLAYER_IDS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("player_ids", [])

    @staticmethod
    async def add_player_id(player_id: int):
        """Add a new player ID to the JSON file"""
        ids = await PlayerIdManager.get_all_ids()
        if player_id not in ids:
            ids.append(player_id)
            with open(PLAYER_IDS_FILE, 'w') as f:
                json.dump({"player_ids": ids}, f)

    @staticmethod
    async def remove_player_id(player_id: int):
        """Remove a player ID from the JSON file"""
        ids = await PlayerIdManager.get_all_ids()
        if player_id in ids:
            ids.remove(player_id)
            with open(PLAYER_IDS_FILE, 'w') as f:
                json.dump({"player_ids": ids}, f)