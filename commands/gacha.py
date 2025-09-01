import random
import discord
from discord.ext import commands
from discord import app_commands, ui
from utilis.utilis import extractId
from structure.heroes import HeroManager
from structure.emoji import getClassEmoji, getEmoji, getRarityEmoji
from structure.player import Player
from structure.items import ItemManager
from discord.ext.commands import cooldown, BucketType
import logging
from typing import List, Optional

BASE_DROP_RATES = {
    "UR": 0.1,  # 0.1% chance - extremely rare
    "SSR": 4.9,    # Increased from 0.9% to 4.9%
    "Super Rare": 95  # Increased from 39% to 95% (Rare removed)
}

class LockedItemsView(ui.View):
    """View for managing locked items from pulls"""

    def __init__(self, ctx, player, locked_items):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.locked_items = locked_items
        self.current_page = 0
        self.items_per_page = 5

    async def create_embed(self):
        """Create embed showing locked items"""
        embed = discord.Embed(
            title="🔒 Your Locked Items",
            description="Items you've locked from pulls. Click unlock to remove them from this list.",
            color=discord.Color.gold()
        )

        # Convert locked_items dict to list for pagination
        items_list = list(self.locked_items.items())
        total_pages = (len(items_list) + self.items_per_page - 1) // self.items_per_page

        if not items_list:
            embed.add_field(
                name="No Locked Items",
                value="You haven't locked any items yet!",
                inline=False
            )
            return embed

        # Get items for current page
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = items_list[start_idx:end_idx]

        for i, (item_key, item_data) in enumerate(page_items):
            item_type = item_data.get('type', 'Unknown')
            item_name = item_data.get('name', 'Unknown Item')
            rarity = item_data.get('rarity', 'Rare')
            locked_date = item_data.get('locked_date', 'Unknown')

            embed.add_field(
                name=f"{getRarityEmoji(rarity)} {item_name}",
                value=f"**Type**: {item_type}\n**Locked**: {locked_date}",
                inline=True
            )

        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages} • {len(items_list)} total locked items")
        return embed

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        items_list = list(self.locked_items.items())
        total_pages = (len(items_list) + self.items_per_page - 1) // self.items_per_page

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @ui.button(label="🔓 Unlock All", style=discord.ButtonStyle.danger)
    async def unlock_all(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
            return

        # Clear all locked items
        self.player.locked_items = {}
        await self.player.save()

        embed = discord.Embed(
            title="🔓 All Items Unlocked",
            description="All your locked items have been unlocked!",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

class PullResultView(ui.View):
    """Enhanced pull result view with HoloCards-style UI."""

    def __init__(self, ctx, player, results, current_index=0):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.results = results
        self.current_index = current_index
        self.total_results = len(results)

        # Update button states
        self._update_buttons()

    def _update_buttons(self):
        """Update button states based on current index."""
        # Clear existing items
        self.clear_items()

        # Navigation buttons
        if self.total_results > 1:
            # Previous button - use safer emoji
            prev_button = ui.Button(
                label="◀ Prev",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_index == 0
            )
            prev_button.callback = self._prev_callback
            self.add_item(prev_button)

            # Next button - use safer emoji
            next_button = ui.Button(
                label="Next ▶",
                style=discord.ButtonStyle.secondary,
                disabled=self.current_index >= self.total_results - 1
            )
            next_button.callback = self._next_callback
            self.add_item(next_button)

            # Page indicator
            page_button = ui.Button(
                label=f"{self.current_index + 1}/{self.total_results}",
                style=discord.ButtonStyle.gray,
                disabled=True
            )
            self.add_item(page_button)

        # Action buttons - Sacrifice button removed, use 'sl sacrifice' command instead



        # Oshi button (for favorites) - use safer emoji
        oshi_button = ui.Button(
            label="❤️ Oshi",
            style=discord.ButtonStyle.primary
        )
        oshi_button.callback = self._oshi_callback
        self.add_item(oshi_button)

    def _is_duplicate_result(self):
        """Check if current result is a duplicate."""
        if self.current_index < len(self.results):
            return self.results[self.current_index][3]  # is_duplicate flag
        return False

    async def _prev_callback(self, interaction: discord.Interaction):
        """Handle previous button click."""
        try:
            if interaction.user.id != self.ctx.author.id:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
                return

            if self.current_index > 0:
                self.current_index -= 1
                self._update_buttons()
                embed = await self._create_current_embed()

                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await interaction.edit_original_response(embed=embed, view=self)
            else:
                if not interaction.response.is_done():
                    await interaction.response.defer()
        except discord.NotFound:
            # Interaction expired, ignore
            pass
        except Exception as e:
            print(f"Error in gacha prev callback: {e}")

    async def _next_callback(self, interaction: discord.Interaction):
        """Handle next button click."""
        try:
            if interaction.user.id != self.ctx.author.id:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
                return

            if self.current_index < self.total_results - 1:
                self.current_index += 1
                self._update_buttons()
                embed = await self._create_current_embed()

                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await interaction.edit_original_response(embed=embed, view=self)
            else:
                if not interaction.response.is_done():
                    await interaction.response.defer()
        except discord.NotFound:
            # Interaction expired, ignore
            pass
        except Exception as e:
            print(f"Error in gacha next callback: {e}")



    # Sacrifice callback removed - use 'sl sacrifice' command instead

    async def _oshi_callback(self, interaction: discord.Interaction):
        """Handle oshi (favorite) button click."""
        try:
            if interaction.user.id != self.ctx.author.id:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Only the command user can use these buttons!", ephemeral=True)
                return

            # Get current result
            if self.current_index < len(self.results):
                _, _, entity, _ = self.results[self.current_index]

                # Save oshi to player data (we'll create a proper oshi system later)
                if not hasattr(self.player, 'oshi_list'):
                    self.player.oshi_list = []

                if entity.id not in self.player.oshi_list:
                    self.player.oshi_list.append(entity.id)
                    await self.player.save()

                    embed = discord.Embed(
                        title="💖 Oshi Added!",
                        description=f"**{entity.name}** has been added to your oshi list! ✨\nUse `sl oshi` to view your collection.",
                        color=discord.Color.pink()
                    )
                    embed.set_thumbnail(url=entity.image if hasattr(entity, 'image') else None)

                    if not interaction.response.is_done():
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    response_text = f"💖 **{entity.name}** is already in your oshi list!"
                    if not interaction.response.is_done():
                        await interaction.response.send_message(response_text, ephemeral=True)
                    else:
                        await interaction.followup.send(response_text, ephemeral=True)
            else:
                if not interaction.response.is_done():
                    await interaction.response.defer()
        except discord.NotFound:
            # Interaction expired, ignore
            pass
        except Exception as e:
            print(f"Error in gacha oshi callback: {e}")

    async def _create_current_embed(self):
        """Create embed for current result."""
        if self.current_index >= len(self.results):
            return discord.Embed(title="Error", description="Invalid result index", color=discord.Color.red())

        res_type, rarity, entity, is_duplicate = self.results[self.current_index]

        # Color based on rarity
        rarity_colors = {"UR": 0xFF0080, "SSR": 0xFFD700, "Super Rare": 0x9932CC}
        color = rarity_colors.get(rarity, 0x7289DA)

        # Create embed
        embed = discord.Embed(
            title=f"#{self.current_index + 1} {getClassEmoji(entity.classType)} {entity.name}",
            color=color
        )

        # Add rarity and level info
        embed.add_field(
            name="📊 Details",
            value=f"**Rarity**: {getRarityEmoji(rarity)} {rarity}\n**Level**: 1 {entity.classType} Spectrum",
            inline=False
        )

        # Add stats if available
        if hasattr(entity, 'attack') and hasattr(entity, 'defense') and hasattr(entity, 'health'):
            embed.add_field(
                name="⚔️ Base Stats",
                value=f"**ATK**: {entity.attack}\n**DEF**: {entity.defense}\n**HP**: {entity.health}",
                inline=True
            )

        # Add description
        if hasattr(entity, 'description') and entity.description:
            description = entity.description[:200] + "..." if len(entity.description) > 200 else entity.description
            embed.add_field(
                name="📖 Description",
                value=description,
                inline=False
            )

        # Add duplicate/new status
        if is_duplicate:
            shard_id = f"s_{entity.id}"
            shard_count = self.player.inventory.get(shard_id, 0)
            embed.add_field(
                name="🔄 Status",
                value=f"**DUPLICATE** - Converted to shard\n**Shards Owned**: {shard_count}",
                inline=False
            )
        else:
            embed.add_field(
                name="✨ Status",
                value="**NEW!** - Added to collection",
                inline=False
            )

        # Set image
        if hasattr(entity, 'image') and entity.image:
            embed.set_image(url=entity.image)

        # Add footer with navigation info
        if self.total_results > 1:
            embed.set_footer(text=f"Pull {self.current_index + 1} of {self.total_results} • Use navigation buttons")
        else:
            embed.set_footer(text="Single pull result")

        return embed

class Gacha(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="gacha", help="View gacha drop rates and your pity progress.")
    async def gacha(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Not Started", description="You haven't started your adventure yet. Use `sl start`.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        qx = getEmoji("qx")
        down = getEmoji("down")
        ssr_rate = BASE_DROP_RATES["SSR"]

        embed = discord.Embed(
            title="Rate-UP Gacha",
            description=(
                "Welcome to the Rate-UP Gacha!\n\n"
                "Each pull has the following chances:\n"
                f"💎 **UR**: {BASE_DROP_RATES['UR']}%\n"
                f"{qx} **SSR**: {BASE_DROP_RATES['SSR']}%\n"
                f"{qx} **Super Rare**: {BASE_DROP_RATES['Super Rare']}%\n\n"
                "Guaranteed **SSR** every 80 pulls!\n"
                "**UR** rarity is the rarest tier - only 0.1% chance!"
            ),
            color=discord.Color.random()
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1312723004467314778/1325234628671574059/solo_leveling_by_avarond_de3ob37-fullview_2.jpg")
        embed.add_field(name="Progress to Guaranteed SSR:", value=f"-# {self.create_progress_bar(player.gacha % 80)}", inline=False)
        embed.add_field(name="Your Tickets:", value=f"{getEmoji('ticket')} {player.ticket}", inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="pull", help="Use gacha tickets to pull for new hunters and weapons.")
    @app_commands.describe(quantity="The number of pulls to perform (1-15).")
    @cooldown(1, 1, BucketType.user)  # Reduced cooldown to 1 second
    async def pull(self, ctx: commands.Context, quantity: int = 1):
        if not 1 <= quantity <= 15:  # Increased from 5 to 15
            embed = discord.Embed(title="Invalid Quantity", description="You can only pull between 1 and 15 times at once!", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            return

        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.reply(embed=discord.Embed(title="Not Started", description="Player not found. Use `sl start` first.", color=discord.Color.red()), mention_author=False)
            return
            
        if player.ticket < quantity:
            await ctx.reply(embed=discord.Embed(title="Not Enough Tickets", description=f"You need {quantity} {getEmoji('ticket')} but you only have {player.ticket}.", color=discord.Color.red()), mention_author=False)
            return
        if player.trade:
            await ctx.send(embed=discord.Embed(title="Trade in Progress", description=f"<@{player.id}> is in a 🤝 trade. Please complete it first.", color=discord.Color.orange()))
            return

        original_ticket_count = player.ticket
        player.ticket -= quantity
        
        try:
            results, luck_values = await self.gacha_pull(player, quantity)
            await player.save()

            # Track gacha achievements
            try:
                from structure.achievement_tracker import AchievementTracker
                await AchievementTracker.track_gacha_pull(player, quantity)
                await AchievementTracker.track_collection(player, "item")
                await AchievementTracker.track_collection(player, "hunter")
            except Exception as e:
                logging.error(f"Error tracking gacha achievements: {e}")

            await self.send_enhanced_results(ctx, player, results, luck_values)
        except Exception as e:
            player.ticket = original_ticket_count # Restore tickets on failure
            await player.save()
            logging.error(f"Gacha pull failed for {ctx.author.id}. Tickets restored. Error: {e}", exc_info=True)
            embed = discord.Embed(title="❌ Gacha Pull Failed", description=f"An error occurred: {e}. Your tickets were not used.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)

    @pull.error
    async def pull_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Cooldown", description=f"Please wait {error.retry_after:.1f} seconds before pulling again.", color=discord.Color.orange())
            await ctx.reply(embed=embed, mention_author=False)

    async def gacha_pull(self, player, pulls):
        results = []
        luck_values = []

        # Get regular items/heroes (non-custom)
        all_heroes = [h for h in await HeroManager.get_all() if h.rarity.lower() != "custom"]
        all_items = [i for i in await ItemManager.get_all() if i.rarity.lower() != "custom"]

        # Get custom items/heroes assigned to this player
        custom_heroes = await self.get_player_custom_heroes(player.id)
        custom_items = await self.get_player_custom_items(player.id)

        # Add custom items to the pool
        all_heroes.extend(custom_heroes)
        all_items.extend(custom_items)

        for _ in range(pulls):
            player.gacha += 1
            if player.gacha > 1_000_000: player.gacha %= 80

            rarity = "SSR" if player.gacha % 80 == 0 else random.choices(list(BASE_DROP_RATES.keys()), list(BASE_DROP_RATES.values()), k=1)[0]
            
            entity, res_type, is_duplicate = None, None, False
            
            possible_heroes = [h for h in all_heroes if h.rarity.lower() == rarity.lower()]
            possible_items = [i for i in all_items if i.rarity.lower() == rarity.lower()]

            if not possible_heroes and not possible_items:
                possible_heroes = all_heroes
                possible_items = all_items
                if not possible_heroes and not possible_items:
                    raise Exception("Configuration Error: No pullable items or heroes exist.")

            is_item_pull = random.random() < 0.35 or rarity == "Rare"
            
            if is_item_pull and possible_items:
                entity = random.choice(possible_items)
                res_type = "Item"
                is_duplicate = player.add_item(entity.id)
            elif not is_item_pull and possible_heroes:
                entity = random.choice(possible_heroes)
                res_type = "Hero"
                is_duplicate = player.add_hunter(entity.id)
            elif possible_heroes:
                entity = random.choice(possible_heroes)
                res_type = "Hero"
                is_duplicate = player.add_hunter(entity.id)
            elif possible_items:
                entity = random.choice(possible_items)
                res_type = "Item"
                is_duplicate = player.add_item(entity.id)

            if entity:
                results.append((res_type, entity.rarity, entity, is_duplicate))
                luck_values.append(self.calculate_luck_value(entity.rarity))
            else:
                raise Exception("Could not find any item/hero to pull.")

        return results, luck_values

    async def get_player_custom_heroes(self, player_id: int):
        """Get custom heroes assigned to this player"""
        try:
            import json
            with open('customs.json', 'r') as f:
                customs = json.load(f)

            # Find customs assigned to this player
            player_customs = []
            for custom in customs:
                if custom.get('type') == 'hunter' and str(custom.get('user_id')) == str(player_id):
                    # Convert custom data to Hero object
                    from structure.heroes import Hero
                    hero = Hero(
                        id=custom['name'].lower().replace(' ', '_'),
                        name=custom['name'],
                        rarity='Custom',
                        classType=custom.get('element', 'Fire'),
                        type=custom.get('classType', 'DPS'),
                        image='https://files.catbox.moe/jvxvcr.png',  # Default image
                        description=f"Custom hero for {custom.get('user_id')}",
                        health=1000,
                        attack=200,
                        defense=150,
                        speed=100,
                        mp=200,
                        precision=100,
                        age=25,
                        gender='Unknown',
                        country='Custom',
                        weapon='Custom Weapon',
                        guild='None',
                        rank='S'
                    )
                    player_customs.append(hero)

            return player_customs
        except Exception as e:
            logging.error(f"Error loading custom heroes: {e}")
            return []

    async def get_player_custom_items(self, player_id: int):
        """Get custom items assigned to this player"""
        try:
            import json
            with open('customs.json', 'r') as f:
                customs = json.load(f)

            # Find custom items assigned to this player
            player_customs = []
            for custom in customs:
                if custom.get('type') == 'item' and str(custom.get('user_id')) == str(player_id):
                    # Convert custom data to Item object
                    from structure.items import Item
                    item = Item(
                        id=custom['name'].lower().replace(' ', '_'),
                        name=custom['name'],
                        rarity='Custom',
                        classType=custom.get('element', 'Fire'),
                        type='Weapon',
                        image='https://files.catbox.moe/jvxvcr.png',  # Default image
                        description=f"Custom item for {custom.get('user_id')}",
                        health=100,
                        attack=150,
                        defense=100,
                        speed=50,
                        mp=50,
                        precision=75
                    )
                    player_customs.append(item)

            return player_customs
        except Exception as e:
            logging.error(f"Error loading custom items: {e}")
            return []

    def calculate_luck_value(self, rarity):
        return {"UR": 1000, "SSR": 500, "Super Rare": 175}.get(rarity, 0)

    def create_progress_bar(self, progress):
        bar_length = 15
        filled_length = int(bar_length * progress / 80)
        bar = "█" * filled_length + "▒" * (bar_length - filled_length)
        return f"`{bar}` {progress}/80"

    async def send_enhanced_results(self, ctx, player, results, luck_values):
        """Send enhanced pull results with HoloCards-style UI."""
        if not results:
            embed = discord.Embed(title="No Results", description="No items were pulled.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create the enhanced view
        view = PullResultView(ctx, player, results)

        # Create initial embed
        embed = await view._create_current_embed()

        # Add pull summary
        if len(results) > 1:
            summary_text = []
            rarity_counts = {}
            for res_type, rarity, entity, is_duplicate in results:
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

            for rarity, count in rarity_counts.items():
                summary_text.append(f"{getRarityEmoji(rarity)} **{rarity}**: {count}")

            embed.add_field(
                name=f"📋 Pull Summary ({len(results)} pulls)",
                value="\n".join(summary_text),
                inline=True
            )

            # Add luck and pity info
            embed.add_field(
                name="🍀 Luck & Progress",
                value=f"**Luck Value**: {sum(luck_values)}\n**SSR Progress**: {self.create_progress_bar(player.gacha % 80)}",
                inline=True
            )

        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.hybrid_command(name="locked", help="View your locked items from pulls")
    @cooldown(1, 5, BucketType.user)
    async def locked_items(self, ctx: commands.Context):
        """View locked items from pulls"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Not Started", description="You haven't started your journey yet! Use `sl start` to begin.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Get locked items from player data (we'll store this in a new field)
        locked_items = getattr(player, 'locked_items', {})

        if not locked_items:
            embed = discord.Embed(
                title="🔒 No Locked Items",
                description="You haven't locked any items from pulls yet!\n\nUse the lock button during pulls to save items for later.",
                color=discord.Color.orange()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create locked items view
        view = LockedItemsView(ctx, player, locked_items)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    async def send_results_embed(self, ctx, player, results, luck_values):
        rarity_colors = {"UR": 0xFF0080, "SSR": 0xFFD700, "Super Rare": 0x9932CC}
        rarity_order = ["Super Rare", "SSR", "UR"]
        
        highest_rarity = "Rare"
        highest_rarity_item = None
        
        hunters, weapons = [], []
        down = getEmoji("down")

        for res_type, rarity, entity, is_duplicate in results:
            if rarity_order.index(rarity) > rarity_order.index(highest_rarity):
                highest_rarity = rarity
                highest_rarity_item = entity

            rarity_emoji = getRarityEmoji(entity.rarity)
            class_emoji = getClassEmoji(getattr(entity, 'classType', ''))
            
            if is_duplicate:
                # --- FIX APPLIED HERE ---
                # Get the specific emoji for the item/hunter shard
                shard_emoji = getEmoji(entity.id) 
                shard_type = "Hunter" if res_type == "Hero" else "Weapon"
                text = f"{rarity_emoji} {class_emoji}—{entity.name}"
                text += f"\n{down} +1 - {shard_type} Shard {shard_emoji}"
            else:
                text = f"(`NEW`) {rarity_emoji} {class_emoji}—{entity.name}"
            
            if res_type == "Item":
                weapons.append(text)
            else:
                hunters.append(text)

        embed = discord.Embed(
            title=f"Gacha Result - {len(results)} Pull{'s' if len(results) > 1 else ''}",
            color=rarity_colors.get(highest_rarity, 0x7289DA)
        )
        
        description = []
        if hunters:
            description.append("**Hunters:**")
            description.extend([f"`{i}.` {h}" for i, h in enumerate(hunters, 1)])
        if weapons:
            description.append("\n**Weapons:**")
            description.extend([f"`{i}.` {w}" for i, w in enumerate(weapons, 1)])

        description.append(f"\n**Luck Value:** {sum(luck_values)}")
        description.append(f"**Progress to Guaranteed SSR:**\n{self.create_progress_bar(player.gacha % 80)}")
        embed.description = "\n".join(description)

        if highest_rarity_item and hasattr(highest_rarity_item, 'image'):
            embed.set_image(url=highest_rarity_item.image)

        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(Gacha(bot))