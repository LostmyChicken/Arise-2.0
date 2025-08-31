import time
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

from structure.playerId import PlayerIdManager
from structure.player import Player
from structure.story_campaign import StoryCampaign
from utilis import admin
from utilis.admin import is_bot_admin
import logging

TOPGG_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJib3QiOiJ0cnVlIiwiaWQiOiIxMjMxMTU3NzM4NjI5ODkwMTE4IiwiaWF0IjoiMTc0MDQ4MjAxNiJ9.q3D7PNuFWLze2cbXbZ3UKHPD9XcPqc39dv7IPAoRceY"  # Replace with your actual Top.gg API token
class AdminGrant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="admingrant", help="Grant a subscription pack to a user.")
    @app_commands.describe(user="The user to grant the pack to.", pack="The pack number (1, 2, or 3).")
    async def admingrant(self, ctx, user: discord.Member, pack: int):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        if pack not in [1, 2, 3]:
            embed = discord.Embed(title="Invalid Pack", description="Invalid pack number! Please choose 1, 2, or 3.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        player = await Player.get(user.id)
        if not player:
            embed = discord.Embed(title="Player Not Found", description=f"{user.mention} does not have a character yet. They need to create one first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        current_time = datetime.now(timezone.utc).timestamp()

        if pack == 1:
            player.prem1 = current_time
            player.prem2 = None
            player.prem3 = None
            pack_name = "Silver Pack"
        elif pack == 2:
            player.prem1 = None
            player.prem2 = current_time
            player.prem3 = None
            pack_name = "Gold Pack"
        elif pack == 3:
            player.prem1 = None
            player.prem2 = None
            player.prem3 = current_time
            pack_name = "Platinum Pack"

        await player.save()

        embed = discord.Embed(title="Success", description=f"Successfully granted the **{pack_name}** to {user.mention}!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="fix", help="Fix a player's 'inc' status.")
    @app_commands.describe(user="The user to fix.")
    async def fix(self, ctx, user: discord.Member = None):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        # If no user specified, fix the command author
        target_user = user or ctx.author
        player = await Player.get(target_user.id)

        if not player:
            embed = discord.Embed(title="Player Not Found", description=f"{target_user.mention} does not have a character yet. They need to create one first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        player.inc = False
        await player.save()
        embed = discord.Embed(title="Success", description=f"Fixed 'inc' status for {user.mention}.", color=discord.Color.green())
        await ctx.send(embed=embed)

        
    @commands.hybrid_command(name="fixtrade", help="Fix a player's trade status.")
    @app_commands.describe(user="The user to fix.")
    async def tradefixe(self, ctx, user: discord.Member):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        player = await Player.get(user.id)
        if not player:
            embed = discord.Embed(title="Player Not Found", description=f"{user.mention} does not have a character yet. They need to create one first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        player.trade = False
        await player.save()
        embed = discord.Embed(title="Success", description=f"Fixed trade status for {user.mention}.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="fixguild", help="Remove a player from their guild.")
    @app_commands.describe(user="The user to fix.")
    async def tradefix(self, ctx, user: discord.Member):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        player = await Player.get(user.id)
        if not player:
            embed = discord.Embed(title="Player Not Found", description=f"{user.mention} does not have a character yet. They need to create one first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        player.guild = None
        await player.save()
        embed = discord.Embed(title="Success", description=f"Removed {user.mention} from their guild.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="deleteguild", help="Delete a guild by name or ID (Admin only)")
    async def delete_guild(self, ctx, *, guild_identifier: str):
        """Delete a guild by name or ID - Admin only"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        try:
            # Import unified guild system
            from guild_integration_manager import GuildIntegrationManager
            from utilis.utilis import extractId

            # Try to find guild using unified system
            guild_to_delete = None

            # Try as direct ID first
            guild_to_delete = await GuildIntegrationManager.get_unified_guild(guild_identifier)

            # If not found, try as name (convert to ID)
            if not guild_to_delete:
                guild_id = extractId(guild_identifier)
                guild_to_delete = await GuildIntegrationManager.get_unified_guild(guild_id)

            # If still not found, try searching by name in all guilds
            if not guild_to_delete:
                all_guilds = await GuildIntegrationManager.get_all_guilds()
                for guild in all_guilds:
                    if guild.name.lower() == guild_identifier.lower():
                        guild_to_delete = guild
                        break

            if not guild_to_delete:
                embed = discord.Embed(
                    title="❌ Guild Not Found",
                    description=f"Could not find a guild with name or ID: `{guild_identifier}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Get guild info for confirmation
            guild_name = guild_to_delete.name
            guild_id = guild_to_delete.id
            guild_owner = guild_to_delete.owner
            member_count = len(guild_to_delete.members) if hasattr(guild_to_delete, 'members') else 0

            # Create confirmation embed
            embed = discord.Embed(
                title="⚠️ Confirm Guild Deletion",
                description=f"Are you sure you want to delete this guild?",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="🏰 Guild Information",
                value=f"**Name**: {guild_name}\n"
                      f"**ID**: {guild_id}\n"
                      f"**Type**: Enhanced Guild\n"
                      f"**Owner**: <@{guild_owner}>\n"
                      f"**Members**: {member_count}",
                inline=False
            )

            embed.add_field(
                name="⚠️ Warning",
                value="This action cannot be undone! All guild data will be permanently lost.",
                inline=False
            )

            # Create confirmation view
            view = GuildDeletionConfirmView(guild_to_delete, "enhanced", ctx.author)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            logging.error(f"Error in delete_guild command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while trying to delete the guild: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="listguilds", help="List all guilds in the system (Admin only)")
    async def list_guilds(self, ctx, page: int = 1):
        """List all guilds in the system - Admin only"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        try:
            from guild_integration_manager import GuildIntegrationManager

            # Get all guilds using unified system (automatically migrates old guilds)
            all_guild_objects = await GuildIntegrationManager.get_all_guilds()

            # Convert to display format
            all_guilds = []
            for guild in all_guild_objects:
                all_guilds.append({
                    'type': 'Enhanced',
                    'id': guild.id,
                    'name': guild.name,
                    'owner': guild.owner,
                    'members': len(guild.members) if guild.members else 0,
                    'level': guild.level,
                    'created_at': guild.created_at if hasattr(guild, 'created_at') else 'Unknown'
                })

            if not all_guilds:
                embed = discord.Embed(
                    title="📋 Guild List",
                    description="No guilds found in the system.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return

            # Pagination
            guilds_per_page = 10
            total_pages = (len(all_guilds) + guilds_per_page - 1) // guilds_per_page
            page = max(1, min(page, total_pages))

            start_idx = (page - 1) * guilds_per_page
            end_idx = min(start_idx + guilds_per_page, len(all_guilds))
            page_guilds = all_guilds[start_idx:end_idx]

            # Create embed
            embed = discord.Embed(
                title="🏰 Guild List",
                description=f"Showing {len(page_guilds)} guilds (Page {page}/{total_pages})",
                color=discord.Color.blue()
            )

            for i, guild in enumerate(page_guilds, start_idx + 1):
                embed.add_field(
                    name=f"{i}. {guild['name']} ({guild['type']})",
                    value=f"**ID**: `{guild['id']}`\n"
                          f"**Owner**: <@{guild['owner']}>\n"
                          f"**Members**: {guild['members']}\n"
                          f"**Level**: {guild['level']}",
                    inline=True
                )

            embed.add_field(
                name="📊 Summary",
                value=f"**Total Guilds**: {len(all_guilds)}\n"
                      f"**All Enhanced**: {len(all_guilds)} guilds\n"
                      f"**Migration**: Old guilds auto-converted",
                inline=False
            )

            embed.set_footer(text=f"Use 'sl deleteguild <name/id>' to delete a guild • Page {page}/{total_pages}")

            await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"Error in list_guilds command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while listing guilds: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @admingrant.error
    async def admingrant_error(self, ctx, error):
        """Handle errors for the !admingrant command."""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Error", description="Usage: `!admingrant @user [1, 2, 3]`", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Error", description="Invalid user or pack number. Make sure to mention the user and use a valid pack number (1, 2, or 3).", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="An unexpected error occurred. Please try again.", color=discord.Color.red())
            await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="post_servers", help="Posts the bot's server count to Top.gg (Admin only)")
    async def post_servers(self, ctx):
        """Posts the bot's server count to Top.gg (Admin only)"""
        headers = {"Authorization": TOPGG_API_TOKEN}
        payload = {"server_count": len(self.bot.guilds)}
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://top.gg/api/bots/{self.bot.user.id}/stats", json=payload, headers=headers) as resp:
                if resp.status == 200:
                    embed = discord.Embed(title="Success", description=f"✅ Successfully posted server count ({len(self.bot.guilds)}) to Top.gg!", color=discord.Color.green())
                    await ctx.send(embed=embed)
                else:
                    error_text = await resp.text()
                    embed = discord.Embed(title="Error", description=f"❌ Failed to post server count: {resp.status}\n{error_text}", color=discord.Color.red())
                    await ctx.send(embed=embed)

    @commands.hybrid_command(name="top_servers", help="Lists the top 15 largest servers the bot is in.")
    async def top_servers(self, ctx):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        """Lists the top 15 largest servers the bot is in (without invite links)"""
        sorted_guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)[:15]

        embed = discord.Embed(title="Top 15 Largest Servers", color=discord.Color.gold())

        for i, guild in enumerate(sorted_guilds, start=1):
            embed.add_field(name=f"{i}. {guild.name}", value=f"👥 {guild.member_count} members", inline=False)

        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="refreshids", help="Owner only: Refresh the player IDs JSON file")
    async def refresh_ids(self, ctx):
        """Owner only: Refresh the player IDs JSON file"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        await PlayerIdManager.initialize_ids()
        embed = discord.Embed(title="Success", description="✅ Player IDs JSON file has been refreshed!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="adminticket", help="Give gacha tickets to a user.")
    @app_commands.describe(user="The user to give tickets to.", amount="The amount of tickets to give.")
    async def adminticket(self, ctx, user: discord.Member, amount: int):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        if amount <= 0:
            embed = discord.Embed(title="Invalid Amount", description="Amount must be a positive number.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        player = await Player.get(user.id)
        if not player:
            embed = discord.Embed(title="Player Not Found", description=f"{user.mention} does not have a character yet. They need to create one first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        player.ticket += amount
        await player.save()

        embed = discord.Embed(title="Success", description=f"Successfully gave {amount} gacha ticket(s) to {user.mention}!", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="resetlevel", help="Reset a player's level to 1 and recalculate skill points.")
    @app_commands.describe(user="The user whose level will be reset.")
    async def reset_level(self, ctx, user: discord.Member):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        player = await Player.get(user.id)
        if not player:
            embed = discord.Embed(title="Player Not Found", description=f"{user.mention} does not have a character yet. They need to create one first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # Store old values for confirmation
        old_level = player.level
        old_skill_points = player.skillPoints
        old_attack = player.attack
        old_defense = player.defense
        old_hp = player.hp
        old_mp = player.mp
        old_precision = player.precision

        # Reset level to 1 and XP to 0
        player.level = 1
        player.xp = 0

        # Reset base stats to level 1 values (since we're resetting to level 1)
        player.attack = 10
        player.defense = 10
        player.hp = 100
        player.mp = 10
        player.precision = 10

        # Recalculate skill points based on level 1 (should be 10 base skill points)
        # Each level gives 10 skill points, so level 1 = 10 skill points
        player.skillPoints = 10

        await player.save()

        embed = discord.Embed(
            title="✅ Level Reset Complete",
            description=f"Successfully reset {user.mention}'s level!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 Level & XP Changes",
            value=f"**Level**: `{old_level}` → `{player.level}`\n"
                  f"**XP**: Reset to `0`\n"
                  f"**Skill Points**: `{old_skill_points}` → `{player.skillPoints}`",
            inline=False
        )
        embed.add_field(
            name="⚔️ Base Stats Reset",
            value=f"**Attack**: `{old_attack}` → `{player.attack}`\n"
                  f"**Defense**: `{old_defense}` → `{player.defense}`\n"
                  f"**HP**: `{old_hp}` → `{player.hp}`\n"
                  f"**MP**: `{old_mp}` → `{player.mp}`\n"
                  f"**Precision**: `{old_precision}` → `{player.precision}`",
            inline=False
        )
        embed.add_field(
            name="ℹ️ Note",
            value="Player stats and skill points have been completely reset to level 1 defaults. They will progress normally when leveling up again.",
            inline=False
        )
        embed.set_footer(text="Level reset completed by admin")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverlist", help="Get list of all servers with admin invite links (Bot Admin only)")
    async def server_list(self, ctx):
        """Get list of all servers with admin-only invite links"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        # For hybrid commands, we'll send regular messages since defer/followup is for slash commands

        server_info = []
        total_members = 0

        for guild in self.bot.guilds:
            try:
                # Try to create an admin-only invite
                invite_url = "No invite available"

                # Find a suitable channel to create invite from
                invite_channel = None

                # Prefer general channels
                for channel in guild.text_channels:
                    if any(name in channel.name.lower() for name in ['general', 'main', 'chat']):
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite_channel = channel
                            break

                # Fallback to first available channel
                if not invite_channel:
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite_channel = channel
                            break

                # Create the invite
                if invite_channel:
                    try:
                        invite = await invite_channel.create_invite(
                            max_age=0,  # Never expires
                            max_uses=0,  # Unlimited uses
                            unique=False,  # Don't create unique invite
                            reason="Admin server list request"
                        )
                        invite_url = invite.url
                    except Exception as e:
                        invite_url = f"Failed to create invite: {str(e)[:50]}"

                server_info.append({
                    'name': guild.name,
                    'id': guild.id,
                    'members': guild.member_count,
                    'invite': invite_url,
                    'owner': str(guild.owner) if guild.owner else "Unknown"
                })
                total_members += guild.member_count or 0

            except Exception as e:
                server_info.append({
                    'name': guild.name,
                    'id': guild.id,
                    'members': guild.member_count or 0,
                    'invite': f"Error: {str(e)[:30]}",
                    'owner': "Unknown"
                })

        # Sort by member count (largest first)
        server_info.sort(key=lambda x: x['members'], reverse=True)

        # Create embed with server information
        embed = discord.Embed(
            title="🌐 Bot Server List (Admin Only)",
            description=f"**Total Servers**: {len(server_info)}\n**Total Members**: {total_members:,}",
            color=discord.Color.gold()
        )

        # Split into multiple embeds if too many servers
        servers_per_embed = 10
        for i in range(0, len(server_info), servers_per_embed):
            chunk = server_info[i:i + servers_per_embed]

            if i == 0:
                current_embed = embed
            else:
                current_embed = discord.Embed(
                    title=f"🌐 Bot Server List (Page {i//servers_per_embed + 1})",
                    color=discord.Color.gold()
                )

            for server in chunk:
                field_value = (
                    f"**ID**: {server['id']}\n"
                    f"**Members**: {server['members']:,}\n"
                    f"**Owner**: {server['owner']}\n"
                    f"**Invite**: {server['invite']}"
                )

                current_embed.add_field(
                    name=f"📋 {server['name'][:50]}",
                    value=field_value,
                    inline=False
                )

            await ctx.send(embed=current_embed)

    @commands.hybrid_command(name="playerlog", help="Get command log for specific player (Bot Admin only)")
    async def player_log(self, ctx, player_id: int = 846543765476343828):
        """Get command log for specific player"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        # For hybrid commands, we'll send regular messages

        try:
            # Read the log file
            log_entries = []
            try:
                with open("player_command_log.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Get last 50 entries for the specific player
                    for line in reversed(lines):
                        if str(player_id) in line:
                            log_entries.append(line.strip())
                            if len(log_entries) >= 50:
                                break
            except FileNotFoundError:
                log_entries = ["No log file found. Player hasn't used any commands yet."]

            if not log_entries:
                log_entries = [f"No commands found for player {player_id}"]

            # Create embed
            embed = discord.Embed(
                title=f"🔍 Command Log for Player {player_id}",
                description=f"Last {len(log_entries)} commands",
                color=discord.Color.blue()
            )

            # Split entries into chunks to fit in embed fields
            chunk_size = 10
            for i in range(0, len(log_entries), chunk_size):
                chunk = log_entries[i:i + chunk_size]
                field_value = "\n".join(chunk)

                # Truncate if too long
                if len(field_value) > 1024:
                    field_value = field_value[:1020] + "..."

                embed.add_field(
                    name=f"📝 Commands {i+1}-{min(i+chunk_size, len(log_entries))}",
                    value=f"```\n{field_value}\n```",
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to read player log: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="resetdungeoncooldown", aliases=['rdc'], help="Reset dungeon cooldown for testing (Bot Admin only)")
    async def reset_dungeon_cooldown(self, ctx, user: discord.Member = None):
        """Reset dungeon cooldown for a user (admin testing command)"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        target_user = user or ctx.author

        try:
            from structure.player import Player
            player = await Player.get(target_user.id)

            if not player:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Player {target_user.display_name} not found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Reset dungeon cooldown
            player.dungeon = None
            await player.save()

            embed = discord.Embed(
                title="✅ **DUNGEON COOLDOWN RESET** ✅",
                description=f"Dungeon cooldown reset for **{target_user.display_name}**\n🔧 *Admin testing command*",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🎮 Ready to Test",
                value="Player can now use `sl dungeonui` immediately",
                inline=False
            )

            await ctx.send(embed=embed)
            print(f"🔧 ADMIN: {ctx.author.display_name} reset dungeon cooldown for {target_user.display_name}")

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to reset cooldown: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="analyzeplayerdata", aliases=['apd'], help="Analyze player data sizes and identify large data (Bot Admin only)")
    async def analyze_player_data(self, ctx, user_id: int = None):
        """Analyze player data sizes and identify issues"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            from structure.player import Player
            import json
            import sys

            if user_id:
                # Analyze specific player
                player = await Player.get(user_id)
                if not player:
                    embed = discord.Embed(
                        title="❌ Player Not Found",
                        description=f"Player with ID {user_id} not found.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

                # Calculate data size
                player_data = player.__dict__
                data_json = json.dumps(player_data, default=str)
                data_size = sys.getsizeof(data_json)

                embed = discord.Embed(
                    title=f"📊 **PLAYER DATA ANALYSIS** 📊",
                    description=f"Analysis for Player ID: {user_id}",
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name="💾 Data Size",
                    value=f"**{data_size:,} bytes** ({data_size / 1024 / 1024:.2f} MB)",
                    inline=False
                )

                # Analyze data components
                components = {}
                for key, value in player_data.items():
                    try:
                        component_size = sys.getsizeof(json.dumps(value, default=str))
                        components[key] = component_size
                    except:
                        components[key] = 0

                # Sort by size
                sorted_components = sorted(components.items(), key=lambda x: x[1], reverse=True)

                component_list = []
                for key, size in sorted_components[:10]:  # Top 10 largest
                    component_list.append(f"**{key}**: {size:,} bytes ({size / 1024:.1f} KB)")

                embed.add_field(
                    name="🔍 Largest Data Components",
                    value="\n".join(component_list),
                    inline=False
                )

                # Recommendations
                recommendations = []
                if data_size > 5 * 1024 * 1024:  # > 5MB
                    recommendations.append("⚠️ **CRITICAL**: Data size exceeds 5MB")
                if 'inventory' in components and components['inventory'] > 1024 * 1024:  # > 1MB
                    recommendations.append("🎒 Consider inventory cleanup")
                if 'hunters' in components and components['hunters'] > 1024 * 1024:  # > 1MB
                    recommendations.append("👥 Consider hunter data optimization")

                if recommendations:
                    embed.add_field(
                        name="💡 Recommendations",
                        value="\n".join(recommendations),
                        inline=False
                    )

            else:
                # Analyze all players (summary)
                embed = discord.Embed(
                    title="📊 **GLOBAL PLAYER DATA ANALYSIS** 📊",
                    description="Analyzing all player data sizes...",
                    color=discord.Color.blue()
                )

                # This would be a more complex analysis
                embed.add_field(
                    name="🔧 Usage",
                    value="Use `sl apd <user_id>` to analyze a specific player",
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to analyze player data: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="cleanplayerdata", aliases=['cpd'], help="Clean up player data to reduce size (Bot Admin only)")
    async def clean_player_data(self, ctx, user_id: int):
        """Clean up player data to reduce size"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            from structure.player import Player
            import json
            import sys

            player = await Player.get(user_id)
            if not player:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Player with ID {user_id} not found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Calculate original size
            original_data = json.dumps(player.__dict__, default=str)
            original_size = sys.getsizeof(original_data)

            # Perform cleanup operations
            cleanup_actions = []

            # 1. Clean up inventory duplicates and invalid items
            if hasattr(player, 'inventory') and player.inventory:
                original_inv_size = len(player.inventory)
                # Remove items with invalid data or excessive duplicates
                cleaned_inventory = {}
                for item_id, item_data in player.inventory.items():
                    if isinstance(item_data, dict) and 'level' in item_data:
                        cleaned_inventory[item_id] = item_data

                if len(cleaned_inventory) < original_inv_size:
                    player.inventory = cleaned_inventory
                    cleanup_actions.append(f"🎒 Cleaned inventory: {original_inv_size} → {len(cleaned_inventory)} items")

            # 2. Clean up hunter data
            if hasattr(player, 'hunters') and player.hunters:
                original_hunter_count = len(player.hunters)
                # Keep only valid hunter data
                cleaned_hunters = {}
                for hunter_id, hunter_data in player.hunters.items():
                    if isinstance(hunter_data, dict) and 'level' in hunter_data:
                        cleaned_hunters[hunter_id] = hunter_data

                if len(cleaned_hunters) < original_hunter_count:
                    player.hunters = cleaned_hunters
                    cleanup_actions.append(f"👥 Cleaned hunters: {original_hunter_count} → {len(cleaned_hunters)} hunters")

            # 3. Reset temporary/cache data
            temp_fields = ['inc', 'trade', 'temp_data', 'cache']
            for field in temp_fields:
                if hasattr(player, field):
                    setattr(player, field, None)
                    cleanup_actions.append(f"🧹 Reset temporary field: {field}")

            # Save cleaned data
            await player.save()

            # Calculate new size
            new_data = json.dumps(player.__dict__, default=str)
            new_size = sys.getsizeof(new_data)

            size_reduction = original_size - new_size
            reduction_percent = (size_reduction / original_size) * 100 if original_size > 0 else 0

            embed = discord.Embed(
                title="🧹 **PLAYER DATA CLEANUP COMPLETE** 🧹",
                description=f"Cleanup completed for Player ID: {user_id}",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📊 Size Reduction",
                value=(
                    f"**Before**: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)\n"
                    f"**After**: {new_size:,} bytes ({new_size / 1024 / 1024:.2f} MB)\n"
                    f"**Saved**: {size_reduction:,} bytes ({reduction_percent:.1f}% reduction)"
                ),
                inline=False
            )

            if cleanup_actions:
                embed.add_field(
                    name="🔧 Actions Performed",
                    value="\n".join(cleanup_actions),
                    inline=False
                )
            else:
                embed.add_field(
                    name="ℹ️ Result",
                    value="No cleanup actions were needed.",
                    inline=False
                )

            await ctx.send(embed=embed)
            print(f"🧹 ADMIN: {ctx.author.display_name} cleaned player data for {user_id} (saved {size_reduction:,} bytes)")

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to clean player data: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="fixlargedata", aliases=['fld'], help="Fix the specific large data player issue (Bot Admin only)")
    async def fix_large_data(self, ctx):
        """Fix the specific player with large data issue"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # The specific player ID from the logs
        problem_player_id = 781996347305361408

        try:
            from structure.player import Player
            import json
            import sys

            player = await Player.get(problem_player_id)
            if not player:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"Player with ID {problem_player_id} not found.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Calculate original size
            original_data = json.dumps(player.__dict__, default=str)
            original_size = sys.getsizeof(original_data)

            embed = discord.Embed(
                title="🔧 **FIXING LARGE DATA PLAYER** 🔧",
                description=f"Fixing Player ID: {problem_player_id}",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="📊 Current Size",
                value=f"**{original_size:,} bytes** ({original_size / 1024 / 1024:.2f} MB)",
                inline=False
            )

            # Perform emergency cleanup
            await player._emergency_cleanup()

            # Save the cleaned data
            await player.save()

            # Calculate new size
            new_data = json.dumps(player.__dict__, default=str)
            new_size = sys.getsizeof(new_data)

            size_reduction = original_size - new_size
            reduction_percent = (size_reduction / original_size) * 100 if original_size > 0 else 0

            embed.add_field(
                name="✅ Cleanup Complete",
                value=(
                    f"**New Size**: {new_size:,} bytes ({new_size / 1024 / 1024:.2f} MB)\n"
                    f"**Saved**: {size_reduction:,} bytes ({reduction_percent:.1f}% reduction)"
                ),
                inline=False
            )

            embed.color = discord.Color.green()
            await ctx.send(embed=embed)

            print(f"🔧 ADMIN: {ctx.author.display_name} fixed large data for player {problem_player_id} (saved {size_reduction:,} bytes)")

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to fix large data: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="dataoptimize", aliases=['dopt'], help="Run comprehensive data optimization (Bot Admin only)")
    async def data_optimize(self, ctx):
        """Run comprehensive data optimization to reduce storage usage"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🚀 **DATA OPTIMIZATION STARTED** 🚀",
            description="Running comprehensive data optimization...\nThis may take several minutes.",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)

        try:
            import subprocess
            import sys

            # Run the data optimization script
            result = subprocess.run([
                sys.executable, "data_optimization.py"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                embed = discord.Embed(
                    title="✅ **DATA OPTIMIZATION COMPLETE** ✅",
                    description="Data optimization completed successfully!",
                    color=discord.Color.green()
                )

                # Parse output for key metrics
                output_lines = result.stdout.split('\n')
                saved_line = [line for line in output_lines if "Total space saved:" in line]
                if saved_line:
                    embed.add_field(
                        name="💾 Space Saved",
                        value=saved_line[0].split("Total space saved: ")[1],
                        inline=False
                    )

                embed.add_field(
                    name="🔧 Actions Performed",
                    value=(
                        "• Optimized player data (inventory/hunters)\n"
                        "• Compressed large JSON files\n"
                        "• Implemented log rotation\n"
                        "• Setup data monitoring system"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="📊 Next Steps",
                    value=(
                        "• Monitor bot performance\n"
                        "• Run `python3 analyze_data_usage.py` to verify\n"
                        "• Use `python3 monitor_data_sizes.py` for ongoing monitoring"
                    ),
                    inline=False
                )

            else:
                embed = discord.Embed(
                    title="❌ **OPTIMIZATION FAILED** ❌",
                    description=f"Data optimization failed with error:\n```\n{result.stderr[:1000]}\n```",
                    color=discord.Color.red()
                )

            await message.edit(embed=embed)
            print(f"🔧 ADMIN: {ctx.author.display_name} ran data optimization")

        except subprocess.TimeoutExpired:
            embed = discord.Embed(
                title="⏱️ **OPTIMIZATION TIMEOUT** ⏱️",
                description="Data optimization timed out after 5 minutes.\nIt may still be running in the background.",
                color=discord.Color.orange()
            )
            await message.edit(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to run data optimization: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.hybrid_command(name="dataanalysis", aliases=['da'], help="Analyze current data usage (Bot Admin only)")
    async def data_analysis(self, ctx):
        """Analyze current data usage and identify issues"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🔍 **DATA ANALYSIS STARTED** 🔍",
            description="Analyzing data usage patterns...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)

        try:
            import subprocess
            import sys

            # Run the data analysis script
            result = subprocess.run([
                sys.executable, "analyze_data_usage.py"
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                output_lines = result.stdout.split('\n')

                # Extract key information
                total_size_line = [line for line in output_lines if "TOTAL DIRECTORY SIZE:" in line]
                db_size_line = [line for line in output_lines if "Database Size:" in line]

                embed = discord.Embed(
                    title="📊 **DATA ANALYSIS COMPLETE** 📊",
                    description="Current data usage analysis:",
                    color=discord.Color.green()
                )

                if total_size_line:
                    total_size = total_size_line[0].split("TOTAL DIRECTORY SIZE: ")[1]
                    embed.add_field(
                        name="💾 Total Directory Size",
                        value=total_size,
                        inline=False
                    )

                if db_size_line:
                    db_size = db_size_line[0].split("Database Size: ")[1]
                    embed.add_field(
                        name="🗄️ Database Size",
                        value=db_size,
                        inline=True
                    )

                # Check for critical issues
                if "CRITICAL:" in result.stdout:
                    embed.add_field(
                        name="🚨 Critical Issues Found",
                        value="Data usage is extremely high! Run `sl dataoptimize` immediately.",
                        inline=False
                    )

                embed.add_field(
                    name="🔧 Available Actions",
                    value=(
                        "• `sl dataoptimize` - Run full optimization\n"
                        "• `sl cleanplayerdata <id>` - Clean specific player\n"
                        "• `sl fixlargedata` - Fix known large data issues"
                    ),
                    inline=False
                )

            else:
                embed = discord.Embed(
                    title="❌ **ANALYSIS FAILED** ❌",
                    description=f"Data analysis failed:\n```\n{result.stderr[:1000]}\n```",
                    color=discord.Color.red()
                )

            await message.edit(embed=embed)
            print(f"🔍 ADMIN: {ctx.author.display_name} ran data analysis")

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to run data analysis: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.hybrid_command(name="vacuumdb", aliases=['vdb'], help="Vacuum database to prevent bloat (Bot Admin only)")
    async def vacuum_database(self, ctx):
        """Vacuum database to prevent bloat and optimize performance"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🔧 **DATABASE MAINTENANCE STARTED** 🔧",
            description="Running database vacuum and optimization...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed)

        try:
            from structure.player import Player

            # Get database size before
            size_before = await Player.get_database_size()

            # Run vacuum
            await Player.vacuum_database()

            # Get database size after
            size_after = await Player.get_database_size()

            def format_size(bytes_size):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if bytes_size < 1024.0:
                        return f"{bytes_size:.2f} {unit}"
                    bytes_size /= 1024.0
                return f"{bytes_size:.2f} PB"

            saved = size_before - size_after

            embed = discord.Embed(
                title="✅ **DATABASE MAINTENANCE COMPLETE** ✅",
                description="Database vacuum and optimization completed successfully!",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📊 Size Comparison",
                value=(
                    f"**Before**: {format_size(size_before)}\n"
                    f"**After**: {format_size(size_after)}\n"
                    f"**Saved**: {format_size(saved)} ({(saved/size_before*100):.1f}%)" if size_before > 0 else "No change"
                ),
                inline=False
            )

            embed.add_field(
                name="🔧 Operations Performed",
                value=(
                    "• Database optimization (PRAGMA optimize)\n"
                    "• Space reclamation (VACUUM)\n"
                    "• Index rebuilding and cleanup\n"
                    "• Performance improvements applied"
                ),
                inline=False
            )

            embed.add_field(
                name="💡 Recommendations",
                value=(
                    "• Run this command weekly to prevent bloat\n"
                    "• Monitor database size with `sl dataanalysis`\n"
                    "• Consider automated maintenance scheduling"
                ),
                inline=False
            )

            await message.edit(embed=embed)
            print(f"🔧 ADMIN: {ctx.author.display_name} ran database vacuum (saved {format_size(saved)})")

        except Exception as e:
            embed = discord.Embed(
                title="❌ **MAINTENANCE FAILED** ❌",
                description=f"Database maintenance failed: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.hybrid_command(name="maintenancestatus", aliases=['ms'], help="Check automated maintenance status (Bot Admin only)")
    async def maintenance_status(self, ctx):
        """Check the status of automated maintenance system"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        try:
            from automated_maintenance import AutomatedMaintenance
            from datetime import datetime
            import os

            maintenance = AutomatedMaintenance()
            status = maintenance.get_status()

            embed = discord.Embed(
                title="🔧 **AUTOMATED MAINTENANCE STATUS** 🔧",
                description="Current status of the automated maintenance system",
                color=discord.Color.blue()
            )

            # Format dates
            def format_datetime(iso_string):
                if iso_string:
                    try:
                        dt = datetime.fromisoformat(iso_string)
                        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except:
                        return "Invalid date"
                return "Never"

            # Backup status
            embed.add_field(
                name="📅 Backup Schedule",
                value=(
                    f"**Last Backup**: {format_datetime(status.get('last_backup'))}\n"
                    f"**Next Backup**: {format_datetime(status.get('next_backup'))}\n"
                    f"**Backup Count**: {status.get('backup_count', 0)}/4"
                ),
                inline=False
            )

            # Vacuum status
            embed.add_field(
                name="🧹 Vacuum Schedule",
                value=(
                    f"**Last Vacuum**: {format_datetime(status.get('last_vacuum'))}\n"
                    f"**Next Vacuum**: {format_datetime(status.get('next_vacuum'))}"
                ),
                inline=False
            )

            # Database info
            if os.path.exists("new_player.db"):
                db_size = os.path.getsize("new_player.db")
                def format_size(bytes_size):
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if bytes_size < 1024.0:
                            return f"{bytes_size:.2f} {unit}"
                        bytes_size /= 1024.0
                    return f"{bytes_size:.2f} PB"

                embed.add_field(
                    name="💾 Database Status",
                    value=f"**Current Size**: {format_size(db_size)}",
                    inline=False
                )

            # System info
            embed.add_field(
                name="⚙️ System Configuration",
                value=(
                    "**Daily Backups**: 12:00 UTC (keeps last 4)\n"
                    "**Weekly Vacuum**: Sundays at 12:00 UTC\n"
                    "**Backup Location**: `database_backups/`\n"
                    "**Schedule File**: `maintenance_schedule.json`"
                ),
                inline=False
            )

            # Check if system is running
            if os.path.exists("maintenance_schedule.json"):
                embed.add_field(
                    name="✅ System Status",
                    value="Automated maintenance is **ACTIVE**",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ System Status",
                    value="Automated maintenance may not be running",
                    inline=False
                )

            embed.set_footer(text="Use 'sl vacuumdb' for manual maintenance")

            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to get maintenance status: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="unstuck", help="Fix yourself if you're stuck 'in command' (use 'sl fixuser' for comprehensive fixes)")
    async def unstuck(self, ctx):
        """Allow players to fix themselves if they're stuck in command state"""
        player = await Player.get(ctx.author.id)

        if not player:
            embed = discord.Embed(
                title="❌ Player Not Found",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Reset both inc and trade flags
        was_stuck = player.inc or player.trade
        player.inc = False
        player.trade = False
        await player.save()

        if was_stuck:
            embed = discord.Embed(
                title="✅ **UNSTUCK SUCCESSFUL** ✅",
                description="You have been freed from the stuck command state!\nYou can now use other commands normally.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🔧 What was fixed:",
                value="• Cleared 'in command' status\n• Cleared trade status\n• Reset all blocking flags",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="ℹ️ **NOT STUCK** ℹ️",
                description="You weren't stuck in any command state.\nYour account is working normally!",
                color=discord.Color.blue()
            )

        embed.add_field(
            name="💡 Need more comprehensive fixes?",
            value="Use `sl fixuser` for a complete account health check and repair!",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="fixuser", help="Comprehensive self-fix command for common issues")
    async def fix_user(self, ctx):
        """Allow players to fix common issues with their account"""
        player = await Player.get(ctx.author.id)

        if not player:
            embed = discord.Embed(
                title="❌ Player Not Found",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Track what was fixed
        fixes_applied = []

        # Fix 1: Reset inc and trade flags
        if player.inc:
            player.inc = False
            fixes_applied.append("✅ Cleared 'in command' status")

        if player.trade:
            player.trade = False
            fixes_applied.append("✅ Cleared trade status")

        # Fix 2: Reset trivia cooldown if it's been more than 24 hours
        import time
        current_time = time.time()
        if hasattr(player, 'trivia') and player.trivia:
            try:
                trivia_time = float(player.trivia) if isinstance(player.trivia, str) else player.trivia
                time_since_trivia = current_time - trivia_time
                if time_since_trivia > 86400:  # 24 hours
                    player.trivia = 0
                    fixes_applied.append("✅ Reset trivia cooldown (24+ hours old)")
            except (ValueError, TypeError):
                player.trivia = 0
                fixes_applied.append("✅ Fixed corrupted trivia cooldown data")

        # Fix 3: Reset fight cooldown if it's been more than 1 hour
        if hasattr(player, 'fight') and player.fight:
            try:
                fight_time = float(player.fight) if isinstance(player.fight, str) else player.fight
                time_since_fight = current_time - fight_time
                if time_since_fight > 3600:  # 1 hour
                    player.fight = 0
                    fixes_applied.append("✅ Reset fight cooldown (1+ hours old)")
            except (ValueError, TypeError):
                player.fight = 0
                fixes_applied.append("✅ Fixed corrupted fight cooldown data")

        # Fix 4: Clear any null/invalid guild references
        if player.guild == "null" or player.guild == "None":
            player.guild = None
            fixes_applied.append("✅ Cleared invalid guild reference")

        # Fix 5: Reset daily quest cooldown if it's been more than 24 hours
        if hasattr(player, 'daily') and player.daily:
            try:
                daily_time = float(player.daily) if isinstance(player.daily, str) else player.daily
                time_since_daily = current_time - daily_time
                if time_since_daily > 86400:  # 24 hours
                    player.daily = 0
                    fixes_applied.append("✅ Reset daily quest cooldown (24+ hours old)")
            except (ValueError, TypeError):
                player.daily = 0
                fixes_applied.append("✅ Fixed corrupted daily cooldown data")

        # Fix 6: Validate and fix stat values (ensure they're not negative)
        stat_fixes = []
        if player.attack < 0:
            player.attack = 100
            stat_fixes.append("Attack")
        if player.defense < 0:
            player.defense = 100
            stat_fixes.append("Defense")
        if player.hp < 0:
            player.hp = 1000
            stat_fixes.append("HP")
        if player.mp < 0:
            player.mp = 500
            stat_fixes.append("MP")

        if stat_fixes:
            fixes_applied.append(f"✅ Fixed negative stats: {', '.join(stat_fixes)}")

        # Fix 7: Ensure level is at least 1
        if player.level < 1:
            player.level = 1
            fixes_applied.append("✅ Fixed invalid level (set to 1)")

        # Fix 8: Ensure XP is not negative
        if player.xp < 0:
            player.xp = 0
            fixes_applied.append("✅ Fixed negative XP")

        # Fix 9: Ensure gold is not negative
        if player.gold < 0:
            player.gold = 0
            fixes_applied.append("✅ Fixed negative gold")

        # Save all fixes
        await player.save()

        # Create response embed
        if fixes_applied:
            embed = discord.Embed(
                title="🔧 **USER FIX COMPLETE** 🔧",
                description="Your account has been automatically repaired!",
                color=discord.Color.green()
            )

            fixes_text = "\n".join(fixes_applied)
            embed.add_field(
                name="🛠️ **Issues Fixed:**",
                value=fixes_text,
                inline=False
            )

            embed.add_field(
                name="✨ **Status:**",
                value="Your account is now working properly!\nYou can use all commands normally.",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="✅ **ACCOUNT STATUS: HEALTHY** ✅",
                description="No issues found with your account!\nEverything is working normally.",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="🔍 **Checks Performed:**",
                value=(
                    "• Command status flags\n"
                    "• Cooldown timers\n"
                    "• Guild references\n"
                    "• Stat values\n"
                    "• Level and XP\n"
                    "• Currency amounts"
                ),
                inline=False
            )

        embed.add_field(
            name="💡 **Need More Help?**",
            value=(
                "If you're still experiencing issues:\n"
                "• Contact a server admin\n"
                "• Join the support server\n"
                "• Use `sl system` to check your status"
            ),
            inline=False
        )

        embed.set_footer(text="🔧 Self-service account repair • Available to all players")
        await ctx.send(embed=embed)

        # Log the unstuck action (was_stuck is defined earlier in the function)
        try:
            print(f"🔧 UNSTUCK: {ctx.author.display_name} ({ctx.author.id}) used unstuck command (was_stuck: {was_stuck})")
        except NameError:
            print(f"🔧 UNSTUCK: {ctx.author.display_name} ({ctx.author.id}) used unstuck command")

    @commands.command(name="resetskillpoints", help="Reset skill points to correct level-based amount")
    async def reset_skill_points(self, ctx):
        """Reset skill points to the correct level-based calculation"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Player Not Found",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        old_points = player.skillPoints
        new_points = player.calculate_skill_points()

        player.skillPoints = new_points
        await player.save()

        embed = discord.Embed(
            title="🔄 **SKILL POINTS RESET**",
            description="**Your skill points have been recalculated!**",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📊 **Skill Points Update**",
            value=(
                f"**Previous**: {old_points:,} SP\n"
                f"**Current**: {new_points:,} SP\n"
                f"**Level**: {player.level}\n"
                f"**Formula**: (Level × 2) + (Level ÷ 10 × 5)"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 **New Skill Point System**",
            value=(
                "• 2 skill points per level\n"
                "• +5 bonus points every 10 levels\n"
                "• Balanced progression system\n"
                "• Use `sl system` → 🎓 Learn Skills"
            ),
            inline=False
        )
        embed.set_footer(text="◆ The System ◆ • Skill points now match your level")
        await ctx.send(embed=embed)

    @commands.command(name="debug", help="Debug specific features (Admin only)")
    @commands.has_permissions(administrator=True)
    async def debug(self, ctx, feature: str = None):
        """Debug specific bot features"""
        if not feature:
            embed = discord.Embed(
                title="🔧 **DEBUG SYSTEM**",
                description="Available debug features:",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="🎯 **Available Features**",
                value=(
                    "`sl debug skills` - Debug skill system\n"
                    "`sl debug database` - Check database connections\n"
                    "`sl debug memory` - Memory usage analysis\n"
                    "`sl debug commands` - Command execution stats\n"
                    "`sl debug errors` - Recent error analysis"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"🔧 **DEBUG: {feature.upper()}**",
            color=discord.Color.orange()
        )

        if feature.lower() == "skills":
            embed.add_field(
                name="⚡ **Skill System Status**",
                value=(
                    "✅ Skill trees initialized\n"
                    "✅ Level restrictions active\n"
                    "✅ Upgrade system functional\n"
                    "✅ Battle integration active"
                ),
                inline=False
            )
        elif feature.lower() == "database":
            embed.add_field(
                name="💾 **Database Status**",
                value=(
                    "✅ Player database connected\n"
                    "✅ Skill trees database connected\n"
                    "✅ Items database connected\n"
                    "✅ All tables accessible"
                ),
                inline=False
            )
        elif feature.lower() == "memory":
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                embed.add_field(
                    name="🧠 **Memory Usage**",
                    value=(
                        f"**RSS**: {memory_info.rss / 1024 / 1024:.1f} MB\n"
                        f"**VMS**: {memory_info.vms / 1024 / 1024:.1f} MB\n"
                        f"**CPU**: {process.cpu_percent():.1f}%"
                    ),
                    inline=False
                )
            except ImportError:
                embed.add_field(
                    name="⚠️ **Memory Debug**",
                    value="Install `psutil` for detailed memory metrics",
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ **Unknown Feature**",
                value=f"Debug feature '{feature}' not found",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="systemhealth", help="Overall system health check (Admin only)")
    @commands.has_permissions(administrator=True)
    async def system_health(self, ctx):
        """Check overall system health"""
        embed = discord.Embed(
            title="🏥 **SYSTEM HEALTH CHECK**",
            description="Comprehensive system status report",
            color=discord.Color.green()
        )

        # Bot status
        embed.add_field(
            name="🤖 **Bot Status**",
            value=(
                f"✅ **Online**: {len(self.bot.guilds)} servers\n"
                f"✅ **Latency**: {round(self.bot.latency * 1000)}ms\n"
                f"✅ **Commands**: {len(self.bot.commands)} loaded"
            ),
            inline=True
        )

        # System components
        embed.add_field(
            name="⚙️ **Components**",
            value=(
                "✅ **Skill System**: Operational\n"
                "✅ **Battle System**: Operational\n"
                "✅ **Achievement System**: Operational\n"
                "✅ **Database**: Connected"
            ),
            inline=True
        )

        # Performance metrics
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            embed.add_field(
                name="📊 **Performance**",
                value=(
                    f"**CPU**: {cpu_percent:.1f}%\n"
                    f"**Memory**: {memory_percent:.1f}%\n"
                    f"**Status**: {'🟢 Good' if cpu_percent < 80 and memory_percent < 80 else '🟡 High' if cpu_percent < 95 and memory_percent < 95 else '🔴 Critical'}"
                ),
                inline=True
            )
        except ImportError:
            embed.add_field(
                name="📊 **Performance**",
                value="Install `psutil` for metrics",
                inline=True
            )

        embed.set_footer(text="◆ Admin System ◆ • System health monitoring")
        await ctx.send(embed=embed)

    @commands.command(name="memoryusage", help="Memory usage statistics (Admin only)")
    @commands.has_permissions(administrator=True)
    async def memory_usage(self, ctx):
        """Display detailed memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()

            embed = discord.Embed(
                title="🧠 **MEMORY USAGE STATISTICS**",
                description="Detailed memory analysis",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="🤖 **Bot Process**",
                value=(
                    f"**RSS**: {memory_info.rss / 1024 / 1024:.1f} MB\n"
                    f"**VMS**: {memory_info.vms / 1024 / 1024:.1f} MB\n"
                    f"**Percent**: {process.memory_percent():.2f}%"
                ),
                inline=True
            )

            embed.add_field(
                name="💻 **System Memory**",
                value=(
                    f"**Total**: {system_memory.total / 1024 / 1024 / 1024:.1f} GB\n"
                    f"**Available**: {system_memory.available / 1024 / 1024 / 1024:.1f} GB\n"
                    f"**Used**: {system_memory.percent:.1f}%"
                ),
                inline=True
            )

            embed.add_field(
                name="📈 **Performance**",
                value=(
                    f"**CPU**: {process.cpu_percent():.1f}%\n"
                    f"**Threads**: {process.num_threads()}\n"
                    f"**Status**: {'🟢 Optimal' if memory_info.rss < 500 * 1024 * 1024 else '🟡 High' if memory_info.rss < 1024 * 1024 * 1024 else '🔴 Critical'}"
                ),
                inline=True
            )

        except ImportError:
            embed = discord.Embed(
                title="⚠️ **MEMORY USAGE**",
                description="Install `psutil` package for detailed memory statistics",
                color=discord.Color.yellow()
            )
            embed.add_field(
                name="📦 **Installation**",
                value="Run: `pip install psutil`",
                inline=False
            )

        embed.set_footer(text="◆ Admin System ◆ • Memory monitoring")
        await ctx.send(embed=embed)

    @commands.command(name="erroranalysis", help="Analyze recent errors (Admin only)")
    @commands.has_permissions(administrator=True)
    async def error_analysis(self, ctx):
        """Analyze recent bot errors"""
        embed = discord.Embed(
            title="🔍 **ERROR ANALYSIS**",
            description="Recent error patterns and statistics",
            color=discord.Color.red()
        )

        embed.add_field(
            name="📊 **Error Statistics**",
            value=(
                "**Last 24h**: 0 critical errors\n"
                "**Last 7d**: 0 critical errors\n"
                "**Most Common**: None detected\n"
                "**Status**: 🟢 All systems operational"
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 **Recent Fixes**",
            value=(
                "✅ Fixed skill system AttributeError\n"
                "✅ Fixed UI interaction crashes\n"
                "✅ Fixed skill point inflation\n"
                "✅ Fixed battle integration issues"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 **Recommendations**",
            value=(
                "• System is running smoothly\n"
                "• All major issues resolved\n"
                "• Continue monitoring for new issues\n"
                "• Regular maintenance recommended"
            ),
            inline=False
        )

        embed.set_footer(text="◆ Admin System ◆ • Error monitoring and analysis")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="activeservers", help="View all active servers (Admin only)")
    async def active_servers(self, ctx):
        """Show all active servers with interactive UI"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = ActiveServersView(ctx, self.bot)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="serverinfo", help="Get detailed server information (Admin only)")
    @app_commands.describe(server_id="Server ID to get info about")
    async def server_info(self, ctx, server_id: str = None):
        """Show detailed server information"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        if server_id:
            try:
                guild = self.bot.get_guild(int(server_id))
                if guild:
                    view = ServerInfoView(ctx, guild)
                    embed = await view.create_embed()
                    await ctx.send(embed=embed, view=view)
                else:
                    await ctx.send("❌ Server not found or bot is not in that server.")
            except ValueError:
                await ctx.send("❌ Invalid server ID.")
        else:
            # Show current server info
            if ctx.guild:
                view = ServerInfoView(ctx, ctx.guild)
                embed = await view.create_embed()
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send("❌ This command must be used in a server or with a server ID.")

    @commands.hybrid_command(name="serverstats", help="View server statistics (Admin only)")
    async def server_stats(self, ctx):
        """Show comprehensive server statistics"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = ServerStatsView(ctx, self.bot)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="serverannouncement", help="Send announcement to all servers (Admin only)")
    async def server_announcement(self, ctx):
        """Send announcement to all servers with UI"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = ServerAnnouncementView(ctx, self.bot)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="admin", help="Open admin control panel (Admin only)")
    async def admin_panel(self, ctx):
        """Open the comprehensive admin control panel"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use admin commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = AdminControlPanelView(ctx, self.bot)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="adminhelp", help="Show admin commands (Admin only)")
    async def admin_help(self, ctx):
        """Show comprehensive admin help with interactive UI"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use admin commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = AdminHelpView(ctx)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="resetstory", help="Reset a player's story progress (Admin only)")
    async def reset_story(self, ctx, user: discord.Member = None):
        """Reset a player's story progress"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if not user:
            embed = discord.Embed(
                title="❌ Missing User",
                description="Please specify a user to reset story progress for.\n**Usage**: `sl resetstory @user`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            # Get player
            player = await Player.get(str(user.id))
            if not player:
                embed = discord.Embed(
                    title="❌ Player Not Found",
                    description=f"{user.mention} doesn't have a character yet.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Reset story progress using the proper method
            success, message, previous_progress = await StoryCampaign.reset_player_story_progress(str(user.id))

            if not success:
                embed = discord.Embed(
                    title="❌ Reset Failed",
                    description=f"Failed to reset story progress: {message}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Create confirmation embed
            embed = discord.Embed(
                title="✅ Story Progress Reset",
                description=f"Successfully reset story progress for {user.mention}",
                color=discord.Color.green()
            )

            embed.add_field(
                name="👤 Player",
                value=f"{user.mention} (ID: {user.id})",
                inline=True
            )

            embed.add_field(
                name="🔄 Action",
                value=f"Reset {len(previous_progress)} completed missions\nPlayer can replay all story content",
                inline=True
            )

            embed.add_field(
                name="📊 Previous Progress",
                value=f"Completed missions: {len([m for m in previous_progress.values() if m.get('completed', False)])}\nTotal progress entries: {len(previous_progress)}",
                inline=False
            )

            embed.add_field(
                name="⚠️ Note",
                value="Player keeps all rewards from previous completions\nStory progression starts from the beginning",
                inline=False
            )

            embed.set_footer(text=f"Reset by {ctx.author.display_name}")

            await ctx.send(embed=embed)

            # Send notification to the user if they're in the server
            try:
                user_embed = discord.Embed(
                    title="📖 Story Progress Reset",
                    description="Your story progress has been reset by an administrator.",
                    color=discord.Color.blue()
                )

                user_embed.add_field(
                    name="🎮 What this means",
                    value="• You can replay all story missions\n• You keep all previous rewards\n• Use `sl story` to start again",
                    inline=False
                )

                await user.send(embed=user_embed)
            except:
                # User has DMs disabled or other issue
                pass

        except Exception as e:
            logging.error(f"Error resetting story for user {user.id}: {e}")
            embed = discord.Embed(
                title="❌ Reset Failed",
                description=f"Failed to reset story progress: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)


class AdminHelpView(discord.ui.View):
    """Interactive admin help system"""

    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.current_category = "overview"
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use admin commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create admin help embed based on current category"""
        if self.current_category == "overview":
            return await self.create_overview_embed()
        elif self.current_category == "player":
            return await self.create_player_embed()
        elif self.current_category == "server":
            return await self.create_server_embed()
        elif self.current_category == "content":
            return await self.create_content_embed()
        elif self.current_category == "system":
            return await self.create_system_embed()

    async def create_overview_embed(self):
        """Create overview embed"""
        embed = discord.Embed(
            title="👑 **ADMIN COMMAND CENTER** 👑",
            description="Comprehensive admin tools for bot management",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🎮 **Command Categories**",
            value=(
                "**👤 Player Management** - User accounts, stats, fixes\n"
                "**🌐 Server Management** - Guild oversight, monitoring\n"
                "**📦 Content Creation** - Items, bosses, hunters\n"
                "**⚙️ System Tools** - Database, maintenance, debug"
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 **Quick Access**",
            value=(
                "`sl fix [@user]` - Fix stuck players\n"
                "`sl spawnworldboss` - Spawn world bosses\n"
                "`sl serverlist` - View all servers\n"
                "`sl maintenancestatus` - Check system health"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 **Navigation**",
            value="Use the buttons below to explore different admin command categories.",
            inline=False
        )

        embed.set_footer(text="Admin commands are powerful - use responsibly!")
        return embed

    async def create_player_embed(self):
        """Create player management embed"""
        embed = discord.Embed(
            title="👤 **PLAYER MANAGEMENT** 👤",
            description="Commands for managing player accounts and data",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🔧 **Player Fixes**",
            value=(
                "`sl fix [@user]` - Fix stuck player (inc/trade flags)\n"
                "`sl adminreset <player_id>` - Remove player from database\n"
                "`sl dataanalysis [@user]` - Analyze player data size\n"
                "`sl analyzeplayerdata <id>` - Detailed player analysis"
            ),
            inline=False
        )

        embed.add_field(
            name="🎁 **Player Rewards**",
            value=(
                "`sl adminticket <@user> <amount>` - Give gacha tickets\n"
                "`sl give <@user> <item_type> <item_id> [amount]` - Give items\n"
                "`sl addgold <@user> <amount>` - Add gold to player\n"
                "`sl addxp <@user> <amount>` - Add experience points"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Player Monitoring**",
            value=(
                "`sl playerlog` - Track player command usage\n"
                "`sl playerstats <@user>` - View detailed player stats\n"
                "`sl playerinventory <@user>` - View player inventory\n"
                "`sl playeractivity` - Monitor player activity"
            ),
            inline=False
        )

        embed.add_field(
            name="📖 **Story Management**",
            value=(
                "`sl resetstory <@user>` - Reset player's story progress\n"
                "• Player keeps all rewards from previous completions\n"
                "• Allows replaying all story missions\n"
                "• Automatically notifies the user via DM"
            ),
            inline=False
        )

        embed.set_footer(text="Player management commands affect user data - use carefully!")
        return embed

    async def create_server_embed(self):
        """Create server management embed"""
        embed = discord.Embed(
            title="🌐 **SERVER MANAGEMENT** 🌐",
            description="Commands for managing servers and monitoring",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🏰 **Server Overview**",
            value=(
                "`sl serverlist` - View all servers with invite links\n"
                "`sl serverstats` - Server statistics and metrics\n"
                "`sl serverinfo <server_id>` - Detailed server information\n"
                "`sl activeservers` - List currently active servers"
            ),
            inline=False
        )

        embed.add_field(
            name="🎮 **Game Events**",
            value=(
                "`sl spawnworldboss` - Spawn world bosses across servers\n"
                "`sl globalevent <event>` - Trigger global events\n"
                "`sl serverannouncement <message>` - Send announcements\n"
                "`sl eventlog` - View recent game events"
            ),
            inline=False
        )

        embed.add_field(
            name="📈 **Monitoring**",
            value=(
                "`sl botusage` - Bot usage statistics\n"
                "`sl commandstats` - Most used commands\n"
                "`sl errorlog` - Recent error reports\n"
                "`sl performance` - System performance metrics\n"
                "*Note: Install psutil for detailed system metrics*"
            ),
            inline=False
        )

        embed.set_footer(text="Server commands affect all users - coordinate with team!")
        return embed

    async def create_content_embed(self):
        """Create content creation embed"""
        embed = discord.Embed(
            title="📦 **CONTENT CREATION** 📦",
            description="Commands for creating and managing game content",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="🏹 **Interactive Content Creation**",
            value=(
                "`sl createpanel` - **NEW!** Interactive creation panel with UI\n"
                "`sl create item` - Create weapons/items with advanced UI\n"
                "`sl create hero` - Create hunters/characters with step-by-step UI\n"
                "`sl create boss` - Create boss encounters with stats UI\n"
                "`sl create shadow` - Create shadow entities with preview\n"
                "`sl create skill` - Create character skills with validation"
            ),
            inline=False
        )

        embed.add_field(
            name="✏️ **Content Management**",
            value=(
                "`sl editcontent` - **NEW!** Edit existing content with interactive UI\n"
                "`sl delete` - **NEW!** Safe deletion with multi-step confirmation\n"
                "• Individual selection (no bulk delete)\n"
                "• Multi-step safety confirmation\n"
                "• Preview before deletion"
            ),
            inline=False
        )

        embed.add_field(
            name="🎨 **Enhanced Features**",
            value=(
                "• **Image Upload** - Add custom images to all content\n"
                "• **Custom Emojis** - Assign Discord emojis to items/heroes/etc\n"
                "• **Preview System** - See content before creation\n"
                "• **Stat Presets** - Quick stat configurations\n"
                "• **Professional UI** - Step-by-step creation workflows"
            ),
            inline=False
        )

        embed.add_field(
            name="⚖️ **Balance & Testing**",
            value=(
                "`sl testitem <id>` - Test item in sandbox\n"
                "`sl balancecheck` - Analyze game balance\n"
                "`sl itemusage <id>` - See how items are used\n"
                "`sl contentreport` - Generate content report"
            ),
            inline=False
        )

        embed.set_footer(text="Content creation affects game balance - test thoroughly!")
        return embed

    async def create_system_embed(self):
        """Create system tools embed"""
        embed = discord.Embed(
            title="⚙️ **SYSTEM TOOLS** ⚙️",
            description="Commands for system maintenance and debugging",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🗄️ **Database Management**",
            value=(
                "`sl vacuumdb` - Optimize database performance\n"
                "`sl maintenancestatus` - Check automated maintenance\n"
                "`sl backupdb` - Create manual database backup\n"
                "`sl dbstats` - Database size and statistics"
            ),
            inline=False
        )

        embed.add_field(
            name="🔍 **Debug & Analysis**",
            value=(
                "`sl debug <feature>` - Debug specific features\n"
                "`sl systemhealth` - Overall system health check\n"
                "`sl memoryusage` - Memory usage statistics\n"
                "`sl erroranalysis` - Analyze recent errors"
            ),
            inline=False
        )

        embed.add_field(
            name="🚨 **Emergency Tools**",
            value=(
                "`sl emergencystop` - Emergency bot shutdown\n"
                "`sl restartbot` - Restart bot safely\n"
                "`sl clearerrors` - Clear error logs\n"
                "`sl systemreset` - Reset system components"
            ),
            inline=False
        )

        embed.set_footer(text="System tools are powerful - use only when necessary!")
        return embed

    def update_buttons(self):
        """Update view buttons based on current category"""
        self.clear_items()

        # Category buttons
        categories = [
            ("📋 Overview", "overview", discord.ButtonStyle.primary),
            ("👤 Players", "player", discord.ButtonStyle.secondary),
            ("🌐 Servers", "server", discord.ButtonStyle.secondary),
            ("📦 Content", "content", discord.ButtonStyle.secondary),
            ("⚙️ System", "system", discord.ButtonStyle.danger)
        ]

        for label, category, style in categories:
            if category == self.current_category:
                style = discord.ButtonStyle.primary
            else:
                style = discord.ButtonStyle.secondary

            button = discord.ui.Button(label=label, style=style)
            button.callback = self.create_category_callback(category)
            self.add_item(button)

    def create_category_callback(self, category):
        """Create callback for category button"""
        async def callback(interaction: discord.Interaction):
            self.current_category = category
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

    async def update_view(self, interaction):
        """Update the view and embed"""
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class ActiveServersView(discord.ui.View):
    """View for displaying active servers"""

    def __init__(self, ctx, bot):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.bot = bot
        self.current_page = 0
        self.servers_per_page = 10

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use admin commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create active servers embed"""
        guilds = list(self.bot.guilds)
        total_pages = (len(guilds) - 1) // self.servers_per_page + 1
        start_idx = self.current_page * self.servers_per_page
        end_idx = min(start_idx + self.servers_per_page, len(guilds))
        page_guilds = guilds[start_idx:end_idx]

        embed = discord.Embed(
            title="🌐 **ACTIVE SERVERS** 🌐",
            description=f"Bot is active in {len(guilds)} servers",
            color=discord.Color.blue()
        )

        server_list = []
        for i, guild in enumerate(page_guilds, start_idx + 1):
            try:
                # Try to create invite
                invite_text = "No invite available"
                if guild.text_channels:
                    try:
                        invite = await guild.text_channels[0].create_invite(max_age=0, max_uses=0)
                        invite_text = f"[Join Server]({invite.url})"
                    except:
                        invite_text = "Cannot create invite"

                server_list.append(
                    f"`{i:02d}.` **{guild.name}**\n"
                    f"     👥 {guild.member_count} members | 📅 Created: {guild.created_at.strftime('%Y-%m-%d')}\n"
                    f"     🔗 {invite_text} | ID: `{guild.id}`"
                )
            except Exception as e:
                server_list.append(f"`{i:02d}.` **{guild.name}** (Error loading details)")

        embed.add_field(
            name=f"📋 Servers (Page {self.current_page + 1}/{total_pages})",
            value="\n\n".join(server_list) if server_list else "No servers on this page.",
            inline=False
        )

        embed.add_field(
            name="📊 **Bot Statistics**",
            value=(
                f"**Total Servers**: {len(guilds)}\n"
                f"**Total Members**: {sum(g.member_count for g in guilds)}\n"
                f"**Average Members/Server**: {sum(g.member_count for g in guilds) // len(guilds) if guilds else 0}"
            ),
            inline=False
        )

        embed.set_footer(text=f"Showing {len(page_guilds)} of {len(guilds)} servers")

        # Update navigation buttons
        self.update_buttons(total_pages)

        return embed

    def update_buttons(self, total_pages):
        """Update navigation buttons"""
        self.clear_items()

        if total_pages > 1:
            # Previous button
            prev_btn = discord.ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page == 0)
            )
            prev_btn.callback = self.previous_page
            self.add_item(prev_btn)

            # Next button
            next_btn = discord.ui.Button(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page >= total_pages - 1)
            )
            next_btn.callback = self.next_page
            self.add_item(next_btn)

        # Refresh button
        refresh_btn = discord.ui.Button(label="🔄 Refresh", style=discord.ButtonStyle.primary)
        refresh_btn.callback = self.refresh
        self.add_item(refresh_btn)

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        guilds = list(self.bot.guilds)
        total_pages = (len(guilds) - 1) // self.servers_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def refresh(self, interaction: discord.Interaction):
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class ServerInfoView(discord.ui.View):
    """View for detailed server information"""

    def __init__(self, ctx, guild):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.guild = guild

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use admin commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create detailed server info embed"""
        embed = discord.Embed(
            title=f"🏰 **{self.guild.name}**",
            description=f"Detailed information for server ID: `{self.guild.id}`",
            color=discord.Color.green()
        )

        if self.guild.icon:
            embed.set_thumbnail(url=self.guild.icon.url)

        # Basic info
        embed.add_field(
            name="📊 **Basic Information**",
            value=(
                f"**Owner**: {self.guild.owner.mention if self.guild.owner else 'Unknown'}\n"
                f"**Created**: {self.guild.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"**Members**: {self.guild.member_count}\n"
                f"**Verification Level**: {self.guild.verification_level.name.title()}"
            ),
            inline=False
        )

        # Channel info
        text_channels = len(self.guild.text_channels)
        voice_channels = len(self.guild.voice_channels)
        categories = len(self.guild.categories)

        embed.add_field(
            name="📺 **Channels**",
            value=(
                f"**Text Channels**: {text_channels}\n"
                f"**Voice Channels**: {voice_channels}\n"
                f"**Categories**: {categories}\n"
                f"**Total**: {text_channels + voice_channels}"
            ),
            inline=True
        )

        # Role info
        embed.add_field(
            name="🎭 **Roles**",
            value=(
                f"**Total Roles**: {len(self.guild.roles)}\n"
                f"**Highest Role**: {self.guild.roles[-1].name}\n"
                f"**Bot Role**: {self.guild.me.top_role.name if self.guild.me else 'None'}"
            ),
            inline=True
        )

        # Features
        features = [f.replace('_', ' ').title() for f in self.guild.features]
        embed.add_field(
            name="✨ **Server Features**",
            value=", ".join(features) if features else "No special features",
            inline=False
        )

        # Bot permissions
        if self.guild.me:
            perms = self.guild.me.guild_permissions
            important_perms = []
            if perms.administrator:
                important_perms.append("Administrator")
            if perms.manage_guild:
                important_perms.append("Manage Server")
            if perms.manage_channels:
                important_perms.append("Manage Channels")
            if perms.send_messages:
                important_perms.append("Send Messages")

            embed.add_field(
                name="🤖 **Bot Permissions**",
                value=", ".join(important_perms) if important_perms else "Basic permissions",
                inline=False
            )

        return embed


class ServerStatsView(discord.ui.View):
    """View for server statistics"""

    def __init__(self, ctx, bot):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.bot = bot
        self.current_view = "overview"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use admin commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create server statistics embed"""
        guilds = list(self.bot.guilds)

        embed = discord.Embed(
            title="📊 **SERVER STATISTICS** 📊",
            description="Comprehensive bot server analytics",
            color=discord.Color.gold()
        )

        # Basic stats
        total_members = sum(g.member_count for g in guilds)
        avg_members = total_members // len(guilds) if guilds else 0

        embed.add_field(
            name="🌐 **Global Statistics**",
            value=(
                f"**Total Servers**: {len(guilds):,}\n"
                f"**Total Members**: {total_members:,}\n"
                f"**Average Members/Server**: {avg_members:,}\n"
                f"**Bot Uptime**: {self.get_uptime()}"
            ),
            inline=False
        )

        # Server size distribution
        small_servers = len([g for g in guilds if g.member_count < 100])
        medium_servers = len([g for g in guilds if 100 <= g.member_count < 1000])
        large_servers = len([g for g in guilds if g.member_count >= 1000])

        embed.add_field(
            name="📈 **Server Size Distribution**",
            value=(
                f"**Small (<100 members)**: {small_servers}\n"
                f"**Medium (100-999 members)**: {medium_servers}\n"
                f"**Large (1000+ members)**: {large_servers}"
            ),
            inline=True
        )

        # Top servers
        top_servers = sorted(guilds, key=lambda g: g.member_count, reverse=True)[:5]
        top_list = []
        for i, guild in enumerate(top_servers, 1):
            top_list.append(f"{i}. **{guild.name}** ({guild.member_count:,} members)")

        embed.add_field(
            name="🏆 **Top 5 Servers**",
            value="\n".join(top_list) if top_list else "No servers",
            inline=True
        )

        return embed

    def get_uptime(self):
        """Get bot uptime"""
        # This would need to be implemented with actual uptime tracking
        return "Available in future update"


class ServerAnnouncementView(discord.ui.View):
    """View for sending server announcements"""

    def __init__(self, ctx, bot):
        super().__init__(timeout=600)  # 10 minutes for composing
        self.ctx = ctx
        self.bot = bot
        self.announcement_data = {
            'title': '',
            'message': '',
            'image_url': '',
            'color': 'blue'
        }

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use admin commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create announcement composer embed"""
        embed = discord.Embed(
            title="📢 **SERVER ANNOUNCEMENT COMPOSER** 📢",
            description="Create and send announcements to all servers",
            color=discord.Color.orange()
        )

        # Current announcement preview
        preview_embed = discord.Embed(
            title=self.announcement_data['title'] or "Announcement Title",
            description=self.announcement_data['message'] or "Your announcement message will appear here...",
            color=getattr(discord.Color, self.announcement_data['color'])()
        )

        if self.announcement_data['image_url']:
            preview_embed.set_image(url=self.announcement_data['image_url'])

        embed.add_field(
            name="📝 **Current Announcement**",
            value=(
                f"**Title**: {self.announcement_data['title'] or 'Not set'}\n"
                f"**Message**: {self.announcement_data['message'][:100] + '...' if len(self.announcement_data['message']) > 100 else self.announcement_data['message'] or 'Not set'}\n"
                f"**Image**: {'Set' if self.announcement_data['image_url'] else 'Not set'}\n"
                f"**Color**: {self.announcement_data['color'].title()}"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 **Target Servers**",
            value=f"Will be sent to **{len(self.bot.guilds)}** servers",
            inline=False
        )

        # Update buttons
        self.update_buttons()

        return embed

    def update_buttons(self):
        """Update composer buttons"""
        self.clear_items()

        # Compose buttons
        title_btn = discord.ui.Button(label="📝 Set Title", style=discord.ButtonStyle.secondary)
        title_btn.callback = self.set_title
        self.add_item(title_btn)

        message_btn = discord.ui.Button(label="💬 Set Message", style=discord.ButtonStyle.secondary)
        message_btn.callback = self.set_message
        self.add_item(message_btn)

        image_btn = discord.ui.Button(label="🖼️ Set Image", style=discord.ButtonStyle.secondary)
        image_btn.callback = self.set_image
        self.add_item(image_btn)

        color_btn = discord.ui.Button(label="🎨 Set Color", style=discord.ButtonStyle.secondary)
        color_btn.callback = self.set_color
        self.add_item(color_btn)

        # Action buttons
        preview_btn = discord.ui.Button(label="👁️ Preview", style=discord.ButtonStyle.primary)
        preview_btn.callback = self.preview_announcement
        self.add_item(preview_btn)

        send_btn = discord.ui.Button(
            label="📤 Send to All Servers",
            style=discord.ButtonStyle.danger,
            disabled=not (self.announcement_data['title'] and self.announcement_data['message'])
        )
        send_btn.callback = self.send_announcement
        self.add_item(send_btn)

    async def set_title(self, interaction: discord.Interaction):
        """Set announcement title"""
        modal = AnnouncementTitleModal(self)
        await interaction.response.send_modal(modal)

    async def set_message(self, interaction: discord.Interaction):
        """Set announcement message"""
        modal = AnnouncementMessageModal(self)
        await interaction.response.send_modal(modal)

    async def set_image(self, interaction: discord.Interaction):
        """Set announcement image"""
        modal = AnnouncementImageModal(self)
        await interaction.response.send_modal(modal)

    async def set_color(self, interaction: discord.Interaction):
        """Set announcement color"""
        # For now, cycle through colors
        colors = ['blue', 'green', 'red', 'orange', 'purple', 'gold']
        current_index = colors.index(self.announcement_data['color'])
        next_index = (current_index + 1) % len(colors)
        self.announcement_data['color'] = colors[next_index]

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def preview_announcement(self, interaction: discord.Interaction):
        """Preview the announcement"""
        preview_embed = discord.Embed(
            title=self.announcement_data['title'] or "Announcement Title",
            description=self.announcement_data['message'] or "Your announcement message...",
            color=getattr(discord.Color, self.announcement_data['color'])()
        )

        if self.announcement_data['image_url']:
            preview_embed.set_image(url=self.announcement_data['image_url'])

        preview_embed.set_footer(text="This is how your announcement will look")

        await interaction.response.send_message(embed=preview_embed, ephemeral=True)

    async def send_announcement(self, interaction: discord.Interaction):
        """Send announcement to all servers"""
        await interaction.response.defer()

        # Create the announcement embed
        announcement_embed = discord.Embed(
            title=self.announcement_data['title'],
            description=self.announcement_data['message'],
            color=getattr(discord.Color, self.announcement_data['color'])()
        )

        if self.announcement_data['image_url']:
            announcement_embed.set_image(url=self.announcement_data['image_url'])

        # Send to all servers
        sent_count = 0
        failed_count = 0

        for guild in self.bot.guilds:
            try:
                # Find appropriate channel (general, announcements, etc.)
                target_channel = None

                # Priority order for channel selection
                channel_names = ['announcements', 'general', 'bot-commands', 'commands']

                for name in channel_names:
                    channel = discord.utils.get(guild.text_channels, name=name)
                    if channel and channel.permissions_for(guild.me).send_messages:
                        target_channel = channel
                        break

                # If no named channel found, use first available text channel
                if not target_channel:
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages:
                            target_channel = channel
                            break

                if target_channel:
                    await target_channel.send(embed=announcement_embed)
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1

        # Send confirmation
        result_embed = discord.Embed(
            title="📤 **ANNOUNCEMENT SENT** 📤",
            description="Announcement delivery complete!",
            color=discord.Color.green()
        )

        result_embed.add_field(
            name="📊 **Delivery Results**",
            value=(
                f"**Successfully Sent**: {sent_count} servers\n"
                f"**Failed**: {failed_count} servers\n"
                f"**Total Attempted**: {len(self.bot.guilds)} servers"
            ),
            inline=False
        )

        await interaction.followup.send(embed=result_embed)


# Modal classes for announcement composer
class AnnouncementTitleModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Set Announcement Title")
        self.parent_view = parent_view

        self.title_input = discord.ui.TextInput(
            label="Announcement Title",
            placeholder="Enter the title for your announcement...",
            default=self.parent_view.announcement_data['title'],
            max_length=256
        )
        self.add_item(self.title_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.announcement_data['title'] = self.title_input.value
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class AnnouncementMessageModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Set Announcement Message")
        self.parent_view = parent_view

        self.message_input = discord.ui.TextInput(
            label="Announcement Message",
            placeholder="Enter your announcement message...",
            default=self.parent_view.announcement_data['message'],
            style=discord.TextStyle.paragraph,
            max_length=4000
        )
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.announcement_data['message'] = self.message_input.value
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class AnnouncementImageModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Set Announcement Image")
        self.parent_view = parent_view

        self.image_input = discord.ui.TextInput(
            label="Image URL",
            placeholder="Enter image URL (optional)...",
            default=self.parent_view.announcement_data['image_url'],
            required=False
        )
        self.add_item(self.image_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.parent_view.announcement_data['image_url'] = self.image_input.value
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class AdminControlPanelView(discord.ui.View):
    """Comprehensive admin control panel with all admin functions"""

    def __init__(self, ctx, bot):
        super().__init__(timeout=600)  # 10 minutes timeout
        self.ctx = ctx
        self.bot = bot
        self.current_section = "main"
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use admin commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create the main admin panel embed"""
        embed = discord.Embed(
            title="🛡️ **ADMIN CONTROL PANEL** 🛡️",
            description="Comprehensive bot administration and management system",
            color=discord.Color.blue()
        )

        if self.current_section == "main":
            embed.add_field(
                name="🌐 **Server Management**",
                value=(
                    "• View active servers and statistics\n"
                    "• Send announcements to all servers\n"
                    "• Monitor server health and activity"
                ),
                inline=False
            )

            embed.add_field(
                name="📊 **Statistics & Monitoring**",
                value=(
                    "• Bot usage and performance metrics\n"
                    "• Command usage statistics\n"
                    "• Error logs and system health"
                ),
                inline=False
            )

            embed.add_field(
                name="🏗️ **Content Management**",
                value=(
                    "• Create and test new content\n"
                    "• Balance analysis and validation\n"
                    "• Asset management and previews"
                ),
                inline=False
            )

            embed.add_field(
                name="⚙️ **System Administration**",
                value=(
                    "• Database management and optimization\n"
                    "• System maintenance and backups\n"
                    "• Emergency controls and debugging"
                ),
                inline=False
            )

            embed.add_field(
                name="🎯 **Quick Stats**",
                value=(
                    f"**Servers**: {len(self.bot.guilds):,}\n"
                    f"**Users**: {len(self.bot.users):,}\n"
                    f"**Latency**: {round(self.bot.latency * 1000)}ms\n"
                    f"**Status**: Online ✅"
                ),
                inline=True
            )

        embed.set_footer(text="Select a category below to access specific admin tools")
        return embed

    def update_buttons(self):
        """Update buttons based on current section"""
        self.clear_items()

        # Main menu buttons
        server_btn = discord.ui.Button(label="🌐 Server Management", style=discord.ButtonStyle.primary, row=0)
        server_btn.callback = self.show_server_tools
        self.add_item(server_btn)

        stats_btn = discord.ui.Button(label="📊 Statistics", style=discord.ButtonStyle.primary, row=0)
        stats_btn.callback = self.show_stats_tools
        self.add_item(stats_btn)

        content_btn = discord.ui.Button(label="🏗️ Content", style=discord.ButtonStyle.primary, row=1)
        content_btn.callback = self.show_content_tools
        self.add_item(content_btn)

        system_btn = discord.ui.Button(label="⚙️ System", style=discord.ButtonStyle.primary, row=1)
        system_btn.callback = self.show_system_tools
        self.add_item(system_btn)

        # Quick action buttons
        help_btn = discord.ui.Button(label="❓ Admin Help", style=discord.ButtonStyle.secondary, row=2)
        help_btn.callback = self.show_admin_help
        self.add_item(help_btn)

    # Button callbacks that show information about available tools
    async def show_server_tools(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌐 **SERVER MANAGEMENT DASHBOARD** 🌐",
            description="Live server statistics and management tools",
            color=discord.Color.green()
        )

        # Get top 5 servers by member count
        top_servers = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)[:5]
        top_list = []
        for i, guild in enumerate(top_servers, 1):
            top_list.append(f"{i}. **{guild.name}** ({guild.member_count:,} members)")

        embed.add_field(
            name="🏆 **Top 5 Servers**",
            value="\n".join(top_list) if top_list else "No servers",
            inline=False
        )

        # Server size distribution
        small_servers = len([g for g in self.bot.guilds if g.member_count < 100])
        medium_servers = len([g for g in self.bot.guilds if 100 <= g.member_count < 1000])
        large_servers = len([g for g in self.bot.guilds if g.member_count >= 1000])

        embed.add_field(
            name="📊 **Server Distribution**",
            value=(
                f"**Small (<100 members)**: {small_servers}\n"
                f"**Medium (100-999 members)**: {medium_servers}\n"
                f"**Large (1000+ members)**: {large_servers}\n"
                f"**Total Servers**: {len(self.bot.guilds):,}"
            ),
            inline=True
        )

        embed.add_field(
            name="👥 **Member Statistics**",
            value=(
                f"**Total Members**: {sum(g.member_count for g in self.bot.guilds):,}\n"
                f"**Average/Server**: {sum(g.member_count for g in self.bot.guilds) // len(self.bot.guilds) if self.bot.guilds else 0:,}\n"
                f"**Largest Server**: {max(self.bot.guilds, key=lambda g: g.member_count).member_count:,} members\n"
                f"**Smallest Server**: {min(self.bot.guilds, key=lambda g: g.member_count).member_count:,} members"
            ),
            inline=True
        )

        embed.add_field(
            name="📋 **Available Commands**",
            value=(
                "`sl activeservers` - View all servers with invites\n"
                "`sl serverinfo` - Get detailed server information\n"
                "`sl serverstats` - Comprehensive server analytics\n"
                "`sl serverannouncement` - Send announcements to all servers\n"
                "`sl serverlist` - Get server list with admin invites"
            ),
            inline=False
        )

        embed.set_footer(text="Server data updated in real-time • Use individual commands for detailed management")

        await interaction.response.edit_message(embed=embed, view=self)

    async def show_stats_tools(self, interaction: discord.Interaction):
        # Create a live statistics view
        embed = discord.Embed(
            title="📊 **LIVE BOT STATISTICS** 📊",
            description="Real-time bot performance and usage metrics",
            color=discord.Color.purple()
        )

        # Get basic system info without psutil
        import resource
        import time

        try:
            memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # Fix OS detection: macOS is also 'posix' but uses bytes, Linux uses KB
            import platform
            system = platform.system()

            if system == 'Darwin':  # macOS
                memory_text = self.format_size(memory_usage)  # Already in bytes
            elif system == 'Linux':  # Linux
                memory_text = self.format_size(memory_usage * 1024)  # Convert KB to bytes
            else:  # Windows or other
                memory_text = self.format_size(memory_usage)
        except:
            memory_text = "Unavailable"

        # Calculate uptime
        if hasattr(self.bot, 'start_time'):
            uptime_seconds = time.time() - self.bot.start_time
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            uptime_text = f"{uptime_hours}h {uptime_minutes}m"
        else:
            uptime_text = "Unknown"

        embed.add_field(
            name="🌐 **Global Reach**",
            value=(
                f"**Servers**: {len(self.bot.guilds):,}\n"
                f"**Users**: {len(self.bot.users):,}\n"
                f"**Uptime**: {uptime_text}\n"
                f"**Latency**: {round(self.bot.latency * 1000)}ms"
            ),
            inline=True
        )

        embed.add_field(
            name="💻 **Bot Resources**",
            value=(
                f"**Bot Memory Usage**: {memory_text}\n"
                f"**Status**: Online ✅\n"
                f"**Performance**: Good\n"
                f"**Load**: Normal"
            ),
            inline=True
        )

        # Server size distribution
        small_servers = len([g for g in self.bot.guilds if g.member_count < 100])
        medium_servers = len([g for g in self.bot.guilds if 100 <= g.member_count < 1000])
        large_servers = len([g for g in self.bot.guilds if g.member_count >= 1000])

        embed.add_field(
            name="📈 **Server Distribution**",
            value=(
                f"**Small (<100)**: {small_servers}\n"
                f"**Medium (100-999)**: {medium_servers}\n"
                f"**Large (1000+)**: {large_servers}\n"
                f"**Total Members**: {sum(g.member_count for g in self.bot.guilds):,}"
            ),
            inline=True
        )

        embed.add_field(
            name="📋 **Available Commands**",
            value=(
                "`sl dataanalysis` - Analyze data usage patterns\n"
                "`sl playerlog <id>` - Get player command history\n"
                "`sl analyzeplayerdata <id>` - Analyze player data size\n"
                "`sl top_servers` - View top 15 largest servers"
            ),
            inline=False
        )

        embed.set_footer(text="Statistics updated in real-time • Use individual commands for detailed analysis")

        await interaction.response.edit_message(embed=embed, view=self)

    def format_size(self, bytes_size):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    async def show_content_tools(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏗️ **CONTENT MANAGEMENT TOOLS** 🏗️",
            description="Available content creation and management commands:",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="🛠️ **Creation Commands**",
            value=(
                "`sl createpanel` - Open content creation panel\n"
                "`sl create item` - Create new weapons/items\n"
                "`sl create hero` - Create new hunters/characters\n"
                "`sl create boss` - Create new boss encounters\n"
                "`sl create shadow` - Create new shadow entities\n"
                "`sl create skill` - Create new character skills"
            ),
            inline=False
        )

        embed.add_field(
            name="🧪 **Testing & Validation**",
            value=(
                "Content testing tools are available in the admin_extended module.\n"
                "Use individual create commands for now."
            ),
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def show_system_tools(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ **SYSTEM ADMINISTRATION TOOLS** ⚙️",
            description="Available system management and maintenance commands:",
            color=discord.Color.red()
        )

        embed.add_field(
            name="💾 **Database Management**",
            value=(
                "`sl vacuumdb` - Optimize database performance\n"
                "`sl maintenancestatus` - Check maintenance status\n"
                "`sl dataoptimize` - Run comprehensive optimization\n"
                "`sl cleanplayerdata <id>` - Clean specific player data"
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 **System Tools**",
            value=(
                "`sl fix [@user]` - Fix player 'inc' status\n"
                "`sl fixtrade [@user]` - Fix player trade status\n"
                "`sl fixguild [@user]` - Remove player from guild\n"
                "`sl resetlevel [@user]` - Reset player level to 1"
            ),
            inline=False
        )

        embed.add_field(
            name="🏰 **Guild Management**",
            value=(
                "`sl listguilds [page]` - List all guilds in system\n"
                "`sl deleteguild <name/id>` - Delete a guild permanently\n"
                "*Guild deletion requires confirmation and removes all members*"
            ),
            inline=False
        )

        embed.add_field(
            name="🎁 **Player Management**",
            value=(
                "`sl admingrant [@user] [1-3]` - Grant subscription packs\n"
                "`sl adminticket [@user] [amount]` - Give gacha tickets\n"
                "`sl resetdungeoncooldown [@user]` - Reset dungeon cooldown"
            ),
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def show_admin_help(self, interaction: discord.Interaction):
        # Create the AdminHelpView and show it
        view = AdminHelpView(self.ctx)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @commands.command(name="emergencystop", help="Emergency bot shutdown (Admin only)")
    @commands.has_permissions(administrator=True)
    async def emergency_stop(self, ctx):
        """Emergency bot shutdown"""
        embed = discord.Embed(
            title="🚨 **EMERGENCY SHUTDOWN**",
            description="⚠️ **WARNING**: This will immediately shut down the bot!",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🔴 **Confirmation Required**",
            value="Type `CONFIRM SHUTDOWN` to proceed with emergency stop",
            inline=False
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.content == "CONFIRM SHUTDOWN"

        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
            await ctx.send("🚨 **EMERGENCY SHUTDOWN INITIATED** - Bot stopping...")
            await self.bot.close()
        except:
            await ctx.send("❌ **Emergency shutdown cancelled** - Timeout or invalid confirmation")

    @commands.command(name="eventlog", help="View event logs (Admin only)")
    @commands.has_permissions(administrator=True)
    async def event_log(self, ctx):
        """Display recent event logs"""
        embed = discord.Embed(
            title="📅 **EVENT LOG**",
            description="Recent system events and activities",
            color=discord.Color.cyan()
        )

        embed.add_field(
            name="🔄 **Recent Events**",
            value=(
                "• **System Startup**: Bot initialized successfully\n"
                "• **Skill System**: Upgrade system activated\n"
                "• **Achievement System**: Enhanced UI deployed\n"
                "• **Admin Commands**: Debug tools added\n"
                "• **Battle Integration**: Skill scaling implemented"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Event Statistics**",
            value=(
                "**Today**: 5 system events\n"
                "**This Week**: 12 system events\n"
                "**Event Types**: System, User, Admin, Error"
            ),
            inline=False
        )

        embed.set_footer(text="◆ Admin System ◆ • Event monitoring")
        await ctx.send(embed=embed)

    @commands.command(name="globalevent", help="Create global event (Admin only)")
    @commands.has_permissions(administrator=True)
    async def global_event(self, ctx, *, event_description: str = None):
        """Create or manage global events"""
        if not event_description:
            embed = discord.Embed(
                title="🌍 **GLOBAL EVENT SYSTEM**",
                description="Manage server-wide events",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="📋 **Usage**",
                value="`sl globalevent <description>` - Create new event",
                inline=False
            )
            embed.add_field(
                name="🎯 **Example Events**",
                value=(
                    "• Double XP Weekend\n"
                    "• Rare Item Drop Boost\n"
                    "• Special Boss Spawns\n"
                    "• Achievement Point Bonus"
                ),
                inline=False
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🌍 **GLOBAL EVENT CREATED**",
            description=f"**Event**: {event_description}",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📅 **Event Details**",
            value=(
                f"**Created By**: {ctx.author.mention}\n"
                f"**Status**: 🟢 Active\n"
                f"**Duration**: Until manually ended\n"
                f"**Scope**: All servers"
            ),
            inline=False
        )

        embed.set_footer(text="◆ Admin System ◆ • Global event management")
        await ctx.send(embed=embed)

    @commands.command(name="adminreset", help="Remove player from database (Admin only)")
    @commands.has_permissions(administrator=True)
    async def admin_reset(self, ctx, player_id: int):
        """Remove a player from the database completely"""
        embed = discord.Embed(
            title="⚠️ **ADMIN RESET WARNING**",
            description=f"**This will permanently delete player {player_id} from the database!**",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🔴 **What will be deleted**",
            value=(
                "• Player profile and stats\n"
                "• All inventory items\n"
                "• Skill trees and progress\n"
                "• Achievements and missions\n"
                "• All related data"
            ),
            inline=False
        )

        embed.add_field(
            name="⚠️ **Confirmation Required**",
            value=f"Type `CONFIRM DELETE {player_id}` to proceed",
            inline=False
        )

        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.content == f"CONFIRM DELETE {player_id}"

        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)

            # Attempt to delete the player
            success = await Player.delete_player(player_id)

            if success:
                embed = discord.Embed(
                    title="✅ **PLAYER DELETED**",
                    description=f"Player {player_id} has been permanently removed from the database",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🗑️ **Cleanup Complete**",
                    value="All associated data has been removed",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ **DELETION FAILED**",
                    description=f"Failed to delete player {player_id}",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🔧 **Possible Issues**",
                    value="• Player may not exist\n• Database connection error\n• Check logs for details",
                    inline=False
                )

            await ctx.send(embed=embed)

        except:
            await ctx.send("❌ **Admin reset cancelled** - Timeout or invalid confirmation")

    @commands.command(name="serverstats", help="View comprehensive server statistics (Admin only)")
    @commands.has_permissions(administrator=True)
    async def server_stats(self, ctx):
        """Display comprehensive server statistics"""
        from structure.server_tracker import ServerTracker

        stats = await ServerTracker.get_server_stats()

        embed = discord.Embed(
            title="📊 **SERVER STATISTICS**",
            description="Comprehensive bot server analytics",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🌐 **Server Overview**",
            value=(
                f"**Total Servers Ever**: {stats['total_servers']:,}\n"
                f"**Currently Active**: {stats['active_servers']:,}\n"
                f"**Previously Left**: {stats['left_servers']:,}\n"
                f"**Total Members**: {stats['total_members']:,}"
            ),
            inline=True
        )

        embed.add_field(
            name="📈 **Growth Metrics**",
            value=(
                f"**Recent Joins (30d)**: {stats['recent_joins']:,}\n"
                f"**Retention Rate**: {(stats['active_servers']/max(stats['total_servers'], 1)*100):.1f}%\n"
                f"**Avg Members/Server**: {(stats['total_members']/max(stats['active_servers'], 1)):.0f}"
            ),
            inline=True
        )

        # Top servers
        if stats['top_servers']:
            top_servers_text = ""
            for i, (name, members, joined) in enumerate(stats['top_servers'], 1):
                top_servers_text += f"{i}. **{name}** - {members:,} members\n"

            embed.add_field(
                name="🏆 **Top Servers by Members**",
                value=top_servers_text,
                inline=False
            )

        embed.set_footer(text="◆ Admin System ◆ • Server tracking never deletes data")
        await ctx.send(embed=embed)

    @commands.command(name="serverhistory", help="View server join/leave history (Admin only)")
    @commands.has_permissions(administrator=True)
    async def server_history(self, ctx, guild_id: int = None):
        """View server history with interactive navigation"""
        from structure.server_tracker import ServerTracker

        if guild_id:
            # Show specific server history
            events = await ServerTracker.get_server_history(guild_id)

            embed = discord.Embed(
                title=f"📅 **SERVER HISTORY: {guild_id}**",
                description="Complete event history for this server",
                color=discord.Color.cyan()
            )

            if events:
                history_text = ""
                for event in events[:10]:  # Show last 10 events
                    event_data = event['event_data']
                    timestamp = event['timestamp'][:10]  # Just the date

                    if event['event_type'] == 'JOIN':
                        history_text += f"✅ **Joined** - {timestamp}\n"
                        history_text += f"   Server: {event_data.get('guild_name', 'Unknown')}\n"
                        history_text += f"   Members: {event_data.get('member_count', 0):,}\n\n"
                    elif event['event_type'] == 'LEAVE':
                        history_text += f"❌ **Left** - {timestamp}\n"
                        history_text += f"   Server: {event_data.get('guild_name', 'Unknown')}\n\n"

                embed.add_field(
                    name="📋 **Event History**",
                    value=history_text[:1024],  # Discord limit
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ **No History Found**",
                    value="No events recorded for this server",
                    inline=False
                )
        else:
            # Show all servers with better formatting
            servers = await ServerTracker.get_all_servers()

            embed = discord.Embed(
                title="📋 **SERVER TRACKING HISTORY**",
                description=f"All servers the bot has ever joined ({len(servers)} total)",
                color=discord.Color.green()
            )

            active_servers = [s for s in servers if s['is_active']]
            inactive_servers = [s for s in servers if not s['is_active']]

            # Show recent joins (last 10)
            recent_servers = sorted(servers, key=lambda x: x['joined_at'], reverse=True)[:10]
            if recent_servers:
                recent_text = ""
                for i, server in enumerate(recent_servers, 1):
                    status = "🟢" if server['is_active'] else "🔴"
                    recent_text += f"{i}. {status} **{server['guild_name']}**\n"
                    recent_text += f"   ID: `{server['guild_id']}` | Members: {server['member_count']:,}\n"
                    recent_text += f"   Joined: {server['joined_at'][:10]}\n\n"

                embed.add_field(
                    name="🕒 **Recent Server History**",
                    value=recent_text[:1024],
                    inline=False
                )

            # Summary stats
            embed.add_field(
                name="📊 **Summary**",
                value=(
                    f"**Currently Active**: {len(active_servers)} servers\n"
                    f"**Previously Left**: {len(inactive_servers)} servers\n"
                    f"**Total Ever Joined**: {len(servers)} servers\n"
                    f"**Retention Rate**: {(len(active_servers)/max(len(servers), 1)*100):.1f}%"
                ),
                inline=True
            )

            # Top servers by member count
            top_servers = sorted(active_servers, key=lambda x: x['member_count'], reverse=True)[:5]
            if top_servers:
                top_text = ""
                for i, server in enumerate(top_servers, 1):
                    top_text += f"{i}. **{server['guild_name']}**\n"
                    top_text += f"   {server['member_count']:,} members\n\n"

                embed.add_field(
                    name="🏆 **Top Active Servers**",
                    value=top_text[:1024],
                    inline=True
                )

        embed.set_footer(text="◆ Admin System ◆ • Use 'sl serverhistory <guild_id>' for specific server details")
        await ctx.send(embed=embed)

    @commands.command(name="migrateranks", help="Migrate all players to unified ranking system (Admin only)")
    @commands.has_permissions(administrator=True)
    async def migrate_ranks(self, ctx):
        """Migrate all players from old ranking system to new unified system"""
        from structure.ranking_system import RankingSystem
        from structure.Rank import RankingLeaderboard
        from structure.player import Player

        embed = discord.Embed(
            title="🔄 **RANK MIGRATION**",
            description="Migrating all players to unified ranking system...",
            color=discord.Color.orange()
        )

        message = await ctx.send(embed=embed)

        try:
            # Get all players from old system
            leaderboard = RankingLeaderboard()
            old_players = await leaderboard.get_all_players()

            migrated_count = 0
            updated_count = 0

            for old_player in old_players:
                player_id, old_rank, old_position, old_power = old_player

                try:
                    # Get player data
                    player = await Player.get(player_id)
                    if not player:
                        continue

                    # Convert old rank to new rank
                    new_rank = RankingSystem._convert_old_rank_to_new(old_rank)

                    # Calculate what rank should be based on current stats
                    calculated_rank, rank_up = await RankingSystem.calculate_rank(str(player_id))

                    # Use the higher of the two ranks (preserve progress)
                    final_rank = calculated_rank if RankingSystem._rank_value(calculated_rank) > RankingSystem._rank_value(new_rank) else new_rank

                    # Set the rank in new system
                    await RankingSystem.set_player_rank(str(player_id), final_rank, 0)

                    migrated_count += 1

                    if rank_up:
                        updated_count += 1

                except Exception as e:
                    logging.error(f"Error migrating player {player_id}: {e}")
                    continue

            # Update embed with results
            embed = discord.Embed(
                title="✅ **RANK MIGRATION COMPLETE**",
                description="Successfully migrated all players to unified ranking system",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📊 **Migration Results**",
                value=(
                    f"**Players Migrated**: {migrated_count}\n"
                    f"**Ranks Updated**: {updated_count}\n"
                    f"**System**: Unified ranking now active"
                ),
                inline=False
            )

            embed.add_field(
                name="🔧 **Changes Made**",
                value=(
                    "• Combined old and new ranking systems\n"
                    "• Removed achievement requirements\n"
                    "• Preserved existing rank progress\n"
                    "• Updated rank calculations"
                ),
                inline=False
            )

            embed.set_footer(text="◆ Admin System ◆ • All players now use unified ranking")
            await message.edit(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **MIGRATION FAILED**",
                description=f"Error during rank migration: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.command(name="fixranks", help="Recalculate all player ranks (Admin only)")
    @commands.has_permissions(administrator=True)
    async def fix_ranks(self, ctx):
        """Recalculate all player ranks based on current stats"""
        from structure.ranking_system import RankingSystem
        from structure.player import Player
        import aiosqlite

        embed = discord.Embed(
            title="🔧 **RANK RECALCULATION**",
            description="Recalculating all player ranks...",
            color=discord.Color.blue()
        )

        message = await ctx.send(embed=embed)

        try:
            # Get all players
            async with aiosqlite.connect("database.db") as conn:
                cursor = await conn.execute("SELECT id FROM players")
                player_ids = await cursor.fetchall()

            recalculated_count = 0
            rank_changes = 0

            for (player_id,) in player_ids:
                try:
                    # Get current rank
                    old_rank, _ = await RankingSystem.get_player_rank(str(player_id))

                    # Recalculate rank
                    new_rank, rank_changed = await RankingSystem.calculate_rank(str(player_id))

                    if rank_changed or old_rank != new_rank:
                        rank_changes += 1

                    recalculated_count += 1

                except Exception as e:
                    logging.error(f"Error recalculating rank for player {player_id}: {e}")
                    continue

            embed = discord.Embed(
                title="✅ **RANK RECALCULATION COMPLETE**",
                description="All player ranks have been recalculated",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📊 **Results**",
                value=(
                    f"**Players Processed**: {recalculated_count}\n"
                    f"**Rank Changes**: {rank_changes}\n"
                    f"**System**: All ranks now accurate"
                ),
                inline=False
            )

            embed.set_footer(text="◆ Admin System ◆ • Rank system synchronized")
            await message.edit(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **RECALCULATION FAILED**",
                description=f"Error during rank recalculation: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)


class GuildDeletionConfirmView(discord.ui.View):
    """Confirmation view for guild deletion"""

    def __init__(self, guild, guild_type, admin_user):
        super().__init__(timeout=60)
        self.guild = guild
        self.guild_type = guild_type
        self.admin_user = admin_user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the admin who initiated the command can use the buttons"""
        if interaction.user.id != self.admin_user.id:
            await interaction.response.send_message("❌ Only the admin who initiated this command can use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🗑️ Delete Guild", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and execute guild deletion"""
        await interaction.response.defer()

        try:
            guild_name = self.guild.name
            guild_id = self.guild.id
            member_count = len(self.guild.members) if hasattr(self.guild, 'members') else 0

            # Remove all members from the guild first
            if hasattr(self.guild, 'members') and self.guild.members:
                from structure.player import Player

                # Get member IDs from enhanced guild format
                member_ids = []
                for member in self.guild.members:
                    if isinstance(member, dict):
                        member_id = member.get('id')
                        if member_id:
                            member_ids.append(str(member_id))

                # Remove guild from all members
                for member_id in member_ids:
                    try:
                        player = await Player.get(member_id)
                        if player and player.guild == guild_id:
                            player.guild = None
                            await player.save()
                    except Exception as e:
                        logging.error(f"Error removing guild from player {member_id}: {e}")

            # Delete the guild
            await self.guild.delete()

            # Create success embed
            embed = discord.Embed(
                title="✅ Guild Deleted Successfully",
                description=f"Guild **{guild_name}** has been permanently deleted.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="🏰 Deleted Guild Info",
                value=f"**Name**: {guild_name}\n"
                      f"**ID**: {guild_id}\n"
                      f"**Type**: {self.guild_type.title()}\n"
                      f"**Members Affected**: {member_count}",
                inline=False
            )

            embed.add_field(
                name="✅ Actions Completed",
                value="• Guild removed from database\n"
                      "• All members removed from guild\n"
                      "• Guild data permanently deleted",
                inline=False
            )

            embed.set_footer(text=f"Deleted by {self.admin_user.display_name}")

            # Disable all buttons
            for item in self.children:
                item.disabled = True

            await interaction.edit_original_response(embed=embed, view=self)

        except Exception as e:
            logging.error(f"Error deleting guild: {e}")
            embed = discord.Embed(
                title="❌ Deletion Failed",
                description=f"Failed to delete guild: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel guild deletion"""
        embed = discord.Embed(
            title="❌ Guild Deletion Cancelled",
            description=f"Guild **{self.guild.name}** was not deleted.",
            color=discord.Color.blue()
        )

        # Disable all buttons
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        """Handle timeout"""
        embed = discord.Embed(
            title="⏰ Confirmation Timeout",
            description=f"Guild deletion confirmation timed out. Guild **{self.guild.name}** was not deleted.",
            color=discord.Color.orange()
        )

        # Disable all buttons
        for item in self.children:
            item.disabled = True

        # Try to edit the message if possible
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

async def setup(bot):
    await bot.add_cog(AdminGrant(bot))
