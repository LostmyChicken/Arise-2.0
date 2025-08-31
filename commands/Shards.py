import discord
from discord.ext import commands
from discord import app_commands
from structure.items import ItemManager
from structure.heroes import HeroManager
from structure.emoji import getEmoji, getRarityEmoji
from structure.player import Player
from discord.ui import View, Button, Select
from typing import Optional
import math

class ShardsCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shards", help="View your collected hunter and weapon shards with interactive filters.")
    async def shards(self, ctx):
        player = await Player.get(ctx.author.id)

        if player is None:
            embed = discord.Embed(
                title="❌ Profile Not Found",
                description="You don't have a profile yet!\n\nUse `sl start` to begin your journey and start collecting shards!",
                color=discord.Color.red()
            )
            embed.set_footer(text="Create your profile to access the shard system!")
            await ctx.send(embed=embed)
            return

        # Create enhanced shards view with filters
        view = EnhancedShardsView(ctx, player)
        embed = await view.create_embed()

        message = await ctx.send(embed=embed, view=view)
        view.message = message

class EnhancedShardsView(View):
    def __init__(self, ctx, player):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.ctx = ctx
        self.player = player
        self.current_page = 0
        self.message = None

        # Filter settings
        self.filters = {
            'type': None,  # None, 'hunter', 'weapon'
            'rarity': None,  # None, 'SSR', 'Super Rare', 'Rare'
            'class_type': None  # None, 'Light', 'Dark', 'Fire', 'Water', 'Wind'
        }

        # Add filter buttons
        self.add_item(TypeFilterSelect())
        self.add_item(RarityFilterSelect())
        self.add_item(ClassFilterSelect())

        # Add navigation buttons
        self.add_item(PreviousPageButton())
        self.add_item(NextPageButton())
        self.add_item(ClearFiltersButton())
        self.add_item(CloseButton())

    async def get_filtered_items(self):
        """Get all shards matching current filters"""
        all_filtered_items = []
        total_shards = 0

        async def process_shards(inventory, item_manager, item_type_str):
            nonlocal total_shards
            for item_id, data in inventory.items():
                # Look for shard entries (prefixed with 's_')
                if item_id.startswith('s_'):
                    # Extract the original item ID
                    original_item_id = item_id[2:]  # Remove 's_' prefix

                    # Get shard quantity
                    shard_quantity = 0
                    if isinstance(data, dict):
                        shard_quantity = data.get('quantity', data.get('level', 0))
                    elif isinstance(data, int):
                        shard_quantity = data

                    if shard_quantity > 0:
                        item = await item_manager.get(original_item_id)
                        if not item: continue

                        # Apply filters
                        if self.filters['type'] and item_type_str != self.filters['type']: continue
                        if self.filters['class_type'] and getattr(item, "classType", "").lower() != self.filters['class_type'].lower(): continue
                        if self.filters['rarity'] and item.rarity != self.filters['rarity']: continue

                        all_filtered_items.append((item, shard_quantity, item_type_str))
                        total_shards += shard_quantity

        # Process both hunter shards and weapon shards from inventory
        if self.filters['type'] != "weapon":
            await process_shards(self.player.get_inventory(), HeroManager, "hunter")
        if self.filters['type'] != "hunter":
            await process_shards(self.player.get_inventory(), ItemManager, "weapon")

        # Sort items alphabetically by name
        all_filtered_items.sort(key=lambda x: x[0].name)
        return all_filtered_items, total_shards

    async def create_embed(self):
        """Create the shards embed with current filters and page"""
        all_filtered_items, total_shards = await self.get_filtered_items()

        # Pagination
        items_per_page = 8
        total_pages = max(1, math.ceil(len(all_filtered_items) / items_per_page))

        # Ensure current page is valid
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)

        start_index = self.current_page * items_per_page
        end_index = start_index + items_per_page
        page_items = all_filtered_items[start_index:end_index]

        # Build filter string
        active_filters = []
        if self.filters['type']: active_filters.append(f"Type: `{self.filters['type'].capitalize()}`")
        if self.filters['rarity']: active_filters.append(f"Rarity: `{self.filters['rarity']}`")
        if self.filters['class_type']: active_filters.append(f"Class: `{self.filters['class_type']}`")

        filter_str = " • ".join(active_filters) if active_filters else "None"

        # Create embed
        embed = discord.Embed(
            title="💎 Fragment Inventory",
            description=(
                "**Shards are used to upgrade the ✯ tier of hunters and weapons.**\n"
                f"Use `sl upgrade` to limit break your items.\n\n"
                f"🔍 **Active Filters**: {filter_str}"
            ),
            color=discord.Color.dark_blue()
        )

        embed.set_author(name=f"{self.ctx.author.display_name}'s Shards", icon_url=self.ctx.author.display_avatar)
        embed.set_thumbnail(url="https://files.catbox.moe/shards.png")

        # Group items by type
        hunter_lines = []
        weapon_lines = []

        for item, shard_quantity, item_type_str in page_items:
            rarity_emoji = getRarityEmoji(item.rarity)
            item_emoji = getEmoji(item.id)
            line = f"{rarity_emoji} {item_emoji} **{item.name}**\n   💎 `{shard_quantity:,}` shards"

            if item_type_str == "hunter":
                hunter_lines.append(line)
            else:
                weapon_lines.append(line)

        # Add fields
        if hunter_lines:
            embed.add_field(
                name="🏹 Hunter Fragments",
                value="\n\n".join(hunter_lines),
                inline=False
            )
        if weapon_lines:
            embed.add_field(
                name="⚔️ Weapon Fragments",
                value="\n\n".join(weapon_lines),
                inline=False
            )

        if not hunter_lines and not weapon_lines:
            embed.add_field(
                name="📭 No Fragments Found",
                value="No fragments match your current filters.\nTry adjusting your filters or collect more shards!",
                inline=False
            )

        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages} • Total Matching Shards: {total_shards:,}")
        return embed

    async def update_embed(self, interaction: discord.Interaction):
        """Update the embed with current filters and page"""
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message("❌ This is not your shard inventory!", ephemeral=True)
        return False

    async def on_timeout(self):
        if self.message:
            try:
                embed = await self.create_embed()
                embed.set_footer(text=f"{embed.footer.text} • Menu timed out")
                await self.message.edit(embed=embed, view=None)
            except:
                pass

class TypeFilterSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="All Types", value="all", emoji="🔄", description="Show both hunters and weapons"),
            discord.SelectOption(label="Hunters Only", value="hunter", emoji="🏹", description="Show only hunter fragments"),
            discord.SelectOption(label="Weapons Only", value="weapon", emoji="⚔️", description="Show only weapon fragments"),
        ]
        super().__init__(placeholder="🔍 Filter by Type", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if self.values[0] == "all":
            view.filters['type'] = None
        else:
            view.filters['type'] = self.values[0]
        view.current_page = 0  # Reset to first page
        await view.update_embed(interaction)

class RarityFilterSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="All Rarities", value="all", emoji="🌟", description="Show all rarity levels"),
            discord.SelectOption(label="SSR", value="SSR", emoji="💎", description="Show only SSR fragments"),
            discord.SelectOption(label="Super Rare", value="Super Rare", emoji="💜", description="Show only SR fragments"),
            discord.SelectOption(label="Rare", value="Rare", emoji="💙", description="Show only Rare fragments"),
        ]
        super().__init__(placeholder="✨ Filter by Rarity", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if self.values[0] == "all":
            view.filters['rarity'] = None
        else:
            view.filters['rarity'] = self.values[0]
        view.current_page = 0  # Reset to first page
        await view.update_embed(interaction)

class ClassFilterSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="All Classes", value="all", emoji="🌈", description="Show all elemental classes"),
            discord.SelectOption(label="Light", value="Light", emoji="☀️", description="Show only Light class"),
            discord.SelectOption(label="Dark", value="Dark", emoji="🌙", description="Show only Dark class"),
            discord.SelectOption(label="Fire", value="Fire", emoji="🔥", description="Show only Fire class"),
            discord.SelectOption(label="Water", value="Water", emoji="💧", description="Show only Water class"),
            discord.SelectOption(label="Wind", value="Wind", emoji="💨", description="Show only Wind class"),
        ]
        super().__init__(placeholder="🌟 Filter by Class", options=options, row=2)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if self.values[0] == "all":
            view.filters['class_type'] = None
        else:
            view.filters['class_type'] = self.values[0]
        view.current_page = 0  # Reset to first page
        await view.update_embed(interaction)

class PreviousPageButton(Button):
    def __init__(self):
        super().__init__(label="◀ Previous", style=discord.ButtonStyle.secondary, row=3)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_embed(interaction)
        else:
            await interaction.response.send_message("❌ You're already on the first page!", ephemeral=True)

class NextPageButton(Button):
    def __init__(self):
        super().__init__(label="Next ▶", style=discord.ButtonStyle.secondary, row=3)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        all_items, _ = await view.get_filtered_items()
        items_per_page = 8
        total_pages = max(1, math.ceil(len(all_items) / items_per_page))

        if view.current_page < total_pages - 1:
            view.current_page += 1
            await view.update_embed(interaction)
        else:
            await interaction.response.send_message("❌ You're already on the last page!", ephemeral=True)

class ClearFiltersButton(Button):
    def __init__(self):
        super().__init__(label="🔄 Clear Filters", style=discord.ButtonStyle.primary, row=3)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.filters = {'type': None, 'rarity': None, 'class_type': None}
        view.current_page = 0
        await view.update_embed(interaction)

class CloseButton(Button):
    def __init__(self):
        super().__init__(label="❌ Close", style=discord.ButtonStyle.danger, row=3)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 Fragment Inventory Closed",
            description="The shard inventory has been closed.\n\nUse `sl shards` to view your fragments again!",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.view.stop()

async def setup(bot):
    await bot.add_cog(ShardsCommand(bot))