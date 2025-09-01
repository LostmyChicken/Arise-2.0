"""
Title System Commands for Solo Leveling Bot
"""
import discord
from discord.ext import commands
from discord import ui
import math
from typing import List, Optional
from structure.player import Player
from structure.title_system import TitleManager, TitleCategory, Title
from utilis.utilis import create_embed, INFO_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR

class TitleSelectDropdown(ui.Select):
    """Dropdown for selecting titles to equip"""
    
    def __init__(self, author: discord.User, unlocked_titles: List[Title]):
        self.author = author
        self.unlocked_titles = unlocked_titles
        
        # Create options from unlocked titles
        options = []
        for title in unlocked_titles[:25]:  # Discord limit of 25 options
            options.append(discord.SelectOption(
                label=title.name,
                description=title.description[:100],  # Truncate if too long
                emoji=title.emoji,
                value=title.id
            ))
        
        # Add "Remove Title" option
        if options:
            options.insert(0, discord.SelectOption(
                label="Remove Title",
                description="Remove your currently equipped title",
                emoji="❌",
                value="remove_title"
            ))
        
        super().__init__(
            placeholder="Select a title to equip..." if options else "No titles available",
            options=options if options else [discord.SelectOption(label="None", value="none")],
            disabled=not bool(options)
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not your title menu.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        selected_title_id = self.values[0]
        
        if selected_title_id == "remove_title":
            # Remove active title
            player = await Player.get(self.author.id)
            if player:
                player.active_title = None
                await player.save()
            
            embed = create_embed(
                "✅ Title Removed",
                "Your title has been removed from your profile.",
                SUCCESS_COLOR,
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Update the main view
            await self.view.refresh_view(interaction)
            return
        
        if selected_title_id == "none":
            await interaction.followup.send("❌ No titles available to select.", ephemeral=True)
            return
        
        # Set the selected title as active
        success = await TitleManager.set_player_active_title(self.author.id, selected_title_id)
        
        if success:
            title = TitleManager.get_title_by_id(selected_title_id)
            embed = create_embed(
                "✅ Title Equipped",
                f"You have equipped the title: {title.get_display_name()}\n\n"
                f"**Description**: {title.description}",
                SUCCESS_COLOR,
                interaction.user
            )
            embed.color = title.get_rarity_color()
        else:
            embed = create_embed(
                "❌ Failed to Equip Title",
                "Could not equip the selected title. Please try again.",
                ERROR_COLOR,
                interaction.user
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        # Update the main view
        await self.view.refresh_view(interaction)

class TitleCategorySelect(ui.Select):
    """Dropdown for selecting title categories"""
    
    def __init__(self, author: discord.User):
        self.author = author
        
        options = [
            discord.SelectOption(
                label="All Titles",
                description="View all your titles",
                emoji="📋",
                value="all"
            ),
            discord.SelectOption(
                label="Story Titles",
                description="Titles earned from story campaign",
                emoji="📖",
                value="story"
            ),
            discord.SelectOption(
                label="Achievement Titles",
                description="Titles earned from achievements",
                emoji="🏆",
                value="achievement"
            ),
            discord.SelectOption(
                label="Rank Titles",
                description="Titles based on your hunter rank",
                emoji="⭐",
                value="rank"
            ),
            discord.SelectOption(
                label="Special Titles",
                description="Rare and special event titles",
                emoji="✨",
                value="special"
            )
        ]
        
        super().__init__(
            placeholder="Select a category to view...",
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not your title menu.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        selected_category = self.values[0]
        self.view.current_category = selected_category
        self.view.current_page = 0  # Reset to first page
        
        await self.view.refresh_view(interaction)

class TitleManagementView(ui.View):
    """Main view for title management"""
    
    def __init__(self, author: discord.User, player: Player):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.current_category = "all"
        self.current_page = 0
        self.titles_per_page = 10
        
        # Add category selector
        self.add_item(TitleCategorySelect(author))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not your title menu.", ephemeral=True)
            return False
        return True
    
    async def get_titles_for_category(self) -> List[tuple]:
        """Get titles for the current category"""
        if self.current_category == "all":
            # Get all unlocked titles
            unlocked_titles = await TitleManager.get_unlocked_titles(self.author.id)
            return [(title, True) for title in unlocked_titles]
        else:
            # Get titles by category
            try:
                category = TitleCategory(self.current_category)
                return await TitleManager.get_titles_by_category(self.author.id, category)
            except ValueError:
                return []
    
    async def create_embed(self) -> discord.Embed:
        """Create the main title management embed"""
        # Get current active title
        active_title_id = await TitleManager.get_player_active_title(self.author.id)
        active_title = TitleManager.get_title_by_id(active_title_id) if active_title_id else None
        
        # Create embed
        embed = discord.Embed(
            title="🏆 Title Management",
            description="Manage your titles and select which one to display on your profile.",
            color=INFO_COLOR
        )
        
        # Show current active title
        if active_title:
            embed.add_field(
                name="👑 Currently Equipped",
                value=f"{active_title.get_display_name()}\n*{active_title.description}*",
                inline=False
            )
        else:
            embed.add_field(
                name="👑 Currently Equipped",
                value="*No title equipped*",
                inline=False
            )
        
        # Get titles for current category
        titles = await self.get_titles_for_category()
        
        if not titles:
            embed.add_field(
                name=f"📋 {self.current_category.title()} Titles",
                value="*No titles found in this category*",
                inline=False
            )
            return embed
        
        # Pagination
        start_idx = self.current_page * self.titles_per_page
        end_idx = min(start_idx + self.titles_per_page, len(titles))
        page_titles = titles[start_idx:end_idx]
        
        # Build title list
        title_list = []
        for title, is_unlocked in page_titles:
            status = "✅" if is_unlocked else "🔒"
            rarity_emoji = {
                "common": "⚪",
                "uncommon": "🟢", 
                "rare": "🔵",
                "epic": "🟣",
                "legendary": "🟠",
                "mythic": "🔴"
            }.get(title.rarity.value, "⚪")
            
            if is_unlocked:
                title_list.append(f"{status} {rarity_emoji} {title.get_display_name()}")
            else:
                title_list.append(f"{status} {rarity_emoji} {title.name} *(Locked)*")
        
        # Add titles to embed
        category_name = self.current_category.title() if self.current_category != "all" else "All"
        total_pages = math.ceil(len(titles) / self.titles_per_page)
        
        embed.add_field(
            name=f"📋 {category_name} Titles (Page {self.current_page + 1}/{total_pages})",
            value="\n".join(title_list) if title_list else "*No titles to display*",
            inline=False
        )
        
        # Add statistics
        unlocked_count = sum(1 for _, is_unlocked in titles if is_unlocked)
        embed.add_field(
            name="📊 Statistics",
            value=f"**Unlocked**: {unlocked_count}/{len(titles)}\n"
                  f"**Category**: {category_name}\n"
                  f"**Page**: {self.current_page + 1}/{total_pages}",
            inline=True
        )
        
        embed.set_footer(text="Use the buttons below to navigate and manage your titles")
        return embed
    
    async def refresh_view(self, interaction: discord.Interaction):
        """Refresh the view with updated data"""
        # Clear existing items except category selector
        self.clear_items()
        self.add_item(TitleCategorySelect(self.author))
        
        # Add title selector for unlocked titles
        unlocked_titles = await TitleManager.get_unlocked_titles(self.author.id)
        if unlocked_titles:
            self.add_item(TitleSelectDropdown(self.author, unlocked_titles))
        
        # Add navigation buttons
        titles = await self.get_titles_for_category()
        total_pages = math.ceil(len(titles) / self.titles_per_page) if titles else 1
        
        if total_pages > 1:
            self.add_item(PreviousPageButton(disabled=self.current_page == 0))
            self.add_item(NextPageButton(disabled=self.current_page >= total_pages - 1))
        
        # Add refresh button
        self.add_item(RefreshButton())
        
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

class PreviousPageButton(ui.Button):
    """Button to go to previous page"""
    
    def __init__(self, disabled: bool = False):
        super().__init__(
            label="◀️ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if self.view.current_page > 0:
            self.view.current_page -= 1
            await self.view.refresh_view(interaction)

class NextPageButton(ui.Button):
    """Button to go to next page"""
    
    def __init__(self, disabled: bool = False):
        super().__init__(
            label="Next ▶️",
            style=discord.ButtonStyle.secondary,
            disabled=disabled,
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        titles = await self.view.get_titles_for_category()
        total_pages = math.ceil(len(titles) / self.view.titles_per_page) if titles else 1
        
        if self.view.current_page < total_pages - 1:
            self.view.current_page += 1
            await self.view.refresh_view(interaction)

class RefreshButton(ui.Button):
    """Button to refresh the view"""
    
    def __init__(self):
        super().__init__(
            label="🔄 Refresh",
            style=discord.ButtonStyle.primary,
            row=2
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Check for new story titles
        await TitleManager.check_and_unlock_story_titles(self.view.author.id)

        await self.view.refresh_view(interaction)

class TitleCog(commands.Cog):
    """Title system commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="titles", help="Manage your titles and select which one to display on your profile")
    async def titles_command(self, ctx: commands.Context):
        """Main title management command"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed(
                "❌ Not Started",
                "You haven't started your adventure yet. Use `sl start` to begin!",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Check for new story titles first
        newly_unlocked = await TitleManager.check_and_unlock_story_titles(ctx.author.id)

        # Create title management view
        view = TitleManagementView(ctx.author, player)

        # Add initial components
        unlocked_titles = await TitleManager.get_unlocked_titles(ctx.author.id)
        if unlocked_titles:
            view.add_item(TitleSelectDropdown(ctx.author, unlocked_titles))

        # Add navigation if needed
        titles = await view.get_titles_for_category()
        total_pages = math.ceil(len(titles) / view.titles_per_page) if titles else 1

        if total_pages > 1:
            view.add_item(PreviousPageButton(disabled=True))  # Start on first page
            view.add_item(NextPageButton(disabled=total_pages <= 1))

        # Add refresh button
        view.add_item(RefreshButton())

        embed = await view.create_embed()

        # If new titles were unlocked, mention them
        if newly_unlocked:
            unlocked_names = []
            for title_id in newly_unlocked:
                title = TitleManager.get_title_by_id(title_id)
                if title:
                    unlocked_names.append(title.get_display_name())

            if unlocked_names:
                embed.add_field(
                    name="🎉 New Titles Unlocked!",
                    value="\n".join(unlocked_names),
                    inline=False
                )

        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name="title", help="Quick command to set or remove your active title")
    async def title_command(self, ctx: commands.Context, *, title_name: str = None):
        """Quick title setting command"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed(
                "❌ Not Started",
                "You haven't started your adventure yet. Use `sl start` to begin!",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        if not title_name:
            # Show current title
            active_title_id = await TitleManager.get_player_active_title(ctx.author.id)
            if active_title_id:
                title = TitleManager.get_title_by_id(active_title_id)
                embed = create_embed(
                    "👑 Current Title",
                    f"Your current title: {title.get_display_name()}\n\n"
                    f"**Description**: {title.description}\n\n"
                    f"Use `sl title remove` to remove it or `sl titles` for full management.",
                    INFO_COLOR,
                    ctx.author
                )
                embed.color = title.get_rarity_color()
            else:
                embed = create_embed(
                    "👑 Current Title",
                    "You don't have any title equipped.\n\n"
                    f"Use `sl titles` to browse and equip titles.",
                    INFO_COLOR,
                    ctx.author
                )
            await ctx.reply(embed=embed, mention_author=False)
            return

        if title_name.lower() in ["remove", "none", "clear"]:
            # Remove current title
            player.active_title = None
            await player.save()

            embed = create_embed(
                "✅ Title Removed",
                "Your title has been removed from your profile.",
                SUCCESS_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Search for title by name
        unlocked_titles = await TitleManager.get_unlocked_titles(ctx.author.id)
        matching_title = None

        for title in unlocked_titles:
            if title.name.lower() == title_name.lower():
                matching_title = title
                break

        if not matching_title:
            # Try partial match
            for title in unlocked_titles:
                if title_name.lower() in title.name.lower():
                    matching_title = title
                    break

        if not matching_title:
            embed = create_embed(
                "❌ Title Not Found",
                f"Could not find a title matching '{title_name}' in your unlocked titles.\n\n"
                f"Use `sl titles` to see all available titles.",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Set the title
        success = await TitleManager.set_player_active_title(ctx.author.id, matching_title.id)

        if success:
            embed = create_embed(
                "✅ Title Equipped",
                f"You have equipped the title: {matching_title.get_display_name()}\n\n"
                f"**Description**: {matching_title.description}",
                SUCCESS_COLOR,
                ctx.author
            )
            embed.color = matching_title.get_rarity_color()
        else:
            embed = create_embed(
                "❌ Failed to Equip Title",
                "Could not equip the selected title. Please try again.",
                ERROR_COLOR,
                ctx.author
            )

        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(TitleCog(bot))
