import discord
from discord.ext import commands
from discord import app_commands, ui
from rapidfuzz import process, fuzz
import math
import logging
from typing import Literal

from structure.player import Player
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.emoji import getEmoji, getClassEmoji, getRarityEmoji
from utilis.utilis import (
    get_emoji_url,
    getStatHunter,
    getStatWeapon,
    player_hunter_autocomplete,
    player_item_autocomplete,
    create_progress_bar,
    create_embed,
    SUCCESS_COLOR,
    ERROR_COLOR,
    INFO_COLOR,
    WARNING_COLOR
)
from commands.missions import track_mission_progress

# --- CONFIGURATION ---
GEAR_MAP = {
    "gear i": "Gear I", "gear1": "Gear I", "1": "Gear I", "g1": "Gear I",
    "gear ii": "Gear II", "gear2": "Gear II", "2": "Gear II", "g2": "Gear II",
    "gear iii": "Gear III", "gear3": "Gear III", "3": "Gear III", "g3": "Gear III"
}
XP_PER_GEAR = {"Gear I": 100, "Gear II": 500, "Gear III": 1000}
GEAR_ATTR_MAP = {"Gear I": "gear1", "Gear II": "gear2", "Gear III": "gear3"}
ITEMS_PER_PAGE = 9
ELEMENT_COLORS = {
    "Dark": 0x5865F2, "Light": 0xFEE75C, "Water": 0x3498DB,
    "Fire": 0xE74C3C, "Wind": 0x2ECC71
}

# --- INTERACTIVE UPGRADE MODAL ---
class UpgradeModal(ui.Modal, title="Upgrade Entity"):
    def __init__(self, cog, entity_data, is_hunter):
        super().__init__()
        self.cog = cog
        self.entity_data = entity_data
        self.is_hunter = is_hunter

    gear_type = ui.TextInput(label="Gear Type", placeholder="e.g., Gear I, g2, 3")
    quantity = ui.TextInput(label="Quantity", placeholder="e.g., 10", default="1")

    async def on_submit(self, interaction: discord.Interaction):
        # The modal automatically defers, so we use followup to respond.
        # We pass the interaction so the handler function can respond.
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                await interaction.response.send_message("Quantity must be a positive number.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Please enter a valid number for quantity.", ephemeral=True)
            return

        await self.cog._handle_upgrade(
            interaction,
            self.entity_data['details'].name,
            self.gear_type.value,
            qty,
            self.is_hunter
        )

# --- INTERACTIVE INFO CARD VIEW ---
class EntityInfoView(ui.View):
    def __init__(self, ctx, cog, entity_data, is_hunter):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.cog = cog
        self.entity_data = entity_data
        self.is_hunter = is_hunter

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not for you.", ephemeral=True)
            return False
        return True

    @ui.button(label="Use sl upgrade", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def redirect_to_upgrade(self, interaction: discord.Interaction, button: ui.Button):
        item_type = "Hunter" if self.is_hunter else "Weapon"
        embed = discord.Embed(
            title="🔄 **Use New Upgrade System**",
            description=(
                f"**For upgrading this {item_type.lower()}, please use the new system:**\n\n"
                f"🆕 **Type `sl upgrade`** and select:\n"
                f"• **{'👤 Upgrade a Hunter' if self.is_hunter else '🗡️ Upgrade a Weapon'}**\n\n"
                "**Benefits of the new system:**\n"
                "• ✨ Better interface with interactive buttons\n"
                "• 📊 Complete upgrade tracking\n"
                "• 🎯 Material requirement validation\n"
                "• 🔍 Smart filtering and sorting\n"
                "• 🧮 Comprehensive cube detection"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="💡 The new system provides a much better experience!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
# --- ADVANCED INVENTORY PAGINATOR VIEW ---
class InventoryPaginatorView(discord.ui.View):
    def __init__(self, ctx, items, item_type):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.all_items = list(items.items())
        self.filtered_items = self.all_items
        self.item_type = item_type
        self.current_page = 0
        self.total_pages = max(1, math.ceil(len(self.filtered_items) / ITEMS_PER_PAGE))
        self.message = None
        self.add_item(InventoryFilterSelect(self))
        self.update_nav_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You cannot control this menu.", ephemeral=True)
            return False
        return True
    
    def update_nav_buttons(self):
        nav_buttons = [item for item in self.children if isinstance(item, discord.ui.Button)]
        for button in nav_buttons:
            self.remove_item(button)

        is_first, is_last = self.current_page == 0, self.current_page >= self.total_pages - 1
        
        self.add_item(discord.ui.Button(emoji="⏪", style=discord.ButtonStyle.blurple, disabled=is_first, custom_id="first", row=1))
        self.add_item(discord.ui.Button(emoji="⬅️", style=discord.ButtonStyle.secondary, disabled=is_first, custom_id="prev", row=1))
        self.add_item(discord.ui.Button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="stop", row=1))
        self.add_item(discord.ui.Button(emoji="➡️", style=discord.ButtonStyle.secondary, disabled=is_last, custom_id="next", row=1))
        self.add_item(discord.ui.Button(emoji="⏩", style=discord.ButtonStyle.blurple, disabled=is_last, custom_id="last", row=1))
        
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.callback = self.on_nav_button_click

    async def on_nav_button_click(self, interaction: discord.Interaction):
        custom_id = interaction.data['custom_id']
        if custom_id == "first": self.current_page = 0
        elif custom_id == "prev": self.current_page -= 1
        elif custom_id == "stop": await interaction.message.delete(); self.stop(); return
        elif custom_id == "next": self.current_page += 1
        elif custom_id == "last": self.current_page = self.total_pages - 1
        
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        self.total_pages = max(1, math.ceil(len(self.filtered_items) / ITEMS_PER_PAGE))
        self.current_page = max(0, min(self.current_page, self.total_pages - 1))
        self.update_nav_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_embed(self):
        start, end = self.current_page * ITEMS_PER_PAGE, (self.current_page + 1) * ITEMS_PER_PAGE
        page_items = self.filtered_items[start:end]

        title = f"{self.ctx.author.display_name}'s {self.item_type.capitalize()} Collection"
        embed = create_embed(title, color=INFO_COLOR, author=self.ctx.author)
        
        description = ""
        manager = HeroManager if self.item_type == "hunter" else ItemManager

        for item_id, item_data in page_items:
            item = await manager.get(item_id)
            if item:
                tier, level = item_data.get('tier', 0), item_data.get('level', 1)
                tier_stars = "★" * tier + "☆" * (5 - tier)
                description += f"{getEmoji(item.id)} **{item.name}** • `{item.type}` • {tier_stars} • `LV {level}`\n"
        
        if not description: description = "No items match your filter criteria."
        embed.description = description
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages} • Displaying {len(page_items)} of {len(self.filtered_items)} items")
        return embed

class InventoryFilterSelect(ui.Select):
    def __init__(self, view: InventoryPaginatorView):
        self.paginator_view = view
        options = [
            discord.SelectOption(label="Sort by Level (High to Low)", value="level_desc", emoji="🔺"),
            discord.SelectOption(label="Sort by Level (Low to High)", value="level_asc", emoji="🔻"),
            discord.SelectOption(label="Sort by Rarity", value="rarity", emoji="✨"),
            discord.SelectOption(label="Filter by Element: Fire", value="fire", emoji=getClassEmoji("Fire")),
            discord.SelectOption(label="Filter by Element: Water", value="water", emoji=getClassEmoji("Water")),
            discord.SelectOption(label="Filter by Element: Wind", value="wind", emoji=getClassEmoji("Wind")),
            discord.SelectOption(label="Filter by Element: Light", value="light", emoji=getClassEmoji("Light")),
            discord.SelectOption(label="Filter by Element: Dark", value="dark", emoji=getClassEmoji("Dark")),
            discord.SelectOption(label="Show All", value="all", emoji="🔄"),
        ]
        super().__init__(placeholder="Filter and sort your inventory...", options=options, row=0)
    
    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        self.paginator_view.current_page = 0
        manager = HeroManager if self.paginator_view.item_type == "hunter" else ItemManager

        if value == "all":
            self.paginator_view.filtered_items = self.paginator_view.all_items
        elif value.startswith("level"):
            reverse = value == "level_desc"
            # Sort by item level - need to get the actual item data
            async def sort_by_level(item_tuple):
                try:
                    item = await manager.get(item_tuple[0])
                    return getattr(item, 'level', 1) if item else 1
                except:
                    return 1

            # Create a list of (sort_key, item_tuple) pairs
            items_with_keys = []
            for item_tuple in self.paginator_view.filtered_items:
                sort_key = await sort_by_level(item_tuple)
                items_with_keys.append((sort_key, item_tuple))

            # Sort by the keys
            items_with_keys.sort(key=lambda x: x[0], reverse=reverse)

            # Extract the sorted item tuples
            self.paginator_view.filtered_items = [item_tuple for _, item_tuple in items_with_keys]
        elif value == "rarity":
            rarity_order = {"SSR": 0, "Super Rare": 1, "Rare": 2}
            async def sort_key(item_tuple):
                item = await manager.get(item_tuple[0])
                return rarity_order.get(item.rarity, 99) if item else 99
            
            sorted_list_with_keys = sorted([(await sort_key(item), item) for item in self.paginator_view.all_items])
            self.paginator_view.filtered_items = [item for _, item in sorted_list_with_keys]
        else:
            self.paginator_view.filtered_items = [
                (item_id, data) for item_id, data in self.paginator_view.all_items
                if (await manager.get(item_id)) and (await manager.get(item_id)).classType.lower() == value
            ]
        await self.paginator_view.update_message(interaction)

# --- MAIN COG ---
class HunterWeaponCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _find_owned_entity(self, player, name: str, is_hunter: bool):
        inventory = player.get_hunters() if is_hunter else player.get_inventory()
        manager = HeroManager if is_hunter else ItemManager
        entity_type_str = "Hunter" if is_hunter else "Weapon"
        if not inventory: return None, f"You don't have any {entity_type_str.lower()}s yet."
        
        owned_names = { (await manager.get(item_id)).name: item_id for item_id in inventory if await manager.get(item_id) }
        if not owned_names: return None, "Could not load details for your items."

        best_match = process.extractOne(name, owned_names.keys(), scorer=fuzz.ratio, score_cutoff=60)
        if not best_match: return None, f"Could not find a {entity_type_str.lower()} named `{name}` in your inventory."

        matched_name, entity_id = best_match[0], owned_names[best_match[0]]
        return {"id": entity_id, "details": await manager.get(entity_id), "player_data": inventory[entity_id]}, None

    # --- HUNTER COMMANDS ---
    @commands.hybrid_group(name="hunter", aliases=["h"], invoke_without_command=True, help="View information about a specific hunter you own.")
    @app_commands.describe(name="The name of the hunter to get info about.")
    @app_commands.autocomplete(name=player_hunter_autocomplete)
    async def hunter(self, ctx: commands.Context, *, name: str):
        player = await Player.get(ctx.author.id)
        if not player: await ctx.send("You don't have a profile yet.", ephemeral=True); return

        entity_data, error_msg = await self._find_owned_entity(player, name, is_hunter=True)
        if error_msg: await ctx.send(error_msg, ephemeral=True); return

        char_info, hunter_data = entity_data['details'], entity_data['player_data']
        level, tier, xp = hunter_data.get("level", 1), hunter_data.get("tier", 0), hunter_data.get("xp", 0)
        xp_needed = level * 100
        xp_bar, tier_stars = create_progress_bar(xp, xp_needed), "★" * tier + "☆" * (5 - tier)
        stats = await getStatHunter(char_info.id, level)

        weapon_text = f"None {getEmoji('slot')}"
        if weapon_id := hunter_data.get("weapon"):
            if weapon_id in player.inventory:
                weapon = await ItemManager.get(weapon_id)
                if weapon: weapon_text = f"{getEmoji(weapon.id)} {weapon.name} (Lv. {player.inventory[weapon_id].get('level', 1)})"

        color = ELEMENT_COLORS.get(char_info.classType, INFO_COLOR)
        embed = create_embed(f"{getClassEmoji(char_info.classType)} {char_info.name}", color=color, author=ctx.author)
        embed.set_thumbnail(url=char_info.image)
        embed.add_field(name="Details", value=f"**Rarity**: {getRarityEmoji(char_info.rarity)}\n**Class**: {char_info.classType}", inline=True)
        embed.add_field(name="Progression", value=f"**Level**: `{level}`\n**Tier**: {tier_stars}", inline=True)
        embed.add_field(name="Experience", value=xp_bar, inline=False)
        embed.add_field(name="Combat Stats", value=f"**Attack**: `{stats.attack}` • **Defense**: `{stats.defense}` • **HP**: `{stats.hp}`", inline=False)
        embed.add_field(name="Equipped Weapon", value=weapon_text, inline=False)

        view = EntityInfoView(ctx, self, entity_data, is_hunter=True)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="hunters", help="View your collection of hunters.")
    async def hunters(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player or not player.get_hunters():
            await ctx.send("You do not own any hunters yet.")
            return

        view = InventoryPaginatorView(ctx, player.get_hunters(), "hunter")
        embed = await view.create_embed()
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
    # --- WEAPON COMMANDS ---
    @commands.hybrid_group(name="weapon", aliases=["w"], invoke_without_command=True, help="View information about a specific weapon you own.")
    @app_commands.describe(name="The name of the weapon to get info about.")
    @app_commands.autocomplete(name=player_item_autocomplete)
    async def weapon(self, ctx: commands.Context, *, name: str):
        player = await Player.get(ctx.author.id)
        if not player: await ctx.send("You don't have a profile yet.", ephemeral=True); return

        entity_data, error_msg = await self._find_owned_entity(player, name, is_hunter=False)
        if error_msg: await ctx.send(error_msg, ephemeral=True); return

        item_info, weapon_data = entity_data['details'], entity_data['player_data']
        level, tier, xp = weapon_data.get("level", 1), weapon_data.get("tier", 0), weapon_data.get("xp", 0)
        xp_needed = (level * 100) + ((level // 10) * 2000)
        xp_bar, tier_stars = create_progress_bar(xp, xp_needed), "★" * tier + "☆" * (5 - tier)
        stats = await getStatWeapon(item_info.id, level)

        color = ELEMENT_COLORS.get(item_info.classType, INFO_COLOR)
        embed = create_embed(f"{getClassEmoji(item_info.classType)} {item_info.name}", color=color, author=ctx.author)
        embed.set_thumbnail(url=item_info.image)
        embed.add_field(name="Details", value=f"**Rarity**: {getRarityEmoji(item_info.rarity)}\n**Class**: {item_info.classType}", inline=True)
        embed.add_field(name="Progression", value=f"**Level**: `{level}`\n**Tier**: {tier_stars}", inline=True)
        embed.add_field(name="Experience", value=xp_bar, inline=False)
        embed.add_field(name="Combat Stats", value=f"**Attack**: `{stats['attack']}` • **Defense**: `{stats['defense']}` • **HP**: `{stats['hp']}`", inline=False)
        embed.add_field(name="Description", value=f"> {item_info.description}", inline=False)
        
        view = EntityInfoView(ctx, self, entity_data, is_hunter=False)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="weapons", help="View your collection of weapons.")
    async def weapons(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player or not player.get_inventory():
            await ctx.send("You do not own any weapons yet.")
            return

        view = InventoryPaginatorView(ctx, player.get_inventory(), "weapon")
        embed = await view.create_embed()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # --- UPGRADE AND BREAK SUBCOMMANDS (DISABLED) ---
    @hunter.command(name="upgrade", help="[DEPRECATED] Use 'sl upgrade' instead.")
    @app_commands.describe(name="The name of the hunter to upgrade.", gear="The gear to use for the upgrade.", quantity="The amount of gear to use.")
    @app_commands.autocomplete(name=player_hunter_autocomplete)
    async def hunter_upgrade(self, ctx: commands.Context, name: str, gear: str, quantity: int = 1):
        embed = discord.Embed(
            title="🔄 **Command Deprecated**",
            description=(
                "**The `sl hunter upgrade` command has been replaced!**\n\n"
                "🆕 **Use `sl upgrade` instead** for a better experience:\n"
                "• Interactive upgrade interface\n"
                "• Better material tracking\n"
                "• Comprehensive cube detection\n\n"
                "**Quick Start**: `sl upgrade` → **👤 Upgrade a Hunter**"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @hunter.command(name="break", help="[DEPRECATED] Use 'sl upgrade' instead.")
    @app_commands.describe(name="The name of the hunter to limit break.")
    @app_commands.autocomplete(name=player_hunter_autocomplete)
    async def hunter_limit_break(self, ctx: commands.Context, *, name: str):
        embed = discord.Embed(
            title="🔄 **Command Deprecated**",
            description=(
                "**The `sl hunter break` command has been replaced!**\n\n"
                "🆕 **Use `sl upgrade` instead** for a better experience:\n"
                "• Interactive limit break interface\n"
                "• Better cube and shard tracking\n"
                "• Comprehensive validation\n\n"
                "**Quick Start**: `sl upgrade` → **👤 Upgrade a Hunter** → Select hunter → **🌟 Limit Break**"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @weapon.command(name="upgrade", help="[DEPRECATED] Use 'sl upgrade' instead.")
    @app_commands.describe(name="The name of the weapon to upgrade.", gear="The gear to use for the upgrade.", quantity="The amount of gear to use.")
    @app_commands.autocomplete(name=player_item_autocomplete)
    async def weapon_upgrade(self, ctx: commands.Context, name: str, gear: str, quantity: int = 1):
        embed = discord.Embed(
            title="🔄 **Command Deprecated**",
            description=(
                "**The `sl weapon upgrade` command has been replaced!**\n\n"
                "🆕 **Use `sl upgrade` instead** for a better experience:\n"
                "• Interactive upgrade interface\n"
                "• Better material tracking\n"
                "• Comprehensive validation\n\n"
                "**Quick Start**: `sl upgrade` → **🗡️ Upgrade a Weapon**"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @weapon.command(name="break", help="[DEPRECATED] Use 'sl upgrade' instead.")
    @app_commands.describe(name="The name of the weapon to limit break.")
    @app_commands.autocomplete(name=player_item_autocomplete)
    async def weapon_limit_break(self, ctx: commands.Context, *, name: str):
        embed = discord.Embed(
            title="🔄 **Command Deprecated**",
            description=(
                "**The `sl weapon break` command has been replaced!**\n\n"
                "🆕 **Use `sl upgrade` instead** for a better experience:\n"
                "• Interactive limit break interface\n"
                "• Better cube and shard tracking\n"
                "• Comprehensive validation\n\n"
                "**Quick Start**: `sl upgrade` → **🗡️ Upgrade a Weapon** → Select weapon → **🌟 Limit Break**"
            ),
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, ephemeral=True)

    # --- SHARED LOGIC FOR UPGRADE/BREAK ---
    async def _handle_upgrade(self, interaction_or_ctx, name: str, gear: str, quantity: int, is_hunter: bool):
        is_interaction = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_interaction else interaction_or_ctx.author
        
        async def respond(embed, ephemeral=False):
            try:
                if is_interaction:
                    # Try followup first, fallback to response if webhook expired
                    try:
                        await interaction_or_ctx.followup.send(embed=embed, ephemeral=ephemeral)
                    except discord.NotFound:
                        # Webhook expired, try to respond directly
                        if not interaction_or_ctx.response.is_done():
                            await interaction_or_ctx.response.send_message(embed=embed, ephemeral=ephemeral)
                        else:
                            # Send to channel as last resort
                            await interaction_or_ctx.channel.send(embed=embed)
                else:
                    await interaction_or_ctx.send(embed=embed, ephemeral=ephemeral)
            except Exception as e:
                logging.error(f"Error in respond function: {e}")
                # Last resort: send to channel
                try:
                    channel = interaction_or_ctx.channel if is_interaction else interaction_or_ctx.channel
                    await channel.send(embed=embed)
                except Exception as e2:
                    logging.error(f"Failed to send message at all: {e2}")

        player = await Player.get(user.id)
        if not player or player.trade:
            await respond(create_embed("Action Blocked", "Cannot perform this action right now.", ERROR_COLOR, user), ephemeral=True)
            return

        entity_data, error_msg = await self._find_owned_entity(player, name, is_hunter)
        if error_msg:
            await respond(create_embed("Error", error_msg, ERROR_COLOR, user), ephemeral=True)
            return

        item, entity_id, entity_info = entity_data['details'], entity_data['id'], entity_data["player_data"]
        entity_type_str = "Hunter" if is_hunter else "Weapon"
        
        level_cap = {0: 10, 1: 20, 2: 40, 3: 60, 4: 80, 5: 100}.get(entity_info.get("tier", 0), 100)
        if entity_info.get("level", 1) >= level_cap:
            await respond(create_embed("Limit Break Required", f"This {entity_type_str.lower()} is at its level cap and needs a Limit-Break.", WARNING_COLOR, user), ephemeral=True)
            return

        gear_name = GEAR_MAP.get(gear.lower())
        if not gear_name:
            await respond(create_embed("Invalid Gear", "Please choose Gear I, II, or III.", ERROR_COLOR, user), ephemeral=True)
            return

        total_xp = XP_PER_GEAR[gear_name] * quantity
        player_gear_attr = GEAR_ATTR_MAP[gear_name]
        if getattr(player, player_gear_attr, 0) < quantity:
            await respond(create_embed("Insufficient Gear", f"You don't have enough {gear_name}.", ERROR_COLOR, user), ephemeral=True)
            return
        
        setattr(player, player_gear_attr, getattr(player, player_gear_attr) - quantity)
        
        if is_hunter: _, xp_added, levels_gained = player.hunter_add_xp(entity_id, total_xp)
        else: _, xp_added, levels_gained = player.weapon_add_xp(entity_id, total_xp)
        await player.save()

        # Track mission progress
        await track_mission_progress(user.id, "upgrade", levels_gained)

        embed = create_embed("Upgrade Successful!", f"**{entity_type_str}:** {item.name}\n**Levels Gained**: +**{levels_gained}**", SUCCESS_COLOR, user)
        embed.set_thumbnail(url=item.image)
        await respond(embed)

    async def _handle_limit_break(self, interaction_or_ctx, name: str, is_hunter: bool):
        is_interaction = isinstance(interaction_or_ctx, discord.Interaction)
        user = interaction_or_ctx.user if is_interaction else interaction_or_ctx.author

        async def respond(embed, ephemeral=False):
            if is_interaction: await interaction_or_ctx.followup.send(embed=embed, ephemeral=ephemeral)
            else: await interaction_or_ctx.send(embed=embed, ephemeral=ephemeral)

        player = await Player.get(user.id)
        if not player or player.trade:
            await respond(create_embed("Action Blocked", "Cannot perform this action right now.", ERROR_COLOR, user), ephemeral=True)
            return

        entity_data, error_msg = await self._find_owned_entity(player, name, is_hunter)
        if error_msg:
            await respond(create_embed("Error", error_msg, ERROR_COLOR, user), ephemeral=True)
            return

        item, entity_id, entity_info = entity_data['details'], entity_data['id'], entity_data["player_data"]
        entity_type_str = "Hunter" if is_hunter else "Weapon"
        
        # Get actual shard count from inventory (stored with 's_' prefix)
        shard_id = f"s_{entity_id}"
        shard_data = player.get_inventory().get(shard_id, 0)
        if isinstance(shard_data, dict):
            shards = shard_data.get('quantity', shard_data.get('level', 0))
        else:
            shards = shard_data if isinstance(shard_data, int) else 0

        level, tier = entity_info.get("level", 1), entity_info.get("tier", 0)

        conditions = {(10, 0): (1, 5), (20, 1): (1, 10), (40, 2): (2, 20), (60, 3): (2, 40), (80, 4): (4, 60)}
        if (level, tier) not in conditions:
            await respond(create_embed("Not Ready", f"This {entity_type_str.lower()} is not at the required level for a limit break.", WARNING_COLOR, user), ephemeral=True)
            return

        shard_req, cube_req = conditions[(level, tier)]
        if shards < shard_req:
            await respond(create_embed("Insufficient Shards", f"You need `x{shard_req}` {getEmoji(entity_id)} shards.", ERROR_COLOR, user), ephemeral=True)
            return

        cube_attr = f"{item.classType.lower()}cube"

        # Use comprehensive cube detection (same as new upgrade system)
        def get_comprehensive_cubes(player, cube_attr, class_type):
            """Get cube count from all possible sources with detailed breakdown"""
            direct_count = getattr(player, cube_attr, 0)
            inventory = player.get_inventory()
            inventory_sources = {}

            # Check inventory for cube items
            cube_item_patterns = [
                f"{class_type.lower()}_cube",
                f"{class_type.lower()}cube",
                f"{class_type}_cube",
                f"{class_type}cube",
                cube_attr
            ]

            for item_id, quantity in inventory.items():
                if any(pattern in item_id.lower() for pattern in cube_item_patterns):
                    inventory_sources[item_id] = quantity

            total_inventory = sum(inventory_sources.values())
            total_cubes = direct_count + total_inventory

            return total_cubes, direct_count, inventory_sources

        current_cubes, direct_cubes, inventory_sources = get_comprehensive_cubes(player, cube_attr, item.classType)

        if current_cubes < cube_req:
            await respond(create_embed("Insufficient Cubes", f"You need `x{cube_req}` {getEmoji(cube_attr)} {item.classType} cubes.\nYou have: `{current_cubes}`", ERROR_COLOR, user), ephemeral=True)
            return

        # Deduct cubes comprehensively (prioritize inventory items first, then direct attributes)
        remaining_to_deduct = cube_req

        # First, deduct from inventory sources
        for item_id, quantity in inventory_sources.items():
            if remaining_to_deduct <= 0:
                break
            deduct_amount = min(quantity, remaining_to_deduct)
            if deduct_amount > 0:
                new_quantity = quantity - deduct_amount
                if new_quantity <= 0:
                    del player.get_inventory()[item_id]
                else:
                    player.get_inventory()[item_id] = new_quantity
                remaining_to_deduct -= deduct_amount

        # Then deduct from direct attributes if needed
        if remaining_to_deduct > 0:
            current_direct = getattr(player, cube_attr, 0)
            setattr(player, cube_attr, current_direct - remaining_to_deduct)
        entity_info["tier"] += 1

        # Deduct shards from inventory (stored with 's_' prefix)
        shard_id = f"s_{entity_id}"
        current_shard_data = player.get_inventory().get(shard_id, 0)
        if isinstance(current_shard_data, dict):
            current_shards = current_shard_data.get('quantity', current_shard_data.get('level', 0))
            current_shard_data['quantity'] = current_shards - shard_req
            if current_shard_data['quantity'] <= 0:
                del player.inventory[shard_id]
        else:
            current_shards = current_shard_data if isinstance(current_shard_data, int) else 0
            new_shard_count = current_shards - shard_req
            if new_shard_count <= 0:
                if shard_id in player.inventory:
                    del player.inventory[shard_id]
            else:
                player.inventory[shard_id] = new_shard_count

        await player.save()

        tier_stars = "★" * entity_info["tier"] + "☆" * (5 - entity_info["tier"])
        embed = create_embed("Limit-Break Successful!", f"**{entity_type_str}:** {item.name}\n**New Tier:** `{tier_stars}`", SUCCESS_COLOR, user)
        embed.set_thumbnail(url=item.image)
        await respond(embed)

async def setup(bot):
    await bot.add_cog(HunterWeaponCog(bot))