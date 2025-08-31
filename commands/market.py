import logging
import re
from discord import app_commands
from structure.emoji import getEmoji
from utilis.utilis import extractId, extractName, get_emoji, player_item_autocomplete, player_hunter_autocomplete
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.market import Market
from structure.player import Player

import discord
from discord.ext import commands
from discord.ui import Select,View,Button
from typing import Literal

class MarketPaginator(View):
    def __init__(self, ctx, pages):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.pages = pages
        self.current_page = 0
        self.message = None

    async def start(self):
        self.update_buttons()
        self.message = await self.ctx.send(embed=self.pages[self.current_page], view=self)

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= len(self.pages) - 1

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)


class MarketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        player = await Player.get(interaction.user.id)
        if not player:
            return []
        
        choices = []
        hunters = player.get_hunters()
        inventory = player.get_inventory()

        # Hunters
        for item_id, data in hunters.items():
            try:
                # Check if data is a dict with quantity or just an integer
                if isinstance(data, dict):
                    quantity = data.get('quantity', 1)
                else:
                    quantity = data if isinstance(data, int) else 1

                if quantity > 1:
                    hunter = await HeroManager.get(item_id)
                    if hunter and current.lower() in hunter.name.lower():
                        choices.append(app_commands.Choice(name=f"[H] {hunter.name}", value=hunter.name))
            except (TypeError, AttributeError):
                # Skip invalid data entries
                continue

        # Weapons
        for item_id, data in inventory.items():
            try:
                # Check if data is a dict with quantity or just an integer
                if isinstance(data, dict):
                    quantity = data.get('quantity', 1)
                else:
                    quantity = data if isinstance(data, int) else 1

                if quantity > 1:
                    item = await ItemManager.get(item_id)
                    if item and current.lower() in item.name.lower():
                        choices.append(app_commands.Choice(name=f"[W] {item.name}", value=item.name))
            except (TypeError, AttributeError):
                # Skip invalid data entries
                continue

        return choices[:25]


    @commands.hybrid_group(name="market", aliases=["marketlist"], help="View market listings or use subcommands to interact with the market.")
    @app_commands.describe(name="Filter by item name.", item_type="Filter by item type.", max_price="Filter by maximum price.")
    async def market(self, ctx: commands.Context, name: str = None, item_type: Literal['hunter', 'weapon'] = None, max_price: int = None):
        """View market listings or use subcommands to interact with the market."""
        if ctx.invoked_subcommand is not None:
            return
            
        filters = {}
        if name: filters['name'] = name
        if item_type: filters['i_t'] = item_type
        if max_price: filters['max_p'] = max_price

        listings = await Market.search(**filters)
        
        if not listings:
            embed = discord.Embed(title="No Listings Found", description="No listings found matching your criteria.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        items_per_page = 10
        pages = [listings[i:i + items_per_page] for i in range(0, len(listings), items_per_page)]

        def create_embed(page_data, page_num, total_pages):
            embed = discord.Embed(title="Market Listings", color=0x2A2C31)
            description = ""
            for listing in page_data:
                description += (
                    f"**#{listing.id}** | Seller: <@{listing.sid}>\n"
                    f"{get_emoji(listing.i_id)} **Offer:** {listing.i_n} ({listing.q})\n"
                    f"{getEmoji('gold')} **Price:** {listing.p}\n\n"
                )
            embed.description = description
            embed.set_footer(text=f"Page {page_num + 1}/{total_pages} | Use 'sl market buy <id>' to purchase")
            return embed

        embed_pages = [create_embed(p, i, len(pages)) for i, p in enumerate(pages)]

        if len(embed_pages) == 1:
            await ctx.send(embed=embed_pages[0])
            return

        paginator = MarketPaginator(ctx, embed_pages)
        await paginator.start()

    @market.command(name="list", help="List an item for sale on the market.")
    @app_commands.describe(quantity="How many units to list.", price="The price for the item.", name="The name of the item to list.")
    @app_commands.autocomplete(name=item_autocomplete)
    async def market_list(self, ctx: commands.Context, quantity: int, price: int, *, name: str):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Error", description="You haven't started yet! Use `sl start` to begin.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        if quantity <= 0 or price <= 0:
            embed = discord.Embed(title="Error", description="Quantity and price must be positive numbers.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        matched_item = None
        item_type = None
        hunters = player.get_hunters()
        inventory = player.get_inventory()
        market_listings = player.market

        # Check hunters
        for item_id, data in hunters.items():
            if data['quantity'] >= quantity + 1:
                hunter = await HeroManager.get(item_id)
                if hunter and hunter.name.lower() == name.lower():
                    matched_item = hunter
                    item_type = "hunter"
                    break
        
        # Check inventory if not found in hunters
        if not matched_item:
            for item_id, data in inventory.items():
                if data['quantity'] >= quantity + 1:
                    item = await ItemManager.get(item_id)
                    if item and item.name.lower() == name.lower():
                        matched_item = item
                        item_type = "weapon"
                        break

        if not matched_item:
            embed = discord.Embed(title="Error", description=f"No exact match found for '{name}' with at least {quantity + 1} shards.", color=discord.Color.red())
            return await ctx.send(embed=embed)

        for mid, data in market_listings.items():
            if data["id"] == matched_item.id:
                existing_listing = await Market.get(mid)
                embed = discord.Embed(title="Error", description=f"You already have an active listing for this shard! (ID: {existing_listing.id})\nUse `sl market unlist {existing_listing.id}` to remove it.", color=discord.Color.red())
                return await ctx.send(embed=embed)

        listing = await Market.create(
            sid=ctx.author.id,
            i_id=matched_item.id,
            i_t=item_type,
            q=quantity,
            p=price,
            i_n=matched_item.name
        )
        market_listings[listing.id] = {"id": matched_item.id, "q": quantity, "p": price}
        
        if item_type == "hunter":
            hunters[matched_item.id]['quantity'] -= quantity
        else:
            inventory[matched_item.id]['quantity'] -= quantity

        await player.save()

        embed = discord.Embed(title="Listing Successful", description=f"🛒 | Successfully listed {get_emoji(matched_item.id)} {matched_item.name} (x{quantity}) for {getEmoji('gold')} **Price:** {price} | **ID:** {listing.id}", color=discord.Color.green())
        await ctx.send(embed=embed)

        market_channel_id = 1346966545846374461 # Replace with your channel ID
        channel = self.bot.get_channel(market_channel_id)
        if channel:
            embed_market = discord.Embed(title=f"Market Offer (ID: {listing.id})", color=discord.Color.blue())
            embed_market.add_field(name="Fragment", value=f"{get_emoji(matched_item.id)} {matched_item.name} (x{quantity})")
            embed_market.add_field(name="Price", value=f"{getEmoji('gold')} {price} Gold", inline=False)
            embed_market.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed_market.set_footer(text=f"Use 'sl market buy {listing.id}' to accept the offer.")
            await channel.send(embed=embed_market)
        else:
            logging.warning(f"Market channel with ID {market_channel_id} not found.")

    
    @market.command(name="buy", help="Purchase an entire market listing.")
    @app_commands.describe(listing_id="The ID of the listing to buy.")
    async def market_buy(self, ctx: commands.Context, listing_id: int):
        """Purchase an entire market listing in one transaction"""
        listing = await Market.get(listing_id)
        if not listing:
            embed = discord.Embed(title="Error", description="❌ Listing doesn't exist!", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        if listing.sid == ctx.author.id:
            embed = discord.Embed(title="Error", description="❌ You can't buy your own listing!", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        buyer = await Player.get(ctx.author.id)
        if not buyer:
            embed = discord.Embed(title="Error", description="❌ Use `sl start` first!", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        total_price = listing.p
        
        if buyer.gold < total_price:
            embed = discord.Embed(title="Error", description=f"❌ You need {total_price}g (You have: {buyer.gold}g)", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        if listing.i_t == "hunter" and listing.i_id not in buyer.get_hunters():
            hunter = await HeroManager.get(listing.i_id)
            embed = discord.Embed(title="Error", description=f"❌ Unlock {hunter.name} first!", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        if listing.i_t == "weapon" and listing.i_id not in buyer.get_inventory():
            item = await ItemManager.get(listing.i_id)
            embed = discord.Embed(title="Error", description=f"❌ Unlock {item.name} first!", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        seller = await Player.get(listing.sid)
        if not seller:
            await listing.delete()
            embed = discord.Embed(title="Error", description="❌ Seller vanished! Listing removed.", color=discord.Color.red())
            return await ctx.send(embed=embed)
        
        try:
            buyer.gold -= total_price
            seller.gold += total_price
            
            target_dict = buyer.get_hunters() if listing.i_t == "hunter" else buyer.get_inventory()
            if listing.i_id not in target_dict:
                 target_dict[listing.i_id] = {'quantity': 0, 'level': 1, 'tier': 0, 'xp': 0} # Default structure
            target_dict[listing.i_id]['quantity'] += listing.q
            
            if str(listing.id) in seller.market:
                del seller.market[str(listing.id)]
            
            await listing.delete()
            
            await buyer.save()
            await seller.save()
            
            item = await HeroManager.get(listing.i_id) if listing.i_t == "hunter" else await ItemManager.get(listing.i_id)
            embed_buyer = discord.Embed(
                title="✅ Purchase Successful",
                description=f"You've purchased {get_emoji(listing.i_id)} {item.name} (x{listing.q}) for {getEmoji('gold')} {total_price} Gold.",
                color=0x2ecc71
            )
            embed_buyer.set_footer(text="Thank you for using the market!")
            await ctx.reply(embed=embed_buyer, mention_author=False)
            
            seller_user = self.bot.get_user(listing.sid)
            if seller_user:
                embed_seller = discord.Embed(
                    title="💰 Market Sale Notification",
                    description=(
                        f"Your market listing has been purchased by **{ctx.author.display_name}**.\n\n"
                        f"**Item Sold:** {item.name} ({listing.q})\n"
                        f"**Total Received:** {total_price}g\n\n"
                        f"*Funds have been automatically credited to your account.*"
                    ),
                    color=0x3498db
                )
                embed_seller.set_footer(text="Thank you for using our marketplace!")
                try:
                    await seller_user.send(embed=embed_seller)
                except discord.Forbidden:
                    logging.warning(f"Could not DM {seller_user.name} (DMs closed)")
            
        except Exception as e:
            logging.error(f"Market buy failed: {str(e)}")
            embed = discord.Embed(title="Error", description="❌ Transaction failed! Gold/items were not deducted.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @market.command(name="unlist", help="Remove your listing from the market.")
    @app_commands.describe(listing_id="The ID of the listing to unlist.")
    async def market_unlist(self, ctx: commands.Context, listing_id: int):
        listing = await Market.get(listing_id)
        if not listing:
            embed = discord.Embed(title="Error", description="Listing not found.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        if listing.sid != ctx.author.id:
            embed = discord.Embed(title="Error", description="You can only unlist your own items.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Error", description="Player data not found.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        if listing.i_t == "hunter":
            hunters = player.get_hunters()
            if listing.i_id not in hunters:
                hunters[listing.i_id] = {'quantity': 0}
            hunters[listing.i_id]['quantity'] += listing.q
        else:
            inventory = player.get_inventory()
            if listing.i_id not in inventory:
                inventory[listing.i_id] = {'quantity': 0}
            inventory[listing.i_id]['quantity'] += listing.q
        
        if str(listing.id) in player.market:
            del player.market[str(listing.id)]
            
        await player.save()
        await listing.delete()
        embed = discord.Embed(title="Success", description=f"Unlisted {listing.q}x {listing.i_n} (returned to your inventory)", color=discord.Color.green())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MarketCommands(bot))
