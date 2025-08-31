import discord
from discord.ext import commands
from discord import app_commands
import time
from structure.player import Player
from structure.emoji import getEmoji

class VoteView(discord.ui.View):
    """A view with buttons linking to voting sites."""
    def __init__(self):
        super().__init__()
        # Replace with actual emoji IDs or use standard emojis
        self.add_item(discord.ui.Button(label="Top.gg", url="https://top.gg/bot/1231157738629890118/vote", style=discord.ButtonStyle.link, emoji="<:topgg:1341053788732854374>"))
        self.add_item(discord.ui.Button(label="DiscordBotList", url="https://discordbotlist.com/bots/arise/upvote", style=discord.ButtonStyle.link, emoji="<:dbl:1341053789982765077>"))

class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="vote", help="Vote for the bot to get rewards and check your vote status.")
    async def vote(self, ctx: commands.Context):
        """Displays vote rewards and provides voting links."""
        player = await Player.get(ctx.author.id)
        
        embed = discord.Embed(
            title="🗳️ Vote for Arise",
            description="Your vote helps the bot grow and rewards you with valuable resources! Vote every 12 hours to maintain your streak.",
            color=0x2A2C31
        )
        
        # Emojis
        g = getEmoji("gold")
        tic = getEmoji("ticket")
        stone = getEmoji("stone")
        gk = getEmoji("gate")
        
        # Base rewards
        embed.add_field(
            name="<:topgg:1341053788732854374> Top.gg Rewards",
            value=f"{g} `5k-10k` | {tic} `5` | {stone} `100-250` | {gk} `1-2`",
            inline=False
        )
        
        embed.add_field(
            name="<:dbl:1341053789982765077> DiscordBotList Rewards",
            value=f"{tic} `2` | {gk} `1`",
            inline=False
        )
        
        if player:
            # Streak calculation
            streak_bonus = min(player.vS, 15)  # Capped at 15%
            time_since_last = time.time() - float(player.lV) if player.lV else float('inf')
            is_active_streak = time_since_last <= 129600  # 36 hours

            if not is_active_streak:
                player.vS = 0 # Reset streak
                streak_bonus = 0
                await player.save()

            # Cooldown message
            next_vote_time = player.vote + 43200 if player.vote else 0
            remaining_cooldown = next_vote_time - time.time()
            if remaining_cooldown > 0:
                hours, rem = divmod(int(remaining_cooldown), 3600)
                minutes, _ = divmod(rem, 60)
                cooldown_msg = f"⏳ Next vote in: **{hours}h {minutes}m**"
            else:
                cooldown_msg = "✅ **Ready to vote now!**"

            # Streak message
            streak_msg = f"🔥 Streak: **{player.vS} days** (+{streak_bonus}%)" if player.vS > 0 else "🔹 No active streak."

            embed.add_field(
                name="Your Status",
                value=f"{cooldown_msg}\n{streak_msg}",
                inline=False
            )

            # Show potential rewards with bonus
            if streak_bonus > 0:
                min_gold = int(5000 * (1 + streak_bonus / 100))
                max_gold = int(10000 * (1 + streak_bonus / 100))
                tickets = int(5 * (1 + streak_bonus / 100))
                stones = int(250 * (1 + streak_bonus / 100))
                
                embed.add_field(
                    name=f"Potential Rewards (w/ {int(streak_bonus)}% bonus)",
                    value=f"{g} `{min_gold}-{max_gold}` | {tic} `{tickets}` | {stone} `{stones}`",
                    inline=False
                )
        
        embed.set_footer(text="Thank you for your support!")
        
        await ctx.send(embed=embed, view=VoteView())

async def setup(bot):
    await bot.add_cog(VoteCog(bot))