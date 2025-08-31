import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands
from structure.items import ItemManager
from utilis.utilis import getStatWeapon
from commands.party import getPartyTotalPower
from structure.emoji import getEmoji
from structure.stats import getStat
from structure.player import DATABASE_PATH, Player
from structure.Rank import RankingLeaderboard

class RankEvaluation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = RankingLeaderboard()

    @commands.hybrid_command(name='evaluate', help="Evaluate your current power level and rank on the leaderboard.")
    async def evaluate_rank(self, ctx: commands.Context):
        await ctx.defer()
        player = await Player.get(ctx.author.id)
        if player is None:
            down = getEmoji("down")
            embed = discord.Embed(
                title="Not Started",
                description=f"You haven't started the bot yet.\n{down} Use `sl start` to get Re-Awakening.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
        if player.trade:
            embed = discord.Embed(
                title="Trade in Progress",
                description=f"<@{player.id}> is in the middle of a 🤝 trade. Please complete it before proceeding.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return
            
        p = await self.leaderboard.get(player.id)
        
        # Calculate Player's Base Power
        base_stats = {"Total Power": (player.hp / 5) + player.attack + player.defense + player.precision + player.mp}
        stats = getStat(["Total Power"], level=player.level, base_stats=base_stats) # Use player level for scaling

        # Calculate Party Power
        party_power = await getPartyTotalPower(player)
        
        # Calculate Equipped Weapon Power
        weapon_power = 0
        for slot in ["Weapon", "Weapon_2"]:
            if item_id := player.equipped.get(slot):
                if item_id in player.inventory:
                    # Handle both old (int) and new (dict) inventory formats
                    item_data = player.inventory[item_id]
                    weapon_level = item_data.get('level', 1) if isinstance(item_data, dict) else 1
                    weapon_stat = await getStatWeapon(item_id, weapon_level)
                    if weapon_stat:
                        weapon_power += weapon_stat.get("total_power", 0)

        new_power = int(stats.Total_Power + party_power + weapon_power)

        if p is None:
            await self.leaderboard.add_player(player.id, new_power)
            # Refetch to get the newly assigned rank
            p = await self.leaderboard.get(player.id)

        # --- FIX APPLIED HERE ---
        # The database returns a tuple, so we access by index, not by string key.
        # Table structure: (id, rank, rank_, power)
        current_power = p[3]  # Access 'power' at index 3
        
        if current_power == new_power:
            # Access 'rank' at index 1 and 'rank_' at index 2
            embed = self.create_anime_rank_embed(ctx.author.display_name, p[1], p[2], new_power, no_change=True)
            await ctx.send(embed=embed)
            return

        rank, rank_ = await self.leaderboard.evaluate(player.id, new_power)
        embed = self.create_anime_rank_embed(ctx.author.display_name, rank, rank_, new_power)
        await ctx.send(embed=embed)

    def create_anime_rank_embed(self, player_name, rank, rank_pos, power, no_change=False):
        """Generate a rank evaluation embed with an anime-inspired flair."""
        rank_titles = {
            'S-Rank': "A Legend Among Mortals!",
            'A-Rank': "An Elite Warrior of Unparalleled Skill!",
            'B-Rank': "A Rising Star with Limitless Potential!",
            'C-Rank': "A Promising Fighter with Much to Prove!",
            'D-Rank': "A Novice with a Heart of Determination!",
            'E-Rank': "A Fighter Who Gives Their All!",
        }
        rank_description = rank_titles.get(rank, "An Unranked Hunter")

        embed = discord.Embed(
            title="System Alert: Mana Signature Analyzed",
            color=discord.Color.dark_purple()
        )
        embed.set_author(name=f"{player_name}'s Evaluation")
        
        description = (
            f"**Power Level:** `{power:,}`\n"
            f"**Assigned Rank:** `{rank}` - *{rank_description}*\n"
            f"**Leaderboard Position:** `#{rank_pos}`\n\n"
        )
        
        if no_change:
            description += "⚔️ **Evaluation Complete:** Your power level remains stable. No change in rank."
        else:
            description += "⚔️ **Evaluation Complete:** Your power has been reassessed and your rank updated."
            
        embed.description = description
        embed.set_footer(text="Only the strongest survive... Will you rise to the top?")
        return embed

    @commands.hybrid_command(name='update_srank', help="Admin only: Update the S-Rank leaderboard.")
    @commands.is_owner()
    async def update_srank(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        result = await self.leaderboard.update_srank()
        embed = discord.Embed(title="S-Rank Leaderboard Update", description=result, color=discord.Color.blue())
        await ctx.send(embed=embed)
    
    async def get_player_power(self, player_id):
        """Fetch the power level of a player by their ID."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT power FROM leaderboard WHERE id = ?', (player_id,))
            result = await cursor.fetchone()
            return result[0] if result else "Unknown"

async def setup(bot):
    await bot.add_cog(RankEvaluation(bot))