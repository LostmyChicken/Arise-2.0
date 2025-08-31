import discord
from discord.ext import commands
from discord import app_commands
from structure.heroes import HeroManager
from structure.guild import Guild
from structure.Rank import RankingLeaderboard
from utilis.utilis import extractName, get_emoji, getStatWeapon
from structure.emoji import getEmoji, getClassEmoji
from structure.items import ItemManager
from structure.player import Player
from structure.title_system import TitleManager
from typing import Optional
import discord.ui as ui
import asyncio
import math

import math

class CollectionView(ui.View):
    def __init__(self, author: discord.User, target: discord.User, player: Player, bot: commands.Bot, collection_type: str = "hunters"):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
        self.player = player
        self.bot = bot
        self.collection_type = collection_type  # "hunters" or "weapons"
        self.current_page = 0
        self.items_per_page = 15
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This collection doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def get_collection_data(self):
        """Get the collection data based on type"""
        if self.collection_type == "hunters":
            data = []
            for hunter_id in self.player.hunters.keys():
                char = await HeroManager.get(hunter_id)
                if char:
                    hunter_emoji = await get_emoji(char.id)
                    data.append(f"{hunter_emoji} {char.name}")

            # Get total available hunters (including custom ones)
            all_hunters = await HeroManager.get_all()
            total_hunters = len(all_hunters)
            return data, f"Hunter Collection ({len(self.player.hunters)}/{total_hunters})"
        else:  # weapons
            data = []
            for weapon_id in self.player.inventory.keys():
                weapon_data = await ItemManager.get(weapon_id)
                if weapon_data:
                    weapon_emoji = await get_emoji(weapon_data.id)
                    weapon_level = self.player.inventory[weapon_id].get('level', 1) if isinstance(self.player.inventory[weapon_id], dict) else 1
                    data.append(f"{weapon_emoji} {weapon_data.name} (Lv.{weapon_level})")

            # Get total available weapons (including custom ones)
            all_weapons = await ItemManager.get_all()
            total_weapons = len(all_weapons)
            return data, f"Weapon Collection ({len(self.player.inventory)}/{total_weapons})"

    async def get_collection_embed(self):
        """Generate the paginated collection embed"""
        data, title = await self.get_collection_data()
        
        if not data:
            embed = discord.Embed(
                title=f"{self.target.display_name}'s {title}",
                description=f"No {'hunters' if self.collection_type == 'hunters' else 'weapons'} found.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=self.target.display_avatar.url)
            return embed

        # Calculate pagination
        total_pages = math.ceil(len(data) / self.items_per_page)
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_data = data[start_idx:end_idx]

        embed = discord.Embed(
            title=f"{self.target.display_name}'s {title}",
            description="\n".join(page_data),
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages}")
        embed.set_thumbnail(url=self.target.display_avatar.url)
        return embed

    @ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        data, _ = await self.get_collection_data()
        total_pages = math.ceil(len(data) / self.items_per_page)
        
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.get_collection_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You're already on the first page!", ephemeral=True)

    @ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        data, _ = await self.get_collection_data()
        total_pages = math.ceil(len(data) / self.items_per_page)
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.get_collection_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("You're already on the last page!", ephemeral=True)

    @ui.button(label="🗡️ Weapons", style=discord.ButtonStyle.primary)
    async def switch_collection(self, interaction: discord.Interaction, button: ui.Button):
        # Switch between hunters and weapons
        if self.collection_type == "hunters":
            self.collection_type = "weapons"
            button.label = "👥 Hunters"
        else:
            self.collection_type = "hunters"
            button.label = "🗡️ Weapons"
        
        self.current_page = 0  # Reset to first page when switching
        embed = await self.get_collection_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="◀️ Back to Profile", style=discord.ButtonStyle.gray, row=1)
    async def back_to_profile(self, interaction: discord.Interaction, button: ui.Button):
        # Return to the main profile view
        profile_view = ProfileView(self.author, self.target, self.player, self.bot)
        embed = await profile_view.get_main_profile_embed()
        await interaction.response.edit_message(embed=embed, view=profile_view)


class ProfileView(ui.View):
    def __init__(self, author: discord.User, target: discord.User, player: Player, bot: commands.Bot):
        super().__init__(timeout=300)
        self.author = author
        self.target = target
        self.player = player
        self.bot = bot
        self.current_view = "main"

    async def on_timeout(self):
        """Ensure player.inc is reset when view times out"""
        try:
            # Only reset inc for the author (person who ran the command)
            if self.author.id == self.target.id:
                author_player = await Player.get(self.author.id)
                if author_player and author_player.inc:
                    author_player.inc = False
                    await author_player.save()
        except Exception as e:
            print(f"Error in ProfileView timeout: {e}")
    
    def _disable_buttons_for_non_owner(self):
        """Disable buttons for users who don't own the profile"""
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This profile doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def ensure_player_not_stuck(self):
        """Ensure the player isn't stuck in inc state from profile interactions"""
        try:
            if self.author.id == self.target.id:
                fresh_player = await Player.get(self.author.id)
                if fresh_player and fresh_player.inc:
                    fresh_player.inc = False
                    await fresh_player.save()
        except Exception as e:
            print(f"Error ensuring player not stuck: {e}")

    async def get_main_profile_embed(self):
        """Generate the main profile embed with original emojis"""
        player = await Player.get(self.target.id)  # Refresh player data
        
        xp_to_next_level = (player.level ** 2) * 100
        current_xp = player.xp
        xp_progress = f"{current_xp}/{xp_to_next_level}"
        xp_bar = self.generate_progress_bar(current_xp, xp_to_next_level)

        # Original emoji variables
        exp = getEmoji("xp")
        health = getEmoji("health")
        mana = getEmoji("mp")
        defense = getEmoji("defense")
        atk = getEmoji("attack")
        down = getEmoji("down")
        slot = getEmoji("slot")
        qx = getEmoji("qx")

        # Weapon fields with original logic
        weapon_fields = []
        for weapon_slot, weapon_emoji in [("Weapon", qx), ("Weapon_2", down)]:
            weapon_id = player.equipped.get(weapon_slot)
            if weapon_id:
                weapon_data = await ItemManager.get(weapon_id)
                if weapon_data:
                    weapon_level = player.inventory[weapon_id]['level'] if isinstance(player.inventory[weapon_id], dict) else 1
                    weapon_fields.append(f"{await get_emoji(weapon_data.id)}")
                else:
                    weapon_fields.append(f"{weapon_emoji} Invalid Weapon Data")
            else:
                weapon_fields.append(f"{slot}")

        # Get player's active title
        title_display = await TitleManager.get_title_display_for_profile(self.target.id)
        title_text = f"\n{title_display}" if title_display else ""

        embed = discord.Embed(
            title=f"{self.target.display_name}'s Profile{title_text}",
            description=(f"Level: `{player.level}`\nExperience: `[{xp_progress}]`\n{xp_bar}"),
            color=discord.Color.dark_blue()
        )

        # Guild info
        t = "None"
        if player.guild:
            g = await Guild.get(player.guild)
            if g:
                t = f"{g.name.title()} `(GC {g.gates})`"

        embed.add_field(
            name="Guild",
            value=f"> {t}",
            inline=False
        )

        # Use same ranking system as sl evaluate and sl system
        try:
            from structure.Rank import RankingLeaderboard
            leaderboard = RankingLeaderboard()
            rank_data = await leaderboard.get(player.id)

            if rank_data:
                # rank_data is a tuple: (id, rank, rank_, power)
                rank_string = rank_data[1]  # e.g., "C-Rank"
                rank_position = rank_data[2]  # position number
                power_level = rank_data[3]  # power level

                embed.add_field(
                    name="Hunter Rank",
                    value=f"> 🏆 **{rank_string}** - Position #{rank_position}\n> Power Level: `{power_level:,}`",
                    inline=False
                )
            else:
                # Player not in leaderboard yet - add them using same logic as sl system
                from commands.evaluate import RankEvaluation
                from structure.stats import getStat
                from commands.party import getPartyTotalPower

                # Calculate power level same as evaluate command
                base_stats = {"Total Power": (player.hp / 5) + player.attack + player.defense + player.precision + player.mp}
                stats = getStat(["Total Power"], level=player.level, base_stats=base_stats)

                # Calculate party power
                party_power = await getPartyTotalPower(player)

                # Calculate weapon power
                weapon_power = 0
                for slot in ["Weapon", "Weapon_2"]:
                    if item_id := player.equipped.get(slot):
                        if item_id in player.inventory:
                            item_data = player.inventory[item_id]
                            weapon_level = item_data.get('level', 1) if isinstance(item_data, dict) else 1
                            from utilis.utilis import getStatWeapon
                            weapon_stat = await getStatWeapon(item_id, weapon_level)
                            if weapon_stat:
                                weapon_power += weapon_stat.get("total_power", 0)

                power_level = int(stats.Total_Power + party_power + weapon_power)

                # Add to leaderboard
                await leaderboard.add_player(player.id, power_level)

                # Get updated rank data
                rank_data = await leaderboard.get(player.id)
                if rank_data:
                    rank_string = rank_data[1]
                    rank_position = rank_data[2]
                    power_level = rank_data[3]

                    embed.add_field(
                        name="Hunter Rank",
                        value=f"> 🏆 **{rank_string}** - Position #{rank_position}\n> Power Level: `{power_level:,}`",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Hunter Rank",
                        value=f"> 🏆 **E-Rank** - Position #999\n> Power Level: `{power_level:,}`",
                        inline=False
                    )

        except Exception as e:
            # Fallback to basic display
            embed.add_field(
                name="Hunter Rank",
                value=f"> 🏆 **E-Rank** - Position #Unranked\n> Power Level: `Calculating...`",
                inline=False
            )

        # Hunter party icons
        hunter_icons = []
        for slot_key in ["Party_1", "Party_2", "Party_3"]:
            hunter_id = player.equipped.get(slot_key)
            if hunter_id:
                hunter = player.hunters.get(hunter_id)
                if hunter:
                    char = await HeroManager.get(hunter_id)
                    if char:
                        hunter_emoji = await get_emoji(char.id)
                        hunter_icons.append(f"{hunter_emoji}")
                    else:
                        hunter_icons.append(f"{slot}")
                else:
                    hunter_icons.append(f"{slot}")
            else:
                hunter_icons.append(f"{slot}")

        embed.add_field(name="Party Hunters", value=f"> {' '.join(hunter_icons)}", inline=False)
        embed.add_field(name="Equipped Weapons", value=f"> {' '.join(weapon_fields)}", inline=False)

        # Streaks
        embed.add_field(
            name="Streaks",
            value=(
                f"> Vote Streak: `{player.vS}`\n"
                f"> Daily Streak: `{player.dS}`\n"
                f"> Arena Streak: `{player.aStreak}`\n"
            ),
            inline=False
        )

        # Lifetime Progress with correct totals
        all_hunters = await HeroManager.get_all()
        all_weapons = await ItemManager.get_all()
        total_hunters = len(all_hunters)
        total_weapons = len(all_weapons)

        embed.add_field(
            name="Lifetime Progress",
            value=(
                f"{down} Hunters Unlocked: `{len(player.hunters)}/{total_hunters}`\n"
                f"{down} Weapons Unlocked: `{len(player.inventory)}/{total_weapons}`\n"
                f"{down} Shadows Unlocked: `{len(player.shadows)}/1`"
            ),
            inline=False
        )

        embed.set_thumbnail(url=self.target.display_avatar.url)
        return embed

    async def get_stats_embed(self):
        """Generate detailed stats embed"""
        player = await Player.get(self.target.id)
        
        # Calculate bonus stats from equipped weapons
        bonus_atk, bonus_def, bonus_hp, bonus_mp = 0, 0, 0, 0
        for weapon_slot in ["Weapon", "Weapon_2"]:
            weapon_id = player.equipped.get(weapon_slot)
            if weapon_id and weapon_id in player.inventory:
                item_data = player.inventory[weapon_id]
                weapon_level = item_data.get('level', 1) if isinstance(item_data, dict) else 1
                stats = await getStatWeapon(weapon_id, weapon_level)
                if stats:
                    bonus_atk += stats['attack']
                    bonus_def += stats['defense']
                    bonus_hp += stats['hp']
                    bonus_mp += stats['mp']

        # Original emojis
        health = getEmoji("health")
        atk = getEmoji("attack")
        defense = getEmoji("defense")
        mana = getEmoji("mp")

        embed = discord.Embed(
            title=f"{self.target.display_name}'s Detailed Statistics",
            color=discord.Color.green()
        )

        stats_text = (
            f"{health} **Health**: `{player.hp:,}` (+{bonus_hp:,}) = `{player.hp + bonus_hp:,}`\n"
            f"{atk} **Attack**: `{player.attack:,}` (+{bonus_atk:,}) = `{player.attack + bonus_atk:,}`\n"
            f"{defense} **Defense**: `{player.defense:,}` (+{bonus_def:,}) = `{player.defense + bonus_def:,}`\n"
            f"{mana} **Mana Points**: `{player.mp:,}` (+{bonus_mp:,}) = `{player.mp + bonus_mp:,}`\n\n"
            f"⭐ **Skill Points**: `{player.skillPoints:,}`"
        )

        embed.add_field(name="Combat Statistics", value=stats_text, inline=False)

        # Currency and resources
        gold = getEmoji("gold")
        stone = getEmoji("stone")
        xp = getEmoji("xp")
        
        resources_text = (
            f"{gold} **Gold**: `{player.gold:,}`\n"
            f"{getEmoji('ticket')} **Gacha Tickets**: `{player.ticket:,}`\n"
            f"{getEmoji('gate_key')} **Gate Keys**: `{player.key:,}`\n"
            f"{stone} **Essence Stones**: `{player.stone:,}`\n"
            f"💎 **Diamonds**: `{player.diamond:,}`\n"
            f"🌑 **Traces of Shadow**: `{player.tos:,}`"
        )

        embed.add_field(name="Resources & Currency", value=resources_text, inline=False)
        embed.set_thumbnail(url=self.target.display_avatar.url)
        return embed

    async def get_inventory_summary_embed(self):
        """Generate inventory summary embed"""
        player = await Player.get(self.target.id)
        
        embed = discord.Embed(
            title=f"{self.target.display_name}'s Collection Overview",
            color=discord.Color.blue()
        )

        # Hunter summary
        hunter_text = f"**Total Hunters**: `{len(player.hunters)}/34`\n"
        if player.hunters:
            hunter_list = []
            for hunter_id in list(player.hunters.keys())[:10]:  # Show first 10
                char = await HeroManager.get(hunter_id)
                if char:
                    hunter_emoji = await get_emoji(char.id)
                    hunter_list.append(f"{hunter_emoji} {char.name}")
            
            hunter_text += "\n".join(hunter_list)
            if len(player.hunters) > 10:
                hunter_text += f"\n... and {len(player.hunters) - 10} more"

        embed.add_field(name="👥 Hunter Collection", value=hunter_text, inline=False)

        # Weapon summary with correct total
        all_weapons = await ItemManager.get_all()
        total_weapons = len(all_weapons)
        weapon_text = f"**Total Weapons**: `{len(player.inventory)}/{total_weapons}`\n"
        if player.inventory:
            weapon_list = []
            weapon_ids = list(player.inventory.keys())[:10]  # Show first 10
            for weapon_id in weapon_ids:
                weapon_data = await ItemManager.get(weapon_id)
                if weapon_data:
                    weapon_emoji = await get_emoji(weapon_data.id)
                    weapon_list.append(f"{weapon_emoji} {weapon_data.name}")
                    
            weapon_text += "\n".join(weapon_list)
            if len(player.inventory) > 10:
                weapon_text += f"\n... and {len(player.inventory) - 10} more"

        embed.add_field(name="⚔️ Weapon Collection", value=weapon_text, inline=False)
        
        embed.set_footer(text="Use /inventory hunters or /inventory weapons for detailed views")
        embed.set_thumbnail(url=self.target.display_avatar.url)
        return embed

    def generate_progress_bar(self, current, total, length=20):
        """Generates a progress bar string for XP."""
        if total == 0:
            return "`[░░░░░░░░░░░░░░░░░░░░]`"
        filled_length = int(length * current // total)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return f"`[{bar}]`"

    @ui.button(label="Statistics", style=discord.ButtonStyle.success, emoji="📊")
    async def view_stats(self, interaction: discord.Interaction, button: ui.Button):
        embed = await self.get_stats_embed()
        self.current_view = "stats"
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Collection", style=discord.ButtonStyle.primary, emoji="🎒")
    async def view_collection(self, interaction: discord.Interaction, button: ui.Button):
        # Switch to the new paginated collection view
        collection_view = CollectionView(self.author, self.target, self.player, self.bot, "hunters")
        embed = await collection_view.get_collection_embed()
        await interaction.response.edit_message(embed=embed, view=collection_view)

    @ui.button(label="Team Setup", style=discord.ButtonStyle.secondary, emoji="⚔️")
    async def team_setup(self, interaction: discord.Interaction, button: ui.Button):
        if self.author.id != self.target.id:
            await interaction.response.send_message("You can only manage your own team!", ephemeral=True)
            return

        # Open the interactive team setup
        await interaction.response.defer()
        team_view = TeamSetupView(self.author, self.player, self.bot)
        embed = await team_view.get_team_embed()
        await interaction.followup.send(embed=embed, view=team_view, ephemeral=True)

    @ui.button(label="Daily Quests", style=discord.ButtonStyle.success, emoji="📋")
    async def daily_quests(self, interaction: discord.Interaction, button: ui.Button):
        if self.author.id != self.target.id:
            await interaction.response.send_message("You can only view your own daily quests!", ephemeral=True)
            return

        await interaction.response.defer()

        # Run the daily quest command for the user
        daily_cog = self.bot.get_cog("DailyCog")
        if daily_cog:
            # Create a proper fake context that handles reply properly
            class FakeContext:
                def __init__(self, interaction, bot):
                    self.author = interaction.user
                    self.channel = interaction.channel
                    self.guild = interaction.guild
                    self.bot = bot
                    self._interaction = interaction

                async def reply(self, *args, **kwargs):
                    # Remove mention_author since webhooks don't support it
                    kwargs.pop('mention_author', None)
                    return await self._interaction.followup.send(*args, **kwargs)

                async def send(self, *args, **kwargs):
                    return await self._interaction.followup.send(*args, **kwargs)

            fake_ctx = FakeContext(interaction, self.bot)
            await daily_cog.daily_quest(fake_ctx)
        else:
            await interaction.followup.send("📋 **Daily quest system not available right now.**", ephemeral=True)

    @ui.button(label="Cooldowns", style=discord.ButtonStyle.secondary, emoji="⏳")
    async def view_cooldowns(self, interaction: discord.Interaction, button: ui.Button):
        if self.author.id != self.target.id:
            await interaction.response.send_message("You can only view your own cooldowns!", ephemeral=True)
            return

        await interaction.response.defer()

        # Run the cooldowns command for the user
        cooldowns_cog = self.bot.get_cog("CooldownsCog")
        if cooldowns_cog:
            # Create a proper fake context that handles reply properly
            class FakeContext:
                def __init__(self, interaction, bot):
                    self.author = interaction.user
                    self.channel = interaction.channel
                    self.guild = interaction.guild
                    self.bot = bot
                    self._interaction = interaction

                async def reply(self, *args, **kwargs):
                    # Remove mention_author since webhooks don't support it
                    kwargs.pop('mention_author', None)
                    return await self._interaction.followup.send(*args, **kwargs)

                async def send(self, *args, **kwargs):
                    return await self._interaction.followup.send(*args, **kwargs)

            fake_ctx = FakeContext(interaction, self.bot)
            await cooldowns_cog.cooldowns(fake_ctx)
        else:
            await interaction.followup.send("⏳ **Cooldowns system not available right now.**", ephemeral=True)

    @ui.button(label="◀️ Back", style=discord.ButtonStyle.gray, row=1)
    async def back_to_main(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_view == "main":
            await interaction.response.send_message("You're already on the main profile page!", ephemeral=True)
            return
            
        embed = await self.get_main_profile_embed()
        self.current_view = "main"
        await interaction.response.edit_message(embed=embed, view=self)


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='profile', aliases=["pf"], help="View your or another user's player profile.")
    @app_commands.describe(user="The user whose profile you want to see.")
    async def view_profile(self, ctx: commands.Context, user: Optional[discord.User] = None):
        target_user = user or ctx.author
        player = await Player.get(target_user.id)
        
        if player is None:
            down = getEmoji("down")
            embed = discord.Embed(
                title="Profile Not Found",
                description=f"**{target_user.display_name}** hasn't started the bot yet.",
                color=discord.Color.red()
            )
            if not user:
                embed.description += f"\n{down} Use `sl start` to get Re-Awakened"
            await ctx.reply(embed=embed, mention_author=False)
            return

        view = ProfileView(ctx.author, target_user, player, self.bot)
        
        # Disable buttons for non-owners after view is fully constructed
        if ctx.author.id != target_user.id:
            view._disable_buttons_for_non_owner()
            
        embed = await view.get_main_profile_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

class TeamSetupView(ui.View):
    """Interactive team setup interface"""

    def __init__(self, author: discord.User, player: Player, bot: commands.Bot):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.bot = bot
        self.current_slot = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This team setup is not for you!", ephemeral=True)
            return False
        return True

    async def get_team_embed(self):
        """Generate the team setup embed"""
        # Refresh player data
        self.player = await Player.get(self.author.id)

        embed = discord.Embed(
            title=f"⚔️ {self.author.display_name}'s Team Setup",
            description="Manage your party hunters, weapons, and player equipment",
            color=discord.Color.dark_purple()
        )

        # Calculate total power
        total_power = 0
        for slot_key in ["Party_1", "Party_2", "Party_3"]:
            hunter_id = self.player.equipped.get(slot_key)
            if hunter_id and hunter_id in self.player.hunters:
                hunter = self.player.hunters[hunter_id]
                char = await HeroManager.get(hunter_id)
                if char:
                    level = hunter.get("level", 1)
                    from utilis.utilis import getStatHunter, getStatWeapon
                    stat = await getStatHunter(char.id, level)

                    weapon_id = hunter.get("weapon")
                    if weapon_id and weapon_id in self.player.inventory:
                        w_level = self.player.inventory[weapon_id].get("level", 1)
                        weapon_stat = await getStatWeapon(weapon_id, w_level)
                        if weapon_stat:
                            stat.total_power += weapon_stat.get("total_power", 0)

                    total_power += stat.total_power

        embed.add_field(
            name="💪 Total Party Power",
            value=f"`{total_power:,}` ⚔️",
            inline=False
        )

        # Show player equipment first
        player_weapons = []
        weapon1 = self.player.equipped.get("Weapon")
        weapon2 = self.player.equipped.get("Weapon_2")
        shadow = self.player.equipped.get("Shadow")

        if weapon1:
            weapon = await ItemManager.get(weapon1)
            if weapon:
                inventory = self.player.get_inventory()
                w_level = inventory.get(weapon1, {}).get("level", 1)
                player_weapons.append(f"**Slot 1**: {getEmoji(weapon.id)} {weapon.name} (Lv.{w_level})")
            else:
                player_weapons.append("**Slot 1**: *Empty*")
        else:
            player_weapons.append("**Slot 1**: *Empty*")

        if weapon2:
            weapon = await ItemManager.get(weapon2)
            if weapon:
                inventory = self.player.get_inventory()
                w_level = inventory.get(weapon2, {}).get("level", 1)
                player_weapons.append(f"**Slot 2**: {getEmoji(weapon.id)} {weapon.name} (Lv.{w_level})")
            else:
                player_weapons.append("**Slot 2**: *Empty*")
        else:
            player_weapons.append("**Slot 2**: *Empty*")

        if shadow:
            from structure.shadow import Shadow
            shadow_obj = await Shadow.get(shadow)
            if shadow_obj:
                shadows = self.player.get_shadows()
                shadow_data = shadows.get(shadow, {})
                s_level = shadow_data.get('level', 1)
                player_weapons.append(f"**Shadow**: 👑 {shadow_obj.name} (Lv.{s_level})")
            else:
                player_weapons.append("**Shadow**: *Empty*")
        else:
            player_weapons.append("**Shadow**: *Empty*")

        embed.add_field(
            name="👤 Your Equipment",
            value="\n".join(player_weapons),
            inline=False
        )

        # Show current party setup
        for i, slot_key in enumerate(["Party_1", "Party_2", "Party_3"], start=1):
            hunter_id = self.player.equipped.get(slot_key)
            if hunter_id and hunter_id in self.player.hunters:
                hunter_data = self.player.hunters.get(hunter_id)
                char = await HeroManager.get(hunter_id)
                if char and hunter_data:
                    level = hunter_data.get("level", 1)
                    tier = hunter_data.get("tier", 0)

                    # Get weapon info
                    weapon_id = hunter_data.get("weapon")
                    weapon_text = "No Weapon"
                    if weapon_id and weapon_id in self.player.inventory:
                        weapon = await ItemManager.get(weapon_id)
                        if weapon:
                            w_level = self.player.inventory[weapon_id].get("level", 1)
                            weapon_text = f"{getEmoji(weapon.id)} {weapon.name} (Lv.{w_level})"

                    tier_stars = "★" * tier + "☆" * (5 - tier)
                    field_value = (
                        f"**Level**: `{level}` | **Tier**: {tier_stars}\n"
                        f"**Weapon**: {weapon_text}"
                    )
                    # Import getClassEmoji locally to ensure it's available
                    from structure.emoji import getClassEmoji
                    embed.add_field(
                        name=f"Slot {i}: {getClassEmoji(char.classType)} {char.name}",
                        value=field_value,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"Slot {i}",
                        value=f"Empty {getEmoji('slot')}",
                        inline=False
                    )
            else:
                embed.add_field(
                    name=f"Slot {i}",
                    value=f"Empty {getEmoji('slot')}",
                    inline=False
                )

        embed.set_footer(text="Use the buttons below to manage your team")
        return embed

    @ui.button(label="Edit Slot 1", style=discord.ButtonStyle.primary, emoji="1️⃣", row=0)
    async def edit_slot_1(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_hunter_selection(interaction, "Party_1", 1)

    @ui.button(label="Edit Slot 2", style=discord.ButtonStyle.primary, emoji="2️⃣", row=0)
    async def edit_slot_2(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_hunter_selection(interaction, "Party_2", 2)

    @ui.button(label="Edit Slot 3", style=discord.ButtonStyle.primary, emoji="3️⃣", row=0)
    async def edit_slot_3(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_hunter_selection(interaction, "Party_3", 3)

    @ui.button(label="Weapon Slot 1", style=discord.ButtonStyle.success, emoji="⚔️", row=1)
    async def weapon_slot_1(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_weapon_selection(interaction, "Party_1", 1)

    @ui.button(label="Weapon Slot 2", style=discord.ButtonStyle.success, emoji="⚔️", row=1)
    async def weapon_slot_2(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_weapon_selection(interaction, "Party_2", 2)

    @ui.button(label="Weapon Slot 3", style=discord.ButtonStyle.success, emoji="⚔️", row=1)
    async def weapon_slot_3(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_weapon_selection(interaction, "Party_3", 3)

    @ui.button(label="Player Equipment", style=discord.ButtonStyle.secondary, emoji="👤", row=2)
    async def player_equipment(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        equipment_view = PlayerEquipmentView(self.author, self.player, self)
        embed = await equipment_view.get_equipment_embed()
        await interaction.edit_original_response(embed=embed, view=equipment_view)

    @ui.button(label="Clear All", style=discord.ButtonStyle.danger, emoji="🗑️", row=2)
    async def clear_all(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()

        # Clear all party slots
        self.player.equipped["Party_1"] = None
        self.player.equipped["Party_2"] = None
        self.player.equipped["Party_3"] = None
        await self.player.save()

        # Refresh the embed
        embed = await self.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄", row=2)
    async def refresh(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        embed = await self.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    async def show_hunter_selection(self, interaction: discord.Interaction, slot_key: str, slot_number: int):
        """Show hunter selection dropdown for a specific slot"""
        await interaction.response.defer()

        # Create hunter selection view
        hunter_view = HunterSelectionView(self.author, self.player, self.bot, slot_key, slot_number, self)
        embed = await hunter_view.get_selection_embed()
        await interaction.edit_original_response(embed=embed, view=hunter_view)

    async def show_weapon_selection(self, interaction: discord.Interaction, slot_key: str, slot_number: int):
        """Show weapon selection dropdown for a specific slot"""
        await interaction.response.defer()

        # Check if there's a hunter in this slot
        hunter_id = self.player.equipped.get(slot_key)
        if not hunter_id or hunter_id not in self.player.hunters:
            embed = discord.Embed(
                title="No Hunter in Slot",
                description=f"Please assign a hunter to Slot {slot_number} first before equipping a weapon.",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed, view=self)
            return

        # Create weapon selection view
        weapon_view = WeaponSelectionView(self.author, self.player, self.bot, slot_key, slot_number, hunter_id, self)
        embed = await weapon_view.get_selection_embed()
        await interaction.edit_original_response(embed=embed, view=weapon_view)

class HunterSelectionView(ui.View):
    """View for selecting hunters for a specific party slot"""

    def __init__(self, author: discord.User, player: Player, bot: commands.Bot, slot_key: str, slot_number: int, parent_view: TeamSetupView):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.bot = bot
        self.slot_key = slot_key
        self.slot_number = slot_number
        self.parent_view = parent_view

        # Add hunter selection dropdown (will be populated asynchronously)
        self.hunter_dropdown = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This selection is not for you!", ephemeral=True)
            return False
        return True

    async def get_selection_embed(self):
        """Generate the hunter selection embed and populate dropdown"""
        embed = discord.Embed(
            title=f"⚔️ Select Hunter for Slot {self.slot_number}",
            description="Choose a hunter from your collection to add to this party slot",
            color=discord.Color.blue()
        )

        # Show current hunter in this slot
        current_hunter_id = self.player.equipped.get(self.slot_key)
        if current_hunter_id and current_hunter_id in self.player.hunters:
            char = await HeroManager.get(current_hunter_id)
            if char:
                from structure.emoji import getClassEmoji
                embed.add_field(
                    name="Currently Equipped",
                    value=f"{getClassEmoji(char.classType)} **{char.name}**",
                    inline=False
                )
        else:
            embed.add_field(
                name="Currently Equipped",
                value=f"Empty {getEmoji('slot')}",
                inline=False
            )

        # Create and populate the dropdown
        await self.populate_hunter_dropdown()

        # Show available hunters count
        available_count = len([h_id for h_id in self.player.hunters.keys() if h_id not in self.player.equipped.values() or h_id == current_hunter_id])
        embed.add_field(
            name="Available Hunters",
            value=f"`{available_count}` hunters available for selection",
            inline=False
        )

        embed.set_footer(text="Use the dropdown below to select a hunter, or click Back to return")
        return embed

    async def populate_hunter_dropdown(self):
        """Populate the hunter dropdown with available hunters"""
        current_hunter_id = self.player.equipped.get(self.slot_key)
        equipped_hunters = {k: v for k, v in self.player.equipped.items() if k.startswith('Party_') and v and v != current_hunter_id}

        options = []

        # Add "Remove Hunter" option if there's currently a hunter equipped
        if current_hunter_id:
            options.append(discord.SelectOption(
                label="Remove Hunter",
                value="remove",
                description="Remove the current hunter from this slot",
                emoji="❌"
            ))

        # Add available hunters
        for hunter_id, hunter_data in self.player.hunters.items():
            if hunter_id not in equipped_hunters.values():  # Not equipped in other slots
                char = await HeroManager.get(hunter_id)

                if char:
                    level = hunter_data.get("level", 1)
                    tier = hunter_data.get("tier", 0)

                    # Check if this hunter is currently equipped in this slot
                    is_current = hunter_id == current_hunter_id
                    label = f"{'[EQUIPPED] ' if is_current else ''}{char.name}"
                    description = f"Level {level} • Tier {tier} • {char.rarity} • {char.classType}"

                    from structure.emoji import getClassEmoji, getRarityEmoji
                    # Use rarity emoji instead of class emoji for better identification
                    rarity_emoji = getRarityEmoji(char.rarity)
                    options.append(discord.SelectOption(
                        label=label[:100],  # Discord limit
                        value=hunter_id,
                        description=description[:100],  # Discord limit
                        emoji=rarity_emoji or getClassEmoji(char.classType)
                    ))

        # Limit to 25 options (Discord limit)
        options = options[:25]

        if not options:
            options.append(discord.SelectOption(
                label="No hunters available",
                value="none",
                description="All hunters are equipped or you have no hunters",
                emoji="❌"
            ))

        # Create and add the dropdown
        self.hunter_dropdown = HunterSelectDropdown(
            self.author, self.player, self.slot_key, self.slot_number, self.parent_view, options
        )
        self.add_item(self.hunter_dropdown)

    @ui.button(label="◀️ Back to Team", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_team(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        embed = await self.parent_view.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

    @ui.button(label="Remove Hunter", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def remove_hunter(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()

        # Remove hunter from this slot
        old_hunter_id = self.player.equipped.get(self.slot_key)
        self.player.equipped[self.slot_key] = None
        await self.player.save()

        # Get hunter name for confirmation
        hunter_name = "Unknown Hunter"
        if old_hunter_id:
            char = await HeroManager.get(old_hunter_id)
            if char:
                hunter_name = char.name

        # Return to team view
        embed = await self.parent_view.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class HunterSelectDropdown(ui.Select):
    """Dropdown for selecting hunters"""

    def __init__(self, author: discord.User, player: Player, slot_key: str, slot_number: int, parent_view: TeamSetupView, options: list):
        self.author = author
        self.player = player
        self.slot_key = slot_key
        self.slot_number = slot_number
        self.parent_view = parent_view

        super().__init__(
            placeholder=f"Choose a hunter for Slot {slot_number}...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This selection is not for you!", ephemeral=True)
            return

        await interaction.response.defer()

        selected_value = self.values[0]

        if selected_value == "none":
            return

        if selected_value == "remove":
            # Remove hunter from slot
            old_hunter_id = self.player.equipped.get(self.slot_key)
            self.player.equipped[self.slot_key] = None
            await self.player.save()

            # Get hunter name for confirmation
            hunter_name = "Unknown Hunter"
            if old_hunter_id:
                char = await HeroManager.get(old_hunter_id)
                if char:
                    hunter_name = char.name

            # Return to team view
            embed = await self.parent_view.get_team_embed()
            await interaction.edit_original_response(embed=embed, view=self.parent_view)
            return

        # Add hunter to slot
        hunter_id = selected_value
        char = await HeroManager.get(hunter_id)

        if not char:
            return

        # Check if hunter is already equipped elsewhere
        for slot, equipped_id in self.player.equipped.items():
            if slot.startswith('Party_') and equipped_id == hunter_id and slot != self.slot_key:
                return

        # Equip the hunter
        self.player.equipped[self.slot_key] = hunter_id
        await self.player.save()

        # Return to team view
        embed = await self.parent_view.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class WeaponSelectionView(ui.View):
    """View for selecting weapons for a specific hunter"""

    def __init__(self, author: discord.User, player: Player, bot: commands.Bot, slot_key: str, slot_number: int, hunter_id: str, parent_view):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.bot = bot
        self.slot_key = slot_key
        self.slot_number = slot_number
        self.hunter_id = hunter_id
        self.parent_view = parent_view

        # Add weapon selection dropdown (will be populated asynchronously)
        self.weapon_dropdown = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This selection is not for you!", ephemeral=True)
            return False
        return True

    async def get_selection_embed(self):
        """Generate the weapon selection embed and populate dropdown"""
        # Get hunter info
        hunter = await HeroManager.get(self.hunter_id)
        hunter_name = hunter.name if hunter else "Unknown Hunter"

        embed = discord.Embed(
            title=f"🗡️ Weapon Selection - Slot {self.slot_number}",
            description=f"Select a weapon for **{hunter_name}**",
            color=discord.Color.blue()
        )

        # Get available weapons
        if not self.player.inventory:
            embed.add_field(
                name="No Weapons Available",
                value="You don't have any weapons in your inventory.",
                inline=False
            )
            return embed

        # Create weapon options
        weapon_options = []
        equipped_weapons = set()

        # Get currently equipped weapons from all hunters
        for hunter_data in self.player.hunters.values():
            weapon_id = hunter_data.get("weapon")
            if weapon_id:
                equipped_weapons.add(weapon_id)

        # Get current weapon for this hunter
        current_weapon_id = self.player.hunters[self.hunter_id].get("weapon")
        if current_weapon_id:
            equipped_weapons.discard(current_weapon_id)  # Allow re-equipping current weapon

        for weapon_id, weapon_data in self.player.inventory.items():
            weapon = await ItemManager.get(weapon_id)
            if weapon and weapon_id not in equipped_weapons:
                level = weapon_data.get("level", 1)
                tier = weapon_data.get("tier", 0)
                tier_stars = "★" * tier + "☆" * (5 - tier)

                # Check if this is the currently equipped weapon
                is_current = weapon_id == current_weapon_id
                status = " (Currently Equipped)" if is_current else ""

                weapon_options.append(discord.SelectOption(
                    label=f"{weapon.name} (Lv.{level}){status}",
                    description=f"Tier: {tier_stars} | Class: {weapon.classType}",
                    value=weapon_id,
                    emoji=getEmoji(weapon.id) if hasattr(weapon, 'id') else "⚔️"
                ))

        if weapon_options:
            # Add "Remove Weapon" option
            weapon_options.append(discord.SelectOption(
                label="Remove Weapon",
                description="Unequip the current weapon",
                value="remove_weapon",
                emoji="❌"
            ))

            # Limit to 25 options (Discord limit)
            if len(weapon_options) > 25:
                weapon_options = weapon_options[:24]
                weapon_options.append(discord.SelectOption(
                    label="More weapons available...",
                    description="Use /hunter weapon equip for more options",
                    value="more_weapons",
                    emoji="➕"
                ))

            self.weapon_dropdown = WeaponSelectDropdown(
                self.author, self.player, self.slot_key, self.slot_number,
                self.hunter_id, self.parent_view, weapon_options
            )
            self.add_item(self.weapon_dropdown)

            embed.add_field(
                name="Available Weapons",
                value=f"Found {len(weapon_options)-1} available weapons",
                inline=False
            )
        else:
            embed.add_field(
                name="No Available Weapons",
                value="All your weapons are currently equipped or you have no weapons.",
                inline=False
            )

        return embed

    @ui.button(label="Back to Team", style=discord.ButtonStyle.secondary, emoji="↩️")
    async def back_to_team(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        embed = await self.parent_view.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

class WeaponSelectDropdown(ui.Select):
    """Dropdown for selecting weapons"""

    def __init__(self, author: discord.User, player: Player, slot_key: str, slot_number: int, hunter_id: str, parent_view, options: list):
        self.author = author
        self.player = player
        self.slot_key = slot_key
        self.slot_number = slot_number
        self.hunter_id = hunter_id
        self.parent_view = parent_view

        super().__init__(
            placeholder=f"Choose a weapon for Slot {slot_number}...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This selection is not for you!", ephemeral=True)
            return

        await interaction.response.defer()

        selected_weapon_id = self.values[0]

        if selected_weapon_id == "remove_weapon":
            # Remove weapon from hunter
            if self.hunter_id in self.player.hunters:
                self.player.hunters[self.hunter_id]["weapon"] = None
                await self.player.save()

                embed = discord.Embed(
                    title="Weapon Removed",
                    description=f"Weapon removed from Slot {self.slot_number}",
                    color=discord.Color.orange()
                )
                await interaction.edit_original_response(embed=embed, view=None)

                # Wait a moment then return to team view
                import asyncio
                await asyncio.sleep(1)
                embed = await self.parent_view.get_team_embed()
                await interaction.edit_original_response(embed=embed, view=self.parent_view)
                return

        elif selected_weapon_id == "more_weapons":
            embed = discord.Embed(
                title="More Weapons",
                description="Use the command `/hunter weapon equip` for more weapon management options.",
                color=discord.Color.blue()
            )
            await interaction.edit_original_response(embed=embed, view=None)
            return

        # Equip the selected weapon
        if self.hunter_id in self.player.hunters:
            # Remove weapon from any other hunter first
            for other_hunter_data in self.player.hunters.values():
                if other_hunter_data.get("weapon") == selected_weapon_id:
                    other_hunter_data["weapon"] = None

            # Equip weapon to this hunter
            self.player.hunters[self.hunter_id]["weapon"] = selected_weapon_id
            await self.player.save()

            # Get weapon name for confirmation
            weapon = await ItemManager.get(selected_weapon_id)
            weapon_name = weapon.name if weapon else "Unknown Weapon"

            embed = discord.Embed(
                title="Weapon Equipped",
                description=f"**{weapon_name}** equipped to Slot {self.slot_number}",
                color=discord.Color.green()
            )
            if weapon:
                embed.set_thumbnail(url=weapon.image)

            await interaction.edit_original_response(embed=embed, view=None)

            # Wait a moment then return to team view
            import asyncio
            await asyncio.sleep(1)
            embed = await self.parent_view.get_team_embed()
            await interaction.edit_original_response(embed=embed, view=self.parent_view)


class PlayerEquipmentView(ui.View):
    """View for managing player equipment (weapons and shadows)"""

    def __init__(self, author: discord.User, player: Player, parent_view):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.parent_view = parent_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This equipment setup is not for you!", ephemeral=True)
            return False
        return True

    async def get_equipment_embed(self):
        """Generate the player equipment embed"""
        # Refresh player data
        self.player = await Player.get(self.author.id)

        embed = discord.Embed(
            title=f"👤 {self.author.display_name}'s Equipment",
            description="Manage your personal weapons and shadow",
            color=discord.Color.blue()
        )

        # Show current equipment
        weapon1 = self.player.equipped.get("Weapon")
        weapon2 = self.player.equipped.get("Weapon_2")
        shadow = self.player.equipped.get("Shadow")

        # Weapon Slot 1
        if weapon1:
            weapon = await ItemManager.get(weapon1)
            if weapon:
                inventory = self.player.get_inventory()
                w_level = inventory.get(weapon1, {}).get("level", 1)
                w_tier = inventory.get(weapon1, {}).get("tier", 0)
                tier_stars = "★" * w_tier + "☆" * (5 - w_tier)
                weapon1_text = f"{getEmoji(weapon.id)} **{weapon.name}**\n**Level**: {w_level} | **Tier**: {tier_stars}"
            else:
                weapon1_text = "*Invalid weapon*"
        else:
            weapon1_text = "*No weapon equipped*"

        embed.add_field(
            name="⚔️ Weapon Slot 1",
            value=weapon1_text,
            inline=True
        )

        # Weapon Slot 2
        if weapon2:
            weapon = await ItemManager.get(weapon2)
            if weapon:
                inventory = self.player.get_inventory()
                w_level = inventory.get(weapon2, {}).get("level", 1)
                w_tier = inventory.get(weapon2, {}).get("tier", 0)
                tier_stars = "★" * w_tier + "☆" * (5 - w_tier)
                weapon2_text = f"{getEmoji(weapon.id)} **{weapon.name}**\n**Level**: {w_level} | **Tier**: {tier_stars}"
            else:
                weapon2_text = "*Invalid weapon*"
        else:
            weapon2_text = "*No weapon equipped*"

        embed.add_field(
            name="⚔️ Weapon Slot 2",
            value=weapon2_text,
            inline=True
        )

        # Shadow
        if shadow:
            from structure.shadow import Shadow
            shadow_obj = await Shadow.get(shadow)
            if shadow_obj:
                shadows = self.player.get_shadows()
                shadow_data = shadows.get(shadow, {})
                s_level = shadow_data.get('level', 1)
                shadow_text = f"👑 **{shadow_obj.name}**\n**Level**: {s_level}\n**Bonuses**: +{shadow_obj.attack}% ATK, +{shadow_obj.defense}% DEF"
            else:
                shadow_text = "*Invalid shadow*"
        else:
            shadow_text = "*No shadow equipped*"

        embed.add_field(
            name="👑 Equipped Shadow",
            value=shadow_text,
            inline=False
        )

        embed.set_footer(text="Use the buttons below to manage your equipment")
        return embed

    @ui.button(label="Weapon Slot 1", style=discord.ButtonStyle.primary, emoji="⚔️", row=0)
    async def weapon_slot_1(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_weapon_selection(interaction, "Weapon", "Weapon Slot 1")

    @ui.button(label="Weapon Slot 2", style=discord.ButtonStyle.primary, emoji="⚔️", row=0)
    async def weapon_slot_2(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_weapon_selection(interaction, "Weapon_2", "Weapon Slot 2")

    @ui.button(label="Shadow", style=discord.ButtonStyle.secondary, emoji="👑", row=0)
    async def shadow_slot(self, interaction: discord.Interaction, button: ui.Button):
        await self.show_shadow_selection(interaction)

    @ui.button(label="◀️ Back to Team", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_team(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        embed = await self.parent_view.get_team_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)

    async def show_weapon_selection(self, interaction: discord.Interaction, slot_key: str, slot_name: str):
        """Show weapon selection for player slots"""
        await interaction.response.defer()

        embed = discord.Embed(
            title=f"⚔️ Select Weapon for {slot_name}",
            description="Choose a weapon to equip",
            color=discord.Color.green()
        )

        # Get available weapons
        inventory = self.player.get_inventory()
        equipped_weapons = set()

        # Get all equipped weapons to avoid duplicates
        if self.player.equipped.get("Weapon"):
            equipped_weapons.add(self.player.equipped["Weapon"])
        if self.player.equipped.get("Weapon_2"):
            equipped_weapons.add(self.player.equipped["Weapon_2"])

        # Add hunter weapons to equipped set
        for hunter_data in self.player.hunters.values():
            if hunter_data.get("weapon"):
                equipped_weapons.add(hunter_data["weapon"])

        # Remove current weapon from equipped set (allow re-equipping same weapon)
        current_weapon = self.player.equipped.get(slot_key)
        if current_weapon:
            equipped_weapons.discard(current_weapon)

        weapon_options = []

        # Add unequip option
        weapon_options.append(discord.SelectOption(
            label="Unequip Current Weapon",
            value="unequip",
            description="Remove the currently equipped weapon",
            emoji="🔓"
        ))

        for weapon_id, weapon_data in inventory.items():
            if weapon_id not in equipped_weapons and len(weapon_options) < 25:
                weapon = await ItemManager.get(weapon_id)
                if weapon and weapon.type in ["Weapon", "Hero_Weapon"]:
                    level = weapon_data.get("level", 1)
                    tier = weapon_data.get("tier", 0)
                    tier_stars = "★" * tier + "☆" * (5 - tier)

                    is_current = weapon_id == current_weapon
                    status = " (Currently Equipped)" if is_current else ""

                    weapon_options.append(discord.SelectOption(
                        label=f"{weapon.name} (Lv.{level}){status}",
                        description=f"Tier: {tier_stars} | Class: {weapon.classType}",
                        value=weapon_id,
                        emoji=getEmoji(weapon.id) if hasattr(weapon, 'id') else "⚔️"
                    ))

        if len(weapon_options) == 1:  # Only unequip option
            weapon_options.append(discord.SelectOption(
                label="No weapons available",
                value="none",
                description="All weapons are equipped or you have no weapons"
            ))

        # Create dropdown
        dropdown = PlayerWeaponSelectDropdown(self.author, self.player, slot_key, slot_name, self, weapon_options)

        # Create view with dropdown and back button
        view = ui.View(timeout=300)
        view.add_item(dropdown)
        view.add_item(PlayerEquipmentBackButton(self))

        embed.add_field(
            name="Available Weapons",
            value=f"Found {len(weapon_options)-1} available weapons" if len(weapon_options) > 1 else "No weapons available",
            inline=False
        )

        await interaction.edit_original_response(embed=embed, view=view)

    async def show_shadow_selection(self, interaction: discord.Interaction):
        """Show shadow selection for player"""
        await interaction.response.defer()

        embed = discord.Embed(
            title="👑 Select Shadow",
            description="Choose a shadow to equip",
            color=discord.Color.purple()
        )

        # Get available shadows
        shadows = self.player.get_shadows()
        current_shadow = self.player.equipped.get("Shadow")

        shadow_options = []

        # Add unequip option
        shadow_options.append(discord.SelectOption(
            label="Unequip Current Shadow",
            value="unequip",
            description="Remove the currently equipped shadow",
            emoji="🔓"
        ))

        for shadow_id, shadow_data in shadows.items():
            if len(shadow_options) >= 25:
                break

            from structure.shadow import Shadow
            shadow = await Shadow.get(shadow_id)
            if shadow:
                level = shadow_data.get('level', 1)
                is_current = shadow_id == current_shadow
                status = " (Currently Equipped)" if is_current else ""

                shadow_options.append(discord.SelectOption(
                    label=f"{shadow.name} (Lv.{level}){status}",
                    description=f"+{shadow.attack}% ATK, +{shadow.defense}% DEF",
                    value=shadow_id,
                    emoji="👑"
                ))

        if len(shadow_options) == 1:  # Only unequip option
            shadow_options.append(discord.SelectOption(
                label="No shadows available",
                value="none",
                description="You have no shadows unlocked"
            ))

        # Create dropdown
        dropdown = PlayerShadowSelectDropdown(self.author, self.player, self, shadow_options)

        # Create view with dropdown and back button
        view = ui.View(timeout=300)
        view.add_item(dropdown)
        view.add_item(PlayerEquipmentBackButton(self))

        embed.add_field(
            name="Available Shadows",
            value=f"Found {len(shadow_options)-1} available shadows" if len(shadow_options) > 1 else "No shadows available",
            inline=False
        )

        await interaction.edit_original_response(embed=embed, view=view)


class PlayerWeaponSelectDropdown(ui.Select):
    """Dropdown for selecting weapons for player slots"""

    def __init__(self, author: discord.User, player: Player, slot_key: str, slot_name: str, parent_view, options):
        super().__init__(placeholder=f"Choose weapon for {slot_name}...", options=options)
        self.author = author
        self.player = player
        self.slot_key = slot_key
        self.slot_name = slot_name
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not your equipment setup!", ephemeral=True)
            return

        await interaction.response.defer()

        if self.values[0] == "none":
            await interaction.followup.send("❌ No weapons available to equip!", ephemeral=True)
            return

        if self.values[0] == "unequip":
            # Unequip current weapon
            self.player.equipped[self.slot_key] = None
            await self.player.save()

            embed = discord.Embed(
                title="✅ Weapon Unequipped",
                description=f"Weapon has been unequipped from {self.slot_name}!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed, view=None)
        else:
            # Equip new weapon
            weapon_id = self.values[0]
            weapon = await ItemManager.get(weapon_id)

            if weapon:
                # Unequip from other locations first
                if self.player.equipped.get("Weapon") == weapon_id:
                    self.player.equipped["Weapon"] = None
                if self.player.equipped.get("Weapon_2") == weapon_id:
                    self.player.equipped["Weapon_2"] = None

                for hunter_data in self.player.hunters.values():
                    if hunter_data.get("weapon") == weapon_id:
                        hunter_data["weapon"] = None

                # Equip to selected slot
                self.player.equipped[self.slot_key] = weapon_id
                await self.player.save()

                embed = discord.Embed(
                    title="✅ Weapon Equipped",
                    description=f"**{weapon.name}** has been equipped to {self.slot_name}!",
                    color=discord.Color.green()
                )
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.followup.send("❌ Weapon not found!", ephemeral=True)
                return

        # Wait a moment then return to equipment view
        import asyncio
        await asyncio.sleep(1)
        embed = await self.parent_view.get_equipment_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)


class PlayerShadowSelectDropdown(ui.Select):
    """Dropdown for selecting shadows for player"""

    def __init__(self, author: discord.User, player: Player, parent_view, options):
        super().__init__(placeholder="Choose shadow to equip...", options=options)
        self.author = author
        self.player = player
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This is not your equipment setup!", ephemeral=True)
            return

        await interaction.response.defer()

        if self.values[0] == "none":
            await interaction.followup.send("❌ No shadows available to equip!", ephemeral=True)
            return

        if self.values[0] == "unequip":
            # Unequip current shadow
            self.player.equipped["Shadow"] = None
            await self.player.save()

            embed = discord.Embed(
                title="✅ Shadow Unequipped",
                description="Shadow has been unequipped!",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(embed=embed, view=None)
        else:
            # Equip new shadow
            shadow_id = self.values[0]
            from structure.shadow import Shadow
            shadow = await Shadow.get(shadow_id)

            if shadow:
                self.player.equipped["Shadow"] = shadow_id
                await self.player.save()

                embed = discord.Embed(
                    title="✅ Shadow Equipped",
                    description=f"**{shadow.name}** has been equipped!\n\n**Bonuses:**\n⚔️ +{shadow.attack}% Attack\n🛡️ +{shadow.defense}% Defense",
                    color=discord.Color.green()
                )
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.followup.send("❌ Shadow not found!", ephemeral=True)
                return

        # Wait a moment then return to equipment view
        import asyncio
        await asyncio.sleep(1)
        embed = await self.parent_view.get_equipment_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)


class PlayerEquipmentBackButton(ui.Button):
    """Back button for player equipment views"""

    def __init__(self, parent_view):
        super().__init__(label="◀️ Back", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = await self.parent_view.get_equipment_embed()
        await interaction.edit_original_response(embed=embed, view=self.parent_view)


async def setup(bot):
    await bot.add_cog(ProfileCog(bot))