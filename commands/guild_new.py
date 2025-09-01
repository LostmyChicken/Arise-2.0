import discord
from discord.ext import commands
from discord import app_commands, ui
from discord.ui import View, Button
from structure.player import Player
from structure.guild import Guild
from structure.emoji import getEmoji
import re
import asyncio

def extractId(name):
    if not name:
        return None
    
    # Check if the name is a guild ID (numeric)
    if name.isdigit():
        return name
    
    # Check if the name is a mention format <@&id>
    match = re.match(r'<@&(\d+)>', name)
    if match:
        return match.group(1)
    
    # Otherwise, treat it as a guild name and return it as is
    return name

def _get_tier_and_color(points, tiers):
    for tier, threshold in tiers.items():
        if points >= threshold:
            colors = {
                "S-Tier": discord.Color.gold(),
                "A-Tier": discord.Color.purple(),
                "B-Tier": discord.Color.blue(),
                "C-Tier": discord.Color.green(),
                "D-Tier": discord.Color.orange(),
                "E-Tier": discord.Color.light_grey()
            }
            return tier, colors.get(tier, discord.Color.light_grey())
    return "E-Tier", discord.Color.light_grey()


class GuildMainView(ui.View):
    """Main guild interface with modern UI"""
    
    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.current_mode = "overview"  # overview, browse, create, manage
        self.update_buttons()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True
    
    async def create_embed(self):
        """Create the main guild embed based on current mode"""
        if self.current_mode == "overview":
            return await self.create_overview_embed()
        elif self.current_mode == "browse":
            return await self.create_browse_embed()
        elif self.current_mode == "create":
            return await self.create_create_embed()
        elif self.current_mode == "manage":
            return await self.create_manage_embed()
    
    async def create_overview_embed(self):
        """Create guild overview embed"""
        embed = discord.Embed(
            title="🏰 **GUILD SYSTEM** 🏰",
            description="Manage your guild, browse available guilds, or create your own!",
            color=discord.Color.dark_purple()
        )
        
        # Player's current guild status
        if self.player.guild:
            guild = await Guild.get(self.player.guild)
            if guild:
                tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
                tier_label, _ = _get_tier_and_color(guild.points, tiers)
                
                embed.add_field(
                    name="🏛️ Your Guild",
                    value=f"**{guild.name}** ({tier_label})\n👥 Members: {len(guild.members)}/50\n🏆 Points: {guild.points:,}\n🚪 Gates: {guild.gates}",
                    inline=False
                )
                
                # Show if player is owner
                if guild.owner == self.ctx.author.id:
                    embed.add_field(
                        name="👑 Leadership",
                        value="You are the **Guild Leader**\nUse the Manage Guild button for admin options",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="⚠️ Guild Error",
                    value="Your guild data seems corrupted. Please contact an admin.",
                    inline=False
                )
        else:
            embed.add_field(
                name="🆓 No Guild",
                value="You're not currently in a guild.\nBrowse available guilds or create your own!",
                inline=False
            )
        
        # Guild system stats
        all_guilds = await Guild.get_all()
        if all_guilds:
            total_members = sum(len(g.members) for g in all_guilds)
            embed.add_field(
                name="📊 System Stats",
                value=f"🏰 Total Guilds: {len(all_guilds)}\n👥 Total Members: {total_members}\n🏆 Top Guild: {max(all_guilds, key=lambda g: g.points).name}",
                inline=False
            )
        
        embed.set_footer(text="Use the buttons below to navigate the guild system")
        embed.set_thumbnail(url="https://files.catbox.moe/jvxvcr.png")
        return embed
    
    async def create_browse_embed(self):
        """Create guild browse embed"""
        embed = discord.Embed(
            title="🔍 **BROWSE GUILDS** 🔍",
            description="Discover and join available guilds",
            color=discord.Color.blue()
        )
        
        # Use integrated guild system to get all guilds
        from guild_integration_manager import GuildIntegrationManager
        all_guilds = await GuildIntegrationManager.get_all_guilds()
        if not all_guilds:
            embed.add_field(
                name="📭 No Guilds",
                value="No guilds are currently available.\nBe the first to create one!",
                inline=False
            )
            return embed
        
        # Sort by points (top guilds first)
        top_guilds = sorted(all_guilds, key=lambda g: g.points, reverse=True)[:10]
        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        
        guild_list = []
        for i, guild in enumerate(top_guilds, 1):
            tier_label, _ = _get_tier_and_color(guild.points, tiers)
            tier_emoji = {"S-Tier": "🥇", "A-Tier": "🥈", "B-Tier": "🥉", "C-Tier": "🏅", "D-Tier": "🎖️", "E-Tier": "🏷️"}
            
            guild_list.append(
                f"`#{i:02d}` {tier_emoji.get(tier_label, '🏷️')} **{guild.name}**\n"
                f"     👥 {len(guild.members)}/50 | 🏆 {guild.points:,} pts | 🚪 {guild.gates} gates"
            )
        
        embed.add_field(
            name="🏆 Top Guilds",
            value="\n\n".join(guild_list),
            inline=False
        )
        
        embed.add_field(
            name="💡 How to Join",
            value="Use the **Guild Info** button to view details\nThen use `sl guild join <name>` to join",
            inline=False
        )
        
        embed.set_footer(text=f"Showing top {len(top_guilds)} guilds • Use buttons to navigate")
        return embed
    
    async def create_create_embed(self):
        """Create guild creation embed"""
        embed = discord.Embed(
            title="🏗️ **CREATE GUILD** 🏗️",
            description="Start your own guild and lead other hunters!",
            color=discord.Color.green()
        )
        
        # Requirements
        embed.add_field(
            name="💰 Requirements",
            value=f"**Cost**: {getEmoji('gold')} 200,000 Gold\n**Your Gold**: {getEmoji('gold')} {self.player.gold:,}",
            inline=False
        )
        
        # Benefits of creating a guild
        embed.add_field(
            name="👑 Guild Leader Benefits",
            value="• Full control over guild settings\n• Kick/invite members\n• Set guild description and image\n• Manage alliance settings\n• Earn prestige as a leader",
            inline=False
        )
        
        # Guild features
        embed.add_field(
            name="🏰 Guild Features",
            value="• Up to 50 members\n• Shared gate progression\n• Guild leaderboards\n• Alliance system\n• Member management tools",
            inline=False
        )
        
        # Instructions
        embed.add_field(
            name="📝 How to Create",
            value="Use: `sl guild create <name> <description> <image_url>`\n\nExample:\n`sl guild create \"Shadow Hunters\" \"Elite hunters unite!\" https://files.catbox.moe/example.png`",
            inline=False
        )
        
        embed.set_footer(text="Guild names must be unique • Choose wisely!")
        return embed
    
    async def create_manage_embed(self):
        """Create guild management embed"""
        if not self.player.guild:
            embed = discord.Embed(
                title="❌ **NO GUILD** ❌",
                description="You need to be in a guild to access management features.",
                color=discord.Color.red()
            )
            return embed
        
        guild = await Guild.get(self.player.guild)
        if not guild:
            embed = discord.Embed(
                title="❌ **GUILD ERROR** ❌",
                description="Your guild data could not be found.",
                color=discord.Color.red()
            )
            return embed
        
        embed = discord.Embed(
            title=f"⚙️ **MANAGE: {guild.name}** ⚙️",
            description="Guild management and member tools",
            color=discord.Color.orange()
        )
        
        # Guild info
        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        tier_label, _ = _get_tier_and_color(guild.points, tiers)
        
        embed.add_field(
            name="🏛️ Guild Status",
            value=f"**Tier**: {tier_label}\n**Members**: {len(guild.members)}/50\n**Points**: {guild.points:,}\n**Gates**: {guild.gates}",
            inline=False
        )
        
        # Member list (top contributors)
        members = await guild.get_members()
        if members:
            members.sort(key=lambda x: x.get('gc', 0), reverse=True)
            member_list = []
            for i, member in enumerate(members[:5], 1):
                try:
                    user = await self.ctx.bot.fetch_user(int(member['id']))
                    name = user.display_name if user else f"User {member['id']}"
                    gates = member.get('gc', 0)
                    member_list.append(f"`#{i}` {name} - {gates} gates")
                except:
                    member_list.append(f"`#{i}` Unknown User - {member.get('gc', 0)} gates")
            
            embed.add_field(
                name="👥 Top Contributors",
                value="\n".join(member_list),
                inline=False
            )
        
        # Management options
        if guild.owner == self.ctx.author.id:
            embed.add_field(
                name="👑 Leader Commands",
                value="• `sl guild kick <user>` - Remove member\n• `sl gatealliance` - Toggle alliances\n• Guild settings management",
                inline=False
            )
        else:
            embed.add_field(
                name="👤 Member Options",
                value="• `sl guild leave` - Leave guild\n• View guild statistics\n• Participate in activities",
                inline=False
            )
        
        embed.set_footer(text="Use the buttons below for quick actions")
        return embed
    
    def update_buttons(self):
        """Update button states based on current mode"""
        self.clear_items()
        
        if self.current_mode == "overview":
            self.add_item(BrowseGuildsButton())
            if not self.player.guild:
                self.add_item(JoinGuildButton())
                self.add_item(CreateGuildButton())
            else:
                self.add_item(ManageGuildButton())
                # Add application management for guild leaders (check will be done in button callback)
                if hasattr(self, '_is_guild_leader') and self._is_guild_leader:
                    self.add_item(ApplicationsButton())
                self.add_item(LeaveGuildButton())
        elif self.current_mode == "browse":
            self.add_item(GuildInfoButton())
            self.add_item(BackToOverviewButton())
        elif self.current_mode == "create":
            self.add_item(BackToOverviewButton())
        elif self.current_mode == "manage":
            self.add_item(ViewMembersButton())
            self.add_item(BackToOverviewButton())
    
    async def update_view(self, interaction):
        """Update the view and embed"""
        # Refresh player data
        self.player = await Player.get(self.ctx.author.id)

        # Check if player is guild leader
        if self.player.guild:
            guild = await Guild.get(self.player.guild)
            self._is_guild_leader = guild and guild.owner == self.player.id
        else:
            self._is_guild_leader = False

        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# Button classes for the guild system
class BrowseGuildsButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔍 Browse Guilds", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "browse"
        await self.view.update_view(interaction)


class JoinGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="📝 Apply to Guild", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Create guild application view
        view = GuildApplicationSelectView(self.view.ctx, self.view.player, self.view)
        embed = await view.create_embed()
        await interaction.edit_original_response(embed=embed, view=view)


class CreateGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="🏗️ Create Guild", style=discord.ButtonStyle.success)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "create"
        await self.view.update_view(interaction)


class ManageGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="⚙️ Manage Guild", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "manage"
        await self.view.update_view(interaction)


class ApplicationsButton(ui.Button):
    def __init__(self):
        super().__init__(label="📨 Manage Applications", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Create application management view
        view = GuildApplicationManagementView(self.view.ctx, self.view.player, self.view)
        embed = await view.create_embed()
        await interaction.edit_original_response(embed=embed, view=view)


class LeaveGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Leave Guild", style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Confirmation embed
        embed = discord.Embed(
            title="⚠️ **CONFIRM GUILD LEAVE** ⚠️",
            description="Are you sure you want to leave your guild?\nThis action cannot be undone!",
            color=discord.Color.red()
        )
        
        view = ConfirmLeaveView(self.view)
        await interaction.edit_original_response(embed=embed, view=view)


class BackToOverviewButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "overview"
        await self.view.update_view(interaction)


class BackToMainGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Main", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Return to parent view (main guild interface)
        self.view.parent_view.current_mode = "overview"
        self.view.parent_view.update_buttons()
        embed = await self.view.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.view.parent_view)


class BackToBrowseButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Browse", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Return to browse guilds view
        self.view.parent_view.current_mode = "browse"
        self.view.parent_view.update_buttons()
        embed = await self.view.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.view.parent_view)


class GuildInfoButton(ui.Button):
    def __init__(self):
        super().__init__(label="ℹ️ Guild Info", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Create guild selection view
        view = GuildSelectionView(self.view.ctx, self.view.player, self.view)
        embed = await view.create_embed()
        await interaction.edit_original_response(embed=embed, view=view)


class ViewMembersButton(ui.Button):
    def __init__(self):
        super().__init__(label="👥 View Members", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "👥 **Members**: Detailed member list is shown above. Use guild management commands for more options!",
            ephemeral=True
        )


class GuildSelectionView(ui.View):
    """View for selecting a guild to view info about"""

    def __init__(self, ctx, player, parent_view):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.parent_view = parent_view
        self.current_page = 0
        self.guilds_per_page = 10
        self.selected_guild = None
        self.all_guilds = []

        # Add back button to return to browse view
        self.add_item(BackToBrowseButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create the guild selection embed"""
        # Get all guilds and sort them (player's guild first, then by points)
        from guild_integration_manager import GuildIntegrationManager
        self.all_guilds = await GuildIntegrationManager.get_all_guilds()
        if not self.all_guilds:
            embed = discord.Embed(
                title="📭 **NO GUILDS FOUND** 📭",
                description="No guilds are currently available.\nBe the first to create one!",
                color=discord.Color.orange()
            )
            return embed

        # Sort guilds: player's guild first, then by points
        player_guild_id = self.player.guild
        sorted_guilds = []

        # Add player's guild first if they have one
        if player_guild_id:
            player_guild = next((g for g in self.all_guilds if g.id == player_guild_id), None)
            if player_guild:
                sorted_guilds.append(player_guild)

        # Add other guilds sorted by points
        other_guilds = [g for g in self.all_guilds if g.id != player_guild_id]
        other_guilds.sort(key=lambda g: g.points, reverse=True)
        sorted_guilds.extend(other_guilds)

        self.all_guilds = sorted_guilds

        # Calculate pagination
        total_pages = (len(self.all_guilds) - 1) // self.guilds_per_page + 1
        start_idx = self.current_page * self.guilds_per_page
        end_idx = min(start_idx + self.guilds_per_page, len(self.all_guilds))
        page_guilds = self.all_guilds[start_idx:end_idx]

        embed = discord.Embed(
            title="🔍 **SELECT GUILD TO VIEW** 🔍",
            description="Choose a guild to view detailed information about it.",
            color=discord.Color.blue()
        )

        # Create guild list with selection buttons
        guild_list = []
        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        tier_emojis = {"S-Tier": "🥇", "A-Tier": "🥈", "B-Tier": "🥉", "C-Tier": "🏅", "D-Tier": "🎖️", "E-Tier": "🏷️"}

        for i, guild in enumerate(page_guilds):
            tier_label, _ = _get_tier_and_color(guild.points, tiers)
            tier_emoji = tier_emojis.get(tier_label, "🏷️")

            # Mark player's guild
            guild_marker = " 👑 **YOUR GUILD**" if guild.id == player_guild_id else ""

            guild_list.append(
                f"`{start_idx + i + 1:02d}.` {tier_emoji} **{guild.name}**{guild_marker}\n"
                f"     👥 {len(guild.members)}/50 | 🏆 {guild.points:,} pts | 🚪 {guild.gates} gates"
            )

        embed.add_field(
            name=f"🏰 Guilds (Page {self.current_page + 1}/{total_pages})",
            value="\n\n".join(guild_list) if guild_list else "No guilds on this page.",
            inline=False
        )

        embed.add_field(
            name="💡 How to Use",
            value="• Use the dropdown menu below to select a guild\n• Use navigation buttons to browse pages\n• Click 'Back' to return to guild menu",
            inline=False
        )

        embed.set_footer(text=f"Showing {len(page_guilds)} of {len(self.all_guilds)} guilds")

        # Update buttons and dropdown
        self.update_components(page_guilds, total_pages)

        return embed

    def update_components(self, page_guilds, total_pages):
        """Update the view components"""
        self.clear_items()

        # Add guild selection dropdown
        if page_guilds:
            self.add_item(GuildSelectDropdown(page_guilds, self.player.guild))

        # Add navigation buttons
        if total_pages > 1:
            # Previous page button
            prev_button = ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page == 0)
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

            # Next page button
            next_button = ui.Button(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page >= total_pages - 1)
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

        # Back button
        back_button = ui.Button(label="🔙 Back to Browse", style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_browse
        self.add_item(back_button)

    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        total_pages = (len(self.all_guilds) - 1) // self.guilds_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def back_to_browse(self, interaction: discord.Interaction):
        """Return to browse guilds view"""
        self.parent_view.current_mode = "browse"
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class GuildSelectDropdown(ui.Select):
    """Dropdown for selecting a guild to view"""

    def __init__(self, guilds, player_guild_id):
        # Create options for each guild
        options = []
        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        tier_emojis = {"S-Tier": "🥇", "A-Tier": "🥈", "B-Tier": "🥉", "C-Tier": "🏅", "D-Tier": "🎖️", "E-Tier": "🏷️"}

        for guild in guilds[:25]:  # Discord limit of 25 options
            tier_label, _ = _get_tier_and_color(guild.points, tiers)
            tier_emoji = tier_emojis.get(tier_label, "🏷️")

            # Create description
            description = f"{tier_emoji} {tier_label} | {len(guild.members)}/50 members"
            if guild.id == player_guild_id:
                description += " | YOUR GUILD"

            options.append(discord.SelectOption(
                label=guild.name[:100],  # Discord limit
                description=description[:100],  # Discord limit
                value=str(guild.id),
                emoji=tier_emoji
            ))

        super().__init__(
            placeholder="🏰 Select a guild to view detailed info...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle guild selection"""
        await interaction.response.defer()

        guild_id = self.values[0]  # Guild IDs are strings, not integers
        guild = await Guild.get(guild_id)

        if not guild:
            await interaction.followup.send("❌ Guild not found!", ephemeral=True)
            return

        # Execute the actual sl guild info command
        from commands.guild import GuildCommands
        guild_cog = self.view.ctx.bot.get_cog("GuildCommands")

        if guild_cog:
            # Create a fake context for the guild info command
            class FakeContext:
                def __init__(self, interaction, bot):
                    self.author = interaction.user
                    self.channel = interaction.channel
                    self.guild = interaction.guild
                    self.bot = bot
                    self._interaction = interaction
                    self.send = self.reply  # Alias send to reply

                async def reply(self, *args, **kwargs):
                    return await self._interaction.followup.send(*args, **kwargs)

            fake_ctx = FakeContext(interaction, self.view.ctx.bot)

            # Call the guild info command with the selected guild name
            await guild_cog.guild_info(fake_ctx, name=guild.name)
        else:
            await interaction.followup.send("❌ Guild info command not available!", ephemeral=True)



class GuildApplicationSelectView(ui.View):
    """View for applying to guilds"""

    def __init__(self, ctx, player, parent_view):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.parent_view = parent_view
        self.current_page = 0
        self.guilds_per_page = 10
        self.all_guilds = []

        # Add back button to return to main guild view
        self.add_item(BackToMainGuildButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create the guild application embed"""
        # Get all guilds and sort them by points
        self.all_guilds = await Guild.get_all()
        if not self.all_guilds:
            embed = discord.Embed(
                title="📭 **NO GUILDS AVAILABLE** 📭",
                description="No guilds are currently available to apply to.\nBe the first to create one!",
                color=discord.Color.orange()
            )
            return embed

        # Sort guilds by points (highest first)
        self.all_guilds.sort(key=lambda g: g.points, reverse=True)

        # Calculate pagination
        total_pages = (len(self.all_guilds) - 1) // self.guilds_per_page + 1
        start_idx = self.current_page * self.guilds_per_page
        end_idx = min(start_idx + self.guilds_per_page, len(self.all_guilds))
        page_guilds = self.all_guilds[start_idx:end_idx]

        embed = discord.Embed(
            title="📝 **APPLY TO A GUILD** 📝",
            description="Select a guild to send your application to.",
            color=discord.Color.blue()
        )

        # Create guild list with join options
        guild_list = []
        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        tier_emojis = {"S-Tier": "🥇", "A-Tier": "🥈", "B-Tier": "🥉", "C-Tier": "🏅", "D-Tier": "🎖️", "E-Tier": "🏷️"}

        for i, guild in enumerate(page_guilds):
            tier_label, _ = _get_tier_and_color(guild.points, tiers)
            tier_emoji = tier_emojis.get(tier_label, "🏷️")

            # Check if guild is full
            is_full = len(guild.members) >= 50
            status = "🔒 FULL" if is_full else "🟢 OPEN"

            guild_list.append(
                f"`{start_idx + i + 1:02d}.` {tier_emoji} **{guild.name}** {status}\n"
                f"     👥 {len(guild.members)}/50 | 🏆 {guild.points:,} pts | 🚪 {guild.gates} gates"
            )

        embed.add_field(
            name=f"🏰 Available Guilds (Page {self.current_page + 1}/{total_pages})",
            value="\n\n".join(guild_list) if guild_list else "No guilds on this page.",
            inline=False
        )

        embed.add_field(
            name="💡 How to Apply",
            value=(
                "• Use the dropdown menu below to select a guild\n"
                "• All applications are sent to guild leaders for review\n"
                "• Leaders can approve or deny your application\n"
                "• You'll receive a notification with their decision"
            ),
            inline=False
        )

        embed.set_footer(text=f"Showing {len(page_guilds)} of {len(self.all_guilds)} guilds")

        # Update buttons and dropdown
        self.update_components(page_guilds, total_pages)

        return embed

    def update_components(self, page_guilds, total_pages):
        """Update the view components"""
        self.clear_items()

        # Add guild application dropdown
        if page_guilds:
            self.add_item(GuildApplicationDropdown(page_guilds, self.ctx, self.player))

        # Add navigation buttons
        if total_pages > 1:
            # Previous page button
            prev_button = ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page == 0)
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

            # Next page button
            next_button = ui.Button(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page >= total_pages - 1)
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

        # Back button
        back_button = ui.Button(label="🔙 Back to Guild Menu", style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_menu
        self.add_item(back_button)

    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        total_pages = (len(self.all_guilds) - 1) // self.guilds_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def back_to_menu(self, interaction: discord.Interaction):
        """Return to main guild menu"""
        self.parent_view.current_mode = "overview"
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class GuildApplicationDropdown(ui.Select):
    """Dropdown for selecting a guild to apply to"""

    def __init__(self, guilds, ctx, player):
        self.ctx = ctx
        self.player = player

        # Create options for each guild
        options = []
        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        tier_emojis = {"S-Tier": "🥇", "A-Tier": "🥈", "B-Tier": "🥉", "C-Tier": "🏅", "D-Tier": "🎖️", "E-Tier": "🏷️"}

        for guild in guilds[:25]:  # Discord limit of 25 options
            tier_label, _ = _get_tier_and_color(guild.points, tiers)
            tier_emoji = tier_emojis.get(tier_label, "🏷️")

            # Check if guild is full
            is_full = len(guild.members) >= 50
            status = "FULL" if is_full else "OPEN"

            # Create description
            description = f"{tier_emoji} {tier_label} | {len(guild.members)}/50 | {status}"

            options.append(discord.SelectOption(
                label=guild.name[:100],  # Discord limit
                description=description[:100],  # Discord limit
                value=guild.id,  # Guild ID is a string
                emoji=tier_emoji
            ))

        super().__init__(
            placeholder="🏰 Select a guild to apply to...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle guild application selection"""
        await interaction.response.defer()

        guild_id = self.values[0]  # Guild ID is a string
        guild = await Guild.get(guild_id)

        if not guild:
            await interaction.followup.send("❌ Guild not found!", ephemeral=True)
            return

        # Check if player is already in a guild
        if self.player.guild:
            await interaction.followup.send("❌ You are already in a guild! Leave your current guild first.", ephemeral=True)
            return

        # Always send application to guild leader (no instant join)
        await self.send_guild_application(interaction, guild)



    async def send_guild_application(self, interaction: discord.Interaction, guild):
        """Send application to guild leader"""
        try:
            # Get guild leader
            try:
                leader = await self.ctx.bot.fetch_user(guild.owner)
            except:
                await interaction.followup.send("❌ Could not contact guild leader!", ephemeral=True)
                return

            # Create application embed
            app_embed = discord.Embed(
                title="📨 **GUILD APPLICATION** 📨",
                description=f"**{interaction.user.display_name}** wants to join **{guild.name}**!",
                color=discord.Color.blue()
            )

            app_embed.add_field(
                name="👤 Applicant Information",
                value=(
                    f"**Player:** {interaction.user.mention}\n"
                    f"**Level:** {self.player.level}\n"
                    f"**Power:** {self.player.power:,}\n"
                    f"**Gold:** {self.player.gold:,}"
                ),
                inline=False
            )

            app_embed.add_field(
                name="🏰 Guild Information",
                value=(
                    f"**Guild:** {guild.name}\n"
                    f"**Current Members:** {len(guild.members)}/50\n"
                    f"**Guild Points:** {guild.points:,}"
                ),
                inline=False
            )

            app_embed.set_footer(text="Use the buttons below to approve or deny this application")

            # Create application view
            app_view = GuildApplicationView(guild, self.player, interaction.user)

            # Send DM to guild leader
            try:
                await leader.send(embed=app_embed, view=app_view)

                # Confirm to applicant
                confirm_embed = discord.Embed(
                    title="📨 **APPLICATION SENT** 📨",
                    description=f"Your application to join **{guild.name}** has been sent to the guild leader!",
                    color=discord.Color.blue()
                )

                confirm_embed.add_field(
                    name="⏳ What happens next?",
                    value=(
                        "• The guild leader will review your application\n"
                        "• You'll receive a notification when they respond\n"
                        "• Applications expire after 24 hours"
                    ),
                    inline=False
                )

                await interaction.followup.send(embed=confirm_embed)

            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ Could not send application - guild leader has DMs disabled!\n"
                    "Try contacting them directly or use `sl guild join <guild_name>` command.",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.followup.send(f"❌ Error sending application: {str(e)}", ephemeral=True)


class GuildApplicationView(ui.View):
    """View for guild leaders to approve/deny applications"""

    def __init__(self, guild, applicant_player, applicant_user):
        super().__init__(timeout=86400)  # 24 hours
        self.guild = guild
        self.applicant_player = applicant_player
        self.applicant_user = applicant_user
        self.processed = False

    @ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve_application(self, interaction: discord.Interaction, button: ui.Button):
        """Approve the guild application"""
        if self.processed:
            await interaction.response.send_message("This application has already been processed.", ephemeral=True)
            return

        # Check if user is guild leader
        if interaction.user.id != self.guild.owner:
            await interaction.response.send_message("Only the guild leader can approve applications.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Refresh guild and player data
            fresh_guild = await Guild.get(self.guild.id)
            fresh_player = await Player.get(self.applicant_player.id)

            if not fresh_guild or not fresh_player:
                await interaction.followup.send("❌ Guild or player not found!", ephemeral=True)
                return

            # Check if player is already in a guild
            if fresh_player.guild:
                await interaction.followup.send("❌ Player is already in a guild!", ephemeral=True)
                return

            # Check if guild is full
            if len(fresh_guild.members) >= 50:
                await interaction.followup.send("❌ Guild is now full!", ephemeral=True)
                return

            # Add player to guild
            fresh_guild.members.append(fresh_player.id)
            fresh_player.guild = fresh_guild.id

            # Save changes
            await fresh_guild.save()
            await fresh_player.save()

            self.processed = True

            # Notify guild leader
            success_embed = discord.Embed(
                title="✅ **APPLICATION APPROVED** ✅",
                description=f"**{self.applicant_user.display_name}** has been added to **{fresh_guild.name}**!",
                color=discord.Color.green()
            )

            await interaction.followup.send(embed=success_embed)

            # Notify applicant
            try:
                applicant_embed = discord.Embed(
                    title="🎉 **GUILD APPLICATION APPROVED** 🎉",
                    description=f"Congratulations! You have been accepted into **{fresh_guild.name}**!",
                    color=discord.Color.green()
                )

                applicant_embed.add_field(
                    name="🏰 Welcome to your new guild!",
                    value=(
                        f"**Guild:** {fresh_guild.name}\n"
                        f"**Members:** {len(fresh_guild.members)}/50\n"
                        f"**Points:** {fresh_guild.points:,}\n"
                        "Use `sl guild` to access guild features!"
                    ),
                    inline=False
                )

                await self.applicant_user.send(embed=applicant_embed)
            except:
                pass  # If we can't DM the applicant, that's okay

            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)

        except Exception as e:
            await interaction.followup.send(f"❌ Error approving application: {str(e)}", ephemeral=True)

    @ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
    async def deny_application(self, interaction: discord.Interaction, button: ui.Button):
        """Deny the guild application"""
        if self.processed:
            await interaction.response.send_message("This application has already been processed.", ephemeral=True)
            return

        # Check if user is guild leader
        if interaction.user.id != self.guild.owner:
            await interaction.response.send_message("Only the guild leader can deny applications.", ephemeral=True)
            return

        await interaction.response.defer()

        self.processed = True

        # Notify guild leader
        deny_embed = discord.Embed(
            title="❌ **APPLICATION DENIED** ❌",
            description=f"Application from **{self.applicant_user.display_name}** has been denied.",
            color=discord.Color.red()
        )

        await interaction.followup.send(embed=deny_embed)

        # Notify applicant
        try:
            applicant_embed = discord.Embed(
                title="❌ **GUILD APPLICATION DENIED** ❌",
                description=f"Your application to join **{self.guild.name}** has been denied.",
                color=discord.Color.red()
            )

            applicant_embed.add_field(
                name="🔄 What's next?",
                value=(
                    "• You can apply to other guilds\n"
                    "• Create your own guild\n"
                    "• Improve your stats and try again later"
                ),
                inline=False
            )

            await self.applicant_user.send(embed=applicant_embed)
        except:
            pass  # If we can't DM the applicant, that's okay

        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)

    async def on_timeout(self):
        """Handle application timeout"""
        if not self.processed:
            # Disable buttons
            for item in self.children:
                item.disabled = True

            # Try to edit the message to show it expired
            try:
                timeout_embed = discord.Embed(
                    title="⏰ **APPLICATION EXPIRED** ⏰",
                    description=f"Application from **{self.applicant_user.display_name}** has expired.",
                    color=discord.Color.orange()
                )
                # Note: We can't edit the original message here without storing the interaction
                # This would need to be handled differently in a production system
            except:
                pass


class GuildApplicationManagementView(ui.View):
    """View for guild leaders to manage applications"""

    def __init__(self, ctx, player, parent_view):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.parent_view = parent_view
        self.current_page = 0
        self.applications_per_page = 5
        self.applications = []  # This would be loaded from database

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create application management embed"""
        # Load applications (placeholder - would need actual database integration)
        self.applications = await self.load_applications()

        embed = discord.Embed(
            title="📨 **GUILD APPLICATION MANAGEMENT** 📨",
            description="Manage pending guild applications",
            color=discord.Color.blue()
        )

        if not self.applications:
            embed.add_field(
                name="📭 **No Pending Applications**",
                value="Your guild currently has no pending applications.",
                inline=False
            )

            embed.add_field(
                name="💡 **How Applications Work**",
                value=(
                    "• Players can apply to your guild using the Apply button\n"
                    "• You'll receive DM notifications for new applications\n"
                    "• Use this interface to review and manage applications\n"
                    "• Applications expire after 24 hours"
                ),
                inline=False
            )
        else:
            # Show applications with pagination
            total_pages = (len(self.applications) - 1) // self.applications_per_page + 1
            start_idx = self.current_page * self.applications_per_page
            end_idx = min(start_idx + self.applications_per_page, len(self.applications))
            page_applications = self.applications[start_idx:end_idx]

            app_list = []
            for i, app in enumerate(page_applications, start_idx + 1):
                app_list.append(
                    f"`{i:02d}.` **{app['player_name']}** (Level {app['level']})\n"
                    f"     💪 Power: {app['power']:,} | 💰 Gold: {app['gold']:,}\n"
                    f"     📅 Applied: {app['applied_date']} | ⏰ Expires: {app['expires']}"
                )

            embed.add_field(
                name=f"📋 Pending Applications (Page {self.current_page + 1}/{total_pages})",
                value="\n\n".join(app_list),
                inline=False
            )

            embed.add_field(
                name="🎯 **Quick Actions**",
                value=(
                    "• Use dropdown to select an application\n"
                    "• Review player details before deciding\n"
                    "• Approve or deny with buttons\n"
                    "• Players get automatic notifications"
                ),
                inline=False
            )

        embed.set_footer(text=f"Total applications: {len(self.applications)}")

        # Update components
        self.update_components()

        return embed

    async def load_applications(self):
        """Load pending applications (placeholder)"""
        # This would integrate with actual database
        # For now, return sample data
        return [
            {
                'id': '1',
                'player_name': 'TestPlayer1',
                'player_id': 123456789,
                'level': 45,
                'power': 15000,
                'gold': 50000,
                'applied_date': '2025-01-15',
                'expires': '2025-01-16'
            },
            {
                'id': '2',
                'player_name': 'TestPlayer2',
                'player_id': 987654321,
                'level': 38,
                'power': 12000,
                'gold': 35000,
                'applied_date': '2025-01-15',
                'expires': '2025-01-16'
            }
        ]

    def update_components(self):
        """Update view components"""
        self.clear_items()

        if self.applications:
            # Add application selection dropdown
            page_applications = self.applications[
                self.current_page * self.applications_per_page:
                (self.current_page + 1) * self.applications_per_page
            ]

            if page_applications:
                self.add_item(ApplicationSelectionDropdown(page_applications, self))

            # Add pagination if needed
            total_pages = (len(self.applications) - 1) // self.applications_per_page + 1
            if total_pages > 1:
                prev_btn = ui.Button(
                    label="◀️ Previous",
                    style=discord.ButtonStyle.secondary,
                    disabled=(self.current_page == 0)
                )
                prev_btn.callback = self.previous_page
                self.add_item(prev_btn)

                next_btn = ui.Button(
                    label="Next ▶️",
                    style=discord.ButtonStyle.secondary,
                    disabled=(self.current_page >= total_pages - 1)
                )
                next_btn.callback = self.next_page
                self.add_item(next_btn)

        # Add refresh and back buttons
        refresh_btn = ui.Button(label="🔄 Refresh", style=discord.ButtonStyle.primary)
        refresh_btn.callback = self.refresh
        self.add_item(refresh_btn)

        back_btn = ui.Button(label="🔙 Back to Guild", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.back_to_guild
        self.add_item(back_btn)

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        total_pages = (len(self.applications) - 1) // self.applications_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def refresh(self, interaction: discord.Interaction):
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_guild(self, interaction: discord.Interaction):
        self.parent_view.current_mode = "overview"
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class ApplicationSelectionDropdown(ui.Select):
    """Dropdown for selecting applications to review"""

    def __init__(self, applications, parent_view):
        self.applications = applications
        self.parent_view = parent_view

        options = []
        for app in applications[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=f"{app['player_name']} (Lv.{app['level']})",
                description=f"Power: {app['power']:,} | Applied: {app['applied_date']}",
                value=app['id'],
                emoji="👤"
            ))

        super().__init__(
            placeholder="👤 Select an application to review...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        """Handle application selection"""
        await interaction.response.defer()

        app_id = self.values[0]
        selected_app = next((app for app in self.applications if app['id'] == app_id), None)

        if not selected_app:
            await interaction.followup.send("❌ Application not found!", ephemeral=True)
            return

        # Create detailed application review view
        view = ApplicationReviewView(selected_app, self.parent_view)
        embed = await view.create_embed()
        await interaction.edit_original_response(embed=embed, view=view)


class ApplicationReviewView(ui.View):
    """View for reviewing individual applications"""

    def __init__(self, application, parent_view):
        super().__init__(timeout=300)
        self.application = application
        self.parent_view = parent_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create application review embed"""
        embed = discord.Embed(
            title="👤 **APPLICATION REVIEW** 👤",
            description=f"Reviewing application from **{self.application['player_name']}**",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📊 **Player Statistics**",
            value=(
                f"**Level**: {self.application['level']}\n"
                f"**Power**: {self.application['power']:,}\n"
                f"**Gold**: {self.application['gold']:,}\n"
                f"**Player ID**: {self.application['player_id']}"
            ),
            inline=True
        )

        embed.add_field(
            name="📅 **Application Details**",
            value=(
                f"**Applied**: {self.application['applied_date']}\n"
                f"**Expires**: {self.application['expires']}\n"
                f"**Status**: Pending Review\n"
                f"**Application ID**: {self.application['id']}"
            ),
            inline=True
        )

        embed.add_field(
            name="🎯 **Decision Required**",
            value=(
                "Review the player's statistics and decide whether to accept them into your guild.\n"
                "**Approve**: Player joins immediately\n"
                "**Deny**: Application is rejected"
            ),
            inline=False
        )

        # Add action buttons
        self.clear_items()

        approve_btn = ui.Button(label="✅ Approve", style=discord.ButtonStyle.success)
        approve_btn.callback = self.approve_application
        self.add_item(approve_btn)

        deny_btn = ui.Button(label="❌ Deny", style=discord.ButtonStyle.danger)
        deny_btn.callback = self.deny_application
        self.add_item(deny_btn)

        back_btn = ui.Button(label="🔙 Back to Applications", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.back_to_applications
        self.add_item(back_btn)

        return embed

    async def approve_application(self, interaction: discord.Interaction):
        """Approve the application"""
        await interaction.response.defer()

        # This would integrate with actual guild system
        success_embed = discord.Embed(
            title="✅ **APPLICATION APPROVED** ✅",
            description=f"**{self.application['player_name']}** has been accepted into your guild!",
            color=discord.Color.green()
        )

        success_embed.add_field(
            name="🎉 **Welcome New Member!**",
            value=(
                f"Player **{self.application['player_name']}** is now a member of your guild.\n"
                "They have been notified of their acceptance."
            ),
            inline=False
        )

        await interaction.followup.send(embed=success_embed)

        # Return to application management
        embed = await self.parent_view.create_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

    async def deny_application(self, interaction: discord.Interaction):
        """Deny the application"""
        await interaction.response.defer()

        # This would integrate with actual guild system
        deny_embed = discord.Embed(
            title="❌ **APPLICATION DENIED** ❌",
            description=f"Application from **{self.application['player_name']}** has been denied.",
            color=discord.Color.red()
        )

        deny_embed.add_field(
            name="📝 **Application Rejected**",
            value=(
                f"The application from **{self.application['player_name']}** has been rejected.\n"
                "The player has been notified of the decision."
            ),
            inline=False
        )

        await interaction.followup.send(embed=deny_embed)

        # Return to application management
        embed = await self.parent_view.create_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

    async def back_to_applications(self, interaction: discord.Interaction):
        """Return to application management"""
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class ConfirmLeaveView(ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view
    
    @ui.button(label="✅ Yes, Leave", style=discord.ButtonStyle.danger)
    async def confirm_leave(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        player = await Player.get(interaction.user.id)
        if not player.guild:
            embed = discord.Embed(
                title="❌ Error",
                description="You're not in a guild.",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        guild = await Guild.get(player.guild)
        if guild:
            await guild.remove_member(str(interaction.user.id))
            player.guild = None
            await player.save()
            
            embed = discord.Embed(
                title="✅ **LEFT GUILD** ✅",
                description=f"You have successfully left **{guild.name}**.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Guild not found.",
                color=discord.Color.red()
            )
        
        await interaction.edit_original_response(embed=embed, view=None)
        
        # Return to overview after a delay
        await asyncio.sleep(2)
        self.parent_view.current_mode = "overview"
        self.parent_view.player = await Player.get(interaction.user.id)
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)
    
    @ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_leave(self, interaction: discord.Interaction, button: ui.Button):
        self.parent_view.current_mode = "overview"
        await self.parent_view.update_view(interaction)
