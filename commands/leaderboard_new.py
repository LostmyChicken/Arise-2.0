import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import aiosqlite
import logging
from structure.emoji import getEmoji
from structure.player import Player

# Constants
LEADERBOARD_FILE = "leaderboard.json"
DATABASE_PATH = "new_player.db"

class LeaderboardMainView(ui.View):
    """Main leaderboard interface with modern UI"""
    
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.current_category = "gold"  # gold, diamond, arena, glory
        self.current_page = 1
        self.update_buttons()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True
    
    async def create_embed(self):
        """Create the leaderboard embed based on current category"""
        if self.current_category == "glory":
            return await self.create_glory_embed()
        else:
            return await self.create_standard_embed()
    
    async def create_standard_embed(self):
        """Create standard leaderboard embed (gold, diamond, arena)"""
        category_info = {
            "gold": {
                "title": f"{getEmoji('gold')} **GOLD LEADERBOARD** {getEmoji('gold')}",
                "db_column": "gold",
                "display_name": "Gold Reserve",
                "color": discord.Color.gold(),
                "format_func": lambda x: f"{x:,}g"
            },
            "diamond": {
                "title": f"{getEmoji('diamond')} **DIAMOND LEADERBOARD** {getEmoji('diamond')}",
                "db_column": "diamond",
                "display_name": "Diamond Cache",
                "color": discord.Color.blue(),
                "format_func": lambda x: f"{x:,} {getEmoji('diamond')}"
            },
            "arena": {
                "title": f"{getEmoji('attack')} **ARENA LEADERBOARD** {getEmoji('attack')}",
                "db_column": "aStreak",
                "display_name": "Arena Streak",
                "color": discord.Color.red(),
                "format_func": lambda x: f"{x:,} wins"
            }
        }
        
        info = category_info[self.current_category]
        
        try:
            with open(LEADERBOARD_FILE, "r") as file:
                data = json.load(file)
            
            db_column = info["db_column"]
            if db_column not in data or not data[db_column]:
                embed = discord.Embed(
                    title="📭 No Data Available",
                    description=f"No data available for {info['display_name']}.\nUse the refresh button to update rankings.",
                    color=discord.Color.orange()
                )
                return embed
            
            leaderboard = data[db_column]
            
            # Create description with rankings
            description = ""
            for index, player in enumerate(leaderboard, start=1):
                rank_icon = self.get_rank_icon(index)
                formatted_value = info["format_func"](player['value'])
                player_name = player.get('name', f"Hunter {player['id']}")
                
                description += (
                    f"`#{index:2}` {rank_icon} **{player_name}**\n"
                    f"     └─ *{formatted_value}*\n\n"
                )
            
            embed = discord.Embed(
                title=info["title"],
                description=description,
                color=info["color"]
            )
            
            # Add user's position if they're not in top 15
            user_position = await self.get_user_position(self.ctx.author.id, db_column)
            if user_position:
                embed.add_field(
                    name="📍 Your Position",
                    value=user_position,
                    inline=False
                )
            
            embed.set_footer(text="🏆 Hunter Association Official Rankings")
            embed.set_thumbnail(url="https://files.catbox.moe/jvxvcr.png")
            
            return embed
            
        except FileNotFoundError:
            embed = discord.Embed(
                title="❌ Data Not Found",
                description="Leaderboard data not found.\nUse the refresh button to generate rankings.",
                color=discord.Color.red()
            )
            return embed
        except Exception as e:
            logging.error(f"Leaderboard error: {e}")
            embed = discord.Embed(
                title="❌ System Error",
                description="An error occurred while loading the leaderboard.",
                color=discord.Color.red()
            )
            return embed
    
    async def create_glory_embed(self):
        """Create glory leaderboard embed"""
        try:
            items_per_page = 15
            offset = (self.current_page - 1) * items_per_page
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Get total count
                async with db.execute("SELECT COUNT(*) FROM glory") as cursor:
                    total_players = (await cursor.fetchone())[0]
                
                if total_players == 0:
                    embed = discord.Embed(
                        title="📭 Empty Glory Board",
                        description="No players found in the glory rankings yet!",
                        color=discord.Color.blue()
                    )
                    return embed
                
                # Get leaderboard data
                async with db.execute(
                    "SELECT user_id, name, points, rank, current_streak FROM glory ORDER BY points DESC LIMIT ? OFFSET ?",
                    (items_per_page, offset)
                ) as cursor:
                    top_players = await cursor.fetchall()
            
            # Create description
            description = ""
            user_position_str = await self.get_glory_position(self.ctx.author.id)
            if user_position_str:
                description += f"**📍 Your Rank:** {user_position_str}\n\n"
            
            for idx, (user_id, name, points, rank, streak) in enumerate(top_players, start=offset + 1):
                rank_icon = self.get_rank_icon(idx)
                description += (
                    f"`#{idx:2}` {rank_icon} **{name}**\n"
                    f"     └─ *AP: {points:,} • Streak: {streak:,}*\n\n"
                )
            
            total_pages = (total_players + items_per_page - 1) // items_per_page
            
            embed = discord.Embed(
                title=f"{getEmoji('SSR')} **GLORY LEADERBOARD** {getEmoji('SSR')}",
                description=description,
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"🏆 Page {self.current_page}/{total_pages} • Arena Points Rankings")
            embed.set_thumbnail(url="https://files.catbox.moe/jvxvcr.png")
            
            return embed
            
        except Exception as e:
            logging.error(f"Glory leaderboard error: {e}")
            embed = discord.Embed(
                title="❌ System Error",
                description="An error occurred while loading the glory leaderboard.",
                color=discord.Color.red()
            )
            return embed
    
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
    
    async def get_user_position(self, user_id, column):
        """Get user's position in leaderboard if not in top 15"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute(
                    f"SELECT COUNT(*) + 1 FROM players WHERE {column} > (SELECT {column} FROM players WHERE id = ?)",
                    (user_id,)
                ) as cursor:
                    position = (await cursor.fetchone())[0]
                
                async with db.execute(f"SELECT {column} FROM players WHERE id = ?", (user_id,)) as cursor:
                    result = await cursor.fetchone()
                    if result and result[0] > 0:
                        return f"#{position} with {result[0]:,}"
            return None
        except:
            return None
    
    async def get_glory_position(self, user_id):
        """Get user's glory position"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute(
                    "SELECT points, current_streak FROM glory WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        points, streak = result
                        async with db.execute(
                            "SELECT COUNT(*) + 1 FROM glory WHERE points > ?",
                            (points,)
                        ) as cursor:
                            position = (await cursor.fetchone())[0]
                        return f"#{position} • AP: {points:,} • Streak: {streak:,}"
            return None
        except:
            return None
    
    def update_buttons(self):
        """Update button states based on current category"""
        self.clear_items()
        
        # Category buttons
        self.add_item(GoldLeaderboardButton(self.current_category == "gold"))
        self.add_item(DiamondLeaderboardButton(self.current_category == "diamond"))
        self.add_item(ArenaLeaderboardButton(self.current_category == "arena"))
        self.add_item(GloryLeaderboardButton(self.current_category == "glory"))
        
        # Utility buttons
        self.add_item(RefreshButton())
        
        # Page navigation for glory
        if self.current_category == "glory":
            self.add_item(PreviousPageButton(self.current_page > 1))
            self.add_item(NextPageButton())
    
    async def update_view(self, interaction, new_category=None, new_page=None):
        """Update the view and embed"""
        if new_category:
            self.current_category = new_category
            self.current_page = 1  # Reset page when changing category
        if new_page:
            self.current_page = new_page
            
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# Button classes for the leaderboard system
class GoldLeaderboardButton(ui.Button):
    def __init__(self, is_active=False):
        super().__init__(
            label="💰 Gold",
            style=discord.ButtonStyle.success if is_active else discord.ButtonStyle.secondary,
            disabled=is_active
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.view.update_view(interaction, new_category="gold")


class DiamondLeaderboardButton(ui.Button):
    def __init__(self, is_active=False):
        super().__init__(
            label="💎 Diamond",
            style=discord.ButtonStyle.primary if is_active else discord.ButtonStyle.secondary,
            disabled=is_active
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.view.update_view(interaction, new_category="diamond")


class ArenaLeaderboardButton(ui.Button):
    def __init__(self, is_active=False):
        super().__init__(
            label="⚔️ Arena",
            style=discord.ButtonStyle.danger if is_active else discord.ButtonStyle.secondary,
            disabled=is_active
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.view.update_view(interaction, new_category="arena")


class GloryLeaderboardButton(ui.Button):
    def __init__(self, is_active=False):
        super().__init__(
            label="🏆 Glory",
            style=discord.ButtonStyle.success if is_active else discord.ButtonStyle.secondary,
            disabled=is_active
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.view.update_view(interaction, new_category="glory")


class RefreshButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔄 Refresh", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Refresh leaderboard data (same logic as original)
        try:
            categories = ["gold", "diamond", "aStreak"]
            leaderboard_data = {}
            
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
                            try:
                                user = await interaction.client.fetch_user(int(user_id))
                                user_name = user.display_name
                            except:
                                user_name = f"Hunter {user_id}"
                            
                            category_data.append({
                                "id": user_id,
                                "name": user_name,
                                "value": row[1]
                            })
                        leaderboard_data[category] = category_data
            
            with open(LEADERBOARD_FILE, "w") as file:
                json.dump(leaderboard_data, file, indent=4)
            
            # Update the view
            embed = await self.view.create_embed()
            await interaction.edit_original_response(embed=embed, view=self.view)
            
        except Exception as e:
            logging.error(f"Refresh error: {e}")
            await interaction.followup.send("❌ Failed to refresh leaderboard data.", ephemeral=True)


class PreviousPageButton(ui.Button):
    def __init__(self, enabled=True):
        super().__init__(label="◀️ Previous", style=discord.ButtonStyle.secondary, disabled=not enabled)
    
    async def callback(self, interaction: discord.Interaction):
        if self.view.current_page > 1:
            await self.view.update_view(interaction, new_page=self.view.current_page - 1)


class NextPageButton(ui.Button):
    def __init__(self):
        super().__init__(label="Next ▶️", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        await self.view.update_view(interaction, new_page=self.view.current_page + 1)
