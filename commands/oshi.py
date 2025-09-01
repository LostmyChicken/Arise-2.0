import discord
from discord.ext import commands
from discord import app_commands, ui
from typing import List, Optional
from structure.player import Player
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.emoji import getEmoji, getClassEmoji, getRarityEmoji
from utilis.utilis import create_embed, INFO_COLOR, ERROR_COLOR, SUCCESS_COLOR

class OshiView(ui.View):
    """View for managing oshi (favorite) characters."""
    
    def __init__(self, ctx, player, oshi_list, current_page=0):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.oshi_list = oshi_list
        self.current_page = current_page
        self.items_per_page = 5
        self.total_pages = max(1, (len(oshi_list) + self.items_per_page - 1) // self.items_per_page)
        
        # Update buttons
        self._update_buttons()
    
    def _update_buttons(self):
        """Update button states based on current page."""
        self.clear_items()
        
        # Navigation buttons
        if self.total_pages > 1:
            prev_button = ui.Button(
                emoji="⬅️",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_page == 0
            )
            prev_button.callback = self._prev_page
            self.add_item(prev_button)
            
            next_button = ui.Button(
                emoji="➡️",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_page >= self.total_pages - 1
            )
            next_button.callback = self._next_page
            self.add_item(next_button)
            
            page_button = ui.Button(
                label=f"{self.current_page + 1}/{self.total_pages}",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
            self.add_item(page_button)
        
        # Action buttons
        if self.oshi_list:
            remove_button = ui.Button(
                emoji="🗑️",
                label="Remove Oshi",
                style=discord.ButtonStyle.danger
            )
            remove_button.callback = self._remove_oshi
            self.add_item(remove_button)
        
        # Close button
        close_button = ui.Button(
            emoji="❌",
            label="Close",
            style=discord.ButtonStyle.secondary
        )
        close_button.callback = self._close
        self.add_item(close_button)
    
    async def _prev_page(self, interaction: discord.Interaction):
        """Handle previous page button."""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            self._update_buttons()
            embed = await self._create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def _next_page(self, interaction: discord.Interaction):
        """Handle next page button."""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return
        
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_buttons()
            embed = await self._create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    async def _remove_oshi(self, interaction: discord.Interaction):
        """Handle remove oshi button."""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return
        
        # Create dropdown for selecting which oshi to remove
        if len(self.oshi_list) == 0:
            await interaction.response.send_message("❌ No oshi to remove!", ephemeral=True)
            return
        
        # Show current page items for removal
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.oshi_list))
        page_items = self.oshi_list[start_idx:end_idx]
        
        if not page_items:
            await interaction.response.send_message("❌ No oshi on this page!", ephemeral=True)
            return
        
        # Create removal view
        removal_view = OshiRemovalView(self.ctx, self.player, page_items, self)
        embed = discord.Embed(
            title="🗑️ **REMOVE OSHI** 🗑️",
            description=(
                "⚠️ **Warning**: This will permanently remove the selected item from your oshi collection!\n\n"
                "Select which oshi you want to remove from your collection:"
            ),
            color=discord.Color.orange()
        )

        # Show items that can be removed
        removal_text = []
        for i, (entity_id, entity_type, entity) in enumerate(page_items, 1):
            emoji = getEmoji(entity_id)
            removal_text.append(f"`{i}.` {emoji} **{entity.name}** (*{entity_type}*)")

        embed.add_field(
            name="📋 Items on Current Page",
            value="\n".join(removal_text) if removal_text else "No items to remove",
            inline=False
        )

        embed.set_footer(text="💡 Click a button below to remove that oshi from your collection")
        await interaction.response.send_message(embed=embed, view=removal_view, ephemeral=True)
    
    async def _close(self, interaction: discord.Interaction):
        """Handle close button."""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return
        
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()
    
    async def _create_embed(self):
        """Create the main oshi embed."""
        embed = discord.Embed(
            title="💖 **YOUR OSHI COLLECTION** 💖",
            description=f"✨ Your favorite characters and items! ✨\n\n**Total Collection**: `{len(self.oshi_list)}` favorites",
            color=discord.Color.from_rgb(255, 105, 180)  # Hot pink
        )

        if not self.oshi_list:
            embed.add_field(
                name="🌟 Empty Collection",
                value=(
                    "Your oshi collection is waiting to be filled!\n\n"
                    "💡 **How to add favorites:**\n"
                    "• Use the 💖 button when pulling characters\n"
                    "• Add your most beloved hunters and items\n"
                    "• Build your dream collection!"
                ),
                inline=False
            )
            embed.set_image(url="https://files.catbox.moe/donb98.webp")  # Cute placeholder image
            return embed
        
        # Show current page items
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.oshi_list))
        page_items = self.oshi_list[start_idx:end_idx]

        # Categorize by type for better organization
        hunters = []
        items = []
        shadows = []

        for i, oshi_data in enumerate(page_items, start_idx + 1):
            entity_id, entity_type, entity = oshi_data

            # Get emoji and class info
            emoji = getEmoji(entity_id)
            class_emoji = getClassEmoji(getattr(entity, 'classType', ''))
            rarity_emoji = getRarityEmoji(getattr(entity, 'rarity', 'Rare'))

            # Create formatted entry
            entry = f"`{i:02d}.` {emoji} {class_emoji} {rarity_emoji} **{entity.name}**"

            # Add description if available
            if hasattr(entity, 'description') and entity.description:
                short_desc = entity.description[:50] + "..." if len(entity.description) > 50 else entity.description
                entry += f"\n     *{short_desc}*"

            # Categorize by type
            if entity_type == "Hunter":
                hunters.append(entry)
            elif entity_type == "Item":
                items.append(entry)
            elif entity_type == "Shadow":
                shadows.append(entry)

        # Add categorized sections
        if hunters:
            embed.add_field(
                name="👤 **Favorite Hunters**",
                value="\n\n".join(hunters),
                inline=False
            )

        if items:
            embed.add_field(
                name="⚔️ **Favorite Items**",
                value="\n\n".join(items),
                inline=False
            )

        if shadows:
            embed.add_field(
                name="👻 **Favorite Shadows**",
                value="\n\n".join(shadows),
                inline=False
            )

        # Add page info
        if self.total_pages > 1:
            embed.add_field(
                name="📄 Page Information",
                value=f"**Current Page**: {self.current_page + 1} of {self.total_pages}\n**Items on Page**: {len(page_items)}",
                inline=True
            )
        
        # Set thumbnail to first oshi on page
        if page_items and hasattr(page_items[0][2], 'image'):
            embed.set_thumbnail(url=page_items[0][2].image)

        # Add collection stats
        if len(self.oshi_list) > 0:
            # Count by type
            type_counts = {"Hunter": 0, "Item": 0, "Shadow": 0}
            for _, entity_type, _ in self.oshi_list:
                type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

            stats_text = []
            if type_counts["Hunter"] > 0:
                stats_text.append(f"👤 {type_counts['Hunter']} Hunters")
            if type_counts["Item"] > 0:
                stats_text.append(f"⚔️ {type_counts['Item']} Items")
            if type_counts["Shadow"] > 0:
                stats_text.append(f"👻 {type_counts['Shadow']} Shadows")

            embed.add_field(
                name="📊 Collection Stats",
                value=" • ".join(stats_text) if stats_text else "No favorites yet",
                inline=True
            )

        embed.set_footer(
            text="💡 Tip: Use the 💖 button when pulling to add more favorites! • Use 🗑️ to remove items",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # Heart emoji
        )
        return embed

class OshiRemovalView(ui.View):
    """View for removing specific oshi items."""
    
    def __init__(self, ctx, player, page_items, parent_view):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.player = player
        self.page_items = page_items
        self.parent_view = parent_view
        
        # Create removal buttons
        for i, (entity_id, entity_type, entity) in enumerate(page_items[:5]):  # Max 5 buttons
            button = ui.Button(
                label=f"Remove {entity.name}",
                style=discord.ButtonStyle.danger,
                emoji="🗑️"
            )
            button.callback = self._create_removal_callback(entity_id, entity.name)
            self.add_item(button)
    
    def _create_removal_callback(self, entity_id, entity_name):
        """Create callback for removal button."""
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
                return
            
            # Remove from player's oshi list
            if hasattr(self.player, 'oshi_list') and entity_id in self.player.oshi_list:
                self.player.oshi_list.remove(entity_id)
                await self.player.save()
                
                embed = discord.Embed(
                    title="✅ **OSHI REMOVED** ✅",
                    description=f"💔 **{entity_name}** has been removed from your oshi collection.\n\nYou can always add it back later using the 💖 button when pulling!",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Your oshi collection has been updated")
                await interaction.response.edit_message(embed=embed, view=None)
                
                # Update parent view
                self.parent_view.oshi_list = [(eid, etype, eobj) for eid, etype, eobj in self.parent_view.oshi_list if eid != entity_id]
                self.parent_view.total_pages = max(1, (len(self.parent_view.oshi_list) + self.parent_view.items_per_page - 1) // self.parent_view.items_per_page)
                if self.parent_view.current_page >= self.parent_view.total_pages:
                    self.parent_view.current_page = max(0, self.parent_view.total_pages - 1)
            else:
                await interaction.response.send_message("❌ Oshi not found in collection!", ephemeral=True)
        
        return callback

class OshiCog(commands.Cog):
    """Cog for managing oshi (favorite) characters and items."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="oshi", help="View and manage your oshi (favorite) collection.")
    async def oshi(self, ctx: commands.Context):
        """Display the player's oshi collection."""
        
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed(
                "Not Started",
                "You haven't started your adventure yet. Use `sl start` to begin!",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Get oshi list - ensure it exists
        if not hasattr(player, 'oshi_list') or player.oshi_list is None:
            player.oshi_list = []
            await player.save()

        oshi_list = player.oshi_list

        # Load oshi data
        oshi_data = []
        for entity_id in oshi_list:
            # Try to load as hunter first
            entity = await HeroManager.get(entity_id)
            if entity:
                oshi_data.append((entity_id, "Hunter", entity))
            else:
                # Try to load as item
                entity = await ItemManager.get(entity_id)
                if entity:
                    oshi_data.append((entity_id, "Item", entity))
                else:
                    # Try to load as shadow
                    from structure.shadow import Shadow
                    entity = await Shadow.get(entity_id)
                    if entity:
                        oshi_data.append((entity_id, "Shadow", entity))
        
        # Create view
        view = OshiView(ctx, player, oshi_data)
        embed = await view._create_embed()
        
        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot):
    await bot.add_cog(OshiCog(bot))
