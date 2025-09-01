import discord
from discord.ext import commands
from discord import ui
from structure.items import ItemManager
from utilis.utilis import getStatWeapon
from structure.emoji import getEmoji
from structure.player import Player
from typing import Optional
import time
from datetime import datetime, timedelta

class StatResetConfirmView(ui.View):
    """Confirmation view for stat reset"""

    def __init__(self, user_id: int, player):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.player = player

    @ui.button(label="✅ Confirm Reset", style=discord.ButtonStyle.danger)
    async def confirm_reset(self, interaction: discord.Interaction, button: ui.Button):
        """Confirm the stat reset"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        # Refresh player data
        fresh_player = await Player.get(self.user_id)
        if not fresh_player:
            await interaction.response.send_message("❌ Player data not found!", ephemeral=True)
            return

        if fresh_player.trade:
            await interaction.response.send_message("❌ You can't reset stats while trading!", ephemeral=True)
            return

        # Check cooldown again
        if not self._can_reset_stats(fresh_player):
            await interaction.response.send_message("❌ You can only reset stats once per week!", ephemeral=True)
            return

        # Use fixed base stats - players should get their original base stats back
        # and receive full skill points based on their level to redistribute
        base_stats = {
            "attack": 10,   # Original base attack
            "defense": 10,  # Original base defense
            "hp": 100,      # Original base health
            "mp": 10,       # Original base mana
            "precision": 10 # Original base precision
        }

        # Reset stats to base values
        for stat_name, base_value in base_stats.items():
            setattr(fresh_player, stat_name, base_value)

        # Give player full stat points including achievement bonuses
        # This ensures they get all stat points they should have for their level + achievements
        total_stat_points = await fresh_player.calculate_total_stat_points_with_achievements()
        fresh_player.statPoints = total_stat_points

        # Set reset timestamp
        fresh_player.last_stat_reset = int(time.time())

        await fresh_player.save()

        # Create success embed
        embed = discord.Embed(
            title="🔄 Stats Reset Successful!",
            description="Your stats have been reset to base values and full stat points restored!",
            color=discord.Color.green()
        )

        # Calculate stat point breakdown
        base_points = fresh_player.level * 10
        achievement_bonus = await fresh_player.get_achievement_stat_points()

        embed.add_field(
            name="📊 Reset Details",
            value=(
                f"**⚔️ Attack:** Reset to {base_stats['attack']}\n"
                f"**🛡️ Defense:** Reset to {base_stats['defense']}\n"
                f"**❤️ Health:** Reset to {base_stats['hp']}\n"
                f"**💙 Mana:** Reset to {base_stats['mp']}\n"
                f"**🎯 Precision:** Reset to {base_stats['precision']}"
            ),
            inline=False
        )

        stat_points_breakdown = f"**📊 Stat Points:** {fresh_player.statPoints}\n"
        stat_points_breakdown += f"   • Base (Level {fresh_player.level} × 10): {base_points}\n"
        if achievement_bonus > 0:
            stat_points_breakdown += f"   • Achievement Bonus: +{achievement_bonus}\n"

        embed.add_field(
            name="💎 Stat Points Restored",
            value=stat_points_breakdown,
            inline=False
        )

        # Calculate next reset time
        next_reset = datetime.fromtimestamp(fresh_player.last_stat_reset + 604800)  # 7 days
        embed.add_field(
            name="⏰ Next Reset Available",
            value=f"<t:{int(next_reset.timestamp())}:F>",
            inline=False
        )

        embed.set_footer(text="Use 'sl stats' to view your reset stats!")

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, interaction: discord.Interaction, button: ui.Button):
        """Cancel the stat reset"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        embed = discord.Embed(
            title="❌ Stat Reset Cancelled",
            description="Your stats remain unchanged.",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    def _can_reset_stats(self, player) -> bool:
        """Check if player can reset stats (once per week)"""
        if not hasattr(player, 'last_stat_reset') or player.last_stat_reset is None:
            return True

        current_time = int(time.time())
        time_since_reset = current_time - player.last_stat_reset
        return time_since_reset >= 604800  # 7 days in seconds

class StatUpgradeView(ui.View):
    """Interactive view for stat upgrades"""

    def __init__(self, user_id: int, player):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.player = player
        self.selected_stat = None
        self.points_to_spend = 1

        # Ensure player has statPoints attribute
        if not hasattr(player, 'statPoints') or player.statPoints is None:
            player.statPoints = player.level * 10  # 10 stat points per level

        # Stat information - BALANCED INCREMENTS
        self.stat_info = {
            "attack": {"emoji": "⚔️", "name": "Attack", "increment": 10, "description": "Increases damage dealt"},
            "defense": {"emoji": "🛡️", "name": "Defense", "increment": 10, "description": "Reduces damage taken"},
            "hp": {"emoji": "❤️", "name": "Health", "increment": 15, "description": "Increases maximum health"},
            "mp": {"emoji": "💙", "name": "Mana", "increment": 5, "description": "Increases maximum mana"},
            "precision": {"emoji": "🎯", "name": "Precision", "increment": 10, "description": "Improves accuracy and critical hits"}
        }

        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current selection"""
        self.clear_items()

        # Add stat selection buttons
        for stat_key, info in self.stat_info.items():
            button = ui.Button(
                label=f"{info['emoji']} {info['name']}",
                style=discord.ButtonStyle.primary if stat_key == self.selected_stat else discord.ButtonStyle.secondary,
                custom_id=f"stat_{stat_key}"
            )
            button.callback = self.create_stat_callback(stat_key)
            self.add_item(button)

        # Add point adjustment buttons if stat is selected
        if self.selected_stat:
            # Point adjustment row
            minus_button = ui.Button(label="➖", style=discord.ButtonStyle.secondary, custom_id="minus", row=1)
            minus_button.callback = self.decrease_points
            self.add_item(minus_button)

            points_button = ui.Button(label=f"{self.points_to_spend} Points", style=discord.ButtonStyle.secondary, disabled=True, row=1)
            self.add_item(points_button)

            plus_button = ui.Button(label="➕", style=discord.ButtonStyle.secondary, custom_id="plus", row=1)
            plus_button.callback = self.increase_points
            self.add_item(plus_button)

            # Upgrade button
            upgrade_button = ui.Button(label="🚀 Upgrade!", style=discord.ButtonStyle.success, custom_id="upgrade", row=2)
            upgrade_button.callback = self.upgrade_stat
            self.add_item(upgrade_button)

            # Reset button
            reset_button = ui.Button(label="🔄 Reset", style=discord.ButtonStyle.secondary, custom_id="reset", row=2)
            reset_button.callback = self.reset_selection
            self.add_item(reset_button)

        # Reset stats button (only if player can reset)
        if self._can_reset_stats():
            reset_stats_button = ui.Button(label="🔄 Reset All Stats", style=discord.ButtonStyle.danger, row=3 if self.selected_stat else 1)
            reset_stats_button.callback = self.reset_all_stats
            self.add_item(reset_stats_button)

        # Close button
        close_button = ui.Button(label="❌ Close", style=discord.ButtonStyle.secondary, row=4 if (self.selected_stat and self._can_reset_stats()) else (3 if self.selected_stat else (2 if self._can_reset_stats() else 1)))
        close_button.callback = self.close_menu
        self.add_item(close_button)

    def create_stat_callback(self, stat_key):
        """Create callback for stat selection buttons"""
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
                return

            self.selected_stat = stat_key
            self.points_to_spend = 1
            self.update_buttons()

            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

        return callback

    async def decrease_points(self, interaction: discord.Interaction):
        """Decrease points to spend"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        if self.points_to_spend > 1:
            self.points_to_spend -= 1
            self.update_buttons()

            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def increase_points(self, interaction: discord.Interaction):
        """Increase points to spend"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        if self.points_to_spend < self.player.statPoints:
            self.points_to_spend += 1
            self.update_buttons()

            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def upgrade_stat(self, interaction: discord.Interaction):
        """Perform the stat upgrade"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        if not self.selected_stat or self.points_to_spend < 1:
            await interaction.response.send_message("❌ Please select a stat and points to spend!", ephemeral=True)
            return

        if self.points_to_spend > self.player.statPoints:
            await interaction.response.send_message("❌ You don't have enough stat points!", ephemeral=True)
            return

        # Refresh player data
        fresh_player = await Player.get(self.user_id)
        if not fresh_player:
            await interaction.response.send_message("❌ Player data not found!", ephemeral=True)
            return

        if fresh_player.trade:
            await interaction.response.send_message("❌ You can't upgrade stats while trading!", ephemeral=True)
            return

        # Perform upgrade
        stat_info = self.stat_info[self.selected_stat]
        increment = stat_info["increment"]
        upgrade_value = self.points_to_spend * increment

        # Update the stat
        previous_value = getattr(fresh_player, self.selected_stat)
        setattr(fresh_player, self.selected_stat, previous_value + upgrade_value)
        fresh_player.statPoints -= self.points_to_spend

        await fresh_player.save()

        # Update local player reference
        self.player = fresh_player

        # Create success embed
        embed = discord.Embed(
            title="🚀 Stat Upgrade Successful!",
            description=f"**{stat_info['emoji']} {stat_info['name']}** has been upgraded!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Upgrade Details",
            value=(
                f"**Points Used:** {self.points_to_spend} 📊\n"
                f"**Stat Increase:** +{upgrade_value}\n"
                f"**Previous Value:** {previous_value}\n"
                f"**New Value:** {previous_value + upgrade_value}\n"
                f"**Remaining Points:** {fresh_player.statPoints} 📊"
            ),
            inline=False
        )

        embed.set_footer(text="Continue upgrading or close the menu!")

        # Reset selection
        self.selected_stat = None
        self.points_to_spend = 1
        self.update_buttons()

        await interaction.response.edit_message(embed=embed, view=self)

    async def reset_selection(self, interaction: discord.Interaction):
        """Reset the current selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        self.selected_stat = None
        self.points_to_spend = 1
        self.update_buttons()

        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def reset_all_stats(self, interaction: discord.Interaction):
        """Show stat reset confirmation"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        if not self._can_reset_stats():
            # Calculate next reset time
            next_reset = datetime.fromtimestamp(self.player.last_stat_reset + 604800)
            embed = discord.Embed(
                title="❌ Stat Reset Not Available",
                description=f"You can only reset stats once per week!\n\n**Next reset available:** <t:{int(next_reset.timestamp())}:R>",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Use fixed base stats for preview - show what they'll get back to
        base_stats = {
            "attack": 10,   # Original base attack
            "defense": 10,  # Original base defense
            "hp": 100,      # Original base health
            "mp": 10,       # Original base mana
            "precision": 10 # Original base precision
        }
        # Calculate full stat points they'll get (level × 10 + achievement bonuses)
        full_stat_points = await self.player.calculate_total_stat_points_with_achievements()
        reset_preview = ""
        has_stats_to_reset = False

        # Show what stats will be reset
        for stat_name, base_value in base_stats.items():
            current_value = getattr(self.player, stat_name)
            if current_value != base_value:
                has_stats_to_reset = True
                stat_emoji = self.stat_info[stat_name]["emoji"]
                reset_preview += f"{stat_emoji} **{self.stat_info[stat_name]['name']}:** {current_value} → {base_value}\n"

        if not has_stats_to_reset:
            embed = discord.Embed(
                title="ℹ️ No Stats to Reset",
                description="Your stats are already at base values. No changes needed!",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Show confirmation dialog
        embed = discord.Embed(
            title="⚠️ Confirm Stat Reset",
            description="**Are you sure you want to reset all your stats?**\n\nThis action cannot be undone and can only be done once per week!",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📊 Stats Will Be Reset To:",
            value=reset_preview,
            inline=False
        )

        # Calculate stat point breakdown for display
        base_points = self.player.level * 10
        achievement_bonus = await self.player.get_achievement_stat_points()

        stat_points_breakdown = f"**{full_stat_points}** stat points\n"
        stat_points_breakdown += f"   • Base (Level {self.player.level} × 10): {base_points}\n"
        if achievement_bonus > 0:
            stat_points_breakdown += f"   • Achievement Bonus: +{achievement_bonus}"

        embed.add_field(
            name="📊 Stat Points After Reset",
            value=stat_points_breakdown,
            inline=False
        )

        embed.set_footer(text="⚠️ This action can only be done once per week!")

        confirm_view = StatResetConfirmView(self.user_id, self.player)
        await interaction.response.edit_message(embed=embed, view=confirm_view)

    async def close_menu(self, interaction: discord.Interaction):
        """Close the upgrade menu"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use this menu!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📊 Stat Upgrade Menu Closed",
            description="Thanks for using the stat upgrade system!\n\nUse `sl stats` to view your updated statistics.",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    def _can_reset_stats(self) -> bool:
        """Check if player can reset stats (once per week)"""
        if not hasattr(self.player, 'last_stat_reset') or self.player.last_stat_reset is None:
            return True

        current_time = int(time.time())
        time_since_reset = current_time - self.player.last_stat_reset
        return time_since_reset >= 604800  # 7 days in seconds

    def create_embed(self):
        """Create the main embed for the upgrade interface"""
        embed = discord.Embed(
            title="🚀 Interactive Stat Upgrade System",
            description="Select a stat to upgrade and choose how many points to spend!",
            color=discord.Color.blue()
        )

        # Add current stats
        stats_text = ""
        for stat_key, info in self.stat_info.items():
            current_value = getattr(self.player, stat_key)
            stats_text += f"{info['emoji']} **{info['name']}**: `{current_value}`\n"

        embed.add_field(
            name="📊 Current Stats",
            value=stats_text,
            inline=True
        )

        # Add stat points info
        embed.add_field(
            name="📊 Available Points",
            value=f"**{self.player.statPoints}** stat points\n\n*You get +5 📊 every level!*",
            inline=True
        )

        # Add upgrade effects
        effects_text = ""
        for stat_key, info in self.stat_info.items():
            effects_text += f"{info['emoji']} **{info['name']}**: +{info['increment']} per point\n"

        embed.add_field(
            name="💪 Upgrade Effects",
            value=effects_text,
            inline=False
        )

        # Add reset information
        if self._can_reset_stats():
            embed.add_field(
                name="🔄 Stat Reset Available",
                value="You can reset all stats to base values once per week!\nClick the **Reset All Stats** button below.",
                inline=False
            )
        else:
            next_reset = datetime.fromtimestamp(self.player.last_stat_reset + 604800)
            embed.add_field(
                name="⏰ Next Reset Available",
                value=f"<t:{int(next_reset.timestamp())}:R>",
                inline=False
            )

        # Add selection info if stat is selected
        if self.selected_stat:
            stat_info = self.stat_info[self.selected_stat]
            current_value = getattr(self.player, self.selected_stat)
            upgrade_value = self.points_to_spend * stat_info["increment"]
            new_value = current_value + upgrade_value

            embed.add_field(
                name=f"🎯 Selected: {stat_info['emoji']} {stat_info['name']}",
                value=(
                    f"**Description:** {stat_info['description']}\n"
                    f"**Points to Spend:** {self.points_to_spend} 📊\n"
                    f"**Stat Increase:** +{upgrade_value}\n"
                    f"**Current → New:** `{current_value}` → `{new_value}`"
                ),
                inline=False
            )

        embed.set_footer(text="💡 Select a stat above to begin upgrading!")
        return embed

class StatUpgrade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats", help="View your stats.")
    async def stats(self, ctx):
        player = await Player.get(ctx.author.id)

        if not player:
            await ctx.send(
                embed=discord.Embed(
                    title="Player Not Found",
                    description="You don't have a profile yet. Use the bot to start your journey!",
                    color=discord.Color.red()
                )
            )
            return

        down = getEmoji("down")
        qx = getEmoji("qx")
        equipped_stats = {"attack": 0, "defense": 0, "hp": 0, "mp": 0, "precision": 0}

        for slot, item_id in player.equipped.items():
            if item_id:  # Check if there's an item equipped in this slot
                item_data = await ItemManager.get(item_id)  # Retrieve item stats
                if item_data:
                    # Handle weapon stats separately
                    if slot in ["Weapon", "Weapon_2"]:
                        try:
                            weapon_level = player.inventory.get(item_id, {}).get('level', 1)  # Default level 1
                            weapon_stat = await getStatWeapon(item_id, weapon_level)
                            if weapon_stat:
                                equipped_stats["attack"] += weapon_stat.get("attack", 0)
                                equipped_stats["defense"] += weapon_stat.get("defense", 0)
                                equipped_stats["hp"] += weapon_stat.get("hp", 0)
                                equipped_stats["mp"] += weapon_stat.get("mp", 0)
                        except Exception as e:
                            # Skip if there's an issue with weapon stats
                            continue
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Stats",
            description=f"Level: **{player.level}**\n**📊** Stat Points: **{player.statPoints}**\n-# {down} You get +10 📊 every level you gain\n__Stat Point Effects__\nAttack +10 , Defense +10 , Health +50 , Mana Points +5, Precision +10",
            color=discord.Color.dark_blue())
        Stats_ = f"""
        ```py
Health       : {player.hp:<5} +({equipped_stats['hp']})
Attack       : {player.attack:<5} +({equipped_stats['attack']})
Defense      : {player.defense:<5} +({equipped_stats['defense']})
Precision    : {player.precision:<5} +({equipped_stats['precision']})
Mana Points  : {player.mp:<5} +({equipped_stats['mp']})
```
"""
        lol = f"{qx}Attack: ` {player.attack} `\n{qx}Defense: ` {player.defense} `\n{qx}Health: ` {player.hp} `\n{qx}Precision: ` {player.precision} `\n{down}Mana Points: ` {player.mp} `"
        embed.add_field(name=f"{getEmoji('attack')} Statistics", value=Stats_, inline=True)
        embed.set_footer(text="Use sl su to upgrade your stats.")
        await ctx.send(embed=embed)
    
    @commands.command(name="statupgrade", aliases=["su"], help="Interactive stat upgrade system.")
    async def stats_upgrade(self, ctx, stat: Optional[str] = None, points: Optional[int] = None):
        player = await Player.get(ctx.author.id)

        if not player:
            await ctx.send(
                embed=discord.Embed(
                    title="Player Not Found",
                    description="You don't have a profile yet. Use the bot to start your journey!",
                    color=discord.Color.red()
                )
            )
            return

        # Check story lock for stat allocation
        from structure.story_campaign import check_story_lock
        can_access, lock_message = await check_story_lock(ctx.author.id, "double_dungeon_002", "Stat Allocation")
        if not can_access:
            embed = discord.Embed(
                title="🔒 Feature Locked",
                description=lock_message,
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        if player.trade:
            await ctx.send(f"<@{player.id}>, is in the middle of a 🤝 trade. Complete it before proceeding or join the support server if this is a bug.")
            return

        # Ensure player has statPoints attribute
        if not hasattr(player, 'statPoints') or player.statPoints is None:
            player.statPoints = player.level * 10  # 10 stat points per level
            await player.save()

        # If no stat points, show message
        if player.statPoints == 0:
            embed = discord.Embed(
                title="❌ No Stat Points Available",
                description="You don't have any stat points to spend!\n\n**How to get stat points:**\n• Level up (+10 📊 per level)\n• Complete daily missions\n• Participate in events",
                color=discord.Color.red()
            )
            embed.set_footer(text="Use 'sl stats' to view your current statistics.")
            await ctx.send(embed=embed)
            return

        # If old-style command with arguments, handle it
        if stat and points:
            await self._handle_legacy_upgrade(ctx, player, stat, points)
            return

        # Show interactive upgrade interface
        view = StatUpgradeView(ctx.author.id, player)
        embed = view.create_embed()

        await ctx.reply(embed=embed, view=view, mention_author=False)

    async def _handle_legacy_upgrade(self, ctx, player, stat: str, points: int):
        """Handle the old-style stat upgrade command for backwards compatibility"""
        # Validate points
        if points < 1:
            await ctx.send(
                embed=discord.Embed(
                    title="Invalid Points",
                    description="Points must be at least 1.",
                    color=discord.Color.red()
                )
            )
            return

        # Standard stat names and their aliases
        stat_aliases = {
            "attack": ["attack", "atk"],
            "defense": ["defense", "def", "df", "defence"],
            "hp": ["health", "hp"],
            "mp": ["mp", "mana"],
            "precision": ["precision", "acc", "accuracy"]
        }

        valid_stats = {
            "attack": 10,
            "defense": 10,
            "hp": 15,
            "mp": 5,
            "precision": 10
        }

        # Convert input to lowercase and match alias
        stat = stat.lower()
        matched_stat = None
        for key, aliases in stat_aliases.items():
            if stat in aliases:
                matched_stat = key
                break

        if not matched_stat:
            await ctx.send(
                embed=discord.Embed(
                    title="Invalid Stat",
                    description="Please choose a valid stat: Attack, Defense, Health, MP, or Precision.\n\n💡 **Tip:** Use `sl su` without arguments for the interactive upgrade menu!",
                    color=discord.Color.red()
                )
            )
            return

        if points > player.statPoints:
            await ctx.send(
                embed=discord.Embed(
                    title="Not Enough Points",
                    description=f"You don't have enough stat points to upgrade this stat.\n\n**Available:** {player.statPoints} 📊\n**Required:** {points} 📊",
                    color=discord.Color.red()
                )
            )
            return

        # Deduct stat points and apply the upgrade
        player.statPoints -= points
        increment = valid_stats[matched_stat]
        upgrade_value = points * increment

        # Update the correct stat
        previous_value = getattr(player, matched_stat)
        setattr(player, matched_stat, previous_value + upgrade_value)

        await player.save()

        # Enhanced success message
        stat_emojis = {
            "attack": "⚔️",
            "defense": "🛡️",
            "hp": "❤️",
            "mp": "💙",
            "precision": "🎯"
        }

        embed = discord.Embed(
            title="🚀 Stat Upgrade Successful!",
            description=f"**{stat_emojis.get(matched_stat, '📊')} {matched_stat.capitalize()}** has been upgraded!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Upgrade Details",
            value=(
                f"**Points Used:** {points} 📊\n"
                f"**Stat Increase:** +{upgrade_value}\n"
                f"**Previous Value:** {previous_value}\n"
                f"**New Value:** {previous_value + upgrade_value}\n"
                f"**Remaining Points:** {player.statPoints} 📊"
            ),
            inline=False
        )

        embed.set_footer(text="💡 Use 'sl su' for the interactive upgrade menu!")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="resetstats", aliases=["rs"], help="Reset all stats to base values (once per week).")
    async def reset_stats_command(self, ctx):
        """Standalone command for stat reset"""
        player = await Player.get(ctx.author.id)

        if not player:
            await ctx.send(
                embed=discord.Embed(
                    title="Player Not Found",
                    description="You don't have a profile yet. Use the bot to start your journey!",
                    color=discord.Color.red()
                )
            )
            return

        if player.trade:
            await ctx.send(f"<@{player.id}>, is in the middle of a 🤝 trade. Complete it before proceeding or join the support server if this is a bug.")
            return

        # Check if player can reset stats
        if not self._can_reset_stats_player(player):
            next_reset = datetime.fromtimestamp(player.last_stat_reset + 604800)
            embed = discord.Embed(
                title="❌ Stat Reset Not Available",
                description=f"You can only reset stats once per week!\n\n**Next reset available:** <t:{int(next_reset.timestamp())}:R>",
                color=discord.Color.red()
            )
            embed.set_footer(text="Use 'sl su' for the interactive upgrade menu!")
            await ctx.send(embed=embed)
            return

        # Use fixed base stats for standalone command
        base_stats = {
            "attack": 10,   # Original base attack
            "defense": 10,  # Original base defense
            "hp": 100,      # Original base health
            "mp": 10,       # Original base mana
            "precision": 10 # Original base precision
        }
        stat_emojis = {
            "attack": "⚔️", "defense": "🛡️", "hp": "❤️", "mp": "💙", "precision": "🎯"
        }

        # Calculate full stat points they'll get (level × 10 + achievement bonuses)
        full_stat_points = await player.calculate_total_stat_points_with_achievements()
        reset_preview = ""
        has_stats_to_reset = False

        # Show what stats will be reset
        for stat_name, base_value in base_stats.items():
            current_value = getattr(player, stat_name)
            if current_value != base_value:
                has_stats_to_reset = True
                stat_emoji = stat_emojis[stat_name]
                stat_display = stat_name.capitalize() if stat_name != "hp" else "Health"
                if stat_name == "mp":
                    stat_display = "Mana"
                reset_preview += f"{stat_emoji} **{stat_display}:** {current_value} → {base_value}\n"

        if not has_stats_to_reset:
            embed = discord.Embed(
                title="ℹ️ No Stats to Reset",
                description="Your stats are already at base values. No changes needed!",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Use 'sl su' to upgrade your stats!")
            await ctx.send(embed=embed)
            return

        # Show confirmation dialog
        embed = discord.Embed(
            title="⚠️ Confirm Stat Reset",
            description="**Are you sure you want to reset all your stats?**\n\nThis action cannot be undone and can only be done once per week!",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📊 Stats Will Be Reset To:",
            value=reset_preview,
            inline=False
        )

        # Calculate stat point breakdown for display
        base_points = player.level * 10
        achievement_bonus = await player.get_achievement_stat_points()

        stat_points_breakdown = f"**{full_stat_points}** stat points\n"
        stat_points_breakdown += f"   • Base (Level {player.level} × 10): {base_points}\n"
        if achievement_bonus > 0:
            stat_points_breakdown += f"   • Achievement Bonus: +{achievement_bonus}"

        embed.add_field(
            name="📊 Stat Points After Reset",
            value=stat_points_breakdown,
            inline=False
        )

        embed.set_footer(text="⚠️ This action can only be done once per week!")

        confirm_view = StatResetConfirmView(ctx.author.id, player)
        await ctx.reply(embed=embed, view=confirm_view, mention_author=False)

    def _can_reset_stats_player(self, player) -> bool:
        """Check if player can reset stats (once per week) - helper for standalone command"""
        if not hasattr(player, 'last_stat_reset') or player.last_stat_reset is None:
            return True

        current_time = int(time.time())
        time_since_reset = current_time - player.last_stat_reset
        return time_since_reset >= 604800  # 7 days in seconds

async def setup(bot):
    await bot.add_cog(StatUpgrade(bot))
