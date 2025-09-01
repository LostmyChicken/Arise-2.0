from enum import Enum, auto
import logging
import discord
from discord.ext import commands
from discord import app_commands
from discord import ui

from structure.shop import Shop
from utilis.utilis import extractId
from structure.shadow import Shadow
from structure.boss import Boss
from structure.heroes import Hero, HeroManager
from structure.items import Item, ItemManager
from structure.skills import Element, Skill, SkillManager
from structure.emoji import getEmoji

# Import centralized admin system
from utilis.admin import is_bot_admin

I_CHOICES = [
    app_commands.Choice(name="Tickets", value="ticket"),
    app_commands.Choice(name="Essence Stones", value="stone"),
    app_commands.Choice(name="Enchantment Gear I", value="gear1"),
    app_commands.Choice(name="Enchantment Gear II", value="gear2"),
    app_commands.Choice(name="Enchantment Gear III", value="gear3"),
    app_commands.Choice(name="Gold", value="gold"),
    app_commands.Choice(name="Diamond", value="diamond"),
    app_commands.Choice(name="Traces of Shadow", value="tos"),
    app_commands.Choice(name="Water Cubes", value="icube"),
    app_commands.Choice(name="Fire Cubes", value="fcube"),
    app_commands.Choice(name="Dark Cubes", value="dcube"),
    app_commands.Choice(name="Wind Cubes", value="wcube"),
    app_commands.Choice(name="Light Cubes", value="lcube"),
]

class EffectType(Enum):
    DAMAGE = auto(); HEAL = auto(); STUN = auto(); BLEED = auto(); SHIELD = auto()
    BUFF = auto(); DEBUFF = auto(); LIFE_STEAL = auto(); CRIT_BOOST = auto()
    AREA_DAMAGE = auto(); INVINCIBILITY = auto()

class SkillType(Enum):
    BASIC = "Basic"; QTE = "QTE"; ULTIMATE = "Ultimate"

async def hunter_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    all_hunters = await HeroManager.get_all()
    hunter_names = ["Sung Jinwoo"] + [hunter.name for hunter in all_hunters]
    filtered_names = [name for name in hunter_names if current.lower() in name.lower()]
    return [app_commands.Choice(name=name, value=name) for name in filtered_names[:25]]

async def skill_type_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=t.value, value=t.value) for t in SkillType if current.lower() in t.value.lower()]

async def effect_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=e.name, value=e.name) for e in EffectType if current.lower() in e.name.lower()]

async def element_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=e.value, value=e.value) for e in Element if current.lower() in e.value.lower()]

class HeroType(Enum):
    HEALER = "Healer"; TANK = "Tank"; DPS = "DPS"; SUPPORT = "Support"; MAGE = "Mage"; ASSASSIN = "Assassin"

HERO_TYPE_CHOICES = [app_commands.Choice(name=ht.value, value=ht.value) for ht in HeroType]
from rarity import Rarity

RARITY_CHOICES = [app_commands.Choice(name=r, value=r) for r in Rarity.get_all_rarities()]

async def item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    all_items = await ItemManager.get_all()
    filtered_items = [item for item in all_items if current.lower() in item.name.lower()]
    return [app_commands.Choice(name=item.name, value=item.name) for item in filtered_items[:25]]

CLASS_CHOICES = [app_commands.Choice(name=c, value=c) for c in ["Dark", "Fire", "Light", "Water", "Wind"]]
TYPE_CHOICES = [app_commands.Choice(name=t, value=t) for t in ["Hero_Weapon", "Weapon"]]

class CreateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shop = Shop()

    @commands.hybrid_group(name="create", help="Bot Admin commands to create in-game entities.")
    async def create(self, ctx: commands.Context):
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        if not ctx.invoked_subcommand:
            embed = discord.Embed(title="Create Command", description="Please specify a subcommand (`item`, `hero`, `shadow`, etc.).", color=discord.Color.blue())
            await ctx.send(embed=embed)

    @create.command(name="shadow", description="Create a new shadow.")
    async def create_shadow(self, ctx: commands.Context):
        """Open interactive shadow creation UI"""
        view = ShadowCreationView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @create.command(name="item", description="Create a new item for the game.")
    async def create_item(self, ctx: commands.Context):
        """Open interactive item creation UI"""
        view = ItemCreationView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @create.command(name="hero", description="Create a new hero for the game.")
    async def create_hero(self, ctx: commands.Context):
        """Open interactive hero creation UI"""
        view = HeroCreationView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @create.command(name="boss", description="Create a new boss for the game.")
    async def create_boss(self, ctx: commands.Context):
        """Open interactive boss creation UI"""
        view = BossCreationView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @create.command(name="skill", description="Create a new skill for a character.")
    async def create_skill(self, ctx: commands.Context):
        """Open interactive skill creation UI"""
        view = SkillCreationView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @create.command(name="worldboss", description="Create a world boss from existing shadows.")
    async def create_worldboss(self, ctx: commands.Context):
        """Open interactive world boss creation UI"""
        view = WorldBossCreationView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @create.command(name="shop-add", description="Add an item to the shop.")
    @app_commands.choices(item=I_CHOICES, currency=I_CHOICES)
    @app_commands.describe(name="Display name in shop", item="Item to sell (from choices)", price="Price", currency="Currency (from choices)", quantity="Quantity per purchase")
    async def add_item_to_shop(self, ctx: commands.Context, name: str, item: str, price: int, currency: str, quantity: int = 1):
        await ctx.defer()
        self.shop.add_item(name, item, price, currency, quantity)
        embed = discord.Embed(title="Item Added to Shop", description=f"Added **{name}** (x{quantity}) to the shop for **{price} {currency}**.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="createpanel", help="Open content creation panel (Admin only)")
    async def create_panel(self, ctx):
        """Open the comprehensive content creation panel"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use content creation commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = ContentCreationPanelView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="delete", help="Delete content from the game (Admin only)")
    async def delete_content(self, ctx):
        """Open content deletion interface"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use content deletion commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = ContentDeletionView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="editcontent", help="Edit existing content in the game (Admin only)")
    async def edit_content(self, ctx):
        """Open content editing interface"""
        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use content editing commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        view = ContentEditingView(ctx, self)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)


class ContentCreationPanelView(ui.View):
    """Comprehensive content creation panel with filters and categories"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)  # 10 minutes timeout
        self.ctx = ctx
        self.cog = cog
        self.current_category = "main"
        self.current_filter = "all"
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create the main content creation embed"""
        embed = discord.Embed(
            title="🏗️ **CONTENT CREATION PANEL** 🏗️",
            description="Comprehensive content creation and management system",
            color=discord.Color.orange()
        )

        if self.current_category == "main":
            embed.add_field(
                name="⚔️ **Items & Weapons**",
                value=(
                    "• Create new weapons and items\n"
                    "• Set stats, rarity, and properties\n"
                    "• Upload images and descriptions\n"
                    "• Balance testing and validation"
                ),
                inline=False
            )

            embed.add_field(
                name="👥 **Heroes & Characters**",
                value=(
                    "• Create new hunters and heroes\n"
                    "• Set abilities and class types\n"
                    "• Configure stats and elements\n"
                    "• Design character progression"
                ),
                inline=False
            )

            embed.add_field(
                name="👹 **Bosses & Enemies**",
                value=(
                    "• Create new boss encounters\n"
                    "• Set difficulty and rewards\n"
                    "• Configure attack patterns\n"
                    "• Balance health and damage"
                ),
                inline=False
            )

            embed.add_field(
                name="🌟 **Skills & Abilities**",
                value=(
                    "• Create new character skills\n"
                    "• Set effects and cooldowns\n"
                    "• Configure elemental properties\n"
                    "• Design skill progressions"
                ),
                inline=False
            )

            embed.add_field(
                name="👤 **Shadows & Entities**",
                value=(
                    "• Create new shadow entities\n"
                    "• Set unlock requirements\n"
                    "• Configure stat bonuses\n"
                    "• Design shadow abilities"
                ),
                inline=False
            )

            embed.add_field(
                name="🏪 **Shop & Economy**",
                value=(
                    "• Add items to shop\n"
                    "• Set prices and currencies\n"
                    "• Configure availability\n"
                    "• Manage shop inventory"
                ),
                inline=False
            )

        embed.set_footer(text="Select a category below to access creation tools")
        return embed

    def update_buttons(self):
        """Update buttons based on current category and filter"""
        self.clear_items()

        if self.current_category == "main":
            # Main category buttons
            item_btn = ui.Button(label="⚔️ Items & Weapons", style=discord.ButtonStyle.primary, row=0)
            item_btn.callback = self.show_item_creation
            self.add_item(item_btn)

            hero_btn = ui.Button(label="👥 Heroes", style=discord.ButtonStyle.primary, row=0)
            hero_btn.callback = self.show_hero_creation
            self.add_item(hero_btn)

            boss_btn = ui.Button(label="👹 Bosses", style=discord.ButtonStyle.primary, row=1)
            boss_btn.callback = self.show_boss_creation
            self.add_item(boss_btn)

            skill_btn = ui.Button(label="🌟 Skills", style=discord.ButtonStyle.primary, row=1)
            skill_btn.callback = self.show_skill_creation
            self.add_item(skill_btn)

            shadow_btn = ui.Button(label="👤 Shadows", style=discord.ButtonStyle.secondary, row=2)
            shadow_btn.callback = self.show_shadow_creation
            self.add_item(shadow_btn)

            shop_btn = ui.Button(label="🏪 Shop", style=discord.ButtonStyle.secondary, row=2)
            shop_btn.callback = self.show_shop_management
            self.add_item(shop_btn)

        else:
            # Back button for sub-categories
            back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=4)
            back_btn.callback = self.back_to_main
            self.add_item(back_btn)

    # Category navigation methods
    async def show_item_creation(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚔️ **ITEM & WEAPON CREATION** ⚔️",
            description="Create new weapons, items, and equipment",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🛠️ **Available Commands**",
            value=(
                "`sl create item` - Create new weapons and items\n"
                "• Set attack, defense, HP, MP, speed, precision\n"
                "• Configure rarity (Rare, Super Rare, SSR)\n"
                "• Set class type (Tank, Assassin, Fighter, Mage, Support)\n"
                "• Add custom images and descriptions"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Item Statistics**",
            value=(
                "• **Attack**: Damage output\n"
                "• **Defense**: Damage reduction\n"
                "• **HP**: Health points\n"
                "• **MP**: Mana/magic points\n"
                "• **Speed**: Action speed\n"
                "• **Precision**: Accuracy/critical chance"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 **Creation Tips**",
            value=(
                "• Balance stats according to rarity\n"
                "• Consider class synergies\n"
                "• Test items before release\n"
                "• Use high-quality images"
            ),
            inline=False
        )

        # Add create button
        self.clear_items()
        create_item_btn = ui.Button(label="⚔️ Create New Item", style=discord.ButtonStyle.success, row=0)
        create_item_btn.callback = self.launch_item_creation
        self.add_item(create_item_btn)

        back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.back_to_main
        self.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=self)

    async def launch_item_creation(self, interaction: discord.Interaction):
        """Launch the item creation interface"""
        view = ItemCreationView(self.ctx, self.cog)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_hero_creation(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👥 **HERO & CHARACTER CREATION** 👥",
            description="Create new hunters, heroes, and characters",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🛠️ **Available Commands**",
            value=(
                "`sl create hero` - Create new heroes and hunters\n"
                "• Set base stats and growth rates\n"
                "• Configure class type and element\n"
                "• Design abilities and skills\n"
                "• Add character artwork and lore"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 **Hero Types**",
            value=(
                "• **Tank**: High defense, crowd control\n"
                "• **Assassin**: High damage, speed\n"
                "• **Fighter**: Balanced combat stats\n"
                "• **Mage**: Magic damage, MP focus\n"
                "• **Support**: Healing, buffs"
            ),
            inline=False
        )

        # Add create button
        self.clear_items()
        create_hero_btn = ui.Button(label="👥 Create New Hero", style=discord.ButtonStyle.success, row=0)
        create_hero_btn.callback = self.launch_hero_creation
        self.add_item(create_hero_btn)

        back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.back_to_main
        self.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=self)

    async def launch_hero_creation(self, interaction: discord.Interaction):
        """Launch the hero creation interface"""
        view = HeroCreationView(self.ctx, self.cog)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_boss_creation(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👹 **BOSS & ENEMY CREATION** 👹",
            description="Create new boss encounters and enemies",
            color=discord.Color.dark_red()
        )

        embed.add_field(
            name="🛠️ **Available Commands**",
            value=(
                "`sl create boss` - Create new boss encounters\n"
                "• Set difficulty and challenge rating\n"
                "• Configure health, attack, and defense\n"
                "• Design special abilities and phases\n"
                "• Set rewards and drop rates"
            ),
            inline=False
        )

        # Add create button
        self.clear_items()
        create_boss_btn = ui.Button(label="👹 Create New Boss", style=discord.ButtonStyle.success, row=0)
        create_boss_btn.callback = self.launch_boss_creation
        self.add_item(create_boss_btn)

        back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.back_to_main
        self.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=self)

    async def launch_boss_creation(self, interaction: discord.Interaction):
        """Launch the boss creation interface"""
        view = BossCreationView(self.ctx, self.cog)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_skill_creation(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌟 **SKILL & ABILITY CREATION** 🌟",
            description="Create new skills, abilities, and effects",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🛠️ **Available Commands**",
            value=(
                "`sl create skill` - Create new character skills\n"
                "• Set skill type (Basic, QTE, Ultimate)\n"
                "• Configure damage and effects\n"
                "• Set cooldowns and MP costs\n"
                "• Add elemental properties"
            ),
            inline=False
        )

        # Add create button
        self.clear_items()
        create_skill_btn = ui.Button(label="🌟 Create New Skill", style=discord.ButtonStyle.success, row=0)
        create_skill_btn.callback = self.launch_skill_creation
        self.add_item(create_skill_btn)

        back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.back_to_main
        self.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=self)

    async def launch_skill_creation(self, interaction: discord.Interaction):
        """Launch the skill creation interface"""
        view = SkillCreationView(self.ctx, self.cog)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_shadow_creation(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👤 **SHADOW ENTITY CREATION** 👤",
            description="Create new shadow entities and unlockables",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="🛠️ **Available Commands**",
            value=(
                "`sl create shadow` - Create new shadow entities\n"
                "• Set unlock requirements and costs\n"
                "• Configure stat bonuses (attack/defense %)\n"
                "• Add shadow abilities and effects\n"
                "• Design shadow artwork"
            ),
            inline=False
        )

        # Add create button
        self.clear_items()
        create_shadow_btn = ui.Button(label="👤 Create New Shadow", style=discord.ButtonStyle.success, row=0)
        create_shadow_btn.callback = self.launch_shadow_creation
        self.add_item(create_shadow_btn)

        back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.back_to_main
        self.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=self)

    async def launch_shadow_creation(self, interaction: discord.Interaction):
        """Launch the shadow creation interface"""
        view = ShadowCreationView(self.ctx, self.cog)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_shop_management(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏪 **SHOP & ECONOMY MANAGEMENT** 🏪",
            description="Manage shop items and economy",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🛠️ **Available Commands**",
            value=(
                "`sl create shop-add` - Add items to shop\n"
                "• Set item prices and currencies\n"
                "• Configure purchase quantities\n"
                "• Manage shop inventory\n"
                "• Control item availability"
            ),
            inline=False
        )

        # Add create button
        self.clear_items()
        create_shop_btn = ui.Button(label="🛒 Create Shop Item", style=discord.ButtonStyle.success, row=0)
        create_shop_btn.callback = self.launch_shop_creation
        self.add_item(create_shop_btn)

        back_btn = ui.Button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=0)
        back_btn.callback = self.back_to_main
        self.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=self)

    async def launch_shop_creation(self, interaction: discord.Interaction):
        """Launch the shop item creation interface"""
        # For now, redirect to item creation since shop items are items
        view = ItemCreationView(self.ctx, self.cog)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def back_to_main(self, interaction: discord.Interaction):
        self.current_category = "main"
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class ItemCreationView(ui.View):
    """Interactive item creation interface"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.item_data = {
            'name': '',
            'description': '',
            'rarity': 'Rare',
            'item_class': 'Fire',
            'item_type': 'Weapon',
            'attack': 0,
            'defense': 0,
            'hp': 0,
            'mp': 0,
            'speed': 0,
            'precision': 0,
            'image_url': 'https://via.placeholder.com/150',
            'custom_emoji': '',
            'emoji_name': ''
        }
        self.current_step = 'basic'  # basic, stats, review
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create embed based on current step"""
        if self.current_step == 'basic':
            return await self.create_basic_embed()
        elif self.current_step == 'stats':
            return await self.create_stats_embed()
        elif self.current_step == 'review':
            return await self.create_review_embed()
        else:
            return await self.create_basic_embed()

    async def create_basic_embed(self):
        """Create basic info step embed"""
        embed = discord.Embed(
            title="⚔️ **ITEM CREATION - BASIC INFO** ⚔️",
            description="Configure the basic properties of your item",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📝 **Current Settings**",
            value=(
                f"**Name**: {self.item_data['name'] or '*Not set*'}\n"
                f"**Description**: {self.item_data['description'] or '*Not set*'}\n"
                f"**Rarity**: {self.item_data['rarity']}\n"
                f"**Element**: {self.item_data['item_class']}\n"
                f"**Type**: {self.item_data['item_type']}"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 **Next Steps**",
            value="Use the buttons below to configure basic properties, then proceed to stats",
            inline=False
        )

        return embed

    async def create_stats_embed(self):
        """Create stats configuration embed"""
        embed = discord.Embed(
            title="⚔️ **ITEM CREATION - STATS** ⚔️",
            description="Configure the combat statistics of your item",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📊 **Current Stats**",
            value=(
                f"{getEmoji('attack')} **Attack**: {self.item_data['attack']:,}\n"
                f"🛡️ **Defense**: {self.item_data['defense']:,}\n"
                f"❤️ **HP**: {self.item_data['hp']:,}\n"
                f"💙 **MP**: {self.item_data['mp']:,}\n"
                f"⚡ **Speed**: {self.item_data['speed']:,}\n"
                f"🎯 **Precision**: {self.item_data['precision']:,}"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 **Instructions**",
            value="Use the buttons below to adjust stats, then proceed to review",
            inline=False
        )

        return embed

    async def create_review_embed(self):
        """Create final review embed"""
        embed = discord.Embed(
            title="⚔️ **ITEM CREATION - REVIEW** ⚔️",
            description=f"Review your item: **{self.item_data['name']}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📝 **Basic Info**",
            value=(
                f"**Name**: {self.item_data['name']}\n"
                f"**Description**: {self.item_data['description']}\n"
                f"**Rarity**: {self.item_data['rarity']}\n"
                f"**Element**: {self.item_data['item_class']}\n"
                f"**Type**: {self.item_data['item_type']}"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Stats**",
            value=(
                f"{getEmoji('attack')} **Attack**: {self.item_data['attack']:,}\n"
                f"🛡️ **Defense**: {self.item_data['defense']:,}\n"
                f"❤️ **HP**: {self.item_data['hp']:,}\n"
                f"💙 **MP**: {self.item_data['mp']:,}\n"
                f"⚡ **Speed**: {self.item_data['speed']:,}\n"
                f"🎯 **Precision**: {self.item_data['precision']:,}"
            ),
            inline=False
        )



        if self.item_data['image_url'] != 'https://via.placeholder.com/150':
            embed.set_image(url=self.item_data['image_url'])

        embed.add_field(
            name="✅ **Ready to Create**",
            value="Click 'Create Item' to add this item to the game!",
            inline=False
        )

        return embed

    def update_buttons(self):
        """Update buttons based on current step"""
        self.clear_items()

        if self.current_step == 'basic':
            # Basic info buttons
            name_btn = ui.Button(label="📝 Set Name", style=discord.ButtonStyle.primary, row=0)
            name_btn.callback = self.set_name
            self.add_item(name_btn)

            desc_btn = ui.Button(label="📄 Set Description", style=discord.ButtonStyle.primary, row=0)
            desc_btn.callback = self.set_description
            self.add_item(desc_btn)

            # Dropdown for rarity
            rarity_options = []
            rarity_emojis = {"UR": "💎", "SSR": "🟠", "Super Rare": "🟣"}

            for rarity in Rarity.get_all_rarities():
                emoji = rarity_emojis.get(rarity, "⚪")
                rarity_options.append(discord.SelectOption(label=rarity, value=rarity, emoji=emoji))

            rarity_select = ui.Select(
                placeholder="Select Rarity",
                options=rarity_options,
                row=1
            )
            rarity_select.callback = self.set_rarity
            self.add_item(rarity_select)

            # Element select
            element_select = ui.Select(
                placeholder="Select Element",
                options=[
                    discord.SelectOption(label="Fire", value="Fire", emoji="🔥"),
                    discord.SelectOption(label="Water", value="Water", emoji="💧"),
                    discord.SelectOption(label="Wind", value="Wind", emoji="💨"),
                    discord.SelectOption(label="Light", value="Light", emoji="✨"),
                    discord.SelectOption(label="Dark", value="Dark", emoji="🌑"),
                ],
                row=2
            )
            element_select.callback = self.set_element
            self.add_item(element_select)

            # Type select
            type_select = ui.Select(
                placeholder="Select Type",
                options=[
                    discord.SelectOption(label="Weapon", value="Weapon", emoji="⚔️"),
                    discord.SelectOption(label="Hero_Weapon", value="Hero_Weapon", emoji="🗡️"),
                ],
                row=3
            )
            type_select.callback = self.set_type
            self.add_item(type_select)

            # Navigation
            if self.item_data['name'] and self.item_data['description']:
                next_btn = ui.Button(label="➡️ Next: Stats", style=discord.ButtonStyle.success, row=4)
                next_btn.callback = self.go_to_stats
                self.add_item(next_btn)

        elif self.current_step == 'stats':
            # Stat adjustment buttons - Row 0
            attack_btn = ui.Button(label=f"{getEmoji('attack')} Attack", style=discord.ButtonStyle.secondary, row=0)
            attack_btn.callback = self.adjust_attack
            self.add_item(attack_btn)

            defense_btn = ui.Button(label="🛡️ Defense", style=discord.ButtonStyle.secondary, row=0)
            defense_btn.callback = self.adjust_defense
            self.add_item(defense_btn)

            hp_btn = ui.Button(label="❤️ HP", style=discord.ButtonStyle.secondary, row=0)
            hp_btn.callback = self.adjust_hp
            self.add_item(hp_btn)

            mp_btn = ui.Button(label="💙 MP", style=discord.ButtonStyle.secondary, row=0)
            mp_btn.callback = self.adjust_mp
            self.add_item(mp_btn)

            # Row 1
            speed_btn = ui.Button(label="⚡ Speed", style=discord.ButtonStyle.secondary, row=1)
            speed_btn.callback = self.adjust_speed
            self.add_item(speed_btn)

            precision_btn = ui.Button(label="🎯 Precision", style=discord.ButtonStyle.secondary, row=1)
            precision_btn.callback = self.adjust_precision
            self.add_item(precision_btn)

            # Quick stat presets - Row 2
            weak_btn = ui.Button(label="📉 Weak Stats", style=discord.ButtonStyle.secondary, row=2)
            weak_btn.callback = self.set_weak_stats
            self.add_item(weak_btn)

            balanced_btn = ui.Button(label="⚖️ Balanced", style=discord.ButtonStyle.secondary, row=2)
            balanced_btn.callback = self.set_balanced_stats
            self.add_item(balanced_btn)

            strong_btn = ui.Button(label="💪 Strong Stats", style=discord.ButtonStyle.secondary, row=2)
            strong_btn.callback = self.set_strong_stats
            self.add_item(strong_btn)

            legendary_btn = ui.Button(label="🌟 Legendary", style=discord.ButtonStyle.secondary, row=2)
            legendary_btn.callback = self.set_legendary_stats
            self.add_item(legendary_btn)

            # Navigation - Row 3
            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=3)
            back_btn.callback = self.go_to_basic
            self.add_item(back_btn)

            next_btn = ui.Button(label="➡️ Review", style=discord.ButtonStyle.success, row=3)
            next_btn.callback = self.go_to_review
            self.add_item(next_btn)

        elif self.current_step == 'review':
            # Final actions - Row 0
            create_btn = ui.Button(label="✅ Create Item", style=discord.ButtonStyle.success, row=0)
            create_btn.callback = self.create_item
            self.add_item(create_btn)

            back_btn = ui.Button(label="⬅️ Back to Stats", style=discord.ButtonStyle.secondary, row=0)
            back_btn.callback = self.go_to_stats
            self.add_item(back_btn)

            # Customization - Row 1
            image_btn = ui.Button(label="🖼️ Set Image", style=discord.ButtonStyle.primary, row=1)
            image_btn.callback = self.set_image
            self.add_item(image_btn)

            emoji_btn = ui.Button(label="🎨 Image & Emoji", style=discord.ButtonStyle.primary, row=1)
            emoji_btn.callback = self.set_image_and_emoji
            self.add_item(emoji_btn)

            # Quick actions - Row 2
            preview_btn = ui.Button(label="👁️ Preview Item", style=discord.ButtonStyle.secondary, row=2)
            preview_btn.callback = self.preview_item
            self.add_item(preview_btn)

            reset_btn = ui.Button(label="🔄 Reset All", style=discord.ButtonStyle.danger, row=2)
            reset_btn.callback = self.reset_item
            self.add_item(reset_btn)

    # Modal for text input
    class TextInputModal(ui.Modal):
        def __init__(self, title, field_name, current_value="", max_length=100):
            super().__init__(title=title)
            self.field_name = field_name
            self.text_input = ui.TextInput(
                label=field_name.replace('_', ' ').title(),
                default=current_value,
                max_length=max_length,
                required=True
            )
            self.add_item(self.text_input)

        async def on_submit(self, interaction: discord.Interaction):
            # This will be overridden by the parent view
            pass

    # Enhanced modal for image and emoji assignment
    class ImageEmojiModal(ui.Modal):
        def __init__(self, current_image="", current_emoji=""):
            super().__init__(title="🎨 Image & Emoji Assignment")

            self.image_input = ui.TextInput(
                label="Image URL",
                placeholder="https://files.catbox.moe/example.png",
                default=current_image,
                max_length=500,
                required=False
            )
            self.add_item(self.image_input)

            self.emoji_input = ui.TextInput(
                label="Custom Emoji",
                placeholder="<:name:1234567890123456789>",
                default=current_emoji,
                max_length=100,
                required=False
            )
            self.add_item(self.emoji_input)

            self.emoji_name_input = ui.TextInput(
                label="Emoji Name (for bot reference)",
                placeholder="my_custom_item",
                max_length=50,
                required=False
            )
            self.add_item(self.emoji_name_input)

        async def on_submit(self, interaction: discord.Interaction):
            # This will be overridden by the parent view
            pass

    # Callback methods
    async def set_name(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Item Name", "name", self.item_data['name'], 50)

        async def modal_callback(modal_interaction):
            self.item_data['name'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_description(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Item Description", "description", self.item_data['description'], 200)

        async def modal_callback(modal_interaction):
            self.item_data['description'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_image(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Image URL", "image_url", self.item_data['image_url'], 500)

        async def modal_callback(modal_interaction):
            from utilis.utilis import validate_url
            self.item_data['image_url'] = validate_url(modal.text_input.value)
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_rarity(self, interaction: discord.Interaction):
        self.item_data['rarity'] = interaction.data['values'][0]
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_element(self, interaction: discord.Interaction):
        self.item_data['item_class'] = interaction.data['values'][0]
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_type(self, interaction: discord.Interaction):
        self.item_data['item_type'] = interaction.data['values'][0]
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # Navigation methods
    async def go_to_stats(self, interaction: discord.Interaction):
        self.current_step = 'stats'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_basic(self, interaction: discord.Interaction):
        self.current_step = 'basic'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_review(self, interaction: discord.Interaction):
        self.current_step = 'review'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # Stat adjustment methods (simplified - you can enhance these with modals for precise input)
    async def adjust_attack(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Attack", "attack", str(self.item_data['attack']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.item_data['attack'] = int(modal.text_input.value)
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def adjust_defense(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Defense", "defense", str(self.item_data['defense']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.item_data['defense'] = int(modal.text_input.value)
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def adjust_hp(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set HP", "hp", str(self.item_data['hp']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.item_data['hp'] = int(modal.text_input.value)
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def adjust_mp(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set MP", "mp", str(self.item_data['mp']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.item_data['mp'] = int(modal.text_input.value)
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def adjust_speed(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Speed", "speed", str(self.item_data['speed']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.item_data['speed'] = int(modal.text_input.value)
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def adjust_precision(self, interaction: discord.Interaction):
        modal = self.TextInputModal("Set Precision", "precision", str(self.item_data['precision']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.item_data['precision'] = int(modal.text_input.value)
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    # Quick stat preset methods
    async def set_weak_stats(self, interaction: discord.Interaction):
        """Set weak stats for common items"""
        self.item_data.update({
            'attack': 50,
            'defense': 30,
            'hp': 100,
            'mp': 50,
            'speed': 40,
            'precision': 35
        })
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_balanced_stats(self, interaction: discord.Interaction):
        """Set balanced stats for rare items"""
        self.item_data.update({
            'attack': 150,
            'defense': 120,
            'hp': 500,
            'mp': 200,
            'speed': 100,
            'precision': 110
        })
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_strong_stats(self, interaction: discord.Interaction):
        """Set strong stats for epic items"""
        self.item_data.update({
            'attack': 300,
            'defense': 250,
            'hp': 1000,
            'mp': 400,
            'speed': 200,
            'precision': 220
        })
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_legendary_stats(self, interaction: discord.Interaction):
        """Set legendary stats for mythic items"""
        self.item_data.update({
            'attack': 500,
            'defense': 400,
            'hp': 2000,
            'mp': 800,
            'speed': 350,
            'precision': 380
        })
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_image_and_emoji(self, interaction: discord.Interaction):
        """Set image and custom emoji for the item"""
        modal = self.ImageEmojiModal(self.item_data['image_url'], self.item_data['custom_emoji'])

        async def modal_callback(modal_interaction):
            from utilis.utilis import validate_url
            if modal.image_input.value:
                self.item_data['image_url'] = validate_url(modal.image_input.value)
            if modal.emoji_input.value:
                self.item_data['custom_emoji'] = modal.emoji_input.value
            if modal.emoji_name_input.value:
                self.item_data['emoji_name'] = modal.emoji_name_input.value

            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def add_emoji_to_json(self, item_id, emoji_string):
        """Add custom emoji to emojis.json file"""
        try:
            import json
            import re

            # Validate emoji format (should be <:name:id> or <a:name:id>)
            if emoji_string and not re.match(r'<a?:\w+:\d+>', emoji_string):
                print(f"⚠️ Warning: Emoji '{emoji_string}' is not in Discord format <:name:id>")
                return False

            # Load current emojis
            try:
                with open('emojis.json', 'r') as f:
                    emojis = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                emojis = {}

            # Add the new emoji
            emojis[item_id] = emoji_string

            # Save back to file with proper encoding
            with open('emojis.json', 'w', encoding='utf-8') as f:
                json.dump(emojis, f, indent=2, ensure_ascii=False)

            print(f"✅ Added emoji to emojis.json: {item_id} -> {emoji_string}")
            return True

        except Exception as e:
            print(f"❌ Failed to add emoji to emojis.json: {e}")
            return False

    async def preview_item(self, interaction: discord.Interaction):
        """Show a preview of how the item will look in game"""
        preview_embed = discord.Embed(
            title=f"🔍 **ITEM PREVIEW** 🔍",
            description=f"Preview of **{self.item_data['name']}**",
            color=discord.Color.blue()
        )

        # Show how it would appear in inventory
        rarity_emojis = {"Rare": "🟢", "Super Rare": "🟣", "SSR": "🟠"}
        rarity_emoji = rarity_emojis.get(self.item_data['rarity'], "⚪")
        element_emoji = getEmoji(f"{self.item_data['item_class'].lower()}_element")

        preview_text = f"{rarity_emoji} {element_emoji} **{self.item_data['name']}**\n"
        preview_text += f"*{self.item_data['description']}*\n\n"
        preview_text += f"{getEmoji('attack')} {self.item_data['attack']:,} | 🛡️ {self.item_data['defense']:,} | ❤️ {self.item_data['hp']:,}\n"
        preview_text += f"💙 {self.item_data['mp']:,} | ⚡ {self.item_data['speed']:,} | 🎯 {self.item_data['precision']:,}"

        if self.item_data['custom_emoji']:
            preview_text = f"{self.item_data['custom_emoji']} {preview_text}"

        preview_embed.add_field(
            name="📦 **Inventory Display**",
            value=preview_text,
            inline=False
        )

        if self.item_data['image_url'] != 'https://via.placeholder.com/150':
            preview_embed.set_image(url=self.item_data['image_url'])

        await interaction.response.send_message(embed=preview_embed, ephemeral=True)

    async def reset_item(self, interaction: discord.Interaction):
        """Reset all item data"""
        self.item_data = {
            'name': '',
            'description': '',
            'rarity': 'Rare',
            'item_class': 'Fire',
            'item_type': 'Weapon',
            'attack': 0,
            'defense': 0,
            'hp': 0,
            'mp': 0,
            'speed': 0,
            'precision': 0,
            'image_url': 'https://via.placeholder.com/150',
            'custom_emoji': ''
        }
        self.current_step = 'basic'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_item(self, interaction: discord.Interaction):
        """Create the item and save it"""
        try:
            item = Item(
                extractId(self.item_data['name']),  # id
                self.item_data['name'],             # name
                self.item_data['rarity'],           # rarity
                self.item_data['item_class'],       # classType
                self.item_data['item_type'],        # type
                self.item_data['image_url'],        # image
                self.item_data['description'],      # description
                self.item_data['hp'],               # health
                self.item_data['attack'],           # attack
                self.item_data['defense'],          # defense
                self.item_data['speed'],            # speed
                self.item_data['mp'],               # mp
                self.item_data['precision'],        # precision
                self.item_data['custom_emoji'],     # custom_emoji
                self.item_data['emoji_name']        # emoji_name
            )
            await ItemManager.save(item)

            # Add custom emoji to emojis.json if provided
            if self.item_data['custom_emoji'] and self.item_data['custom_emoji'].strip():
                await self.add_emoji_to_json(item.id, self.item_data['custom_emoji'])

            # Success embed
            embed = discord.Embed(
                title="✅ **ITEM CREATED SUCCESSFULLY** ✅",
                description=f"**{self.item_data['name']}** has been added to the game!",
                color=discord.Color.green()
            )

            embed.add_field(name="📝 **Description**", value=self.item_data['description'], inline=False)
            embed.add_field(name="✨ **Rarity**", value=self.item_data['rarity'], inline=True)
            embed.add_field(name="🌟 **Element**", value=self.item_data['item_class'], inline=True)
            embed.add_field(name="🎯 **Type**", value=self.item_data['item_type'], inline=True)

            embed.add_field(name=f"{getEmoji('attack')} **Attack**", value=f"{self.item_data['attack']:,}", inline=True)
            embed.add_field(name="🛡️ **Defense**", value=f"{self.item_data['defense']:,}", inline=True)
            embed.add_field(name="❤️ **HP**", value=f"{self.item_data['hp']:,}", inline=True)
            embed.add_field(name="💙 **MP**", value=f"{self.item_data['mp']:,}", inline=True)
            embed.add_field(name="⚡ **Speed**", value=f"{self.item_data['speed']:,}", inline=True)
            embed.add_field(name="🎯 **Precision**", value=f"{self.item_data['precision']:,}", inline=True)



            embed.add_field(name="🆔 **Item ID**", value=f"`{extractId(self.item_data['name'])}`", inline=True)
            embed.set_image(url=self.item_data['image_url'])
            embed.set_footer(text="Item is now available in the game! Players can now obtain this item.")

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **CREATION FAILED** ❌",
                description=f"Failed to create item: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)


class HeroCreationView(ui.View):
    """Interactive hero creation interface"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.hero_data = {
            'name': '',
            'description': '',
            'rarity': 'Rare',
            'hero_class': 'Fire',
            'hero_type': 'Fighter',
            'weapon': '',
            'attack': 100,
            'defense': 80,
            'hp': 1000,
            'mp': 200,
            'speed': 90,
            'age': 20,
            'gender': 'Male',
            'country': 'Unknown',
            'guild': 'None',
            'rank': 'E',
            'image_url': 'https://files.catbox.moe/jvxvcr.png',
            'custom_emoji': '',
            'emoji_name': ''
        }
        self.current_step = 'basic'
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create embed based on current step"""
        if self.current_step == 'basic':
            return await self.create_basic_embed()
        elif self.current_step == 'stats':
            return await self.create_stats_embed()
        elif self.current_step == 'details':
            return await self.create_details_embed()
        elif self.current_step == 'review':
            return await self.create_review_embed()
        else:
            return await self.create_basic_embed()

    async def create_basic_embed(self):
        """Create basic info step embed"""
        embed = discord.Embed(
            title="👥 **HERO CREATION - BASIC INFO** 👥",
            description="Configure the basic properties of your hero",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📝 **Current Settings**",
            value=(
                f"**Name**: {self.hero_data['name'] or '*Not set*'}\n"
                f"**Description**: {self.hero_data['description'] or '*Not set*'}\n"
                f"**Rarity**: {self.hero_data['rarity']}\n"
                f"**Element**: {self.hero_data['hero_class']}\n"
                f"**Type**: {self.hero_data['hero_type']}"
            ),
            inline=False
        )

        return embed

    async def create_stats_embed(self):
        """Create stats configuration embed"""
        embed = discord.Embed(
            title="👥 **HERO CREATION - STATS** 👥",
            description="Configure the combat statistics of your hero",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📊 **Current Stats**",
            value=(
                f"{getEmoji('attack')} **Attack**: {self.hero_data['attack']:,}\n"
                f"🛡️ **Defense**: {self.hero_data['defense']:,}\n"
                f"❤️ **HP**: {self.hero_data['hp']:,}\n"
                f"💙 **MP**: {self.hero_data['mp']:,}\n"
                f"⚡ **Speed**: {self.hero_data['speed']:,}"
            ),
            inline=False
        )

        return embed

    async def create_details_embed(self):
        """Create character details embed"""
        embed = discord.Embed(
            title="👥 **HERO CREATION - CHARACTER DETAILS** 👥",
            description="Configure character background and details",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="👤 **Character Info**",
            value=(
                f"**Age**: {self.hero_data['age']}\n"
                f"**Gender**: {self.hero_data['gender']}\n"
                f"**Country**: {self.hero_data['country']}\n"
                f"**Guild**: {self.hero_data['guild']}\n"
                f"**Rank**: {self.hero_data['rank']}\n"
                f"**Weapon**: {self.hero_data['weapon'] or '*Not set*'}"
            ),
            inline=False
        )

        return embed

    async def create_review_embed(self):
        """Create final review embed"""
        embed = discord.Embed(
            title="👥 **HERO CREATION - REVIEW** 👥",
            description=f"Review your hero: **{self.hero_data['name']}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📝 **Basic Info**",
            value=(
                f"**Name**: {self.hero_data['name']}\n"
                f"**Description**: {self.hero_data['description']}\n"
                f"**Rarity**: {self.hero_data['rarity']}\n"
                f"**Element**: {self.hero_data['hero_class']}\n"
                f"**Type**: {self.hero_data['hero_type']}"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Stats**",
            value=(
                f"{getEmoji('attack')} **Attack**: {self.hero_data['attack']:,}\n"
                f"🛡️ **Defense**: {self.hero_data['defense']:,}\n"
                f"❤️ **HP**: {self.hero_data['hp']:,}\n"
                f"💙 **MP**: {self.hero_data['mp']:,}\n"
                f"⚡ **Speed**: {self.hero_data['speed']:,}"
            ),
            inline=True
        )

        embed.add_field(
            name="👤 **Details**",
            value=(
                f"**Age**: {self.hero_data['age']}\n"
                f"**Gender**: {self.hero_data['gender']}\n"
                f"**Country**: {self.hero_data['country']}\n"
                f"**Guild**: {self.hero_data['guild']}\n"
                f"**Rank**: {self.hero_data['rank']}"
            ),
            inline=True
        )

        if self.hero_data['image_url'] != 'https://via.placeholder.com/150':
            embed.set_image(url=self.hero_data['image_url'])

        return embed

    def update_buttons(self):
        """Update buttons based on current step"""
        self.clear_items()

        if self.current_step == 'basic':
            # Basic info buttons - Row 0
            name_btn = ui.Button(label="📝 Set Name", style=discord.ButtonStyle.primary, row=0)
            name_btn.callback = self.set_name
            self.add_item(name_btn)

            desc_btn = ui.Button(label="📄 Set Description", style=discord.ButtonStyle.primary, row=0)
            desc_btn.callback = self.set_description
            self.add_item(desc_btn)

            # Properties buttons - Row 1
            rarity_btn = ui.Button(label=f"💎 Rarity: {self.hero_data['rarity']}", style=discord.ButtonStyle.secondary, row=1)
            rarity_btn.callback = self.set_rarity
            self.add_item(rarity_btn)

            element_btn = ui.Button(label=f"🔥 Element: {self.hero_data['hero_class']}", style=discord.ButtonStyle.secondary, row=1)
            element_btn.callback = self.set_element
            self.add_item(element_btn)

            type_btn = ui.Button(label=f"⚔️ Type: {self.hero_data['hero_type']}", style=discord.ButtonStyle.secondary, row=1)
            type_btn.callback = self.set_type
            self.add_item(type_btn)

            # Image & Emoji - Row 2
            image_btn = ui.Button(label="🎨 Image & Emoji", style=discord.ButtonStyle.secondary, row=2)
            image_btn.callback = self.set_image_and_emoji
            self.add_item(image_btn)

            # Navigation - Row 3
            if self.hero_data['name'] and self.hero_data['description']:
                next_btn = ui.Button(label="➡️ Next: Stats", style=discord.ButtonStyle.success, row=3)
                next_btn.callback = self.go_to_stats
                self.add_item(next_btn)

        elif self.current_step == 'stats':
            # Individual stat buttons - Row 0
            attack_btn = ui.Button(label=f"⚔️ Attack: {self.hero_data['attack']:,}", style=discord.ButtonStyle.primary, row=0)
            attack_btn.callback = self.set_attack
            self.add_item(attack_btn)

            defense_btn = ui.Button(label=f"🛡️ Defense: {self.hero_data['defense']:,}", style=discord.ButtonStyle.primary, row=0)
            defense_btn.callback = self.set_defense
            self.add_item(defense_btn)

            hp_btn = ui.Button(label=f"❤️ HP: {self.hero_data['hp']:,}", style=discord.ButtonStyle.primary, row=0)
            hp_btn.callback = self.set_hp
            self.add_item(hp_btn)

            # Row 1
            mp_btn = ui.Button(label=f"💙 MP: {self.hero_data['mp']:,}", style=discord.ButtonStyle.primary, row=1)
            mp_btn.callback = self.set_mp
            self.add_item(mp_btn)

            speed_btn = ui.Button(label=f"⚡ Speed: {self.hero_data['speed']:,}", style=discord.ButtonStyle.primary, row=1)
            speed_btn.callback = self.set_speed
            self.add_item(speed_btn)

            # Navigation - Row 2
            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=2)
            back_btn.callback = self.go_to_basic
            self.add_item(back_btn)

            next_btn = ui.Button(label="➡️ Next: Details", style=discord.ButtonStyle.success, row=2)
            next_btn.callback = self.go_to_details
            self.add_item(next_btn)

        elif self.current_step == 'details':
            # Detail buttons
            details_btn = ui.Button(label="👤 Set Details", style=discord.ButtonStyle.primary, row=0)
            details_btn.callback = self.set_details_modal
            self.add_item(details_btn)

            weapon_btn = ui.Button(label="⚔️ Set Weapon", style=discord.ButtonStyle.primary, row=0)
            weapon_btn.callback = self.set_weapon
            self.add_item(weapon_btn)

            # Navigation
            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=1)
            back_btn.callback = self.go_to_stats
            self.add_item(back_btn)

            next_btn = ui.Button(label="➡️ Review", style=discord.ButtonStyle.success, row=1)
            next_btn.callback = self.go_to_review
            self.add_item(next_btn)

        elif self.current_step == 'review':
            # Final actions
            create_btn = ui.Button(label="✅ Create Hero", style=discord.ButtonStyle.success, row=0)
            create_btn.callback = self.create_hero
            self.add_item(create_btn)

            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
            back_btn.callback = self.go_to_details
            self.add_item(back_btn)

    # Simplified callback methods (you can expand these)
    async def set_name(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Hero Name", "name", self.hero_data['name'], 50)

        async def modal_callback(modal_interaction):
            self.hero_data['name'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_description(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Hero Description", "description", self.hero_data['description'], 200)

        async def modal_callback(modal_interaction):
            self.hero_data['description'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    # New property setting methods
    async def set_rarity(self, interaction: discord.Interaction):
        """Set hero rarity with dropdown selection"""
        view = HeroPropertySelectView(self, "rarity", Rarity.get_all_rarities())
        embed = discord.Embed(
            title="💎 **SELECT RARITY** 💎",
            description="Choose the rarity level for your hero",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_element(self, interaction: discord.Interaction):
        """Set hero element with dropdown selection"""
        view = HeroPropertySelectView(self, "hero_class", ["Fire", "Water", "Earth", "Air", "Light", "Dark", "Lightning", "Ice"])
        embed = discord.Embed(
            title="🔥 **SELECT ELEMENT** 🔥",
            description="Choose the elemental affinity for your hero",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_type(self, interaction: discord.Interaction):
        """Set hero type with dropdown selection"""
        view = HeroPropertySelectView(self, "hero_type", ["Fighter", "Mage", "Assassin", "Tank", "Support", "Ranger"])
        embed = discord.Embed(
            title="⚔️ **SELECT TYPE** ⚔️",
            description="Choose the combat role for your hero",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_image_and_emoji(self, interaction: discord.Interaction):
        """Set image and custom emoji for the hero"""
        modal = ItemCreationView.ImageEmojiModal(self.hero_data['image_url'], self.hero_data['custom_emoji'])

        async def modal_callback(modal_interaction):
            from utilis.utilis import validate_url
            if modal.image_input.value:
                self.hero_data['image_url'] = validate_url(modal.image_input.value)
            if modal.emoji_input.value:
                self.hero_data['custom_emoji'] = modal.emoji_input.value
            if modal.emoji_name_input.value:
                self.hero_data['emoji_name'] = modal.emoji_name_input.value

            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    # Individual stat setting methods
    async def set_attack(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Attack", "attack", str(self.hero_data['attack']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.hero_data['attack'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_defense(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Defense", "defense", str(self.hero_data['defense']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.hero_data['defense'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_hp(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set HP", "hp", str(self.hero_data['hp']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.hero_data['hp'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_mp(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set MP", "mp", str(self.hero_data['mp']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.hero_data['mp'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_speed(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Speed", "speed", str(self.hero_data['speed']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.hero_data['speed'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_details_modal(self, interaction: discord.Interaction):
        # Simplified details setting
        embed = discord.Embed(
            title="👤 **DETAILS SET**",
            description="Hero details have been configured with default values.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def set_weapon(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Weapon", "weapon", self.hero_data['weapon'], 50)

        async def modal_callback(modal_interaction):
            self.hero_data['weapon'] = modal.text_input.value
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def add_emoji_to_json(self, hero_id, emoji_string):
        """Add custom emoji to emojis.json file"""
        try:
            import json
            import re

            # Validate emoji format (should be <:name:id> or <a:name:id>)
            if emoji_string and not re.match(r'<a?:\w+:\d+>', emoji_string):
                print(f"⚠️ Warning: Hero emoji '{emoji_string}' is not in Discord format <:name:id>")
                return False

            # Load current emojis
            try:
                with open('emojis.json', 'r') as f:
                    emojis = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                emojis = {}

            # Add the new emoji
            emojis[hero_id] = emoji_string

            # Save back to file with proper encoding
            with open('emojis.json', 'w', encoding='utf-8') as f:
                json.dump(emojis, f, indent=2, ensure_ascii=False)

            print(f"✅ Added hero emoji to emojis.json: {hero_id} -> {emoji_string}")
            return True

        except Exception as e:
            print(f"❌ Failed to add hero emoji to emojis.json: {e}")
            return False

    # Navigation methods
    async def go_to_stats(self, interaction: discord.Interaction):
        self.current_step = 'stats'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_basic(self, interaction: discord.Interaction):
        self.current_step = 'basic'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_details(self, interaction: discord.Interaction):
        self.current_step = 'details'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_review(self, interaction: discord.Interaction):
        self.current_step = 'review'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_hero(self, interaction: discord.Interaction):
        """Create the hero and save it"""
        try:
            hero = Hero(
                extractId(self.hero_data['name']),  # id
                self.hero_data['name'],             # name
                self.hero_data['rarity'],           # rarity
                self.hero_data['hero_class'],       # classType
                self.hero_data['hero_type'],        # type
                self.hero_data['image_url'],        # image
                self.hero_data['description'],      # description
                self.hero_data['hp'],               # health
                self.hero_data['attack'],           # attack
                self.hero_data['defense'],          # defense
                self.hero_data['speed'],            # speed
                self.hero_data['mp'],               # mp
                self.hero_data['age'],              # age
                self.hero_data['gender'],           # gender
                self.hero_data['country'],          # country
                self.hero_data['weapon'],           # weapon
                self.hero_data['guild'],            # guild
                self.hero_data['rank'],             # rank
                self.hero_data['custom_emoji'],     # custom_emoji
                self.hero_data['emoji_name']        # emoji_name
            )
            await HeroManager.save(hero)

            # Add custom emoji to emojis.json if provided
            if self.hero_data['custom_emoji'] and self.hero_data['custom_emoji'].strip():
                await self.add_emoji_to_json(hero.id, self.hero_data['custom_emoji'])

            # Success embed
            embed = discord.Embed(
                title="✅ **HERO CREATED SUCCESSFULLY** ✅",
                description=f"**{self.hero_data['name']}** has been added to the game!",
                color=discord.Color.green()
            )

            embed.add_field(name="📝 **Description**", value=self.hero_data['description'], inline=False)
            embed.add_field(name="✨ **Rarity**", value=self.hero_data['rarity'], inline=True)
            embed.add_field(name="🌟 **Element**", value=self.hero_data['hero_class'], inline=True)
            embed.add_field(name="🎯 **Type**", value=self.hero_data['hero_type'], inline=True)

            embed.add_field(name=f"{getEmoji('attack')} **Attack**", value=f"{self.hero_data['attack']:,}", inline=True)
            embed.add_field(name="🛡️ **Defense**", value=f"{self.hero_data['defense']:,}", inline=True)
            embed.add_field(name="❤️ **HP**", value=f"{self.hero_data['hp']:,}", inline=True)

            embed.add_field(name="🆔 **Hero ID**", value=f"`{extractId(self.hero_data['name'])}`", inline=True)
            embed.set_image(url=self.hero_data['image_url'])
            embed.set_footer(text="Hero is now available in the game!")

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **CREATION FAILED** ❌",
                description=f"Failed to create hero: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)


class HeroPropertySelectView(ui.View):
    """Dropdown selection view for hero properties"""

    def __init__(self, parent_view, property_name, options):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.property_name = property_name
        self.options = options

        # Create dropdown
        dropdown = ui.Select(
            placeholder=f"Choose {property_name}...",
            options=[discord.SelectOption(label=option, value=option) for option in options]
        )
        dropdown.callback = self.property_selected
        self.add_item(dropdown)

        # Back button
        back_btn = ui.Button(label="🔙 Back", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.back_to_hero
        self.add_item(back_btn)

    async def property_selected(self, interaction: discord.Interaction):
        """Handle property selection"""
        selected_value = interaction.data['values'][0]
        self.parent_view.hero_data[self.property_name] = selected_value

        # Update parent view
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

    async def back_to_hero(self, interaction: discord.Interaction):
        """Return to hero creation"""
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class BossCreationView(ui.View):
    """Interactive boss creation interface"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.boss_data = {
            'name': '',
            'description': '',
            'image': 'https://files.catbox.moe/jvxvcr.png',
            'attack': 500,
            'defense': 300,
            'health': 10000,
            'speed': 150,
            'precision': 200,
            'rarity': 'Rare',
            'boss_class': 'Fire',
            'weakness_class': 'Water',
            'custom_emoji': '',
            'emoji_name': ''
        }
        self.current_step = 'basic'
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create embed based on current step"""
        if self.current_step == 'basic':
            return await self.create_basic_embed()
        elif self.current_step == 'stats':
            return await self.create_stats_embed()
        elif self.current_step == 'review':
            return await self.create_review_embed()
        else:
            return await self.create_basic_embed()

    async def create_basic_embed(self):
        """Create basic info step embed"""
        embed = discord.Embed(
            title="👹 **BOSS CREATION - BASIC INFO** 👹",
            description="Configure the basic properties of your boss",
            color=discord.Color.red()
        )

        embed.add_field(
            name="📝 **Current Settings**",
            value=(
                f"**Name**: {self.boss_data['name'] or '*Not set*'}\n"
                f"**Description**: {self.boss_data['description'] or '*Not set*'}\n"
                f"**Rarity**: {self.boss_data['rarity']}\n"
                f"**Element**: {self.boss_data['boss_class']}\n"
                f"**Weakness**: {self.boss_data['weakness_class']}"
            ),
            inline=False
        )

        return embed

    async def create_stats_embed(self):
        """Create stats configuration embed"""
        embed = discord.Embed(
            title="👹 **BOSS CREATION - STATS** 👹",
            description="Configure the combat statistics of your boss",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📊 **Current Stats**",
            value=(
                f"{getEmoji('attack')} **Attack**: {self.boss_data['attack']:,}\n"
                f"🛡️ **Defense**: {self.boss_data['defense']:,}\n"
                f"❤️ **Health**: {self.boss_data['health']:,}\n"
                f"⚡ **Speed**: {self.boss_data['speed']:,}\n"
                f"🎯 **Precision**: {self.boss_data['precision']:,}"
            ),
            inline=False
        )

        return embed

    async def create_review_embed(self):
        """Create final review embed"""
        embed = discord.Embed(
            title="👹 **BOSS CREATION - REVIEW** 👹",
            description=f"Review your boss: **{self.boss_data['name']}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📝 **Basic Info**",
            value=(
                f"**Name**: {self.boss_data['name']}\n"
                f"**Description**: {self.boss_data['description']}\n"
                f"**Rarity**: {self.boss_data['rarity']}\n"
                f"**Element**: {self.boss_data['boss_class']}\n"
                f"**Weakness**: {self.boss_data['weakness_class']}"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Stats**",
            value=(
                f"{getEmoji('attack')} **Attack**: {self.boss_data['attack']:,}\n"
                f"🛡️ **Defense**: {self.boss_data['defense']:,}\n"
                f"❤️ **Health**: {self.boss_data['health']:,}\n"
                f"⚡ **Speed**: {self.boss_data['speed']:,}\n"
                f"🎯 **Precision**: {self.boss_data['precision']:,}"
            ),
            inline=False
        )

        if self.boss_data['image'] != 'https://via.placeholder.com/150':
            embed.set_image(url=self.boss_data['image'])

        return embed

    def update_buttons(self):
        """Update buttons based on current step"""
        self.clear_items()

        if self.current_step == 'basic':
            # Basic info buttons - Row 0
            name_btn = ui.Button(label="📝 Set Name", style=discord.ButtonStyle.primary, row=0)
            name_btn.callback = self.set_name
            self.add_item(name_btn)

            desc_btn = ui.Button(label="📄 Set Description", style=discord.ButtonStyle.primary, row=0)
            desc_btn.callback = self.set_description
            self.add_item(desc_btn)

            # Properties buttons - Row 1
            rarity_btn = ui.Button(label=f"💎 Rarity: {self.boss_data['rarity']}", style=discord.ButtonStyle.secondary, row=1)
            rarity_btn.callback = self.set_rarity
            self.add_item(rarity_btn)

            element_btn = ui.Button(label=f"🔥 Element: {self.boss_data['boss_class']}", style=discord.ButtonStyle.secondary, row=1)
            element_btn.callback = self.set_element
            self.add_item(element_btn)

            weakness_btn = ui.Button(label=f"💧 Weakness: {self.boss_data['weakness_class']}", style=discord.ButtonStyle.secondary, row=1)
            weakness_btn.callback = self.set_weakness
            self.add_item(weakness_btn)

            # Image & Emoji - Row 2
            image_btn = ui.Button(label="🎨 Image & Emoji", style=discord.ButtonStyle.secondary, row=2)
            image_btn.callback = self.set_image_and_emoji
            self.add_item(image_btn)

            # Navigation - Row 3
            if self.boss_data['name'] and self.boss_data['description']:
                next_btn = ui.Button(label="➡️ Next: Stats", style=discord.ButtonStyle.success, row=3)
                next_btn.callback = self.go_to_stats
                self.add_item(next_btn)

        elif self.current_step == 'stats':
            # Individual stat buttons - Row 0
            attack_btn = ui.Button(label=f"⚔️ Attack: {self.boss_data['attack']:,}", style=discord.ButtonStyle.primary, row=0)
            attack_btn.callback = self.set_attack
            self.add_item(attack_btn)

            defense_btn = ui.Button(label=f"🛡️ Defense: {self.boss_data['defense']:,}", style=discord.ButtonStyle.primary, row=0)
            defense_btn.callback = self.set_defense
            self.add_item(defense_btn)

            health_btn = ui.Button(label=f"❤️ Health: {self.boss_data['health']:,}", style=discord.ButtonStyle.primary, row=0)
            health_btn.callback = self.set_health
            self.add_item(health_btn)

            # Row 1
            speed_btn = ui.Button(label=f"⚡ Speed: {self.boss_data['speed']:,}", style=discord.ButtonStyle.primary, row=1)
            speed_btn.callback = self.set_speed
            self.add_item(speed_btn)

            precision_btn = ui.Button(label=f"🎯 Precision: {self.boss_data['precision']:,}", style=discord.ButtonStyle.primary, row=1)
            precision_btn.callback = self.set_precision
            self.add_item(precision_btn)

            # Navigation - Row 2
            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=2)
            back_btn.callback = self.go_to_basic
            self.add_item(back_btn)

            next_btn = ui.Button(label="➡️ Review", style=discord.ButtonStyle.success, row=2)
            next_btn.callback = self.go_to_review
            self.add_item(next_btn)

        elif self.current_step == 'review':
            # Final actions
            create_btn = ui.Button(label="✅ Create Boss", style=discord.ButtonStyle.success, row=0)
            create_btn.callback = self.create_boss
            self.add_item(create_btn)

            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
            back_btn.callback = self.go_to_stats
            self.add_item(back_btn)

            image_btn = ui.Button(label="🖼️ Set Image", style=discord.ButtonStyle.primary, row=1)
            image_btn.callback = self.set_image
            self.add_item(image_btn)

    # Callback methods (simplified)
    async def set_name(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Boss Name", "name", self.boss_data['name'], 50)

        async def modal_callback(modal_interaction):
            self.boss_data['name'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_description(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Boss Description", "description", self.boss_data['description'], 200)

        async def modal_callback(modal_interaction):
            self.boss_data['description'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_image(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Image URL", "image", self.boss_data['image'], 500)

        async def modal_callback(modal_interaction):
            from utilis.utilis import validate_url
            self.boss_data['image'] = validate_url(modal.text_input.value)
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    # New property setting methods
    async def set_rarity(self, interaction: discord.Interaction):
        """Set boss rarity with dropdown selection"""
        view = BossPropertySelectView(self, "rarity", Rarity.get_all_rarities())
        embed = discord.Embed(
            title="💎 **SELECT RARITY** 💎",
            description="Choose the rarity level for your boss",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_element(self, interaction: discord.Interaction):
        """Set boss element with dropdown selection"""
        view = BossPropertySelectView(self, "boss_class", ["Fire", "Water", "Earth", "Air", "Light", "Dark", "Lightning", "Ice"])
        embed = discord.Embed(
            title="🔥 **SELECT ELEMENT** 🔥",
            description="Choose the elemental affinity for your boss",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_weakness(self, interaction: discord.Interaction):
        """Set boss weakness with dropdown selection"""
        view = BossPropertySelectView(self, "weakness_class", ["Fire", "Water", "Earth", "Air", "Light", "Dark", "Lightning", "Ice"])
        embed = discord.Embed(
            title="💧 **SELECT WEAKNESS** 💧",
            description="Choose the elemental weakness for your boss",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_image_and_emoji(self, interaction: discord.Interaction):
        """Set image and custom emoji for the boss"""
        modal = ItemCreationView.ImageEmojiModal(self.boss_data['image'], self.boss_data['custom_emoji'])

        async def modal_callback(modal_interaction):
            from utilis.utilis import validate_url
            if modal.image_input.value:
                self.boss_data['image'] = validate_url(modal.image_input.value)
            if modal.emoji_input.value:
                self.boss_data['custom_emoji'] = modal.emoji_input.value
            if modal.emoji_name_input.value:
                self.boss_data['emoji_name'] = modal.emoji_name_input.value

            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    # Individual stat setting methods
    async def set_attack(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Attack", "attack", str(self.boss_data['attack']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.boss_data['attack'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_defense(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Defense", "defense", str(self.boss_data['defense']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.boss_data['defense'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_health(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Health", "health", str(self.boss_data['health']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.boss_data['health'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_speed(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Speed", "speed", str(self.boss_data['speed']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.boss_data['speed'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_precision(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Precision", "precision", str(self.boss_data['precision']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.boss_data['precision'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def add_emoji_to_json(self, boss_id, emoji_string):
        """Add custom emoji to emojis.json file"""
        try:
            import json
            import re

            # Validate emoji format (should be <:name:id> or <a:name:id>)
            if emoji_string and not re.match(r'<a?:\w+:\d+>', emoji_string):
                print(f"⚠️ Warning: Boss emoji '{emoji_string}' is not in Discord format <:name:id>")
                return False

            # Load current emojis
            try:
                with open('emojis.json', 'r') as f:
                    emojis = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                emojis = {}

            # Add the new emoji
            emojis[boss_id] = emoji_string

            # Save back to file with proper encoding
            with open('emojis.json', 'w', encoding='utf-8') as f:
                json.dump(emojis, f, indent=2, ensure_ascii=False)

            print(f"✅ Added boss emoji to emojis.json: {boss_id} -> {emoji_string}")
            return True

        except Exception as e:
            print(f"❌ Failed to add boss emoji to emojis.json: {e}")
            return False

    # Navigation methods
    async def go_to_stats(self, interaction: discord.Interaction):
        self.current_step = 'stats'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_basic(self, interaction: discord.Interaction):
        self.current_step = 'basic'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_review(self, interaction: discord.Interaction):
        self.current_step = 'review'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_boss(self, interaction: discord.Interaction):
        """Create the boss and save it"""
        try:
            boss = Boss(
                extractId(self.boss_data['name']),
                self.boss_data['name'],
                self.boss_data['description'],
                self.boss_data['image'],
                self.boss_data['attack'],
                self.boss_data['defense'],
                self.boss_data['health'],
                self.boss_data['speed'],
                self.boss_data['precision'],
                self.boss_data['rarity'],
                self.boss_data['boss_class'],
                self.boss_data['weakness_class']
            )
            await boss.save()

            # Add custom emoji to emojis.json if provided
            if self.boss_data['custom_emoji'] and self.boss_data['custom_emoji'].strip():
                await self.add_emoji_to_json(boss.id, self.boss_data['custom_emoji'])

            # Success embed
            embed = discord.Embed(
                title="✅ **BOSS CREATED SUCCESSFULLY** ✅",
                description=f"**{self.boss_data['name']}** has been added to the game!",
                color=discord.Color.green()
            )

            embed.add_field(name="📝 **Description**", value=self.boss_data['description'], inline=False)
            embed.add_field(name="✨ **Rarity**", value=self.boss_data['rarity'], inline=True)
            embed.add_field(name="🌟 **Element**", value=self.boss_data['boss_class'], inline=True)
            embed.add_field(name="💥 **Weakness**", value=self.boss_data['weakness_class'], inline=True)

            embed.add_field(name=f"{getEmoji('attack')} **Attack**", value=f"{self.boss_data['attack']:,}", inline=True)
            embed.add_field(name="🛡️ **Defense**", value=f"{self.boss_data['defense']:,}", inline=True)
            embed.add_field(name="❤️ **Health**", value=f"{self.boss_data['health']:,}", inline=True)

            embed.add_field(name="🆔 **Boss ID**", value=f"`{extractId(self.boss_data['name'])}`", inline=True)
            embed.set_image(url=self.boss_data['image'])
            embed.set_footer(text="Boss is now available in the game!")

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **CREATION FAILED** ❌",
                description=f"Failed to create boss: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)


class BossPropertySelectView(ui.View):
    """Dropdown selection view for boss properties"""

    def __init__(self, parent_view, property_name, options):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.property_name = property_name
        self.options = options

        # Create dropdown
        dropdown = ui.Select(
            placeholder=f"Choose {property_name}...",
            options=[discord.SelectOption(label=option, value=option) for option in options]
        )
        dropdown.callback = self.property_selected
        self.add_item(dropdown)

        # Back button
        back_btn = ui.Button(label="🔙 Back", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.back_to_boss
        self.add_item(back_btn)

    async def property_selected(self, interaction: discord.Interaction):
        """Handle property selection"""
        selected_value = interaction.data['values'][0]
        self.parent_view.boss_data[self.property_name] = selected_value

        # Update parent view
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

    async def back_to_boss(self, interaction: discord.Interaction):
        """Return to boss creation"""
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class ShadowCreationView(ui.View):
    """Interactive shadow creation interface"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.shadow_data = {
            'name': '',
            'description': '',
            'image': 'https://files.catbox.moe/jvxvcr.png',
            'price': 1000,
            'attack': 10,
            'defense': 10,
            'required_boss': '',
            'custom_emoji': '',
            'emoji_name': ''
        }
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create shadow creation embed"""
        embed = discord.Embed(
            title="👤 **SHADOW CREATION** 👤",
            description="Create a new shadow entity",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="📝 **Current Settings**",
            value=(
                f"**Name**: {self.shadow_data['name'] or '*Not set*'}\n"
                f"**Description**: {self.shadow_data['description'] or '*Not set*'}\n"
                f"**Price**: {self.shadow_data['price']} TOS\n"
                f"**Required Boss**: {self.shadow_data['required_boss'] or '*None*'}\n"
                f"**Attack Boost**: +{self.shadow_data['attack']}%\n"
                f"**Defense Boost**: +{self.shadow_data['defense']}%"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 **Instructions**",
            value="Use the buttons below to configure your shadow, then create it!",
            inline=False
        )

        return embed

    def update_buttons(self):
        """Update buttons"""
        self.clear_items()

        # Configuration buttons - Row 0
        name_btn = ui.Button(label="📝 Set Name", style=discord.ButtonStyle.primary, row=0)
        name_btn.callback = self.set_name
        self.add_item(name_btn)

        desc_btn = ui.Button(label="📄 Set Description", style=discord.ButtonStyle.primary, row=0)
        desc_btn.callback = self.set_description
        self.add_item(desc_btn)

        # Stats and customization - Row 1
        stats_btn = ui.Button(label="📊 Set Stats & Price", style=discord.ButtonStyle.secondary, row=1)
        stats_btn.callback = self.set_stats
        self.add_item(stats_btn)

        boss_btn = ui.Button(label="👹 Required Boss", style=discord.ButtonStyle.secondary, row=1)
        boss_btn.callback = self.set_required_boss
        self.add_item(boss_btn)

        image_emoji_btn = ui.Button(label="🎨 Image & Emoji", style=discord.ButtonStyle.secondary, row=1)
        image_emoji_btn.callback = self.set_image_and_emoji
        self.add_item(image_emoji_btn)

        # Preview and create - Row 2
        if self.shadow_data['name']:
            preview_btn = ui.Button(label="👁️ Preview Shadow", style=discord.ButtonStyle.secondary, row=2)
            preview_btn.callback = self.preview_shadow
            self.add_item(preview_btn)

        if self.shadow_data['name'] and self.shadow_data['description']:
            create_btn = ui.Button(label="✅ Create Shadow", style=discord.ButtonStyle.success, row=2)
            create_btn.callback = self.create_shadow
            self.add_item(create_btn)

    # Simplified callback methods
    async def set_name(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Shadow Name", "name", self.shadow_data['name'], 50)

        async def modal_callback(modal_interaction):
            self.shadow_data['name'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_description(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Shadow Description", "description", self.shadow_data['description'], 200)

        async def modal_callback(modal_interaction):
            self.shadow_data['description'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_required_boss(self, interaction: discord.Interaction):
        """Set the required boss for this shadow"""
        modal = ItemCreationView.TextInputModal("Set Required Boss ID", "required_boss", self.shadow_data['required_boss'], 50)

        async def modal_callback(modal_interaction):
            self.shadow_data['required_boss'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_stats(self, interaction: discord.Interaction):
        """Open interactive stats editing interface"""
        view = ShadowStatsEditView(self)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_image_and_emoji(self, interaction: discord.Interaction):
        """Set image and custom emoji for the shadow"""
        modal = ItemCreationView.ImageEmojiModal(self.shadow_data['image'], self.shadow_data['custom_emoji'])

        async def modal_callback(modal_interaction):
            from utilis.utilis import validate_url
            if modal.image_input.value:
                self.shadow_data['image'] = validate_url(modal.image_input.value)
            if modal.emoji_input.value:
                self.shadow_data['custom_emoji'] = modal.emoji_input.value
            if modal.emoji_name_input.value:
                self.shadow_data['emoji_name'] = modal.emoji_name_input.value

            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def preview_shadow(self, interaction: discord.Interaction):
        """Show a preview of how the shadow will look in game"""
        preview_embed = discord.Embed(
            title=f"🔍 **SHADOW PREVIEW** 🔍",
            description=f"Preview of **{self.shadow_data['name']}**",
            color=discord.Color.purple()
        )

        preview_text = f"👤 **{self.shadow_data['name']}**\n"
        preview_text += f"*{self.shadow_data['description']}*\n\n"
        preview_text += f"{getEmoji('attack')} **Attack Boost**: +{self.shadow_data['attack']}%\n"
        preview_text += f"🛡️ **Defense Boost**: +{self.shadow_data['defense']}%"

        if self.shadow_data['custom_emoji']:
            preview_text = f"{self.shadow_data['custom_emoji']} {preview_text}"

        preview_embed.add_field(
            name="👤 **Shadow Display**",
            value=preview_text,
            inline=False
        )

        if self.shadow_data['image'] != 'https://via.placeholder.com/150':
            preview_embed.set_image(url=self.shadow_data['image'])

        await interaction.response.send_message(embed=preview_embed, ephemeral=True)

    async def create_shadow(self, interaction: discord.Interaction):
        """Create the shadow and save it"""
        try:
            shadow_id = extractId(self.shadow_data['name'])
            shadow = Shadow(
                shadow_id,
                self.shadow_data['name'],
                self.shadow_data['description'],
                self.shadow_data['image'],
                self.shadow_data['price'],
                self.shadow_data['attack'],
                self.shadow_data['defense'],
                self.shadow_data['required_boss'] if self.shadow_data['required_boss'] else None,
                self.shadow_data['custom_emoji'],
                self.shadow_data['emoji_name']
            )
            await shadow.save()

            # Add emoji to emojis.json if provided
            if self.shadow_data['custom_emoji']:
                await self.add_emoji_to_json(shadow_id, self.shadow_data['custom_emoji'])

            # Success embed
            embed = discord.Embed(
                title="✅ **SHADOW CREATED SUCCESSFULLY** ✅",
                description=f"**{self.shadow_data['name']}** has been added to the shadow collection!",
                color=discord.Color.green()
            )

            embed.add_field(name="📝 **Description**", value=self.shadow_data['description'], inline=False)
            embed.add_field(name=f"{getEmoji('attack')} **Attack Boost**", value=f"+{self.shadow_data['attack']}%", inline=True)
            embed.add_field(name="🛡️ **Defense Boost**", value=f"+{self.shadow_data['defense']}%", inline=True)
            embed.add_field(name="💰 **Price**", value=f"{self.shadow_data['price']} TOS", inline=True)
            embed.add_field(name="👹 **Required Boss**", value=self.shadow_data['required_boss'] or "None", inline=True)
            embed.add_field(name="🆔 **Shadow ID**", value=f"`{shadow_id}`", inline=True)
            embed.set_image(url=self.shadow_data['image'])
            embed.set_footer(text="Shadow is now available for players to unlock!")

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **CREATION FAILED** ❌",
                description=f"Failed to create shadow: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

    async def add_emoji_to_json(self, shadow_id, emoji_string):
        """Add custom emoji to emojis.json file"""
        try:
            import json
            import re

            # Validate emoji format (should be <:name:id> or <a:name:id>)
            if emoji_string and not re.match(r'<a?:\w+:\d+>', emoji_string):
                print(f"⚠️ Warning: Shadow emoji '{emoji_string}' is not in Discord format <:name:id>")
                return False

            # Load current emojis
            try:
                with open('emojis.json', 'r') as f:
                    emojis = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                emojis = {}

            # Add the new emoji
            emojis[shadow_id] = emoji_string

            # Save back to file with proper encoding
            with open('emojis.json', 'w', encoding='utf-8') as f:
                json.dump(emojis, f, indent=2, ensure_ascii=False)

            print(f"✅ Added shadow emoji to emojis.json: {shadow_id} -> {emoji_string}")
            return True

        except Exception as e:
            print(f"❌ Failed to add shadow emoji to emojis.json: {e}")
            return False


class ShadowStatsEditView(ui.View):
    """Interactive shadow stats editing interface"""

    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.update_buttons()

    async def create_embed(self):
        """Create shadow stats editing embed"""
        embed = discord.Embed(
            title="📊 **SHADOW STATS EDITOR** 📊",
            description="Configure your shadow's stat bonuses",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="⚔️ **Current Stats & Price**",
            value=(
                f"{getEmoji('attack')} **Attack Boost**: +{self.parent_view.shadow_data['attack']}%\n"
                f"🛡️ **Defense Boost**: +{self.parent_view.shadow_data['defense']}%\n"
                f"💰 **Price**: {self.parent_view.shadow_data['price']} TOS"
            ),
            inline=False
        )

        embed.add_field(
            name="💡 **Tips**",
            value=(
                "• Attack boost affects damage dealt\n"
                "• Defense boost affects damage reduction\n"
                "• Typical ranges: 5-50% for balanced shadows\n"
                "• Higher stats make shadows more valuable"
            ),
            inline=False
        )

        return embed

    def update_buttons(self):
        """Update button layout"""
        self.clear_items()

        # Stat adjustment buttons
        attack_btn = ui.Button(label="⚔️ Set Attack", style=discord.ButtonStyle.primary, row=0)
        attack_btn.callback = self.set_attack
        self.add_item(attack_btn)

        defense_btn = ui.Button(label="🛡️ Set Defense", style=discord.ButtonStyle.primary, row=0)
        defense_btn.callback = self.set_defense
        self.add_item(defense_btn)

        price_btn = ui.Button(label="💰 Set Price", style=discord.ButtonStyle.primary, row=0)
        price_btn.callback = self.set_price
        self.add_item(price_btn)

        # Back button
        back_btn = ui.Button(label="🔙 Back to Shadow", style=discord.ButtonStyle.secondary, row=1)
        back_btn.callback = self.back_to_shadow
        self.add_item(back_btn)

    async def set_attack(self, interaction: discord.Interaction):
        """Set attack boost percentage"""
        modal = ItemCreationView.TextInputModal("Set Attack Boost", "attack", str(self.parent_view.shadow_data['attack']), 10)

        async def modal_callback(modal_interaction):
            try:
                value = int(modal.text_input.value)
                if value < 0 or value > 100:
                    await modal_interaction.response.send_message("❌ Attack boost must be between 0-100%!", ephemeral=True)
                    return
                self.parent_view.shadow_data['attack'] = value
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_defense(self, interaction: discord.Interaction):
        """Set defense boost percentage"""
        modal = ItemCreationView.TextInputModal("Set Defense Boost", "defense", str(self.parent_view.shadow_data['defense']), 10)

        async def modal_callback(modal_interaction):
            try:
                value = int(modal.text_input.value)
                if value < 0 or value > 100:
                    await modal_interaction.response.send_message("❌ Defense boost must be between 0-100%!", ephemeral=True)
                    return
                self.parent_view.shadow_data['defense'] = value
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_price(self, interaction: discord.Interaction):
        """Set shadow price in TOS"""
        modal = ItemCreationView.TextInputModal("Set Shadow Price (TOS)", "price", str(self.parent_view.shadow_data['price']), 10)

        async def modal_callback(modal_interaction):
            try:
                value = int(modal.text_input.value)
                if value < 1:
                    await modal_interaction.response.send_message("❌ Price must be at least 1 TOS!", ephemeral=True)
                    return
                self.parent_view.shadow_data['price'] = value
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def back_to_shadow(self, interaction: discord.Interaction):
        """Return to shadow creation"""
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class SkillCreationView(ui.View):
    """Interactive skill creation interface"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.skill_data = {
            'owner_type': 'Hero',  # Hero, Item, Boss, Shadow, Global
            'owner_id': '',
            'skill_type': 'Basic',
            'name': '',
            'description': '',
            'effects': 'DAMAGE',
            'damage': 0,
            'mp_cost': 0,
            'required_level': 1,
            'element': 'Fire',
            'unlock_condition': 'Level',  # Level, Quest, Defeat, Purchase
            'unlock_value': 1,
            'custom_emoji': '',
            'emoji_name': ''
        }
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create skill creation embed"""
        embed = discord.Embed(
            title="🌟 **SKILL CREATION** 🌟",
            description="Create a new character skill",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="📝 **Skill Settings**",
            value=(
                f"**Owner Type**: {self.skill_data['owner_type']}\n"
                f"**Owner**: {self.skill_data['owner_id'] or '*Not set*'}\n"
                f"**Skill Name**: {self.skill_data['name'] or '*Not set*'}\n"
                f"**Type**: {self.skill_data['skill_type']}\n"
                f"**Element**: {self.skill_data['element']}\n"
                f"**Description**: {self.skill_data['description'][:50] + '...' if len(self.skill_data['description']) > 50 else self.skill_data['description'] or '*Not set*'}"
            ),
            inline=False
        )

        embed.add_field(
            name="⚔️ **Combat Stats**",
            value=(
                f"**Effect**: {self.skill_data['effects']}\n"
                f"**Damage**: {self.skill_data['damage']}%\n"
                f"**MP Cost**: {self.skill_data['mp_cost']}"
            ),
            inline=True
        )

        embed.add_field(
            name="🔓 **Unlock Requirements**",
            value=(
                f"**Condition**: {self.skill_data['unlock_condition']}\n"
                f"**Value**: {self.skill_data['unlock_value']}\n"
                f"**Required Level**: {self.skill_data['required_level']}"
            ),
            inline=True
        )

        return embed

    def update_buttons(self):
        """Update buttons"""
        self.clear_items()

        # Owner configuration - Row 0
        owner_type_btn = ui.Button(label=f"📋 Owner Type: {self.skill_data['owner_type']}", style=discord.ButtonStyle.primary, row=0)
        owner_type_btn.callback = self.set_owner_type
        self.add_item(owner_type_btn)

        owner_btn = ui.Button(label="👤 Set Owner", style=discord.ButtonStyle.primary, row=0)
        owner_btn.callback = self.set_owner
        self.add_item(owner_btn)

        # Skill properties - Row 1
        name_btn = ui.Button(label="📝 Set Name", style=discord.ButtonStyle.secondary, row=1)
        name_btn.callback = self.set_name
        self.add_item(name_btn)

        desc_btn = ui.Button(label="📄 Set Description", style=discord.ButtonStyle.secondary, row=1)
        desc_btn.callback = self.set_description
        self.add_item(desc_btn)

        type_btn = ui.Button(label=f"🌟 Type: {self.skill_data['skill_type']}", style=discord.ButtonStyle.secondary, row=1)
        type_btn.callback = self.set_skill_type
        self.add_item(type_btn)

        # Combat stats - Row 2
        element_btn = ui.Button(label=f"🔥 Element: {self.skill_data['element']}", style=discord.ButtonStyle.secondary, row=2)
        element_btn.callback = self.set_element
        self.add_item(element_btn)

        damage_btn = ui.Button(label=f"⚔️ Damage: {self.skill_data['damage']}%", style=discord.ButtonStyle.secondary, row=2)
        damage_btn.callback = self.set_damage
        self.add_item(damage_btn)

        mp_btn = ui.Button(label=f"💙 MP Cost: {self.skill_data['mp_cost']}", style=discord.ButtonStyle.secondary, row=2)
        mp_btn.callback = self.set_mp_cost
        self.add_item(mp_btn)

        # Unlock system - Row 3
        unlock_btn = ui.Button(label=f"🔓 Unlock: {self.skill_data['unlock_condition']}", style=discord.ButtonStyle.secondary, row=3)
        unlock_btn.callback = self.set_unlock_condition
        self.add_item(unlock_btn)

        emoji_btn = ui.Button(label="🎨 Image & Emoji", style=discord.ButtonStyle.secondary, row=3)
        emoji_btn.callback = self.set_image_and_emoji
        self.add_item(emoji_btn)

        # Create button - Row 4
        if self.skill_data['owner_id'] and self.skill_data['name']:
            create_btn = ui.Button(label="✅ Create Skill", style=discord.ButtonStyle.success, row=4)
            create_btn.callback = self.create_skill
            self.add_item(create_btn)

    # Enhanced callback methods
    async def set_owner_type(self, interaction: discord.Interaction):
        """Set the type of owner for this skill"""
        view = SkillOwnerTypeSelectView(self)
        embed = discord.Embed(
            title="📋 **SELECT OWNER TYPE** 📋",
            description="Choose what type of entity this skill belongs to",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_owner(self, interaction: discord.Interaction):
        """Set the specific owner for this skill"""
        modal = ItemCreationView.TextInputModal("Set Owner Name/ID", "owner", self.skill_data['owner_id'], 50)

        async def modal_callback(modal_interaction):
            self.skill_data['owner_id'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_name(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Skill Name", "name", self.skill_data['name'], 50)

        async def modal_callback(modal_interaction):
            self.skill_data['name'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_description(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Skill Description", "description", self.skill_data['description'], 200)

        async def modal_callback(modal_interaction):
            self.skill_data['description'] = modal.text_input.value
            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_skill_type(self, interaction: discord.Interaction):
        """Set skill type with dropdown"""
        view = SkillPropertySelectView(self, "skill_type", ["Basic", "QTE", "Ultimate"])
        embed = discord.Embed(
            title="🌟 **SELECT SKILL TYPE** 🌟",
            description="Choose the type of skill",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_element(self, interaction: discord.Interaction):
        """Set skill element with dropdown"""
        view = SkillPropertySelectView(self, "element", ["Fire", "Water", "Earth", "Air", "Light", "Dark", "Lightning", "Ice"])
        embed = discord.Embed(
            title="🔥 **SELECT ELEMENT** 🔥",
            description="Choose the elemental affinity for the skill",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_damage(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set Damage %", "damage", str(self.skill_data['damage']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.skill_data['damage'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_mp_cost(self, interaction: discord.Interaction):
        modal = ItemCreationView.TextInputModal("Set MP Cost", "mp_cost", str(self.skill_data['mp_cost']), 10)

        async def modal_callback(modal_interaction):
            try:
                self.skill_data['mp_cost'] = int(modal.text_input.value)
                self.update_buttons()
                embed = await self.create_embed()
                await modal_interaction.response.edit_message(embed=embed, view=self)
            except ValueError:
                await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)

    async def set_unlock_condition(self, interaction: discord.Interaction):
        """Set unlock condition with dropdown"""
        view = SkillPropertySelectView(self, "unlock_condition", ["Level", "Quest", "Defeat", "Purchase"])
        embed = discord.Embed(
            title="🔓 **SELECT UNLOCK CONDITION** 🔓",
            description="Choose how this skill is unlocked",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def set_image_and_emoji(self, interaction: discord.Interaction):
        """Set image and custom emoji for the skill"""
        modal = ItemCreationView.ImageEmojiModal("", self.skill_data['custom_emoji'])

        async def modal_callback(modal_interaction):
            if modal.emoji_input.value:
                self.skill_data['custom_emoji'] = modal.emoji_input.value
            if modal.emoji_name_input.value:
                self.skill_data['emoji_name'] = modal.emoji_name_input.value

            self.update_buttons()
            embed = await self.create_embed()
            await modal_interaction.response.edit_message(embed=embed, view=self)

        modal.on_submit = modal_callback
        await interaction.response.send_modal(modal)


class SkillOwnerTypeSelectView(ui.View):
    """View for selecting skill owner type"""

    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @ui.select(placeholder="Choose owner type...", options=[
        discord.SelectOption(label="Hero", description="Skill belongs to a specific hero", emoji="👤"),
        discord.SelectOption(label="Item", description="Skill belongs to a weapon/item", emoji="⚔️"),
        discord.SelectOption(label="Boss", description="Skill belongs to a boss", emoji="👹"),
        discord.SelectOption(label="Shadow", description="Skill belongs to a shadow", emoji="👤"),
        discord.SelectOption(label="Global", description="Universal skill available to all", emoji="🌍")
    ])
    async def select_owner_type(self, interaction: discord.Interaction, select: ui.Select):
        self.parent_view.skill_data['owner_type'] = select.values[0]
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class SkillPropertySelectView(ui.View):
    """Generic view for selecting skill properties"""

    def __init__(self, parent_view, property_name, options):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.property_name = property_name

        # Create select options
        select_options = [discord.SelectOption(label=option, value=option) for option in options]

        select = ui.Select(placeholder=f"Choose {property_name}...", options=select_options)
        select.callback = self.select_property
        self.add_item(select)

    async def select_property(self, interaction: discord.Interaction):
        select = interaction.data['values'][0]
        self.parent_view.skill_data[self.property_name] = select
        self.parent_view.update_buttons()
        embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

    async def set_stats(self, interaction: discord.Interaction):
        # Simplified stats setting
        self.skill_data.update({
            'damage': 100,
            'mp_cost': 50,
            'required_level': 1
        })
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_skill(self, interaction: discord.Interaction):
        """Create the skill and save it"""
        try:
            # Note: This is simplified - you may need to import proper enums
            embed = discord.Embed(
                title="✅ **SKILL CREATED SUCCESSFULLY** ✅",
                description=f"**{self.skill_data['name']}** has been created for {self.skill_data['character']}!",
                color=discord.Color.green()
            )

            embed.add_field(name="👤 **Character**", value=self.skill_data['character'], inline=True)
            embed.add_field(name="🌟 **Type**", value=self.skill_data['skill_type'], inline=True)
            embed.add_field(name="🔥 **Element**", value=self.skill_data['element'], inline=True)
            embed.add_field(name="💥 **Damage**", value=f"{self.skill_data['damage']}%", inline=True)
            embed.add_field(name="💙 **MP Cost**", value=f"{self.skill_data['mp_cost']}", inline=True)
            embed.add_field(name="📊 **Required Level**", value=f"{self.skill_data['required_level']}", inline=True)
            embed.set_footer(text="Skill is now available in the game!")

            # Add emoji to emojis.json if provided
            if self.skill_data['custom_emoji']:
                skill_id = extractId(self.skill_data['name'])
                await self.add_emoji_to_json(skill_id, self.skill_data['custom_emoji'])

            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **CREATION FAILED** ❌",
                description=f"Failed to create skill: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

    async def add_emoji_to_json(self, skill_id, emoji_string):
        """Add custom emoji to emojis.json file"""
        try:
            import json
            import re

            # Validate emoji format (should be <:name:id> or <a:name:id>)
            if emoji_string and not re.match(r'<a?:\w+:\d+>', emoji_string):
                print(f"⚠️ Warning: Skill emoji '{emoji_string}' is not in Discord format <:name:id>")
                return False

            # Load current emojis
            try:
                with open('emojis.json', 'r') as f:
                    emojis = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                emojis = {}

            # Add the new emoji
            emojis[skill_id] = emoji_string

            # Save back to file with proper encoding
            with open('emojis.json', 'w', encoding='utf-8') as f:
                json.dump(emojis, f, indent=2, ensure_ascii=False)

            print(f"✅ Added skill emoji to emojis.json: {skill_id} -> {emoji_string}")
            return True

        except Exception as e:
            print(f"❌ Failed to add skill emoji to emojis.json: {e}")
            return False


class WorldBossCreationView(ui.View):
    """Interactive world boss creation from shadows"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.selected_shadow = None
        self.boss_data = {
            'name': '',
            'description': '',
            'health_multiplier': 10,
            'attack_multiplier': 2,
            'defense_multiplier': 1.5,
            'custom_emoji': '',
            'emoji_name': ''
        }
        self.current_step = 'select'
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content creation commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create embed based on current step"""
        if self.current_step == 'select':
            return await self.create_selection_embed()
        elif self.current_step == 'configure':
            return await self.create_configuration_embed()
        elif self.current_step == 'review':
            return await self.create_review_embed()
        else:
            return await self.create_selection_embed()

    async def create_selection_embed(self):
        """Create shadow selection embed"""
        embed = discord.Embed(
            title="🌍 **WORLD BOSS CREATION** 🌍",
            description="Create a world boss from existing shadows",
            color=discord.Color.dark_red()
        )

        embed.add_field(
            name="📋 **Instructions**",
            value=(
                "1. Select a shadow to convert into a world boss\n"
                "2. Configure boss multipliers and properties\n"
                "3. Review and create the world boss\n\n"
                "World bosses are powerful versions of shadows that spawn globally!"
            ),
            inline=False
        )

        if self.selected_shadow:
            embed.add_field(
                name="👤 **Selected Shadow**",
                value=f"**{self.selected_shadow.name}**\n*{self.selected_shadow.description}*",
                inline=False
            )

        return embed

    async def create_configuration_embed(self):
        """Create configuration embed"""
        embed = discord.Embed(
            title="🌍 **WORLD BOSS CONFIGURATION** 🌍",
            description=f"Configure world boss: **{self.selected_shadow.name}**",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📝 **Boss Settings**",
            value=(
                f"**Name**: {self.boss_data['name'] or f'{self.selected_shadow.name} (World Boss)'}\n"
                f"**Description**: {self.boss_data['description'] or f'World boss version of {self.selected_shadow.name}'}\n"
                f"**Health Multiplier**: x{self.boss_data['health_multiplier']}\n"
                f"**Attack Multiplier**: x{self.boss_data['attack_multiplier']}\n"
                f"**Defense Multiplier**: x{self.boss_data['defense_multiplier']}"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Calculated Stats**",
            value=(
                f"**Base Attack**: {self.selected_shadow.attack}% → {int(self.selected_shadow.attack * self.boss_data['attack_multiplier'])}%\n"
                f"**Base Defense**: {self.selected_shadow.defense}% → {int(self.selected_shadow.defense * self.boss_data['defense_multiplier'])}%\n"
                f"**Estimated Health**: {10000 * self.boss_data['health_multiplier']:,} HP"
            ),
            inline=False
        )

        return embed

    async def create_review_embed(self):
        """Create final review embed"""
        embed = discord.Embed(
            title="🌍 **WORLD BOSS REVIEW** 🌍",
            description=f"Review your world boss: **{self.boss_data['name'] or f'{self.selected_shadow.name} (World Boss)'}**",
            color=discord.Color.green()
        )

        embed.add_field(
            name="👤 **Source Shadow**",
            value=f"**{self.selected_shadow.name}**\n*{self.selected_shadow.description}*",
            inline=False
        )

        embed.add_field(
            name="🌍 **World Boss Stats**",
            value=(
                f"**Name**: {self.boss_data['name'] or f'{self.selected_shadow.name} (World Boss)'}\n"
                f"**Attack**: {int(self.selected_shadow.attack * self.boss_data['attack_multiplier'])}%\n"
                f"**Defense**: {int(self.selected_shadow.defense * self.boss_data['defense_multiplier'])}%\n"
                f"**Health**: {10000 * self.boss_data['health_multiplier']:,} HP"
            ),
            inline=False
        )

        return embed

    def update_buttons(self):
        """Update buttons based on current step"""
        self.clear_items()

        if self.current_step == 'select':
            # Shadow selection dropdown will be added dynamically
            select_btn = ui.Button(label="📋 Select Shadow", style=discord.ButtonStyle.primary, row=0)
            select_btn.callback = self.show_shadow_selection
            self.add_item(select_btn)

            if self.selected_shadow:
                next_btn = ui.Button(label="➡️ Configure", style=discord.ButtonStyle.success, row=1)
                next_btn.callback = self.go_to_configure
                self.add_item(next_btn)

        elif self.current_step == 'configure':
            # Configuration buttons
            name_btn = ui.Button(label="📝 Set Name", style=discord.ButtonStyle.primary, row=0)
            name_btn.callback = self.set_name
            self.add_item(name_btn)

            desc_btn = ui.Button(label="📄 Set Description", style=discord.ButtonStyle.primary, row=0)
            desc_btn.callback = self.set_description
            self.add_item(desc_btn)

            # Multiplier buttons
            health_btn = ui.Button(label=f"❤️ Health: x{self.boss_data['health_multiplier']}", style=discord.ButtonStyle.secondary, row=1)
            health_btn.callback = self.set_health_multiplier
            self.add_item(health_btn)

            attack_btn = ui.Button(label=f"⚔️ Attack: x{self.boss_data['attack_multiplier']}", style=discord.ButtonStyle.secondary, row=1)
            attack_btn.callback = self.set_attack_multiplier
            self.add_item(attack_btn)

            defense_btn = ui.Button(label=f"🛡️ Defense: x{self.boss_data['defense_multiplier']}", style=discord.ButtonStyle.secondary, row=1)
            defense_btn.callback = self.set_defense_multiplier
            self.add_item(defense_btn)

            # Navigation
            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=2)
            back_btn.callback = self.go_to_select
            self.add_item(back_btn)

            next_btn = ui.Button(label="➡️ Review", style=discord.ButtonStyle.success, row=2)
            next_btn.callback = self.go_to_review
            self.add_item(next_btn)

        elif self.current_step == 'review':
            # Final actions
            create_btn = ui.Button(label="✅ Create World Boss", style=discord.ButtonStyle.success, row=0)
            create_btn.callback = self.create_world_boss
            self.add_item(create_btn)

            back_btn = ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary, row=0)
            back_btn.callback = self.go_to_configure
            self.add_item(back_btn)

    # Callback methods will be added here - for now using simplified versions
    async def show_shadow_selection(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shadow selection coming soon!", ephemeral=True)

    async def set_name(self, interaction: discord.Interaction):
        await interaction.response.send_message("Name setting coming soon!", ephemeral=True)

    async def set_description(self, interaction: discord.Interaction):
        await interaction.response.send_message("Description setting coming soon!", ephemeral=True)

    async def set_health_multiplier(self, interaction: discord.Interaction):
        await interaction.response.send_message("Health multiplier setting coming soon!", ephemeral=True)

    async def set_attack_multiplier(self, interaction: discord.Interaction):
        await interaction.response.send_message("Attack multiplier setting coming soon!", ephemeral=True)

    async def set_defense_multiplier(self, interaction: discord.Interaction):
        await interaction.response.send_message("Defense multiplier setting coming soon!", ephemeral=True)

    async def go_to_configure(self, interaction: discord.Interaction):
        self.current_step = 'configure'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_select(self, interaction: discord.Interaction):
        self.current_step = 'select'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def go_to_review(self, interaction: discord.Interaction):
        self.current_step = 'review'
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_world_boss(self, interaction: discord.Interaction):
        await interaction.response.send_message("World boss creation coming soon!", ephemeral=True)


class ContentDeletionView(ui.View):
    """Content deletion interface for all content types"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.current_type = "main"
        self.selected_items = []
        self.content_list = []
        self.current_page = 0
        self.items_per_page = 10
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content deletion commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create deletion interface embed"""
        if self.current_type == "main":
            embed = discord.Embed(
                title="🗑️ **CONTENT DELETION PANEL** 🗑️",
                description="⚠️ **WARNING**: Deletion is permanent and cannot be undone!",
                color=discord.Color.red()
            )

            embed.add_field(
                name="📋 **Available Deletion Options**",
                value=(
                    "• **Items/Weapons** - Delete specific weapons and items\n"
                    "• **Heroes** - Remove specific heroes and characters\n"
                    "• **Bosses** - Delete specific boss encounters\n"
                    "• **Shadows** - Remove specific shadow entities\n"
                    "• **Skills** - Delete specific character skills"
                ),
                inline=False
            )

            embed.add_field(
                name="⚠️ **Safety Features**",
                value=(
                    "• **Individual Selection** - Choose specific items to delete\n"
                    "• **Confirmation Required** - Multiple confirmations before deletion\n"
                    "• **Preview System** - See exactly what will be deleted\n"
                    "• **No Bulk Delete** - Cannot delete everything at once"
                ),
                inline=False
            )

        elif self.current_type in ["items", "heroes", "bosses", "shadows", "skills", "shop_items"]:
            embed = discord.Embed(
                title=f"🗑️ **DELETE {self.current_type.upper().replace('_', ' ')}** 🗑️",
                description=f"Select specific {self.current_type.replace('_', ' ')} to delete. **This action is permanent!**",
                color=discord.Color.red()
            )

            if self.content_list:
                # Show current page of items
                start_idx = self.current_page * self.items_per_page
                end_idx = min(start_idx + self.items_per_page, len(self.content_list))

                items_text = ""
                for i in range(start_idx, end_idx):
                    item = self.content_list[i]
                    status = "✅" if item['id'] in self.selected_items else "⬜"
                    items_text += f"{status} **{item['name']}** (ID: `{item['id']}`)\n"

                embed.add_field(
                    name=f"📋 **{self.current_type.title()} List** (Page {self.current_page + 1}/{(len(self.content_list) - 1) // self.items_per_page + 1})",
                    value=items_text or "No items found",
                    inline=False
                )

                if self.selected_items:
                    embed.add_field(
                        name="🎯 **Selected for Deletion**",
                        value=f"**{len(self.selected_items)}** {self.current_type} selected",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="📭 **No Content Found**",
                    value=f"No {self.current_type} found in the database.",
                    inline=False
                )

        return embed

    def update_buttons(self):
        """Update buttons based on current type"""
        self.clear_items()

        if self.current_type == "main":
            # Content type buttons
            item_btn = ui.Button(label="⚔️ Delete Items", style=discord.ButtonStyle.danger, row=0)
            item_btn.callback = self.show_items
            self.add_item(item_btn)

            hero_btn = ui.Button(label="👥 Delete Heroes", style=discord.ButtonStyle.danger, row=0)
            hero_btn.callback = self.show_heroes
            self.add_item(hero_btn)

            boss_btn = ui.Button(label="👹 Delete Bosses", style=discord.ButtonStyle.danger, row=1)
            boss_btn.callback = self.show_bosses
            self.add_item(boss_btn)

            shadow_btn = ui.Button(label="👤 Delete Shadows", style=discord.ButtonStyle.danger, row=1)
            shadow_btn.callback = self.show_shadows
            self.add_item(shadow_btn)

            skill_btn = ui.Button(label="🌟 Delete Skills", style=discord.ButtonStyle.danger, row=2)
            skill_btn.callback = self.show_skills
            self.add_item(skill_btn)

            shop_btn = ui.Button(label="🛒 Delete Shop Items", style=discord.ButtonStyle.danger, row=2)
            shop_btn.callback = self.show_shop_items
            self.add_item(shop_btn)

        elif self.current_type in ["items", "heroes", "bosses", "shadows", "skills", "shop_items"]:
            # Item selection interface
            if self.content_list:
                # Page navigation
                if self.current_page > 0:
                    prev_btn = ui.Button(label="⬅️ Previous", style=discord.ButtonStyle.secondary, row=0)
                    prev_btn.callback = self.previous_page
                    self.add_item(prev_btn)

                if (self.current_page + 1) * self.items_per_page < len(self.content_list):
                    next_btn = ui.Button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
                    next_btn.callback = self.next_page
                    self.add_item(next_btn)

                # Selection buttons for current page items
                start_idx = self.current_page * self.items_per_page
                end_idx = min(start_idx + self.items_per_page, len(self.content_list))

                for i in range(start_idx, min(start_idx + 5, end_idx)):  # Max 5 buttons per row
                    item = self.content_list[i]
                    is_selected = item['id'] in self.selected_items
                    btn_style = discord.ButtonStyle.success if is_selected else discord.ButtonStyle.secondary
                    btn_label = f"✅ {item['name'][:15]}" if is_selected else f"⬜ {item['name'][:15]}"

                    btn = ui.Button(label=btn_label, style=btn_style, row=1)
                    btn.callback = lambda interaction, item_id=item['id']: self.toggle_selection(interaction, item_id)
                    self.add_item(btn)

                # Second row of selection buttons if needed
                for i in range(start_idx + 5, end_idx):
                    item = self.content_list[i]
                    is_selected = item['id'] in self.selected_items
                    btn_style = discord.ButtonStyle.success if is_selected else discord.ButtonStyle.secondary
                    btn_label = f"✅ {item['name'][:15]}" if is_selected else f"⬜ {item['name'][:15]}"

                    btn = ui.Button(label=btn_label, style=btn_style, row=2)
                    btn.callback = lambda interaction, item_id=item['id']: self.toggle_selection(interaction, item_id)
                    self.add_item(btn)

                # Action buttons
                if self.selected_items:
                    delete_btn = ui.Button(label=f"🗑️ Delete Selected ({len(self.selected_items)})", style=discord.ButtonStyle.danger, row=3)
                    delete_btn.callback = self.confirm_deletion
                    self.add_item(delete_btn)

                clear_btn = ui.Button(label="🔄 Clear Selection", style=discord.ButtonStyle.secondary, row=3)
                clear_btn.callback = self.clear_selection
                self.add_item(clear_btn)

            # Back button
            back_btn = ui.Button(label="⬅️ Back to Main", style=discord.ButtonStyle.primary, row=4)
            back_btn.callback = self.back_to_main
            self.add_item(back_btn)

    # Content loading methods
    async def show_items(self, interaction: discord.Interaction):
        """Show items for deletion selection"""
        try:
            all_items = await ItemManager.get_all()
            self.content_list = [{'id': item.id, 'name': item.name} for item in all_items]
            self.current_type = "items"
            self.selected_items = []
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load items: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_heroes(self, interaction: discord.Interaction):
        """Show heroes for deletion selection"""
        try:
            all_heroes = await HeroManager.get_all()
            self.content_list = [{'id': hero.id, 'name': hero.name} for hero in all_heroes]
            self.current_type = "heroes"
            self.selected_items = []
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load heroes: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_bosses(self, interaction: discord.Interaction):
        """Show bosses for deletion selection"""
        try:
            # Assuming Boss has a get_all method similar to others
            from structure.boss import Boss
            all_bosses = await Boss.get_all()
            self.content_list = [{'id': boss.id, 'name': boss.name} for boss in all_bosses]
            self.current_type = "bosses"
            self.selected_items = []
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load bosses: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_shadows(self, interaction: discord.Interaction):
        """Show shadows for deletion selection"""
        try:
            all_shadows = await Shadow.get_all()
            self.content_list = [{'id': shadow.id, 'name': shadow.name} for shadow in all_shadows]
            self.current_type = "shadows"
            self.selected_items = []
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load shadows: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_skills(self, interaction: discord.Interaction):
        """Show skills for deletion selection"""
        try:
            # This would need to be implemented based on your skill system
            embed = discord.Embed(
                title="🌟 **SKILL DELETION** 🌟",
                description="Skill deletion system needs skill database implementation.",
                color=discord.Color.orange()
            )
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load skills: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_shop_items(self, interaction: discord.Interaction):
        """Show shop items for deletion selection"""
        try:
            shop = Shop()
            all_shop_items = shop.get_all_items()
            self.content_list = [{'id': item['id'], 'name': item['name']} for item in all_shop_items]
            self.current_type = "shop_items"
            self.selected_items = []
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load shop items: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    # Navigation methods
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if (self.current_page + 1) * self.items_per_page < len(self.content_list):
            self.current_page += 1
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def toggle_selection(self, interaction: discord.Interaction, item_id: str):
        """Toggle item selection"""
        if item_id in self.selected_items:
            self.selected_items.remove(item_id)
        else:
            self.selected_items.append(item_id)

        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def clear_selection(self, interaction: discord.Interaction):
        """Clear all selections"""
        self.selected_items = []
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_main(self, interaction: discord.Interaction):
        """Go back to main deletion menu"""
        self.current_type = "main"
        self.selected_items = []
        self.content_list = []
        self.current_page = 0
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def confirm_deletion(self, interaction: discord.Interaction):
        """Show confirmation dialog for deletion"""
        if not self.selected_items:
            await interaction.response.send_message("❌ No items selected for deletion!", ephemeral=True)
            return

        # Get names of selected items for confirmation
        selected_names = []
        for item in self.content_list:
            if item['id'] in self.selected_items:
                selected_names.append(item['name'])

        embed = discord.Embed(
            title="⚠️ **CONFIRM DELETION** ⚠️",
            description=f"**YOU ARE ABOUT TO PERMANENTLY DELETE {len(self.selected_items)} {self.current_type.upper()}!**",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🗑️ **Items to be deleted:**",
            value="\n".join([f"• **{name}**" for name in selected_names[:10]]) +
                  (f"\n• ... and {len(selected_names) - 10} more" if len(selected_names) > 10 else ""),
            inline=False
        )

        embed.add_field(
            name="⚠️ **WARNING**",
            value=(
                "**THIS ACTION CANNOT BE UNDONE!**\n"
                "• Items will be removed from all players\n"
                "• All associated data will be lost\n"
                "• This is PERMANENT deletion"
            ),
            inline=False
        )

        # Create confirmation view
        confirm_view = ConfirmDeletionView(self, self.selected_items, self.current_type)
        await interaction.response.edit_message(embed=embed, view=confirm_view)


class ConfirmDeletionView(ui.View):
    """Confirmation view for deletion with safety measures"""

    def __init__(self, parent_view, selected_items, content_type):
        super().__init__(timeout=300)  # 5 minute timeout for safety
        self.parent_view = parent_view
        self.selected_items = selected_items
        self.content_type = content_type
        self.confirmation_step = 0  # Multi-step confirmation

    @ui.button(label="❌ CANCEL - Keep Items Safe", style=discord.ButtonStyle.success, row=0)
    async def cancel_deletion(self, interaction: discord.Interaction, button: ui.Button):
        """Cancel deletion and go back"""
        embed = discord.Embed(
            title="✅ **DELETION CANCELLED** ✅",
            description="Your items are safe! No deletion was performed.",
            color=discord.Color.green()
        )

        # Go back to selection view
        self.parent_view.update_buttons()
        parent_embed = await self.parent_view.create_embed()
        await interaction.response.edit_message(embed=parent_embed, view=self.parent_view)

    @ui.button(label="⚠️ I UNDERSTAND - PROCEED TO DELETE", style=discord.ButtonStyle.danger, row=1)
    async def proceed_deletion(self, interaction: discord.Interaction, button: ui.Button):
        """Proceed with deletion after confirmation"""
        if self.confirmation_step == 0:
            # First confirmation step
            self.confirmation_step = 1
            embed = discord.Embed(
                title="⚠️ **FINAL CONFIRMATION** ⚠️",
                description=f"**LAST CHANCE TO CANCEL!**\n\nYou are about to delete **{len(self.selected_items)} {self.content_type}** permanently.",
                color=discord.Color.red()
            )

            embed.add_field(
                name="🚨 **FINAL WARNING**",
                value=(
                    "**THIS IS YOUR LAST CHANCE TO CANCEL!**\n"
                    "• Click **CANCEL** to keep your items safe\n"
                    "• Click **DELETE NOW** to permanently remove them\n"
                    "• There is NO way to recover deleted items"
                ),
                inline=False
            )

            # Update buttons for final confirmation
            self.clear_items()

            cancel_btn = ui.Button(label="✅ CANCEL - I Changed My Mind", style=discord.ButtonStyle.success, row=0)
            cancel_btn.callback = self.cancel_deletion
            self.add_item(cancel_btn)

            delete_btn = ui.Button(label="🗑️ DELETE NOW - I'M SURE", style=discord.ButtonStyle.danger, row=1)
            delete_btn.callback = self.execute_deletion
            self.add_item(delete_btn)

            await interaction.response.edit_message(embed=embed, view=self)

    async def execute_deletion(self, interaction: discord.Interaction):
        """Actually perform the deletion"""
        try:
            deleted_count = 0
            failed_deletions = []

            for item_id in self.selected_items:
                try:
                    if self.content_type == "items":
                        await ItemManager.delete(item_id)
                    elif self.content_type == "heroes":
                        await HeroManager.delete(item_id)
                    elif self.content_type == "bosses":
                        from structure.boss import Boss
                        await Boss.delete(item_id)
                    elif self.content_type == "shadows":
                        await Shadow.delete(item_id)
                    elif self.content_type == "shop_items":
                        shop = Shop()
                        shop.delete_item(item_id)

                    deleted_count += 1
                except Exception as e:
                    failed_deletions.append(f"{item_id}: {str(e)}")

            # Create result embed
            if deleted_count > 0:
                embed = discord.Embed(
                    title="✅ **DELETION COMPLETED** ✅",
                    description=f"Successfully deleted **{deleted_count}** {self.content_type}!",
                    color=discord.Color.green()
                )

                if failed_deletions:
                    embed.add_field(
                        name="⚠️ **Some Deletions Failed**",
                        value="\n".join(failed_deletions[:5]) +
                              (f"\n... and {len(failed_deletions) - 5} more" if len(failed_deletions) > 5 else ""),
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="❌ **DELETION FAILED** ❌",
                    description="No items were deleted due to errors.",
                    color=discord.Color.red()
                )

                if failed_deletions:
                    embed.add_field(
                        name="❌ **Errors**",
                        value="\n".join(failed_deletions[:5]),
                        inline=False
                    )

            # Go back to main menu
            self.parent_view.current_type = "main"
            self.parent_view.selected_items = []
            self.parent_view.content_list = []
            self.parent_view.update_buttons()
            main_embed = await self.parent_view.create_embed()

            await interaction.response.edit_message(embed=embed, view=None)

            # Send new main menu after a brief delay
            import asyncio
            await asyncio.sleep(3)
            await interaction.followup.edit_message(interaction.message.id, embed=main_embed, view=self.parent_view)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **DELETION ERROR** ❌",
                description=f"An error occurred during deletion: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)


class ContentEditingView(ui.View):
    """Content editing interface for all content types"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.current_type = "main"
        self.selected_item = None
        self.content_list = []
        self.current_page = 0
        self.items_per_page = 10
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_bot_admin(interaction.user.id):
            await interaction.response.send_message("🚫 You are not authorized to use content editing commands.", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create editing interface embed"""
        if self.current_type == "main":
            embed = discord.Embed(
                title="✏️ **CONTENT EDITING PANEL** ✏️",
                description="Select content type to edit existing items",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📋 **Available Editing Options**",
                value=(
                    "• **Items/Weapons** - Edit existing weapons and items\n"
                    "• **Heroes** - Modify existing heroes and characters\n"
                    "• **Bosses** - Edit existing boss encounters\n"
                    "• **Shadows** - Modify existing shadow entities\n"
                    "• **Skills** - Edit existing character skills"
                ),
                inline=False
            )

            embed.add_field(
                name="✏️ **Editing Features**",
                value=(
                    "• **Select & Edit** - Choose specific items to modify\n"
                    "• **All Properties** - Edit stats, descriptions, images, emojis\n"
                    "• **Preview Changes** - See modifications before saving\n"
                    "• **Safe Updates** - Changes are saved properly to database"
                ),
                inline=False
            )

        elif self.current_type in ["items", "heroes", "bosses", "shadows", "skills"]:
            embed = discord.Embed(
                title=f"✏️ **EDIT {self.current_type.upper()}** ✏️",
                description=f"Select a {self.current_type[:-1]} to edit",
                color=discord.Color.blue()
            )

            if self.content_list:
                # Show current page of items
                start_idx = self.current_page * self.items_per_page
                end_idx = min(start_idx + self.items_per_page, len(self.content_list))

                items_text = ""
                for i in range(start_idx, end_idx):
                    item = self.content_list[i]
                    items_text += f"📝 **{item['name']}** (ID: `{item['id']}`)\n"

                embed.add_field(
                    name=f"📋 **{self.current_type.title()} List** (Page {self.current_page + 1}/{(len(self.content_list) - 1) // self.items_per_page + 1})",
                    value=items_text or "No items found",
                    inline=False
                )
            else:
                embed.add_field(
                    name="📭 **No Content Found**",
                    value=f"No {self.current_type} found in the database.",
                    inline=False
                )

        return embed

    def update_buttons(self):
        """Update buttons based on current type"""
        self.clear_items()

        if self.current_type == "main":
            # Content type buttons
            item_btn = ui.Button(label="⚔️ Edit Items", style=discord.ButtonStyle.primary, row=0)
            item_btn.callback = self.show_items_for_edit
            self.add_item(item_btn)

            hero_btn = ui.Button(label="👥 Edit Heroes", style=discord.ButtonStyle.primary, row=0)
            hero_btn.callback = self.show_heroes_for_edit
            self.add_item(hero_btn)

            boss_btn = ui.Button(label="👹 Edit Bosses", style=discord.ButtonStyle.primary, row=1)
            boss_btn.callback = self.show_bosses_for_edit
            self.add_item(boss_btn)

            shadow_btn = ui.Button(label="👤 Edit Shadows", style=discord.ButtonStyle.primary, row=1)
            shadow_btn.callback = self.show_shadows_for_edit
            self.add_item(shadow_btn)

        elif self.current_type in ["items", "heroes", "bosses", "shadows", "skills"]:
            # Item selection interface
            if self.content_list:
                # Page navigation
                if self.current_page > 0:
                    prev_btn = ui.Button(label="⬅️ Previous", style=discord.ButtonStyle.secondary, row=0)
                    prev_btn.callback = self.previous_page
                    self.add_item(prev_btn)

                if (self.current_page + 1) * self.items_per_page < len(self.content_list):
                    next_btn = ui.Button(label="➡️ Next", style=discord.ButtonStyle.secondary, row=0)
                    next_btn.callback = self.next_page
                    self.add_item(next_btn)

                # Selection buttons for current page items
                start_idx = self.current_page * self.items_per_page
                end_idx = min(start_idx + self.items_per_page, len(self.content_list))

                for i in range(start_idx, min(start_idx + 5, end_idx)):  # Max 5 buttons per row
                    item = self.content_list[i]
                    btn_label = f"✏️ {item['name'][:15]}"

                    btn = ui.Button(label=btn_label, style=discord.ButtonStyle.success, row=1)
                    btn.callback = lambda interaction, item_data=item: self.edit_item(interaction, item_data)
                    self.add_item(btn)

                # Second row of selection buttons if needed
                for i in range(start_idx + 5, end_idx):
                    item = self.content_list[i]
                    btn_label = f"✏️ {item['name'][:15]}"

                    btn = ui.Button(label=btn_label, style=discord.ButtonStyle.success, row=2)
                    btn.callback = lambda interaction, item_data=item: self.edit_item(interaction, item_data)
                    self.add_item(btn)

            # Back button
            back_btn = ui.Button(label="⬅️ Back to Main", style=discord.ButtonStyle.primary, row=4)
            back_btn.callback = self.back_to_main
            self.add_item(back_btn)

    # Content loading methods (similar to deletion view)
    async def show_items_for_edit(self, interaction: discord.Interaction):
        """Show items for editing selection"""
        try:
            all_items = await ItemManager.get_all()
            self.content_list = [{'id': item.id, 'name': item.name} for item in all_items]
            self.current_type = "items"
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load items: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_heroes_for_edit(self, interaction: discord.Interaction):
        """Show heroes for editing selection"""
        try:
            all_heroes = await HeroManager.get_all()
            self.content_list = [{'id': hero.id, 'name': hero.name} for hero in all_heroes]
            self.current_type = "heroes"
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load heroes: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_bosses_for_edit(self, interaction: discord.Interaction):
        """Show bosses for editing selection"""
        try:
            from structure.boss import Boss
            all_bosses = await Boss.get_all()
            self.content_list = [{'id': boss.id, 'name': boss.name} for boss in all_bosses]
            self.current_type = "bosses"
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load bosses: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    async def show_shadows_for_edit(self, interaction: discord.Interaction):
        """Show shadows for editing selection"""
        try:
            all_shadows = await Shadow.get_all()
            self.content_list = [{'id': shadow.id, 'name': shadow.name} for shadow in all_shadows]
            self.current_type = "shadows"
            self.current_page = 0
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = discord.Embed(
                title="❌ **ERROR** ❌",
                description=f"Failed to load shadows: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

    # Navigation methods
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if (self.current_page + 1) * self.items_per_page < len(self.content_list):
            self.current_page += 1
            self.update_buttons()
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_main(self, interaction: discord.Interaction):
        """Go back to main editing menu"""
        self.current_type = "main"
        self.content_list = []
        self.current_page = 0
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def edit_item(self, interaction: discord.Interaction, item_data):
        """Edit a specific item"""
        embed = discord.Embed(
            title="✏️ **ITEM EDITING** ✏️",
            description=f"Editing functionality for **{item_data['name']}** coming soon!\n\nThis will open the same creation interface but pre-filled with existing data.",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🔧 **Planned Features**",
            value=(
                "• Load existing item data into creation interface\n"
                "• Edit all properties (stats, description, image, emoji)\n"
                "• Preview changes before saving\n"
                "• Update database with modified data"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(CreateCog(bot))