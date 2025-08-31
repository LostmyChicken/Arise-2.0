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
from structure.skills import SkillManager
from structure.elements import ElementalSystem, ElementalCombat, Element

# --- Constants & Helper Functions ---

ELEMENTAL_EFFECTIVENESS = {
    "Dark": {"super_effective": ["Light"], "not_very_effective": ["Dark"]},
    "Light": {"super_effective": ["Dark"], "not_very_effective": ["Light"]},
    "Water": {"super_effective": ["Fire"], "not_very_effective": ["Wind"]},
    "Fire": {"super_effective": ["Wind"], "not_very_effective": ["Water"]},
    "Wind": {"super_effective": ["Water"], "not_very_effective": ["Fire"]},
}

def calculate_elemental_multiplier(attacker_element, target_element):
    """Calculates damage multiplier based on elemental advantages using new system."""
    try:
        # Convert string elements to Element enum
        attacker_elem = ElementalSystem.parse_element_from_string(attacker_element)
        defender_elem = ElementalSystem.parse_element_from_string(target_element)

        # Use the new elemental system
        multiplier = ElementalSystem.calculate_damage_multiplier(attacker_elem, defender_elem)
        return multiplier
    except:
        # Fallback to original system if conversion fails
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


# --- Main Battle View ---

class DungeonBattleView(ui.View):
    def __init__(self, ctx, hunters, enemies):
        super().__init__(timeout=300.0) # 5-minute timeout for the whole dungeon
        self.ctx = ctx
        self.user_id = ctx.author.id
        self.hunters = hunters
        self.enemies = enemies
        self.current_tier = 0
        self.battle_log = deque(maxlen=4)
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your dungeon run!", ephemeral=True)
            return False
        return True

    async def start_dungeon(self):
        """Initializes and starts the dungeon battle."""
        self.battle_log.append("The dungeon entrance creaks open...")
        embed = await self._create_battle_embed()
        self._update_buttons()
        self.message = await self.ctx.send(embed=embed, view=self)

    def _update_buttons(self):
        """Dynamically creates a button for each alive hunter."""
        self.clear_items()
        for index, hunter in enumerate(self.hunters):
            button = ui.Button(
                label=hunter['name'],
                style=discord.ButtonStyle.secondary,
                custom_id=str(index),
                emoji=getEmoji(hunter['id']),
                disabled=hunter['hp'] <= 0
            )
            button.callback = self._hunter_attack_callback
            self.add_item(button)

    async def _hunter_attack_callback(self, interaction: discord.Interaction):
        """Handles the logic when a hunter's attack button is pressed."""
        await interaction.response.defer()
        
        for item in self.children: item.disabled = True
        if self.message: await self.message.edit(view=self)

        hunter_index = int(interaction.data["custom_id"])
        hunter = self.hunters[hunter_index]
        enemy = self.enemies[self.current_tier]

        # Player's Turn - Calculate elemental damage
        multiplier = calculate_elemental_multiplier(hunter["element"], enemy["element"])
        base_dmg = round((hunter['attack'] / enemy["defense"]) * 1000)
        dmg = round(base_dmg * multiplier)
        enemy["hp"] = max(0, enemy["hp"] - dmg)
        hunter['dmg'] += dmg

        # Get elemental emojis and effectiveness text
        try:
            hunter_elem = ElementalSystem.parse_element_from_string(hunter["element"])
            enemy_elem = ElementalSystem.parse_element_from_string(enemy["element"])
            hunter_emoji = ElementalSystem.get_element_emoji(hunter_elem)
            enemy_emoji = ElementalSystem.get_element_emoji(enemy_elem)
            effectiveness_text = ElementalSystem.get_effectiveness_text(multiplier)
            effectiveness_emoji = ElementalSystem.get_effectiveness_emoji(multiplier)
        except:
            hunter_emoji = "⚔️"
            enemy_emoji = "🛡️"
            effectiveness_text = ""
            effectiveness_emoji = ""

        # Create enhanced attack message
        attack_message = f"⚔️ {hunter_emoji} **{hunter['name']}** attacks {enemy_emoji} **{enemy['name']}** for `{dmg}` damage!"
        if effectiveness_text:
            attack_message += f" {effectiveness_emoji} {effectiveness_text}"

        self.battle_log.append(attack_message)

        if self.message: await self.message.edit(embed=await self._create_battle_embed())
        await asyncio.sleep(1.5)

        if enemy["hp"] <= 0:
            self.battle_log.append(f"✅ **{enemy['name']}** has been defeated!")
            self.current_tier += 1
            if self.current_tier >= len(self.enemies):
                await self._end_battle(victory=True)
                return
            else:
                self.battle_log.append(f"➡️ Moving to Tier {self.current_tier + 1}...")
                if self.message: await self.message.edit(embed=await self._create_battle_embed())
                await asyncio.sleep(2)
        else: # Enemy's Turn - Boss attacks ONE random hunter (not AOE unless specified)
            target_hunter = random.choice([h for h in self.hunters if h["hp"] > 0])

            # Calculate elemental damage with new system
            multiplier = calculate_elemental_multiplier(enemy["element"], target_hunter["element"])
            base_damage = round((enemy['attack'] / target_hunter["defense"]) * 1500)
            boss_damage = round(base_damage * multiplier)
            target_hunter["hp"] = max(0, target_hunter["hp"] - boss_damage)

            # Get elemental emojis and effectiveness text
            try:
                enemy_elem = ElementalSystem.parse_element_from_string(enemy["element"])
                hunter_elem = ElementalSystem.parse_element_from_string(target_hunter["element"])
                enemy_emoji = ElementalSystem.get_element_emoji(enemy_elem)
                hunter_emoji = ElementalSystem.get_element_emoji(hunter_elem)
                effectiveness_text = ElementalSystem.get_effectiveness_text(multiplier)
                effectiveness_emoji = ElementalSystem.get_effectiveness_emoji(multiplier)
            except:
                enemy_emoji = "⚔️"
                hunter_emoji = "🛡️"
                effectiveness_text = ""
                effectiveness_emoji = ""

            # Create enhanced battle message
            battle_message = f"🩸 {enemy_emoji} **{enemy['name']}** attacks {hunter_emoji} **{target_hunter['name']}** for `{boss_damage}` damage!"
            if effectiveness_text:
                battle_message += f" {effectiveness_emoji} {effectiveness_text}"

            self.battle_log.append(battle_message)

        if all(h["hp"] <= 0 for h in self.hunters):
            await self._end_battle(victory=False)
            return

        self._update_buttons()
        if self.message: await self.message.edit(embed=await self._create_battle_embed(), view=self)

    async def _create_battle_embed(self) -> discord.Embed:
        enemy = self.enemies[self.current_tier]
        if "max_hp" not in enemy: enemy["max_hp"] = enemy["hp"]

        enemy_health_bar = pbar(enemy["hp"], enemy["max_hp"], 12)
        log_text = "\n".join(f"> {log}" for log in self.battle_log)
        
        embed = discord.Embed(title=f"Dungeon Tier {self.current_tier + 1} of {len(self.enemies)}", color=0x2b2d31)
        embed.set_author(name=f"{self.ctx.author.display_name}'s Run")
        
        embed.description = (
            f"### {getClassEmoji(enemy['element'])} {enemy['name']}\n"
            f"**ATK:** `{enemy['attack']}` | **DEF:** `{enemy['defense']}`\n{enemy_health_bar}"
        )
        embed.set_thumbnail(url=enemy.get('image'))
        embed.add_field(name="Battle Log", value=log_text or "No actions yet.", inline=False)
        
        party_display = []
        for hunter in self.hunters:
            status_emoji = "❤️" if hunter['hp'] > 0 else "💀"
            party_display.append(f"{status_emoji} **{hunter['name']}**: `{hunter['hp']}/{hunter['max_hp']}`")
        embed.add_field(name="Your Party", value="\n".join(party_display), inline=False)

        embed.set_footer(text="Click a hunter's button below to attack!")
        return embed

    async def _end_battle(self, victory: bool):
        self.stop()
        player = await Player.get(self.user_id)
        if player:
            player.inc = False
            player.mIncrease("dungeon")
            for hunter in self.hunters:
                player.hunter_add_xp(extractId(hunter['name']), round(hunter['dmg'] / 10))
            await player.save()

        total_damage = sum(h["dmg"] for h in self.hunters) or 1
        star_hunter = max(self.hunters, key=lambda h: h["dmg"])

        title = "⚔️ Dungeon Cleared! ⚔️" if victory else "💀 Dungeon Failed 💀"
        color = discord.Color.gold() if victory else discord.Color.red()
        
        results_embed = discord.Embed(title=title, color=color)
        results_embed.set_author(name=f"{self.ctx.author.display_name}'s Results")
        results_embed.add_field(
            name="Summary", 
            value=f"Your party cleared **{self.current_tier}** out of **{len(self.enemies)}** tiers.", 
            inline=False
        )

        for hunter in self.hunters:
            status_icon = "🏆" if hunter == star_hunter else ("✅" if hunter['hp'] > 0 else "☠️")
            dmg_percent = (hunter['dmg'] / total_damage) * 100
            results_embed.add_field(
                name=f"{status_icon} {hunter['name']}",
                value=f"**Damage Dealt**: `{hunter['dmg']:,}` ({dmg_percent:.1f}%)\n**XP Gained**: `{round(hunter['dmg'] / 10):,}`",
                inline=True
            )
        # Set thumbnail with validation
        from utilis.utilis import safe_set_thumbnail
        thumbnail_url = star_hunter.get('image')
        safe_set_thumbnail(results_embed, thumbnail_url)
        if self.message: await self.message.edit(embed=results_embed, view=None)

    async def on_timeout(self):
        if not self.is_finished():
            self.battle_log.append("The party hesitated for too long and was overwhelmed.")
            await self._end_battle(victory=False)

class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="dungeon", help="Enter the dungeon system with modern interface.")
    async def dungeon(self, ctx: commands.Context):
        """Modern dungeon interface with interactive UI"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Import the new dungeon view
        from commands.dungeon_new import DungeonMainView

        view = DungeonMainView(ctx, player)
        embed = await view.create_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)



async def setup(bot):
    await bot.add_cog(Dungeon(bot))