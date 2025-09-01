#!/usr/bin/env python3
"""
Guild Integration Manager - Ensures seamless integration between old and enhanced guild systems
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from structure.guild import Guild
from structure.enhanced_guild import EnhancedGuild, GuildRole
from structure.player import Player
from datetime import datetime

class GuildIntegrationManager:
    """Manages integration between old Guild and new EnhancedGuild systems"""
    
    @staticmethod
    async def get_unified_guild(guild_id: str) -> Optional[EnhancedGuild]:
        """
        Get a guild, automatically converting from old format if needed.
        This is the main method all guild operations should use.
        """
        if not guild_id:
            return None
            
        try:
            # 1. Try to get enhanced guild first
            enhanced_guild = await EnhancedGuild.get(guild_id)
            if enhanced_guild:
                logging.info(f"Found enhanced guild: {guild_id}")
                return enhanced_guild
            
            # 2. Try to get old guild and convert it
            old_guild = await Guild.get(guild_id)
            if old_guild:
                logging.info(f"Converting old guild to enhanced: {guild_id}")
                enhanced_guild = await GuildIntegrationManager.convert_old_to_enhanced(old_guild)
                
                # Delete old guild after successful conversion
                if enhanced_guild:
                    await old_guild.delete()
                    logging.info(f"Deleted old guild after conversion: {guild_id}")
                
                return enhanced_guild
            
            # 3. Guild doesn't exist in either system
            logging.info(f"Guild not found in either system: {guild_id}")
            return None
            
        except Exception as e:
            logging.error(f"Error getting unified guild {guild_id}: {e}")
            return None
    
    @staticmethod
    async def convert_old_to_enhanced(old_guild: Guild) -> Optional[EnhancedGuild]:
        """Convert old guild to enhanced guild format with full data preservation"""
        try:
            # Convert members to enhanced format
            enhanced_members = []
            
            if hasattr(old_guild, 'members') and old_guild.members:
                for member_data in old_guild.members:
                    try:
                        if isinstance(member_data, dict):
                            # Handle dictionary format
                            member_id = member_data.get("id") or member_data.get("user_id")
                            if member_id:
                                # Determine role - owner becomes guild master, others become members
                                role = GuildRole.GUILD_MASTER.value if int(member_id) == old_guild.owner else GuildRole.MEMBER.value
                                
                                enhanced_members.append({
                                    "id": int(member_id),
                                    "role": role,
                                    "joined_at": member_data.get("joined_at", datetime.now().isoformat()),
                                    "contribution": member_data.get("gc", member_data.get("contribution", 0)),
                                    "last_active": member_data.get("last_active", datetime.now().isoformat())
                                })
                        elif isinstance(member_data, (int, str)):
                            # Handle simple ID format
                            member_id = int(member_data)
                            role = GuildRole.GUILD_MASTER.value if member_id == old_guild.owner else GuildRole.MEMBER.value
                            
                            enhanced_members.append({
                                "id": member_id,
                                "role": role,
                                "joined_at": datetime.now().isoformat(),
                                "contribution": 0,
                                "last_active": datetime.now().isoformat()
                            })
                    except Exception as e:
                        logging.warning(f"Error converting member {member_data}: {e}")
                        continue
            
            # Ensure owner is in members list
            owner_in_members = any(member["id"] == old_guild.owner for member in enhanced_members)
            if not owner_in_members:
                enhanced_members.append({
                    "id": old_guild.owner,
                    "role": GuildRole.GUILD_MASTER.value,
                    "joined_at": datetime.now().isoformat(),
                    "contribution": 0,
                    "last_active": datetime.now().isoformat()
                })
            
            # Create enhanced guild with all preserved data
            enhanced_guild = EnhancedGuild(
                id=old_guild.id,
                name=old_guild.name,
                owner=old_guild.owner,
                members=enhanced_members,
                level=getattr(old_guild, 'level', 1),
                points=getattr(old_guild, 'points', 0),
                image=getattr(old_guild, 'image', ''),
                description=getattr(old_guild, 'description', ''),
                gates=getattr(old_guild, 'gates', 0),
                allow_alliances=getattr(old_guild, 'allow_alliances', False),
                # Initialize enhanced features
                guild_bank={"gold": 0, "diamond": 0, "crystals": 0},
                applications=[],
                settings={
                    "auto_accept_applications": False,
                    "min_level_requirement": 1,
                    "application_required": True,
                    "max_members": 50,
                    "public_visibility": True,
                    "motto": ""
                },
                created_at=getattr(old_guild, 'created_at', datetime.now().isoformat()),
                last_active=datetime.now().isoformat()
            )
            
            # Save enhanced guild
            await enhanced_guild.save()
            
            logging.info(f"Successfully converted guild '{old_guild.name}' with {len(enhanced_members)} members")
            return enhanced_guild
            
        except Exception as e:
            logging.error(f"Error converting old guild {old_guild.id}: {e}")
            return None
    
    @staticmethod
    async def get_all_guilds() -> List[EnhancedGuild]:
        """Get all guilds from both systems, converting old ones as needed"""
        all_guilds = []
        
        try:
            # Get all enhanced guilds
            enhanced_guilds = await EnhancedGuild.get_all()
            all_guilds.extend(enhanced_guilds)
            enhanced_guild_ids = {guild.id for guild in enhanced_guilds}
            
            # Get old guilds that haven't been converted yet
            old_guilds = await Guild.get_all()
            for old_guild in old_guilds:
                if old_guild.id not in enhanced_guild_ids:
                    # Convert old guild
                    enhanced_guild = await GuildIntegrationManager.convert_old_to_enhanced(old_guild)
                    if enhanced_guild:
                        all_guilds.append(enhanced_guild)
                        # Delete old guild after conversion
                        await old_guild.delete()
            
            return all_guilds
            
        except Exception as e:
            logging.error(f"Error getting all guilds: {e}")
            return []
    
    @staticmethod
    async def update_player_guild_references():
        """Update all player guild references to ensure consistency"""
        try:
            from structure.player import Player
            import aiosqlite
            
            # Get all players with guild references
            async with aiosqlite.connect("new_player.db") as db:
                async with db.execute("SELECT id, guild FROM players WHERE guild IS NOT NULL AND guild != ''") as cursor:
                    players_with_guilds = await cursor.fetchall()
            
            updated_count = 0
            for player_id, guild_id in players_with_guilds:
                try:
                    # Check if guild exists in enhanced system
                    enhanced_guild = await EnhancedGuild.get(guild_id)
                    if enhanced_guild:
                        # Guild exists in enhanced system, player reference is correct
                        continue
                    
                    # Check if guild exists in old system and convert
                    old_guild = await Guild.get(guild_id)
                    if old_guild:
                        enhanced_guild = await GuildIntegrationManager.convert_old_to_enhanced(old_guild)
                        if enhanced_guild:
                            await old_guild.delete()
                            updated_count += 1
                    else:
                        # Guild doesn't exist, clear player reference
                        player = await Player.get(player_id)
                        if player:
                            player.guild = None
                            await player.save()
                            logging.info(f"Cleared invalid guild reference for player {player_id}")
                
                except Exception as e:
                    logging.error(f"Error updating guild reference for player {player_id}: {e}")
            
            logging.info(f"Updated {updated_count} guild references")
            return updated_count
            
        except Exception as e:
            logging.error(f"Error updating player guild references: {e}")
            return 0
    
    @staticmethod
    async def run_full_migration():
        """Run a complete migration from old to enhanced guild system"""
        try:
            logging.info("Starting full guild system migration...")
            
            # 1. Get all old guilds
            old_guilds = await Guild.get_all()
            logging.info(f"Found {len(old_guilds)} old guilds to migrate")
            
            migrated_count = 0
            failed_count = 0
            
            for old_guild in old_guilds:
                try:
                    # Check if already converted
                    existing_enhanced = await EnhancedGuild.get(old_guild.id)
                    if existing_enhanced:
                        logging.info(f"Guild {old_guild.id} already converted, deleting old version")
                        await old_guild.delete()
                        continue
                    
                    # Convert to enhanced
                    enhanced_guild = await GuildIntegrationManager.convert_old_to_enhanced(old_guild)
                    if enhanced_guild:
                        await old_guild.delete()
                        migrated_count += 1
                        logging.info(f"Migrated guild: {old_guild.name}")
                    else:
                        failed_count += 1
                        logging.error(f"Failed to migrate guild: {old_guild.name}")
                
                except Exception as e:
                    failed_count += 1
                    logging.error(f"Error migrating guild {old_guild.id}: {e}")
            
            # 2. Update player references
            updated_players = await GuildIntegrationManager.update_player_guild_references()
            
            logging.info(f"Migration complete: {migrated_count} guilds migrated, {failed_count} failed, {updated_players} player references updated")
            
            return {
                "migrated": migrated_count,
                "failed": failed_count,
                "updated_players": updated_players
            }
            
        except Exception as e:
            logging.error(f"Error during full migration: {e}")
            return {"migrated": 0, "failed": 0, "updated_players": 0}

async def main():
    """Test the guild integration system"""
    print("🔄 Guild Integration Manager Test")
    print("=" * 40)
    
    # Test getting all guilds
    all_guilds = await GuildIntegrationManager.get_all_guilds()
    print(f"Found {len(all_guilds)} total guilds")
    
    # Test migration
    migration_result = await GuildIntegrationManager.run_full_migration()
    print(f"Migration result: {migration_result}")
    
    print("✅ Guild integration test complete")

if __name__ == "__main__":
    asyncio.run(main())
