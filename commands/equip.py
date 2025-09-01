import discord
from discord.ext import commands
from discord import app_commands, ui
from utilis.utilis import extractId, extractName
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.player import Player
from structure.emoji import getEmoji, getRarityEmoji
from typing import List

# --- Autocomplete Functions ---

async def player_unequippable_item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocompletes with items currently equipped by the player or their hunters."""
    player = await Player.get(interaction.user.id)
    if not player:
        return []

    equipped_item_ids = set()
    # Player's equipped weapons
    if player.equipped.get("Weapon"): equipped_item_ids.add(player.equipped["Weapon"])
    if player.equipped.get("Weapon_2"): equipped_item_ids.add(player.equipped["Weapon_2"])
    
    # Hunters' equipped weapons
    for hunter_data in player.hunters.values():
        if hunter_data.get("weapon"):
            equipped_item_ids.add(hunter_data["weapon"])
            
    choices = []
    for item_id in equipped_item_ids:
        item = await ItemManager.get(item_id)
        if item and current.lower() in item.name.lower():
            choices.append(app_commands.Choice(name=item.name, value=item.name))
            
    return choices[:25]

async def player_equippable_item_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocompletes with WEAPONS from the player's inventory that are NOT currently equipped."""
    player = await Player.get(interaction.user.id)
    if not player:
        return []

    # Get all currently equipped weapon IDs
    equipped_ids = set()
    if player.equipped.get("Weapon"): equipped_ids.add(player.equipped["Weapon"])
    if player.equipped.get("Weapon_2"): equipped_ids.add(player.equipped["Weapon_2"])
    for hunter_data in player.hunters.values():
        if weapon_id := hunter_data.get("weapon"):
            equipped_ids.add(weapon_id)

    choices = []
    inventory = player.get_inventory()
    for item_id, item_data in inventory.items():
        if item_id not in equipped_ids:
            item = await ItemManager.get(item_id)
            # Ensure it's a weapon and matches the current input
            if item and item.type in ["Weapon", "Hero_Weapon"] and current.lower() in item.name.lower():
                choices.append(app_commands.Choice(name=item.name, value=item.name))

    return choices[:25]

async def hunter_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocompletes with 'Player' and the player's owned hunters."""
    player = await Player.get(interaction.user.id)
    if not player:
        return []
    
    hunter_names = ["Player"]
    for hunter_id in player.hunters.keys():
        hunter_info = await HeroManager.get(hunter_id)
        if hunter_info:
            hunter_names.append(hunter_info.name)
            
    filtered_names = [name for name in hunter_names if current.lower() in name.lower()]
    return [app_commands.Choice(name=name, value=name) for name in filtered_names[:25]]

async def slot_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocompletes weapon slots for the Player."""
    slots = ["Slot 1", "Slot 2"]
    filtered_slots = [slot for slot in slots if current.lower() in slot.lower()]
    return [app_commands.Choice(name=slot, value=slot.replace(" ", "_")) for slot in filtered_slots]

# --- Cog ---

class Equip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="equip", help="Equip a weapon to a hunter or your player character.")
    @app_commands.describe(hunter="The character to equip the weapon to.", weapon="The weapon to equip.", slot="The player weapon slot (for Player only).")
    @app_commands.autocomplete(hunter=hunter_autocomplete, weapon=player_equippable_item_autocomplete, slot=slot_autocomplete)
    async def equip(self, ctx: commands.Context, hunter: str, weapon: str, slot: str = "Slot_1"):
        # Remove ephemeral for prefix command support
        if ctx.interaction:
            await ctx.defer(ephemeral=False)
        else:
            await ctx.defer()
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You don't have a character yet. Use `sl start` to create one.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        item_id = extractId(weapon)
        inventory = player.get_inventory()
        if item_id not in inventory:
            embed = discord.Embed(
                title="❌ Item Not Found",
                description="You don't own this item.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        item_data = await ItemManager.get(item_id)
        if not item_data:
            embed = discord.Embed(
                title="❌ Item Data Error",
                description="The selected item could not be found.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
            
        # Unequip the item from wherever it might be currently equipped
        if player.equipped.get("Weapon") == item_id: player.equipped["Weapon"] = None
        if player.equipped.get("Weapon_2") == item_id: player.equipped["Weapon_2"] = None
        for h_id in player.hunters:
            if player.hunters[h_id].get("weapon") == item_id:
                player.hunters[h_id]["weapon"] = None

        # Equip logic
        target_name = "your Player"
        if hunter.lower() == "player":
            if slot == "Slot_1": player.equipped["Weapon"] = item_id
            elif slot == "Slot_2": player.equipped["Weapon_2"] = item_id
            else:
                embed = discord.Embed(
                    title="❌ Invalid Slot",
                    description="Invalid slot for Player. Choose Slot 1 or Slot 2.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=False)
                return
        else:
            hunter_id = extractId(hunter)
            if hunter_id in player.hunters:
                player.hunters[hunter_id]['weapon'] = item_id
                target_name = f"your hunter **{hunter}**"
            else:
                embed = discord.Embed(
                    title="❌ Hunter Not Found",
                    description=f"Hunter `{hunter}` not found in your collection.",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

        player.inventory[item_id]["equipped"] = True
        await player.save()

        embed = discord.Embed(
            title="⚔️ Weapon Equipped!",
            description=f"✅ Successfully equipped **{weapon}** to {target_name}.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=item_data.image)
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.hybrid_command(name="unequip", help="Unequip a weapon from a hunter or your player character.")
    @app_commands.describe(weapon="The weapon you want to unequip.")
    @app_commands.autocomplete(weapon=player_unequippable_item_autocomplete)
    async def unequip(self, ctx: commands.Context, weapon: str):
        # Remove ephemeral for prefix command support
        if ctx.interaction:
            await ctx.defer(ephemeral=False)
        else:
            await ctx.defer()
        weapon_id = extractId(weapon)
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You don't have a character yet. Use `sl start` to create one.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        item = player.inventory.get(weapon_id)
        if not item:
            embed = discord.Embed(
                title="❌ Weapon Not Found",
                description=f"You do not own the weapon `{weapon}`.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        item_data = await ItemManager.get(weapon_id)
        if not item_data:
            embed = discord.Embed(
                title="❌ Item Data Error",
                description="The selected item's data could not be found.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        unequipped_from = None
        # Unequip from player slots
        if player.equipped.get("Weapon") == weapon_id:
            player.equipped["Weapon"] = None
            unequipped_from = "your Player"
        elif player.equipped.get("Weapon_2") == weapon_id:
            player.equipped["Weapon_2"] = None
            unequipped_from = "your Player"
            
        # Unequip from hunters
        for hunter_id, hunter_data in player.hunters.items():
            if hunter_data.get('weapon') == weapon_id:
                hunter_data['weapon'] = None
                hunter_info = await HeroManager.get(hunter_id)
                unequipped_from = f"your hunter **{hunter_info.name}**"
                break
        
        if not unequipped_from:
            embed = discord.Embed(
                title="❌ Not Equipped",
                description=f"The weapon `{weapon}` is not currently equipped.",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        item["equipped"] = False
        await player.save()

        embed = discord.Embed(
            title="🔓 Weapon Unequipped!",
            description=f"✅ Successfully unequipped **{weapon}** from {unequipped_from}.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=item_data.image)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="equipment", aliases=['eq'], help="Interactive equipment management interface.")
    async def equipment(self, ctx: commands.Context):
        """Show interactive equipment management interface."""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You don't have a character yet. Use `sl start` to create one.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        view = EquipmentView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)


class EquipmentView(ui.View):
    """Interactive view for equipment management."""

    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.current_mode = "overview"  # overview, equip, unequip
        self.selected_target = None  # player or hunter_id
        self.selected_slot = None  # Weapon, Weapon_2, or weapon (for hunters)

    async def create_embed(self):
        """Create the main equipment embed."""
        if self.current_mode == "overview":
            return await self.create_overview_embed()
        elif self.current_mode == "equip":
            return await self.create_equip_embed()
        elif self.current_mode == "unequip":
            return await self.create_unequip_embed()

    async def create_overview_embed(self):
        """Create overview of current equipment."""
        embed = discord.Embed(
            title="⚔️ **EQUIPMENT MANAGEMENT** ⚔️",
            description="Manage your weapons and equipment",
            color=discord.Color.blue()
        )

        # Player equipment
        player_weapons = []
        weapon1 = self.player.equipped.get("Weapon")
        weapon2 = self.player.equipped.get("Weapon_2")

        if weapon1:
            item = await ItemManager.get(weapon1)
            if item:
                player_weapons.append(f"**Slot 1**: {getRarityEmoji(item.rarity)} {item.name}")
        else:
            player_weapons.append("**Slot 1**: *Empty*")

        if weapon2:
            item = await ItemManager.get(weapon2)
            if item:
                player_weapons.append(f"**Slot 2**: {getRarityEmoji(item.rarity)} {item.name}")
        else:
            player_weapons.append("**Slot 2**: *Empty*")

        embed.add_field(
            name=f"{getEmoji('player')} Your Equipment",
            value="\n".join(player_weapons),
            inline=False
        )

        # Hunter equipment
        hunter_equipment = []
        for hunter_id, hunter_data in self.player.hunters.items():
            hunter_info = await HeroManager.get(hunter_id)
            if hunter_info:
                weapon_id = hunter_data.get('weapon')
                if weapon_id:
                    weapon = await ItemManager.get(weapon_id)
                    if weapon:
                        hunter_equipment.append(f"**{hunter_info.name}**: {getRarityEmoji(weapon.rarity)} {weapon.name}")
                else:
                    hunter_equipment.append(f"**{hunter_info.name}**: *No weapon*")

        if hunter_equipment:
            embed.add_field(
                name=f"{getEmoji('hunter')} Hunter Equipment",
                value="\n".join(hunter_equipment[:10]),  # Limit to 10
                inline=False
            )
        else:
            embed.add_field(
                name=f"{getEmoji('hunter')} Hunter Equipment",
                value="*No hunters recruited*",
                inline=False
            )

        embed.set_footer(text="Use the buttons below to equip or unequip items")
        return embed

    async def create_equip_embed(self):
        """Create equip interface embed."""
        embed = discord.Embed(
            title="⚔️ **EQUIP WEAPON** ⚔️",
            description="Select a weapon to equip",
            color=discord.Color.green()
        )

        # Show available weapons
        inventory = self.player.get_inventory()
        equipped_ids = self.get_equipped_weapon_ids()

        available_weapons = []
        for item_id, item_data in inventory.items():
            if item_id not in equipped_ids:
                item = await ItemManager.get(item_id)
                if item and item.type in ["Weapon", "Hero_Weapon"]:
                    level = item_data.get('level', 1)
                    tier = item_data.get('tier', 0)
                    tier_text = f" T{tier}" if tier > 0 else ""
                    available_weapons.append(f"{getRarityEmoji(item.rarity)} **{item.name}** (Lv.{level}{tier_text})")

        if available_weapons:
            embed.add_field(
                name="📦 Available Weapons",
                value="\n".join(available_weapons[:15]),  # Show first 15
                inline=False
            )
        else:
            embed.add_field(
                name="📦 Available Weapons",
                value="*No unequipped weapons available*",
                inline=False
            )

        if self.selected_target:
            if self.selected_target == "player":
                embed.add_field(
                    name="🎯 Target",
                    value="**Your Player Character**",
                    inline=True
                )
            else:
                hunter = await HeroManager.get(self.selected_target)
                if hunter:
                    embed.add_field(
                        name="🎯 Target",
                        value=f"**{hunter.name}**",
                        inline=True
                    )

        embed.set_footer(text="Select a target and weapon to equip")
        return embed

    async def create_unequip_embed(self):
        """Create unequip interface embed."""
        embed = discord.Embed(
            title="🔓 **UNEQUIP WEAPON** 🔓",
            description="Select a weapon to unequip",
            color=discord.Color.orange()
        )

        equipped_weapons = []

        # Player weapons
        weapon1 = self.player.equipped.get("Weapon")
        weapon2 = self.player.equipped.get("Weapon_2")

        if weapon1:
            item = await ItemManager.get(weapon1)
            if item:
                equipped_weapons.append(f"**Your Player (Slot 1)**: {getRarityEmoji(item.rarity)} {item.name}")

        if weapon2:
            item = await ItemManager.get(weapon2)
            if item:
                equipped_weapons.append(f"**Your Player (Slot 2)**: {getRarityEmoji(item.rarity)} {item.name}")

        # Hunter weapons
        for hunter_id, hunter_data in self.player.hunters.items():
            weapon_id = hunter_data.get('weapon')
            if weapon_id:
                hunter_info = await HeroManager.get(hunter_id)
                weapon = await ItemManager.get(weapon_id)
                if hunter_info and weapon:
                    equipped_weapons.append(f"**{hunter_info.name}**: {getRarityEmoji(weapon.rarity)} {weapon.name}")

        if equipped_weapons:
            embed.add_field(
                name="⚔️ Equipped Weapons",
                value="\n".join(equipped_weapons),
                inline=False
            )
        else:
            embed.add_field(
                name="⚔️ Equipped Weapons",
                value="*No weapons currently equipped*",
                inline=False
            )

        embed.set_footer(text="Select a weapon to unequip")
        return embed

    def get_equipped_weapon_ids(self):
        """Get all currently equipped weapon IDs."""
        equipped_ids = set()
        if self.player.equipped.get("Weapon"):
            equipped_ids.add(self.player.equipped["Weapon"])
        if self.player.equipped.get("Weapon_2"):
            equipped_ids.add(self.player.equipped["Weapon_2"])

        for hunter_data in self.player.hunters.values():
            if weapon_id := hunter_data.get("weapon"):
                equipped_ids.add(weapon_id)

        return equipped_ids

    def update_buttons(self):
        """Update button states based on current mode."""
        self.clear_items()

        if self.current_mode == "overview":
            self.add_item(EquipButton())
            self.add_item(UnequipButton())
        elif self.current_mode == "equip":
            self.add_item(WeaponEquipSelect(self))
            self.add_item(TargetEquipSelect(self))
            self.add_item(BackButton())
        elif self.current_mode == "unequip":
            self.add_item(WeaponUnequipSelect(self))
            self.add_item(BackButton())

    async def update_view(self, interaction):
        """Update the view and embed."""
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class EquipButton(ui.Button):
    """Button to switch to equip mode."""

    def __init__(self):
        super().__init__(label="⚔️ Equip Weapon", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        self.view.current_mode = "equip"
        await self.view.update_view(interaction)


class UnequipButton(ui.Button):
    """Button to switch to unequip mode."""

    def __init__(self):
        super().__init__(label="🔓 Unequip Weapon", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        self.view.current_mode = "unequip"
        await self.view.update_view(interaction)


class BackButton(ui.Button):
    """Button to go back to overview."""

    def __init__(self):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        self.view.current_mode = "overview"
        await self.view.update_view(interaction)


class WeaponEquipSelect(ui.Select):
    """Select dropdown for choosing weapon to equip."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(placeholder="Select a weapon to equip...", min_values=1, max_values=1)
        self.populate_options()

    async def populate_options(self):
        """Populate weapon options."""
        inventory = self.parent_view.player.get_inventory()
        equipped_ids = self.parent_view.get_equipped_weapon_ids()

        options = []
        for item_id, item_data in inventory.items():
            if item_id not in equipped_ids and len(options) < 25:
                item = await ItemManager.get(item_id)
                if item and item.type in ["Weapon", "Hero_Weapon"]:
                    level = item_data.get('level', 1)
                    tier = item_data.get('tier', 0)
                    tier_text = f" T{tier}" if tier > 0 else ""

                    options.append(discord.SelectOption(
                        label=f"{item.name} (Lv.{level}{tier_text})",
                        value=item_id,
                        description=f"{item.rarity} {item.type}",
                        emoji=getRarityEmoji(item.rarity)
                    ))

        if not options:
            options.append(discord.SelectOption(
                label="No weapons available",
                value="none",
                description="All weapons are equipped"
            ))

        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        if self.values[0] == "none":
            await interaction.response.send_message("❌ No weapons available to equip!", ephemeral=True)
            return

        self.parent_view.selected_weapon = self.values[0]
        await interaction.response.send_message(f"✅ Selected weapon! Now choose a target.", ephemeral=True)


class TargetEquipSelect(ui.Select):
    """Select dropdown for choosing equip target."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(placeholder="Select target to equip to...", min_values=1, max_values=1)
        self.populate_options()

    async def populate_options(self):
        """Populate target options."""
        options = [
            discord.SelectOption(
                label="Your Player (Slot 1)",
                value="player_slot1",
                description="Equip to your main weapon slot",
                emoji="👤"
            ),
            discord.SelectOption(
                label="Your Player (Slot 2)",
                value="player_slot2",
                description="Equip to your secondary weapon slot",
                emoji="👤"
            )
        ]

        # Add hunters
        for hunter_id, hunter_data in self.parent_view.player.hunters.items():
            hunter_info = await HeroManager.get(hunter_id)
            if hunter_info and len(options) < 25:
                options.append(discord.SelectOption(
                    label=hunter_info.name,
                    value=f"hunter_{hunter_id}",
                    description="Equip to this hunter",
                    emoji="⚔️"
                ))

        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        if not hasattr(self.parent_view, 'selected_weapon'):
            await interaction.response.send_message("❌ Please select a weapon first!", ephemeral=True)
            return

        weapon_id = self.parent_view.selected_weapon
        target = self.values[0]

        # Perform the equip action
        weapon = await ItemManager.get(weapon_id)
        if not weapon:
            await interaction.response.send_message("❌ Weapon not found!", ephemeral=True)
            return

        # Unequip from current location first
        player = self.parent_view.player
        if player.equipped.get("Weapon") == weapon_id:
            player.equipped["Weapon"] = None
        if player.equipped.get("Weapon_2") == weapon_id:
            player.equipped["Weapon_2"] = None
        for h_id in player.hunters:
            if player.hunters[h_id].get("weapon") == weapon_id:
                player.hunters[h_id]["weapon"] = None

        # Equip to new location
        if target == "player_slot1":
            player.equipped["Weapon"] = weapon_id
            target_name = "Your Player (Slot 1)"
        elif target == "player_slot2":
            player.equipped["Weapon_2"] = weapon_id
            target_name = "Your Player (Slot 2)"
        elif target.startswith("hunter_"):
            hunter_id = target.replace("hunter_", "")
            if hunter_id in player.hunters:
                player.hunters[hunter_id]['weapon'] = weapon_id
                hunter_info = await HeroManager.get(hunter_id)
                target_name = hunter_info.name if hunter_info else "Hunter"
            else:
                await interaction.response.send_message("❌ Hunter not found!", ephemeral=True)
                return

        await player.save()

        embed = discord.Embed(
            title="✅ **WEAPON EQUIPPED** ✅",
            description=f"**{weapon.name}** has been equipped to **{target_name}**!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Update the main view
        self.parent_view.current_mode = "overview"
        await self.parent_view.update_view(interaction)


class WeaponUnequipSelect(ui.Select):
    """Select dropdown for choosing weapon to unequip."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(placeholder="Select a weapon to unequip...", min_values=1, max_values=1)
        self.populate_options()

    async def populate_options(self):
        """Populate unequip options."""
        options = []
        player = self.parent_view.player

        # Player weapons
        weapon1 = player.equipped.get("Weapon")
        weapon2 = player.equipped.get("Weapon_2")

        if weapon1:
            item = await ItemManager.get(weapon1)
            if item:
                options.append(discord.SelectOption(
                    label=f"Your Player (Slot 1): {item.name}",
                    value=f"player_slot1_{weapon1}",
                    description=f"{item.rarity} {item.type}",
                    emoji="👤"
                ))

        if weapon2:
            item = await ItemManager.get(weapon2)
            if item:
                options.append(discord.SelectOption(
                    label=f"Your Player (Slot 2): {item.name}",
                    value=f"player_slot2_{weapon2}",
                    description=f"{item.rarity} {item.type}",
                    emoji="👤"
                ))

        # Hunter weapons
        for hunter_id, hunter_data in player.hunters.items():
            weapon_id = hunter_data.get('weapon')
            if weapon_id and len(options) < 25:
                hunter_info = await HeroManager.get(hunter_id)
                weapon = await ItemManager.get(weapon_id)
                if hunter_info and weapon:
                    options.append(discord.SelectOption(
                        label=f"{hunter_info.name}: {weapon.name}",
                        value=f"hunter_{hunter_id}_{weapon_id}",
                        description=f"{weapon.rarity} {weapon.type}",
                        emoji="⚔️"
                    ))

        if not options:
            options.append(discord.SelectOption(
                label="No weapons equipped",
                value="none",
                description="Nothing to unequip"
            ))

        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        if self.values[0] == "none":
            await interaction.response.send_message("❌ No weapons to unequip!", ephemeral=True)
            return

        value_parts = self.values[0].split("_")
        player = self.parent_view.player

        if value_parts[0] == "player":
            slot = value_parts[1]
            weapon_id = value_parts[2]

            if slot == "slot1":
                player.equipped["Weapon"] = None
                target_name = "Your Player (Slot 1)"
            elif slot == "slot2":
                player.equipped["Weapon_2"] = None
                target_name = "Your Player (Slot 2)"

        elif value_parts[0] == "hunter":
            hunter_id = value_parts[1]
            weapon_id = value_parts[2]

            if hunter_id in player.hunters:
                player.hunters[hunter_id]['weapon'] = None
                hunter_info = await HeroManager.get(hunter_id)
                target_name = hunter_info.name if hunter_info else "Hunter"
            else:
                await interaction.response.send_message("❌ Hunter not found!", ephemeral=True)
                return

        weapon = await ItemManager.get(weapon_id)
        weapon_name = weapon.name if weapon else "Unknown Weapon"

        await player.save()

        embed = discord.Embed(
            title="✅ **WEAPON UNEQUIPPED** ✅",
            description=f"**{weapon_name}** has been unequipped from **{target_name}**!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Update the main view
        self.parent_view.current_mode = "overview"
        await self.parent_view.update_view(interaction)


async def setup(bot):
    await bot.add_cog(Equip(bot))