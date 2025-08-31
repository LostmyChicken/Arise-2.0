"""
Enhanced PvP Fight System with Accept/Reject and Turn-Based Combat
"""

import discord
from discord.ext import commands
import asyncio
import random
from collections import deque
from structure.player import Player
from structure.skills import SkillManager
from structure.emoji import getEmoji
from structure.BossDrop import pbar


class PvPFightRequest:
    """Handles PvP fight requests with accept/reject system"""
    
    def __init__(self, challenger_id: int, target_id: int, bot: commands.Bot):
        self.challenger_id = challenger_id
        self.target_id = target_id
        self.bot = bot
        self.accepted = False
        self.expired = False
        
    async def create_request_embed(self):
        """Create the fight request embed"""
        challenger = await self.bot.fetch_user(self.challenger_id)
        target = await self.bot.fetch_user(self.target_id)
        
        embed = discord.Embed(
            title="⚔️ **PvP FIGHT REQUEST**",
            description=f"**{challenger.display_name}** has challenged **{target.display_name}** to a duel!",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="🎯 **Challenge Details**",
            value=f"**Challenger**: {challenger.mention}\n**Target**: {target.mention}\n**Type**: Turn-based PvP Combat",
            inline=False
        )
        
        embed.add_field(
            name="⏰ **Time Limit**",
            value="You have **60 seconds** to accept or reject this challenge!",
            inline=False
        )
        
        embed.set_footer(text="💡 Click Accept to start the fight or Reject to decline")
        return embed


class PvPFightRequestView(discord.ui.View):
    """UI for accepting/rejecting PvP fight requests"""
    
    def __init__(self, fight_request: PvPFightRequest):
        super().__init__(timeout=60)
        self.fight_request = fight_request
        
    @discord.ui.button(label="✅ Accept Challenge", style=discord.ButtonStyle.success)
    async def accept_fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.fight_request.target_id:
            await interaction.response.send_message("❌ Only the challenged player can accept this fight!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Mark as accepted
        self.fight_request.accepted = True
        
        # Create acceptance embed
        challenger = await self.fight_request.bot.fetch_user(self.fight_request.challenger_id)
        target = await self.fight_request.bot.fetch_user(self.fight_request.target_id)
        
        embed = discord.Embed(
            title="⚔️ **FIGHT ACCEPTED!**",
            description=f"**{target.display_name}** accepted the challenge!\n\n🚀 **Starting PvP battle...**",
            color=discord.Color.green()
        )
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
            
        await interaction.edit_original_response(embed=embed, view=self)
        
        # Start the PvP fight
        pvp_fight = PvPFightHandler(
            self.fight_request.bot,
            self.fight_request.challenger_id,
            self.fight_request.target_id
        )
        await pvp_fight.initialize(interaction.message)
        
    @discord.ui.button(label="❌ Reject Challenge", style=discord.ButtonStyle.danger)
    async def reject_fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.fight_request.target_id:
            await interaction.response.send_message("❌ Only the challenged player can reject this fight!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        # Create rejection embed
        challenger = await self.fight_request.bot.fetch_user(self.fight_request.challenger_id)
        target = await self.fight_request.bot.fetch_user(self.fight_request.target_id)
        
        embed = discord.Embed(
            title="❌ **FIGHT REJECTED**",
            description=f"**{target.display_name}** declined the challenge from **{challenger.display_name}**.",
            color=discord.Color.red()
        )
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
            
        await interaction.edit_original_response(embed=embed, view=self)
        self.stop()
        
    async def on_timeout(self):
        """Handle timeout"""
        self.fight_request.expired = True
        
        # Create timeout embed
        embed = discord.Embed(
            title="⏰ **FIGHT REQUEST EXPIRED**",
            description="The fight request has expired due to no response.",
            color=discord.Color.dark_grey()
        )
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
            
        # Try to edit the message if possible
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(embed=embed, view=self)
        except:
            pass


class PvPFightHandler:
    """Handles turn-based PvP combat between two players"""
    
    def __init__(self, bot: commands.Bot, player1_id: int, player2_id: int):
        self.bot = bot
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.current_turn = player1_id  # Player 1 goes first
        self.fight_over = False
        self.message = None
        
        # Player stats
        self.p1_name = None
        self.p2_name = None
        self.p1_hp = 0
        self.p1_max_hp = 0
        self.p1_mp = 0
        self.p1_atk = 0
        self.p1_def = 0
        self.p1_skills = {}
        
        self.p2_hp = 0
        self.p2_max_hp = 0
        self.p2_mp = 0
        self.p2_atk = 0
        self.p2_def = 0
        self.p2_skills = {}
        
        # Combat tracking
        self.move_log = deque(maxlen=4)
        self.p1_skill_cooldowns = {}
        self.p2_skill_cooldowns = {}
        self.p1_skill_charges = {}
        self.p2_skill_charges = {}
        
    async def initialize(self, message: discord.Message):
        """Initialize the PvP fight"""
        self.message = message
        
        # Load player data
        player1 = await Player.get(self.player1_id)
        player2 = await Player.get(self.player2_id)
        
        if not player1 or not player2:
            await message.edit(content="❌ **Error**: One or both players not found!", embed=None, view=None)
            return
            
        # Get player names
        self.p1_name = await self.bot.fetch_user(self.player1_id)
        self.p2_name = await self.bot.fetch_user(self.player2_id)
        
        # Initialize player 1 stats
        self.p1_hp = self.p1_max_hp = player1.hp
        self.p1_mp = player1.mp
        self.p1_atk = player1.attack
        self.p1_def = player1.defense
        self.p1_precision = player1.precision
        self.p1_skills = player1.skills or {}

        # Initialize player 2 stats
        self.p2_hp = self.p2_max_hp = player2.hp
        self.p2_mp = player2.mp
        self.p2_atk = player2.attack
        self.p2_def = player2.defense
        self.p2_precision = player2.precision
        self.p2_skills = player2.skills or {}

        # Initialize skill charges for ultimate skills
        from structure.battle_skills import BattleSkillIntegration
        self.p1_skill_charges = await BattleSkillIntegration.initialize_skill_charges(self.p1_skills)
        self.p2_skill_charges = await BattleSkillIntegration.initialize_skill_charges(self.p2_skills)

        # Start the first turn
        await self.start_turn()
        
    async def start_turn(self):
        """Start a player's turn"""
        if self.fight_over:
            return
            
        # Check for victory conditions
        if self.p1_hp <= 0:
            await self.end_fight(winner_id=self.player2_id)
            return
        elif self.p2_hp <= 0:
            await self.end_fight(winner_id=self.player1_id)
            return
            
        # Create battle embed
        embed = self.create_battle_embed()
        
        # Get current player info
        current_player = self.p1_name if self.current_turn == self.player1_id else self.p2_name
        current_mp = self.p1_mp if self.current_turn == self.player1_id else self.p2_mp
        current_skills = self.p1_skills if self.current_turn == self.player1_id else self.p2_skills
        current_cooldowns = self.p1_skill_cooldowns if self.current_turn == self.player1_id else self.p2_skill_cooldowns
        current_charges = self.p1_skill_charges if self.current_turn == self.player1_id else self.p2_skill_charges
        
        # Create skill options
        skill_options = [{"name": "👊 Punch", "description": "Basic Attack | 100% Damage | 0 MP | Always Available", "value": "punch"}]
        
        # Add player skills with cooldown info
        for skill_id in current_skills:
            try:
                skill = await SkillManager.get_skill_with_player_level(skill_id, str(self.current_turn))
                if skill:
                    cooldown_remaining = current_cooldowns.get(skill_id, 0)
                    is_on_cooldown = cooldown_remaining > 0
                    can_use_mp = current_mp >= skill.mp_cost

                    # Check charge status for ultimate skills
                    if skill.skill_type.value == "Ultimate":
                        from structure.battle_skills import BattleSkillIntegration
                        charge_check = await BattleSkillIntegration.can_use_ultimate_skill(
                            skill_id, self.current_turn, current_charges, current_cooldowns
                        )
                        can_use_ultimate = charge_check["can_use"]
                        ultimate_reason = charge_check["reason"]
                    else:
                        can_use_ultimate = True
                        ultimate_reason = ""

                    can_use = can_use_mp and not is_on_cooldown and can_use_ultimate

                    # Status indicator
                    if is_on_cooldown:
                        status = f"🕒{cooldown_remaining}"
                    elif skill.skill_type.value == "Ultimate" and not can_use_ultimate:
                        if "Charging" in ultimate_reason:
                            current_charge = current_charges.get(skill_id, 0)
                            status = f"⚡{current_charge}/3"
                        else:
                            status = "❌"
                    elif not can_use_mp:
                        status = "❌"
                    else:
                        status = "✅"
                    
                    skill_emoji = "💥" if skill.skill_type.value == "Ultimate" else "⚡"
                    description = f"Lvl {skill.level} | {status} {skill.damage}% DMG | {skill.mp_cost} MP"
                    if is_on_cooldown:
                        description += f" | Cooldown: {cooldown_remaining} turns"
                    elif skill.skill_type.value == "Ultimate" and not can_use_ultimate and "Charging" in ultimate_reason:
                        current_charge = current_charges.get(skill_id, 0)
                        description += f" | Charging: {current_charge}/3 turns"
                    
                    skill_options.append({
                        "name": f"{skill_emoji} {skill.name}",
                        "description": description,
                        "value": skill_id
                    })
            except:
                continue
                
        # Create UI
        options = [discord.SelectOption(label=s["name"], description=s["description"], value=s["value"]) for s in skill_options[:25]]
        select_menu = discord.ui.Select(placeholder=f"{current_player.display_name}'s turn - Choose your action...", options=options)
        select_menu.callback = self.handle_player_action
        
        view = discord.ui.View(timeout=60)
        view.add_item(select_menu)
        view.on_timeout = self.on_timeout
        
        embed.set_footer(text=f"🎯 {current_player.display_name}'s turn! Choose your action within 60 seconds.")
        
        await self.message.edit(embed=embed, view=view)
        
    def create_battle_embed(self):
        """Create the battle status embed"""
        embed = discord.Embed(
            title="⚔️ **PvP BATTLE IN PROGRESS**",
            description=f"**{self.p1_name.display_name}** vs **{self.p2_name.display_name}**",
            color=discord.Color.red()
        )
        
        # Player 1 stats
        p1_bar = pbar(self.p1_hp, self.p1_max_hp, 8)
        embed.add_field(
            name=f"🔵 {self.p1_name.display_name}",
            value=f"{getEmoji('attack')} {self.p1_atk} | {getEmoji('defense')} {self.p1_def}\n**MP:** `{self.p1_mp}`\n{p1_bar}",
            inline=True
        )
        
        # Player 2 stats  
        p2_bar = pbar(self.p2_hp, self.p2_max_hp, 8)
        embed.add_field(
            name=f"🔴 {self.p2_name.display_name}",
            value=f"{getEmoji('attack')} {self.p2_atk} | {getEmoji('defense')} {self.p2_def}\n**MP:** `{self.p2_mp}`\n{p2_bar}",
            inline=True
        )
        
        # Move log
        if self.move_log:
            embed.add_field(
                name="📜 **Recent Actions**",
                value="\n".join(list(self.move_log)),
                inline=False
            )
            
        return embed
        
    async def handle_player_action(self, interaction: discord.Interaction):
        """Handle player action selection"""
        if interaction.user.id != self.current_turn:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
            
        await interaction.response.defer()

        action = interaction.data['values'][0]

        # Update skill charges at start of turn
        from structure.battle_skills import BattleSkillIntegration
        if self.current_turn == self.player1_id:
            self.p1_skill_charges = await BattleSkillIntegration.update_skill_charges(self.p1_skill_charges, self.p1_skills)
        else:
            self.p2_skill_charges = await BattleSkillIntegration.update_skill_charges(self.p2_skill_charges, self.p2_skills)
        
        # Get current player stats
        if self.current_turn == self.player1_id:
            attacker_hp, attacker_mp, attacker_atk, attacker_precision = self.p1_hp, self.p1_mp, self.p1_atk, self.p1_precision
            defender_hp, defender_def, defender_precision = self.p2_hp, self.p2_def, self.p2_precision
            attacker_name = self.p1_name
            cooldowns = self.p1_skill_cooldowns
        else:
            attacker_hp, attacker_mp, attacker_atk, attacker_precision = self.p2_hp, self.p2_mp, self.p2_atk, self.p2_precision
            defender_hp, defender_def, defender_precision = self.p1_hp, self.p1_def, self.p1_precision
            attacker_name = self.p2_name
            cooldowns = self.p2_skill_cooldowns
            
        # Update cooldowns
        for skill_id in list(cooldowns.keys()):
            cooldowns[skill_id] -= 1
            if cooldowns[skill_id] <= 0:
                del cooldowns[skill_id]
                
        # Process action
        if action == "punch":
            # Basic punch with precision/evasion
            from structure.battle_skills import BattleSkillIntegration

            hit_result = BattleSkillIntegration.calculate_hit_chance(attacker_precision, defender_precision)

            if hit_result["hit"]:
                damage = max(1, round(attacker_atk * (100 / (100 + defender_def))))
                self.move_log.append(f"👊 {attacker_name.display_name} punched for **{damage}** damage! ({hit_result['hit_chance']}% hit chance)")
            else:
                damage = 0
                self.move_log.append(f"👊 {attacker_name.display_name}'s punch **MISSED**! {hit_result['miss_reason']} ({hit_result['hit_chance']}% hit chance)")
        else:
            # Handle skill usage with precision
            skill = await SkillManager.get_skill_with_player_level(action, str(self.current_turn))
            if not skill:
                await interaction.followup.send("❌ Skill not found!", ephemeral=True)
                return

            if cooldowns.get(action, 0) > 0:
                await interaction.followup.send(f"❌ Skill on cooldown for {cooldowns[action]} turns!", ephemeral=True)
                return

            # Check charge for ultimate skills
            if skill.skill_type.value == "Ultimate":
                current_charges = self.p1_skill_charges if self.current_turn == self.player1_id else self.p2_skill_charges
                charge_check = await BattleSkillIntegration.can_use_ultimate_skill(
                    action, self.current_turn, current_charges, cooldowns
                )
                if not charge_check["can_use"]:
                    await interaction.followup.send(f"❌ {charge_check['reason']}", ephemeral=True)
                    return

            if attacker_mp < skill.mp_cost:
                await interaction.followup.send("❌ Not enough MP!", ephemeral=True)
                return

            # Calculate skill damage with precision/evasion
            from structure.battle_skills import BattleSkillIntegration

            damage_result = await BattleSkillIntegration.calculate_skill_damage(
                self.current_turn, action, attacker_atk, defender_def, attacker_precision, defender_precision
            )

            # Apply MP cost and cooldown regardless of hit/miss
            if self.current_turn == self.player1_id:
                self.p1_mp -= skill.mp_cost
            else:
                self.p2_mp -= skill.mp_cost

            if skill.skill_type.value == "Ultimate":
                cooldowns[action] = 3
                # Reset charge after use
                if self.current_turn == self.player1_id:
                    self.p1_skill_charges[action] = 0
                else:
                    self.p2_skill_charges[action] = 0

            if damage_result and damage_result["hit"]:
                damage = damage_result["damage"]

                # Apply skill effects
                if "effects" in damage_result:
                    effects = damage_result["effects"]

                    # Apply healing to attacker
                    if effects["heal_amount"] > 0:
                        if self.current_turn == self.player1_id:
                            self.p1_hp = min(self.p1_max_hp, self.p1_hp + effects["heal_amount"])
                        else:
                            self.p2_hp = min(self.p2_max_hp, self.p2_hp + effects["heal_amount"])
                        self.move_log.append(f"  💚 {attacker_name.display_name} healed for {effects['heal_amount']} HP!")

                    # Apply life steal
                    if effects["life_steal_amount"] > 0:
                        life_steal_heal = max(1, round(damage * effects["life_steal_amount"] / 100))
                        if self.current_turn == self.player1_id:
                            self.p1_hp = min(self.p1_max_hp, self.p1_hp + life_steal_heal)
                        else:
                            self.p2_hp = min(self.p2_max_hp, self.p2_hp + life_steal_heal)
                        self.move_log.append(f"  🩸 {attacker_name.display_name} life steal healed {life_steal_heal} HP!")

                # Create damage message with effects
                damage_msg = f"⚡ {attacker_name.display_name} used **{skill.name}** for **{damage}** damage! ({damage_result['hit_chance']}% hit chance)"
                if "effects" in damage_result and damage_result["effects"]["special_effects"]:
                    damage_msg += f" | {', '.join(damage_result['effects']['special_effects'])}"
                self.move_log.append(damage_msg)
            else:
                damage = 0
                miss_reason = damage_result["miss_reason"] if damage_result else "Attack failed!"
                self.move_log.append(f"⚡ {attacker_name.display_name}'s **{skill.name}** **MISSED**! {miss_reason} ({damage_result['hit_chance'] if damage_result else 50}% hit chance)")
            
        # Apply damage
        if self.current_turn == self.player1_id:
            self.p2_hp = max(0, self.p2_hp - damage)
        else:
            self.p1_hp = max(0, self.p1_hp - damage)
            
        # Switch turns
        self.current_turn = self.player2_id if self.current_turn == self.player1_id else self.player1_id
        
        # Continue to next turn
        await self.start_turn()
        
    async def end_fight(self, winner_id: int):
        """End the PvP fight"""
        self.fight_over = True
        
        winner = await self.bot.fetch_user(winner_id)
        loser = await self.bot.fetch_user(self.player1_id if winner_id == self.player2_id else self.player2_id)
        
        embed = discord.Embed(
            title="🏆 **PvP BATTLE COMPLETE!**",
            description=f"**{winner.display_name}** defeated **{loser.display_name}**!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🎉 **Victory!**",
            value=f"**Winner**: {winner.mention}\n**Loser**: {loser.mention}",
            inline=False
        )
        
        if self.move_log:
            embed.add_field(
                name="📜 **Final Actions**",
                value="\n".join(list(self.move_log)),
                inline=False
            )
            
        await self.message.edit(embed=embed, view=None)
        
    async def on_timeout(self):
        """Handle turn timeout"""
        if not self.fight_over:
            current_player = self.p1_name if self.current_turn == self.player1_id else self.p2_name
            
            embed = discord.Embed(
                title="⏰ **FIGHT TIMEOUT**",
                description=f"**{current_player.display_name}** took too long to make a move!\n\nFight ended due to inactivity.",
                color=discord.Color.dark_grey()
            )
            
            await self.message.edit(embed=embed, view=None)
            self.fight_over = True
