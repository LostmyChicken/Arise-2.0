import discord
from discord.ext import commands
import logging
from structure.server_tracker import ServerTracker

class ServerTrackingEvents(commands.Cog):
    """Event handlers for server tracking"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize server tracking when bot is ready"""
        await ServerTracker.initialize_database()
        
        # Track all current servers on startup
        for guild in self.bot.guilds:
            await ServerTracker.update_server_info(guild)
        
        logging.info(f"Server tracking initialized for {len(self.bot.guilds)} servers")
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Track when bot joins a new server"""
        await ServerTracker.track_server_join(guild)
        
        # Send notification to admin webhook if configured
        try:
            embed = discord.Embed(
                title="🎉 **NEW SERVER JOINED**",
                description=f"Bot has been invited to a new server!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 **Server Details**",
                value=(
                    f"**Name**: {guild.name}\n"
                    f"**ID**: {guild.id}\n"
                    f"**Owner**: {guild.owner.display_name if guild.owner else 'Unknown'}\n"
                    f"**Members**: {guild.member_count:,}\n"
                    f"**Created**: {guild.created_at.strftime('%Y-%m-%d')}"
                ),
                inline=False
            )
            
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.set_footer(text="◆ Server Tracking ◆ • Permanent record created")
            
            # Log to console
            logging.info(f"🎉 Bot joined new server: {guild.name} ({guild.id}) - {guild.member_count:,} members")
            
        except Exception as e:
            logging.error(f"Error sending server join notification: {e}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Track when bot leaves a server"""
        await ServerTracker.track_server_leave(guild)
        
        # Send notification to admin webhook if configured
        try:
            embed = discord.Embed(
                title="👋 **SERVER LEFT**",
                description=f"Bot has been removed from a server",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="📋 **Server Details**",
                value=(
                    f"**Name**: {guild.name}\n"
                    f"**ID**: {guild.id}\n"
                    f"**Members**: {guild.member_count:,}\n"
                    f"**Reason**: Bot removed or server deleted"
                ),
                inline=False
            )
            
            embed.add_field(
                name="💾 **Data Retention**",
                value="Server data has been preserved for historical tracking",
                inline=False
            )
            
            embed.set_footer(text="◆ Server Tracking ◆ • Historical record maintained")
            
            # Log to console
            logging.info(f"👋 Bot left server: {guild.name} ({guild.id}) - {guild.member_count:,} members")
            
        except Exception as e:
            logging.error(f"Error sending server leave notification: {e}")
    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Track server updates"""
        # Only update if significant changes occurred
        if (before.name != after.name or 
            before.owner_id != after.owner_id or 
            abs(before.member_count - after.member_count) > 10):  # Only if member count changed significantly
            
            await ServerTracker.update_server_info(after)
            
            # Log significant changes
            if before.name != after.name:
                logging.info(f"Server renamed: {before.name} → {after.name} ({after.id})")
            
            if before.owner_id != after.owner_id:
                old_owner = before.owner.display_name if before.owner else "Unknown"
                new_owner = after.owner.display_name if after.owner else "Unknown"
                logging.info(f"Server ownership changed: {old_owner} → {new_owner} in {after.name} ({after.id})")

async def setup(bot):
    await bot.add_cog(ServerTrackingEvents(bot))
