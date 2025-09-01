import discord
from discord.ext import commands
from discord import app_commands, ui
from typing import Optional

from structure.emoji import getEmoji
from structure.player import Player
from structure.items import ItemManager
from structure.heroes import HeroManager

class InventoryView(ui.View):
    """Beautiful inventory view matching profile.py style with functional buttons."""

    def __init__(self, author: discord.User, target: discord.User, player: Player, bot: commands.Bot):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
        self.player = player
        self.bot = bot
        self.current_view = "main"  # main, currencies, cubes, gear, shards

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command author can interact with this inventory"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This inventory doesn't belong to you!", ephemeral=True)
            return False
        return True

    def _disable_buttons_for_non_owner(self):
        """Disable buttons for users who don't own the inventory"""
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This inventory doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def get_main_inventory_embed(self):
        """Generate the main inventory overview embed"""
        player = await Player.get(self.target.id)  # Refresh player data

        embed = discord.Embed(
            title=f"🎒 {self.target.display_name}'s Inventory",
            description="Your complete collection of items and resources",
            color=discord.Color.dark_blue()
        )

        # Currency Overview with new emojis
        gold = getEmoji("gold")
        diamond = getEmoji("diamond")
        stone = getEmoji("stone")
        trace = getEmoji("trace")
        wallet = getEmoji("wallet")

        currency_text = (
            f"{wallet} **WALLET**\n"
            f"{gold} **Gold**: `{player.gold:,}`\n"
            f"{diamond} **Diamonds**: `{player.diamond:,}`\n"
            f"{stone} **Stones**: `{player.stone:,}`\n"
            f"{trace} **Shadow Traces**: `{player.tos:,}`"
        )
        embed.add_field(name="💰 Currencies", value=currency_text, inline=False)

        # Keys & Tickets
        tickets = player.ticket
        keys = player.key

        keys_text = (
            f"{getEmoji('ticket')} **Gacha Tickets**: `{tickets:,}`\n"
            f"{getEmoji('gate_key')} **Gate Keys**: `{keys:,}`"
        )
        embed.add_field(name="🗝️ Keys & Tickets", value=keys_text, inline=False)

        # Elemental Cubes Summary
        wcube = player.wcube
        fcube = player.fcube
        lcube = player.lcube
        dcube = player.dcube
        icube = player.icube
        ecube = player.ecube
        total_cubes = wcube + fcube + lcube + dcube + icube + ecube

        cubes_text = (
            f"{getEmoji('wcube')} Wind: `{wcube:,}` | {getEmoji('fcube')} Fire: `{fcube:,}`\n"
            f"{getEmoji('lcube')} Light: `{lcube:,}` | {getEmoji('dcube')} Dark: `{dcube:,}`\n"
            f"{getEmoji('icube')} Water: `{icube:,}` | {getEmoji('ecube')} Earth: `{ecube:,}`\n"
            f"**Total Cubes**: `{total_cubes:,}`"
        )
        embed.add_field(name="🧊 Melding Cubes", value=cubes_text, inline=False)

        # Enhancement Gear Summary
        gear1 = player.gear1
        gear2 = player.gear2
        gear3 = player.gear3
        total_gear = gear1 + gear2 + gear3

        gear_text = (
            f"{getEmoji('gear1')} **Tier I**: `{gear1:,}`\n"
            f"{getEmoji('gear2')} **Tier II**: `{gear2:,}`\n"
            f"{getEmoji('gear3')} **Tier III**: `{gear3:,}`\n"
            f"**Total Gear**: `{total_gear:,}`"
        )
        embed.add_field(name="⚙️ Enhancement Gear", value=gear_text, inline=False)

        # Shards Summary
        shard_count = 0
        ssr_count = 0
        sr_count = 0
        rare_count = 0

        for item_id, data in player.get_inventory().items():
            if item_id.startswith('s_'):
                shard_quantity = 0
                if isinstance(data, dict):
                    shard_quantity = data.get('quantity', data.get('level', 0))
                elif isinstance(data, int):
                    shard_quantity = data

                if shard_quantity > 0:
                    shard_count += shard_quantity
                    # Get item rarity for counting
                    try:
                        original_item_id = item_id[2:]
                        # Try ItemManager first (weapons)
                        item = await ItemManager.get(original_item_id)
                        if not item:
                            # Try HeroManager (hunters)
                            item = await HeroManager.get(original_item_id)

                        if item and hasattr(item, 'rarity'):
                            rarity = item.rarity.lower()
                            if rarity == 'ssr':
                                ssr_count += shard_quantity
                            elif rarity in ['sr', 'super rare']:
                                sr_count += shard_quantity
                            elif rarity == 'rare':
                                rare_count += shard_quantity
                    except:
                        # Silently skip items that can't be processed
                        pass

        shards_text = (
            f"💎 **Total Shards**: `{shard_count:,}`\n"
            f"{getEmoji('SSR')} SSR: `{ssr_count:,}` | {getEmoji('SR')} SR: `{sr_count:,}` | {getEmoji('rare')} Rare: `{rare_count:,}`"
        )
        embed.add_field(name="💎 Hunter & Weapon Shards", value=shards_text, inline=False)

        embed.set_thumbnail(url=self.target.display_avatar.url)
        embed.set_footer(text="Use the buttons below to explore different sections")
        return embed

    @ui.button(label="Shop", style=discord.ButtonStyle.success, emoji="🛒")
    async def open_shop(self, interaction: discord.Interaction, button: ui.Button):
        """Open the shop menu for the user"""
        if self.author.id != self.target.id:
            await interaction.response.send_message("You can only access your own shop!", ephemeral=True)
            return

        await interaction.response.defer()

        # Get shop cog and run shops command to show available shops
        shop_cog = self.bot.get_cog("ShopCommands")
        if shop_cog:
            # Create a simple fake context
            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'bot': self.bot
            })()

            await shop_cog.view_shops(fake_ctx)
        else:
            await interaction.followup.send("🛒 **Shop system not available right now.**", ephemeral=True)

    @ui.button(label="Enhance Gear", style=discord.ButtonStyle.primary, emoji="⚙️")
    async def enhance_gear(self, interaction: discord.Interaction, button: ui.Button):
        """Open the upgrade menu for the user"""
        if self.author.id != self.target.id:
            await interaction.response.send_message("You can only enhance your own gear!", ephemeral=True)
            return

        await interaction.response.defer()

        # Get upgrade cog and run upgrade command
        upgrade_cog = self.bot.get_cog("UpgradeCog")
        if upgrade_cog:
            # Create a simple fake context
            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'reply': interaction.followup.send,
                'bot': self.bot
            })()

            await upgrade_cog.upgrade(fake_ctx)
        else:
            await interaction.followup.send("⚙️ **Upgrade system not available right now.**", ephemeral=True)

    @ui.button(label="View Shards", style=discord.ButtonStyle.secondary, emoji="💎")
    async def view_shards(self, interaction: discord.Interaction, button: ui.Button):
        """Show the shards menu for the user"""
        await interaction.response.defer()

        # Get shards cog and run shards command
        shards_cog = self.bot.get_cog("ShardsCommand")
        if shards_cog:
            # Create a simple fake context
            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'reply': interaction.followup.send,
                'bot': self.bot
            })()

            await shards_cog.shards(fake_ctx)
        else:
            await interaction.followup.send("💎 **Shards system not available right now.**", ephemeral=True)

    # Sacrifice button removed - use 'sl sacrifice' command instead

    @ui.button(label="◀️ Back to Balance", style=discord.ButtonStyle.gray, row=1)
    async def back_to_balance(self, interaction: discord.Interaction, button: ui.Button):
        """Return to the balance view"""
        await interaction.response.send_message("◀️ **Use `/bal` to view your balance!**", ephemeral=True)

class InventoryButtons(ui.View):
    """Simple buttons for balance command"""

    def __init__(self, user_id: int, bot=None):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ These buttons are not for you!", ephemeral=True)
            return False
        return True

    @ui.button(label="Full Inventory", style=discord.ButtonStyle.primary, emoji="🎒")
    async def view_inventory_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show the full inventory."""
        await interaction.response.defer()

        # Get inventory cog and run inventory command
        inventory_cog = self.bot.get_cog("Inventory")
        if inventory_cog:
            # Create a simple fake context with proper reply method
            async def safe_reply(*args, embed=None, view=None, mention_author=None, **kwargs):
                # Handle both positional and keyword arguments
                # Remove mention_author since followup doesn't support it
                if args:
                    # If called with positional arguments, treat first as embed
                    if len(args) > 0 and embed is None:
                        embed = args[0]
                    if len(args) > 1 and view is None:
                        view = args[1]
                return await interaction.followup.send(embed=embed, view=view, **kwargs)

            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'reply': safe_reply,
                'bot': self.bot
            })()

            await inventory_cog.view_inventory(fake_ctx)
        else:
            await interaction.followup.send("🎒 **Inventory system not available right now.**", ephemeral=True)

    @ui.button(label="Shop", style=discord.ButtonStyle.success, emoji="🛒")
    async def open_shop(self, interaction: discord.Interaction, button: ui.Button):
        """Open the shop."""
        await interaction.response.defer()

        # Get shop cog and run shops command
        shop_cog = self.bot.get_cog("ShopCommands")
        if shop_cog:
            # Create a simple fake context with safe reply method
            async def safe_reply(*args, embed=None, view=None, mention_author=None, **kwargs):
                # Handle both positional and keyword arguments
                if args:
                    if len(args) > 0 and embed is None:
                        embed = args[0]
                    if len(args) > 1 and view is None:
                        view = args[1]
                return await interaction.followup.send(embed=embed, view=view, **kwargs)

            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'reply': safe_reply,
                'bot': self.bot
            })()

            await shop_cog.view_shops(fake_ctx)
        else:
            await interaction.followup.send("🛒 **Shop system not available right now.**", ephemeral=True)

    @ui.button(label="Enhance Gear", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def enhance_gear(self, interaction: discord.Interaction, button: ui.Button):
        """Open the upgrade menu."""
        await interaction.response.defer()

        # Get upgrade cog and run upgrade command
        upgrade_cog = self.bot.get_cog("UpgradeCog")
        if upgrade_cog:
            # Create a simple fake context with safe reply method
            async def safe_reply(*args, embed=None, view=None, mention_author=None, **kwargs):
                # Handle both positional and keyword arguments
                if args:
                    if len(args) > 0 and embed is None:
                        embed = args[0]
                    if len(args) > 1 and view is None:
                        view = args[1]
                return await interaction.followup.send(embed=embed, view=view, **kwargs)

            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'reply': safe_reply,
                'bot': self.bot
            })()

            await upgrade_cog.upgrade(fake_ctx)
        else:
            await interaction.followup.send("⚙️ **Upgrade system not available right now.**", ephemeral=True)

    @ui.button(label="View Shards", style=discord.ButtonStyle.secondary, emoji="💎")
    async def view_shards(self, interaction: discord.Interaction, button: ui.Button):
        """View all shards."""
        await interaction.response.defer()

        # Get shards cog and run shards command
        shards_cog = self.bot.get_cog("ShardsCommand")
        if shards_cog:
            # Create a simple fake context with safe reply method
            async def safe_reply(*args, embed=None, view=None, mention_author=None, **kwargs):
                # Handle both positional and keyword arguments
                if args:
                    if len(args) > 0 and embed is None:
                        embed = args[0]
                    if len(args) > 1 and view is None:
                        view = args[1]
                return await interaction.followup.send(embed=embed, view=view, **kwargs)

            fake_ctx = type('Context', (), {
                'author': interaction.user,
                'channel': interaction.channel,
                'guild': interaction.guild,
                'send': interaction.followup.send,
                'reply': safe_reply,
                'bot': self.bot
            })()

            await shards_cog.shards(fake_ctx)
        else:
            await interaction.followup.send("💎 **Shards system not available right now.**", ephemeral=True)

class Inventory(commands.Cog):
    """Cog for managing and displaying player inventories and balances."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="bal", aliases=["balance", "wallet", "wal"], help="Check your or another user's balance.")
    @app_commands.describe(user="The user whose balance you want to see.")
    async def view_balance(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Displays the player's currency balance with interactive buttons."""

        target_user = user or ctx.author
        player = await Player.get(target_user.id)

        if not player:
            embed = discord.Embed(
                title="🚫 Profile Not Found",
                description=f"**{target_user.display_name}** hasn't started their journey yet!\nUse `/start` to begin your adventure.",
                color=0xFF4757
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1325516643262009394.png")
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Get currency emojis
        gold = getEmoji("gold")
        diamond = getEmoji("diamond")
        stone = getEmoji("stone")
        trace = getEmoji("trace")
        wallet = getEmoji("wallet")

        # Create balance embed matching your format
        embed = discord.Embed(color=0x2F3136)
        embed.set_author(
            name=f"{wallet} {target_user.display_name} [BALANCE]",
            icon_url=target_user.display_avatar.url
        )

        # Format exactly like your example
        embed.description = (
            f"{gold} **Gold**: x{player.gold:,}\n"
            f"{diamond} **Diamonds**: x{player.diamond:,}\n"
            f"{stone} **Stones**: x{player.stone:,}\n"
            f"{trace} **Shadow Traces**: x{player.tos:,}"
        )

        embed.set_thumbnail(url=target_user.display_avatar.url)

        # Add interactive buttons (only for the command issuer)
        view = InventoryButtons(ctx.author.id, self.bot)

        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.hybrid_command(name="inventory", aliases=["inv"], help="Check your or another user's full inventory.")
    @app_commands.describe(user="The user whose inventory you want to see.")
    async def view_inventory(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Displays the player's full item inventory with beautiful UI and functional buttons."""

        target_user = user or ctx.author
        player = await Player.get(target_user.id)

        if not player:
            down = getEmoji("down")
            embed = discord.Embed(
                title="Profile Not Found",
                description=f"**{target_user.display_name}** hasn't started the bot yet.",
                color=discord.Color.red()
            )
            if not user:
                embed.description += f"\n{down} Use `sl start` to get Re-Awakened"
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create the beautiful inventory view matching profile.py style
        view = InventoryView(ctx.author, target_user, player, self.bot)

        # Disable buttons for non-owners after view is fully constructed
        if ctx.author.id != target_user.id:
            view._disable_buttons_for_non_owner()

        embed = await view.get_main_inventory_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot: commands.Bot):
    """Sets up the cog and adds it to the bot."""
    await bot.add_cog(Inventory(bot))