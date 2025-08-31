import random
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import cooldown, BucketType

from structure.emoji import getEmoji
from structure.player import Player

CHANNEL_ID = 1337190833593651200  # The channel where the /boost command can be used

class Claim(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = commands.CooldownMapping.from_cooldown(1, 86400, BucketType.user)  # 1 use per 24 hours

    @commands.hybrid_command(name="boost", help="Claim your daily booster rewards if you are a server booster.")
    async def boost(self, ctx: commands.Context):
        """Allows a user to claim booster rewards."""
        if ctx.channel.id != CHANNEL_ID:
            embed = discord.Embed(title="Wrong Channel", description="This command can only be used in the designated booster rewards channel!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        # --- CRITICAL FIX: Added check to ensure the user is a server booster ---
        if not ctx.author.premium_since:
            embed = discord.Embed(title="Not a Booster", description="This reward is exclusively for members who are boosting the server. Thank you for your support!", color=discord.Color.nitro_pink())
            await ctx.send(embed=embed)
            return

        # Manually check the cooldown
        bucket = self.cooldowns.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            remaining_hours = round(retry_after / 3600, 1)
            embed = discord.Embed(title="Cooldown", description=f"⏳ You can claim your booster rewards again in **{remaining_hours}** hours!", color=discord.Color.orange())
            await ctx.reply(embed=embed, mention_author=False)
            return

        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Not Started", description="You haven't started the bot yet. Use `sl start` to begin your journey.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            return

        gacha_tickets = random.randint(3, 4)
        player.ticket += gacha_tickets
        player.diamond += 250
        await player.save()
        
        tix = getEmoji("ticket")
        diamond_ = getEmoji("diamond")
        embed = discord.Embed(
            title="Boost Rewards Claimed!", 
            description=f"Thank you for boosting the server, {ctx.author.mention}! You've received **{gacha_tickets}** {tix} and **250** {diamond_}!", 
            color=discord.Color.green()
        )
        await ctx.reply(embed=embed, mention_author=False)
        
async def setup(bot):
    await bot.add_cog(Claim(bot))