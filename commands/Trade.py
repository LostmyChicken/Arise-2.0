import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, Any

from utilis.utilis import extractId
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.emoji import getEmoji
from structure.player import Player

# --- Constants ---
TRADE_TIMEOUT = 300.0  # 5 minutes for a trade to complete
REQUEST_TIMEOUT = 60.0 # 1 minute for the initial request

# --- Helper Functions ---
async def get_item_name(item_type: str, item_id: str) -> str:
    """Gets the display name for a given item ID and type."""
    if item_type == "weapon":
        item = await ItemManager.get(item_id)
        return item.name if item else "Unknown Weapon"
    elif item_type == "hunter":
        item = await HeroManager.get(item_id)
        return item.name if item else "Unknown Hunter"
    return item_id.replace("_", " ").title()

# --- Trade Session State Management ---
class TradeSession:
    """Manages the state of a single trade instance."""
    def __init__(self, sender: Player, receiver: Player, sender_user: discord.User, receiver_user: discord.User):
        self.sender = sender
        self.receiver = receiver
        self.sender_user = sender_user
        self.receiver_user = receiver_user
        
        self.sender_offer: Dict[str, Dict[str, int]] = {"currency": {}, "items": {}, "weapon": {}, "hunter": {}}
        self.receiver_offer: Dict[str, Dict[str, int]] = {"currency": {}, "items": {}, "weapon": {}, "hunter": {}}
        
        self.sender_locked = False
        self.receiver_locked = False
        self.message: Optional[discord.WebhookMessage] = None

    def is_trade_locked(self) -> bool:
        return self.sender_locked and self.receiver_locked

    def lock_user(self, user_id: int):
        if user_id == self.sender.id:
            self.sender_locked = True
        elif user_id == self.receiver.id:
            self.receiver_locked = True

    async def add_item(self, user_id: int, item_type: str, item_id: str, quantity: int):
        # Get the player making the offer
        player = self.sender if user_id == self.sender.id else self.receiver
        offer = self.sender_offer if user_id == self.sender.id else self.receiver_offer

        # Validate the player can actually offer this item
        if item_type == "currency":
            current_amount = getattr(player, item_id, 0)
            # Check if they have enough including what's already offered
            already_offered = offer[item_type].get(item_id, 0)
            if current_amount < (already_offered + quantity):
                raise ValueError(f"Not enough {item_id}. Have: {current_amount}, Trying to offer: {already_offered + quantity}")
        elif item_type in ["items", "weapon"]:
            inventory = player.get_inventory()
            if item_id not in inventory:
                raise ValueError(f"Player doesn't own item: {item_id}")
            # For items, we can only trade 1 (the item itself)
            if offer[item_type].get(item_id, 0) + quantity > 1:
                raise ValueError(f"Can only trade 1 of item: {item_id}")
        elif item_type == "hunter":
            hunters = player.get_hunters()
            if item_id not in hunters:
                raise ValueError(f"Player doesn't own hunter: {item_id}")
            # For hunters, we can only trade 1 (the hunter itself)
            if offer[item_type].get(item_id, 0) + quantity > 1:
                raise ValueError(f"Can only trade 1 of hunter: {item_id}")

        # Add to offer if validation passes
        offer[item_type][item_id] = offer[item_type].get(item_id, 0) + quantity
        await self.update_message()

    async def update_message(self):
        if self.message:
            embed = await self.generate_embed()
            await self.message.edit(embed=embed)

    async def generate_embed(self) -> discord.Embed:
        """Generates an embed showing the current state of the trade."""
        embed = discord.Embed(title="Trade in Progress", color=discord.Color.blue())
        embed.description = "**Note:** Cross-trading or using alternate accounts is strictly prohibited and will result in a ban."

        async def format_offer(offer: Dict[str, Dict[str, int]], is_locked: bool) -> str:
            if not any(offer.values()):
                return "```diff\n- Nothing offered yet. -\n```"
            
            status = "+ Ready +" if is_locked else "- Not Ready -"
            lines = [f"```diff\n{status}"]
            
            for category, items in offer.items():
                if items:
                    lines.append(f"# {category.capitalize()}")
                    for item_id, quantity in items.items():
                        name = await get_item_name(category, item_id)
                        lines.append(f"+ {name}: x{quantity}")
            lines.append("```")
            return "\n".join(lines)

        sender_name = f"{'🔒 ' if self.sender_locked else ''}{self.sender_user.display_name}"
        receiver_name = f"{'🔒 ' if self.receiver_locked else ''}{self.receiver_user.display_name}"

        embed.add_field(name=f"{sender_name}'s Offer", value=await format_offer(self.sender_offer, self.sender_locked), inline=True)
        embed.add_field(name=f"{receiver_name}'s Offer", value=await format_offer(self.receiver_offer, self.receiver_locked), inline=True)
        embed.set_footer(text="Use the menus below to add items or manage the trade.")
        return embed

# --- Trade Execution Logic ---
class TradeExecutor:
    """Handles the final execution of a confirmed trade."""
    def __init__(self, session: TradeSession):
        self.session = session

    async def execute(self) -> str:
        if not self.session.is_trade_locked():
            return "Both users must lock the trade before it can be executed."
        if not self.session.sender_offer and not self.session.receiver_offer:
            return "Both users must offer at least one item."

        try:
            # Exchange items from sender to receiver
            await self._exchange_items(self.session.sender_offer, self.session.sender, self.session.receiver)
            # Exchange items from receiver to sender
            await self._exchange_items(self.session.receiver_offer, self.session.receiver, self.session.sender)
            
            await self._finalize_trade_status()
            return "Trade completed successfully."
        except Exception as e:
            await self._finalize_trade_status()
            return f"An error occurred during the trade: {e}"

    async def _exchange_items(self, offer: Dict[str, Dict[str, int]], from_player: Player, to_player: Player):
        for category, items in offer.items():
            for item_id, quantity in items.items():
                # For items and hunters, preserve the original stats
                if category in ["items", "weapon", "hunter"]:
                    await self._transfer_item_with_stats(from_player, to_player, category, item_id)
                else:
                    # For currency, just transfer the amount
                    await self._update_inventory(to_player, category, item_id, quantity)
                    await self._update_inventory(from_player, category, item_id, -quantity)

    async def _transfer_item_with_stats(self, from_player: Player, to_player: Player, category: str, item_id: str):
        """Transfer an item/hunter with its original stats preserved"""
        if category in ["items", "weapon"]:
            from_inventory = from_player.get_inventory()
            to_inventory = to_player.get_inventory()

            if item_id in from_inventory:
                item_data = from_inventory[item_id].copy()  # Preserve original stats

                # Add to receiver
                if item_id in to_inventory:
                    # Already exists, convert to shards
                    shard_id = f"s_{item_id}"
                    to_inventory[shard_id] = to_inventory.get(shard_id, 0) + 1
                else:
                    # Transfer with original stats
                    to_inventory[item_id] = item_data

                # Remove from sender
                del from_inventory[item_id]

        elif category == "hunter":
            from_hunters = from_player.get_hunters()
            to_hunters = to_player.get_hunters()

            if item_id in from_hunters:
                hunter_data = from_hunters[item_id].copy()  # Preserve original stats

                # Add to receiver
                if item_id in to_hunters:
                    # Already exists, convert to shards
                    shard_id = f"s_{item_id}"
                    to_inventory = to_player.get_inventory()
                    to_inventory[shard_id] = to_inventory.get(shard_id, 0) + 1
                else:
                    # Transfer with original stats
                    to_hunters[item_id] = hunter_data

                # Remove from sender
                del from_hunters[item_id]

    async def _update_inventory(self, player: Player, category: str, item_id: str, quantity: int):
        if category == "currency":
            # Handle currency items (gold, diamond, etc.)
            if hasattr(player, item_id):
                current_val = getattr(player, item_id, 0)
                new_val = max(0, current_val + quantity)
                setattr(player, item_id, new_val)
        elif category in ["items", "weapon"]:
            # Handle regular items in inventory
            inventory = player.get_inventory()
            if quantity > 0:  # Adding items
                if item_id in inventory:
                    # Item already exists, convert to shards
                    shard_id = f"s_{item_id}"
                    inventory[shard_id] = inventory.get(shard_id, 0) + 1  # Always add 1 shard for duplicate
                else:
                    # Get the original item data to preserve stats
                    from_player_inventory = None
                    # We need to get the item data from the sender
                    # For now, create with base stats
                    inventory[item_id] = {'level': 1, 'tier': 1, 'xp': 0}
            else:  # Removing items (quantity is negative)
                if item_id in inventory:
                    del inventory[item_id]
        elif category == "hunter":
            # Handle hunters
            hunters = player.get_hunters()
            if quantity > 0:  # Adding hunters
                if item_id in hunters:
                    # Hunter already exists, convert to shards
                    shard_id = f"s_{item_id}"
                    inventory = player.get_inventory()
                    inventory[shard_id] = inventory.get(shard_id, 0) + 1  # Always add 1 shard for duplicate
                else:
                    # Add new hunter with base stats
                    hunters[item_id] = {'level': 1, 'tier': 1, 'xp': 0}
            else:  # Removing hunters (quantity is negative)
                if item_id in hunters:
                    del hunters[item_id]
        await player.save()

    async def _finalize_trade_status(self):
        self.session.sender.trade = False
        self.session.receiver.trade = False
        await self.session.sender.save()
        await self.session.receiver.save()

# --- UI Components (Views, Modals) ---

class AddItemModal(discord.ui.Modal):
    """A generic modal for adding items or currency to a trade."""
    item_name = discord.ui.TextInput(label="Item/Currency Name", placeholder="e.g., Gold, Diamond, Kim Chul, etc.", required=True)
    quantity = discord.ui.TextInput(label="Quantity", placeholder="Enter the amount to trade", required=True)

    def __init__(self, title: str, category: str, trade_session: TradeSession):
        super().__init__(title=title)
        self.category = category
        self.trade_session = trade_session

    async def on_submit(self, interaction: discord.Interaction):
        # Basic validation
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                await interaction.response.send_message("Quantity must be a positive number.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Invalid quantity. Please enter a number.", ephemeral=True)
            return

        # Get the player making the trade
        player = await Player.get(interaction.user.id)
        if not player:
            await interaction.response.send_message("Player not found.", ephemeral=True)
            return

        # Validate item based on category
        item_name = self.item_name.value.strip()
        item_id = extractId(item_name)

        if self.category == "currency":
            # Validate currency type
            valid_currencies = ["gold", "diamond", "stone", "ticket", "crystals", "fcube", "icube", "wcube", "dcube", "lcube", "tos", "gear1", "gear2", "gear3", "key"]
            if item_id not in valid_currencies:
                await interaction.response.send_message(f"Invalid currency: {item_name}. Valid currencies: {', '.join(valid_currencies)}", ephemeral=True)
                return

            # Check if player has enough currency
            current_amount = getattr(player, item_id, 0)
            if current_amount < qty:
                await interaction.response.send_message(f"You don't have enough {item_name}. You have {current_amount}, need {qty}.", ephemeral=True)
                return

        elif self.category in ["items", "weapon"]:
            # Validate item exists in database
            item_data = await ItemManager.get(item_id)
            if not item_data:
                await interaction.response.send_message(f"Item '{item_name}' not found in database.", ephemeral=True)
                return

            # Check if player owns this item
            inventory = player.get_inventory()
            if item_id not in inventory:
                await interaction.response.send_message(f"You don't own the item '{item_name}'.", ephemeral=True)
                return

        elif self.category == "hunter":
            # Validate hunter exists in database
            hunter_data = await HeroManager.get(item_id)
            if not hunter_data:
                await interaction.response.send_message(f"Hunter '{item_name}' not found in database.", ephemeral=True)
                return

            # Check if player owns this hunter
            hunters = player.get_hunters()
            if item_id not in hunters:
                await interaction.response.send_message(f"You don't own the hunter '{item_name}'.", ephemeral=True)
                return

        # Add item to trade offer with error handling
        try:
            await self.trade_session.add_item(interaction.user.id, self.category, item_id, qty)

            # Check if interaction is still valid before responding
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Added `x{qty}` of `{item_name}` to your offer.", ephemeral=True)
            else:
                # Interaction already responded to, use followup
                await interaction.followup.send(f"Added `x{qty}` of `{item_name}` to your offer.", ephemeral=True)

        except ValueError as e:
            # Handle trade validation errors gracefully
            error_message = str(e)
            response_text = ""

            if "Can only trade 1 of hunter" in error_message:
                response_text = f"❌ You can only trade 1 of each hunter. You already have `{item_name}` in your offer."
            elif "Can only trade 1 of item" in error_message:
                response_text = f"❌ You can only trade 1 of `{item_name}`. You already have it in your offer."
            elif "doesn't own" in error_message:
                response_text = f"❌ You don't own `{item_name}` to trade."
            else:
                response_text = f"❌ Cannot add item to trade: {error_message}"

            # Safe response handling
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(response_text, ephemeral=True)
                else:
                    await interaction.followup.send(response_text, ephemeral=True)
            except discord.NotFound:
                # Interaction expired, ignore
                pass
            except Exception as response_error:
                print(f"Error responding to trade interaction: {response_error}")

        except Exception as e:
            # Handle any other unexpected errors
            error_text = f"❌ An error occurred while adding the item: {str(e)}"
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(error_text, ephemeral=True)
                else:
                    await interaction.followup.send(error_text, ephemeral=True)
            except discord.NotFound:
                # Interaction expired, ignore
                pass
            except Exception as response_error:
                print(f"Error responding to trade interaction: {response_error}")

class TradeControlView(discord.ui.View):
    """The main view for controlling an active trade."""
    def __init__(self, trade_session: TradeSession):
        super().__init__(timeout=TRADE_TIMEOUT)
        self.trade_session = trade_session

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in [self.trade_session.sender.id, self.trade_session.receiver.id]:
            await interaction.response.send_message("You are not part of this trade.", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="Select a category to add items...",
        options=[
            discord.SelectOption(label="Currency", emoji="💰"),
            discord.SelectOption(label="Misc Items", emoji="📦"),
            discord.SelectOption(label="Weapon Shards", emoji="⚔️"),
            discord.SelectOption(label="Hunter Shards", emoji="🏹"),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category_map = {
            "Currency": "currency",
            "Misc Items": "items",
            "Weapon Shards": "weapon",
            "Hunter Shards": "hunter",
        }
        category = category_map[select.values[0]]
        modal = AddItemModal(title=f"Add {select.values[0]}", category=category, trade_session=self.trade_session)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Lock Offer", style=discord.ButtonStyle.primary, emoji="🔒", row=1)
    async def lock_offer(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Validate the user's offer before locking
        try:
            await self._validate_user_offer(interaction.user.id)
        except ValueError as e:
            await interaction.response.send_message(f"❌ Cannot lock offer: {str(e)}", ephemeral=True)
            return

        self.trade_session.lock_user(interaction.user.id)
        await self.trade_session.update_message()

        if self.trade_session.is_trade_locked():
            executor = TradeExecutor(self.trade_session)
            result = await executor.execute()

            final_embed = await self.trade_session.generate_embed()
            final_embed.title = "Trade Finalized"
            final_embed.color = discord.Color.green() if "successfully" in result else discord.Color.red()
            final_embed.description = result

            await interaction.message.edit(embed=final_embed, view=None)
            self.stop()
        else:
            await interaction.response.defer()

    async def _validate_user_offer(self, user_id: int):
        """Validate that the user actually owns all items they're offering"""
        player = self.trade_session.sender if user_id == self.trade_session.sender.id else self.trade_session.receiver
        offer = self.trade_session.sender_offer if user_id == self.trade_session.sender.id else self.trade_session.receiver_offer

        for category, items in offer.items():
            for item_id, quantity in items.items():
                if category == "currency":
                    current_amount = getattr(player, item_id, 0)
                    if current_amount < quantity:
                        raise ValueError(f"Not enough {item_id}. Have: {current_amount}, Offering: {quantity}")
                elif category in ["items", "weapon"]:
                    inventory = player.get_inventory()
                    if item_id not in inventory:
                        raise ValueError(f"You don't own item: {item_id}")
                elif category == "hunter":
                    hunters = player.get_hunters()
                    if item_id not in hunters:
                        raise ValueError(f"You don't own hunter: {item_id}")

    @discord.ui.button(label="Cancel Trade", style=discord.ButtonStyle.danger, emoji="✖️", row=1)
    async def cancel_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        executor = TradeExecutor(self.trade_session)
        await executor._finalize_trade_status()
        
        embed = await self.trade_session.generate_embed()
        embed.title = "Trade Canceled"
        embed.description = f"The trade was canceled by {interaction.user.mention}."
        embed.color = discord.Color.red()
        
        await interaction.message.edit(embed=embed, view=None)
        self.stop()

    async def on_timeout(self):
        executor = TradeExecutor(self.trade_session)
        await executor._finalize_trade_status()
        if self.trade_session.message:
            embed = discord.Embed(title="Trade Timed Out", description="The trade was canceled due to inactivity.", color=discord.Color.orange())
            await self.trade_session.message.edit(embed=embed, view=None)

class TradeRequestView(discord.ui.View):
    """View for the trade recipient to accept or decline."""
    def __init__(self, trade_session: TradeSession):
        super().__init__(timeout=REQUEST_TIMEOUT)
        self.trade_session = trade_session

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.trade_session.receiver.id:
            await interaction.response.send_message("You are not the recipient of this trade request.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.trade_session.receiver.trade = True
        await self.trade_session.receiver.save()
        
        embed = await self.trade_session.generate_embed()
        view = TradeControlView(self.trade_session)
        await interaction.response.edit_message(content=None, embed=embed, view=view)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.trade_session.sender.trade = False
        await self.trade_session.sender.save()
        
        embed = discord.Embed(title="Trade Declined", description=f"{self.trade_session.receiver_user.mention} has declined the trade request.", color=discord.Color.red())
        await interaction.response.edit_message(content=None, embed=embed, view=None)
        self.stop()

    async def on_timeout(self):
        self.trade_session.sender.trade = False
        await self.trade_session.sender.save()
        if self.trade_session.message:
            embed = discord.Embed(title="Trade Request Timed Out", description="The trade request was not answered in time.", color=discord.Color.orange())
            await self.trade_session.message.edit(content=None, embed=embed, view=None)

# --- Cog ---
class TradeCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="trade", help="Initiate a trade with another user.")
    @app_commands.describe(user="The user you want to trade with.")
    async def trade(self, ctx: commands.Context, user: discord.Member):
        if user.bot or user == ctx.author:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Invalid Target**\nYou cannot trade with yourself or a bot.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        sender = await Player.get(ctx.author.id)
        receiver = await Player.get(user.id)

        if not sender or not receiver:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Player Not Found**\nBoth users must have a profile (`sl start`).", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if sender.trade or receiver.trade:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Already in Trade**\nOne of the users is already in a trade.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        sender.trade = True
        await sender.save()

        session = TradeSession(sender, receiver, ctx.author, user)
        view = TradeRequestView(session)
        
        embed = discord.Embed(
            title="Incoming Trade Request",
            description=f"{ctx.author.mention} has sent you a trade request. Do you accept?",
            color=discord.Color.gold()
        )
        message = await ctx.send(content=user.mention, embed=embed, view=view)
        session.message = message

async def setup(bot):
    await bot.add_cog(TradeCommands(bot))