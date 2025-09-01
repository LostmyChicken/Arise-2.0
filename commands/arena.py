import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import time
from typing import List, Optional

from structure.playerId import PlayerIdManager
from structure.emoji import getClassEmoji, getEmoji
from structure.heroes import HeroManager
from structure.player import Player
from structure.glory import Glory
from structure.skills import SkillManager
from utilis.utilis import PremiumCheck, extractId, get_emoji, getStatHunter, getStatWeapon
from commands.missions import track_mission_progress

ELEMENT_WEAKNESSES = {
    "Dark": {"weak_to": ["Light"], "effective_against": ["Light"]},
    "Light": {"weak_to": ["Dark"], "effective_against": ["Dark"]},
    "Water": {"weak_to": ["Wind"], "effective_against": ["Fire"]},
    "Fire": {"weak_to": ["Water"], "effective_against": ["Wind"]},
    "Wind": {"weak_to": ["Fire"], "effective_against": ["Water"]},
}

def calculate_elemental_advantage(attacker_element, defender_element):
    if not attacker_element or not defender_element:
        return 1.0
    
    attacker_element = attacker_element.capitalize()
    defender_element = defender_element.capitalize()
    
    if defender_element in ELEMENT_WEAKNESSES.get(attacker_element, {}).get("effective_against", []):
        return 1.5
    
    if attacker_element in ELEMENT_WEAKNESSES.get(defender_element, {}).get("weak_to", []):
        return 0.5
    
    return 1.0

class BattleHunter:
    def __init__(self, hunter_id, level, tier, weapon_id=None):
        self.id = hunter_id
        self.level = level
        self.tier = tier
        self.weapon_id = weapon_id
        self.max_hp = 0
        self.current_hp = 0
        self.attack = 0
        self.defense = 0
        self.name = ""
        self.class_type = ""
        self.element = ""
        self.alive = True
        self.damage_dealt = 0
        self.fainted = False
        
    async def initialize(self):
        char = await HeroManager.get(self.id)
        stat = await getStatHunter(char.id, self.level)
        
        self.name = char.name
        self.class_type = char.classType
        self.element = char.classType
        self.max_hp = stat.hp
        self.current_hp = stat.hp
        self.attack = stat.attack
        self.defense = stat.defense
        
        if self.weapon_id:
            weapon_stat = await getStatWeapon(self.weapon_id, self.level)
            self.attack += weapon_stat["attack"]
            self.defense += weapon_stat["defense"]
            self.max_hp += weapon_stat["hp"]
            self.current_hp = self.max_hp

async def create_battle_embed(ctx, player_party, opponent_party, opponent_name=None, battle_logs=None):
    """Create an enhanced battle embed with proper emoji handling"""
    embed = discord.Embed(
        title=f"{getEmoji('attack')} Arena Battle",
        color=discord.Color.dark_blue()
    )

    # Player team section
    player_alive = sum(1 for h in player_party if h.alive)
    player_total = len(player_party)

    player_description = [f"🔵 **{ctx.author.display_name}'s Team** ({player_alive}/{player_total} alive)\n"]
    for i, hunter in enumerate(player_party, 1):
        status_emoji = getEmoji("health") if hunter.alive else "💀"
        p = pbar(hunter.current_hp, hunter.max_hp, 8)
        class_emoji = getClassEmoji(hunter.class_type)
        hunter_emoji = getEmoji(extractId(hunter.name))  # Use sync version

        player_description.append(
            f"{status_emoji} **{i}.** {hunter_emoji} {class_emoji} **{hunter.name}** (Lv.{hunter.level})\n"
            f"   {p} `{hunter.current_hp:,}/{hunter.max_hp:,}` HP\n"
            f"   {getEmoji('attack')} `{hunter.attack:,}` ATK • {getEmoji('defense')} `{hunter.defense:,}` DEF\n\n"
        )

    # Opponent team section
    opponent_alive = sum(1 for h in opponent_party if h.alive)
    opponent_total = len(opponent_party)

    opponent_description = [f"🔴 **{opponent_name or 'Opponent'}'s Team** ({opponent_alive}/{opponent_total} alive)\n"]
    for i, hunter in enumerate(opponent_party, 1):
        status_emoji = getEmoji("health") if hunter.alive else "💀"
        p = pbar(hunter.current_hp, hunter.max_hp, 8)
        class_emoji = getClassEmoji(hunter.class_type)
        hunter_emoji = getEmoji(extractId(hunter.name))  # Use sync version

        opponent_description.append(
            f"{status_emoji} **{i}.** {hunter_emoji} {class_emoji} **{hunter.name}** (Lv.{hunter.level})\n"
            f"   {p} `{hunter.current_hp:,}/{hunter.max_hp:,}` HP\n"
            f"   {getEmoji('attack')} `{hunter.attack:,}` ATK • {getEmoji('defense')} `{hunter.defense:,}` DEF\n\n"
        )

    embed.description = "".join(player_description + ["─" * 40 + "\n\n"] + opponent_description)

    if battle_logs:
        recent_logs = battle_logs[-3:]  # Show last 3 logs
        embed.add_field(
            name="📜 Battle Log",
            value="\n".join(f"• {log}" for log in recent_logs) or "Battle starting...",
            inline=False
        )

    embed.set_thumbnail(url="https://files.catbox.moe/8h3wqr.png")  # Arena icon
    return embed

class BattleView(discord.ui.View):
    def __init__(self, cog, ctx, player_party):
        super().__init__(timeout=45)  # Increased timeout
        self.cog = cog
        self.ctx = ctx
        self.player_party = player_party
        self.choice = None
        self.timed_out = False

        # Add hunter buttons with enhanced styling
        for i, hunter in enumerate(player_party):
            self.add_item(
                HunterButton(
                    hunter=hunter,
                    index=i,
                    disabled=not hunter.alive
                )
            )

        # Add forfeit button
        self.add_item(ForfeitButton())

    async def on_timeout(self):
        self.timed_out = True
        for hunter in self.player_party:
            hunter.alive = False
        self.stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="This isn't your battle! You can only control your own arena matches.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

class HunterButton(discord.ui.Button):
    def __init__(self, hunter, index, disabled=False):
        # Enhanced button styling based on hunter status
        if disabled:
            style = discord.ButtonStyle.secondary
            label = hunter.name
            emoji = "💀"
        else:
            # Color based on HP percentage, use custom health emoji as button emoji
            hp_percent = hunter.current_hp / hunter.max_hp if hunter.max_hp > 0 else 0
            label = hunter.name
            if hp_percent > 0.7:
                style = discord.ButtonStyle.success
                emoji = getEmoji('health')
            elif hp_percent > 0.3:
                style = discord.ButtonStyle.primary
                emoji = getEmoji('health')
            else:
                style = discord.ButtonStyle.danger
                emoji = getEmoji('health')

        super().__init__(
            style=style,
            label=label,
            emoji=emoji,
            custom_id=str(index),
            disabled=disabled,
            row=0
        )
        self.hunter = hunter

    async def callback(self, interaction):
        self.view.choice = int(self.custom_id)

        # Enhanced feedback
        embed = discord.Embed(
            title=f"{getEmoji('attack')} Attack Selected!",
            description=f"**{self.hunter.name}** is preparing to attack!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Processing attack...")

        await interaction.response.edit_message(embed=embed, view=None)
        self.view.stop()

class ForfeitButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="🏳️ Forfeit",
            custom_id="forfeit",
            row=1
        )

    async def callback(self, interaction):
        # Confirmation embed
        embed = discord.Embed(
            title="⚠️ Forfeit Battle?",
            description="Are you sure you want to forfeit this battle?\n\n**Consequences:**\n• You will lose your win streak\n• You will lose arena points\n• Your hunters will not gain XP",
            color=discord.Color.orange()
        )

        view = ForfeitConfirmView()
        await interaction.response.edit_message(embed=embed, view=view)
        await view.wait()

        if view.confirmed:
            # Mark all player hunters as defeated
            for hunter in self.view.player_party:
                hunter.alive = False
            self.view.stop()
        else:
            # Return to battle
            embed = await create_battle_embed(self.view.ctx, self.view.player_party, [], "Opponent", [])
            embed.set_footer(text="Battle resumed! Choose your next move.")
            await interaction.edit_original_response(embed=embed, view=self.view)

class ForfeitConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.confirmed = False

    @discord.ui.button(label="✅ Yes, Forfeit", style=discord.ButtonStyle.danger)
    async def confirm_forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        embed = discord.Embed(
            title="🏳️ Battle Forfeited",
            description="You have forfeited the battle. Returning to results...",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.defer()
        self.stop()

class ArenaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles = set()
        self.battle_messages = {}

    async def get_random_opponent(self, player_id: int) -> Optional[int]:
        try:
            # Use cached player IDs for better performance
            all_ids = await PlayerIdManager.get_all_ids()
            valid_opponents = [
                opponent_id for opponent_id in all_ids
                if opponent_id != player_id and opponent_id not in self.active_battles
            ]

            # Limit the number of opponents to check for better performance
            if len(valid_opponents) > 50:
                valid_opponents = random.sample(valid_opponents, 50)

            opponents_with_parties = []
            # Batch load opponents for better performance
            for oid in valid_opponents[:20]:  # Limit to first 20 for speed
                opponent = await Player.get(oid)
                if opponent and opponent.hunters:  # Quick check if they have any hunters
                    party_count = sum(1 for slot in ["Party_1", "Party_2", "Party_3"]
                                      if opponent.equipped.get(slot) in opponent.hunters)
                    if party_count >= 1:
                        opponents_with_parties.append(oid)
                        if len(opponents_with_parties) >= 10:  # Stop after finding 10 valid opponents
                            break

            return random.choice(opponents_with_parties) if opponents_with_parties else None
        except Exception as e:
            print(f"Error getting random opponent: {e}")
            # Fallback to simple random selection
            all_ids = await Player.get_all_player_ids()
            fallback_opponents = [pid for pid in all_ids if pid != player_id]
            return random.choice(fallback_opponents) if fallback_opponents else None

    async def load_party(self, player) -> List[BattleHunter]:
        party = []
        # Batch initialize all hunters for better performance
        battle_hunters = []

        for slot_key in ["Party_1", "Party_2", "Party_3"]:
            hunter_id = player.equipped.get(slot_key)
            if hunter_id and hunter_id in player.hunters:
                hunter_data = player.hunters[hunter_id]
                weapon_id = hunter_data.get("weapon")
                bh = BattleHunter(
                    hunter_id=hunter_id,
                    level=hunter_data.get("level", 1),
                    tier=hunter_data.get("tier", 0),
                    weapon_id=weapon_id
                )
                battle_hunters.append(bh)

        # Initialize all hunters concurrently for better performance
        if battle_hunters:
            await asyncio.gather(*[bh.initialize() for bh in battle_hunters])
            party.extend(battle_hunters)

        return party

    async def calculate_xp_rewards(self, player, player_party, opponent_party, player_won):
        xp_rewards = {}
        level_up_messages = []
        
        total_damage = sum(h.damage_dealt for h in player_party) or 1
        base_xp = 100 if player_won else 50
        
        player_strength = sum(h.level * (h.tier + 1) for h in player_party)
        opponent_strength = sum(h.level * (h.tier + 1) for h in opponent_party) or 1
        strength_ratio = max(0.5, min(2.0, opponent_strength / player_strength))
        
        for hunter in player_party:
            damage_ratio = hunter.damage_dealt / total_damage
            performance_xp = base_xp * strength_ratio * damage_ratio
            
            if hunter.alive:
                performance_xp *= 1.5
                
            performance_xp = max(10, performance_xp if hunter.damage_dealt > 0 else 10)
                
            xp_to_add = int(round(performance_xp))
            success = player.hunter_add_xp(hunter.id, xp_to_add)
            
            xp_rewards[hunter.name] = {
                'xp_gained': xp_to_add if success else 0,
                'level': hunter.level,
            }
            
            if success and xp_to_add > 0:
                level_up_messages.append(f"**{hunter.name}** gained {xp_to_add} XP!")
        
        return xp_rewards, level_up_messages

    async def create_results_embed(self, ctx, player_party, opponent_party, player_won, xp_rewards, win_streak):
        # Enhanced results embed with better visual design
        if player_won:
            embed = discord.Embed(
                title="🏆 VICTORY!",
                description="**Congratulations!** You have emerged victorious in the arena!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url="https://files.catbox.moe/victory.png")
        else:
            embed = discord.Embed(
                title="💀 DEFEAT",
                description="**Better luck next time!** Your opponent proved stronger today.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://files.catbox.moe/defeat.png")

        # Battle outcome section
        player_survivors = sum(1 for h in player_party if h.alive)
        opponent_survivors = sum(1 for h in opponent_party if h.alive)

        outcome_text = (
            f"🔵 **Your Team**: `{player_survivors}/3` survivors\n"
            f"🔴 **Opponent**: `{opponent_survivors}/3` survivors\n"
            f"🔥 **Win Streak**: `{win_streak}`"
        )

        embed.add_field(
            name="📊 Battle Summary",
            value=outcome_text,
            inline=False
        )

        # Enhanced XP display
        xp_info = []
        total_xp = 0
        for hunter in player_party:
            xp_gained = xp_rewards.get(hunter.name, {}).get('xp_gained', 0)
            total_xp += xp_gained
            status_emoji = getEmoji("health") if hunter.alive else "💀"
            hunter_emoji = getEmoji(extractId(hunter.name))  # Use sync version
            class_emoji = getClassEmoji(hunter.class_type)

            xp_info.append(
                f"{status_emoji} {hunter_emoji} {class_emoji} **{hunter.name}** (Lv.{hunter.level})\n"
                f"   {getEmoji('xp')} `+{xp_gained:,} XP` • {getEmoji('attack')} `{hunter.damage_dealt:,}` DMG"
            )

        embed.add_field(
            name=f"⭐ Experience Gained (Total: {total_xp:,} XP)",
            value="\n\n".join(xp_info) if xp_info else "No XP gained",
            inline=False
        )

        # Performance stats
        total_damage_dealt = sum(h.damage_dealt for h in player_party)
        total_damage_taken = sum(h.max_hp - h.current_hp for h in player_party)

        performance_text = (
            f"{getEmoji('attack')} **Total Damage Dealt**: `{total_damage_dealt:,}`\n"
            f"🩸 **Total Damage Taken**: `{total_damage_taken:,}`\n"
            f"💪 **Battle Rating**: `{'S' if player_won and player_survivors == 3 else 'A' if player_won else 'B' if player_survivors >= 2 else 'C'}`"
        )

        embed.add_field(
            name=f"{getEmoji('xp')} Performance Stats",
            value=performance_text,
            inline=False
        )

        embed.set_footer(text="🎯 Ready for another battle? Use 'sl arena' again!")
        return embed

    async def update_glory(self, player_id: int, opponent_id: int, player_won: bool, 
                           win_streak: int, player_name: str, opponent_name: str):
        player_glory = await Glory.get(player_id) or Glory(user_id=player_id, name=player_name)
        opponent_glory = await Glory.get(opponent_id) or Glory(user_id=opponent_id, name=opponent_name)
        
        player_glory.name = player_name
        opponent_glory.name = opponent_name
        
        base_points = 10
        min_points = 5
        
        if player_won:
            streak_bonus = min(win_streak * 2, 20)
            points_to_add = max(min_points, base_points + streak_bonus)
            
            player_glory.points += points_to_add
            player_glory.current_streak = win_streak + 1
            player_glory.hs = max(player_glory.hs, player_glory.current_streak)
            
            points_lost = min(opponent_glory.points, (points_to_add + 1) // 2)
            opponent_glory.points = max(0, opponent_glory.points - points_lost)
            opponent_glory.current_streak = 0
            
            await opponent_glory.add_log_entry({
                'content': f"Your defense failed against **{player_name}** 🔻 -{points_lost} ({opponent_glory.points})"
            })
        else:
            points_lost = min(player_glory.points, min_points)
            player_glory.points = max(0, player_glory.points - points_lost)
            player_glory.current_streak = 0
            
            opponent_glory.points += base_points
            opponent_glory.current_streak += 1
            opponent_glory.hs = max(opponent_glory.hs, opponent_glory.current_streak)
            
            await opponent_glory.add_log_entry({
                'content': f"You successfully defended against **{player_name}**\n🔺 +{base_points} ({opponent_glory.points})"
            })

        await player_glory.update_rank()
        await opponent_glory.update_rank()
        
        await player_glory.save()
        await opponent_glory.save()
        
        return player_glory

    async def simulate_battle(self, ctx, player_party, opponent_party, opponent_name=None, opponent_id=None):
        self.battle_messages[ctx.author.id] = None
        battle_logs = []
        
        try:
            battle_round = 1
            while any(h.alive for h in player_party) and any(h.alive for h in opponent_party):
                # Enhanced battle embed with round counter
                embed = await create_battle_embed(ctx, player_party, opponent_party, opponent_name, battle_logs)
                embed.set_footer(text=f"Round {battle_round} • Choose your hunter to attack! (45s timeout)")
                view = BattleView(self, ctx, player_party)

                if self.battle_messages.get(ctx.author.id):
                    await self.battle_messages[ctx.author.id].edit(embed=embed, view=view)
                else:
                    self.battle_messages[ctx.author.id] = await ctx.send(embed=embed, view=view)

                await view.wait()

                if view.timed_out:
                    timeout_embed = discord.Embed(
                        title="⏰ Battle Timeout",
                        description="You took too long to make a decision. Your hunters have been overwhelmed!",
                        color=discord.Color.red()
                    )
                    battle_logs.append("⏰ **Battle timed out** - Player failed to respond in time!")
                    for hunter in player_party:
                        hunter.alive = False
                    await self.battle_messages[ctx.author.id].edit(embed=timeout_embed, view=None)
                    break

                # Safety check: ensure a valid choice was made
                if view.choice is None:
                    # This shouldn't happen if timeout is handled correctly, but add safety
                    battle_logs.append("❌ **No hunter selected** - Battle ended unexpectedly!")
                    for hunter in player_party:
                        hunter.alive = False
                    break

                # Player's turn
                hunter = player_party[view.choice]
                alive_opponents = [h for h in opponent_party if h.alive]
                target = random.choice(alive_opponents)

                # Enhanced damage calculation with more variety
                base_damage = random.randint(hunter.attack, hunter.attack * 2)
                defense_reduction = base_damage / max(target.defense, 1)
                element_mod = calculate_elemental_advantage(hunter.element, target.element)
                critical_chance = random.random()
                critical_mod = 1.5 if critical_chance < 0.15 else 1.0  # 15% crit chance

                final_damage = round(650 * defense_reduction * element_mod * critical_mod)
                target.current_hp = max(0, target.current_hp - final_damage)
                hunter.damage_dealt += final_damage

                # Enhanced battle log with more detail
                effectiveness = ""
                if element_mod > 1:
                    effectiveness = " ⚡ **(Super Effective!)**"
                elif element_mod < 1:
                    effectiveness = f" {getEmoji('defense')} **(Not Very Effective)**"

                critical_text = f" {getEmoji('attack')} **CRITICAL HIT!**" if critical_mod > 1 else ""

                battle_logs.append(f"{getEmoji('attack')} **{hunter.name}** attacks **{target.name}** for `{final_damage:,}` damage{effectiveness}{critical_text}")

                if target.current_hp == 0:
                    target.alive = False
                    battle_logs.append(f"💀 **{target.name}** has been defeated!")

                # Update battle display
                battle_embed = await create_battle_embed(ctx, player_party, opponent_party, opponent_name, battle_logs)
                await self.battle_messages[ctx.author.id].edit(
                    embed=battle_embed,
                    view=None
                )
                await asyncio.sleep(1.5)  # Slightly longer for better readability

                if not any(h.alive for h in opponent_party):
                    break

                # AI opponent's turn with enhanced logic
                alive_ai_hunters = [h for h in opponent_party if h.alive]
                alive_player_hunters = [h for h in player_party if h.alive]

                # AI strategy: target lowest HP hunter or random
                ai_hunter = random.choice(alive_ai_hunters)

                # Smart targeting: 70% chance to target weakest, 30% random
                if random.random() < 0.7:
                    player_target = min(alive_player_hunters, key=lambda h: h.current_hp)
                else:
                    player_target = random.choice(alive_player_hunters)

                # Enhanced AI damage calculation
                base_damage = random.randint(ai_hunter.attack, ai_hunter.attack * 2)
                defense_reduction = base_damage / max(player_target.defense, 1)
                element_mod = calculate_elemental_advantage(ai_hunter.element, player_target.element)
                critical_chance = random.random()
                critical_mod = 1.5 if critical_chance < 0.12 else 1.0  # Slightly lower crit for AI

                ai_damage = round(650 * defense_reduction * element_mod * critical_mod)
                player_target.current_hp = max(0, player_target.current_hp - ai_damage)

                # Enhanced AI battle log
                effectiveness = ""
                if element_mod > 1:
                    effectiveness = " ⚡ **(Super Effective!)**"
                elif element_mod < 1:
                    effectiveness = f" {getEmoji('defense')} **(Not Very Effective)**"

                critical_text = f" {getEmoji('attack')} **CRITICAL HIT!**" if critical_mod > 1 else ""

                battle_logs.append(f"🔴 **{ai_hunter.name}** attacks **{player_target.name}** for `{ai_damage:,}` damage{effectiveness}{critical_text}")

                if player_target.current_hp == 0:
                    player_target.alive = False
                    battle_logs.append(f"💀 **{player_target.name}** has fallen in battle!")

                # Update battle display
                battle_embed = await create_battle_embed(ctx, player_party, opponent_party, opponent_name, battle_logs)
                await self.battle_messages[ctx.author.id].edit(
                    embed=battle_embed,
                    view=None
                )
                await asyncio.sleep(1.5)

                battle_round += 1

            player = await Player.get(ctx.author.id)
            player_won = any(h.alive for h in player_party)
            
            if player_won:
                player.aStreak += 1
                # Track mission progress for arena wins
                await track_mission_progress(ctx.author.id, "arena", 1)
            else:
                player.aStreak = 0

            glory = await self.update_glory(ctx.author.id, opponent_id, player_won, player.aStreak, ctx.author.name, opponent_name)
            xp_rewards, _ = await self.calculate_xp_rewards(player, player_party, opponent_party, player_won)

            player.inc = False
            player.mIncrease("arena")
            await player.save()
            
            # Enhanced results with glory points integration
            results_embed = await self.create_results_embed(ctx, player_party, opponent_party, player_won, xp_rewards, player.aStreak)

            # Add glory points information
            points_change = glory.points - (await Glory.get(ctx.author.id) or Glory(user_id=ctx.author.id)).points if player_won else 0

            glory_text = (
                f"🏅 **Arena Points**: `{glory.points:,}` "
                f"{getEmoji('xp') if player_won else '📉'} `({'+' if points_change >= 0 else ''}{points_change})`\n"
                f"🔥 **Highest Streak**: `{glory.hs}`\n"
                f"🏆 **Current Rank**: `#{glory.rank}` in the arena"
            )

            results_embed.add_field(
                name="🎖️ Arena Standing",
                value=glory_text,
                inline=False
            )

            # Add next battle info
            cooldown_seconds = 120
            cooldown_reduction = PremiumCheck(player)
            adjusted_cooldown_seconds = int(cooldown_seconds * cooldown_reduction)
            next_battle_text = (
                f"⏰ **Next Battle**: Available in `{adjusted_cooldown_seconds//60}` minutes\n"
                f"💎 **Premium**: `{int((1-cooldown_reduction)*100)}%` cooldown reduction"
            )

            results_embed.add_field(
                name=f"{getEmoji('attack')} Battle Info",
                value=next_battle_text,
                inline=False
            )

            await ctx.send(embed=results_embed)
            
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="Battle Error", description=f"An error occurred: {e}", color=discord.Color.red()))
        finally:
            if ctx.author.id in self.battle_messages:
                del self.battle_messages[ctx.author.id]
            if ctx.author.id in self.active_battles:
                self.active_battles.remove(ctx.author.id)

    @commands.command(name="arena", help="Engage in a PvP battle against another player's team.")
    async def arena(self, ctx):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Profile Not Found",
                description="You haven't started your journey yet!\n\nUse `sl start` to begin your adventure and unlock the arena.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Create your profile to access PvP battles!")
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Enhanced party validation
        party_slots = ["Party_1", "Party_2", "Party_3"]
        equipped_hunters = []
        for slot in party_slots:
            hunter_id = player.equipped.get(slot)
            if hunter_id and hunter_id in player.hunters:
                equipped_hunters.append(hunter_id)

        if len(equipped_hunters) < 3:
            embed = discord.Embed(
                title="⚠️ Incomplete Team",
                description=f"You need **3 hunters** in your party to enter the arena!\n\n**Current Team**: `{len(equipped_hunters)}/3` hunters",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="💡 How to Fix",
                value="• Use `sl party add <hunter>` to add hunters\n• Make sure you have 3 hunters equipped\n• Check `sl party` to view your current team",
                inline=False
            )
            embed.set_thumbnail(url="https://files.catbox.moe/team.png")
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Enhanced cooldown display
        cooldown_seconds = 120
        cooldown_reduction = PremiumCheck(player)
        adjusted_cooldown_seconds = int(cooldown_seconds * cooldown_reduction)

        current_time = time.time()
        if player.aC and current_time - float(player.aC) <= adjusted_cooldown_seconds:
            remaining_time = adjusted_cooldown_seconds - (current_time - float(player.aC))
            minutes, seconds = divmod(int(remaining_time), 60)

            embed = discord.Embed(
                title="⏰ Arena Cooldown Active",
                description=f"Your hunters are still recovering from the last battle!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="⏳ Time Remaining",
                value=f"`{minutes:02d}:{seconds:02d}`",
                inline=True
            )
            embed.add_field(
                name="💎 Premium Benefits",
                value=f"Cooldown reduced by `{int((1-cooldown_reduction)*100)}%`" if cooldown_reduction < 1 else "No active premium",
                inline=True
            )
            embed.set_thumbnail(url="https://files.catbox.moe/cooldown.png")
            embed.set_footer(text="Premium users get reduced cooldowns!")
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Battle state validation
        if ctx.author.id in self.active_battles:
            embed = discord.Embed(
                title=f"{getEmoji('attack')} Already in Battle",
                description="You're currently engaged in an arena battle!\n\nPlease wait for your current battle to finish before starting a new one.",
                color=discord.Color.red()
            )
            embed.set_footer(text="One battle at a time!")
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Set cooldown and battle state
        player.inc = True
        player.aC = time.time()
        await player.save()
        self.active_battles.add(ctx.author.id)
        
        try:
            # Streamlined loading sequence - removed artificial delays
            loading_embed = discord.Embed(
                title=f"{getEmoji('searching')} Matchmaking in Progress",
                description="Searching for a worthy opponent...",
                color=discord.Color.blue()
            )
            loading_embed.add_field(
                name="⚡ Status",
                value=f"{getEmoji('searching')} Finding opponent...",
                inline=False
            )
            loading_msg = await ctx.reply(embed=loading_embed, mention_author=False)

            # Find opponent immediately without artificial delay
            opponent_id = await self.get_random_opponent(ctx.author.id)
            if not opponent_id:
                embed = discord.Embed(
                    title="😔 No Opponents Available",
                    description="Unable to find a suitable opponent at this time.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 Try Again Later",
                    value="More players may be available soon!\nConsider inviting friends to join the arena.",
                    inline=False
                )
                embed.set_footer(text="The arena needs more warriors!")
                await loading_msg.edit(embed=embed)
                return

            opponent = await Player.get(opponent_id)
            if not opponent:
                embed = discord.Embed(
                    title="❌ Opponent Data Error",
                    description="Failed to load opponent information.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Please try again in a moment.")
                await loading_msg.edit(embed=embed)
                return

            # Get opponent info
            try:
                opponent_user = await self.bot.fetch_user(opponent_id)
                opponent_name = opponent_user.global_name or opponent_user.name
            except:
                opponent_name = f"Player {opponent_id}"

            # Update loading with opponent found
            found_embed = discord.Embed(
                title="🎯 Opponent Found!",
                description=f"**{opponent_name}** has been selected as your opponent!",
                color=discord.Color.green()
            )
            found_embed.add_field(
                name=f"{getEmoji('attack')} Preparing Battle",
                value="Loading hunter parties and initializing combat...",
                inline=False
            )
            found_embed.set_thumbnail(url="https://files.catbox.moe/battle_prep.png")
            await loading_msg.edit(embed=found_embed)

            # Load parties concurrently for better performance
            player_party, opponent_party = await asyncio.gather(
                self.load_party(player),
                self.load_party(opponent)
            )

            # Quick preparation message without delay
            prep_embed = discord.Embed(
                title=f"{getEmoji('attack')} Battle Commencing!",
                description=f"**{ctx.author.display_name}** vs **{opponent_name}**\n\nMay the strongest hunter prevail!",
                color=discord.Color.gold()
            )
            prep_embed.set_footer(text="Battle starting now!")
            await loading_msg.edit(embed=prep_embed)

            await self.simulate_battle(ctx, player_party, opponent_party, opponent_name, opponent_id)
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="An Error Occurred", description=str(e), color=discord.Color.red()))
        finally:
            player.inc = False
            await player.save()
            if ctx.author.id in self.active_battles:
                self.active_battles.remove(ctx.author.id)

async def setup(bot):
    await bot.add_cog(ArenaCog(bot))
 
def pbar(current, max_val, divs):
    if max_val == 0: return ""
    progress = max(0, min(1, current / max_val))
    
    fill_styles = {
        "default": (getEmoji("gs"), getEmoji("gm"), getEmoji("ge")),
        "50": (getEmoji("ol"), getEmoji("om"), getEmoji("ge")),
        "25": (getEmoji("rl"), getEmoji("rm"), getEmoji("ge"))
    }
    empty_style = (getEmoji("es"), getEmoji("em"), getEmoji("ee"))

    if progress <= 0.25: style = "25"
    elif progress <= 0.5: style = "50"
    else: style = "default"
    
    fill_start, fill_middle, fill_end = fill_styles[style]
    empty_start, empty_middle, empty_end = empty_style

    filled_length = round(divs * progress)
    
    if divs <= 1:
        return fill_start if filled_length > 0 else empty_start

    bar = []
    bar.append(fill_start if filled_length > 0 else empty_start)
    for i in range(1, divs - 1):
        bar.append(fill_middle if i < filled_length else empty_middle)
    bar.append(fill_end if filled_length == divs else empty_end)

    return "".join(bar)