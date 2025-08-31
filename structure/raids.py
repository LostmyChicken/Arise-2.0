import json
import logging
import random
import re
import aiosqlite
import discord
from discord.ui import View, Button, Select
from discord import ui
from discord.ext import commands, tasks
import asyncio
import time
from datetime import datetime
from typing import Dict

from utilis.utilis import ELEMENT_WEAKNESSES, getStatHunter, getStatWeapon
from structure.emoji import getClassEmoji, getEmoji
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.player import Player
from utilis.interaction_handler import InteractionHandler

# --- Database Path and Stat Calculation ---
def get_database_path():
    try:
        with open("db.json", "r") as f:
            return json.load(f).get("player", "data/player.db")
    except Exception:
        return "data/player.db"

DATABASE_PATH = get_database_path()

def statCalc(level: int, stat: int):
    return round(stat * (level / 12 + 1)) if level > 1 else stat

def pbar(current, max_val, divs=10):
    if max_val <= 0: return "`[NO HP]`"
    progress = max(0, min(1, current / max_val))
    fill = {'s': getEmoji("GSTART"), 'm': getEmoji("GMID"), 'e': getEmoji("GEND")}
    empty = {'s': getEmoji("EGSTART"), 'm': getEmoji("EGMIDDLE"), 'e': getEmoji("EGEND")}
    
    filled_len = round(divs * progress)
    if divs <= 1: return fill['s'] if filled_len > 0 else empty['s']
    bar = [fill['s'] if filled_len > 0 else empty['s']]
    for i in range(1, divs - 1): bar.append(fill['m'] if i < filled_len else empty['m'])
    bar.append(fill['e'] if filled_len == divs else empty['e'])
    return "".join(bar) + f" `[{int(current)}/{int(max_val)}]`"

# --- Forward Declarations for Type Hinting ---
class Raid: pass
class JoinRaidView: pass
class RaidBattleView: pass


class JoinRaidView(View):
    """Manages the raid lobby before the battle starts."""
    def __init__(self, raid_instance: Raid, bot):
        super().__init__(timeout=300.0) # 5 minute lobby
        self.raid = raid_instance
        self.bot = bot
        self.message = None
        self.force_start_votes = set()

    async def on_timeout(self):
        if not self.raid.members:
            if self.message:
                try:
                    await self.message.edit(content="Raid timed out: No one joined.", embed=None, view=None)
                except (discord.NotFound, discord.HTTPException):
                    # Message was deleted or interaction expired
                    pass
            await self.raid.delete()
        else:
            await self.start_battle()

    async def start_battle(self):
        for child in self.children: child.disabled = True
        if self.message:
            await self.message.edit(content="The shadow is manifesting... The raid is starting!", view=self)

        # Scale boss stats based on joined players
        await self.raid.scale_boss_to_players()
        await self.raid.save()

        battle_view = RaidBattleView(self.raid, self.bot, self.message)
        await battle_view.start()

    @discord.ui.button(label="Join Raid", style=discord.ButtonStyle.success, emoji="⚔️")
    async def join_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        member = interaction.user
        
        if len(self.raid.members) >= 5:
            await interaction.followup.send("This raid is full!", ephemeral=True)
            return
        if member.id in self.raid.members:
            await interaction.followup.send("You have already joined!", ephemeral=True)
            return
        
        player = await Player.get(member.id)
        if not player:
            await interaction.followup.send("You need to `sl start` first.", ephemeral=True)
            return
        if player.inc or player.trade:
            await interaction.followup.send("You are busy and cannot join right now.", ephemeral=True)
            return

        required_slots = ["Party_1", "Party_2", "Party_3"]
        if not all(player.equipped.get(slot) for slot in required_slots):
            await interaction.followup.send("You must have three hunters in your party to join!", ephemeral=True)
            return
            
        # FIX: Pass the discord user/member object to add_member
        await self.raid.add_member(player, member)
        player.inc = True
        await player.save()

        if self.message and self.message.embeds:
            embed = self.message.embeds[0]
            participants = ", ".join([f"<@{mid}>" for mid in self.raid.members.keys()])
            embed.set_field_at(2, name=f"Hunters [{len(self.raid.members)}/5]", value=participants)
            await self.message.edit(embed=embed)
        
        await interaction.followup.send(f"{member.mention} has joined the raid!", ephemeral=False, allowed_mentions=discord.AllowedMentions.none())

    @discord.ui.button(label="0/3 Force Start", style=discord.ButtonStyle.primary, emoji="💨")
    async def force_start_button(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        if member.id not in self.raid.members:
            await interaction.response.send_message("You must join the raid to vote.", ephemeral=True)
            return
        if member.id in self.force_start_votes:
            await interaction.response.send_message("You have already voted.", ephemeral=True)
            return
        
        self.force_start_votes.add(member.id)
        button.label = f"{len(self.force_start_votes)}/3 Force Start"
        await interaction.response.edit_message(view=self)
        
        if len(self.force_start_votes) >= 3:
            self.stop()
            await self.start_battle()


class RaidBattleView(View):
    """Manages the active combat UI and logic for the raid."""
    def __init__(self, raid: Raid, bot, message: discord.Message):
        super().__init__(timeout=900.0) # 15 minutes for the battle
        self.raid = raid
        self.bot = bot
        self.message = message
        self.battle_log = []
        self.boss_retaliate_task = None

    async def start(self):
        await self.raid.start_raid_db()
        self.boss_retaliate_task = asyncio.create_task(self.boss_retaliation_loop())
        embed = self.create_battle_embed()
        if self.message:
            await self.message.edit(content=None, embed=embed, view=self)

    def create_battle_embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"Raid Battle: {self.raid.shadow}", color=discord.Color.dark_purple())
        embed.set_image(url=self.raid.image)

        boss_health_bar = pbar(self.raid.health, self.raid.max_health)
        embed.description = f"**Level**: `{self.raid.level}`\n{getClassEmoji(self.raid.raid_class)} **Element**: `{self.raid.raid_class}`\n**Health**: {boss_health_bar}"

        participants_status = []
        for user_id, data in self.raid.members.items():
            display_name = data.get('name', f"User {user_id}")
            status_emoji = "❤️" if data['health'] > 0 else "💀"
            participants_status.append(f"{status_emoji} {display_name}: `{data['health']}/{data['max_health']}`")
        
        embed.add_field(name="Party Status", value="\n".join(participants_status), inline=False)
        
        if self.battle_log:
            embed.add_field(name="Battle Log", value=">>> " + "\n".join(self.battle_log[-4:]), inline=False)
        
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        if user_id not in self.raid.members:
            await interaction.response.send_message("You are not part of this raid.", ephemeral=True)
            return False
        if self.raid.members[user_id]['health'] <= 0:
            await interaction.response.send_message("You have been defeated and cannot act.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.boss_retaliate_task: self.boss_retaliate_task.cancel()
        await self.end_battle(victory=False, reason="The hunters ran out of time and were overwhelmed.")

    async def calculate_damage(self, attacker, defender):
        base_damage = int((attacker["attack"] ** 2) / (attacker["attack"] + defender["defense"]))
        multiplier = 1.0
        if defender["element"] in ELEMENT_WEAKNESSES.get(attacker["element"], {}).get("effective_against", []): multiplier = 1.5
        elif attacker["element"] in ELEMENT_WEAKNESSES.get(defender["element"], {}).get("effective_against", []): multiplier = 0.5
        return int(base_damage * multiplier * random.uniform(0.9, 1.1))

    async def boss_retaliation_loop(self):
        while not self.is_finished() and self.raid.health > 0:
            await asyncio.sleep(random.randint(20, 30))
            if self.is_finished() or self.raid.health <= 0:
                logging.info("Regular boss retaliation loop ending: battle finished or boss dead")
                break

            alive_players_ids = [uid for uid, pdata in self.raid.members.items() if pdata['health'] > 0]
            if not alive_players_ids: continue

            # Double check boss is still alive before attacking
            if self.raid.health <= 0 or self.is_finished():
                logging.info("Boss attack cancelled: boss is dead or battle finished")
                break

            target_id = random.choice(alive_players_ids)
            target_data = self.raid.members[target_id]
            target_display_name = target_data.get('name', f"User {target_id}")

            damage = await self.calculate_damage({"attack": self.raid.attack, "element": self.raid.raid_class, "defense": self.raid.defense}, target_data)
            target_data['health'] -= damage
            
            self.battle_log.append(f"🩸 The Shadow attacks **{target_display_name}** for `{damage}` damage!")

            if target_data['health'] <= 0:
                target_data['health'] = 0
                self.battle_log.append(f"💀 **{target_display_name}** has been defeated!")
            
            if not any(p['health'] > 0 for p in self.raid.members.values()):
                await self.end_battle(victory=False, reason="The entire party has been defeated.")
                return

            if self.message:
                await self.message.edit(embed=self.create_battle_embed())

    async def end_battle(self, victory: bool, reason: str):
        if self.is_finished(): return

        # Ensure boss is dead and stays dead
        if victory:
            self.raid.health = 0
        self.stop()
        if self.boss_retaliate_task:
            self.boss_retaliate_task.cancel()

        final_embed = discord.Embed(color=discord.Color.green() if victory else discord.Color.red())
        final_embed.title = "Raid Victory!" if victory else "Raid Defeated"
        final_embed.description = reason
        
        total_damage = sum(p.get('damage', 0) for p in self.raid.members.values()) or 1
        
        for user_id, data in self.raid.members.items():
            player_obj = await Player.get(user_id)
            if not player_obj: continue

            damage_dealt = data.get('damage', 0)
            damage_percent = (damage_dealt / total_damage) * 100

            # Enhanced reward calculation based on raid level and performance
            base_gold = 2000 + (self.raid.level * 50)  # Level-scaled base gold
            damage_bonus_gold = int(damage_dealt * 0.15)  # Increased damage bonus
            participation_bonus = 1000 if victory else 500  # Victory/participation bonus
            gold_reward = base_gold + damage_bonus_gold + participation_bonus

            # XP rewards scaled by level and damage
            base_xp = 200 + (self.raid.level * 10)  # Level-scaled base XP
            damage_xp = int(damage_dealt / 8)  # Better XP from damage
            xp_reward = base_xp + damage_xp

            # Trace rewards only on victory, scaled by level and performance
            if victory:
                base_traces = 50 + (self.raid.level * 2)  # Level-scaled traces
                performance_traces = int(damage_dealt / 100)  # Performance bonus
                traces_reward = base_traces + performance_traces
            else:
                traces_reward = 0

            # Bonus rewards for high performers
            if damage_percent >= 40:  # MVP bonus (40%+ damage)
                gold_reward = int(gold_reward * 1.5)
                xp_reward = int(xp_reward * 1.3)
                traces_reward = int(traces_reward * 1.2) if victory else 0
                mvp_bonus = " 🏆 **MVP BONUS!**"
            elif damage_percent >= 25:  # High performer bonus (25%+ damage)
                gold_reward = int(gold_reward * 1.2)
                xp_reward = int(xp_reward * 1.1)
                traces_reward = int(traces_reward * 1.1) if victory else 0
                mvp_bonus = " ⭐ **High Performer!**"
            else:
                mvp_bonus = ""

            # Apply rewards
            player_obj.gold += gold_reward
            if self.message:
                await player_obj.add_xp(self.bot, xp_reward, self.message.channel)
            if traces_reward > 0:
                player_obj.tos += traces_reward

            # Additional rewards for victory
            if victory:
                # Gate keys for completing raids
                key_reward = 1 + (self.raid.level // 25)  # 1 key + bonus for high level raids
                player_obj.key += key_reward

                # Tickets for raid participation
                ticket_reward = 2 + (self.raid.level // 50)  # 2 tickets + bonus
                player_obj.ticket += ticket_reward

            player_obj.inc = False
            player_obj.mIncrease("raid")
            await player_obj.save()

            # Build reward string
            reward_str = f"{getEmoji('gold')} `{gold_reward:,}` | {getEmoji('xp')} `{xp_reward:,}`"
            if traces_reward > 0:
                reward_str += f" | {getEmoji('trace')} `{traces_reward}`"
            if victory:
                reward_str += f" | {getEmoji('key')} `{key_reward}` | {getEmoji('ticket')} `{ticket_reward}`"

            user_display_name = data.get('name', f"User {user_id}")
            final_embed.add_field(
                name=f"{user_display_name}{mvp_bonus}",
                value=f"⚔️ Damage: `{damage_dealt:,}` ({damage_percent:.1f}%)\n🎁 Rewards: {reward_str}",
                inline=False
            )
        
        if self.message:
            await self.message.edit(embed=final_embed, view=None)
        await self.raid.delete()

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger)
    async def raid_attack(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        player_data = self.raid.members[user_id]
        
        damage = await self.calculate_damage(player_data, {"defense": self.raid.defense, "element": self.raid.raid_class, "attack": self.raid.attack})
        self.raid.health -= damage
        player_data['damage'] = player_data.get('damage', 0) + damage
        
        self.battle_log.append(f"⚔️ **{interaction.user.display_name}** attacks for `{damage}` damage!")
        
        if self.raid.health <= 0:
            self.raid.health = 0
            await self.end_battle(victory=True, reason=f"The shadow **{self.raid.shadow}** has been defeated!")
        else:
            if self.message:
                await self.message.edit(embed=self.create_battle_embed())


class Raid:
    def __init__(self, channel, level, shadow, raid_class, health, image, attack, defense, max_health, members=None, started=False, message_id=None, bot=None):
        self.bot = bot
        self.channel = channel
        self.level = level
        self.shadow = shadow
        self.raid_class = raid_class
        self.health = health
        self.image = image
        self.attack = attack
        self.defense = defense
        self.max_health = max_health
        self.members = members or {}
        self.started = started
        self.message_id = message_id

    @staticmethod
    async def clear_all_raids():
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("DELETE FROM raids")
                await db.commit()
            logging.info("Successfully cleared all stale raids from the database.")
        except Exception as e:
            logging.error(f"Failed to clear raids table on startup: {e}")

    @staticmethod
    async def initialize():
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create the table with all required columns
            await db.execute('''
                CREATE TABLE IF NOT EXISTS raids (
                    channel INTEGER PRIMARY KEY, level INTEGER, shadow TEXT, raid_class TEXT,
                    health INTEGER, image TEXT, attack INTEGER, defense INTEGER, max_health INTEGER,
                    members TEXT, started INTEGER, message_id INTEGER,
                    is_world_boss INTEGER DEFAULT 0, is_admin_spawned INTEGER DEFAULT 0, rarity TEXT
                )
            ''')

            # Check for missing columns and add them (for existing databases)
            cursor = await db.execute("PRAGMA table_info(raids)")
            columns = await cursor.fetchall()
            column_names = [column[1] for column in columns]

            # List of required columns with their types
            required_columns = {
                'image': 'TEXT',
                'attack': 'INTEGER',
                'defense': 'INTEGER',
                'max_health': 'INTEGER',
                'message_id': 'INTEGER'
            }

            # Add missing columns
            for column_name, column_type in required_columns.items():
                if column_name not in column_names:
                    await db.execute(f'ALTER TABLE raids ADD COLUMN {column_name} {column_type}')
                    logging.info(f"Added missing '{column_name}' column to raids table")

            await db.commit()

    @classmethod
    async def get(cls, channel_id, bot=None):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            try:
                cursor = await db.execute('SELECT channel, level, shadow, raid_class, health, image, attack, defense, max_health, members, started, message_id, is_world_boss, is_admin_spawned, rarity FROM raids WHERE channel = ?', (channel_id,))
                row = await cursor.fetchone()
                if row:
                    try:
                        members = json.loads(row[9]) if row[9] else {}
                        raid = cls(
                            channel=row[0],
                            level=row[1],
                            shadow=row[2],
                            raid_class=row[3],
                            health=row[4],
                            image=row[5] or "",
                            attack=row[6] or 100,
                            defense=row[7] or 50,
                            max_health=row[8] or row[4],
                            members=members,
                            started=bool(row[10]),
                            message_id=row[11] if len(row) > 11 else None,
                            bot=bot
                        )

                        # Set world boss flags from database
                        if len(row) > 12:
                            raid.is_world_boss = bool(row[12])
                            raid.is_admin_spawned = bool(row[13]) if len(row) > 13 else False
                            raid.rarity = row[14] if len(row) > 14 else None

                        return raid
                    except (IndexError, TypeError) as e:
                        logging.error(f"Error loading raid from database: {e}")
                        return None
            except Exception as e:
                # If the query fails due to missing columns, try a fallback approach
                logging.warning(f"Failed to load raid with full query, trying fallback: {e}")
                try:
                    cursor = await db.execute('SELECT * FROM raids WHERE channel = ?', (channel_id,))
                    row = await cursor.fetchone()
                    if row and len(row) >= 10:  # Minimum required columns
                        members = json.loads(row[9]) if len(row) > 9 and row[9] else {}
                        return cls(
                            channel=row[0],
                            level=row[1],
                            shadow=row[2],
                            raid_class=row[3],
                            health=row[4],
                            image=row[5] if len(row) > 5 else "",
                            attack=row[6] if len(row) > 6 else 100,
                            defense=row[7] if len(row) > 7 else 50,
                            max_health=row[8] if len(row) > 8 else row[4],
                            members=members,
                            started=bool(row[10]) if len(row) > 10 else False,
                            message_id=row[11] if len(row) > 11 else None,
                            bot=bot
                        )
                except Exception as fallback_error:
                    logging.error(f"Fallback raid loading also failed: {fallback_error}")
            return None

    async def save(self):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO raids (channel, level, shadow, raid_class, health, image, attack, defense, max_health, members, started, message_id, is_world_boss, is_admin_spawned, rarity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.channel, self.level, self.shadow, self.raid_class, self.health, self.image,
                self.attack, self.defense, self.max_health, json.dumps(self.members), int(self.started),
                self.message_id, int(getattr(self, 'is_world_boss', False)),
                int(getattr(self, 'is_admin_spawned', False)), getattr(self, 'rarity', None)
            ))
            await db.commit()

    async def delete(self):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM raids WHERE channel = ?", (self.channel,))
            await db.commit()

    async def start_raid_db(self):
        self.started = True
        await self.save()
        
    async def add_member(self, player: Player, user: discord.User):
        # FIX: Changed signature to accept a discord.User object for the name.
        required_slots = ["Party_1", "Party_2", "Party_3"]

        # START WITH PLAYER BASE STATS (this was missing!)
        total_hp = player.hp
        total_attack = player.attack
        total_defense = player.defense
        primary_element = "Neutral"

        # ADD PLAYER EQUIPMENT STATS (weapons, armor, accessories)
        equipment_slots = ["Weapon", "Weapon_2", "Armor", "Accessory", "Accessory_2"]
        for slot in equipment_slots:
            if equipment_id := player.equipped.get(slot):
                if equipment_id in player.inventory:
                    equipment_stats = await getStatWeapon(equipment_id, player.inventory[equipment_id].get("level", 1))
                    if equipment_stats:
                        total_hp += equipment_stats.get('hp', 0)
                        total_attack += equipment_stats.get('attack', 0)
                        total_defense += equipment_stats.get('defense', 0)

        # ADD HUNTER STATS (party members)
        for i, slot_key in enumerate(required_slots):
            hunter_id = player.equipped.get(slot_key)
            if hunter_id:
                hunter_data = player.hunters.get(hunter_id)
                char_info = await HeroManager.get(hunter_id)
                if hunter_data and char_info:
                    if i == 0: primary_element = char_info.classType

                    hunter_stats = await getStatHunter(hunter_id, hunter_data.get('level', 1))
                    total_hp += hunter_stats.hp
                    total_attack += hunter_stats.attack
                    total_defense += hunter_stats.defense

                    # ADD HUNTER WEAPON STATS
                    if (weapon_id := hunter_data.get("weapon")) and (weapon_id in player.inventory):
                        weapon_stats = await getStatWeapon(weapon_id, player.inventory[weapon_id].get("level", 1))
                        total_hp += weapon_stats.get('hp', 0)
                        total_attack += weapon_stats.get('attack', 0)
                        total_defense += weapon_stats.get('defense', 0)

        # FIX: Use user.display_name instead of player.name
        self.members[player.id] = {
            'name': user.display_name, 'health': total_hp, 'max_health': total_hp,
            'attack': total_attack, 'defense': total_defense, 'element': primary_element, 'damage': 0
        }
        await self.save()

    async def remove_member(self, member_id: int):
        if member_id in self.members:
            del self.members[member_id]
            player = await Player.get(member_id)
            if player: 
                player.inc = False
                await player.save()
            await self.save()
            
    @classmethod
    def load_shadow_data(cls, shadow_name):
        try:
            with open("shadows.json", "r") as f:
                return json.load(f)["shadows"].get(shadow_name)
        except (FileNotFoundError, KeyError):
            return None

    @classmethod
    async def spawn_raid(cls, bot, channel: discord.TextChannel, shadow_name: str, level: int):
        shadow_data = cls.load_shadow_data(shadow_name)
        if not shadow_data: return None

        health = statCalc(level, shadow_data["health"])
        attack = statCalc(level, shadow_data["attack"])
        defense = statCalc(level, shadow_data["defense"])
        
        raid = cls(channel.id, level, shadow_name, shadow_data['type'], health, shadow_data['image'], attack, defense, health, bot=bot)
        
        embed = discord.Embed(
            title=f"A Shadow Gate has opened!",
            description=f"**Boss**: {shadow_name}\n**Level**: `{level}`\n{getClassEmoji(raid.raid_class)} **Element**: `{raid.raid_class}`\n\n⏱️ Lobby closes in **5 minutes**",
            color=discord.Color.dark_purple()
        )
        embed.set_image(url=raid.image)
        embed.add_field(name="Statistics", value=f"⚔️ Attack: `{raid.attack}`\n🛡️ Defense: `{raid.defense}`", inline=True)
        embed.add_field(name="Health", value=pbar(raid.health, raid.max_health), inline=False)
        embed.add_field(name="Hunters [0/5]", value="No one has joined yet.", inline=False)
        
        view = JoinRaidView(raid, bot)
        message = await channel.send(embed=embed, view=view)
        view.message = message
        raid.message_id = message.id
        
        await raid.save()
        return raid

    async def scale_boss_to_players(self):
        """Scale boss stats based on the players who joined"""
        if not self.members:
            return

        total_player_power = 0
        player_count = len(self.members)

        # Calculate total player power
        for user_id, member_data in self.members.items():
            player_attack = member_data.get('attack', 100)
            player_defense = member_data.get('defense', 50)
            player_health = member_data.get('max_health', 1000)

            # Calculate player power score
            player_power = (player_attack * 0.4) + (player_defense * 0.3) + (player_health * 0.0003)
            total_player_power += player_power

        # Calculate scaling multiplier based on average player power
        average_player_power = total_player_power / player_count
        base_power = 200  # Expected base player power
        power_ratio = max(0.5, min(3.0, average_player_power / base_power))  # Cap between 0.5x and 3.0x

        # Additional scaling for player count (more players = stronger boss)
        player_count_multiplier = 1.0 + (player_count - 1) * 0.15  # +15% per additional player

        # Final scaling multiplier
        final_multiplier = power_ratio * player_count_multiplier

        # Apply scaling to boss stats
        original_health = self.max_health
        self.health = int(original_health * final_multiplier)
        self.max_health = int(original_health * final_multiplier)
        self.attack = int(self.attack * final_multiplier)
        self.defense = int(self.defense * final_multiplier)

        # Log the scaling for debugging
        logging.info(f"Boss scaled: {player_count} players, avg power: {average_player_power:.1f}, multiplier: {final_multiplier:.2f}")

    @classmethod
    async def spawn_world_boss(cls, bot, channel: discord.TextChannel, boss_data: dict, level: int):
        """Spawn a world boss with enhanced stats and rewards"""
        shadow_data = cls.load_shadow_data(boss_data['name'])
        if not shadow_data:
            # Create dynamic shadow data for world bosses (much stronger than regular raids)
            rarity_stats = {
                'Common': {'health': 2500, 'attack': 300, 'defense': 200},
                'Rare': {'health': 3500, 'attack': 400, 'defense': 250},
                'Epic': {'health': 5000, 'attack': 550, 'defense': 350},
                'Legendary': {'health': 8000, 'attack': 750, 'defense': 500},
                'UR': {'health': 12000, 'attack': 1000, 'defense': 750}
            }

            base_stats = rarity_stats.get(boss_data['rarity'], rarity_stats['Epic'])
            shadow_data = {
                'health': base_stats['health'],
                'attack': base_stats['attack'],
                'defense': base_stats['defense'],
                'type': boss_data['type'],
                'image': boss_data.get('image', 'https://files.catbox.moe/donb98.webp')
            }

        # World bosses have massively enhanced stats based on rarity
        rarity_multipliers = {
            'Common': {'health': 2.0, 'attack': 1.5, 'defense': 1.3},
            'Rare': {'health': 2.5, 'attack': 1.7, 'defense': 1.4},
            'Epic': {'health': 3.0, 'attack': 2.0, 'defense': 1.6},
            'Legendary': {'health': 4.0, 'attack': 2.5, 'defense': 2.0},
            'UR': {'health': 6.0, 'attack': 3.5, 'defense': 3.0}
        }

        multiplier = rarity_multipliers.get(boss_data['rarity'], rarity_multipliers['Epic'])
        health = int(statCalc(level, shadow_data["health"]) * multiplier['health'])
        attack = int(statCalc(level, shadow_data["attack"]) * multiplier['attack'])
        defense = int(statCalc(level, shadow_data["defense"]) * multiplier['defense'])

        raid = cls(channel.id, level, boss_data['name'], boss_data['type'], health, shadow_data['image'], attack, defense, health, bot=bot)
        raid.is_world_boss = True  # Mark as world boss
        raid.rarity = boss_data['rarity']  # Store rarity for rewards
        raid.boss_attack_pattern = 0  # Track attack patterns
        raid.turns_since_special = 0  # Track special attack timing

        embed = discord.Embed(
            title=f"🌍 WORLD BOSS: {boss_data['name']} 🌍",
            description=f"**Rarity**: `{boss_data['rarity']}`\n**Level**: `{level}`\n{getClassEmoji(raid.raid_class)} **Element**: `{raid.raid_class}`\n\n⚔️ **Click to join the battle!**",
            color=discord.Color.gold() if boss_data['rarity'] == 'Legendary' else discord.Color.purple()
        )
        embed.set_image(url=raid.image)
        embed.add_field(name="Boss Statistics", value=f"⚔️ Attack: `{raid.attack:,}`\n🛡️ Defense: `{raid.defense:,}`", inline=True)
        embed.add_field(name="Health", value=pbar(raid.health, raid.max_health), inline=False)
        embed.add_field(name="Hunters [0/10]", value="No brave souls have joined yet...", inline=False)
        embed.set_footer(text="⏰ World Boss will despawn in 30 minutes!")

        view = WorldBossJoinView(raid, bot)
        message = await channel.send(embed=embed, view=view)
        view.message = message
        view.start_timer()  # Start the countdown timer
        raid.message_id = message.id
        await raid.save()

        # Set despawn timer (30 minutes)
        asyncio.create_task(cls._world_boss_despawn_timer(raid, bot, 1800))

        return raid

    @classmethod
    async def spawn_shadow_world_boss(cls, bot, channel: discord.TextChannel, shadow_data: dict, level: int):
        """Spawn a shadow world boss that players can kill to unlock the shadow"""
        from structure.player import Player
        from structure.shadow import Shadow

        # Calculate shadow boss stats (much stronger than regular raids)
        rarity_multipliers = {
            'Common': {'health': 3.0, 'attack': 2.5, 'defense': 2.0},
            'Rare': {'health': 4.0, 'attack': 3.0, 'defense': 2.5},
            'Epic': {'health': 5.5, 'attack': 4.0, 'defense': 3.5},
            'Legendary': {'health': 8.0, 'attack': 6.0, 'defense': 5.0},
            'UR': {'health': 12.0, 'attack': 9.0, 'defense': 8.0}
        }

        multiplier = rarity_multipliers.get(shadow_data['rarity'], rarity_multipliers['Common'])

        # Base stats scaled by level and rarity (minimum values)
        base_health = 2000 + (level * 50)
        base_attack = 200 + (level * 10)
        base_defense = 150 + (level * 8)

        # Apply rarity multipliers to get minimum boss stats
        min_health = int(base_health * multiplier['health'])
        min_attack = int(base_attack * multiplier['attack'])
        min_defense = int(base_defense * multiplier['defense'])

        # Initial stats (will be scaled when battle starts based on participants)
        health = min_health
        attack = min_attack
        defense = min_defense

        # Create the shadow world boss raid
        raid = cls(
            channel.id,
            level,
            shadow_data['name'],
            shadow_data['type'],
            health,
            shadow_data['image'],
            attack,
            defense,
            health,
            bot=bot
        )

        # Mark as world boss for special handling
        raid.is_world_boss = True
        raid.is_admin_spawned = True  # Mark as admin spawned for special handling
        raid.shadow_unlock = shadow_data.get('shadow_unlock', shadow_data['name'].lower())
        raid.rarity = shadow_data['rarity']
        raid.min_health = min_health
        raid.min_attack = min_attack
        raid.min_defense = min_defense
        raid.scaled = False  # Track if boss has been scaled yet

        # Debug logging for world boss flags
        logging.info(f"🌍 World boss flags set: is_world_boss={raid.is_world_boss}, is_admin_spawned={raid.is_admin_spawned}, rarity={raid.rarity}")

        # Create embed using the same style as regular raids but with world boss theming
        embed = discord.Embed(
            title=f"🌍 **SHADOW WORLD BOSS APPEARED!** 🌍",
            description=(
                f"**Shadow**: {shadow_data['name']}\n"
                f"**Type**: {shadow_data['type']}\n"
                f"**Level**: `{level}`\n"
                f"**Rarity**: `{shadow_data['rarity']}`\n\n"
                f"💀 **Defeat this shadow to unlock it for your army!**\n"
                f"⏱️ **Auto-start in 3 minutes (TESTING MODE)**"
            ),
            color=discord.Color.dark_purple()
        )
        embed.set_image(url=shadow_data['image'])
        embed.add_field(name="Boss Statistics", value=f"⚔️ Attack: `{raid.attack:,}`\n🛡️ Defense: `{raid.defense:,}`", inline=True)
        embed.add_field(name="Health", value=pbar(raid.health, raid.max_health), inline=False)
        embed.add_field(name="Hunters [0/10]", value="No brave souls have joined yet...", inline=False)
        embed.set_footer(text="🌍 World Boss • Defeat to unlock shadow for all participants!")

        # Use the same view as regular raids but with world boss functionality
        view = WorldBossJoinView(raid, bot)
        message = await channel.send(embed=embed, view=view)
        view.message = message

        # No custom timer - use Discord's built-in timeout like regular raids
        logging.info(f"🌍 World boss will auto-start in 3 minutes via Discord timeout")

        raid.message_id = message.id
        await raid.save()

        # Set despawn timer (30 minutes)
        asyncio.create_task(cls._world_boss_despawn_timer(raid, bot, 1800))

        return raid

    @classmethod
    async def _world_boss_despawn_timer(cls, raid, bot, timeout: int):
        """Handle world boss despawn after timeout"""
        await asyncio.sleep(timeout)

        # Check if boss is still active
        current_raid = await cls.get(raid.channel, bot)
        if current_raid and current_raid.health > 0:
            # Boss despawned due to timeout - update the original message
            channel = bot.get_channel(raid.channel)
            if channel and raid.message_id:
                try:
                    message = await channel.fetch_message(raid.message_id)
                    embed = discord.Embed(
                        title="🌫️ World Boss Despawned",
                        description=f"**{raid.shadow}** has retreated back to the shadows...\n\nBetter luck next time, hunters!",
                        color=discord.Color.dark_grey()
                    )
                    embed.set_image(url=raid.image)
                    embed.set_footer(text="The world boss has vanished into the void...")
                    await message.edit(embed=embed, view=None)
                except (discord.NotFound, discord.HTTPException):
                    pass  # Message was deleted or bot lacks permissions

            # Remove from world boss manager
            world_boss_manager = get_world_boss_manager(bot)
            world_boss_manager.remove_boss(channel.guild.id if channel else 0)

            await raid.delete()

    def scale_world_boss_to_participants(self):
        """Scale world boss stats based on participant power level"""
        if not hasattr(self, 'is_world_boss') or not self.is_world_boss or self.scaled:
            return

        if not self.members:
            return

        # Calculate average participant stats
        total_attack = 0
        total_defense = 0
        total_health = 0
        participant_count = len(self.members)

        for member_data in self.members.values():
            total_attack += member_data.get('attack', 100)
            total_defense += member_data.get('defense', 100)
            total_health += member_data.get('health', 1000)

        avg_attack = total_attack / participant_count
        avg_defense = total_defense / participant_count
        avg_health = total_health / participant_count

        # Calculate scaling factor based on participant power
        # Scale boss to be challenging but not impossible
        participant_power = (avg_attack + avg_defense + avg_health/10) / 3

        # Scaling formula: boss should be 2-4x stronger than average participant
        base_scaling = max(2.0, min(4.0, participant_power / 200))

        # Additional scaling based on participant count (more players = stronger boss)
        count_scaling = 1.0 + (participant_count - 1) * 0.3  # +30% per additional player

        total_scaling = base_scaling * count_scaling

        # Apply scaling but ensure minimums
        new_health = max(self.min_health, int(self.min_health * total_scaling))
        new_attack = max(self.min_attack, int(self.min_attack * total_scaling))
        new_defense = max(self.min_defense, int(self.min_defense * total_scaling))

        # Cap maximum scaling to prevent impossible fights
        max_health_cap = self.min_health * 6  # Max 6x base health
        max_attack_cap = self.min_attack * 4   # Max 4x base attack
        max_defense_cap = self.min_defense * 4 # Max 4x base defense

        self.health = min(new_health, max_health_cap)
        self.max_health = self.health
        self.attack = min(new_attack, max_attack_cap)
        self.defense = min(new_defense, max_defense_cap)

        self.scaled = True

        print(f"🌍 World Boss scaled: {participant_count} participants, power factor {total_scaling:.2f}")
        print(f"   Health: {self.min_health:,} → {self.health:,}")
        print(f"   Attack: {self.min_attack:,} → {self.attack:,}")
        print(f"   Defense: {self.min_defense:,} → {self.defense:,}")

class ShadowWorldBossBattle(discord.ui.View):
    def __init__(self, raid, bot):
        super().__init__(timeout=1800)  # 30 minutes battle time
        self.raid = raid
        self.bot = bot
        self.battle_active = True
        self.last_attack_time = {}  # user_id -> timestamp

    async def start_battle(self, message):
        """Start the shadow world boss battle"""
        # Scale boss based on participants before battle starts
        self.raid.scale_world_boss_to_participants()

        # Create battle embed
        embed = discord.Embed(
            title=f"⚔️ **SHADOW HUNT IN PROGRESS** ⚔️",
            description=(
                f"**Target**: {self.raid.shadow}\n"
                f"**Hunters**: {len(self.raid.members)}\n\n"
                f"💀 **Defeat this shadow to unlock it for your army!**"
            ),
            color=discord.Color.red()
        )

        # Add health bar
        health_bar = self.create_health_bar(self.raid.health, self.raid.max_health)
        embed.add_field(
            name=f"❤️ {self.raid.shadow} Health",
            value=f"{health_bar}\n`{self.raid.health:,} / {self.raid.max_health:,} HP`",
            inline=False
        )

        # Add participants
        participants_list = []
        for user_id, data in self.raid.members.items():
            user = self.bot.get_user(user_id)
            if user:
                participants_list.append(f"⚔️ {user.display_name}: `{data['damage']:,}` damage")

        if participants_list:
            embed.add_field(
                name="👥 Shadow Hunters",
                value="\n".join(participants_list[:10]),  # Show top 10
                inline=False
            )

        # Add battle log if available
        if hasattr(self, 'battle_log') and self.battle_log:
            log_text = "\n".join(self.battle_log[-5:])  # Show last 5 entries
            embed.add_field(
                name="⚔️ Battle Log",
                value=log_text,
                inline=False
            )

        embed.set_image(url=self.raid.image)
        embed.set_footer(text="🌍 Shadow World Boss • Attack to deal damage!")

        # Update message with battle interface
        await message.edit(embed=embed, view=self)

        # Start boss counter-attack loop
        asyncio.create_task(self.boss_counter_attack_loop(message))

    def create_health_bar(self, current_hp, max_hp):
        """Create a visual health bar"""
        if max_hp <= 0:
            return "💀 DEFEATED"

        percentage = current_hp / max_hp
        bar_length = 20
        filled_length = int(bar_length * percentage)

        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        return f"[{bar}] {percentage:.1%}"



    async def boss_counter_attack_loop(self, message):
        """Boss attacks players periodically"""
        while self.battle_active and self.raid.health > 0:
            await asyncio.sleep(8)  # Boss attacks every 8 seconds

            if not self.battle_active or self.raid.health <= 0:
                break

            # Boss attacks a random participant
            if self.raid.members:
                target_id = random.choice(list(self.raid.members.keys()))
                target = self.bot.get_user(target_id)

                if target:
                    # Calculate boss damage
                    boss_damage = random.randint(self.raid.attack // 2, self.raid.attack)

                    # Add counter-attack to battle log instead of sending separate message
                    if not hasattr(self, 'battle_log'):
                        self.battle_log = []

                    self.battle_log.append(f"💥 **{self.raid.shadow}** counter-attacked **{target.display_name}** for **{boss_damage:,}** damage!")

                    # Keep only last 10 battle log entries
                    if len(self.battle_log) > 10:
                        self.battle_log = self.battle_log[-10:]

    async def update_battle_display(self, message):
        """Update the battle embed with current stats"""
        embed = discord.Embed(
            title=f"⚔️ **SHADOW HUNT IN PROGRESS** ⚔️",
            description=(
                f"**Target**: {self.raid.shadow}\n"
                f"**Hunters**: {len(self.raid.members)}\n\n"
                f"💀 **Defeat this shadow to unlock it for your army!**"
            ),
            color=discord.Color.red()
        )

        # Add health bar
        health_bar = self.create_health_bar(self.raid.health, self.raid.max_health)
        embed.add_field(
            name=f"❤️ {self.raid.shadow} Health",
            value=f"{health_bar}\n`{self.raid.health:,} / {self.raid.max_health:,} HP`",
            inline=False
        )

        # Add top damage dealers
        sorted_members = sorted(
            self.raid.members.items(),
            key=lambda x: x[1]['damage'],
            reverse=True
        )

        participants_list = []
        for user_id, data in sorted_members[:10]:  # Top 10
            user = self.bot.get_user(user_id)
            if user:
                participants_list.append(f"⚔️ {user.display_name}: `{data['damage']:,}` damage")

        if participants_list:
            embed.add_field(
                name="👥 Top Shadow Hunters",
                value="\n".join(participants_list),
                inline=False
            )

        embed.set_image(url=self.raid.image)
        embed.set_footer(text="🌍 Shadow World Boss • Attack to deal damage!")

        try:
            await message.edit(embed=embed, view=self)
        except:
            pass  # Message might be deleted or edited by another process

    async def handle_victory(self, interaction):
        """Handle shadow world boss victory and shadow unlocking"""
        self.battle_active = False

        # Create victory embed
        victory_embed = discord.Embed(
            title="🎉 **SHADOW DEFEATED!** 🎉",
            description=f"**{self.raid.shadow}** has been vanquished by the shadow hunters!",
            color=discord.Color.gold()
        )

        # Calculate total damage
        total_damage = sum(data['damage'] for data in self.raid.members.values())

        victory_embed.add_field(
            name="📊 Battle Statistics",
            value=(
                f"**Total Damage**: {total_damage:,}\n"
                f"**Hunters**: {len(self.raid.members)}\n"
                f"**Shadow Unlocked**: {self.raid.shadow}"
            ),
            inline=False
        )

        # Track shadow defeat for arise command (don't auto-unlock)
        from structure.player import Player
        eligible_players = []

        for user_id in self.raid.members.keys():
            player = await Player.get(user_id)
            if player:
                # Track boss defeat for arise command eligibility
                player.add_boss_defeat(self.raid.shadow_unlock)
                eligible_players.append(f"⚔️ {self.bot.get_user(user_id).display_name}")

                # Send DM notification about arise eligibility
                try:
                    user = self.bot.get_user(user_id)
                    if user:
                        arise_embed = discord.Embed(
                            title="⚔️ **SHADOW DEFEATED!** ⚔️",
                            description=f"You have defeated **{self.raid.shadow}** and can now use the arise command!",
                            color=discord.Color.purple()
                        )
                        arise_embed.add_field(
                            name="🔮 Next Step",
                            value=f"Use `sl arise {self.raid.shadow_unlock}` to add this shadow to your army!",
                            inline=False
                        )
                        arise_embed.add_field(
                            name="Shadow Details",
                            value=f"**Name**: {self.raid.shadow}\n**Type**: Shadow\n**Rarity**: Unlockable",
                            inline=False
                        )
                        arise_embed.set_footer(text="Use the arise command to claim your shadow!")
                        await user.send(embed=arise_embed)
                except:
                    pass  # DM failed, continue

                try:
                    await player.save()
                except Exception as e:
                    print(f"Error saving player {user_id} after shadow defeat: {e}")
                    # Continue without saving to prevent blocking

        if eligible_players:
            victory_embed.add_field(
                name="⚔️ Eligible for Arise Command",
                value="\n".join(eligible_players[:15]) + f"\n\n🔮 **Use `sl arise {self.raid.shadow_unlock}` to claim your shadow!**",  # Show up to 15 players
                inline=False
            )

        victory_embed.set_image(url=self.raid.image)
        victory_embed.set_footer(text="🌍 Shadow World Boss • Victory achieved!")

        # Update message
        await interaction.response.edit_message(embed=victory_embed, view=None)

        # Clean up raid
        await self.raid.delete()

        # Remove from world boss manager (mark as defeated)
        world_boss_manager = get_world_boss_manager(self.bot)
        world_boss_manager.remove_boss(interaction.guild.id, defeated=True)


class WorldBossJoinView(ui.View):
    """Enhanced join view for world bosses - using same logic as regular raids"""

    def __init__(self, raid: Raid, bot: commands.Bot):
        super().__init__(timeout=180.0)  # 3 minutes like regular raids (was 30 seconds)
        self.raid = raid
        self.bot = bot
        self.message = None
        self.force_start_votes = set()  # Track force start votes

    async def on_timeout(self):
        """Handle timeout - same logic as regular raids"""
        if not self.raid.members:
            # No one joined, despawn with embed
            if self.message:
                try:
                    embed = discord.Embed(
                        title="🌍 **WORLD BOSS DESPAWNED**",
                        description=f"**{self.raid.shadow}** has vanished into the shadows...\n\n*No brave hunters stepped forward to challenge it.*",
                        color=discord.Color.orange()
                    )
                    embed.set_image(url=self.raid.image)
                    embed.add_field(
                        name="⏰ Timeout",
                        value="The world boss waited 3 minutes but no one joined the battle.",
                        inline=False
                    )
                    embed.set_footer(text="World bosses will return when hunters are ready for the challenge!")

                    await self.message.edit(content=None, embed=embed, view=None)
                except (discord.NotFound, discord.HTTPException):
                    pass
            await self.raid.delete()
            logging.info("🌍 World boss despawned - no players joined")
        else:
            # Players joined, start battle
            logging.info(f"🌍 World boss timeout - starting battle with {len(self.raid.members)} players")
            await self.start_battle()

    async def start_battle(self):
        """Start the world boss battle - same logic as regular raids"""
        # Disable all buttons
        for child in self.children:
            child.disabled = True

        if self.message:
            await self.message.edit(content="The world boss is manifesting... The battle is starting!", view=self)

        # Scale boss stats based on joined players (same as regular raids)
        await self.raid.scale_boss_to_players()
        await self.raid.save()

        # Create world boss battle view
        battle_view = WorldBossBattleView(self.raid, self.bot, self.message)
        await battle_view.start()

        logging.info(f"🌍 World boss battle started with {len(self.raid.members)} players")

    async def auto_start_battle(self):
        """Automatically start the battle when timer expires"""
        try:
            logging.info(f"🌍 AUTO-STARTING WORLD BOSS BATTLE FOR {self.raid.shadow}")
            logging.info(f"🔍 DEBUG: battle_started={self.battle_started}, raid.started={getattr(self.raid, 'started', 'NOT_SET')}")

            # Double-check battle hasn't started (with additional safety checks)
            if self.battle_started or getattr(self.raid, 'started', False):
                logging.info("❌ Battle already started, skipping auto-start")
                return

            # Check if we have enough players (world bosses always need at least 1 player)
            is_admin_spawned = getattr(self.raid, 'is_admin_spawned', False)
            min_players_needed = 1  # Always require at least 1 player for world bosses

            if len(self.raid.members) < min_players_needed:
                logging.info(f"❌ Not enough players joined ({len(self.raid.members)}/{min_players_needed}), cannot start battle")
                return

            # Set battle started flag FIRST to prevent race conditions
            self.battle_started = True
            self.raid.started = True
            logging.info("✅ Battle flags set - battle_started = True")

            # Cancel the timer task to prevent further updates
            if self.timer_task:
                self.timer_task.cancel()
                logging.info("✅ Timer task cancelled")

            # Scale boss stats based on joined players
            try:
                await self.raid.scale_boss_to_players()
                await self.raid.save()
                logging.info("✅ Boss stats scaled and saved")
            except Exception as e:
                logging.error(f"❌ Error scaling boss: {e}")

            # Create battle view with error handling
            try:
                battle_view = WorldBossBattleView(self.raid, self.bot, self.message)
                logging.info(f"✅ WorldBossBattleView created with {len(battle_view.children)} buttons")

                # Verify the battle view has buttons
                if len(battle_view.children) == 0:
                    logging.error("❌ WorldBossBattleView has no buttons!")
                    # Reset battle flags if view creation failed
                    self.battle_started = False
                    self.raid.started = False
                    return
                else:
                    for i, child in enumerate(battle_view.children):
                        if hasattr(child, 'label'):
                            logging.info(f"   Button {i+1}: {child.label}")

            except Exception as e:
                logging.error(f"❌ Error creating WorldBossBattleView: {e}")
                # Reset battle flags if view creation failed
                self.battle_started = False
                self.raid.started = False
                return

            # Create battle embed
            try:
                embed = battle_view.create_battle_embed()
                logging.info("✅ Battle embed created")
            except Exception as e:
                logging.error(f"❌ Error creating battle embed: {e}")
                return

            # Update message with battle view
            if self.message:
                try:
                    await self.message.edit(embed=embed, view=battle_view)
                    logging.info("✅ MESSAGE SUCCESSFULLY UPDATED WITH BATTLE VIEW AND BUTTONS")

                    # Start the battle retaliation loop
                    if hasattr(battle_view, 'boss_retaliation_loop'):
                        battle_view.boss_retaliate_task = asyncio.create_task(battle_view.boss_retaliation_loop())
                        logging.info("✅ Boss retaliation loop started")

                except discord.NotFound:
                    logging.error("❌ Message not found - it may have been deleted")
                    # Reset battle flags if message update failed
                    self.battle_started = False
                    self.raid.started = False
                    return
                except discord.HTTPException as e:
                    logging.error(f"❌ HTTP error editing message: {e}")
                    # Reset battle flags if message update failed
                    self.battle_started = False
                    self.raid.started = False
                    return
                except Exception as e:
                    logging.error(f"❌ Unexpected error editing message: {e}")
                    # Reset battle flags if message update failed
                    self.battle_started = False
                    self.raid.started = False
                    return
            else:
                logging.error("❌ No message to update!")
                # Reset battle flags if no message
                self.battle_started = False
                self.raid.started = False
                return

            # Stop this view to prevent further interactions
            self.stop()
            logging.info("✅ WorldBossJoinView stopped")

        except Exception as e:
            logging.error(f"❌ CRITICAL ERROR in auto_start_battle: {e}")
            import traceback
            traceback.print_exc()

            # Reset battle started flag if there was an error
            self.battle_started = False

            # Notify all participants that the battle has auto-started
            participant_mentions = []
            for user_id in self.raid.members.keys():
                participant_mentions.append(f"<@{user_id}>")

            if participant_mentions:
                notification_embed = discord.Embed(
                    title="⏰ **WORLD BOSS BATTLE AUTO-STARTED!** ⏰",
                    description=f"The timer expired! The battle against **{self.raid.shadow}** has begun!\n\n🔗 **[Jump to Battle]({self.message.jump_url})**",
                    color=discord.Color.orange()
                )
                notification_embed.set_footer(text="Click the link above to join the battle!")

                # Send notification in the same channel
                try:
                    await self.message.channel.send(
                        content=" ".join(participant_mentions),
                        embed=notification_embed
                    )
                except Exception as e:
                    logging.error(f"Failed to send auto-start notification: {e}")

        # Start enhanced boss retaliation system for auto-started battles
        battle_view.enhanced_boss_retaliate_task = asyncio.create_task(battle_view.enhanced_boss_retaliate_loop())

        # Remove from world boss manager (not defeated, just started)
        world_boss_manager = get_world_boss_manager(self.bot)
        world_boss_manager.remove_boss(self.message.guild.id if self.message else 0, defeated=False)

        self.stop()

    async def despawn_due_to_inactivity(self):
        """Despawn the world boss due to 5 minutes of inactivity"""
        if self.battle_started:
            return

        embed = discord.Embed(
            title="🌍 **WORLD BOSS DESPAWNED**",
            description="The world boss has disappeared due to lack of activity...\n\n*No hunters showed interest in the battle.*",
            color=discord.Color.orange()
        )
        embed.set_footer(text="World bosses will return when hunters are more active!")

        if self.message:
            await self.message.edit(embed=embed, view=None)

        # Remove from world boss manager
        world_boss_manager = get_world_boss_manager(self.bot)
        world_boss_manager.remove_boss(self.message.guild.id if self.message else 0, defeated=False)

        # Clean up
        await self.raid.delete()
        self.stop()

    async def despawn_no_players(self):
        """Despawn the world boss when no players joined after 30 minutes"""
        if self.battle_started:
            return

        embed = discord.Embed(
            title="🌍 **WORLD BOSS DESPAWNED**",
            description="The world boss has vanished after waiting too long...\n\n*No brave hunters stepped forward to challenge it.*",
            color=discord.Color.red()
        )
        embed.set_footer(text="The next world boss will appear when conditions are right!")

        if self.message:
            await self.message.edit(embed=embed, view=None)

        # Remove from world boss manager
        world_boss_manager = get_world_boss_manager(self.bot)
        world_boss_manager.remove_boss(self.message.guild.id if self.message else 0, defeated=False)

        # Clean up
        await self.raid.delete()
        self.stop()

    async def update_embed(self):
        """Update the embed with current timer and vote status"""
        if not self.message:
            return

        embed = discord.Embed(
            title=f"🌍 WORLD BOSS: {self.raid.shadow} 🌍",
            description=f"**Rarity**: `{getattr(self.raid, 'rarity', 'Epic')}`\n**Level**: `{self.raid.level}`\n{getClassEmoji(self.raid.raid_class)} **Element**: `{self.raid.raid_class}`\n\n⚔️ **Click to join the battle!**",
            color=discord.Color.gold() if getattr(self.raid, 'rarity', '') == 'Legendary' else discord.Color.purple()
        )
        embed.set_image(url=self.raid.image)
        embed.add_field(name="Boss Statistics", value=f"⚔️ Attack: `{self.raid.attack:,}`\n🛡️ Defense: `{self.raid.defense:,}`", inline=True)
        embed.add_field(name="Health", value=pbar(self.raid.health, self.raid.max_health), inline=False)

        # Show joined hunters
        hunter_list = []
        for user_id, data in self.raid.members.items():
            hunter_list.append(f"⚔️ {data['name']}")

        hunters_text = "\n".join(hunter_list) if hunter_list else "No brave souls have joined yet..."
        embed.add_field(name=f"Hunters [{len(self.raid.members)}/10]", value=hunters_text, inline=False)

        # Update timer
        time_remaining = max(0, self.start_time - time.time())
        if time_remaining > 0:
            minutes = int(time_remaining // 60)
            seconds = int(time_remaining % 60)
            timer_text = f"⏰ **Auto-start in**: `{minutes}m {seconds}s`"

            if len(self.raid.members) >= 3:
                votes_needed = max(1, len(self.raid.members) // 2)
                current_votes = len(self.force_start_votes)
                timer_text += f"\n🗳️ **Force Start**: `{current_votes}/{votes_needed}` votes"

            embed.add_field(name="⏱️ Battle Timer", value=timer_text, inline=False)

        embed.set_footer(text="⏰ World Boss will despawn in 30 minutes if not defeated!")

        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass  # Message might be deleted or bot lacks permissions

    def stop(self):
        """Stop the view and cancel timer"""
        if self.timer_task:
            self.timer_task.cancel()
        super().stop()

    @ui.button(label="Join World Boss", style=discord.ButtonStyle.danger, emoji="🌍")
    async def join_world_boss(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()

        logging.info(f"🌍 {interaction.user.display_name} clicked join world boss button")

        # Update activity tracker
        self.last_activity = time.time()

        player = await Player.get(interaction.user.id)
        if not player:
            await interaction.followup.send("❌ **You need to create a character first!** Use `/start` to begin your journey.", ephemeral=True)
            return

        if interaction.user.id in self.raid.members:
            await interaction.followup.send("⚔️ **You're already in this world boss battle!**", ephemeral=True)
            return

        if len(self.raid.members) >= 10:  # World bosses allow more players
            await interaction.followup.send("❌ **This world boss battle is full!** (10/10 hunters)", ephemeral=True)
            return

        # Check if player has required party setup
        required_slots = ["Party_1", "Party_2", "Party_3"]
        equipped_hunters = [player.equipped.get(slot) for slot in required_slots if player.equipped.get(slot)]

        if len(equipped_hunters) < 3:
            await interaction.followup.send("❌ **You need a full party of 3 hunters to join a world boss!** Use `/profile` → Team Setup to configure your party.", ephemeral=True)
            return

        await self.raid.add_member(player, interaction.user)

        # Update the embed - simple version like regular raids
        embed = discord.Embed(
            title=f"🌍 WORLD BOSS: {self.raid.shadow} 🌍",
            description=f"**Rarity**: `{getattr(self.raid, 'rarity', 'Epic')}`\n**Level**: `{self.raid.level}`\n{getClassEmoji(self.raid.raid_class)} **Element**: `{self.raid.raid_class}`\n\n⚔️ **Click to join the battle!**",
            color=discord.Color.gold() if getattr(self.raid, 'rarity', '') == 'Legendary' else discord.Color.purple()
        )
        embed.set_image(url=self.raid.image)
        embed.add_field(name="Boss Statistics", value=f"⚔️ Attack: `{self.raid.attack:,}`\n🛡️ Defense: `{self.raid.defense:,}`", inline=True)
        embed.add_field(name="Health", value=pbar(self.raid.health, self.raid.max_health), inline=False)

        # Show joined hunters
        hunter_list = []
        for user_id, data in self.raid.members.items():
            hunter_list.append(f"⚔️ {data['name']}")

        hunters_text = "\n".join(hunter_list) if hunter_list else "No brave souls have joined yet..."
        embed.add_field(name=f"Hunters [{len(self.raid.members)}/10]", value=hunters_text, inline=False)
        embed.set_footer(text="⏰ World Boss will auto-start in 3 minutes!")

        await interaction.edit_original_response(embed=embed, view=self)
        await interaction.followup.send(f"✅ **{interaction.user.display_name}** joined the world boss battle!", ephemeral=True)

    @ui.button(label="Force Start", style=discord.ButtonStyle.secondary, emoji="💨")
    async def force_start_world_boss(self, interaction: discord.Interaction, button: ui.Button):
        """Allow players to vote to force start the battle early"""
        await interaction.response.defer()

        # Check if battle already started
        if getattr(self.raid, 'started', False):
            await interaction.followup.send("⚔️ **The battle has already started!**", ephemeral=True)
            return

        # Check if no players joined
        if not self.raid.members:
            await interaction.followup.send("❌ **No players have joined yet!**", ephemeral=True)
            return

        # Special handling for admin spawned bosses - admins can instantly start
        from utilis.admin import is_bot_admin
        is_admin_spawned = getattr(self.raid, 'is_admin_spawned', False)

        if is_admin_spawned and is_bot_admin(interaction.user.id):
            # Admin can instantly start admin spawned bosses
            await interaction.followup.send(f"👑 **Admin Force Start!** Starting world boss battle now...", ephemeral=False)
            await self.start_battle()
            return

        # Regular force start voting system
        # Check if user is in the battle
        if interaction.user.id not in self.raid.members:
            await interaction.followup.send("❌ **You must join the world boss battle to vote for force start!**", ephemeral=True)
            return

        # Check if already voted
        if interaction.user.id in self.force_start_votes:
            await interaction.followup.send("⚠️ **You have already voted to force start!**", ephemeral=True)
            return

        # Add vote
        self.force_start_votes.add(interaction.user.id)
        votes_needed = max(2, len(self.raid.members) // 2)  # Need at least 2 votes or half the players

        # Update button label
        button.label = f"💨 Force Start ({len(self.force_start_votes)}/{votes_needed})"

        if len(self.force_start_votes) >= votes_needed:
            # Enough votes, start the battle
            await interaction.edit_original_response(view=self)
            await interaction.followup.send(f"🚀 **Force start activated!** Starting world boss battle now...", ephemeral=False)
            await self.start_battle()
        else:
            await interaction.edit_original_response(view=self)
            await interaction.followup.send(f"🗳️ **Vote registered!** ({len(self.force_start_votes)}/{votes_needed} votes needed to force start)", ephemeral=True)



class WorldBossBattleView(RaidBattleView):
    """Enhanced battle view for world bosses with interactive combat and boss attacks"""

    def __init__(self, raid: 'Raid', bot: commands.Bot, message: discord.Message):
        super().__init__(raid, bot, message)
        self.battle_active = True  # Battle is active when view is created
        self.boss_attack_cooldown = 0  # Tracks boss attack timing
        self.boss_special_cooldown = 0  # Tracks boss special attack timing
        self.boss_enrage_threshold = 0.3  # Boss enrages at 30% health
        self.is_enraged = False
        self.boss_abilities = self.get_boss_abilities()
        self.last_update_time = 0  # Track last UI update to prevent rate limiting
        self.player_attack_cooldowns = {}  # Track individual player attack cooldowns
        self.last_attack_time = {}  # Track last attack time for cooldowns

        # Scale boss based on participants when battle view is created
        if hasattr(self.raid, 'scale_world_boss_to_participants'):
            self.raid.scale_world_boss_to_participants()

        # Remove the parent class's attack button to avoid conflicts
        # We'll use our own attack_button method instead
        for item in self.children[:]:  # Create a copy to iterate over
            if hasattr(item, 'callback') and hasattr(item.callback, 'callback') and item.callback.callback.__name__ == 'raid_attack':
                self.remove_item(item)
                break

        # Attack button is added via @ui.button decorator below

    def get_boss_abilities(self):
        """Get boss-specific abilities based on rarity and type"""
        rarity = getattr(self.raid, 'rarity', 'Epic')
        boss_type = self.raid.raid_class.lower()

        abilities = {
            'basic_attacks': [
                {'name': 'Crushing Blow', 'damage_multiplier': 1.2, 'description': 'deals massive damage'},
                {'name': 'Shadow Strike', 'damage_multiplier': 1.0, 'description': 'strikes from the shadows'},
                {'name': 'Elemental Burst', 'damage_multiplier': 1.1, 'description': f'unleashes {boss_type} energy'},
            ],
            'special_attacks': [
                {'name': 'Devastating Roar', 'damage_multiplier': 1.5, 'description': 'roars with devastating power', 'cooldown': 3},
                {'name': 'Area Devastation', 'damage_multiplier': 1.3, 'description': 'attacks all hunters', 'targets_all': True, 'cooldown': 4},
                {'name': 'Elemental Storm', 'damage_multiplier': 1.4, 'description': f'summons a {boss_type} storm', 'cooldown': 5},
            ]
        }

        # Legendary bosses get enhanced abilities
        if rarity == 'Legendary':
            abilities['special_attacks'].append({
                'name': 'World Shatter', 'damage_multiplier': 2.0, 'description': 'attempts to shatter reality itself',
                'targets_all': True, 'cooldown': 6
            })

        return abilities

    def stop_all_boss_activities(self):
        """Stop all boss-related tasks and activities"""
        if hasattr(self, 'boss_retaliate_task') and self.boss_retaliate_task:
            self.boss_retaliate_task.cancel()
            self.boss_retaliate_task = None
        if hasattr(self, 'enhanced_boss_retaliate_task') and self.enhanced_boss_retaliate_task:
            self.enhanced_boss_retaliate_task.cancel()
            self.enhanced_boss_retaliate_task = None
        # Mark boss as dead to prevent any further actions
        self.raid.health = 0
        # Set a flag to indicate battle is completely over
        self._battle_ended = True

    @ui.button(label="Attack World Boss", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def attack_world_boss(self, interaction: discord.Interaction, button: ui.Button):
        """World boss attack callback method"""
        if self.is_finished() or not self.battle_active:
            await InteractionHandler.safe_response(interaction, content="❌ **This battle has ended!**", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id not in self.raid.members:
            await InteractionHandler.safe_response(interaction, content="❌ **You are not part of this world boss battle!**", ephemeral=True)
            return

        player_data = self.raid.members[user_id]
        if player_data['health'] <= 0:
            await InteractionHandler.safe_response(interaction, content="💀 **You are defeated and cannot attack!**", ephemeral=True)
            return

        # Check individual player attack cooldown (0.5 seconds)
        import time
        current_time = time.time()
        if user_id in self.player_attack_cooldowns:
            if current_time - self.player_attack_cooldowns[user_id] < 0.5:
                await InteractionHandler.safe_response(interaction, content="⏰ **Attack too fast!** Wait 0.5 seconds between attacks.", ephemeral=True)
                return

        self.player_attack_cooldowns[user_id] = current_time

        # Calculate damage
        damage = await self.calculate_damage(player_data, {
            "defense": self.raid.defense,
            "element": self.raid.raid_class,
            "attack": self.raid.attack
        })

        # Apply damage
        self.raid.health -= damage
        player_data['damage'] = player_data.get('damage', 0) + damage

        self.battle_log.append(f"⚔️ **{interaction.user.display_name}** attacks for `{damage}` damage!")

        # Save raid data (batch with other operations to reduce API calls)
        try:
            await self.raid.save()
        except:
            pass  # Continue even if save fails

        # Check for victory using world boss victory handler
        if self.raid.health <= 0:
            self.raid.health = 0
            await self.handle_victory(interaction)
            return

        # Send attack confirmation first (before any other operations)
        await InteractionHandler.safe_defer(interaction)

        # Update battle display with rate limiting protection (max once per 2 seconds)
        if self.message and (current_time - self.last_update_time) >= 2.0:
            try:
                await self.message.edit(embed=self.create_battle_embed())
                self.last_update_time = current_time
            except discord.errors.NotFound:
                pass  # Message was deleted
            except discord.errors.HTTPException:
                pass  # Rate limited or other HTTP error

    async def handle_victory(self, interaction):
        """Handle world boss victory with shadow unlocking and rewards"""
        # CRITICAL: Immediately stop all boss activities and disable view
        self.battle_active = False
        self.stop_all_boss_activities()
        self.stop()

        # CRITICAL: Disable all buttons to prevent any further interaction
        for item in self.children:
            item.disabled = True

        # Create victory embed
        victory_embed = discord.Embed(
            title="🎉 **SHADOW WORLD BOSS DEFEATED!** 🎉",
            description=f"**{self.raid.shadow}** has been vanquished by the shadow hunters!",
            color=discord.Color.gold()
        )

        # Calculate total damage
        total_damage = sum(data['damage'] for data in self.raid.members.values())

        victory_embed.add_field(
            name="📊 Battle Statistics",
            value=(
                f"**Total Damage**: {total_damage:,}\n"
                f"**Hunters**: {len(self.raid.members)}\n"
                f"**Shadow Unlocked**: {self.raid.shadow}"
            ),
            inline=False
        )

        # Handle shadow unlocking - 25% RNG SYSTEM (as requested)
        from structure.player import Player
        from structure.shadow import Shadow
        import random

        unlocked_players = []
        failed_players = []
        already_owned_players = []
        eligible_players = []  # Players with >1% damage

        # Get the shadow data
        shadow = await Shadow.get(self.raid.shadow_unlock)

        # Calculate total damage and determine eligible players
        total_damage = sum(data['damage'] for data in self.raid.members.values())

        # Base reward pool (scales with boss difficulty)
        base_gold_pool = random.randint(50000, 100000)
        base_diamond_pool = random.randint(500, 1000)  # Renamed from gem to diamond
        base_tos_pool = random.randint(1000, 2000)
        base_xp_pool = random.randint(20000, 40000)

        for user_id in self.raid.members.keys():
            player = await Player.get(user_id)
            if player:
                player_data = self.raid.members[user_id]
                player_damage = player_data['damage']

                # Calculate damage percentage
                damage_percentage = (player_damage / total_damage) if total_damage > 0 else 0

                # Only reward players with >1% damage contribution
                if damage_percentage >= 0.01:  # 1% minimum
                    eligible_players.append(user_id)

                    # Track boss defeat for arise command eligibility
                    player.add_boss_defeat(self.raid.shadow_unlock)

                    # Calculate fair rewards based on damage contribution (capped at 25% max)
                    contribution_factor = min(damage_percentage, 0.25)  # Cap at 25%

                    # Distribute rewards based on contribution
                    gold_reward = int(base_gold_pool * contribution_factor)
                    diamond_reward = int(base_diamond_pool * contribution_factor)  # Renamed from gem to diamond
                    tos_reward = int(base_tos_pool * contribution_factor)
                    xp_reward = int(base_xp_pool * contribution_factor)

                    # Ensure minimum rewards for eligible players
                    gold_reward = max(gold_reward, 2000)
                    diamond_reward = max(diamond_reward, 25)  # Renamed from gem to diamond
                    tos_reward = max(tos_reward, 50)
                    xp_reward = max(xp_reward, 1000)

                    # Add rewards to player
                    player.gold += gold_reward
                    player.diamond += diamond_reward  # Using diamond as premium currency
                    player.tos += tos_reward
                    player.xp += xp_reward

                    # Check if player already owns this shadow
                    if shadow and self.raid.shadow_unlock in player.get_shadows():
                        already_owned_players.append(f"⚔️ {self.bot.get_user(user_id).display_name} ({damage_percentage:.1%})")
                    elif shadow:
                        # 25% CHANCE TO UNLOCK SHADOW (same as arise command)
                        unlock_roll = random.random()
                        if unlock_roll < 0.25:  # 25% success rate
                            player.add_shadow(self.raid.shadow_unlock)
                            unlocked_players.append(f"👤 {self.bot.get_user(user_id).display_name} ({damage_percentage:.1%})")

                            # Send DM notification about shadow unlock (with rate limit protection)
                            try:
                                user = self.bot.get_user(user_id)
                                if user:
                                    unlock_embed = discord.Embed(
                                        title="👤 **SHADOW UNLOCKED!** 👤",
                                        description=f"**{self.raid.shadow}** has joined your shadow army!",
                                        color=discord.Color.purple()
                                    )
                                    unlock_embed.add_field(
                                        name="🎉 Congratulations!",
                                        value=f"You rolled successfully (25% chance) and unlocked **{shadow.name}**!\nDamage Contribution: **{damage_percentage:.1%}**",
                                        inline=False
                                    )
                                    unlock_embed.add_field(
                                        name="📊 Shadow Stats",
                                        value=f"⚔️ **Attack Boost**: +{shadow.attack}%\n🛡️ **Defense Boost**: +{shadow.defense}%",
                                        inline=False
                                    )
                                    unlock_embed.add_field(
                                        name="🎁 Victory Rewards",
                                        value=f"💰 **Gold**: +{gold_reward:,}\n💎 **Diamonds**: +{diamond_reward}\n🔮 **TOS**: +{tos_reward}\n⚡ **XP**: +{xp_reward:,}",
                                        inline=False
                                    )
                                    unlock_embed.add_field(
                                        name="⚔️ Next Steps",
                                        value="Use `sl equip shadow` to equip your new shadow and gain its stat bonuses!",
                                        inline=False
                                    )
                                    unlock_embed.set_footer(text="Lucky! You got the 25% chance!")

                                    # Add delay to prevent rate limiting
                                    import asyncio
                                    await asyncio.sleep(0.5)  # 500ms delay between DMs
                                    await user.send(embed=unlock_embed)
                            except discord.errors.HTTPException:
                                pass  # Rate limited or DM failed
                            except:
                                pass  # Other DM failure
                        else:
                            # Failed the 25% roll
                            failed_players.append(f"💔 {self.bot.get_user(user_id).display_name} ({damage_percentage:.1%})")

                            # Send DM notification about failed attempt (with rate limit protection)
                            try:
                                user = self.bot.get_user(user_id)
                                if user:
                                    fail_embed = discord.Embed(
                                        title="💔 **Shadow Unlock Failed** 💔",
                                        description=f"You didn't get lucky this time (25% chance).\nDamage Contribution: **{damage_percentage:.1%}**",
                                        color=discord.Color.orange()
                                    )
                                    fail_embed.add_field(
                                        name="🔮 Try Again",
                                        value=f"Use `sl arise {self.raid.shadow_unlock}` to attempt unlocking **{shadow.name}** again!",
                                        inline=False
                                    )
                                    fail_embed.add_field(
                                        name="🎁 Victory Rewards",
                                        value=f"💰 **Gold**: +{gold_reward:,}\n💎 **Diamonds**: +{diamond_reward}\n🔮 **TOS**: +{tos_reward}\n⚡ **XP**: +{xp_reward:,}",
                                        inline=False
                                    )
                                    fail_embed.add_field(
                                        name="💰 Cost",
                                        value=f"Each arise attempt costs **{shadow.price} TOS** with a 25% success rate.",
                                        inline=False
                                    )
                                    fail_embed.set_footer(text="Better luck next time!")

                                    # Add delay to prevent rate limiting
                                    await asyncio.sleep(0.5)  # 500ms delay between DMs
                                    await user.send(embed=fail_embed)
                            except discord.errors.HTTPException:
                                pass  # Rate limited or DM failed
                            except:
                                pass  # Other DM failure

                    try:
                        await player.save()
                    except Exception as e:
                        print(f"Error saving player {user_id} after shadow defeat: {e}")
                else:
                    # Player didn't meet 1% damage requirement - no rewards or shadow unlock
                    pass

        # Show unlock results
        if unlocked_players:
            victory_embed.add_field(
                name="👤 **SHADOWS UNLOCKED! (25% Success)**",
                value="\n".join(unlocked_players[:10]) + f"\n\n🎉 **Lucky! {shadow.name} joined their shadow army!**",
                inline=False
            )

        if failed_players:
            victory_embed.add_field(
                name="💔 **Unlock Failed (75% Chance)**",
                value="\n".join(failed_players[:10]) + f"\n\n🔮 **Use `sl arise {self.raid.shadow_unlock}` to try again!**",
                inline=False
            )

        if already_owned_players:
            victory_embed.add_field(
                name="⚔️ **Already Own This Shadow**",
                value="\n".join(already_owned_players[:10]),
                inline=False
            )

        # Add rewards information
        eligible_count = len(eligible_players)
        total_participants = len(self.raid.members)

        victory_embed.add_field(
            name="🎁 **Victory Rewards (Damage-Based)**",
            value=(
                f"**Eligible Players**: {eligible_count}/{total_participants} (>1% damage)\n"
                f"💰 **Gold Pool**: {base_gold_pool:,} (split by contribution)\n"
                f"💎 **Diamond Pool**: {base_diamond_pool:,} (split by contribution)\n"
                f"🔮 **TOS Pool**: {base_tos_pool:,} (split by contribution)\n"
                f"⚡ **XP Pool**: {base_xp_pool:,} (split by contribution)\n"
                f"🎲 **Shadow Unlock**: 25% chance (eligible players only)\n"
                f"📊 **Max Contribution**: 25% cap (prevents monopolization)"
            ),
            inline=False
        )

        victory_embed.set_image(url=self.raid.image)
        victory_embed.set_footer(text="🌍 Shadow World Boss • Victory Rewards & Shadow Unlocks!")

        # CRITICAL: Update message with victory embed and COMPLETELY remove all interaction capability
        message_updated = False

        # Create a completely disabled view to prevent any further interaction
        disabled_view = discord.ui.View()
        disabled_view.stop()  # Immediately stop the view

        try:
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=victory_embed, view=disabled_view)
                message_updated = True
            else:
                await interaction.followup.edit_message(interaction.message.id, embed=victory_embed, view=disabled_view)
                message_updated = True
        except discord.errors.NotFound:
            # Interaction expired, try editing the message directly
            if self.message:
                try:
                    await self.message.edit(embed=victory_embed, view=disabled_view)
                    message_updated = True
                except:
                    pass  # Message editing failed
        except discord.errors.HTTPException:
            # Rate limited or other HTTP error, try direct message edit
            if self.message and not message_updated:
                try:
                    await self.message.edit(embed=victory_embed, view=disabled_view)
                    message_updated = True
                except:
                    pass

        # If all else fails, send a new message
        if not message_updated:
            try:
                await interaction.channel.send(embed=victory_embed)
            except:
                pass

        # Clean up raid
        await self.raid.delete()

        # Remove from world boss manager (mark as defeated)
        world_boss_manager = get_world_boss_manager(self.bot)
        world_boss_manager.remove_boss(interaction.guild.id, defeated=True)

    async def boss_retaliate(self):
        """Enhanced boss retaliation with interactive attacks"""
        if self.is_finished() or self.raid.health <= 0:
            logging.info("Boss retaliate cancelled: battle finished or boss dead")
            return

        # Determine attack type based on cooldowns and boss state
        self.boss_attack_cooldown -= 1
        self.boss_special_cooldown -= 1

        # Check if boss should enrage
        health_percentage = self.raid.health / self.raid.max_health
        if health_percentage <= self.boss_enrage_threshold and not self.is_enraged:
            self.is_enraged = True
            await self.boss_enrage()
            return

        # Choose attack type
        if self.boss_special_cooldown <= 0 and random.randint(1, 100) <= 30:  # 30% chance for special
            await self.boss_special_attack()
        else:
            await self.boss_basic_attack()

        # Update battle display with rate limiting protection
        if self.message and not self.is_finished():
            try:
                await self.message.edit(embed=self.create_battle_embed())
            except discord.errors.HTTPException:
                pass  # Rate limited, skip this update

    async def boss_enrage(self):
        """Boss enters enraged state at low health"""
        rarity = getattr(self.raid, 'rarity', 'Epic')
        enrage_message = f"💀 **{self.raid.shadow}** enters a BERSERK RAGE! All attacks are now more powerful!"

        if rarity == 'Legendary':
            enrage_message = f"🌟 **{self.raid.shadow}** transcends mortal limits! Reality bends to its will!"

        self.battle_log.append(enrage_message)

        # Enraged bosses attack more frequently and hit harder
        self.boss_attack_cooldown = 0
        self.boss_special_cooldown = 0

    async def boss_basic_attack(self):
        """Boss performs a basic attack on a random player"""
        if not self.raid.members:
            return

        # Select random alive player
        alive_players = [(uid, data) for uid, data in self.raid.members.items() if data['health'] > 0]
        if not alive_players:
            return

        target_id, target_data = random.choice(alive_players)
        attack = random.choice(self.boss_abilities['basic_attacks'])

        # Calculate damage (balanced for world bosses)
        base_damage = int(self.raid.attack * attack['damage_multiplier'])

        # Balance world boss damage to not be overpowered
        balanced_damage = max(1, int(base_damage * 0.6))  # 40% damage reduction for balance

        if self.is_enraged:
            balanced_damage = int(balanced_damage * 1.3)  # 30% more damage when enraged (reduced from 50%)

        # Apply damage with player defense
        actual_damage = max(1, balanced_damage - target_data.get('defense', 0))
        self.raid.members[target_id]['health'] = max(0, target_data['health'] - actual_damage)

        # Log the attack
        attack_message = f"💥 **{self.raid.shadow}** {attack['description']} against **{target_data['name']}** for `{actual_damage}` damage!"
        if self.is_enraged:
            attack_message = f"🔥 **ENRAGED** {attack_message}"

        self.battle_log.append(attack_message)

        # Check if player died
        if self.raid.members[target_id]['health'] <= 0:
            self.battle_log.append(f"💀 **{target_data['name']}** has been defeated!")

        self.boss_attack_cooldown = 2  # 2 turns until next basic attack

    async def boss_special_attack(self):
        """Boss performs a special attack"""
        if not self.raid.members:
            return

        attack = random.choice(self.boss_abilities['special_attacks'])
        rarity = getattr(self.raid, 'rarity', 'Epic')

        # Calculate balanced damage for special attacks
        base_damage = int(self.raid.attack * attack['damage_multiplier'])

        # Balance special attack damage to not be overpowered
        balanced_damage = max(1, int(base_damage * 0.7))  # 30% damage reduction for balance

        if self.is_enraged:
            balanced_damage = int(balanced_damage * 1.4)  # 40% more damage when enraged (reduced from 80%)

        if rarity == 'Legendary':
            balanced_damage = int(balanced_damage * 1.2)  # Legendary bosses hit harder (reduced from 30% to 20%)

        targets = []
        if attack.get('targets_all', False):
            # Attack all alive players
            targets = [(uid, data) for uid, data in self.raid.members.items() if data['health'] > 0]
            attack_message = f"🌪️ **{self.raid.shadow}** {attack['description']} hitting ALL hunters!"
        else:
            # Attack random player
            alive_players = [(uid, data) for uid, data in self.raid.members.items() if data['health'] > 0]
            if alive_players:
                targets = [random.choice(alive_players)]
                attack_message = f"⚡ **{self.raid.shadow}** {attack['description']} against **{targets[0][1]['name']}**!"

        if self.is_enraged:
            attack_message = f"🔥 **ENRAGED** {attack_message}"

        self.battle_log.append(attack_message)

        # Apply damage to all targets
        total_damage_dealt = 0
        for target_id, target_data in targets:
            actual_damage = max(1, balanced_damage - target_data.get('defense', 0))
            self.raid.members[target_id]['health'] = max(0, target_data['health'] - actual_damage)
            total_damage_dealt += actual_damage

            if self.raid.members[target_id]['health'] <= 0:
                self.battle_log.append(f"💀 **{target_data['name']}** has been defeated by the special attack!")

        if len(targets) > 1:
            self.battle_log.append(f"💥 Total damage dealt: `{total_damage_dealt}`")
        else:
            self.battle_log.append(f"💥 Damage dealt: `{total_damage_dealt}`")

        self.boss_special_cooldown = attack.get('cooldown', 4)  # Set cooldown for next special

    async def enhanced_boss_retaliate_loop(self):
        """Enhanced boss retaliation loop with more frequent and intelligent attacks"""
        try:
            while not self.is_finished() and self.raid.health > 0 and not getattr(self, '_battle_ended', False):
                # Wait between boss actions (faster than regular raids)
                await asyncio.sleep(8)  # Boss attacks every 8 seconds instead of 15

                # CRITICAL: Check if battle is finished or boss is dead BEFORE doing anything
                if (self.is_finished() or self.raid.health <= 0 or not hasattr(self, 'raid') or
                    getattr(self, '_battle_ended', False)):
                    logging.info("Boss retaliate loop ending: battle finished, boss dead, or raid deleted")
                    break

                # Check if any players are alive
                alive_players = [data for data in self.raid.members.values() if data['health'] > 0]
                if not alive_players:
                    await self.end_battle(False, "💀 All hunters have been defeated by the World Boss!")
                    break

                # CRITICAL: Double check boss is still alive before attacking
                if self.raid.health <= 0:
                    logging.info("Boss retaliate loop ending: boss health is 0")
                    break

                # Boss attacks only if still alive and battle not finished
                if self.raid.health > 0 and not self.is_finished():
                    await self.boss_retaliate()

                # CRITICAL: Final check after boss attack - if boss died during attack, stop immediately
                if self.is_finished() or self.raid.health <= 0:
                    logging.info("Boss retaliate loop ending: battle finished or boss died during attack")
                    break

                # Check if all players are dead after attack
                alive_players = [data for data in self.raid.members.values() if data['health'] > 0]
                if not alive_players:
                    await self.end_battle(False, "💀 The World Boss has defeated all hunters!")
                    break

        except asyncio.CancelledError:
            logging.info("Boss retaliate loop cancelled")
        except Exception as e:
            logging.error(f"Error in enhanced boss retaliate loop: {e}")

    def create_battle_embed(self):
        """Create enhanced battle embed for world boss with boss status"""
        rarity = getattr(self.raid, 'rarity', 'Epic')
        health_percentage = self.raid.health / self.raid.max_health

        # Dynamic title based on boss state
        title = f"🌍 WORLD BOSS BATTLE: {self.raid.shadow}"
        if self.is_enraged:
            title = f"🔥 ENRAGED WORLD BOSS: {self.raid.shadow}"

        embed = discord.Embed(
            title=title,
            description=f"**Rarity**: `{rarity}`\n**Level**: `{self.raid.level}`\n{getClassEmoji(self.raid.raid_class)} **Element**: `{self.raid.raid_class}`",
            color=discord.Color.gold() if rarity == 'Legendary' else discord.Color.red()
        )

        embed.set_image(url=self.raid.image)

        # Enhanced boss health display with status
        health_bar = pbar(self.raid.health, self.raid.max_health)
        boss_status = ""

        if self.is_enraged:
            boss_status = " 🔥 **ENRAGED**"
        elif health_percentage <= 0.5:
            boss_status = " ⚠️ **WOUNDED**"
        elif health_percentage <= 0.75:
            boss_status = " 🟡 **INJURED**"

        embed.add_field(name=f"Boss Health{boss_status}", value=health_bar, inline=False)

        # Boss abilities status
        if self.is_enraged:
            abilities_text = "💀 **All abilities enhanced!**\n⚡ **Attacks more frequently**\n🔥 **+50% damage to basic attacks**\n🌪️ **+80% damage to special attacks**"
        else:
            next_special = max(0, self.boss_special_cooldown)
            abilities_text = f"⚔️ **Basic Attack**: Ready\n⚡ **Special Attack**: {next_special} turns"
            if health_percentage <= self.boss_enrage_threshold + 0.1:
                abilities_text += f"\n⚠️ **Enrage Warning**: Boss will enrage at 30% health!"

        embed.add_field(name="🎯 Boss Status", value=abilities_text, inline=True)

        # Show battle log with enhanced formatting
        log_text = "\n".join(self.battle_log[-6:]) if self.battle_log else "The epic battle begins..."
        embed.add_field(name="⚔️ Battle Log", value=f"```{log_text}```", inline=False)

        # Show active hunters with health bars
        alive_hunters = []
        dead_hunters = []

        for data in self.raid.members.values():
            health_percent = data['health'] / data['max_health'] if data['max_health'] > 0 else 0
            if data['health'] > 0:
                if health_percent > 0.7:
                    status = "💚"
                elif health_percent > 0.3:
                    status = "🟡"
                else:
                    status = "🔴"
                alive_hunters.append(f"{status} **{data['name']}**: `{data['health']}/{data['max_health']}`")
            else:
                dead_hunters.append(f"💀 **{data['name']}**: `0/{data['max_health']}`")

        all_hunters = alive_hunters + dead_hunters
        hunters_text = "\n".join(all_hunters) if all_hunters else "No hunters in battle"
        embed.add_field(name=f"🏹 Hunters ({len(alive_hunters)} alive)", value=hunters_text, inline=False)

        # Enhanced footer with boss difficulty indicator
        difficulty_text = "🌍 World Boss Battle"
        if rarity == 'Legendary':
            difficulty_text += " • ⭐ LEGENDARY DIFFICULTY"
        elif rarity == 'Epic':
            difficulty_text += " • 🟣 EPIC DIFFICULTY"
        elif rarity == 'Rare':
            difficulty_text += " • 🔵 RARE DIFFICULTY"

        if self.is_enraged:
            difficulty_text += " • 🔥 ENRAGED STATE"

        embed.set_footer(text=difficulty_text)
        return embed

    async def end_battle(self, victory: bool, reason: str):
        """Enhanced end battle with world boss rewards"""
        if self.is_finished(): return

        # CRITICAL: Set battle as inactive
        self.battle_active = False

        # CRITICAL: Ensure boss is dead and stays dead
        if victory:
            self.raid.health = 0

        # Immediately stop all boss activities
        self.stop_all_boss_activities()
        self.stop()

        # Cancel the enhanced boss retaliate task if it exists
        if hasattr(self, 'enhanced_boss_retaliate_task') and self.enhanced_boss_retaliate_task:
            self.enhanced_boss_retaliate_task.cancel()
            self.enhanced_boss_retaliate_task = None

        final_embed = discord.Embed(color=discord.Color.gold() if victory else discord.Color.red())
        final_embed.title = "🌍 WORLD BOSS VICTORY! 🌍" if victory else "💀 World Boss Defeated You"
        final_embed.description = reason

        total_damage = sum(p.get('damage', 0) for p in self.raid.members.values()) or 1
        rarity = getattr(self.raid, 'rarity', 'Epic')

        # World boss rarity multipliers (applied to the existing raid reward system)
        rarity_multipliers = {
            'Common': 1.2,
            'Rare': 1.5,
            'Epic': 2.0,
            'Legendary': 2.5,
            'UR': 4.0
        }
        multiplier = rarity_multipliers.get(rarity, 2.0)

        for user_id, data in self.raid.members.items():
            player_obj = await Player.get(user_id)
            if not player_obj: continue

            damage_dealt = data.get('damage', 0)
            damage_percent = (damage_dealt / total_damage) * 100

            # World boss rewards are 50% less and split among participants
            participant_count = len(self.raid.members)
            split_factor = max(1, participant_count)  # Ensure we don't divide by 0

            # Reduced base rewards (50% less than regular raids)
            base_gold = (2000 + (self.raid.level * 50)) * 0.5  # 50% reduction
            damage_bonus_gold = int(damage_dealt * 0.075)  # Reduced damage bonus (50% less)
            participation_bonus = (1000 if victory else 500) * 0.5  # 50% less participation bonus

            # Split rewards among all participants
            gold_reward = int((base_gold + damage_bonus_gold + participation_bonus) / split_factor * multiplier)

            # XP rewards also reduced by 50% and split
            base_xp = (200 + (self.raid.level * 10)) * 0.5  # 50% reduction
            damage_xp = int(damage_dealt / 16)  # Reduced XP from damage (50% less)
            xp_reward = int((base_xp + damage_xp) / split_factor * multiplier)

            # Trace rewards only on victory, scaled by level and performance
            if victory:
                base_traces = 50 + (self.raid.level * 2)  # Level-scaled traces
                performance_traces = int(damage_dealt / 100)  # Performance bonus
                traces_reward = int((base_traces + performance_traces) * multiplier)
            else:
                traces_reward = 0

            # Same MVP system as regular raids
            if damage_percent >= 40:  # MVP bonus (40%+ damage)
                gold_reward = int(gold_reward * 1.5)
                xp_reward = int(xp_reward * 1.3)
                traces_reward = int(traces_reward * 1.2) if victory else 0
                mvp_bonus = " 🏆 **MVP BONUS!**"
            elif damage_percent >= 25:  # High performer bonus (25%+ damage)
                gold_reward = int(gold_reward * 1.2)
                xp_reward = int(xp_reward * 1.1)
                traces_reward = int(traces_reward * 1.1) if victory else 0
                mvp_bonus = " ⭐ **High Performer!**"
            else:
                mvp_bonus = ""

            # Apply rewards
            player_obj.gold += gold_reward
            if self.message:
                await player_obj.add_xp(self.bot, xp_reward, self.message.channel)
            if traces_reward > 0:
                player_obj.tos += traces_reward

            # Additional rewards for victory (same as regular raids but with multiplier)
            if victory:
                # Gate keys for completing raids
                key_reward = int((1 + (self.raid.level // 25)) * multiplier)  # 1 key + bonus for high level raids
                player_obj.key += key_reward

                # Tickets for raid participation
                ticket_reward = int((2 + (self.raid.level // 50)) * multiplier)  # 2 tickets + bonus
                player_obj.ticket += ticket_reward

                # Special world boss bonus: rare chance for diamonds on legendary bosses
                if rarity == 'Legendary' and random.randint(1, 100) <= 20:
                    diamond_bonus = random.randint(25, 100)
                    player_obj.diamond += diamond_bonus
                    mvp_bonus += f" 💎 **+{diamond_bonus} DIAMONDS!**"

            player_obj.inc = False
            # Track world boss completion for missions
            if victory and hasattr(self.raid, 'is_world_boss') and self.raid.is_world_boss:
                player_obj.mIncrease("worldboss")
                # Track mission progress for world boss victories
                from commands.missions import track_mission_progress
                await track_mission_progress(user_id, "worldboss", 1)
            else:
                player_obj.mIncrease("raid")
            await player_obj.save()

            # Build reward string (same format as regular raids)
            reward_str = f"{getEmoji('gold')} `{gold_reward:,}` | {getEmoji('xp')} `{xp_reward:,}`"
            if traces_reward > 0:
                reward_str += f" | {getEmoji('trace')} `{traces_reward}`"
            if victory:
                reward_str += f" | {getEmoji('key')} `{key_reward}` | {getEmoji('ticket')} `{ticket_reward}`"

            user_display_name = data.get('name', f"User {user_id}")
            final_embed.add_field(
                name=f"{user_display_name}{mvp_bonus}",
                value=f"⚔️ Damage: `{damage_dealt:,}` ({damage_percent:.1f}%)\n🎁 Rewards: {reward_str}",
                inline=False
            )

        if victory:
            final_embed.add_field(
                name="🌍 World Boss Defeated!",
                value=f"The **{rarity} {self.raid.shadow}** has been vanquished!\nAll participants receive enhanced rewards!",
                inline=False
            )

        if self.message:
            await self.message.edit(embed=final_embed, view=None)

        # Remove from world boss manager BEFORE deleting raid
        if hasattr(self.raid, 'is_world_boss') and self.raid.is_world_boss:
            world_boss_manager = get_world_boss_manager(self.bot)
            # Mark as defeated if victory, otherwise just timeout/despawn
            world_boss_manager.remove_boss(self.message.guild.id if self.message else 0, defeated=victory)

        await self.raid.delete()


class WorldBossManager:
    """Manages world boss spawns across all servers"""

    def __init__(self, bot):
        self.bot = bot
        self.active_bosses: Dict[int, Raid] = {}  # guild_id -> Raid
        self.spawn_triggers = {
            'time_based': {'weight': 30, 'cooldown': 3600},  # Every 1-2 hours
            'player_activity': {'weight': 25, 'threshold': 50},  # 50 commands in 10 minutes
            'arena_streak': {'weight': 20, 'threshold': 10},  # Someone gets 10+ win streak
            'raid_completion': {'weight': 15, 'trigger_count': 3},  # 3 regular raids completed
            'gate_clear': {'weight': 10, 'trigger_count': 2},  # 2 gates cleared
        }
        self.activity_tracker = {}  # guild_id -> {'commands': count, 'last_reset': time}
        self.last_spawn_time = {}  # guild_id -> timestamp
        self.defeated_bosses = {}  # guild_id -> timestamp (for longer cooldown tracking)

        # Shadow World Boss pool - players kill these to unlock shadows
        self.shadow_boss_pool = {
            'common': [
                {'name': 'Igris', 'type': 'Knight', 'rarity': 'Common', 'level_range': (60, 80), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'igris'},
                {'name': 'Iron', 'type': 'Warrior', 'rarity': 'Common', 'level_range': (55, 75), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'iron'},
                {'name': 'Tank', 'type': 'Guardian', 'rarity': 'Common', 'level_range': (50, 70), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'tank'},
            ],
            'rare': [
                {'name': 'Tusk', 'type': 'Beast', 'rarity': 'Rare', 'level_range': (70, 90), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'tusk'},
                {'name': 'Kaisel', 'type': 'Dragon', 'rarity': 'Rare', 'level_range': (75, 95), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'kaisel'},
                {'name': 'Greed', 'type': 'Assassin', 'rarity': 'Rare', 'level_range': (65, 85), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'greed'},
            ],
            'epic': [
                {'name': 'Beru', 'type': 'Earth', 'rarity': 'Epic', 'level_range': (80, 100), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'beru'},
                {'name': 'Bellion', 'type': 'Dark', 'rarity': 'Epic', 'level_range': (85, 105), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'bellion'},
                {'name': 'Flame General', 'type': 'Fire', 'rarity': 'Epic', 'level_range': (75, 95), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'flame_general'},
                {'name': 'Storm Lord', 'type': 'Wind', 'rarity': 'Epic', 'level_range': (80, 100), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'storm_lord'},
                {'name': 'Tide Master', 'type': 'Water', 'rarity': 'Epic', 'level_range': (78, 98), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'tide_master'},
                {'name': 'Radiant Knight', 'type': 'Light', 'rarity': 'Epic', 'level_range': (82, 102), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'radiant_knight'},
            ],
            'legendary': [
                {'name': 'Antares', 'type': 'Fire', 'rarity': 'Legendary', 'level_range': (100, 150), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'antares'},
                {'name': 'Thomas Andre', 'type': 'Earth', 'rarity': 'Legendary', 'level_range': (110, 160), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'thomas_andre'},
                {'name': 'Frost Monarch', 'type': 'Water', 'rarity': 'Legendary', 'level_range': (105, 155), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'frost_monarch'},
                {'name': 'Shadow Monarch', 'type': 'Dark', 'rarity': 'Legendary', 'level_range': (120, 170), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'shadow_monarch'},
                {'name': 'Wind Sovereign', 'type': 'Wind', 'rarity': 'Legendary', 'level_range': (100, 150), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'wind_sovereign'},
                {'name': 'Light Emperor', 'type': 'Light', 'rarity': 'Legendary', 'level_range': (115, 165), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'light_emperor'},
            ]
        }

    async def start_world_boss_system(self):
        """Initialize the world boss system"""
        if not self.world_boss_loop.is_running():
            self.world_boss_loop.start()
        logging.info("🌍 World Boss system started!")

    @tasks.loop(minutes=5)  # Check every 5 minutes
    async def world_boss_loop(self):
        """Main loop for world boss spawning"""
        try:
            for guild in self.bot.guilds:
                if await self.should_spawn_boss(guild.id):
                    await self.spawn_world_boss(guild)
        except Exception as e:
            logging.error(f"Error in world boss loop: {e}")

    async def should_spawn_boss(self, guild_id: int) -> bool:
        """Determine if a world boss should spawn in this guild"""
        # Don't spawn if there's already an active boss
        if guild_id in self.active_bosses:
            return False

        # Check cooldown - different cooldowns based on how last boss ended
        last_spawn = self.last_spawn_time.get(guild_id, 0)
        current_time = time.time()

        # Check if we have a defeated boss record (longer cooldown)
        if hasattr(self, 'defeated_bosses') and guild_id in getattr(self, 'defeated_bosses', {}):
            # 2 hours cooldown after defeat (as requested)
            if current_time - last_spawn < 7200:  # 2 hours
                return False
            # Remove from defeated list after cooldown
            del self.defeated_bosses[guild_id]
        else:
            # 2 hours minimum cooldown for timeout/despawn (changed from 30 minutes)
            if current_time - last_spawn < 7200:  # 2 hours
                return False

        # Random chance based on activity and time
        base_chance = 0.1  # 10% base chance every 5 minutes

        # Increase chance based on activity
        activity = self.activity_tracker.get(guild_id, {})
        if activity.get('commands', 0) > 20:  # High activity
            base_chance *= 1.5

        # Increase chance based on time since last spawn
        time_multiplier = min(2.0, (time.time() - last_spawn) / 7200)  # Max 2x after 2 hours
        final_chance = base_chance * time_multiplier

        return random.random() < final_chance

    async def spawn_world_boss(self, guild: discord.Guild):
        """Spawn a world boss in the specified guild"""
        try:
            # Find a suitable channel (general, raids, or first available)
            channel = None
            for ch in guild.text_channels:
                if any(name in ch.name.lower() for name in ['general', 'raid', 'boss', 'world']):
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break

            if not channel:
                # Fallback to first available channel
                for ch in guild.text_channels:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break

            if not channel:
                return  # No suitable channel found

            # Select boss based on rarity weights
            rarity_weights = {'common': 45, 'rare': 30, 'epic': 15, 'legendary': 8, 'ur': 2}
            selected_rarity = random.choices(
                list(rarity_weights.keys()),
                weights=list(rarity_weights.values())
            )[0]

            boss_data = random.choice(self.shadow_boss_pool[selected_rarity])
            level = random.randint(*boss_data['level_range'])

            # Create the shadow world boss raid (this already sends the message)
            raid = await Raid.spawn_shadow_world_boss(self.bot, channel, boss_data, level)
            if raid:
                self.active_bosses[guild.id] = raid
                self.last_spawn_time[guild.id] = time.time()

                logging.info(f"🌍 World Boss '{boss_data['name']}' spawned in {guild.name}")

                # Send notifications to users who have world boss alerts enabled
                await self.send_world_boss_notifications(guild, boss_data, channel)

        except Exception as e:
            logging.error(f"Error spawning world boss in {guild.name}: {e}")

    def track_activity(self, guild_id: int):
        """Track command activity for spawn triggers"""
        current_time = time.time()

        if guild_id not in self.activity_tracker:
            self.activity_tracker[guild_id] = {'commands': 0, 'last_reset': current_time}

        activity = self.activity_tracker[guild_id]

        # Reset counter every 10 minutes
        if current_time - activity['last_reset'] > 600:
            activity['commands'] = 0
            activity['last_reset'] = current_time

        activity['commands'] += 1

    async def trigger_special_spawn(self, guild_id: int, trigger_type: str):
        """Trigger a special world boss spawn based on events"""
        if guild_id in self.active_bosses:
            return  # Already has active boss

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        # Higher chance for special triggers
        if random.random() < 0.3:  # 30% chance
            await self.spawn_world_boss(guild)

    def remove_boss(self, guild_id: int, defeated: bool = False):
        """Remove a world boss when it's defeated or expires"""
        if guild_id in self.active_bosses:
            del self.active_bosses[guild_id]

            # Set last spawn time to current time
            self.last_spawn_time[guild_id] = time.time()

            # Track defeated bosses for reference (both defeated and despawned now have 2-hour cooldown)
            if defeated:
                if not hasattr(self, 'defeated_bosses'):
                    self.defeated_bosses = {}
                self.defeated_bosses[guild_id] = time.time()
                logging.info(f"🌍 World Boss defeated in guild {guild_id}, 2-hour cooldown started")
            else:
                logging.info(f"🌍 World Boss despawned in guild {guild_id}, 2-hour cooldown started")

    async def send_world_boss_notifications(self, guild: discord.Guild, boss_data: dict, channel: discord.TextChannel):
        """Send notifications to users with world boss alerts enabled"""
        try:
            from structure.notification_system import get_notification_manager
            notification_manager = get_notification_manager(self.bot)

            # Get all users who have world boss alerts enabled with their specific settings
            import aiosqlite
            import json
            from datetime import datetime

            async with aiosqlite.connect("new_player.db") as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute("""
                    SELECT * FROM notification_settings
                    WHERE world_boss_alerts = 1
                """)

                user_rows = await cursor.fetchall()

                for row in user_rows:
                    user_id = row['user_id']

                    # Check if user is in this guild
                    member = guild.get_member(user_id)
                    if member:
                        # Check server-specific settings
                        allowed_servers = json.loads(row['world_boss_servers'] or '[]')
                        if allowed_servers and str(guild.id) not in allowed_servers:
                            continue  # User doesn't want notifications from this server

                        # Check rarity filter
                        allowed_rarities = json.loads(row['world_boss_rarities'] or '["common","rare","epic","legendary"]')
                        boss_rarity = boss_data.get('rarity', 'common').lower()
                        if boss_rarity not in allowed_rarities:
                            continue  # User doesn't want notifications for this rarity

                        # Check time-based filter (UTC time)
                        wb_hours_start = row['world_boss_hours_start']
                        wb_hours_end = row['world_boss_hours_end']
                        if wb_hours_start is not None and wb_hours_end is not None:
                            current_hour = datetime.utcnow().hour  # Always use UTC for filtering

                            # Check if current UTC time is within allowed hours
                            if wb_hours_start <= wb_hours_end:
                                if not (wb_hours_start <= current_hour < wb_hours_end):
                                    continue  # Outside allowed hours
                            else:  # Hours span midnight
                                if not (current_hour >= wb_hours_start or current_hour < wb_hours_end):
                                    continue  # Outside allowed hours
                        # Send immediate notification
                        try:
                            user = self.bot.get_user(user_id)
                            if user:
                                embed = discord.Embed(
                                    title="⚔️ World Boss Spawned!",
                                    description=f"**{boss_data['name']}** has appeared in **{guild.name}**!\n\n🔗 **[Join the Battle]({channel.jump_url})**",
                                    color=discord.Color.red()
                                )
                                embed.add_field(
                                    name="📍 Location",
                                    value=f"{channel.mention}",
                                    inline=True
                                )
                                embed.add_field(
                                    name="⭐ Rarity",
                                    value=boss_data.get('rarity', 'Unknown').title(),
                                    inline=True
                                )
                                embed.set_footer(text="⚔️ World Boss Alert • Solo Leveling Bot")

                                # Get user settings to determine delivery method
                                settings = await notification_manager.get_user_settings(user_id)

                                if settings.get('dm_notifications', 1):
                                    try:
                                        await user.send(embed=embed)
                                    except discord.Forbidden:
                                        # Try channel notification if DM fails (ephemeral to avoid spam)
                                        if settings.get('channel_notifications', 0):
                                            await notification_manager.send_channel_notification(user_id, embed, settings, ephemeral=True)
                                elif settings.get('channel_notifications', 0):
                                    # Channel-only notifications are ephemeral for world bosses to avoid spam
                                    await notification_manager.send_channel_notification(user_id, embed, settings, ephemeral=True)

                        except Exception as e:
                            logging.error(f"Error sending world boss notification to user {user_id}: {e}")

        except Exception as e:
            logging.error(f"Error sending world boss notifications: {e}")


# Global world boss manager instance
world_boss_manager = None

def get_world_boss_manager(bot) -> WorldBossManager:
    """Get or create the world boss manager"""
    global world_boss_manager
    if world_boss_manager is None:
        world_boss_manager = WorldBossManager(bot)
    return world_boss_manager