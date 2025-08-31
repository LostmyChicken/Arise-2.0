import json
from pathlib import Path
import random
import time
import discord
from discord.ext import commands
from discord import app_commands
from structure.emoji import getEmoji
from structure.player import Player

class DailyQuestView(discord.ui.View):
    """A simple view with a button to navigate to the quest command."""
    def __init__(self, author_id: int):
        super().__init__(timeout=180.0)
        self.author_id = author_id
        quest_button = discord.ui.Button(
            label="View Quests",
            style=discord.ButtonStyle.secondary,
            emoji="📜"
        )
        quest_button.callback = self.show_quest_info
        self.add_item(quest_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command author can interact with this view"""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This daily quest menu is not for you!", ephemeral=True)
            return False
        return True
    
    async def show_quest_info(self, interaction: discord.Interaction):
        await interaction.response.send_message("Use the command `sl quest` to see your new daily tasks!", ephemeral=True)

class DailyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='daily', help="Claim your daily rewards and receive new quests.")
    async def daily_quest(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        
        if player is None:
            embed = discord.Embed(title="Not Started", description=f"You haven't started the bot yet.\n`sl start` to get Re-Awakening.", color=0xE74C3C)
            await ctx.send(embed=embed)
            return
        if player.inc:
            embed = discord.Embed(title="Busy", description="❌ You are in between a command. Please finish it or wait for it to complete.", color=0xE74C3C)
            await ctx.send(embed=embed)
            return
        if player.trade:
            embed = discord.Embed(title="Trade in Progress", description=f"<@{player.id}> is in the middle of a 🤝 trade. Please complete it before proceeding.", color=0xE74C3C)
            await ctx.send(embed=embed)
            return
        
        cooldown_seconds = 86400
        current_time = time.time()
        
        if not hasattr(player, 'dS'): player.dS = 0
        if not hasattr(player, 'lD'): player.lD = None
        
        if player.lD and (current_time - float(player.lD if player.lD else 0)) > (cooldown_seconds * 2):
            player.dS = 0

        if player.daily is None or current_time - float(player.daily if player.daily else 0) >= cooldown_seconds:
            g = random.randint(1000, 10000)
            t = 10
            ke = random.randint(2, 3)
            s = 500
            
            gold_emoji = getEmoji("gold")
            stone_emoji = getEmoji("stone")
            gate_key_emoji = getEmoji("gate")
            ticket_emoji = getEmoji("ticket")
            
            max_streak_days = 10
            capped_streak = min(player.dS, max_streak_days)
            streak_bonus = 1 + (capped_streak * 0.1)
            g = int(g * streak_bonus)
            s = int(s * streak_bonus)
            t = int(t * streak_bonus)
            ke = int(ke * streak_bonus)
            
            player.dS += 1
            player.lD = current_time
            player.daily = current_time
            player.quests = {
                'situps': {'current': 0, 'required': 100},
                'pushups': {'current': 0, 'required': 100},
                'squats': {'current': 0, 'required': 100},
                'run': {'current': 0, 'required': 100}
            }
            player.stone += s
            player.gold += g
            player.ticket += t 
            player.key += ke
            await player.save()
            
            embed = discord.Embed(
                title="System Alert: Daily Login Protocol",
                description="Rewards successfully dispensed to Player inventory.",
                color=0x3498DB
            )
            embed.set_author(name=f"{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url="https://i.imgur.com/8QO92vj.png")

            embed.add_field(
                name="Dispensed Items",
                value=(
                    f"{gold_emoji} Gold: **{g:,}**\n"
                    f"{stone_emoji} Essence Stones: **{s:,}**\n"
                    f"{ticket_emoji} Gacha Tickets: **{t:,}**\n"
                    f"{gate_key_emoji} Gate Key: **{ke:,}**"
                ),
                inline=False
            )
            
            streak_percentage = int((streak_bonus - 1) * 100)
            embed.add_field(
                name="Streak Bonus",
                value=f"🔥 **Daily Streak:** `{player.dS}` Days\n✨ **Bonus Multiplier:** `+{streak_percentage}%`",
                inline=True
            )
            embed.add_field(
                name="New Orders",
                value="📜 **Quests refreshed!**\nClick the button below\nto check your new tasks.",
                inline=True
            )
            embed.set_footer(text="The System rewards diligence. Return tomorrow for more rewards.")
            
            await ctx.reply(embed=embed, view=DailyQuestView(ctx.author.id), mention_author=False)
            return
        
        remaining_time = cooldown_seconds - (current_time - float(player.daily if player.daily else 0))
        minutes, seconds = divmod(int(remaining_time), 60)
        hours, minutes = divmod(minutes, 60)
        remaining_time_str = f"in **{hours}** hours **{minutes}** minutes **{seconds}** seconds"
        
        embed = discord.Embed(
            title="System Notice: Daily Protocol on Cooldown",
            color=0xF39C12
        )
        embed.set_thumbnail(url="https://i.redd.it/official-solo-leveling-emotes-from-koreas-kakaotalk-app-v0-4gu5a1u2e92e1.png?width=210&format=png&auto=webp&s=12568200e6361c02e9e86f7cc21d00e2e4f46e0e")
        embed.add_field(name="Time Remaining", value=f"You can claim your next daily reward {remaining_time_str}.", inline=False)
        
        if hasattr(player, 'dS') and player.dS > 0:
            embed.add_field(name="Active Streak", value=f"🔥 Your current streak is **{player.dS}** days. Don't lose it!", inline=False)

        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.hybrid_command(name="quest", aliases=["q", "quests"], help="View your daily quest progress")
    async def view_quest(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        
        if player is None:
            embed = discord.Embed(title="Not Started", description=f"You haven't started the bot yet.\n{getEmoji('down')} Use `sl start` to get Re-Awakening.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        xp_reward = 400 * player.level
        ticket_reward = 5
        ticket_emoji = getEmoji("ticket")
        xp_emoji = getEmoji("xp")
        
        remaining_time = 86400 - (time.time() - float(player.daily if player.daily else 0))
        minutes, seconds = divmod(int(remaining_time), 60)
        hours, minutes = divmod(minutes, 60)
        reset_time_str = f"in **{hours}** hours **{minutes}** minutes **{seconds}** seconds"
        
        embed = discord.Embed(
            title="**DAILY QUEST PROGRESS**",
            description=(
                f"Quests reset {reset_time_str}.\n`sl train` to make progress.\n\n**__Completion Rewards__**\n"
                f"> Experience: +{xp_reward} {xp_emoji}\n> Gacha Tickets: +{ticket_reward} {ticket_emoji}"
            ),
            color=0x2A2C31
        )
        
        completed_count = 0

        # Initialize quests if they don't exist
        if not player.quests or not isinstance(player.quests, dict):
            player.quests = {
                'situps': {'current': 0, 'required': 100},
                'pushups': {'current': 0, 'required': 100},
                'squats': {'current': 0, 'required': 100},
                'run': {'current': 0, 'required': 100}
            }
            await player.save()

        # Display quests
        for quest_name, progress_data in player.quests.items():
            current = progress_data.get('current', 0)
            total = progress_data.get('required', 100)

            bar_width = 28
            progress_ratio = current / total if total > 0 else 0
            filled_length = int(bar_width * progress_ratio)
            progress_bar = "█" * filled_length + "░" * (bar_width - filled_length)

            status_emoji = "<:tick:1337057714999656469>" if current >= total else ""

            if current >= total:
                completed_count += 1

            embed.add_field(
                name=f"{quest_name.capitalize()}",
                value=f"{status_emoji} Progress: `{current}/{total}`\n-# `[{progress_bar}]`",
                inline=False
            )
        
        if completed_count == 4:
            player.quests = {}  # Clear quests
            await player.add_xp(self.bot, xp_reward, ctx.channel)
            player.ticket += ticket_reward
            await player.save()

            # Track daily quest achievement
            try:
                from structure.achievement_tracker import AchievementTracker
                await AchievementTracker.track_daily_quest(player)
            except Exception as e:
                logging.error(f"Error tracking daily quest achievement: {e}")

            embed.add_field(
                name="All Quests Complete!",
                value="Congratulations! You've finished all daily quests and earned your rewards! 🎉",
                inline=False
            )
            
        embed.set_footer(text="Complete all quests to earn rewards and grow stronger!")
        
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(DailyCog(bot))