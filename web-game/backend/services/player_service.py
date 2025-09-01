import json
import time
from typing import Dict, Any, Optional
from services.database_service import db_service, get_player_by_id

class PlayerService:
    def __init__(self):
        pass
    
    async def create_new_player(self, player_id: str, username: str):
        """Create a new player with starting stats and items"""
        
        # Starting player data (similar to Discord bot)
        player_data = {
            'id': player_id,
            'username': username,
            'level': 1,
            'xp': 0,
            'attack': 10,
            'defense': 10,
            'hp': 100,
            'mp': 10,
            'precision': 10,
            'gold': 10000,  # Starting gold (more generous)
            'diamond': 10000,   # Generous starting gems for testing
            'stone': 50,      # Match database schema
            'ticket': 10,     # Match database schema, more generous
            'crystals': 25,   # More generous starting crystals
            'premiumT': 0,
            'premium': False,
            'quests': json.dumps({}),
            'inventory': json.dumps({
                'health_potion': 10,
                'mana_potion': 5,
                'iron_ore': 20,
                'magic_crystal': 2,
                'xp_boost': 1,
                'gold_boost': 1
            }),
            'equipped': json.dumps({
                'Weapon': None, 'Weapon_2': None, 'Basic': None, 'QTE': None, 'Ultimate': None,
                'Helmet': None, 'Armor': None, 'Gloves': None, 'Boots': None, 'Necklaces': None,
                'Bracelets': None, 'Rings': None, 'Earrings': None, 'Party_1': None, 'Party_2': None,
                'Party_3': None, 'army_1': None, 'army_2': None, 'army_3': None
            }),
            'hunters': json.dumps({}),

            'skillPoints': 5,   # Starting skill points
            'afk': None,
            'afk_level': 1,
            'gacha': 0,
            'skills': json.dumps({}),
            'army_lv': 1,
            'shadows': json.dumps({})
        }
        
        # Insert player into database
        columns = ', '.join(player_data.keys())
        placeholders = ', '.join(['?' for _ in player_data])
        query = f"INSERT OR REPLACE INTO players ({columns}) VALUES ({placeholders})"
        
        await db_service.execute_query('players', query, tuple(player_data.values()))
        
        return player_data
    
    async def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player data by ID"""
        result = await get_player_by_id(player_id)
        if not result:
            return None
        
        # Convert database row to dictionary
        # This assumes the database columns match the expected structure
        player_dict = dict(result) if hasattr(result, 'keys') else self._row_to_dict(result)
        
        # Parse JSON fields
        json_fields = ['quests', 'inventory', 'equipped', 'hunters', 'skills', 'shadows', 
                      'oshi_list', 'locked_items', 'story_progress', 'achievements', 'titles']
        
        for field in json_fields:
            if field in player_dict and player_dict[field]:
                try:
                    player_dict[field] = json.loads(player_dict[field])
                except (json.JSONDecodeError, TypeError):
                    player_dict[field] = {} if field != 'oshi_list' else []
        
        return player_dict
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary (fallback method)"""
        # This is a simplified conversion - in production you'd want proper column mapping
        columns = [
            'id', 'level', 'xp', 'attack', 'defense', 'hp', 'mp', 'precision',
            'gold', 'diamond', 'stone', 'ticket', 'crystals', 'premiumT', 'premium',
            'quests', 'inventory', 'equipped', 'hunters', 'skillPoints',
            'afk', 'afk_level', 'gacha', 'skills', 'army_lv',
            'shadows', 'fcube', 'icube', 'wcube', 'dcube', 'lcube', 'tos',
            'gear1', 'gear2', 'gear3', 'gear4'
        ]
        
        return {col: row[i] if i < len(row) else None for i, col in enumerate(columns)}
    
    async def update_player(self, player_id: str, updates: Dict[str, Any]):
        """Update player data"""
        if not updates:
            return
        
        # Convert dict/list fields to JSON strings
        json_fields = ['quests', 'inventory', 'equipped', 'hunters', 'skills', 'shadows',
                      'oshi_list', 'locked_items', 'story_progress', 'achievements', 'titles']
        
        processed_updates = {}
        for key, value in updates.items():
            if key in json_fields and isinstance(value, (dict, list)):
                processed_updates[key] = json.dumps(value)
            else:
                processed_updates[key] = value
        
        # Build update query
        set_clause = ', '.join([f"{key} = ?" for key in processed_updates.keys()])
        query = f"UPDATE players SET {set_clause} WHERE id = ?"

        values = list(processed_updates.values()) + [player_id]
        await db_service.execute_query('players', query, values)
    
    async def add_xp(self, player_id: str, xp_amount: int):
        """Add XP to player and handle level ups"""
        player = await self.get_player(player_id)
        if not player:
            return None
        
        old_level = player['level']
        new_xp = player['xp'] + xp_amount
        
        # Calculate new level (100 XP per level)
        new_level = max(1, new_xp // 100 + 1)
        
        updates = {
            'xp': new_xp,
            'level': new_level
        }
        
        # If leveled up, add stat and skill points
        if new_level > old_level:
            levels_gained = new_level - old_level
            updates['statPoints'] = player['statPoints'] + (levels_gained * 10)
            updates['skillPoints'] = player['skillPoints'] + (levels_gained * 5)
        
        await self.update_player(player_id, updates)
        
        return {
            'old_level': old_level,
            'new_level': new_level,
            'xp_gained': xp_amount,
            'leveled_up': new_level > old_level
        }
    
    async def add_gold(self, player_id: str, gold_amount: int):
        """Add gold to player"""
        player = await self.get_player(player_id)
        if not player:
            return False
        
        new_gold = max(0, player['gold'] + gold_amount)
        await self.update_player(player_id, {'gold': new_gold})
        return True
    
    async def spend_gold(self, player_id: str, gold_amount: int) -> bool:
        """Spend gold if player has enough"""
        player = await self.get_player(player_id)
        if not player or player['gold'] < gold_amount:
            return False
        
        new_gold = player['gold'] - gold_amount
        await self.update_player(player_id, {'gold': new_gold})
        return True
    
    async def add_item(self, player_id: str, item_id: str, quantity: int = 1):
        """Add item to player inventory"""
        player = await self.get_player(player_id)
        if not player:
            return False
        
        inventory = player.get('inventory', {})
        current_quantity = inventory.get(item_id, 0)
        inventory[item_id] = current_quantity + quantity
        
        await self.update_player(player_id, {'inventory': inventory})
        return True
    
    async def remove_item(self, player_id: str, item_id: str, quantity: int = 1) -> bool:
        """Remove item from player inventory"""
        player = await self.get_player(player_id)
        if not player:
            return False
        
        inventory = player.get('inventory', {})
        current_quantity = inventory.get(item_id, 0)
        
        if current_quantity < quantity:
            return False
        
        if current_quantity == quantity:
            inventory.pop(item_id, None)
        else:
            inventory[item_id] = current_quantity - quantity
        
        await self.update_player(player_id, {'inventory': inventory})
        return True
    
    async def equip_item(self, player_id: str, slot: str, item_id: str):
        """Equip an item to a specific slot"""
        player = await self.get_player(player_id)
        if not player:
            return False
        
        equipped = player.get('equipped', {})
        equipped[slot] = item_id
        
        await self.update_player(player_id, {'equipped': equipped})
        return True
    
    async def get_player_stats(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get calculated player stats including equipment bonuses"""
        player = await self.get_player(player_id)
        if not player:
            return None
        
        # Base stats
        stats = {
            'level': player['level'],
            'xp': player['xp'],
            'attack': player['attack'],
            'defense': player['defense'],
            'hp': player['hp'],
            'mp': player['mp'],
            'precision': player['precision']
        }
        
        # TODO: Add equipment bonuses calculation
        # This would require loading item data and calculating bonuses
        
        return stats

# Global player service instance
player_service = PlayerService()