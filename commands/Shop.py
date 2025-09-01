import discord
from discord.ext import commands
from discord import app_commands
from structure.emoji import getEmoji
from structure.player import Player
from structure.shop import Shop
from typing import Optional

# This list and the helper functions are used to map between display names,
# internal values (often for player attributes), and emoji keys.
I_CHOICES = [
    app_commands.Choice(name="Tickets", value="ticket"),
    app_commands.Choice(name="Essence Stones", value="stone"),
    app_commands.Choice(name="Enchanment Gear I", value="gear1"),
    app_commands.Choice(name="Enchanment Gear II", value="gear2"),
    app_commands.Choice(name="Enchanment Gear III", value="gear3"),
    app_commands.Choice(name="Gold", value="gold"),
    app_commands.Choice(name="Diamond", value="diamond"),
    app_commands.Choice(name="Traces of Shadow", value="tos"),
    app_commands.Choice(name="Water Cubes", value="icube"),
    app_commands.Choice(name="Fire Cubes", value="fcube"),
    app_commands.Choice(name="Dark Cubes", value="dcube"),
    app_commands.Choice(name="Wind Cubes", value="wcube"),
    app_commands.Choice(name="Light Cubes", value="lcube")
]

def get_currency_value(currency_name: str) -> str:
    for choice in I_CHOICES:
        if choice.name == currency_name:
            return choice.value
    return "Unknown Currency"

def get_currency_name(currency_value: str) -> str:
    for choice in I_CHOICES:
        if choice.value == currency_value:
            return choice.name
    return "Unknown Currency"

class ShopCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop = Shop()

    @commands.hybrid_command(name="buy", help="Purchase an item from the shop.")
    @app_commands.describe(id="The ID of the item to purchase.", quantity="The amount you want to purchase.")
    async def buy(self, ctx: commands.Context, id: int, quantity: int = 1):
        """Command to purchase items from the shop."""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Player Not Found**\nYou don't have a profile yet. Use `sl start` to begin your journey!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if quantity < 1:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Invalid Quantity**\nQuantity must be at least 1.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        item = self.shop.get_item(id)
        if item is None:
            embed = discord.Embed(title="SYSTEM MESSAGE", description=f"**[ERROR] Item Not Found**\nNo item with ID `{id}` was found in the shop.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        currency = item['currency']
        total_cost = item['price'] * quantity
        player_balance = getattr(player, currency, 0)

        if player_balance < total_cost:
            embed = discord.Embed(
                title="SYSTEM MESSAGE",
                description=f"**[ERROR] Insufficient Funds**\nYou don't have enough {getEmoji(currency.lower())} {get_currency_name(currency)} to buy this item.",
                color=discord.Color.red()
            )
            embed.add_field(name="Required", value=f"`{total_cost}`", inline=True)
            embed.add_field(name="Balance", value=f"`{player_balance}`", inline=True)
            await ctx.send(embed=embed)
            return

        setattr(player, currency, player_balance - total_cost)
        setattr(player, item['item'], getattr(player, item['item'], 0) + quantity)
        await player.save()

        embed = discord.Embed(
            title="SYSTEM MESSAGE",
            description=f"**[SUCCESS] Purchase Complete**\nYou successfully bought `x{quantity}` {getEmoji(get_currency_value(item['name']))} **{item['name']}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Cost", value=f"`{total_cost}` {getEmoji(currency.lower())}", inline=True)
        embed.add_field(name="New Balance", value=f"`{getattr(player, currency)}` {getEmoji(currency.lower())}", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shops", help="View all available shops and their currencies.")
    async def view_shops(self, ctx: commands.Context):
        """Views all shops and how to open them."""
        all_items = self.shop.get_all_items()
        if not all_items:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[NOTICE] Shop Empty**\nThe shop is currently empty.", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return
        
        currency_groups = {}
        for item in all_items:
            currency = item['currency']
            if currency not in currency_groups:
                currency_groups[currency] = []
            currency_groups[currency].append(item)

        embed = discord.Embed(title="Shop Overview", description="Here are the available shops. Use `sl shop [ID]` to view items.", color=0x2A2C31)
        for index, currency in enumerate(currency_groups.keys(), start=1):
            embed.add_field(name=f"Shop ID: {index}", value=f"Currency: {getEmoji(currency)} **{get_currency_name(currency)}**", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", help="View items available in a specific shop.")
    @app_commands.describe(id="The ID of the shop to view.")
    async def view_shop_by_id(self, ctx: commands.Context, id: int):
        """Views all items in the shop filtered by ID (currency group)."""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Player Not Found**\nYou don't have a profile yet. Use `sl start` to begin your journey!", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        all_items = self.shop.get_all_items()
        currency_groups = {}
        for item in all_items:
            currency = item['currency']
            if currency not in currency_groups:
                currency_groups[currency] = []
            currency_groups[currency].append(item)

        currency_list = list(currency_groups.keys())
        if not (0 < id <= len(currency_list)):
            embed = discord.Embed(title="SYSTEM MESSAGE", description=f"**[ERROR] Invalid Shop ID**\nNo shop found with ID `{id}`. Use `sl shops` to see available shops.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        selected_currency = currency_list[id - 1]
        items = currency_groups[selected_currency]
        
        embed = discord.Embed(title=f"{get_currency_name(selected_currency)} Shop", description="Use `sl buy [ID] [Amount]` to make a purchase.", color=0x2A2C31)
        
        for item in items:
            item_emoji = getEmoji(get_currency_value(item["name"]))
            price_emoji = getEmoji(item["currency"])
            embed.add_field(
                name=f"{item_emoji} {item['name']}",
                value=f"**ID**: `{item['id']}`\n**Price**: `{item['price']}` {price_emoji}",
                inline=True
            )
        
        balance = getattr(player, selected_currency, 0)
        embed.set_footer(text=f"Your Balance: {balance} {get_currency_name(selected_currency)}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ShopCommands(bot))