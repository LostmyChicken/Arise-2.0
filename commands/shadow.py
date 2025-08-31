import asyncio
import json
import random
import discord
from discord.ext import commands
from discord import app_commands, ui
import aiosqlite
from structure.emoji import getEmoji
from structure.player import Player
from utilis.utilis import extractId
from structure.shadow import Shadow

class ShadowPaginationView(ui.View):
    def __init__(self, ctx, shadows_data, total_pages, current_page=1):
        super().__init__(timeout=300)  # Increased timeout
        self.ctx = ctx
        self.shadows_data = shadows_data
        self.total_pages = total_pages
        self.current_page = current_page
        self.message = None
        self.authorized_user_id = ctx.author.id  # Store authorized user ID

    @ui.button(label="◀◀", style=discord.ButtonStyle.secondary, disabled=True)
    async def first_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        if self.current_page == 1:
            await interaction.response.send_message("You're already on the first page!", ephemeral=True)
            return

        self.current_page = 1
        await self.update_embed(interaction)

    @ui.button(label="◀", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        if self.current_page == 1:
            await interaction.response.send_message("You're already on the first page!", ephemeral=True)
            return

        self.current_page -= 1
        await self.update_embed(interaction)

    @ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        if self.current_page == self.total_pages:
            await interaction.response.send_message("You're already on the last page!", ephemeral=True)
            return

        self.current_page += 1
        await self.update_embed(interaction)

    @ui.button(label="▶▶", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        if self.current_page == self.total_pages:
            await interaction.response.send_message("You're already on the last page!", ephemeral=True)
            return

        self.current_page = self.total_pages
        await self.update_embed(interaction)

    @ui.button(label="🔮 Arise Shadow", style=discord.ButtonStyle.primary, row=1)
    async def arise_shadow(self, interaction: discord.Interaction, button: ui.Button):
        """Open arise shadow interface"""
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        arise_view = AriseShadowView(interaction.user.id)
        await arise_view.show_arise_interface(interaction)

    @ui.button(label="📊 Shadow Stats", style=discord.ButtonStyle.secondary, row=1)
    async def shadow_stats(self, interaction: discord.Interaction, button: ui.Button):
        """Show detailed shadow statistics"""
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        stats_view = ShadowStatsView(interaction.user.id, self.shadows_data)
        await stats_view.show_stats(interaction)

    @ui.button(label="🎯 Available Shadows", style=discord.ButtonStyle.success, row=1)
    async def available_shadows(self, interaction: discord.Interaction, button: ui.Button):
        """Show shadows available to unlock"""
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        available_view = AvailableShadowsView(interaction.user.id)
        await available_view.show_available(interaction)

    @ui.button(label="⚔️ Shadow Army", style=discord.ButtonStyle.danger, row=1)
    async def shadow_army(self, interaction: discord.Interaction, button: ui.Button):
        """Show shadow army formation"""
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        army_view = ShadowArmyView(interaction.user.id, self.shadows_data)
        await army_view.show_army(interaction)

    @ui.button(label="🗑️ Close", style=discord.ButtonStyle.danger, row=2)
    async def close_menu(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

    async def update_embed(self, interaction: discord.Interaction):
        try:
            embed = await self.create_embed()
            self.update_buttons()

            # Check if interaction is still valid
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                # Use followup if response is already done
                await interaction.followup.edit_message(
                    interaction.message.id,
                    embed=embed,
                    view=self
                )
        except discord.errors.NotFound:
            # Interaction expired, stop the view
            self.stop()
        except Exception as e:
            print(f"Error updating shadow embed: {e}")
            # Try to send error message if possible
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while updating the display.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ An error occurred while updating the display.", ephemeral=True)
            except:
                pass

    def update_buttons(self):
        # Update button states
        self.children[0].disabled = (self.current_page == 1)  # First page
        self.children[1].disabled = (self.current_page == 1)  # Previous page
        self.children[2].disabled = (self.current_page == self.total_pages)  # Next page
        self.children[3].disabled = (self.current_page == self.total_pages)  # Last page

    async def create_embed(self):
        shadows_per_page = 6
        start_index = (self.current_page - 1) * shadows_per_page
        end_index = min(start_index + shadows_per_page, len(self.shadows_data))

        current_shadows = list(self.shadows_data.items())[start_index:end_index]

        # Calculate total boosts
        total_attack_boost = sum(shadow_info['attack'] for shadow_info in self.shadows_data.values())
        total_defense_boost = sum(shadow_info['defense'] for shadow_info in self.shadows_data.values())

        embed = discord.Embed(
            title="👥 Shadow Army",
            description=f"**Total Shadows**: `{len(self.shadows_data)}`\n**🗡️ Attack Boost**: `+{total_attack_boost}%`\n**🛡️ Defense Boost**: `+{total_defense_boost}%`",
            color=discord.Color.dark_purple()
        )

        for shadow_id, shadow_info in current_shadows:
            shadow = shadow_info['shadow']
            data = shadow_info['data']

            # Calculate required XP for next level
            required_xp = data['level'] * 1000  # Simple formula

            # Add shadow description if available - make it more visible
            description = shadow.description if hasattr(shadow, 'description') and shadow.description else "A powerful shadow warrior"
            # Don't truncate description, show it in full

            embed.add_field(
                name=f"👤 {shadow.name}",
                value=(
                    f"**Level**: `{data['level']}`\n"
                    f"**XP**: `{data['xp']:,}` / `{required_xp:,}`\n"
                    f"**Attack**: `+{shadow.attack}%`\n"
                    f"**Defense**: `+{shadow.defense}%`"
                ),
                inline=True
            )

            # Add description as a separate field for better visibility
            embed.add_field(
                name="📖 Description",
                value=f"*{description}*",
                inline=False
            )

        embed.set_footer(text=f"Page {self.current_page}/{self.total_pages} • Use buttons below to manage your shadows")

        # Set image to the first shadow on the current page if available
        if current_shadows:
            first_shadow = current_shadows[0][1]  # Get the shadow_info from the tuple
            if first_shadow['shadow'].image:
                embed.set_image(url=first_shadow['shadow'].image)
            else:
                embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")
        else:
            embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")

        return embed

class ShadowCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shadows", description="View your obtained shadows")
    async def shadows(self, ctx):
        player = await Player.get(ctx.author.id)

        if not player:
            embed = discord.Embed(
                title="❌ Player Not Found",
                description="You don't have a profile yet. Use `sl start` to begin your journey!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        shadows = player.get_shadows()

        if not shadows:
            # Show available shadows and their requirements
            all_shadows = await Shadow.get_all()
            available_shadows = []
            locked_shadows = []

            boss_names = {
                "iron_golem": "Iron Golem",
                "shadow_knight": "Shadow Knight",
                "tank_demon": "Tank Demon",
                "orc_warlord": "Orc Warlord",
                "greed_demon": "Greed Demon",
                "igris_boss": "Igris (World Boss)"
            }

            for shadow in all_shadows:
                if shadow.required_boss and not player.has_defeated_boss(shadow.required_boss):
                    required_boss_name = boss_names.get(shadow.required_boss, shadow.required_boss)
                    locked_shadows.append(f"🔒 **{shadow.name}** - Defeat {required_boss_name}")
                else:
                    available_shadows.append(f"✅ **{shadow.name}** - {shadow.price} TOS")

            embed = discord.Embed(
                title="👥 Shadow Army",
                description="**Your shadow army is empty!**\n\nUse `sl arise <shadow_name>` to summon shadows and build your army.",
                color=discord.Color.dark_grey()
            )

            if available_shadows:
                embed.add_field(
                    name="✅ Available Shadows",
                    value="\n".join(available_shadows),
                    inline=False
                )

            if locked_shadows:
                embed.add_field(
                    name="🔒 Locked Shadows",
                    value="\n".join(locked_shadows),
                    inline=False
                )

            embed.add_field(
                name="❓ How Shadow Unlocking Works",
                value=(
                    "**🎯 Shadow Unlock Process:**\n"
                    "1️⃣ **Defeat World Boss** - Automatic 25% chance unlock attempt when boss is defeated\n"
                    "2️⃣ **Victory Screen** - Shows who got lucky with the 25% chance\n"
                    "3️⃣ **Retry with Arise** - Use `sl arise <shadow_name>` for additional 25% attempts\n\n"
                    "**🎲 RNG SYSTEM:**\n"
                    "• **25% chance** to unlock shadow from world boss victory\n"
                    "• **FREE attempt** when you participate in defeating the boss\n"
                    "• **Additional attempts** cost TOS via arise command\n"
                    "• **Same 25% rate** for both victory and arise attempts"
                ),
                inline=False
            )
            embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")
            embed.set_footer(text="Defeat world bosses for free 25% unlock attempts!")
            await ctx.send(embed=embed)
            return

        # Prepare shadow data with full info
        shadows_data = {}
        for shadow_id, shadow_data in shadows.items():
            shadow = await Shadow.get(shadow_id)
            if shadow:
                shadows_data[shadow_id] = {
                    'shadow': shadow,
                    'data': shadow_data,
                    'attack': shadow.attack,
                    'defense': shadow.defense
                }

        if not shadows_data:
            embed = discord.Embed(
                title="👥 Shadow Army",
                description="**No valid shadows found!**\n\nUse `sl arise <shadow_name>` to summon shadows.",
                color=discord.Color.dark_grey()
            )
            await ctx.send(embed=embed)
            return

        # Calculate pagination
        shadows_per_page = 6
        total_pages = max(1, (len(shadows_data) + shadows_per_page - 1) // shadows_per_page)

        # Create pagination view
        view = ShadowPaginationView(ctx, shadows_data, total_pages)
        embed = await view.create_embed()
        view.update_buttons()

        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @commands.hybrid_command(name="shadow_upgrade", aliases=['sup'], description="Upgrade your shadows using Traces of Shadow")
    @app_commands.describe(shadow_name="The name of the shadow to upgrade", levels="Number of levels to upgrade (default: 1)")
    async def shadow_upgrade(self, ctx, shadow_name: str, levels: int = 1):
        """Upgrade a shadow using Traces of Shadow."""
        player = await Player.get(ctx.author.id)

        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Get shadow
        shadow_id = extractId(shadow_name)
        shadow = await Shadow.get(shadow_id)

        if not shadow:
            embed = discord.Embed(
                title="❌ Shadow Not Found",
                description=f"Shadow '{shadow_name}' doesn't exist.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Check if player owns the shadow
        shadows = player.get_shadows()
        if shadow_id not in shadows:
            embed = discord.Embed(
                title="❌ Shadow Not Owned",
                description=f"You don't own **{shadow.name}**. Use `sl arise {shadow.name}` to unlock it first.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Get shadow data
        shadow_data = shadows[shadow_id]
        current_level = shadow_data.get('level', 1)
        current_xp = shadow_data.get('xp', 0)

        # Check level cap
        max_level = 100
        if current_level >= max_level:
            embed = discord.Embed(
                title="❌ Max Level Reached",
                description=f"**{shadow.name}** is already at maximum level ({max_level})!",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Limit levels to not exceed max
        levels = min(levels, max_level - current_level)

        if levels <= 0:
            embed = discord.Embed(
                title="❌ Invalid Level Count",
                description="Please specify a positive number of levels to upgrade.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Calculate cost (100 TOS per level * current level)
        total_cost = 0
        for i in range(levels):
            level_cost = (current_level + i) * 100
            total_cost += level_cost

        # Check if player has enough TOS
        if player.tos < total_cost:
            embed = discord.Embed(
                title="❌ Insufficient Resources",
                description=f"You need **{total_cost:,}** {getEmoji('trace')} Traces of Shadow to upgrade **{shadow.name}** by {levels} level{'s' if levels > 1 else ''}.\n\nYou have: **{player.tos:,}** TOS",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Perform upgrade
        player.tos -= total_cost

        # Add XP to level up the shadow
        xp_to_add = 0
        for i in range(levels):
            level_xp_needed = (current_level + i) * 1000
            xp_to_add += level_xp_needed

        player.add_shadow(shadow_id, xp=xp_to_add)
        await player.save()

        # Get new level after upgrade
        updated_shadows = player.get_shadows()
        new_shadow_data = updated_shadows[shadow_id]
        new_level = new_shadow_data.get('level', 1)
        new_xp = new_shadow_data.get('xp', 0)

        # Create success embed
        embed = discord.Embed(
            title="🆙 Shadow Upgrade Successful!",
            description=f"**{shadow.name}** has been upgraded!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Upgrade Results",
            value=f"**Level**: {current_level} → **{new_level}**\n**Levels Gained**: +{levels}",
            inline=True
        )

        embed.add_field(
            name="💰 Cost",
            value=f"{getEmoji('trace')} **{total_cost:,}** TOS\n**Remaining**: {player.tos:,} TOS",
            inline=True
        )

        embed.add_field(
            name="⚔️ Shadow Stats",
            value=f"**Attack Boost**: +{shadow.attack}%\n**Defense Boost**: +{shadow.defense}%",
            inline=True
        )

        # Calculate next level requirements
        if new_level < max_level:
            next_level_xp = new_level * 1000
            embed.add_field(
                name="📈 Next Level",
                value=f"**XP**: {new_xp:,} / {next_level_xp:,}\n**Cost**: {new_level * 100:,} TOS",
                inline=False
            )
        else:
            embed.add_field(
                name="🏆 Maximum Level",
                value="This shadow has reached maximum power!",
                inline=False
            )

        embed.set_thumbnail(url=shadow.image)
        embed.set_footer(text="Your shadow grows stronger! Use 'sl shadows' to see your army.")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="arise", description="Arise and summon a shadow")
    async def arise(self, ctx, name: str, tries: int = None):
        player = await Player.get(ctx.author.id)
        trace = getEmoji("trace")

        if player is None:
            down = getEmoji("down")
            await ctx.send(f"You haven't started the bot yet\n{down}Use `sl start` to get Re-Awakening")
            return

        # Check story lock for shadow extraction
        from structure.story_campaign import check_story_lock
        can_access, lock_message = await check_story_lock(ctx.author.id, "cartenon_002", "Shadow Extraction")
        if not can_access:
            embed = create_embed("🔒 Feature Locked", lock_message, WARNING_COLOR, ctx.author)
            await ctx.reply(embed=embed, mention_author=False)
            return

        shadow = await Shadow.get(extractId(name))
        if isinstance(player.shadows, str):  # Fix the issue if shadows is a string
            player.shadows = json.loads(player.shadows)

        # Check if shadow is already unlocked
        if shadow and shadow.id in player.shadows:
            embed = discord.Embed(
                title="🔮 Shadow Already Unlocked!",
                description=f"**{shadow.name}** is already in your shadow army!\n\nUse `sl shadows` to view your collection.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=shadow.image)
            await ctx.send(embed=embed)
            return

        if not shadow:
            embed = discord.Embed(
                title="❌ Shadow Not Found",
                description=f"No shadow with the name `{name}` was found.\n\nUse `sl shadows` to see available shadows.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Check your spelling and try again!")
            await ctx.send(embed=embed)
            return

        # Check if player has defeated the required world boss
        if shadow.required_boss and not player.has_defeated_boss(shadow.required_boss):
            boss_names = {
                "iron_golem": "Iron Golem",
                "shadow_knight": "Shadow Knight",
                "tank_demon": "Tank Demon",
                "orc_warlord": "Orc Warlord",
                "greed_demon": "Greed Demon",
                "igris_boss": "Igris (World Boss)"
            }
            required_boss_name = boss_names.get(shadow.required_boss, shadow.required_boss)

            embed = discord.Embed(
                title="🔒 Shadow Locked",
                description=f"**{shadow.name}** cannot be summoned yet!\n\nYou must first defeat the **{required_boss_name}** world boss to unlock this shadow.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="🌍 World Boss Requirement",
                value=f"Defeat **{required_boss_name}** in world boss battles to unlock **{shadow.name}**",
                inline=False
            )
            embed.add_field(
                name="💡 How to Fight World Bosses",
                value="World bosses spawn randomly in servers. Look for boss announcements and join the fight!",
                inline=False
            )
            embed.set_footer(text="World bosses provide powerful shadows when defeated!")
            await ctx.send(embed=embed)
            return

        if shadow.id not in player.shadows and tries:
            await ctx.reply("You can't use the tries argument. You haven't unlocked the shadow yet.", mention_author=False)
            return

        tries = tries or 1
        total_cost = 2000 * tries

        if player.tos < total_cost:
            embed = discord.Embed(
                title="❌ Insufficient Resources",
                description=f"You don't have enough {trace} **Traces of Shadow**.",
                color=discord.Color.red()
            )
            embed.add_field(name="Required", value=f"`{total_cost:,}` {trace}", inline=True)
            embed.add_field(name="Available", value=f"`{player.tos:,}` {trace}", inline=True)
            embed.add_field(name="Missing", value=f"`{total_cost - player.tos:,}` {trace}", inline=True)
            await ctx.send(embed=embed)
            return

        player.tos -= total_cost
        await player.save()

        success_count = 0
        fail_count = 0
        total_xp_gained = 0
        total_levels_gained = 0
        fragments_obtained = 0

        if isinstance(player.shadows, str):  # Fix the issue if shadows is a string
            player.shadows = json.loads(player.shadows)

        for _ in range(tries):
            # Determine the outcome based on probabilities
            outcome = random.random()  # Random number between 0 and 1

            if outcome < 0.25:  # 25% chance to unlock the shadow
                if shadow.id not in player.shadows:
                    player.add_shadow(shadow.id)
                    success_count += 1
                else:
                    # If the shadow is already unlocked, treat it as a fragment
                    fragments_obtained += 1
            elif outcome < 0.55:  # 30% chance to get a fragment (25% + 30% = 55%)
                fragments_obtained += 1
            else:  # 45% chance to fail
                fail_count += 1

        # Convert fragments into XP
        if fragments_obtained > 0:
            if shadow.id in player.shadows:
                old_level = player.shadows[shadow.id]["level"]
                xp_gained = fragments_obtained * 500  # 500 XP per fragment
                player.add_shadow(shadow.id, xp=xp_gained)
                new_level = player.shadows[shadow.id]["level"]

                levels_gained = new_level - old_level
                total_xp_gained += xp_gained
                total_levels_gained += levels_gained

        await player.save()

        # Create enhanced result embed
        if success_count > 0 or fragments_obtained > 0:
            embed = discord.Embed(
                title="🌟 SHADOW SUMMONING SUCCESS! 🌟",
                color=discord.Color.dark_green()
            )

            if success_count > 0:
                embed.description = f"🎉 **You have successfully summoned {shadow.name}!**\n\n"
                embed.set_image(url=shadow.image)
            else:
                embed.description = ""

            if fragments_obtained > 0:
                embed.description += f"💎 **Fragments Obtained**: `x{fragments_obtained}`\n📈 **XP Gained**: `+{total_xp_gained:,}`"

            # Results summary
            embed.add_field(
                name="📊 Summoning Results",
                value=(
                    f"✅ **Successful**: `{success_count}`\n"
                    f"💎 **Fragments**: `{fragments_obtained}`\n"
                    f"❌ **Failed**: `{fail_count}`"
                ),
                inline=True
            )

            embed.add_field(
                name="💰 Resources Used",
                value=f"{trace} `{total_cost:,}` Traces of Shadow",
                inline=True
            )

            if total_levels_gained > 0:
                embed.add_field(
                    name="🆙 Level Progress",
                    value=f"**+{total_levels_gained}** Level{'s' if total_levels_gained > 1 else ''}",
                    inline=True
                )

            embed.set_footer(text="Your shadow army grows stronger! Check 'sl shadows' to see your progress.")
            embed.set_thumbnail(url=shadow.image)

        else:
            embed = discord.Embed(
                title="💀 SHADOW SUMMONING FAILED",
                description=f"All `{tries}` attempt{'s' if tries > 1 else ''} to summon **{shadow.name}** have failed.",
                color=discord.Color.dark_red()
            )
            embed.add_field(
                name="💰 Resources Used",
                value=f"{trace} `{total_cost:,}` Traces of Shadow",
                inline=True
            )
            embed.add_field(
                name="💡 Tip",
                value="Try again or consider upgrading your summoning abilities!",
                inline=False
            )
            embed.set_footer(text="Better luck next time! Patreons have higher success rates.")
            embed.set_thumbnail(url=shadow.image)

        await ctx.send(embed=embed)

class AriseShadowView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.authorized_user_id = user_id  # Fix missing attribute

    async def show_arise_interface(self, interaction: discord.Interaction):
        """Show the arise shadow interface"""
        from structure.player import Player
        from structure.shadow import Shadow

        player = await Player.get(self.user_id)
        if not player:
            await interaction.response.send_message("❌ Player not found!", ephemeral=True)
            return

        # Get all shadows and check which ones are available
        all_shadows = await Shadow.get_all()
        available_shadows = []
        locked_shadows = []

        boss_names = {
            "igris": "Igris (Shadow World Boss)",
            "iron": "Iron (Shadow World Boss)",
            "tank": "Tank (Shadow World Boss)",
            "tusk": "Tusk (Shadow World Boss)",
            "kaisel": "Kaisel (Shadow World Boss)",
            "greed": "Greed (Shadow World Boss)",
            "beru": "Beru (Shadow World Boss)",
            "bellion": "Bellion (Shadow World Boss)",
            "antares": "Antares (Shadow World Boss)",
            "thomas_andre": "Thomas Andre (Shadow World Boss)"
        }

        owned_shadows = []
        current_shadows = player.get_shadows()

        for shadow in all_shadows:
            shadow_id = shadow.id
            if shadow_id in boss_names and player.has_defeated_boss(shadow_id):
                # Check if already owned
                if shadow_id not in current_shadows:
                    available_shadows.append({
                        'shadow': shadow,
                        'cost': shadow.price,
                        'success_rate': '25%'
                    })
                else:
                    # Already owned
                    shadow_data = current_shadows[shadow_id]
                    level = shadow_data.get('level', 1)
                    owned_shadows.append({
                        'shadow': shadow,
                        'level': level
                    })
            elif shadow_id in boss_names:
                locked_shadows.append({
                    'shadow': shadow,
                    'requirement': boss_names[shadow_id]
                })

        embed = discord.Embed(
            title="🔮 **ARISE SHADOW INTERFACE** 🔮",
            description="Manage your shadow army and attempt to arise new shadows.",
            color=discord.Color.purple()
        )

        if owned_shadows:
            owned_text = ""
            for item in owned_shadows[:10]:  # Show up to 10
                owned_text += f"👑 **{item['shadow'].name}** - Level {item['level']}\n"

            embed.add_field(
                name="🌟 Your Shadow Army",
                value=owned_text,
                inline=False
            )

        if available_shadows:
            available_text = ""
            for item in available_shadows[:10]:  # Show up to 10
                available_text += f"✅ **{item['shadow'].name}** - {item['cost']} TOS (25% success)\n"

            embed.add_field(
                name="🔓 Available to Arise",
                value=available_text,
                inline=False
            )

        if locked_shadows:
            locked_text = ""
            for item in locked_shadows[:10]:  # Show up to 10
                locked_text += f"🔒 **{item['shadow'].name}** - Defeat {item['requirement']}\n"

            embed.add_field(
                name="🔒 Locked Shadows",
                value=locked_text,
                inline=False
            )

        embed.add_field(
            name="💰 Your Resources",
            value=f"**Traces of Shadow**: {player.tos:,}",
            inline=True
        )

        embed.add_field(
            name="📊 Success Rates",
            value="**Shadow Unlock**: 25%\n**Fragment**: 30%\n**Nothing**: 45%",
            inline=True
        )

        embed.set_footer(text="Select a shadow below to attempt arising!")

        # Set image to the first available shadow if any
        if available_shadows:
            embed.set_image(url=available_shadows[0]['shadow'].image)
        elif locked_shadows:
            embed.set_image(url=locked_shadows[0]['shadow'].image)
        else:
            embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")

        # Create arise buttons for available shadows
        self.clear_items()
        for i, item in enumerate(available_shadows[:4]):  # Max 4 buttons per row
            button = ui.Button(
                label=f"🔮 {item['shadow'].name}",
                style=discord.ButtonStyle.primary,
                custom_id=f"arise_{item['shadow'].id}"
            )
            button.callback = self.create_arise_callback(item['shadow'])
            self.add_item(button)

        # Add back button
        back_button = ui.Button(label="🔙 Back to Shadows", style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_shadows
        self.add_item(back_button)

        await interaction.response.edit_message(embed=embed, view=self)

    def create_arise_callback(self, shadow):
        async def arise_callback(interaction: discord.Interaction):
            # CRITICAL: Check if user is authorized to use this button
            if interaction.user.id != self.authorized_user_id:
                await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
                return

            from structure.player import Player
            import random

            player = await Player.get(self.authorized_user_id)  # Use authorized user ID, not interaction user
            if not player:
                await interaction.response.send_message("❌ Player not found!", ephemeral=True)
                return

            # Check if player has enough Traces of Shadow
            if player.tos < shadow.price:
                await interaction.response.send_message(
                    f"❌ **Insufficient Traces of Shadow!**\n\n"
                    f"**Required**: {shadow.price:,} TOS\n"
                    f"**You have**: {player.tos:,} TOS\n"
                    f"**Need**: {shadow.price - player.tos:,} more TOS",
                    ephemeral=True
                )
                return

            # Check if shadow is already owned
            current_shadows = player.get_shadows()
            if shadow.id in current_shadows:
                await interaction.response.send_message(
                    f"❌ **{shadow.name}** is already in your shadow army!",
                    ephemeral=True
                )
                return

            # Check if boss was defeated
            if not player.has_defeated_boss(shadow.id):
                await interaction.response.send_message(
                    f"❌ **You haven't defeated {shadow.name} yet!**\n\n"
                    f"Defeat the shadow world boss first to unlock this shadow.",
                    ephemeral=True
                )
                return

            # Deduct cost
            player.tos -= shadow.price

            # 25% success rate for shadow unlock
            success_roll = random.random()

            if success_roll <= 0.25:  # 25% success
                # Add shadow to army
                player.add_shadow(shadow.id, 100)  # Start with 100 XP

                success_embed = discord.Embed(
                    title="🎉 **ARISE SUCCESSFUL!** 🎉",
                    description=f"**{shadow.name}** has joined your shadow army!",
                    color=discord.Color.gold()
                )
                success_embed.set_image(url=shadow.image)
                success_embed.add_field(
                    name="Shadow Details",
                    value=f"**Name**: {shadow.name}\n**Level**: 1\n**Starting XP**: 100",
                    inline=False
                )
                success_embed.add_field(
                    name="Cost",
                    value=f"**Spent**: {shadow.price:,} TOS\n**Remaining**: {player.tos:,} TOS",
                    inline=False
                )

                await interaction.response.send_message(embed=success_embed, ephemeral=True)

            elif success_roll <= 0.55:  # 30% fragment (25% + 30% = 55%)
                # Give shadow fragment (placeholder - implement if needed)
                fragment_embed = discord.Embed(
                    title="💎 **Shadow Fragment Obtained** 💎",
                    description=f"You obtained a fragment of **{shadow.name}**!\n\nCollect more fragments to eventually summon this shadow.",
                    color=discord.Color.blue()
                )
                fragment_embed.set_image(url=shadow.image)
                fragment_embed.add_field(
                    name="Cost",
                    value=f"**Spent**: {shadow.price:,} TOS\n**Remaining**: {player.tos:,} TOS",
                    inline=False
                )

                await interaction.response.send_message(embed=fragment_embed, ephemeral=True)

            else:  # 45% nothing
                fail_embed = discord.Embed(
                    title="💨 **Arise Failed** 💨",
                    description=(
                        f"The shadow of **{shadow.name}** slipped away...\n\n"
                        f"**🎲 RNG System Explanation:**\n"
                        f"• 25% chance to unlock shadow ✅\n"
                        f"• 30% chance to get fragment 💎\n"
                        f"• 45% chance to fail ❌ (this attempt)\n\n"
                        f"**💡 This is normal!** Shadows are rare and powerful."
                    ),
                    color=discord.Color.red()
                )
                fail_embed.set_image(url=shadow.image)
                fail_embed.add_field(
                    name="💰 Cost & Remaining",
                    value=f"**Spent**: {shadow.price:,} TOS\n**Remaining**: {player.tos:,} TOS",
                    inline=False
                )
                fail_embed.add_field(
                    name="🔄 Next Steps",
                    value="• Collect more Traces of Shadow from world bosses\n• Try summoning again - each attempt is independent\n• Remember: RNG means some players get lucky, others need more tries!",
                    inline=False
                )

                await interaction.response.send_message(embed=fail_embed, ephemeral=True)

            # Save player data
            try:
                await player.save()
            except Exception as e:
                print(f"Error saving player {interaction.user.id} after arise attempt: {e}")

        return arise_callback

    async def back_to_shadows(self, interaction: discord.Interaction):
        """Go back to main shadows view"""
        # CRITICAL: Check if user is authorized to use this button
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        from structure.player import Player

        player = await Player.get(self.user_id)
        shadows = player.get_shadows()

        if not shadows:
            embed = discord.Embed(
                title="👥 Shadow Army",
                description="**Your shadow army is empty!**\n\nUse the arise interface to summon shadows.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Recreate the main shadows view
        shadows_data = {}
        for shadow_id, shadow_data in shadows.items():
            shadow = await Shadow.get(shadow_id)
            if shadow:
                shadows_data[shadow_id] = {
                    'shadow': shadow,
                    'data': shadow_data,
                    'attack': shadow.attack,
                    'defense': shadow.defense
                }

        total_pages = max(1, (len(shadows_data) + 5) // 6)  # 6 shadows per page

        # Create a mock context for ShadowPaginationView
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.response.send_message

        mock_ctx = MockContext(interaction)
        view = ShadowPaginationView(mock_ctx, shadows_data, total_pages, 1)
        embed = await view.create_embed()

        await interaction.response.edit_message(embed=embed, view=view)

class ShadowStatsView(ui.View):
    def __init__(self, user_id, shadows_data):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.shadows_data = shadows_data

    async def show_stats(self, interaction: discord.Interaction):
        """Show detailed shadow statistics"""
        if not self.shadows_data:
            embed = discord.Embed(
                title="📊 Shadow Statistics",
                description="**No shadows to analyze!**\n\nUse the arise interface to summon shadows first.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Calculate statistics
        total_shadows = len(self.shadows_data)
        total_levels = sum(data['data'].get('level', 1) for data in self.shadows_data.values())
        avg_level = total_levels / total_shadows if total_shadows > 0 else 0
        total_attack = sum(data['attack'] for data in self.shadows_data.values())
        total_defense = sum(data['defense'] for data in self.shadows_data.values())

        # Categorize by rarity using shadow requirements mapping
        shadow_requirements = {
            "igris": {"name": "Igris", "type": "Knight", "rarity": "Common"},
            "iron": {"name": "Iron", "type": "Warrior", "rarity": "Common"},
            "tank": {"name": "Tank", "type": "Guardian", "rarity": "Common"},
            "tusk": {"name": "Tusk", "type": "Beast", "rarity": "Rare"},
            "kaisel": {"name": "Kaisel", "type": "Dragon", "rarity": "Rare"},
            "greed": {"name": "Greed", "type": "Assassin", "rarity": "Rare"},
            "beru": {"name": "Beru", "type": "Ant King", "rarity": "Epic"},
            "bellion": {"name": "Bellion", "type": "Grand Marshal", "rarity": "Epic"},
            "antares": {"name": "Antares", "type": "Dragon Emperor", "rarity": "Legendary"},
            "thomas_andre": {"name": "Thomas Andre", "type": "Nation Level Hunter", "rarity": "Legendary"}
        }

        rarity_count = {'Common': 0, 'Rare': 0, 'Epic': 0, 'Legendary': 0}
        for shadow_id, data in self.shadows_data.items():
            shadow_info = shadow_requirements.get(shadow_id)
            if shadow_info:
                rarity = shadow_info['rarity']
                rarity_count[rarity] += 1

        embed = discord.Embed(
            title="📊 **SHADOW ARMY STATISTICS** 📊",
            description="Detailed analysis of your shadow collection",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🔢 Army Overview",
            value=(
                f"**Total Shadows**: {total_shadows}\n"
                f"**Average Level**: {avg_level:.1f}\n"
                f"**Combined Attack**: {total_attack:,}\n"
                f"**Combined Defense**: {total_defense:,}"
            ),
            inline=True
        )

        embed.add_field(
            name="✨ Rarity Distribution",
            value=(
                f"🟡 **Legendary**: {rarity_count['Legendary']}\n"
                f"🟣 **Epic**: {rarity_count['Epic']}\n"
                f"🔵 **Rare**: {rarity_count['Rare']}\n"
                f"⚪ **Common**: {rarity_count['Common']}"
            ),
            inline=True
        )

        # Top 5 strongest shadows
        strongest_shadows = sorted(
            self.shadows_data.items(),
            key=lambda x: x[1]['attack'] + x[1]['defense'],
            reverse=True
        )[:5]

        strongest_text = ""
        for i, (shadow_id, data) in enumerate(strongest_shadows, 1):
            shadow = data['shadow']
            level = data['data'].get('level', 1)
            power = data['attack'] + data['defense']
            strongest_text += f"{i}. **{shadow.name}** (Lv.{level}) - {power:,} Power\n"

        embed.add_field(
            name="💪 Strongest Shadows",
            value=strongest_text or "No shadows available",
            inline=False
        )

        embed.set_footer(text="Your shadow army grows stronger with each battle!")

        # Set image to the strongest shadow if available
        if strongest_shadows:
            strongest_shadow_data = strongest_shadows[0][1]
            embed.set_image(url=strongest_shadow_data['shadow'].image)
        else:
            embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")

        # Add back button
        back_button = ui.Button(label="🔙 Back to Shadows", style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_shadows
        self.add_item(back_button)

        await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_shadows(self, interaction: discord.Interaction):
        """Go back to main shadows view"""
        # CRITICAL: Check if user is authorized to use this button
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        total_pages = max(1, (len(self.shadows_data) + 5) // 6)

        # Create a mock context for ShadowPaginationView
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.response.send_message

        mock_ctx = MockContext(interaction)
        view = ShadowPaginationView(mock_ctx, self.shadows_data, total_pages, 1)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class AvailableShadowsView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    async def show_available(self, interaction: discord.Interaction):
        """Show all shadows available to unlock"""
        from structure.player import Player
        from structure.shadow import Shadow

        player = await Player.get(self.user_id)
        if not player:
            await interaction.response.send_message("❌ Player not found!", ephemeral=True)
            return

        # Shadow world boss requirements
        shadow_requirements = {
            "igris": {"name": "Igris", "type": "Knight", "rarity": "Common", "boss": "Igris (Shadow World Boss)"},
            "iron": {"name": "Iron", "type": "Warrior", "rarity": "Common", "boss": "Iron (Shadow World Boss)"},
            "tank": {"name": "Tank", "type": "Guardian", "rarity": "Common", "boss": "Tank (Shadow World Boss)"},
            "tusk": {"name": "Tusk", "type": "Beast", "rarity": "Rare", "boss": "Tusk (Shadow World Boss)"},
            "kaisel": {"name": "Kaisel", "type": "Dragon", "rarity": "Rare", "boss": "Kaisel (Shadow World Boss)"},
            "greed": {"name": "Greed", "type": "Assassin", "rarity": "Rare", "boss": "Greed (Shadow World Boss)"},
            "beru": {"name": "Beru", "type": "Ant King", "rarity": "Epic", "boss": "Beru (Shadow World Boss)"},
            "bellion": {"name": "Bellion", "type": "Grand Marshal", "rarity": "Epic", "boss": "Bellion (Shadow World Boss)"},
            "antares": {"name": "Antares", "type": "Dragon Emperor", "rarity": "Legendary", "boss": "Antares (Shadow World Boss)"},
            "thomas_andre": {"name": "Thomas Andre", "type": "Nation Level Hunter", "rarity": "Legendary", "boss": "Thomas Andre (Shadow World Boss)"}
        }

        # Get player's owned shadows (shadow IDs)
        owned_shadow_ids = list(player.shadows.keys()) if player.shadows else []

        embed = discord.Embed(
            title="🎯 **AVAILABLE SHADOWS** 🎯",
            description="Hunt these shadow world bosses to unlock new shadows for your army!",
            color=discord.Color.green()
        )

        # Categorize shadows
        categories = {"Common": [], "Rare": [], "Epic": [], "Legendary": []}

        for shadow_id, info in shadow_requirements.items():
            status = ""
            if shadow_id in owned_shadow_ids:
                status = "✅ **OWNED**"
            elif player.has_defeated_boss(shadow_id):
                status = "🔮 **READY TO ARISE**"
            else:
                status = "🔒 **LOCKED**"

            categories[info["rarity"]].append(f"{status} **{info['name']}** ({info['type']})")

        # Add fields for each rarity
        rarity_emojis = {"Common": "⚪", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟡"}

        for rarity, shadows in categories.items():
            if shadows:
                embed.add_field(
                    name=f"{rarity_emojis[rarity]} {rarity} Shadows",
                    value="\n".join(shadows),
                    inline=False
                )

        embed.add_field(
            name="📋 Legend",
            value=(
                "✅ **OWNED** - Already in your army\n"
                "🔮 **READY TO ARISE** - Use `sl arise <name>`\n"
                "🔒 **LOCKED** - Defeat the shadow world boss first"
            ),
            inline=False
        )

        embed.set_footer(text="Join shadow world boss battles to unlock new shadows!")

        # Set image to a featured shadow (first legendary, then epic, then rare, then common)
        featured_shadow_image = None
        for rarity in ["Legendary", "Epic", "Rare", "Common"]:
            for shadow_id, info in shadow_requirements.items():
                if info["rarity"] == rarity:
                    # Get the shadow image from database
                    shadow = await Shadow.get(shadow_id)
                    if shadow and shadow.image:
                        featured_shadow_image = shadow.image
                        break
            if featured_shadow_image:
                break

        if featured_shadow_image:
            embed.set_image(url=featured_shadow_image)
        else:
            embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")

        # Add back button
        back_button = ui.Button(label="🔙 Back to Shadows", style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_shadows
        self.add_item(back_button)

        # Safe interaction response
        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await interaction.followup.edit_message(
                    interaction.message.id,
                    embed=embed,
                    view=self
                )
        except discord.errors.NotFound:
            # Interaction expired
            self.stop()
        except Exception as e:
            print(f"Error showing available shadows: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred while loading shadows.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ An error occurred while loading shadows.", ephemeral=True)
            except:
                pass

    async def back_to_shadows(self, interaction: discord.Interaction):
        """Go back to main shadows view"""
        # CRITICAL: Check if user is authorized to use this button
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        from structure.player import Player

        player = await Player.get(self.user_id)
        shadows = player.get_shadows()

        if not shadows:
            embed = discord.Embed(
                title="👥 Shadow Army",
                description="**Your shadow army is empty!**\n\nUse the arise interface to summon shadows.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Recreate shadows data
        shadows_data = {}
        for shadow_id, shadow_data in shadows.items():
            shadow = await Shadow.get(shadow_id)
            if shadow:
                shadows_data[shadow_id] = {
                    'shadow': shadow,
                    'data': shadow_data,
                    'attack': shadow.attack,
                    'defense': shadow.defense
                }

        total_pages = max(1, (len(shadows_data) + 5) // 6)

        # Create a mock context for ShadowPaginationView
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.response.send_message

        mock_ctx = MockContext(interaction)
        view = ShadowPaginationView(mock_ctx, shadows_data, total_pages, 1)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class ShadowArmyView(ui.View):
    def __init__(self, user_id, shadows_data):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.shadows_data = shadows_data

    async def show_army(self, interaction: discord.Interaction):
        """Show shadow army formation and management"""
        if not self.shadows_data:
            embed = discord.Embed(
                title="⚔️ Shadow Army Formation",
                description="**Your shadow army is empty!**\n\nUse the arise interface to summon shadows first.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        embed = discord.Embed(
            title="⚔️ **SHADOW ARMY FORMATION** ⚔️",
            description="Manage your shadow army and battle formations",
            color=discord.Color.red()
        )

        # Sort shadows by power (attack + defense)
        sorted_shadows = sorted(
            self.shadows_data.items(),
            key=lambda x: x[1]['attack'] + x[1]['defense'],
            reverse=True
        )

        # Front line (top 3 strongest)
        front_line = sorted_shadows[:3]
        front_text = ""
        for i, (shadow_id, data) in enumerate(front_line, 1):
            shadow = data['shadow']
            level = data['data'].get('level', 1)
            power = data['attack'] + data['defense']
            front_text += f"{i}. **{shadow.name}** (Lv.{level}) - {power:,} Power\n"

        embed.add_field(
            name="🛡️ Front Line",
            value=front_text or "No shadows assigned",
            inline=True
        )

        # Support line (next 3)
        support_line = sorted_shadows[3:6]
        support_text = ""
        for i, (shadow_id, data) in enumerate(support_line, 1):
            shadow = data['shadow']
            level = data['data'].get('level', 1)
            power = data['attack'] + data['defense']
            support_text += f"{i}. **{shadow.name}** (Lv.{level}) - {power:,} Power\n"

        embed.add_field(
            name="⚔️ Support Line",
            value=support_text or "No shadows assigned",
            inline=True
        )

        # Reserve (remaining shadows)
        reserve = sorted_shadows[6:]
        if reserve:
            reserve_text = ""
            for i, (shadow_id, data) in enumerate(reserve[:5], 1):  # Show up to 5 reserves
                shadow = data['shadow']
                level = data['data'].get('level', 1)
                reserve_text += f"{i}. **{shadow.name}** (Lv.{level})\n"

            if len(reserve) > 5:
                reserve_text += f"... and {len(reserve) - 5} more"

            embed.add_field(
                name="🏃 Reserve Forces",
                value=reserve_text,
                inline=False
            )

        # Army stats
        total_power = sum(data['attack'] + data['defense'] for data in self.shadows_data.values())
        avg_level = sum(data['data'].get('level', 1) for data in self.shadows_data.values()) / len(self.shadows_data)

        embed.add_field(
            name="📊 Army Statistics",
            value=(
                f"**Total Shadows**: {len(self.shadows_data)}\n"
                f"**Combined Power**: {total_power:,}\n"
                f"**Average Level**: {avg_level:.1f}"
            ),
            inline=True
        )

        embed.set_footer(text="Your shadow army stands ready for battle!")

        # Set image to the strongest shadow (front line leader)
        if sorted_shadows:
            leader_shadow_data = sorted_shadows[0][1]
            embed.set_image(url=leader_shadow_data['shadow'].image)
        else:
            embed.set_thumbnail(url="https://files.catbox.moe/donb98.webp")

        # Add back button
        back_button = ui.Button(label="🔙 Back to Shadows", style=discord.ButtonStyle.secondary)
        back_button.callback = self.back_to_shadows
        self.add_item(back_button)

        await interaction.response.edit_message(embed=embed, view=self)

    async def back_to_shadows(self, interaction: discord.Interaction):
        """Go back to main shadows view"""
        # CRITICAL: Check if user is authorized to use this button
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        total_pages = max(1, (len(self.shadows_data) + 5) // 6)

        # Create a mock context for ShadowPaginationView
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.response.send_message

        mock_ctx = MockContext(interaction)
        view = ShadowPaginationView(mock_ctx, self.shadows_data, total_pages, 1)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @commands.hybrid_command(name="shadow_equip", aliases=['seq'], description="Interactive shadow equipment management")
    async def shadow_equip(self, ctx):
        """Interactive shadow equipment management interface."""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        view = ShadowEquipView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)


class ShadowEquipView(ui.View):
    """Interactive view for shadow equipment management."""

    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.current_mode = "overview"  # overview, equip, upgrade
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command author can interact with this shadow equipment view"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True

    async def create_embed(self):
        """Create the main shadow equipment embed."""
        if self.current_mode == "overview":
            return await self.create_overview_embed()
        elif self.current_mode == "equip":
            return await self.create_equip_embed()
        elif self.current_mode == "upgrade":
            return await self.create_upgrade_embed()

    async def create_overview_embed(self):
        """Create overview of shadow equipment."""
        embed = discord.Embed(
            title="👑 **SHADOW ARMY MANAGEMENT** 👑",
            description="Manage your shadow army and equipment",
            color=discord.Color.dark_purple()
        )

        # Current equipped shadow
        equipped_shadow = self.player.equipped.get("Shadow")
        if equipped_shadow:
            shadow = await Shadow.get(equipped_shadow)
            shadows = self.player.get_shadows()
            shadow_data = shadows.get(equipped_shadow, {})
            level = shadow_data.get('level', 1)

            if shadow:
                embed.add_field(
                    name="⚔️ Equipped Shadow",
                    value=f"👑 **{shadow.name}** (Level {level})\n**Attack Boost**: +{shadow.attack}%\n**Defense Boost**: +{shadow.defense}%",
                    inline=False
                )
        else:
            embed.add_field(
                name="⚔️ Equipped Shadow",
                value="*No shadow equipped*",
                inline=False
            )

        # Show owned shadows
        shadows = self.player.get_shadows()
        if shadows:
            shadow_list = []
            for shadow_id, shadow_data in list(shadows.items())[:8]:  # Show first 8
                shadow = await Shadow.get(shadow_id)
                if shadow:
                    level = shadow_data.get('level', 1)
                    equipped_indicator = " ⚡" if shadow_id == equipped_shadow else ""
                    shadow_list.append(f"👑 **{shadow.name}** (Lv.{level}){equipped_indicator}")

            embed.add_field(
                name="🌟 Your Shadow Army",
                value="\n".join(shadow_list),
                inline=False
            )
        else:
            embed.add_field(
                name="🌟 Your Shadow Army",
                value="*No shadows unlocked*\nUse `sl arise` to unlock shadows!",
                inline=False
            )

        embed.set_footer(text="Use the buttons below to manage your shadows")
        return embed

    async def create_equip_embed(self):
        """Create shadow equip interface."""
        embed = discord.Embed(
            title="⚔️ **EQUIP SHADOW** ⚔️",
            description="Select a shadow to equip for battle",
            color=discord.Color.green()
        )

        shadows = self.player.get_shadows()
        if shadows:
            shadow_list = []
            for shadow_id, shadow_data in shadows.items():
                shadow = await Shadow.get(shadow_id)
                if shadow:
                    level = shadow_data.get('level', 1)
                    shadow_list.append(f"👑 **{shadow.name}** (Lv.{level})\n   ⚔️ +{shadow.attack}% ATK | 🛡️ +{shadow.defense}% DEF")

            embed.add_field(
                name="🌟 Available Shadows",
                value="\n\n".join(shadow_list[:10]),
                inline=False
            )
        else:
            embed.add_field(
                name="🌟 Available Shadows",
                value="*No shadows available*",
                inline=False
            )

        embed.set_footer(text="Use the dropdown below to select a shadow to equip")
        return embed

    async def create_upgrade_embed(self):
        """Create shadow upgrade interface."""
        embed = discord.Embed(
            title="🆙 **UPGRADE SHADOWS** 🆙",
            description="Upgrade your shadows using Traces of Shadow",
            color=discord.Color.gold()
        )

        shadows = self.player.get_shadows()
        if shadows:
            shadow_list = []
            for shadow_id, shadow_data in shadows.items():
                shadow = await Shadow.get(shadow_id)
                if shadow:
                    level = shadow_data.get('level', 1)
                    upgrade_cost = level * 100
                    shadow_list.append(f"👑 **{shadow.name}** (Lv.{level})\n   💰 Next upgrade: {upgrade_cost:,} TOS")

            embed.add_field(
                name="🌟 Your Shadows",
                value="\n\n".join(shadow_list[:8]),
                inline=False
            )
        else:
            embed.add_field(
                name="🌟 Your Shadows",
                value="*No shadows available*",
                inline=False
            )

        embed.add_field(
            name="💰 Your Resources",
            value=f"{getEmoji('trace')} **{self.player.tos:,}** Traces of Shadow",
            inline=False
        )

        embed.set_footer(text="Use the dropdown below to select a shadow to upgrade")
        return embed

    def update_buttons(self):
        """Update button states based on current mode."""
        self.clear_items()

        if self.current_mode == "overview":
            self.add_item(ShadowEquipButton())
            self.add_item(ShadowUpgradeButton())
        elif self.current_mode == "equip":
            self.add_item(ShadowEquipSelect(self))
            self.add_item(ShadowBackButton())
        elif self.current_mode == "upgrade":
            self.add_item(ShadowUpgradeSelect(self))
            self.add_item(ShadowBackButton())

    async def update_view(self, interaction):
        """Update the view and embed."""
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class ShadowEquipButton(ui.Button):
    """Button to switch to equip mode."""

    def __init__(self):
        super().__init__(label="⚔️ Equip Shadow", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        self.view.current_mode = "equip"
        await self.view.update_view(interaction)


class ShadowUpgradeButton(ui.Button):
    """Button to switch to upgrade mode."""

    def __init__(self):
        super().__init__(label="🆙 Upgrade Shadow", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        self.view.current_mode = "upgrade"
        await self.view.update_view(interaction)


class ShadowBackButton(ui.Button):
    """Button to go back to overview."""

    def __init__(self):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.gray)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        self.view.current_mode = "overview"
        await self.view.update_view(interaction)


class ShadowEquipSelect(ui.Select):
    """Select dropdown for equipping shadows."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(placeholder="Select a shadow to equip...", min_values=1, max_values=1)
        self.populate_options()

    async def populate_options(self):
        """Populate shadow options."""
        shadows = self.parent_view.player.get_shadows()
        options = []

        # Add unequip option
        options.append(discord.SelectOption(
            label="Unequip Current Shadow",
            value="unequip",
            description="Remove currently equipped shadow",
            emoji="🔓"
        ))

        for shadow_id, shadow_data in shadows.items():
            if len(options) >= 25:
                break
            shadow = await Shadow.get(shadow_id)
            if shadow:
                level = shadow_data.get('level', 1)
                options.append(discord.SelectOption(
                    label=f"{shadow.name} (Lv.{level})",
                    value=shadow_id,
                    description=f"+{shadow.attack}% ATK, +{shadow.defense}% DEF",
                    emoji="👑"
                ))

        if len(options) == 1:  # Only unequip option
            options.append(discord.SelectOption(
                label="No shadows available",
                value="none",
                description="Unlock shadows first"
            ))

        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        if self.values[0] == "none":
            await interaction.response.send_message("❌ No shadows available to equip!", ephemeral=True)
            return

        player = self.parent_view.player

        if self.values[0] == "unequip":
            player.equipped["Shadow"] = None
            await player.save()

            embed = discord.Embed(
                title="✅ **SHADOW UNEQUIPPED** ✅",
                description="Your shadow has been unequipped!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            shadow_id = self.values[0]
            shadow = await Shadow.get(shadow_id)

            if shadow:
                player.equipped["Shadow"] = shadow_id
                await player.save()

                embed = discord.Embed(
                    title="✅ **SHADOW EQUIPPED** ✅",
                    description=f"**{shadow.name}** has been equipped!\n\n**Bonuses:**\n⚔️ +{shadow.attack}% Attack\n🛡️ +{shadow.defense}% Defense",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        # Update the main view
        self.parent_view.current_mode = "overview"
        await self.parent_view.update_view(interaction)


class ShadowUpgradeSelect(ui.Select):
    """Select dropdown for upgrading shadows."""

    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(placeholder="Select a shadow to upgrade...", min_values=1, max_values=1)
        self.populate_options()

    async def populate_options(self):
        """Populate upgrade options."""
        shadows = self.parent_view.player.get_shadows()
        options = []

        for shadow_id, shadow_data in shadows.items():
            if len(options) >= 25:
                break
            shadow = await Shadow.get(shadow_id)
            if shadow:
                level = shadow_data.get('level', 1)
                upgrade_cost = level * 100
                options.append(discord.SelectOption(
                    label=f"{shadow.name} (Lv.{level})",
                    value=shadow_id,
                    description=f"Upgrade cost: {upgrade_cost:,} TOS",
                    emoji="👑"
                ))

        if not options:
            options.append(discord.SelectOption(
                label="No shadows available",
                value="none",
                description="Unlock shadows first"
            ))

        self.options = options

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this!", ephemeral=True)
            return

        if self.values[0] == "none":
            await interaction.response.send_message("❌ No shadows available to upgrade!", ephemeral=True)
            return

        shadow_id = self.values[0]
        shadow = await Shadow.get(shadow_id)
        player = self.parent_view.player

        if not shadow:
            await interaction.response.send_message("❌ Shadow not found!", ephemeral=True)
            return

        shadows = player.get_shadows()
        shadow_data = shadows.get(shadow_id, {})
        current_level = shadow_data.get('level', 1)
        upgrade_cost = current_level * 100

        if player.tos < upgrade_cost:
            embed = discord.Embed(
                title="❌ Insufficient Resources",
                description=f"You need **{upgrade_cost:,}** {getEmoji('trace')} TOS to upgrade **{shadow.name}**.\n\nYou have: **{player.tos:,}** TOS",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Perform upgrade
        player.tos -= upgrade_cost
        xp_to_add = current_level * 1000
        player.add_shadow(shadow_id, xp=xp_to_add)
        await player.save()

        # Get new level
        updated_shadows = player.get_shadows()
        new_shadow_data = updated_shadows[shadow_id]
        new_level = new_shadow_data.get('level', 1)

        embed = discord.Embed(
            title="🆙 **SHADOW UPGRADED** 🆙",
            description=f"**{shadow.name}** has been upgraded!\n\n**Level**: {current_level} → **{new_level}**\n**Cost**: {upgrade_cost:,} TOS",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Update the main view
        self.parent_view.current_mode = "overview"
        await self.parent_view.update_view(interaction)


async def setup(bot):
    await bot.add_cog(ShadowCommands(bot))


