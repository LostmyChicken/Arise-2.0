import time
import discord
import random
from discord.ext import commands
from discord import app_commands
from structure.player import Player
from structure.raids import Raid  # Assuming Raid class is in structure/raids.py
from structure.emoji import getEmoji
from utilis.utilis import PremiumCheck
from utilis.admin import is_bot_admin

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._processing_raids = set()  # Track users currently processing raid commands

    @commands.hybrid_command(name="raid", help="Spawns a shadow raid in the current channel for your party.")
    async def raid(self, ctx: commands.Context):
        """Spawns a cooperative shadow raid that players in the channel can join. (Bot Admin Only)"""

        # Prevent duplicate processing
        if ctx.author.id in self._processing_raids:
            return

        self._processing_raids.add(ctx.author.id)

        try:
            if not is_bot_admin(ctx.author.id):
                embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
                await ctx.send(embed=embed, ephemeral=True)
                return
            player = await Player.get(ctx.author.id)
            if not player:
                embed = discord.Embed(title="Error", description="You haven't started yet. Use `sl start` to begin!", color=discord.Color.red())
                await ctx.send(embed=embed)
                return

            base_cooldown = 28800  # 8 hours
            cooldown = int(base_cooldown * PremiumCheck(player))

            on_cooldown = False
            if player.raid:
                try:
                    if (time.time() - float(player.raid)) < cooldown:
                        on_cooldown = True
                        remaining = cooldown - (time.time() - float(player.raid))
                except (ValueError, TypeError):
                    player.raid = None # Clear bad data if it's not a valid timestamp
                    await player.save()

            if on_cooldown:
                h, rem = divmod(int(remaining), 3600)
                m, s = divmod(rem, 60)

                embed = discord.Embed(
                    title="Command On Cooldown!",
                    description=f"You can spawn another Raid in **{h}h {m}m {s}s**.",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url="https://i.redd.it/official-solo-leveling-emotes-from-koreas-kakaotalk-app-v0-4gu5a1u2e92e1.png?width=210&format=png&auto=webp&s=12568200e6361c02e9e86f7cc21d00e2e4f46e0e")
                await ctx.reply(embed=embed, mention_author=False)
                return

            if player.trade or player.inc:
                status = "in a trade" if player.trade else "busy with another command"
                await ctx.send(f"<@{player.id}>, you are currently {status}. Please finish before starting a raid.", ephemeral=True)
                return

            if await Raid.get(ctx.channel.id):
                await ctx.send("There is already an active raid in this channel.", ephemeral=True)
                return

            # --- THIS IS THE CORRECTED PART ---
            player.raid = time.time()
            await player.save()

            level = random.randint(50, 100)
            shadow_name = random.choice(["Igris", "Tusk", "Tank"])

            # Send a loading message
            loading_msg = await ctx.send(f"{getEmoji('searching')} **Spawning shadow raid...**")

            # The spawn_raid function now handles sending the message and the view
            await Raid.spawn_raid(self.bot, ctx.channel, shadow_name, level)

            # Edit the loading message to show success
            await loading_msg.edit(content=f"{getEmoji('tick')} **You have successfully spawned a shadow raid!**")

        finally:
            # Always remove from processing set
            self._processing_raids.discard(ctx.author.id)

    @commands.hybrid_command(name="raidleave", help="Leave the current raid in this channel.")
    async def raidleave(self, ctx: commands.Context):
        """Allows a player to leave an ongoing raid if they are a participant."""
        raid = await Raid.get(ctx.channel.id, self.bot)
        if raid and ctx.author.id in raid.members:
            await raid.remove_member(ctx.author.id)
            await ctx.send(embed=discord.Embed(title="Raid Left", description=f"{ctx.author.mention} has left the raid.", color=discord.Color.orange()), ephemeral=True)

            try:
                raid_message = await ctx.channel.fetch_message(raid.message_id)
                if raid_message and raid_message.embeds:
                    updated_embed = raid_message.embeds[0]
                    participants_list = ", ".join([f"<@{m}>" for m in raid.members.keys()]) or "No one has joined yet."
                    updated_embed.set_field_at(2, name=f"Hunters [{len(raid.members)}/5]", value=participants_list, inline=False)
                    await raid_message.edit(embed=updated_embed)
            except (discord.NotFound, discord.HTTPException, IndexError):
                pass
        else:
            await ctx.send("You are not part of an active raid in this channel.", ephemeral=True)

    @raid.error
    async def raid_error(self, ctx: commands.Context, error):
        """Handle errors for the raid command"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🚫 Permission Denied",
                description="**Only administrators can spawn raids!**\n\nWorld bosses spawn automatically based on server activity.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="🌍 World Boss System",
                value="World bosses spawn automatically when:\n• Server is active (50+ commands)\n• High arena streaks (10+)\n• Gates are cleared\n• Random events",
                inline=False
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            # Re-raise other errors
            raise error

async def setup(bot):
    await bot.add_cog(RaidCog(bot))