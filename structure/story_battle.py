"""
Interactive Story Battle System for Solo Leveling
Uses the exact same battle mechanics as the gate system
"""
import discord
import asyncio
import random
from typing import Dict, List, Optional, Tuple, Any
from structure.player import Player
from structure.emoji import getEmoji
from utilis.utilis import getStatWeapon
from structure.skills import SkillManager
from utilis.utilis import create_embed, INFO_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR

def pbar(current, max_val, divs=10):
    """Progress bar function copied from gates.py"""
    if max_val <= 0: return "`[----------------]`"
    percent = max(0, min(1, current / max_val))
    filled = int(percent * divs)
    return f"`[{'█' * filled}{' ' * (divs - filled)}]` {int(current)}/{int(max_val)}"

class StoryBattleView(discord.ui.View):
    """Story battle view using gate battle mechanics"""

    def __init__(self, bot, player_id, enemy_data, story_session, battle_modifiers=None):
        super().__init__(timeout=180)
        self.bot = bot
        self.player_id = player_id
        self.enemy = enemy_data
        self.story_session = story_session
        self.battle_modifiers = battle_modifiers or {}
        self.player_stats = {}
        self.enemy_hp = enemy_data['hp']
        self.enemy_mhp = enemy_data['hp']
        self.log = []
        self.turn = "player"
        self.battle_won = False

    async def start(self, interaction: discord.Interaction):
        """Initialize and start the battle"""
        player = await Player.get(str(self.player_id))

        # Initialize player stats (copied from gate battle system)
        self.player_stats = {
            "name": interaction.user.display_name,
            "hp": player.hp,
            "mhp": player.hp,
            "mp": player.mp,
            "atk": player.attack,
            "def": player.defense,
            "skills": player.skills,
            "last_action_time": 0
        }

        # Apply weapon stats (copied from gate battle system)
        for slot in ["Weapon", "Weapon_2"]:
            weapon_id = player.equipped.get(slot)
            if weapon_id and weapon_id in player.inventory:
                weapon_stats = await getStatWeapon(weapon_id, player.inventory[weapon_id].get("level", 1))
                if weapon_stats:
                    self.player_stats['atk'] += weapon_stats.get('attack', 0)
                    self.player_stats['def'] += weapon_stats.get('defense', 0)
                    self.player_stats['hp'] += weapon_stats.get('hp', 0)
                    self.player_stats['mp'] += weapon_stats.get('mp', 0)

        self.player_stats['mhp'] = self.player_stats['hp']

        # Apply battle modifiers from story choices
        if 'damage_bonus' in self.battle_modifiers:
            self.player_stats['atk'] = int(self.player_stats['atk'] * (1 + self.battle_modifiers['damage_bonus']))
        if 'defense_bonus' in self.battle_modifiers:
            self.player_stats['def'] = int(self.player_stats['def'] * (1 + self.battle_modifiers['defense_bonus']))

        await self.update_battle_ui(interaction, first_time=True)

    async def update_battle_ui(self, interaction: discord.Interaction, first_time=False):
        """Update the battle UI (copied from gate battle system)"""
        embed = self.create_embed()
        self.clear_items()

        if self.player_stats['hp'] > 0 and self.enemy_hp > 0:
            await self.add_action_buttons()

        try:
            if first_time:
                await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
            else:
                await interaction.edit_original_response(embed=embed, view=self)
        except discord.InteractionResponded:
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)

    def create_embed(self):
        """Create battle embed (copied from gate battle system)"""
        embed = discord.Embed(
            title="📖 Story Battle!",
            description=f"> Defeat the **{self.enemy['name']}** to continue the story.",
            color=discord.Color.red()
        )

        # Add enemy image if available
        if 'image' in self.enemy and self.enemy['image']:
            embed.set_image(url=self.enemy['image'])

        # Health bars (copied from gate battle system)
        player_hp_bar = pbar(self.player_stats['hp'], self.player_stats['mhp'])
        enemy_hp_bar = pbar(self.enemy_hp, self.enemy_mhp)

        embed.add_field(
            name=f"{self.player_stats['name']}",
            value=f"HP: {self.player_stats['hp']}/{self.player_stats['mhp']}\n{player_hp_bar}\nMP: {self.player_stats['mp']}",
            inline=True
        )
        embed.add_field(
            name=f"{self.enemy['name']}",
            value=f"HP: {self.enemy_hp}/{self.enemy_mhp}\n{enemy_hp_bar}",
            inline=True
        )

        # Battle log (copied from gate battle system)
        if self.log:
            embed.add_field(name="Battle Log", value="\n".join(self.log[-3:]), inline=False)

        # Battle result messages (copied from gate battle system)
        if self.player_stats['hp'] <= 0:
            embed.description = f"You have been defeated by the {self.enemy['name']}!"
            embed.color = discord.Color.dark_red()
        elif self.enemy_hp <= 0:
            embed.description = f"You have defeated the {self.enemy['name']}!"
            embed.color = discord.Color.green()

        return embed

    async def add_action_buttons(self):
        """Add action buttons (copied from gate battle system)"""
        # Punch button (basic attack)
        punch_button = discord.ui.Button(
            label="Punch",
            style=discord.ButtonStyle.primary,
            disabled=(self.turn != 'player')
        )
        punch_button.callback = self.punch
        self.add_item(punch_button)

        # Skills dropdown (copied from gate battle system) - limit to 25 options
        if self.player_stats['skills']:
            options = []
            skill_count = 0
            for skill_id, skill_data in self.player_stats['skills'].items():
                if skill_count >= 25:  # Discord limit
                    break

                # Get skill with player's current level applied
                skill = await SkillManager.get_skill_with_player_level(skill_id, str(self.player_id))
                if skill and self.player_stats['mp'] >= skill.mp_cost:
                    options.append(discord.SelectOption(
                        label=f"{skill.name} Lv.{skill.level} (MP: {skill.mp_cost}, DMG: {skill.damage}%)",
                        value=skill_id,
                        emoji="⚡"
                    ))
                    skill_count += 1

            if options:
                skill_select = discord.ui.Select(
                    placeholder="Use a skill...",
                    options=options,
                    disabled=(self.turn != 'player')
                )
                skill_select.callback = self.use_skill
                self.add_item(skill_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user can interact (copied from gate battle system)"""
        if interaction.user.id != int(self.player_id):
            await interaction.response.send_message("This is not your battle.", ephemeral=True)
            return False
        if self.turn != 'player':
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return False
        return True

    async def punch(self, interaction: discord.Interaction):
        """Basic attack (copied from gate battle system)"""
        await interaction.response.defer()

        # Balanced damage calculation with random variance (copied from gate battle system)
        base_damage = max(1, self.player_stats['atk'] - self.enemy.get('defense', 0))
        damage = random.randint(max(1, base_damage - 5), base_damage + 10)
        self.enemy_hp -= damage
        self.log.append(f"{getEmoji('attack')} You punched and dealt {damage} damage.")
        self.turn = "enemy"
        await self.check_battle_status(interaction)

    async def use_skill(self, interaction: discord.Interaction):
        """Use skill (copied from gate battle system)"""
        await interaction.response.defer()
        skill_id = interaction.data['values'][0]

        # Get skill with player's current level applied
        skill = await SkillManager.get_skill_with_player_level(skill_id, str(interaction.user.id))

        if not skill:
            await interaction.followup.send("❌ **Skill not found.**", ephemeral=True)
            return

        self.player_stats['mp'] -= skill.mp_cost

        # Balanced skill damage with random variance (copied from gate battle system)
        base_damage = max(1, int((self.player_stats['atk'] * (skill.damage / 100)) - self.enemy.get('defense', 0)))
        damage = random.randint(max(1, base_damage - 3), base_damage + 8)
        self.enemy_hp -= damage
        self.log.append(f"✨ You used {skill.name} (Lv.{skill.level}) and dealt {damage} damage.")
        self.turn = "enemy"
        await self.check_battle_status(interaction)

    async def check_battle_status(self, interaction: discord.Interaction):
        """Check battle status (copied from gate battle system)"""
        if self.enemy_hp <= 0:
            self.enemy_hp = 0
            await self.end_battle(interaction, True)
            return

        await self.update_battle_ui(interaction)
        await asyncio.sleep(1.5)
        await self.enemy_turn(interaction)

        if self.player_stats['hp'] <= 0:
            self.player_stats['hp'] = 0
            await self.end_battle(interaction, False)
            return

        self.turn = "player"
        await self.update_battle_ui(interaction)

    async def enemy_turn(self, interaction: discord.Interaction):
        """Enemy turn (copied from gate battle system)"""
        # Balanced enemy damage (not overpowered)
        base_damage = max(1, self.enemy.get('attack', 10) - self.player_stats['def'])
        # Reduce enemy damage to be more balanced
        balanced_damage = max(1, int(base_damage * 0.7))  # 30% damage reduction
        damage = random.randint(max(1, balanced_damage - 3), balanced_damage + 5)
        self.player_stats['hp'] -= damage
        self.log.append(f"🩸 The enemy attacked and dealt {damage} damage.")

    async def end_battle(self, interaction: discord.Interaction, won: bool):
        """End battle (adapted from gate battle system)"""
        self.battle_won = won

        if won:
            self.log.append(f"🎉 Victory! You defeated the {self.enemy['name']}!")
        else:
            self.log.append(f"💀 Defeat... You were defeated by the {self.enemy['name']}.")

        # Save player's current HP to database
        await self.save_player_state()

        await self.update_battle_ui(interaction)
        await asyncio.sleep(3)

        # Continue story after battle
        if self.story_session:
            await self.story_session.handle_battle_result(won)

    async def save_player_state(self):
        """Save the player's current battle state to the database"""
        try:
            from structure.player import Player
            player = await Player.get(str(self.player_id))

            if player:
                # Update player's HP and MP based on battle results
                player.hp = max(1, self.player_stats['hp'])  # Ensure HP doesn't go below 1
                player.mp = max(0, self.player_stats['mp'])
                await player.save()

        except Exception as e:
            print(f"Error saving player state after story battle: {e}")

class StoryBattleSystem:
    """Simple wrapper to start story battles using gate battle mechanics"""

    def __init__(self, player_id: str, ctx, bot):
        self.player_id = player_id
        self.ctx = ctx
        self.bot = bot

    async def start_battle(self, enemies_data: List[Dict], battle_description: str = None, battle_modifiers: Dict = None) -> bool:
        """Start a story battle using gate battle mechanics"""
        try:
            if not enemies_data:
                return False

            # Use the first enemy (story battles are typically 1v1)
            enemy_data = enemies_data[0]

            # Create battle view using gate battle mechanics
            battle_view = StoryBattleView(
                bot=self.bot,
                player_id=self.player_id,
                enemy_data=enemy_data,
                story_session=None,  # Will be set by story session
                battle_modifiers=battle_modifiers
            )

            # Create initial interaction for the battle
            embed = discord.Embed(
                title="⚔️ Story Battle Beginning!",
                description=battle_description or f"You face the **{enemy_data['name']}** in combat!",
                color=ERROR_COLOR
            )

            # Send initial message and start battle
            message = await self.ctx.send(embed=embed)

            # Create a fake interaction for the battle system
            # This is a workaround since we don't have a real interaction
            class FakeInteraction:
                def __init__(self, user, channel):
                    self.user = user
                    self.channel = channel
                    self.response = self
                    self.message = message

                async def send_message(self, *args, **kwargs):
                    return await self.channel.send(*args, **kwargs)

                async def edit_original_response(self, *args, **kwargs):
                    return await message.edit(*args, **kwargs)

                async def defer(self):
                    pass

            fake_interaction = FakeInteraction(self.ctx.author, self.ctx.channel)
            await battle_view.start(fake_interaction)

            return True

        except Exception as e:
            print(f"Error starting story battle: {e}")
            return False
