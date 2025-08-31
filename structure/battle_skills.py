"""
Universal Battle Skill System
Provides skill buttons and integration for all battle systems
"""

import discord
from discord import ui
from typing import List, Optional, Dict, Any
from structure.skills import SkillManager
from structure.player import Player


class SkillSelectView(discord.ui.View):
    """Universal skill selection component for battles with cooldown support"""

    def __init__(self, player_id: int, current_mp: int, callback_func, skill_cooldowns: dict = None, skill_charges: dict = None, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.player_id = player_id
        self.current_mp = current_mp
        self.callback_func = callback_func
        self.skill_cooldowns = skill_cooldowns or {}  # skill_id -> turns_remaining
        self.skill_charges = skill_charges or {}  # skill_id -> charge_progress
        self.skills_loaded = False
        
    async def load_skills(self):
        """Load player's skills and create selection options"""
        if self.skills_loaded:
            return
            
        player = await Player.get(self.player_id)
        if not player or not player.skills:
            return
        
        options = []
        
        # Add basic punch option
        options.append(discord.SelectOption(
            label="👊 Punch",
            description="Basic Attack | 100% Damage | 0 MP",
            value="punch",
            emoji="👊"
        ))
        
        # Add player's skills with scaled stats, cooldown, and charge info
        for skill_id, skill_data in player.skills.items():
            skill = await SkillManager.get_skill_with_player_level(skill_id, str(self.player_id))
            if skill:
                # Check cooldown for ultimate skills
                cooldown_remaining = self.skill_cooldowns.get(skill_id, 0)
                is_on_cooldown = cooldown_remaining > 0

                # Check charge status for ultimate skills
                is_ultimate = skill.skill_type.value == "Ultimate"
                charge_status = await BattleSkillIntegration.is_ultimate_skill_ready(
                    skill_id, self.player_id, self.skill_charges, self.skill_cooldowns
                )
                is_charging = not charge_status["ready"] and "Charging" in charge_status["reason"]

                # Check if player has enough MP
                can_use_mp = self.current_mp >= skill.mp_cost
                can_use = can_use_mp and charge_status["ready"]

                # Create status indicator with priority: cooldown > charging > MP > ready
                if is_on_cooldown:
                    status_indicator = f"🕒{cooldown_remaining}"
                elif is_charging:
                    # Extract charge progress from reason
                    if "(" in charge_status["reason"]:
                        charge_info = charge_status["reason"].split("(")[1].split(")")[0]
                        status_indicator = f"⚡{charge_info}"
                    else:
                        status_indicator = "⚡"
                elif not can_use_mp:
                    status_indicator = "❌"
                else:
                    status_indicator = "✅"

                # Add skill type emoji
                skill_emoji = "💥" if skill.skill_type.value == "Ultimate" else "⚡"

                # Create description with cooldown and charge info
                description = f"{status_indicator} {skill.damage}% DMG | {skill.mp_cost} MP | {skill.element.value}"
                if is_on_cooldown:
                    description += f" | Cooldown: {cooldown_remaining} turns"
                elif is_charging:
                    description += f" | {charge_status['reason']}"
                elif is_ultimate and charge_status["ready"]:
                    description += f" | Ultimate Ready!"

                options.append(discord.SelectOption(
                    label=f"{skill.name} (Lv.{skill.level})",
                    description=description,
                    value=skill_id,
                    emoji=skill_emoji
                ))
        
        if len(options) > 1:  # More than just punch
            select = discord.ui.Select(
                placeholder="Choose your action...",
                options=options[:25],  # Discord limit
                row=0
            )
            select.callback = self.skill_selected
            self.add_item(select)
            
        self.skills_loaded = True
    
    async def skill_selected(self, interaction: discord.Interaction):
        """Handle skill selection"""
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("❌ **This is not your battle.**", ephemeral=True)
            return
            
        skill_id = interaction.data['values'][0]
        
        # Call the provided callback function
        await self.callback_func(interaction, skill_id)


class BattleSkillIntegration:
    """Helper class for integrating skills into battle systems"""
    
    @staticmethod
    async def get_player_skills_info(player_id: int) -> Dict[str, Any]:
        """Get comprehensive skill information for a player"""
        player = await Player.get(player_id)
        if not player or not player.skills:
            return {"has_skills": False, "skills": {}}
        
        skills_info = {}
        for skill_id, skill_data in player.skills.items():
            skill = await SkillManager.get_skill_with_player_level(skill_id, str(player_id))
            if skill:
                skills_info[skill_id] = {
                    "name": skill.name,
                    "level": skill.level,
                    "damage": skill.damage,
                    "mp_cost": skill.mp_cost,
                    "element": skill.element.value,
                    "description": skill.get_skill_description()
                }
        
        return {
            "has_skills": len(skills_info) > 0,
            "skills": skills_info,
            "count": len(skills_info)
        }
    
    @staticmethod
    async def calculate_skill_damage(player_id: int, skill_id: str, base_attack: int,
                                   enemy_defense: int = 0, player_precision: int = 0,
                                   enemy_evasion: int = 0) -> Dict[str, Any]:
        """Calculate damage for a skill with proper scaling and hit chance"""

        # Calculate hit chance based on precision vs evasion
        hit_result = BattleSkillIntegration.calculate_hit_chance(player_precision, enemy_evasion)

        if skill_id == "punch":
            # Basic punch damage
            base_damage = max(1, round(base_attack * (100 / (100 + enemy_defense if enemy_defense > 0 else 1))))
            final_damage = base_damage if hit_result["hit"] else 0

            return {
                "damage": final_damage,
                "skill_name": "Punch",
                "skill_level": 1,
                "mp_cost": 0,
                "element": "Physical",
                "hit": hit_result["hit"],
                "hit_chance": hit_result["hit_chance"],
                "miss_reason": hit_result.get("miss_reason", "")
            }

        # Get scaled skill
        skill = await SkillManager.get_skill_with_player_level(skill_id, str(player_id))
        if not skill:
            return None

        # Check if this is a buff-only skill (no damage)
        from structure.skills import EffectType
        is_buff_only = (skill.damage == 0 or
                       (EffectType.BUFF in skill.effects and
                        EffectType.DAMAGE not in skill.effects and
                        EffectType.AREA_DAMAGE not in skill.effects))

        if is_buff_only:
            # Buff skills don't do damage but always "hit" for effect application
            final_damage = 0
            hit_result["hit"] = True  # Buffs always succeed
        else:
            # Calculate base damage with proper skill scaling and defense
            skill_multiplier = skill.damage / 100.0  # Convert percentage to decimal
            defense_reduction = 100.0 / (100.0 + max(0, enemy_defense))
            base_damage = max(1, round(base_attack * skill_multiplier * defense_reduction))

            # Apply hit chance
            final_damage = base_damage if hit_result["hit"] else 0

        # Calculate skill effects
        effects_result = BattleSkillIntegration.calculate_skill_effects(skill, base_attack, hit_result["hit"])

        return {
            "damage": final_damage,
            "skill_name": skill.name,
            "skill_level": skill.level,
            "mp_cost": skill.mp_cost,
            "element": skill.element.value,
            "base_damage_percent": skill.damage,
            "hit": hit_result["hit"],
            "hit_chance": hit_result["hit_chance"],
            "miss_reason": hit_result.get("miss_reason", ""),
            "effects": effects_result
        }
    
    @staticmethod
    async def create_skill_embed(player_id: int, title: str = "⚡ **AVAILABLE SKILLS**") -> Optional[discord.Embed]:
        """Create an embed showing player's available skills"""
        skills_info = await BattleSkillIntegration.get_player_skills_info(player_id)
        
        if not skills_info["has_skills"]:
            return None
        
        embed = discord.Embed(
            title=title,
            description="Your mastered skills are ready for battle!",
            color=discord.Color.gold()
        )
        
        skills_text = ""
        for skill_id, skill_data in skills_info["skills"].items():
            skills_text += (
                f"⚡ **{skill_data['name']}** (Level {skill_data['level']})\n"
                f"   • Damage: {skill_data['damage']}% | MP: {skill_data['mp_cost']} | {skill_data['element']}\n\n"
            )
        
        embed.add_field(
            name=f"🎯 **Skills Available** ({skills_info['count']})",
            value=skills_text[:1024],  # Discord field limit
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Use skills wisely in battle")
        return embed
    
    @staticmethod
    def create_skill_buttons() -> List[discord.ui.Button]:
        """Create skill-related buttons for battle interfaces"""
        buttons = []
        
        # Skill info button
        info_button = discord.ui.Button(
            label="⚡ Skills",
            style=discord.ButtonStyle.secondary,
            emoji="⚡"
        )
        buttons.append(info_button)
        
        return buttons

    @staticmethod
    def calculate_hit_chance(attacker_precision: int, defender_evasion: int) -> Dict[str, Any]:
        """Calculate hit chance based on precision vs evasion"""
        import random

        # Base hit chance is 85%
        base_hit_chance = 85.0

        # Calculate precision advantage/disadvantage
        precision_diff = attacker_precision - defender_evasion

        # Each point of precision difference affects hit chance by 0.5%
        # Max bonus/penalty is ±25% (50 point difference)
        precision_modifier = max(-25.0, min(25.0, precision_diff * 0.5))

        # Final hit chance (minimum 10%, maximum 95%)
        final_hit_chance = max(10.0, min(95.0, base_hit_chance + precision_modifier))

        # Roll for hit
        roll = random.uniform(0, 100)
        hit = roll <= final_hit_chance

        # Determine miss reason
        miss_reason = ""
        if not hit:
            if precision_diff < -20:
                miss_reason = "Enemy too agile!"
            elif precision_diff < -10:
                miss_reason = "Enemy dodged!"
            elif precision_diff < 0:
                miss_reason = "Attack missed!"
            else:
                miss_reason = "Bad luck!"

        return {
            "hit": hit,
            "hit_chance": round(final_hit_chance, 1),
            "precision_diff": precision_diff,
            "roll": round(roll, 1),
            "miss_reason": miss_reason
        }

    @staticmethod
    def get_ultimate_skill_cooldown(skill_type_value: str) -> int:
        """Get cooldown turns for ultimate skills"""
        if skill_type_value == "Ultimate":
            return 3  # Ultimate skills have 3-turn cooldown
        return 0  # No cooldown for Basic and QTE skills

    @staticmethod
    def get_ultimate_skill_charge_time(skill_type_value: str) -> int:
        """Get charge time required for ultimate skills"""
        if skill_type_value == "Ultimate":
            return 3  # Ultimate skills need 3 turns to charge
        return 0  # No charge time for Basic and QTE skills



    @staticmethod
    async def is_ultimate_skill_ready(skill_id: str, player_id: int, skill_charges, skill_cooldowns: dict) -> dict:
        """Check if an ultimate skill is ready to use"""
        # Safety check: if skill_charges is a coroutine, await it
        import inspect
        if inspect.iscoroutine(skill_charges):
            skill_charges = await skill_charges

        # Ensure skill_charges is a dict
        if not isinstance(skill_charges, dict):
            skill_charges = {}

        skill = await SkillManager.get_skill_with_player_level(skill_id, str(player_id))
        if not skill:
            return {"ready": False, "reason": "Skill not found"}

        if skill.skill_type.value != "Ultimate":
            return {"ready": True, "reason": "Not an ultimate skill"}

        # Check cooldown
        if skill_cooldowns.get(skill_id, 0) > 0:
            return {"ready": False, "reason": f"On cooldown ({skill_cooldowns[skill_id]} turns)"}

        # Check charge
        current_charge = skill_charges.get(skill_id, 0)
        required_charge = BattleSkillIntegration.get_ultimate_skill_charge_time("Ultimate")

        if current_charge < required_charge:
            return {"ready": False, "reason": f"Charging ({current_charge}/{required_charge} turns)"}

        return {"ready": True, "reason": "Ready to use"}

    @staticmethod
    def get_ultimate_skill_charge_time(skill_type_value: str) -> int:
        """Get charge time required for ultimate skills"""
        if skill_type_value == "Ultimate":
            return 3  # Ultimate skills need 3 turns to charge
        return 0  # No charge time for Basic and QTE skills

    @staticmethod
    async def initialize_skill_charges(player_skills: dict) -> dict:
        """Initialize charge counters for all ultimate skills"""
        from structure.skills import SkillManager

        skill_charges = {}
        for skill_id in player_skills.keys():
            # All skills start with 0 charge (ultimate skills need 3 to use)
            skill_charges[skill_id] = 0
        return skill_charges

    @staticmethod
    async def update_skill_charges(skill_charges: dict, player_skills: dict) -> dict:
        """Update skill charges each turn"""
        from structure.skills import SkillManager

        # Ensure skill_charges is a dict, not a coroutine
        if hasattr(skill_charges, '__await__'):
            skill_charges = await skill_charges

        updated_charges = skill_charges.copy()

        for skill_id in player_skills.keys():
            current_charge = updated_charges.get(skill_id, 0)

            # Only increment charge for ultimate skills, and only if not at max
            try:
                skill = await SkillManager.get(skill_id)
                if skill and skill.skill_type.value == "Ultimate" and current_charge < 3:
                    updated_charges[skill_id] = current_charge + 1
            except:
                # Skip if skill can't be loaded
                continue

        return updated_charges

    @staticmethod
    async def can_use_ultimate_skill(skill_id: str, player_id: int, skill_charges, skill_cooldowns: dict) -> Dict[str, Any]:
        """Check if an ultimate skill can be used (charged and not on cooldown)"""
        # Safety check: if skill_charges is a coroutine, await it
        import inspect
        if inspect.iscoroutine(skill_charges):
            skill_charges = await skill_charges

        # Ensure skill_charges is a dict
        if not isinstance(skill_charges, dict):
            skill_charges = {}

        skill = await SkillManager.get_skill_with_player_level(skill_id, str(player_id))
        if not skill:
            return {"can_use": False, "reason": "Skill not found"}

        if skill.skill_type.value != "Ultimate":
            return {"can_use": True, "reason": "Not an ultimate skill"}

        # Check cooldown
        if skill_cooldowns.get(skill_id, 0) > 0:
            return {"can_use": False, "reason": f"On cooldown ({skill_cooldowns[skill_id]} turns)"}

        # Check charge
        required_charge = BattleSkillIntegration.get_ultimate_skill_charge_time("Ultimate")
        current_charge = skill_charges.get(skill_id, 0)

        if current_charge < required_charge:
            return {"can_use": False, "reason": f"Charging ({current_charge}/{required_charge} turns)"}

        return {"can_use": True, "reason": "Ready to use"}

    @staticmethod
    def update_skill_cooldowns(cooldowns: dict) -> dict:
        """Reduce all skill cooldowns by 1 turn"""
        updated_cooldowns = {}
        for skill_id, turns_remaining in cooldowns.items():
            if turns_remaining > 1:
                updated_cooldowns[skill_id] = turns_remaining - 1
            # Skills with 1 or 0 turns remaining are removed (ready to use)
        return updated_cooldowns

    @staticmethod
    async def apply_skill_cooldown(skill_id: str, player_id: int, cooldowns: dict) -> dict:
        """Apply cooldown to a skill after use"""
        skill = await SkillManager.get_skill_with_player_level(skill_id, str(player_id))
        if skill and skill.skill_type.value == "Ultimate":
            cooldowns[skill_id] = BattleSkillIntegration.get_ultimate_skill_cooldown("Ultimate")
        return cooldowns

    @staticmethod
    def calculate_skill_effects(skill, base_attack: int, hit: bool) -> Dict[str, Any]:
        """Calculate additional effects of a skill"""
        from structure.skills import EffectType

        effects_result = {
            "heal_amount": 0,
            "life_steal_amount": 0,
            "buff_effects": [],
            "debuff_effects": [],
            "special_effects": []
        }

        if not hit or not hasattr(skill, 'effects'):
            return effects_result

        for effect in skill.effects:
            if effect == EffectType.HEAL:
                # Heal based on skill damage percentage
                heal_amount = max(10, round(base_attack * (skill.damage / 200.0)))  # Half of damage as heal
                effects_result["heal_amount"] = heal_amount
                effects_result["special_effects"].append(f"Heals {heal_amount} HP")

            elif effect == EffectType.LIFE_STEAL:
                # Life steal based on actual damage dealt
                life_steal_percent = min(50, skill.damage // 4)  # Up to 50% life steal
                effects_result["life_steal_amount"] = life_steal_percent
                effects_result["special_effects"].append(f"Life steal {life_steal_percent}%")

            elif effect == EffectType.BUFF:
                # Buff effects based on skill type
                if skill.skill_type.value == "Ultimate":
                    buff_amount = 20  # 20% stat boost for ultimates
                elif skill.skill_type.value == "QTE":
                    buff_amount = 15  # 15% stat boost for QTE
                else:
                    buff_amount = 10  # 10% stat boost for basic

                effects_result["buff_effects"].append({
                    "type": "attack_boost",
                    "amount": buff_amount,
                    "duration": 3  # 3 turns
                })
                effects_result["special_effects"].append(f"Attack +{buff_amount}% (3 turns)")

            elif effect == EffectType.DEBUFF:
                # Debuff effects
                debuff_amount = 15  # 15% stat reduction
                effects_result["debuff_effects"].append({
                    "type": "defense_reduction",
                    "amount": debuff_amount,
                    "duration": 2  # 2 turns
                })
                effects_result["special_effects"].append(f"Enemy defense -{debuff_amount}% (2 turns)")

            elif effect == EffectType.STUN:
                effects_result["special_effects"].append("Stuns enemy (1 turn)")

            elif effect == EffectType.CRIT_BOOST:
                effects_result["buff_effects"].append({
                    "type": "crit_boost",
                    "amount": 25,  # 25% crit chance boost
                    "duration": 3
                })
                effects_result["special_effects"].append("Critical hit chance +25% (3 turns)")

            elif effect == EffectType.AREA_DAMAGE:
                effects_result["special_effects"].append("Area of effect damage")

            elif effect == EffectType.SHIELD:
                shield_amount = max(50, round(base_attack * (skill.damage / 300.0)))
                effects_result["special_effects"].append(f"Shield absorbs {shield_amount} damage")

        return effects_result
    
    @staticmethod
    async def validate_skill_usage(player_id: int, skill_id: str, current_mp: int) -> Dict[str, Any]:
        """Validate if a player can use a specific skill"""
        if skill_id == "punch":
            return {"can_use": True, "reason": "Basic attack"}
        
        skill = await SkillManager.get_skill_with_player_level(skill_id, str(player_id))
        if not skill:
            return {"can_use": False, "reason": "Skill not found"}
        
        if current_mp < skill.mp_cost:
            return {"can_use": False, "reason": f"Need {skill.mp_cost} MP (have {current_mp})"}
        
        return {"can_use": True, "reason": "Ready to use", "skill": skill}


class SkillTestView(discord.ui.View):
    """Test view for skill system - can be used in any channel"""
    
    def __init__(self, player_id: int):
        super().__init__(timeout=300)
        self.player_id = player_id
    
    @discord.ui.button(label="Test Skills", style=discord.ButtonStyle.primary, emoji="⚡")
    async def test_skills(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Test skill system functionality"""
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("❌ **This is not your test.**", ephemeral=True)
            return
        
        # Get player's skills
        skills_info = await BattleSkillIntegration.get_player_skills_info(self.player_id)
        
        if not skills_info["has_skills"]:
            await interaction.response.send_message(
                "❌ **No skills found!** Learn some skills first using `sl system` → 🎓 Learn Skills",
                ephemeral=True
            )
            return
        
        # Create skill embed
        embed = await BattleSkillIntegration.create_skill_embed(
            self.player_id, 
            "🧪 **SKILL SYSTEM TEST**"
        )
        
        # Create skill selection view
        async def skill_callback(inter, skill_id):
            damage_info = await BattleSkillIntegration.calculate_skill_damage(
                self.player_id, skill_id, 1000, 100  # Test with 1000 ATK vs 100 DEF
            )
            
            if damage_info:
                test_embed = discord.Embed(
                    title="⚡ **SKILL TEST RESULT**",
                    description=f"Testing **{damage_info['skill_name']}** (Level {damage_info['skill_level']})",
                    color=discord.Color.green()
                )
                
                test_embed.add_field(
                    name="📊 **Damage Calculation**",
                    value=(
                        f"**Base Attack**: 1,000\n"
                        f"**Enemy Defense**: 100\n"
                        f"**Skill Damage**: {damage_info.get('base_damage_percent', 100)}%\n"
                        f"**Final Damage**: {damage_info['damage']}\n"
                        f"**MP Cost**: {damage_info['mp_cost']}\n"
                        f"**Element**: {damage_info['element']}"
                    ),
                    inline=False
                )
                
                test_embed.set_footer(text="◆ The System ◆ • Skill test completed")
                await inter.response.edit_message(embed=test_embed, view=self)
            else:
                await inter.response.send_message("❌ **Skill test failed.**", ephemeral=True)
        
        skill_view = SkillSelectView(self.player_id, 1000, skill_callback)  # Test with 1000 MP
        await skill_view.load_skills()
        
        await interaction.response.edit_message(embed=embed, view=skill_view)
    
    @discord.ui.button(label="🔙 Back", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to original state"""
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("❌ **This is not your test.**", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🧪 **SKILL SYSTEM TESTER**",
            description="Test your skills and see their damage calculations!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🎯 **How to Test**",
            value=(
                "1. Click **⚡ Test Skills** to see your available skills\n"
                "2. Select a skill to see damage calculation\n"
                "3. Test different skills to compare effectiveness"
            ),
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Skill testing interface")
        await interaction.response.edit_message(embed=embed, view=self)
