import discord
import math
from discord.ext import commands
from discord import app_commands, ui
from structure.player import Player
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.shadow import Shadow
from structure.emoji import getEmoji
from utilis.utilis import create_embed, INFO_COLOR, ERROR_COLOR, SUCCESS_COLOR, WARNING_COLOR, create_progress_bar
from commands.missions import track_mission_progress
import math

def get_comprehensive_cube_count(player, cube_attr, class_type):
    """Get cube count from multiple possible sources"""
    print(f"    DEBUG - get_comprehensive_cube_count called:")
    print(f"      cube_attr: {cube_attr}")
    print(f"      class_type: {class_type}")

    # Primary source: direct attribute
    direct_count = getattr(player, cube_attr, 0)
    print(f"      direct_count: {direct_count}")

    # Secondary source: check inventory for cube items
    inventory = player.get_inventory()
    inventory_count = 0

    # Comprehensive list of possible cube storage keys
    possible_cube_keys = [
        # Standard naming
        f"{class_type.lower()}_cube",
        f"{cube_attr}",
        f"cube_{class_type.lower()}",
        # Alternative naming patterns
        f"{class_type}Cube",
        f"{class_type}_Cube",
        f"{class_type.upper()}_CUBE",
        f"{class_type.lower()}cube",
        # Specific cube type names
        f"{class_type.lower()}_melding_cube",
        f"{class_type}_melding_cube",
        # Item ID patterns (some cubes might be stored as items)
        f"cube_{cube_attr}",
        f"item_{cube_attr}",
        # Legacy naming
        f"old_{cube_attr}",
        f"legacy_{cube_attr}"
    ]

    # Check all possible keys
    for key in possible_cube_keys:
        if key in inventory:
            item_data = inventory[key]
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', item_data.get('level', item_data.get('amount', 0)))
            elif isinstance(item_data, int):
                quantity = item_data
            else:
                quantity = 0
            inventory_count += quantity

    # Also check for cube items by searching all inventory keys
    for key, item_data in inventory.items():
        # Look for cube-related items that might contain the element type
        key_lower = key.lower()
        class_lower = class_type.lower()

        # Standard element matching
        if 'cube' in key_lower and class_lower in key_lower:
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', item_data.get('level', item_data.get('amount', 0)))
            elif isinstance(item_data, int):
                quantity = item_data
            else:
                quantity = 0
            inventory_count += quantity

        # Special case for Earth cubes - they might be stored as "sandstorm_cube"
        elif class_type == "Earth" and 'cube' in key_lower and ('sandstorm' in key_lower or 'earth' in key_lower or 'ground' in key_lower):
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', item_data.get('level', item_data.get('amount', 0)))
            elif isinstance(item_data, int):
                quantity = item_data
            else:
                quantity = 0
            inventory_count += quantity

        # Special case for other elements that might have alternative names
        elif 'cube' in key_lower:
            # Check for alternative element names
            element_aliases = {
                'Fire': ['flame', 'burn', 'heat', 'inferno'],
                'Water': ['ice', 'frost', 'aqua', 'hydro', 'ocean'],
                'Wind': ['air', 'storm', 'gale', 'breeze', 'tornado'],
                'Earth': ['stone', 'rock', 'ground', 'sand', 'sandstorm', 'terra'],
                'Light': ['holy', 'divine', 'radiant', 'bright', 'solar'],
                'Dark': ['shadow', 'void', 'night', 'evil', 'lunar']
            }

            if class_type in element_aliases:
                for alias in element_aliases[class_type]:
                    if alias in key_lower:
                        if isinstance(item_data, dict):
                            quantity = item_data.get('quantity', item_data.get('level', item_data.get('amount', 0)))
                        elif isinstance(item_data, int):
                            quantity = item_data
                        else:
                            quantity = 0
                        inventory_count += quantity
                        break  # Only count once per item

    total_count = max(direct_count, inventory_count)  # Use the higher count
    print(f"      inventory_count: {inventory_count}")
    print(f"      total_count (max): {total_count}")
    return total_count

class UpgradeItemSelect(ui.Select):
    def __init__(self, author: discord.User, item_type: str, upgrade_cog):
        self.author = author
        self.item_type = item_type
        self.upgrade_cog = upgrade_cog
        super().__init__(placeholder=f'Select a {item_type} to upgrade...', min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        item_id = self.values[0]
        await self.upgrade_cog.show_upgrade_details(interaction, self.item_type, item_id)

class UpgradeItemSelectView(ui.View):
    def __init__(self, author: discord.User, item_type: str, upgrade_cog):
        super().__init__(timeout=180)
        self.author = author
        self.item_type = item_type
        self.upgrade_cog = upgrade_cog
        self.current_page = 0
        self.items_per_page = 25  # Discord limit
        self.all_options = []
        self.select_menu = UpgradeItemSelect(author, item_type, upgrade_cog)
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False
        return True

    async def populate_items(self):
        player = await Player.get(self.author.id)
        if not player:
            return

        options = []

        if self.item_type == 'shadow':
            # Handle shadows - check if player actually has arisen shadows
            from structure.shadow import Shadow
            shadows = player.get_shadows()

            if not shadows:
                options.append(discord.SelectOption(
                    label="No Shadows Found",
                    value="no_shadows",
                    description="You must arise shadows before upgrading them. Use 'sl arise' command.",
                    emoji="❌"
                ))
            else:
                upgradeable_shadows = []
                for shadow_id, shadow_data in shadows.items():
                    shadow_obj = await Shadow.get(shadow_id)
                    if shadow_obj:
                        level = shadow_data.get('level', 1)
                        xp = shadow_data.get('xp', 0)
                        required_xp = level * 1000

                        # Check if player has materials to upgrade
                        tos_cost = level * 100
                        can_upgrade = player.tos >= tos_cost
                        status_emoji = "✅" if can_upgrade else "❌"

                        upgradeable_shadows.append(discord.SelectOption(
                            label=f"{shadow_obj.name} (Lv. {level})",
                            value=shadow_obj.id,
                            description=f"Level {level} • {xp}/{required_xp} XP • {status_emoji} TOS: {tos_cost}",
                            emoji="👻"
                        ))

                if upgradeable_shadows:
                    options.extend(upgradeable_shadows)
                else:
                    options.append(discord.SelectOption(
                        label="No Arisen Shadows",
                        value="no_arisen_shadows",
                        description="You must arise shadows before upgrading them. Use 'sl arise' command.",
                        emoji="❌"
                    ))
        else:
            # Handle hunters and weapons with comprehensive filtering and material checking
            is_hunter = self.item_type == 'hunter'
            inventory = player.get_hunters() if is_hunter else player.get_inventory()

            if not inventory:
                item_type_name = "Hunters" if is_hunter else "Weapons"
                options.append(discord.SelectOption(
                    label=f"No {item_type_name} Found",
                    value=f"no_{self.item_type}s",
                    description=f"You don't have any {item_type_name.lower()} to upgrade",
                    emoji="❌"
                ))
            else:
                upgradeable_items = []

                for item_id, data in inventory.items():
                    # Skip shard items (they start with 's_')
                    if item_id.startswith('s_'):
                        continue

                    # Only include items that have level data (upgradeable items)
                    if not isinstance(data, dict) or 'level' not in data:
                        continue

                    # Get item object
                    item_obj = await (HeroManager.get(item_id) if is_hunter else ItemManager.get(item_id))
                    if item_obj:
                        level = data.get('level', 1)
                        tier = data.get('tier', 1)

                        # Check if player has materials to upgrade with tier-based requirements
                        if is_hunter:
                            gold_cost = (150 * level) + ((level // 10) * 500)
                            # Hunters use different gear based on tier (higher tier = more expensive)
                            if tier >= 3:  # High tier hunters need more gear
                                gear_cost = (8 * level) + ((level // 10) * 25)
                                gear_type = "gear3"
                                gear_name = "Enhancement Gear III"
                                can_upgrade = player.gold >= gold_cost and player.gear3 >= gear_cost
                            elif tier >= 2:  # Mid tier hunters
                                gear_cost = (5 * level) + ((level // 10) * 15)
                                gear_type = "gear2"
                                gear_name = "Enhancement Gear II"
                                can_upgrade = player.gold >= gold_cost and player.gear2 >= gear_cost
                            else:  # Low tier hunters (cheapest)
                                gear_cost = (3 * level) + ((level // 10) * 10)
                                gear_type = "gear1"
                                gear_name = "Enhancement Gear I"
                                can_upgrade = player.gold >= gold_cost and player.gear1 >= gear_cost
                        else:  # weapon
                            gold_cost = 1000 + (level * 300) + ((level // 10) * 1000)
                            # Weapons use different gear based on tier and level (higher tier = more expensive)
                            if tier >= 3 or level >= 40:  # High tier/level weapons (most expensive)
                                gear_cost = (12 * level) + ((level // 15) * 35)
                                gear_type = "gear3"
                                gear_name = "Enhancement Gear III"
                                can_upgrade = player.gold >= gold_cost and player.gear3 >= gear_cost
                            elif tier >= 2 or level >= 20:  # Mid tier/level weapons
                                gear_cost = (8 * level) + ((level // 15) * 20)
                                gear_type = "gear2"
                                gear_name = "Enhancement Gear II"
                                can_upgrade = player.gold >= gold_cost and player.gear2 >= gear_cost
                            else:  # Low tier/level weapons (cheapest)
                                gear_cost = (5 * level) + ((level // 15) * 10)
                                gear_type = "gear1"
                                gear_name = "Enhancement Gear I"
                                can_upgrade = player.gold >= gold_cost and player.gear1 >= gear_cost
                        status_emoji = "✅" if can_upgrade else "❌"

                        # Create detailed description with material status
                        description = f"Level {level}"
                        if tier > 1:
                            description += f" • Tier {tier}"
                        description += f" • {status_emoji} Gold: {gold_cost:,}, {gear_name}: {gear_cost}"

                        upgradeable_items.append({
                            'option': discord.SelectOption(
                                label=f"{item_obj.name} (Lv. {level})",
                                value=item_obj.id,
                                description=description[:100],  # Discord limit
                                emoji=getEmoji(item_obj.id)
                            ),
                            'level': level,
                            'can_upgrade': can_upgrade
                        })
                    else:
                        # If item not found in database, still show it for debugging
                        upgradeable_items.append({
                            'option': discord.SelectOption(
                                label=f"Unknown Item: {item_id} (Lv. {data.get('level', 1)})",
                                value=item_id,
                                description=f"Level {data.get('level', 1)} • Database entry missing",
                                emoji="❓"
                            ),
                            'level': data.get('level', 1),
                            'can_upgrade': False
                        })

                if not upgradeable_items:
                    item_type_name = "Hunters" if is_hunter else "Weapons"
                    options.append(discord.SelectOption(
                        label=f"No Upgradeable {item_type_name}",
                        value=f"no_upgradeable_{self.item_type}s",
                        description=f"No {item_type_name.lower()} with upgrade data found",
                        emoji="❌"
                    ))
                else:
                    # Sort by level (highest first), then by upgrade availability
                    upgradeable_items.sort(key=lambda x: (x['can_upgrade'], x['level']), reverse=True)
                    options = [item['option'] for item in upgradeable_items]

        # Sort options by upgrade availability first, then by level (highest first)
        def sort_key(option):
            # Extract level from label
            try:
                level = int(option.label.split('Lv. ')[1].split(')')[0])
            except:
                level = 0

            # Prioritize upgradeable items (✅ in description)
            can_upgrade = "✅" in option.description
            return (can_upgrade, level)

        options.sort(key=sort_key, reverse=True)

        # Store all options for pagination
        self.all_options = options

        # Update the select menu with current page
        await self.update_page_display()

    async def update_page_display(self):
        """Update the select menu to show current page of items"""
        if not self.all_options:
            return

        # Calculate pagination
        total_items = len(self.all_options)
        total_pages = max(1, math.ceil(total_items / self.items_per_page))
        self.current_page = min(self.current_page, total_pages - 1)

        # Get items for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_options = self.all_options[start_idx:end_idx]

        # Update select menu options
        self.select_menu.options = page_options

        # Update placeholder with pagination info
        upgradeable_count = len([opt for opt in self.all_options if "✅" in opt.description])
        if total_pages > 1:
            self.select_menu.placeholder = f'Select a {self.item_type} to upgrade... ({upgradeable_count} ready, {total_items} total) - Page {self.current_page + 1}/{total_pages}'
        else:
            self.select_menu.placeholder = f'Select a {self.item_type} to upgrade... ({upgradeable_count} ready, {total_items} total)'

        # Update navigation buttons visibility
        await self.update_navigation_buttons(total_pages)

    async def update_navigation_buttons(self, total_pages):
        """Add or remove navigation buttons based on pagination needs"""
        # Remove existing navigation buttons
        self.clear_items()
        self.add_item(self.select_menu)

        # Add navigation buttons if needed
        if total_pages > 1:
            # Previous page button
            prev_button = ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page == 0),
                row=1
            )
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

            # Page info button (disabled, just for display)
            page_info_button = ui.Button(
                label=f"Page {self.current_page + 1}/{total_pages}",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=1
            )
            self.add_item(page_info_button)

            # Next page button
            next_button = ui.Button(
                label="Next ▶️",
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page >= total_pages - 1),
                row=1
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            await self.update_page_display()

            # Update the message
            embed = create_embed(f"Upgrade {self.item_type.capitalize()}", f"Select the {self.item_type} you wish to upgrade from the list below.", INFO_COLOR, self.author)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on the first page.", ephemeral=True)

    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return

        total_pages = max(1, math.ceil(len(self.all_options) / self.items_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            await self.update_page_display()

            # Update the message
            embed = create_embed(f"Upgrade {self.item_type.capitalize()}", f"Select the {self.item_type} you wish to upgrade from the list below.", INFO_COLOR, self.author)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on the last page.", ephemeral=True)

class UpgradeTypeSelectView(ui.View):
    def __init__(self, author: discord.User, upgrade_cog):
        super().__init__(timeout=180)
        self.author = author
        self.upgrade_cog = upgrade_cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False
        return True

    async def show_item_select(self, interaction: discord.Interaction, item_type: str):
        view = UpgradeItemSelectView(self.author, item_type, self.upgrade_cog)
        await view.populate_items()

        if not view.select_menu.options:
            embed = create_embed(f"No {item_type.capitalize()}s Found", f"You don't have any {item_type}s in your inventory.", ERROR_COLOR, self.author)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        embed = create_embed(f"Upgrade {item_type.capitalize()}", f"Select the {item_type} you wish to upgrade from the list below.", INFO_COLOR, self.author)
        await interaction.response.edit_message(embed=embed, view=view)

    @ui.button(label="Upgrade a Hunter", style=discord.ButtonStyle.primary, emoji="👤")
    async def hunter_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_item_select(interaction, 'hunter')

    @ui.button(label="Upgrade a Weapon", style=discord.ButtonStyle.secondary, emoji="🗡️")
    async def weapon_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_item_select(interaction, 'weapon')

    @ui.button(label="Upgrade a Shadow", style=discord.ButtonStyle.success, emoji="👻")
    async def shadow_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_item_select(interaction, 'shadow')

    @ui.button(label="🔧 Enhanced View", style=discord.ButtonStyle.primary, emoji="🔍", row=1)
    async def enhanced_view_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show all upgradeable items with advanced filtering like codex"""
        await interaction.response.defer()

        player = await Player.get(self.author.id)
        if not player:
            embed = create_embed("❌ Error", "Player not found.", ERROR_COLOR, interaction.user)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Create enhanced filtered view
        view = UpgradeFilterView(self.author, player, self.upgrade_cog)
        embed = await view.create_main_embed()
        await interaction.edit_original_response(embed=embed, view=view)

    @ui.button(label="📋 Simple View", style=discord.ButtonStyle.secondary, emoji="📄", row=1)
    async def simple_view_button(self, interaction: discord.Interaction, button: ui.Button):
        """Show all upgradeable items in simple paginated view"""
        await interaction.response.defer()

        player = await Player.get(self.author.id)
        if not player:
            embed = create_embed("❌ Error", "Player not found.", ERROR_COLOR, interaction.user)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Create simple paginated view
        view = UpgradeAllItemsView(self.author, player, self.upgrade_cog)
        embed = await view.create_main_embed()
        await interaction.edit_original_response(embed=embed, view=view)


class UpgradeFilterView(ui.View):
    """Enhanced upgrade view with filtering like codex"""

    def __init__(self, author, player, upgrade_cog=None):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.upgrade_cog = upgrade_cog
        self.current_page = 0
        self.items_per_page = 10
        self.current_filter = "all"  # all, hunters, weapons, shadows
        self.current_rarity = "all"  # all, common, rare, epic, legendary
        self.current_status = "all"  # all, upgradeable, not_upgradeable
        self.search_query = ""
        self.all_items = []

    async def create_main_embed(self):
        """Create the main upgrade embed with filtering"""
        await self.collect_all_items()

        # Apply filters
        filtered_items = self.apply_filters()

        # Calculate pagination
        total_items = len(filtered_items)
        total_pages = max(1, math.ceil(total_items / self.items_per_page))
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered_items[start_idx:end_idx]

        # Create embed
        embed = discord.Embed(
            title="🔧 **UPGRADE SYSTEM**",
            description=f"Filter and upgrade your hunters, weapons, and shadows\n"
                       f"**Page {self.current_page + 1}/{total_pages}** • **{total_items} items** • **{len([i for i in filtered_items if i['can_upgrade']])} upgradeable**",
            color=INFO_COLOR
        )

        # Add filter status
        filter_status = []
        if self.current_filter != "all":
            filter_status.append(f"Type: {self.current_filter.title()}")
        if self.current_rarity != "all":
            filter_status.append(f"Rarity: {self.current_rarity.title()}")
        if self.current_status != "all":
            filter_status.append(f"Status: {self.current_status.replace('_', ' ').title()}")
        if self.search_query:
            filter_status.append(f"Search: '{self.search_query}'")

        if filter_status:
            embed.add_field(
                name="🔍 **Active Filters**",
                value=" • ".join(filter_status),
                inline=False
            )

        # Add items to embed
        if page_items:
            for item in page_items:
                status_emoji = "✅" if item['can_upgrade'] else "❌"
                upgrade_info = item['upgrade_info'] if item['can_upgrade'] else "Missing materials"

                embed.add_field(
                    name=f"{status_emoji} **{item['name']}** (Level {item['level']})",
                    value=f"**Type:** {item['type'].title()}\n"
                          f"**Rarity:** {item['rarity'].title()}\n"
                          f"**Status:** {upgrade_info}",
                    inline=True
                )
        else:
            embed.add_field(
                name="❌ **No Items Found**",
                value="No items match your current filters.\nTry adjusting your filters or search query.",
                inline=False
            )

        # Update select menu options
        await self.update_select_options(page_items)

        embed.set_footer(text="Use the buttons and dropdowns to filter and navigate • Select an item to upgrade")
        return embed

    async def collect_all_items(self):
        """Collect all upgradeable items from player inventory"""
        self.all_items = []

        # Collect hunters
        hunters = self.player.get_hunters()
        for hunter_id, data in hunters.items():
            if not isinstance(data, dict) or 'level' not in data:
                continue

            hunter_obj = await HeroManager.get(hunter_id)
            if hunter_obj:
                level = data.get('level', 1)
                tier = data.get('tier', 1)

                # Calculate upgrade requirements
                gold_cost = (150 * level) + ((level // 10) * 500)
                if tier >= 3:
                    gear_cost = (8 * level) + ((level // 10) * 25)
                    gear_type = "gear3"
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear3 >= gear_cost
                elif tier >= 2:
                    gear_cost = (5 * level) + ((level // 10) * 15)
                    gear_type = "gear2"
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear2 >= gear_cost
                else:
                    gear_cost = (3 * level) + ((level // 10) * 10)
                    gear_type = "gear1"
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear1 >= gear_cost

                upgrade_info = f"Gold: {gold_cost:,}, Gear: {gear_cost}" if can_upgrade else f"Need: {gold_cost:,} gold, {gear_cost} {gear_type}"

                self.all_items.append({
                    'id': hunter_id,
                    'name': hunter_obj.name,
                    'type': 'hunter',
                    'level': level,
                    'tier': tier,
                    'rarity': hunter_obj.rarity.lower(),
                    'can_upgrade': can_upgrade,
                    'upgrade_info': upgrade_info,
                    'obj': hunter_obj
                })

        # Collect weapons
        weapons = self.player.get_inventory()
        for weapon_id, data in weapons.items():
            if weapon_id.startswith('s_') or not isinstance(data, dict) or 'level' not in data:
                continue

            weapon_obj = await ItemManager.get(weapon_id)
            if weapon_obj:
                level = data.get('level', 1)
                tier = data.get('tier', 1)

                # Calculate upgrade requirements
                gold_cost = 1000 + (level * 300) + ((level // 10) * 1000)
                if tier >= 3 or level >= 40:
                    gear_cost = (12 * level) + ((level // 15) * 35)
                    gear_type = "gear3"
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear3 >= gear_cost
                elif tier >= 2 or level >= 20:
                    gear_cost = (8 * level) + ((level // 15) * 20)
                    gear_type = "gear2"
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear2 >= gear_cost
                else:
                    gear_cost = (5 * level) + ((level // 15) * 10)
                    gear_type = "gear1"
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear1 >= gear_cost

                upgrade_info = f"Gold: {gold_cost:,}, Gear: {gear_cost}" if can_upgrade else f"Need: {gold_cost:,} gold, {gear_cost} {gear_type}"

                self.all_items.append({
                    'id': weapon_id,
                    'name': weapon_obj.name,
                    'type': 'weapon',
                    'level': level,
                    'tier': tier,
                    'rarity': weapon_obj.rarity.lower(),
                    'can_upgrade': can_upgrade,
                    'upgrade_info': upgrade_info,
                    'obj': weapon_obj
                })

        # Collect shadows
        shadows = self.player.get_shadows()
        for shadow_id, data in shadows.items():
            shadow_obj = await Shadow.get(shadow_id)
            if shadow_obj:
                level = data.get('level', 1)
                tos_cost = level * 100
                can_upgrade = self.player.tos >= tos_cost

                upgrade_info = f"TOS: {tos_cost}" if can_upgrade else f"Need: {tos_cost} TOS"

                self.all_items.append({
                    'id': shadow_id,
                    'name': shadow_obj.name,
                    'type': 'shadow',
                    'level': level,
                    'tier': 1,
                    'rarity': shadow_obj.rarity.lower() if hasattr(shadow_obj, 'rarity') else 'common',
                    'can_upgrade': can_upgrade,
                    'upgrade_info': upgrade_info,
                    'obj': shadow_obj
                })

    def apply_filters(self):
        """Apply current filters to all items"""
        filtered = self.all_items.copy()

        # Filter by type
        if self.current_filter != "all":
            filtered = [item for item in filtered if item['type'] == self.current_filter]

        # Filter by rarity
        if self.current_rarity != "all":
            filtered = [item for item in filtered if item['rarity'] == self.current_rarity]

        # Filter by upgrade status
        if self.current_status == "upgradeable":
            filtered = [item for item in filtered if item['can_upgrade']]
        elif self.current_status == "not_upgradeable":
            filtered = [item for item in filtered if not item['can_upgrade']]

        # Filter by search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [item for item in filtered if query in item['name'].lower()]

        # Sort by upgrade status (upgradeable first), then by level (highest first)
        filtered.sort(key=lambda x: (x['can_upgrade'], x['level']), reverse=True)

        return filtered

    async def update_select_options(self, page_items):
        """Update the select menu with current page items"""
        options = []

        if not page_items:
            options.append(discord.SelectOption(
                label="No items available",
                value="no_items",
                description="No items match your current filters",
                emoji="❌"
            ))
        else:
            for item in page_items[:25]:  # Discord limit
                status_emoji = "✅" if item['can_upgrade'] else "❌"
                description = f"Level {item['level']} • {item['rarity'].title()} • {status_emoji}"

                options.append(discord.SelectOption(
                    label=f"{item['name']} (Lv. {item['level']})",
                    value=item['id'],
                    description=description[:100],  # Discord limit
                    emoji=getEmoji(item['id']) if hasattr(item['obj'], 'id') else "🔧"
                ))

        # Update select menu
        for item in self.children:
            if isinstance(item, discord.ui.Select) and item.placeholder and "Select item" in item.placeholder:
                item.options = options
                break

    @discord.ui.select(placeholder="🔧 Select item to upgrade...", row=0)
    async def item_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle item selection for upgrade"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        if select.values[0] == "no_items":
            await interaction.response.send_message("❌ No items available to upgrade.", ephemeral=True)
            return

        # Show upgrade details for selected item
        item_id = select.values[0]
        item = next((i for i in self.all_items if i['id'] == item_id), None)

        if item and self.upgrade_cog:
            await self.upgrade_cog.show_upgrade_details(interaction, item['type'], item_id)

    @discord.ui.select(
        placeholder="📂 Filter by type...",
        options=[
            discord.SelectOption(label="All Types", value="all", emoji="🔧"),
            discord.SelectOption(label="Hunters", value="hunter", emoji="🏆"),
            discord.SelectOption(label="Weapons", value="weapon", emoji="🗡️"),
            discord.SelectOption(label="Shadows", value="shadow", emoji="👻")
        ],
        row=1
    )
    async def type_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Filter by item type"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        self.current_filter = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="⭐ Filter by rarity...",
        options=[
            discord.SelectOption(label="All Rarities", value="all", emoji="🔧"),
            discord.SelectOption(label="Common", value="common", emoji="⚪"),
            discord.SelectOption(label="Rare", value="rare", emoji="🔵"),
            discord.SelectOption(label="Epic", value="epic", emoji="🟣"),
            discord.SelectOption(label="Legendary", value="legendary", emoji="🟡")
        ],
        row=2
    )
    async def rarity_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Filter by rarity"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        self.current_rarity = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="✅ Filter by status...",
        options=[
            discord.SelectOption(label="All Items", value="all", emoji="🔧"),
            discord.SelectOption(label="Can Upgrade", value="upgradeable", emoji="✅"),
            discord.SelectOption(label="Cannot Upgrade", value="not_upgradeable", emoji="❌")
        ],
        row=3
    )
    async def status_filter(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Filter by upgrade status"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        self.current_status = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=4)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on the first page.", ephemeral=True)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=4)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        filtered_items = self.apply_filters()
        total_pages = max(1, math.ceil(len(filtered_items) / self.items_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Already on the last page.", ephemeral=True)

    @discord.ui.button(label="🔄 Reset Filters", style=discord.ButtonStyle.danger, row=4)
    async def reset_filters(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reset all filters"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return

        self.current_filter = "all"
        self.current_rarity = "all"
        self.current_status = "all"
        self.search_query = ""
        self.current_page = 0
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class UpgradeAllItemsView(ui.View):
    """Paginated view for showing all upgradeable items"""

    def __init__(self, author, player, upgrade_cog=None):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.upgrade_cog = upgrade_cog
        self.current_page = 0
        self.items_per_page = 15
        self.all_items = []

    async def create_main_embed(self):
        """Create the main embed with all upgradeable items"""
        await self.collect_all_items()

        total_items = len(self.all_items)
        total_pages = max(1, math.ceil(total_items / self.items_per_page))

        # Ensure current page is valid
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_items)
        page_items = self.all_items[start_idx:end_idx]

        embed = discord.Embed(
            title="🔍 **ALL UPGRADEABLE ITEMS**",
            description=f"Complete inventory scan for upgradeable content\n"
                       f"**Total Items**: {total_items} | **Page**: {self.current_page + 1}/{total_pages}",
            color=INFO_COLOR
        )

        if page_items:
            # Group items by type
            hunters = [item for item in page_items if item['type'] == 'hunter']
            weapons = [item for item in page_items if item['type'] == 'weapon']
            shadows = [item for item in page_items if item['type'] == 'shadow']

            # Add hunters section
            if hunters:
                hunter_text = ""
                for item in hunters:
                    status = "✅" if item['can_upgrade'] else "❌"
                    hunter_text += f"{status} **{item['name']}** (Lv.{item['level']})\n"
                    hunter_text += f"   💰 {item['cost_text']}\n"

                embed.add_field(
                    name=f"🏆 **Hunters ({len(hunters)})**",
                    value=hunter_text,
                    inline=False
                )

            # Add weapons section
            if weapons:
                weapon_text = ""
                for item in weapons:
                    status = "✅" if item['can_upgrade'] else "❌"
                    tier_text = f", T.{item['tier']}" if item['tier'] > 1 else ""
                    weapon_text += f"{status} **{item['name']}** (Lv.{item['level']}{tier_text})\n"
                    weapon_text += f"   💰 {item['cost_text']}\n"

                embed.add_field(
                    name=f"⚔️ **Weapons ({len(weapons)})**",
                    value=weapon_text,
                    inline=False
                )

            # Add shadows section
            if shadows:
                shadow_text = ""
                for item in shadows:
                    status = "✅" if item['can_upgrade'] else "❌"
                    shadow_text += f"{status} **{item['name']}** (Lv.{item['level']})\n"
                    shadow_text += f"   {getEmoji('trace')} {item['cost_text']}\n"

                embed.add_field(
                    name=f"👻 **Shadows ({len(shadows)})**",
                    value=shadow_text,
                    inline=False
                )
        else:
            embed.add_field(
                name="❌ **No Items Found**",
                value="No upgradeable items found in your inventory.",
                inline=False
            )

        # Add summary
        hunters_count = len([item for item in self.all_items if item['type'] == 'hunter'])
        weapons_count = len([item for item in self.all_items if item['type'] == 'weapon'])
        shadows_count = len([item for item in self.all_items if item['type'] == 'shadow'])

        embed.add_field(
            name="📊 **Summary**",
            value=f"**Total**: {total_items} | **Hunters**: {hunters_count} | **Weapons**: {weapons_count} | **Shadows**: {shadows_count}",
            inline=False
        )

        embed.set_footer(text="Use the buttons below to navigate • Timeout: 5 minutes")
        return embed

    async def collect_all_items(self):
        """Collect all upgradeable items from player inventory"""
        self.all_items = []

        # Check hunters
        hunters = self.player.get_hunters()
        for hunter_id, data in hunters.items():
            if isinstance(data, dict) and 'level' in data:
                level = data.get('level', 1)
                tier = data.get('tier', 1)
                hunter_obj = await HeroManager.get(hunter_id)
                if hunter_obj:
                    # Calculate upgrade cost
                    gold_cost = level * 1000
                    gear_cost = max(1, level // 10)
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear1 >= gear_cost

                    self.all_items.append({
                        'type': 'hunter',
                        'name': hunter_obj.name,
                        'level': level,
                        'tier': tier,
                        'can_upgrade': can_upgrade,
                        'cost_text': f"Gold: {gold_cost:,}, Gear: {gear_cost}"
                    })

        # Check weapons
        inventory = self.player.get_inventory()
        for item_id, data in inventory.items():
            if not item_id.startswith('s_') and isinstance(data, dict) and 'level' in data:
                level = data.get('level', 1)
                tier = data.get('tier', 1)
                item_obj = await ItemManager.get(item_id)
                if item_obj:
                    # Calculate upgrade cost
                    gold_cost = level * 1000
                    gear_cost = max(1, level // 10)
                    can_upgrade = self.player.gold >= gold_cost and self.player.gear1 >= gear_cost

                    self.all_items.append({
                        'type': 'weapon',
                        'name': item_obj.name,
                        'level': level,
                        'tier': tier,
                        'can_upgrade': can_upgrade,
                        'cost_text': f"Gold: {gold_cost:,}, Gear: {gear_cost}"
                    })

        # Check shadows
        shadows = self.player.get_shadows()
        for shadow_id, shadow_data in shadows.items():
            shadow_obj = await Shadow.get(shadow_id)
            if shadow_obj:
                level = shadow_data.get('level', 1)
                tos_cost = level * 100
                can_upgrade = self.player.tos >= tos_cost

                self.all_items.append({
                    'type': 'shadow',
                    'name': shadow_obj.name,
                    'level': level,
                    'tier': 1,
                    'can_upgrade': can_upgrade,
                    'cost_text': f"TOS: {tos_cost:,}"
                })

        # Sort by upgrade availability, then by level
        self.all_items.sort(key=lambda x: (x['can_upgrade'], x['level']), reverse=True)

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not your upgrade view.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the first page.", ephemeral=True)

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not your upgrade view.", ephemeral=True)
            return

        total_pages = max(1, math.ceil(len(self.all_items) / self.items_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the last page.", ephemeral=True)

    @ui.button(label="🔄 Back to Upgrade", style=discord.ButtonStyle.primary, row=0)
    async def back_to_upgrade(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This is not your upgrade view.", ephemeral=True)
            return

        # Go back to main upgrade view
        embed = create_embed(
            title="Upgrade System",
            description="What would you like to upgrade? Please select a category below.",
            color=INFO_COLOR,
            author=self.author
        )
        view = UpgradeTypeSelectView(self.author, self.upgrade_cog)
        await interaction.response.edit_message(embed=embed, view=view)


class UpgradeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="upgrade", aliases=['up'], help="Interactively upgrade a hunter or weapon.")
    async def upgrade(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed("Not Registered", "You don't have a profile yet. Use `/start` to get started!", ERROR_COLOR, ctx.author)
            await ctx.send(embed=embed, ephemeral=True)
            return

        embed = create_embed(
            title="Upgrade System",
            description="What would you like to upgrade? Please select a category below.",
            color=INFO_COLOR,
            author=ctx.author
        )
        view = UpgradeTypeSelectView(ctx.author, self)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="cubes", help="Debug command to check all your elemental cube counts.")
    async def cube_debug_command(self, ctx: commands.Context):
        """Debug command to check cube counts across all systems"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed("Player Not Found", "You need to start your journey first! Use `sl start` to begin.", ERROR_COLOR, ctx.author)
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Comprehensive cube validation function
        def get_all_cube_sources(player, cube_attr, class_type):
            """Get cube count from all possible sources with detailed breakdown"""
            direct_count = getattr(player, cube_attr, 0)
            inventory = player.get_inventory()
            inventory_sources = {}

            # Use the same comprehensive detection as the upgrade system
            for key, item_data in inventory.items():
                key_lower = key.lower()
                class_lower = class_type.lower()

                # Check if this is a cube item for this element
                is_cube_item = False

                # Standard element matching
                if 'cube' in key_lower and class_lower in key_lower:
                    is_cube_item = True

                # Special case for Earth cubes (sandstorm_cube)
                elif class_type == "Earth" and 'cube' in key_lower and ('sandstorm' in key_lower or 'earth' in key_lower):
                    is_cube_item = True

                # Check element aliases
                elif 'cube' in key_lower:
                    element_aliases = {
                        'Fire': ['flame', 'burn', 'heat', 'inferno'],
                        'Water': ['ice', 'frost', 'aqua', 'hydro', 'ocean'],
                        'Wind': ['air', 'storm', 'gale', 'breeze', 'tornado'],
                        'Earth': ['stone', 'rock', 'ground', 'sand', 'sandstorm', 'terra'],
                        'Light': ['holy', 'divine', 'radiant', 'bright', 'solar'],
                        'Dark': ['shadow', 'void', 'night', 'evil', 'lunar']
                    }

                    if class_type in element_aliases:
                        for alias in element_aliases[class_type]:
                            if alias in key_lower:
                                is_cube_item = True
                                break

                if is_cube_item:
                    if isinstance(item_data, dict):
                        quantity = item_data.get('quantity', item_data.get('level', item_data.get('amount', 0)))
                    elif isinstance(item_data, int):
                        quantity = item_data
                    else:
                        quantity = 0
                    if quantity > 0:
                        inventory_sources[key] = quantity

            return direct_count, inventory_sources

        embed = create_embed(
            "🧊 Elemental Cube Debug Report",
            "Comprehensive cube count analysis across all storage systems",
            INFO_COLOR,
            ctx.author
        )

        cube_types = [
            ("Fire", "fcube"), ("Water", "icube"), ("Wind", "wcube"),
            ("Earth", "ecube"), ("Light", "lcube"), ("Dark", "dcube")
        ]

        total_direct = 0
        total_inventory = 0

        for class_type, cube_attr in cube_types:
            direct_count, inventory_sources = get_all_cube_sources(player, cube_attr, class_type)
            inventory_total = sum(inventory_sources.values())

            total_direct += direct_count
            total_inventory += inventory_total

            # Create field for each cube type
            field_value = f"**Direct ({cube_attr})**: `{direct_count}`\n"

            if inventory_sources:
                field_value += f"**Inventory Sources**:\n"
                for key, count in inventory_sources.items():
                    field_value += f"  • {key}: `{count}`\n"
                field_value += f"**Inventory Total**: `{inventory_total}`\n"
            else:
                field_value += f"**Inventory Sources**: None found\n"

            field_value += f"**Combined Total**: `{max(direct_count, inventory_total)}`"

            element_emoji = getEmoji(f'{class_type.lower()}_element') or "❓"
            embed.add_field(
                name=f"{element_emoji} {class_type} Cubes",
                value=field_value,
                inline=True
            )

        # Summary
        embed.add_field(
            name="📊 Summary",
            value=(
                f"**Total Direct Cubes**: `{total_direct}`\n"
                f"**Total Inventory Cubes**: `{total_inventory}`\n"
                f"**Grand Total**: `{total_direct + total_inventory}`"
            ),
            inline=False
        )

        # Additional debug info
        inventory = player.get_inventory()
        cube_related_keys = [k for k in inventory.keys() if 'cube' in k.lower()]

        if cube_related_keys:
            embed.add_field(
                name="🔍 All Cube-Related Inventory Keys",
                value=f"Found {len(cube_related_keys)} cube-related items:\n" +
                      "\n".join([f"• {key}" for key in cube_related_keys[:10]]) +
                      (f"\n... and {len(cube_related_keys) - 10} more" if len(cube_related_keys) > 10 else ""),
                inline=False
            )

        embed.set_footer(text="If you're having cube issues, share this report for debugging!")

        # Send as ephemeral if it's an interaction
        try:
            from utilis.interaction_handler import InteractionHandler
            if ctx.interaction:
                success = await InteractionHandler.safe_response(ctx.interaction, embed=embed, ephemeral=True)
                if not success:
                    await ctx.reply(embed=embed, mention_author=False)
            else:
                await ctx.reply(embed=embed, mention_author=False)
        except:
            await ctx.reply(embed=embed, mention_author=False)

    async def show_upgrade_details(self, interaction: discord.Interaction, item_type: str, item_id: str):
        player = await Player.get(interaction.user.id)

        # Handle special cases for empty inventories
        if item_id.startswith('no_'):
            embed = create_embed(
                "No Items Available",
                f"You don't have any {item_type}s to upgrade. Acquire some {item_type}s first!",
                WARNING_COLOR,
                interaction.user
            )
            await interaction.message.edit(embed=embed, view=None)
            return

        if item_type == 'shadow':
            # Handle shadows with validation
            from structure.shadow import Shadow
            shadows = player.get_shadows()
            item_data = shadows.get(item_id)

            if not item_data:
                embed = create_embed(
                    "Shadow Not Found",
                    f"You don't own this shadow or it was removed from your collection.",
                    ERROR_COLOR,
                    interaction.user
                )
                await interaction.message.edit(embed=embed, view=None)
                return

            item_obj = await Shadow.get(item_id)
            if not item_obj:
                embed = create_embed(
                    "Shadow Data Missing",
                    f"Shadow data not found in database. Contact an administrator.",
                    ERROR_COLOR,
                    interaction.user
                )
                await interaction.message.edit(embed=embed, view=None)
                return

            level = item_data.get('level', 1)
            tier = 0  # Shadows don't have tiers
        else:
            # Handle hunters and weapons with comprehensive validation
            is_hunter = item_type == 'hunter'
            inventory = player.get_hunters() if is_hunter else player.get_inventory()
            item_data = inventory.get(item_id)

            if not item_data:
                embed = create_embed(
                    f"{item_type.capitalize()} Not Found",
                    f"You don't own this {item_type} or it was removed from your inventory.",
                    ERROR_COLOR,
                    interaction.user
                )
                await interaction.message.edit(embed=embed, view=None)
                return

            # Validate that this is an upgradeable item
            if not isinstance(item_data, dict) or 'level' not in item_data:
                embed = create_embed(
                    "Not Upgradeable",
                    f"This {item_type} doesn't have upgrade data. It may be a consumable or special item.",
                    WARNING_COLOR,
                    interaction.user
                )
                await interaction.message.edit(embed=embed, view=None)
                return

            item_obj = await (HeroManager.get(item_id) if is_hunter else ItemManager.get(item_id))
            if not item_obj:
                embed = create_embed(
                    "Item Data Missing",
                    f"Item data not found in database. Item ID: {item_id}",
                    ERROR_COLOR,
                    interaction.user
                )
                await interaction.message.edit(embed=embed, view=None)
                return

            level = item_data.get('level', 1)
            tier = item_data.get('tier', 0)

        # Define level caps for limit breaks
        limit_break_caps = [10, 20, 40, 60, 80, 100]
        level_cap = limit_break_caps[tier] if tier < len(limit_break_caps) else 100

        embed = create_embed(f"Upgrade: {item_obj.name}", color=INFO_COLOR, author=interaction.user)

        if item_type == 'shadow':
            embed.set_thumbnail(url=item_obj.image)
        else:
            embed.set_thumbnail(url=getEmoji(item_obj.id, as_url=True))

        if item_type == 'shadow':
            # Shadow-specific display
            xp = item_data.get('xp', 0)
            required_xp = level * 1000  # Shadow XP formula
            xp_bar = create_progress_bar(xp, required_xp)

            embed.add_field(
                name="Shadow Level & Experience",
                value=f"**Level**: `{level}` (Max: 100)\n**XP**: {xp_bar}",
                inline=False
            )

            embed.add_field(
                name="Shadow Stats",
                value=f"**Attack Boost**: `+{item_obj.attack}%`\n**Defense Boost**: `+{item_obj.defense}%`",
                inline=True
            )

            # Shadow upgrade costs (using Traces of Shadow)
            tos_cost = level * 100  # 100 TOS per level
            can_upgrade = player.tos >= tos_cost
            status_emoji = "✅" if can_upgrade else "❌"

            embed.add_field(
                name="💰 Materials Required for +1 Level",
                value=(
                    f"{getEmoji('trace')} **Traces of Shadow**: `{tos_cost:,}` / `{player.tos:,}` {status_emoji}\n"
                    f"**Status**: {'Can upgrade!' if can_upgrade else 'Insufficient materials'}"
                ),
                inline=False
            )

            # Show max possible upgrades
            max_upgrades = 0
            temp_tos = player.tos
            temp_level = level
            while temp_level < 100 and temp_tos >= (temp_level * 100):
                temp_tos -= temp_level * 100
                temp_level += 1
                max_upgrades += 1

            if max_upgrades > 0:
                embed.add_field(
                    name="📊 Upgrade Potential",
                    value=f"**Max Levels**: +{max_upgrades} (to Level {level + max_upgrades})",
                    inline=True
                )

        elif item_type == 'hunter':
            xp = item_data.get('xp', 0)
            xp_needed = level * 100
            xp_bar = create_progress_bar(xp, xp_needed)
            embed.add_field(name="Level & Experience", value=f"**Level**: `{level}` / `{level_cap}` (Tier {tier})\n**XP**: {xp_bar}", inline=False)

            # Show limit break requirements if at level cap
            if level >= level_cap and tier < len(limit_break_caps) - 1:
                shard_requirements = [1, 1, 2, 2, 4]
                cube_requirements = [5, 10, 20, 40, 60]

                # Check current shards
                shard_key = f"s_{item_id}"
                player_inventory = player.get_inventory()
                current_shards = 0

                if shard_key in player_inventory:
                    shard_data = player_inventory[shard_key]
                    if isinstance(shard_data, dict):
                        current_shards = shard_data.get('quantity', shard_data.get('level', 0))
                    elif isinstance(shard_data, int):
                        current_shards = shard_data

                # Check current cubes using classType
                class_type = getattr(item_obj, 'classType', 'Fire')
                cube_mapping = {
                    'Fire': 'fcube',
                    'Water': 'icube',
                    'Wind': 'wcube',
                    'Earth': 'ecube',
                    'Light': 'lcube',
                    'Dark': 'dcube'
                }
                cube_attr = cube_mapping.get(class_type, 'fcube')
                current_cubes = getattr(player, cube_attr, 0)

                # DEBUG: Print cube information
                print(f"DEBUG - Display Cube Check:")
                print(f"  Item: {item_id}")
                print(f"  Class Type: {class_type}")
                print(f"  Cube Attribute: {cube_attr}")
                print(f"  Current Cubes: {current_cubes}")

                required_shards = shard_requirements[tier]
                required_cubes = cube_requirements[tier]

                embed.add_field(
                    name="🌟 Limit Break Requirements",
                    value=(
                        f"{getEmoji(item_id)} **Shards**: `{current_shards}` / `{required_shards}`\n"
                        f"{getEmoji(f'{class_type.lower()}_element')} **{class_type} Cubes**: `{current_cubes}` / `{required_cubes}`\n"
                        f"**Next Level Cap**: `{limit_break_caps[tier + 1]}`"
                    ),
                    inline=False
                )
            else:
                gold_cost = (150 * level) + ((level // 10) * 500)

                # Determine gear type based on tier (higher tier = more expensive)
                if tier >= 3:  # High tier hunters need more gear
                    gear_cost = (8 * level) + ((level // 10) * 25)
                    gear_type = "gear3"
                    gear_name = "Enhancement Gear III"
                    player_gear = player.gear3
                elif tier >= 2:  # Mid tier hunters
                    gear_cost = (5 * level) + ((level // 10) * 15)
                    gear_type = "gear2"
                    gear_name = "Enhancement Gear II"
                    player_gear = player.gear2
                else:  # Low tier hunters (cheapest)
                    gear_cost = (3 * level) + ((level // 10) * 10)
                    gear_type = "gear1"
                    gear_name = "Enhancement Gear I"
                    player_gear = player.gear1

                can_upgrade_gold = player.gold >= gold_cost
                can_upgrade_gear = player_gear >= gear_cost
                can_upgrade = can_upgrade_gold and can_upgrade_gear

                gold_emoji = "✅" if can_upgrade_gold else "❌"
                gear_emoji = "✅" if can_upgrade_gear else "❌"

                embed.add_field(
                    name="💰 Materials Required for +1 Level",
                    value=(
                        f"{getEmoji('gold')} **Gold**: `{gold_cost:,}` / `{player.gold:,}` {gold_emoji}\n"
                        f"{getEmoji(gear_type)} **{gear_name}**: `{gear_cost}` / `{player_gear}` {gear_emoji}\n"
                        f"**Status**: {'Can upgrade!' if can_upgrade else 'Insufficient materials'}"
                    ),
                    inline=False
                )

                # Show max possible upgrades
                max_upgrades = 0
                temp_gold = player.gold
                temp_gear1 = player.gear1
                temp_level = level

                while temp_level < level_cap:
                    level_gold_cost = (150 * temp_level) + ((temp_level // 10) * 500)
                    level_gear1_cost = (5 * temp_level) + ((temp_level // 10) * 25)

                    if temp_gold >= level_gold_cost and temp_gear1 >= level_gear1_cost:
                        temp_gold -= level_gold_cost
                        temp_gear1 -= level_gear1_cost
                        temp_level += 1
                        max_upgrades += 1
                    else:
                        break

                if max_upgrades > 0:
                    embed.add_field(
                        name="📊 Upgrade Potential",
                        value=f"**Max Levels**: +{max_upgrades} (to Level {level + max_upgrades})",
                        inline=True
                    )
        else: # It's a weapon
            xp = item_data.get('xp', 0)
            xp_needed = (level * 100) + ((level // 10) * 2000) # Weapons need more xp
            xp_bar = create_progress_bar(xp, xp_needed)
            embed.add_field(name="Level & Experience", value=f"**Level**: `{level}` / `{level_cap}` (Tier {tier})\n**XP**: {xp_bar}", inline=False)

            # Show limit break requirements if at level cap
            if level >= level_cap and tier < len(limit_break_caps) - 1:
                shard_requirements = [1, 1, 2, 2, 4]
                cube_requirements = [5, 10, 20, 40, 60]

                # Check current shards
                shard_key = f"s_{item_id}"
                player_inventory = player.get_inventory()
                current_shards = 0

                if shard_key in player_inventory:
                    shard_data = player_inventory[shard_key]
                    if isinstance(shard_data, dict):
                        current_shards = shard_data.get('quantity', shard_data.get('level', 0))
                    elif isinstance(shard_data, int):
                        current_shards = shard_data

                # Check current cubes using classType
                class_type = getattr(item_obj, 'classType', 'Fire')
                cube_mapping = {
                    'Fire': 'fcube',
                    'Water': 'icube',
                    'Wind': 'wcube',
                    'Earth': 'ecube',
                    'Light': 'lcube',
                    'Dark': 'dcube'
                }
                cube_attr = cube_mapping.get(class_type, 'fcube')
                current_cubes = getattr(player, cube_attr, 0)

                required_shards = shard_requirements[tier]
                required_cubes = cube_requirements[tier]

                embed.add_field(
                    name="🌟 Limit Break Requirements",
                    value=(
                        f"{getEmoji(item_id)} **Shards**: `{current_shards}` / `{required_shards}`\n"
                        f"{getEmoji(f'{class_type.lower()}_element')} **{class_type} Cubes**: `{current_cubes}` / `{required_cubes}`\n"
                        f"**Next Level Cap**: `{limit_break_caps[tier + 1]}`"
                    ),
                    inline=False
                )
            else:
                gold_cost = 1000 + (level * 300) + ((level // 10) * 1000)

                # Determine gear type based on tier and level for weapons (higher tier = more expensive)
                if tier >= 3 or level >= 40:  # High tier/level weapons (most expensive)
                    gear_cost = (12 * level) + ((level // 15) * 35)
                    gear_type = "gear3"
                    gear_name = "Enhancement Gear III"
                    player_gear = player.gear3
                elif tier >= 2 or level >= 20:  # Mid tier/level weapons
                    gear_cost = (8 * level) + ((level // 15) * 20)
                    gear_type = "gear2"
                    gear_name = "Enhancement Gear II"
                    player_gear = player.gear2
                else:  # Low tier/level weapons (cheapest)
                    gear_cost = (5 * level) + ((level // 15) * 10)
                    gear_type = "gear1"
                    gear_name = "Enhancement Gear I"
                    player_gear = player.gear1

                can_upgrade_gold = player.gold >= gold_cost
                can_upgrade_gear = player_gear >= gear_cost
                can_upgrade = can_upgrade_gold and can_upgrade_gear

                gold_emoji = "✅" if can_upgrade_gold else "❌"
                gear_emoji = "✅" if can_upgrade_gear else "❌"

                embed.add_field(
                    name="💰 Materials Required for +1 Level",
                    value=(
                        f"{getEmoji('gold')} **Gold**: `{gold_cost:,}` / `{player.gold:,}` {gold_emoji}\n"
                        f"{getEmoji(gear_type)} **{gear_name}**: `{gear_cost}` / `{player_gear}` {gear_emoji}\n"
                        f"**Status**: {'Can upgrade!' if can_upgrade else 'Insufficient materials'}"
                    ),
                    inline=False
                )

                # Show max possible upgrades for weapons
                max_upgrades = 0
                temp_gold = player.gold
                temp_gear1 = player.gear1
                temp_level = level

                while temp_level < level_cap:
                    level_gold_cost = 1000 + (temp_level * 300) + ((temp_level // 10) * 1000)
                    level_gear1_cost = 10 * temp_level

                    if temp_gold >= level_gold_cost and temp_gear1 >= level_gear1_cost:
                        temp_gold -= level_gold_cost
                        temp_gear1 -= level_gear1_cost
                        temp_level += 1
                        max_upgrades += 1
                    else:
                        break

                if max_upgrades > 0:
                    embed.add_field(
                        name="📊 Upgrade Potential",
                        value=f"**Max Levels**: +{max_upgrades} (to Level {level + max_upgrades})",
                        inline=True
                    )
        
        view = UpgradeActionsView(interaction.user, self, item_type, item_id)
        await interaction.message.edit(embed=embed, view=view)


class UpgradeActionsView(ui.View):
    def __init__(self, author: discord.User, upgrade_cog, item_type: str, item_id: str):
        super().__init__(timeout=180)
        self.author = author
        self.upgrade_cog = upgrade_cog
        self.item_type = item_type
        self.item_id = item_id

        # Only add limit break button for items and hunters, not shadows
        if self.item_type != 'shadow':
            self.add_item(LimitBreakButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False
        return True

    async def perform_upgrade(self, interaction: discord.Interaction, levels_to_add: int):
        await interaction.response.defer()
        player = await Player.get(self.author.id)

        if self.item_type == 'shadow':
            await self.perform_shadow_upgrade(interaction, player, levels_to_add)
            return

        is_hunter = self.item_type == 'hunter'
        inventory = player.get_hunters() if is_hunter else player.get_inventory()
        item_data = inventory.get(self.item_id)
        
        if not item_data:
            embed = create_embed("Error", f"Could not find the {self.item_type} to upgrade.", ERROR_COLOR, self.author)
            await interaction.edit_original_response(embed=embed, view=None)
            return

        current_level = item_data.get('level', 1)
        tier = item_data.get('tier', 0)
        
        # Define level caps for limit breaks
        limit_break_caps = [10, 20, 40, 60, 80, 100]
        level_cap = limit_break_caps[tier] if tier < len(limit_break_caps) else 100

        # Check if at level cap and needs limit break
        at_level_cap = current_level >= level_cap and tier < len(limit_break_caps) - 1

        # If a specific number of levels isn't provided, calculate the max possible
        if levels_to_add == -1: # -1 will signify "MAX"
            levels_to_add = 0
            temp_gold = player.gold

            # Determine gear type based on tier
            if is_hunter:
                if tier >= 3:
                    temp_gear = player.gear3
                    gear_attr = "gear3"
                elif tier >= 2:
                    temp_gear = player.gear2
                    gear_attr = "gear2"
                else:
                    temp_gear = player.gear1
                    gear_attr = "gear1"
            else:  # weapon
                if tier >= 3 or current_level >= 40:
                    temp_gear = player.gear3
                    gear_attr = "gear3"
                elif tier >= 2 or current_level >= 20:
                    temp_gear = player.gear2
                    gear_attr = "gear2"
                else:
                    temp_gear = player.gear1
                    gear_attr = "gear1"

            for i in range(current_level, level_cap):
                level_for_cost = current_level + levels_to_add
                if is_hunter:
                    gold_cost = (150 * level_for_cost) + ((level_for_cost // 10) * 500)
                    if tier >= 3:
                        gear_cost = (8 * level_for_cost) + ((level_for_cost // 10) * 25)
                    elif tier >= 2:
                        gear_cost = (5 * level_for_cost) + ((level_for_cost // 10) * 15)
                    else:
                        gear_cost = (3 * level_for_cost) + ((level_for_cost // 10) * 10)
                else: # Weapon costs
                    gold_cost = 1000 + (level_for_cost * 300) + ((level_for_cost // 10) * 1000)
                    if tier >= 3 or level_for_cost >= 40:
                        gear_cost = (12 * level_for_cost) + ((level_for_cost // 15) * 35)
                    elif tier >= 2 or level_for_cost >= 20:
                        gear_cost = (8 * level_for_cost) + ((level_for_cost // 15) * 20)
                    else:
                        gear_cost = (5 * level_for_cost) + ((level_for_cost // 15) * 10)

                if temp_gold >= gold_cost and temp_gear >= gear_cost:
                    temp_gold -= gold_cost
                    temp_gear -= gear_cost
                    levels_to_add += 1
                else:
                    break
            
            if levels_to_add == 0:
                embed = create_embed("Cannot Upgrade", "You don't have enough materials for even one level.", WARNING_COLOR, self.author)
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        if current_level + levels_to_add > level_cap:
            levels_to_add = level_cap - current_level
            if levels_to_add <= 0:
                embed = create_embed(
                    "Limit Break Required",
                    f"This {self.item_type} is at its current level cap of `{level_cap}` and needs a Limit-Break to upgrade further.",
                    WARNING_COLOR,
                    self.author
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        # Calculate total costs with correct gear types
        total_gold_cost = 0
        total_gear_cost = 0

        # Determine gear type based on tier
        if is_hunter:
            if tier >= 3:
                gear_attr = "gear3"
                player_gear = player.gear3
            elif tier >= 2:
                gear_attr = "gear2"
                player_gear = player.gear2
            else:
                gear_attr = "gear1"
                player_gear = player.gear1
        else:  # weapon
            if tier >= 3 or current_level >= 40:
                gear_attr = "gear3"
                player_gear = player.gear3
            elif tier >= 2 or current_level >= 20:
                gear_attr = "gear2"
                player_gear = player.gear2
            else:
                gear_attr = "gear1"
                player_gear = player.gear1

        for i in range(levels_to_add):
            level_for_cost = current_level + i
            if is_hunter:
                total_gold_cost += (150 * level_for_cost) + ((level_for_cost // 10) * 500)
                if tier >= 3:
                    total_gear_cost += (8 * level_for_cost) + ((level_for_cost // 10) * 25)
                elif tier >= 2:
                    total_gear_cost += (5 * level_for_cost) + ((level_for_cost // 10) * 15)
                else:
                    total_gear_cost += (3 * level_for_cost) + ((level_for_cost // 10) * 10)
            else: # Weapon costs
                total_gold_cost += 1000 + (level_for_cost * 300) + ((level_for_cost // 10) * 1000)
                if tier >= 3 or level_for_cost >= 40:
                    total_gear_cost += (12 * level_for_cost) + ((level_for_cost // 15) * 35)
                elif tier >= 2 or level_for_cost >= 20:
                    total_gear_cost += (8 * level_for_cost) + ((level_for_cost // 15) * 20)
                else:
                    total_gear_cost += (5 * level_for_cost) + ((level_for_cost // 15) * 10)

        if player.gold < total_gold_cost or player_gear < total_gear_cost:
            embed = create_embed("Insufficient Materials", f"You can't afford to upgrade by `{levels_to_add}` levels.", ERROR_COLOR, self.author)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Deduct costs
        player.gold -= total_gold_cost
        setattr(player, gear_attr, player_gear - total_gear_cost)

        # Apply level ups
        # For now, we just add levels. XP system can be added if needed.
        item_data['level'] += levels_to_add

        await player.save()

        # Track mission progress
        await track_mission_progress(self.author.id, "upgrade", levels_to_add)

        # Refresh the details view
        await self.upgrade_cog.show_upgrade_details(interaction, self.item_type, self.item_id)
        
        item_obj = await (HeroManager.get(self.item_id) if is_hunter else ItemManager.get(self.item_id))
        embed = create_embed(
            "Upgrade Successful!",
            f"**{item_obj.name}** is now **Level `{item_data['level']}`**!\n"
            f"**Levels Gained**: `{levels_to_add}`",
            SUCCESS_COLOR,
            self.author
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def perform_shadow_upgrade(self, interaction: discord.Interaction, player, levels_to_add: int):
        """Handle shadow upgrades using Traces of Shadow"""
        from structure.shadow import Shadow

        shadows = player.get_shadows()
        shadow_data = shadows.get(self.item_id)

        if not shadow_data:
            embed = create_embed("Error", "Could not find the shadow to upgrade.", ERROR_COLOR, self.author)
            await interaction.edit_original_response(embed=embed, view=None)
            return

        current_level = shadow_data.get('level', 1)

        # Calculate total cost for shadow upgrades
        if levels_to_add == -1:  # MAX upgrade
            levels_to_add = 0
            temp_tos = player.tos
            temp_level = current_level

            while temp_level < 100 and temp_tos >= (temp_level * 100):
                cost = temp_level * 100
                temp_tos -= cost
                temp_level += 1
                levels_to_add += 1

            if levels_to_add == 0:
                embed = create_embed("Insufficient Resources", "You don't have enough Traces of Shadow to upgrade this shadow.", WARNING_COLOR, self.author)
                await interaction.edit_original_response(embed=embed, view=None)
                return

        # Calculate total cost
        total_cost = 0
        for i in range(levels_to_add):
            level_cost = (current_level + i) * 100
            total_cost += level_cost

        # Check if player has enough TOS
        if player.tos < total_cost:
            embed = create_embed(
                "Insufficient Resources",
                f"You need **{total_cost:,}** {getEmoji('trace')} Traces of Shadow to upgrade by {levels_to_add} level{'s' if levels_to_add > 1 else ''}.\n\nYou have: **{player.tos:,}** TOS",
                WARNING_COLOR,
                self.author
            )
            await interaction.edit_original_response(embed=embed, view=None)
            return

        # Perform upgrade
        player.tos -= total_cost

        # Add XP to level up the shadow
        xp_to_add = 0
        for i in range(levels_to_add):
            level_xp_needed = (current_level + i) * 1000
            xp_to_add += level_xp_needed

        player.add_shadow(self.item_id, xp_to_add)
        await player.save()

        # Track mission progress
        await track_mission_progress(self.author.id, "upgrade", levels_to_add)

        # Refresh the details view
        await self.upgrade_cog.show_upgrade_details(interaction, self.item_type, self.item_id)

        shadow_obj = await Shadow.get(self.item_id)
        new_level = current_level + levels_to_add

        embed = create_embed(
            "🌟 Shadow Upgrade Successful!",
            f"**{shadow_obj.name}** is now **Level `{new_level}`**!\n"
            f"**Levels Gained**: `{levels_to_add}`\n"
            f"**Cost**: {getEmoji('trace')} `{total_cost:,}` TOS",
            SUCCESS_COLOR,
            self.author
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def perform_limit_break(self, interaction: discord.Interaction):
        """Perform limit break on the selected item"""
        await interaction.response.defer()
        player = await Player.get(self.author.id)

        is_hunter = self.item_type == 'hunter'
        inventory = player.get_hunters() if is_hunter else player.get_inventory()
        item_data = inventory.get(self.item_id)

        if not item_data:
            embed = create_embed("Error", "Could not find the item to limit break.", ERROR_COLOR, self.author)
            await interaction.edit_original_response(embed=embed, view=None)
            return

        # Handle both dict and int item_data formats
        if isinstance(item_data, dict):
            current_level = item_data.get('level', 1)
            tier = item_data.get('tier', 0)
        else:
            # Convert integer to dict format for consistency
            current_level = item_data if isinstance(item_data, int) else 1
            tier = 0
            # Update the inventory with proper dict format
            item_data = {'level': current_level, 'tier': tier}
            inventory[self.item_id] = item_data

        # Ensure item_data is always a dict from this point forward
        if not isinstance(item_data, dict):
            item_data = {'level': current_level, 'tier': tier}
            inventory[self.item_id] = item_data

        # Define level caps and requirements for limit breaks
        limit_break_caps = [10, 20, 40, 60, 80, 100]
        shard_requirements = [1, 1, 2, 2, 4]  # Shards needed for each tier
        cube_requirements = [5, 10, 20, 40, 60]  # Cubes needed for each tier

        if tier >= len(limit_break_caps) - 1:
            embed = create_embed(
                "Max Tier Reached",
                f"This {self.item_type} is already at maximum tier!",
                WARNING_COLOR,
                self.author
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        required_level = limit_break_caps[tier]
        if current_level < required_level:
            embed = create_embed(
                "Level Requirement Not Met",
                f"This {self.item_type} must be level `{required_level}` to limit break.\n"
                f"Current level: `{current_level}`",
                WARNING_COLOR,
                self.author
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Check shard requirements
        shard_key = f"s_{self.item_id}"
        player_inventory = player.get_inventory()
        current_shards = 0

        if shard_key in player_inventory:
            shard_data = player_inventory[shard_key]
            if isinstance(shard_data, dict):
                current_shards = shard_data.get('quantity', shard_data.get('level', 0))
            elif isinstance(shard_data, int):
                current_shards = shard_data

        required_shards = shard_requirements[tier]
        if current_shards < required_shards:
            embed = create_embed(
                "Insufficient Shards",
                f"You need `{required_shards}` shards but only have `{current_shards}`.\n"
                f"Required: {getEmoji(self.item_id)} **x{required_shards}**",
                ERROR_COLOR,
                self.author
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Check cube requirements (use the item's classType)
        item_obj = await (HeroManager.get(self.item_id) if is_hunter else ItemManager.get(self.item_id))
        class_type = getattr(item_obj, 'classType', 'Fire')

        # Refresh player data to ensure we have the latest cube counts
        await player.save()  # Save any pending changes
        fresh_player = await Player.get(player.id)  # Get fresh data from database
        if fresh_player:
            player = fresh_player

        # Map classType to cube attributes
        cube_mapping = {
            'Fire': 'fcube',
            'Water': 'icube',
            'Wind': 'wcube',
            'Earth': 'ecube',
            'Light': 'lcube',
            'Dark': 'dcube'
        }

        cube_attr = cube_mapping.get(class_type, 'fcube')
        current_cubes = getattr(player, cube_attr, 0)
        required_cubes = cube_requirements[tier]

        print(f"DEBUG - Cube Requirements:")
        print(f"  Current tier: {tier}")
        print(f"  Cube requirements array: {cube_requirements}")
        print(f"  Required cubes for tier {tier}: {required_cubes}")
        print(f"  Array length: {len(cube_requirements)}")
        print(f"  Tier valid: {tier < len(cube_requirements)}")

        # Additional validation - check multiple sources for cube data

        # Use comprehensive cube count - this is the ACTUAL count we should use
        comprehensive_cubes = get_comprehensive_cube_count(player, cube_attr, class_type)
        current_cubes = comprehensive_cubes  # Use comprehensive count, not max

        # DEBUG: Print comprehensive cube information for ALL cube types
        print(f"DEBUG - Limit Break Cube Check:")
        print(f"  Item: {self.item_id}")
        print(f"  Class Type: {class_type}")
        print(f"  Cube Attribute: {cube_attr}")
        print(f"  Direct Cubes: {getattr(player, cube_attr, 0)}")
        print(f"  Comprehensive Cubes: {comprehensive_cubes}")
        print(f"  Final Current Cubes: {current_cubes}")
        print(f"  Required Cubes: {required_cubes}")
        print(f"  VALIDATION RESULT: {'PASS' if current_cubes >= required_cubes else 'FAIL'}")
        print(f"")
        print(f"  ALL PLAYER CUBE COUNTS:")
        print(f"    Fire Cubes (fcube): {getattr(player, 'fcube', 'NOT_FOUND')}")
        print(f"    Water Cubes (icube): {getattr(player, 'icube', 'NOT_FOUND')}")
        print(f"    Wind Cubes (wcube): {getattr(player, 'wcube', 'NOT_FOUND')}")
        print(f"    Earth Cubes (ecube): {getattr(player, 'ecube', 'NOT_FOUND')}")
        print(f"    Light Cubes (lcube): {getattr(player, 'lcube', 'NOT_FOUND')}")
        print(f"    Dark Cubes (dcube): {getattr(player, 'dcube', 'NOT_FOUND')}")
        print(f"    Custom Cubes (ccube): {getattr(player, 'ccube', 'NOT_FOUND')}")
        print(f"")
        print(f"  INVENTORY CUBE SEARCH:")
        inventory = player.get_inventory()
        cube_related_keys = [k for k in inventory.keys() if 'cube' in k.lower()]
        print(f"    Cube-related inventory keys: {cube_related_keys}")
        for key in cube_related_keys[:5]:  # Show first 5 cube-related items
            item_data = inventory[key]
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', item_data.get('level', 0))
            else:
                quantity = item_data
            print(f"      {key}: {quantity}")
        print(f"  Player inventory total keys: {len(list(player.get_inventory().keys()))}")
        print(f"")
        print(f"  COMPREHENSIVE CUBE DETECTION TEST:")
        test_comprehensive = get_comprehensive_cube_count(player, cube_attr, class_type)
        print(f"    get_comprehensive_cube_count returned: {test_comprehensive}")
        print(f"    This should match Final Current Cubes: {current_cubes}")
        print(f"="*50)

        if current_cubes < required_cubes:
            element_emoji = getEmoji(f'{class_type.lower()}_element') or "❓"
            cube_emoji = getEmoji(cube_attr) or "🧊"

            embed = create_embed(
                "Insufficient Elemental Cubes",
                f"You need **{required_cubes}** {class_type} cubes but only have **{current_cubes}**.\n\n"
                f"**Required for Limit Break:**\n"
                f"{element_emoji} {cube_emoji} **{class_type} Cubes**: `{required_cubes}`\n\n"
                f"**Your Current Cubes:**\n"
                f"{element_emoji} {cube_emoji} **{class_type} Cubes**: `{current_cubes}`\n\n"
                f"**How to Get More Cubes:**\n"
                f"• Complete dungeons and raids\n"
                f"• Sacrifice duplicate items\n"
                f"• Participate in events\n"
                f"• Use `sl cubes` to check all your cube counts",
                ERROR_COLOR,
                self.author
            )

            # Add field showing all cube types for reference
            all_cubes_text = []
            cube_types = [("Fire", "fcube"), ("Water", "icube"), ("Wind", "wcube"), ("Earth", "ecube"), ("Light", "lcube"), ("Dark", "dcube")]
            for ct, ca in cube_types:
                count = getattr(player, ca, 0)
                emoji = getEmoji(f'{ct.lower()}_element') or "❓"
                cube_e = getEmoji(ca) or "🧊"
                status = "✅" if count > 0 else "❌"
                all_cubes_text.append(f"{status} {emoji} {cube_e} {ct}: `{count:,}`")

            embed.add_field(
                name="📊 All Your Cube Counts",
                value="\n".join(all_cubes_text),
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Perform the limit break
        # Deduct shards
        if isinstance(player_inventory[shard_key], dict):
            player_inventory[shard_key]['quantity'] = current_shards - required_shards
            if player_inventory[shard_key]['quantity'] <= 0:
                del player_inventory[shard_key]
        else:
            player_inventory[shard_key] = current_shards - required_shards
            if player_inventory[shard_key] <= 0:
                del player_inventory[shard_key]

        # Deduct cubes - handle both direct attributes and inventory sources
        await self.deduct_cubes_comprehensive(player, cube_attr, class_type, required_cubes, current_cubes)

        # Increase tier - ensure item_data is dict and update inventory
        if not isinstance(item_data, dict):
            item_data = {'level': current_level, 'tier': tier}

        item_data['tier'] = tier + 1

        # CRITICAL FIX: Update the correct player attribute directly
        if is_hunter:
            player.hunters[self.item_id] = item_data
        else:
            player.inventory[self.item_id] = item_data

        # Also update the local inventory reference for consistency
        inventory[self.item_id] = item_data

        await player.save()

        # VERIFICATION: Double-check that the tier was actually updated
        verification_player = await Player.get(self.author.id)
        verification_inventory = verification_player.get_hunters() if is_hunter else verification_player.get_inventory()
        verification_data = verification_inventory.get(self.item_id, {})
        actual_tier = verification_data.get('tier', 0) if isinstance(verification_data, dict) else 0

        if actual_tier != tier + 1:
            # If verification fails, try to fix it immediately
            if is_hunter:
                verification_player.hunters[self.item_id] = item_data
            else:
                verification_player.inventory[self.item_id] = item_data
            await verification_player.save()
            print(f"🔧 LIMIT BREAK FIX: Corrected tier for {self.item_id} from {actual_tier} to {tier + 1}")

        # Track mission progress for limit break (items/hunters only, not shadows)
        await track_mission_progress(self.author.id, "break", 1)

        # Refresh the details view
        await self.upgrade_cog.show_upgrade_details(interaction, self.item_type, self.item_id)

        new_level_cap = limit_break_caps[tier + 1]
        embed = create_embed(
            "🌟 Limit Break Successful!",
            f"**{item_obj.name}** has been limit broken!\n"
            f"**New Tier**: `{tier + 1}`\n"
            f"**New Level Cap**: `{new_level_cap}`\n"
            f"**Materials Used**: {getEmoji(self.item_id)} x{int(required_shards)}, {getEmoji(f'{class_type.lower()}_element')} x{int(required_cubes)}",
            SUCCESS_COLOR,
            self.author
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def deduct_cubes_comprehensive(self, player, cube_attr, class_type, required_cubes, total_available):
        """Deduct cubes from both direct attributes and inventory sources"""
        remaining_to_deduct = required_cubes

        # First, try to deduct from direct attribute
        direct_cubes = getattr(player, cube_attr, 0)
        if direct_cubes > 0:
            deduct_from_direct = min(direct_cubes, remaining_to_deduct)
            setattr(player, cube_attr, direct_cubes - deduct_from_direct)
            remaining_to_deduct -= deduct_from_direct

        # If we still need to deduct more, remove from inventory
        if remaining_to_deduct > 0:
            inventory = player.get_inventory()

            # Find cube items in inventory and deduct from them
            for key in list(inventory.keys()):  # Use list() to avoid modification during iteration
                if remaining_to_deduct <= 0:
                    break

                key_lower = key.lower()
                class_lower = class_type.lower()

                # Check if this inventory item contains cubes of the needed type
                is_cube_item = False

                # Standard element matching
                if 'cube' in key_lower and class_lower in key_lower:
                    is_cube_item = True

                # Special case for Earth cubes (sandstorm_cube)
                elif class_type == "Earth" and 'cube' in key_lower and ('sandstorm' in key_lower or 'earth' in key_lower):
                    is_cube_item = True

                # Check element aliases
                elif 'cube' in key_lower:
                    element_aliases = {
                        'Fire': ['flame', 'burn', 'heat', 'inferno'],
                        'Water': ['ice', 'frost', 'aqua', 'hydro', 'ocean'],
                        'Wind': ['air', 'storm', 'gale', 'breeze', 'tornado'],
                        'Earth': ['stone', 'rock', 'ground', 'sand', 'sandstorm', 'terra'],
                        'Light': ['holy', 'divine', 'radiant', 'bright', 'solar'],
                        'Dark': ['shadow', 'void', 'night', 'evil', 'lunar']
                    }

                    if class_type in element_aliases:
                        for alias in element_aliases[class_type]:
                            if alias in key_lower:
                                is_cube_item = True
                                break

                if is_cube_item:
                    item_data = inventory[key]
                    if isinstance(item_data, dict):
                        current_quantity = item_data.get('quantity', item_data.get('level', item_data.get('amount', 0)))
                    elif isinstance(item_data, int):
                        current_quantity = item_data
                    else:
                        current_quantity = 0

                    if current_quantity > 0:
                        deduct_from_item = min(current_quantity, remaining_to_deduct)
                        new_quantity = current_quantity - deduct_from_item
                        remaining_to_deduct -= deduct_from_item

                        # Update or remove the inventory item
                        if new_quantity <= 0:
                            del inventory[key]
                        else:
                            if isinstance(item_data, dict):
                                if 'quantity' in item_data:
                                    item_data['quantity'] = new_quantity
                                elif 'level' in item_data:
                                    item_data['level'] = new_quantity
                                elif 'amount' in item_data:
                                    item_data['amount'] = new_quantity
                            else:
                                inventory[key] = new_quantity

        print(f"DEBUG - Cube Deduction Complete:")
        print(f"  Required: {required_cubes}")
        print(f"  Remaining after deduction: {remaining_to_deduct}")
        print(f"  Successfully deducted: {required_cubes - remaining_to_deduct}")

    @ui.button(label="Upgrade x1", style=discord.ButtonStyle.success, row=0)
    async def upgrade_x1(self, interaction: discord.Interaction, button: ui.Button):
        await self.perform_upgrade(interaction, 1)

    @ui.button(label="Upgrade x5", style=discord.ButtonStyle.success, row=0)
    async def upgrade_x5(self, interaction: discord.Interaction, button: ui.Button):
        await self.perform_upgrade(interaction, 5)

    @ui.button(label="Upgrade MAX", style=discord.ButtonStyle.success, row=0)
    async def upgrade_max(self, interaction: discord.Interaction, button: ui.Button):
        await self.perform_upgrade(interaction, -1) # Use -1 to signify MAX



    @ui.button(label="Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        # This will take the user back to the item selection
        view = UpgradeItemSelectView(self.author, self.item_type, self.upgrade_cog)
        await view.populate_items()
        embed = create_embed(f"Upgrade {self.item_type.capitalize()}", f"Select the {self.item_type} you wish to upgrade.", INFO_COLOR, self.author)
        await interaction.response.edit_message(embed=embed, view=view)


class LimitBreakButton(ui.Button):
    """Separate limit break button for items and hunters only"""
    def __init__(self):
        super().__init__(label="🌟 Limit Break", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        await self.view.perform_limit_break(interaction)


async def setup(bot):
    await bot.add_cog(UpgradeCog(bot))
