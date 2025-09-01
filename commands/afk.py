import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime, timedelta

from structure.emoji import getEmoji
from structure.player import Player

class AFKRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="activity-fund", aliases=["af"], description="Claim your activity funds.")
    async def afk_rewards(self, ctx: commands.Context):
        down = getEmoji("down")
        player = await Player.get(ctx.author.id)
        
        if not player:
            embed = discord.Embed(title="Not Started", description=f"You haven't started the bot yet\n{down}Use `sl start` to get Re-Awakening!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        if player.inc:
            embed = discord.Embed(title="Busy", description="❌ You are in between a command. Finish it or wait for it to complete.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        if player.trade:
            embed = discord.Embed(title="Trade in Progress", description=f"<@{player.id}>, is in the middle of a 🤝 trade. Complete it before proceeding or join the support server if this is a bug.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        now = datetime.now()
        last_claim_time = datetime.fromisoformat(player.afk) if player.afk else None

        # Determine activity tier based on premium subscriptions
        base_afk_level = getattr(player, 'afk_level', 1)
        if player.prem3:
            afk_level = 4
        elif player.prem2:
            afk_level = 3
        elif player.prem1:
            afk_level = 2
        else:
            afk_level = base_afk_level

        elapsed_time = now - last_claim_time if last_claim_time else timedelta(days=1)

        # Calculate rewards
        minutes_elapsed = min(elapsed_time.total_seconds() // 60, 1440)
        gold_per_minute = 10 + (afk_level - 1) * 2
        xp_per_minute = 5 + (afk_level - 1) * 1
        gold = int(gold_per_minute * minutes_elapsed * (1 + (afk_level - 1) * 0.015))
        xp = int(xp_per_minute * minutes_elapsed * (1 + (afk_level - 1) * 0.015))
        
        player.inc = True
        await player.save()

        # Create an embed with reward details
        g = getEmoji("gold")
        xp_emoji = getEmoji("xp")
        embed = discord.Embed(
            title="Activity Funds",
            description=f":stopwatch: __Time Elapsed:__ **{int(minutes_elapsed)}** minutes\n"
                        f"✦ Activity Tier: **{afk_level}**\n\n"
                        f"__Earning__\n"
                        f"{g} Gold: **{gold_per_minute}/m**\n"
                        f"{xp_emoji} Experience: **{xp_per_minute}/m**",
            color=discord.Color.dark_blue()
        )
        embed.add_field(name="<a:twinkling_stars:1321908767071272970> Total Earned", value=f"{gold:,} gold and {xp:,} XP", inline=False)
        embed.set_footer(text="Click 'Claim' to receive your rewards!")

        class ClaimButton(View):
            def __init__(self, player, gold, xp, message_to_edit, bot):
                super().__init__(timeout=15) # Increased timeout slightly for better UX
                self.player = player
                self.gold = gold
                self.xp = xp
                self.message_to_edit = message_to_edit
                self.bot = bot

            @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary)
            async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    await interaction.response.defer()
                except discord.errors.NotFound:
                    # Interaction expired, try to send a followup instead
                    try:
                        await interaction.followup.send("⚠️ Interaction expired, but processing your claim...", ephemeral=True)
                    except:
                        # If even followup fails, just process silently
                        pass
                except discord.InteractionResponded:
                    # Already responded, continue processing
                    pass

                now = datetime.now()
                self.player.gold += self.gold
                # Fixed: Pass the bot instance, amount, and channel to add_xp in correct order
                await self.player.add_xp(self.bot, self.xp, interaction.channel)
                self.player.afk = now.isoformat()
                self.player.inc = False
                await self.player.save()
                self.stop()

                claimed_embed = discord.Embed(
                    title="Activity Funds Claimed!",
                    description=f"Successfully claimed rewards!\n\n"
                                f"**__You have received:__**\n"
                                f"{g} Gold - **x{self.gold:,}**\n"
                                f"{xp_emoji} Experience - **x{self.xp:,}**",
                    color=discord.Color.green()
                )
                claimed_embed.set_footer(text="Your activity time has been reset.")

                await interaction.edit_original_response(embed=claimed_embed, view=None)

            async def on_timeout(self):
                # Check if the view has already been stopped (e.g., by the button)
                if self.is_finished():
                    return

                try:
                    self.player.inc = False
                    await self.player.save()
                    timeout_embed = discord.Embed(
                        title="⏳ Timed Out",
                        description="This interaction has timed out. Please run the command again to claim your rewards.",
                        color=discord.Color.orange()
                    )
                    await self.message_to_edit.edit(embed=timeout_embed, view=None)
                except Exception as e:
                    print(f"Error in AFK timeout: {e}")
                    # Ensure player.inc is reset even if message edit fails
                    try:
                        self.player.inc = False
                        await self.player.save()
                    except:
                        pass
        
        # Send the initial message and then attach the view
        message = await ctx.send(embed=embed)
        view = ClaimButton(player, gold, xp, message, self.bot)
        await message.edit(view=view)

async def setup(bot):
    await bot.add_cog(AFKRewards(bot))