import json
import time
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from structure.emoji import getEmoji
from structure.player import Player

def load_json(filename):
    try:
        with open(filename, "r") as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {}

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f, indent=4)

CODES = {
    "valentines2025": {"expiry": 1746076800, "rewards": [{"type": "gold", "amount": 20000}, {"type": "ticket", "amount": 30}, {"type": "stone", "amount": 750}, {"type": "diamond", "amount": 1000}]},
    "servers1k": {"expiry": 1767225600, "rewards": [{"type": "gold", "amount": 25000}, {"type": "ticket", "amount": 50}, {"type": "stone", "amount": 1000}, {"type": "diamond", "amount": 500}]}
}

EMBEDS = {
    "valentines2025": discord.Embed(title="💖 Valentine's 2025 Reward!", description="Enjoy your special reward! ❤️🎁", color=discord.Color.pink()).set_footer(text="Happy Valentine's Day!"),
    "servers1k": discord.Embed(title="🎉 1000 Servers Celebration!", description="Thank you for being part of our community! Enjoy these rewards!", color=discord.Color.gold()).set_footer(text="Thank you for your support!")
}

class Redeem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="redeem", help="Redeem a special code for rewards.")
    @app_commands.describe(code="The code you want to redeem.")
    async def redeem(self, ctx: commands.Context, code: Optional[str] = None):
        support_server_id = 1314218626294878209
        if ctx.guild.id != support_server_id:
            view = discord.ui.View().add_item(discord.ui.Button(label="Join Support Server", url="https://discord.gg/ariseigris", style=discord.ButtonStyle.link))
            await ctx.send("This command can only be used in the support server!", view=view, ephemeral=True)
            return

        if not code:
            await ctx.send("Active Codes: `valentines2025`, `servers1k`\nUse `/redeem <code>` to claim.", ephemeral=True)
            return

        user_id = str(ctx.author.id)
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.send("You haven't started yet. Use `sl start`.", ephemeral=True)
            return

        redeem_data = load_json("redeem.json")
        code = code.lower()

        if code not in CODES:
            await ctx.send("⚠️ Invalid code!", ephemeral=True)
            return
        if time.time() > CODES[code]["expiry"]:
            await ctx.send("⏳ This code has expired!", ephemeral=True)
            return
        if code in redeem_data and user_id in redeem_data[code]:
            await ctx.send("❌ You have already redeemed this code!", ephemeral=True)
            return

        if code not in redeem_data: redeem_data[code] = []
        redeem_data[code].append(user_id)

        reward_text = ""
        for reward in CODES[code]["rewards"]:
            attr = reward["type"]
            amount = reward["amount"]
            setattr(player, attr, getattr(player, attr, 0) + amount)
            reward_text += f"> Obtained {amount} {getEmoji(attr)} {attr.title()}\n"
        
        await player.save()
        save_json("redeem.json", redeem_data)

        embed = EMBEDS.get(code, discord.Embed(title="Success!", color=discord.Color.green()))
        embed.add_field(name="Your Rewards:", value=reward_text, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Redeem(bot))