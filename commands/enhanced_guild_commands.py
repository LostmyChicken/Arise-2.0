"""
Enhanced Guild Commands with Vice Masters and Advanced Features
"""
import discord
from discord.ext import commands
from discord import app_commands
from structure.enhanced_guild import EnhancedGuild, GuildRole, GuildPermission
from structure.player import Player
from commands.enhanced_guild_ui import EnhancedGuildMainView
from commands.guild_creation import GuildCreationView, GuildBrowserView
from utilis.utilis import extractId
from structure.emoji import getEmoji

class EnhancedGuildCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="eguild", invoke_without_command=True, help="Enhanced guild system with advanced features")
    async def enhanced_guild(self, ctx: commands.Context):
        """Enhanced guild interface with roles and permissions"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        view = EnhancedGuildMainView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @enhanced_guild.command(name="create", help="Create a new guild with advanced features and customization")
    async def create_guild(self, ctx: commands.Context):
        """Create a new enhanced guild with full customization"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Check if player is already in a guild
        if player.guild:
            embed = discord.Embed(
                title="❌ Already in Guild",
                description="You're already a member of a guild. Leave your current guild first to create a new one.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create guild creation view
        view = GuildCreationView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @enhanced_guild.command(name="browse", help="Browse and search for guilds to join with advanced filters")
    async def browse_guilds(self, ctx: commands.Context):
        """Browse available guilds with filtering options"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create guild browser view with integrated guild system
        view = GuildBrowserView(ctx, player)
        await view.load_guilds()
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @enhanced_guild.command(name="promote", help="Promote a guild member to a higher role")
    @app_commands.describe(user="The user to promote", role="The role to promote them to")
    @app_commands.choices(role=[
        app_commands.Choice(name="Officer", value="officer"),
        app_commands.Choice(name="Vice Master", value="vice_master")
    ])
    async def promote_member(self, ctx: commands.Context, user: discord.User, role: str):
        """Promote a guild member"""
        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await EnhancedGuild.get(player.guild)
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

    @enhanced_guild.command(name="demote", help="Demote a guild member to a lower role")
    @app_commands.describe(user="The user to demote")
    async def demote_member(self, ctx: commands.Context, user: discord.User):
        """Demote a guild member"""
        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await EnhancedGuild.get(player.guild)
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

    @enhanced_guild.command(name="kick", help="Kick a member from the guild")
    @app_commands.describe(user="The user to kick", reason="Reason for kicking")
    async def kick_member(self, ctx: commands.Context, user: discord.User, reason: str = "No reason provided"):
        """Kick a member from the guild"""
        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await EnhancedGuild.get(player.guild)
        if not guild:
            await ctx.reply("❌ Guild not found!", ephemeral=True)
            return

        # Check permissions
        if not guild.has_permission(ctx.author.id, GuildPermission.KICK_MEMBERS):
            await ctx.reply("❌ You don't have permission to kick members!", ephemeral=True)
            return

        # Check if target is a member
        if not guild.is_member(user.id):
            await ctx.reply("❌ That user is not a member of your guild!", ephemeral=True)
            return

        # Can't kick guild master
        if user.id == guild.owner:
            await ctx.reply("❌ You can't kick the Guild Master!", ephemeral=True)
            return

        # Remove from guild
        success = await guild.remove_member(user.id)
        if success:
            # Update player's guild status
            kicked_player = await Player.get(user.id)
            if kicked_player:
                kicked_player.guild = None
                await kicked_player.save()

            embed = discord.Embed(
                title="🦵 Member Kicked",
                description=f"{user.mention} has been kicked from **{guild.name}**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Kicked by", value=ctx.author.mention, inline=False)
            
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("❌ Failed to kick member!", ephemeral=True)

    @enhanced_guild.command(name="invite", help="Invite a player to join your guild")
    @app_commands.describe(user="The user to invite")
    async def invite_member(self, ctx: commands.Context, user: discord.User):
        """Invite a player to the guild"""
        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await EnhancedGuild.get(player.guild)
        if not guild:
            await ctx.reply("❌ Guild not found!", ephemeral=True)
            return

        # Check permissions
        if not guild.has_permission(ctx.author.id, GuildPermission.INVITE_MEMBERS):
            await ctx.reply("❌ You don't have permission to invite members!", ephemeral=True)
            return

        # Check if target player exists
        target_player = await Player.get(user.id)
        if not target_player:
            await ctx.reply("❌ That player hasn't started their adventure yet!", ephemeral=True)
            return

        # Check if already in a guild
        if target_player.guild:
            await ctx.reply("❌ That player is already in a guild!", ephemeral=True)
            return

        # Check guild capacity
        total_members = len(guild.members) + 1  # +1 for owner
        if total_members >= guild.settings.get("max_members", 50):
            await ctx.reply("❌ Your guild is full!", ephemeral=True)
            return

        # Check level requirement
        min_level = guild.settings.get("min_level_requirement", 1)
        if target_player.level < min_level:
            await ctx.reply(f"❌ That player needs to be level {min_level} or higher!", ephemeral=True)
            return

        # Create invite embed
        embed = discord.Embed(
            title="🏰 Guild Invitation",
            description=f"{user.mention}, you've been invited to join **{guild.name}**!",
            color=discord.Color.blue()
        )

        tier, _ = guild.get_guild_tier()
        embed.add_field(
            name="🏛️ Guild Info",
            value=(
                f"**Name**: {guild.name}\n"
                f"**Tier**: {tier}\n"
                f"**Level**: {guild.level}\n"
                f"**Members**: {total_members}/{guild.settings.get('max_members', 50)}\n"
                f"**Points**: {guild.points:,}"
            ),
            inline=False
        )

        embed.add_field(
            name="📝 Description",
            value=guild.description,
            inline=False
        )

        embed.add_field(
            name="👤 Invited by",
            value=ctx.author.mention,
            inline=False
        )

        # Create accept/decline view
        view = GuildInviteView(guild, target_player, ctx.author)
        await ctx.reply(embed=embed, view=view)

    @enhanced_guild.command(name="bank", help="View or manage guild bank")
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
        player = await Player.get(ctx.author.id)
        if not player or not player.guild:
            await ctx.reply("❌ You're not in a guild!", ephemeral=True)
            return

        guild = await EnhancedGuild.get(player.guild)
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


class GuildInviteView(discord.ui.View):
    def __init__(self, guild: EnhancedGuild, target_player: Player, inviter: discord.User):
        super().__init__(timeout=300)
        self.guild = guild
        self.target_player = target_player
        self.inviter = inviter

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target_player.id:
            await interaction.response.send_message("❌ Only the invited player can respond to this invitation!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Add player to guild
        success = await self.guild.add_member(self.target_player.id)
        if success:
            self.target_player.guild = self.guild.id
            await self.target_player.save()

            embed = discord.Embed(
                title="🎉 Welcome to the Guild!",
                description=f"You've successfully joined **{self.guild.name}**!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🏰 Your New Guild",
                value=(
                    f"**Name**: {self.guild.name}\n"
                    f"**Role**: {self.guild.get_role_display_name('member')}\n"
                    f"**Members**: {len(self.guild.members)}/{self.guild.settings.get('max_members', 50)}"
                ),
                inline=False
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Join",
                description="Could not join the guild. It may be full or you may already be in a guild.",
                color=discord.Color.red()
            )

        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="❌ Invitation Declined",
            description=f"You declined the invitation to join **{self.guild.name}**.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)


async def setup(bot):
    await bot.add_cog(EnhancedGuildCommands(bot))
