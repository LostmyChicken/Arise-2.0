import logging
import discord
import json
import aiosqlite
from discord.ext import commands
from discord import app_commands
from typing import List

from structure.emoji import getEmoji

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player","data/player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/player.db"

DATABASE_PATH = get_database_path()
LEADERBOARD_FILE = "leaderboard.json"

async def leaderboard_category_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    categories = ["arena", "gold", "diamond"]
    return [
        app_commands.Choice(name=category.capitalize(), value=category)
        for category in categories if current.lower() in category.lower()
    ]

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_rank_icon(self, rank):
        """Returns rank icons based on position"""
        if rank == 1:
            return "👑"  # Crown for 1st place
        elif 2 <= rank <= 3:
            return "🔥"  # Fire for 2nd-3rd
        elif 4 <= rank <= 5:
            return "<:d_:1344279927356133427>"  # Custom emoji for 4th-5th
        elif 6 <= rank <= 10:
            return "<:d_:1344279927356133427>"  # Custom emoji for 6th-10th
        else:
            return "<:d_:1344279927356133427>"  # Custom emoji for 11th-15th

    async def fetch_user_name(self, user_id):
        """Fetch and cache user names with fallback"""
        try:
            user = await self.bot.fetch_user(int(user_id))
            return user.display_name
        except:
            return f"Hunter {user_id}"

    @commands.hybrid_command(name="leaderboard", aliases=["lb"], help="Display interactive leaderboard with multiple categories.")
    async def leaderboard(self, ctx: commands.Context, category: str = "gold"):
        """Modern leaderboard interface with interactive UI"""
        # Import the new leaderboard view
        from commands.leaderboard_new import LeaderboardMainView

        # Validate category
        valid_categories = ["gold", "diamond", "arena", "glory"]
        if category.lower() not in valid_categories:
            category = "gold"  # Default to gold if invalid

        view = LeaderboardMainView(ctx)
        view.current_category = category.lower()
        view.update_buttons()
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.hybrid_command(name="refreshlb", aliases=["refresh_leaderboard"], help="Refreshes the leaderboard cache (Bot Owner Only).")
    @commands.is_owner()
    async def refresh_leaderboard(self, ctx: commands.Context):
        """Refreshes and caches all leaderboard data with usernames (Bot Owner Only)"""
        await ctx.defer()
        
        categories = ["aStreak", "gold", "diamond"]
        leaderboard_data = {category: [] for category in categories}
        
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                async with conn.cursor() as cursor:
                    for category in categories:
                        await cursor.execute(
                            f"SELECT id, {category} FROM players "
                            f"ORDER BY {category} DESC LIMIT 15"
                        )
                        rows = await cursor.fetchall()
                        
                        category_data = []
                        for row in rows:
                            user_id = str(row[0])
                            user_name = await self.fetch_user_name(user_id)
                            category_data.append({
                                "id": user_id,
                                "name": user_name,
                                "value": row[1]
                            })
                        leaderboard_data[category] = category_data

            with open(LEADERBOARD_FILE, "w") as file:
                json.dump(leaderboard_data, file, indent=4)

            embed = discord.Embed(
                title="📊 Rankings Updated",
                description=(
                    "Hunter profiles have been scanned and updated.\n"
                    f"Use `{ctx.prefix}leaderboard <category>` to view rankings."
                ),
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="🛑 System Malfunction",
                description="The Hunter Network is unavailable. Try again later.",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)
            logging.error(f"Leaderboard refresh error: {e}")

    @commands.hybrid_command(name="top", aliases=["gloryboard"], help="Displays the top players by Glory points.")
    @app_commands.describe(page="The page number of the leaderboard to view.")
    async def top_players(self, ctx: commands.Context, page: int = 1):
        """Display the top 15 players by Glory points"""
        if page < 1:
            await ctx.send(embed=discord.Embed(title="Error", description="Page number must be 1 or greater.", color=discord.Color.red()))
            return

        items_per_page = 15
        offset = (page - 1) * items_per_page

        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute("SELECT COUNT(*) FROM glory") as cursor:
                    total_players = (await cursor.fetchone())[0]
                
                if total_players == 0:
                    await ctx.send(embed=discord.Embed(title="Empty Leaderboard", description="No players found in the glory rankings yet!", color=discord.Color.blue()))
                    return

                total_pages = (total_players + items_per_page - 1) // items_per_page
                if page > total_pages:
                    await ctx.send(embed=discord.Embed(title="Error", description=f"Invalid page number. There are only {total_pages} pages.", color=discord.Color.red()))
                    return

                async with db.execute(
                    "SELECT user_id, name, points, rank, current_streak FROM glory ORDER BY points DESC LIMIT ? OFFSET ?",
                    (items_per_page, offset)
                ) as cursor:
                    top_players = await cursor.fetchall()

            description = []
            player_position_str = await self.get_player_position(ctx.author.id)
            if player_position_str:
                description.append(f"**Your Rank:** {player_position_str}\n")
            
            for idx, (user_id, name, points, rank, hs) in enumerate(top_players, start=offset + 1):
                description.append(
                    f"`#{idx}` **{name}** • "
                    f"AP: `{points:,}` • Streak: `{hs:,}`"
                )

            embed = discord.Embed(
                title="Top Arena Leaderboard",
                description="\n".join(description),
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Page {page}/{total_pages}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Error", description=f"An error occurred while fetching the leaderboard: {e}", color=discord.Color.red()))
            logging.error(f"Top players command error: {e}")

    async def get_player_position(self, user_id: int) -> str:
        """Get a player's position in the leaderboard"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Count how many players have higher points
                async with db.execute(
                    "SELECT COUNT(*) FROM glory WHERE points > (SELECT points FROM glory WHERE user_id = ?)",
                    (user_id,)
                ) as cursor:
                    position = (await cursor.fetchone())[0] + 1

                # Get the player's glory data
                async with db.execute(
                    "SELECT points, rank, current_streak FROM glory WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    player_data = await cursor.fetchone()

            if player_data:
                points, rank, hs = player_data
                return f"#{position} | **Arena Points**: {points:,} | **Highest Streak**: {hs:,}"
            return "Not ranked yet"
        except Exception:
            return "Not ranked yet"

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))