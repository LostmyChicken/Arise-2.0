"""
Enhanced Guild UI System with Vice Masters and Advanced Management
"""
import discord
from discord.ext import commands
from discord import ui
from datetime import datetime, timedelta
from structure.enhanced_guild import EnhancedGuild, GuildRole, GuildPermission
from structure.player import Player
from utilis.utilis import extractId
from structure.emoji import getEmoji
import time
import logging
import asyncio

async def safe_send_error(interaction: discord.Interaction, message: str):
    """Safely send error message, using followup if interaction already responded"""
    try:
        await interaction.response.send_message(message, ephemeral=True)
    except discord.InteractionResponded:
        await interaction.followup.send(message, ephemeral=True)

class EnhancedGuildMainView(ui.View):
    """Main enhanced guild interface"""
    
    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.current_mode = "overview"
        self.current_page = 0
        self.guild = None
        self.sort_mode = "points"  # Default sort by points
        self.update_buttons()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True
    
    async def create_embed(self):
        """Create embed based on current mode"""
        if self.current_mode == "overview":
            return await self.create_overview_embed()
        elif self.current_mode == "browse":
            return await self.create_browse_embed()
        elif self.current_mode == "manage":
            return await self.create_manage_embed()
        elif self.current_mode == "members":
            return await self.create_members_embed()
        elif self.current_mode == "applications":
            return await self.create_applications_embed()
        elif self.current_mode == "bank":
            return await self.create_bank_embed()
        elif self.current_mode == "settings":
            return await self.create_settings_embed()
        elif self.current_mode == "info":
            return await self.create_info_embed()
        elif self.current_mode == "role_permissions":
            return await self.create_role_permissions_embed()
        else:
            return await self.create_overview_embed()
    
    async def create_overview_embed(self):
        """Create guild overview embed"""
        embed = discord.Embed(
            title="🏰 **ENHANCED GUILD SYSTEM** 🏰",
            description="Advanced guild management with roles, permissions, and features!",
            color=discord.Color.dark_purple()
        )
        
        # Load player's guild if they have one
        if self.player.guild:
            # Try enhanced guild first, then convert from old format if needed
            self.guild = await EnhancedGuild.get(self.player.guild)
            if not self.guild:
                # Try to convert from old guild format
                from structure.guild import Guild
                old_guild = await Guild.get(self.player.guild)
                if old_guild:
                    self.guild = await self.convert_old_guild(old_guild)

            if self.guild:
                tier, color = self.guild.get_guild_tier()
                embed.color = discord.Color(color)
                
                # Guild info
                role_counts = self.guild.get_member_count_by_role()
                total_members = sum(role_counts.values())
                
                embed.add_field(
                    name="🏛️ Your Guild",
                    value=(
                        f"**{self.guild.name}** ({tier})\n"
                        f"👥 Members: {total_members}/{self.guild.settings['max_members']}\n"
                        f"🏆 Points: {self.guild.points:,}\n"
                        f"🚪 Gates: {self.guild.gates}\n"
                        f"📊 Level: {self.guild.level}"
                    ),
                    inline=False
                )
                
                # Player's role
                player_role = self.guild.get_member_role(self.player.id)
                if player_role:
                    role_display = self.guild.get_role_display_name(player_role.value)
                    embed.add_field(
                        name="👤 Your Role",
                        value=f"{role_display}",
                        inline=True
                    )
                
                # Guild bank
                bank = self.guild.guild_bank
                gold_emoji = getEmoji('gold') if getEmoji('gold') != "❔" else "🪙"
                diamond_emoji = getEmoji('diamond') if getEmoji('diamond') != "❔" else "💎"
                crystals_emoji = getEmoji('crystals') if getEmoji('crystals') != "❔" else "💠"

                embed.add_field(
                    name="🏦 Guild Bank",
                    value=(
                        f"{gold_emoji} {bank.get('gold', 0):,}\n"
                        f"{diamond_emoji} {bank.get('diamond', 0):,}\n"
                        f"{crystals_emoji} {bank.get('crystals', 0):,}"
                    ),
                    inline=True
                )
                
                # Recent activity
                if self.guild.applications:
                    embed.add_field(
                        name="📝 Pending Applications",
                        value=f"{len(self.guild.applications)} waiting for review",
                        inline=True
                    )
        else:
            embed.add_field(
                name="🚫 No Guild",
                value="You're not currently in a guild. Browse available guilds or create your own!",
                inline=False
            )
        
        # Guild features
        embed.add_field(
            name="✨ Enhanced Features",
            value=(
                "• **Role System**: Guild Master, Vice Master, Officer, Member\n"
                "• **Permission System**: Granular role-based permissions\n"
                "• **Guild Bank**: Shared resources and contributions\n"
                "• **Application System**: Manage join requests\n"
                "• **Activity Tracking**: Monitor member engagement\n"
                "• **Advanced Settings**: Customize guild behavior"
            ),
            inline=False
        )
        
        embed.set_footer(text="Enhanced Guild System • Advanced management tools")
        return embed
    
    async def create_browse_embed(self):
        """Create enhanced guild browsing embed with sorting"""
        guilds = await self.get_all_guilds_unified()

        embed = discord.Embed(
            title="🔍 **BROWSE GUILDS**",
            description="Discover and join amazing guilds across the realm!",
            color=discord.Color.blue()
        )

        if not guilds:
            embed.add_field(
                name="📭 No Guilds Found",
                value="No guilds exist yet. Be the first to create one!",
                inline=False
            )
            return embed

        # Sort guilds based on current sort mode
        sort_mode = getattr(self, 'sort_mode', 'points')
        if sort_mode == "points":
            guilds.sort(key=lambda g: g.points, reverse=True)
        elif sort_mode == "members":
            guilds.sort(key=lambda g: len(g.members), reverse=True)
        elif sort_mode == "level":
            guilds.sort(key=lambda g: g.level, reverse=True)
        elif sort_mode == "name":
            guilds.sort(key=lambda g: g.name.lower())
        else:  # Default: points
            guilds.sort(key=lambda g: g.points, reverse=True)

        # Enhanced pagination - show more guilds per page
        per_page = 9  # Increased from 5 to 9 (3x3 grid)
        start_idx = self.current_page * per_page
        end_idx = start_idx + per_page
        page_guilds = guilds[start_idx:end_idx]

        # Add sorting info
        sort_names = {
            "points": "🏆 Guild Points",
            "members": "👥 Member Count",
            "level": "📊 Guild Level",
            "name": "📝 Alphabetical"
        }
        embed.add_field(
            name="📋 Current Sort",
            value=f"Sorted by: **{sort_names.get(sort_mode, 'Guild Points')}**",
            inline=False
        )

        # Display guilds in a more compact format
        for i, guild in enumerate(page_guilds):
            tier, tier_color = guild.get_guild_tier()
            member_count = len(guild.members) + 1  # +1 for owner

            # Check if accepting applications
            if member_count >= guild.settings.get("max_members", 50):
                status = "🚫 Full"
            elif guild.settings.get("application_required", True):
                status = "📝 Apply"
            else:
                status = "✅ Open"

            # More compact display with rank indicator
            rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏰"

            embed.add_field(
                name=f"{rank_emoji} {guild.name}",
                value=(
                    f"**{tier}** • Lv.{guild.level}\n"
                    f"👥 {member_count}/{guild.settings.get('max_members', 50)} • 🏆 {guild.points:,}\n"
                    f"{status}"
                ),
                inline=True
            )

        # Enhanced pagination info with sorting
        total_pages = (len(guilds) + per_page - 1) // per_page
        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages} • {len(guilds)} guilds • Sort: {sort_names.get(sort_mode, 'Points')}")

        # Add guild image if there are guilds on this page
        if page_guilds:
            # Show the image of the first guild on the page (top-ranked)
            top_guild = page_guilds[0]
            if top_guild.image and top_guild.image.strip():
                try:
                    # Validate if it's a proper URL
                    if top_guild.image.startswith(('http://', 'https://')):
                        embed.set_thumbnail(url=top_guild.image)
                        embed.add_field(
                            name="🖼️ Featured Guild",
                            value=f"Showing image for **{top_guild.name}** (Top {sort_names.get(sort_mode, 'Points')})",
                            inline=False
                        )
                except Exception as e:
                    print(f"Error setting guild image: {e}")

        return embed

    async def create_role_permissions_embed(self):
        """Create embed for role permissions management"""
        embed = discord.Embed(
            title=f"{getEmoji('info') or '⚙️'} Role Permissions",
            description=f"Configure permissions for **{self.guild.name}** roles",
            color=discord.Color.gold()
        )

        # Officer permissions
        officer_perms = self.guild.get_role_permissions(GuildRole.OFFICER)
        officer_perm_list = []

        if GuildPermission.INVITE_MEMBERS in officer_perms:
            officer_perm_list.append(f"{getEmoji('tick') or '✅'} Invite Members")
        else:
            officer_perm_list.append(f"{getEmoji('negative') or '❌'} Invite Members")

        if GuildPermission.KICK_MEMBERS in officer_perms:
            officer_perm_list.append(f"{getEmoji('tick') or '✅'} Kick Members")
        else:
            officer_perm_list.append(f"{getEmoji('negative') or '❌'} Kick Members")

        if GuildPermission.MANAGE_GUILD_BANK in officer_perms:
            officer_perm_list.append(f"{getEmoji('tick') or '✅'} Manage Bank")
        else:
            officer_perm_list.append(f"{getEmoji('negative') or '❌'} Manage Bank")

        embed.add_field(
            name=f"{getEmoji('d_') or '🛡️'} Officer Permissions",
            value="\n".join(officer_perm_list),
            inline=True
        )

        # Vice Master permissions
        vice_master_perms = self.guild.get_role_permissions(GuildRole.VICE_MASTER)
        vice_perm_list = []

        if GuildPermission.INVITE_MEMBERS in vice_master_perms:
            vice_perm_list.append(f"{getEmoji('tick') or '✅'} Invite Members")
        else:
            vice_perm_list.append(f"{getEmoji('negative') or '❌'} Invite Members")

        if GuildPermission.KICK_MEMBERS in vice_master_perms:
            vice_perm_list.append(f"{getEmoji('tick') or '✅'} Kick Members")
        else:
            vice_perm_list.append(f"{getEmoji('negative') or '❌'} Kick Members")

        if GuildPermission.PROMOTE_MEMBERS in vice_master_perms:
            vice_perm_list.append(f"{getEmoji('tick') or '✅'} Promote Members")
        else:
            vice_perm_list.append(f"{getEmoji('negative') or '❌'} Promote Members")

        if GuildPermission.MANAGE_GUILD_BANK in vice_master_perms:
            vice_perm_list.append(f"{getEmoji('tick') or '✅'} Manage Bank")
        else:
            vice_perm_list.append(f"{getEmoji('negative') or '❌'} Manage Bank")

        if GuildPermission.EDIT_GUILD_INFO in vice_master_perms:
            vice_perm_list.append(f"{getEmoji('tick') or '✅'} Manage Settings")
        else:
            vice_perm_list.append(f"{getEmoji('negative') or '❌'} Manage Settings")

        embed.add_field(
            name=f"{getEmoji('thumb') or '👑'} Vice Master Permissions",
            value="\n".join(vice_perm_list),
            inline=True
        )

        embed.add_field(
            name=f"{getEmoji('info') or 'ℹ️'} Note",
            value="Only the Guild Master can modify role permissions. Click the buttons below to configure permissions for each role.",
            inline=False
        )

        return embed

    async def get_all_guilds_unified(self):
        """Get all guilds from both old and new systems"""
        all_guilds = []

        # Get enhanced guilds (new system)
        try:
            enhanced_guilds = await EnhancedGuild.get_all()
            all_guilds.extend(enhanced_guilds)
        except Exception as e:
            print(f"Error getting enhanced guilds: {e}")

        # Get old guilds and convert them to enhanced guild format
        try:
            from structure.guild import Guild
            import aiosqlite
            import json

            # Get database path
            def get_database_path():
                try:
                    with open("db.json", "r") as f:
                        config = json.load(f)
                        return config.get("player", "data/player.db")
                except Exception as e:
                    return "data/player.db"

            DATABASE_PATH = get_database_path()

            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute("SELECT * FROM guilds") as cursor:
                    rows = await cursor.fetchall()
                    for row in rows:
                        # Skip if this guild already exists in enhanced guilds
                        guild_id = row[0]
                        if any(g.id == guild_id for g in all_guilds):
                            continue

                        # Convert old guild to enhanced guild format
                        old_guild = Guild(
                            id=row[0], name=row[1], owner=row[2],
                            members=json.loads(row[3]) if row[3] else [],
                            level=row[4], points=row[5], image=row[6],
                            description=row[7], gates=row[8] if len(row) > 8 else 0,
                            allow_alliances=bool(row[9]) if len(row) > 9 else False
                        )

                        # Create enhanced guild wrapper
                        enhanced_wrapper = EnhancedGuild(
                            id=old_guild.id,
                            name=old_guild.name,
                            owner=old_guild.owner,
                            members=old_guild.members,
                            level=old_guild.level,
                            points=old_guild.points,
                            image=old_guild.image,
                            description=old_guild.description,
                            gates=old_guild.gates,
                            allow_alliances=old_guild.allow_alliances
                        )
                        all_guilds.append(enhanced_wrapper)
        except Exception as e:
            print(f"Error getting old guilds: {e}")

        return all_guilds

    async def create_manage_embed(self):
        """Create guild management embed"""
        if not self.guild:
            return discord.Embed(
                title="❌ Error",
                description="You're not in a guild!",
                color=discord.Color.red()
            )
        
        embed = discord.Embed(
            title=f"⚙️ **MANAGE: {self.guild.name}**",
            description="Advanced guild management tools",
            color=discord.Color.green()
        )
        
        # Player's permissions
        player_role = self.guild.get_member_role(self.player.id)
        if not player_role:
            embed.add_field(
                name="❌ Access Denied",
                value="You don't have management permissions.",
                inline=False
            )
            return embed
        
        permissions = self.guild.get_role_permissions(player_role)
        
        # Management options based on permissions
        management_options = []
        
        if GuildPermission.MANAGE_APPLICATIONS in permissions:
            pending_apps = len(self.guild.applications)
            management_options.append(f"📝 **Applications** ({pending_apps} pending)")
        
        if GuildPermission.INVITE_MEMBERS in permissions or GuildPermission.KICK_MEMBERS in permissions:
            management_options.append("👥 **Member Management**")
        
        if GuildPermission.MANAGE_GUILD_BANK in permissions:
            management_options.append("🏦 **Guild Bank**")
        
        if GuildPermission.EDIT_GUILD_INFO in permissions:
            management_options.append("⚙️ **Guild Settings**")
        
        if management_options:
            embed.add_field(
                name="🛠️ Available Tools",
                value="\n".join(management_options),
                inline=False
            )
        
        # Guild statistics
        role_counts = self.guild.get_member_count_by_role()
        embed.add_field(
            name="📊 Guild Statistics",
            value=(
                f"🏆 Guild Master: {role_counts['guild_master']}\n"
                f"👑 Vice Masters: {role_counts['vice_master']}\n"
                f"⭐ Officers: {role_counts['officer']}\n"
                f"👤 Members: {role_counts['member']}"
            ),
            inline=True
        )
        
        # Recent activity
        inactive_members = self.guild.get_inactive_members(7)
        embed.add_field(
            name="📈 Activity",
            value=(
                f"💤 Inactive (7d): {len(inactive_members)}\n"
                f"📝 Applications: {len(self.guild.applications)}\n"
                f"🏦 Bank Total: {sum(self.guild.guild_bank.values()):,}"
            ),
            inline=True
        )
        
        embed.set_footer(text=f"Your Role: {self.guild.get_role_display_name(player_role.value)}")
        return embed

    async def create_members_embed(self):
        """Create guild members embed with activity tracking"""
        if not self.guild:
            return discord.Embed(
                title="❌ Error",
                description="You're not in a guild!",
                color=discord.Color.red()
            )

        embed = discord.Embed(
            title=f"👥 **MEMBERS: {self.guild.name}**",
            description="Guild member management with activity tracking",
            color=discord.Color.blue()
        )

        from datetime import datetime, timedelta
        now = datetime.now()
        inactive_threshold = timedelta(days=7)  # 7 days inactive

        # Helper function to get activity status
        def get_activity_status(member_data):
            if member_data.get("is_owner", False):
                return getEmoji("rightee") or "👑", True  # Guild Master always active

            last_active = member_data.get("last_active")
            if not last_active:
                return getEmoji("negative") or "❌", False  # No activity data = inactive

            try:
                last_active_dt = datetime.fromisoformat(last_active)
                is_active = (now - last_active_dt) <= inactive_threshold
                emoji = getEmoji("tick") or "✅" if is_active else getEmoji("negative") or "❌"
                return emoji, is_active
            except:
                return getEmoji("negative") or "❌", False

        # Guild Master
        try:
            guild_master = await self.ctx.bot.fetch_user(self.guild.owner)
            activity_emoji, _ = get_activity_status({"is_owner": True})
            embed.add_field(
                name=f"{getEmoji('rightee') or '🏆'} Guild Master",
                value=f"{activity_emoji} {guild_master.mention} ({guild_master.display_name})",
                inline=False
            )
        except:
            activity_emoji, _ = get_activity_status({"is_owner": True})
            embed.add_field(
                name=f"{getEmoji('rightee') or '🏆'} Guild Master",
                value=f"{activity_emoji} <@{self.guild.owner}>",
                inline=False
            )

        # Categorize members by role and activity
        vice_masters = []
        officers = []
        regular_members = []
        inactive_members = []

        for member in self.guild.members:
            role = member.get("role", "member")
            activity_emoji, is_active = get_activity_status(member)

            try:
                user = await self.ctx.bot.fetch_user(member["id"])
                display_name = user.display_name
                mention = user.mention
            except:
                display_name = f"User {member['id']}"
                mention = f"<@{member['id']}>"

            contribution = member.get("contribution", 0)
            contrib_text = f" ({contribution:,} pts)" if contribution > 0 else ""
            member_text = f"{activity_emoji} {mention} ({display_name}){contrib_text}"

            if role == "vice_master":
                vice_masters.append(member_text)
            elif role == "officer":
                officers.append(member_text)
            else:
                if is_active:
                    regular_members.append(member_text)
                else:
                    inactive_members.append(member_text)

        # Display Vice Masters
        if vice_masters:
            embed.add_field(
                name=f"{getEmoji('thumb') or '👑'} Vice Masters ({len(vice_masters)})",
                value="\n".join(vice_masters[:5]),
                inline=False
            )

        # Display Officers
        if officers:
            embed.add_field(
                name=f"{getEmoji('info') or '⭐'} Officers ({len(officers)})",
                value="\n".join(officers[:5]),
                inline=False
            )

        # Display Active Members
        if regular_members:
            display_members = regular_members[:8]
            if len(regular_members) > 8:
                display_members.append(f"... and {len(regular_members) - 8} more active members")

            embed.add_field(
                name=f"{getEmoji('tick') or '✅'} Active Members ({len(regular_members)})",
                value="\n".join(display_members),
                inline=False
            )

        # Display Inactive Members
        if inactive_members:
            display_inactive = inactive_members[:5]
            if len(inactive_members) > 5:
                display_inactive.append(f"... and {len(inactive_members) - 5} more inactive")

            embed.add_field(
                name=f"{getEmoji('negative') or '❌'} Inactive Members ({len(inactive_members)}) - 7+ days",
                value="\n".join(display_inactive),
                inline=False
            )

        # Member statistics with proper emojis
        total_members = len(self.guild.members) + 1  # +1 for owner
        active_count = len(vice_masters) + len(officers) + len(regular_members) + 1  # +1 for guild master

        embed.add_field(
            name=f"{getEmoji('info') or '📊'} Statistics",
            value=(
                f"**Total Members**: {total_members}/{self.guild.settings.get('max_members', 50)}\n"
                f"**Active Members**: {active_count}\n"
                f"**Inactive Members**: {len(inactive_members)}\n"
                f"**Activity Rate**: {(active_count/total_members*100):.1f}%"
            ),
            inline=False
        )

        return embed

    async def create_applications_embed(self):
        """Create guild applications embed"""
        if not self.guild:
            return discord.Embed(
                title="❌ Error",
                description="You're not in a guild!",
                color=discord.Color.red()
            )

        embed = discord.Embed(
            title=f"📝 **APPLICATIONS: {self.guild.name}**",
            description="Manage guild join requests",
            color=discord.Color.orange()
        )

        if not self.guild.applications:
            embed.add_field(
                name="📭 No Applications",
                value="No pending applications at this time.",
                inline=False
            )
        else:
            for i, app in enumerate(self.guild.applications[:5], 1):  # Show up to 5
                try:
                    user = await self.ctx.bot.fetch_user(app["user_id"])
                    user_name = f"{user.mention} ({user.display_name})"
                except:
                    user_name = f"<@{app['user_id']}>"

                embed.add_field(
                    name=f"📋 Application #{i}",
                    value=(
                        f"**User**: {user_name}\n"
                        f"**Message**: {app.get('message', 'No message provided')[:100]}...\n"
                        f"**Applied**: {app.get('applied_at', 'Unknown')[:10]}"
                    ),
                    inline=False
                )

            if len(self.guild.applications) > 5:
                embed.add_field(
                    name="📊 More Applications",
                    value=f"... and {len(self.guild.applications) - 5} more applications",
                    inline=False
                )

        # Application settings
        embed.add_field(
            name="⚙️ Settings",
            value=(
                f"**Auto-Accept**: {'✅ Enabled' if self.guild.settings.get('auto_accept_applications', False) else '❌ Disabled'}\n"
                f"**Min Level**: {self.guild.settings.get('min_level_requirement', 1)}\n"
                f"**Applications Required**: {'✅ Yes' if self.guild.settings.get('application_required', True) else '❌ No'}"
            ),
            inline=False
        )

        return embed

    async def create_bank_embed(self):
        """Create guild bank embed"""
        if not self.guild:
            return discord.Embed(
                title="❌ Error",
                description="You're not in a guild!",
                color=discord.Color.red()
            )

        embed = discord.Embed(
            title=f"🏦 **BANK: {self.guild.name}**",
            description="Guild shared resources",
            color=discord.Color.gold()
        )

        bank = self.guild.guild_bank

        # Use proper emojis from the emoji system
        gold_emoji = getEmoji('gold') or "🪙"
        diamond_emoji = getEmoji('diamond') or "💎"
        stone_emoji = getEmoji('stone') or "🪨"
        wallet_emoji = getEmoji('wallet') or "💰"

        embed.add_field(
            name=f"{wallet_emoji} Available Funds",
            value=(
                f"{gold_emoji} **Gold**: {bank.get('gold', 0):,}\n"
                f"{diamond_emoji} **Diamond**: {bank.get('diamond', 0):,}\n"
                f"{stone_emoji} **Stones**: {bank.get('stones', 0):,}"
            ),
            inline=False
        )

        # Calculate total value (using same conversion rates as rest of bot)
        total_value = bank.get('gold', 0) + (bank.get('diamond', 0) * 100) + (bank.get('stones', 0) * 10)
        embed.add_field(
            name="📊 Total Value",
            value=f"{total_value:,} gold equivalent",
            inline=True
        )

        # Recent contributions (if we had tracking)
        embed.add_field(
            name="📈 Bank Usage",
            value=(
                "Use `/sl guild bank deposit` to contribute\n"
                "Use `/sl guild bank withdraw` to withdraw (Vice Master+)"
            ),
            inline=False
        )

        # Player's permissions
        player_role = self.guild.get_member_role(self.player.id)
        if player_role:
            from structure.enhanced_guild import GuildPermission
            can_withdraw = self.guild.has_permission(self.player.id, GuildPermission.MANAGE_GUILD_BANK)
            embed.add_field(
                name="🔐 Your Permissions",
                value=(
                    f"**Deposit**: ✅ Allowed\n"
                    f"**Withdraw**: {'✅ Allowed' if can_withdraw else '❌ Not Allowed'}"
                ),
                inline=True
            )

        return embed

    async def create_settings_embed(self):
        """Create guild settings embed"""
        if not self.guild:
            return discord.Embed(
                title="❌ Error",
                description="You're not in a guild!",
                color=discord.Color.red()
            )

        embed = discord.Embed(
            title=f"⚙️ **SETTINGS: {self.guild.name}**",
            description="Guild configuration and preferences",
            color=discord.Color.purple()
        )

        # Basic settings
        settings = self.guild.settings
        embed.add_field(
            name="🔧 Basic Settings",
            value=(
                f"**Max Members**: {settings.get('max_members', 50)}\n"
                f"**Min Level Requirement**: {settings.get('min_level_requirement', 1)}\n"
                f"**Public Visibility**: {'✅ Public' if settings.get('public_visibility', True) else '❌ Private'}"
            ),
            inline=False
        )

        # Application settings
        embed.add_field(
            name="📝 Application Settings",
            value=(
                f"**Applications Required**: {'✅ Yes' if settings.get('application_required', True) else '❌ No'}\n"
                f"**Auto-Accept**: {'✅ Enabled' if settings.get('auto_accept_applications', False) else '❌ Disabled'}"
            ),
            inline=False
        )

        # Guild features
        embed.add_field(
            name="✨ Guild Features",
            value=(
                f"**Allow Alliances**: {'✅ Enabled' if self.guild.allow_alliances else '❌ Disabled'}\n"
                f"**Guild Bank**: ✅ Active\n"
                f"**Role System**: ✅ Active"
            ),
            inline=False
        )

        # Player's permissions
        player_role = self.guild.get_member_role(self.player.id)
        if player_role:
            from structure.enhanced_guild import GuildPermission
            can_edit = self.guild.has_permission(self.player.id, GuildPermission.EDIT_GUILD_INFO)
            embed.add_field(
                name="🔐 Your Permissions",
                value=f"**Edit Settings**: {'✅ Allowed' if can_edit else '❌ Not Allowed'}",
                inline=True
            )

        return embed

    async def create_info_embed(self):
        """Create guild info embed (like the old system)"""
        if not self.guild:
            return discord.Embed(
                title="❌ Error",
                description="You're not in a guild!",
                color=discord.Color.red()
            )

        tier, color = self.guild.get_guild_tier()
        embed = discord.Embed(
            title=f"🏰 **{self.guild.name}**",
            description=self.guild.description or "No description set",
            color=discord.Color(color)
        )

        # Set guild image if available and valid
        if self.guild.image and self.guild.image.strip():
            try:
                # Validate if it's a proper URL
                if self.guild.image.startswith(('http://', 'https://')):
                    embed.set_thumbnail(url=self.guild.image)
            except Exception:
                # Skip invalid thumbnail URLs
                pass

        # Basic guild info
        total_members = len(self.guild.members) + 1  # +1 for owner
        embed.add_field(
            name="📊 Guild Statistics",
            value=(
                f"**Tier**: {tier}\n"
                f"**Level**: {self.guild.level}\n"
                f"**Points**: {self.guild.points:,}\n"
                f"**Gates Cleared**: {self.guild.gates}\n"
                f"**Members**: {total_members}/{self.guild.settings.get('max_members', 50)}"
            ),
            inline=True
        )

        # Guild Master info
        try:
            guild_master = await self.ctx.bot.fetch_user(self.guild.owner)
            embed.add_field(
                name="🏆 Guild Master",
                value=f"{guild_master.mention}\n({guild_master.display_name})",
                inline=True
            )
        except:
            embed.add_field(
                name="🏆 Guild Master",
                value=f"<@{self.guild.owner}>",
                inline=True
            )

        # Guild bank summary
        bank = self.guild.guild_bank
        total_value = bank.get('gold', 0) + (bank.get('diamond', 0) * 100) + (bank.get('stones', 0) * 10)
        gold_emoji = getEmoji('gold') if getEmoji('gold') != "❔" else "🪙"
        diamond_emoji = getEmoji('diamond') if getEmoji('diamond') != "❔" else "💎"
        stone_emoji = getEmoji('stone') if getEmoji('stone') != "❔" else "🪨"

        embed.add_field(
            name="🏦 Guild Bank",
            value=(
                f"{gold_emoji} {bank.get('gold', 0):,}\n"
                f"{diamond_emoji} {bank.get('diamond', 0):,}\n"
                f"{stone_emoji} {bank.get('stones', 0):,}\n"
                f"**Total**: {total_value:,} gold equiv."
            ),
            inline=True
        )

        # Role breakdown
        role_counts = self.guild.get_member_count_by_role()
        embed.add_field(
            name="👥 Member Roles",
            value=(
                f"🏆 Guild Master: {role_counts['guild_master']}\n"
                f"👑 Vice Masters: {role_counts['vice_master']}\n"
                f"⭐ Officers: {role_counts['officer']}\n"
                f"👤 Members: {role_counts['member']}"
            ),
            inline=True
        )

        # Guild settings
        embed.add_field(
            name="⚙️ Guild Settings",
            value=(
                f"**Applications**: {'✅ Open' if self.guild.settings.get('application_required', True) else '❌ Closed'}\n"
                f"**Min Level**: {self.guild.settings.get('min_level_requirement', 1)}\n"
                f"**Alliances**: {'✅ Allowed' if self.guild.allow_alliances else '❌ Disabled'}"
            ),
            inline=True
        )

        # Activity info
        if self.guild.applications:
            embed.add_field(
                name="📝 Recent Activity",
                value=f"{len(self.guild.applications)} pending applications",
                inline=True
            )

        embed.set_footer(text=f"Created: {self.guild.created_at[:10]} • Enhanced Guild System")
        return embed
    
    def update_buttons(self):
        """Update buttons based on current mode"""
        self.clear_items()
        
        if self.current_mode == "overview":
            self.add_item(BrowseGuildsButton())
            if not self.player.guild:
                self.add_item(CreateGuildButton())
            else:
                self.add_item(GuildInfoButton())
                self.add_item(ManageGuildButton())
                self.add_item(LeaveGuildButton())
        
        elif self.current_mode == "browse":
            # Sorting buttons (row 0)
            self.add_item(SortByPointsButton())
            self.add_item(SortByMembersButton())
            self.add_item(SortByLevelButton())
            self.add_item(SortByNameButton())

            # Navigation buttons (row 1)
            if self.current_page > 0:
                self.add_item(PreviousPageButton())
            self.add_item(NextPageButton())
            self.add_item(ViewGuildDetailsButton())
            self.add_item(JoinGuildButton())
            self.add_item(BackToOverviewButton())
        
        elif self.current_mode == "manage":
            if self.guild:
                player_role = self.guild.get_member_role(self.player.id)
                if player_role:
                    permissions = self.guild.get_role_permissions(player_role)

                    if GuildPermission.MANAGE_APPLICATIONS in permissions:
                        self.add_item(ApplicationsButton())

                    if GuildPermission.INVITE_MEMBERS in permissions or GuildPermission.KICK_MEMBERS in permissions:
                        self.add_item(MembersButton())

                    if GuildPermission.MANAGE_GUILD_BANK in permissions:
                        self.add_item(BankButton())

                    if GuildPermission.EDIT_GUILD_INFO in permissions:
                        self.add_item(SettingsButton())

            self.add_item(BackToOverviewButton())

        elif self.current_mode == "info":
            self.add_item(BackToOverviewButton())

        elif self.current_mode == "applications":
            self.add_item(BackToManageButton())

        elif self.current_mode == "members":
            # Add member management buttons if user has permissions
            if self.guild:
                player_role = self.guild.get_member_role(self.player.id)
                if player_role:
                    permissions = self.guild.get_role_permissions(player_role)

                    if GuildPermission.INVITE_MEMBERS in permissions:
                        self.add_item(InviteMemberButton())

                    if GuildPermission.KICK_MEMBERS in permissions:
                        self.add_item(KickMemberButton())

                    if GuildPermission.PROMOTE_MEMBERS in permissions:
                        self.add_item(PromoteMemberButton())

                    if GuildPermission.DEMOTE_MEMBERS in permissions:
                        self.add_item(DemoteMemberButton())

            self.add_item(BackToManageButton())

        elif self.current_mode == "bank":
            # Add bank management buttons
            if self.guild:
                player_role = self.guild.get_member_role(self.player.id)
                if player_role:
                    permissions = self.guild.get_role_permissions(player_role)

                    if GuildPermission.MANAGE_GUILD_BANK in permissions:
                        self.add_item(DepositBankButton())
                        self.add_item(WithdrawBankButton())

            self.add_item(BackToManageButton())

        elif self.current_mode == "settings":
            # Add setting management buttons
            self.add_item(MaxMembersButton())
            self.add_item(MinLevelButton())
            self.add_item(PublicVisibilityButton())
            self.add_item(ApplicationRequiredButton())
            self.add_item(AutoAcceptButton())
            self.add_item(AlliancesButton())

            # Add role permissions button for guild master only
            if self.guild and self.player.id == self.guild.owner:
                self.add_item(RolePermissionsButton())
                self.add_item(TransferOwnershipButton())
                self.add_item(DisbandGuildButton())

            self.add_item(BackToManageButton())

        elif self.current_mode == "role_permissions":
            # Role permission management
            self.add_item(OfficerPermissionsButton())
            self.add_item(ViceMasterPermissionsButton())
            self.add_item(BackToSettingsButton())
    
    async def convert_old_guild(self, old_guild):
        """Convert old guild to enhanced guild format"""
        from datetime import datetime

        # Convert old member format to new format
        enhanced_members = []
        if hasattr(old_guild, 'members') and old_guild.members:
            for member_data in old_guild.members:
                if isinstance(member_data, dict):
                    member_id = member_data.get("id") or member_data.get("user_id")
                    if member_id:
                        enhanced_members.append({
                            "id": int(member_id),
                            "role": "member",
                            "joined_at": member_data.get("joined_at", datetime.now().isoformat()),
                            "contribution": member_data.get("gc", member_data.get("contribution", 0)),
                            "last_active": member_data.get("last_active", datetime.now().isoformat())
                        })
                elif isinstance(member_data, (int, str)):
                    enhanced_members.append({
                        "id": int(member_data),
                        "role": "member",
                        "joined_at": datetime.now().isoformat(),
                        "contribution": 0,
                        "last_active": datetime.now().isoformat()
                    })

        # Create enhanced guild
        enhanced_guild = EnhancedGuild(
            id=old_guild.id,
            name=old_guild.name,
            owner=old_guild.owner,
            members=enhanced_members,
            level=getattr(old_guild, 'level', 1),
            points=getattr(old_guild, 'points', 0),
            image=getattr(old_guild, 'image', ''),
            description=getattr(old_guild, 'description', ''),
            gates=getattr(old_guild, 'gates', 0),
            allow_alliances=getattr(old_guild, 'allow_alliances', False)
        )

        await enhanced_guild.save()
        return enhanced_guild

    async def update_view(self, interaction: discord.Interaction):
        """Update the view with new embed and buttons"""
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def update_view_after_modal(self, interaction: discord.Interaction):
        """Update the view after a modal submission (interaction already responded)"""
        self.update_buttons()
        embed = await self.create_embed()
        # Use followup since modal already responded
        await interaction.edit_original_response(embed=embed, view=self)


# Button classes
class BrowseGuildsButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔍 Browse Guilds", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "browse"
        self.view.current_page = 0
        await self.view.update_view(interaction)


class CreateGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="🏗️ Create Guild", style=discord.ButtonStyle.success)
    
    async def callback(self, interaction: discord.Interaction):
        modal = CreateGuildModal()
        await interaction.response.send_modal(modal)


class GuildInfoButton(ui.Button):
    def __init__(self):
        super().__init__(label="ℹ️ Guild Info", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "info"
        await self.view.update_view(interaction)


class ManageGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="⚙️ Manage Guild", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "manage"
        await self.view.update_view(interaction)


class LeaveGuildConfirmModal(ui.Modal):
    """Modal for confirming guild leave"""

    def __init__(self, view):
        super().__init__(title="Confirm Leave Guild")
        self.view = view

        self.confirmation = ui.TextInput(
            label="Type 'LEAVE' to confirm",
            placeholder="Type LEAVE to confirm leaving the guild",
            required=True,
            max_length=10
        )
        self.add_item(self.confirmation)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.upper() != "LEAVE":
            await interaction.response.send_message(
                "❌ Confirmation failed. You must type 'LEAVE' exactly.",
                ephemeral=True
            )
            return

        try:
            from structure.guild import Guild

            # Get player's guild
            player = await Player.get(str(interaction.user.id))
            if not player or not player.guild:
                await interaction.response.send_message(
                    "❌ You are not in a guild.",
                    ephemeral=True
                )
                return

            guild = await Guild.get(player.guild)
            if not guild:
                await interaction.response.send_message(
                    "❌ Guild not found.",
                    ephemeral=True
                )
                return

            # Remove player from guild
            if str(interaction.user.id) in guild.members:
                guild.members.remove(str(interaction.user.id))

            # If player was leader, handle leadership transfer or guild deletion
            if guild.leader == str(interaction.user.id):
                if len(guild.members) > 0:
                    # Transfer leadership to first member
                    guild.leader = guild.members[0]
                else:
                    # Delete empty guild
                    await guild.delete()
                    embed = discord.Embed(
                        title="🏰 Guild Disbanded",
                        description="You were the last member, so the guild has been disbanded.",
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=embed)
                    return

            await guild.save()

            # Clear player's guild
            player.guild = None
            await player.save()

            embed = discord.Embed(
                title="🚪 Left Guild",
                description=f"You have successfully left **{guild.name}**.",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logging.error(f"Error leaving guild: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while leaving the guild.",
                ephemeral=True
            )


class LeaveGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Leave Guild", style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction):
        # Create confirmation modal
        modal = LeaveGuildConfirmModal(self.view)
        await interaction.response.send_modal(modal)


class BackToOverviewButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "overview"
        await self.view.update_view(interaction)


# Guild Sorting Buttons
class SortByPointsButton(ui.Button):
    def __init__(self):
        super().__init__(label="🏆 Points", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.sort_mode = "points"
        self.view.current_page = 0  # Reset to first page
        await self.view.update_view(interaction)


class SortByMembersButton(ui.Button):
    def __init__(self):
        super().__init__(label="👥 Members", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.sort_mode = "members"
        self.view.current_page = 0  # Reset to first page
        await self.view.update_view(interaction)


class SortByLevelButton(ui.Button):
    def __init__(self):
        super().__init__(label="📊 Level", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.sort_mode = "level"
        self.view.current_page = 0  # Reset to first page
        await self.view.update_view(interaction)


class SortByNameButton(ui.Button):
    def __init__(self):
        super().__init__(label="📝 Name", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.view.sort_mode = "name"
        self.view.current_page = 0  # Reset to first page
        await self.view.update_view(interaction)


# Role Permission Management Buttons
class RolePermissionsButton(ui.Button):
    def __init__(self):
        super().__init__(label=f"{getEmoji('info') or '⚙️'} Role Permissions", style=discord.ButtonStyle.primary, row=2)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "role_permissions"
        await self.view.update_view(interaction)


class OfficerPermissionsButton(ui.Button):
    def __init__(self):
        super().__init__(label=f"{getEmoji('d_') or '🛡️'} Officer Perms", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        # Create officer permission selection view
        view = RolePermissionSelectionView(self.view, GuildRole.OFFICER, "Officer")
        embed = await view.create_permission_selection_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class ViceMasterPermissionsButton(ui.Button):
    def __init__(self):
        super().__init__(label=f"{getEmoji('thumb') or '👑'} Vice Master Perms", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        # Create vice master permission selection view
        view = RolePermissionSelectionView(self.view, GuildRole.VICE_MASTER, "Vice Master")
        embed = await view.create_permission_selection_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class BackToSettingsButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Settings", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "settings"
        await self.view.update_view(interaction)


class ViewGuildDetailsButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔍 View Details", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        # Create guild selection view
        view = GuildDetailsSelectionView(self.view)
        embed = await view.create_guild_selection_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class BackToManageButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Manage", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "manage"
        await self.view.update_view(interaction)


class PreviousPageButton(ui.Button):
    def __init__(self):
        super().__init__(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page = max(0, self.view.current_page - 1)
        await self.view.update_view(interaction)


class NextPageButton(ui.Button):
    def __init__(self):
        super().__init__(label="Next ▶️", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page += 1
        await self.view.update_view(interaction)


class JoinGuildModal(ui.Modal):
    def __init__(self, view, guild_name=None):
        super().__init__(title="📝 Guild Application")
        self.view = view
        self.guild_name = guild_name

        self.reason = ui.TextInput(
            label="Why do you want to join this guild?",
            placeholder="Tell us why you'd like to join...",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        from structure.player import Player
        from structure.guild import Guild

        try:
            # Get player data
            player = await Player.get(interaction.user.id)
            if not player:
                await interaction.response.send_message("❌ **Player not found!** Please use `sl start` first.", ephemeral=True)
                return

            # Check if player is already in a guild
            if player.guild:
                await interaction.response.send_message("❌ **You're already in a guild!** Leave your current guild first.", ephemeral=True)
                return

            # Get guild data
            guild_name = self.guild_name or getattr(self.view, 'guild_name', None)
            if not guild_name:
                await interaction.response.send_message("❌ **Guild information not available!**", ephemeral=True)
                return

            guild = await Guild.get(guild_name)
            if not guild:
                await interaction.response.send_message("❌ **Guild not found!**", ephemeral=True)
                return

            # Check if guild is full
            if len(guild.members) >= guild.max_members:
                await interaction.response.send_message("❌ **Guild is full!** Cannot accept more members.", ephemeral=True)
                return

            # Check if player already has pending application
            if interaction.user.id in guild.applications:
                await interaction.response.send_message("⚠️ **You already have a pending application!**", ephemeral=True)
                return

            # Add application
            guild.applications[interaction.user.id] = {
                'name': interaction.user.display_name,
                'reason': self.reason.value,
                'timestamp': time.time()
            }
            await guild.save()

            await interaction.response.send_message(
                f"✅ **Application submitted!**\n"
                f"Your application to join **{guild.name}** has been sent to the guild leaders.\n"
                f"You'll be notified when they respond.",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Error in guild application: {e}")
            await interaction.response.send_message("❌ **Error submitting application!** Please try again.", ephemeral=True)


class JoinGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="📝 Apply to Guild", style=discord.ButtonStyle.success, row=1)

    async def callback(self, interaction: discord.Interaction):
        modal = JoinGuildModal(self.view)
        await interaction.response.send_modal(modal)


class ApplicationsButton(ui.Button):
    def __init__(self):
        super().__init__(label="📝 Applications", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "applications"
        await self.view.update_view(interaction)


class MembersButton(ui.Button):
    def __init__(self):
        super().__init__(label="👥 Members", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "members"
        await self.view.update_view(interaction)


class BankButton(ui.Button):
    def __init__(self):
        super().__init__(label="🏦 Bank", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "bank"
        await self.view.update_view(interaction)


class SettingsButton(ui.Button):
    def __init__(self):
        super().__init__(label="⚙️ Settings", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "settings"
        await self.view.update_view(interaction)


# Settings Management Buttons
class MaxMembersButton(ui.Button):
    def __init__(self):
        super().__init__(label="👥 Max Members", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        modal = MaxMembersModal(self.view)
        await interaction.response.send_modal(modal)


class MinLevelButton(ui.Button):
    def __init__(self):
        super().__init__(label="📊 Min Level", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        modal = MinLevelModal(self.view)
        await interaction.response.send_modal(modal)


class PublicVisibilityButton(ui.Button):
    def __init__(self):
        super().__init__(label="👁️ Visibility", style=discord.ButtonStyle.secondary, row=0)

    async def callback(self, interaction: discord.Interaction):
        # Toggle public visibility
        current = self.view.guild.settings.get('public_visibility', True)
        self.view.guild.settings['public_visibility'] = not current
        await self.view.guild.save()
        await self.view.update_view(interaction)


class ApplicationRequiredButton(ui.Button):
    def __init__(self):
        super().__init__(label="📝 Applications", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        # Toggle application requirement
        current = self.view.guild.settings.get('application_required', True)
        self.view.guild.settings['application_required'] = not current
        await self.view.guild.save()
        await self.view.update_view(interaction)


class AutoAcceptButton(ui.Button):
    def __init__(self):
        super().__init__(label="🤖 Auto-Accept", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        # Toggle auto-accept applications
        current = self.view.guild.settings.get('auto_accept_applications', False)
        self.view.guild.settings['auto_accept_applications'] = not current
        await self.view.guild.save()
        await self.view.update_view(interaction)


class AlliancesButton(ui.Button):
    def __init__(self):
        super().__init__(label="🤝 Alliances", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        # Toggle alliance system
        self.view.guild.allow_alliances = not self.view.guild.allow_alliances
        await self.view.guild.save()
        await self.view.update_view(interaction)


# Member Management Buttons with Dropdowns
class InviteMemberButton(ui.Button):
    def __init__(self):
        super().__init__(label="📨 Invite Member", style=discord.ButtonStyle.success, row=0)

    async def callback(self, interaction: discord.Interaction):
        modal = InviteMemberModal(self.view)
        await interaction.response.send_modal(modal)


class KickMemberButton(ui.Button):
    def __init__(self):
        super().__init__(label="👢 Kick Member", style=discord.ButtonStyle.danger, row=0)

    async def callback(self, interaction: discord.Interaction):
        # Create member selection view
        view = MemberSelectionView(self.view, "kick")
        embed = await view.create_member_selection_embed("kick")
        await interaction.response.edit_message(embed=embed, view=view)


class PromoteMemberButton(ui.Button):
    def __init__(self):
        super().__init__(label="⬆️ Promote", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        # Create member selection view
        view = MemberSelectionView(self.view, "promote")
        embed = await view.create_member_selection_embed("promote")
        await interaction.response.edit_message(embed=embed, view=view)


class DemoteMemberButton(ui.Button):
    def __init__(self):
        super().__init__(label="⬇️ Demote", style=discord.ButtonStyle.secondary, row=1)

    async def callback(self, interaction: discord.Interaction):
        # Create member selection view
        view = MemberSelectionView(self.view, "demote")
        embed = await view.create_member_selection_embed("demote")
        await interaction.response.edit_message(embed=embed, view=view)


# Bank Management Buttons
class DepositBankButton(ui.Button):
    def __init__(self):
        super().__init__(label="💰 Deposit", style=discord.ButtonStyle.success, row=0)

    async def callback(self, interaction: discord.Interaction):
        modal = DepositBankModal(self.view)
        await interaction.response.send_modal(modal)


class WithdrawBankButton(ui.Button):
    def __init__(self):
        super().__init__(label="💸 Withdraw", style=discord.ButtonStyle.danger, row=0)

    async def callback(self, interaction: discord.Interaction):
        modal = WithdrawBankModal(self.view)
        await interaction.response.send_modal(modal)


# Additional Guild Management Buttons
class TransferOwnershipButton(ui.Button):
    def __init__(self):
        super().__init__(label="👑 Transfer Ownership", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction):
        # Only guild master can transfer ownership
        if interaction.user.id != self.view.guild.owner:
            await interaction.response.send_message("❌ Only the Guild Master can transfer ownership!", ephemeral=True)
            return

        # Create member selection view for ownership transfer
        view = MemberSelectionView(self.view, "transfer_ownership")
        embed = await view.create_member_selection_embed("transfer_ownership")
        await interaction.response.edit_message(embed=embed, view=view)


class DisbandGuildButton(ui.Button):
    def __init__(self):
        super().__init__(label="💥 Disband Guild", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction):
        # Only guild master can disband
        if interaction.user.id != self.view.guild.owner:
            await interaction.response.send_message("❌ Only the Guild Master can disband the guild!", ephemeral=True)
            return

        # Confirmation view
        view = DisbandConfirmationView(self.view)
        embed = discord.Embed(
            title="⚠️ Disband Guild Confirmation",
            description=f"Are you sure you want to disband **{self.view.guild.name}**?\n\n**This action cannot be undone!**\n\nAll members will be removed and the guild will be permanently deleted.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=view)


# Modal classes
class CreateGuildModal(ui.Modal):
    def __init__(self):
        super().__init__(title="🏗️ Create New Guild")

        self.guild_name = ui.TextInput(
            label="Guild Name",
            placeholder="Enter your guild name...",
            required=True,
            max_length=50
        )

        self.description = ui.TextInput(
            label="Description",
            placeholder="Describe your guild...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=200
        )

        self.image_url = ui.TextInput(
            label="Image URL (Optional)",
            placeholder="https://example.com/image.png",
            required=False
        )

        self.add_item(self.guild_name)
        self.add_item(self.description)
        self.add_item(self.image_url)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        player = await Player.get(interaction.user.id)
        if not player:
            await interaction.followup.send("❌ Player not found!", ephemeral=True)
            return

        if player.guild:
            await interaction.followup.send("❌ You're already in a guild!", ephemeral=True)
            return

        if player.gold < 200000:
            await interaction.followup.send(f"❌ You need 200,000 {getEmoji('gold')} gold to create a guild!", ephemeral=True)
            return

        guild_id = extractId(self.guild_name.value)
        existing_guild = await EnhancedGuild.get(guild_id)
        if existing_guild:
            await interaction.followup.send("❌ A guild with this name already exists!", ephemeral=True)
            return

        # Create the guild
        player.gold -= 200000
        await player.save()

        new_guild = EnhancedGuild(
            id=guild_id,
            name=self.guild_name.value,
            owner=interaction.user.id,
            members=[],
            level=1,
            points=0,
            image=self.image_url.value if self.image_url.value else "",
            description=self.description.value,
            gates=0
        )

        await new_guild.save()

        # Add player to guild
        player.guild = guild_id
        await player.save()

        embed = discord.Embed(
            title="🎉 Guild Created Successfully!",
            description=f"**{self.guild_name.value}** has been created!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🏰 Guild Info",
            value=(
                f"**Name**: {self.guild_name.value}\n"
                f"**Description**: {self.description.value}\n"
                f"**Guild Master**: {interaction.user.mention}\n"
                f"**Cost**: 200,000 {getEmoji('gold')} gold"
            ),
            inline=False
        )

        await interaction.followup.send(embed=embed)


# Settings Management Modals
class MaxMembersModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Set Maximum Members")
        self.view = view

        current_max = self.view.guild.settings.get('max_members', 50)
        self.max_members = ui.TextInput(
            label="Maximum Members",
            placeholder=f"Current: {current_max} (Range: 10-100)",
            default=str(current_max),
            min_length=2,
            max_length=3
        )
        self.add_item(self.max_members)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            new_max = int(self.max_members.value)
            if new_max < 10 or new_max > 100:
                await interaction.response.send_message("❌ Maximum members must be between 10 and 100!", ephemeral=True)
                return

            # Check if new max is less than current members
            current_members = len(self.view.guild.members) + 1  # +1 for owner
            if new_max < current_members:
                await interaction.response.send_message(f"❌ Cannot set max members to {new_max} - you currently have {current_members} members!", ephemeral=True)
                return

            self.view.guild.settings['max_members'] = new_max
            await self.view.guild.save()

            await interaction.response.send_message(f"✅ Maximum members updated to {new_max}!", ephemeral=True)
            await self.view.update_view_after_modal(interaction)

        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while updating max members!", ephemeral=True)


class MinLevelModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Set Minimum Level Requirement")
        self.view = view

        current_min = self.view.guild.settings.get('min_level_requirement', 1)
        self.min_level = ui.TextInput(
            label="Minimum Level",
            placeholder=f"Current: {current_min} (Range: 1-200)",
            default=str(current_min),
            min_length=1,
            max_length=3
        )
        self.add_item(self.min_level)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            new_min = int(self.min_level.value)
            if new_min < 1 or new_min > 200:
                await interaction.response.send_message("❌ Minimum level must be between 1 and 200!", ephemeral=True)
                return

            self.view.guild.settings['min_level_requirement'] = new_min
            await self.view.guild.save()

            await interaction.response.send_message(f"✅ Minimum level requirement updated to {new_min}!", ephemeral=True)
            await self.view.update_view_after_modal(interaction)

        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ An error occurred while updating minimum level!", ephemeral=True)


# Member Management Modals
class InviteMemberModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Invite Member to Guild")
        self.view = view

        self.user_input = ui.TextInput(
            label="User ID or @mention",
            placeholder="Enter user ID (e.g., 123456789) or @username",
            min_length=3,
            max_length=50
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None

            # Try to extract user ID from mention or direct ID
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_id = int(user_input[2:-1].replace('!', ''))
            else:
                try:
                    user_id = int(user_input)
                except ValueError:
                    await interaction.response.send_message("❌ Please provide a valid user ID or @mention!", ephemeral=True)
                    return

            # Get user
            try:
                user = await interaction.client.fetch_user(user_id)
            except discord.NotFound:
                await interaction.response.send_message("❌ User not found!", ephemeral=True)
                return

            # Check if user is already in a guild
            from structure.player import Player
            target_player = await Player.get(user_id)
            if not target_player:
                await interaction.response.send_message("❌ User hasn't started playing yet!", ephemeral=True)
                return

            if target_player.guild:
                await interaction.response.send_message("❌ User is already in a guild!", ephemeral=True)
                return

            # Check guild capacity
            if len(self.view.guild.members) >= self.view.guild.settings["max_members"]:
                await interaction.response.send_message("❌ Guild is at maximum capacity!", ephemeral=True)
                return

            # Send guild invitation
            from commands.enhanced_guild_commands import GuildInviteView
            embed = discord.Embed(
                title="🏰 Guild Invitation",
                description=f"You've been invited to join **{self.view.guild.name}**!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Guild Info", value=f"Level {self.view.guild.level} • {len(self.view.guild.members)}/{self.view.guild.settings['max_members']} members", inline=False)
            embed.add_field(name="Invited by", value=interaction.user.mention, inline=True)

            view = GuildInviteView(self.view.guild.id, user_id)

            try:
                await user.send(embed=embed, view=view)
                await interaction.response.send_message(f"✅ Invitation sent to {user.mention}!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(f"❌ Could not send DM to {user.mention}. They may have DMs disabled.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while sending the invitation!", ephemeral=True)
            print(f"Error in invite modal: {e}")


class KickMemberModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Kick Member from Guild")
        self.view = view

        self.user_input = ui.TextInput(
            label="User ID or @mention",
            placeholder="Enter user ID (e.g., 123456789) or @username",
            min_length=3,
            max_length=50
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None

            # Try to extract user ID from mention or direct ID
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_id = int(user_input[2:-1].replace('!', ''))
            else:
                try:
                    user_id = int(user_input)
                except ValueError:
                    await interaction.response.send_message("❌ Please provide a valid user ID or @mention!", ephemeral=True)
                    return

            # Check if user is a member
            if not self.view.guild.is_member(user_id):
                await interaction.response.send_message("❌ User is not a member of this guild!", ephemeral=True)
                return

            # Can't kick guild master
            if user_id == self.view.guild.owner:
                await interaction.response.send_message("❌ You cannot kick the Guild Master!", ephemeral=True)
                return

            # Can't kick yourself
            if user_id == interaction.user.id:
                await interaction.response.send_message("❌ You cannot kick yourself! Use leave guild instead.", ephemeral=True)
                return

            # Remove member
            success = await self.view.guild.remove_member(user_id)
            if success:
                # Update player's guild status
                from structure.player import Player
                target_player = await Player.get(user_id)
                if target_player:
                    target_player.guild = None
                    await target_player.save()

                try:
                    user = await interaction.client.fetch_user(user_id)
                    await interaction.response.send_message(f"✅ {user.mention} has been kicked from the guild!", ephemeral=True)
                except:
                    await interaction.response.send_message(f"✅ Member (ID: {user_id}) has been kicked from the guild!", ephemeral=True)

                # Update the view
                await self.view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to kick member!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while kicking the member!", ephemeral=True)
            print(f"Error in kick modal: {e}")


class PromoteMemberModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Promote Guild Member")
        self.view = view

        self.user_input = ui.TextInput(
            label="User ID or @mention",
            placeholder="Enter user ID (e.g., 123456789) or @username",
            min_length=3,
            max_length=50
        )
        self.add_item(self.user_input)

        self.role_input = ui.TextInput(
            label="New Role",
            placeholder="officer, elder, or vice_master",
            min_length=4,
            max_length=20
        )
        self.add_item(self.role_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            from structure.enhanced_guild import GuildRole

            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None

            # Try to extract user ID from mention or direct ID
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_id = int(user_input[2:-1].replace('!', ''))
            else:
                try:
                    user_id = int(user_input)
                except ValueError:
                    await interaction.response.send_message("❌ Please provide a valid user ID or @mention!", ephemeral=True)
                    return

            # Parse role
            role_str = self.role_input.value.strip().lower()
            role_mapping = {
                'officer': GuildRole.OFFICER,
                'elder': GuildRole.ELDER,
                'vice_master': GuildRole.VICE_MASTER,
                'vice master': GuildRole.VICE_MASTER
            }

            if role_str not in role_mapping:
                await interaction.response.send_message("❌ Invalid role! Use: officer, elder, or vice_master", ephemeral=True)
                return

            target_role = role_mapping[role_str]

            # Check if user is a member
            if not self.view.guild.is_member(user_id):
                await interaction.response.send_message("❌ User is not a member of this guild!", ephemeral=True)
                return

            # Check role hierarchy
            promoter_role = self.view.guild.get_member_role(interaction.user.id)
            if not self.view.guild.can_promote_to_role(promoter_role, target_role):
                await interaction.response.send_message("❌ You don't have permission to promote to that role!", ephemeral=True)
                return

            # Promote the member
            success = await self.view.guild.promote_member(user_id, target_role)
            if success:
                try:
                    user = await interaction.client.fetch_user(user_id)
                    role_display = self.view.guild.get_role_display_name(target_role.value)
                    await interaction.response.send_message(f"✅ {user.mention} has been promoted to **{role_display}**!", ephemeral=True)
                except:
                    await interaction.response.send_message(f"✅ Member (ID: {user_id}) has been promoted!", ephemeral=True)

                # Update the view
                await self.view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to promote member!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while promoting the member!", ephemeral=True)
            print(f"Error in promote modal: {e}")


class DemoteMemberModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Demote Guild Member")
        self.view = view

        self.user_input = ui.TextInput(
            label="User ID or @mention",
            placeholder="Enter user ID (e.g., 123456789) or @username",
            min_length=3,
            max_length=50
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            from structure.enhanced_guild import GuildRole

            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None

            # Try to extract user ID from mention or direct ID
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_id = int(user_input[2:-1].replace('!', ''))
            else:
                try:
                    user_id = int(user_input)
                except ValueError:
                    await interaction.response.send_message("❌ Please provide a valid user ID or @mention!", ephemeral=True)
                    return

            # Check if user is a member
            if not self.view.guild.is_member(user_id):
                await interaction.response.send_message("❌ User is not a member of this guild!", ephemeral=True)
                return

            # Can't demote guild master
            if user_id == self.view.guild.owner:
                await interaction.response.send_message("❌ You cannot demote the Guild Master!", ephemeral=True)
                return

            # Demote to member
            success = await self.view.guild.promote_member(user_id, GuildRole.MEMBER)
            if success:
                try:
                    user = await interaction.client.fetch_user(user_id)
                    await interaction.response.send_message(f"✅ {user.mention} has been demoted to **Member**!", ephemeral=True)
                except:
                    await interaction.response.send_message(f"✅ Member (ID: {user_id}) has been demoted!", ephemeral=True)

                # Update the view
                await self.view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to demote member!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while demoting the member!", ephemeral=True)
            print(f"Error in demote modal: {e}")


# Bank Management Modals
class DepositBankModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Deposit to Guild Bank")
        self.view = view

        self.currency_input = ui.TextInput(
            label="Currency Type",
            placeholder="gold, diamond, or stones",
            min_length=4,
            max_length=10
        )
        self.add_item(self.currency_input)

        self.amount_input = ui.TextInput(
            label="Amount",
            placeholder="Enter amount to deposit",
            min_length=1,
            max_length=15
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            currency = self.currency_input.value.strip().lower()
            if currency not in ['gold', 'diamond', 'stones']:
                await interaction.response.send_message("❌ Invalid currency! Use: gold, diamond, or stones", ephemeral=True)
                return

            try:
                amount = int(self.amount_input.value.strip())
                if amount <= 0:
                    await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
                    return
            except ValueError:
                await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
                return

            # Check if player has enough currency (map stones to stone attribute)
            currency_attr = "stone" if currency == "stones" else currency
            player_amount = getattr(self.view.player, currency_attr, 0)
            if player_amount < amount:
                await interaction.response.send_message(f"❌ You don't have enough {currency}! You have {player_amount:,}", ephemeral=True)
                return

            # Deposit to guild bank
            success = await self.view.guild.deposit_to_bank(currency, amount)
            if success:
                # Deduct from player (use correct attribute name)
                setattr(self.view.player, currency_attr, player_amount - amount)
                await self.view.player.save()

                await interaction.response.send_message(f"✅ Deposited {amount:,} {currency} to the guild bank!", ephemeral=True)
                await self.view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to deposit to guild bank!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while depositing!", ephemeral=True)
            print(f"Error in deposit modal: {e}")


class WithdrawBankModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Withdraw from Guild Bank")
        self.view = view

        self.currency_input = ui.TextInput(
            label="Currency Type",
            placeholder="gold, diamond, or stones",
            min_length=4,
            max_length=10
        )
        self.add_item(self.currency_input)

        self.amount_input = ui.TextInput(
            label="Amount",
            placeholder="Enter amount to withdraw",
            min_length=1,
            max_length=15
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            currency = self.currency_input.value.strip().lower()
            if currency not in ['gold', 'diamond', 'crystals']:
                await interaction.response.send_message("❌ Invalid currency! Use: gold, diamond, or crystals", ephemeral=True)
                return

            try:
                amount = int(self.amount_input.value.strip())
                if amount <= 0:
                    await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
                    return
            except ValueError:
                await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
                return

            # Check if guild bank has enough currency
            bank_amount = self.view.guild.guild_bank.get(currency, 0)
            if bank_amount < amount:
                await interaction.response.send_message(f"❌ Guild bank doesn't have enough {currency}! Bank has {bank_amount:,}", ephemeral=True)
                return

            # Withdraw from guild bank
            success = await self.view.guild.withdraw_from_bank(currency, amount)
            if success:
                # Add to player
                player_amount = getattr(self.view.player, currency, 0)
                setattr(self.view.player, currency, player_amount + amount)
                await self.view.player.save()

                await interaction.response.send_message(f"✅ Withdrew {amount:,} {currency} from the guild bank!", ephemeral=True)
                await self.view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to withdraw from guild bank!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while withdrawing!", ephemeral=True)
            print(f"Error in withdraw modal: {e}")


# Guild Administration Modals and Views
class TransferOwnershipModal(ui.Modal):
    def __init__(self, view):
        super().__init__(title="Transfer Guild Ownership")
        self.view = view

        self.user_input = ui.TextInput(
            label="New Guild Master",
            placeholder="Enter user ID (e.g., 123456789) or @username",
            min_length=3,
            max_length=50
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None

            # Try to extract user ID from mention or direct ID
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_id = int(user_input[2:-1].replace('!', ''))
            else:
                try:
                    user_id = int(user_input)
                except ValueError:
                    await interaction.response.send_message("❌ Please provide a valid user ID or @mention!", ephemeral=True)
                    return

            # Check if user is a member
            if not self.view.guild.is_member(user_id):
                await interaction.response.send_message("❌ User is not a member of this guild!", ephemeral=True)
                return

            # Can't transfer to yourself
            if user_id == interaction.user.id:
                await interaction.response.send_message("❌ You're already the Guild Master!", ephemeral=True)
                return

            # Transfer ownership
            old_owner = self.view.guild.owner
            self.view.guild.owner = user_id

            # Demote old owner to vice master
            from structure.enhanced_guild import GuildRole
            await self.view.guild.promote_member(old_owner, GuildRole.VICE_MASTER)

            # Promote new owner to guild master (remove from members list since owner is separate)
            self.view.guild.members = [m for m in self.view.guild.members if m["id"] != user_id]

            await self.view.guild.save()

            try:
                user = await interaction.client.fetch_user(user_id)
                await interaction.response.send_message(f"✅ Guild ownership transferred to {user.mention}!", ephemeral=True)
            except:
                await interaction.response.send_message(f"✅ Guild ownership transferred to user ID: {user_id}!", ephemeral=True)

            # Update the view
            await self.view.update_view_after_modal(interaction)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while transferring ownership!", ephemeral=True)
            print(f"Error in transfer ownership modal: {e}")


class DisbandConfirmationView(ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @ui.button(label="✅ Yes, Disband", style=discord.ButtonStyle.danger)
    async def confirm_disband(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Remove all members from guild
            from structure.player import Player
            for member in self.parent_view.guild.members:
                try:
                    player = await Player.get(member["id"])
                    if player:
                        player.guild = None
                        await player.save()
                except:
                    pass

            # Remove guild master from guild
            try:
                owner_player = await Player.get(self.parent_view.guild.owner)
                if owner_player:
                    owner_player.guild = None
                    await owner_player.save()
            except:
                pass

            # Delete the guild
            await self.parent_view.guild.delete()

            embed = discord.Embed(
                title="💥 Guild Disbanded",
                description=f"**{self.parent_view.guild.name}** has been permanently disbanded.\n\nAll members have been removed and the guild data has been deleted.",
                color=discord.Color.red()
            )

            # Clear the view
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while disbanding the guild!", ephemeral=True)
            print(f"Error disbanding guild: {e}")

    @ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_disband(self, interaction: discord.Interaction, button: ui.Button):
        # Return to settings view
        self.parent_view.current_mode = "settings"
        await self.parent_view.update_view(interaction)


# Guild Details Selection View
class GuildDetailsSelectionView(ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

        # Add guild selection dropdown
        self.add_item(GuildDetailsDropdown(self))
        self.add_item(BackToBrowseButton())

    async def create_guild_selection_embed(self):
        """Create embed for guild selection"""
        embed = discord.Embed(
            title="🔍 View Guild Details",
            description="Select a guild to view its detailed information and image:",
            color=discord.Color.blue()
        )

        # Get all guilds for selection
        guilds = await self.parent_view.get_all_guilds_unified()

        embed.add_field(
            name="📋 Available Guilds",
            value=f"Choose from {len(guilds)} available guilds to view detailed information, images, and stats.",
            inline=False
        )

        embed.set_footer(text="Use the dropdown below to select a guild")
        return embed


class GuildDetailsDropdown(ui.Select):
    def __init__(self, view):
        self.parent_view = view
        self.guilds = []  # Store guilds for reference

        # Initialize with placeholder
        options = [discord.SelectOption(
            label="Click to load guilds...",
            value="load",
            description="Select this to load available guilds"
        )]

        super().__init__(
            placeholder="Select a guild to view details...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "load":
            # Load guilds and update dropdown
            await self.load_guilds(interaction)
        else:
            # Show selected guild details
            await self.show_guild_details(interaction, self.values[0])

    async def load_guilds(self, interaction):
        """Load guilds and update dropdown options"""
        try:
            # Get all guilds
            self.guilds = await self.parent_view.parent_view.get_all_guilds_unified()

            if not self.guilds:
                await interaction.response.send_message("❌ No guilds found!", ephemeral=True)
                return

            # Update dropdown options with actual guilds
            self.options = []
            for guild in self.guilds[:25]:  # Discord limit of 25 options
                tier, _ = guild.get_guild_tier()
                member_count = len(guild.members) + 1  # +1 for owner

                self.options.append(discord.SelectOption(
                    label=f"{guild.name} ({tier})",
                    value=guild.id,
                    description=f"Lv.{guild.level} • {member_count} members • {guild.points:,} points"
                ))

            # Update the view
            embed = discord.Embed(
                title="🔍 View Guild Details",
                description=f"Select from {len(self.guilds)} available guilds:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📋 Guilds Loaded",
                value="Use the dropdown below to select a guild and view its detailed information.",
                inline=False
            )

            await interaction.response.edit_message(embed=embed, view=self.view)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error loading guilds: {e}", ephemeral=True)

    async def show_guild_details(self, interaction, guild_id):
        """Show detailed information for selected guild"""
        try:
            # Find the selected guild
            selected_guild = None
            for guild in self.guilds:
                if guild.id == guild_id:
                    selected_guild = guild
                    break

            if not selected_guild:
                await interaction.response.send_message("❌ Guild not found!", ephemeral=True)
                return

            # Create detailed guild embed
            embed = await self.create_guild_details_embed(selected_guild)

            # Create back button view
            view = ui.View(timeout=300)
            back_button = BackToBrowseButton()
            view.add_item(back_button)

            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error showing guild details: {e}", ephemeral=True)

    async def create_guild_details_embed(self, guild):
        """Create detailed embed for a specific guild"""
        tier, tier_color = guild.get_guild_tier()
        member_count = len(guild.members) + 1  # +1 for owner

        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            description=guild.description or "No description available.",
            color=tier_color
        )

        # Guild image as main image (large display)
        if guild.image and guild.image.strip():
            try:
                if guild.image.startswith(('http://', 'https://')):
                    embed.set_image(url=guild.image)
            except Exception as e:
                print(f"Error setting guild image: {e}")

        # Basic info
        embed.add_field(
            name="📊 Guild Stats",
            value=(
                f"**Tier**: {tier}\n"
                f"**Level**: {guild.level}\n"
                f"**Points**: {guild.points:,}\n"
                f"**Gates Cleared**: {guild.gates}"
            ),
            inline=True
        )

        # Member info
        embed.add_field(
            name="👥 Members",
            value=(
                f"**Total**: {member_count}/{guild.settings.get('max_members', 50)}\n"
                f"**Recruiting**: {'Yes' if member_count < guild.settings.get('max_members', 50) else 'Full'}\n"
                f"**Min Level**: {guild.settings.get('min_level_requirement', 1)}\n"
                f"**Applications**: {'Required' if guild.settings.get('application_required', True) else 'Open Join'}"
            ),
            inline=True
        )

        # Guild settings
        embed.add_field(
            name="⚙️ Settings",
            value=(
                f"**Public**: {'Yes' if guild.settings.get('public_visibility', True) else 'No'}\n"
                f"**Alliances**: {'Allowed' if guild.allow_alliances else 'Disabled'}\n"
                f"**Auto-Accept**: {'Yes' if guild.settings.get('auto_accept_applications', False) else 'No'}"
            ),
            inline=True
        )

        # Guild bank (if available)
        if hasattr(guild, 'guild_bank') and guild.guild_bank:
            bank = guild.guild_bank
            total_value = bank.get('gold', 0) + (bank.get('diamond', 0) * 100) + (bank.get('stones', 0) * 10)
            embed.add_field(
                name="🏦 Guild Bank",
                value=(
                    f"💰 Gold: {bank.get('gold', 0):,}\n"
                    f"💎 Diamond: {bank.get('diamond', 0):,}\n"
                    f"🪨 Stones: {bank.get('stones', 0):,}\n"
                    f"**Total Value**: {total_value:,} gold equiv."
                ),
                inline=False
            )

        embed.set_footer(text=f"Guild ID: {guild.id} • Created: {getattr(guild, 'created_at', 'Unknown')[:10] if hasattr(guild, 'created_at') else 'Unknown'}")

        return embed


class BackToBrowseButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Browse", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Return to browse view - handle different view types
        if hasattr(self.view, 'parent_view') and self.view.parent_view:
            self.view.parent_view.current_mode = "browse"
            await self.view.parent_view.update_view(interaction)
        else:
            # Fallback - create new guild view
            from structure.player import Player
            player = await Player.get(interaction.user.id)
            if player:
                # Create a new guild main view instead of calling the command
                # Create a mock context for the view
                class MockContext:
                    def __init__(self, user):
                        self.author = user

                mock_ctx = MockContext(interaction.user)
                view = EnhancedGuildMainView(mock_ctx, player)
                embed = await view.create_embed()
                await interaction.response.edit_message(embed=embed, view=view)


# Role Permission Selection View
class RolePermissionSelectionView(ui.View):
    def __init__(self, parent_view, role, role_name):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.role = role
        self.role_name = role_name
        self.guild = parent_view.guild

        # Add permission toggle buttons
        self.add_item(ToggleInvitePermissionButton(role))
        self.add_item(ToggleKickPermissionButton(role))
        self.add_item(TogglePromotePermissionButton(role))
        self.add_item(ToggleBankPermissionButton(role))
        if role == GuildRole.VICE_MASTER:
            self.add_item(ToggleSettingsPermissionButton(role))

        self.add_item(BackToRolePermissionsButton())

    async def create_permission_selection_embed(self):
        """Create embed for permission selection"""
        embed = discord.Embed(
            title=f"{getEmoji('info') or '⚙️'} {self.role_name} Permissions",
            description=f"Configure permissions for **{self.role_name}** role in **{self.guild.name}**",
            color=discord.Color.gold()
        )

        # Get current permissions
        current_perms = self.guild.get_role_permissions(self.role)

        # List all available permissions with status
        perm_status = []

        invite_status = getEmoji('tick') or '✅' if GuildPermission.INVITE_MEMBERS in current_perms else getEmoji('negative') or '❌'
        perm_status.append(f"{invite_status} **Invite Members** - Can send guild invitations")

        kick_status = getEmoji('tick') or '✅' if GuildPermission.KICK_MEMBERS in current_perms else getEmoji('negative') or '❌'
        perm_status.append(f"{kick_status} **Kick Members** - Can remove members from guild")

        promote_status = getEmoji('tick') or '✅' if GuildPermission.PROMOTE_MEMBERS in current_perms else getEmoji('negative') or '❌'
        perm_status.append(f"{promote_status} **Promote Members** - Can promote/demote members")

        bank_status = getEmoji('tick') or '✅' if GuildPermission.MANAGE_GUILD_BANK in current_perms else getEmoji('negative') or '❌'
        perm_status.append(f"{bank_status} **Manage Bank** - Can deposit/withdraw from guild bank")

        if self.role == GuildRole.VICE_MASTER:
            settings_status = getEmoji('tick') or '✅' if GuildPermission.EDIT_GUILD_INFO in current_perms else getEmoji('negative') or '❌'
            perm_status.append(f"{settings_status} **Manage Settings** - Can modify guild settings")

        embed.add_field(
            name="🔐 Current Permissions",
            value="\n".join(perm_status),
            inline=False
        )

        embed.add_field(
            name="💡 How to Use",
            value="Click the buttons below to toggle permissions on/off for this role. Changes are saved immediately.",
            inline=False
        )

        return embed


# Permission Toggle Buttons
class ToggleInvitePermissionButton(ui.Button):
    def __init__(self, role):
        self.role = role
        super().__init__(label="📨 Toggle Invite", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        await self.toggle_permission(interaction, GuildPermission.INVITE_MEMBERS)

    async def toggle_permission(self, interaction, permission):
        # Note: Role permissions are currently hardcoded in EnhancedGuild.get_role_permissions()
        # This is a placeholder for future dynamic permission system

        await interaction.response.send_message(
            f"⚠️ **Role Permission System**\n"
            f"Role permissions are currently fixed based on role hierarchy.\n"
            f"**{self.view.role_name}** roles have predefined permissions that cannot be modified.\n\n"
            f"This feature will be enhanced in a future update for custom permission management.",
            ephemeral=True
        )

        # Update the view
        embed = await self.view.create_permission_selection_embed()
        await interaction.edit_original_response(embed=embed, view=self.view)


class ToggleKickPermissionButton(ui.Button):
    def __init__(self, role):
        self.role = role
        super().__init__(label="👢 Toggle Kick", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        await self.toggle_permission(interaction, GuildPermission.KICK_MEMBERS)

    async def toggle_permission(self, interaction, permission):
        # Note: Role permissions are currently hardcoded in EnhancedGuild.get_role_permissions()
        # This is a placeholder for future dynamic permission system

        await interaction.response.send_message(
            f"⚠️ **Role Permission System**\n"
            f"Role permissions are currently fixed based on role hierarchy.\n"
            f"**{self.view.role_name}** roles have predefined permissions that cannot be modified.\n\n"
            f"This feature will be enhanced in a future update for custom permission management.",
            ephemeral=True
        )

        embed = await self.view.create_permission_selection_embed()
        await interaction.edit_original_response(embed=embed, view=self.view)


class TogglePromotePermissionButton(ui.Button):
    def __init__(self, role):
        self.role = role
        super().__init__(label="⬆️ Toggle Promote", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        await self.toggle_permission(interaction, GuildPermission.PROMOTE_MEMBERS)

    async def toggle_permission(self, interaction, permission):
        # Note: Role permissions are currently hardcoded in EnhancedGuild.get_role_permissions()
        # This is a placeholder for future dynamic permission system

        await interaction.response.send_message(
            f"⚠️ **Role Permission System**\n"
            f"Role permissions are currently fixed based on role hierarchy.\n"
            f"**{self.view.role_name}** roles have predefined permissions that cannot be modified.\n\n"
            f"This feature will be enhanced in a future update for custom permission management.",
            ephemeral=True
        )

        embed = await self.view.create_permission_selection_embed()
        await interaction.edit_original_response(embed=embed, view=self.view)


class ToggleBankPermissionButton(ui.Button):
    def __init__(self, role):
        self.role = role
        super().__init__(label="💰 Toggle Bank", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        await self.toggle_permission(interaction, GuildPermission.MANAGE_GUILD_BANK)

    async def toggle_permission(self, interaction, permission):
        # Note: Role permissions are currently hardcoded in EnhancedGuild.get_role_permissions()
        # This is a placeholder for future dynamic permission system

        await interaction.response.send_message(
            f"⚠️ **Role Permission System**\n"
            f"Role permissions are currently fixed based on role hierarchy.\n"
            f"**{self.view.role_name}** roles have predefined permissions that cannot be modified.\n\n"
            f"This feature will be enhanced in a future update for custom permission management.",
            ephemeral=True
        )

        embed = await self.view.create_permission_selection_embed()
        await interaction.edit_original_response(embed=embed, view=self.view)


class ToggleSettingsPermissionButton(ui.Button):
    def __init__(self, role):
        self.role = role
        super().__init__(label="⚙️ Toggle Settings", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        await self.toggle_permission(interaction, GuildPermission.EDIT_GUILD_INFO)

    async def toggle_permission(self, interaction, permission):
        # Note: Role permissions are currently hardcoded in EnhancedGuild.get_role_permissions()
        # This is a placeholder for future dynamic permission system

        await interaction.response.send_message(
            f"⚠️ **Role Permission System**\n"
            f"Role permissions are currently fixed based on role hierarchy.\n"
            f"**{self.view.role_name}** roles have predefined permissions that cannot be modified.\n\n"
            f"This feature will be enhanced in a future update for custom permission management.",
            ephemeral=True
        )


class BackToRolePermissionsButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Role Permissions", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction):
        # Return to role permissions view
        self.view.parent_view.current_mode = "role_permissions"
        await self.view.parent_view.update_view(interaction)


# Member Selection View with Dropdowns
class MemberSelectionView(ui.View):
    def __init__(self, parent_view, action_type):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.action_type = action_type  # "kick", "promote", "demote"
        self.guild = parent_view.guild
        self.bot = parent_view.ctx.bot

        # Add member selection dropdown
        self.add_item(MemberSelectDropdown(self))
        self.add_item(BackToMembersButton())

    async def create_member_selection_embed(self, action_type):
        """Create embed for member selection"""
        action_titles = {
            "kick": "👢 Kick Member",
            "promote": "⬆️ Promote Member",
            "demote": "⬇️ Demote Member",
            "transfer_ownership": "👑 Transfer Ownership"
        }

        action_descriptions = {
            "kick": "Select a member to remove from the guild:",
            "promote": "Select a member to promote to a higher role:",
            "demote": "Select a member to demote to a lower role:",
            "transfer_ownership": "⚠️ Select a member to transfer guild ownership to:"
        }

        embed = discord.Embed(
            title=f"{action_titles[action_type]}",
            description=action_descriptions[action_type],
            color=discord.Color.blue()
        )

        # Show current members
        member_count = len(self.guild.members)
        embed.add_field(
            name="📊 Guild Members",
            value=f"Total Members: {member_count + 1} (including Guild Master)",
            inline=False
        )

        embed.set_footer(text="Use the dropdown below to select a member")
        return embed


class MemberSelectDropdown(ui.Select):
    def __init__(self, view):
        self.parent_view = view
        self.guild = view.guild
        self.action_type = view.action_type

        # Create options from guild members
        options = []

        # Add guild members (excluding owner for kick/demote, including for promote)
        for member in self.guild.members:
            try:
                # Get member role
                member_role = self.guild.get_member_role(member["id"])
                role_display = self.guild.get_role_display_name(member_role.value) if member_role else "Member"

                # Skip owner for kick/demote (but include for transfer_ownership)
                if self.action_type in ["kick", "demote"] and member["id"] == self.guild.owner:
                    continue

                # Get username (try to fetch from Discord)
                try:
                    user = view.bot.get_user(member["id"])
                    if not user:
                        # If not in cache, we'll use the ID
                        username = f"User {member['id']}"
                    else:
                        username = user.display_name
                except:
                    username = f"User {member['id']}"

                options.append(discord.SelectOption(
                    label=f"{username} ({role_display})",
                    value=str(member["id"]),
                    description=f"Level: {member.get('level', 'Unknown')} • Role: {role_display}"
                ))

            except Exception as e:
                print(f"Error processing member {member}: {e}")
                continue

        # If no valid options, add a placeholder
        if not options:
            options.append(discord.SelectOption(
                label="No members available",
                value="none",
                description="No members can be selected for this action"
            ))

        super().__init__(
            placeholder=f"Select a member to {self.action_type}...",
            options=options[:25],  # Discord limit of 25 options
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ No valid members to select!", ephemeral=True)
            return

        selected_user_id = int(self.values[0])

        # Get the selected user
        try:
            user = await interaction.client.fetch_user(selected_user_id)
            username = user.display_name
        except:
            username = f"User {selected_user_id}"

        # Perform the action based on type
        if self.action_type == "kick":
            await self.handle_kick(interaction, selected_user_id, username)
        elif self.action_type == "promote":
            await self.handle_promote(interaction, selected_user_id, username)
        elif self.action_type == "demote":
            await self.handle_demote(interaction, selected_user_id, username)
        elif self.action_type == "transfer_ownership":
            await self.handle_transfer_ownership(interaction, selected_user_id, username)

    async def handle_kick(self, interaction, user_id, username):
        """Handle kicking a member"""
        try:
            # Remove member from guild
            success = await self.guild.remove_member(user_id)
            if success:
                # Update player's guild status
                from structure.player import Player
                target_player = await Player.get(user_id)
                if target_player:
                    target_player.guild = None
                    await target_player.save()

                embed = discord.Embed(
                    title="✅ Member Kicked",
                    description=f"**{username}** has been removed from the guild.",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)

                # Return to members view after 3 seconds
                await asyncio.sleep(3)
                self.parent_view.parent_view.current_mode = "members"
                await self.parent_view.parent_view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to kick member!", ephemeral=True)
        except Exception as e:
            await safe_send_error(interaction, "❌ An error occurred while kicking the member!")
            print(f"Error kicking member: {e}")

    async def handle_promote(self, interaction, user_id, username):
        """Handle promoting a member - show role selection"""
        view = RoleSelectionView(self.parent_view, user_id, username, "promote")
        embed = await view.create_role_selection_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_demote(self, interaction, user_id, username):
        """Handle demoting a member"""
        try:
            from structure.enhanced_guild import GuildRole

            # Demote to member
            success = await self.guild.promote_member(user_id, GuildRole.MEMBER)
            if success:
                embed = discord.Embed(
                    title="✅ Member Demoted",
                    description=f"**{username}** has been demoted to **Member**.",
                    color=discord.Color.orange()
                )
                await interaction.response.edit_message(embed=embed, view=None)

                # Return to members view after 3 seconds
                await asyncio.sleep(3)
                self.parent_view.parent_view.current_mode = "members"
                await self.parent_view.parent_view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to demote member!", ephemeral=True)
        except Exception as e:
            await safe_send_error(interaction, "❌ An error occurred while demoting the member!")
            print(f"Error demoting member: {e}")

    async def handle_transfer_ownership(self, interaction, user_id, username):
        """Handle transferring guild ownership"""
        try:
            # Can't transfer to yourself
            if user_id == interaction.user.id:
                await interaction.response.send_message("❌ You're already the Guild Master!", ephemeral=True)
                return

            # Show confirmation dialog
            view = TransferOwnershipConfirmationView(self.parent_view, user_id, username)
            embed = discord.Embed(
                title="⚠️ Transfer Ownership Confirmation",
                description=f"Are you sure you want to transfer guild ownership to **{username}**?\n\n**This action cannot be undone!**\n\nYou will become a Vice Master and they will become the new Guild Master.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="👤 New Guild Master",
                value=f"**{username}**",
                inline=True
            )
            embed.add_field(
                name="👤 Your New Role",
                value="**Vice Master**",
                inline=True
            )
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while preparing ownership transfer!", ephemeral=True)
            print(f"Error in transfer ownership: {e}")


class BackToMembersButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Members", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Return to members view
        self.view.parent_view.current_mode = "members"
        await self.view.parent_view.update_view(interaction)


# Role Selection View for Promotions
class RoleSelectionView(ui.View):
    def __init__(self, parent_view, user_id, username, action_type):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.user_id = user_id
        self.username = username
        self.action_type = action_type
        self.guild = parent_view.guild

        # Add role selection dropdown
        self.add_item(RoleSelectDropdown(self))
        self.add_item(BackToMemberSelectionButton())

    async def create_role_selection_embed(self):
        """Create embed for role selection"""
        embed = discord.Embed(
            title="⬆️ Select New Role",
            description=f"Choose the new role for **{self.username}**:",
            color=discord.Color.blue()
        )

        # Show current role
        current_role = self.guild.get_member_role(self.user_id)
        current_display = self.guild.get_role_display_name(current_role.value) if current_role else "Member"

        embed.add_field(
            name="👤 Member Info",
            value=f"**Name**: {self.username}\n**Current Role**: {current_display}",
            inline=False
        )

        embed.add_field(
            name="📋 Available Roles",
            value="• **Officer** - Basic management permissions\n• **Elder** - Advanced management permissions\n• **Vice Master** - Full management permissions",
            inline=False
        )

        embed.set_footer(text="Use the dropdown below to select a new role")
        return embed


class RoleSelectDropdown(ui.Select):
    def __init__(self, view):
        self.parent_view = view
        self.guild = view.guild
        self.user_id = view.user_id
        self.username = view.username

        # Get promoter's role to determine available promotions
        # Navigate up the view hierarchy to get the main view
        main_view = view.parent_view
        while hasattr(main_view, 'parent_view') and main_view.parent_view:
            main_view = main_view.parent_view

        promoter_role = self.guild.get_member_role(main_view.player.id)

        options = []
        from structure.enhanced_guild import GuildRole

        # Add available roles based on promoter's permissions
        if self.guild.can_promote_to_role(promoter_role, GuildRole.OFFICER):
            options.append(discord.SelectOption(
                label="Officer",
                value="officer",
                description="Basic management permissions",
                emoji="👮"
            ))

        if self.guild.can_promote_to_role(promoter_role, GuildRole.ELDER):
            options.append(discord.SelectOption(
                label="Elder",
                value="elder",
                description="Advanced management permissions",
                emoji="👴"
            ))

        if self.guild.can_promote_to_role(promoter_role, GuildRole.VICE_MASTER):
            options.append(discord.SelectOption(
                label="Vice Master",
                value="vice_master",
                description="Full management permissions",
                emoji="👑"
            ))

        # If no valid options, add placeholder
        if not options:
            options.append(discord.SelectOption(
                label="No roles available",
                value="none",
                description="You don't have permission to promote to any roles"
            ))

        super().__init__(
            placeholder="Select a role to promote to...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ No valid roles to promote to!", ephemeral=True)
            return

        role_str = self.values[0]

        # Map role strings to GuildRole enum
        from structure.enhanced_guild import GuildRole
        role_mapping = {
            'officer': GuildRole.OFFICER,
            'elder': GuildRole.ELDER,
            'vice_master': GuildRole.VICE_MASTER
        }

        target_role = role_mapping[role_str]

        try:
            # Promote the member
            success = await self.guild.promote_member(self.user_id, target_role)
            if success:
                role_display = self.guild.get_role_display_name(target_role.value)
                embed = discord.Embed(
                    title="✅ Member Promoted",
                    description=f"**{self.username}** has been promoted to **{role_display}**!",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)

                # Return to members view after 3 seconds
                await asyncio.sleep(3)
                # Navigate to main view
                main_view = self.parent_view.parent_view
                while hasattr(main_view, 'parent_view') and main_view.parent_view:
                    main_view = main_view.parent_view
                main_view.current_mode = "members"
                await main_view.update_view_after_modal(interaction)
            else:
                await interaction.response.send_message("❌ Failed to promote member!", ephemeral=True)
        except Exception as e:
            await safe_send_error(interaction, "❌ An error occurred while promoting the member!")
            print(f"Error promoting member: {e}")


class BackToMemberSelectionButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back to Member Selection", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Return to member selection view
        view = MemberSelectionView(self.view.parent_view.parent_view, "promote")
        embed = await view.create_member_selection_embed("promote")
        await interaction.response.edit_message(embed=embed, view=view)


# Transfer Ownership Confirmation View
class TransferOwnershipConfirmationView(ui.View):
    def __init__(self, parent_view, user_id, username):
        super().__init__(timeout=60)
        self.parent_view = parent_view
        self.user_id = user_id
        self.username = username
        self.guild = parent_view.guild

    @ui.button(label="✅ Yes, Transfer", style=discord.ButtonStyle.danger)
    async def confirm_transfer(self, interaction: discord.Interaction, button: ui.Button):
        try:
            # Transfer ownership
            old_owner = self.guild.owner
            self.guild.owner = self.user_id

            # Demote old owner to vice master
            from structure.enhanced_guild import GuildRole
            await self.guild.promote_member(old_owner, GuildRole.VICE_MASTER)

            # Remove new owner from members list (since owner is separate)
            self.guild.members = [m for m in self.guild.members if m["id"] != self.user_id]

            await self.guild.save()

            embed = discord.Embed(
                title="✅ Ownership Transferred",
                description=f"Guild ownership has been successfully transferred to **{self.username}**!\n\nYou are now a Vice Master.",
                color=discord.Color.green()
            )

            # Clear the view
            self.clear_items()
            await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            await interaction.response.send_message("❌ An error occurred while transferring ownership!", ephemeral=True)
            print(f"Error transferring ownership: {e}")

    @ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_transfer(self, interaction: discord.Interaction, button: ui.Button):
        # Return to settings view
        self.parent_view.parent_view.current_mode = "settings"
        await self.parent_view.parent_view.update_view(interaction)
