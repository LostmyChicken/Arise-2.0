"""
Channel-specific command management system
Allows enabling/disabling specific commands in specific channels
"""

import aiosqlite
import discord
from discord.ext import commands
from typing import List, Dict, Set, Optional
import logging

class ChannelCommandManager:
    """Manages channel-specific command enable/disable functionality"""
    
    def __init__(self):
        self.db_path = "data/channel_commands.db"
        self._cache = {}  # Cache for faster lookups: {channel_id: {disabled_commands}}
        
    async def initialize_database(self):
        """Initialize the database table for channel command settings"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channel_disabled_commands (
                    channel_id INTEGER,
                    command_name TEXT,
                    disabled_by INTEGER,
                    disabled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (channel_id, command_name)
                )
            """)
            await db.commit()
    
    async def disable_command(self, channel_id: int, command_name: str, disabled_by: int) -> bool:
        """
        Disable a command in a specific channel
        
        Args:
            channel_id: Discord channel ID
            command_name: Name of the command to disable
            disabled_by: User ID who disabled the command
            
        Returns:
            bool: True if successfully disabled, False if already disabled
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Check if already disabled
                cursor = await db.execute(
                    "SELECT 1 FROM channel_disabled_commands WHERE channel_id = ? AND command_name = ?",
                    (channel_id, command_name)
                )
                if await cursor.fetchone():
                    return False  # Already disabled
                
                # Add to disabled commands
                await db.execute(
                    "INSERT INTO channel_disabled_commands (channel_id, command_name, disabled_by) VALUES (?, ?, ?)",
                    (channel_id, command_name, disabled_by)
                )
                await db.commit()
                
                # Update cache
                if channel_id not in self._cache:
                    self._cache[channel_id] = set()
                self._cache[channel_id].add(command_name)
                
                return True
                
        except Exception as e:
            logging.error(f"Error disabling command {command_name} in channel {channel_id}: {e}")
            return False
    
    async def enable_command(self, channel_id: int, command_name: str) -> bool:
        """
        Enable a command in a specific channel (remove from disabled list)
        
        Args:
            channel_id: Discord channel ID
            command_name: Name of the command to enable
            
        Returns:
            bool: True if successfully enabled, False if wasn't disabled
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM channel_disabled_commands WHERE channel_id = ? AND command_name = ?",
                    (channel_id, command_name)
                )
                await db.commit()
                
                if cursor.rowcount == 0:
                    return False  # Wasn't disabled
                
                # Update cache
                if channel_id in self._cache:
                    self._cache[channel_id].discard(command_name)
                    if not self._cache[channel_id]:  # Remove empty set
                        del self._cache[channel_id]
                
                return True
                
        except Exception as e:
            logging.error(f"Error enabling command {command_name} in channel {channel_id}: {e}")
            return False
    
    async def is_command_disabled(self, channel_id: int, command_name: str) -> bool:
        """
        Check if a command is disabled in a specific channel
        
        Args:
            channel_id: Discord channel ID
            command_name: Name of the command to check
            
        Returns:
            bool: True if disabled, False if enabled
        """
        # Check cache first
        if channel_id in self._cache:
            return command_name in self._cache[channel_id]
        
        # Load from database and cache
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT command_name FROM channel_disabled_commands WHERE channel_id = ?",
                    (channel_id,)
                )
                disabled_commands = {row[0] for row in await cursor.fetchall()}
                
                # Cache the result
                if disabled_commands:
                    self._cache[channel_id] = disabled_commands
                
                return command_name in disabled_commands
                
        except Exception as e:
            logging.error(f"Error checking if command {command_name} is disabled in channel {channel_id}: {e}")
            return False
    
    async def get_disabled_commands(self, channel_id: int) -> Set[str]:
        """
        Get all disabled commands for a specific channel
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            Set[str]: Set of disabled command names
        """
        # Check cache first
        if channel_id in self._cache:
            return self._cache[channel_id].copy()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT command_name FROM channel_disabled_commands WHERE channel_id = ?",
                    (channel_id,)
                )
                disabled_commands = {row[0] for row in await cursor.fetchall()}
                
                # Cache the result
                if disabled_commands:
                    self._cache[channel_id] = disabled_commands
                
                return disabled_commands
                
        except Exception as e:
            logging.error(f"Error getting disabled commands for channel {channel_id}: {e}")
            return set()
    
    async def get_all_channel_settings(self) -> Dict[int, Set[str]]:
        """
        Get all channel command settings
        
        Returns:
            Dict[int, Set[str]]: Dictionary mapping channel_id to set of disabled commands
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT channel_id, command_name FROM channel_disabled_commands")
                rows = await cursor.fetchall()
                
                result = {}
                for channel_id, command_name in rows:
                    if channel_id not in result:
                        result[channel_id] = set()
                    result[channel_id].add(command_name)
                
                # Update cache
                self._cache = result.copy()
                
                return result
                
        except Exception as e:
            logging.error(f"Error getting all channel settings: {e}")
            return {}
    
    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()

# Global instance
channel_command_manager = ChannelCommandManager()

async def is_command_allowed(ctx: commands.Context) -> bool:
    """
    Check if a command is allowed to run in the current channel

    Args:
        ctx: Command context

    Returns:
        bool: True if command is allowed, False if disabled
    """
    if not ctx.guild or not ctx.channel:
        return True  # Allow in DMs

    if not ctx.command:
        return True  # No command to check

    command_name = ctx.command.name

    # Never disable channel management commands themselves
    if command_name in ['channelcommands', 'disablecommand', 'enablecommand', 'listcommands']:
        return True

    # Never disable core essential commands
    essential_commands = [
        'help', 'start', 'profile', 'guild', 'fixuser', 'unstuck', 'ping'
    ]
    if command_name in essential_commands:
        return True

    # Never disable admin commands (bot admin only commands)
    admin_only_commands = [
        'admin', 'adminhelp', 'give', 'create', 'createpanel', 'fix', 'adminreset',
        'spawnboss', 'spawnworldboss', 'worldbossstatus', 'serveranalytics',
        'servertracking', 'rankmigration', 'rankrecalc', 'testitem', 'balancecheck',
        'itemusage', 'contentreport', 'contenteditor'
    ]
    if command_name in admin_only_commands:
        return True

    channel_id = ctx.channel.id

    return not await channel_command_manager.is_command_disabled(channel_id, command_name)

def command_enabled_check():
    """
    Decorator check function for commands to verify they're enabled in the channel
    """
    async def predicate(ctx: commands.Context) -> bool:
        return await is_command_allowed(ctx)
    
    return commands.check(predicate)
