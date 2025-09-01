import json
import aiosqlite
import asyncio
from datetime import datetime
from structure.player import Player
from structure.heroes import HeroManager
from structure.items import ItemManager

class RareItemRetirement:
    """System to retire all Rare items and move them to badge collections"""
    
    def __init__(self):
        self.retired_items = []
        self.retired_hunters = []
        self.affected_players = []
        
    async def retire_all_rare_items(self):
        """Complete retirement process for all Rare items"""
        print("🔄 Starting Rare Item Retirement Process...")
        
        # Step 1: Identify all Rare items in databases
        await self.identify_rare_items()
        
        # Step 2: Move Rare items from all players to badge collections
        await self.migrate_player_rare_items()
        
        # Step 3: Remove Rare items from game databases
        await self.remove_rare_from_databases()
        
        # Step 4: Generate retirement report
        await self.generate_retirement_report()
        
        print("✅ Rare Item Retirement Process Complete!")
        
    async def identify_rare_items(self):
        """Identify all Rare items and hunters in the databases"""
        print("🔍 Identifying Rare items in databases...")
        
        # Get all hunters and find Rare ones
        all_hunters = await HeroManager.get_all()
        self.retired_hunters = [h for h in all_hunters if h.rarity == "Rare"]
        
        # Get all items and find Rare ones
        all_items = await ItemManager.get_all()
        self.retired_items = [i for i in all_items if i.rarity == "Rare"]
        
        print(f"📊 Found {len(self.retired_hunters)} Rare hunters to retire")
        print(f"📊 Found {len(self.retired_items)} Rare items to retire")
        
    async def migrate_player_rare_items(self):
        """Move all Rare items from player inventories to badge collections"""
        print("🔄 Migrating Rare items from player inventories...")
        
        # Get all players
        all_players = await Player.get_all()
        migration_count = 0
        
        for player in all_players:
            player_migrated = False
            
            # Check player's hunters for Rare items
            hunters_to_remove = []
            for hunter_id, hunter_data in player.hunters.items():
                # Find the hunter in our retired list
                retired_hunter = next((h for h in self.retired_hunters if h.id == hunter_id), None)
                if retired_hunter:
                    # Add to badge collection
                    await self.add_to_badge_collection(
                        player, hunter_id, retired_hunter.name, 
                        "Rare", "hunter", hunter_data
                    )
                    hunters_to_remove.append(hunter_id)
                    player_migrated = True
            
            # Remove Rare hunters from active inventory
            for hunter_id in hunters_to_remove:
                del player.hunters[hunter_id]
            
            # Check player's items for Rare items
            items_to_remove = []
            for item_id, item_data in player.inventory.items():
                # Find the item in our retired list
                retired_item = next((i for i in self.retired_items if i.id == item_id), None)
                if retired_item:
                    # Add to badge collection
                    await self.add_to_badge_collection(
                        player, item_id, retired_item.name, 
                        "Rare", "item", item_data
                    )
                    items_to_remove.append(item_id)
                    player_migrated = True
            
            # Remove Rare items from active inventory
            for item_id in items_to_remove:
                del player.inventory[item_id]
            
            # Save player if any changes were made
            if player_migrated:
                await player.save()
                self.affected_players.append(player.id)
                migration_count += 1
                
                # Also remove from equipped items if equipped
                await self.remove_from_equipped(player, hunters_to_remove + items_to_remove)
        
        print(f"✅ Migrated Rare items for {migration_count} players")
        
    async def add_to_badge_collection(self, player, item_id, name, rarity, item_type, item_data):
        """Add an item to player's badge collection"""
        if not hasattr(player, 'badge_collection'):
            player.badge_collection = {}
        
        # Get level and tier info if available
        level = 1
        tier = 0
        if isinstance(item_data, dict):
            level = item_data.get('level', 1)
            tier = item_data.get('tier', 0)
        
        player.badge_collection[item_id] = {
            'name': name,
            'rarity': rarity,
            'type': item_type,
            'level': level,
            'tier': tier,
            'owned_date': datetime.now().strftime("%Y-%m-%d"),
            'retirement_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    async def remove_from_equipped(self, player, removed_item_ids):
        """Remove retired items from player's equipped slots"""
        changes_made = False
        
        for slot, equipped_id in player.equipped.items():
            if equipped_id in removed_item_ids:
                player.equipped[slot] = None
                changes_made = True
                print(f"🔧 Removed {equipped_id} from {player.id}'s {slot} slot")
        
        if changes_made:
            await player.save()
    
    async def remove_rare_from_databases(self):
        """Remove all Rare items from game databases"""
        print("🗑️ Removing Rare items from game databases...")
        
        # Remove from hunters.json
        await self.remove_rare_from_hunters_db()
        
        # Remove from items.json  
        await self.remove_rare_from_items_db()
        
        print("✅ Rare items removed from all databases")
        
    async def remove_rare_from_hunters_db(self):
        """Remove Rare hunters from hunters.json"""
        try:
            with open('hunters.json', 'r') as f:
                hunters_data = json.load(f)
            
            # Filter out Rare hunters
            original_count = len(hunters_data)
            hunters_data = [h for h in hunters_data if h.get('rarity') != 'Rare']
            removed_count = original_count - len(hunters_data)
            
            # Save updated hunters.json
            with open('hunters.json', 'w') as f:
                json.dump(hunters_data, f, indent=2)
            
            print(f"🗑️ Removed {removed_count} Rare hunters from hunters.json")
            
        except Exception as e:
            print(f"❌ Error removing Rare hunters: {e}")
    
    async def remove_rare_from_items_db(self):
        """Remove Rare items from items.json"""
        try:
            with open('items.json', 'r') as f:
                items_data = json.load(f)
            
            # Filter out Rare items
            original_count = len(items_data)
            items_data = [i for i in items_data if i.get('rarity') != 'Rare']
            removed_count = original_count - len(items_data)
            
            # Save updated items.json
            with open('items.json', 'w') as f:
                json.dump(items_data, f, indent=2)
            
            print(f"🗑️ Removed {removed_count} Rare items from items.json")
            
        except Exception as e:
            print(f"❌ Error removing Rare items: {e}")
    
    async def generate_retirement_report(self):
        """Generate a comprehensive retirement report"""
        report = {
            'retirement_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'retired_hunters': len(self.retired_hunters),
            'retired_items': len(self.retired_items),
            'affected_players': len(self.affected_players),
            'retired_hunter_list': [{'id': h.id, 'name': h.name} for h in self.retired_hunters],
            'retired_item_list': [{'id': i.id, 'name': i.name} for i in self.retired_items],
            'affected_player_ids': self.affected_players
        }
        
        # Save retirement report
        with open('rare_retirement_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📊 RETIREMENT REPORT:")
        print(f"   🏆 Retired Hunters: {report['retired_hunters']}")
        print(f"   ⚔️ Retired Items: {report['retired_items']}")
        print(f"   👥 Affected Players: {report['affected_players']}")
        print(f"   📄 Report saved to: rare_retirement_report.json")

async def main():
    """Run the Rare item retirement process"""
    retirement_system = RareItemRetirement()
    await retirement_system.retire_all_rare_items()

if __name__ == "__main__":
    asyncio.run(main())
