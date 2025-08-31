import logging
import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands
from structure.heroes import HeroManager
from structure.emoji import getEmoji
from utilis.utilis import extractId
from structure.items import ItemManager
from structure.player import DATABASE_PATH, Player
from utilis.utilis import item_autocomplete,hunter_autocomplete

# Import centralized admin system
from utilis.admin import is_bot_admin

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
    app_commands.Choice(name="Light Cubes", value="lcube"),
    app_commands.Choice(name="Key",value="key")
]

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.hybrid_group(name="give", help="Bot Admin commands to give items, currency, or XP to players.")
    async def give(self, ctx: commands.Context):
        """The parent command for the 'give' group."""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid give command passed. Use `sl help give` for more info.')

    @give.command(name="xp", help="Give a specified amount of XP to a player.")
    @app_commands.describe(player_id="The player to give XP to.", xp_amount="The amount of XP to give.")
    async def admin_give_me_xp(self, ctx: commands.Context, player_id: discord.User, xp_amount: int):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        await ctx.defer()
        try:
            player = await Player.get(player_id.id)
            if not player:
                await ctx.send(embed=discord.Embed(
                    title="❌ Error",
                    description=f"Player with ID `{player_id.id}` not found.",
                    color=discord.Color.red()
                ))
                return

            await player.add_xp(self.bot, xp_amount, ctx.channel)
            await player.save()

            embed = discord.Embed(
                title="✅ XP Granted",
                description=f"Successfully granted **{xp_amount} XP** to Player `{player_id}`.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Admin Command Executed")
            await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"An error occurred in adminGiveMeXp: {e}")
            await ctx.send(embed=discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again later.",
                color=discord.Color.red()
            ))
    
    @give.command(name="hunter", help="Give a hunter to a player for testing purposes.")
    @app_commands.describe(item="The ID of the hunter to give", level="The level of the hunter", tier="The tier of the hunter", xp="The XP of the hunter", user_id="The user ID to give to (admin only)")
    @app_commands.autocomplete(item=hunter_autocomplete)
    async def givemhunter(
        self,
        ctx: commands.Context,
        item: str,
        level: int = 1,
        tier: int = 1,
        xp: int = 0,
        user_id: discord.User = None
    ):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        await ctx.defer()
        target_player = user_id or ctx.author

        try:
            item_id = extractId(item)
            player = await Player.get(target_player.id)

            if not player:
                down = getEmoji("down")
                embed = discord.Embed(title="Error", description=f"Target player hasn't started yet\n{down}Use `sl start` first", color=discord.Color.red())
                return await ctx.send(embed=embed)

            item_data = await HeroManager.get(item_id)
            if not item_data:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Hunter Not Found",
                        description=f"No hunter found with the ID `{item_id}`.",
                        color=discord.Color.red()
                    )
                )

            player.add_hunter(item_id, level, tier, xp)
            await player.save()

            await ctx.send(
                embed=discord.Embed(
                    title="Hunter Added",
                    description=(
                        f"Given **{item_data.name}** to {target_player.mention}!\n"
                        f"- **Level:** {level}\n"
                        f"- **Tier:** {tier}\n"
                        f"- **XP:** {xp}"
                    ),
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
            )
            
    @give.command(name="removeitem", help="Admin only: Remove an item from a user's inventory.")
    @app_commands.describe(user="The user whose item will be removed", item="The ID of the item to remove", confirm="Confirm you want to remove this item")
    @app_commands.autocomplete(item=item_autocomplete)
    async def removeitem(
        self,
        ctx: commands.Context,
        user: discord.User,
        item: str,
        confirm: bool = False
    ):
        await ctx.defer(ephemeral=True)
        
        if not is_bot_admin(ctx.author.id):
            return await ctx.send(
                embed=discord.Embed(
                    title="🚫 Unauthorized",
                    description="You are not authorized to use this command.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
        if not confirm:
            return await ctx.send(
                embed=discord.Embed(
                    title="⚠️ Confirmation Required",
                    description=f"Please confirm you want to remove item `{item}` from {user.mention}'s inventory by setting `confirm: True`.",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )
        
        try:
            player = await Player.get(user.id)
            if not player:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Player Not Found",
                        description=f"Player with ID `{user.id}` not found.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            extracted_item_id = extractId(item)
            inventory = player.get_inventory()
            
            if extracted_item_id not in inventory:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Item Not Found",
                        description=f"Player doesn't have an item with ID `{extracted_item_id}` in their inventory.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            item_info = await ItemManager.get(extracted_item_id)
            
            del inventory[extracted_item_id]
            await player.save()
            
            embed = discord.Embed(
                title="✅ Item Removed",
                description=f"Successfully removed **{item_info.name if item_info else 'Item'}** from {user.mention}'s inventory.",
                color=discord.Color.green()
            )
            
            if item_info and hasattr(item_info, 'image') and item_info.image:
                embed.set_thumbnail(url=item_info.image)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Error in removeitem: {e}")
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred while processing your request: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            
    @give.command(name="item", help="Give an item to a player for testing purposes.")
    @app_commands.describe(item="The ID of the item to give", level="The level of the item", tier="The tier of the item", xp="The XP of the item", user_id="The user ID to give to (admin only)")
    @app_commands.autocomplete(item=item_autocomplete)
    async def givemeitem(
        self,
        ctx: commands.Context,
        item: str,
        level: int = 1,
        tier: int = 1,
        xp: int = 0,
        user_id: discord.User = None
    ):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        await ctx.defer()
        target_player = user_id or ctx.author
        
        try:
            item_id = extractId(item)
            player = await Player.get(target_player.id)

            if not player:
                down = getEmoji("down")
                embed = discord.Embed(title="Error", description=f"Target player hasn't started yet\n{down}Use `sl start` first", color=discord.Color.red())
                return await ctx.send(embed=embed)

            item_data = await ItemManager.get(item_id)
            if not item_data:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Item Not Found",
                        description=f"No item found with the ID `{item_id}`.",
                        color=discord.Color.red()
                    )
                )

            player.add_item(item_id, level, tier, xp)
            await player.save()

            await ctx.send(
                embed=discord.Embed(
                    title="Item Added",
                    description=(
                        f"Given **{item_data.name}** to {target_player.mention}!\n"
                        f"- **Level:** {level}\n"
                        f"- **Tier:** {tier}\n"
                        f"- **XP:** {xp}"
                    ),
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
            )
        
    @commands.hybrid_command(name='clear', help="Admin only: Clears all fight records from the database.")
    @commands.is_owner()
    async def clear(self, ctx: commands.Context):
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute('''DELETE FROM fights''')
                await db.commit()
            embed = discord.Embed(title="Success", description="All fights have been cleared from the database.", color=discord.Color.green())
            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"Error in /clear command: {e}")
            embed = discord.Embed(title="Error", description="An error occurred while clearing the fights.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @give.command(name="currency", help="Give a specified amount of a currency to a player.")
    @app_commands.describe(player_id="The player to give currency to", currency="The currency to give", amount="The amount to give")
    @app_commands.choices(currency=I_CHOICES)
    async def give_currency(
        self,
        ctx: commands.Context,
        player_id: discord.User,
        currency: str,
        amount: int = 1
    ):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return

        await ctx.defer()
        try:
            player = await Player.get(player_id.id)
            if not player:
                await ctx.send(embed=discord.Embed(
                    title="❌ Error",
                    description=f"Player with ID `{player_id.id}` not found.",
                    color=discord.Color.red()
                ))
                return

            current_balance = getattr(player, currency, None)
            if current_balance is None:
                await ctx.send(embed=discord.Embed(
                    title="❌ Error",
                    description=f"Currency `{currency}` not found for the player.",
                    color=discord.Color.red()
                ))
                return

            setattr(player, currency, current_balance + amount)
            await player.save()

            embed = discord.Embed(
                title="✅ Currency Granted",
                description=f"Successfully granted **{amount} {currency.capitalize()}** to Player `{player_id}`.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Admin Command Executed")
            await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"An error occurred in give_currency: {e}")
            await ctx.send(embed=discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again later.",
                color=discord.Color.red()
            ))
    
    @give.command(name="item_tier", help="Admin only: Increase the tier of a player's item.")
    @app_commands.describe(user="The user whose item tier will be increased", item="The ID of the item to upgrade", tiers="Number of tiers to increase")
    @app_commands.autocomplete(item=item_autocomplete)
    async def increase_item_tier(
        self,
        ctx: commands.Context,
        user: discord.User,
        item: str,
        tiers: int = 1
    ):
        await ctx.defer(ephemeral=True)
        
        if not is_bot_admin(ctx.author.id):
            return await ctx.send(
                embed=discord.Embed(
                    title="🚫 Unauthorized",
                    description="You are not authorized to use this command.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
        try:
            player = await Player.get(user.id)
            if not player:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Player Not Found",
                        description=f"Player with ID `{user.id}` not found.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            extracted_item_id = extractId(item)
            
            if extracted_item_id not in player.get_inventory():
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Item Not Found",
                        description=f"Player doesn't have an item with ID `{extracted_item_id}` in their inventory.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            item_info = await ItemManager.get(extracted_item_id)
            if not item_info:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Item Info Not Found",
                        description=f"No item found with ID `{extracted_item_id}` in the database.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            item_data = player.get_inventory()[extracted_item_id]
            current_tier = item_data.get('tier', 0)
            new_tier = min(current_tier + tiers, 6)
            actual_tiers_increased = new_tier - current_tier
            
            if actual_tiers_increased <= 0:
                return await ctx.send(
                    embed=discord.Embed(
                        title="⚠️ Already Max Tier",
                        description=f"This item is already at maximum tier (6).",
                        color=discord.Color.orange()
                    ),
                    ephemeral=True
                )
            
            player.get_inventory()[extracted_item_id]['tier'] = new_tier
            await player.save()
            
            embed = discord.Embed(
                title="✅ Item Tier Increased",
                description=(
                    f"Successfully increased **{item_info.name}**'s tier for {user.mention}!\n"
                    f"**Old Tier:** {current_tier}\n"
                    f"**New Tier:** {new_tier}\n"
                    f"**Tiers Increased:** {actual_tiers_increased}"
                ),
                color=discord.Color.green()
            )
            
            if hasattr(item_info, 'image') and item_info.image:
                embed.set_thumbnail(url=item_info.image)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Error in increase_item_tier: {e}")
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred while processing your request: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            
    @give.command(name="hunter_tier", help="Admin only: Increase the tier of a player's hunter.")
    @app_commands.describe(user="The user whose hunter tier will be increased", hunter="The ID of the hunter to upgrade", tiers="Number of tiers to increase")
    @app_commands.autocomplete(hunter=hunter_autocomplete)
    async def increase_hunter_tier(
        self,
        ctx: commands.Context,
        user: discord.User,
        hunter: str,
        tiers: int = 1
    ):
        await ctx.defer(ephemeral=True)
        
        if not is_bot_admin(ctx.author.id):
            return await ctx.send(
                embed=discord.Embed(
                    title="🚫 Unauthorized",
                    description="You are not authorized to use this command.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
        try:
            player = await Player.get(user.id)
            if not player:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Player Not Found",
                        description=f"Player with ID `{user.id}` not found.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            extracted_hunter_id = extractId(hunter)
            
            if extracted_hunter_id not in player.hunters:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Hunter Not Found",
                        description=f"Player doesn't have a hunter with ID `{extracted_hunter_id}`.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            hunter_info = await HeroManager.get(extracted_hunter_id)
            if not hunter_info:
                return await ctx.send(
                    embed=discord.Embed(
                        title="❌ Hunter Info Not Found",
                        description=f"No hunter found with ID `{extracted_hunter_id}` in the database.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            
            current_tier = player.hunters[extracted_hunter_id]['tier']
            new_tier = min(current_tier + tiers, 5)
            actual_tiers_increased = new_tier - current_tier
            
            if actual_tiers_increased <= 0:
                return await ctx.send(
                    embed=discord.Embed(
                        title="⚠️ Already Max Tier",
                        description=f"This hunter is already at maximum tier (5).",
                        color=discord.Color.orange()
                    ),
                    ephemeral=True
                )
            
            player.hunters[extracted_hunter_id]['tier'] = new_tier
            await player.save()
            
            embed = discord.Embed(
                title="✅ Hunter Tier Increased",
                description=(
                    f"Successfully increased **{hunter_info.name}**'s tier for {user.mention}!\n"
                    f"**Old Tier:** {current_tier}\n"
                    f"**New Tier:** {new_tier}\n"
                    f"**Tiers Increased:** {actual_tiers_increased}"
                ),
                color=discord.Color.green()
            )
            
            if hasattr(hunter_info, 'image') and hunter_info.image:
                embed.set_thumbnail(url=hunter_info.image)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Error in increase_hunter_tier: {e}")
            await ctx.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred while processing your request: {str(e)}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            
async def setup(bot):
    await bot.add_cog(AdminCommands(bot))