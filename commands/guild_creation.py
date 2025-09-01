"""
Enhanced Guild Creation System with Descriptions and Filters
"""
import discord
from discord.ext import commands
from discord import ui
import asyncio
from typing import Optional
from structure.enhanced_guild import EnhancedGuild, GuildRole, GuildPermission
from structure.player import Player
from structure.emoji import getEmoji
from utilis.utilis import extractId, create_embed, SUCCESS_COLOR, ERROR_COLOR, INFO_COLOR
import logging
from datetime import datetime

class GuildCreationModal(ui.Modal):
    """Modal for guild creation with all details"""
    
    def __init__(self, view):
        super().__init__(title="Create New Guild", timeout=300)
        self.view = view
        
        # Guild name input
        self.name_input = ui.TextInput(
            label="Guild Name",
            placeholder="Enter your guild name (3-32 characters)",
            min_length=3,
            max_length=32,
            required=True
        )
        self.add_item(self.name_input)
        
        # Guild description input
        self.description_input = ui.TextInput(
            label="Guild Description",
            placeholder="Describe your guild's purpose and goals",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=True
        )
        self.add_item(self.description_input)
        
        # Guild image URL input
        self.image_input = ui.TextInput(
            label="Guild Image URL (Optional)",
            placeholder="https://example.com/image.png",
            required=False
        )
        self.add_item(self.image_input)
        
        # Guild motto/slogan
        self.motto_input = ui.TextInput(
            label="Guild Motto (Optional)",
            placeholder="A short motto or slogan for your guild",
            max_length=100,
            required=False
        )
        self.add_item(self.motto_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Validate inputs
        name = self.name_input.value.strip()
        description = self.description_input.value.strip()
        image_url = self.image_input.value.strip() if self.image_input.value else ""
        motto = self.motto_input.value.strip() if self.motto_input.value else ""
        
        # Check if guild name already exists
        guild_id = extractId(name)
        existing_guild = await EnhancedGuild.get(guild_id)
        if existing_guild:
            embed = create_embed(
                "❌ Guild Name Taken",
                f"A guild with the name '{name}' already exists. Please choose a different name.",
                ERROR_COLOR,
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Store the guild data for confirmation
        self.view.guild_data = {
            "name": name,
            "description": description,
            "image_url": image_url,
            "motto": motto
        }
        
        # Update the view to show confirmation
        self.view.current_step = "confirm"
        embed = await self.view.create_embed()
        await interaction.edit_original_response(embed=embed, view=self.view)

class GuildSettingsModal(ui.Modal):
    """Modal for guild settings configuration"""
    
    def __init__(self, view):
        super().__init__(title="Guild Settings", timeout=300)
        self.view = view
        
        # Minimum level requirement
        self.min_level_input = ui.TextInput(
            label="Minimum Level Requirement",
            placeholder="1-100 (default: 1)",
            default="1",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.min_level_input)
        
        # Maximum members
        self.max_members_input = ui.TextInput(
            label="Maximum Members",
            placeholder="10-100 (default: 50)",
            default="50",
            min_length=2,
            max_length=3,
            required=True
        )
        self.add_item(self.max_members_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            min_level = int(self.min_level_input.value)
            max_members = int(self.max_members_input.value)
            
            # Validate ranges
            if not (1 <= min_level <= 100):
                raise ValueError("Minimum level must be between 1 and 100")
            if not (10 <= max_members <= 100):
                raise ValueError("Maximum members must be between 10 and 100")
            
            # Store settings
            if not hasattr(self.view, 'guild_data'):
                self.view.guild_data = {}
            
            self.view.guild_data.update({
                "min_level": min_level,
                "max_members": max_members
            })
            
            # Update view
            self.view.current_step = "confirm"
            embed = await self.view.create_embed()
            await interaction.edit_original_response(embed=embed, view=self.view)
            
        except ValueError as e:
            embed = create_embed(
                "❌ Invalid Input",
                str(e),
                ERROR_COLOR,
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class GuildCreationView(ui.View):
    """Main guild creation interface"""
    
    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.author = ctx.author
        self.current_step = "start"
        self.guild_data = {}
        
        # Default settings
        self.guild_data = {
            "name": "",
            "description": "",
            "image_url": "",
            "motto": "",
            "min_level": 1,
            "max_members": 50,
            "application_required": True,
            "public_visibility": True,
            "allow_alliances": False
        }
    
    async def create_embed(self):
        """Create embed based on current step"""
        if self.current_step == "start":
            return await self.create_start_embed()
        elif self.current_step == "confirm":
            return await self.create_confirmation_embed()
        elif self.current_step == "success":
            return await self.create_success_embed()
    
    async def create_start_embed(self):
        """Create the initial guild creation embed"""
        embed = discord.Embed(
            title="🏰 Create New Guild",
            description="Welcome to the guild creation system! Create your own guild and lead other hunters.",
            color=INFO_COLOR
        )
        
        embed.add_field(
            name="💰 Cost",
            value=f"{getEmoji('gold')} **100,000 Gold**",
            inline=True
        )
        
        embed.add_field(
            name="👑 Benefits",
            value="• Lead your own guild\n• Recruit members\n• Guild bank system\n• Alliance capabilities",
            inline=True
        )
        
        embed.add_field(
            name="📋 Requirements",
            value=f"• Level 10+\n• 100,000 {getEmoji('gold')} Gold\n• Not in another guild",
            inline=True
        )
        
        # Check requirements
        requirements_met = []
        if self.player.level >= 10:
            requirements_met.append(f"✅ Level Requirement ({self.player.level}/10)")
        else:
            requirements_met.append(f"❌ Level Requirement ({self.player.level}/10)")
        
        if self.player.gold >= 100000:
            requirements_met.append(f"✅ Gold Requirement ({self.player.gold:,}/100,000)")
        else:
            requirements_met.append(f"❌ Gold Requirement ({self.player.gold:,}/100,000)")
        
        if not self.player.guild:
            requirements_met.append("✅ Not in a guild")
        else:
            requirements_met.append("❌ Already in a guild")
        
        embed.add_field(
            name="📊 Your Status",
            value="\n".join(requirements_met),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Next Steps",
            value="1. Click **Basic Info** to set guild name and description\n2. Click **Settings** to configure guild options\n3. Click **Create Guild** to finalize",
            inline=False
        )
        
        embed.set_footer(text="Guild creation system • Click buttons below to continue")
        return embed
    
    async def create_confirmation_embed(self):
        """Create confirmation embed showing all guild details"""
        embed = discord.Embed(
            title="🏰 Confirm Guild Creation",
            description="Please review your guild details before creating:",
            color=INFO_COLOR
        )
        
        # Basic info
        embed.add_field(
            name="📝 Basic Information",
            value=f"**Name**: {self.guild_data.get('name', 'Not set')}\n"
                  f"**Description**: {self.guild_data.get('description', 'Not set')[:100]}{'...' if len(self.guild_data.get('description', '')) > 100 else ''}\n"
                  f"**Motto**: {self.guild_data.get('motto', 'None') or 'None'}",
            inline=False
        )
        
        # Settings
        embed.add_field(
            name="⚙️ Guild Settings",
            value=f"**Min Level**: {self.guild_data.get('min_level', 1)}\n"
                  f"**Max Members**: {self.guild_data.get('max_members', 50)}\n"
                  f"**Applications**: {'Required' if self.guild_data.get('application_required', True) else 'Open Join'}\n"
                  f"**Visibility**: {'Public' if self.guild_data.get('public_visibility', True) else 'Private'}",
            inline=True
        )
        
        # Cost
        embed.add_field(
            name="💰 Creation Cost",
            value=f"{getEmoji('gold')} **100,000 Gold**\n"
                  f"Your Gold: {self.player.gold:,}",
            inline=True
        )
        
        if self.guild_data.get('image_url'):
            embed.set_thumbnail(url=self.guild_data['image_url'])
        
        embed.set_footer(text="Click 'Create Guild' to confirm or 'Back' to make changes")
        return embed
    
    async def create_success_embed(self):
        """Create success embed after guild creation"""
        embed = discord.Embed(
            title="🎉 Guild Created Successfully!",
            description=f"**{self.guild_data['name']}** has been created and you are now the Guild Master!",
            color=SUCCESS_COLOR
        )
        
        embed.add_field(
            name="🏰 Your New Guild",
            value=f"**Name**: {self.guild_data['name']}\n"
                  f"**Members**: 1/{self.guild_data.get('max_members', 50)}\n"
                  f"**Your Role**: Guild Master",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Next Steps",
            value="• Use `sl guild` to manage your guild\n"
                  "• Invite members to join\n"
                  "• Set up guild bank\n"
                  "• Configure permissions",
            inline=True
        )
        
        embed.add_field(
            name="💰 Cost Deducted",
            value=f"{getEmoji('gold')} 100,000 Gold\n"
                  f"Remaining: {self.player.gold:,}",
            inline=False
        )
        
        if self.guild_data.get('image_url'):
            embed.set_thumbnail(url=self.guild_data['image_url'])
        
        embed.set_footer(text="Welcome to guild leadership!")
        return embed

    def can_create_guild(self):
        """Check if player meets all requirements to create a guild"""
        return (
            self.player.level >= 10 and
            self.player.gold >= 100000 and
            not self.player.guild
        )

    @ui.button(label="📝 Basic Info", style=discord.ButtonStyle.primary, row=0)
    async def basic_info_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        modal = GuildCreationModal(self)
        await interaction.response.send_modal(modal)

    @ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary, row=0)
    async def settings_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        modal = GuildSettingsModal(self)
        await interaction.response.send_modal(modal)

    @ui.button(label="🔄 Toggle Applications", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_applications_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        self.guild_data["application_required"] = not self.guild_data.get("application_required", True)

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="👁️ Toggle Visibility", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_visibility_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        self.guild_data["public_visibility"] = not self.guild_data.get("public_visibility", True)

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="🤝 Toggle Alliances", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_alliances_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        self.guild_data["allow_alliances"] = not self.guild_data.get("allow_alliances", False)

        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="🏰 Create Guild", style=discord.ButtonStyle.success, row=2)
    async def create_guild_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        # Check requirements again
        if not self.can_create_guild():
            embed = create_embed(
                "❌ Requirements Not Met",
                "You don't meet the requirements to create a guild. Check your level, gold, and guild status.",
                ERROR_COLOR,
                interaction.user
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if basic info is set
        if not self.guild_data.get("name") or not self.guild_data.get("description"):
            embed = create_embed(
                "❌ Missing Information",
                "Please set the basic guild information (name and description) first.",
                ERROR_COLOR,
                interaction.user
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Create the guild
            guild_id = extractId(self.guild_data["name"])

            # Create enhanced guild
            enhanced_guild = EnhancedGuild(
                id=guild_id,
                name=self.guild_data["name"],
                owner=int(self.player.id),
                members=[{
                    "id": int(self.player.id),
                    "role": GuildRole.GUILD_MASTER.value,
                    "joined_at": datetime.now().isoformat()
                }],
                level=1,
                points=0,
                image=self.guild_data.get("image_url", ""),
                description=self.guild_data["description"],
                gates=0,
                allow_alliances=self.guild_data.get("allow_alliances", False),
                guild_bank={"gold": 0, "items": {}},
                applications=[],
                settings={
                    "min_level_requirement": self.guild_data.get("min_level", 1),
                    "application_required": self.guild_data.get("application_required", True),
                    "max_members": self.guild_data.get("max_members", 50),
                    "public_visibility": self.guild_data.get("public_visibility", True),
                    "motto": self.guild_data.get("motto", "")
                },
                created_at=datetime.now().isoformat(),
                last_active=datetime.now().isoformat()
            )

            # Save the guild
            await enhanced_guild.save()

            # Update player
            self.player.guild = guild_id
            self.player.gold -= 100000
            await self.player.save()

            # Update view to success
            self.current_step = "success"
            self.clear_items()  # Remove all buttons

            embed = await self.create_embed()
            await interaction.edit_original_response(embed=embed, view=self)

        except Exception as e:
            logging.error(f"Error creating guild: {e}")
            embed = create_embed(
                "❌ Creation Failed",
                f"Failed to create guild: {str(e)}",
                ERROR_COLOR,
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @ui.button(label="🔙 Back", style=discord.ButtonStyle.gray, row=2)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        if self.current_step == "confirm":
            self.current_step = "start"
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Nothing to go back to.", ephemeral=True)

    async def update_buttons(self):
        """Update button states based on current step and data"""
        if self.current_step == "start":
            # Enable/disable create button based on requirements and data
            create_button = discord.utils.get(self.children, label="🏰 Create Guild")
            if create_button:
                create_button.disabled = not (
                    self.can_create_guild() and
                    self.guild_data.get("name") and
                    self.guild_data.get("description")
                )
        elif self.current_step == "confirm":
            # Hide unnecessary buttons in confirmation
            for child in self.children:
                if child.label not in ["🏰 Create Guild", "🔙 Back"]:
                    child.disabled = True

class GuildBrowserView(ui.View):
    """Guild browser with filtering capabilities"""

    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.author = ctx.author
        self.current_page = 0
        self.guilds_per_page = 5
        self.filters = {
            "min_level": 1,
            "max_level": 100,
            "has_space": True,
            "applications_open": None,  # None = all, True = open, False = closed
            "alliance_enabled": None,  # None = all, True = enabled, False = disabled
            "search_term": ""
        }
        self.all_guilds = []
        self.filtered_guilds = []

    async def load_guilds(self):
        """Load all guilds from database using integrated guild system"""
        try:
            from guild_integration_manager import GuildIntegrationManager
            self.all_guilds = await GuildIntegrationManager.get_all_guilds()
            # TODO: Load actual guilds from database
            await self.apply_filters()
        except Exception as e:
            logging.error(f"Error loading guilds: {e}")
            self.all_guilds = []
            self.filtered_guilds = []

    async def apply_filters(self):
        """Apply current filters to guild list"""
        self.filtered_guilds = []

        for guild in self.all_guilds:
            # Check level requirements
            if guild.settings.get("min_level_requirement", 1) > self.player.level:
                continue

            # Check if guild has space
            if self.filters["has_space"]:
                max_members = guild.settings.get("max_members", 50)
                if len(guild.members) >= max_members:
                    continue

            # Check application requirements
            if self.filters["applications_open"] is not None:
                app_required = guild.settings.get("application_required", True)
                if self.filters["applications_open"] and app_required:
                    continue
                if not self.filters["applications_open"] and not app_required:
                    continue

            # Check alliance settings
            if self.filters["alliance_enabled"] is not None:
                if guild.allow_alliances != self.filters["alliance_enabled"]:
                    continue

            # Check search term
            if self.filters["search_term"]:
                search_term = self.filters["search_term"].lower()
                if (search_term not in guild.name.lower() and
                    search_term not in guild.description.lower()):
                    continue

            self.filtered_guilds.append(guild)

        # Reset page if needed
        max_pages = max(0, (len(self.filtered_guilds) - 1) // self.guilds_per_page)
        if self.current_page > max_pages:
            self.current_page = 0

    async def create_embed(self):
        """Create guild browser embed"""
        embed = discord.Embed(
            title="🏰 Guild Browser",
            description="Browse and filter available guilds to join",
            color=INFO_COLOR
        )

        if not self.filtered_guilds:
            embed.add_field(
                name="❌ No Guilds Found",
                value="No guilds match your current filters. Try adjusting your search criteria.",
                inline=False
            )
            return embed

        # Calculate pagination
        start_idx = self.current_page * self.guilds_per_page
        end_idx = min(start_idx + self.guilds_per_page, len(self.filtered_guilds))
        current_guilds = self.filtered_guilds[start_idx:end_idx]

        # Add guild listings
        for i, guild in enumerate(current_guilds, start_idx + 1):
            member_count = len(guild.members)
            max_members = guild.settings.get("max_members", 50)
            min_level = guild.settings.get("min_level_requirement", 1)

            # Guild status indicators
            status_indicators = []
            if guild.settings.get("application_required", True):
                status_indicators.append("📝 Applications Required")
            else:
                status_indicators.append("🚪 Open Join")

            if guild.allow_alliances:
                status_indicators.append("🤝 Alliances Enabled")

            if member_count >= max_members:
                status_indicators.append("🔒 Full")
            else:
                status_indicators.append(f"✅ {max_members - member_count} spots available")

            guild_info = (
                f"**Level Req**: {min_level}+\n"
                f"**Members**: {member_count}/{max_members}\n"
                f"**Status**: {' • '.join(status_indicators[:2])}\n"
                f"**Description**: {guild.description[:100]}{'...' if len(guild.description) > 100 else ''}"
            )

            embed.add_field(
                name=f"{i}. {guild.name}",
                value=guild_info,
                inline=False
            )

        # Add pagination info
        total_pages = max(1, (len(self.filtered_guilds) + self.guilds_per_page - 1) // self.guilds_per_page)
        embed.set_footer(
            text=f"Page {self.current_page + 1}/{total_pages} • {len(self.filtered_guilds)} guilds found"
        )

        return embed

    @ui.button(label="🔍 Search", style=discord.ButtonStyle.primary, row=0)
    async def search_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        modal = GuildSearchModal(self)
        await interaction.response.send_modal(modal)

    @ui.button(label="🎚️ Filters", style=discord.ButtonStyle.secondary, row=0)
    async def filters_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        modal = GuildFiltersModal(self)
        await interaction.response.send_modal(modal)

    @ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        await interaction.response.defer()
        await self.load_guilds()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @ui.button(label="⬅️", style=discord.ButtonStyle.gray, row=1)
    async def previous_page_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on first page.", ephemeral=True)

    @ui.button(label="➡️", style=discord.ButtonStyle.gray, row=1)
    async def next_page_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can use this.", ephemeral=True)
            return

        max_pages = max(1, (len(self.filtered_guilds) + self.guilds_per_page - 1) // self.guilds_per_page)
        if self.current_page < max_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on last page.", ephemeral=True)

class GuildSearchModal(ui.Modal):
    """Modal for guild search"""

    def __init__(self, view):
        super().__init__(title="Search Guilds", timeout=300)
        self.view = view

        self.search_input = ui.TextInput(
            label="Search Term",
            placeholder="Search guild names and descriptions...",
            default=self.view.filters["search_term"],
            required=False
        )
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        self.view.filters["search_term"] = self.search_input.value.strip()
        await self.view.apply_filters()

        embed = await self.view.create_embed()
        await interaction.edit_original_response(embed=embed, view=self.view)

class GuildFiltersModal(ui.Modal):
    """Modal for guild filters"""

    def __init__(self, view):
        super().__init__(title="Guild Filters", timeout=300)
        self.view = view

        self.min_level_input = ui.TextInput(
            label="Minimum Level (1-100)",
            placeholder="1",
            default=str(self.view.filters["min_level"]),
            required=False
        )
        self.add_item(self.min_level_input)

        self.max_level_input = ui.TextInput(
            label="Maximum Level (1-100)",
            placeholder="100",
            default=str(self.view.filters["max_level"]),
            required=False
        )
        self.add_item(self.max_level_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            if self.min_level_input.value:
                min_level = int(self.min_level_input.value)
                if 1 <= min_level <= 100:
                    self.view.filters["min_level"] = min_level

            if self.max_level_input.value:
                max_level = int(self.max_level_input.value)
                if 1 <= max_level <= 100:
                    self.view.filters["max_level"] = max_level

            await self.view.apply_filters()
            embed = await self.view.create_embed()
            await interaction.edit_original_response(embed=embed, view=self.view)

        except ValueError:
            embed = create_embed(
                "❌ Invalid Input",
                "Please enter valid numbers for level filters.",
                ERROR_COLOR,
                interaction.user
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
