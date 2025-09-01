import discord
from discord.ext import commands
from discord import app_commands

from utilis.utilis import extractId
from structure.heroes import HeroManager
from structure.emoji import getEmoji
from structure.player import Player

class BadgesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="badges", help="View your collection of max-level hunter badges.")
    async def badges(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)

        if not player:
            down = getEmoji("down")
            embed = discord.Embed(
                title="Not Started", 
                description=f"You haven't started the bot yet.\n{down} Use `sl start` to get Re-Awakening.", 
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        inventory = player.get_hunters()

        if not inventory:
            embed = discord.Embed(
                title="Badges",
                description="> *Max your hunters to earn its badge.*",
                color=discord.Color.dark_blue()
            ).set_footer(text="System Notification")
            await ctx.send(embed=embed)
            return

        level_100_hunters = []
        for item_id, hunter_data in inventory.items():
            if hunter_data.get('level') == 100:
                hunter = await HeroManager.get(item_id)
                if hunter:
                    level_100_hunters.append(hunter.name)

        if not level_100_hunters:
            embed = discord.Embed(
                title="Badges",
                description="> *Max out your hunters to earn their badge.*",
                color=discord.Color.dark_blue()
            ).set_footer(text="System Notification")
            await ctx.send(embed=embed)
            return

        # Get all emojis and then join them
        emojis = [getEmoji(extractId(name)) for name in level_100_hunters]
        hunter_list = " ".join(emojis)

        embed = discord.Embed(
            title="Badges",
            description=f"**Hunters at Level 100**\n{hunter_list}",
            color=discord.Color.dark_teal()
        ).set_footer(text="Solo Leveling Bot | Badges")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BadgesCog(bot))