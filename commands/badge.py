import discord
from discord.ext import commands
from discord import app_commands, ui
from structure.player import Player
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.emoji import getEmoji, getRarityEmoji
import json
import math

class BadgeCog(commands.Cog):
    """Badge system for displaying previously owned items/hunters that no longer exist"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="badge", help="View your collection of previously owned items and hunters")
    async def badge(self, ctx: commands.Context):
        """Display badge collection of legacy items/hunters"""
        player = await Player.get(ctx.author.id)
        
        # Get all legacy items from player's badge collection
        badge_data = getattr(player, 'badge_collection', {})
        
        if not badge_data:
            embed = discord.Embed(
                title="🏆 **BADGE COLLECTION** 🏆",
                description="You don't have any legacy items or hunters in your badge collection yet!\n\n"
                           "Badges are earned when you previously owned items or hunters that no longer exist in the game.",
                color=discord.Color.gold()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Create badge view
        view = BadgeView(ctx.author, badge_data)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

class BadgeView(ui.View):
    """View for displaying badge collection with pagination"""
    
    def __init__(self, author, badge_data):
        super().__init__(timeout=300)
        self.author = author
        self.badge_data = badge_data
        self.current_page = 0
        self.current_item_index = 0  # For detailed view navigation
        self.items_per_page = 6
        self.current_filter = "all"  # all, hunters, items
        
    async def create_embed(self):
        """Create the main badge collection embed"""
        # Check if badge collection is empty
        if not self.badge_data:
            embed = discord.Embed(
                title="🏆 BADGE COLLECTION 🏆",
                description="You don't have any legacy items or hunters in your badge collection yet!\n\nBadges are earned when you previously owned items or hunters that no longer exist in the game.",
                color=discord.Color.gold()
            )
            return embed

        # Filter items based on current filter
        filtered_items = []

        for item_id, item_info in self.badge_data.items():
            if self.current_filter == "all":
                filtered_items.append((item_id, item_info))
            elif self.current_filter == "hunters" and item_info.get('type') == 'hunter':
                filtered_items.append((item_id, item_info))
            elif self.current_filter == "items" and item_info.get('type') == 'item':
                filtered_items.append((item_id, item_info))
        
        # Calculate pagination
        total_items = len(filtered_items)
        total_pages = max(1, math.ceil(total_items / self.items_per_page))
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered_items[start_idx:end_idx]
        
        # Create embed
        embed = discord.Embed(
            title="🏆 **LEGACY BADGE COLLECTION** 🏆",
            description=f"**Previously Owned Items & Hunters**\n"
                       f"*These items/hunters no longer exist in the game*\n\n"
                       f"**Filter:** {self.current_filter.title()} | **Total Items:** {len(filtered_items)}",
            color=discord.Color.gold()
        )
        
        if not page_items:
            embed.add_field(
                name="No Items Found",
                value="No legacy items match your current filter.",
                inline=False
            )
        else:
            # Show current item in detailed view (like the picture)
            if page_items:
                # Ensure current_item_index is within bounds
                if self.current_item_index >= len(page_items):
                    self.current_item_index = 0

                item_id, item_info = page_items[self.current_item_index]
                await self.create_detailed_item_embed(embed, item_id, item_info)

            # Add navigation info
            total_filtered = len(filtered_items)
            if total_filtered > 1:
                current_absolute_index = (self.current_page * self.items_per_page) + self.current_item_index + 1
                embed.add_field(
                    name="📋 Navigation",
                    value=f"Showing item {current_absolute_index} of {total_filtered}\nUse ◀️ ▶️ to navigate (auto-advances through all items)",
                    inline=False
                )
        
        # Add footer with collection stats
        hunter_count = sum(1 for _, info in self.badge_data.items() if info.get('type') == 'hunter')
        item_count = sum(1 for _, info in self.badge_data.items() if info.get('type') == 'item')
        
        embed.set_footer(
            text=f"Total Collection: {len(self.badge_data)} | Hunters: {hunter_count} | Items: {item_count}"
        )
        
        return embed

    async def create_detailed_item_embed(self, embed, item_id, item_info):
        """Create detailed item display like the picture shown"""
        name = item_info.get('name', 'Unknown Item')
        rarity = item_info.get('rarity', 'Rare')
        item_type = item_info.get('type', 'item')
        level = item_info.get('level', 1)
        tier = item_info.get('tier', 0)
        quantity = item_info.get('quantity', 1)
        owned_date = item_info.get('owned_date', 'Unknown')

        # Get rarity emoji and color
        rarity_emoji = getRarityEmoji(rarity)

        # Try to get original item/hero data for detailed info
        original_data = None
        if item_type == 'hunter':
            try:
                original_data = await HeroManager.get(item_id)
            except:
                pass
        else:
            try:
                original_data = await ItemManager.get(item_id)
            except:
                pass

        # Set embed color based on rarity
        if rarity == "SSR":
            embed.color = discord.Color.red()
        elif rarity == "SR":
            embed.color = discord.Color.orange()
        elif rarity == "R":
            embed.color = discord.Color.blue()
        else:
            embed.color = discord.Color.gold()

        # Add rarity indicator in top right
        embed.title = f"🏆 **{name}** {rarity_emoji}"

        # Add description if available
        if original_data and hasattr(original_data, 'description'):
            embed.description = original_data.description
        else:
            embed.description = f"*A legendary {item_type} that once belonged to you.*\n\n" \
                              f"This {item_type} was retired from the game but remains in your badge collection as a testament to your journey."

        # Add general information section
        general_info = f"• **Type:** {item_type.title()}\n"
        general_info += f"• **Rank:** {rarity}\n"

        if original_data:
            if hasattr(original_data, 'classType'):
                general_info += f"• **Element:** {original_data.classType}\n"
            elif hasattr(original_data, 'type'):
                general_info += f"• **Class:** {original_data.type}\n"

        embed.add_field(
            name="General Information",
            value=general_info,
            inline=True
        )

        # Add statistics section
        stats_info = ""
        if original_data:
            if hasattr(original_data, 'attack'):
                stats_info += f"• **Attack:** {original_data.attack}\n"
            if hasattr(original_data, 'defense'):
                stats_info += f"• **Defense:** {original_data.defense}\n"
            if hasattr(original_data, 'hp'):
                stats_info += f"• **Health:** {original_data.hp}\n"

        # Add player-specific stats
        stats_info += f"• **Your Level:** {level}\n"
        stats_info += f"• **Your Tier:** {tier}\n"
        if quantity > 1:
            stats_info += f"• **Quantity:** {quantity}\n"

        embed.add_field(
            name=f"{'Hunter' if item_type == 'hunter' else 'Item'} Statistics",
            value=stats_info if stats_info else "• **Level:** {level}\n• **Tier:** {tier}",
            inline=True
        )

        # Add image if available
        if original_data and hasattr(original_data, 'image'):
            embed.set_image(url=original_data.image)

        # Add footer with ownership info
        embed.set_footer(text=f"Owned: {owned_date} | Retired from active game")

    @ui.button(label="All", style=discord.ButtonStyle.primary, emoji="🏆")
    async def filter_all(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return
        
        self.current_filter = "all"
        self.current_page = 0
        self.current_item_index = 0
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="Hunters", style=discord.ButtonStyle.secondary, emoji="👥")
    async def filter_hunters(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return
        
        self.current_filter = "hunters"
        self.current_page = 0
        self.current_item_index = 0
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="Items", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def filter_items(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return
        
        self.current_filter = "items"
        self.current_page = 0
        self.current_item_index = 0
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="◀️", style=discord.ButtonStyle.gray, row=1)
    async def previous_item(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        # Get all filtered items
        filtered_items = []
        for item_id, item_info in self.badge_data.items():
            if self.current_filter == "all":
                filtered_items.append((item_id, item_info))
            elif self.current_filter == "hunters" and item_info.get('type') == 'hunter':
                filtered_items.append((item_id, item_info))
            elif self.current_filter == "items" and item_info.get('type') == 'item':
                filtered_items.append((item_id, item_info))

        if not filtered_items:
            await interaction.response.defer()
            return

        # Calculate current absolute position
        current_absolute_index = (self.current_page * self.items_per_page) + self.current_item_index

        # Go to previous item
        if current_absolute_index > 0:
            current_absolute_index -= 1
        else:
            # Wrap to last item
            current_absolute_index = len(filtered_items) - 1

        # Calculate new page and item index
        self.current_page = current_absolute_index // self.items_per_page
        self.current_item_index = current_absolute_index % self.items_per_page

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="▶️", style=discord.ButtonStyle.gray, row=1)
    async def next_item(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        # Get all filtered items
        filtered_items = []
        for item_id, item_info in self.badge_data.items():
            if self.current_filter == "all":
                filtered_items.append((item_id, item_info))
            elif self.current_filter == "hunters" and item_info.get('type') == 'hunter':
                filtered_items.append((item_id, item_info))
            elif self.current_filter == "items" and item_info.get('type') == 'item':
                filtered_items.append((item_id, item_info))

        if not filtered_items:
            await interaction.response.defer()
            return

        # Calculate current absolute position
        current_absolute_index = (self.current_page * self.items_per_page) + self.current_item_index

        # Go to next item
        if current_absolute_index < len(filtered_items) - 1:
            current_absolute_index += 1
        else:
            # Wrap to first item
            current_absolute_index = 0

        # Calculate new page and item index
        self.current_page = current_absolute_index // self.items_per_page
        self.current_item_index = current_absolute_index % self.items_per_page

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)



async def setup(bot):
    await bot.add_cog(BadgeCog(bot))
