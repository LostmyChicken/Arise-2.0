import discord
from discord.ext import commands
from discord import app_commands

from utilis.utilis import extractId, item_autocomplete, hunter_autocomplete
from structure import boss
from structure.heroes import HeroManager
from structure.items import ItemManager

# Import centralized admin system
from utilis.admin import is_bot_admin

# Define rarity and class choices
RARITY_CHOICES = [
    app_commands.Choice(name="UR", value="UR"),
    app_commands.Choice(name="SSR", value="SSR"),
    app_commands.Choice(name="Super Rare", value="Super Rare"),
]

CLASS_CHOICES = [
    app_commands.Choice(name="Dark", value="Dark"),
    app_commands.Choice(name="Fire", value="Fire"),
    app_commands.Choice(name="Light", value="Light"),
    app_commands.Choice(name="Water", value="Water"),
    app_commands.Choice(name="Wind", value="Wind"),
]

TYPE_CHOICES = [
    app_commands.Choice(name="Hero Weapon", value="Hero_Weapon"),
    app_commands.Choice(name="Weapon", value="Weapon"),
]

class EditCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="edit", description="Bot Admin commands to modify existing game entities.")
    async def edit(self, ctx: commands.Context):
        """Main group command for editing game entities."""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        if not ctx.invoked_subcommand:
            await ctx.send("Please specify what you want to edit (`item` or `hero`).")

    @edit.command(name="item", description="Edit an existing item in the game")
    @app_commands.describe(
        item="Name of the item to edit",
        name="New name of the item",
        description="New description of the item",
        rarity="New rarity of the item",
        item_class="New class of the item",
        item_type="New type of the item",
        attack="New attack value",
        defense="New defense value",
        hp="New HP value",
        mp="New MP value",
        speed="New speed value",
        precision="New precision value",
        image_url="New image URL",
    )
    @app_commands.choices(rarity=RARITY_CHOICES, item_class=CLASS_CHOICES, item_type=TYPE_CHOICES)
    @app_commands.autocomplete(item=item_autocomplete)
    async def edit_item(
        self,
        ctx: commands.Context,
        item: str,
        name: str = None, description: str = None, rarity: str = None,
        item_class: str = None, item_type: str = None, attack: int = None,
        defense: int = None, hp: int = None, mp: int = None, speed: int = None,
        precision: int = None, image_url: str = None,
    ):
        await ctx.defer(ephemeral=True)
        item_data = await ItemManager.get(extractId(item))
        if not item_data:
            embed = discord.Embed(title="Error", description=f"Item `{item}` not found.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # Update attributes if provided
        if name is not None: item_data.name = name
        if description is not None: item_data.description = description
        if rarity is not None: item_data.rarity = rarity
        if item_class is not None: item_data.classType = item_class
        if item_type is not None: item_data.type = item_type
        if attack is not None: item_data.attack = attack
        if defense is not None: item_data.defense = defense
        if hp is not None: item_data.health = hp
        if mp is not None: item_data.mp = mp
        if speed is not None: item_data.speed = speed
        if precision is not None: item_data.precision = precision
        if image_url is not None: item_data.image = image_url

        await ItemManager.save(item_data)
        embed = discord.Embed(title="Item Edited", description=f"Successfully edited **{item_data.name}**.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @edit.command(name="hero", description="Edit an existing hero in the game")
    @app_commands.describe(
        hero="Name of the hero to edit",
        name="New name of the hero",
        description="New description of the hero",
        rarity="New rarity of the hero",
        hero_class="New class of the hero",
        attack="New attack value",
        defense="New defense value",
        hp="New HP value",
        mp="New MP value",
        speed="New speed value",
        image_url="New image URL",
    )
    @app_commands.choices(rarity=RARITY_CHOICES, hero_class=CLASS_CHOICES)
    @app_commands.autocomplete(hero=hunter_autocomplete)
    async def edit_hero(
        self,
        ctx: commands.Context,
        hero: str,
        name: str = None, description: str = None, rarity: str = None,
        hero_class: str = None, attack: int = None, defense: int = None,
        hp: int = None, mp: int = None, speed: int = None, image_url: str = None,
    ):
        await ctx.defer(ephemeral=True)
        hero_data = await HeroManager.get(extractId(hero))
        if not hero_data:
            embed = discord.Embed(title="Error", description=f"Hero `{hero}` not found.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # Update attributes if provided
        if name is not None: hero_data.name = name
        if description is not None: hero_data.description = description
        if rarity is not None: hero_data.rarity = rarity
        if hero_class is not None: hero_data.classType = hero_class
        if attack is not None: hero_data.attack = attack
        if defense is not None: hero_data.defense = defense
        if hp is not None: hero_data.health = hp
        if mp is not None: hero_data.mp = mp
        if speed is not None: hero_data.speed = speed
        if image_url is not None: hero_data.image = image_url

        await HeroManager.save(hero_data)
        embed = discord.Embed(title="Hero Edited", description=f"Successfully edited **{hero_data.name}**.", color=discord.Color.green())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EditCog(bot))