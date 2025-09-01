import logging
import discord
from discord.ext import commands
from discord import app_commands
from structure.emoji import getEmoji
from structure.player import Player
from utilis.utilis import extractId
from structure.guild import Guild
from commands.guild_creation import GuildCreationView
import re

# Re-imported in case this file is used standalone
from discord.ui import Button, View

# Forward-declare view classes for type hinting
class MembersPaginator:
    pass
class GuildInfoView:
    pass

def _get_tier_and_color(points: int, tiers: dict) -> tuple[str, discord.Colour]:
    """Return the tier label and an appropriate embed colour based on points."""
    ordered = list(tiers.items())
    palette: dict[str, discord.Colour] = {
        "S-Tier": discord.Color.gold(),
        "A-Tier": discord.Color.from_str("#9b59b6"),
        "B-Tier": discord.Color.blue(),
        "C-Tier": discord.Color.green(),
        "D-Tier": discord.Color.orange(),
        "E-Tier": discord.Color.light_grey(),
    }
    for tier_name, threshold in ordered:
        if points >= threshold:
            return tier_name, palette.get(tier_name, discord.Color.light_grey())
    return "E-Tier", palette["E-Tier"]


class GuildPaginationView(View):
    """Paginated view for listing guilds, locked to the command author."""

    def __init__(self, guilds, tiers, ctx):
        super().__init__(timeout=60)
        self.guilds = guilds
        self.tiers = tiers
        self.ctx = ctx
        self.author_id = ctx.author.id
        self.page = 0
        self.page_size = 10
        self.max_page = (len(guilds) - 1) // self.page_size
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
            return False
        return True

    async def update_embed(self, interaction: discord.Interaction = None):
        start = self.page * self.page_size
        end = start + self.page_size
        guilds_to_display = self.guilds[start:end]
        
        description = "> Type `sl guild join [name]` to join a guild! and `sl guild info [name]` to view more information about the guild.\n"
        description += "### List of all guilds\n\n"

        for idx, guild in enumerate(guilds_to_display, start=start + 1):
            tier_label, _ = _get_tier_and_color(guild.points, self.tiers)
            e = "<:e_tier1:1353347619791044668><:e_tier2:1353347635888656424>"
            if tier_label == "S-Tier":
                e = "<:s_tier1:1353345107826442240><:s_tier2:1353345128483262545>"
            elif tier_label == "A-Tier":
                e = "<:a_tier1:1353345662149722122><:a_tier2:1353345680571109428>"
            elif tier_label == "B-Tier":
                e = "<:b_tier1:1353346122717986890><:b_tier2:1353346140074151980>"
            elif tier_label == "C-Tier":
                e = "<:c_tier1:1353346570191376455><:c_tier2:1353346589569187912>"
            elif tier_label == "D-Tier":
                e = "<:d_tier1:1353347123738837102><:d_tier2:1353347139610214441>"
            
            # Using your original format for the guild listing
            entry = (
                f"`#{idx:>3}` - **{guild.name}** ( {e} )\n"
                f"-# **Members** [{len(guild.members)}/50] | **{guild.points:,}** points\n"
            )
            description += entry + "\n"
        
        embed = discord.Embed(title="Guild Leaderboard", description=description)
        embed.set_footer(text=f"Viewing Page {self.page + 1}/{self.max_page + 1}")
        embed.set_image(url="https://media1.tenor.com/m/8-S-r_BKN7cAAAAd/sung-jinwoo-monarca-das-sombras.gif")
        
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)
        else:
            self.message = await self.ctx.reply(embed=embed, view=self, mention_author=False)

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary, row=0)
    async def first_button(self, interaction: discord.Interaction, button: Button):
        if self.page != 0: self.page = 0; await self.update_embed(interaction)
        else: await interaction.response.defer()

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.page > 0: self.page -= 1; await self.update_embed(interaction)
        else: await interaction.response.defer()

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.primary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.page < self.max_page: self.page += 1; await self.update_embed(interaction)
        else: await interaction.response.defer()

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary, row=0)
    async def last_button(self, interaction: discord.Interaction, button: Button):
        if self.page != self.max_page: self.page = self.max_page; await self.update_embed(interaction)
        else: await interaction.response.defer()

    async def on_timeout(self):
        for item in self.children: item.disabled = True
        if self.message: await self.message.edit(view=self)


class MembersPaginator(View):
    def __init__(self, guild, player, members, bot, author_id, original_view, page=0):
        super().__init__(timeout=30)
        self.guild = guild; self.player = player; self.members = members
        self.bot = bot; self.author_id = author_id; self.original_view = original_view
        self.page = page; self.page_size = 10; self.max_pages = (len(members) - 1) // self.page_size + 1
        self.update_buttons()

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.author_id: await i.response.send_message("You cannot use these buttons.", ephemeral=True); return False
        return True

    def update_buttons(self):
        self.clear_items()
        self.add_item(PreviousPageButton(self))
        self.add_item(NextPageButton(self))
        self.add_item(BackButton(self))

    async def update_message(self, interaction: discord.Interaction):
        start = self.page * self.page_size
        end = start + self.page_size
        members_list = self.members[start:end]
        down = getEmoji('down')
        lines = [f"`#{start + idx + 1}` <@{m['id']}>\n{down} Gates Cleared: `{m['gc']}`" for idx, m in enumerate(members_list)]
        leaderboard = "\n".join(lines) if lines else "No members found."
        
        embed = discord.Embed(title=f"{self.guild.name} Leaderboard", description=leaderboard)
        embed.set_thumbnail(url="https://files.catbox.moe/jvxvcr.png")
        embed.set_footer(text=f"Page {self.page + 1}/{self.max_pages} | Total Members: {len(self.members)}")
        await interaction.response.edit_message(embed=embed, view=self)

class PreviousPageButton(discord.ui.Button):
    def __init__(self, paginator: MembersPaginator): super().__init__(style=discord.ButtonStyle.secondary, label="Previous"); self.paginator = paginator
    async def callback(self, i: discord.Interaction):
        if self.paginator.page > 0: self.paginator.page -= 1; await self.paginator.update_message(i)
        else: await i.response.defer()

class NextPageButton(discord.ui.Button):
    def __init__(self, paginator: MembersPaginator): super().__init__(style=discord.ButtonStyle.primary, label="Next"); self.paginator = paginator
    async def callback(self, i: discord.Interaction):
        if self.paginator.page < self.paginator.max_pages - 1: self.paginator.page += 1; await self.paginator.update_message(i)
        else: await i.response.defer()

class BackButton(discord.ui.Button):
    def __init__(self, paginator: MembersPaginator): super().__init__(style=discord.ButtonStyle.grey, label="Back", row=1); self.paginator = paginator
    async def callback(self, i: discord.Interaction): await i.response.edit_message(embed=self.paginator.original_view.original_embed, view=self.paginator.original_view)

class MembersButton(discord.ui.Button):
    def __init__(self, guild, player, bot, author_id, original_view):
        super().__init__(style=discord.ButtonStyle.primary, label="Members", emoji="👥")
        self.guild = guild; self.player = player; self.bot = bot
        self.author_id = author_id; self.original_view = original_view

    async def callback(self, i: discord.Interaction):
        if self.player.guild != self.guild.id: await i.response.send_message("You are not in this guild.", ephemeral=True); return
        members = await self.guild.get_members()
        members.sort(key=lambda x: x['gc'], reverse=True)
        view = MembersPaginator(self.guild, self.player, members, self.bot, self.author_id, self.original_view)
        await view.update_message(i)


class BackToGuildMainButton(discord.ui.Button):
    def __init__(self, original_embed):
        super().__init__(style=discord.ButtonStyle.secondary, label="Back", emoji="🔙")
        self.original_embed = original_embed

    async def callback(self, i: discord.Interaction):
        await i.response.edit_message(embed=self.original_embed, view=None)

class GuildInfoView(discord.ui.View):
    def __init__(self, guild, player, bot, author_id, original_embed, timeout: float = 20.0):
        super().__init__(timeout=timeout)
        self.guild=guild; self.player=player; self.bot=bot
        self.author_id = author_id; self.original_embed = original_embed
        self.add_item(MembersButton(guild, player, bot, author_id, self))
        self.add_item(BackToGuildMainButton(original_embed))

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.author_id: await i.response.send_message("You cannot use these buttons.", ephemeral=True); return False
        return True

class GuildCommands(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.hybrid_group(name="guild", invoke_without_command=True, help="Enhanced guild interface with roles, permissions, and advanced features.")
    async def guild_group(self, ctx: commands.Context):
        """Enhanced guild interface with modern UI and advanced features"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Import the enhanced guild view
        from commands.enhanced_guild_ui import EnhancedGuildMainView

        view = EnhancedGuildMainView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @guild_group.command(name="create", help="Create a new guild with enhanced features and customization.")
    async def create_guild(self, ctx: commands.Context):
        """Create a new guild using the enhanced creation system"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        if player.trade:
            embed = discord.Embed(
                title="❌ In Trade",
                description=f"<@{player.id}> is currently in a trade.",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        if player.guild:
            embed = discord.Embed(
                title="❌ Already in Guild",
                description="You're already a member of a guild. Leave your current guild first to create a new one.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Use the enhanced guild creation system
        view = GuildCreationView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @guild_group.command(name="transfer", help="Transfer ownership of your guild to another member.")
    @app_commands.describe(target="The member to transfer ownership to.")
    async def transfer_guild(self, ctx: commands.Context, target: discord.Member):
        player = await Player.get(ctx.author.id)
        if player is None or not player.guild: await ctx.send(embed=discord.Embed(title="Error", description="You are not in a guild.", color=discord.Color.red())); return
        if player.trade: await ctx.send(embed=discord.Embed(title="Error", description=f"<@{player.id}> is in a trade.", color=discord.Color.orange())); return

        guild = await Guild.get(player.guild)
        if not guild or guild.owner != ctx.author.id: await ctx.send(embed=discord.Embed(title="Error", description="You are not the owner of a guild.", color=discord.Color.red())); return

        target_player = await Player.get(target.id)
        if not target_player or target_player.guild != guild.id: await ctx.send(embed=discord.Embed(title="Error", description=f"{target.mention} is not in your guild.", color=discord.Color.red())); return

        guild.owner = target.id
        await guild.save()
        await ctx.send(embed=discord.Embed(title="Success", description=f"Ownership transferred to {target.mention}.", color=discord.Color.green()))

    @guild_group.command(name="join", help="Join an existing guild.")
    @app_commands.describe(name="The name of the guild to join.")
    async def join_guild(self, ctx: commands.Context, *, name: str):
        player = await Player.get(ctx.author.id)
        if player is None: await ctx.send(embed=discord.Embed(title="Error", description="You haven't started.", color=discord.Color.red())); return
        if player.trade: await ctx.send(embed=discord.Embed(title="Error", description=f"<@{player.id}> is in a trade.", color=discord.Color.orange())); return
        if player.guild: await ctx.send(embed=discord.Embed(title="Error", description="You are already in a guild.", color=discord.Color.red())); return

        guild_id = extractId(name)
        guild = await Guild.get(guild_id)
        if not guild: await ctx.send(embed=discord.Embed(title="Error", description="This guild doesn't exist.", color=discord.Color.red())); return
        if len(guild.members) >= 50: await ctx.send(embed=discord.Embed(title="Error", description="This guild is full.", color=discord.Color.red())); return

        player.guild = guild_id
        await player.save()
        await guild.add_member(player.id)

        # Track guild join achievement
        try:
            from structure.achievement_tracker import AchievementTracker
            await AchievementTracker.track_guild_join(player, guild.name)
        except Exception as e:
            logging.error(f"Error tracking guild join achievement: {e}")

        await ctx.send(embed=discord.Embed(title="Success", description=f"You have joined '{guild.name}'!", color=discord.Color.green()))

    @guild_group.command(name="leave", help="Leave your current guild.")
    async def leave_guild(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player or not player.guild: await ctx.send(embed=discord.Embed(title="Error", description="You are not in a guild.", color=discord.Color.red())); return
        if player.trade: await ctx.send(embed=discord.Embed(title="Error", description=f"<@{player.id}> is in a trade.", color=discord.Color.orange())); return
        guild = await Guild.get(player.guild)
        if guild.owner == ctx.author.id: await ctx.send(embed=discord.Embed(title="Error", description="Guild owners cannot leave; they must delete or transfer.", color=discord.Color.red())); return
        
        await guild.remove_member(ctx.author.id)
        player.guild = None
        await player.save()
        await ctx.send(embed=discord.Embed(title="Success", description=f"You have left '{guild.name}'.", color=discord.Color.green()))

    @guild_group.command(name="info", help="Get information about a specific guild or your own.")
    @app_commands.describe(name="The name of the guild to get info about.")
    async def guild_info(self, ctx: commands.Context, *, name: str = None):
        player = await Player.get(ctx.author.id)
        if player is None: await ctx.send(embed=discord.Embed(title="Error", description="You haven't started. Use `sl start`.", color=discord.Color.red())); return

        guild_id = extractId(name) if name else player.guild
        text = f"To join this guild use sl guild join {name}" if name else "Viewing your guild."
        if not guild_id: await ctx.send(embed=discord.Embed(title="Error", description="Provide a guild name or be in a guild.", color=discord.Color.red())); return
        guild = await Guild.get(guild_id)
        if not guild: await ctx.send(embed=discord.Embed(title="Error", description="Guild does not exist.", color=discord.Color.red())); return

        tiers = {"S-Tier": 1000000, "A-Tier": 500000, "B-Tier": 250000, "C-Tier": 100000, "D-Tier": 50000, "E-Tier": 0}
        tier_label, embed_color = _get_tier_and_color(guild.points, tiers)
        
        embed = discord.Embed(title=guild.name, description=f'"*{guild.description}*"', color=embed_color)
        embed.set_thumbnail(url="https://files.catbox.moe/jvxvcr.png")
        if guild.image and guild.image.startswith(('http://', 'https://')): embed.set_image(url=guild.image)

        owner = await self.bot.fetch_user(guild.owner)
        qx = getEmoji("qx")
        down = getEmoji("down")
        
        embed.add_field(name="<:info:1341396155690520618> Info", value=f"{qx}Leader: **{owner.name}**\n{down}Hunters: `[{len(guild.members)}/50]`", inline=False)
        embed.add_field(name=f"{getEmoji('attack')} Stats", value=f"{qx}Level: **{guild.level}**\n{qx}Gates Cleared: **{guild.gates}**\n{down}Guild Points: `{guild.points}`", inline=False)
        embed.set_footer(text=text)

        view = GuildInfoView(guild, player, self.bot, ctx.author.id, original_embed=embed)
        await ctx.send(embed=embed, view=view)

    @guild_group.command(name="promote", help="Promote a guild member to a higher role")
    @app_commands.describe(user="The user to promote", role="The role to promote them to")
    @app_commands.choices(role=[
        app_commands.Choice(name="Officer", value="officer"),
        app_commands.Choice(name="Vice Master", value="vice_master")
    ])
    async def promote_member(self, ctx: commands.Context, user: discord.User, role: str):
        """Promote a guild member"""
        from structure.enhanced_guild import EnhancedGuild, GuildRole, GuildPermission

        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        # Get or convert guild to enhanced format
        guild = await self.get_or_convert_guild(player.guild)
        if not guild:
            await ctx.reply("❌ Guild not found!", ephemeral=True)
            return

        # Check permissions
        if not guild.has_permission(ctx.author.id, GuildPermission.PROMOTE_MEMBERS):
            await ctx.reply("❌ You don't have permission to promote members!", ephemeral=True)
            return

        # Check if target is a member
        if not guild.is_member(user.id):
            await ctx.reply("❌ That user is not a member of your guild!", ephemeral=True)
            return

        # Check role hierarchy
        promoter_role = guild.get_member_role(ctx.author.id)
        target_role = GuildRole(role)

        if not guild.can_promote_to_role(promoter_role, target_role):
            await ctx.reply("❌ You can't promote to that role!", ephemeral=True)
            return

        # Promote the member
        success = await guild.promote_member(user.id, target_role)
        if success:
            embed = discord.Embed(
                title="🎉 Member Promoted!",
                description=f"{user.mention} has been promoted to **{guild.get_role_display_name(role)}**!",
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("❌ Failed to promote member!", ephemeral=True)

    @guild_group.command(name="demote", help="Demote a guild member to a lower role")
    @app_commands.describe(user="The user to demote")
    async def demote_member(self, ctx: commands.Context, user: discord.User):
        """Demote a guild member"""
        from structure.enhanced_guild import EnhancedGuild, GuildRole, GuildPermission

        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await self.get_or_convert_guild(player.guild)
        if not guild:
            await ctx.reply("❌ Guild not found!", ephemeral=True)
            return

        # Check permissions
        if not guild.has_permission(ctx.author.id, GuildPermission.DEMOTE_MEMBERS):
            await ctx.reply("❌ You don't have permission to demote members!", ephemeral=True)
            return

        # Check if target is a member
        if not guild.is_member(user.id):
            await ctx.reply("❌ That user is not a member of your guild!", ephemeral=True)
            return

        # Can't demote guild master
        if user.id == guild.owner:
            await ctx.reply("❌ You can't demote the Guild Master!", ephemeral=True)
            return

        # Demote to member
        success = await guild.promote_member(user.id, GuildRole.MEMBER)
        if success:
            embed = discord.Embed(
                title="📉 Member Demoted",
                description=f"{user.mention} has been demoted to **{guild.get_role_display_name('member')}**!",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("❌ Failed to demote member!", ephemeral=True)

    @guild_group.command(name="bank", help="View or manage guild bank")
    @app_commands.describe(action="Action to perform", currency="Currency type", amount="Amount to deposit/withdraw")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="View", value="view"),
            app_commands.Choice(name="Deposit", value="deposit"),
            app_commands.Choice(name="Withdraw", value="withdraw")
        ],
        currency=[
            app_commands.Choice(name="Gold", value="gold"),
            app_commands.Choice(name="Diamond", value="diamond"),
            app_commands.Choice(name="Crystals", value="crystals")
        ]
    )
    async def guild_bank(self, ctx: commands.Context, action: str, currency: str = None, amount: int = None):
        """Manage guild bank"""
        from structure.enhanced_guild import EnhancedGuild, GuildPermission

        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await self.get_or_convert_guild(player.guild)
        if not guild:
            await ctx.reply("❌ Guild not found!", ephemeral=True)
            return

        if action == "view":
            embed = discord.Embed(
                title=f"🏦 {guild.name} Bank",
                description="Guild shared resources",
                color=discord.Color.gold()
            )

            bank = guild.guild_bank
            embed.add_field(
                name="💰 Available Funds",
                value=(
                    f"{getEmoji('gold')} Gold: {bank.get('gold', 0):,}\n"
                    f"{getEmoji('diamond')} Diamond: {bank.get('diamond', 0):,}\n"
                    f"{getEmoji('crystals')} Crystals: {bank.get('crystals', 0):,}"
                ),
                inline=False
            )

            total_value = bank.get('gold', 0) + (bank.get('diamond', 0) * 100) + (bank.get('crystals', 0) * 10)
            embed.add_field(
                name="📊 Total Value",
                value=f"{total_value:,} gold equivalent",
                inline=False
            )

            await ctx.reply(embed=embed)

        elif action in ["deposit", "withdraw"]:
            if not currency or not amount:
                await ctx.reply("❌ Please specify currency and amount!", ephemeral=True)
                return

            if amount <= 0:
                await ctx.reply("❌ Amount must be positive!", ephemeral=True)
                return

            # Check permissions for withdraw
            if action == "withdraw" and not guild.has_permission(ctx.author.id, GuildPermission.MANAGE_GUILD_BANK):
                await ctx.reply("❌ You don't have permission to withdraw from the guild bank!", ephemeral=True)
                return

            if action == "deposit":
                # Check if player has enough currency
                player_amount = getattr(player, currency, 0)
                if player_amount < amount:
                    await ctx.reply(f"❌ You don't have enough {currency}! You have {player_amount:,}, need {amount:,}.", ephemeral=True)
                    return

                # Transfer from player to guild
                setattr(player, currency, player_amount - amount)
                await player.save()
                await guild.contribute_to_bank(currency, amount)

                embed = discord.Embed(
                    title="💰 Deposit Successful",
                    description=f"Deposited {amount:,} {currency} to the guild bank!",
                    color=discord.Color.green()
                )

            else:  # withdraw
                # Check if guild has enough
                guild_amount = guild.guild_bank.get(currency, 0)
                if guild_amount < amount:
                    await ctx.reply(f"❌ Guild doesn't have enough {currency}! Guild has {guild_amount:,}, need {amount:,}.", ephemeral=True)
                    return

                # Transfer from guild to player
                success = await guild.withdraw_from_bank(currency, amount)
                if success:
                    player_amount = getattr(player, currency, 0)
                    setattr(player, currency, player_amount + amount)
                    await player.save()

                    embed = discord.Embed(
                        title="💸 Withdrawal Successful",
                        description=f"Withdrew {amount:,} {currency} from the guild bank!",
                        color=discord.Color.blue()
                    )
                else:
                    await ctx.reply("❌ Failed to withdraw from guild bank!", ephemeral=True)
                    return

            await ctx.reply(embed=embed)

    async def convert_to_enhanced_guild(self, old_guild: Guild):
        """Convert old guild to enhanced guild format with comprehensive data preservation"""
        from structure.enhanced_guild import EnhancedGuild
        from datetime import datetime

        # Convert old member format to new format with proper data handling
        enhanced_members = []

        # Handle different member data formats from old guild system
        if hasattr(old_guild, 'members') and old_guild.members:
            for member_data in old_guild.members:
                if isinstance(member_data, dict):
                    # Extract member ID - handle different formats
                    member_id = member_data.get("id") or member_data.get("user_id")
                    if member_id:
                        enhanced_members.append({
                            "id": int(member_id),
                            "role": "member",  # All old members become regular members
                            "joined_at": member_data.get("joined_at", datetime.now().isoformat()),
                            "contribution": member_data.get("gc", member_data.get("contribution", 0)),
                            "last_active": member_data.get("last_active", datetime.now().isoformat())
                        })
                elif isinstance(member_data, (int, str)):
                    # Handle simple member ID format
                    enhanced_members.append({
                        "id": int(member_data),
                        "role": "member",
                        "joined_at": datetime.now().isoformat(),
                        "contribution": 0,
                        "last_active": datetime.now().isoformat()
                    })

        # Preserve all original guild data
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
            allow_alliances=getattr(old_guild, 'allow_alliances', False),
            # Initialize new enhanced features with defaults
            guild_bank={"gold": 0, "diamond": 0, "crystals": 0},
            applications=[],
            settings={
                "auto_accept_applications": False,
                "min_level_requirement": 1,
                "application_required": True,
                "max_members": 50,
                "public_visibility": True
            },
            created_at=getattr(old_guild, 'created_at', datetime.now().isoformat()),
            last_active=datetime.now().isoformat()
        )

        # Save the enhanced guild
        await enhanced_guild.save()

        print(f"✅ Converted guild '{old_guild.name}' to enhanced format with {len(enhanced_members)} members")
        return enhanced_guild

    async def get_or_convert_guild(self, guild_id: str):
        """Get enhanced guild or convert from old format if needed"""
        from structure.enhanced_guild import EnhancedGuild

        # Try to get enhanced guild first
        enhanced_guild = await EnhancedGuild.get(guild_id)
        if enhanced_guild:
            return enhanced_guild

        # If not found, try to get old guild and convert
        old_guild = await Guild.get(guild_id)
        if old_guild:
            return await self.convert_to_enhanced_guild(old_guild)

        return None

    @guild_group.command(name="kick", help="Kick a member from your guild (owner only).")
    @app_commands.describe(user="The user to kick.", reason="The reason for kicking the user.")
    async def kick_member(self, ctx: commands.Context, user: discord.User, reason: str = None):
        player = await Player.get(ctx.author.id)
        if not player or not player.guild: await ctx.send(embed=discord.Embed(title="Error", description="You are not in a guild.", color=discord.Color.red())); return
        if player.trade: await ctx.send(embed=discord.Embed(title="Error", description="You are in a trade.", color=discord.Color.orange())); return

        guild = await Guild.get(player.guild)
        if not guild or guild.owner != ctx.author.id: await ctx.send(embed=discord.Embed(title="Error", description="You are not the owner.", color=discord.Color.red())); return
        if user.id == ctx.author.id: await ctx.send(embed=discord.Embed(title="Error", description="You cannot kick yourself.", color=discord.Color.red())); return

        members = await guild.get_members()
        if not any(m['id'] == user.id for m in members): await ctx.send(embed=discord.Embed(title="Error", description="User is not in your guild.", color=discord.Color.red())); return

        kicked_player = await Player.get(user.id)
        await guild.remove_member(user.id)
        if kicked_player:
            kicked_player.guild = None; await kicked_player.save()
            try:
                dm = f"You have been kicked from **{guild.name}**."
                if reason: dm += f"\n> Reason: \"{reason}\""
                await user.send(embed=discord.Embed(title="Kicked from Guild", description=dm, color=discord.Color.orange()))
            except discord.Forbidden: pass
        
        response = f"<@{user.id}> was kicked from '{guild.name}'."
        if reason: response += f"\n**Reason:** {reason}"
        await ctx.send(embed=discord.Embed(title="Success", description=response, color=discord.Color.green()))

    @commands.hybrid_command(name="guilds", help="Browse all guilds with modern interface.")
    async def view_guilds(self, ctx: commands.Context):
        """Browse guilds using the modern UI"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Import the new guild view and set to browse mode
        from commands.guild_new import GuildMainView

        view = GuildMainView(ctx, player)
        view.current_mode = "browse"
        view.update_buttons()
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @guild_group.command(name="delete", aliases=["remove"], help="Delete your guild (owner only).")
    async def delete_guild(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if player is None: await ctx.send(embed=discord.Embed(title="Error", description="You haven't started.", color=discord.Color.red())); return

        guild_id = player.guild
        is_admin = ctx.author.id == 1325220545439993888
        if not guild_id and not is_admin: await ctx.send(embed=discord.Embed(title="Error", description="You are not in a guild.", color=discord.Color.red())); return

        guild = await Guild.get(guild_id)
        if not guild: await ctx.send(embed=discord.Embed(title="Error", description="Guild not found.", color=discord.Color.red())); return
        if guild.owner != ctx.author.id and not is_admin: await ctx.send(embed=discord.Embed(title="Error", description="Only the guild owner can delete the guild.", color=discord.Color.red())); return
            
        members = await guild.get_members()
        for member_data in members:
            member_player = await Player.get(member_data['id'])
            if member_player: member_player.guild = None; await member_player.save()
        
        await guild.delete()
        await ctx.send(embed=discord.Embed(title="Success", description=f"The guild '{guild.name}' has been deleted.", color=discord.Color.green()))

    @guild_group.command(name="change_image", description="Change a guild's image (Admin only).")
    @app_commands.describe(guild_name="The name of the guild.", new_image_url="The new image URL for the guild.")
    async def change_guild_image(self, ctx: commands.Context, guild_name: str, new_image_url: str):
        if not ctx.author.guild_permissions.administrator and ctx.author.id != 1325220545439993888: await ctx.send(embed=discord.Embed(title="Error", description="You don't have permission.", color=discord.Color.red())); return
        guild_id = extractId(guild_name)
        guild = await Guild.get(guild_id)
        if not guild: await ctx.send(embed=discord.Embed(title="Error", description=f"Guild '{guild_name}' not found.", color=discord.Color.red())); return
        guild.image = new_image_url
        await guild.save()
        await ctx.send(embed=discord.Embed(title="Success", description=f"✅ Image for **{guild.name}** updated.", color=discord.Color.green()))



async def setup(bot):
    # Initialize enhanced guild database
    try:
        from structure.enhanced_guild import EnhancedGuild
        EnhancedGuild.initialize()
        print("✅ Enhanced Guild system initialized")
    except Exception as e:
        print(f"⚠️ Enhanced Guild initialization failed: {e}")
        print("🔄 Bot will continue with basic guild functionality")

    await bot.add_cog(GuildCommands(bot))