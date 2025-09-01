import random
import discord
from discord.ext import commands
from structure.emoji import getEmoji
from structure.player import Player

# Define the missions list
missions = [
    {"cmd": "worldboss", "times": 3, "quantity": 4, "description": "Participate and defeat 3 World Bosses."},
    {"cmd": "gate", "times": 5, "quantity": 3, "description": "Participate and win 5 Gates."},
    {"cmd": "train", "times": 10, "quantity": 2, "description": "Train your body x10 times"},
    {"cmd": "upgrade", "times": 100, "quantity": 4, "description": "Upgrade any weapon/hunter x100 times"},
    {"cmd": "arena", "times": 15, "quantity": 3, "description": "Win x15 Arena matchups."},
]

# Helper function to create a progress bar
def create_progress_bar(progress, total, bar_length=22):
    progress = min(progress, total) # Ensure progress doesn't exceed total
    filled_length = int(bar_length * progress / total)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    return f"`[{bar}]` `{progress}/{total}`"

# Missions Cog
class Missions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="missions", aliases=["m", "mission"], help="View your current mission, progress, or claim rewards.")
    async def missions(self, ctx: commands.Context):
        """Assigns a new mission if none exists, shows current progress, and gives rewards upon completion."""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Error", description="You haven't started your journey yet. Use `sl start`.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        TIX = getEmoji("ticket")
        
        if not player.mission or not player.mission.get("cmd"):  # Assign new mission
            mission = random.choice(missions)
            player.mission = {"cmd": mission["cmd"], "times": 0}
            await player.save()
            
            embed = discord.Embed(
                title="New Mission Assigned",
                description=f"`📜 Quest: {mission['description']}`",
                color=discord.Color.blue()
            )
            embed.add_field(name="Reward", value=f"> Obtain {TIX} x{mission['quantity']} Tickets", inline=False)
            embed.add_field(name="Progress", value=create_progress_bar(0, mission["times"]), inline=False)
            embed.set_footer(text="Complete the quest by performing the required action.")
            await ctx.send(embed=embed)
        else:  # Show current mission or complete it
            mission_details = next((m for m in missions if m["cmd"] == player.mission.get("cmd")), None)
            
            if mission_details:
                current_progress = player.mission.get("times", 0)
                if current_progress >= mission_details["times"]:
                    # Reward player and reset mission
                    player.ticket += mission_details["quantity"]
                    player.mission = {} # Reset mission
                    await player.save()
                    
                    embed = discord.Embed(
                        title="Mission Completed!",
                        description=f"`✅ Quest: {mission_details['description']} completed!`",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Reward Claimed", value=f"> Obtained {TIX} x{mission_details['quantity']} Tickets", inline=False)
                    embed.set_footer(text="Use `sl mission` to assign a new mission.")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Current Mission",
                        description=f"`📜 Quest: {mission_details['description']}`",
                        color=discord.Color.purple()
                    )
                    embed.add_field(name="Reward", value=f"> Obtain {TIX} x{mission_details['quantity']} Tickets", inline=False)
                    embed.add_field(name="Progress", value=create_progress_bar(current_progress, mission_details["times"]), inline=False)
                    embed.set_footer(text="Complete the quest by performing the required action.")
                    await ctx.send(embed=embed)
            else:
                # If mission in player data is invalid, reset it
                player.mission = {}
                await player.save()
                embed = discord.Embed(title="Mission Error", description="Your mission data was corrupted. A new one will be assigned next time.", color=discord.Color.orange())
                await ctx.send(embed=embed)

# Mission tracking function
async def track_mission_progress(user_id: int, command: str, amount: int = 1):
    """Track mission progress for a user when they perform certain actions"""
    try:
        player = await Player.get(user_id)
        if not player or not player.mission or not player.mission.get("cmd"):
            return  # No player or no active mission

        # Check if the command matches the current mission
        if player.mission["cmd"] == command:
            # Find the mission details
            mission_details = None
            for mission in missions:
                if mission["cmd"] == command:
                    mission_details = mission
                    break

            if mission_details:
                # Update progress
                current_progress = player.mission.get("times", 0)
                new_progress = min(current_progress + amount, mission_details["times"])
                player.mission["times"] = new_progress
                await player.save()

                # Check if mission is completed
                if new_progress >= mission_details["times"]:
                    # Mission completed - this will be handled when they check /missions
                    pass

    except Exception as e:
        print(f"Error tracking mission progress: {e}")

# Setup function to add the cog to the bot
async def setup(bot):
    await bot.add_cog(Missions(bot))
