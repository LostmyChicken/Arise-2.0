import asyncio
import time
import discord
from discord.ext import commands
from discord import app_commands, ui
import random
import json
from collections import deque
import logging

# Utility and Structure Imports
from utilis.utilis import PremiumCheck, extractId, getStatHunter, getStatWeapon
from structure.emoji import getClassEmoji, getEmoji
from structure.heroes import HeroManager
from structure.player import Player

# --- Constants & Helper Functions ---

ELEMENTAL_EFFECTIVENESS = {
    "Dark": {"super_effective": ["Light"], "not_very_effective": ["Dark"]},
    "Light": {"super_effective": ["Dark"], "not_very_effective": ["Light"]},
    "Water": {"super_effective": ["Fire"], "not_very_effective": ["Wind"]},
    "Fire": {"super_effective": ["Wind"], "not_very_effective": ["Water"]},
    "Wind": {"super_effective": ["Water"], "not_very_effective": ["Fire"]},
}

def calculate_elemental_multiplier(attacker_element, target_element):
    """Calculates damage multiplier based on elemental advantages."""
    if not attacker_element or not target_element: return 1.0
    attacker_element, target_element = attacker_element.title(), target_element.title()
    if target_element in ELEMENTAL_EFFECTIVENESS.get(attacker_element, {}).get("super_effective", []): return 1.5
    if attacker_element in ELEMENTAL_EFFECTIVENESS.get(target_element, {}).get("super_effective", []): return 0.5
    return 1.0

def pbar(current, max_val, divs=10):
    """Creates a stylish, emoji-based progress bar."""
    if max_val <= 0: return ""
    progress = max(0, min(1, current / max_val))
    fill = {'s': getEmoji("GSTART"), 'm': getEmoji("GMID"), 'e': getEmoji("GEND")}
    empty = {'s': getEmoji("EGSTART"), 'm': getEmoji("EGMIDDLE"), 'e': getEmoji("EGEND")}
    filled_len = round(divs * progress)
    if divs <= 1: return fill['s'] if filled_len > 0 else empty['s']
    bar = [fill['s'] if filled_len > 0 else empty['s']]
    for i in range(1, divs - 1): bar.append(fill['m'] if i < filled_len else empty['m'])
    bar.append(fill['e'] if filled_len == divs else empty['e'])
    return "".join(bar) + f" `[{int(current)}/{int(max_val)}]`"


class DungeonMainView(ui.View):
    """Main dungeon interface with modern UI"""
    
    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.current_mode = "overview"  # overview, select, battle
        self.selected_dungeon = None
        self.update_buttons()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True
    
    async def create_embed(self):
        """Create the main dungeon embed based on current mode"""
        if self.current_mode == "overview":
            return await self.create_overview_embed()
        elif self.current_mode == "select":
            return await self.create_select_embed()
    
    async def create_overview_embed(self):
        """Create dungeon overview embed"""
        # Check if user is admin for testing features
        admin_ids = [1322159704117350400, 1325220545439993888]
        is_admin = self.ctx.author.id in admin_ids

        embed = discord.Embed(
            title=f"{getEmoji('attack')} **DUNGEON SYSTEM** {getEmoji('defense')}",
            description="Challenge dangerous dungeons and earn powerful rewards!" +
                       (f"\n\n{getEmoji('diamond')} **ADMIN MODE**: Cooldown bypass active" if is_admin else ""),
            color=discord.Color.gold() if is_admin else discord.Color.dark_red()
        )
        
        # Define required slots at the top so it's always available
        required_slots = ["Party_1", "Party_2", "Party_3"]

        # Check if player is currently in a dungeon battle
        if self.player.inc:
            embed.add_field(
                name="⚔️ Battle in Progress",
                value="**You're currently in a dungeon battle!**\nUse the **Resume Battle** button to continue\nOr wait for the battle to timeout",
                inline=False
            )
        else:
            # Player readiness check
            equipped_hunters = [self.player.equipped.get(slot) for slot in required_slots]
            ready_hunters = sum(1 for h in equipped_hunters if h)

            if ready_hunters == 3:
                embed.add_field(
                    name="✅ Party Status",
                    value="**Ready for Battle!**\nAll 3 party slots are filled\nYou can enter dungeons",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Party Status",
                    value=f"**Not Ready** ({ready_hunters}/3 hunters)\nEquip hunters in all party slots\nUse `sl team` to manage your party",
                    inline=False
                )

        # Show current party
        party_info = []
        for i, slot in enumerate(required_slots, 1):
            hunter_id = self.player.equipped.get(slot)
            if hunter_id:
                hunter_info = await HeroManager.get(hunter_id)
                hunter_data = self.player.hunters.get(hunter_id, {})
                level = hunter_data.get('level', 1)
                if hunter_info:
                    party_info.append(f"**Slot {i}**: {getEmoji(hunter_id)} {hunter_info.name} (Lv.{level})")
                else:
                    party_info.append(f"**Slot {i}**: ❌ Invalid Hunter")
            else:
                party_info.append(f"**Slot {i}**: *Empty*")
        
        embed.add_field(
            name="👥 Current Party",
            value="\n".join(party_info),
            inline=False
        )
        
        # Dungeon info
        embed.add_field(
            name="🎯 Dungeon Features",
            value="• **Multi-tier battles** with increasing difficulty\n• **Elemental advantages** matter in combat\n• **Rich rewards** including gold, items, and XP\n• **Strategic gameplay** with hunter selection",
            inline=False
        )
        
        embed.set_footer(text="Use the buttons below to select and enter dungeons")
        embed.set_thumbnail(url="https://files.catbox.moe/jvxvcr.png")
        return embed
    
    async def create_select_embed(self):
        """Create dungeon selection embed"""
        embed = discord.Embed(
            title="🎯 **SELECT DUNGEON** 🎯",
            description="Choose your challenge level and prepare for battle!",
            color=discord.Color.orange()
        )
        
        # Available dungeons (matching actual enemy tiers)
        dungeons = [
            {"name": "Goblin Cave", "difficulty": "Easy", "tiers": 4, "emoji": getEmoji('attack'), "rewards": "Basic"},
            {"name": "Shadow Fortress", "difficulty": "Medium", "tiers": 4, "emoji": getEmoji('defense'), "rewards": "Good"},
            {"name": "Dragon's Lair", "difficulty": "Hard", "tiers": 4, "emoji": getEmoji('diamond'), "rewards": "Excellent"},
            {"name": "Void Temple", "difficulty": "Extreme", "tiers": 4, "emoji": getEmoji('SSR'), "rewards": "Legendary"}
        ]
        
        dungeon_list = []
        for dungeon in dungeons:
            dungeon_list.append(
                f"{dungeon['emoji']} **{dungeon['name']}**\n"
                f"   📊 Difficulty: {dungeon['difficulty']}\n"
                f"   🏆 Tiers: {dungeon['tiers']}\n"
                f"   💎 Rewards: {dungeon['rewards']}"
            )
        
        embed.add_field(
            name="🗺️ Available Dungeons",
            value="\n\n".join(dungeon_list),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Battle System",
            value="• Each dungeon has multiple tiers of enemies\n• Use elemental advantages for bonus damage\n• Manage your hunters' HP carefully\n• Defeat all tiers to claim victory!",
            inline=False
        )
        
        embed.set_footer(text="Select a dungeon to begin your adventure!")
        return embed
    
    def update_buttons(self):
        """Update button states based on current mode"""
        self.clear_items()

        if self.current_mode == "overview":
            # Check if player is in battle
            if self.player.inc:
                self.add_item(ResumeBattleButton())
                self.add_item(DungeonInfoButton())
            else:
                # Check if player is ready
                required_slots = ["Party_1", "Party_2", "Party_3"]
                equipped_hunters = [self.player.equipped.get(slot) for slot in required_slots]
                ready_hunters = sum(1 for h in equipped_hunters if h)

                if ready_hunters == 3:
                    self.add_item(SelectDungeonButton())
                else:
                    self.add_item(SetupPartyButton())

                self.add_item(DungeonInfoButton())

        elif self.current_mode == "select":
            self.add_item(EasyDungeonButton())
            self.add_item(MediumDungeonButton())
            self.add_item(HardDungeonButton())
            self.add_item(ExtremeDungeonButton())
            self.add_item(BackToOverviewButton())
    
    async def update_view(self, interaction):
        """Update the view and embed"""
        # Refresh player data
        self.player = await Player.get(self.ctx.author.id)
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# Button classes for the dungeon system
class SelectDungeonButton(ui.Button):
    def __init__(self):
        super().__init__(label="🎯 Select Dungeon", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "select"
        await self.view.update_view(interaction)


class ResumeBattleButton(ui.Button):
    def __init__(self):
        super().__init__(label="⚔️ Resume Battle", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "⚔️ **Battle Resume**: Your ongoing dungeon battle should be visible in this channel.\n"
            "If you can't see it, the battle may have timed out. Try starting a new dungeon.",
            ephemeral=True
        )


class SetupPartyButton(ui.Button):
    def __init__(self):
        super().__init__(label="👥 Setup Party", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "💡 **Setup Party**: Use `sl team` to manage your party and equip hunters in all 3 slots!",
            ephemeral=True
        )


class DungeonInfoButton(ui.Button):
    def __init__(self):
        super().__init__(label="ℹ️ Info", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ℹ️ **DUNGEON INFORMATION** ℹ️",
            description="Everything you need to know about dungeons!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎮 How to Play",
            value="1. Equip 3 hunters in your party slots\n2. Select a dungeon difficulty\n3. Battle through multiple tiers\n4. Use elemental advantages\n5. Claim your rewards!",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Elemental System",
            value="• **Dark** > Light\n• **Light** > Dark\n• **Water** > Fire\n• **Fire** > Wind\n• **Wind** > Water",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Rewards",
            value="• Gold and experience points\n• Rare items and equipment\n• Hunter upgrade materials\n• Achievement progress",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class BackToOverviewButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔙 Back", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        self.view.current_mode = "overview"
        await self.view.update_view(interaction)


class EasyDungeonButton(ui.Button):
    def __init__(self):
        super().__init__(label="🟢 Goblin Cave", style=discord.ButtonStyle.success)
    
    async def callback(self, interaction: discord.Interaction):
        await self.start_dungeon(interaction, "easy")


class MediumDungeonButton(ui.Button):
    def __init__(self):
        super().__init__(label="🟡 Shadow Fortress", style=discord.ButtonStyle.primary)
    
    async def callback(self, interaction: discord.Interaction):
        await self.start_dungeon(interaction, "medium")


class HardDungeonButton(ui.Button):
    def __init__(self):
        super().__init__(label="🔴 Dragon's Lair", style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction):
        await self.start_dungeon(interaction, "hard")


class ExtremeDungeonButton(ui.Button):
    def __init__(self):
        super().__init__(label="🟣 Void Temple", style=discord.ButtonStyle.secondary)
    
    async def callback(self, interaction: discord.Interaction):
        await self.start_dungeon(interaction, "extreme")


# Add the start_dungeon method to all dungeon buttons
async def start_dungeon(self, interaction, difficulty):
    """Start a dungeon with the specified difficulty"""
    await interaction.response.defer()
    
    # Import the original dungeon battle system
    from commands.dungeons import DungeonBattleView
    
    player = await Player.get(interaction.user.id)

    # Check if player is already in combat or trade
    if player.inc or player.trade:
        embed = discord.Embed(
            title="❌ Already Busy",
            description="You're already in a battle or trade! Finish your current activity first.",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed, view=None)
        return

    # Check dungeon cooldown (same as original system) - ADMIN BYPASS FOR TESTING
    admin_ids = [1322159704117350400, 1325220545439993888]  # Admin IDs
    is_admin = interaction.user.id in admin_ids

    if not is_admin:  # Skip cooldown check for admins
        cooldown_seconds = 1800  # 30 minutes
        adjusted_cooldown = int(cooldown_seconds * PremiumCheck(player))

        on_cooldown = False
        remaining = 0
        if player.dungeon:
            try:
                last_dungeon_time = float(player.dungeon)
                if (time.time() - last_dungeon_time) < adjusted_cooldown:
                    on_cooldown = True
                    remaining = adjusted_cooldown - (time.time() - last_dungeon_time)
            except (ValueError, TypeError):
                player.dungeon = None
                await player.save()

        if on_cooldown:
            minutes, seconds = divmod(int(remaining), 60)
            embed = discord.Embed(
                title="⏱️ Cooldown",
                description=f"Your party is resting. Next dungeon in **{minutes}m {seconds}s**.",
                color=discord.Color.blue()
            )
            await interaction.edit_original_response(embed=embed, view=None)
            return
    else:
        # Admin bypass message
        print(f"🔧 ADMIN BYPASS: {interaction.user.display_name} ({interaction.user.id}) bypassed dungeon cooldown")

    # Set player in combat and update dungeon timestamp
    player.inc = True
    player.dungeon = time.time()
    await player.save()
    
    # Load enemies using the same logic as original dungeon system
    try:
        with open("enemy.json", "r") as f:  # Use enemy.json in root, not data/enemy.json
            all_enemies = json.load(f)
    except FileNotFoundError:
        embed = discord.Embed(
            title="❌ Error",
            description="Enemy data not found. Please contact an admin.",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed, view=None)
        player.inc = False
        await player.save()
        return

    # Use the exact same enemy processing as original dungeon system
    if difficulty == "easy":
        # Easy: Use original dungeon logic (tiers 1-4)
        enemies_by_tier = {1: [], 2: [], 3: [], 4: []}
        for enemy in all_enemies:
            try:
                enemy_tier = int(enemy.get('tier', 0))
                if enemy_tier in enemies_by_tier:
                    enemy['attack'] = int(enemy.get('attack', 10))
                    enemy['defense'] = int(enemy.get('defense', 10))
                    enemy['hp'] = int(enemy.get('hp', 100))
                    enemies_by_tier[enemy_tier].append(enemy)
            except (ValueError, TypeError):
                continue
        enemy_run_list = [random.choice(enemies_by_tier[tier]) for tier in sorted(enemies_by_tier.keys()) if enemies_by_tier[tier]]
    else:
        # For other difficulties, use extended tiers
        difficulty_tiers = {
            "medium": [2, 3, 4, 5],
            "hard": [3, 4, 5, 6],
            "extreme": [4, 5, 6, 7]
        }

        selected_tiers = difficulty_tiers.get(difficulty, [1, 2, 3, 4])
        enemies_by_tier = {tier: [] for tier in selected_tiers}

        for enemy in all_enemies:
            try:
                enemy_tier = int(enemy.get('tier', 0))
                if enemy_tier in enemies_by_tier:
                    enemy['attack'] = int(enemy.get('attack', 10))
                    enemy['defense'] = int(enemy.get('defense', 10))
                    enemy['hp'] = int(enemy.get('hp', 100))
                    enemies_by_tier[enemy_tier].append(enemy)
            except (ValueError, TypeError):
                continue

        enemy_run_list = [random.choice(enemies_by_tier[tier]) for tier in sorted(enemies_by_tier.keys()) if enemies_by_tier[tier]]
    
    if not enemy_run_list:
        embed = discord.Embed(
            title="❌ Error",
            description="No enemies available for this difficulty.",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed, view=None)
        player.inc = False
        await player.save()
        return
    
    # Prepare hunters using exact same logic as original dungeon system
    required_slots = ["Party_1", "Party_2", "Party_3"]
    hunters = []

    for slot in required_slots:
        hunter_id = player.equipped[slot]
        hunter_data = player.hunters.get(hunter_id)
        hunter_info = await HeroManager.get(hunter_id)
        stat = await getStatHunter(hunter_id, hunter_data['level'])

        # Add weapon stats if equipped (using same logic as original)
        if (weapon_id := hunter_data.get("weapon")) and (weapon_id in player.inventory):
            weapon_level = player.inventory[weapon_id].get("level", 1)  # Safe get
            weapon_stat = await getStatWeapon(weapon_id, weapon_level)
            if weapon_stat:
                stat.attack += weapon_stat.get("attack", 0)
                stat.defense += weapon_stat.get("defense", 0)
                stat.hp += weapon_stat.get("hp", 0)

        hunters.append({
            "id": hunter_id, "name": hunter_info.name, "attack": stat.attack,
            "defense": stat.defense, "hp": stat.hp, "max_hp": stat.hp,
            "dmg": 0, "image": hunter_info.image, "element": hunter_info.classType
        })
    
    # Start the battle
    battle_view = DungeonBattleView(self.view.ctx, hunters, enemy_run_list)
    await battle_view.start_dungeon()
    
    # Close the selection interface
    embed = discord.Embed(
        title="⚔️ **DUNGEON STARTED** ⚔️",
        description=f"You have entered the **{difficulty.title()}** dungeon!\nGood luck, hunter!",
        color=discord.Color.green()
    )
    await interaction.edit_original_response(embed=embed, view=None)

# Bind the method to all dungeon button classes
EasyDungeonButton.start_dungeon = start_dungeon
MediumDungeonButton.start_dungeon = start_dungeon
HardDungeonButton.start_dungeon = start_dungeon
ExtremeDungeonButton.start_dungeon = start_dungeon
