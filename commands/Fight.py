import string
import time
import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands
import logging
import hashlib
import random
from typing import Optional
from structure.emoji import getEmoji
from collections import deque
from structure.playerId import PlayerIdManager
from utilis.utilis import PremiumCheck, extractId, getStatWeapon
from structure.skills import SkillManager
from structure.player import Player
from structure.emoji import getEmoji
from structure.BossDrop import pbar
from structure.pvp_system import PvPFightRequest, PvPFightRequestView
import asyncio

class FightHandleAI:
    def __init__(self, bot, user_id):
        self.bot = bot
        self.user_id = user_id
        self.active_battles = set()
        self.move_log = deque(maxlen=4)
        self.fight_id = hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]
        self.fight_over = False # State flag to prevent spam
        self.p_name = None; self.o_name = None
        self.p_atk = 0; self.o_atk = 0
        self.p_def = 0; self.o_def = 0
        self.p_hp = 0; self.o_hp = 0
        self.p_mhp = 0; self.o_mhp = 0
        self.p_mp = 0; self.o_mp = 0
        self.p_skills = {}; self.o_skills = {}
        self.message = None
        self.opponent_id = None
        self.skill_cooldowns = {}  # Track ultimate skill cooldowns
        self.skill_charges = {}    # Track ultimate skill charges (need 3 turns to charge)

    async def initialize(self, message_url: str):
        player = await Player.get(self.user_id)
        self.p_name = await self.bot.fetch_user(self.user_id)
        self.p_atk, self.p_def, self.p_hp, self.p_mp = player.attack, player.defense, player.hp, player.mp
        self.p_skills = player.skills
        self.p_mhp = player.hp

        # Initialize skill charges for ultimate skills (start at 0, need 3 to use)
        from structure.battle_skills import BattleSkillIntegration
        self.skill_charges = await BattleSkillIntegration.initialize_skill_charges(self.p_skills or {})

        self.opponent_id = await self._get_random_opponent()
        opponent = await Player.get(self.opponent_id) if self.opponent_id else None

        if not opponent:
            await self._create_fallback_ai()
        else:
            self.o_name = await self.bot.fetch_user(self.opponent_id)
            self.o_atk, self.o_def, self.o_hp, self.o_mp = opponent.attack, opponent.defense, opponent.hp, opponent.mp
            self.o_skills = opponent.skills.copy() if opponent.skills else {}
            self.o_mhp = opponent.hp
            await self._add_equipment_stats(player, opponent)

        self.p_mhp = self.p_hp
        self.o_mhp = self.o_hp
        self.message = await self._extract_message(message_url)

    async def _get_random_opponent(self) -> Optional[int]:
        try:
            all_ids = await PlayerIdManager.get_all_ids()
            valid_opponents = [oid for oid in all_ids if oid != self.user_id and oid not in self.active_battles]
            return random.choice(valid_opponents) if valid_opponents else None
        except Exception as e:
            logging.error(f"Error finding opponent: {e}")
            return None

    async def _create_fallback_ai(self):
        self.o_name = "AI Opponent"
        self.o_atk, self.o_def = random.randint(50, 200), random.randint(30, 150)
        self.o_hp = random.randint(100, 500)
        self.o_mhp = self.o_hp
        self.o_mp = random.randint(50, 150)
        self.o_skills = {"punch": {"level": 1}}

    async def _add_equipment_stats(self, player, opponent):
        for p, role in [(player, 'p'), (opponent, 'o')]:
            for slot in ["Weapon", "Weapon_2"]:
                if weapon_id := p.equipped.get(slot):
                    if weapon_id in p.inventory:
                        weapon_level = p.inventory[weapon_id].get("level", 1)
                        stats = await getStatWeapon(weapon_id, weapon_level)
                        if stats:
                            if role == 'p':
                                self.p_atk += stats['attack']; self.p_def += stats['defense']; self.p_hp += stats['hp']; self.p_mp += stats['mp']
                            else:
                                self.o_atk += stats['attack']; self.o_def += stats['defense']; self.o_hp += stats['hp']; self.o_mp += stats['mp']

    async def _extract_message(self, message_url: str):
        try:
            parts = message_url.split('/')
            guild_id, channel_id, message_id = int(parts[4]), int(parts[5]), int(parts[6])
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            return await channel.fetch_message(message_id)
        except (IndexError, ValueError, discord.NotFound, discord.Forbidden):
            logging.error(f"Failed to extract message from URL: {message_url}")
            return None

    async def start_turn(self):
        embed = self._create_battle_embed("Choose your action. You have 60 seconds to make a move.")
        
        # Always include punch as basic attack
        skill_options = [{"name": "👊 Punch", "description": "Basic Attack | 100% Damage | 0 MP | Always Available", "value": "punch"}]

        player = await Player.get(self.user_id)
        if player and player.skills:
            for skill_id, data in player.skills.items():
                # Get skill with player's current level applied
                try:
                    if skill := await SkillManager.get_skill_with_player_level(skill_id, str(self.user_id)):
                        # Check cooldown for ultimate skills
                        cooldown_remaining = self.skill_cooldowns.get(skill_id, 0)
                        is_on_cooldown = cooldown_remaining > 0

                        # Check charge status for ultimate skills
                        if skill.skill_type.value == "Ultimate":
                            from structure.battle_skills import BattleSkillIntegration
                            charge_check = await BattleSkillIntegration.is_ultimate_skill_ready(
                                skill_id, self.user_id, self.skill_charges, self.skill_cooldowns
                            )
                            can_use_ultimate = charge_check["ready"]
                            ultimate_reason = charge_check["reason"]
                        else:
                            can_use_ultimate = True
                            ultimate_reason = ""

                        # Check MP availability
                        can_use_mp = self.p_mp >= skill.mp_cost
                        can_use = can_use_mp and not is_on_cooldown and can_use_ultimate

                        # Create status indicator
                        if is_on_cooldown:
                            status = f"🕒{cooldown_remaining}"
                        elif skill.skill_type.value == "Ultimate" and not can_use_ultimate:
                            if "Charging" in ultimate_reason:
                                current_charge = self.skill_charges.get(skill_id, 0)
                                status = f"⚡{current_charge}/3"
                            else:
                                status = "❌"
                        elif not can_use_mp:
                            status = "❌"
                        else:
                            status = "✅"

                        # Add skill type emoji
                        skill_emoji = "💥" if skill.skill_type.value == "Ultimate" else "⚡"

                        # Create description with cooldown and charge info
                        description = f"Lvl {skill.level} | {status} {skill.damage}% DMG | {skill.mp_cost} MP"
                        if is_on_cooldown:
                            description += f" | Cooldown: {cooldown_remaining} turns"
                        elif skill.skill_type.value == "Ultimate" and not can_use_ultimate and "Charging" in ultimate_reason:
                            current_charge = self.skill_charges.get(skill_id, 0)
                            description += f" | Charging: {current_charge}/3 turns"

                        skill_options.append({
                            "name": f"{skill_emoji} {skill.name}",
                            "description": description,
                            "value": skill_id
                        })
                except Exception as e:
                    # Skip invalid skills
                    continue

        # Ensure we always have at least one option (Punch)
        if not skill_options:
            skill_options = [{"name": "Punch", "description": "Basic Attack | 100% Damage | 0 MP", "value": "punch"}]

        # Limit to 25 options (Discord limit)
        skill_options = skill_options[:25]

        options = [discord.SelectOption(label=s["name"], description=s["description"], value=s["value"]) for s in skill_options]
        select_menu = discord.ui.Select(placeholder="Choose your action...", options=options)
        select_menu.callback = self.handle_player_action
        view = discord.ui.View(timeout=60)
        view.add_item(select_menu)
        view.on_timeout = self.on_timeout
        
        await self.message.edit(content="`☑️ Matchmaking Successful!`", embed=embed, view=view)

    def _create_battle_embed(self, footer_text=""):
        p_bar = pbar(self.p_hp, self.p_mhp, 8)
        o_bar = pbar(self.o_hp, self.o_mhp, 8)
        
        embed = discord.Embed(title=f"Fight ID: {self.fight_id}", description="\n".join(self.move_log), color=discord.Color.dark_grey())
        embed.add_field(
            name=f"{self.p_name.display_name}",
            value=f"{getEmoji('attack')} {self.p_atk} | {getEmoji('defense')} {self.p_def}\n"
                  f"**MP:** `{self.p_mp}`\n{p_bar}",
            inline=True
        )
        embed.add_field(
            name=f"{getattr(self.o_name, 'display_name', self.o_name)}",
            value=f"{getEmoji('attack')} {self.o_atk} | {getEmoji('defense')} {self.o_def}\n"
                  f"**MP:** `{self.o_mp}`\n{o_bar}",
            inline=True
        )
        if footer_text:
            embed.set_footer(text=footer_text)
        return embed

    async def handle_player_action(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await interaction.response.defer()

        action = interaction.data['values'][0]

        # Update skill cooldowns at start of turn
        self.skill_cooldowns = {skill_id: turns - 1 for skill_id, turns in self.skill_cooldowns.items() if turns > 1}

        # Update skill charges at start of turn
        from structure.battle_skills import BattleSkillIntegration
        self.skill_charges = await BattleSkillIntegration.update_skill_charges(self.skill_charges, self.p_skills or {})

        if action == "punch":
            # Basic punch attack with precision/evasion
            from structure.battle_skills import BattleSkillIntegration

            # Get player precision (need to fetch from database)
            player = await Player.get(self.user_id)
            player_precision = player.precision if player else 10

            # AI opponent has evasion based on defense (simple formula)
            ai_evasion = max(5, self.o_def // 10)  # 1 evasion per 10 defense, minimum 5

            hit_result = BattleSkillIntegration.calculate_hit_chance(player_precision, ai_evasion)

            if hit_result["hit"]:
                damage = max(1, round(self.p_atk * (100 / (100 + self.o_def if self.o_def > 0 else 1))))
                self.o_hp = max(0, self.o_hp - damage)
                self.move_log.append(f"> {self.p_name.display_name} punched for **{damage}** damage! ({hit_result['hit_chance']}% hit chance)")
            else:
                self.move_log.append(f"> {self.p_name.display_name}'s punch **MISSED**! {hit_result['miss_reason']} ({hit_result['hit_chance']}% hit chance)")
        else:
            # Get skill with player's current level applied
            skill = await SkillManager.get_skill_with_player_level(action, str(self.user_id))

            # Check if skill exists and is usable
            if not skill:
                await interaction.followup.send("Skill not found.", ephemeral=True)
                return

            # Check cooldown
            if self.skill_cooldowns.get(action, 0) > 0:
                await interaction.followup.send(f"Skill is on cooldown for {self.skill_cooldowns[action]} more turns.", ephemeral=True)
                return

            # Check charge for ultimate skills
            if skill.skill_type.value == "Ultimate":
                from structure.battle_skills import BattleSkillIntegration
                charge_check = await BattleSkillIntegration.is_ultimate_skill_ready(
                    action, self.user_id, self.skill_charges, self.skill_cooldowns
                )
                if not charge_check["ready"]:
                    await interaction.followup.send(f"❌ {charge_check['reason']}", ephemeral=True)
                    return

            # Check MP
            if self.p_mp < skill.mp_cost:
                await interaction.followup.send("Not enough MP to use this skill.", ephemeral=True)
                return

            # Calculate damage with precision/evasion system
            from structure.battle_skills import BattleSkillIntegration

            # Get player precision
            player = await Player.get(self.user_id)
            player_precision = player.precision if player else 10

            # AI opponent evasion
            ai_evasion = max(5, self.o_def // 10)

            # Calculate damage with hit chance
            damage_result = await BattleSkillIntegration.calculate_skill_damage(
                self.user_id, action, self.p_atk, self.o_def, player_precision, ai_evasion
            )

            if damage_result and damage_result["hit"]:
                damage = damage_result["damage"]
                self.o_hp = max(0, self.o_hp - damage)
                self.p_mp -= skill.mp_cost

                # Apply skill effects
                if "effects" in damage_result:
                    effects = damage_result["effects"]

                    # Apply healing
                    if effects["heal_amount"] > 0:
                        self.p_hp = min(self.p_mhp, self.p_hp + effects["heal_amount"])
                        self.move_log.append(f"  💚 Healed for {effects['heal_amount']} HP!")

                    # Apply life steal
                    if effects["life_steal_amount"] > 0:
                        life_steal_heal = max(1, round(damage * effects["life_steal_amount"] / 100))
                        self.p_hp = min(self.p_mhp, self.p_hp + life_steal_heal)
                        self.move_log.append(f"  🩸 Life steal healed {life_steal_heal} HP!")

                # Apply cooldown and reset charge for ultimate skills
                if skill.skill_type.value == "Ultimate":
                    self.skill_cooldowns[action] = 3
                    self.skill_charges[action] = 0  # Reset charge after use

                # Create damage message with effects
                damage_msg = f"> {self.p_name.display_name} used **{skill.name} (Lv.{skill.level})** for **{damage}** damage! ({damage_result['hit_chance']}% hit chance)"
                if "effects" in damage_result and damage_result["effects"]["special_effects"]:
                    damage_msg += f" | {', '.join(damage_result['effects']['special_effects'])}"
                self.move_log.append(damage_msg)
            else:
                # Skill missed - still consume MP and apply cooldown
                self.p_mp -= skill.mp_cost

                if skill.skill_type.value == "Ultimate":
                    self.skill_cooldowns[action] = 3
                    self.skill_charges[action] = 0  # Reset charge after use (even if missed)

                miss_reason = damage_result["miss_reason"] if damage_result else "Attack failed!"
                self.move_log.append(f"> {self.p_name.display_name}'s **{skill.name}** **MISSED**! {miss_reason} ({damage_result['hit_chance'] if damage_result else 50}% hit chance)")
        
        await self._process_turn_end(interaction)

    async def ai_turn(self):
        await asyncio.sleep(1.5)
        
        skill_options = [s_id for s_id in self.o_skills if (skill := await SkillManager.get(s_id)) and self.o_mp >= skill.mp_cost]
        
        if skill_options and random.random() > 0.3:
            skill_id = random.choice(skill_options)
            skill = await SkillManager.get(skill_id)
            # Calculate AI skill damage with proper scaling
            skill_multiplier = skill.damage / 100.0
            defense_reduction = 100.0 / (100.0 + max(0, self.p_def))
            damage = max(1, round(self.o_atk * skill_multiplier * defense_reduction))
            self.p_hp = max(0, self.p_hp - damage)
            self.o_mp -= skill.mp_cost
            self.move_log.append(f"> {getattr(self.o_name, 'display_name', self.o_name)} used **{skill.name}** for **{damage}** damage!")
        else:
            damage = max(1, round(self.o_atk * (100 / (100 + self.p_def if self.p_def > 0 else 1))))
            self.p_hp = max(0, self.p_hp - damage)
            self.move_log.append(f"> {getattr(self.o_name, 'display_name', self.o_name)} punched for **{damage}** damage!")
        
        await self._process_turn_end()

    async def _process_turn_end(self, interaction: Optional[discord.Interaction] = None):
        if self.p_hp <= 0 or self.o_hp <= 0:
            await self.end_fight()
            return

        if interaction:
            await self.message.edit(embed=self._create_battle_embed("Opponent is making a move..."), view=None)
            await self.ai_turn()
        else:
            await self.start_turn()

    async def end_fight(self, timed_out=False):
        if self.fight_over:
            return
        self.fight_over = True

        winner = None
        if timed_out:
            winner = self.o_name
            self.move_log.append("> You took too long to act and forfeited the match.")
        elif self.o_hp <= 0:
            winner = self.p_name
        elif self.p_hp <= 0:
            winner = self.o_name

        await self.message.edit(embed=self._create_battle_embed("The fight has concluded."), view=None)

        xp = random.randint(100, 300); gold = random.randint(1000, 2000)
        player = await Player.get(self.user_id)
        
        if winner == self.p_name:
            embed = discord.Embed(title=f"{getEmoji('tick')} Victory!", description=f"You defeated {getattr(self.o_name, 'display_name', self.o_name)}!", color=discord.Color.green())
            embed.add_field(name="🎁 Rewards", value=f"{getEmoji('xp')} +{xp} XP\n{getEmoji('gold')} +{gold} Gold")
            await player.add_xp(self.bot, xp, self.message.channel)
            player.gold += gold

            # Track combat victory achievement
            try:
                from structure.achievement_tracker import AchievementTracker
                await AchievementTracker.track_combat_victory(player, "player")
                await AchievementTracker.track_wealth(player)
            except Exception as e:
                logging.error(f"Error tracking combat achievements: {e}")
        else:
            embed = discord.Embed(title=f"{getEmoji('negative')} Defeat!", description=f"You were defeated by {getattr(self.o_name, 'display_name', self.o_name)}.", color=discord.Color.red())

        await self.message.channel.send(embed=embed)
        
        player.inc = False
        await player.save()

    async def on_timeout(self):
        await self.end_fight(timed_out=True)

class FightCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='fight', aliases=['f'], help="Fight against an AI opponent or challenge another player")
    async def fight(self, ctx: commands.Context, target: discord.Member = None):
        """Enhanced fight command supporting both NPC and PvP battles"""
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.reply(embed=discord.Embed(title="Not Started", description="You haven't started yet. Use `sl start`.", color=discord.Color.red()))
            return
        if player.inc:
            await ctx.reply(embed=discord.Embed(title="Busy", description="You are already in another command.", color=discord.Color.orange()))
            return

        if target is not None:
            # PvP fight request
            if target.id == ctx.author.id:
                await ctx.reply(embed=discord.Embed(title="Invalid Target", description="You can't fight yourself!", color=discord.Color.red()))
                return

            if target.bot:
                await ctx.reply(embed=discord.Embed(title="Invalid Target", description="You can't fight bots!", color=discord.Color.red()))
                return

            # Check if target player exists
            target_player = await Player.get(target.id)
            if not target_player:
                await ctx.reply(embed=discord.Embed(title="Player Not Found", description=f"{target.display_name} needs to create a character first!", color=discord.Color.red()))
                return

            if target_player.inc:
                await ctx.reply(embed=discord.Embed(title="Target Busy", description=f"{target.display_name} is already in combat!", color=discord.Color.red()))
                return

            # Create PvP fight request
            fight_request = PvPFightRequest(ctx.author.id, target.id, self.bot)
            embed = await fight_request.create_request_embed()
            view = PvPFightRequestView(fight_request)

            # Send the fight request
            message = await ctx.reply(embed=embed, view=view)
            view.message = message  # Store message reference for timeout handling
            return

        cooldown = int(180 * PremiumCheck(player))
        if player.fight and time.time() - float(player.fight) < cooldown:
            remaining = cooldown - (time.time() - float(player.fight))
            minutes, seconds = divmod(int(remaining), 60)
            embed = discord.Embed(title="On Cooldown", description=f"You can fight again in **{minutes}m {seconds}s**.", color=discord.Color.orange())
            await ctx.reply(embed=embed)
            return

        player.inc = True
        player.fight = time.time()
        await player.save()

        msg = None
        try:
            embed = discord.Embed(title="Fight Initiated!", description=f"{getEmoji('searching')} Finding an opponent...", color=discord.Color.blue())
            msg = await ctx.reply(embed=embed, mention_author=False)
            
            fight_handle = FightHandleAI(self.bot, ctx.author.id)
            await fight_handle.initialize(generate_message_url(msg))
            
            if not fight_handle.opponent_id:
                await msg.edit(content="⚠️ No suitable opponents found. Engaging a generic AI.")
            
            await fight_handle.start_turn()
        except Exception as e:
            if msg:
                await msg.edit(content=None, embed=discord.Embed(title="Error", description="An error occurred while starting the fight.", color=discord.Color.red()), view=None)
            logging.error(f"Error in fight command: {e}", exc_info=True)
            # Ensure player's status is reset on error
            player.inc = False
            await player.save()

def generate_message_url(message):
    return f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

async def setup(bot):
    await bot.add_cog(FightCog(bot))