"""
Channel-specific command management commands
Allows admins to enable/disable commands in specific channels
"""

import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from typing import List, Dict, Optional
import asyncio

from structure.channel_commands import channel_command_manager
from utilis.interaction_handler import InteractionHandler

class ChannelCommandManagementCog(commands.Cog):
    """Cog for managing channel-specific command settings"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # All available commands organized by category
        self.command_categories = {
            "👤 Player & Profile": ["start", "profile", "stats", "inventory", "team", "equip", "afk"],
            "⚔️ Combat & Battles": ["fight", "arena", "dungeonui", "gates", "skills", "system"],
            "🎲 Gacha & Items": ["pull", "gacha", "upgrade", "sacrifice", "oshi", "redeem"],
            "🏰 Guild & Social": ["guild", "leaderboard", "lb", "vote"],
            "💰 Economy & Trading": ["daily", "shop", "trade", "market", "boost"],
            "📖 Story & Quests": ["story", "trivia", "train", "missions", "tutorial", "cooldowns"],
            "🔔 Notifications & Settings": ["notifications", "timezone"],
            "🌍 World Boss & Raids": ["raid", "worldboss"],
            "🔧 Utility & Help": ["help", "fixuser", "unstuck", "ping", "changelog", "view"]
        }
        
        # Flatten all commands for easy access
        self.all_commands = []
        for commands_list in self.command_categories.values():
            self.all_commands.extend(commands_list)
    
    @commands.command(name="channelcommands", help="Manage command availability in this channel")
    @commands.has_permissions(administrator=True)
    async def channel_commands(self, ctx: commands.Context):
        """Interactive UI for managing channel-specific command settings"""

        # Additional check: Allow server owner even without administrator permission
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(
                title="🚫 **Access Denied**",
                description="You need **Administrator** permission or be the **Server Owner** to manage channel commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Get current disabled commands for this channel
        disabled_commands = await channel_command_manager.get_disabled_commands(ctx.channel.id)
        
        embed = discord.Embed(
            title="🔧 **Channel Command Management**",
            description=f"Manage which commands are available in {ctx.channel.mention}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 **Current Status**",
            value=f"**Disabled Commands**: {len(disabled_commands)}\n**Enabled Commands**: {len(self.all_commands) - len(disabled_commands)}",
            inline=False
        )
        
        if disabled_commands:
            disabled_list = ", ".join(f"`{cmd}`" for cmd in sorted(disabled_commands))
            embed.add_field(
                name="🚫 **Currently Disabled**",
                value=disabled_list[:1024],  # Discord field limit
                inline=False
            )
        
        embed.add_field(
            name="ℹ️ **How to Use**",
            value=(
                "• Use the buttons below to manage commands\n"
                "• **Disable**: Prevent a command from working in this channel\n"
                "• **Enable**: Allow a disabled command to work again\n"
                "• **View All**: See complete list of all commands\n"
                "• **Requires**: Administrator permission or Server Owner"
            ),
            inline=False
        )
        
        view = ChannelCommandView(ctx, disabled_commands, self.command_categories, self.all_commands)

        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="disablecommand", help="Quickly disable a specific command in this channel")
    @commands.has_permissions(administrator=True)
    async def disable_command(self, ctx: commands.Context, command_name: str):
        """Quickly disable a specific command"""

        # Additional check: Allow server owner even without administrator permission
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(
                title="🚫 **Access Denied**",
                description="You need **Administrator** permission or be the **Server Owner** to disable commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if command_name not in self.all_commands:
            embed = discord.Embed(
                title="❌ **Invalid Command**",
                description=f"Command `{command_name}` not found.\n\nUse `sl channelcommands` to see all available commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        success = await channel_command_manager.disable_command(
            ctx.channel.id, 
            command_name, 
            ctx.author.id
        )
        
        if success:
            embed = discord.Embed(
                title="✅ **Command Disabled**",
                description=f"Command `{command_name}` has been disabled in {ctx.channel.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="⚠️ **Already Disabled**",
                description=f"Command `{command_name}` is already disabled in {ctx.channel.mention}",
                color=discord.Color.orange()
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="enablecommand", help="Quickly enable a specific command in this channel")
    @commands.has_permissions(administrator=True)
    async def enable_command(self, ctx: commands.Context, command_name: str):
        """Quickly enable a specific command"""

        # Additional check: Allow server owner even without administrator permission
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(
                title="🚫 **Access Denied**",
                description="You need **Administrator** permission or be the **Server Owner** to enable commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if command_name not in self.all_commands:
            embed = discord.Embed(
                title="❌ **Invalid Command**",
                description=f"Command `{command_name}` not found.\n\nUse `sl channelcommands` to see all available commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        success = await channel_command_manager.enable_command(ctx.channel.id, command_name)
        
        if success:
            embed = discord.Embed(
                title="✅ **Command Enabled**",
                description=f"Command `{command_name}` has been enabled in {ctx.channel.mention}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="⚠️ **Already Enabled**",
                description=f"Command `{command_name}` is already enabled in {ctx.channel.mention}",
                color=discord.Color.orange()
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="listcommands", help="List all available commands by category")
    @commands.has_permissions(administrator=True)
    async def list_commands(self, ctx: commands.Context):
        """List all available commands organized by category"""

        # Additional check: Allow server owner even without administrator permission
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(
                title="🚫 **Access Denied**",
                description="You need **Administrator** permission or be the **Server Owner** to list commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="📋 **All Available Commands**",
            description="Complete list of all bot commands organized by category",
            color=discord.Color.blue()
        )

        for category, commands_list in self.command_categories.items():
            command_text = ", ".join(f"`{cmd}`" for cmd in commands_list)
            embed.add_field(
                name=category,
                value=command_text,
                inline=False
            )

        embed.set_footer(text=f"Total Commands: {len(self.all_commands)} • Use 'sl channelcommands' to manage them")

        await ctx.send(embed=embed)

    @commands.command(name="fixessentialcommands", help="Re-enable essential commands that should never be disabled")
    @commands.has_permissions(administrator=True)
    async def fix_essential_commands(self, ctx: commands.Context):
        """Re-enable essential commands that should never be disabled"""

        # Additional check: Allow server owner even without administrator permission
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(
                title="🚫 **Access Denied**",
                description="You need **Administrator** permission or be the **Server Owner** to fix commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        essential_commands = ['help', 'start', 'profile', 'guild', 'fixuser', 'unstuck', 'ping']
        fixed_commands = []

        for command_name in essential_commands:
            success = await channel_command_manager.enable_command(ctx.channel.id, command_name)
            if success:
                fixed_commands.append(command_name)

        if fixed_commands:
            embed = discord.Embed(
                title="✅ **Essential Commands Fixed**",
                description=f"Re-enabled essential commands in {ctx.channel.mention}:\n" +
                           "\n".join(f"• `{cmd}`" for cmd in fixed_commands),
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ **No Changes Needed**",
                description="All essential commands are already enabled in this channel.",
                color=discord.Color.blue()
            )

        await ctx.send(embed=embed)

class ChannelCommandView(View):
    """Interactive view for managing channel commands"""
    
    def __init__(self, ctx, disabled_commands, command_categories, all_commands):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.disabled_commands = disabled_commands
        self.command_categories = command_categories
        self.all_commands = all_commands
    
    @discord.ui.button(label="🚫 Disable Commands", style=discord.ButtonStyle.danger)
    async def disable_commands_button(self, interaction: discord.Interaction, button: Button):
        """Show interface to disable commands"""
        
        # Create select menu with enabled commands
        enabled_commands = [cmd for cmd in self.all_commands if cmd not in self.disabled_commands]
        
        if not enabled_commands:
            await InteractionHandler.safe_response(
                interaction,
                content="❌ **All commands are already disabled in this channel!**",
                ephemeral=True
            )
            return
        
        # Create select options (max 25)
        options = []
        for cmd in sorted(enabled_commands)[:25]:
            options.append(discord.SelectOption(
                label=cmd,
                description=f"Disable the {cmd} command",
                value=cmd
            ))
        
        select = CommandSelect(
            placeholder="Select commands to disable...",
            options=options,
            action="disable",
            channel_id=self.ctx.channel.id,
            user_id=self.ctx.author.id
        )
        
        view = View()
        view.add_item(select)
        
        await InteractionHandler.safe_response(
            interaction,
            content="**Select commands to disable:**",
            view=view,
            ephemeral=True
        )
    
    @discord.ui.button(label="✅ Enable Commands", style=discord.ButtonStyle.success)
    async def enable_commands_button(self, interaction: discord.Interaction, button: Button):
        """Show interface to enable commands"""
        
        if not self.disabled_commands:
            await InteractionHandler.safe_response(
                interaction,
                content="❌ **No commands are disabled in this channel!**",
                ephemeral=True
            )
            return
        
        # Create select options (max 25)
        options = []
        for cmd in sorted(self.disabled_commands)[:25]:
            options.append(discord.SelectOption(
                label=cmd,
                description=f"Enable the {cmd} command",
                value=cmd
            ))
        
        select = CommandSelect(
            placeholder="Select commands to enable...",
            options=options,
            action="enable",
            channel_id=self.ctx.channel.id,
            user_id=self.ctx.author.id
        )
        
        view = View()
        view.add_item(select)
        
        await InteractionHandler.safe_response(
            interaction,
            content="**Select commands to enable:**",
            view=view,
            ephemeral=True
        )
    
    @discord.ui.button(label="📋 View All Commands", style=discord.ButtonStyle.secondary)
    async def view_all_button(self, interaction: discord.Interaction, button: Button):
        """Show all commands organized by category"""
        
        embed = discord.Embed(
            title="📋 **All Available Commands**",
            description=f"Commands for {self.ctx.channel.mention}",
            color=discord.Color.blue()
        )
        
        for category, commands_list in self.command_categories.items():
            status_commands = []
            for cmd in commands_list:
                if cmd in self.disabled_commands:
                    status_commands.append(f"🚫 `{cmd}`")
                else:
                    status_commands.append(f"✅ `{cmd}`")
            
            embed.add_field(
                name=category,
                value="\n".join(status_commands),
                inline=True
            )
        
        embed.set_footer(text="🚫 = Disabled | ✅ = Enabled")
        
        await InteractionHandler.safe_response(interaction, embed=embed, ephemeral=True)

class CommandSelect(Select):
    """Select menu for choosing commands to enable/disable"""
    
    def __init__(self, placeholder, options, action, channel_id, user_id):
        super().__init__(placeholder=placeholder, options=options, max_values=len(options))
        self.action = action
        self.channel_id = channel_id
        self.user_id = user_id
    
    async def callback(self, interaction: discord.Interaction):
        """Handle command selection"""
        
        if interaction.user.id != self.user_id:
            await InteractionHandler.safe_response(
                interaction,
                content="❌ **Only the command initiator can use this!**",
                ephemeral=True
            )
            return
        
        results = []
        
        for command_name in self.values:
            if self.action == "disable":
                success = await channel_command_manager.disable_command(
                    self.channel_id, command_name, self.user_id
                )
                if success:
                    results.append(f"✅ Disabled `{command_name}`")
                else:
                    results.append(f"⚠️ `{command_name}` was already disabled")
            
            elif self.action == "enable":
                success = await channel_command_manager.enable_command(
                    self.channel_id, command_name
                )
                if success:
                    results.append(f"✅ Enabled `{command_name}`")
                else:
                    results.append(f"⚠️ `{command_name}` was already enabled")
        
        embed = discord.Embed(
            title=f"🔧 **Commands {self.action.title()}d**",
            description="\n".join(results),
            color=discord.Color.green() if self.action == "enable" else discord.Color.red()
        )
        
        await InteractionHandler.safe_response(interaction, embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChannelCommandManagementCog(bot))
    
    # Initialize the database
    await channel_command_manager.initialize_database()
