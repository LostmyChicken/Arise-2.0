import time
import discord
from discord.ext import commands
from discord import app_commands
from utilis.utilis import PremiumCheck
from structure.player import Player
import random
from typing import Optional
from commands.missions import track_mission_progress

class ExerciseView(discord.ui.View):
    def __init__(self, author: discord.User, max_tries: int):
        super().__init__(timeout=60.0)
        self.author = author
        self.progress = {"run": 0, "pushups": 0, "squats": 0, "situps": 0}
        self.tries = 0
        self.max_tries = max_tries
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not your training session.", ephemeral=True)
            return False
        if self.tries >= self.max_tries:
            await interaction.response.send_message("You have completed your training for now.", ephemeral=True)
            return False
        return True

    async def handle_training(self, interaction: discord.Interaction, quest_name: str):
        self.tries += 1
        increment = random.randint(5, 15)
        self.progress[quest_name] += increment

        player = await Player.get(interaction.user.id)
        if player:
            await player.dq_update(quest_name, increment)
            await player.save()
        
        embed = discord.Embed(
            title="Training in Progress...",
            description=(
                f'<:beru:1332348079516553216> "*Keep going, Monarch!*"\n\n'
                f"You performed **{quest_name.capitalize()}** and gained `+{increment}` progress.\n\n"
                f"**Attempts Remaining**: `{self.max_tries - self.tries}`"
            ),
            color=0x313239
        )
        await interaction.response.edit_message(embed=embed)

        if self.tries >= self.max_tries:
            await self.end_training()

    async def end_training(self):
        for item in self.children:
            item.disabled = True
        
        player = await Player.get(self.author.id)
        if player:
            player.inc = False
            # --- FEATURE RESTORED & GUARANTEED ---
            # This line is crucial for mission progress.
            player.mIncrease("train")
            await player.save()

            # Track mission progress
            await track_mission_progress(self.author.id, "train", 1)

        embed = discord.Embed(
            title="Training Session Complete!",
            description=(
                f'<:beru:1332348079516553216> "*An excellent session, my Liege. Here are your results:*"',
            ),
            color=discord.Color.green()
        )
        embed.add_field(name="Distance Run", value=f"`{self.progress['run']} km`", inline=True)
        embed.add_field(name="Pushups", value=f"`{self.progress['pushups']}`", inline=True)
        embed.add_field(name="Squats", value=f"`{self.progress['squats']}`", inline=True)
        embed.add_field(name="Situps", value=f"`{self.progress['situps']}`", inline=True)
        embed.set_footer(text="Check `sl quest` to see your daily quest progress.")
        
        if self.message:
            await self.message.edit(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        if not self.is_finished():
            await self.end_training()

    @discord.ui.button(emoji="🏃‍♂️", style=discord.ButtonStyle.secondary, custom_id="run")
    async def run_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_training(interaction, "run")

    @discord.ui.button(emoji="<:pushup:1317372099345776721>", style=discord.ButtonStyle.secondary, custom_id="pushup")
    async def pushup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_training(interaction, "pushups")

    @discord.ui.button(emoji="🏋️", style=discord.ButtonStyle.secondary, custom_id="squats")
    async def squats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_training(interaction, "squats")

    @discord.ui.button(emoji="<:situp:1317372972369186817>", style=discord.ButtonStyle.secondary, custom_id="situps")
    async def situp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_training(interaction, "situps")

class TrainCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="train", help="Start a training session to improve your daily quest progress.")
    async def train(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Player Not Found**\nYou don't have a profile yet. Use `sl start` to begin.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        if player.inc or player.trade:
            status = "in the middle of another command" if player.inc else "in a 🤝 trade"
            embed = discord.Embed(title="SYSTEM MESSAGE", description=f"**[ERROR] Action Blocked**\nYou are currently {status}. Please complete it before starting a new one.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        base_cooldown = 180
        premium_multiplier = PremiumCheck(player)
        cooldown = int(base_cooldown * premium_multiplier)
        
        # --- DEFINITIVE BUG FIX ---
        # This new check robustly handles bad data in the database.
        on_cooldown = False
        remaining = 0
        try:
            # Ensure player.train is a number before comparison
            if player.train and (time.time() - float(player.train) < cooldown):
                on_cooldown = True
                remaining = cooldown - (time.time() - float(player.train))
        except (ValueError, TypeError):
            # If player.train is bad data (like a string), reset it and proceed.
            player.train = None
            await player.save()

        if on_cooldown:
            minutes, seconds = divmod(int(remaining), 60)
            embed = discord.Embed(
                title="SYSTEM MESSAGE",
                description=f"**[COOLDOWN]**\nYou can train again in **{minutes}m {seconds}s**.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url="https://i.redd.it/official-solo-leveling-emotes-from-koreas-kakaotalk-app-v0-4gu5a1u2e92e1.png?width=210&format=png&auto=webp&s=12568200e6361c02e9e86f7cc21d00e2e4f46e0e")
            await ctx.send(embed=embed)
            return

        player.train = time.time()
        player.inc = True
        await player.save()
        
        embed = discord.Embed(
            title="Training Session Initiated!",
            description=(
                "Choose an exercise to begin your training. You have **5** attempts.\n\n"
                "> **Run:** Increase your stamina and endurance.\n"
                "> **Pushups:** Enhance your upper body power.\n"
                "> **Squats:** Build leg strength for better movement.\n"
                "> **Situps:** Strengthen your core."
            ),
            color=0x313239
        )
        embed.set_footer(text="Train hard and become the strongest hunter!")
        
        view = ExerciseView(ctx.author, 5)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(TrainCog(bot))